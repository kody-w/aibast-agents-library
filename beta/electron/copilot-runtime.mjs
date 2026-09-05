import { existsSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

import { CopilotClient, RuntimeConnection } from "@github/copilot-sdk";

const require = createRequire(import.meta.url);
const DEFAULT_START_TIMEOUT_MS = 30_000;
const RUNNING_FROM_ASAR = /[\\/]app\.asar[\\/]/.test(import.meta.url);

function asarUnpackedPath(filePath, resourcesPath = process.resourcesPath) {
  const value = String(filePath || "");
  const match = value.match(
    /^(.*?)([\\/])app\.asar[\\/](.+)$/,
  );
  if (!match) return value;
  const paths = match[2] === "\\" ? path.win32 : path.posix;
  if (resourcesPath) {
    return paths.join(resourcesPath, "app.asar.unpacked", match[3]);
  }
  return value.replace(
    /([\\/])app\.asar([\\/])/,
    "$1app.asar.unpacked$2",
  );
}

function executableCandidate(
  candidate,
  {
    fileExists = existsSync,
    resourcesPath = process.resourcesPath,
  } = {},
) {
  if (!candidate) return undefined;
  const unpacked = asarUnpackedPath(candidate, resourcesPath);
  if (unpacked !== candidate) {
    return fileExists(unpacked) ? unpacked : undefined;
  }
  return fileExists(candidate) ? candidate : undefined;
}

export function copilotPackageName(
  platform = process.platform,
  arch = process.arch,
) {
  const os = platform === "win32"
    ? "win32"
    : platform === "darwin"
      ? "darwin"
      : "linux";
  return `@github/copilot-${os}-${arch}`;
}

export function resolveCopilotCliPath(
  platform = process.platform,
  arch = process.arch,
  {
    fileExists = existsSync,
    requireResolve = require.resolve,
    resourcesPath = process.resourcesPath,
  } = {},
) {
  const packageName = copilotPackageName(platform, arch);
  try {
    const resolved = executableCandidate(requireResolve(packageName), {
      fileExists,
      resourcesPath,
    });
    if (resolved) return resolved;
  } catch {}

  try {
    const packageDir = path.dirname(
      requireResolve(`${packageName}/package.json`),
    );
    const binaryName = platform === "win32" ? "copilot.exe" : "copilot";
    const binaryPath = executableCandidate(
      path.join(packageDir, binaryName),
      { fileExists, resourcesPath },
    );
    if (binaryPath) return binaryPath;
  } catch {}

  return undefined;
}

export function readGitHubTokenFile(tokenFile) {
  if (!tokenFile || !existsSync(tokenFile)) return null;
  try {
    const value = JSON.parse(readFileSync(tokenFile, "utf8"));
    return typeof value?.access_token === "string" && value.access_token
      ? value.access_token
      : null;
  } catch {
    return null;
  }
}

export function withTimeout(
  promise,
  label,
  timeoutMs = DEFAULT_START_TIMEOUT_MS,
) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(
      () => reject(new Error(`${label} did not start within ${timeoutMs}ms`)),
      timeoutMs,
    );
    promise.then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      (error) => {
        clearTimeout(timer);
        reject(error);
      },
    );
  });
}

export class CopilotRuntime {
  constructor({
    timeoutMs = DEFAULT_START_TIMEOUT_MS,
    tokenFile = null,
    workingDirectory = process.cwd(),
  } = {}) {
    this.timeoutMs = timeoutMs;
    this.tokenFile = tokenFile;
    this.workingDirectory = workingDirectory;
    this.client = null;
    this.activeToken = null;
    this.startPromise = null;
  }

  async start() {
    if (this.startPromise) return this.startPromise;

    this.startPromise = (async () => {
      const cliPath = resolveCopilotCliPath();
      if (RUNNING_FROM_ASAR && !cliPath) {
        throw new Error(
          "The packaged GitHub Copilot CLI is missing from app.asar.unpacked. "
          + "Reinstall RAPP Brainstem Frontier from the published package.",
        );
      }
      const gitHubToken = readGitHubTokenFile(this.tokenFile);
      const options = cliPath
        ? {
          connection: RuntimeConnection.forStdio({ path: cliPath }),
          gitHubToken: gitHubToken || undefined,
          mode: "copilot-cli",
          workingDirectory: this.workingDirectory,
        }
        : {
            gitHubToken: gitHubToken || undefined,
            mode: "copilot-cli",
            workingDirectory: this.workingDirectory,
          };
      const client = new CopilotClient(options);

      try {
        await withTimeout(
          client.start(),
          "Bundled GitHub Copilot CLI",
          this.timeoutMs,
        );
        const auth = await client.getAuthStatus();
        this.client = client;
        this.activeToken = gitHubToken;
        return {
          available: true,
          authenticated: Boolean(auth?.isAuthenticated),
          login: auth?.login || null,
          cliPath: cliPath || null,
        };
      } catch (error) {
        await client.stop().catch(() => undefined);
        throw error;
      }
    })();

    try {
      return await this.startPromise;
    } catch (error) {
      this.startPromise = null;
      throw error;
    }
  }

  async stop() {
    const client = this.client;
    this.client = null;
    this.activeToken = null;
    this.startPromise = null;
    if (!client) return;
    try {
      await withTimeout(
        client.stop(),
        "Bundled GitHub Copilot CLI shutdown",
        5000,
      );
    } catch {
      await client.forceStop().catch(() => undefined);
    }
  }

  async createSession(config) {
    const currentToken = readGitHubTokenFile(this.tokenFile);
    if (
      this.client
      && currentToken !== this.activeToken
      && (currentToken || this.activeToken)
    ) {
      await this.stop();
    }
    await this.start();
    if (!this.client) throw new Error("Bundled GitHub Copilot CLI is unavailable.");
    return this.client.createSession(config);
  }
}

export const copilotRuntimeInternals = {
  asarUnpackedPath,
  executableCandidate,
};
