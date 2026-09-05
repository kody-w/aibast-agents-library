import {
  closeSync,
  existsSync,
  mkdirSync,
  openSync,
  readFileSync,
  readSync,
  readdirSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { createHash } from "node:crypto";
import { homedir } from "node:os";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";
import { pathToFileURL } from "node:url";

import { extractFile, listPackage } from "@electron/asar";

import {
  artifactName,
  publisherMatchesApplicationId,
} from "./package-contract.mjs";
import { evaluateNativeMedia } from "./native-media-gate.mjs";
import { loadBootstrapBundle } from "../electron/brainstem-provisioner.mjs";


const betaDir = path.resolve(import.meta.dirname, "..");
const releaseDir = path.join(betaDir, "release");
let productName = "RAPP Brainstem Frontier";
const results = [];
const evidence = {
  bootstrap: null,
  installation: null,
  nativeMedia: null,
  notarization: null,
  runtime: null,
  standardUser: null,
  windowsLifecycle: null,
  windowsUpgrade: null,
};

function fail(message) {
  throw new Error(message);
}

function requirement(name, pass, detail = "") {
  results.push({ name, pass: Boolean(pass), detail });
  process.stdout.write(
    `${pass ? " PASS" : "*FAIL"}  ${name}${detail ? ` — ${detail}` : ""}\n`,
  );
}

function command(commandName, args, options = {}) {
  const result = spawnSync(commandName, args, {
    encoding: "utf8",
    windowsHide: true,
    ...options,
  });
  return {
    ...result,
    output: [result.stdout, result.stderr, result.error]
      .filter(Boolean)
      .map(String)
      .join("\n")
      .trim(),
  };
}

function normalizePlatform(value = process.platform) {
  if (["darwin", "mac", "macos"].includes(value)) return "macos";
  if (["win32", "win", "windows"].includes(value)) return "windows";
  fail(`Unsupported package-gate platform: ${value}`);
}

export function parseGateArguments(argv, host = {
  platform: process.platform,
  arch: process.arch,
}) {
  const values = {};
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (!argument.startsWith("--")) fail(`Unexpected argument: ${argument}`);
    const name = argument.slice(2);
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) fail(`Missing value for --${name}.`);
    if (Object.hasOwn(values, name)) fail(`Duplicate argument: --${name}.`);
    values[name] = value;
    index += 1;
  }

  const supported = new Set([
    "platform",
    "arch",
    "mode",
    "artifact",
    "app-dir",
    "scratch-dir",
    "identity",
    "team-id",
    "expected-publisher",
    "brainstem-python",
    "brainstem-source",
    "report",
    "release-tag",
    "release-commit",
    "runtime-version-url",
    "require-standard-user",
    "previous-installer",
    "previous-release-tag",
    "first-binary-release",
  ]);
  for (const name of Object.keys(values)) {
    if (!supported.has(name)) fail(`Unsupported argument: --${name}.`);
  }

  const platform = normalizePlatform(values.platform || host.platform);
  const arch = values.arch || host.arch;
  const mode = values.mode || process.env.FRONTIER_SIGNING_MODE || "unsigned";
  if (!["signed", "unsigned"].includes(mode)) {
    fail("--mode must be signed or unsigned.");
  }
  if (platform === "macos" && !["x64", "arm64"].includes(arch)) {
    fail("macOS package gates support x64 or arm64.");
  }
  if (platform === "windows" && arch !== "x64") {
    fail("Windows ARM64 is intentionally unsupported until every native dependency is proven.");
  }
  const expectedHostPlatform = platform === "macos" ? "darwin" : "win32";
  if (normalizePlatform(host.platform) !== platform || host.arch !== arch) {
    fail(
      `Package gate requires a native ${expectedHostPlatform}/${arch} host; ` +
        `received ${host.platform}/${host.arch}.`,
    );
  }
  if (mode === "signed" && platform === "macos") {
    if (!values.identity || !values["team-id"]) {
      fail("Signed macOS gates require --identity and --team-id.");
    }
  }
  if (mode === "signed" && platform === "windows" && !values["expected-publisher"]) {
    fail("Signed Windows gates require --expected-publisher.");
  }
  if (
    mode === "signed" &&
    (
      !values["release-tag"] ||
      !values["release-commit"] ||
      !values["runtime-version-url"]
    )
  ) {
    fail(
      "Signed package gates require --release-tag, --release-commit, and --runtime-version-url.",
    );
  }
  if (
    values["require-standard-user"] &&
    !["true", "false"].includes(values["require-standard-user"])
  ) {
    fail("--require-standard-user must be true or false.");
  }
  if (values["require-standard-user"] === "true" && platform !== "windows") {
    fail("--require-standard-user is valid only for Windows.");
  }
  if (
    mode === "signed" &&
    platform === "windows" &&
    values["require-standard-user"] !== "true"
  ) {
    fail("Signed Windows package gates require --require-standard-user true.");
  }
  if (
    values["first-binary-release"]
    && !["true", "false"].includes(values["first-binary-release"])
  ) {
    fail("--first-binary-release must be true or false.");
  }
  const firstBinaryRelease = values["first-binary-release"] === "true";
  const previousInstaller = values["previous-installer"];
  if (
    mode === "signed"
    && platform === "windows"
    && Boolean(previousInstaller) === firstBinaryRelease
  ) {
    fail(
      "Signed Windows gates require exactly one of --previous-installer "
      + "or --first-binary-release true.",
    );
  }
  if (
    previousInstaller
    && !/^brainstem-beta-v/.test(values["previous-release-tag"] || "")
  ) {
    fail("--previous-installer requires --previous-release-tag.");
  }

  return {
    platform,
    arch,
    mode,
    artifact: values.artifact,
    appDir: values["app-dir"],
    scratchDir: values["scratch-dir"],
    identity: values.identity,
    teamId: values["team-id"],
    expectedPublisher: values["expected-publisher"],
    brainstemPython: values["brainstem-python"],
    brainstemSource: values["brainstem-source"],
    report: values.report,
    releaseTag: values["release-tag"],
    releaseCommit: values["release-commit"],
    runtimeVersionUrl: values["runtime-version-url"],
    requireStandardUser: values["require-standard-user"] === "true",
    previousInstaller,
    previousReleaseTag: values["previous-release-tag"],
    firstBinaryRelease,
  };
}

function sha256(filePath) {
  return createHash("sha256").update(readFileSync(filePath)).digest("hex");
}

function readHeader(filePath, bytes = 4096) {
  const descriptor = openSync(filePath, "r");
  try {
    const buffer = Buffer.alloc(bytes);
    const length = readSync(descriptor, buffer, 0, buffer.length, 0);
    return buffer.subarray(0, length);
  } finally {
    closeSync(descriptor);
  }
}

function cpuArchitecture(cpuType) {
  if (cpuType === 0x01000007) return "x64";
  if (cpuType === 0x0100000c) return "arm64";
  if (cpuType === 0x00000007) return "ia32";
  return `unknown-0x${cpuType.toString(16)}`;
}

export function binaryArchitectures(buffer) {
  if (buffer.length < 8) return [];

  if (buffer[0] === 0x4d && buffer[1] === 0x5a) {
    if (buffer.length < 0x40) return [];
    const peOffset = buffer.readUInt32LE(0x3c);
    if (
      peOffset + 6 > buffer.length ||
      buffer.toString("ascii", peOffset, peOffset + 4) !== "PE\0\0"
    ) {
      return [];
    }
    const machine = buffer.readUInt16LE(peOffset + 4);
    if (machine === 0x8664) return ["x64"];
    if (machine === 0xaa64) return ["arm64"];
    if (machine === 0x014c) return ["ia32"];
    return [`unknown-0x${machine.toString(16)}`];
  }

  const magic = buffer.readUInt32BE(0);
  const littleMagic = buffer.readUInt32LE(0);
  if ([0xfeedface, 0xfeedfacf].includes(littleMagic)) {
    return [cpuArchitecture(buffer.readUInt32LE(4))];
  }
  if ([0xfeedface, 0xfeedfacf].includes(magic)) {
    return [cpuArchitecture(buffer.readUInt32BE(4))];
  }

  const fatFormats = new Map([
    [0xcafebabe, { littleEndian: false, entrySize: 20 }],
    [0xcafebabf, { littleEndian: false, entrySize: 24 }],
    [0xbebafeca, { littleEndian: true, entrySize: 20 }],
    [0xbfbafeca, { littleEndian: true, entrySize: 24 }],
  ]);
  const fat = fatFormats.get(magic);
  if (!fat) return [];
  const read32 = fat.littleEndian
    ? (offset) => buffer.readUInt32LE(offset)
    : (offset) => buffer.readUInt32BE(offset);
  const count = read32(4);
  if (count < 1 || count > 32 || 8 + count * fat.entrySize > buffer.length) {
    return [];
  }
  const architectures = [];
  for (let index = 0; index < count; index += 1) {
    architectures.push(cpuArchitecture(read32(8 + index * fat.entrySize)));
  }
  return [...new Set(architectures)].sort();
}

function architectureCheck(label, filePath, expectedArchitecture) {
  if (!filePath || !existsSync(filePath)) {
    requirement(`${label} has ${expectedArchitecture} architecture`, false, filePath || "missing");
    return;
  }
  const architectures = binaryArchitectures(readHeader(filePath));
  requirement(
    `${label} has ${expectedArchitecture} architecture`,
    architectures.length === 1 && architectures[0] === expectedArchitecture,
    architectures.length ? architectures.join(",") : "unrecognized executable format",
  );
}

function findNamed(root, name) {
  if (!root || !existsSync(root)) return null;
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    const filePath = path.join(root, entry.name);
    if (entry.isDirectory()) {
      const found = findNamed(filePath, name);
      if (found) return found;
    } else if (entry.name === name) {
      return filePath;
    }
  }
  return null;
}

function collectFiles(root, predicate) {
  if (!root || !existsSync(root)) return [];
  const files = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    const filePath = path.join(root, entry.name);
    if (entry.isDirectory()) files.push(...collectFiles(filePath, predicate));
    else if (predicate(filePath)) files.push(filePath);
  }
  return files.sort();
}

