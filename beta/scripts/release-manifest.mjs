import { createHash } from "node:crypto";
import { existsSync, readFileSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

import {
  artifactName,
  publisherMatchesApplicationId,
} from "./package-contract.mjs";

const betaDir = path.resolve(import.meta.dirname, "..");
export const RELEASE_MANIFEST_SCHEMA =
  "rapp-brainstem-frontier-release-manifest/v1";
export const RELEASE_MANIFEST_FENCE = "rapp-frontier-release-manifest";

function fail(message) {
  throw new Error(message);
}

function requiredEnvironment(name) {
  const value = String(process.env[name] || "").trim();
  if (!value) fail(`${name} is required.`);
  return value;
}

function sha256(filePath) {
  return createHash("sha256").update(readFileSync(filePath)).digest("hex");
}

function releaseDownloadUrl(serverUrl, repository, tag, name) {
  return `${serverUrl}/${repository}/releases/download/${encodeURIComponent(
    tag,
  )}/${encodeURIComponent(name)}`;
}

function sourceFallback(serverUrl, repository, commit) {
  const repositoryUrl = `${serverUrl}/${repository}.git`;
  const rawBase = `https://raw.githubusercontent.com/${repository}/${commit}/beta`;
  const unixUrl = `${rawBase}/install.sh`;
  const windowsUrl = `${rawBase}/install.cmd`;
  return {
    commit,
    resolves_latest: false,
    repository_url: repositoryUrl,
    macos_linux: {
      installer_url: unixUrl,
      command:
        `BRAINSTEM_BETA_COMMIT='${commit}' `
        + `BRAINSTEM_BETA_REPO_URL='${repositoryUrl}' `
        + `bash -c 'curl -fsSL \"${unixUrl}\" | bash'`,
    },
    windows: {
      installer_url: windowsUrl,
      command:
        `$env:BRAINSTEM_BETA_COMMIT='${commit}'; `
        + `$env:BRAINSTEM_BETA_REPO_URL='${repositoryUrl}'; `
        + `$file=Join-Path $PWD 'rapp-frontier-${commit}.cmd'; `
        + `Invoke-WebRequest '${windowsUrl}' -OutFile $file -UseBasicParsing; `
        + `& cmd.exe /d /c $file`,
    },
  };
}

export function parseChecksums(text) {
  const entries = [];
  for (const line of text.split(/\r?\n/)) {
    if (!line.trim()) continue;
    const match = /^([0-9a-f]{64}) [ *](.+)$/i.exec(line);
    if (!match) fail(`Invalid SHA256SUMS line: ${line}`);
    const name = path.basename(match[2]);
    if (name !== match[2]) fail(`Checksum paths must be basenames: ${match[2]}`);
    entries.push({ name, sha256: match[1].toLowerCase() });
  }
  if (!entries.length) fail("SHA256SUMS contains no entries.");
  const names = new Set(entries.map((entry) => entry.name));
  if (names.size !== entries.length) fail("SHA256SUMS contains duplicate filenames.");
  return entries.sort((left, right) => left.name.localeCompare(right.name));
}

function expectedMatrix(version) {
  return [
    {
      name: artifactName({
        platform: "macos",
        arch: "arm64",
        version,
        mode: "signed",
      }),
      os: "macos",
      arch: "arm64",
      minimumVersion: "12.0",
    },
    {
      name: artifactName({
        platform: "macos",
        arch: "x64",
        version,
        mode: "signed",
      }),
      os: "macos",
      arch: "x64",
      minimumVersion: "12.0",
    },
    {
      name: artifactName({
        platform: "windows",
        arch: "x64",
        version,
        mode: "signed",
      }),
      os: "windows",
      arch: "x64",
      minimumVersion: "11",
    },
  ].sort((left, right) => left.name.localeCompare(right.name));
}

function validateGateReport(
  report,
  expected,
  checksum,
  assetSize,
  signingIdentity,
  appleTeamId,
  electronVersion,
) {
  if (
    report?.schema !==
    "https://github.com/microsoft/aibast-agents-library/frontier-package-gate/v1"
  ) {
    fail(`${expected.name} has an unsupported gate report schema.`);
  }
  if (
    report.artifact?.name !== expected.name ||
    report.artifact?.sha256 !== checksum ||
    report.artifact?.size !== assetSize ||
    !Number.isSafeInteger(report.artifact?.size) ||
    report.artifact.size < 1 ||
    report.artifact?.os !== expected.os ||
    report.artifact?.arch !== expected.arch ||
    report.artifact?.signing_mode !== "signed"
  ) {
    fail(`${expected.name} gate report does not describe the exact signed artifact.`);
  }
  if (report.source?.application_id !== expected.applicationId) {
    fail(`${expected.name} application ID is not bound to its gate report.`);
  }
  if (
    report.gate?.status !== "passed" ||
    !Number.isInteger(report.gate?.total) ||
    report.gate.total < 1 ||
    report.gate.passed !== report.gate.total ||
    report.gate.failures?.length
  ) {
    fail(`${expected.name} did not pass every package gate.`);
  }
  const signingProvider =
    expected.os === "macos" ? "Apple Developer ID" : "Azure Artifact Signing";
  if (
    report.signing?.verified !== true ||
    report.signing?.identity !== signingIdentity ||
    report.signing?.provider !== signingProvider
  ) {
    fail(`${expected.name} signing identity was not verified.`);
  }
  if (
    report.runtime?.service_ready !== true ||
    report.runtime?.service_stopped !== true ||
    report.runtime?.isolated_home !== true ||
    report.runtime?.copilot_auth_startup !== true ||
    !["ready", "signed-out"].includes(report.runtime?.copilot_phase)
  ) {
    fail(`${expected.name} did not prove isolated Brainstem service readiness.`);
  }
  if (
    expected.os === "windows" &&
    report.execution?.windows_standard_user !== true
  ) {
    fail(`${expected.name} was not installed and run as a standard Windows user.`);
  }
  if (
    report.bootstrap?.executed !== true ||
    report.bootstrap?.authority_mode !== "canonical-release" ||
    !/^[0-9a-f]{40}$/i.test(report.bootstrap?.installed_commit || "") ||
    !report.bootstrap?.release_tag ||
    report.bootstrap?.manifest?.mode !== "release" ||
    report.bootstrap?.manifest?.repositoryUrl !==
      "https://github.com/microsoft/aibast-agents-library.git" ||
    report.bootstrap?.manifest?.commit !==
      report.bootstrap?.installed_commit ||
    report.bootstrap?.manifest?.sourceRef !==
      report.bootstrap?.release_tag ||
    report.bootstrap?.manifest?.authority?.requestedMode !== "release" ||
    report.bootstrap?.manifest?.authority?.releaseTag !==
      report.bootstrap?.release_tag ||
    report.bootstrap?.manifest?.publication?.ready !== true
  ) {
    fail(`${expected.name} did not pass the canonical package bootstrap gate.`);
  }
  if (
    report.publication?.status !== "ready" ||
    report.publication?.blockers?.length ||
    report.native_media?.publication_ready !== true ||
    report.native_media?.components?.length !== 2 ||
    report.native_media.components.some(
      (component) =>
        component.publication_ready !== true ||
        !component.sha256 ||
        component.size < 1 ||
        !component.approved_provenance?.source_url ||
        component.approved_provenance?.redistributable !== true,
    )
  ) {
    fail(`${expected.name} native media is not approved for redistribution.`);
  }
  const installationMethod =
    expected.os === "macos" ? "dmg-mount-and-ditto" : "nsis-silent-install";
  if (report.installation?.method !== installationMethod) {
    fail(`${expected.name} was not installed through its platform package.`);
  }
  if (
    expected.os === "macos" &&
    (
      report.notarization?.app?.submission?.status !== "Accepted" ||
      report.notarization?.app?.log?.status !== "Accepted" ||
      report.notarization?.app?.stapled !== true ||
      report.notarization?.app?.target?.code_signature?.ad_hoc !== false ||
      !report.notarization?.app?.target?.code_signature?.timestamp ||
      report.notarization?.app?.target?.code_signature?.team_id !==
        appleTeamId ||
      report.notarization?.dmg?.submission?.status !== "Accepted" ||
      report.notarization?.dmg?.log?.status !== "Accepted" ||
      report.notarization?.dmg?.stapled !== true ||
      report.notarization?.dmg?.target?.code_signature?.ad_hoc !== false ||
      !report.notarization?.dmg?.target?.code_signature?.timestamp
    )
  ) {
    fail(`${expected.name} lacks Accepted app and DMG notarization evidence.`);
  }
  const compatibility = report.runtime_compatibility;
  const operatingSystemName = expected.os === "macos" ? "macOS" : "Windows";
  if (
    compatibility?.operating_system?.name !== operatingSystemName ||
    compatibility?.operating_system?.minimum_version !== expected.minimumVersion ||
    compatibility?.architecture !== expected.arch ||
    compatibility?.electron !== electronVersion ||
    !compatibility?.node_engine ||
    !compatibility?.native_dependencies?.ffmpeg_static ||
    !compatibility?.native_dependencies?.ffprobe_installer ||
    !compatibility?.native_dependencies?.copilot_sdk ||
    compatibility?.brainstem?.python !== "3.11" ||
    compatibility?.brainstem?.protocol !== "RAPP/1" ||
    !compatibility?.brainstem?.version ||
    compatibility?.update_channel !== "binary-release-manifest-v1" ||
    compatibility?.source_checkout_updater_compatible !== false
  ) {
    fail(`${expected.name} runtime compatibility is incomplete or unsafe.`);
  }
}

export function createReleaseManifest(metadata, checksums, bundles, reports) {
  if (!/^\d+\.\d+\.\d+-beta\.\d+$/.test(metadata.version)) {
    fail(`Invalid Frontier release version: ${metadata.version}`);
  }
  if (metadata.tag !== `brainstem-beta-v${metadata.version}`) {
    fail(`Release tag does not match version: ${metadata.tag}`);
  }
  const expectedManifestName =
    `RAPP-Brainstem-Frontier-${metadata.version}-binary-manifest.json`;
  if (metadata.manifestName !== expectedManifestName) {
    fail(`Binary manifest name must be ${expectedManifestName}.`);
  }
  if (!/^[0-9a-f]{40}$/i.test(metadata.commit)) {
    fail("Release manifest requires a full 40-character commit.");
  }
  if (
    metadata.electronVersion !== "43.4.1" ||
    metadata.electronBuilderVersion !== "26.15.7"
  ) {
    fail("Release manifest requires the tested Electron 43 and builder patches.");
  }
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(metadata.repository)) {
    fail("Release manifest requires an owner/repository slug.");
  }
  const serverUrl = new URL(metadata.serverUrl);
  if (
    serverUrl.protocol !== "https:" ||
    serverUrl.origin !== "https://github.com" ||
    serverUrl.pathname !== "/"
  ) {
    fail("Release manifest requires the public https://github.com server URL.");
  }
  const normalizedServerUrl = serverUrl.origin;
  if (!metadata.macosIdentity.startsWith("Developer ID Application:")) {
    fail("Release manifest requires a Developer ID Application identity.");
  }
  if (
    !publisherMatchesApplicationId(
      metadata.applicationId,
      metadata.macosIdentity,
    ) ||
    !publisherMatchesApplicationId(
      metadata.applicationId,
      metadata.windowsSubject,
    )
  ) {
    fail("Release manifest publisher identities do not match the application ID.");
  }
  if (
    metadata.windowsProfileType !== "PublicTrust" ||
    metadata.windowsFileDigest !== "SHA256" ||
    metadata.windowsTimestampDigest !== "SHA256" ||
    metadata.windowsTimestampUrl !== "http://timestamp.acs.microsoft.com/" ||
    !metadata.windowsSigningBackendSchema
  ) {
    fail("Release manifest requires the approved Windows signing schema.");
  }
  if (!metadata.macosIdentity.includes(`(${metadata.appleTeamId})`)) {
    fail("Release manifest Apple identity and team do not match.");
  }
  const azureEndpoint = new URL(metadata.azureEndpoint);
  if (
    azureEndpoint.protocol !== "https:" ||
    !azureEndpoint.hostname.endsWith(".codesigning.azure.net")
  ) {
    fail("Release manifest has an invalid Artifact Signing endpoint.");
  }
  const gateRunUrl = new URL(metadata.gateRunUrl);
  const expectedGatePrefix =
    `/${metadata.repository.toLowerCase()}/actions/runs/`;
  if (
    gateRunUrl.protocol !== "https:" ||
    gateRunUrl.origin !== normalizedServerUrl ||
    !gateRunUrl.pathname.toLowerCase().startsWith(expectedGatePrefix) ||
    !/^[0-9]+$/.test(gateRunUrl.pathname.slice(expectedGatePrefix.length))
  ) {
    fail("Release manifest requires this repository's GitHub Actions run URL.");
  }

  const matrix = expectedMatrix(metadata.version);
  for (const entry of matrix) entry.applicationId = metadata.applicationId;
  const checksumNames = checksums.map((entry) => entry.name);
  if (new Set(checksumNames).size !== checksumNames.length) {
    fail("Release artifacts contain duplicate names.");
  }
  for (const entry of checksums) {
    if (!Number.isSafeInteger(entry.size) || entry.size < 1) {
      fail(`${entry.name} must have a positive byte size.`);
    }
  }
  const actualArtifacts = checksums.map((entry) => entry.name).sort();
  const expectedArtifacts = matrix.map((entry) => entry.name);
  if (JSON.stringify(actualArtifacts) !== JSON.stringify(expectedArtifacts)) {
    fail(
      `Release artifacts differ from the required matrix. Expected ${expectedArtifacts.join(
        ", ",
      )}; received ${actualArtifacts.join(", ")}.`,
    );
  }

  const checksumByName = Object.fromEntries(
    checksums.map((entry) => [entry.name, entry]),
  );
  const expectedSbomName =
    `RAPP-Brainstem-Frontier-${metadata.version}-windows-x64-setup.exe.spdx.json`;
  if (
    metadata.windowsSbom?.name !== expectedSbomName ||
    !Number.isSafeInteger(metadata.windowsSbom?.size) ||
    metadata.windowsSbom.size < 1 ||
    !/^[0-9a-f]{64}$/i.test(metadata.windowsSbom?.sha256 || "") ||
    metadata.windowsSbom?.spdx_version !== "SPDX-2.3"
  ) {
    fail("Release manifest requires a nonempty Windows SPDX-2.3 SBOM.");
  }
  const artifacts = matrix.map((expected) => {
    const bundle = bundles[expected.name];
    const report = reports[expected.name];
    if (!bundle) fail(`Missing Sigstore bundle for ${expected.name}.`);
    if (!report) fail(`Missing package-gate report for ${expected.name}.`);
    if (
      report.content.bootstrap?.installed_commit !== metadata.commit ||
      report.content.bootstrap?.manifest?.commit !== metadata.commit ||
      report.content.bootstrap?.release_tag !== metadata.tag ||
      report.content.bootstrap?.manifest?.sourceRef !== metadata.tag
    ) {
      fail(`${expected.name} package bootstrap is not bound to the release commit.`);
    }
    if (!Number.isSafeInteger(bundle.size) || bundle.size < 1) {
      fail(`${bundle.name || expected.name} Sigstore bundle is empty.`);
    }
    if (!Number.isSafeInteger(report.size) || report.size < 1) {
      fail(`${report.name || expected.name} package-gate report is empty.`);
    }
    const signingIdentity =
      expected.os === "macos"
        ? metadata.macosIdentity
        : metadata.windowsSubject;
    if (
      expected.os === "windows" &&
      (
        report.content.signing?.backend_schema !==
          metadata.windowsSigningBackendSchema ||
        report.content.signing?.endpoint !== metadata.azureEndpoint ||
        report.content.signing?.account !== metadata.azureAccount ||
        report.content.signing?.certificate_profile !== metadata.azureProfile ||
        report.content.signing?.profile_type !== metadata.windowsProfileType ||
        report.content.signing?.file_digest !== metadata.windowsFileDigest ||
        report.content.signing?.timestamp_digest !==
          metadata.windowsTimestampDigest ||
        report.content.signing?.timestamp_url !== metadata.windowsTimestampUrl
      )
    ) {
      fail(`${expected.name} Windows signing configuration is not approved.`);
    }
    validateGateReport(
      report.content,
      expected,
      checksumByName[expected.name].sha256,
      checksumByName[expected.name].size,
      signingIdentity,
      metadata.appleTeamId,
      metadata.electronVersion,
    );
    const downloadUrl = releaseDownloadUrl(
      normalizedServerUrl,
      metadata.repository,
      metadata.tag,
      expected.name,
    );
    return {
      filename: expected.name,
      platform: expected.os,
      architecture: expected.arch,
      size: checksumByName[expected.name].size,
      sha256: checksumByName[expected.name].sha256,
      download_url: downloadUrl,
      signing: {
        status: "verified",
        provider: report.content.signing.provider,
        identity: signingIdentity,
        verified: true,
      },
      runtime: {
        compatible: true,
        version: metadata.version,
        commit: metadata.commit,
        node: report.content.runtime_compatibility.node_engine,
        electron: report.content.runtime_compatibility.electron,
        details: report.content.runtime_compatibility,
      },
      native_media: report.content.native_media,
      ...(expected.os === "windows"
        ? {
            sbom: {
              ...metadata.windowsSbom,
              url: releaseDownloadUrl(
                normalizedServerUrl,
                metadata.repository,
                metadata.tag,
                metadata.windowsSbom.name,
              ),
            },
          }
        : {}),
      gate: {
        status: "passed",
        name: `frontier-package-gate-${expected.os}-${expected.arch}`,
        commit: metadata.commit,
        run_url: gateRunUrl.href,
        passed: report.content.gate.passed,
        total: report.content.gate.total,
        report: {
          name: report.name,
          size: report.size,
          sha256: report.sha256,
          url: releaseDownloadUrl(
            normalizedServerUrl,
            metadata.repository,
            metadata.tag,
            report.name,
          ),
        },
      },
      provenance: {
        sigstore_bundle: bundle.name,
        url: releaseDownloadUrl(
          normalizedServerUrl,
          metadata.repository,
          metadata.tag,
          bundle.name,
        ),
      },
    };
  });

  const manifestUrl = releaseDownloadUrl(
    normalizedServerUrl,
    metadata.repository,
    metadata.tag,
    metadata.manifestName,
  );

  return {
    schema: RELEASE_MANIFEST_SCHEMA,
    product: "RAPP Brainstem Frontier",
    application_id: metadata.applicationId,
    release: {
      tag: metadata.tag,
      version: metadata.version,
      commit: metadata.commit,
      url: `${normalizedServerUrl}/${metadata.repository}/releases/tag/${encodeURIComponent(
        metadata.tag,
      )}`,
      immutable_after_publication: true,
    },
    source: {
      repository: metadata.repository,
      commit: metadata.commit,
      ref: `refs/tags/${metadata.tag}`,
    },
    publication_policy: {
      allow_unlisted_binary_assets: false,
      require_sha256: true,
      require_signed_manifest: true,
      require_verified_platform_signature: true,
      require_runtime_service_gate: true,
      page_discovery_requires_this_manifest: true,
      windows_arm64_allowed: false,
      windows_arm64_requires: [
        "native ffmpeg ARM64 package gate",
        "native ffprobe ARM64 package gate",
      ],
    },
    toolchain: {
      electron: metadata.electronVersion,
      electron_builder: metadata.electronBuilderVersion,
    },
    signing: {
      macos: {
        identity: metadata.macosIdentity,
        team_id: metadata.appleTeamId,
      },
      windows: {
        service: "Azure Artifact Signing",
        endpoint: metadata.azureEndpoint,
        account: metadata.azureAccount,
        certificate_profile: metadata.azureProfile,
        profile_type: metadata.windowsProfileType,
        identity: metadata.windowsSubject,
        backend_schema: metadata.windowsSigningBackendSchema,
        file_digest: metadata.windowsFileDigest,
        timestamp_digest: metadata.windowsTimestampDigest,
        timestamp: metadata.windowsTimestampUrl,
      },
    },
    integrity: {
      hash_file: "SHA256SUMS",
      hash_url: releaseDownloadUrl(
        normalizedServerUrl,
        metadata.repository,
        metadata.tag,
        "SHA256SUMS",
      ),
      sigstore_bundle: `${metadata.manifestName}.sigstore.json`,
      sigstore_bundle_url: `${manifestUrl}.sigstore.json`,
    },
    manifest_url: manifestUrl,
    source_fallback: sourceFallback(
      normalizedServerUrl,
      metadata.repository,
      metadata.commit,
    ),
    artifacts,
  };
}

