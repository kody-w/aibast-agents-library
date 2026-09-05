import {
  chmodSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  realpathSync,
  readdirSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { createHash } from "node:crypto";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";

import { loadBootstrapBundle } from "../electron/brainstem-provisioner.mjs";

const betaDir = path.resolve(import.meta.dirname, "..");
const targetArch = String(
  process.env.FRONTIER_FIRST_RUN_ARCH || process.arch,
).trim();
const productName = String(
  process.env.FRONTIER_FIRST_RUN_PRODUCT_NAME || "RAPP Brainstem Frontier",
).trim();
if (!productName || /[\\/]/.test(productName)) {
  throw new Error("FRONTIER_FIRST_RUN_PRODUCT_NAME is missing or unsafe.");
}
const appDir = process.env.FRONTIER_FIRST_RUN_APP_DIR
  ? path.resolve(process.env.FRONTIER_FIRST_RUN_APP_DIR)
  : path.join(
      betaDir,
      "release",
      targetArch === "arm64" ? "mac-arm64" : "mac",
      `${productName}.app`,
    );
const executable = path.join(
  appDir,
  "Contents",
  "MacOS",
  productName,
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
  if (process.platform === "darwin") {
    const architecture = spawnSync("file", [filePath], { encoding: "utf8" });
    requirement(
      `${label} contains the required ${targetArch} slice`,
      architecture.status === 0
        && new RegExp(
          targetArch === "arm64" ? "arm64|universal" : "x86_64|universal",
          "i",
        ).test(architecture.stdout),
      architecture.stdout.trim(),
    );
  }
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function safeRead(filePath) {
  try {
    return { ok: true, value: readFileSync(filePath, "utf8") };
  } catch (error) {
    return {
      ok: false,
      detail: `${filePath}: ${String(error?.message || error)}`,
      value: "",
    };
  }
}

function safeRealpath(filePath) {
  try {
    return { ok: true, value: realpathSync(filePath) };
  } catch (error) {
    return {
      ok: false,
      detail: `${filePath}: ${String(error?.message || error)}`,
      value: null,
    };
  }
}

function runPackaged(executablePath, env, timeoutMs = 30_000) {
  return new Promise((resolve) => {
    const child = spawn(executablePath, [], {
      env,
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    });
    let output = "";
    let settled = false;
    const finish = (result) => {
      if (settled) return;
      settled = true;
      resolve(result);
    };
    child.stdout.on("data", (chunk) => { output += chunk; });
    child.stderr.on("data", (chunk) => { output += chunk; });
    const timeout = setTimeout(() => {
      child.kill("SIGKILL");
    }, timeoutMs);
    child.once("error", (error) => {
      clearTimeout(timeout);
      finish({ status: null, output: String(error?.message || error) });
    });
    child.once("close", (code, signal) => {
      clearTimeout(timeout);
      finish({
        status: code,
        output: `${output}${signal ? `\nSignal: ${signal}` : ""}`.trim(),
      });
    });
  });
}

async function main() {
  requirement(
    `packaged macOS ${targetArch} app exists`,
    existsSync(executable),
    executable,
  );
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
    REQUESTED_USER_DATA_DIR: process.env.BRAINSTEM_BETA_USER_DATA_DIR,
    ACTUAL_USER_DATA_DIR: process.env.BRAINSTEM_BETA_ACTUAL_USER_DATA_DIR,
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
        product: "rapp-brainstem-frontier-development",
        mode: "development",
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
      const packagedEnvironment = (
        home,
        label,
        marker,
        overrides = {},
      ) => {
        const target = path.join(home, ".brainstem");
        return {
          ...smokeEnv,
          HOME: home,
          USERPROFILE: home,
          BRAINSTEM_HOME: target,
          BRAINSTEM_BETA_HEADLESS: "1",
          BRAINSTEM_BETA_HOME: path.join(target, "beta-launcher"),
          BRAINSTEM_BETA_SMOKE_EXIT_MS: "8000",
          BRAINSTEM_BETA_SMOKE_REQUIRE_READY: "1",
          BRAINSTEM_BETA_CAPTURE_USER_DATA_PATH: "1",
          BRAINSTEM_BETA_USER_DATA_DIR: path.join(
            home,
            "electron-user-data",
            label,
          ),
          FAKE_NODE_PATH: process.execPath,
          FAKE_BRAINSTEM_MARKER: marker,
          ...overrides,
        };
      };
      const packagedEnv = packagedEnvironment(
        isolatedHome,
        "provision",
        serviceMarker,
      );
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
      const markerRead = safeRead(serviceMarker);
      let serviceEnvironment = {};
      let markerDetail = markerRead.detail || serviceMarker;
      if (markerRead.ok) {
        try {
          serviceEnvironment = JSON.parse(markerRead.value);
        } catch (error) {
          markerDetail = `${serviceMarker}: ${String(error?.message || error)}`;
        }
      }
      requirement(
        "packaged smoke kept HOME and BRAINSTEM_HOME isolated",
        serviceEnvironment.HOME === isolatedHome
          && serviceEnvironment.USERPROFILE === isolatedHome
          && serviceEnvironment.BRAINSTEM_HOME === brainstemHome
          && serviceEnvironment.REQUESTED_USER_DATA_DIR
            === packagedEnv.BRAINSTEM_BETA_USER_DATA_DIR
          && serviceEnvironment.ACTUAL_USER_DATA_DIR
            === packagedEnv.BRAINSTEM_BETA_USER_DATA_DIR,
        Object.keys(serviceEnvironment).length
          ? JSON.stringify(serviceEnvironment)
          : markerDetail,
      );
      requirement(
        "missing-runtime bootstrap atomically activated the shared home",
        existsSync(path.join(runtime, "brainstem.py"))
          && existsSync(python),
        brainstemHome,
      );
      const stagedHomes = readdirSync(isolatedHome)
        .filter((name) => name.includes("frontier-stage-"));
      const targetPath = safeRealpath(brainstemHome);
      const stagedPaths = stagedHomes.map((name) => (
        safeRealpath(path.join(isolatedHome, name))
      ));
      requirement(
        "missing-runtime bootstrap left no abandoned staging home",
        targetPath.ok
          && stagedPaths.length === 1
          && stagedPaths[0].ok
          && stagedPaths[0].value === targetPath.value,
        targetPath.ok
          ? targetPath.value
          : targetPath.detail,
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
        env: packagedEnvironment(
          isolatedHome,
          "ready",
          serviceMarker,
          { BRAINSTEM_BETA_SMOKE_EXIT_MS: "5000" },
        ),
        timeout: 30000,
        windowsHide: true,
      });
      const readyOutput = String(
        readySmoke.stderr || readySmoke.stdout || "",
      ).trim();
      const readyLog = safeRead(provisionLog);
      requirement(
        "already-ready packaged launch skips provisioning",
        readySmoke.status === 0
          && readyLog.ok
          && readyLog.value === firstLog
          && !/Error occurred in handler|UnhandledPromiseRejection|TypeError:/.test(
            readyOutput,
          ),
        readyLog.ok ? readyOutput : readyLog.detail,
      );
      const concurrentHome = mkdtempSync(
        path.join(scratchRoot, "concurrent-shared-home-"),
      );
      const concurrentTargets = [
        path.join(concurrentHome, "brainstem-a"),
        path.join(concurrentHome, "brainstem-b"),
      ];
      const concurrentMarkers = concurrentTargets.map(
        (_target, index) => path.join(
          concurrentHome,
          `service-ready-${index + 1}`,
        ),
      );
      const concurrentEnvironments = concurrentTargets.map((target, index) => (
        packagedEnvironment(
          concurrentHome,
          `concurrent-${index + 1}`,
          concurrentMarkers[index],
          {
            BRAINSTEM_HOME: target,
            BRAINSTEM_BETA_HOME: path.join(target, "beta-launcher"),
          },
        )
      ));
      const concurrentResults = await Promise.all(
        concurrentEnvironments.map((environment) => (
          runPackaged(executable, environment)
        )),
      );
      requirement(
        "two concurrent packaged smokes both reach their own backend",
        concurrentResults.every((result) => result.status === 0)
          && concurrentMarkers.every((marker) => existsSync(marker)),
        concurrentResults.map((result) => result.output).join("\n---\n"),
      );
      for (let index = 0; index < concurrentTargets.length; index += 1) {
        const evidence = safeRead(concurrentMarkers[index]);
        let measured = null;
        try {
          measured = evidence.ok ? JSON.parse(evidence.value) : null;
        } catch {}
        requirement(
          `concurrent smoke ${index + 1} kept a unique userData identity`,
          measured?.HOME === concurrentHome
            && measured?.USERPROFILE === concurrentHome
            && measured?.BRAINSTEM_HOME === concurrentTargets[index]
            && measured?.REQUESTED_USER_DATA_DIR
              === concurrentEnvironments[index].BRAINSTEM_BETA_USER_DATA_DIR
            && measured?.ACTUAL_USER_DATA_DIR
              === concurrentEnvironments[index].BRAINSTEM_BETA_USER_DATA_DIR,
          measured ? JSON.stringify(measured) : evidence.detail,
        );
      }
      const failureFixtureReady = existsSync(python);
      requirement(
        "backend-failure fixture has an activated Python launcher",
        failureFixtureReady,
        python,
      );
      if (failureFixtureReady) {
        writeFileSync(
          python,
          "#!/bin/sh\n"
          + 'if [ "$1" = "-B" ]; then exit 0; fi\n'
          + "exit 17\n",
        );
        chmodSync(python, 0o700);
      }
      rmSync(serviceMarker, { force: true });
      const failingSmoke = failureFixtureReady
        ? spawnSync(executable, [], {
            encoding: "utf8",
            env: packagedEnvironment(
              isolatedHome,
              "backend-failure",
              serviceMarker,
              { BRAINSTEM_BETA_SMOKE_EXIT_MS: "2000" },
            ),
            timeout: 30000,
            windowsHide: true,
          })
        : {
            status: null,
            stderr: "Activated Python launcher was unavailable.",
          };
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

}

function summarize() {
  const failures = results.filter((result) => !result.pass);
  process.stdout.write(
    `\n${failures.length ? "PACKAGE NOT READY" : "PACKAGE READY"} — ${
      results.length - failures.length
    }/${results.length} pass\n`,
  );
  process.exitCode = failures.length ? 1 : 0;
}

main().then(summarize).catch((error) => {
  requirement(
    "package gate completed without an internal crash",
    false,
    String(error?.stack || error),
  );
  summarize();
});
