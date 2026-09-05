import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import {
  after,
  before,
  test,
} from "node:test";
import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

import {
  BrainstemProvisioner,
  buildInstallerInvocation,
  inspectBrainstemRuntime,
  loadBootstrapBundle,
  validateBootstrapProvenance,
} from "../electron/brainstem-provisioner.mjs";

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
  assert.equal(result.issues.length, 4);
  assert.match(result.issues.join("\n"), /brainstem\.py/);
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
  const brainstemHome = "/isolated/brainstem";
  const result = await inspectBrainstemRuntime(config(brainstemHome), {
    fileExists: () => true,
    readText: () => "0.6.16\n",
    runPython: async (_python, receivedHome) => {
      probedHome = receivedHome;
    },
  });
  assert.equal(result.ready, true);
  assert.equal(probedHome, brainstemHome);
});

test("packaged provisioning runs the pinned runtime-only installer then verifies", async () => {
  const root = scratch("success");
  const brainstemHome = path.join(root, "brainstem");
  const bundleDirectory = path.join(root, "bootstrap");
  writeBundle(bundleDirectory);
  const states = [];
  let inspections = 0;
  let invocation;
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
  assert.equal(invocation.env.BRAINSTEM_HOME, brainstemHome);
  assert.equal(invocation.env.HOME, "/developer-home");
  assert.notEqual(invocation.env.HOME, invocation.env.BRAINSTEM_HOME);
  assert.equal(
    invocation.env.BRAINSTEM_REPO_URL,
    "https://github.com/microsoft/aibast-agents-library.git",
  );
  assert.match(invocation.env.BRAINSTEM_VERSION_URL, new RegExp(COMMIT));
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
  const provisioner = new BrainstemProvisioner({
    config: config(brainstemHome),
    isPackaged: true,
    bootstrapDirectory: bundleDirectory,
    inspectRuntime: async () => ({
      ready: false,
      issues: ["Python is missing"],
    }),
    runInstaller: async () => ({ code: 23, signal: null }),
  });

  await assert.rejects(
    provisioner.ensure(),
    (error) => {
      assert.match(error.message, /exited with code 23/);
      assert.match(error.message, /frontier-provision\.log/);
      assert.match(error.message, /fix the prerequisite or network error/);
      assert.match(error.message, /Nothing was launched/);
      return true;
    },
  );
  assert.equal(
    existsSync(path.join(brainstemHome, ".frontier-provision.lock")),
    false,
  );
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
  const mutatedModule = await import(
    `${pathToFileURL(mutantPath).href}?mutation=${Date.now()}`
  );

  assert.throws(
    () => gate(mutatedModule.validateBootstrapProvenance),
    /Missing expected exception/,
  );
});
