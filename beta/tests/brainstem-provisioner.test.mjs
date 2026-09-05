import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import {
  after,
  before,
  test,
} from "node:test";
import {
  chmodSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

import {
  BrainstemProvisioner,
  buildInstallerInvocation,
  inspectBrainstemRuntime,
  loadBootstrapBundle,
  PYTHON_READINESS_SCRIPT,
  validateBootstrapProvenance,
} from "../electron/brainstem-provisioner.mjs";
import { provisioningLockPath } from "../electron/provision-lock.mjs";

const betaDir = path.resolve(import.meta.dirname, "..");
const scratchRoot = path.join(betaDir, ".test-tmp", "brainstem-provisioner");
const COMMIT = "a".repeat(40);

before(() => {
  rmSync(scratchRoot, { recursive: true, force: true });
  mkdirSync(scratchRoot, { recursive: true });
});

after(() => {
  rmSync(scratchRoot, { recursive: true, force: true });
});

function scratch(name) {
  return mkdtempSync(path.join(scratchRoot, `${name}-`));
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function provenance(commit = COMMIT) {
  const unix = "#!/bin/bash\n";
  const windows = "Write-Host bootstrap\n";
  return {
    manifest: {
      schema: 1,
      product: "rapp-brainstem-frontier",
      mode: "release",
      commit,
      repositoryUrl: "https://github.com/microsoft/aibast-agents-library.git",
      sourceRef: "main",
      installers: {
        "install.sh": { sha256: sha256(unix) },
        "install.ps1": { sha256: sha256(windows) },
      },
    },
    unix,
    windows,
  };
}

function writeBundle(directory, commit = COMMIT) {
  const fixture = provenance(commit);
  mkdirSync(directory, { recursive: true });
  writeFileSync(path.join(directory, "install.sh"), fixture.unix);
  writeFileSync(path.join(directory, "install.ps1"), fixture.windows);
  writeFileSync(
    path.join(directory, "provenance.json"),
    `${JSON.stringify(fixture.manifest, null, 2)}\n`,
  );
  return fixture.manifest;
}

function config(brainstemHome) {
  return {
    brainstemHome,
    brainstemDir: path.join(brainstemHome, "src", "rapp_brainstem"),
    python: path.join(brainstemHome, "venv", "bin", "python"),
  };
}

function materializeRuntime(brainstemHome) {
  const runtime = path.join(brainstemHome, "src", "rapp_brainstem");
  const agents = path.join(runtime, "agents");
  const python = path.join(brainstemHome, "venv", "bin", "python");
  mkdirSync(agents, { recursive: true });
  mkdirSync(path.dirname(python), { recursive: true });
  writeFileSync(path.join(runtime, "brainstem.py"), "print('ready')\n");
  writeFileSync(path.join(runtime, "requirements.txt"), "flask\n");
  writeFileSync(path.join(runtime, "VERSION"), "0.6.16\n");
  writeFileSync(path.join(runtime, "soul.md"), "safe soul\n");
  writeFileSync(
    path.join(agents, "context_memory_agent.py"),
    "class ContextMemoryAgent: pass\n",
  );
  writeFileSync(
    path.join(agents, "manage_memory_agent.py"),
    "class ManageMemoryAgent: pass\n",
  );
  writeFileSync(python, "#!/bin/sh\nexit 0\n");
  chmodSync(python, 0o700);
  return { agents, python, runtime };
}

function snapshotTree(root) {
  if (!existsSync(root)) return null;
  const entries = [];
  const walk = (directory) => {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const absolute = path.join(directory, entry.name);
      const relative = path.relative(root, absolute);
      if (entry.isDirectory()) {
        entries.push([`${relative}/`, statSync(absolute).mode & 0o777]);
        walk(absolute);
      } else {
        entries.push([
          relative,
          createHash("sha256").update(readFileSync(absolute)).digest("hex"),
        ]);
      }
    }
  };
  walk(root);
  return entries.sort((left, right) => left[0].localeCompare(right[0]));
}

async function fixturePythonProbe(_python, _home, brainstemFile) {
  const source = readFileSync(brainstemFile, "utf8");
  if (source.includes("SYNTAX_ERROR")) {
    throw new Error("SyntaxError: invalid syntax");
  }
}

function processExists(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

async function waitFor(predicate, timeoutMs = 5_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (predicate()) return true;
    await new Promise((resolve) => setTimeout(resolve, 25));
  }
  return false;
}

test("already-ready runtime returns without reading provenance or mutating home", async () => {
  const root = scratch("ready");
  const brainstemHome = path.join(root, "untouched-home");
  let installerCalls = 0;
  const provisioner = new BrainstemProvisioner({
    config: config(brainstemHome),
    isPackaged: true,
    resourcesPath: path.join(root, "missing-resources"),
    inspectRuntime: async () => ({ ready: true, issues: [] }),
    loadBundle: () => {
      throw new Error("provenance must not be read for a ready runtime");
    },
    runInstaller: async () => {
      installerCalls += 1;
      return { code: 0 };
    },
  });

  assert.deepEqual(await provisioner.ensure(), {
    provisioned: false,
    reused: true,
  });
  assert.equal(installerCalls, 0);
  assert.equal(existsSync(brainstemHome), false);
});

test("clean runtime inspection reports provisioning is needed", async () => {
  let pythonCalls = 0;
  const result = await inspectBrainstemRuntime(config("/isolated/brainstem"), {
    fileExists: () => false,
    runPython: async () => {
      pythonCalls += 1;
    },
  });
  assert.equal(result.ready, false);
  assert.equal(result.issues.length, 7);
  assert.match(result.issues.join("\n"), /brainstem\.py/);
  assert.match(result.issues.join("\n"), /soul\.md/);
  assert.match(result.issues.join("\n"), /context_memory_agent\.py/);
  assert.match(result.issues.join("\n"), /manage_memory_agent\.py/);
  assert.match(result.issues.join("\n"), /Python environment/);
  assert.equal(pythonCalls, 0);
});

test("an installed but incompatible runtime requires provisioning", async () => {
  let pythonCalls = 0;
  const result = await inspectBrainstemRuntime(config("/isolated/brainstem"), {
    fileExists: () => true,
    readText: () => "0.6.15\n",
    runPython: async () => {
      pythonCalls += 1;
    },
  });
  assert.equal(result.ready, false);
  assert.match(result.issues.join("\n"), /compatible minimum 0\.6\.16/);
  assert.equal(pythonCalls, 0);
});

test("runtime dependency probe receives the isolated BRAINSTEM_HOME", async () => {
  let probedHome;
  let probedSource;
  const brainstemHome = "/isolated/brainstem";
  const result = await inspectBrainstemRuntime(config(brainstemHome), {
    fileExists: () => true,
    readText: () => "0.6.16\n",
    runPython: async (_python, receivedHome, brainstemFile) => {
      probedHome = receivedHome;
      probedSource = brainstemFile;
    },
  });
  assert.equal(result.ready, true);
  assert.equal(probedHome, brainstemHome);
  assert.equal(probedSource, "/isolated/brainstem/src/rapp_brainstem/brainstem.py");
  assert.match(PYTHON_READINESS_SCRIPT, /sys\.version_info < required/);
  assert.match(PYTHON_READINESS_SCRIPT, /compile\(source/);
});

test("partial or old runtimes fail closed without mutation", async (context) => {
  const cases = [
    {
      name: "missing soul",
      mutate: ({ runtime }) => rmSync(path.join(runtime, "soul.md")),
      expected: /Brainstem soul is missing/,
    },
    {
      name: "missing ContextMemory",
      mutate: ({ agents }) => rmSync(
        path.join(agents, "context_memory_agent.py"),
      ),
      expected: /ContextMemory agent is missing/,
    },
    {
      name: "missing ManageMemory",
      mutate: ({ agents }) => rmSync(
        path.join(agents, "manage_memory_agent.py"),
      ),
      expected: /ManageMemory agent is missing/,
    },
    {
      name: "missing brainstem.py",
      mutate: ({ runtime }) => rmSync(path.join(runtime, "brainstem.py")),
      expected: /Brainstem server is missing/,
    },
    {
      name: "missing Python",
      mutate: ({ python }) => rmSync(python),
      expected: /Python environment is missing/,
    },
    {
      name: "old runtime",
      mutate: ({ runtime }) => writeFileSync(
        path.join(runtime, "VERSION"),
        "0.6.15\n",
      ),
      expected: /compatible minimum 0\.6\.16/,
    },
    {
      name: "invalid brainstem syntax",
      mutate: ({ runtime }) => writeFileSync(
        path.join(runtime, "brainstem.py"),
        "SYNTAX_ERROR\n",
      ),
      expected: /SyntaxError/,
    },
    {
      name: "Python 3.10",
      mutate: () => {},
      probe: async () => {
        throw new Error("Python 3.11+ is required; found 3.10");
      },
      expected: /Python 3\.11\+ is required/,
    },
  ];

  for (const fixture of cases) {
    await context.test(fixture.name, async () => {
      const root = scratch(`partial-${fixture.name.replaceAll(" ", "-")}`);
      const brainstemHome = path.join(root, "brainstem");
      const paths = materializeRuntime(brainstemHome);
      fixture.mutate(paths);
      const before = snapshotTree(brainstemHome);
      let installerCalls = 0;
      const provisioner = new BrainstemProvisioner({
        config: config(brainstemHome),
        isPackaged: true,
        bootstrapDirectory: path.join(root, "unused-bootstrap"),
        inspectRuntime: (runtimeConfig) => inspectBrainstemRuntime(
          runtimeConfig,
          { runPython: fixture.probe || fixturePythonProbe },
        ),
        runInstaller: async () => {
          installerCalls += 1;
          return { code: 0 };
        },
      });

      await assert.rejects(provisioner.ensure(), (error) => {
        assert.match(error.message, fixture.expected);
        assert.match(error.message, /Automatic repair was not attempted/);
        assert.match(error.message, /no existing files were changed/i);
        return true;
      });
      assert.equal(installerCalls, 0);
      assert.deepEqual(snapshotTree(brainstemHome), before);
      assert.equal(existsSync(provisioningLockPath(brainstemHome)), false);
    });
  }
});

test("packaged provisioning runs the pinned runtime-only installer then verifies", async () => {
  const root = scratch("success");
  const brainstemHome = path.join(root, "brainstem");
  const bundleDirectory = path.join(root, "bootstrap");
  writeBundle(bundleDirectory);
  const states = [];
  let inspections = 0;
  let invocation;
  let stageHome;
  const provisioner = new BrainstemProvisioner({
    config: config(brainstemHome),
    isPackaged: true,
    bootstrapDirectory: bundleDirectory,
    env: {
      HOME: "/developer-home",
      USERPROFILE: String.raw`C:\Users\developer`,
    },
    inspectRuntime: async () => {
      inspections += 1;
      return inspections >= 3
        ? { ready: true, issues: [] }
        : { ready: false, issues: ["runtime missing"] };
    },
    runInstaller: async (request) => {
      invocation = request.invocation;
      stageHome = request.stageHome;
      return { code: 0, signal: null };
    },
    onState: (state) => states.push(state),
  });

  const result = await provisioner.ensure();
  assert.equal(result.provisioned, true);
  assert.equal(result.commit, COMMIT);
  assert.equal(invocation.command, "/bin/bash");
  assert.deepEqual(invocation.args.slice(-4), [
    "--runtime-only",
    "--no-launch",
    "--version",
    COMMIT,
  ]);
  assert.equal(invocation.env.BRAINSTEM_HOME, stageHome);
  assert.notEqual(stageHome, brainstemHome);
  assert.equal(invocation.env.HOME, "/developer-home");
  assert.notEqual(invocation.env.HOME, invocation.env.BRAINSTEM_HOME);
  assert.equal(
    invocation.env.BRAINSTEM_REPO_URL,
    "https://github.com/microsoft/aibast-agents-library.git",
  );
  assert.match(invocation.env.BRAINSTEM_VERSION_URL, new RegExp(COMMIT));
  assert.equal(inspections, 4);
  assert.equal(existsSync(brainstemHome), true);
  assert.equal(existsSync(stageHome), false);
  assert.deepEqual(
    states.map((state) => state.phase),
    ["checking", "provisioning", "verifying"],
  );
});

test("provisioning failure remains fail-closed with log and next action", async () => {
  const root = scratch("failure");
  const brainstemHome = path.join(root, "brainstem");
  const bundleDirectory = path.join(root, "bootstrap");
  writeBundle(bundleDirectory);
  let stageHome;
  const provisioner = new BrainstemProvisioner({
    config: config(brainstemHome),
    isPackaged: true,
    bootstrapDirectory: bundleDirectory,
    inspectRuntime: async () => ({
      ready: false,
      issues: ["Python is missing"],
    }),
    runInstaller: async (request) => {
      stageHome = request.stageHome;
      writeFileSync(path.join(stageHome, "partial"), "must be removed");
      return { code: 23, signal: null };
    },
  });

  await assert.rejects(
    provisioner.ensure(),
    (error) => {
      assert.match(error.message, /exited with code 23/);
      assert.match(error.message, /frontier-provision\.log/);
      assert.match(error.message, /fix the prerequisite or network error/);
      assert.match(error.message, /No runtime was activated/);
      return true;
    },
  );
  assert.equal(existsSync(brainstemHome), false);
  assert.equal(existsSync(stageHome), false);
  assert.equal(existsSync(provisioningLockPath(brainstemHome)), false);
});

test("failed final readiness rolls activation back to an absent target", async () => {
  const root = scratch("rollback");
  const brainstemHome = path.join(root, "brainstem");
  const bundleDirectory = path.join(root, "bootstrap");
  writeBundle(bundleDirectory);
  let stageHome;
  const provisioner = new BrainstemProvisioner({
    config: config(brainstemHome),
    isPackaged: true,
    bootstrapDirectory: bundleDirectory,
    inspectRuntime: async (runtimeConfig) => ({
      ready: runtimeConfig.brainstemHome !== brainstemHome,
      issues: runtimeConfig.brainstemHome === brainstemHome
        ? ["final target rejected"]
        : [],
    }),
    runInstaller: async (request) => {
      stageHome = request.stageHome;
      writeFileSync(path.join(stageHome, "verified-stage"), "yes");
      return { code: 0, signal: null };
    },
  });

  await assert.rejects(
    provisioner.ensure(),
    /failed its final readiness check[\s\S]*rolled back/,
  );
  assert.equal(existsSync(brainstemHome), false);
  assert.equal(existsSync(stageHome), false);
  assert.equal(existsSync(provisioningLockPath(brainstemHome)), false);
});

test("a target created during staging is preserved and never overwritten", async () => {
  const root = scratch("activation-race");
  const brainstemHome = path.join(root, "brainstem");
  const bundleDirectory = path.join(root, "bootstrap");
  writeBundle(bundleDirectory);
  let stageHome;
  const provisioner = new BrainstemProvisioner({
    config: config(brainstemHome),
    isPackaged: true,
    bootstrapDirectory: bundleDirectory,
    inspectRuntime: async (runtimeConfig) => ({
      ready: runtimeConfig.brainstemHome !== brainstemHome,
      issues: runtimeConfig.brainstemHome === brainstemHome ? ["absent"] : [],
    }),
    runInstaller: async (request) => {
      stageHome = request.stageHome;
      mkdirSync(brainstemHome);
      writeFileSync(path.join(brainstemHome, "manual-owner"), "preserve me");
      return { code: 0, signal: null };
    },
  });

  await assert.rejects(
    provisioner.ensure(),
    /appeared while staging was in progress[\s\S]*existing target was preserved/,
  );
  assert.equal(
    readFileSync(path.join(brainstemHome, "manual-owner"), "utf8"),
    "preserve me",
  );
  assert.equal(existsSync(stageHome), false);
});

test("invalid packaged provenance blocks before installer or home mutation", async () => {
  const root = scratch("invalid");
  const brainstemHome = path.join(root, "brainstem");
  const bundleDirectory = path.join(root, "bootstrap");
  writeBundle(bundleDirectory, "moving-main");
  let installerCalls = 0;
  const provisioner = new BrainstemProvisioner({
    config: config(brainstemHome),
    isPackaged: true,
    bootstrapDirectory: bundleDirectory,
    inspectRuntime: async () => ({ ready: false, issues: ["missing"] }),
    runInstaller: async () => {
      installerCalls += 1;
      return { code: 0 };
    },
  });

  await assert.rejects(
    provisioner.ensure(),
    /full 40-character SHA[\s\S]*Nothing was installed[\s\S]*published Frontier package/,
  );
  assert.equal(installerCalls, 0);
  assert.equal(existsSync(brainstemHome), false);
});

test("release provenance is canonical and fork builds are distinctly development", () => {
  const release = provenance().manifest;
  assert.equal(validateBootstrapProvenance(release).mode, "release");
  assert.throws(
    () => validateBootstrapProvenance({
      ...release,
      repositoryUrl: "https://github.com/example/fork.git",
    }),
    /release provenance must use .*microsoft\/aibast-agents-library/,
  );
  const development = validateBootstrapProvenance({
    ...release,
    mode: "development",
    product: "rapp-brainstem-frontier-development",
    repositoryUrl: "https://github.com/example/fork.git",
  });
  assert.equal(development.mode, "development");
  assert.equal(development.product, "rapp-brainstem-frontier-development");
});

test("concurrent launches share one provisioning transaction", async () => {
  const root = scratch("concurrent");
  const brainstemHome = path.join(root, "brainstem");
  const bundleDirectory = path.join(root, "bootstrap");
  writeBundle(bundleDirectory);
  let ready = false;
  let installerCalls = 0;
  const options = {
    config: config(brainstemHome),
    isPackaged: true,
    bootstrapDirectory: bundleDirectory,
    inspectRuntime: async () => ({
      ready,
      issues: ready ? [] : ["missing"],
    }),
    runInstaller: async () => {
      installerCalls += 1;
      await new Promise((resolve) => setImmediate(resolve));
      ready = true;
      return { code: 0, signal: null };
    },
  };
  const first = new BrainstemProvisioner(options);
  const second = new BrainstemProvisioner(options);

  const results = await Promise.all([first.ensure(), second.ensure()]);
  assert.equal(installerCalls, 1);
  assert.equal(results[0].provisioned, true);
  assert.deepEqual(results[1], results[0]);
});

test("shutdown during readiness check cannot start a late installer", async () => {
  const root = scratch("shutdown");
  const brainstemHome = path.join(root, "brainstem");
  const bundleDirectory = path.join(root, "bootstrap");
  writeBundle(bundleDirectory);
  let finishInspection;
  let installerCalls = 0;
  const provisioner = new BrainstemProvisioner({
    config: config(brainstemHome),
    isPackaged: true,
    bootstrapDirectory: bundleDirectory,
    inspectRuntime: () => new Promise((resolve) => {
      finishInspection = resolve;
    }),
    runInstaller: async () => {
      installerCalls += 1;
      return { code: 0 };
    },
  });

  const pending = provisioner.ensure();
  await new Promise((resolve) => setImmediate(resolve));
  await provisioner.stop();
  finishInspection({ ready: false, issues: ["missing"] });
  await assert.rejects(pending, /Frontier is closing/);
  assert.equal(installerCalls, 0);
  assert.equal(existsSync(brainstemHome), false);
});

test("installer logs scrub credential canaries", async () => {
  const root = scratch("scrubbed-log");
  const bundleDirectory = path.join(root, "bootstrap");
  writeBundle(bundleDirectory);
  const bundle = loadBootstrapBundle({ directory: bundleDirectory });
  const logPath = path.join(root, "provision.log");
  const provisioner = new BrainstemProvisioner({
    config: config(path.join(root, "brainstem")),
  });
  const result = await provisioner.runInstaller({
    command: "/bin/bash",
    args: [
      "-c",
      "printf '%s\\n' 'GITHUB_TOKEN=ghp_CanarySecret123456' "
        + "'Authorization: Bearer canaryBearer123456' "
        + "'https://alice:supersecret@example.test/path'",
    ],
    env: process.env,
  }, bundle, logPath);
  assert.equal(result.code, 0);
  const log = readFileSync(logPath, "utf8");
  for (const secret of [
    "ghp_CanarySecret123456",
    "canaryBearer123456",
    "alice",
    "supersecret",
  ]) {
    assert.doesNotMatch(log, new RegExp(secret));
  }
  assert.match(log, /\[REDACTED\]/);
});

test("cancellation terminates the installer process group and grandchild", {
  skip: process.platform === "win32",
}, async () => {
  const root = scratch("process-tree");
  const bundleDirectory = path.join(root, "bootstrap");
  writeBundle(bundleDirectory);
  const bundle = loadBootstrapBundle({ directory: bundleDirectory });
  const marker = path.join(root, "grandchild.pid");
  const provisioner = new BrainstemProvisioner({
    config: config(path.join(root, "brainstem")),
  });
  const running = provisioner.runInstaller({
    command: process.execPath,
    args: [
      path.join(
        betaDir,
        "tests",
        "fixtures",
        "process-tree-parent.mjs",
      ),
      marker,
    ],
    env: process.env,
  }, bundle, path.join(root, "tree.log"));
  assert.equal(await waitFor(() => existsSync(marker)), true);
  const grandchildPid = Number.parseInt(readFileSync(marker, "utf8"), 10);
  assert.equal(processExists(grandchildPid), true);
  await provisioner.stop();
  await running;
  assert.equal(await waitFor(() => !processExists(grandchildPid)), true);
});

test("Windows invocation also pins the same immutable commit", () => {
  const root = scratch("windows");
  const bundleDirectory = path.join(root, "bootstrap");
  writeBundle(bundleDirectory);
  const bundle = loadBootstrapBundle({
    directory: bundleDirectory,
    platform: "win32",
  });
  const invocation = buildInstallerInvocation({
    bundle,
    config: config(String.raw`C:\isolated\.brainstem`),
    env: {
      HOME: "/developer-home",
      PATH: "fixture",
      USERPROFILE: String.raw`C:\Users\developer`,
    },
    platform: "win32",
  });
  assert.equal(invocation.command, "powershell.exe");
  assert.deepEqual(invocation.args.slice(-4), [
    "--runtime-only",
    "--no-launch",
    "--version",
    COMMIT,
  ]);
  assert.equal(invocation.env.BRAINSTEM_HOME, String.raw`C:\isolated\.brainstem`);
  assert.equal(invocation.env.USERPROFILE, String.raw`C:\Users\developer`);
  assert.notEqual(
    invocation.env.USERPROFILE,
    invocation.env.BRAINSTEM_HOME,
  );
});

test("Windows packaged first launch provisions then verifies as the user", async () => {
  const root = scratch("windows-first-launch");
  const brainstemHome = path.join(root, "user-brainstem");
  const bundleDirectory = path.join(root, "bootstrap");
  writeBundle(bundleDirectory);
  let inspections = 0;
  let invocation;
  let stageHome;
  const phases = [];
  const provisioner = new BrainstemProvisioner({
    config: config(brainstemHome),
    isPackaged: true,
    bootstrapDirectory: bundleDirectory,
    env: {
      USERPROFILE: String.raw`C:\Users\standard`,
      PATH: String.raw`C:\Windows\System32`,
    },
    platform: "win32",
    inspectRuntime: async () => {
      inspections += 1;
      return inspections >= 3
        ? { ready: true, issues: [] }
        : { ready: false, issues: ["runtime missing"] };
    },
    runInstaller: async (request) => {
      invocation = request.invocation;
      stageHome = request.stageHome;
      return { code: 0, signal: null };
    },
    onState: (state) => phases.push(state.phase),
  });

  const result = await provisioner.ensure();
  assert.equal(result.provisioned, true);
  assert.equal(inspections, 4);
  assert.equal(invocation.command, "powershell.exe");
  assert.ok(invocation.args.includes("-NonInteractive"));
  assert.ok(invocation.args.includes("--runtime-only"));
  assert.ok(invocation.args.includes("--no-launch"));
  assert.equal(invocation.env.BRAINSTEM_HOME, stageHome);
  assert.notEqual(stageHome, brainstemHome);
  assert.equal(invocation.env.USERPROFILE, String.raw`C:\Users\standard`);
  assert.equal(existsSync(brainstemHome), true);
  assert.deepEqual(phases, ["checking", "provisioning", "verifying"]);
});

test("commit provenance gate kills a permissive-regex mutant", async () => {
  const invalid = provenance("moving-main").manifest;
  const gate = (validate) => {
    assert.throws(
      () => validate(invalid),
      /commit must be a full 40-character SHA/,
    );
  };
  gate(validateBootstrapProvenance);

  const sourcePath = path.join(
    betaDir,
    "electron",
    "brainstem-provisioner.mjs",
  );
  const original = readFileSync(sourcePath, "utf8");
  const mutant = original.replace(
    "const COMMIT_PATTERN = /^[0-9a-f]{40}$/i;",
    "const COMMIT_PATTERN = /^.+$/;",
  );
  assert.notEqual(mutant, original, "mutation target must exist exactly");
  const mutantDirectory = scratch("mutant");
  const mutantPath = path.join(mutantDirectory, "brainstem-provisioner.mjs");
  writeFileSync(mutantPath, mutant);
  writeFileSync(
    path.join(mutantDirectory, "brainstem-process.mjs"),
    readFileSync(
      path.join(betaDir, "electron", "brainstem-process.mjs"),
      "utf8",
    ),
  );
  for (const dependency of ["provision-lock.mjs", "safe-log.mjs"]) {
    writeFileSync(
      path.join(mutantDirectory, dependency),
      readFileSync(path.join(betaDir, "electron", dependency), "utf8"),
    );
  }
  const mutatedModule = await import(
    `${pathToFileURL(mutantPath).href}?mutation=${Date.now()}`
  );

  assert.throws(
    () => gate(mutatedModule.validateBootstrapProvenance),
    /Missing expected exception/,
  );
});