function newestSourceMtime(directory) {
  let newest = 0;
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    if (["node_modules", "release"].includes(entry.name)) continue;
    const filePath = path.join(directory, entry.name);
    newest = Math.max(
      newest,
      entry.isDirectory()
        ? newestSourceMtime(filePath)
        : statSync(filePath).mtimeMs,
    );
  }
  return newest;
}

function appLayout(appPath, platform) {
  if (platform === "macos") {
    const contents = path.join(appPath, "Contents");
    return {
      executable: path.join(contents, "MacOS", productName),
      resources: path.join(contents, "Resources"),
    };
  }
  return {
    executable: path.join(appPath, `${productName}.exe`),
    resources: path.join(appPath, "resources"),
  };
}

function executableCheck(label, filePath, arch, versionArguments) {
  requirement(`${label} exists`, Boolean(filePath && existsSync(filePath)), filePath || "missing");
  architectureCheck(label, filePath, arch);
  if (!filePath || !existsSync(filePath)) {
    requirement(`${label} executes`, false, "missing");
    return;
  }
  const version = command(filePath, versionArguments, { timeout: 30000 });
  requirement(
    `${label} executes`,
    version.status === 0,
    version.status === 0
      ? String(version.stdout || "").split(/\r?\n/, 1)[0]
      : version.output,
  );
}

function inspectPackagedApp(appPath, label, platform, arch, checkFreshness = false) {
  requirement(`${label} exists`, existsSync(appPath), appPath);
  const { executable, resources } = appLayout(appPath, platform);
  requirement(`${label} executable exists`, existsSync(executable), executable);
  architectureCheck(`${label} executable`, executable, arch);

  const asarPath = path.join(resources, "app.asar");
  requirement(`${label} app.asar exists`, existsSync(asarPath), asarPath);
  if (checkFreshness && existsSync(asarPath)) {
    requirement(
      `${label} is newer than beta source`,
      statSync(asarPath).mtimeMs >= newestSourceMtime(betaDir),
      new Date(statSync(asarPath).mtimeMs).toISOString(),
    );
  }

  if (existsSync(asarPath)) {
    let entries = [];
    try {
      entries = listPackage(asarPath).map((entry) => entry.replace(/^[/\\]/, ""));
      requirement(`${label} app.asar is readable`, entries.length > 0, `${entries.length} entries`);
    } catch (error) {
      requirement(`${label} app.asar is readable`, false, String(error.message || error));
    }
    for (const requiredEntry of [
      "electron/main.mjs",
      "electron/brainstem-process.mjs",
      "electron/copilot-runtime.mjs",
      "electron/video-tools.mjs",
      "scripts/brainstem_ui_driver_agent.py",
      "ui/index.html",
      "ui/renderer.js",
      "package.json",
      "VERSION",
    ]) {
      requirement(
        `${label} contains ${requiredEntry}`,
        entries.includes(requiredEntry),
      );
    }
    requirement(
      `${label} excludes electron-builder`,
      !entries.some((entry) => entry.startsWith("node_modules/electron-builder/")),
    );
    requirement(
      `${label} contains the Copilot SDK`,
      entries.some((entry) => entry.startsWith("node_modules/@github/copilot-sdk/")),
    );

    try {
      const packagedMetadata = JSON.parse(
        extractFile(asarPath, "package.json").toString("utf8"),
      );
      const sourceMetadata = JSON.parse(
        readFileSync(path.join(betaDir, "package.json"), "utf8"),
      );
      requirement(
        `${label} version matches source`,
        packagedMetadata.version === sourceMetadata.version,
        String(packagedMetadata.version || "missing"),
      );
      requirement(
        `${label} declares the binary manifest update channel`,
        packagedMetadata.frontierDistributionChannel ===
          "binary-release-manifest-v1",
        String(packagedMetadata.frontierDistributionChannel || "missing"),
      );
      requirement(
        `${label} blocks the source-checkout updater`,
        packagedMetadata.frontierSourceCheckoutUpdaterCompatible === false,
        String(packagedMetadata.frontierSourceCheckoutUpdaterCompatible),
      );
      const packagedVersion = extractFile(asarPath, "VERSION").toString("utf8").trim();
      requirement(
        `${label} VERSION matches package metadata`,
        packagedVersion === sourceMetadata.version,
        packagedVersion,
      );
    } catch (error) {
      requirement(`${label} metadata can be extracted`, false, String(error.message || error));
    }
  }

  const unpackedModules = path.join(
    resources,
    "app.asar.unpacked",
    "node_modules",
  );
  const executableName = platform === "windows" ? "ffmpeg.exe" : "ffmpeg";
  const ffprobeName = platform === "windows" ? "ffprobe.exe" : "ffprobe";
  const ffmpeg = findNamed(unpackedModules, executableName);
  const ffprobe = findNamed(unpackedModules, ffprobeName);
  executableCheck(`${label} ffmpeg`, ffmpeg, arch, ["-version"]);
  executableCheck(`${label} ffprobe`, ffprobe, arch, ["-version"]);
  const copilotPackage =
    platform === "windows"
      ? "@github/copilot-win32-x64"
      : `@github/copilot-darwin-${arch}`;
  const copilot = path.join(
    unpackedModules,
    copilotPackage,
    platform === "windows" ? "copilot.exe" : "copilot",
  );
  executableCheck(`${label} Copilot CLI`, copilot, arch, ["--version"]);

  const nativeAddons = collectFiles(unpackedModules, (filePath) =>
    filePath.endsWith(".node"),
  );
  const badAddons = nativeAddons.filter((filePath) => {
    const architectures = binaryArchitectures(readHeader(filePath));
    return architectures.length !== 1 || architectures[0] !== arch;
  });
  requirement(
    `${label} native addon architecture scan completed`,
    badAddons.length === 0,
    nativeAddons.length
      ? `${nativeAddons.length} checked${badAddons.length ? `; bad: ${badAddons.join(", ")}` : ""}`
      : "0 native addons; ffmpeg and ffprobe checked separately",
  );

  if (platform === "macos") {
    const machPayload = collectFiles(appPath, (filePath) => {
      try {
        return binaryArchitectures(readHeader(filePath)).length > 0;
      } catch {
        return false;
      }
    });
    const badPayload = machPayload.filter((filePath) => {
      const architectures = binaryArchitectures(readHeader(filePath));
      return architectures.length !== 1 || architectures[0] !== arch;
    });
    requirement(
      `${label} every Mach-O slice is ${arch}`,
      machPayload.length >= 3 && badPayload.length === 0,
      badPayload.length
        ? badPayload.join(", ")
        : `${machPayload.length} Mach-O files checked`,
    );
  }

  if (platform === "windows") {
    const pePayload = collectFiles(appPath, (filePath) => {
      const extension = path.extname(filePath).toLowerCase();
      return [".exe", ".dll", ".node"].includes(extension) &&
        !path.basename(filePath).toLowerCase().startsWith("uninstall");
    });
    const badPayload = pePayload.filter((filePath) => {
      const architectures = binaryArchitectures(readHeader(filePath));
      return architectures.length !== 1 || architectures[0] !== arch;
    });
    requirement(
      `${label} Windows PE payload is entirely ${arch}`,
      pePayload.length >= 3 && badPayload.length === 0,
      badPayload.length
        ? badPayload.join(", ")
        : `${pePayload.length} executable payload files checked`,
    );
  }

  return { executable, resources, ffmpeg, ffprobe, copilot };
}

function entitlementEnabled(plist, entitlement) {
  const escaped = entitlement.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`<key>\\s*${escaped}\\s*</key>\\s*<true\\s*/>`, "s").test(plist);
}

function validateSourceEntitlements() {
  const main = readFileSync(path.join(betaDir, "build", "entitlements.mac.plist"), "utf8");
  const inherit = readFileSync(
    path.join(betaDir, "build", "entitlements.mac.inherit.plist"),
    "utf8",
  );
  requirement(
    "main entitlements allow Electron JIT",
    entitlementEnabled(main, "com.apple.security.cs.allow-jit"),
  );
  requirement(
    "main entitlements allow explicit microphone input",
    entitlementEnabled(main, "com.apple.security.device.audio-input"),
  );
  requirement(
    "inherited entitlements allow Electron JIT",
    entitlementEnabled(inherit, "com.apple.security.cs.allow-jit"),
  );
  for (const broadEntitlement of [
    "com.apple.security.cs.allow-unsigned-executable-memory",
    "com.apple.security.cs.disable-library-validation",
  ]) {
    requirement(
      `main entitlements omit ${broadEntitlement}`,
      !entitlementEnabled(main, broadEntitlement),
    );
    requirement(
      `inherited entitlements omit ${broadEntitlement}`,
      !entitlementEnabled(inherit, broadEntitlement),
    );
  }
}

function verifyMacSignature(filePath, label, identity, teamId, expectRuntime = false) {
  const verify = command("codesign", ["--verify", "--deep", "--strict", "--verbose=4", filePath]);
  requirement(`${label} code signature verifies`, verify.status === 0, verify.output);
  const display = command("codesign", ["-d", "--verbose=4", filePath]);
  requirement(
    `${label} uses the configured Developer ID`,
    display.output.includes(`Authority=${identity}`),
    display.output.split(/\r?\n/).filter((line) => /Authority=|TeamIdentifier=/.test(line)).join("; "),
  );
  requirement(
    `${label} is not ad-hoc signed`,
    !/Signature=adhoc/i.test(display.output),
    display.output.split(/\r?\n/).find((line) => line.includes("Signature=")) || "not ad-hoc",
  );
  requirement(
    `${label} has a secure signing timestamp`,
    /^Timestamp=/im.test(display.output),
    display.output.split(/\r?\n/).find((line) => line.startsWith("Timestamp=")) || "missing",
  );
  if (teamId) {
    requirement(
      `${label} uses Apple team ${teamId}`,
      display.output.includes(`TeamIdentifier=${teamId}`),
      display.output.split(/\r?\n/).find((line) => line.includes("TeamIdentifier=")) || "missing",
    );
  }

  if (expectRuntime) {
    requirement(
      `${label} has hardened runtime`,
      /\bflags=.*\bruntime\b/i.test(display.output),
      display.output.split(/\r?\n/).find((line) => line.includes("flags=")) || "missing",
    );
  }
}

