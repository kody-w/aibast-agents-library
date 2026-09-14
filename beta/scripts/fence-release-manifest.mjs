import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

import {
  RELEASE_MANIFEST_FENCE,
  RELEASE_MANIFEST_SCHEMA,
} from "./release-manifest.mjs";

function fail(message) {
  throw new Error(message);
}

function parseArguments(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const value = argv[index + 1];
    if (!["--body", "--manifest", "--output"].includes(argument)) {
      fail(`Unsupported argument: ${argument}`);
    }
    if (!value || value.startsWith("--")) {
      fail(`Missing value for ${argument}.`);
    }
    values[argument.slice(2)] = value;
    index += 1;
  }
  for (const name of ["body", "manifest", "output"]) {
    if (!values[name]) fail(`--${name} is required.`);
  }
  return values;
}

export function upsertReleaseManifestFence(body, manifest) {
  if (
    !manifest
    || typeof manifest !== "object"
    || Array.isArray(manifest)
    || manifest.schema !== RELEASE_MANIFEST_SCHEMA
  ) {
    fail(`Manifest schema must be ${RELEASE_MANIFEST_SCHEMA}.`);
  }
  if (
    !manifest.release
    || !/^brainstem-beta-v/.test(manifest.release.tag || "")
    || !/^[0-9a-f]{40}$/i.test(manifest.release.commit || "")
    || !Array.isArray(manifest.artifacts)
    || manifest.artifacts.length === 0
  ) {
    fail("Manifest release binding and artifacts are required.");
  }

  const escapedFence = RELEASE_MANIFEST_FENCE.replace(
    /[.*+?^${}()|[\]\\]/g,
    "\\$&",
  );
  const pattern = new RegExp(
    "(?:^|\\n)```"
      + escapedFence
      + "\\s*\\n[\\s\\S]*?\\n```(?=\\n|$)",
    "g",
  );
  const matches = [...String(body || "").matchAll(pattern)];
  if (matches.length > 1) {
    fail("Release body contains more than one Frontier manifest fence.");
  }
  const withoutManifest = String(body || "").replace(pattern, "\n").trimEnd();
  const fenced = [
    `\`\`\`${RELEASE_MANIFEST_FENCE}`,
    JSON.stringify(manifest, null, 2),
    "```",
  ].join("\n");
  return `${withoutManifest ? `${withoutManifest}\n\n` : ""}${fenced}\n`;
}

export function writeReleaseManifestFence(argv = process.argv.slice(2)) {
  const args = parseArguments(argv);
  const bodyPath = path.resolve(args.body);
  const manifestPath = path.resolve(args.manifest);
  const outputPath = path.resolve(args.output);
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const updated = upsertReleaseManifestFence(
    readFileSync(bodyPath, "utf8"),
    manifest,
  );
  writeFileSync(outputPath, updated, "utf8");
  return outputPath;
}

if (
  process.argv[1]
  && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  try {
    process.stdout.write(`${writeReleaseManifestFence()}\n`);
  } catch (error) {
    process.stderr.write(
      `Release manifest fence failed: ${String(error.stack || error)}\n`,
    );
    process.exit(1);
  }
}
