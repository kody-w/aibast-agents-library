import { readFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

function fail(message) {
  throw new Error(message);
}

export function assertImmutableReleasesEnabled(settings) {
  if (
    !settings
    || typeof settings !== "object"
    || Array.isArray(settings)
    || settings.enabled !== true
  ) {
    fail("Repository immutable releases setting must report enabled=true.");
  }
  return true;
}

function parseArguments(argv) {
  if (argv.length !== 2 || argv[0] !== "--input" || !argv[1]) {
    fail("Usage: immutable-release-policy.mjs --input <settings.json>");
  }
  return path.resolve(argv[1]);
}

export function verifyImmutableReleaseSettingsFile(argv = process.argv.slice(2)) {
  const input = parseArguments(argv);
  const settings = JSON.parse(readFileSync(input, "utf8"));
  assertImmutableReleasesEnabled(settings);
  return input;
}

if (
  process.argv[1]
  && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  try {
    process.stdout.write(`${verifyImmutableReleaseSettingsFile()}\n`);
  } catch (error) {
    process.stderr.write(
      `Immutable release policy failed: ${String(error.stack || error)}\n`,
    );
    process.exit(1);
  }
}