function verifyMacBundleIdentity(appPath, applicationId, signingIdentity = null) {
  const infoPlist = path.join(appPath, "Contents", "Info.plist");
  const identifier = command("plutil", [
    "-extract",
    "CFBundleIdentifier",
    "raw",
    "-o",
    "-",
    infoPlist,
  ]);
  requirement(
    "installed macOS bundle ID matches package configuration",
    identifier.status === 0 && String(identifier.stdout || "").trim() === applicationId,
    identifier.output,
  );
  if (signingIdentity) {
    requirement(
      "macOS publisher is compatible with the bundle ID",
      publisherMatchesApplicationId(applicationId, signingIdentity),
      `${applicationId}; ${signingIdentity}`,
    );
  }
}

function verifyActualMacEntitlements(appPath) {
  const displayed = command("codesign", ["-d", "--entitlements", ":-", appPath]);
  requirement(
    "signed app entitlements are readable",
    displayed.status === 0 && displayed.output.includes("<plist"),
    displayed.status === 0 ? "plist present" : displayed.output,
  );
  const plist = displayed.output.slice(displayed.output.indexOf("<plist"));
  requirement(
    "signed app entitlement allows Electron JIT",
    entitlementEnabled(plist, "com.apple.security.cs.allow-jit"),
  );
  requirement(
    "signed app entitlement allows explicit microphone input",
    entitlementEnabled(plist, "com.apple.security.device.audio-input"),
  );
  for (const broadEntitlement of [
    "com.apple.security.cs.allow-unsigned-executable-memory",
    "com.apple.security.cs.disable-library-validation",
  ]) {
    requirement(
      `signed app omits ${broadEntitlement}`,
      !entitlementEnabled(plist, broadEntitlement),
    );
  }
}

function verifyMacNotarization(appPath, dmgPath) {
  const appStaple = command("xcrun", ["stapler", "validate", appPath]);
  requirement("app notarization ticket is stapled", appStaple.status === 0, appStaple.output);
  const dmgStaple = command("xcrun", ["stapler", "validate", dmgPath]);
  requirement("DMG notarization ticket is stapled", dmgStaple.status === 0, dmgStaple.output);
  const appAssessment = command("spctl", [
    "--assess",
    "--type",
    "execute",
    "--verbose=4",
    appPath,
  ]);
  requirement(
    "Gatekeeper accepts the app",
    appAssessment.status === 0,
    appAssessment.output,
  );
  const dmgAssessment = command("spctl", [
    "--assess",
    "--type",
    "open",
    "--context",
    "context:primary-signature",
    "--verbose=4",
    dmgPath,
  ]);
  requirement(
    "Gatekeeper accepts the DMG",
    dmgAssessment.status === 0,
    dmgAssessment.output,
  );
}

function readNotarizationEvidence(evidencePath, expectedType) {
  requirement(
    `${expectedType} notarization evidence exists`,
    existsSync(evidencePath),
    evidencePath,
  );
  if (!existsSync(evidencePath)) return null;
  let value;
  try {
    value = JSON.parse(readFileSync(evidencePath, "utf8"));
  } catch (error) {
    requirement(
      `${expectedType} notarization evidence is readable`,
      false,
      String(error.message || error),
    );
    return null;
  }
  const logPath = path.join(path.dirname(evidencePath), value.log?.name || "");
  const logExists = Boolean(value.log?.name && existsSync(logPath));
  const logDigest = logExists ? sha256(logPath) : null;
  let rawLog = null;
  if (logExists) {
    try {
      rawLog = JSON.parse(readFileSync(logPath, "utf8"));
    } catch {
      rawLog = null;
    }
  }
  const evidenceIssues = Array.isArray(value.log?.issues)
    ? value.log.issues
    : null;
  const rawIssues = Array.isArray(rawLog?.issues)
    ? rawLog.issues
    : rawLog?.issues == null
      ? []
      : null;
  requirement(
    `${expectedType} notarization result is Accepted`,
    value.submission?.status === "Accepted" &&
      value.log?.status === "Accepted" &&
      Boolean(value.submission?.id),
    JSON.stringify({
      submission: value.submission,
      log_status: value.log?.status,
    }),
  );
  requirement(
    `${expectedType} notarization log is present and clean`,
    logExists &&
      value.log?.sha256 === logDigest &&
      rawLog?.status === "Accepted" &&
      rawLog?.sha256?.toLowerCase() === value.target?.submitted_sha256 &&
      evidenceIssues?.length === 0 &&
      rawIssues?.length === 0,
    logExists
      ? `${value.log?.name}; issues=${evidenceIssues?.length ?? "invalid"}`
      : "missing log",
  );
  requirement(
    `${expectedType} notarization evidence is stapled and timestamped`,
    value.stapled === true &&
      value.target?.type === expectedType &&
      value.target?.code_signature?.ad_hoc === false &&
      Boolean(value.target?.code_signature?.timestamp),
    JSON.stringify(value.target?.code_signature || {}),
  );
  return value;
}

function verifyNotarizationEvidence(artifactPath, options) {
  const appEvidence = readNotarizationEvidence(
    `${artifactPath}.app.notarization.json`,
    "app",
  );
  const dmgEvidence = readNotarizationEvidence(
    `${artifactPath}.notarization.json`,
    "dmg",
  );
  requirement(
    "app notarization evidence binds bundle ID and Team ID",
    appEvidence?.target?.bundle_id === options.applicationId &&
      appEvidence?.target?.code_signature?.team_id === options.teamId &&
      appEvidence?.target?.code_signature?.authorities?.includes(
        options.identity,
      ),
    JSON.stringify(appEvidence?.target || {}),
  );
  requirement(
    "DMG notarization evidence binds the stapled artifact bytes",
    dmgEvidence?.target?.stapled_sha256 === sha256(artifactPath) &&
      dmgEvidence?.target?.code_signature?.authorities?.includes(
        options.identity,
      ),
    JSON.stringify(dmgEvidence?.target || {}),
  );
  evidence.notarization = {
    app: appEvidence,
    dmg: dmgEvidence,
  };
}

function verifyUnsignedMacApp(appPath, label) {
  const display = command("codesign", ["-d", "--verbose=4", appPath]);
  requirement(
    `${label} is not Developer ID signed`,
    !display.output.includes("Authority=Developer ID Application:"),
    display.output.split(/\r?\n/).filter((line) => /Authority=|Signature=/.test(line)).join("; "),
  );
}

function powershellLiteral(value) {
  return `'${String(value).replace(/'/g, "''")}'`;
}

function powershellJson(script) {
  const result = command("powershell.exe", [
    "-NoLogo",
    "-NoProfile",
    "-NonInteractive",
    "-Command",
    script,
  ]);
  if (result.status !== 0) {
    return { error: result.output, value: null };
  }
  try {
    return {
      error: null,
      value: JSON.parse(String(result.stdout || "").trim()),
    };
  } catch (error) {
    return { error: String(error.message || error), value: null };
  }
}

function windowsLifecycleState() {
  const product = powershellLiteral(productName);
  const script = [
    "$ErrorActionPreference = 'Stop'",
    `$product = ${product}`,
    "function Entries([string]$root) {",
    "  if (-not (Test-Path -LiteralPath $root)) { return @() }",
    "  return @(Get-ChildItem -LiteralPath $root -ErrorAction SilentlyContinue |",
    "    ForEach-Object { Get-ItemProperty -LiteralPath $_.PSPath } |",
    "    Where-Object { $_.DisplayName -eq $product } |",
    "    ForEach-Object { [pscustomobject]@{",
    "      Key = $_.PSChildName",
    "      DisplayName = [string]$_.DisplayName",
    "      InstallLocation = [string]$_.InstallLocation",
    "      UninstallString = [string]$_.UninstallString",
    "    } })",
    "}",
    "$userEntries = @(Entries 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall')",
    "$machineEntries = @(",
    "  Entries 'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall'",
    "  Entries 'HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall'",
    ")",
    "$desktop = [Environment]::GetFolderPath('Desktop')",
    "$programs = [Environment]::GetFolderPath('Programs')",
    "$links = @(",
    "  Get-ChildItem -LiteralPath $desktop -Filter \"$product.lnk\" -File -ErrorAction SilentlyContinue",
    "  Get-ChildItem -LiteralPath $programs -Filter \"$product.lnk\" -File -Recurse -ErrorAction SilentlyContinue",
    ")",
    "$shell = New-Object -ComObject WScript.Shell",
    "$shortcuts = @($links | ForEach-Object {",
    "  $shortcut = $shell.CreateShortcut($_.FullName)",
    "  [pscustomobject]@{",
    "    Path = $_.FullName",
    "    TargetPath = [string]$shortcut.TargetPath",
    "    Arguments = [string]$shortcut.Arguments",
    "  }",
    "})",
    "[pscustomobject]@{",
    "  UserEntries = $userEntries",
    "  MachineEntries = $machineEntries",
    "  Shortcuts = $shortcuts",
    "} | ConvertTo-Json -Depth 6 -Compress",
  ].join("\n");
  const result = powershellJson(script);
  if (result.value) {
    for (const name of ["UserEntries", "MachineEntries", "Shortcuts"]) {
      const value = result.value[name];
      result.value[name] = value == null
        ? []
        : Array.isArray(value)
          ? value
          : [value];
    }
  }
  return result;
}

