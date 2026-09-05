import { createHash } from "node:crypto";
import { execFile, spawn } from "node:child_process";
import {
  closeSync,
  existsSync,
  mkdirSync,
  openSync,
  readFileSync,
  rmSync,
  statSync,
  writeFileSync,
  writeSync,
} from "node:fs";
import path from "node:path";
import { promisify } from "node:util";

import {
  MINIMUM_BRAINSTEM_VERSION,
  versionAtLeast,
} from "./brainstem-process.mjs";

const execFileAsync = promisify(execFile);
const COMMIT_PATTERN = /^[0-9a-f]{40}$/i;
const SHA256_PATTERN = /^[0-9a-f]{64}$/i;
const SOURCE_REF_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._/-]*$/;
const PROVENANCE_SCHEMA = 1;
const PROVISION_LOCK = ".frontier-provision.lock";
const provisionByHome = new Map();

function message(error) {
  return String(error?.message || error);
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function validateSourceRef(value) {
  const ref = String(value || "").trim();
  if (
    !SOURCE_REF_PATTERN.test(ref)
    || ref.includes("..")
    || ref.includes("//")
    || ref.endsWith("/")
    || ref.endsWith(".")
    || ref.endsWith(".lock")
  ) {
    throw new Error(`sourceRef is invalid: ${ref || "(empty)"}`);
  }
  return ref;
}

export function normalizeGitHubRepositoryUrl(value) {
  const raw = String(value || "").trim();
  const ssh = raw.match(/^git@github\.com:([^/]+)\/([^/]+?)(?:\.git)?$/i);
  if (ssh) {
    return `https://github.com/${ssh[1]}/${ssh[2]}.git`;
  }

  let url;
  try {
    url = new URL(raw);
  } catch {
    throw new Error("repositoryUrl must be a GitHub HTTPS repository.");
  }
  const parts = url.pathname
    .replace(/^\/+|\/+$/g, "")
    .replace(/\.git$/i, "")
    .split("/");
  if (
    url.protocol !== "https:"
    || url.hostname.toLowerCase() !== "github.com"
    || url.username
    || url.password
    || url.search
    || url.hash
    || parts.length !== 2
    || parts.some((part) => !/^[A-Za-z0-9_.-]+$/.test(part))
  ) {
    throw new Error(
      "repositoryUrl must be a credential-free https://github.com/owner/repo URL.",
    );
  }
  return `https://github.com/${parts[0]}/${parts[1]}.git`;
}

export function validateBootstrapProvenance(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("bootstrap provenance must be a JSON object.");
  }
  if (value.schema !== PROVENANCE_SCHEMA) {
    throw new Error(`bootstrap provenance schema must be ${PROVENANCE_SCHEMA}.`);
  }
  if (value.product !== "rapp-brainstem-frontier") {
    throw new Error("bootstrap provenance has the wrong product.");
  }
  if (!COMMIT_PATTERN.test(value.commit || "")) {
    throw new Error("bootstrap provenance commit must be a full 40-character SHA.");
  }
  const repositoryUrl = normalizeGitHubRepositoryUrl(value.repositoryUrl);
  const sourceRef = validateSourceRef(value.sourceRef || "main");
  const installers = {};
  for (const filename of ["install.sh", "install.ps1"]) {
    const entry = value.installers?.[filename];
    if (
      !entry
      || typeof entry !== "object"
      || !SHA256_PATTERN.test(entry.sha256 || "")
    ) {
      throw new Error(
        `bootstrap provenance is missing the SHA-256 for ${filename}.`,
      );
    }
    installers[filename] = { sha256: entry.sha256.toLowerCase() };
  }
  return {
    schema: PROVENANCE_SCHEMA,
    product: "rapp-brainstem-frontier",
    commit: value.commit.toLowerCase(),
    repositoryUrl,
    sourceRef,
    installers,
  };
}

export function rawGitHubUrl(repositoryUrl, commit, filePath) {
  const normalized = normalizeGitHubRepositoryUrl(repositoryUrl);
  if (!COMMIT_PATTERN.test(commit || "")) {
    throw new Error("A full 40-character commit SHA is required.");
  }
  const repository = new URL(normalized);
  const encodedPath = String(filePath)
    .split("/")
    .map((part) => encodeURIComponent(part))
    .join("/");
  return `https://raw.githubusercontent.com${repository.pathname.replace(
    /\.git$/,
    "",
  )}/${commit.toLowerCase()}/${encodedPath}`;
}

