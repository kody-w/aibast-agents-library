import path from "node:path";
import { pathToFileURL } from "node:url";

const shaPattern = /^[0-9a-f]{40}$/i;
const tagPattern = /^brainstem-beta-v[0-9A-Za-z][0-9A-Za-z._-]*$/;

function fail(message) {
  throw new Error(message);
}

function normalizedSnapshot(value, label) {
  const tag = String(value?.tag || "").trim();
  const tagObject = String(value?.tagObject || "").trim().toLowerCase();
  const commit = String(value?.commit || "").trim().toLowerCase();
  const releaseId = String(value?.releaseId || "").trim();
  if (!tagPattern.test(tag)) fail(`${label} tag is invalid.`);
  if (!shaPattern.test(tagObject)) fail(`${label} annotated tag object is invalid.`);
  if (!shaPattern.test(commit)) fail(`${label} peeled commit is invalid.`);
  if (!/^[1-9][0-9]*$/.test(releaseId)) fail(`${label} release ID is invalid.`);
  return { tag, tagObject, commit, releaseId };
}

export function verifyReleaseSnapshot(expected, actual) {
  const baseline = normalizedSnapshot(expected, "Expected");
  const observed = normalizedSnapshot(actual, "Observed");
  for (const field of ["tag", "tagObject", "commit", "releaseId"]) {
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
        "--actual-tag",
        "--actual-tag-object",
        "--actual-commit",
        "--actual-release-id",
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
  return verifyReleaseSnapshot(
    {
      tag: values["expected-tag"],
      tagObject: values["expected-tag-object"],
      commit: values["expected-commit"],
      releaseId: values["expected-release-id"],
    },
    {
      tag: values["actual-tag"],
      tagObject: values["actual-tag-object"],
      commit: values["actual-commit"],
      releaseId: values["actual-release-id"],
    },
  );
}

if (
  process.argv[1]
  && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  try {
    const snapshot = runReleaseRaceGuard();
    process.stdout.write(
      `Release snapshot verified: ${snapshot.tagObject} -> ${snapshot.commit} `
      + `(release ${snapshot.releaseId}).\n`,
    );
  } catch (error) {
    process.stderr.write(
      `Release race guard failed: ${String(error.stack || error)}\n`,
    );
    process.exit(1);
  }
}