function prepareSourceInstallMigrationFixture() {
  const userProfile = String(process.env.USERPROFILE || "").trim();
  const localAppData = String(process.env.LOCALAPPDATA || "").trim();
  if (!userProfile || !localAppData) {
    return {
      error: "USERPROFILE or LOCALAPPDATA is missing.",
      sentinel: null,
      shims: [],
    };
  }
  const sentinel = `SOURCE_FRONTIER_${process.pid}_${Date.now()}`;
  const shims = [
    path.join(userProfile, ".local", "bin", "brainstem-frontier.cmd"),
    path.join(
      localAppData,
      "Microsoft",
      "WindowsApps",
      "brainstem-frontier.cmd",
    ),
  ];
  for (const shim of shims) {
    mkdirSync(path.dirname(shim), { recursive: true });
    writeFileSync(shim, `@echo off\r\necho ${sentinel}\r\n`, "utf8");
  }
  const shortcutScript = [
    "$ErrorActionPreference = 'Stop'",
    `$sentinel = ${powershellLiteral(sentinel)}`,
    "$shell = New-Object -ComObject WScript.Shell",
    "$paths = @(",
    "  (Join-Path ([Environment]::GetFolderPath('Desktop')) 'RAPP Brainstem Frontier.lnk'),",
    "  (Join-Path ([Environment]::GetFolderPath('Programs')) 'RAPP Brainstem Frontier.lnk')",
    ")",
    "foreach ($shortcutPath in $paths) {",
    "  $shortcut = $shell.CreateShortcut($shortcutPath)",
    "  $shortcut.TargetPath = $env:ComSpec",
    "  $shortcut.Arguments = \"/d /c echo $sentinel\"",
    "  $shortcut.Description = 'Source-installed Frontier migration fixture'",
    "  $shortcut.Save()",
    "}",
  ].join("\n");
  const shortcutResult = command("powershell.exe", [
    "-NoLogo",
    "-NoProfile",
    "-NonInteractive",
    "-Command",
    shortcutScript,
  ]);
  return {
    error: shortcutResult.status === 0 ? null : shortcutResult.output,
    sentinel,
    shims,
  };
}

function shimsContainSentinel(fixture) {
  return fixture.shims.every(
    (shim) => existsSync(shim) && readFileSync(shim, "utf8").includes(
      fixture.sentinel,
    ),
  );
}

function shortcutTargetsInstalledExecutable(state, installedExecutable) {
  const expected = path.resolve(installedExecutable).toLowerCase();
  return (
    Array.isArray(state?.Shortcuts)
    && state.Shortcuts.length === 2
    && state.Shortcuts.every(
      (shortcut) =>
        path.resolve(shortcut.TargetPath || "").toLowerCase() === expected,
    )
  );
}

function windowsSignatureRecords(root) {
  const script = [
    "$ErrorActionPreference = 'Stop'",
    `$root = ${powershellLiteral(root)}`,
    "$records = Get-ChildItem -LiteralPath $root -Recurse -File |",
    "  Where-Object { $_.Extension -in '.exe', '.dll', '.node' } |",
    "  ForEach-Object {",
    "    $signature = Get-AuthenticodeSignature -LiteralPath $_.FullName",
    "    [pscustomobject]@{",
    "      Path = $_.FullName",
    "      Status = [string]$signature.Status",
    "      SignerSubject = [string]$signature.SignerCertificate.Subject",
    "      TimestampSubject = [string]$signature.TimeStamperCertificate.Subject",
    "    }",
    "  }",
    "$records | ConvertTo-Json -Compress",
  ].join("\n");
  const result = command("powershell.exe", [
    "-NoLogo",
    "-NoProfile",
    "-NonInteractive",
    "-Command",
    script,
  ]);
  if (result.status !== 0) {
    return { error: result.output, records: [] };
  }
  const text = String(result.stdout || "").trim();
  if (!text) return { error: "PowerShell returned no signature records.", records: [] };
  try {
    const parsed = JSON.parse(text);
    return { error: null, records: Array.isArray(parsed) ? parsed : [parsed] };
  } catch (error) {
    return { error: String(error.message || error), records: [] };
  }
}

function resolveSignTool() {
  const located = command("where.exe", ["signtool.exe"]);
  if (located.status === 0) {
    const first = String(located.stdout || "").split(/\r?\n/).find(Boolean);
    if (first && existsSync(first)) return first;
  }
  const kitsRoot = path.join(
    process.env["ProgramFiles(x86)"] || "C:\\Program Files (x86)",
    "Windows Kits",
    "10",
    "bin",
  );
  if (!existsSync(kitsRoot)) return null;
  const candidates = [];
  for (const version of readdirSync(kitsRoot, { withFileTypes: true })) {
    if (!version.isDirectory()) continue;
    const candidate = path.join(kitsRoot, version.name, "x64", "signtool.exe");
    if (existsSync(candidate)) candidates.push(candidate);
  }
  return candidates.sort((left, right) =>
    right.localeCompare(left, undefined, { numeric: true }),
  )[0] || null;
}

function verifyWithSignTool(files, label) {
  const signTool = resolveSignTool();
  if (!signTool) {
    requirement(
      `${label} passes signtool /pa /all /v /tw`,
      false,
      "signtool.exe is missing",
    );
    return;
  }
  const failures = [];
  for (const filePath of files) {
    const verification = command(signTool, [
      "verify",
      "/pa",
      "/all",
      "/v",
      "/tw",
      filePath,
    ], { timeout: 120000 });
    if (verification.status !== 0) {
      failures.push(
        `${filePath}: exit=${verification.status ?? "spawn-error"} ${verification.output}`,
      );
    }
  }
  requirement(
    `${label} passes signtool /pa /all /v /tw`,
    files.length > 0 && failures.length === 0,
    failures.length
      ? failures.slice(0, 8).join(" | ")
      : `${files.length} PE files verified`,
  );
}

function verifySignedWindowsTree(root, label, expectedPublisher) {
  const { records, error } = windowsSignatureRecords(root);
  requirement(`${label} signature inventory is readable`, !error, error || `${records.length} files`);
  requirement(`${label} contains signed PE files`, records.length >= 3, `${records.length} files`);
  const failures = records.filter(
    (record) =>
      record.Status !== "Valid" ||
      record.SignerSubject !== expectedPublisher ||
      !record.TimestampSubject,
  );
  requirement(
    `${label} PE signatures and timestamps verify`,
    records.length >= 3 && failures.length === 0,
    failures.length
      ? failures
          .slice(0, 8)
          .map(
            (record) =>
              `${record.Path}: ${record.Status}; signer=${record.SignerSubject || "none"}; ` +
              `timestamp=${record.TimestampSubject || "none"}`,
          )
          .join(" | ")
      : `${records.length} files signed by ${expectedPublisher}`,
  );
  verifyWithSignTool(
    records.map((record) => record.Path),
    label,
  );
}

function windowsFileSignature(filePath) {
  const script = [
    "$ErrorActionPreference = 'Stop'",
    `$signature = Get-AuthenticodeSignature -LiteralPath ${powershellLiteral(filePath)}`,
    "[pscustomobject]@{",
    "  Status = [string]$signature.Status",
    "  SignerSubject = [string]$signature.SignerCertificate.Subject",
    "  TimestampSubject = [string]$signature.TimeStamperCertificate.Subject",
    "} | ConvertTo-Json -Compress",
  ].join("\n");
  const result = command("powershell.exe", [
    "-NoLogo",
    "-NoProfile",
    "-NonInteractive",
    "-Command",
    script,
  ]);
  if (result.status !== 0) return { error: result.output };
  try {
    return JSON.parse(String(result.stdout || "").trim());
  } catch (error) {
    return { error: String(error.message || error) };
  }
}

function verifySignedWindowsFile(filePath, label, expectedPublisher) {
  const signature = windowsFileSignature(filePath);
  requirement(
    `${label} has a valid Artifact Signing signature`,
    !signature.error &&
      signature.Status === "Valid" &&
      signature.SignerSubject === expectedPublisher &&
      Boolean(signature.TimestampSubject),
    signature.error ||
      `${signature.Status}; signer=${signature.SignerSubject || "none"}; ` +
        `timestamp=${signature.TimestampSubject || "none"}`,
  );
  verifyWithSignTool([filePath], label);
}

function verifyUnsignedWindowsFile(filePath, label) {
  const signature = windowsFileSignature(filePath);
  requirement(
    `${label} is unsigned`,
    !signature.error && signature.Status === "NotSigned",
    signature.error || `${signature.Status}; signer=${signature.SignerSubject || "none"}`,
  );
}

function verifyNativeMediaPublication(options, packagedApp) {
  const media = evaluateNativeMedia({
    ffmpegPath: packagedApp.ffmpeg,
    ffprobePath: packagedApp.ffprobe,
    platform: options.platform,
    arch: options.arch,
  });
  evidence.nativeMedia = media;
  if (options.mode === "signed") {
    requirement(
      "native media license and provenance permit binary publication",
      media.publication_ready,
      media.blockers.join(" | "),
    );
  } else {
    requirement(
      "native media publication status is recorded",
      true,
      media.publication_ready
        ? "approved"
        : `BLOCKED: ${media.blockers.join(" | ")}`,
    );
  }
}

