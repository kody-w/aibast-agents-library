import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import {
  existsSync,
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";
import test from "node:test";
import {
  validateConfiguration,
} from "app-builder-lib/out/util/config/config.js";

import {
  createBuilderConfiguration,
  evaluateWindowsSigningPolicy,
  parsePackagingArguments,
} from "../scripts/package-platform.mjs";
import { validateNotarizationLog } from "../scripts/notarize-target.mjs";
import {
  artifactName,
  publisherMatchesApplicationId,
} from "../scripts/package-contract.mjs";
import {
  binaryArchitectures,
  parseGateArguments,
} from "../scripts/package-gate.mjs";
import {
  createReleaseManifest,
  parseChecksums,
  RELEASE_MANIFEST_SCHEMA,
} from "../scripts/release-manifest.mjs";
import { upsertReleaseManifestFence } from "../scripts/fence-release-manifest.mjs";
import {
  parseReleaseManifest,
  RELEASE_MANIFEST_SCHEMA as DOWNLOAD_CENTER_MANIFEST_SCHEMA,
} from "../download-center.js";
import {
  evaluatePolicyReadiness,
  loadNativeMediaPolicy,
} from "../scripts/native-media-gate.mjs";
import {
  resolvePackageAuthority,
} from "../scripts/prepare-package-bootstrap.mjs";
import {
  assertUnsignedUploadPolicy,
} from "../scripts/unsigned-upload-gate.mjs";
import {
  evaluateToolchainPolicy,
  installedToolchain,
  loadToolchainPolicy,
} from "../scripts/toolchain-policy.mjs";
import {
  releaseContentFingerprint,
  verifyReleaseSnapshot,
} from "../scripts/release-race-guard.mjs";
import {
  assertImmutableReleasesEnabled,
} from "../scripts/immutable-release-policy.mjs";
import {
  createWindowsSigningInput,
  verifyWindowsSigningInput,
} from "../scripts/windows-signing-input.mjs";
import {
  createAtomicStateWriter,
  createSnapshotVerifier,
  mergeDurableState,
  quiescePublishOperation,
  reconcileInterruptedSignal,
  recoverFromDurableState,
  recoveryRequiredFromState,
  runReleaseTransition,
  startAbortableExecFile,
} from "../scripts/publish-release-state-machine.mjs";
import {
  createValidatedWindowsBuilderConfiguration,
} from "../scripts/sign-validated-windows-input.mjs";
import {
  selectPreviousWindowsBinary,
} from "../scripts/windows-upgrade-policy.mjs";
import {
  loadWindowsSigningPolicy,
  validateWindowsSigningEvidence,
} from "../scripts/windows-signing-policy.mjs";


const betaDir = path.resolve(import.meta.dirname, "..");
const repositoryDir = path.resolve(betaDir, "..");
const workflowPath = path.join(
  repositoryDir,
  ".github",
  "workflows",
  "frontier-binaries.yml",
);
let workflowContract;

function loadWorkflowContract() {
  if (workflowContract !== undefined) {
    return workflowContract;
  }
  if (existsSync(workflowPath)) {
    workflowContract = readFileSync(workflowPath, "utf8");
    return workflowContract;
  }
  const sparsePaths = execFileSync(
    "git",
    ["-C", repositoryDir, "sparse-checkout", "list"],
    { encoding: "utf8" },
  ).split(/\r?\n/).filter(Boolean).sort();
  assert.deepEqual(
    sparsePaths,
    ["beta", "tools/rapp1"],
    "the workflow contract may be absent only from the intentional beta runtime sparse checkout",
  );
  workflowContract = null;
  return workflowContract;
}

function workflowJob(workflow, name) {
  const marker = `\n  ${name}:\n`;
  const start = workflow.indexOf(marker);
  assert.ok(start >= 0, `workflow job ${name} is missing`);
  const bodyStart = start + marker.length;
  const remainder = workflow.slice(bodyStart);
  const next = remainder.search(/\n  [a-z0-9-]+:\n/);
  return next < 0 ? remainder : remainder.slice(0, next);
}

function mach64(cpuType) {
  const buffer = Buffer.alloc(32);
  buffer.writeUInt32LE(0xfeedfacf, 0);
  buffer.writeUInt32LE(cpuType, 4);
  return buffer;
}

function pe64(machine) {
  const buffer = Buffer.alloc(256);
  buffer.write("MZ", 0, "ascii");
  buffer.writeUInt32LE(128, 0x3c);
  buffer.write("PE\0\0", 128, "ascii");
  buffer.writeUInt16LE(machine, 132);
  return buffer;
}

test("binary architecture parser identifies native Mach-O and PE files", () => {
  assert.deepEqual(binaryArchitectures(mach64(0x0100000c)), ["arm64"]);
  assert.deepEqual(binaryArchitectures(mach64(0x01000007)), ["x64"]);
  assert.deepEqual(binaryArchitectures(pe64(0x8664)), ["x64"]);
  assert.deepEqual(binaryArchitectures(pe64(0xaa64)), ["arm64"]);
  const universal = Buffer.alloc(48);
  universal.writeUInt32BE(0xcafebabe, 0);
  universal.writeUInt32BE(2, 4);
  universal.writeUInt32BE(0x01000007, 8);
  universal.writeUInt32BE(0x0100000c, 28);
  assert.deepEqual(binaryArchitectures(universal), ["arm64", "x64"]);
  assert.deepEqual(binaryArchitectures(Buffer.from("not a binary")), []);
});

test("packaging refuses Windows ARM64 and cross-architecture hosts", () => {
  assert.throws(
    () => parsePackagingArguments(["--platform", "windows", "--arch", "arm64"]),
    /intentionally blocked/,
  );
  assert.throws(
    () =>
      parsePackagingArguments([
        "--platform",
        "macos",
        "--arch",
        "arm64",
        "--skip-signing",
        "true",
      ]),
    /Unsupported argument/,
  );
  assert.throws(
    () =>
      parseGateArguments(
        ["--platform", "macos", "--arch", "x64", "--mode", "unsigned"],
        { platform: "darwin", arch: "arm64" },
      ),
    /native darwin\/x64 host/,
  );
});

test("current nonfree native media keeps binary publication blocked", () => {
  const policy = loadNativeMediaPolicy(
    path.join(betaDir, "build", "native-media-policy.json"),
  );
  const readiness = evaluatePolicyReadiness(policy);
  assert.equal(policy.publication_enabled, false);
  assert.equal(readiness.publication_ready, false);
  assert.match(readiness.blockers.join("\n"), /enable-nonfree/);
  assert.match(readiness.blockers.join("\n"), /macos-arm64\/ffmpeg/);
  assert.match(readiness.blockers.join("\n"), /windows-x64\/ffprobe/);
  const booleanOnlyMutation = structuredClone(policy);
  booleanOnlyMutation.publication_enabled = true;
  assert.equal(
    evaluatePolicyReadiness(booleanOnlyMutation).publication_ready,
    false,
    "flipping only the media publication boolean must not bypass provenance",
  );
  const gateSource = readFileSync(
    path.join(betaDir, "scripts", "package-gate.mjs"),
    "utf8",
  );
  assert.match(gateSource, /PACKAGE VERIFIED, PUBLICATION BLOCKED/);
});

test("package bootstrap release authority is canonical and staging is distinct", () => {
  const canonical = resolvePackageAuthority({
    signingMode: "signed",
    mode: "release",
    sourceRepository: "microsoft/aibast-agents-library",
    authorityUrl:
      "https://github.com/microsoft/aibast-agents-library.git",
  });

  test("unsigned workflow has deterministic non-production identity defaults", () => {
    const workflow = loadWorkflowContract();
    if (workflow === null) {
      return;
    }
    const mac = workflowJob(workflow, "verify-macos");
    assert.match(
      mac,
      /export FRONTIER_PACKAGE_APP_ID="\$\{FRONTIER_PACKAGE_APP_ID:-io\.github\.aibast\.frontier-staging\}"/,
    );
    assert.match(
      mac,
      /export FRONTIER_PACKAGE_PRODUCT_NAME="\$\{FRONTIER_PACKAGE_PRODUCT_NAME:-RAPP Brainstem Frontier Staging\}"/,
    );
    const windows = workflowJob(workflow, "verify-windows");
    assert.match(
      windows,
      /IsNullOrWhiteSpace\(\$env:FRONTIER_PACKAGE_APP_ID\)[\s\S]*io\.github\.aibast\.frontier-staging/,
    );
    assert.match(
      windows,
      /IsNullOrWhiteSpace\(\$env:FRONTIER_PACKAGE_PRODUCT_NAME\)[\s\S]*RAPP Brainstem Frontier Staging/,
    );
  });

  assert.equal(canonical.applicationId, "com.microsoft.aibast.rapp-brainstem-beta");
  assert.throws(
    () =>
      resolvePackageAuthority({
        signingMode: "signed",
        mode: "release",
        sourceRepository: "example/fork",
        authorityUrl: "https://github.com/example/fork.git",
      }),
    /must be canonical/,
  );
  assert.throws(
    () =>
      resolvePackageAuthority({
        signingMode: "unsigned",
        mode: "staging",
        sourceRepository: "example/fork",
        authorityUrl: "https://github.com/example/fork.git",
      }),
    /distinct application ID/,
  );
  const staging = resolvePackageAuthority({
    signingMode: "unsigned",
    mode: "staging",
    sourceRepository: "example/fork",
    authorityUrl: "https://github.com/example/fork.git",
    applicationId: "com.example.frontier-staging",
    productName: "RAPP Brainstem Frontier Staging",
  });
  assert.equal(staging.authorityRepository, "example/fork");
  const policy = JSON.parse(
    readFileSync(
      path.join(betaDir, "build", "package-bootstrap-policy.json"),
      "utf8",
    ),
  );
  assert.equal(policy.publication_enabled, true);
  assert.deepEqual(policy.publication_blockers, []);
  assert.ok(policy.required_package_gate_contracts.length >= 9);
});

test("unavailable requested toolchain versions block publication honestly", () => {
  const policy = loadToolchainPolicy();
  const installed = installedToolchain();
  assert.deepEqual(policy.required, {
    electron: "43.6.0",
    electron_builder: "26.16.0",
    macos_minimum: "12.0",
  });
  assert.deepEqual(installed, {
    electron: "43.4.1",
    electronBuilder: "26.15.7",
    macosMinimum: "12.0",
  });
  const blockers = policy.publication_blockers.join("\n");
  assert.match(blockers, /electron-builder@26\.16\.0 release and tag exist/);
  assert.match(blockers, /configured or public npm registry/);
  assert.doesNotMatch(blockers, /no .*upstream .*tag/i);
  assert.equal(
    evaluateToolchainPolicy(policy, installed).publicationReady,
    false,
  );
  assert.equal(
    evaluateToolchainPolicy(
      { ...policy, publication_enabled: true },
      installed,
    ).publicationReady,
    false,
    "flipping only the toolchain policy cannot fabricate unavailable versions",
  );
});

test("signed gates fail closed when verification identities are absent", () => {
  assert.throws(
    () =>
      parseGateArguments(
        ["--platform", "macos", "--arch", "arm64", "--mode", "signed"],
        { platform: "darwin", arch: "arm64" },
      ),
    /--identity and --team-id/,
  );
  assert.throws(
    () =>
      parseGateArguments(
        ["--platform", "windows", "--arch", "x64", "--mode", "signed"],
        { platform: "win32", arch: "x64" },
      ),
    /--expected-publisher/,
  );
  assert.throws(
    () =>
      parseGateArguments(
        [
          "--platform", "windows",
          "--arch", "x64",
          "--mode", "signed",
          "--expected-publisher", "CN=Microsoft Corporation",
        ],
        { platform: "win32", arch: "x64" },
      ),
    /--release-tag/,
  );
});

test("artifact names are deterministic and unsigned verification is obvious", () => {
  assert.equal(
    artifactName({
      platform: "macos",
      arch: "arm64",
      version: "1.2.3-beta.4",
      mode: "signed",
    }),
    "RAPP-Brainstem-Frontier-1.2.3-beta.4-macos-arm64.dmg",
  );
  assert.equal(
    artifactName({
      platform: "windows",
      arch: "x64",
      version: "1.2.3-beta.4",
      mode: "unsigned",
    }),
    "RAPP-Brainstem-Frontier-1.2.3-beta.4-windows-x64-setup-unsigned.exe",
  );
  assert.throws(
    () =>
      artifactName({
        platform: "windows",
        arch: "arm64",
        version: "1.2.3-beta.4",
        mode: "signed",
      }),
    /Unsupported Windows artifact architecture/,
  );
});

test("com.microsoft bundle IDs require a Microsoft signing identity", () => {
  assert.equal(
    publisherMatchesApplicationId(
      "com.microsoft.aibast.frontier",
      "Developer ID Application: Microsoft Corporation (TEAM123456)",
    ),
    true,
  );
  assert.equal(
    publisherMatchesApplicationId(
      "com.microsoft.aibast.frontier",
      "Developer ID Application: Example Corp (TEAM123456)",
    ),
    false,
  );
});

test("release manifest requires the complete three-binary matrix", () => {
  const version = "1.2.3-beta.4";
  const names = [
    artifactName({ platform: "macos", arch: "arm64", version, mode: "signed" }),
    artifactName({ platform: "macos", arch: "x64", version, mode: "signed" }),
    artifactName({ platform: "windows", arch: "x64", version, mode: "signed" }),
  ];
  const checksums = names.map((name, index) => ({
    name,
    sha256: String(index + 1).padStart(64, "0"),
    size: index + 100,
  }));
  const bundles = Object.fromEntries(
    names.map((name) => [
      name,
      {
        name: `${name}.sigstore.json`,
        size: 200,
      },
    ]),
  );
  const metadata = {
    tag: `brainstem-beta-v${version}`,
    version,
    repository: "owner/repository",
    serverUrl: "https://github.com",
    commit: "a".repeat(40),
    applicationId: "com.microsoft.aibast.rapp-brainstem-beta",
    electronVersion: "43.4.1",
    electronBuilderVersion: "26.15.7",
    macosIdentity:
      "Developer ID Application: Microsoft Corporation (TEAM123456)",
    appleTeamId: "TEAM123456",
    azureEndpoint: "https://eus.codesigning.azure.net",
    azureAccount: "frontier",
    azureProfile: "public-trust",
    windowsSubject: "CN=Microsoft Corporation",
    windowsSigningBackendSchema: "test-approved-artifact-signing/v1",
    windowsProfileType: "PublicTrust",
    windowsFileDigest: "SHA256",
    windowsTimestampDigest: "SHA256",
    windowsTimestampUrl: "http://timestamp.acs.microsoft.com/",
    gateRunUrl:
      "https://github.com/owner/repository/actions/runs/123456789",
    windowsPolicy: {
      schema:
        "https://github.com/microsoft/aibast-agents-library/frontier-windows-signing-policy/v1",
      publication_enabled: true,
      current_backend_schema: "test-approved-artifact-signing/v1",
      backend_approval: "approved",
      approved_backend_schema: "test-approved-artifact-signing/v1",
      protected_signer_validation: "approved",
      required_environment: "windows-production",
      required_profile_type: "PublicTrust",
      client_secret_allowed: false,
    },
    windowsExpected: {
      endpoint: "https://eus.codesigning.azure.net",
      account: "frontier",
      certificateProfile: "public-trust",
      publisherSubject: "CN=Microsoft Corporation",
      profileType: "PublicTrust",
    },
    windowsSbom: {
      name:
        `RAPP-Brainstem-Frontier-${version}-windows-x64-setup.exe.spdx.json`,
      size: 500,
      sha256: "c".repeat(64),
      spdx_version: "SPDX-2.3",
    },
    manifestName: `RAPP-Brainstem-Frontier-${version}-binary-manifest.json`,
  };
  const reports = Object.fromEntries(
    names.map((name, index) => {
      const windows = name.includes("-windows-");
      const arch = name.includes("-arm64.") ? "arm64" : "x64";
      const identity = windows
        ? metadata.windowsSubject
        : metadata.macosIdentity;
      return [
        name,
        {
          name: `${name}.gate.json`,
          size: 300,
          sha256: "e".repeat(64),
          content: {
            schema:
              "https://github.com/microsoft/aibast-agents-library/frontier-package-gate/v1",
            artifact: {
              name,
              sha256: checksums[index].sha256,
              size: checksums[index].size,
              os: windows ? "windows" : "macos",
              arch,
              signing_mode: "signed",
            },
            source: {
              application_id: metadata.applicationId,
            },
            runtime_compatibility: {
              operating_system: {
                name: windows ? "Windows" : "macOS",
                minimum_version: windows ? "11" : "12.0",
              },
              architecture: arch,
              electron: metadata.electronVersion,
              node_engine: ">=24.19.0 <26",
              native_dependencies: {
                ffmpeg_static: "5.3.0",
                ffprobe_installer: "2.1.2",
                copilot_sdk: "1.0.6",
              },
              brainstem: {
                python: "3.11",
                protocol: "RAPP/1",
                version: "0.3.0",
              },
              update_channel: "binary-release-manifest-v1",
              source_checkout_updater_compatible: false,
            },
            signing: {
              provider: windows
                ? "Azure Artifact Signing"
                : "Apple Developer ID",
              identity,
              verified: true,
              ...(windows
                ? {
                    backend_schema: metadata.windowsSigningBackendSchema,
                    endpoint: metadata.azureEndpoint,
                    account: metadata.azureAccount,
                    certificate_profile: metadata.azureProfile,
                    profile_type: metadata.windowsProfileType,
                    file_digest: metadata.windowsFileDigest,
                    timestamp_digest: metadata.windowsTimestampDigest,
                    timestamp_url: metadata.windowsTimestampUrl,
                  }
                : {}),
            },
            runtime: {
              service_ready: true,
              service_stopped: true,
              isolated_home: true,
              copilot_auth_startup: true,
              copilot_phase: "signed-out",
            },
            bootstrap: {
              executed: true,
              authority_mode: "canonical-release",
              installed_commit: "a".repeat(40),
              release_tag: metadata.tag,
              manifest: {
                schema: 1,
                product: "rapp-brainstem-frontier",
                mode: "release",
                commit: "a".repeat(40),
                repositoryUrl:
                  "https://github.com/microsoft/aibast-agents-library.git",
                sourceRef: metadata.tag,
                authority: {
                  canonical: true,
                  requestedMode: "release",
                  releaseTag: metadata.tag,
                },
                publication: {
                  ready: true,
                  blockers: [],
                },
              },
            },
            execution: {
              windows_standard_user: windows ? true : null,
              windows_lifecycle: windows
                ? {
                    passed: true,
                    per_user_registry_only: true,
                    machine_registry_entries: 0,
                    reinstall_single_entry: true,
                    installed_files_removed: true,
                    registry_and_shortcuts_removed: true,
                    shared_brainstem_preserved: true,
                    user_data_preserved: true,
                    source_migration_safe: true,
                  }
                : null,
              windows_upgrade: windows
                ? {
                    passed: true,
                    mode: "first-binary-release",
                    previous_release_tag: null,
                    previous_installer_sha256: null,
                  }
                : null,
            },
            publication: {
              status: "ready",
              blockers: [],
            },
            native_media: {
              publication_ready: true,
              components: ["ffmpeg", "ffprobe"].map((component) => ({
                component,
                sha256: "d".repeat(64),
                size: 1000,
                publication_ready: true,
                approved_provenance: {
                  source_url: `https://example.com/${component}`,
                  redistributable: true,
                  license: "LGPL-2.1-or-later",
                },
              })),
            },
            installation: {
              method: windows
                ? "nsis-silent-install"
                : "dmg-mount-and-ditto",
            },
            notarization: windows
              ? null
              : {
                  app: {
                    submission: { status: "Accepted" },
                    log: { status: "Accepted", issues: [] },
                    stapled: true,
                    target: {
                      code_signature: {
                        ad_hoc: false,
                        timestamp: "Sep 4, 2026",
                        team_id: metadata.appleTeamId,
                      },
                    },
                  },
                  dmg: {
                    submission: { status: "Accepted" },
                    log: { status: "Accepted", issues: [] },
                    stapled: true,
                    target: {
                      code_signature: {
                        ad_hoc: false,
                        timestamp: "Sep 4, 2026",
                      },
                    },
                  },
                },
            gate: {
              status: "passed",
              passed: 80,
              total: 80,
              failures: [],
            },
          },
        },
      ];
    }),
  );
  const manifest = createReleaseManifest(metadata, checksums, bundles, reports);
  assert.equal(RELEASE_MANIFEST_SCHEMA, DOWNLOAD_CENTER_MANIFEST_SCHEMA);
  assert.equal(manifest.schema, DOWNLOAD_CENTER_MANIFEST_SCHEMA);
  assert.equal(manifest.release.commit, metadata.commit);
  assert.equal(manifest.artifacts.length, 3);
  assert.equal(manifest.publication_policy.allow_unlisted_binary_assets, false);
  assert.equal(manifest.publication_policy.require_signed_manifest, true);
  assert.equal(manifest.publication_policy.windows_arm64_allowed, false);
  assert.ok(manifest.artifacts.every((asset) => asset.gate.status === "passed"));
  assert.ok(manifest.artifacts.every((asset) => asset.gate.commit === metadata.commit));
  assert.ok(manifest.artifacts.every((asset) => asset.gate.run_url === metadata.gateRunUrl));
  assert.ok(
    manifest.artifacts.every((asset) => asset.native_media.publication_ready),
  );
  assert.equal(
    manifest.artifacts.find((asset) => asset.platform === "windows").sbom.spdx_version,
    "SPDX-2.3",
  );
  assert.equal(manifest.signing.windows.profile_type, "PublicTrust");
  assert.equal(
    manifest.signing.windows.timestamp,
    "http://timestamp.acs.microsoft.com/",
  );
  assert.ok(
    manifest.artifacts.every(
      (asset) =>
        asset.runtime.details.source_checkout_updater_compatible === false,
    ),
  );
  assert.ok(manifest.artifacts.every((asset) => asset.download_url.startsWith(
    "https://github.com/owner/repository/releases/download/brainstem-beta-v",
  )));
  assert.ok(manifest.artifacts.every((asset) => asset.signing.status === "verified"));
  assert.ok(manifest.artifacts.every((asset) => asset.runtime.compatible === true));
  const fenced = upsertReleaseManifestFence("Release notes\n", manifest);
  assert.deepEqual(parseReleaseManifest(fenced), manifest);
  assert.equal(
    fenced.match(/^```rapp-frontier-release-manifest$/gm)?.length,
    1,
  );
  assert.equal(
    upsertReleaseManifestFence(fenced, manifest)
      .match(/^```rapp-frontier-release-manifest$/gm)?.length,
    1,
  );
  assert.equal(manifest.source_fallback.commit, metadata.commit);
  assert.equal(manifest.source_fallback.resolves_latest, false);
  assert.match(manifest.source_fallback.macos_linux.command, new RegExp(metadata.commit));
  assert.doesNotMatch(manifest.source_fallback.macos_linux.command, /latest/i);
  assert.match(manifest.source_fallback.windows.command, new RegExp(metadata.commit));
  assert.doesNotMatch(manifest.source_fallback.windows.command, /latest/i);
  assert.throws(
    () =>
      createReleaseManifest(
        metadata,
        checksums.slice(1),
        bundles,
        reports,
      ),
    /required matrix/,
  );
  const unsafeReports = structuredClone(reports);
  unsafeReports[names[0]].content.runtime.service_ready = false;
  assert.throws(
    () => createReleaseManifest(metadata, checksums, bundles, unsafeReports),
    /service readiness/,
  );
  const nonfreeReports = structuredClone(reports);
  nonfreeReports[names[0]].content.publication.status = "blocked";
  nonfreeReports[names[0]].content.publication.blockers = ["--enable-nonfree"];
  nonfreeReports[names[0]].content.native_media.publication_ready = false;
  assert.throws(
    () => createReleaseManifest(metadata, checksums, bundles, nonfreeReports),
    /not approved for redistribution/,
  );
  const mismatchedBootstrapReports = structuredClone(reports);
  mismatchedBootstrapReports[names[0]].content.bootstrap.manifest.commit =
    "b".repeat(40);
  assert.throws(
    () => createReleaseManifest(
      metadata,
      checksums,
      bundles,
      mismatchedBootstrapReports,
    ),
    /bootstrap is not bound to the release commit/,
  );
  const warningReports = structuredClone(reports);
  warningReports[names[0]].content.notarization.dmg.log.issues = [{
    severity: "warning",
    message: "unknown warning",
  }];
  assert.throws(
    () => createReleaseManifest(
      metadata,
      checksums,
      bundles,
      warningReports,
    ),
    /notarization evidence/,
  );
  const machineInstallReports = structuredClone(reports);
  machineInstallReports[names[2]].content.execution.windows_lifecycle
    .machine_registry_entries = 1;
  assert.throws(
    () => createReleaseManifest(
      metadata,
      checksums,
      bundles,
      machineInstallReports,
    ),
    /lifecycle and upgrade gates/,
  );
  const missingUpgradeReports = structuredClone(reports);
  missingUpgradeReports[names[2]].content.execution.windows_upgrade.passed =
    false;
  assert.throws(
    () => createReleaseManifest(
      metadata,
      checksums,
      bundles,
      missingUpgradeReports,
    ),
    /lifecycle and upgrade gates/,
  );
  const unsignedDmgReports = structuredClone(reports);
  unsignedDmgReports[names[0]].content.notarization.dmg.target
    .code_signature.ad_hoc = true;
  assert.throws(
    () => createReleaseManifest(
      metadata,
      checksums,
      bundles,
      unsignedDmgReports,
    ),
    /notarization evidence/,
  );
  assert.throws(
    () => upsertReleaseManifestFence("", {
      ...manifest,
      schema: "mutated-schema",
    }),
    /Manifest schema/,
  );
  assert.throws(
    () => createReleaseManifest(
      {
        ...metadata,
        gateRunUrl: "https://github.com/attacker/repository/actions/runs/123",
      },
      checksums,
      bundles,
      reports,
    ),
    /GitHub Actions run URL/,
  );
  const blockedWindowsPolicy = JSON.parse(
    readFileSync(
      path.join(betaDir, "build", "windows-signing-policy.json"),
      "utf8",
    ),
  );
  assert.throws(
    () => createReleaseManifest(
      {
        ...metadata,
        windowsPolicy: blockedWindowsPolicy,
        windowsSigningBackendSchema:
          blockedWindowsPolicy.current_backend_schema,
      },
      checksums,
      bundles,
      reports,
    ),
    /Windows signing policy is blocked/,
  );
  const mismatchedSigningReports = structuredClone(reports);
  mismatchedSigningReports[names[2]].content.signing.endpoint =
    "https://other.codesigning.azure.net";
  assert.throws(
    () => createReleaseManifest(
      metadata,
      checksums,
      bundles,
      mismatchedSigningReports,
    ),
    /independently protected policy/,
  );
  assert.throws(
    () =>
      createReleaseManifest(
        metadata,
        [{ ...checksums[0], size: 0 }, ...checksums.slice(1)],
        bundles,
        reports,
      ),
    /positive byte size/,
  );
  assert.throws(
    () =>
      createReleaseManifest(
        {
          ...metadata,
          windowsSbom: { ...metadata.windowsSbom, size: 0 },
        },
        checksums,
        bundles,
        reports,
      ),
    /Windows SPDX-2.3 SBOM/,
  );
  assert.throws(
    () =>
      createReleaseManifest(
        { ...metadata, commit: "abc" },
        checksums,
        bundles,
        reports,
      ),
    /40-character commit/,
  );
  assert.throws(
    () =>
      createReleaseManifest(
        { ...metadata, tag: "brainstem-beta-v9.9.9-beta.9" },
        checksums,
        bundles,
        reports,
      ),
    /tag does not match version/,
  );
  assert.throws(
    () =>
      createReleaseManifest(
        {
          ...metadata,
          macosIdentity:
            "Developer ID Application: Example Corp (TEAM123456)",
        },
        checksums,
        bundles,
        reports,
      ),
    /publisher identities do not match/,
  );
  assert.throws(
    () =>
      createReleaseManifest(
        { ...metadata, serverUrl: "" },
        checksums,
        bundles,
        reports,
      ),
    /Invalid URL/,
  );
  const unknown = {
    ...checksums[2],
    name: `Uninstall-RAPP-Brainstem-Frontier-${version}.exe`,
  };
  assert.throws(
    () =>
      createReleaseManifest(
        metadata,
        [checksums[0], checksums[1], unknown],
        bundles,
        reports,
      ),
    /required matrix/,
  );
  assert.equal(
    JSON.stringify(createReleaseManifest(metadata, checksums, bundles, reports)),
    JSON.stringify(createReleaseManifest(metadata, checksums, bundles, reports)),
  );
});

test("checksum parser rejects paths and malformed digests", () => {
  assert.deepEqual(parseChecksums(`${"a".repeat(64)}  app.exe\n`), [
    { name: "app.exe", sha256: "a".repeat(64) },
  ]);
  assert.throws(
    () => parseChecksums(`${"a".repeat(64)}  dist/app.exe\n`),
    /basenames/,
  );
  assert.throws(() => parseChecksums("not-a-checksum\n"), /Invalid SHA256SUMS/);
  assert.throws(
    () =>
      parseChecksums(
        `${"a".repeat(64)}  app.exe\n${"b".repeat(64)}  app.exe\n`,
      ),
    /duplicate filenames/,
  );
});

test("packaged builds declare and enforce the binary update channel", () => {
  const packageMetadata = JSON.parse(
    readFileSync(path.join(betaDir, "package.json"), "utf8"),
  );
  assert.equal(
    packageMetadata.build.extraMetadata.frontierDistributionChannel,
    "binary-release-manifest-v1",
  );
  assert.equal(
    packageMetadata.build.extraMetadata.frontierSourceCheckoutUpdaterCompatible,
    false,
  );
  assert.equal(
    packageMetadata.build.extraResources[0].to,
    "bootstrap",
  );
  assert.equal(packageMetadata.devDependencies.electron, "43.4.1");
  assert.equal(packageMetadata.devDependencies["electron-builder"], "26.15.7");
  assert.equal(packageMetadata.build.mac.minimumSystemVersion, "12.0");
  const main = readFileSync(path.join(betaDir, "electron", "main.mjs"), "utf8");
  assert.match(main, /update:\s*app\.isPackaged/);
  assert.match(main, /packagedUpdateState\(\)/);
  assert.match(main, /if \(app\.isPackaged\)/);
});

test("macOS release signing is forced and notarization evidence is inspected", () => {
  const notarization = readFileSync(
    path.join(betaDir, "scripts", "notarize-target.mjs"),
    "utf8",
  );
  const entitlements = readFileSync(
    path.join(betaDir, "build", "entitlements.mac.plist"),
    "utf8",
  );
  const bootstrap = {
    applicationId: "com.microsoft.aibast.rapp-brainstem-beta",
    productName: "RAPP Brainstem Frontier",
  };
  const packageMetadata = {
    build: { appId: bootstrap.applicationId },
  };
  const signed = createBuilderConfiguration({
    platform: "macos",
    mode: "signed",
    bootstrap,
    packageMetadata,
    macSigning: {
      identity: "Developer ID Application: Microsoft Corporation (TEAM123456)",
      notarize: false,
    },
  });
  const unsigned = createBuilderConfiguration({
    platform: "macos",
    mode: "unsigned",
    bootstrap,
    packageMetadata,
    macSigning: { identity: null, notarize: false },
  });
  assert.equal(signed.forceCodeSigning, true);
  assert.equal(signed.dmg.sign, true);
  assert.match(signed.afterSign, /notarize-target\.mjs$/);
  assert.equal(unsigned.forceCodeSigning, false);
  assert.equal(unsigned.dmg.sign, false);
  assert.equal(unsigned.afterSign, undefined);
  assert.match(notarization, /notarytool",\s*"log"/);
  assert.match(notarization, /stapler",\s*"staple"/);
  assert.match(notarization, /Signature=adhoc/);
  assert.match(entitlements, /com\.apple\.security\.cs\.allow-jit/);
  assert.doesNotMatch(
    entitlements,
    /allow-unsigned-executable-memory|disable-library-validation/,
  );
  const digest = "a".repeat(64);
  assert.deepEqual(
    validateNotarizationLog({
      status: "Accepted",
      sha256: digest,
      issues: [],
    }, digest),
    { issues: [] },
  );
  for (const severity of ["warning", "info", "unknown"]) {
    assert.throws(
      () => validateNotarizationLog({
        status: "Accepted",
        sha256: digest,
        issues: [{ severity, message: "review required" }],
      }, digest),
      /issue-free/,
    );
  }


});

test("blocked native media permits report-only unsigned uploads", () => {
  const evidence = [
    "release/app.dmg.gate.json",
    "release/app.dmg.gate.log",
    "release/UNSIGNED-NOT-FOR-DISTRIBUTION.txt",
  ];
  assert.equal(
    assertUnsignedUploadPolicy({
      publicationReady: false,
      paths: evidence,
      requireFiles: false,
    }),
    true,
  );
  for (const artifact of ["release/app.dmg", "release/setup.exe"]) {
    assert.throws(
      () => assertUnsignedUploadPolicy({
        publicationReady: false,
        paths: [...evidence, artifact],
        requireFiles: false,
      }),
      /reports only/,
    );
  }
  const workflow = loadWorkflowContract();
  if (workflow === null) {
    return;
  }
  for (const jobName of ["verify-macos", "verify-windows"]) {
    const job = workflowJob(workflow, jobName);
    const upload = job.slice(job.indexOf("uses: actions/upload-artifact@"));
    assert.match(job, /unsigned-upload-gate\.mjs/);
    assert.match(upload, /UNSIGNED-REPORTS-/);
    assert.doesNotMatch(upload, /^\s+beta\/release\/.*-unsigned\.(?:dmg|exe)$/m);
    assert.match(upload, /\.gate\.json/);
    assert.match(upload, /\.gate\.log/);
  }
});

test("Windows NSIS identity and production signing policy are frozen", async () => {
  const packageMetadata = JSON.parse(
    readFileSync(path.join(betaDir, "package.json"), "utf8"),
  );
  const policy = loadWindowsSigningPolicy();
  const packaging = readFileSync(
    path.join(betaDir, "scripts", "package-platform.mjs"),
    "utf8",
  );
  const main = readFileSync(path.join(betaDir, "electron", "main.mjs"), "utf8");
  const standardUserGate = readFileSync(
    path.join(
      betaDir,
      "scripts",
      "run-windows-package-gate-standard-user.ps1",
    ),
    "utf8",
  );
  const isolatedSigner = readFileSync(
    path.join(
      betaDir,
      "scripts",
      "sign-validated-windows-input.mjs",
    ),
    "utf8",
  );
  const signingHook = readFileSync(
    path.join(betaDir, "scripts", "artifact-signing-hook.cjs"),
    "utf8",
  );
  assert.equal(
    packageMetadata.build.appId,
    "com.microsoft.aibast.rapp-brainstem-beta",
  );
  assert.equal(
    packageMetadata.build.nsis.guid,
    "48d3a204-a20a-516d-b74f-5ac374e1c8bb",
  );
  assert.equal(packageMetadata.build.nsis.oneClick, true);
  assert.equal(packageMetadata.build.nsis.perMachine, false);
  assert.equal(
    packageMetadata.build.nsis.allowToChangeInstallationDirectory,
    false,
  );
  assert.equal(packageMetadata.build.nsis.runAfterFinish, false);
  assert.equal(packageMetadata.build.nsis.deleteAppDataOnUninstall, false);
  assert.equal(packageMetadata.build.nsis.warningsAsErrors, true);
  assert.equal(packageMetadata.build.win.requestedExecutionLevel, "asInvoker");
  assert.equal(policy.publication_enabled, false);
  assert.equal(policy.backend_approval, "approved");
  assert.equal(
    policy.approved_backend_schema,
    "electron-builder-26.15.7/custom-ArtifactSigning-0.1.8/v1",
  );
  assert.equal(
    policy.protected_signer_validation,
    "pending-native-windows-evidence",
  );
  assert.equal(policy.required_environment, "windows-production");
  assert.equal(policy.required_profile_type, "PublicTrust");
  assert.equal(policy.client_secret_allowed, false);
  const booleanOnlyMutation = {
    ...policy,
    publication_enabled: true,
  };
  assert.equal(
    evaluateWindowsSigningPolicy(booleanOnlyMutation).publicationReady,
    false,
    "flipping only the Windows publication boolean must not approve an unvalidated signer",
  );
  assert.throws(
    () => validateWindowsSigningEvidence({
      backend_schema: policy.current_backend_schema,
    }, policy, {
      endpoint: "https://eus.codesigning.azure.net",
      account: "frontier",
      certificateProfile: "public-trust",
      publisherSubject: "CN=Microsoft Corporation",
      profileType: "PublicTrust",
    }),
    /policy is blocked/,
  );
  assert.match(packaging, /entry\.endsWith\("\.blockmap"\)/);
  assert.match(packaging, /\^latest/);
  assert.match(packaging, /installers\.length !== 1/);
  assert.match(main, /app\.setAppUserModelId\(APP_ID\)/);
  assert.match(standardUserGate, /New-LocalUser/);
  assert.match(standardUserGate, /Add-LocalGroupMember/);
  assert.match(standardUserGate, /Start-Process[\s\S]*-Credential/);
  assert.match(standardUserGate, /Remove-LocalUser/);
  assert.match(isolatedSigner, /prepackaged: prepackagedApp/);
  assert.match(isolatedSigner, /npmRebuild: false/);
  assert.match(isolatedSigner, /collectSignableFiles/);
  assert.match(signingHook, /Invoke-ArtifactSigning/);
  assert.match(signingHook, /Import-Module ArtifactSigning/);
  assert.doesNotMatch(signingHook, /Install-Module|Save-Module/);
  const validBuilderConfig = createValidatedWindowsBuilderConfiguration({
    packageMetadata,
    hookPath: path.join(betaDir, "scripts", "artifact-signing-hook.cjs"),
    publisher: "CN=Microsoft Corporation",
    outputDirectory: path.join(betaDir, "release", "schema-test"),
  });
  const debugLogger = { isEnabled: false, add() {} };
  await validateConfiguration(validBuilderConfig, debugLogger);
  assert.equal(
    validBuilderConfig.win.signtoolOptions.signingHashAlgorithms[0],
    "sha256",
  );
  assert.equal(validBuilderConfig.win.sign, undefined);
  const invalidDirectShape = structuredClone(validBuilderConfig);
  Object.assign(
    invalidDirectShape.win,
    invalidDirectShape.win.signtoolOptions,
  );
  delete invalidDirectShape.win.signtoolOptions;
  await assert.rejects(
    () => validateConfiguration(invalidDirectShape, debugLogger),
    /unknown property 'sign'|invalid configuration/i,
  );
  const stagedVerifier = readFileSync(
    path.join(betaDir, "scripts", "verify-staged-release.mjs"),
    "utf8",
  );
  assert.match(stagedVerifier, /loadWindowsSigningPolicy/);
  assert.match(stagedVerifier, /validateWindowsSigningEvidence/);
  const workflow = loadWorkflowContract();
  if (workflow === null) {
    return;
  }
  const stage = workflowJob(workflow, "stage-release");
  for (const name of [
    "WINDOWS_SIGNING_SUBJECT",
    "AZURE_ARTIFACT_SIGNING_ENDPOINT",
    "AZURE_ARTIFACT_SIGNING_ACCOUNT_NAME",
    "AZURE_ARTIFACT_SIGNING_CERTIFICATE_PROFILE_NAME",
    "AZURE_ARTIFACT_SIGNING_PROFILE_TYPE",
  ]) {
    assert.ok(
      stage.includes(`${name}: $` + `{{ vars.${name} }}`),
      `${name} must come from the protected staging environment`,
    );
  }
});

test("workflow contract pins actions and never creates or moves a release tag", () => {
  const workflow = loadWorkflowContract();
  if (workflow === null) {
    return;
  }
  const actions = [
    ...workflow.matchAll(/^\s*-\s+uses:\s*([^#\n]+)(?:#.*)?$/gm),
  ];
  assert.ok(actions.length >= 10, "workflow action scan did not find the expected steps");
  for (const match of actions) {
    assert.match(match[1].trim(), /@[0-9a-f]{40}$/, `unpinned action: ${match[1]}`);
  }
  assert.doesNotMatch(workflow, /\bgh release create\b/);
  assert.doesNotMatch(workflow, /\bgit (?:tag|push)\b/);
  assert.doesNotMatch(workflow, /--clobber/);
  assert.equal(workflow.match(/contents:\s+write/g)?.length, 2);
  assert.equal(workflow.match(/id-token:\s+write/g)?.length, 2);
  assert.doesNotMatch(workflow, /^\s+push:/m);
  assert.match(workflow, /publish_release:[\s\S]*default:\s+false/);
  assert.match(workflow, /\.immutable \/\/ false/);
  assert.doesNotMatch(workflow, /--draft=true/);
  assert.match(workflow, /Artifact Signing Certificate[\s\S]*Profile Signer/);
  assert.match(workflow, /macos-26-intel/);
  assert.match(workflow, /macos-26/);
  assert.match(workflow, /windows-2025/);
  assert.match(workflow, /binary-manifest\.json/);
  assert.match(workflow, /\.gate\.json/);
  assert.match(workflow, /fence-release-manifest\.mjs/);
  assert.match(workflow, /verify-staged-release\.mjs/);
  assert.match(workflow, /FRONTIER_GATE_RUN_URL/);
  assert.match(workflow, /test -s "\$asset"/);
  assert.match(workflow, /native-media-gate\.mjs/);
  assert.match(workflow, /windows-signing-policy\.json/);
  assert.match(workflow, /package-bootstrap-policy\.json/);
  assert.match(workflow, /microsoft\/aibast-agents-library/);
  assert.match(workflow, /run-windows-package-gate-standard-user\.ps1/);
  assert.match(workflow, /--release-tag/);
  assert.match(workflow, /environment:\s+windows-production/);
  assert.match(workflow, /verify \/pa \/all \/v \/tw/);
  assert.doesNotMatch(workflow, /AZURE_CLIENT_SECRET/);
  assert.doesNotMatch(workflow, /runner:\s*windows[^\n]*arm/i);
  assert.doesNotMatch(workflow, /RAPP-[^\n]*windows-arm64/i);
});

test("signing credentials are exposed only after dependency and media gates", () => {
  const workflow = loadWorkflowContract();
  if (workflow === null) {
    return;
  }
  const mac = workflowJob(workflow, "release-macos");
  const macInstall = mac.indexOf("npm ci --no-audit --no-fund");
  const macTests = mac.indexOf("npm test");
  const macMedia = mac.indexOf("native-media-preflight.mjs");
  const macClean = mac.indexOf("git diff --exit-code");
  const macAuthority = mac.indexOf("Materialize isolated Apple signing authority");
  const macBuild = mac.indexOf("Build, Developer ID sign, and notarize native DMG");
  const macCleanup = mac.indexOf("Remove Apple signing authority immediately");
  const macGate = mac.indexOf("Gate signed and notarized DMG");
  assert.ok(
    0 <= macInstall
      && macInstall < macTests
      && macTests < macMedia
      && macMedia < macClean
      && macClean < macAuthority
      && macAuthority < macBuild
      && macBuild < macCleanup
      && macCleanup < macGate,
  );
  assert.doesNotMatch(
    mac.slice(0, macAuthority),
    /MACOS_CERTIFICATE_P12_BASE64|APPLE_API_KEY_P8_BASE64|CSC_LINK|CSC_KEYCHAIN/,
  );
  assert.equal(mac.lastIndexOf("npm ci --no-audit --no-fund"), macInstall);
  assert.match(mac, /test -z "\$\{CSC_LINK:-\}"/);
  assert.match(mac, /security delete-keychain/);

  const preparation = workflowJob(workflow, "prepare-windows-release");
  assert.match(preparation, /actions\/checkout@/);
  assert.match(preparation, /npm ci --no-audit --no-fund/);
  assert.match(preparation, /npm test/);
  assert.match(preparation, /native-media-preflight\.mjs/);
  assert.match(preparation, /windows-signing-input\.mjs/);
  assert.match(preparation, /Save-Module -Name ArtifactSigning/);
  assert.doesNotMatch(preparation, /id-token:\s+write/);
  assert.doesNotMatch(preparation, /environment:\s+windows-production/);

  const signer = workflowJob(workflow, "release-windows");
  const inputVerify = signer.indexOf(
    "Verify immutable signing input before OIDC use",
  );
  const outerDigest = signer.indexOf("Get-FileHash");
  const innerManifest = signer.indexOf("--mode verify");
  const azureLogin = signer.indexOf("azure/login@");
  const winBuild = signer.indexOf(
    "Sign validated app, uninstaller, and NSIS package",
  );
  const azureCleanup = signer.indexOf(
    "Clear Azure CLI session immediately after signing",
  );
  const seal = signer.indexOf("Seal signed workspace after OIDC cleanup");
  assert.ok(
    0 <= inputVerify
      && inputVerify < outerDigest
      && outerDigest < innerManifest
      && innerManifest < azureLogin
      && azureLogin < winBuild
      && winBuild < azureCleanup
      && azureCleanup < seal,
  );
  assert.match(signer, /environment: windows-production/);
  assert.match(signer, /id-token:\s+write/);
  assert.doesNotMatch(signer, /actions\/checkout@|actions\/setup-node@/);
  assert.doesNotMatch(
    signer,
    /\bnpm(?:\.cmd)?\s+(?:ci|install|test)|\bpip\s+install|Install-Module|Install-PackageProvider|Save-Module/,
  );
  assert.match(signer, /windows-signing-input\.mjs[\s\S]*--mode verify/);
  assert.match(signer, /az account clear/);

  const verification = workflowJob(workflow, "verify-windows-release");
  assert.doesNotMatch(verification, /id-token:\s+write/);
  assert.match(verification, /run-windows-package-gate-standard-user\.ps1/);
  assert.match(verification, /frontier-verified-windows-x64/);

  const jobNames = [
    ...workflow.matchAll(/^\s{2}([a-z0-9-]+):\s*$/gm),
  ].map((match) => match[1]);
  const idTokenJobs = jobNames.filter((name) =>
    /id-token:\s+write/.test(workflowJob(workflow, name)),
  );
  assert.ok(idTokenJobs.length >= 2);
  for (const name of idTokenJobs) {
    assert.doesNotMatch(
      workflowJob(workflow, name),
      /\bnpm(?:\.cmd)?\s+(?:ci|install|test)|\bpip\s+install|Install-Module|Install-PackageProvider|Save-Module/,
      `${name} must not run dependency-install or general-test lifecycles`,
    );
  }
});

test("Windows signing input hash manifest detects any post-validation mutation", () => {
  const root = path.join(
    betaDir,
    "release",
    `signing-input-test-${process.pid}-${Date.now()}`,
  );
  const commit = "a".repeat(40);
  try {
    mkdirSync(path.join(root, "beta"), { recursive: true });
    writeFileSync(
      path.join(root, "beta", "package.json"),
      JSON.stringify({
        version: "1.2.3-beta.4",
        engines: { node: ">=24.19.0 <26" },
        build: {
          appId: "com.microsoft.aibast.rapp-brainstem-beta",
          productName: "RAPP Brainstem Frontier",
        },
      }),
    );
    writeFileSync(
      path.join(root, "beta", "package-lock.json"),
      JSON.stringify({
        packages: {
          "node_modules/electron": { version: "43.4.1" },
          "node_modules/electron-builder": { version: "26.15.7" },
        },
      }),
    );
    writeFileSync(path.join(root, "payload.exe"), "validated bytes");
    createWindowsSigningInput(root, commit);
    assert.equal(verifyWindowsSigningInput(root, commit).commit, commit);
    writeFileSync(path.join(root, "payload.exe"), "mutated bytes");
    assert.throws(
      () => verifyWindowsSigningInput(root, commit),
      /do not match the validated manifest/,
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("publication revalidates the full set and immutable setting at the last gate", () => {
  const workflow = loadWorkflowContract();
  if (workflow === null) {
    return;
  }
  const publish = workflowJob(workflow, "publish");
  const download = publish.indexOf("--dir publish-verification");
  const count = publish.indexOf("= 13");
  const checksums = publish.indexOf("sha256sum -c SHA256SUMS");
  const attestations = publish.indexOf("gh attestation verify");
  const staged = publish.indexOf("verify-staged-release.mjs");
  const immutableSetting = publish.indexOf(
    'repos/$GITHUB_REPOSITORY/immutable-releases',
  );
  const immutableJson = publish.indexOf(
    "jq -e '.enabled == true'",
  );
  const immutablePolicy = publish.indexOf(
    "immutable-release-policy.mjs",
  );
  const traps = publish.indexOf("trap report_transition_error ERR");
  const stateMachine = publish.indexOf("publish-release-state-machine.mjs");
  assert.ok(
    0 <= download
      && download < count
      && count < checksums
      && checksums < attestations
      && attestations < staged
      && staged < immutableSetting
      && immutableSetting < immutableJson
      && immutableJson < immutablePolicy
      && immutablePolicy < traps
      && traps < stateMachine,
  );
  assert.match(publish, /RAPP-Brainstem-Frontier-\$\{VERSION\}-macos-arm64\.dmg/);
  assert.match(publish, /RAPP-Brainstem-Frontier-\$\{VERSION\}-macos-x64\.dmg/);
  assert.match(publish, /RAPP-Brainstem-Frontier-\$\{VERSION\}-windows-x64-setup\.exe/);
  assert.doesNotMatch(publish, /--draft=true/);
  assert.doesNotMatch(publish, /gh release edit/);
  assert.match(publish, /IMMUTABLE RELEASE INCIDENT/);
  assert.match(publish, /trap report_transition_exit EXIT/);
  const transitionSource = readFileSync(
    path.join(
      betaDir,
      "scripts",
      "publish-release-state-machine.mjs",
    ),
    "utf8",
  );
  assert.doesNotMatch(transitionSource, /draft=true|rollbackRelease|ROLLED_BACK/);
  assert.match(transitionSource, /publish-intent-recorded/);
  assert.match(transitionSource, /terminal-immutable/);
  assert.match(transitionSource, /startGhPublishOperation/);
  assert.match(transitionSource, /new AbortController\(\)/);
  assert.match(transitionSource, /startAbortableExecFile/);
  assert.doesNotMatch(transitionSource, /Promise\.race|DEFAULT_OPERATION_TIMEOUT/);
});

test("immutable release settings require enabled true at runtime", () => {
  assert.equal(assertImmutableReleasesEnabled({ enabled: true }), true);
  for (const settings of [
    { enabled: false },
    {},
    null,
    [],
    { enabled: "true" },
  ]) {
    assert.throws(
      () => assertImmutableReleasesEnabled(settings),
      /enabled=true/,
    );
  }
});

test("annotated tag object, peeled commit, and release ID are race-bound", () => {
  const release = {
    id: 12345,
    tag_name: "brainstem-beta-v1.2.3",
    body: "exact release body\n",
    assets: [{
      id: 2,
      name: "b.exe",
      state: "uploaded",
      size: 20,
      digest: `sha256:${"b".repeat(64)}`,
    }, {
      id: 1,
      name: "a.dmg",
      state: "uploaded",
      size: 10,
      digest: `sha256:${"a".repeat(64)}`,
    }],
  };
  const releaseFingerprint = releaseContentFingerprint(release);
  const snapshot = {
    tag: release.tag_name,
    tagObject: "a".repeat(40),
    commit: "b".repeat(40),
    releaseId: String(release.id),
    releaseFingerprint,
  };
  assert.deepEqual(verifyReleaseSnapshot(snapshot, snapshot), snapshot);
  for (const [field, value] of [
    ["tag", "brainstem-beta-v1.2.4"],
    ["tagObject", "c".repeat(40)],
    ["commit", "d".repeat(40)],
    ["releaseId", "54321"],
    ["releaseFingerprint", "e".repeat(64)],
  ]) {
    assert.throws(
      () => verifyReleaseSnapshot(snapshot, {
        ...snapshot,
        [field]: value,
      }),
      new RegExp(`${field} changed`),
    );
  }
  assert.equal(
    releaseContentFingerprint({
      ...release,
      assets: [...release.assets].reverse(),
    }),
    releaseFingerprint,
    "release asset ordering must not change the canonical fingerprint",
  );
  const contentMutations = [
    { ...release, body: `${release.body}changed` },
    {
      ...release,
      assets: release.assets.map((asset, index) =>
        index ? asset : { ...asset, id: 99 }),
    },
    {
      ...release,
      assets: release.assets.map((asset, index) =>
        index ? asset : { ...asset, name: "changed.exe" }),
    },
    {
      ...release,
      assets: release.assets.map((asset, index) =>
        index ? asset : { ...asset, state: "new" }),
    },
    {
      ...release,
      assets: release.assets.map((asset, index) =>
        index ? asset : { ...asset, size: asset.size + 1 }),
    },
    {
      ...release,
      assets: release.assets.map((asset, index) =>
        index ? asset : { ...asset, digest: `sha256:${"f".repeat(64)}` }),
    },
  ];
  for (const mutatedRelease of contentMutations) {
    assert.throws(
      () => verifyReleaseSnapshot(snapshot, {
        ...snapshot,
        releaseFingerprint: releaseContentFingerprint(mutatedRelease),
      }),
      /releaseFingerprint changed/,
    );
  }

  const workflow = loadWorkflowContract();
  if (workflow === null) {
    return;
  }
  const context = workflowJob(workflow, "context");
  assert.match(context, /tag_object:/);
  assert.match(context, /--fingerprint-file/);
  assert.match(context, /refs\/tags\/\$tag\^\{\}/);
  assert.match(context, /release-race-guard\.mjs/);
  const publish = workflowJob(workflow, "publish");
  assert.match(publish, /TAG_OBJECT: \$\{\{ needs\.context\.outputs\.tag_object \}\}/);
  assert.match(
    publish,
    /RELEASE_FINGERPRINT: \$\{\{ needs\.stage-release\.outputs\.release_fingerprint \}\}/,
  );
  const stateMachineSource = readFileSync(
    path.join(betaDir, "scripts", "publish-release-state-machine.mjs"),
    "utf8",
  );
  assert.match(stateMachineSource, /verifyReleaseSnapshot/);
  assert.match(stateMachineSource, /releaseContentFingerprint/);
  assert.match(
    publish,
    /repos\/\$GITHUB_REPOSITORY\/releases\/\$RELEASE_ID/,
  );
});

test("monotonic publication reconciles only to exact immutable success", async () => {
  const draft = { id: 1, draft: true, immutable: false };
  const mutable = { id: 1, draft: false, immutable: false };
  const immutable = { id: 1, draft: false, immutable: true };
  const intentIdentity = {
    repository: "microsoft/aibast-agents-library",
    releaseId: "1",
    tag: "brainstem-beta-v1.2.3",
    tagObject: "a".repeat(40),
    commit: "b".repeat(40),
    releaseFingerprint: "c".repeat(64),
  };
  let current = { ...draft };
  let publishCalls = 0;
  const result = await runReleaseTransition({
    getRelease: async () => ({ ...current }),
    startPublishRelease: () => {
      publishCalls += 1;
      current = { ...mutable };
      return {
        response: Promise.resolve({ ...current }),
        settled: Promise.resolve(),
        cancel: async () => {},
      };
    },
    verifySnapshot: async () => true,
    pollDelayMs: 0,
    sleep: async () => { current = { ...immutable }; },
    intentIdentity,
  });
  assert.equal(result.status, "immutable");
  assert.equal(result.release.immutable, true);
  assert.equal(result.state.publishIntent, true);
  assert.equal(result.state.automaticRecoveryAllowed, true);
  assert.deepEqual(result.state.intentIdentity, intentIdentity);
  assert.equal(publishCalls, 1);
  assert.doesNotMatch(
    JSON.stringify(result.state.history),
    /rollback|terminal-draft|NOT_PUBLISHED|ROLLED_BACK/,
  );
});

test("exact public snapshot durably authorizes monotonic reconciliation", async () => {
  const draft = { id: 1, draft: true, immutable: false };
  const mutable = { id: 1, draft: false, immutable: false };
  const immutable = { id: 1, draft: false, immutable: true };
  let reads = 0;
  let current = { ...draft };
  const persisted = [];
  const result = await runReleaseTransition({
    getRelease: async () => {
      reads += 1;
      if (reads === 2) current = { ...mutable };
      return { ...current };
    },
    startPublishRelease: () => {
      throw new Error("verified public snapshot should be polled, not republished");
    },
    verifySnapshot: async () => true,
    onState: (state) => {
      persisted.push(structuredClone(state));
      return { ok: true };
    },
    pollDelayMs: 0,
    sleep: async () => { current = { ...immutable }; },
  });
  assert.equal(result.status, "immutable");
  assert.equal(result.state.automaticRecoveryAllowed, true);
  assert.ok(persisted.some((state) =>
    state.phase.endsWith("-automatic-recovery-authorized")
    && state.automaticRecoveryAllowed === true));
});

test("a public-mutable release cannot be adopted before durable intent", async () => {
  let publishCalled = false;
  await assert.rejects(
    () => runReleaseTransition({
      getRelease: async () => ({
        id: 1,
        draft: false,
        immutable: false,
      }),
      startPublishRelease: () => {
        publishCalled = true;
        throw new Error("pre-existing transition must not be adopted");
      },
      verifySnapshot: async () => true,
    }),
    (error) => {
      assert.equal(error.code, "INTEGRITY_INCIDENT");
      assert.equal(error.state.publishIntent, false);
      return true;
    },
  );
  assert.equal(publishCalled, false);
});

test("ambiguous publication before a safe marker requires manual recovery", async () => {
  const draft = { id: 1, draft: true, immutable: false };
  let durableState;
  let cancelCalled = false;
  await assert.rejects(
    () => runReleaseTransition({
      getRelease: async () => ({ ...draft }),
      startPublishRelease: () => ({
        response: Promise.reject(new Error("client exited before response")),
        settled: new Promise(() => {}),
        cancel: async () => { cancelCalled = true; },
      }),
      verifySnapshot: async () => true,
      onState: (state) => {
        durableState = structuredClone(state);
        return { ok: true };
      },
      overallDeadlineMs: 50,
      pollDelayMs: 0,
      sleep: async () => {},
    }),
    (error) => {
      assert.equal(error.code, "SETTLEMENT_UNPROVEN");
      assert.equal(error.state.publishIntent, true);
      assert.equal(error.state.publishSettlementUnproven, true);
      return true;
    },
  );
  assert.equal(cancelCalled, true);
  assert.equal(durableState.publishIntent, true);
  assert.equal(durableState.automaticRecoveryAllowed, false);

  let recoveryReads = 0;
  let recoveryPublishCalls = 0;
  await assert.rejects(
    () => recoverFromDurableState(durableState, {
      getRelease: async () => {
        recoveryReads += 1;
        return { id: 1, draft: false, immutable: true };
      },
      startPublishRelease: () => {
        recoveryPublishCalls += 1;
        throw new Error("manual recovery must not PATCH");
      },
      verifySnapshot: async () => true,
    }),
    (error) => {
      assert.equal(error.code, "MANUAL_RECOVERY_REQUIRED");
      assert.match(error.message, /inspect the exact release/i);
      return true;
    },
  );
  assert.equal(recoveryReads, 0);
  assert.equal(recoveryPublishCalls, 0);
});

test("crash immediately after dispatch leaves a manual-only marker", async () => {
  const draft = { id: 1, draft: true, immutable: false };
  let dispatched = false;
  let lastPersistedBytes = null;
  await assert.rejects(
    () => runReleaseTransition({
      getRelease: async () => ({ ...draft }),
      startPublishRelease: () => {
        dispatched = true;
        throw new Error("simulated process crash after dispatch");
      },
      verifySnapshot: async () => true,
      onState: (state) => {
        if (dispatched) {
          return { ok: false, error: new Error("process no longer persists") };
        }
        lastPersistedBytes = `${JSON.stringify(state)}\n`;
        return { ok: true };
      },
    }),
    (error) => {
      assert.equal(error.code, "PERSISTENCE_INCIDENT");
      return true;
    },
  );
  const lastPersisted = JSON.parse(lastPersistedBytes);
  assert.equal(dispatched, true);
  assert.match(lastPersisted.phase, /-publish-dispatch-armed$/);
  assert.equal(lastPersisted.automaticRecoveryAllowed, false);

  let reads = 0;
  let patches = 0;
  await assert.rejects(
    () => recoverFromDurableState(lastPersisted, {
      getRelease: async () => {
        reads += 1;
        return { id: 1, draft: false, immutable: true };
      },
      startPublishRelease: () => {
        patches += 1;
        throw new Error("manual-only marker must not PATCH");
      },
      verifySnapshot: async () => true,
    }),
    (error) => {
      assert.equal(error.code, "MANUAL_RECOVERY_REQUIRED");
      return true;
    },
  );
  assert.equal(reads, 0);
  assert.equal(patches, 0);
});

test("draft publish responses are reconciled by idempotent publish retries", async () => {
  const draft = { id: 1, draft: true, immutable: false };
  const immutable = { id: 1, draft: false, immutable: true };
  let publishCalls = 0;
  let current = { ...draft };
  const result = await runReleaseTransition({
    getRelease: async () => ({ ...current }),
    startPublishRelease: () => {
      publishCalls += 1;
      if (publishCalls === 2) current = { ...immutable };
      return {
        response: Promise.resolve({ ...current }),
        settled: Promise.resolve(),
        cancel: async () => {},
      };
    },
    verifySnapshot: async () => true,
    pollDelayMs: 0,
    sleep: async () => {},
  });
  assert.equal(result.release.immutable, true);
  assert.equal(publishCalls, 2);
});

test("an immutable PATCH response is never terminal without a confirming GET", async () => {
  let reads = 0;
  await assert.rejects(
    () => runReleaseTransition({
      getRelease: async () => {
        reads += 1;
        return { id: 1, draft: true, immutable: false };
      },
      startPublishRelease: () => ({
        response: Promise.resolve({
          id: 1,
          draft: false,
          immutable: true,
        }),
        settled: Promise.resolve(),
        cancel: async () => {},
      }),
      verifySnapshot: async () => true,
      maxCycles: 1,
      pollDelayMs: 0,
      sleep: async () => {},
    }),
    (error) => {
      assert.equal(error.code, "SETTLEMENT_UNPROVEN");
      return true;
    },
  );
  assert.equal(reads, 3);
});

test("recover-only reconciles exact mutable release to immutable", async () => {
  const mutable = { id: 1, draft: false, immutable: false };
  const immutable = { id: 1, draft: false, immutable: true };
  let current = { ...mutable };
  const result = await recoverFromDurableState({
    transitionAttempted: true,
    publishIntent: true,
    automaticRecoveryAllowed: true,
    history: [],
  }, {
    getRelease: async () => ({ ...current }),
    startPublishRelease: () => ({
      response: Promise.resolve({ ...current }),
      settled: Promise.resolve(),
      cancel: async () => {},
    }),
    verifySnapshot: async () => true,
    pollDelayMs: 0,
    sleep: async () => { current = { ...immutable }; },
  });
  assert.equal(result.status, "immutable");
});

test("recovery rejects a different durable publication identity", async () => {
  const intentIdentity = {
    repository: "microsoft/aibast-agents-library",
    releaseId: "1",
    tag: "brainstem-beta-v1.2.3",
    tagObject: "a".repeat(40),
    commit: "b".repeat(40),
    releaseFingerprint: "c".repeat(64),
  };
  let reads = 0;
  await assert.rejects(
    () => recoverFromDurableState({
      transitionAttempted: true,
      publishIntent: true,
      intentIdentity,
      history: [],
    }, {
      getRelease: async () => {
        reads += 1;
        return { id: 1, draft: false, immutable: true };
      },
      startPublishRelease: () => {
        throw new Error("publish must not run");
      },
      verifySnapshot: async () => true,
      intentIdentity: {
        ...intentIdentity,
        releaseFingerprint: "d".repeat(64),
      },
    }),
    (error) => {
      assert.equal(error.code, "INTEGRITY_INCIDENT");
      return true;
    },
  );
  assert.equal(reads, 0);
});

test("integrity drift is a sticky terminal incident", async () => {
  let reads = 0;
  const durable = {
    transitionAttempted: true,
    publishIntent: true,
    integrityViolation: true,
    integrityDetail: "asset drift",
    history: [],
  };
  await assert.rejects(
    () => recoverFromDurableState(durable, {
      getRelease: async () => {
        reads += 1;
        return { id: 1, draft: false, immutable: true };
      },
      startPublishRelease: () => {
        throw new Error("publish must not run");
      },
      verifySnapshot: async () => true,
    }),
    (error) => {
      assert.equal(error.code, "INTEGRITY_INCIDENT");
      assert.equal(error.state.integrityViolation, true);
      return true;
    },
  );
  assert.equal(reads, 0);

  let current = { id: 1, draft: false, immutable: false, drift: true };
  await assert.rejects(
    () => recoverFromDurableState({
      transitionAttempted: true,
      publishIntent: true,
      automaticRecoveryAllowed: true,
      history: [],
    }, {
      getRelease: async () => ({ ...current }),
      startPublishRelease: () => ({
        response: Promise.resolve({ ...current }),
        settled: Promise.resolve(),
        cancel: async () => {},
      }),
      verifySnapshot: async (release) => {
        if (release.drift) throw new Error("body fingerprint drift");
        return true;
      },
      maxCycles: 1,
      pollDelayMs: 0,
      sleep: async () => { current = { id: 1, draft: false, immutable: true }; },
    }),
    (error) => {
      assert.equal(error.code, "INTEGRITY_INCIDENT");
      return true;
    },
  );
});

test("response drift survives settlement-state persistence failure", async () => {
  const draft = { id: 1, draft: true, immutable: false };
  const drifted = {
    id: 1,
    draft: false,
    immutable: false,
    drift: true,
  };
  let failedState;
  await assert.rejects(
    () => runReleaseTransition({
      getRelease: async () => ({ ...draft }),
      startPublishRelease: () => ({
        response: Promise.resolve({ ...drifted }),
        settled: Promise.resolve(),
        cancel: async () => {},
      }),
      verifySnapshot: async (release) => {
        if (release.drift) throw new Error("response asset digest drift");
        return true;
      },
      onState: (state) => state.phase.endsWith("-publish-operation-settled")
        ? { ok: false, error: new Error("settlement state write failed") }
        : { ok: true },
    }),
    (error) => {
      failedState = structuredClone(error.state);
      assert.equal(error.code, "PERSISTENCE_INCIDENT");
      assert.equal(error.state.integrityViolation, true);
      assert.equal(error.state.automaticRecoveryAllowed, false);
      assert.match(error.state.integrityDetail, /asset digest drift/);
      return true;
    },
  );
  let recoveryReads = 0;
  await assert.rejects(
    () => recoverFromDurableState(failedState, {
      getRelease: async () => {
        recoveryReads += 1;
        return { id: 1, draft: false, immutable: true };
      },
      startPublishRelease: () => {
        throw new Error("latched integrity incident must not publish");
      },
      verifySnapshot: async () => true,
    }),
    (error) => {
      assert.equal(error.code, "INTEGRITY_INCIDENT");
      return true;
    },
  );
  assert.equal(recoveryReads, 0);
});

test("last persisted bytes forbid recovery after integrity directory-sync failure", async () => {
  const draft = { id: 1, draft: true, immutable: false };
  const drifted = {
    id: 1,
    draft: false,
    immutable: false,
    drift: true,
  };
  let marker = null;
  let temporary = "";
  let failCombinedDirectorySync = false;
  let directoryFailureTriggered = false;
  let nextDescriptor = 0;
  const descriptorKinds = new Map();
  const writer = createAtomicStateWriter("state.json", {
    readFileSync: () => {
      if (marker === null) {
        throw Object.assign(new Error("missing"), { code: "ENOENT" });
      }
      return Buffer.from(marker);
    },
    openSync: (filePath) => {
      nextDescriptor += 1;
      descriptorKinds.set(
        nextDescriptor,
        filePath === "." ? "directory" : "file",
      );
      return nextDescriptor;
    },
    writeFileSync: (_descriptor, value) => { temporary = value; },
    fsyncSync: (descriptor) => {
      if (
        descriptorKinds.get(descriptor) === "directory"
        && failCombinedDirectorySync
        && !directoryFailureTriggered
      ) {
        directoryFailureTriggered = true;
        throw new Error("combined-state directory fsync failed");
      }
    },
    closeSync() {},
    renameSync: () => {
      marker = Buffer.isBuffer(temporary)
        ? temporary.toString("utf8")
        : temporary;
      temporary = "";
    },
    rmSync: (filePath) => {
      if (filePath === "state.json") marker = null;
      else temporary = "";
    },
  });
  await assert.rejects(
    () => runReleaseTransition({
      getRelease: async () => ({ ...draft }),
      startPublishRelease: () => ({
        response: Promise.resolve({ ...drifted }),
        settled: Promise.resolve(),
        cancel: async () => {},
      }),
      verifySnapshot: async (release) => {
        if (release.drift) throw new Error("response fingerprint drift");
        return true;
      },
      onState: (state) => {
        failCombinedDirectorySync =
          state.phase.endsWith("-publish-operation-settled");
        return writer(state);
      },
    }),
    (error) => {
      assert.equal(error.code, "PERSISTENCE_INCIDENT");
      assert.equal(error.state.integrityViolation, true);
      assert.equal(error.state.automaticRecoveryAllowed, false);
      return true;
    },
  );
  assert.equal(directoryFailureTriggered, true);
  const lastPersisted = JSON.parse(marker);
  assert.match(lastPersisted.phase, /-publish-dispatch-armed$/);
  assert.equal(lastPersisted.publishIntent, true);
  assert.equal(lastPersisted.automaticRecoveryAllowed, false);
  assert.equal(lastPersisted.integrityViolation, false);

  let recoveryReads = 0;
  let recoveryPatches = 0;
  let immutableSuccess = false;
  await assert.rejects(
    async () => {
      const result = await recoverFromDurableState(lastPersisted, {
        getRelease: async () => {
          recoveryReads += 1;
          return { id: 1, draft: false, immutable: true };
        },
        startPublishRelease: () => {
          recoveryPatches += 1;
          throw new Error("fresh recovery must not PATCH");
        },
        verifySnapshot: async () => true,
      });
      immutableSuccess = result.status === "immutable";
      return result;
    },
    (error) => {
      assert.equal(error.code, "MANUAL_RECOVERY_REQUIRED");
      return true;
    },
  );
  assert.equal(recoveryReads, 0);
  assert.equal(recoveryPatches, 0);
  assert.equal(immutableSuccess, false);
});

test("snapshot verification cannot be mutated into a no-op", async () => {
  let publishCalled = false;
  await assert.rejects(
    () => runReleaseTransition({
      getRelease: async () => ({ id: 1, draft: true, immutable: false }),
      startPublishRelease: () => {
        publishCalled = true;
        return {
          response: Promise.resolve({ id: 1, draft: false, immutable: false }),
          settled: Promise.resolve(),
          cancel: async () => {},
        };
      },
      verifySnapshot: async () => undefined,
    }),
    (error) => {
      assert.equal(error.code, "INTEGRITY_INCIDENT");
      return true;
    },
  );
  assert.equal(publishCalled, false);
});

test("cancellable publish handle settles before reconciliation continues", async () => {
  let cancelCalled = false;
  let settle;
  const settled = new Promise((resolve) => { settle = resolve; });
  const handle = {
    response: Promise.reject(new Error("response lost")),
    settled,
    cancel: async () => {
      cancelCalled = true;
      setTimeout(settle, 10);
    },
  };
  const started = Date.now();
  await quiescePublishOperation(handle, 100);
  assert.equal(cancelCalled, true);
  assert.ok(Date.now() - started >= 8);
});

test("local interruption stops dispatch after durable publish intent", async () => {
  let abortChecks = 0;
  let publishCalled = false;
  await assert.rejects(
    () => runReleaseTransition({
      getRelease: async () => ({ id: 1, draft: true, immutable: false }),
      startPublishRelease: () => {
        publishCalled = true;
        throw new Error("interrupted main operation must not publish");
      },
      verifySnapshot: async () => true,
      shouldAbort: () => {
        abortChecks += 1;
        return abortChecks >= 2;
      },
    }),
    (error) => {
      assert.equal(error.code, "LOCAL_OPERATION_INTERRUPTED");
      assert.equal(error.state.publishIntent, true);
      assert.equal(error.state.automaticRecoveryAllowed, false);
      return true;
    },
  );
  assert.equal(publishCalled, false);
});

test("signal reconciliation waits for the interrupted operation", async () => {
  const merged = mergeDurableState({
    transitionAttempted: true,
    publishIntent: true,
    integrityViolation: true,
    integrityDetail: "digest drift",
    history: [{ phase: "integrity", detail: "drift" }],
  }, {
    phase: "signal-reconciliation-started",
    signal: "SIGTERM",
    history: [{ phase: "signal-reconciliation-started", detail: "SIGTERM" }],
  });
  assert.equal(recoveryRequiredFromState(merged), true);
  assert.equal(merged.integrityViolation, true);
  assert.equal(merged.integrityDetail, "digest drift");
  assert.equal(merged.history.length, 2);
  assert.equal(
    mergeDurableState(merged, merged).history.length,
    2,
    "concurrent signal/main snapshots must not duplicate durable history",
  );
  assert.equal(
    mergeDurableState(
      { automaticRecoveryAllowed: false },
      { automaticRecoveryAllowed: true },
    ).automaticRecoveryAllowed,
    false,
    "concurrent state merging must never bless a manual-only marker",
  );
  const workflow = loadWorkflowContract();
  if (workflow === null) {
    return;
  }
  const publish = workflowJob(workflow, "publish");
  assert.match(publish, /Reconcile interrupted release publication/);
  assert.match(publish, /failure\(\) \|\| cancelled\(\)/);
  assert.match(publish, /--recover-only/);
  const recoveryStep = publish.slice(
    publish.indexOf("Reconcile interrupted release publication"),
  );
  const recoveryAuthorization = recoveryStep.indexOf(
    "automaticRecoveryAllowed == true",
  );
  const recoveryImmutable = recoveryStep.indexOf("immutable-releases");
  const recoverOnly = recoveryStep.indexOf("--recover-only");
  assert.ok(
    recoveryAuthorization >= 0
      && recoveryImmutable >= 0
      && recoverOnly >= 0
      && recoveryAuthorization < recoveryImmutable
      && recoveryImmutable < recoverOnly,
    "recovery must require durable authorization and immutable-release policy",
  );
  assert.match(recoveryStep, /jq -e '\.enabled == true'/);
  const transitionSource = readFileSync(
    path.join(betaDir, "scripts", "publish-release-state-machine.mjs"),
    "utf8",
  );
  assert.match(transitionSource, /waitForMain/);
  assert.match(transitionSource, /process\.exitCode = 130/);
  assert.doesNotMatch(transitionSource, /process\.exit\(130\)/);

  let latest = {
    transitionAttempted: true,
    publishIntent: true,
    automaticRecoveryAllowed: true,
    history: [],
  };
  const cliState = {
    get latest() {
      return latest;
    },
    merge(patch) {
      latest = mergeDurableState(latest, patch);
      return { ok: true };
    },
    persist(state) {
      latest = structuredClone(state);
      return { ok: true };
    },
  };
  let mainFinished = false;
  const result = await reconcileInterruptedSignal({
    signal: "SIGTERM",
    cliState,
    getRelease: async () => {
      assert.equal(mainFinished, true);
      return { id: 1, draft: false, immutable: true };
    },
    startPublishRelease: () => {
      throw new Error("an immutable release must not be republished");
    },
    verifySnapshot: async () => true,
    waitForMain: async () => {
      await new Promise((resolve) => setTimeout(resolve, 5));
      mainFinished = true;
    },
    overallDeadlineMs: 100,
  });
  assert.equal(result.status, "immutable");
  assert.equal(latest.phase, "terminal-immutable");

  let manualLatest = {
    transitionAttempted: true,
    publishIntent: true,
    automaticRecoveryAllowed: false,
    history: [],
  };
  const manualCliState = {
    get latest() {
      return manualLatest;
    },
    merge(patch) {
      manualLatest = mergeDurableState(manualLatest, patch);
      return { ok: true };
    },
    persist(state) {
      manualLatest = structuredClone(state);
      return { ok: true };
    },
  };
  let manualReads = 0;
  let manualPatches = 0;
  const manualResult = await reconcileInterruptedSignal({
    signal: "SIGINT",
    cliState: manualCliState,
    getRelease: async () => {
      manualReads += 1;
      return { id: 1, draft: false, immutable: true };
    },
    startPublishRelease: () => {
      manualPatches += 1;
      throw new Error("unsafe signal recovery must not PATCH");
    },
    verifySnapshot: async () => true,
    waitForMain: async () => {},
    overallDeadlineMs: 100,
  });
  assert.equal(manualResult, null);
  assert.equal(manualReads, 0);
  assert.equal(manualPatches, 0);
  assert.equal(manualLatest.automaticRecoveryAllowed, false);
  assert.equal(manualLatest.phase, "manual-recovery-required");
});

test("atomic state persistence retains previous valid marker", () => {
  const previous = '{"phase":"publish-intent-recorded"}\n';
  const temporaryPaths = [];
  let directoryOpens = 0;
  let directoryFsyncs = 0;
  let directoryCloses = 0;
  const operationOrder = [];
  const successfulWriter = createAtomicStateWriter("state.json", {
    readFileSync: () => {
      throw Object.assign(new Error("missing"), { code: "ENOENT" });
    },
    openSync: (filePath) => {
      if (filePath === ".") {
        operationOrder.push("open-directory");
        directoryOpens += 1;
        return 100 + directoryOpens;
      }
      operationOrder.push("open-file");
      temporaryPaths.push(filePath);
      return temporaryPaths.length;
    },
    writeFileSync() { operationOrder.push("write-file"); },
    fsyncSync: (descriptor) => {
      if (descriptor >= 100) {
        operationOrder.push("fsync-directory");
        directoryFsyncs += 1;
      } else {
        operationOrder.push("fsync-file");
      }
    },
    closeSync: (descriptor) => {
      if (descriptor >= 100) {
        operationOrder.push("close-directory");
        directoryCloses += 1;
      } else {
        operationOrder.push("close-file");
      }
    },
    renameSync() { operationOrder.push("rename"); },
    rmSync() {},
  });
  assert.equal(successfulWriter({ phase: "one" }).ok, true);
  assert.equal(successfulWriter({ phase: "two" }).ok, true);
  assert.equal(new Set(temporaryPaths).size, 2);
  assert.ok(temporaryPaths.every((entry) => entry.endsWith(".state.tmp")));
  assert.equal(directoryOpens, 2);
  assert.equal(directoryFsyncs, 2);
  assert.equal(directoryCloses, 2);
  assert.deepEqual(operationOrder.slice(0, 8), [
    "open-file",
    "write-file",
    "fsync-file",
    "close-file",
    "rename",
    "open-directory",
    "fsync-directory",
    "close-directory",
  ]);

  for (const failurePoint of [
    "open-disk-full",
    "write",
    "rename",
    "directory-open",
    "directory-fsync",
    "directory-close",
  ]) {
    let marker = previous;
    let temporary = "";
    let directoryFailureTriggered = false;
    let directoryOpenCalls = 0;
    let directoryFsyncCalls = 0;
    let directoryCloseCalls = 0;
    const descriptorKinds = new Map();
    let nextDescriptor = 1;
    const writer = createAtomicStateWriter("state.json", {
      readFileSync: () => Buffer.from(marker),
      openSync: (filePath) => {
        const isDirectory = filePath === ".";
        if (
          isDirectory
          && failurePoint === "directory-open"
          && !directoryFailureTriggered
        ) {
          directoryFailureTriggered = true;
          throw new Error("directory open failed");
        }
        if (
          !isDirectory
          && !filePath.endsWith(".restore.tmp")
          && failurePoint === "open-disk-full"
        ) {
          throw Object.assign(new Error("disk full"), { code: "ENOSPC" });
        }
        const descriptor = nextDescriptor;
        nextDescriptor += 1;
        descriptorKinds.set(descriptor, isDirectory ? "directory" : "file");
        if (isDirectory) directoryOpenCalls += 1;
        return descriptor;
      },
      writeFileSync: (_descriptor, value) => {
        if (
          failurePoint === "write"
          && !String(value).includes("publish-intent-recorded")
        ) {
          throw new Error("write failed");
        }
        temporary = value;
      },
      fsyncSync: (descriptor) => {
        if (descriptorKinds.get(descriptor) !== "directory") return;
        directoryFsyncCalls += 1;
        if (
          failurePoint === "directory-fsync"
          && !directoryFailureTriggered
        ) {
          directoryFailureTriggered = true;
          throw new Error("directory fsync failed");
        }
      },
      closeSync: (descriptor) => {
        if (descriptorKinds.get(descriptor) !== "directory") return;
        directoryCloseCalls += 1;
        if (
          failurePoint === "directory-close"
          && !directoryFailureTriggered
        ) {
          directoryFailureTriggered = true;
          throw new Error("directory close failed");
        }
      },
      renameSync: (source) => {
        if (
          failurePoint === "rename"
          && !source.endsWith(".restore.tmp")
        ) {
          throw new Error("rename failed");
        }
        marker = Buffer.isBuffer(temporary)
          ? temporary.toString("utf8")
          : temporary;
        temporary = "";
      },
      rmSync: (filePath) => {
        if (filePath === "state.json") marker = null;
        else temporary = "";
      },
    });
    assert.equal(writer({ phase: "new" }).ok, false);
    assert.equal(marker, previous);
    if (failurePoint.startsWith("directory-")) {
      assert.equal(directoryFailureTriggered, true);
    }
    if (failurePoint === "directory-fsync") {
      assert.ok(directoryOpenCalls >= 2);
      assert.ok(directoryFsyncCalls >= 2);
      assert.ok(directoryCloseCalls >= 2);
    }
    if (failurePoint === "directory-close") {
      assert.ok(directoryOpenCalls >= 2);
      assert.ok(directoryFsyncCalls >= 2);
      assert.ok(directoryCloseCalls >= 2);
    }
    assert.equal(writer({ phase: "later" }).ok, false);
  }
});

test("persistence failures and terminal write failures forbid success", async () => {
  const draft = { id: 1, draft: true, immutable: false };
  const immutable = { id: 1, draft: false, immutable: true };
  let current = { ...draft };
  await assert.rejects(
    () => runReleaseTransition({
      getRelease: async () => ({ ...current }),
      startPublishRelease: () => {
        current = { ...immutable };
        return {
          response: Promise.resolve({ ...immutable }),
          settled: Promise.resolve(),
          cancel: async () => {},
        };
      },
      verifySnapshot: async () => true,
      onState: (state) => state.phase === "terminal-immutable"
        ? { ok: false, error: new Error("terminal write failed") }
        : { ok: true },
      pollDelayMs: 0,
      sleep: async () => {},
    }),
    (error) => {
      assert.equal(error.code, "PERSISTENCE_INCIDENT");
      return true;
    },
  );

  let intentRecorded = false;
  await assert.rejects(
    () => runReleaseTransition({
      getRelease: async () => ({ ...draft }),
      startPublishRelease: () => {
        throw new Error("must not dispatch without durable intent");
      },
      verifySnapshot: async () => true,
      onState: (state) => {
        if (state.phase === "publish-intent-recorded") {
          intentRecorded = true;
          return { ok: false, error: new Error("disk full") };
        }
        return { ok: true };
      },
    }),
    (error) => {
      assert.equal(error.code, "PERSISTENCE_INCIDENT");
      return true;
    },
  );
  assert.equal(intentRecorded, true);

  let marker = null;
  let temporary = "";
  let failDirectorySync = false;
  let directoryFailureTriggered = false;
  let descriptor = 0;
  const descriptorKinds = new Map();
  const directoryFailingWriter = createAtomicStateWriter("state.json", {
    readFileSync: () => {
      if (marker === null) {
        throw Object.assign(new Error("missing"), { code: "ENOENT" });
      }
      return Buffer.from(marker);
    },
    openSync: (filePath) => {
      descriptor += 1;
      descriptorKinds.set(
        descriptor,
        filePath === "." ? "directory" : "file",
      );
      return descriptor;
    },
    writeFileSync: (_descriptor, value) => { temporary = value; },
    fsyncSync: (currentDescriptor) => {
      if (
        descriptorKinds.get(currentDescriptor) === "directory"
        && failDirectorySync
        && !directoryFailureTriggered
      ) {
        directoryFailureTriggered = true;
        throw new Error("directory fsync failed");
      }
    },
    closeSync() {},
    renameSync: () => {
      marker = Buffer.isBuffer(temporary)
        ? temporary.toString("utf8")
        : temporary;
      temporary = "";
    },
    rmSync: (filePath) => {
      if (filePath === "state.json") marker = null;
      else temporary = "";
    },
  });
  let directoryFailurePublishCalled = false;
  await assert.rejects(
    () => runReleaseTransition({
      getRelease: async () => ({ ...draft }),
      startPublishRelease: () => {
        directoryFailurePublishCalled = true;
        throw new Error("directory durability failure must block dispatch");
      },
      verifySnapshot: async () => true,
      onState: (state) => {
        failDirectorySync = state.phase === "publish-intent-recorded";
        return directoryFailingWriter(state);
      },
    }),
    (error) => {
      assert.equal(error.code, "PERSISTENCE_INCIDENT");
      return true;
    },
  );
  assert.equal(directoryFailureTriggered, true);
  assert.equal(directoryFailurePublishCalled, false);
  assert.equal(JSON.parse(marker).publishIntent, false);
});

test("post-publication write failures retain manual-only durable intent", async () => {
  const draft = { id: 1, draft: true, immutable: false };
  const immutable = { id: 1, draft: false, immutable: true };
  for (const failurePoint of ["open-disk-full", "write", "rename"]) {
    let current = { ...draft };
    let marker = null;
    let temporary = "";
    let failNow = false;
    const writer = createAtomicStateWriter("state.json", {
      openSync: () => {
        if (failNow && failurePoint === "open-disk-full") {
          throw Object.assign(new Error("disk full"), { code: "ENOSPC" });
        }
        return 7;
      },
      writeFileSync: (_descriptor, value) => {
        if (failNow && failurePoint === "write") {
          throw Object.assign(new Error("write failed"), { code: "EIO" });
        }
        temporary = value;
      },
      fsyncSync() {},
      closeSync() {},
      renameSync: () => {
        if (failNow && failurePoint === "rename") {
          throw new Error("rename failed");
        }
        marker = temporary;
        temporary = "";
      },
      rmSync: () => { temporary = ""; },
    });
    await assert.rejects(
      () => runReleaseTransition({
        getRelease: async () => ({ ...current }),
        startPublishRelease: () => {
          current = { ...immutable };
          return {
            response: Promise.resolve({ ...immutable }),
            settled: Promise.resolve(),
            cancel: async () => {},
          };
        },
        verifySnapshot: async () => true,
        onState: (state) => {
          failNow = state.phase.endsWith("-publish-operation-settled");
          return writer(state);
        },
        pollDelayMs: 0,
        sleep: async () => {},
      }),
      (error) => {
        assert.equal(error.code, "PERSISTENCE_INCIDENT");
        assert.equal(error.state.publishIntent, true);
        assert.equal(error.state.persistenceFailure, true);
        return true;
      },
    );
    const durable = JSON.parse(marker);
    assert.equal(durable.publishIntent, true);
    assert.equal(durable.automaticRecoveryAllowed, false);
    assert.notEqual(durable.phase, "terminal-immutable");
    let reads = 0;
    let patches = 0;
    await assert.rejects(
      () => recoverFromDurableState(durable, {
        getRelease: async () => {
          reads += 1;
          return { ...immutable };
        },
        startPublishRelease: () => {
          patches += 1;
          throw new Error("manual recovery must not publish");
        },
        verifySnapshot: async () => true,
      }),
      (error) => {
        assert.equal(error.code, "MANUAL_RECOVERY_REQUIRED");
        return true;
      },
    );
    assert.equal(reads, 0);
    assert.equal(patches, 0);
  }
});

test("reconciliation operations and polling sleeps are deadline bounded", async () => {
  const durable = {
    transitionAttempted: true,
    publishIntent: true,
    automaticRecoveryAllowed: true,
    history: [],
  };
  const hangingOperation = (signal, evidence) => {
    let settle;
    let rejectResult;
    const settled = new Promise((resolve) => { settle = resolve; });
    const result = new Promise((_, reject) => { rejectResult = reject; });
    signal.addEventListener("abort", () => {
      evidence.abortObserved = true;
      evidence.settled = true;
      settle();
      rejectResult(signal.reason);
    }, { once: true });
    return {
      result,
      settled,
      cancel: async () => { evidence.cancelCalled = true; },
    };
  };
  const checkedSignal = ({ signal, deadline, hardDeadline }) => {
    assert.ok(signal instanceof AbortSignal);
    assert.ok(Number.isFinite(deadline));
    assert.ok(hardDeadline > deadline);
    return signal;
  };

  const getEvidence = {};
  let getLaterWork = false;
  const started = Date.now();
  await assert.rejects(
    () => recoverFromDurableState(durable, {
      getRelease: (operation) =>
        hangingOperation(checkedSignal(operation), getEvidence),
      startPublishRelease: () => {
        getLaterWork = true;
        throw new Error("publish must not start after aborted GET");
      },
      verifySnapshot: async () => true,
      overallDeadlineMs: 100,
      pollDelayMs: 0,
      sleep: async () => {},
    }),
    (error) => {
      assert.equal(error.code, "SETTLEMENT_UNPROVEN");
      assert.equal(error.state.publishSettlementUnproven, true);
      return true;
    },
  );
  assert.equal(getEvidence.abortObserved, true);
  assert.equal(getEvidence.cancelCalled, true);
  assert.equal(getEvidence.settled, true);
  assert.equal(getLaterWork, false);
  assert.ok(Date.now() - started < 500);

  const snapshotEvidence = {};
  let snapshotLaterWork = false;
  await assert.rejects(
    () => recoverFromDurableState(durable, {
      getRelease: async () => ({
        id: 1,
        draft: false,
        immutable: false,
      }),
      startPublishRelease: () => {
        snapshotLaterWork = true;
        throw new Error("publish must not start after aborted snapshot");
      },
      verifySnapshot: (_release, operation) =>
        hangingOperation(checkedSignal(operation), snapshotEvidence),
      overallDeadlineMs: 100,
      pollDelayMs: 0,
      sleep: async () => {},
    }),
    (error) => {
      assert.equal(error.code, "SETTLEMENT_UNPROVEN");
      assert.equal(error.state.integrityViolation, false);
      return true;
    },
  );
  assert.equal(snapshotEvidence.abortObserved, true);
  assert.equal(snapshotEvidence.cancelCalled, true);
  assert.equal(snapshotEvidence.settled, true);
  assert.equal(snapshotLaterWork, false);

  const publishEvidence = {};
  let publishGetCalls = 0;
  await assert.rejects(
    () => recoverFromDurableState(durable, {
      getRelease: async () => {
        publishGetCalls += 1;
        return { id: 1, draft: true, immutable: false };
      },
      startPublishRelease: (context) => {
        const operation = hangingOperation(
          checkedSignal(context),
          publishEvidence,
        );
        return {
          response: operation.result,
          settled: operation.settled,
          cancel: operation.cancel,
        };
      },
      verifySnapshot: async () => true,
      overallDeadlineMs: 100,
      pollDelayMs: 0,
      sleep: async () => {},
    }),
    /settlement is unproven|persistence failed|deadline/i,
  );
  assert.equal(publishEvidence.abortObserved, true);
  assert.equal(publishEvidence.cancelCalled, true);
  assert.equal(publishEvidence.settled, true);
  assert.equal(publishGetCalls, 1);

  const sleepEvidence = {};
  let sleepLaterWork = false;
  await assert.rejects(
    () => recoverFromDurableState(durable, {
      getRelease: async () => ({
        id: 1,
        draft: false,
        immutable: false,
      }),
      startPublishRelease: () => {
        sleepLaterWork = true;
        throw new Error("publish must not start after aborted sleep");
      },
      verifySnapshot: async () => true,
      maxCycles: 2,
      overallDeadlineMs: 100,
      pollDelayMs: 200,
      sleep: (_milliseconds, operation) =>
        hangingOperation(checkedSignal(operation), sleepEvidence),
    }),
    /settlement is unproven|deadline/i,
  );
  assert.equal(sleepEvidence.abortObserved, true);
  assert.equal(sleepEvidence.cancelCalled, true);
  assert.equal(sleepEvidence.settled, true);
  assert.equal(sleepLaterWork, false);
  assert.ok(Date.now() - started < 1000);
});

test("abort callback cannot settle a SIGTERM-resistant Git child", async () => {
  const childSignals = [];
  const closeHandlers = [];
  let callbackReported = false;
  let callbackBeforeClose = false;
  let childAlive = true;
  let childSettled = false;
  let publishCalled = false;
  const fakeExecFile = (_command, _args, options, callback) => {
    const child = {
      exitCode: null,
      signalCode: null,
      once(event, handler) {
        if (event === "close") closeHandlers.push(handler);
        return child;
      },
      kill(signal = "SIGTERM") {
        childSignals.push(signal);
        if (signal === "SIGTERM" && !callbackReported) {
          callbackReported = true;
          callbackBeforeClose = childAlive;
          callback(
            Object.assign(new Error("git aborted"), { code: "ABORT_ERR" }),
            "",
            "",
          );
          return true;
        }
        if (signal !== "SIGKILL" || !childAlive) return true;
        child.signalCode = "SIGKILL";
        childAlive = false;
        childSettled = true;
        for (const handler of closeHandlers) handler(null, "SIGKILL");
        return true;
      },
    };
    options.signal.addEventListener(
      "abort",
      () => child.kill(options.killSignal),
      { once: true },
    );
    return child;
  };
  const started = Date.now();
  await assert.rejects(
    () => recoverFromDurableState({
      transitionAttempted: true,
      publishIntent: true,
      automaticRecoveryAllowed: true,
      history: [],
    }, {
      getRelease: (operation) => {
        assert.ok(Number.isFinite(operation.deadline));
        assert.ok(operation.hardDeadline > operation.deadline);
        return startAbortableExecFile(
          "git",
          ["ls-remote", "https://github.com/example/example.git"],
          { encoding: "utf8" },
          operation,
          fakeExecFile,
        );
      },
      startPublishRelease: () => {
        publishCalled = true;
        throw new Error("work after Git abort must not start");
      },
      verifySnapshot: async () => true,
      overallDeadlineMs: 1000,
    }),
    /settlement is unproven|deadline/i,
  );
  assert.ok(childSignals.includes("SIGTERM"));
  assert.ok(childSignals.includes("SIGKILL"));
  assert.equal(callbackReported, true);
  assert.equal(callbackBeforeClose, true);
  assert.equal(childAlive, false);
  assert.equal(childSettled, true);
  assert.equal(publishCalled, false);
  assert.ok(Date.now() - started < 2500);
});

test("production snapshot verifier awaits every Git child close", async () => {
  const tag = "brainstem-beta-v1.2.3";
  const tagObject = "a".repeat(40);
  const commit = "b".repeat(40);
  const release = {
    id: 1,
    tag_name: tag,
    draft: false,
    immutable: false,
    body: "exact release body",
    assets: [{
      id: 10,
      name: "asset.exe",
      state: "uploaded",
      size: 123,
      digest: `sha256:${"c".repeat(64)}`,
    }],
  };
  const verifierArgs = {
    repository: "microsoft/aibast-agents-library",
    tag,
    "tag-object": tagObject,
    commit,
    "release-id": "1",
    "release-fingerprint": releaseContentFingerprint(release),
  };

  for (const failingChild of [1, 2]) {
    const caseStarted = Date.now();
    let spawnedChildren = 0;
    let closedChildren = 0;
    let liveChildren = 0;
    let sigkillCount = 0;
    let callbackBeforeClose = false;
    let secondSpawnedAfterFirstClose = null;
    let publishCalled = false;
    const createRemoteOperation = (_repository, ref, operation) => {
      spawnedChildren += 1;
      const childIndex = spawnedChildren;
      if (childIndex === 2) {
        secondSpawnedAfterFirstClose = closedChildren === 1;
      }
      const expectedSha = ref.endsWith("^{}") ? commit : tagObject;
      const subprocess = startAbortableExecFile(
        "git",
        ["ls-remote", ref],
        { encoding: "utf8" },
        operation,
        (_command, _args, options, callback) => {
          const closeHandlers = [];
          let callbackReported = false;
          let closed = false;
          liveChildren += 1;
          const child = {
            exitCode: null,
            signalCode: null,
            once(event, handler) {
              if (event === "close") closeHandlers.push(handler);
              return child;
            },
            kill(signal = "SIGTERM") {
              if (closed) return true;
              if (signal === "SIGTERM" && childIndex === failingChild) {
                if (!callbackReported) {
                  callbackReported = true;
                  callbackBeforeClose = liveChildren > 0;
                  callback(
                    Object.assign(
                      new Error(`git child ${childIndex} aborted`),
                      { code: "ABORT_ERR" },
                    ),
                    "",
                    "",
                  );
                }
                return true;
              }
              if (signal === "SIGKILL" && childIndex === failingChild) {
                sigkillCount += 1;
                if (closed) return true;
                closed = true;
                child.signalCode = "SIGKILL";
                liveChildren -= 1;
                closedChildren += 1;
                for (const handler of closeHandlers) {
                  handler(null, "SIGKILL");
                }
              }
              return true;
            },
          };
          options.signal.addEventListener(
            "abort",
            () => child.kill(options.killSignal),
            { once: true },
          );
          if (childIndex < failingChild) {
            queueMicrotask(() => {
              callbackReported = true;
              callback(null, `${expectedSha}\t${ref}\n`, "");
              queueMicrotask(() => {
                if (closed) return;
                closed = true;
                child.exitCode = 0;
                liveChildren -= 1;
                closedChildren += 1;
                for (const handler of closeHandlers) handler(0, null);
              });
            });
          }
          return child;
        },
      );
      return {
        result: subprocess.result.then(({ stdout }) =>
          stdout.trim().split(/\s+/)[0]),
        settled: subprocess.settled,
        cancel: subprocess.cancel,
      };
    };
    const verifySnapshot = createSnapshotVerifier(
      verifierArgs,
      createRemoteOperation,
    );
    await assert.rejects(
      () => recoverFromDurableState({
        transitionAttempted: true,
        publishIntent: true,
        automaticRecoveryAllowed: true,
        history: [],
      }, {
        getRelease: async () => structuredClone(release),
        startPublishRelease: () => {
          publishCalled = true;
          throw new Error("snapshot failure must stop later publication work");
        },
        verifySnapshot,
        overallDeadlineMs: 1000,
      }),
      /settlement is unproven|deadline/i,
    );
    assert.equal(spawnedChildren, failingChild);
    assert.equal(closedChildren, failingChild);
    assert.equal(liveChildren, 0);
    assert.equal(sigkillCount, 1);
    assert.equal(callbackBeforeClose, true);
    assert.equal(publishCalled, false);
    if (failingChild === 2) {
      assert.equal(secondSpawnedAfterFirstClose, true);
    }
    assert.ok(Date.now() - caseStarted < 2500);
  }
});

test("second Windows binary release requires immutable N-1 evidence", () => {
  const currentTag = "brainstem-beta-v2.0.0-beta.2";
  assert.deepEqual(selectPreviousWindowsBinary([], currentTag), {
    firstBinaryRelease: true,
    previousReleaseTag: null,
    previousAssetId: null,
    previousAssetName: null,
    previousAssetDigest: null,
  });
  const previous = {
    id: 10,
    tag_name: "brainstem-beta-v2.0.0-beta.1",
    draft: false,
    immutable: true,
    published_at: "2026-09-01T00:00:00Z",
    assets: [{
      id: 99,
      name:
        "RAPP-Brainstem-Frontier-2.0.0-beta.1-windows-x64-setup.exe",
      digest: `sha256:${"a".repeat(64)}`,
      state: "uploaded",
      size: 1234,
    }],
  };
  assert.deepEqual(selectPreviousWindowsBinary([previous], currentTag), {
    firstBinaryRelease: false,
    previousReleaseTag: previous.tag_name,
    previousAssetId: "99",
    previousAssetName: previous.assets[0].name,
    previousAssetDigest: previous.assets[0].digest,
  });
  assert.throws(
    () => selectPreviousWindowsBinary(
      [{ ...previous, immutable: false }],
      currentTag,
    ),
    /not immutable/,
  );
  assert.throws(
    () => selectPreviousWindowsBinary([{
      ...previous,
      assets: [...previous.assets, { ...previous.assets[0], id: 100 }],
    }], currentTag),
    /exactly one/,
  );
  assert.throws(
    () => parseGateArguments([
      "--platform", "windows",
      "--arch", "x64",
      "--mode", "signed",
      "--expected-publisher", "CN=Microsoft Corporation",
      "--release-tag", currentTag,
      "--release-commit", "b".repeat(40),
      "--runtime-version-url",
      `https://raw.githubusercontent.com/test/repo/${"b".repeat(40)}/VERSION`,
      "--require-standard-user", "true",
    ], { platform: "win32", arch: "x64" }),
    /exactly one of --previous-installer/,
  );
  const workflow = loadWorkflowContract();
  if (workflow === null) {
    return;
  }
  const context = workflowJob(workflow, "context");
  assert.match(context, /windows-upgrade-policy\.mjs/);
  assert.match(context, /previous_windows_asset_id/);
  assert.match(context, /first_binary_release/);
  const windows = workflowJob(workflow, "verify-windows-release");
  assert.match(windows, /releases\/assets\/\$env:PREVIOUS_ASSET_ID/);
  assert.match(windows, /PREVIOUS_ASSET_DIGEST/);
  assert.match(windows, /PreviousInstaller/);
  assert.match(windows, /FirstBinaryRelease/);
});

test("protected clean-Mac gate exercises quarantine and LaunchServices", () => {
  const workflow = loadWorkflowContract();
  if (workflow === null) {
    return;
  }
  const quarantine = workflowJob(workflow, "quarantine-macos");
  assert.match(quarantine, /environment: frontier-clean-mac-acceptance/);
  assert.match(quarantine, /runs-on: macos-26/);
  assert.match(quarantine, /com\.apple\.quarantine/);
  assert.match(quarantine, /\/Applications\/RAPP Brainstem Frontier\.app/);
  assert.match(quarantine, /sudo ditto/);
  assert.match(quarantine, /open -W -n/);
  assert.match(quarantine, /quarantine-acceptance\.json/);
  const publish = workflowJob(workflow, "publish");
  assert.match(publish, /- quarantine-macos/);
});
