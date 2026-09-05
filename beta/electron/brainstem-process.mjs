import {
  closeSync,
  existsSync,
  mkdirSync,
  openSync,
} from "node:fs";
import { homedir } from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";

const DEFAULT_PORT = 7071;
const START_TIMEOUT_MS = 90_000;
export const MINIMUM_BRAINSTEM_VERSION = "0.6.16";

export function resolveBrainstemConfig({
  env = process.env,
  platform = process.platform,
  home = homedir(),
} = {}) {
  const paths = platform === "win32" ? path.win32 : path.posix;
  const brainstemHome = paths.resolve(
    env.BRAINSTEM_HOME || paths.join(home, ".brainstem"),
  );
  const brainstemDir = env.BRAINSTEM_BETA_SOURCE_DIR
    ? paths.resolve(env.BRAINSTEM_BETA_SOURCE_DIR)
    : paths.join(brainstemHome, "src", "rapp_brainstem");
  const python = env.BRAINSTEM_BETA_PYTHON
    ? paths.resolve(env.BRAINSTEM_BETA_PYTHON)
    : (platform === "win32"
      ? paths.join(brainstemHome, "venv", "Scripts", "python.exe")
      : paths.join(brainstemHome, "venv", "bin", "python"));
  const port = Number.parseInt(
    env.BRAINSTEM_BETA_PORT || env.PORT || String(DEFAULT_PORT),
    10,
  );

  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error(`Invalid Brainstem port: ${port}`);
  }

  return {
    brainstemHome,
    brainstemDir,
    python,
    port,
    url: `http://127.0.0.1:${port}`,
    logFile: paths.join(brainstemHome, "logs", "beta-brainstem.log"),
  };
}

function parseVersion(value) {
  const match = String(value || "").trim().match(
    /^v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$/,
  );
  return match ? match.slice(1).map(Number) : null;
}

export function versionAtLeast(value, minimum) {
  const actual = parseVersion(value);
  const required = parseVersion(minimum);
  if (!actual || !required) return false;
  for (let index = 0; index < required.length; index += 1) {
    if (actual[index] > required[index]) return true;
    if (actual[index] < required[index]) return false;
  }
  return true;
}

export function assessBrainstemHealth(
  value,
  {
    expectedAgents = [],
    minimumAgentCount = 1,
    minimumVersion = MINIMUM_BRAINSTEM_VERSION,
    rejectQuarantined = true,
  } = {},
) {
  const issues = [];
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return { ok: false, issues: ["Health response is not a JSON object."] };
  }
  if (!["ok", "unauthenticated"].includes(value.status)) {
    issues.push(`Health status is ${String(value.status || "missing")}.`);
  }
  if (!versionAtLeast(value.version, minimumVersion)) {
    issues.push(
      `Brainstem version ${String(value.version || "missing")} is older than `
      + `the compatible minimum ${minimumVersion}.`,
    );
  }
  if (typeof value.soul !== "string" || value.soul === "missing") {
    issues.push("Brainstem soul is missing.");
  }
  if (!Array.isArray(value.agents)) {
    issues.push("Health response does not include loaded-agent evidence.");
  } else {
    if (value.agents.length < minimumAgentCount) {
      issues.push(
        `Health response loaded ${value.agents.length} agents; at least `
        + `${minimumAgentCount} are required.`,
      );
    }
    const missing = expectedAgents.filter(
      (agent) => !value.agents.includes(agent),
    );
    if (missing.length) {
      issues.push(`Expected agents did not load: ${missing.join(", ")}.`);
    }
  }
  if (!Array.isArray(value.quarantined)) {
    issues.push("Health response does not include agent load-error evidence.");
  } else if (rejectQuarantined && value.quarantined.length) {
    const failed = value.quarantined.map((entry) => (
      entry?.file
        ? `${entry.file}${entry.reason ? ` (${entry.reason})` : ""}`
        : "unknown agent"
    ));
    issues.push(`Agents were quarantined during load: ${failed.join(", ")}.`);
  }
  return { ok: issues.length === 0, issues };
}

export function isBrainstemHealth(value, requirements) {
  return assessBrainstemHealth(value, requirements).ok;
}

