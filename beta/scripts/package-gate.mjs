import {
  chmodSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { createHash } from "node:crypto";
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

function executableCheck(label, filePath, args = ["-version"]) {
  requirement(`${label} exists in app.asar.unpacked`, Boolean(filePath), filePath || "");
  if (!filePath) return;
  const version = spawnSync(filePath, args, {
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

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
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
  executableCheck(
    "Copilot CLI",
    findNamed(unpackedModules, "copilot"),
    ["--version"],
  );
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
    const serviceMarker = path.join(isolatedHome, "service-ready");
    const provisionLog = path.join(
      isolatedHome,
      ".brainstem.frontier-provision.log",
    );
    const bootstrapFiles = ["install.sh", "install.ps1", "provenance.json"];
    const originalBootstrap = Object.fromEntries(
      bootstrapFiles.map((filename) => [
        filename,
        readFileSync(path.join(bootstrapDirectory, filename)),
      ]),
    );
    try {
      const fakeServerSource = `import { writeFileSync } from "node:fs";
import http from "node:http";
const health = ${JSON.stringify({
          status: "unauthenticated",
          version: "0.6.16",
          soul: "fixture-soul.md",
          agents: ["ContextMemory", "ManageMemory"],
          quarantined: [],
        })};
const server = http.createServer((request, response) => {
  if (request.url !== "/health") {
    response.writeHead(404).end();
    return;
  }
  response.writeHead(200, { "Content-Type": "application/json" });
  response.end(JSON.stringify(health));
});
server.listen(Number(process.env.PORT), "127.0.0.1", () => {
  writeFileSync(process.env.FAKE_BRAINSTEM_MARKER, JSON.stringify({
    HOME: process.env.HOME,
    USERPROFILE: process.env.USERPROFILE,
    BRAINSTEM_HOME: process.env.BRAINSTEM_HOME,
  }));
});
for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => server.close(() => process.exit(0)));
}
`;
      const fixtureInstaller = `#!/bin/bash
set -eu
runtime="$BRAINSTEM_HOME/src/rapp_brainstem"
agents="$runtime/agents"
python="$BRAINSTEM_HOME/venv/bin/python"
mkdir -p "$agents" "$(dirname "$python")"
printf '%s\\n' "print('fixture')" > "$runtime/brainstem.py"
printf '%s\\n' "flask" > "$runtime/requirements.txt"
printf '%s\\n' "0.6.16" > "$runtime/VERSION"
printf '%s\\n' "package gate soul" > "$runtime/soul.md"
printf '%s\\n' "class ContextMemoryAgent: pass" > "$agents/context_memory_agent.py"
printf '%s\\n' "class ManageMemoryAgent: pass" > "$agents/manage_memory_agent.py"
cat > "$runtime/package-gate-server.mjs" <<'SERVER'
${fakeServerSource}
SERVER
cat > "$python" <<'PYTHON'
#!/bin/sh
if [ "$1" = "-B" ]; then exit 0; fi
exec "$FAKE_NODE_PATH" "$BRAINSTEM_HOME/src/rapp_brainstem/package-gate-server.mjs"
PYTHON
chmod 700 "$python"
printf '%s\\n' 'GITHUB_TOKEN=ghp_PackageGateCanary123456' >&2
printf '%s\\n' 'https://fixture:PackageGatePassword@example.test/path' >&2
`;
      const fixturePowerShell = "throw 'macOS package-gate fixture only'\n";
      const fixtureManifest = {
        schema: 1,
        product: "rapp-brainstem-frontier",
        mode: "release",
        commit: "f".repeat(40),
        repositoryUrl:
          "https://github.com/microsoft/aibast-agents-library.git",
        sourceRef: "main",
        installers: {
          "install.sh": { sha256: sha256(fixtureInstaller) },
          "install.ps1": { sha256: sha256(fixturePowerShell) },
        },
      };
      writeFileSync(
        path.join(bootstrapDirectory, "install.sh"),
        fixtureInstaller,
      );
      writeFileSync(
        path.join(bootstrapDirectory, "install.ps1"),
        fixturePowerShell,
      );
      writeFileSync(
        path.join(bootstrapDirectory, "provenance.json"),
        `${JSON.stringify(fixtureManifest, null, 2)}\n`,
      );
      const smokeEnv = Object.fromEntries(
        Object.entries(process.env).filter(([key]) => (
          !key.startsWith("BRAINSTEM_")
          && ![
            "COPILOT_TOKEN",
            "GH_TOKEN",
            "GITHUB_TOKEN",
            "PORT",
          ].includes(key)
        )),
      );
      const packagedEnv = {
        ...smokeEnv,
        HOME: isolatedHome,
        USERPROFILE: isolatedHome,
        BRAINSTEM_HOME: brainstemHome,
        BRAINSTEM_BETA_HEADLESS: "1",
        BRAINSTEM_BETA_HOME: path.join(brainstemHome, "beta-launcher"),
        BRAINSTEM_BETA_SMOKE_EXIT_MS: "8000",
        BRAINSTEM_BETA_SMOKE_REQUIRE_READY: "1",
        FAKE_NODE_PATH: process.execPath,
        FAKE_BRAINSTEM_MARKER: serviceMarker,
      };
      const smoke = spawnSync(executable, [], {
        encoding: "utf8",
        env: packagedEnv,
        timeout: 30000,
        windowsHide: true,
      });
      const smokeOutput = String(smoke.stderr || smoke.stdout || "").trim();
      requirement(
        "packaged app provisions a missing runtime and reaches readiness",
        smoke.status === 0
          && !/Error occurred in handler|UnhandledPromiseRejection|TypeError:/.test(
            smokeOutput,
          ),
        smokeOutput,
      );
      requirement(
        "packaged smoke reached a compatible Brainstem service",
        existsSync(serviceMarker),
        serviceMarker,
      );
      const serviceEnvironment = existsSync(serviceMarker)
        ? JSON.parse(readFileSync(serviceMarker, "utf8"))
        : {};
      requirement(
        "packaged smoke kept HOME and BRAINSTEM_HOME isolated",
        serviceEnvironment.HOME === isolatedHome
          && serviceEnvironment.USERPROFILE === isolatedHome
          && serviceEnvironment.BRAINSTEM_HOME === brainstemHome,
        JSON.stringify(serviceEnvironment),
      );
      requirement(
        "missing-runtime bootstrap atomically activated the shared home",
        existsSync(path.join(runtime, "brainstem.py"))
          && existsSync(python),
        brainstemHome,
      );
      requirement(
        "missing-runtime bootstrap cleaned every staging home",
        readdirSync(isolatedHome).every(
          (name) => !name.includes("frontier-stage-"),
        ),
        isolatedHome,
      );
      const sanitizedLog = existsSync(provisionLog)
        ? readFileSync(provisionLog, "utf8")
        : "";
      requirement(
        "provisioning log scrubs credential canaries",
        sanitizedLog.includes("[REDACTED]")
          && !sanitizedLog.includes("ghp_PackageGateCanary123456")
          && !sanitizedLog.includes("PackageGatePassword"),
        provisionLog,
      );
      const firstLog = sanitizedLog;
      rmSync(serviceMarker, { force: true });
      const readySmoke = spawnSync(executable, [], {
        encoding: "utf8",
        env: {
          ...packagedEnv,
          BRAINSTEM_BETA_SMOKE_EXIT_MS: "5000",
        },
        timeout: 30000,
        windowsHide: true,
      });
      const readyOutput = String(
        readySmoke.stderr || readySmoke.stdout || "",
      ).trim();
      requirement(
        "already-ready packaged launch skips provisioning",
        readySmoke.status === 0
          && readFileSync(provisionLog, "utf8") === firstLog
          && !/Error occurred in handler|UnhandledPromiseRejection|TypeError:/.test(
            readyOutput,
          ),
        readyOutput,
      );
      writeFileSync(
        python,
        "#!/bin/sh\n"
        + 'if [ "$1" = "-B" ]; then exit 0; fi\n'
        + "exit 17\n",
      );
      chmodSync(python, 0o700);
      rmSync(serviceMarker, { force: true });
      const failingSmoke = spawnSync(executable, [], {
        encoding: "utf8",
        env: {
          ...packagedEnv,
          BRAINSTEM_BETA_SMOKE_EXIT_MS: "2000",
        },
        timeout: 30000,
        windowsHide: true,
      });
      requirement(
        "packaged smoke fails closed when its Brainstem service fails",
        failingSmoke.status !== 0,
        String(failingSmoke.stderr || failingSmoke.stdout || "").trim(),
      );
    } finally {
      for (const [filename, bytes] of Object.entries(originalBootstrap)) {
        writeFileSync(path.join(bootstrapDirectory, filename), bytes);
      }
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
