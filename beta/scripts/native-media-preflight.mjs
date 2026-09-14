import { createRequire } from "node:module";
import { writeFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

import { evaluateNativeMedia } from "./native-media-gate.mjs";

const require = createRequire(import.meta.url);

function fail(message) {
  throw new Error(message);
}

function parseArguments(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const value = argv[index + 1];
    if (!["--platform", "--arch", "--output"].includes(argument)) {
      fail(`Unsupported argument: ${argument}`);
    }
    if (!value || value.startsWith("--")) {
      fail(`Missing value for ${argument}.`);
    }
    values[argument.slice(2)] = value;
    index += 1;
  }
  if (!["macos", "windows"].includes(values.platform)) {
    fail("--platform must be macos or windows.");
  }
  if (
    (values.platform === "macos" && !["arm64", "x64"].includes(values.arch))
    || (values.platform === "windows" && values.arch !== "x64")
  ) {
    fail("--arch is not supported for the selected platform.");
  }
  if (!values.output) fail("--output is required.");
  return values;
}

export function installedNativeMediaPaths() {
  return {
    ffmpegPath: require("ffmpeg-static"),
    ffprobePath: require("@ffprobe-installer/ffprobe").path,
  };
}

export function runNativeMediaPreflight(argv = process.argv.slice(2)) {
  const args = parseArguments(argv);
  const paths = installedNativeMediaPaths();
  const result = evaluateNativeMedia({
    ...paths,
    platform: args.platform,
    arch: args.arch,
  });
  const evidence = {
    ...result,
    generated_at: new Date().toISOString(),
    phase: "pre-signing",
  };
  const outputPath = path.resolve(args.output);
  writeFileSync(outputPath, `${JSON.stringify(evidence, null, 2)}\n`, {
    mode: 0o600,
  });
  process.stdout.write(`${JSON.stringify(evidence, null, 2)}\n`);
  if (!result.publication_ready) {
    fail(
      `Native media is not approved before signing: ${result.blockers.join(" | ")}`,
    );
  }
  return outputPath;
}

if (
  process.argv[1]
  && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  try {
    runNativeMediaPreflight();
  } catch (error) {
    process.stderr.write(
      `Native media preflight failed: ${String(error.stack || error)}\n`,
    );
    process.exit(1);
  }
}
