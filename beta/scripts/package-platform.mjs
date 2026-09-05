import { existsSync, readFileSync, readdirSync, rmSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

import { Arch, Platform, build } from "electron-builder";

import {
  artifactName,
  publisherMatchesApplicationId,
} from "./package-contract.mjs";
import {
  evaluatePolicyReadiness,
  loadNativeMediaPolicy,
} from "./native-media-gate.mjs";
import { notarizeTarget } from "./notarize-target.mjs";
import { preparePackageBootstrap } from "./prepare-package-bootstrap.mjs";
import {
  evaluateToolchainPolicy,
  installedToolchain,
  loadToolchainPolicy,
} from "./toolchain-policy.mjs";
import {
  evaluateWindowsSigningPolicy,
  loadWindowsSigningPolicy,
} from "./windows-signing-policy.mjs";

export { evaluateWindowsSigningPolicy } from "./windows-signing-policy.mjs";


const betaDir = path.resolve(import.meta.dirname, "..");
const releaseDir = path.join(betaDir, "release");

function fail(message) {
  throw new Error(message);
}

function requiredEnvironment(name) {
  const value = String(process.env[name] || "").trim();
  if (!value) fail(`${name} is required for a signed package.`);
  return value;
}

export function parsePackagingArguments(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (!argument.startsWith("--")) fail(`Unexpected argument: ${argument}`);
    const name = argument.slice(2);
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) fail(`Missing value for --${name}.`);
    if (Object.hasOwn(values, name)) fail(`Duplicate argument: --${name}.`);
    values[name] = value;
    index += 1;
  }
  for (const name of Object.keys(values)) {
    if (!["platform", "arch"].includes(name)) {
      fail(`Unsupported argument: --${name}.`);
    }
  }
  const platform = values.platform;
  if (!["macos", "windows"].includes(platform)) {
    fail("--platform must be macos or windows.");
  }
  let arch = values.arch;
  if (arch === "native") arch = process.arch;
  if (platform === "macos" && !["x64", "arm64"].includes(arch)) {
    fail("macOS packaging supports exactly x64 or arm64.");
  }
  if (platform === "windows" && arch !== "x64") {
    fail("Windows packaging supports x64 only. ARM64 is intentionally blocked.");
  }
  return { platform, arch };
}

function builderArtifactPattern({ platform, mode }) {
  const qualifier = mode === "unsigned" ? "-unsigned" : "";
  if (platform === "macos") {
    return `RAPP-Brainstem-Frontier-\${version}-macos-\${arch}${qualifier}.\${ext}`;
  }
  return `RAPP-Brainstem-Frontier-\${version}-windows-\${arch}-setup${qualifier}.\${ext}`;
}

function appOutputDirectory(platform, arch) {
  if (platform === "windows") return path.join(releaseDir, "win-unpacked");
  return path.join(releaseDir, arch === "arm64" ? "mac-arm64" : "mac");
}

function assertNativeHost(platform, arch) {
  const expectedPlatform = platform === "macos" ? "darwin" : "win32";
  if (process.platform !== expectedPlatform) {
    fail(`${platform} packages must be built on ${expectedPlatform}; host is ${process.platform}.`);
  }
  if (process.arch !== arch) {
    fail(
      `${platform} ${arch} packages must be built on a native ${arch} runner; host is ${process.arch}.`,
    );
  }
}

function signingMode() {
  const mode = String(process.env.FRONTIER_SIGNING_MODE || "unsigned").trim();
  if (!["signed", "unsigned"].includes(mode)) {
    fail("FRONTIER_SIGNING_MODE must be signed or unsigned.");
  }
  return mode;
}

