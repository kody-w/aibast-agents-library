import { createHash } from "node:crypto";
import { execFile, spawn } from "node:child_process";
import {
  closeSync,
  existsSync,
  lstatSync,
  mkdirSync,
  openSync,
  readFileSync,
  renameSync,
  rmSync,
  writeSync,
} from "node:fs";
import path from "node:path";
import { promisify } from "node:util";

import {
  MINIMUM_BRAINSTEM_VERSION,
  versionAtLeast,
} from "./brainstem-process.mjs";
import {
  acquireProvisioningLock,
  provisioningLockPath,
} from "./provision-lock.mjs";
import { attachScrubbedLog, scrubSecrets } from "./safe-log.mjs";

const execFileAsync = promisify(execFile);
const COMMIT_PATTERN = /^[0-9a-f]{40}$/i;
const SHA256_PATTERN = /^[0-9a-f]{64}$/i;
const SOURCE_REF_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._/-]*$/;
const PROVENANCE_SCHEMA = 1;
const CANONICAL_REPOSITORY =
  "https://github.com/microsoft/aibast-agents-library.git";
const provisionByHome = new Map();

export const PYTHON_READINESS_SCRIPT = [
  "import pathlib, sys",
  "required = (3, 11)",
  "if sys.version_info < required:",
  "    raise RuntimeError(",
  "        f'Python 3.11+ is required; found {sys.version_info.major}.{sys.version_info.minor}'",
  "    )",
  "source = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')",
  "compile(source, sys.argv[1], 'exec')",
  "import flask, flask_cors, requests, dotenv",
].join("\n");

