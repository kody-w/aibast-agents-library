import { createHash } from "node:crypto";
import {
  lstatSync,
  readFileSync,
  readdirSync,
  statSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const schema = "rapp-brainstem-frontier-windows-signing-input/v1";

function fail(message) {
  throw new Error(message);
}

function sha256(filePath) {
  return createHash("sha256").update(readFileSync(filePath)).digest("hex");
}

function filesUnder(root, directory = root) {
  const files = [];
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const absolute = path.join(directory, entry.name);
    const relative = path.relative(root, absolute).split(path.sep).join("/");
    if (entry.isSymbolicLink() || lstatSync(absolute).isSymbolicLink()) {
      fail(`Signing input must not contain symbolic links: ${relative}`);
    }
    if (entry.isDirectory()) files.push(...filesUnder(root, absolute));
    else if (relative !== "windows-signing-input.json") files.push(relative);
  }
  return files.sort((left, right) => (
    left < right ? -1 : left > right ? 1 : 0
  ));
}

function inventory(root) {
  return filesUnder(root).map((relative) => {
    const absolute = path.join(root, ...relative.split("/"));
    return {
      path: relative,
      size: statSync(absolute).size,
      sha256: sha256(absolute),
    };
  });
}

export function createWindowsSigningInput(root, commit) {
  if (!/^[0-9a-f]{40}$/i.test(commit || "")) {
    fail("Windows signing input requires a full commit SHA.");
  }
  const packageMetadata = JSON.parse(
    readFileSync(path.join(root, "beta", "package.json"), "utf8"),
  );
  const packageLock = JSON.parse(
    readFileSync(path.join(root, "beta", "package-lock.json"), "utf8"),
  );
  const manifest = {
    schema,
    commit: commit.toLowerCase(),
    version: packageMetadata.version,
    application_id: packageMetadata.build.appId,
    product_name: packageMetadata.build.productName,
    toolchain: {
      node: packageMetadata.engines.node,
      electron: packageLock.packages["node_modules/electron"].version,
      electron_builder:
        packageLock.packages["node_modules/electron-builder"].version,
      artifact_signing_module: "0.1.8",
    },
    files: inventory(root),
  };
  writeFileSync(
    path.join(root, "windows-signing-input.json"),
    `${JSON.stringify(manifest, null, 2)}\n`,
    "utf8",
  );
  return manifest;
}

export function verifyWindowsSigningInput(root, expectedCommit) {
  const manifest = JSON.parse(
    readFileSync(path.join(root, "windows-signing-input.json"), "utf8"),
  );
  if (
    manifest.schema !== schema
    || manifest.commit !== String(expectedCommit || "").toLowerCase()
    || !/^[0-9a-f]{40}$/.test(manifest.commit)
    || !Array.isArray(manifest.files)
  ) {
    fail("Windows signing input identity is invalid.");
  }
  const actual = inventory(root);
  if (
    actual.length !== manifest.files.length
    || actual.some((entry, index) => (
      entry.path !== manifest.files[index]?.path
      || entry.size !== manifest.files[index]?.size
      || entry.sha256 !== manifest.files[index]?.sha256
    ))
  ) {
    fail("Windows signing input files do not match the validated manifest.");
  }
  return manifest;
}

function parseArguments(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const value = argv[index + 1];
    if (!["--mode", "--root", "--commit"].includes(argument)) {
      fail(`Unsupported argument: ${argument}`);
    }
    if (!value || value.startsWith("--")) fail(`Missing value for ${argument}.`);
    values[argument.slice(2)] = value;
    index += 1;
  }
  if (!["create", "verify"].includes(values.mode)) {
    fail("--mode must be create or verify.");
  }
  if (!values.root || !values.commit) fail("--root and --commit are required.");
  return values;
}

if (
  process.argv[1]
  && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  try {
    const args = parseArguments(process.argv.slice(2));
    const root = path.resolve(args.root);
    const result = args.mode === "create"
      ? createWindowsSigningInput(root, args.commit)
      : verifyWindowsSigningInput(root, args.commit);
    process.stdout.write(
      `Windows signing input ${args.mode} verified ${result.files.length} files.\n`,
    );
  } catch (error) {
    process.stderr.write(
      `Windows signing input failed: ${String(error.stack || error)}\n`,
    );
    process.exit(1);
  }
}
