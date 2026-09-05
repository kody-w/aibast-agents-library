import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync, statSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

import {
  analyzePackagedDownloads,
  parseReleaseManifestBlock,
  RELEASE_MANIFEST_SCHEMA,
  safeReleaseAssetUrl,
} from "../download-center.js";
import {
  loadWindowsSigningPolicy,
  validateWindowsSigningEvidence,
} from "./windows-signing-policy.mjs";

function fail(message) {
  throw new Error(message);
}

function sha256(filePath) {
  return createHash("sha256").update(readFileSync(filePath)).digest("hex");
}

function parseArguments(argv) {
  const supported = new Set([
    "release-json",
    "artifact-dir",
    "manifest",
    "tag",
    "version",
    "commit",
  ]);
  const values = {};
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const name = argument.startsWith("--") ? argument.slice(2) : "";
    const value = argv[index + 1];
    if (!supported.has(name)) fail(`Unsupported argument: ${argument}`);
    if (!value || value.startsWith("--")) fail(`Missing value for ${argument}.`);
    values[name] = value;
    index += 1;
  }
  for (const name of supported) {
    if (!values[name]) fail(`--${name} is required.`);
  }
  return values;
}

export function verifyStagedRelease({
  release,
  manifest,
  artifactDir,
  tag,
  version,
  commit,
  repository,
  serverUrl,
  windowsPolicy,
  windowsExpected,
}) {
  if (manifest.schema !== RELEASE_MANIFEST_SCHEMA) {
    fail(`Unsupported release manifest schema: ${manifest.schema}`);
  }
  if (
    release.tag_name !== tag
    || release.draft !== true
    || release.prerelease !== true
    || manifest.release?.tag !== tag
    || manifest.release?.version !== version
    || manifest.release?.commit !== commit
    || manifest.source?.repository !== repository
    || manifest.source?.commit !== commit
    || manifest.source?.ref !== `refs/tags/${tag}`
  ) {
    fail("Staged release identity does not match the exact tag and commit.");
  }

  const bodyBlock = parseReleaseManifestBlock(release.body);
  const bodyManifest = bodyBlock.manifest;
  assert.deepEqual(
    bodyManifest,
    manifest,
    "release body manifest differs from the signed manifest asset",
  );
  const manifestName =
    `RAPP-Brainstem-Frontier-${version}-binary-manifest.json`;
  const manifestPath = path.join(artifactDir, manifestName);
  const manifestBytes = readFileSync(manifestPath);
  const manifestAssets = release.assets.filter(
    (asset) => asset?.name === manifestName,
  );
  if (
    manifestAssets.length !== 1
    || manifestAssets[0].state !== "uploaded"
    || manifestAssets[0].size !== manifestBytes.length
    || String(manifestAssets[0].digest || "").toLowerCase()
      !== `sha256:${sha256(manifestPath)}`
    || !safeReleaseAssetUrl(
      manifestAssets[0].browser_download_url,
      repository,
      tag,
      manifestName,
    )
    || manifestBytes.toString("utf8") !== `${bodyBlock.source}\n`
  ) {
    fail("Signed manifest asset metadata, digest, URL, or body bytes differ.");
  }
  const pageAnalysis = analyzePackagedDownloads({
    ...release,
    immutable: true,
  }, {
    repository,
    commit,
    version,
    manifest: bodyManifest,
  });
  if (pageAnalysis.downloads.length !== 3) {
    fail(`Download Center accepted ${pageAnalysis.downloads.length}, expected 3.`);
  }

  if (
    manifest.application_id !== "com.microsoft.aibast.rapp-brainstem-beta"
    || manifest.toolchain?.electron !== "43.4.1"
    || manifest.toolchain?.electron_builder !== "26.15.7"
    || manifest.publication_policy?.allow_unlisted_binary_assets !== false
    || manifest.publication_policy?.require_signed_manifest !== true
    || manifest.publication_policy?.require_runtime_service_gate !== true
    || manifest.publication_policy?.windows_arm64_allowed !== false
  ) {
    fail("Release manifest publication policy is incomplete.");
  }
  if (
    manifest.signing?.windows?.profile_type !== "PublicTrust"
    || manifest.signing?.windows?.file_digest !== "SHA256"
    || manifest.signing?.windows?.timestamp_digest !== "SHA256"
    || manifest.signing?.windows?.timestamp
      !== "http://timestamp.acs.microsoft.com/"
    || !/Microsoft/i.test(manifest.signing?.windows?.identity || "")
    || !manifest.signing?.windows?.backend_schema
  ) {
    fail("Windows signing manifest does not match production policy.");
  }
  validateWindowsSigningEvidence({
    backend_schema: manifest.signing.windows.backend_schema,
    endpoint: manifest.signing.windows.endpoint,
    account: manifest.signing.windows.account,
    certificate_profile: manifest.signing.windows.certificate_profile,
    identity: manifest.signing.windows.identity,
    profile_type: manifest.signing.windows.profile_type,
    file_digest: manifest.signing.windows.file_digest,
    timestamp_digest: manifest.signing.windows.timestamp_digest,
    timestamp_url: manifest.signing.windows.timestamp,
  }, windowsPolicy, windowsExpected);

  const releaseBase =
    `${serverUrl}/${repository}/releases/download/${encodeURIComponent(tag)}/`;
  if (
    manifest.manifest_url
      !== `${releaseBase}${encodeURIComponent(manifestName)}`
  ) {
    fail("Manifest URL is outside the selected release.");
  }
  if (
    manifest.source_fallback?.commit !== commit
    || manifest.source_fallback?.resolves_latest !== false
    || !manifest.source_fallback?.macos_linux?.installer_url?.includes(
      `/${commit}/beta/install.sh`,
    )
    || !manifest.source_fallback?.windows?.installer_url?.includes(
      `/${commit}/beta/install.cmd`,
    )
    || !manifest.source_fallback?.macos_linux?.command?.includes(commit)
    || !manifest.source_fallback?.windows?.command?.includes(commit)
    || /latest/i.test(manifest.source_fallback?.macos_linux?.command || "")
    || /latest/i.test(manifest.source_fallback?.windows?.command || "")
  ) {
    fail("Source fallback is not pinned to the displayed release commit.");
  }

  const expected = new Map([
    [`RAPP-Brainstem-Frontier-${version}-macos-arm64.dmg`, ["macos", "arm64"]],
    [`RAPP-Brainstem-Frontier-${version}-macos-x64.dmg`, ["macos", "x64"]],
    [`RAPP-Brainstem-Frontier-${version}-windows-x64-setup.exe`, ["windows", "x64"]],
  ]);
  for (const artifact of manifest.artifacts) {
    const tuple = expected.get(artifact.filename);
    if (
      !tuple
      || artifact.platform !== tuple[0]
      || artifact.architecture !== tuple[1]
    ) {
      fail(`Unexpected manifest artifact: ${artifact.filename}`);
    }
    expected.delete(artifact.filename);

    const binaryPath = path.join(artifactDir, artifact.filename);
    const reportName = `${artifact.filename}.gate.json`;
    const reportPath = path.join(artifactDir, reportName);
    const bundleName = `${artifact.filename}.sigstore.json`;
    if (
      statSync(binaryPath).size !== artifact.size
      || sha256(binaryPath) !== artifact.sha256
      || artifact.download_url
        !== `${releaseBase}${encodeURIComponent(artifact.filename)}`
      || artifact.gate?.report?.name !== reportName
      || artifact.gate?.report?.size !== statSync(reportPath).size
      || artifact.gate?.report?.sha256 !== sha256(reportPath)
      || artifact.provenance?.sigstore_bundle !== bundleName
      || artifact.provenance?.url
        !== `${releaseBase}${encodeURIComponent(bundleName)}`
    ) {
      fail(`Artifact evidence mismatch: ${artifact.filename}`);
    }

    const report = JSON.parse(readFileSync(reportPath, "utf8"));
    if (
      artifact.signing?.status !== "verified"
      || artifact.signing?.verified !== true
      || artifact.runtime?.compatible !== true
      || artifact.runtime?.version !== version
      || artifact.runtime?.commit !== commit
      || artifact.gate?.status !== "passed"
      || artifact.gate?.commit !== commit
      || report.gate?.status !== "passed"
      || report.runtime?.service_ready !== true
      || report.runtime?.service_stopped !== true
      || report.runtime?.isolated_home !== true
      || report.runtime?.copilot_auth_startup !== true
      || report.bootstrap?.executed !== true
      || report.bootstrap?.authority_mode !== "canonical-release"
      || report.bootstrap?.installed_commit !== commit
      || report.bootstrap?.release_tag !== tag
      || report.bootstrap?.manifest?.mode !== "release"
      || report.bootstrap?.manifest?.repositoryUrl
        !== "https://github.com/microsoft/aibast-agents-library.git"
      || report.bootstrap?.manifest?.commit !== commit
      || report.bootstrap?.manifest?.sourceRef !== tag
      || report.bootstrap?.manifest?.authority?.requestedMode !== "release"
      || report.bootstrap?.manifest?.authority?.releaseTag !== tag
      || report.bootstrap?.manifest?.publication?.ready !== true
      || report.signing?.verified !== true
      || report.signing?.identity !== artifact.signing.identity
      || report.publication?.status !== "ready"
      || report.publication?.blockers?.length
      || report.native_media?.publication_ready !== true
      || report.runtime_compatibility?.source_checkout_updater_compatible
        !== false
    ) {
      fail(`Unsafe package-gate evidence: ${artifact.filename}`);
    }
    if (
      artifact.platform === "windows"
      && report.execution?.windows_standard_user !== true
    ) {
      fail("Windows package was not gated as a standard user.");
    }
    if (
      artifact.platform === "windows"
      && (
        report.execution?.windows_lifecycle?.passed !== true
        || report.execution.windows_lifecycle.per_user_registry_only !== true
        || report.execution.windows_lifecycle.machine_registry_entries !== 0
        || report.execution.windows_lifecycle.reinstall_single_entry !== true
        || report.execution.windows_lifecycle.installed_files_removed !== true
        || report.execution.windows_lifecycle.registry_and_shortcuts_removed
          !== true
        || report.execution.windows_lifecycle.shared_brainstem_preserved !== true
        || report.execution.windows_lifecycle.user_data_preserved !== true
        || report.execution.windows_lifecycle.source_migration_safe !== true
        || report.execution?.windows_upgrade?.passed !== true
        || !["first-binary-release", "n-minus-one-to-n"].includes(
          report.execution.windows_upgrade.mode,
        )
      )
    ) {
      fail("Windows package lifecycle or N-1 upgrade evidence is incomplete.");
    }
    if (artifact.platform === "windows") {
      validateWindowsSigningEvidence(
        report.signing,
        windowsPolicy,
        windowsExpected,
      );
    }
    if (
      artifact.platform === "macos"
      && (
        report.notarization?.app?.submission?.status !== "Accepted"
        || report.notarization?.app?.log?.status !== "Accepted"
        || !Array.isArray(report.notarization?.app?.log?.issues)
        || report.notarization.app.log.issues.length !== 0
        || report.notarization?.app?.stapled !== true
        || report.notarization?.app?.target?.code_signature?.ad_hoc !== false
        || !report.notarization?.app?.target?.code_signature?.timestamp
        || report.notarization?.dmg?.submission?.status !== "Accepted"
        || report.notarization?.dmg?.log?.status !== "Accepted"
        || !Array.isArray(report.notarization?.dmg?.log?.issues)
        || report.notarization.dmg.log.issues.length !== 0
        || report.notarization?.dmg?.stapled !== true
        || report.notarization?.dmg?.target?.code_signature?.ad_hoc !== false
        || !report.notarization?.dmg?.target?.code_signature?.timestamp
      )
    ) {
      fail(`Notarization evidence mismatch: ${artifact.filename}`);
    }
    if (artifact.platform === "windows") {
      const sbomPath = path.join(artifactDir, `${artifact.filename}.spdx.json`);
      const sbom = JSON.parse(readFileSync(sbomPath, "utf8"));
      if (
        artifact.sbom?.name !== path.basename(sbomPath)
        || artifact.sbom?.size !== statSync(sbomPath).size
        || artifact.sbom?.sha256 !== sha256(sbomPath)
        || artifact.sbom?.spdx_version !== "SPDX-2.3"
        || sbom.spdxVersion !== "SPDX-2.3"
        || !Array.isArray(sbom.packages)
        || sbom.packages.length === 0
      ) {
        fail("Windows SPDX SBOM evidence is invalid.");
      }
    } else if (artifact.sbom) {
      fail(`Unexpected SBOM on ${artifact.filename}.`);
    }
  }
  if (expected.size) {
    fail(`Missing allowlisted artifacts: ${[...expected.keys()].join(", ")}`);
  }
  return pageAnalysis;
}