function delay(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function sanitizedSmokeEnvironment(runtime, metadataPath, statusPath) {
  const env = { ...process.env };
  for (const name of Object.keys(env)) {
    if (
      /^(APPLE_|AZURE_|CSC_|GH_TOKEN$|GITHUB_TOKEN$|MACOS_CERTIFICATE_|WINDOWS_SIGNING_)/.test(
        name,
      )
    ) {
      delete env[name];
    }
  }
  delete env.GIT_DISCOVERY_ACROSS_FILESYSTEM;
  return {
    ...env,
    HOME: runtime.home,
    USERPROFILE: runtime.home,
    BRAINSTEM_HOME: runtime.brainstemHome,
    BRAINSTEM_BETA_HEADLESS: "1",
    BRAINSTEM_BETA_HOME: runtime.betaHome,
    BRAINSTEM_BETA_PYTHON: runtime.pythonPath,
    BRAINSTEM_BETA_SOURCE_DIR: runtime.isolatedSource,
    BRAINSTEM_BETA_SMOKE_EXIT_MS: "840000",
    BRAINSTEM_BETA_SMOKE_EXIT_ON_READY: "1",
    BRAINSTEM_BETA_SMOKE_REQUIRE_READY: "1",
    BRAINSTEM_BETA_SMOKE_STATUS_FILE: statusPath,
    BRAINSTEM_BETA_CAPTURE_USER_DATA_PATH: "1",
    BRAINSTEM_BETA_USER_DATA_DIR: path.join(
      runtime.home,
      "electron-user-data",
    ),
    BRAINSTEM_BETA_UI_DRIVER_FILE: metadataPath,
    BRAINSTEM_LAN_MODE: "0",
  };
}

function launchInstalledApp({ executable, env }) {
  return {
    child: spawn(executable, [], {
      env,
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    }),
    outputPaths: [],
  };
}

function collectChildOutput(child) {
  let output = "";
  const append = (chunk) => {
    output = `${output}${String(chunk)}`.slice(-12000);
  };
  child.stdout?.on("data", append);
  child.stderr?.on("data", append);
  return () => output;
}

async function waitForChildExit(child, timeoutMs) {
  if (child.exitCode !== null) {
    return { code: child.exitCode, signal: child.signalCode };
  }
  return Promise.race([
    new Promise((resolve) => {
      child.once("exit", (code, signal) => resolve({ code, signal }));
    }),
    delay(timeoutMs).then(() => null),
  ]);
}

async function fetchJson(url, options = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      signal: AbortSignal.timeout(1500),
    });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

async function waitForUiDriver(metadataPath, child, timeoutMs = 25000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline && child.exitCode === null) {
    if (existsSync(metadataPath)) {
      try {
        const metadata = JSON.parse(readFileSync(metadataPath, "utf8"));
        if (
          metadata.host === "127.0.0.1" &&
          Number.isInteger(metadata.port) &&
          metadata.token
        ) {
          return metadata;
        }
      } catch {
        // The atomic metadata write might still be settling.
      }
    }
    await delay(250);
  }
  return null;
}

async function waitForSmokeStatus(statusPath, child, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (existsSync(statusPath)) {
      try {
        return JSON.parse(readFileSync(statusPath, "utf8"));
      } catch {
        // The status file might still be settling.
      }
    }
    if (child.exitCode !== null) break;
    await delay(250);
  }
  return null;
}

async function waitForRoutedBrainstem(metadata, child, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;
  const commandUrl = `http://${metadata.host}:${metadata.port}/v1/command`;
  while (Date.now() < deadline && child.exitCode === null) {
    const telemetry = await fetchJson(commandUrl, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${metadata.token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ action: "route_telemetry" }),
    });
    const routeUrl = telemetry?.result?.active_route?.url;
    if (routeUrl) {
      const health = await fetchJson(`${routeUrl}/health`);
      if (health) return { health, routeUrl, telemetry: telemetry.result };
    }
    await delay(300);
  }
  return null;
}

async function endpointResponds(url) {
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(1000) });
    return response.ok;
  } catch {
    return false;
  }
}

async function smokeApp({
  executable,
  scratchDir,
  brainstemPython,
  brainstemSource,
  packagedResources,
  applicationId,
  platform,
  arch,
  mode,
  appDir,
  releaseTag,
  releaseCommit,
  runtimeVersionUrl,
}) {
  if (platform === "macos" && mode === "unsigned") {
    const canonicalGate = command(
      process.execPath,
      [path.join(betaDir, "scripts", "package-first-run-gate.mjs")],
      {
        env: {
          ...process.env,
          FRONTIER_FIRST_RUN_APP_DIR: appDir,
          FRONTIER_FIRST_RUN_ARCH: arch,
          FRONTIER_FIRST_RUN_PRODUCT_NAME: productName,
        },
        timeout: 4 * 60 * 1000,
        maxBuffer: 4 * 1024 * 1024,
      },
    );
    const summary = canonicalGate.output.match(
      /PACKAGE READY — (\d+)\/(\d+) pass/,
    );
    requirement(
      "canonical first-run/concurrent package gate passes",
      canonicalGate.status === 0
        && Boolean(summary)
        && summary[1] === summary[2],
      canonicalGate.output.slice(-12000),
    );
    const provenance = JSON.parse(
      readFileSync(
        path.join(packagedResources, "bootstrap", "provenance.json"),
        "utf8",
      ),
    );
    evidence.bootstrap = {
      executed: canonicalGate.status === 0,
      authority_mode: "controlled-development-fixture",
      installed_commit: provenance.commit,
      manifest: provenance,
      canonical_first_run_checks: summary
        ? { passed: Number(summary[1]), total: Number(summary[2]) }
        : null,
    };
    evidence.runtime = {
      service_ready: canonicalGate.status === 0,
      service_stopped: canonicalGate.status === 0,
      isolated_home: true,
      first_run_fixture: true,
      concurrent_smokes: 2,
      user_data_measured: true,
      copilot_auth_startup: canonicalGate.status === 0,
    };
    return;
  }

  const bootstrapDirectory = path.join(packagedResources, "bootstrap");
  let bundle = null;
  let rawProvenance = null;
  try {
    rawProvenance = JSON.parse(
      readFileSync(path.join(bootstrapDirectory, "provenance.json"), "utf8"),
    );
    bundle = loadBootstrapBundle({
      directory: bootstrapDirectory,
      platform: platform === "windows" ? "win32" : "darwin",
    });
    requirement(
      "packaged bootstrap bytes match immutable provenance",
      true,
      `${bundle.provenance.mode}:${bundle.provenance.commit}`,
    );
  } catch (error) {
    requirement(
      "packaged bootstrap bytes match immutable provenance",
      false,
      String(error.message || error),
    );
  }
  if (!bundle) {
    requirement("packaged app starts a ready Brainstem service", false, "bootstrap unavailable");
    requirement("final installed app exits cleanly", false, "bootstrap unavailable");
    return;
  }

  if (mode === "signed") {
    const expectedRuntimeVersionUrl =
      `https://raw.githubusercontent.com/microsoft/aibast-agents-library/`
      + `${releaseCommit}/rapp_brainstem/VERSION`;
    requirement(
      "sealed release bootstrap uses canonical immutable authority",
      bundle.provenance.mode === "release"
        && bundle.provenance.repositoryUrl
          === "https://github.com/microsoft/aibast-agents-library.git"
        && bundle.provenance.commit === releaseCommit
        && bundle.provenance.sourceRef === releaseTag
        && rawProvenance?.authority?.requestedMode === "release"
        && rawProvenance?.authority?.releaseTag === releaseTag
        && runtimeVersionUrl === expectedRuntimeVersionUrl,
      `${releaseTag || "missing"}@${releaseCommit || "missing"}`,
    );
  }

  const home = path.join(scratchDir, "home");
  const brainstemHome = path.join(home, ".brainstem");
  const isolatedSource = path.join(brainstemHome, "src", "rapp_brainstem");
  requirement(
    "package bootstrap begins without BRAINSTEM_HOME",
    !existsSync(brainstemHome),
    brainstemHome,
  );
  if (existsSync(brainstemHome)) return;
  mkdirSync(home, { recursive: true });
  const runtime = {
    home,
    brainstemHome,
    betaHome: path.join(brainstemHome, "beta-launcher"),
    isolatedSource,
    pythonPath:
      platform === "windows"
        ? path.join(brainstemHome, "venv", "Scripts", "python.exe")
        : path.join(brainstemHome, "venv", "bin", "python"),
    expectedVersion: readFileSync(
      path.join(brainstemSource, "VERSION"),
      "utf8",
    ).trim(),
  };
  evidence.bootstrap = {
    executed: false,
    authority_mode:
      bundle.provenance.mode === "release"
        ? "canonical-release"
        : "development",
    installed_commit: bundle.provenance.commit,
    release_tag:
      bundle.provenance.mode === "release" ? releaseTag : null,
    manifest: rawProvenance,
  };

  const metadataPath = path.join(runtime.betaHome, "ui-driver.json");
  const statusPath = path.join(runtime.betaHome, "package-smoke-status.json");
  const env = sanitizedSmokeEnvironment(runtime, metadataPath, statusPath);
  const launched = launchInstalledApp({
    executable,
    env,
  });
  const child = launched.child;
  const childOutput = collectChildOutput(child);
  let metadata = null;
  try {
  metadata = await waitForUiDriver(metadataPath, child, 12 * 60 * 1000);
  requirement(
    "installed app launches from the platform package",
    Boolean(metadata),
    metadata ? `${metadata.host}:${metadata.port}; pid=${metadata.pid}` : childOutput(),
  );

  const ready = metadata
    ? await waitForRoutedBrainstem(metadata, child, 2 * 60 * 1000)
    : null;
  const health = ready?.health;
  const serviceReady = Boolean(
    health &&
      ["ok", "unauthenticated"].includes(health.status) &&
      health.version === runtime.expectedVersion &&
      Array.isArray(health.agents) &&
      health.agents.includes("ContextMemory") &&
      typeof health.soul === "string" &&
      path.resolve(health.soul).startsWith(`${runtime.isolatedSource}${path.sep}`),
  );
  requirement(
    "packaged app starts a ready Brainstem service",
    serviceReady,
    health ? JSON.stringify(health) : childOutput(),
  );

  let frontendReady = false;
  let modelsReady = false;
  if (ready?.routeUrl) {
    try {
      const frontend = await fetch(ready.routeUrl, {
        signal: AbortSignal.timeout(1500),
      });
      frontendReady = frontend.ok && (await frontend.text()).includes("RAPP Brainstem");
    } catch {
      frontendReady = false;
    }
    modelsReady = await endpointResponds(`${ready.routeUrl}/models`);
  }
  requirement("routed Brainstem frontend is ready", frontendReady, ready?.routeUrl || "missing");
  requirement("routed Brainstem models endpoint is ready", modelsReady, ready?.routeUrl || "missing");
  const smokeStatus = await waitForSmokeStatus(
    statusPath,
    child,
    2 * 60 * 1000,
  );
  const copilotAuthStarted = Boolean(
    ["ready", "signed-out"].includes(smokeStatus?.copilot?.phase) &&
    ["ready", "signed-out"].includes(smokeStatus?.surgeon?.phase) &&
    smokeStatus?.brainstem?.phase === "ready" &&
    smokeStatus?.url === ready?.routeUrl &&
    smokeStatus?.requestedUserData === env.BRAINSTEM_BETA_USER_DATA_DIR &&
    smokeStatus?.actualUserData === env.BRAINSTEM_BETA_USER_DATA_DIR,
  );
  requirement(
    "packaged Copilot CLI auth startup completes",
    copilotAuthStarted,
    smokeStatus ? JSON.stringify(smokeStatus) : "status file missing",
  );

  const exit = await waitForChildExit(child, 30000);
  if (!exit) {
    if (metadata?.pid) {
      try {
        process.kill(metadata.pid, "SIGTERM");
      } catch {
        // The application may have exited between the timeout and cleanup.
      }
    }
    child.kill();
  }
  const output = [
    childOutput(),
    ...launched.outputPaths
      .filter(existsSync)
      .map((filePath) => readFileSync(filePath, "utf8")),
  ]
    .filter(Boolean)
    .join("\n")
    .slice(-12000);
  requirement(
    "final installed app exits cleanly",
    Boolean(exit && exit.code === 0),
    exit ? `code=${exit.code}; signal=${exit.signal || "none"}` : output,
  );

  let stopped = !ready?.routeUrl;
  if (ready?.routeUrl) {
    const deadline = Date.now() + 10000;
    while (Date.now() < deadline) {
      if (!(await endpointResponds(`${ready.routeUrl}/health`))) {
        stopped = true;
        break;
      }
      await delay(250);
    }
  }
  requirement("Brainstem service stops with the installed app", stopped, ready?.routeUrl || "missing");
  requirement(
    "UI driver metadata is removed on shutdown",
    !existsSync(metadataPath),
    metadataPath,
  );

  const installedCommit = existsSync(path.join(brainstemHome, "src", ".git"))
    ? command("git", [
        "-C",
        path.join(brainstemHome, "src"),
        "rev-parse",
        "HEAD",
      ])
    : { status: 1, stdout: "", output: "installed source missing" };
  const exactCommit =
    installedCommit.status === 0
    && String(installedCommit.stdout || "").trim()
      === bundle.provenance.commit;
  requirement(
    "packaged bootstrap installed the exact provenance commit",
    exactCommit,
    String(installedCommit.stdout || installedCommit.output || "").trim(),
  );
  evidence.bootstrap.executed = Boolean(
    smokeStatus?.provisioned && exactCommit,
  );

  evidence.runtime = {
    service_ready: serviceReady && frontendReady && modelsReady,
    service_stopped: stopped,
    isolated_home: true,
    brainstem_home: brainstemHome,
    health: health || null,
    route_url: ready?.routeUrl || null,
    python: "3.11",
    protocol: "RAPP/1",
    copilot_auth_startup: copilotAuthStarted,
    copilot_phase: smokeStatus?.copilot?.phase || null,
    requested_user_data: smokeStatus?.requestedUserData || null,
    actual_user_data: smokeStatus?.actualUserData || null,
  };
  } finally {
    if (child.exitCode === null) {
      if (metadata?.pid) {
        try {
          process.kill(metadata.pid, "SIGTERM");
        } catch {
          // The application may already be exiting.
        }
      }
      child.kill();
      await waitForChildExit(child, 5000);
    }
  }
}