export async function probeHealthEvidence(
  url,
  timeoutMs = 1_500,
  requirements = {},
) {
  let response;
  try {
    response = await fetch(`${url}/health`, {
      signal: AbortSignal.timeout(timeoutMs),
      headers: { Accept: "application/json" },
    });
  } catch (error) {
    return {
      health: null,
      issues: [String(error?.message || error)],
      reachable: false,
    };
  }
  if (!response.ok) {
    return {
      health: null,
      issues: [`Health endpoint returned HTTP ${response.status}.`],
      reachable: true,
    };
  }
  try {
    const body = await response.json();
    const assessment = assessBrainstemHealth(body, requirements);
    return {
      health: assessment.ok ? body : null,
      issues: assessment.issues,
      reachable: true,
    };
  } catch (error) {
    return {
      health: null,
      issues: [`Health endpoint returned invalid JSON: ${String(error?.message || error)}`],
      reachable: true,
    };
  }
}

export async function probeHealth(url, timeoutMs = 1_500, requirements = {}) {
  return (await probeHealthEvidence(url, timeoutMs, requirements)).health;
}

export async function waitForHealth(
  url,
  {
    timeoutMs = START_TIMEOUT_MS,
    intervalMs = 500,
    probe = probeHealth,
    exited = () => false,
  } = {},
) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const health = await probe(url);
    if (health) return health;
    if (exited()) return null;
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  return null;
}

export function buildBrainstemEnvironment(
  config,
  inherited = process.env,
) {
  return {
    ...inherited,
    ...(config.env || {}),
    BRAINSTEM_HOME: config.brainstemHome,
    PORT: String(config.port),
    BRAINSTEM_BETA_LAUNCHER: "1",
    PYTHONUTF8: "1",
  };
}

export class BrainstemProcess {
  constructor(config = resolveBrainstemConfig()) {
    this.config = config;
    this.child = null;
    this.logFd = null;
    this.owned = false;
  }

  async start() {
    const requirements = this.config.healthRequirements || {};
    const existing = await probeHealthEvidence(
      this.config.url,
      1_500,
      requirements,
    );
    if (existing.health) {
      this.owned = false;
      return { reused: true, health: existing.health, ...this.config };
    }
    if (existing.reachable) {
      throw new Error(
        `An incompatible service is already running at ${this.config.url}: `
        + `${existing.issues.join(" ")} Stop it, then reopen Frontier.`,
      );
    }

    const serverFile = path.join(this.config.brainstemDir, "brainstem.py");
    if (!existsSync(serverFile)) {
      throw new Error(
        `Brainstem source is missing at ${this.config.brainstemDir}. Re-run the Frontier installer.`,
      );
    }
    if (!existsSync(this.config.python)) {
      throw new Error(
        `Brainstem Python environment is missing at ${this.config.python}. Re-run the Frontier installer.`,
      );
    }

    mkdirSync(path.dirname(this.config.logFile), { recursive: true });
    this.logFd = openSync(this.config.logFile, "a");
    this.child = spawn(this.config.python, ["brainstem.py"], {
      cwd: this.config.brainstemDir,
      env: buildBrainstemEnvironment(this.config),
      windowsHide: true,
      shell: false,
      stdio: ["ignore", this.logFd, this.logFd],
    });
    this.owned = true;

    let incompatible = null;
    const health = await waitForHealth(this.config.url, {
      probe: async (url) => {
        const evidence = await probeHealthEvidence(
          url,
          1_500,
          requirements,
        );
        if (evidence.reachable && !evidence.health) incompatible = evidence;
        return evidence.health;
      },
      exited: () => (
        this.child?.exitCode !== null
        || Boolean(incompatible)
      ),
    });
    if (!health) {
      const exitCode = this.child?.exitCode;
      await this.stop();
      throw new Error(
        incompatible
          ? `Brainstem started but failed the compatibility gate: ${
              incompatible.issues.join(" ")
            } Nothing was opened. See ${this.config.logFile}.`
          : `Brainstem did not become healthy${
              exitCode === null ? "" : ` (exit ${exitCode})`
            }. See ${this.config.logFile}.`,
      );
    }

    return { reused: false, health, ...this.config };
  }

  async stop() {
    const child = this.child;
    this.child = null;
    this.owned = false;

    if (child && child.exitCode === null) {
      child.kill("SIGTERM");
      await Promise.race([
        new Promise((resolve) => child.once("exit", resolve)),
        new Promise((resolve) => setTimeout(resolve, 5_000)),
      ]);
      if (child.exitCode === null) child.kill("SIGKILL");
    }

    if (this.logFd !== null) {
      closeSync(this.logFd);
      this.logFd = null;
    }
  }
}
