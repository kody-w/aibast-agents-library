import { existsSync, statSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

import {
  evaluatePolicyReadiness,
  loadNativeMediaPolicy,
} from "./native-media-gate.mjs";

const blockedPolicyAllowedNames = new Set([
  "UNSIGNED-NOT-FOR-DISTRIBUTION.txt",
]);

function fail(message) {
  throw new Error(message);
}

function parseArguments(argv) {
  const paths = [];
  for (let index = 0; index < argv.length; index += 1) {
    if (argv[index] !== "--path") {
      fail(`Unsupported argument: ${argv[index]}`);
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) fail("--path requires a value.");
    paths.push(value);
    index += 1;
  }
  if (!paths.length) fail("At least one --path is required.");
  return paths;
}

export function assertUnsignedUploadPolicy({
  publicationReady,
  paths,
  requireFiles = true,
}) {
  if (!Array.isArray(paths) || paths.length === 0) {
    fail("Unsigned upload evidence paths are required.");
  }
  for (const entry of paths) {
    const filePath = String(entry || "");
    const name = path.basename(filePath);
    if (!name || filePath.split(/[\\/]/).includes("..")) {
      fail(`Unsigned upload path is unsafe: ${filePath}`);
    }
    if (
      !publicationReady
      && !blockedPolicyAllowedNames.has(name)
      && !name.endsWith(".gate.json")
      && !name.endsWith(".gate.log")
    ) {
      fail(
        `Native-media policy is blocked; unsigned upload may contain reports `
        + `only, not ${name}.`,
      );
    }
    if (requireFiles) {
      if (!existsSync(filePath) || statSync(filePath).size < 1) {
        fail(`Unsigned upload evidence is missing or empty: ${filePath}`);
      }
    }
  }
  return true;
}

export function runUnsignedUploadGate(argv = process.argv.slice(2)) {
  const paths = parseArguments(argv).map((entry) => path.resolve(entry));
  const readiness = evaluatePolicyReadiness(loadNativeMediaPolicy());
  assertUnsignedUploadPolicy({
    publicationReady: readiness.publication_ready,
    paths,
  });
  process.stdout.write(
    `Unsigned upload policy accepted ${paths.length} report-only files; `
    + `native-media publication=${readiness.publication_ready}.\n`,
  );
}

if (
  process.argv[1]
  && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  try {
    runUnsignedUploadGate();
  } catch (error) {
    process.stderr.write(
      `Unsigned upload gate failed: ${String(error.stack || error)}\n`,
    );
    process.exit(1);
  }
}