function sha256File(filePath) {
  return createHash("sha256").update(readFileSync(filePath)).digest("hex");
}

export function loadBootstrapBundle({
  directory,
  platform = process.platform,
} = {}) {
  const provenancePath = path.join(directory || "", "provenance.json");
  let parsed;
  try {
    parsed = JSON.parse(readFileSync(provenancePath, "utf8"));
  } catch (error) {
    throw new Error(
      `immutable bootstrap provenance could not be read at ${provenancePath}: ${message(error)}`,
    );
  }
  const provenance = validateBootstrapProvenance(parsed);
  const installerName = platform === "win32" ? "install.ps1" : "install.sh";
  const installerPath = path.join(directory, installerName);
  if (!existsSync(installerPath)) {
    throw new Error(`the packaged ${installerName} is missing at ${installerPath}.`);
  }
  const actualHash = sha256File(installerPath);
  const expectedHash = provenance.installers[installerName].sha256;
  if (actualHash !== expectedHash) {
    throw new Error(
      `the packaged ${installerName} hash is ${actualHash}, expected ${expectedHash}.`,
    );
  }
  return {
    directory,
    installerName,
    installerPath,
    provenance,
    provenancePath,
  };
}

async function probePython(python, brainstemHome) {
  await execFileAsync(
    python,
    [
      "-B",
      "-c",
      "import flask, flask_cors, requests, dotenv",
    ],
    {
      encoding: "utf8",
      env: {
        ...process.env,
        BRAINSTEM_HOME: brainstemHome,
        PYTHONDONTWRITEBYTECODE: "1",
        PYTHONUTF8: "1",
      },
      maxBuffer: 64 * 1024,
      timeout: 15_000,
      windowsHide: true,
    },
  );
}

export async function inspectBrainstemRuntime(
  config,
  {
    fileExists = existsSync,
    minimumVersion = MINIMUM_BRAINSTEM_VERSION,
    readText = (filePath) => readFileSync(filePath, "utf8"),
    runPython = probePython,
  } = {},
) {
  const versionPath = path.join(config.brainstemDir, "VERSION");
  const required = [
    ["Brainstem server", path.join(config.brainstemDir, "brainstem.py")],
    ["Brainstem requirements", path.join(config.brainstemDir, "requirements.txt")],
    ["Brainstem version", versionPath],
    ["Brainstem Python environment", config.python],
  ];
  const issues = required
    .filter(([, filePath]) => !fileExists(filePath))
    .map(([label, filePath]) => `${label} is missing at ${filePath}.`);
  if (fileExists(versionPath)) {
    try {
      const version = readText(versionPath).trim();
      if (!versionAtLeast(version, minimumVersion)) {
        issues.push(
          `Brainstem version ${version || "missing"} is older than the `
          + `compatible minimum ${minimumVersion}.`,
        );
      }
    } catch (error) {
      issues.push(
        `Brainstem version could not be read at ${versionPath}: ${message(error)}.`,
      );
    }
  }
  if (issues.length === 0) {
    try {
      await runPython(config.python, config.brainstemHome);
    } catch {
      issues.push(
        `Brainstem Python dependencies are not usable from ${config.python}.`,
      );
    }
  }
  return { ready: issues.length === 0, issues };
}

export function buildInstallerInvocation({
  bundle,
  config,
  env = process.env,
  platform = process.platform,
} = {}) {
  const provenance = bundle.provenance;
  const installerEnv = {
    ...env,
    BRAINSTEM_HOME: config.brainstemHome,
    BRAINSTEM_REPO_REF: provenance.sourceRef,
    BRAINSTEM_REPO_URL: provenance.repositoryUrl,
    BRAINSTEM_VERSION_URL: rawGitHubUrl(
      provenance.repositoryUrl,
      provenance.commit,
      "rapp_brainstem/VERSION",
    ),
  };
  const installerArgs = [
    "--runtime-only",
    "--no-launch",
    "--version",
    provenance.commit,
  ];
  if (platform === "win32") {
    return {
      command: "powershell.exe",
      args: [
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        bundle.installerPath,
        ...installerArgs,
      ],
      env: installerEnv,
    };
  }
  return {
    command: "/bin/bash",
    args: [bundle.installerPath, ...installerArgs],
    env: installerEnv,
  };
}

