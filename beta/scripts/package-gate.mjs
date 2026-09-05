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

function shellQuote(value) {
  return `'${String(value).replaceAll("'", "'\\''")}'`;
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
    const fakeServer = path.join(runtime, "package-gate-server.mjs");
    const serviceMarker = path.join(isolatedHome, "service-ready");
    try {
      mkdirSync(path.join(runtime, "agents"), { recursive: true });
      mkdirSync(path.dirname(python), { recursive: true });
      writeFileSync(path.join(runtime, "brainstem.py"), "\n");
      writeFileSync(path.join(runtime, "requirements.txt"), "\n");
      writeFileSync(path.join(runtime, "VERSION"), "0.6.16\n");
      writeFileSync(
        fakeServer,
        `import { writeFileSync } from "node:fs";
import http from "node:http";
const health = ${JSON.stringify({
          status: "unauthenticated",
          version: "0.6.16",
          soul: path.join(runtime, "soul.md"),
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
`,
      );
      writeFileSync(path.join(runtime, "soul.md"), "package gate\n");
      writeFileSync(
        python,
        "#!/bin/sh\n"
        + 'if [ "$1" = "-B" ]; then exit 0; fi\n'
        + `exec ${shellQuote(process.execPath)} ${shellQuote(fakeServer)}\n`,
      );
      chmodSync(python, 0o700);
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
        BRAINSTEM_BETA_SMOKE_EXIT_MS: "5000",
        BRAINSTEM_BETA_SMOKE_REQUIRE_READY: "1",
        FAKE_BRAINSTEM_MARKER: serviceMarker,
      };
      const smoke = spawnSync(executable, [], {
        encoding: "utf8",
        env: packagedEnv,
        timeout: 30000,
        windowsHide: true,
      });
      requirement(
        "packaged app passes isolated headless smoke",
        smoke.status === 0,
        String(smoke.stderr || smoke.stdout || "").trim(),
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
