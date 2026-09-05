import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const tagPattern = /^brainstem-beta-v[0-9A-Za-z][0-9A-Za-z._-]*$/;
const installerPattern =
  /^RAPP-Brainstem-Frontier-.+-windows-x64-setup\.exe$/;
const versionTagPattern =
  /^brainstem-beta-v(\d+)\.(\d+)\.(\d+)-beta\.(\d+)$/;

function fail(message) {
  throw new Error(message);
}

function timestamp(value) {
  const parsed = Date.parse(String(value || ""));
  return Number.isFinite(parsed) ? parsed : 0;
}

function versionTuple(tag) {
  const match = versionTagPattern.exec(tag || "");
  if (!match) fail(`Windows binary release tag is not a beta semver: ${tag}`);
  return match.slice(1).map(Number);
}

function compareVersions(left, right) {
  for (let index = 0; index < left.length; index += 1) {
    if (left[index] !== right[index]) return left[index] - right[index];
  }
  return 0;
}

export function selectPreviousWindowsBinary(releases, currentTag) {
  if (!Array.isArray(releases) || !tagPattern.test(currentTag || "")) {
    fail("Windows upgrade release inventory is invalid.");
  }
  const currentVersion = versionTuple(currentTag);
  const allBinaryReleases = releases
    .filter(
      (release) =>
        release?.tag_name !== currentTag
        && tagPattern.test(release?.tag_name || "")
        && release?.draft !== true
        && Array.isArray(release?.assets)
        && release.assets.some((asset) => installerPattern.test(asset?.name || "")),
    );
  for (const release of allBinaryReleases) {
    if (compareVersions(versionTuple(release.tag_name), currentVersion) >= 0) {
      fail(
        `Binary release ${release.tag_name} is not older than ${currentTag}; `
        + "N-1 selection would be ambiguous.",
      );
    }
  }
  const candidates = allBinaryReleases
    .sort(
      (left, right) =>
        compareVersions(
          versionTuple(right.tag_name),
          versionTuple(left.tag_name),
        )
        || timestamp(right.published_at) - timestamp(left.published_at)
        || Number(right.id || 0) - Number(left.id || 0),
    );
  if (!candidates.length) {
    return {
      firstBinaryRelease: true,
      previousReleaseTag: null,
      previousAssetId: null,
      previousAssetName: null,
      previousAssetDigest: null,
    };
  }

  const release = candidates[0];
  if (release.immutable !== true) {
    fail(
      `Previous binary release ${release.tag_name} is not immutable; `
      + "N-1 upgrade evidence cannot trust it.",
    );
  }
  const installers = release.assets.filter((asset) =>
    installerPattern.test(asset?.name || ""),
  );
  if (installers.length !== 1) {
    fail(
      `Previous binary release ${release.tag_name} must contain exactly one `
      + "Windows x64 installer.",
    );
  }
  const asset = installers[0];
  if (
    !Number.isSafeInteger(asset.id)
    || asset.id <= 0
    || !/^sha256:[0-9a-f]{64}$/i.test(asset.digest || "")
    || asset.state !== "uploaded"
    || !Number.isSafeInteger(asset.size)
    || asset.size <= 0
  ) {
    fail(`Previous Windows installer metadata is incomplete for ${release.tag_name}.`);
  }
  return {
    firstBinaryRelease: false,
    previousReleaseTag: release.tag_name,
    previousAssetId: String(asset.id),
    previousAssetName: asset.name,
    previousAssetDigest: asset.digest.toLowerCase(),
  };
}

function parseArguments(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const value = argv[index + 1];
    if (!["--releases", "--current-tag", "--output"].includes(argument)) {
      fail(`Unsupported argument: ${argument}`);
    }
    if (!value || value.startsWith("--")) fail(`Missing value for ${argument}.`);
    values[argument.slice(2)] = value;
    index += 1;
  }
  for (const name of ["releases", "current-tag", "output"]) {
    if (!values[name]) fail(`--${name} is required.`);
  }
  return values;
}

export function writeWindowsUpgradePolicy(argv = process.argv.slice(2)) {
  const args = parseArguments(argv);
  const result = selectPreviousWindowsBinary(
    JSON.parse(readFileSync(path.resolve(args.releases), "utf8")),
    args["current-tag"],
  );
  const output = path.resolve(args.output);
  writeFileSync(output, `${JSON.stringify(result, null, 2)}\n`, "utf8");
  return result;
}

if (
  process.argv[1]
  && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  try {
    const result = writeWindowsUpgradePolicy();
    process.stdout.write(`${JSON.stringify(result)}\n`);
  } catch (error) {
    process.stderr.write(
      `Windows upgrade policy failed: ${String(error.stack || error)}\n`,
    );
    process.exit(1);
  }
}