async function gateMac(options, artifactPath, appDir, scratchDir) {
  validateSourceEntitlements();
  const staging = inspectPackagedApp(
    appDir,
    "staging macOS app",
    "macos",
    options.arch,
    true,
  );

  if (options.mode === "signed") {
    verifyMacSignature(
      artifactPath,
      "DMG",
      options.identity,
      null,
      false,
    );
    verifyMacSignature(
      appDir,
      "staging macOS app",
      options.identity,
      options.teamId,
      true,
    );
    for (const [label, executable] of [
      ["staging ffmpeg", staging.ffmpeg],
      ["staging ffprobe", staging.ffprobe],
      ["staging Copilot CLI", staging.copilot],
    ]) {
      if (executable) {
        verifyMacSignature(executable, label, options.identity, options.teamId, true);
      } else {
        requirement(`${label} code signature verifies`, false, "missing");
      }
    }
  } else {
    verifyUnsignedMacApp(appDir, "staging macOS app");
  }

  const mountPoint = path.join(scratchDir, "mounted-dmg");
  const installedApp = path.join(
    scratchDir,
    "Applications",
    `${productName}.app`,
  );
  mkdirSync(mountPoint, { recursive: true });
  const imageVerify = command("hdiutil", ["verify", artifactPath], {
    timeout: 120000,
  });
  requirement(
    "DMG passes hdiutil verification",
    imageVerify.status === 0,
    imageVerify.output,
  );
  let mounted = false;
  try {
    const attach = command("hdiutil", [
      "attach",
      artifactPath,
      "-nobrowse",
      "-readonly",
      "-mountpoint",
      mountPoint,
    ]);
    mounted = attach.status === 0;
    requirement("DMG mounts read-only", mounted, attach.output);

    const finalApp = path.join(mountPoint, `${productName}.app`);
    inspectPackagedApp(
      finalApp,
      "app inside DMG",
      "macos",
      options.arch,
    );
    if (options.mode === "signed") {
      verifyMacSignature(
        finalApp,
        "app inside DMG",
        options.identity,
        options.teamId,
        true,
      );
    } else {
      verifyUnsignedMacApp(finalApp, "app inside DMG");
    }
    mkdirSync(path.dirname(installedApp), { recursive: true });
    const install = command("ditto", [finalApp, installedApp], { timeout: 120000 });
    requirement("DMG app installs into isolated Applications", install.status === 0, install.output);
    evidence.installation = {
      method: "dmg-mount-and-ditto",
      source: finalApp,
      installed_path: installedApp,
    };
  } finally {
    if (mounted) {
      const detach = command("hdiutil", ["detach", mountPoint]);
      requirement("DMG detaches cleanly", detach.status === 0, detach.output);
    } else {
      requirement("DMG detaches cleanly", false, "DMG never mounted");
    }
  }

  const installed = inspectPackagedApp(
    installedApp,
    "installed macOS app",
    "macos",
    options.arch,
  );
  verifyMacBundleIdentity(
    installedApp,
    options.applicationId,
    options.mode === "signed" ? options.identity : null,
  );
  if (options.mode === "signed") {
    verifyMacSignature(
      installedApp,
      "installed macOS app",
      options.identity,
      options.teamId,
      true,
    );
    verifyActualMacEntitlements(installedApp);
    verifyMacNotarization(installedApp, artifactPath);
    verifyNotarizationEvidence(artifactPath, options);
  } else {
    verifyUnsignedMacApp(installedApp, "installed macOS app");
  }
  verifyNativeMediaPublication(options, installed);
  if (existsSync(installed.executable)) {
    await smokeApp({
      executable: installed.executable,
      scratchDir,
      brainstemPython: options.brainstemPython,
      brainstemSource: options.brainstemSource,
      packagedResources: installed.resources,
      applicationId: options.applicationId,
      platform: "macos",
      arch: options.arch,
      mode: options.mode,
      appDir: installedApp,
      releaseTag: options.releaseTag,
      releaseCommit: options.releaseCommit,
      runtimeVersionUrl: options.runtimeVersionUrl,
    });
  } else {
    requirement("installed app launches from the platform package", false, "missing executable");
    requirement("packaged app starts a ready Brainstem service", false, "missing executable");
    requirement("final installed app exits cleanly", false, "missing executable");
  }
}

