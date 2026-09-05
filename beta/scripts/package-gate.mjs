import {
  chmodSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

import { loadBootstrapBundle } from "../electron/brainstem-provisioner.mjs";

const betaDir = path.resolve(import.meta.dirname, "..");
const appDir = path.join(
  betaDir,
  "release",
  "mac-arm64",
  "RAPP Brainstem Frontier.app",
);
const executable = path.join(
  appDir,
  "Contents",
  "MacOS",
  "RAPP Brainstem Frontier",
);
const resources = path.join(appDir, "Contents", "Resources");
const unpackedModules = path.join(resources, "app.asar.unpacked", "node_modules");
const bootstrapDirectory = path.join(resources, "bootstrap");
const results = [];

function requirement(name, pass, detail = "") {
  results.push({ name, pass: Boolean(pass), detail });
  process.stdout.write(
    `${pass ? " PASS" : "*FAIL"}  ${name}${detail ? ` — ${detail}` : ""}\n`,
  );
}

function findNamed(root, name) {
  if (!existsSync(root)) return null;
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

function executableCheck(label, filePath) {
  requirement(`${label} exists in app.asar.unpacked`, Boolean(filePath), filePath || "");
  if (!filePath) return;
  const version = spawnSync(filePath, ["-version"], {
    encoding: "utf8",
    windowsHide: true,
  });
  requirement(`${label} executes`, version.status === 0, version.stderr.trim());
  if (process.platform === "darwin" && process.arch === "arm64") {
    const architecture = spawnSync("file", [filePath], { encoding: "utf8" });
    requirement(
      `${label} is native arm64 or universal`,
      architecture.status === 0 && /arm64|universal/i.test(architecture.stdout),
      architecture.stdout.trim(),
    );
  }
}

function main() {
  requirement("packaged macOS app exists", existsSync(executable), executable);
  const asarPath = path.join(resources, "app.asar");
  requirement("packaged app.asar exists", existsSync(asarPath), asarPath);
  if (existsSync(asarPath)) {
    requirement(
      "packaged app is newer than beta source",
      statSync(asarPath).mtimeMs >= newestSourceMtime(betaDir),
      new Date(statSync(asarPath).mtimeMs).toISOString(),
    );
  }
  executableCheck("ffmpeg", findNamed(unpackedModules, "ffmpeg"));
  executableCheck("ffprobe", findNamed(unpackedModules, "ffprobe"));
  for (const platform of ["darwin", "win32"]) {
    try {
      const bundle = loadBootstrapBundle({
        directory: bootstrapDirectory,
        platform,
      });
      requirement(
        `packaged ${bundle.installerName} matches immutable provenance`,
        true,
        bundle.provenance.commit,
      );
    } catch (error) {
      requirement(
        `packaged ${platform === "win32" ? "install.ps1" : "install.sh"} matches immutable provenance`,
        false,
        String(error.message || error),
      );
    }
  }

  if (existsSync(executable)) {
    const scratchRoot = path.join(betaDir, "release", ".package-gate");
    mkdirSync(scratchRoot, { recursive: true });
    const isolatedHome = mkdtempSync(
      path.join(scratchRoot, "rapp-beta-package-gate-"),
    );
    const brainstemHome = path.join(isolatedHome, ".brainstem");
    const runtime = path.join(brainstemHome, "src", "rapp_brainstem");
    const python = path.join(brainstemHome, "venv", "bin", "python");
    try {
      mkdirSync(path.join(runtime, "agents"), { recursive: true });
      mkdirSync(path.dirname(python), { recursive: true });
      writeFileSync(path.join(runtime, "brainstem.py"), "\n");
      writeFileSync(path.join(runtime, "requirements.txt"), "\n");
      writeFileSync(path.join(runtime, "VERSION"), "package-gate\n");
      writeFileSync(python, "#!/bin/sh\nexit 0\n");
      chmodSync(python, 0o700);
      const smoke = spawnSync(executable, [], {
        encoding: "utf8",
        env: {
          ...process.env,
          HOME: isolatedHome,
          BRAINSTEM_HOME: brainstemHome,
          BRAINSTEM_BETA_HEADLESS: "1",
          BRAINSTEM_BETA_HOME: path.join(brainstemHome, "beta-launcher"),
          BRAINSTEM_BETA_SMOKE_EXIT_MS: "3000",
        },
        timeout: 30000,
        windowsHide: true,
      });
      requirement(
        "packaged app passes isolated headless smoke",
        smoke.status === 0,
        String(smoke.stderr || smoke.stdout || "").trim(),
      );
      requirement(
        "already-ready packaged smoke skipped provisioning",
        !existsSync(
          path.join(brainstemHome, "logs", "frontier-provision.log"),
        ),
        brainstemHome,
      );
    } finally {
      rmSync(isolatedHome, { recursive: true, force: true });
      rmSync(scratchRoot, { recursive: true, force: true });
    }
  }

  const failures = results.filter((result) => !result.pass);
  process.stdout.write(
    `\n${failures.length ? "PACKAGE NOT READY" : "PACKAGE READY"} — ${
      results.length - failures.length
    }/${results.length} pass\n`,
  );
  process.exit(failures.length ? 1 : 0);
}

main();