function message(error) {
  return scrubSecrets(error?.stderr || error?.message || error);
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function pathEntryExists(filePath) {
  try {
    lstatSync(filePath);
    return true;
  } catch (error) {
    if (error?.code === "ENOENT") return false;
    throw error;
  }
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
  const mode = value.mode;
  if (!["development", "release"].includes(mode)) {
    throw new Error("bootstrap provenance mode must be release or development.");
  }
  const expectedProduct = mode === "release"
    ? "rapp-brainstem-frontier"
    : "rapp-brainstem-frontier-development";
  if (value.product !== expectedProduct) {
    throw new Error(`bootstrap provenance product must be ${expectedProduct}.`);
  }
  if (!COMMIT_PATTERN.test(value.commit || "")) {
    throw new Error("bootstrap provenance commit must be a full 40-character SHA.");
  }
  const repositoryUrl = normalizeGitHubRepositoryUrl(value.repositoryUrl);
  if (mode === "release" && repositoryUrl !== CANONICAL_REPOSITORY) {
    throw new Error(
      `release provenance must use ${CANONICAL_REPOSITORY}; `
      + "use explicit development mode for a fork.",
    );
  }
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
    product: expectedProduct,
    mode,
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

async function probePython(python, brainstemHome, brainstemFile) {
  await execFileAsync(
    python,
    ["-B", "-c", PYTHON_READINESS_SCRIPT, brainstemFile],
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
  const brainstemFile = path.join(config.brainstemDir, "brainstem.py");
  const versionPath = path.join(config.brainstemDir, "VERSION");
  const required = [
    ["Brainstem server", brainstemFile],
    ["Brainstem requirements", path.join(config.brainstemDir, "requirements.txt")],
    ["Brainstem version", versionPath],
    ["Brainstem soul", path.join(config.brainstemDir, "soul.md")],
    [
      "ContextMemory agent",
      path.join(config.brainstemDir, "agents", "context_memory_agent.py"),
    ],
    [
      "ManageMemory agent",
      path.join(config.brainstemDir, "agents", "manage_memory_agent.py"),
    ],
    ["Brainstem Python environment", config.python],
  ];
  const present = new Map(required.map(([, filePath]) => (
    [filePath, fileExists(filePath)]
  )));
  const issues = required
    .filter(([, filePath]) => !present.get(filePath))
    .map(([label, filePath]) => `${label} is missing at ${filePath}.`);
  if (present.get(versionPath)) {
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
      await runPython(config.python, config.brainstemHome, brainstemFile);
    } catch (error) {
      issues.push(
        `Brainstem Python or source validation failed at ${config.python}: `
        + `${message(error)}.`,
      );
    }
  }
  return { ready: issues.length === 0, issues };
}

function platformPaths(platform) {
  return platform === "win32" ? path.win32 : path.posix;
}

export function configForBrainstemHome(config, brainstemHome, platform) {
  const paths = platformPaths(platform);
  return {
    ...config,
    brainstemHome,
    brainstemDir: paths.join(brainstemHome, "src", "rapp_brainstem"),
    python: platform === "win32"
      ? paths.join(brainstemHome, "venv", "Scripts", "python.exe")
      : paths.join(brainstemHome, "venv", "bin", "python"),
  };
}

export function buildInstallerInvocation({
  bundle,
  config,
  env = process.env,
  platform = process.platform,
} = {}) {
  const paths = platformPaths(platform);
  const provenance = bundle.provenance;
  const temporaryDirectory = paths.join(config.brainstemHome, "tmp");
  const installerEnv = {
    ...env,
    BRAINSTEM_HOME: config.brainstemHome,
    BRAINSTEM_BIN: paths.join(config.brainstemHome, "bin"),
    BRAINSTEM_REPO_REF: provenance.sourceRef,
    BRAINSTEM_REPO_URL: provenance.repositoryUrl,
    BRAINSTEM_VERSION_URL: rawGitHubUrl(
      provenance.repositoryUrl,
      provenance.commit,
      "rapp_brainstem/VERSION",
    ),
    TMP: temporaryDirectory,
    TEMP: temporaryDirectory,
    TMPDIR: temporaryDirectory,
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

function siblingArtifact(brainstemHome, suffix) {
  const resolved = path.resolve(brainstemHome);
  return path.join(
    path.dirname(resolved),
    `${path.basename(resolved)}.${suffix}`,
  );
}

export function provisioningLogPath(brainstemHome) {
  return siblingArtifact(brainstemHome, "frontier-provision.log");
}

function stagingHome(brainstemHome, bundle, token) {
  return siblingArtifact(
    brainstemHome,
    `frontier-stage-${bundle.provenance.commit.slice(0, 12)}-${token.slice(0, 16)}`,
  );
}

function manualRepairError(config, inspection) {
  return new Error(
    `Existing BRAINSTEM_HOME is present but not compatible: ${
      inspection.issues.join(" ")
    } Automatic repair was not attempted and no existing files were changed. `
    + `Back up ${config.brainstemHome}, then run the published source installer `
    + "manually to repair it, or choose a new empty BRAINSTEM_HOME.",
  );
}

async function terminateWindowsTree(pid) {
  try {
    await execFileAsync(
      "taskkill.exe",
      ["/pid", String(pid), "/t", "/f"],
      { windowsHide: true },
    );
  } catch {}
}

function signalUnixTree(pid, signal) {
  try {
    process.kill(-pid, signal);
  } catch (error) {
    if (error?.code !== "ESRCH") throw error;
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
    acquireLock = acquireProvisioningLock,
    lockTimeoutMs = 10 * 60_000,
    invalidOwnerGraceMs = 2_000,
    pollIntervalMs = 100,
    sleep = wait,
    pathExists = pathEntryExists,
    makeDirectory = mkdirSync,
    move = renameSync,
    remove = rmSync,
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
    this.acquireLock = acquireLock;
    this.lockTimeoutMs = lockTimeoutMs;
    this.invalidOwnerGraceMs = invalidOwnerGraceMs;
    this.pollIntervalMs = pollIntervalMs;
    this.sleep = sleep;
    this.pathExists = pathExists;
    this.makeDirectory = makeDirectory;
    this.move = move;
    this.remove = remove;
    this.child = null;
    this.ensurePromise = null;
    this.lockLease = null;
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
      if (this.ensurePromise === shared) this.ensurePromise = null;
    });
    provisionByHome.set(key, shared);
    this.ensurePromise = shared;
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
    if (this.pathExists(this.config.brainstemHome)) {
      throw manualRepairError(this.config, initial);
    }
    if (!this.bootstrapDirectory) {
      const installer = path.join(this.packageDir || "beta", "install.sh");
      throw new Error(
        `The shared Brainstem runtime is absent. Nothing was launched. Run `
        + `${installer}, then reopen Frontier.`,
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

    const logPath = provisioningLogPath(this.config.brainstemHome);
    const lease = await this.acquireLock({
      brainstemHome: this.config.brainstemHome,
      invalidOwnerGraceMs: this.invalidOwnerGraceMs,
      lockPath: provisioningLockPath(this.config.brainstemHome),
      onWait: () => {
        this.onState({
          phase: "waiting",
          message: "Another Frontier process is preparing the shared Brainstem...",
          detail: `Waiting for its provisioning lock. Progress log: ${logPath}`,
        });
      },
      pollIntervalMs: this.pollIntervalMs,
      sleep: this.sleep,
      timeoutMs: this.lockTimeoutMs,
    });
    this.lockLease = lease;
    let stageHome = null;
    try {
      const afterLock = await this.inspectRuntime(this.config);
      this.assertRunning();
      if (afterLock.ready) {
        return { provisioned: false, reused: true, waited: true };
      }
      if (this.pathExists(this.config.brainstemHome)) {
        throw manualRepairError(this.config, afterLock);
      }

      stageHome = stagingHome(
        this.config.brainstemHome,
        bundle,
        lease.token,
      );
      if (this.pathExists(stageHome)) {
        throw new Error(
          `Private Brainstem staging path already exists: ${stageHome}. `
          + "Nothing was installed; remove that abandoned stage and reopen Frontier.",
        );
      }
      this.makeDirectory(stageHome, { mode: 0o700 });
      this.makeDirectory(path.join(stageHome, "tmp"), {
        recursive: true,
        mode: 0o700,
      });
      const stageConfig = configForBrainstemHome(
        this.config,
        stageHome,
        this.platform,
      );
      this.onState({
        phase: "provisioning",
        message: "Installing a staged shared Brainstem runtime...",
        detail: `The existing target remains untouched. Sanitized log: ${logPath}`,
      });
      const invocation = buildInstallerInvocation({
        bundle,
        config: stageConfig,
        env: this.env,
        platform: this.platform,
      });
      this.assertRunning();
      const result = this.runInstallerOverride
        ? await this.runInstallerOverride({
            bundle,
            config: stageConfig,
            invocation,
            logPath,
            stageHome,
          })
        : await this.runInstaller(invocation, bundle, logPath);
      if (result?.code !== 0) {
        const ending = result?.signal
          ? `was stopped by ${result.signal}`
          : `exited with code ${result?.code ?? "unknown"}`;
        throw new Error(
          `Brainstem staging failed: ${bundle.installerName} ${ending}. `
          + `No runtime was activated. Review the sanitized log at ${logPath}, `
          + "fix the prerequisite or network error, then reopen Frontier.",
        );
      }

      this.onState({
        phase: "verifying",
        message: "Verifying the staged Brainstem runtime...",
        detail: `Sanitized installer log: ${logPath}`,
      });
      const staged = await this.inspectRuntime(stageConfig);
      this.assertRunning();
      if (!staged.ready) {
        throw new Error(
          "Staged Brainstem verification failed: "
          + `${staged.issues.join(" ")} No runtime was activated. Review the `
          + `sanitized log at ${logPath}, then reopen Frontier.`,
        );
      }
      if (this.pathExists(this.config.brainstemHome)) {
        throw new Error(
          `BRAINSTEM_HOME appeared while staging was in progress: ${
            this.config.brainstemHome
          }. The staged runtime was discarded and the existing target was preserved.`,
        );
      }

      this.move(stageHome, this.config.brainstemHome);
      const activatedStage = stageHome;
      stageHome = null;
      const activated = await this.inspectRuntime(this.config);
      this.assertRunning();
      if (!activated.ready) {
        const rollback = `${activatedStage}.rollback`;
        this.move(this.config.brainstemHome, rollback);
        this.remove(rollback, { recursive: true, force: true });
        throw new Error(
          "Activated Brainstem failed its final readiness check and was rolled "
          + `back to an absent target: ${activated.issues.join(" ")} Reopen `
          + "Frontier to retry.",
        );
      }
      return {
        commit: bundle.provenance.commit,
        logPath,
        provisioned: true,
        reused: false,
      };
    } finally {
      if (stageHome && this.pathExists(stageHome)) {
        this.remove(stageHome, { recursive: true, force: true });
      }
      lease.release();
      if (this.lockLease === lease) this.lockLease = null;
    }
  }

  async runInstaller(invocation, bundle, logPath) {
    this.assertRunning();
    this.makeDirectory(path.dirname(logPath), {
      recursive: true,
      mode: 0o700,
    });
    const logFd = openSync(logPath, "a", 0o600);
    writeSync(
      logFd,
      scrubSecrets(
        `\n[${new Date().toISOString()}] Staging Brainstem from `
        + `${bundle.provenance.commit}\n`,
      ),
    );
    const cleanups = [];
    try {
      return await new Promise((resolve, reject) => {
        let settled = false;
        const finish = (callback, value) => {
          if (settled) return;
          settled = true;
          callback(value);
        };
        this.child = spawn(invocation.command, invocation.args, {
          detached: this.platform !== "win32",
          env: invocation.env,
          shell: false,
          stdio: ["ignore", "pipe", "pipe"],
          windowsHide: true,
        });
        cleanups.push(
          attachScrubbedLog(this.child.stdout, logFd),
          attachScrubbedLog(this.child.stderr, logFd),
        );
        this.child.once("error", (error) => finish(reject, error));
        this.child.once("close", (code, signal) => {
          finish(resolve, { code, signal });
        });
      });
    } catch (error) {
      throw new Error(
        `Could not start ${bundle.installerName}: ${message(error)}. `
        + `No runtime was activated. Review the sanitized log at ${logPath}.`,
      );
    } finally {
      for (const cleanup of cleanups) cleanup();
      this.child = null;
      closeSync(logFd);
    }
  }

  async stop() {
    this.stopped = true;
    const child = this.child;
    if (!child?.pid) return;
    const closed = new Promise((resolve) => child.once("close", resolve));
    if (this.platform === "win32") {
      await terminateWindowsTree(child.pid);
    } else {
      signalUnixTree(child.pid, "SIGTERM");
    }
    let timeout;
    await Promise.race([
      closed,
      new Promise((resolve) => {
        timeout = setTimeout(resolve, 5_000);
      }),
    ]);
    clearTimeout(timeout);
    if (this.platform !== "win32" && this.child) {
      signalUnixTree(child.pid, "SIGKILL");
    }
    if (this.lockLease && this.ensurePromise) {
      let releaseTimeout;
      await Promise.race([
        this.ensurePromise.catch(() => undefined),
        new Promise((resolve) => {
          releaseTimeout = setTimeout(resolve, 5_000);
        }),
      ]);
      clearTimeout(releaseTimeout);
    }
  }
}