function processExists(pid) {
  if (!Number.isInteger(pid) || pid < 1) return false;
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    return error?.code === "EPERM";
  }
}

function staleLock(lockPath, staleMs) {
  let age;
  try {
    age = Date.now() - statSync(lockPath).mtimeMs;
  } catch {
    return false;
  }
  if (age < staleMs) return false;
  try {
    const owner = JSON.parse(readFileSync(path.join(lockPath, "owner.json"), "utf8"));
    return !processExists(owner.pid);
  } catch {
    return true;
  }
}

export class BrainstemProvisioner {
  constructor({
    config,
    isPackaged = false,
    resourcesPath = "",
    packageDir = "",
    bootstrapDirectory = null,
    env = process.env,
    platform = process.platform,
    inspectRuntime = inspectBrainstemRuntime,
    loadBundle = loadBootstrapBundle,
    runInstaller = null,
    onState = () => {},
    lockTimeoutMs = 10 * 60_000,
    staleLockMs = 30 * 60_000,
    pollIntervalMs = 500,
    sleep = wait,
  } = {}) {
    this.config = config;
    this.isPackaged = isPackaged;
    this.resourcesPath = resourcesPath;
    this.packageDir = packageDir;
    this.bootstrapDirectory = bootstrapDirectory
      || (isPackaged ? path.join(resourcesPath, "bootstrap") : null);
    this.env = env;
    this.platform = platform;
    this.inspectRuntime = inspectRuntime;
    this.loadBundle = loadBundle;
    this.runInstallerOverride = runInstaller;
    this.onState = onState;
    this.lockTimeoutMs = lockTimeoutMs;
    this.staleLockMs = staleLockMs;
    this.pollIntervalMs = pollIntervalMs;
    this.sleep = sleep;
    this.child = null;
    this.stopped = false;
  }

  ensure() {
    const key = path.resolve(this.config.brainstemHome);
    const existing = provisionByHome.get(key);
    if (existing) {
      this.onState({
        phase: "waiting",
        message: "Another Frontier launch is preparing the shared Brainstem...",
      });
      return existing;
    }

    const pending = this.ensureOnce();
    const shared = pending.finally(() => {
      if (provisionByHome.get(key) === shared) provisionByHome.delete(key);
    });
    provisionByHome.set(key, shared);
    return shared;
  }

  assertRunning() {
    if (this.stopped) {
      throw new Error(
        "Brainstem provisioning was canceled because Frontier is closing. "
        + "Nothing was launched.",
      );
    }
  }

  async ensureOnce() {
    this.assertRunning();
    this.onState({
      phase: "checking",
      message: "Checking the shared Brainstem runtime...",
    });
    const initial = await this.inspectRuntime(this.config);
    this.assertRunning();
    if (initial.ready) {
      return { provisioned: false, reused: true };
    }

    if (!this.bootstrapDirectory) {
      const installer = path.join(this.packageDir || "beta", "install.sh");
      throw new Error(
        `The shared Brainstem runtime is not ready: ${initial.issues.join(" ")} `
        + `Nothing was launched. Run ${installer}, then reopen Frontier.`,
      );
    }

    let bundle;
    try {
      bundle = this.loadBundle({
        directory: this.bootstrapDirectory,
        platform: this.platform,
      });
    } catch (error) {
      throw new Error(
        `Packaged Brainstem provisioning is blocked: ${message(error)} `
        + "Nothing was installed. Download a complete published Frontier package "
        + "from https://microsoft.github.io/aibast-agents-library/beta/.",
      );
    }

    const logPath = path.join(
      this.config.brainstemHome,
      "logs",
      "frontier-provision.log",
    );
    const releaseLock = await this.acquireLock(logPath);
    try {
      const afterLock = await this.inspectRuntime(this.config);
      this.assertRunning();
      if (afterLock.ready) {
        return { provisioned: false, reused: true, waited: true };
      }

      this.onState({
        phase: "provisioning",
        message: "Installing the shared Brainstem runtime...",
        detail: `This can take several minutes. Progress log: ${logPath}`,
      });
      const invocation = buildInstallerInvocation({
        bundle,
        config: this.config,
        env: this.env,
        platform: this.platform,
      });
      this.assertRunning();
      const result = this.runInstallerOverride
        ? await this.runInstallerOverride({
            bundle,
            config: this.config,
            invocation,
            logPath,
          })
        : await this.runInstaller(invocation, bundle, logPath);
      if (result?.code !== 0) {
        const ending = result?.signal
          ? `was stopped by ${result.signal}`
          : `exited with code ${result?.code ?? "unknown"}`;
        throw new Error(
          `Brainstem provisioning failed: ${bundle.installerName} ${ending}. `
          + `Nothing was launched. Review ${logPath}, fix the prerequisite or `
          + "network error shown there, then reopen Frontier.",
        );
      }

      this.onState({
        phase: "verifying",
        message: "Verifying the installed Brainstem runtime...",
        detail: `Installer log: ${logPath}`,
      });
      const verified = await this.inspectRuntime(this.config);
      this.assertRunning();
      if (!verified.ready) {
        throw new Error(
          "Brainstem provisioning did not produce a usable runtime: "
          + `${verified.issues.join(" ")} Nothing was launched. Review ${logPath}, `
          + "then rerun the published Frontier installer or reopen this app.",
        );
      }
      return {
        commit: bundle.provenance.commit,
        logPath,
        provisioned: true,
        reused: false,
      };
    } finally {
      releaseLock();
    }
  }

