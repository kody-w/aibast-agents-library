import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";

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
    windowsSigningBackendSchema:
      "electron-builder-26.15.7/WindowsAzureSigningConfiguration-v26",
    windowsProfileType: "PublicTrust",
    windowsFileDigest: "SHA256",
    windowsTimestampDigest: "SHA256",
    windowsTimestampUrl: "http://timestamp.acs.microsoft.com/",
    gateRunUrl:
      "https://github.com/owner/repository/actions/runs/123456789",
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

test("Windows NSIS identity and production signing policy are frozen", () => {
  const packageMetadata = JSON.parse(
    readFileSync(path.join(betaDir, "package.json"), "utf8"),
  );
  const policy = JSON.parse(
    readFileSync(
      path.join(betaDir, "build", "windows-signing-policy.json"),
      "utf8",
    ),
  );
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
  assert.equal(
    packageMetadata.build.appId,
    "com.microsoft.aibast.rapp-brainstem-beta",
  );
  assert.equal(
    packageMetadata.build.nsis.guid,
    "48d3a204-a20a-516d-b74f-5ac374e1c8bb",
  );
  assert.equal(packageMetadata.build.nsis.perMachine, false);
  assert.equal(packageMetadata.build.nsis.runAfterFinish, false);
  assert.equal(packageMetadata.build.nsis.deleteAppDataOnUninstall, false);
  assert.equal(packageMetadata.build.nsis.warningsAsErrors, true);
  assert.equal(packageMetadata.build.win.requestedExecutionLevel, "asInvoker");
  assert.equal(policy.publication_enabled, false);
  assert.equal(policy.backend_approval, "blocked-deprecated-v26");
  assert.equal(policy.approved_backend_schema, null);
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
    "flipping only the Windows publication boolean must not approve v26",
  );
  assert.match(packaging, /entry\.endsWith\("\.blockmap"\)/);
  assert.match(packaging, /\^latest/);
  assert.match(packaging, /installers\.length !== 1/);
  assert.match(main, /app\.setAppUserModelId\(APP_ID\)/);
  assert.match(standardUserGate, /New-LocalUser/);
  assert.match(standardUserGate, /Add-LocalGroupMember/);
  assert.match(standardUserGate, /Start-Process[\s\S]*-Credential/);
  assert.match(standardUserGate, /Remove-LocalUser/);
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
  assert.equal(workflow.match(/id-token:\s+write/g)?.length, 3);
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

  const windows = workflowJob(workflow, "release-windows");
  const winInstall = windows.indexOf("npm ci --no-audit --no-fund");
  const winTests = windows.indexOf("npm test");
  const winMedia = windows.indexOf("native-media-preflight.mjs");
  const winClean = windows.indexOf("git diff --quiet");
  const azureLogin = windows.indexOf("azure/login@");
  const winBuild = windows.indexOf("Build and Artifact Sign native NSIS installer");
  const azureCleanup = windows.indexOf(
    "Clear Azure CLI session immediately after signing",
  );
  const winGate = windows.indexOf("Gate signed NSIS package");
  assert.ok(
    0 <= winInstall
      && winInstall < winTests
      && winTests < winMedia
      && winMedia < winClean
      && winClean < azureLogin
      && azureLogin < winBuild
      && winBuild < azureCleanup
      && azureCleanup < winGate,
  );
  assert.equal(windows.lastIndexOf("npm ci --no-audit --no-fund"), winInstall);
  assert.doesNotMatch(windows.slice(0, azureLogin), /AZURE_CLIENT_SECRET/);
  assert.match(windows, /az account clear/);
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
  const publishRelease = publish.indexOf(
    'gh release edit "$TAG" --draft=false',
  );
  assert.ok(
    0 <= download
      && download < count
      && count < checksums
      && checksums < attestations
      && attestations < staged
      && staged < immutableSetting
      && immutableSetting < publishRelease,
  );
  assert.match(publish, /RAPP-Brainstem-Frontier-\$\{VERSION\}-macos-arm64\.dmg/);
  assert.match(publish, /RAPP-Brainstem-Frontier-\$\{VERSION\}-macos-x64\.dmg/);
  assert.match(publish, /RAPP-Brainstem-Frontier-\$\{VERSION\}-windows-x64-setup\.exe/);
  assert.doesNotMatch(publish, /--draft=true/);
  assert.match(publish, /Immutable release incident/);
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
