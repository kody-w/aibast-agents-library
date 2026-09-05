import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const shaPattern = /^[0-9a-f]{40}$/i;
const digestPattern = /^[0-9a-f]{64}$/i;
const tagPattern = /^brainstem-beta-v[0-9A-Za-z][0-9A-Za-z._-]*$/;

function fail(message) {
  throw new Error(message);
}

export function releaseContentFingerprint(release) {
  if (
    !release
    || typeof release !== "object"
    || typeof release.body !== "string"
    || !Array.isArray(release.assets)
  ) {
    fail("Release content fingerprint input is invalid.");
  }
  const assets = release.assets.map((asset) => {
    if (
      !Number.isSafeInteger(asset?.id)
      || asset.id <= 0
      || typeof asset.name !== "string"
      || !asset.name
      || typeof asset.state !== "string"
      || !asset.state
      || !Number.isSafeInteger(asset.size)
      || asset.size <= 0
      || !/^sha256:[0-9a-f]{64}$/i.test(asset.digest || "")
    ) {
      fail("Release asset metadata is incomplete for content fingerprinting.");
    }
    return {
      id: asset.id,
      name: asset.name,
      state: asset.state,
      size: asset.size,
      digest: asset.digest.toLowerCase(),
    };
  }).sort((left, right) => (
    left.name < right.name
      ? -1
      : left.name > right.name
        ? 1
        : left.id - right.id
  ));
  return createHash("sha256")
    .update(JSON.stringify({ body: release.body, assets }), "utf8")
    .digest("hex");
}

function normalizedSnapshot(value, label) {
  const tag = String(value?.tag || "").trim();
  const tagObject = String(value?.tagObject || "").trim().toLowerCase();
  const commit = String(value?.commit || "").trim().toLowerCase();
  const releaseId = String(value?.releaseId || "").trim();
  const releaseFingerprint = String(
    value?.releaseFingerprint || "",
  ).trim().toLowerCase();
  if (!tagPattern.test(tag)) fail(`${label} tag is invalid.`);
  if (!shaPattern.test(tagObject)) fail(`${label} annotated tag object is invalid.`);
  if (!shaPattern.test(commit)) fail(`${label} peeled commit is invalid.`);
  if (!/^[1-9][0-9]*$/.test(releaseId)) fail(`${label} release ID is invalid.`);
  if (!digestPattern.test(releaseFingerprint)) {
    fail(`${label} release content fingerprint is invalid.`);
  }
  return { tag, tagObject, commit, releaseId, releaseFingerprint };
}

export function verifyReleaseSnapshot(expected, actual) {
  const baseline = normalizedSnapshot(expected, "Expected");
  const observed = normalizedSnapshot(actual, "Observed");
  for (const field of [
    "tag",
    "tagObject",
    "commit",
    "releaseId",
    "releaseFingerprint",
  ]) {
    if (observed[field] !== baseline[field]) {
      fail(
        `Release race detected: ${field} changed from `
        + `${baseline[field]} to ${observed[field]}.`,
      );
    }
  }
  return observed;
}

function parseArguments(argv) {
  if (argv.length === 2 && argv[0] === "--fingerprint-file") {
    return {
      fingerprintFile: argv[1],
    };
  }
  const values = {};
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const value = argv[index + 1];
    if (
      ![
        "--expected-tag",
        "--expected-tag-object",
        "--expected-commit",
        "--expected-release-id",
        "--expected-release-fingerprint",
        "--actual-tag-object",
        "--actual-commit",
        "--actual-release-file",
      ].includes(argument)
    ) {
      fail(`Unsupported argument: ${argument}`);
    }
    if (!value || value.startsWith("--")) fail(`Missing value for ${argument}.`);
    values[argument.slice(2)] = value;
    index += 1;
  }
  return values;
}

export function runReleaseRaceGuard(argv = process.argv.slice(2)) {
  const values = parseArguments(argv);
  if (values.fingerprintFile) {
    return releaseContentFingerprint(
      JSON.parse(readFileSync(path.resolve(values.fingerprintFile), "utf8")),
    );
  }
  const actualRelease = JSON.parse(
    readFileSync(path.resolve(values["actual-release-file"]), "utf8"),
  );
  return verifyReleaseSnapshot(
    {
      tag: values["expected-tag"],
      tagObject: values["expected-tag-object"],
      commit: values["expected-commit"],
      releaseId: values["expected-release-id"],
      releaseFingerprint: values["expected-release-fingerprint"],
    },
    {
      tag: actualRelease.tag_name,
      tagObject: values["actual-tag-object"],
      commit: values["actual-commit"],
      releaseId: String(actualRelease.id),
      releaseFingerprint: releaseContentFingerprint(actualRelease),
    },
  );
}

if (
  process.argv[1]
  && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  try {
    const snapshot = runReleaseRaceGuard();
    if (typeof snapshot === "string") process.stdout.write(`${snapshot}\n`);
    else {
      process.stdout.write(
        `Release snapshot verified: ${snapshot.tagObject} -> ${snapshot.commit} `
        + `(release ${snapshot.releaseId}, content `
        + `${snapshot.releaseFingerprint}).\n`,
      );
    }
  } catch (error) {
    process.stderr.write(
      `Release race guard failed: ${String(error.stack || error)}\n`,
    );
    process.exit(1);
  }
}
