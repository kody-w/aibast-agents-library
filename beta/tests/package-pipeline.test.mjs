import assert from "node:assert/strict";
import {
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
  recoverInterruptedRelease,
  recoveryRequiredFromState,
  ReleaseTransitionError,
  runReleaseTransition,
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
  const workflow = readFileSync(
    path.join(repositoryDir, ".github", "workflows", "frontier-binaries.yml"),
    "utf8",
  );
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
  const workflow = readFileSync(
    path.join(repositoryDir, ".github", "workflows", "frontier-binaries.yml"),
    "utf8",
  );
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
  const workflow = readFileSync(
    path.join(repositoryDir, ".github", "workflows", "frontier-binaries.yml"),
    "utf8",
  );
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
  const workflow = readFileSync(
    path.join(repositoryDir, ".github", "workflows", "frontier-binaries.yml"),
    "utf8",
  );
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
  const workflow = readFileSync(
    path.join(repositoryDir, ".github", "workflows", "frontier-binaries.yml"),
    "utf8",
  );
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
  assert.match(transitionSource, /maxRollbackAttempts = 5/);
  assert.match(transitionSource, /\["-F", "draft=true"\]/);
  assert.match(transitionSource, /immediately-before-publication/);
  assert.match(transitionSource, /publish-response/);
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

  const workflow = readFileSync(
    path.join(repositoryDir, ".github", "workflows", "frontier-binaries.yml"),
    "utf8",
  );
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

test("publication state machine recovers from ambiguous API outcomes", async () => {
  const draft = { id: 1, draft: true, immutable: false };
  const mutable = { id: 1, draft: false, immutable: false };
  const immutable = { id: 1, draft: false, immutable: true };
  const verifySnapshot = async (release) => {
    assert.equal(release.id, 1);
    return true;
  };

  {
    let current = { ...draft };
    let reads = 0;
    const result = await runReleaseTransition({
      getRelease: async () => {
        reads += 1;
        if (reads >= 3) current = { ...immutable };
        return { ...current };
      },
      publishRelease: async () => {
        current = { ...mutable };
        throw new Error("response lost after server-side success");
      },
      rollbackRelease: async () => {
        throw new Error("rollback must not run");
      },
      verifySnapshot,
      pollDelayMs: 0,
      sleep: async () => {},
    });

    assert.equal(result.release.immutable, true);
    assert.match(
      JSON.stringify(result.state.history),
      /publish-transport-failed/,
    );
  }

  {
    let current = { ...draft };
    let pollReads = 0;
    const result = await runReleaseTransition({
      getRelease: async () => {
        if (current.draft) return { ...current };
        pollReads += 1;
        if (pollReads <= 2) throw new Error("temporary polling failure");
        return { ...immutable };
      },
      publishRelease: async () => {
        current = { ...mutable };
        return { ...current };
      },
      rollbackRelease: async () => {
        throw new Error("rollback must not run");
      },
      verifySnapshot,
      pollDelayMs: 0,
      sleep: async () => {},
    });
    assert.equal(result.release.immutable, true);
    assert.match(
      JSON.stringify(result.state.history),
      /poll-1-transport-failed/,
    );
  }

  {
    let current = { ...draft };
    let afterPublishReads = 0;
    await assert.rejects(
      () => runReleaseTransition({
        getRelease: async () => {
          if (current.draft) return { ...current };
          afterPublishReads += 1;
          if (afterPublishReads === 2) {
            throw new Error("initial rollback state read failed");
          }
          return { ...current };
        },
        publishRelease: async () => {
          current = { ...mutable };
          return { ...current };
        },
        rollbackRelease: async () => {
          current = { ...draft };
          throw new Error("rollback response lost");
        },
        verifySnapshot,
        maxPolls: 1,
        maxRollbackAttempts: 2,
        pollDelayMs: 0,
        sleep: async () => {},
      }),
      (error) => {
        assert.ok(error instanceof ReleaseTransitionError);
        assert.equal(error.code, "ROLLED_BACK");
        assert.match(
          JSON.stringify(error.state.history),
          /initial-read-transport-failed/,
        );
        return true;
      },
    );
  }
  {
    let firstRead = true;
    await assert.rejects(
      () => runReleaseTransition({
        getRelease: async () => {
          if (firstRead) {
            firstRead = false;
            return { ...draft };
          }
          throw new Error("release state unavailable");
        },
        publishRelease: async () => {
          throw new Error("ambiguous publish response");
        },
        rollbackRelease: async () => {
          throw new Error("ambiguous rollback response");
        },
        verifySnapshot,
        maxPolls: 1,
        maxRollbackAttempts: 2,
        pollDelayMs: 0,
        sleep: async () => {},
      }),
      (error) => {
        assert.equal(error.code, "INCIDENT");
        assert.match(error.message, /could not be proven/);
        return true;
      },
    );
  }
});

test("publication state machine rolls back mutable content drift", async () => {
  const baseRelease = {
    id: 77,
    tag_name: "brainstem-beta-v1.2.3",
    draft: true,
    immutable: false,
    body: "bound body",
    assets: [{
      id: 1,
      name: "asset.exe",
      state: "uploaded",
      size: 10,
      digest: `sha256:${"a".repeat(64)}`,
    }],
  };
  const expected = {
    tag: baseRelease.tag_name,
    tagObject: "b".repeat(40),
    commit: "c".repeat(40),
    releaseId: String(baseRelease.id),
    releaseFingerprint: releaseContentFingerprint(baseRelease),
  };
  let current = structuredClone(baseRelease);
  let published = false;
  await assert.rejects(
    () => runReleaseTransition({
      getRelease: async () => {
        if (published && current.draft === false) {
          return { ...current, body: "mutated after staging" };
        }
        return structuredClone(current);
      },
      publishRelease: async () => {
        published = true;
        current.draft = false;
        return structuredClone(current);
      },
      rollbackRelease: async () => {
        current = structuredClone(baseRelease);
        return structuredClone(current);
      },
      verifySnapshot: async (release) => {
        verifyReleaseSnapshot(expected, {
          tag: release.tag_name,
          tagObject: expected.tagObject,
          commit: expected.commit,
          releaseId: String(release.id),
          releaseFingerprint: releaseContentFingerprint(release),
        });
        return true;
      },
      maxPolls: 1,
      maxRollbackAttempts: 1,
      pollDelayMs: 0,
      sleep: async () => {},
    }),
    (error) => {
      assert.equal(error.code, "INTEGRITY_ROLLED_BACK");
      assert.equal(current.draft, true);
      return true;
    },
  );
});

test("integrity drift stays latched even if a later response is canonical immutable", async () => {
  const draft = { id: 1, draft: true, immutable: false };
  const mutable = { id: 1, draft: false, immutable: false };
  const immutable = { id: 1, draft: false, immutable: true };
  let phase = "draft";
  await assert.rejects(
    () => runReleaseTransition({
      getRelease: async () => {
        if (phase === "draft") return { ...draft };
        if (phase === "drift") {
          phase = "immutable";
          return { ...mutable, drifted: true };
        }
        return { ...immutable };
      },
      publishRelease: async () => {
        phase = "drift";
        return { ...mutable };
      },
      rollbackRelease: async () => ({ ...immutable }),
      verifySnapshot: async (release) => {
        if (release.drifted) throw new Error("fingerprint mismatch");
        return true;
      },
      maxPolls: 1,
      maxRollbackAttempts: 1,
      pollDelayMs: 0,
      sleep: async () => {},
    }),
    (error) => {
      assert.equal(error.code, "INCIDENT");
      assert.equal(error.state.integrityViolation, true);
      assert.match(error.state.integrityDetail, /fingerprint mismatch/);
      return true;
    },
  );
});

test("snapshot verification cannot be mutated into a no-op", async () => {
  let publishCalled = false;
  await assert.rejects(
    () => runReleaseTransition({
      getRelease: async () => ({ id: 1, draft: true, immutable: false }),
      publishRelease: async () => {
        publishCalled = true;
        return { id: 1, draft: false, immutable: false };
      },
      rollbackRelease: async () => ({ id: 1, draft: true, immutable: false }),
      verifySnapshot: async () => undefined,
      pollDelayMs: 0,
      sleep: async () => {},
    }),
    (error) => {
      assert.equal(error.code, "INTEGRITY");
      assert.match(error.message, /verifier did not return an explicit true proof/);
      return true;
    },
  );
  assert.equal(publishCalled, false);
});

test("signal recovery retries until release ID is proven draft or immutable", async () => {
  assert.equal(
    recoveryRequiredFromState({
      phase: "interrupted-recovery-started",
      transitionAttempted: true,
    }),
    true,
  );
  assert.equal(
    recoveryRequiredFromState({
      phase: "prepublication-failure",
      transitionAttempted: false,
    }),
    false,
  );

  let release = { id: 1, draft: false, immutable: false };
  let reads = 0;
  const draftRecovery = await recoverInterruptedRelease({
    getRelease: async () => {
      reads += 1;
      if (reads === 1) throw new Error("initial recovery GET unavailable");
      return { ...release };
    },
    rollbackRelease: async () => {
      release = { id: 1, draft: true, immutable: false };
      throw new Error("rollback response lost");
    },
    verifySnapshot: async () => true,
    maxAttempts: 2,
    pollDelayMs: 0,
    sleep: async () => {},
  });
  assert.equal(draftRecovery.status, "draft");
  assert.equal(draftRecovery.release.draft, true);

  const immutableRecovery = await recoverInterruptedRelease({
    getRelease: async () => ({ id: 1, draft: false, immutable: true }),
    rollbackRelease: async () => {
      throw new Error("rollback must not run for immutable release");
    },
    verifySnapshot: async () => true,
    maxAttempts: 1,
    pollDelayMs: 0,
    sleep: async () => {},
  });
  assert.equal(immutableRecovery.status, "immutable");

  const workflow = readFileSync(
    path.join(repositoryDir, ".github", "workflows", "frontier-binaries.yml"),
    "utf8",
  );
  const publish = workflowJob(workflow, "publish");
  assert.match(publish, /if: \$\{\{ failure\(\) \|\| cancelled\(\) \}\}/);
  assert.match(publish, /Recover interrupted mutable release transition/);
  assert.match(publish, /--recover-only/);
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
  const workflow = readFileSync(
    path.join(repositoryDir, ".github", "workflows", "frontier-binaries.yml"),
    "utf8",
  );
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
  const workflow = readFileSync(
    path.join(repositoryDir, ".github", "workflows", "frontier-binaries.yml"),
    "utf8",
  );
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