function macSigningConfiguration(mode, applicationId) {
  if (mode === "unsigned") {
    process.env.CSC_IDENTITY_AUTO_DISCOVERY = "false";
    return {
      identity: null,
      notarize: false,
    };
  }

  const identity = requiredEnvironment("MACOS_SIGNING_IDENTITY");
  const teamId = requiredEnvironment("APPLE_TEAM_ID");
  const keychain = requiredEnvironment("CSC_KEYCHAIN");
  const appleApiKey = requiredEnvironment("APPLE_API_KEY");
  const appleApiKeyId = requiredEnvironment("APPLE_API_KEY_ID");
  const appleApiIssuer = requiredEnvironment("APPLE_API_ISSUER");
  if (!existsSync(appleApiKey)) {
    fail(`APPLE_API_KEY does not exist: ${appleApiKey}`);
  }
  if (!existsSync(keychain)) {
    fail(`CSC_KEYCHAIN does not exist: ${keychain}`);
  }
  if (process.env.CSC_LINK || process.env.CSC_KEY_PASSWORD) {
    fail(
      "CSC_LINK and CSC_KEY_PASSWORD must be removed after certificate import "
      + "and before packaging.",
    );
  }
  if (!identity.startsWith("Developer ID Application:")) {
    fail("MACOS_SIGNING_IDENTITY must be a Developer ID Application identity.");
  }
  if (!publisherMatchesApplicationId(applicationId, identity)) {
    fail(`${identity} cannot sign application ID ${applicationId}.`);
  }
  if (!/^[A-Z0-9]{10}$/.test(teamId)) {
    fail("APPLE_TEAM_ID must be a 10-character Apple Team ID.");
  }
  if (!/^[A-Z0-9]{10}$/.test(appleApiKeyId)) {
    fail("APPLE_API_KEY_ID must be a 10-character App Store Connect key ID.");
  }
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(appleApiIssuer)) {
    fail("APPLE_API_ISSUER must be an App Store Connect issuer UUID.");
  }
  if (!identity.includes(`(${teamId})`)) {
    fail("MACOS_SIGNING_IDENTITY must contain the configured APPLE_TEAM_ID.");
  }
  return {
    identity,
    notarize: false,
  };
}

function windowsSigningConfiguration(mode, applicationId) {
  if (mode === "unsigned") {
    process.env.CSC_IDENTITY_AUTO_DISCOVERY = "false";
    return {
      signExecutable: false,
    };
  }
  const endpoint = requiredEnvironment("AZURE_ARTIFACT_SIGNING_ENDPOINT");
  let endpointUrl;
  try {
    endpointUrl = new URL(endpoint);
  } catch {
    fail("AZURE_ARTIFACT_SIGNING_ENDPOINT must be a valid URL.");
  }
  if (
    endpointUrl.protocol !== "https:" ||
    !endpointUrl.hostname.endsWith(".codesigning.azure.net")
  ) {
    fail("AZURE_ARTIFACT_SIGNING_ENDPOINT must be an HTTPS codesigning.azure.net endpoint.");
  }
  const publisherName = requiredEnvironment("WINDOWS_SIGNING_SUBJECT");
  if (!publisherMatchesApplicationId(applicationId, publisherName)) {
    fail(`${publisherName} cannot publish application ID ${applicationId}.`);
  }
  const profileType = requiredEnvironment(
    "AZURE_ARTIFACT_SIGNING_PROFILE_TYPE",
  );
  if (profileType !== "PublicTrust") {
    fail("AZURE_ARTIFACT_SIGNING_PROFILE_TYPE must be PublicTrust.");
  }
  return {
    azureSignOptions: {
      publisherName,
      endpoint,
      certificateProfileName: requiredEnvironment(
        "AZURE_ARTIFACT_SIGNING_CERTIFICATE_PROFILE_NAME",
      ),
      codeSigningAccountName: requiredEnvironment(
        "AZURE_ARTIFACT_SIGNING_ACCOUNT_NAME",
      ),
      fileDigest: "SHA256",
      timestampRfc3161: "http://timestamp.acs.microsoft.com/",
      timestampDigest: "SHA256",
    },
  };
}

export function createBuilderConfiguration({
  platform,
  mode,
  bootstrap,
  packageMetadata,
  macSigning,
  windowsSigning,
}) {
  const outputPattern = builderArtifactPattern({ platform, mode });
  if (platform === "macos") {
    return {
      appId: bootstrap.applicationId,
      productName: bootstrap.productName,
      forceCodeSigning: mode === "signed",
      ...(mode === "signed"
        ? {
            afterSign: path.join(
              betaDir,
              "scripts",
              "notarize-target.mjs",
            ),
          }
        : {}),
      mac: {
        ...(macSigning
          ?? macSigningConfiguration(mode, bootstrap.applicationId)),
        artifactName: outputPattern,
      },
      dmg: {
        artifactName: outputPattern,
        sign: mode === "signed",
      },
    };
  }
  return {
    appId: bootstrap.applicationId,
    productName: bootstrap.productName,
    forceCodeSigning: mode === "signed",
    win: {
      ...(windowsSigning
        ?? windowsSigningConfiguration(mode, bootstrap.applicationId)),
      signExts: [".exe", ".dll", ".node"],
      artifactName: outputPattern,
    },
  };
}