async function gateWindows(options, artifactPath, appDir, scratchDir) {
  if (options.requireStandardUser) {
    const membership = command("powershell.exe", [
      "-NoLogo",
      "-NoProfile",
      "-NonInteractive",
      "-Command",
      "$p=[Security.Principal.WindowsPrincipal]::new(" +
        "[Security.Principal.WindowsIdentity]::GetCurrent());" +
        "$p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)",
    ]);
    requirement(
      "Windows package gate runs as a standard user",
      membership.status === 0 &&
        String(membership.stdout || "").trim().toLowerCase() === "false",
      membership.output,
    );
    evidence.standardUser =
      membership.status === 0 &&
      String(membership.stdout || "").trim().toLowerCase() === "false";
  }
  const updaterMetadata = readdirSync(path.dirname(artifactPath)).filter(
    (entry) =>
      entry.endsWith(".blockmap") ||
      /^latest.*\.ya?ml$/i.test(entry),
  );
  requirement(
    "Windows package does not publish updater metadata",
    updaterMetadata.length === 0,
    updaterMetadata.join(", "),
  );
  const staging = inspectPackagedApp(
    appDir,
    "staging Windows app",
    "windows",
    options.arch,
    true,
  );
  if (options.mode === "signed") {
    requirement(
      "Windows signing configuration uses Azure Public Trust",
      process.env.AZURE_ARTIFACT_SIGNING_PROFILE_TYPE === "PublicTrust" &&
        Boolean(process.env.AZURE_ARTIFACT_SIGNING_ENDPOINT) &&
        Boolean(process.env.AZURE_ARTIFACT_SIGNING_ACCOUNT_NAME) &&
        Boolean(process.env.AZURE_ARTIFACT_SIGNING_CERTIFICATE_PROFILE_NAME),
      process.env.AZURE_ARTIFACT_SIGNING_PROFILE_TYPE || "missing",
    );
    requirement(
      "Windows publisher is compatible with the application ID",
      publisherMatchesApplicationId(
        options.applicationId,
        options.expectedPublisher,
      ),
      `${options.applicationId}; ${options.expectedPublisher}`,
    );
    verifySignedWindowsFile(artifactPath, "NSIS installer", options.expectedPublisher);
    verifySignedWindowsTree(appDir, "staging Windows app", options.expectedPublisher);
  } else {
    verifyUnsignedWindowsFile(artifactPath, "NSIS installer");
    verifyUnsignedWindowsFile(staging.executable, "staging Windows app");
  }

  const sourceFixture = prepareSourceInstallMigrationFixture();
  requirement(
    "source-installed shortcut and shim migration fixture is ready",
    !sourceFixture.error && shimsContainSentinel(sourceFixture),
    sourceFixture.error || sourceFixture.shims.join(", "),
  );

  const installDir = path.join(scratchDir, "installed");
  mkdirSync(installDir, { recursive: true });
  if (options.mode === "signed" && options.previousInstaller) {
    const previousInstaller = path.resolve(options.previousInstaller);
    requirement(
      "N-1 Windows installer exists",
      existsSync(previousInstaller),
      previousInstaller,
    );
    if (existsSync(previousInstaller)) {
      verifySignedWindowsFile(
        previousInstaller,
        "N-1 NSIS installer",
        options.expectedPublisher,
      );
      const previousInstall = command(
        previousInstaller,
        ["/S", `/D=${installDir}`],
        { timeout: 120000 },
      );
      const previousState = windowsLifecycleState();
      requirement(
        "N-1 installer establishes one per-user entry and no machine entry",
        previousInstall.status === 0
          && !previousState.error
          && previousState.value?.UserEntries?.length === 1
          && previousState.value?.MachineEntries?.length === 0,
        previousState.error || previousInstall.output,
      );
      evidence.windowsUpgrade = {
        passed:
          previousInstall.status === 0
          && !previousState.error
          && previousState.value?.UserEntries?.length === 1
          && previousState.value?.MachineEntries?.length === 0,
        mode: "n-minus-one-to-n",
        previous_release_tag: options.previousReleaseTag,
        previous_installer_sha256: sha256(previousInstaller),
      };
    }
  } else if (options.mode === "signed") {
    requirement(
      "first binary release is explicitly recorded when no N-1 exists",
      options.firstBinaryRelease === true,
      String(options.firstBinaryRelease),
    );
    evidence.windowsUpgrade = {
      passed: options.firstBinaryRelease === true,
      mode: "first-binary-release",
      previous_release_tag: null,
      previous_installer_sha256: null,
    };
  } else {
    evidence.windowsUpgrade = {
      passed: true,
      mode: "unsigned-verification",
      previous_release_tag: null,
      previous_installer_sha256: null,
    };
  }

  const install = command(artifactPath, ["/S", `/D=${installDir}`], {
    timeout: 120000,
  });
  requirement("NSIS installer completes silently", install.status === 0, install.output);

  const installedExecutable = findNamed(installDir, `${productName}.exe`);
  const installedAppDir = installedExecutable ? path.dirname(installedExecutable) : installDir;
  const installedState = windowsLifecycleState();
  const perUserInstalled = Boolean(
    !installedState.error
      && installedState.value?.UserEntries?.length === 1
      && installedState.value?.MachineEntries?.length === 0,
  );
  requirement(
    "NSIS install creates exactly one HKCU entry and no HKLM entry",
    perUserInstalled,
    installedState.error || JSON.stringify(installedState.value),
  );
  requirement(
    "native shortcuts replace source shortcuts with the installed executable",
    Boolean(
      installedExecutable
      && shortcutTargetsInstalledExecutable(
        installedState.value,
        installedExecutable,
      ),
    ),
    JSON.stringify(installedState.value?.Shortcuts || []),
  );
  requirement(
    "source-installed command shims remain intact during native migration",
    shimsContainSentinel(sourceFixture),
    sourceFixture.shims.join(", "),
  );
  evidence.installation = {
    method: "nsis-silent-install",
    source: artifactPath,
    installed_path: installDir,
    user_registry_entries: installedState.value?.UserEntries?.length ?? null,
    machine_registry_entries:
      installedState.value?.MachineEntries?.length ?? null,
    shortcuts: installedState.value?.Shortcuts || [],
  };
  const installed = inspectPackagedApp(
    installedAppDir,
    "installed Windows app",
    "windows",
    options.arch,
  );
  if (options.mode === "signed") {
    verifySignedWindowsTree(
      installedAppDir,
      "installed Windows app",
      options.expectedPublisher,
    );
  } else if (installed.executable) {
    verifyUnsignedWindowsFile(installed.executable, "installed Windows app");
  }
  verifyNativeMediaPublication(options, installed);
  if (installedExecutable) {
    await smokeApp({
      executable: installedExecutable,
      scratchDir,
      brainstemPython: options.brainstemPython,
      brainstemSource: options.brainstemSource,
      packagedResources: installed.resources,
      applicationId: options.applicationId,
      platform: "windows",
      arch: options.arch,
      mode: options.mode,
      appDir: installedAppDir,
      releaseTag: options.releaseTag,
      releaseCommit: options.releaseCommit,
      runtimeVersionUrl: options.runtimeVersionUrl,
    });
  } else {
    requirement("installed app launches from the platform package", false, "missing executable");
    requirement("packaged app starts a ready Brainstem service", false, "missing executable");
    requirement("final installed app exits cleanly", false, "missing executable");
  }

  const reinstall = command(artifactPath, ["/S", `/D=${installDir}`], {
    timeout: 120000,
  });
  const reinstalledState = windowsLifecycleState();
  const singleReinstallEntry = Boolean(
    reinstall.status === 0
      && !reinstalledState.error
      && reinstalledState.value?.UserEntries?.length === 1
      && reinstalledState.value?.MachineEntries?.length === 0
      && installedExecutable
      && shortcutTargetsInstalledExecutable(
        reinstalledState.value,
        installedExecutable,
      ),
  );
  requirement(
    "reinstall preserves one per-user entry and one native shortcut set",
    singleReinstallEntry,
    reinstalledState.error || reinstall.output,
  );

  const brainstemSentinel = evidence.runtime?.brainstem_home
    ? path.join(evidence.runtime.brainstem_home, "package-gate-preserve.txt")
    : null;
  const userDataSentinel = evidence.runtime?.actual_user_data
    ? path.join(evidence.runtime.actual_user_data, "package-gate-preserve.txt")
    : null;
  for (const sentinel of [brainstemSentinel, userDataSentinel].filter(Boolean)) {
    mkdirSync(path.dirname(sentinel), { recursive: true });
    writeFileSync(sentinel, "preserve\n", "utf8");
  }

  const uninstaller = collectFiles(
    installDir,
    (filePath) =>
      path.extname(filePath).toLowerCase() === ".exe" &&
      path.basename(filePath).toLowerCase().startsWith("uninstall"),
  )[0];
  requirement("NSIS uninstaller exists", Boolean(uninstaller), uninstaller || "missing");
  if (uninstaller) {
    if (options.mode === "signed") {
      verifySignedWindowsFile(
        uninstaller,
        "NSIS uninstaller",
        options.expectedPublisher,
      );
    }
    const uninstall = command(uninstaller, ["/S"], { timeout: 120000 });
    requirement("NSIS uninstaller completes silently", uninstall.status === 0, uninstall.output);
  } else {
    requirement("NSIS uninstaller completes silently", false, "missing");
  }
  await delay(1000);
  const uninstalledState = windowsLifecycleState();
  const installedFilesRemoved =
    !existsSync(path.join(installedAppDir, `${productName}.exe`))
    && !existsSync(path.join(installedAppDir, "resources"))
    && !collectFiles(
      installDir,
      (filePath) => path.extname(filePath).toLowerCase() === ".exe",
    ).length;
  requirement(
    "uninstall removes installed executable, resources, and uninstaller",
    installedFilesRemoved,
    installDir,
  );
  const registryAndShortcutsRemoved = Boolean(
    !uninstalledState.error
      && uninstalledState.value?.UserEntries?.length === 0
      && uninstalledState.value?.MachineEntries?.length === 0
      && uninstalledState.value?.Shortcuts?.length === 0,
  );
  requirement(
    "uninstall removes per-user registry entry and native shortcuts",
    registryAndShortcutsRemoved,
    uninstalledState.error || JSON.stringify(uninstalledState.value),
  );
  const sharedBrainstemPreserved = Boolean(
    brainstemSentinel && existsSync(brainstemSentinel),
  );
  const userDataPreserved = Boolean(
    userDataSentinel && existsSync(userDataSentinel),
  );
  requirement(
    "uninstall preserves shared Brainstem runtime",
    sharedBrainstemPreserved,
    brainstemSentinel || "missing runtime path",
  );
  requirement(
    "uninstall preserves Frontier user data",
    userDataPreserved,
    userDataSentinel || "missing userData path",
  );
  const sourceMigrationSafe = Boolean(
    shimsContainSentinel(sourceFixture)
      && uninstalledState.value?.Shortcuts?.length === 0,
  );
  requirement(
    "uninstall leaves source command shims usable without stale shortcuts",
    sourceMigrationSafe,
    sourceFixture.shims.join(", "),
  );
  evidence.windowsLifecycle = {
    passed:
      perUserInstalled
      && singleReinstallEntry
      && installedFilesRemoved
      && registryAndShortcutsRemoved
      && sharedBrainstemPreserved
      && userDataPreserved
      && sourceMigrationSafe,
    per_user_registry_only: perUserInstalled,
    machine_registry_entries:
      installedState.value?.MachineEntries?.length ?? null,
    reinstall_single_entry: singleReinstallEntry,
    installed_files_removed: installedFilesRemoved,
    registry_and_shortcuts_removed: registryAndShortcutsRemoved,
    shared_brainstem_preserved: sharedBrainstemPreserved,
    user_data_preserved: userDataPreserved,
    source_migration_safe: sourceMigrationSafe,
  };
  for (const shim of sourceFixture.shims) rmSync(shim, { force: true });
}

export function defaultGatePaths(options, version) {
  const outputName = artifactName({ ...options, version });
  const appDir =
    options.platform === "windows"
      ? path.join(releaseDir, "win-unpacked")
      : path.join(
          releaseDir,
          options.arch === "arm64" ? "mac-arm64" : "mac",
          `${productName}.app`,
        );
  return {
    artifact: path.join(releaseDir, outputName),
    appDir,
    scratchDir: path.join(
      releaseDir,
      `package-gate-${options.platform}-${options.arch}-${options.mode}`,
    ),
    report: path.join(releaseDir, `${outputName}.gate.json`),
  };
}