function parseArguments(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (!argument.startsWith("--")) fail(`Unexpected argument: ${argument}`);
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) fail(`Missing value for ${argument}.`);
    const name = argument.slice(2);
    if (!["artifact-dir", "checksums", "output"].includes(name)) {
      fail(`Unsupported argument: ${argument}.`);
    }
    if (Object.hasOwn(values, name)) fail(`Duplicate argument: ${argument}.`);
    values[name] = value;
    index += 1;
  }
  for (const name of ["artifact-dir", "checksums", "output"]) {
    if (!values[name]) fail(`--${name} is required.`);
  }
  return values;
}

export function writeReleaseManifest(argv = process.argv.slice(2)) {
  const args = parseArguments(argv);
  const artifactDir = path.resolve(args["artifact-dir"]);
  const checksumsPath = path.resolve(args.checksums);
  const outputPath = path.resolve(args.output);
  const checksums = parseChecksums(readFileSync(checksumsPath, "utf8")).map(
    (entry) => {
      const artifactPath = path.join(artifactDir, entry.name);
      if (!existsSync(artifactPath)) fail(`Missing release artifact: ${artifactPath}`);
      const size = statSync(artifactPath).size;
      if (size < 1) fail(`Release artifact is empty: ${artifactPath}`);
      if (sha256(artifactPath) !== entry.sha256) {
        fail(`Release artifact checksum mismatch: ${artifactPath}`);
      }
      return { ...entry, size };
    },
  );
  const bundles = {};
  const reports = {};
  const packageMetadata = JSON.parse(
    readFileSync(path.join(betaDir, "package.json"), "utf8"),
  );
  const packageLock = JSON.parse(
    readFileSync(path.join(betaDir, "package-lock.json"), "utf8"),
  );
  for (const entry of checksums) {
    const bundleName = `${entry.name}.sigstore.json`;
    const bundlePath = path.join(artifactDir, bundleName);
    if (!existsSync(bundlePath)) fail(`Missing Sigstore bundle: ${bundlePath}`);
    const bundleSize = statSync(bundlePath).size;
    if (bundleSize < 1) fail(`Sigstore bundle is empty: ${bundlePath}`);
    bundles[entry.name] = { name: bundleName, size: bundleSize };

    const reportName = `${entry.name}.gate.json`;
    const reportPath = path.join(artifactDir, reportName);
    if (!existsSync(reportPath)) fail(`Missing package-gate report: ${reportPath}`);
    const reportSize = statSync(reportPath).size;
    if (reportSize < 1) fail(`Package-gate report is empty: ${reportPath}`);
    reports[entry.name] = {
      name: reportName,
      size: reportSize,
      sha256: sha256(reportPath),
      content: JSON.parse(readFileSync(reportPath, "utf8")),
    };
  }
  const windowsReport = Object.values(reports).find(
    (report) => report.content.artifact?.os === "windows",
  );
  if (!windowsReport) fail("Windows package-gate report is missing.");
  const windowsSigning = windowsReport.content.signing;
  const windowsSbomName =
    `RAPP-Brainstem-Frontier-${requiredEnvironment(
      "FRONTIER_RELEASE_VERSION",
    )}-windows-x64-setup.exe.spdx.json`;
  const windowsSbomPath = path.join(artifactDir, windowsSbomName);
  if (!existsSync(windowsSbomPath)) {
    fail(`Missing Windows SPDX SBOM: ${windowsSbomPath}`);
  }
  const windowsSbomSize = statSync(windowsSbomPath).size;
  if (windowsSbomSize < 1) fail(`Windows SPDX SBOM is empty: ${windowsSbomPath}`);
  const windowsSbomDocument = JSON.parse(
    readFileSync(windowsSbomPath, "utf8"),
  );
  if (
    windowsSbomDocument.spdxVersion !== "SPDX-2.3" ||
    !Array.isArray(windowsSbomDocument.packages) ||
    windowsSbomDocument.packages.length < 1
  ) {
    fail("Windows SPDX SBOM is not a valid SPDX-2.3 package document.");
  }

  const manifest = createReleaseManifest(
    {
      tag: requiredEnvironment("FRONTIER_RELEASE_TAG"),
      version: requiredEnvironment("FRONTIER_RELEASE_VERSION"),
      repository: requiredEnvironment("GITHUB_REPOSITORY"),
      serverUrl: requiredEnvironment("GITHUB_SERVER_URL"),
      commit: requiredEnvironment("FRONTIER_RELEASE_COMMIT"),
      manifestName: path.basename(outputPath),
      applicationId: packageMetadata.build.appId,
      electronVersion: packageLock.packages["node_modules/electron"].version,
      electronBuilderVersion:
        packageLock.packages["node_modules/electron-builder"].version,
      macosIdentity: requiredEnvironment("MACOS_SIGNING_IDENTITY"),
      appleTeamId: requiredEnvironment("APPLE_TEAM_ID"),
      azureEndpoint: windowsSigning.endpoint,
      azureAccount: windowsSigning.account,
      azureProfile: windowsSigning.certificate_profile,
      windowsSubject: windowsSigning.identity,
      windowsSigningBackendSchema: windowsSigning.backend_schema,
      windowsProfileType: windowsSigning.profile_type,
      windowsFileDigest: windowsSigning.file_digest,
      windowsTimestampDigest: windowsSigning.timestamp_digest,
      windowsTimestampUrl: windowsSigning.timestamp_url,
      windowsSbom: {
        name: windowsSbomName,
        size: windowsSbomSize,
        sha256: sha256(windowsSbomPath),
        spdx_version: windowsSbomDocument.spdxVersion,
      },
      gateRunUrl: requiredEnvironment("FRONTIER_GATE_RUN_URL"),
    },
    checksums,
    bundles,
    reports,
  );
  writeFileSync(outputPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  return outputPath;
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  try {
    process.stdout.write(`${writeReleaseManifest()}\n`);
  } catch (error) {
    process.stderr.write(`Release manifest failed: ${String(error.stack || error)}\n`);
    process.exit(1);
  }
}