  async acquireLock(logPath) {
    mkdirSync(this.config.brainstemHome, { recursive: true, mode: 0o700 });
    const lockPath = path.join(this.config.brainstemHome, PROVISION_LOCK);
    const deadline = Date.now() + this.lockTimeoutMs;
    while (Date.now() < deadline) {
      this.assertRunning();
      try {
        mkdirSync(lockPath, { mode: 0o700 });
        writeFileSync(
          path.join(lockPath, "owner.json"),
          `${JSON.stringify({
            pid: process.pid,
            startedAt: new Date().toISOString(),
          })}\n`,
          { mode: 0o600 },
        );
        return () => rmSync(lockPath, { recursive: true, force: true });
      } catch (error) {
        if (error?.code !== "EEXIST") throw error;
        if (staleLock(lockPath, this.staleLockMs)) {
          rmSync(lockPath, { recursive: true, force: true });
          continue;
        }
        this.onState({
          phase: "waiting",
          message: "Another Frontier process is preparing the shared Brainstem...",
          detail: `Waiting for its provisioning lock. Progress log: ${logPath}`,
        });
        await this.sleep(this.pollIntervalMs);
      }
    }
    throw new Error(
      "Another Frontier process still holds the Brainstem provisioning lock. "
      + `Nothing was launched. Close the other Frontier launch, check ${logPath}, `
      + "then reopen the app.",
    );
  }

  async runInstaller(invocation, bundle, logPath) {
    this.assertRunning();
    mkdirSync(path.dirname(logPath), { recursive: true, mode: 0o700 });
    const logFd = openSync(logPath, "a", 0o600);
    writeSync(
      logFd,
      `\n[${new Date().toISOString()}] Provisioning Brainstem from `
      + `${bundle.provenance.commit}\n`,
    );
    try {
      return await new Promise((resolve, reject) => {
        let settled = false;
        const finish = (callback, value) => {
          if (settled) return;
          settled = true;
          callback(value);
        };
        this.child = spawn(invocation.command, invocation.args, {
          env: invocation.env,
          shell: false,
          stdio: ["ignore", logFd, logFd],
          windowsHide: true,
        });
        this.child.once("error", (error) => finish(reject, error));
        this.child.once("exit", (code, signal) => {
          finish(resolve, { code, signal });
        });
      });
    } catch (error) {
      throw new Error(
        `Could not start ${bundle.installerName}: ${message(error)}. `
        + `Nothing was launched. Review ${logPath}, then reopen Frontier.`,
      );
    } finally {
      this.child = null;
      closeSync(logFd);
    }
  }

  async stop() {
    this.stopped = true;
    const child = this.child;
    if (!child || child.exitCode !== null) return;
    child.kill("SIGTERM");
    await Promise.race([
      new Promise((resolve) => child.once("exit", resolve)),
      this.sleep(5_000),
    ]);
    if (child.exitCode === null) child.kill("SIGKILL");
  }
}