function defaultBrainstemPython(platform) {
  if (process.env.BRAINSTEM_PACKAGE_GATE_PYTHON) {
    return path.resolve(process.env.BRAINSTEM_PACKAGE_GATE_PYTHON);
  }
  return path.join(
    homedir(),
    ".brainstem",
    "venv",
    platform === "windows" ? path.join("Scripts", "python.exe") : path.join("bin", "python"),
  );
}

function signingEvidence(options, failures) {
  const signingChecks = results.filter((result) =>
    /signature|Developer ID|Apple team|hardened runtime|notarization|Gatekeeper|is unsigned|not Developer ID signed/i.test(
      result.name,
    ),
  );
  const value = {
    provider:
      options.mode === "unsigned"
        ? "none"
        : options.platform === "macos"
          ? "Apple Developer ID"
          : "Azure Artifact Signing",
    identity:
      options.mode === "unsigned"
        ? null
        : options.platform === "macos"
          ? options.identity
          : options.expectedPublisher,
    verified:
      failures.length === 0 &&
      signingChecks.length > 0 &&
      signingChecks.every((result) => result.pass),
    checks: signingChecks.map((result) => ({
      name: result.name,
      passed: result.pass,
    })),
  };
  if (options.platform === "windows" && options.mode === "signed") {
    value.backend_schema =
      "electron-builder-26.15.7/custom-ArtifactSigning-0.1.8/v1";
    value.endpoint =
      process.env.AZURE_ARTIFACT_SIGNING_ENDPOINT || null;
    value.account =
      process.env.AZURE_ARTIFACT_SIGNING_ACCOUNT_NAME || null;
    value.certificate_profile =
      process.env.AZURE_ARTIFACT_SIGNING_CERTIFICATE_PROFILE_NAME || null;
    value.profile_type =
      process.env.AZURE_ARTIFACT_SIGNING_PROFILE_TYPE || null;
    value.file_digest = "SHA256";
    value.timestamp_digest = "SHA256";
    value.timestamp_url = "http://timestamp.acs.microsoft.com/";
  }

  return value;
}

function publicationEvidence(options) {
  const blockers = [
    ...(evidence.nativeMedia?.blockers || [
      "Native media publication evidence was not produced.",
    ]),
  ];
  if (evidence.bootstrap?.manifest?.publication?.ready !== true) {
    blockers.push(
      ...(evidence.bootstrap?.manifest?.publication?.blockers || [
        "Package bootstrap publication is not approved.",
      ]),
    );
  }
  if (options.platform === "windows") {
    const policy = JSON.parse(
      readFileSync(
        path.join(betaDir, "build", "windows-signing-policy.json"),
        "utf8",
      ),
    );
    if (policy.publication_enabled !== true) {
      blockers.push(
        policy.publication_blocker ||
        "Windows signing backend publication is not approved.",
      );
    }
  }
  return {
    status: blockers.length ? "blocked" : "ready",
    blockers,
  };
}

function gateReport({
  options,
  artifactPath,
  packageMetadata,
  electronVersion,
  nativeVersions,
  reportPath,
}) {
  const failures = results.filter((result) => !result.pass);
  const runtimeMinimum =
    options.platform === "macos"
      ? { name: "macOS", minimum_version: "12.0" }
      : { name: "Windows", minimum_version: "11" };
  return {
    schema: "https://github.com/microsoft/aibast-agents-library/frontier-package-gate/v1",
    generated_at: new Date().toISOString(),
    artifact: {
      name: path.basename(artifactPath),
      sha256: existsSync(artifactPath) ? sha256(artifactPath) : null,
      size: existsSync(artifactPath) ? statSync(artifactPath).size : 0,
      os: options.platform,
      arch: options.arch,
      signing_mode: options.mode,
    },
    source: {
      version: packageMetadata.version,
      application_id: options.applicationId,
      product_name: productName,
    },
    runtime_compatibility: {
      operating_system: runtimeMinimum,
      architecture: options.arch,
      electron: electronVersion,
      node_engine: packageMetadata.engines.node,
      native_dependencies: nativeVersions,
      brainstem: {
        python: "3.11",
        protocol: "RAPP/1",
        version: evidence.runtime?.health?.version || null,
      },
      update_channel: "binary-release-manifest-v1",
      source_checkout_updater_compatible: false,
    },
    signing: signingEvidence(options, failures),
    bootstrap: evidence.bootstrap,
    publication: publicationEvidence(options),
    native_media: evidence.nativeMedia,
    notarization: evidence.notarization,
    installation: evidence.installation,
    runtime: evidence.runtime,
    execution: {
      windows_standard_user:
        options.platform === "windows" ? evidence.standardUser : null,
      windows_lifecycle:
        options.platform === "windows" ? evidence.windowsLifecycle : null,
      windows_upgrade:
        options.platform === "windows" ? evidence.windowsUpgrade : null,
    },
    gate: {
      status: failures.length ? "failed" : "passed",
      passed: results.length - failures.length,
      total: results.length,
      failures: failures.map((result) => ({
        name: result.name,
        detail: result.detail,
      })),
      checks: results.map((result) => ({
        name: result.name,
        passed: result.pass,
        detail: result.detail,
      })),
    },
    report: {
      name: path.basename(reportPath),
    },
  };
}

export async function runPackageGate(argv = process.argv.slice(2)) {
  results.length = 0;
  evidence.installation = null;
  evidence.bootstrap = null;
  evidence.nativeMedia = null;
  evidence.notarization = null;
  evidence.runtime = null;
  evidence.standardUser = null;
  evidence.windowsLifecycle = null;
  evidence.windowsUpgrade = null;
  const options = parseGateArguments(argv);
  const packageMetadata = JSON.parse(
    readFileSync(path.join(betaDir, "package.json"), "utf8"),
  );
  const packageLock = JSON.parse(
    readFileSync(path.join(betaDir, "package-lock.json"), "utf8"),
  );
  let packageIdentity = {};
  try {
    packageIdentity = JSON.parse(
      readFileSync(
        path.join(
          betaDir,
          "build",
          "generated",
          "bootstrap",
          "provenance.json",
        ),
        "utf8",
      ),
    ).packageIdentity || {};
  } catch {
    // A missing generated identity is reported by the packaged bootstrap gate.
  }
  productName = String(
    packageIdentity.productName || packageMetadata.build.productName,
  ).trim();
  if (!productName || /[\\/]/.test(productName)) {
    fail("Packaged product name is missing or unsafe.");
  }
  options.applicationId = String(
    packageIdentity.appId || packageMetadata.build.appId,
  ).trim();
  if (!/^[A-Za-z0-9.-]+$/.test(options.applicationId)) {
    fail("Packaged application ID is missing or unsafe.");
  }
  const defaults = defaultGatePaths(options, packageMetadata.version);
  const artifactPath = path.resolve(options.artifact || defaults.artifact);
  const appDir = path.resolve(options.appDir || defaults.appDir);
  const scratchDir = path.resolve(options.scratchDir || defaults.scratchDir);
  const reportPath = path.resolve(options.report || defaults.report);
  options.brainstemPython = path.resolve(
    options.brainstemPython || defaultBrainstemPython(options.platform),
  );
  options.brainstemSource = path.resolve(
    options.brainstemSource || path.resolve(betaDir, "..", "rapp_brainstem"),
  );
  const expectedName = artifactName({
    ...options,
    version: packageMetadata.version,
  });

  requirement("artifact uses deterministic release name", path.basename(artifactPath) === expectedName, expectedName);
  requirement("release artifact exists", existsSync(artifactPath), artifactPath);
  if (!existsSync(artifactPath)) {
    requirement("artifact platform gate ran", false, "artifact missing");
  } else {
    rmSync(scratchDir, { recursive: true, force: true });
    mkdirSync(scratchDir, { recursive: true });
    try {
      if (options.platform === "macos") {
        await gateMac(options, artifactPath, appDir, scratchDir);
      } else {
        await gateWindows(options, artifactPath, appDir, scratchDir);
      }
      requirement("artifact platform gate ran", true, `${options.platform}/${options.arch}/${options.mode}`);
    } catch (error) {
      requirement("artifact platform gate ran", false, String(error.stack || error));
    } finally {
      rmSync(scratchDir, { recursive: true, force: true });
    }
  }

  const failures = results.filter((result) => !result.pass);
  mkdirSync(path.dirname(reportPath), { recursive: true });
  writeFileSync(
    reportPath,
    `${JSON.stringify(
      gateReport({
        options,
        artifactPath,
        packageMetadata,
        electronVersion: packageLock.packages["node_modules/electron"].version,
        nativeVersions: {
          ffmpeg_static:
            packageLock.packages["node_modules/ffmpeg-static"].version,
          ffprobe_installer:
            packageLock.packages["node_modules/@ffprobe-installer/ffprobe"].version,
          copilot_sdk:
            packageLock.packages["node_modules/@github/copilot-sdk"].version,
        },
        reportPath,
      }),
      null,
      2,
    )}\n`,
    "utf8",
  );
  process.stdout.write(`Gate report: ${reportPath}\n`);
  const publication = publicationEvidence(options);
  const summary = failures.length
    ? "PACKAGE NOT READY"
    : publication.status === "ready"
      ? "PACKAGE READY FOR PUBLICATION"
      : "PACKAGE VERIFIED, PUBLICATION BLOCKED";
  process.stdout.write(
    `\n${summary} — ${
      results.length - failures.length
    }/${results.length} pass\n`,
  );
  return failures.length ? 1 : 0;
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  runPackageGate()
    .then((exitCode) => process.exit(exitCode))
    .catch((error) => {
    process.stderr.write(`Package gate crashed: ${String(error.stack || error)}\n`);
    process.exit(2);
    });
}