export function verifyStagedReleaseFiles(argv = process.argv.slice(2)) {
  const args = parseArguments(argv);
  const manifestPath = path.resolve(args.manifest);
  const windowsPolicy = loadWindowsSigningPolicy();
  const windowsExpected = {
    endpoint: process.env.AZURE_ARTIFACT_SIGNING_ENDPOINT,
    account: process.env.AZURE_ARTIFACT_SIGNING_ACCOUNT_NAME,
    certificateProfile:
      process.env.AZURE_ARTIFACT_SIGNING_CERTIFICATE_PROFILE_NAME,
    publisherSubject: process.env.WINDOWS_SIGNING_SUBJECT,
    profileType: process.env.AZURE_ARTIFACT_SIGNING_PROFILE_TYPE,
  };
  return verifyStagedRelease({
    release: JSON.parse(readFileSync(path.resolve(args["release-json"]), "utf8")),
    manifest: JSON.parse(readFileSync(manifestPath, "utf8")),
    manifestPath,
    artifactDir: path.resolve(args["artifact-dir"]),
    tag: args.tag,
    version: args.version,
    commit: args.commit,
    repository: process.env.GITHUB_REPOSITORY,
    serverUrl: process.env.GITHUB_SERVER_URL,
    windowsPolicy,
    windowsExpected,
  });
}

if (
  process.argv[1]
  && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  try {
    const result = verifyStagedReleaseFiles();
    process.stdout.write(
      `Verified ${result.downloads.length} Download Center release artifacts.\n`,
    );
  } catch (error) {
    process.stderr.write(
      `Staged release verification failed: ${String(error.stack || error)}\n`,
    );
    process.exit(1);
  }
}
