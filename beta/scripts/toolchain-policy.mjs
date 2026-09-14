import { readFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const betaDir = path.resolve(import.meta.dirname, "..");
const policyPath = path.join(betaDir, "build", "toolchain-policy.json");

function fail(message) {
  throw new Error(message);
}

export function loadToolchainPolicy(filePath = policyPath) {
  const policy = JSON.parse(readFileSync(filePath, "utf8"));
  if (
    policy?.schema !==
      "https://github.com/microsoft/aibast-agents-library/frontier-toolchain-policy/v1"
    || typeof policy.publication_enabled !== "boolean"
    || typeof policy.required?.electron !== "string"
    || typeof policy.required?.electron_builder !== "string"
    || policy.required?.macos_minimum !== "12.0"
    || !Array.isArray(policy.publication_blockers)
  ) {
    fail("Frontier toolchain policy is malformed.");
  }
  return policy;
}

export function evaluateToolchainPolicy(policy, installed) {
  const blockers = [
    ...(policy.publication_enabled
      ? []
      : policy.publication_blockers.length
        ? policy.publication_blockers
        : ["Toolchain publication is disabled."]),
  ];
  if (installed.electron !== policy.required.electron) {
    blockers.push(
      `electron ${installed.electron || "missing"} does not match required `
      + `${policy.required.electron}.`,
    );
  }
  if (installed.electronBuilder !== policy.required.electron_builder) {
    blockers.push(
      `electron-builder ${installed.electronBuilder || "missing"} does not `
      + `match required ${policy.required.electron_builder}.`,
    );
  }
  if (installed.macosMinimum !== policy.required.macos_minimum) {
    blockers.push(
      `macOS minimum ${installed.macosMinimum || "missing"} does not match `
      + `${policy.required.macos_minimum}.`,
    );
  }
  return {
    publicationReady: blockers.length === 0,
    blockers,
  };
}

export function installedToolchain() {
  const packageMetadata = JSON.parse(
    readFileSync(path.join(betaDir, "package.json"), "utf8"),
  );
  const packageLock = JSON.parse(
    readFileSync(path.join(betaDir, "package-lock.json"), "utf8"),
  );
  return {
    electron: packageLock.packages["node_modules/electron"]?.version || null,
    electronBuilder:
      packageLock.packages["node_modules/electron-builder"]?.version || null,
    macosMinimum: packageMetadata.build?.mac?.minimumSystemVersion || null,
  };
}

export function runToolchainPolicy(argv = process.argv.slice(2)) {
  for (const argument of argv) {
    if (argument !== "--require-publication") {
      fail(`Unsupported argument: ${argument}`);
    }
  }
  const result = evaluateToolchainPolicy(
    loadToolchainPolicy(),
    installedToolchain(),
  );
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  if (argv.includes("--require-publication") && !result.publicationReady) {
    return 1;
  }
  return 0;
}

if (
  process.argv[1]
  && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  try {
    process.exit(runToolchainPolicy());
  } catch (error) {
    process.stderr.write(
      `Toolchain policy failed: ${String(error.stack || error)}\n`,
    );
    process.exit(2);
  }
}