export async function packagePlatform(argv = process.argv.slice(2)) {
  const { platform, arch } = parsePackagingArguments(argv);
  const mode = signingMode();
  assertNativeHost(platform, arch);
  const bootstrap = preparePackageBootstrap({ signingMode: mode });
  if (mode === "signed") {
    const toolchain = evaluateToolchainPolicy(
      loadToolchainPolicy(),
      installedToolchain(),
    );
    if (!toolchain.publicationReady) {
      fail(
        `Signed binary packaging is blocked by toolchain policy: `
        + toolchain.blockers.join(" | "),
      );
    }
    if (bootstrap.manifest.publication.ready !== true) {
      fail(
        `Signed binary packaging is blocked by package bootstrap policy: ` +
        bootstrap.manifest.publication.blockers.join(" | "),
      );
    }
    const mediaPolicy = evaluatePolicyReadiness(loadNativeMediaPolicy());
    if (!mediaPolicy.publication_ready) {
      fail(
        `Signed binary packaging is blocked by native media policy: ` +
        mediaPolicy.blockers.join(" | "),
      );
    }
    if (platform === "windows") {
      const windowsSigningPolicy = loadWindowsSigningPolicy();
      const readiness = evaluateWindowsSigningPolicy(windowsSigningPolicy);
      if (!readiness.publicationReady) {
        fail(
          `Signed Windows packaging is blocked: ${readiness.blockers.join(" | ")}`,
        );
      }
    }
  }

  const packageMetadata = JSON.parse(
    readFileSync(path.join(betaDir, "package.json"), "utf8"),
  );
  const version = String(packageMetadata.version || "").trim();
  if (!/^\d+\.\d+\.\d+-beta\.\d+$/.test(version)) {
    fail(`Package version is not a beta semantic version: ${version}`);
  }

  const outputName = artifactName({ platform, arch, version, mode });
  const outputPath = path.join(releaseDir, outputName);
  const appNotarizationEvidence = `${outputPath}.app.notarization.json`;
  const dmgNotarizationEvidence = `${outputPath}.notarization.json`;
  if (platform === "macos" && mode === "signed") {
    process.env.FRONTIER_NOTARIZATION_APP_EVIDENCE =
      appNotarizationEvidence;
  }
  const config = createBuilderConfiguration({
    platform,
    mode,
    bootstrap,
    packageMetadata,
  });
  rmSync(outputPath, { force: true });
  rmSync(appOutputDirectory(platform, arch), { recursive: true, force: true });
  for (const evidencePath of [
    appNotarizationEvidence,
    dmgNotarizationEvidence,
  ]) {
    rmSync(evidencePath, { force: true });
    rmSync(`${evidencePath}.log.json`, { force: true });
  }

  const builderArch = arch === "arm64" ? Arch.arm64 : Arch.x64;
  const targets =
    platform === "macos"
      ? Platform.MAC.createTarget(["dmg"], builderArch)
      : Platform.WINDOWS.createTarget(["nsis"], builderArch);
  await build({
    targets,
    publish: "never",
    config,
  });

  if (!existsSync(outputPath)) {
    fail(`electron-builder did not produce the expected artifact: ${outputPath}`);
  }
  if (platform === "windows") {
    for (const entry of readdirSync(releaseDir)) {
      if (
        entry.endsWith(".blockmap") ||
        /^latest.*\.ya?ml$/i.test(entry)
      ) {
        rmSync(path.join(releaseDir, entry), { force: true });
      }
    }
    const installers = readdirSync(releaseDir).filter((entry) =>
      entry.toLowerCase().endsWith(".exe"),
    );
    if (
      installers.length !== 1 ||
      installers[0] !== outputName
    ) {
      fail(
        `Windows packaging must produce exactly ${outputName}; received ` +
        installers.join(", "),
      );
    }
  }
  if (platform === "macos" && mode === "signed") {
    await notarizeTarget(outputPath, dmgNotarizationEvidence);
  }

  process.stdout.write(`FRONTIER_ARTIFACT=${outputPath}\n`);
  return outputPath;
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  packagePlatform().catch((error) => {
    process.stderr.write(`Packaging failed: ${String(error.stack || error)}\n`);
    process.exit(1);
  });
}
