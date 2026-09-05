import { existsSync, readFileSync, readdirSync, rmSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";

import { Arch, Platform, build } from "electron-builder";

import {
  evaluatePolicyReadiness,
  loadNativeMediaPolicy,
} from "./native-media-gate.mjs";
import { publisherMatchesApplicationId } from "./package-contract.mjs";
import {
  evaluateToolchainPolicy,
  installedToolchain,
  loadToolchainPolicy,
} from "./toolchain-policy.mjs";
import {
  evaluateWindowsSigningPolicy,
  loadWindowsSigningPolicy,
} from "./windows-signing-policy.mjs";

const betaDir = path.resolve(import.meta.dirname, "..");
const inputRoot = path.resolve(betaDir, "..");
const releaseDir = path.join(betaDir, "release");
const signedDir = path.join(releaseDir, "signed");
const prepackagedApp = path.join(releaseDir, "win-unpacked");
const require = createRequire(import.meta.url);

function fail(message) {
  throw new Error(message);
}

function required(name) {
  const value = String(process.env[name] || "").trim();
  if (!value) fail(`${name} is required.`);
  return value;
}

function collectSignableFiles(root) {
  const files = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    const filePath = path.join(root, entry.name);
    if (entry.isDirectory()) files.push(...collectSignableFiles(filePath));
    else if ([".exe", ".dll", ".node"].includes(path.extname(filePath).toLowerCase())) {
      files.push(filePath);
    }
  }
  return files.sort();
}

export async function signValidatedWindowsInput() {
  if (process.platform !== "win32" || process.arch !== "x64") {
    fail("Validated Windows signing requires a native x64 Windows host.");
  }
  const toolchain = evaluateToolchainPolicy(
    loadToolchainPolicy(),
    installedToolchain(),
  );
  if (!toolchain.publicationReady) {
    fail(`Toolchain policy is blocked: ${toolchain.blockers.join(" | ")}`);
  }
  const media = evaluatePolicyReadiness(loadNativeMediaPolicy());
  if (!media.publication_ready) {
    fail(`Native media policy is blocked: ${media.blockers.join(" | ")}`);
  }
  const signingPolicy = evaluateWindowsSigningPolicy(
    loadWindowsSigningPolicy(),
  );
  if (!signingPolicy.publicationReady) {
    fail(`Windows signing policy is blocked: ${signingPolicy.blockers.join(" | ")}`);
  }

  const packageMetadata = JSON.parse(
    readFileSync(path.join(betaDir, "package.json"), "utf8"),
  );
  const version = packageMetadata.version;
  const outputName =
    `RAPP-Brainstem-Frontier-${version}-windows-x64-setup.exe`;
  const outputPath = path.join(signedDir, outputName);
  const hook = path.join(betaDir, "scripts", "artifact-signing-hook.cjs");
  process.env.FRONTIER_SIGNING_ROOT = inputRoot;
  required("FRONTIER_ARTIFACT_SIGNING_MODULE_ROOT");
  const builderCache = required("ELECTRON_BUILDER_CACHE");
  if (!existsSync(builderCache)) {
    fail(`Validated electron-builder cache is missing: ${builderCache}`);
  }
  required("AZURE_ARTIFACT_SIGNING_ENDPOINT");
  required("AZURE_ARTIFACT_SIGNING_ACCOUNT_NAME");
  required("AZURE_ARTIFACT_SIGNING_CERTIFICATE_PROFILE_NAME");
  const publisher = required("WINDOWS_SIGNING_SUBJECT");
  if (!publisherMatchesApplicationId(packageMetadata.build.appId, publisher)) {
    fail("Protected Windows publisher does not match the application ID.");
  }
  if (!existsSync(prepackagedApp)) {
    fail(`Validated prepackaged app is missing: ${prepackagedApp}`);
  }
  rmSync(signedDir, { recursive: true, force: true });
  const sign = require(hook);
  const signableFiles = collectSignableFiles(prepackagedApp);
  if (signableFiles.length < 3) {
    fail("Validated prepackaged app does not contain enough signable PE files.");
  }
  for (const filePath of signableFiles) {
    await sign({ path: filePath, hash: "sha256", isNest: false });
  }

  await build({
    targets: Platform.WINDOWS.createTarget(["nsis"], Arch.x64),
    publish: "never",
    prepackaged: prepackagedApp,
    config: {
      appId: packageMetadata.build.appId,
      productName: packageMetadata.build.productName,
      forceCodeSigning: true,
      npmRebuild: false,
      directories: {
        output: signedDir,
        buildResources: path.join(betaDir, "build"),
      },
      win: {
        target: [{ target: "nsis", arch: ["x64"] }],
        icon: path.join(betaDir, "build", "icon.ico"),
        requestedExecutionLevel: "asInvoker",
        sign: hook,
        publisherName: publisher,
        signingHashAlgorithms: ["sha256"],
        signExts: [".exe", ".dll", ".node"],
        artifactName:
          "RAPP-Brainstem-Frontier-${version}-windows-x64-setup.${ext}",
      },
      nsis: packageMetadata.build.nsis,
    },
  });
  if (!existsSync(outputPath)) fail(`Signed NSIS output is missing: ${outputPath}`);
  for (const entry of readdirSync(signedDir)) {
    if (entry.endsWith(".blockmap") || /^latest.*\.ya?ml$/i.test(entry)) {
      rmSync(path.join(signedDir, entry), { force: true });
    }
  }
  process.stdout.write(`FRONTIER_ARTIFACT=${outputPath}\n`);
  return outputPath;
}

if (
  process.argv[1]
  && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  signValidatedWindowsInput().catch((error) => {
    process.stderr.write(
      `Validated Windows signing failed: ${String(error.stack || error)}\n`,
    );
    process.exit(1);
  });
}
