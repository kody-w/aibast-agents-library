import assert from "node:assert/strict";
import { spawn } from "node:child_process";
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
  readdirSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";

import {
  acquireProvisioningLock,
  provisioningLockPath,
} from "../electron/provision-lock.mjs";

const betaDir = path.resolve(import.meta.dirname, "..");
const scratchRoot = path.join(betaDir, ".test-tmp", "provision-lock");
const worker = path.join(
  betaDir,
  "tests",
  "fixtures",
  "provision-lock-worker.mjs",
);

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

async function waitFor(predicate, timeoutMs = 10_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (predicate()) return true;
    await new Promise((resolve) => setTimeout(resolve, 20));
  }
  return false;
}

function launch(args) {
  const child = spawn(process.execPath, [worker, ...args], {
    stdio: ["ignore", "pipe", "pipe"],
  });
  let output = "";
  child.stdout.on("data", (chunk) => { output += chunk; });
  child.stderr.on("data", (chunk) => { output += chunk; });
  return {
    child,
    completed: new Promise((resolve, reject) => {
      child.once("error", reject);
      child.once("close", (code, signal) => {
        if (code === 0) resolve({ code, signal, output });
        else reject(new Error(
          `lock worker failed (${code ?? signal}): ${output}`,
        ));
      });
    }),
  };
}

test("killed fresh owner is atomically reclaimed by one of two processes", async () => {
  const root = scratch("killed-owner");
  const brainstemHome = path.join(root, "brainstem");
  const events = path.join(root, "events.jsonl");
  const holderReady = path.join(root, "holder.ready");
  const holder = launch([
    brainstemHome,
    events,
    holderReady,
    "hold",
    "0",
  ]);
  assert.equal(await waitFor(() => existsSync(holderReady)), true);
  holder.child.kill("SIGKILL");
  await assert.rejects(holder.completed, /lock worker failed/);
  rmSync(`${events}.active`, { force: true });

  const first = launch([
    brainstemHome,
    events,
    "",
    "once",
    "300",
  ]);
  const second = launch([
    brainstemHome,
    events,
    "",
    "once",
    "300",
  ]);
  await Promise.all([first.completed, second.completed]);

  const rows = readFileSync(events, "utf8")
    .trim()
    .split("\n")
    .map((line) => JSON.parse(line));
  const reclaimers = rows.filter((row) => (
    row.event === "acquired" && row.pid !== holder.child.pid
  ));
  assert.equal(reclaimers.length, 2);
  assert.equal(reclaimers.filter((row) => row.reclaimed).length, 1);
  assert.equal(new Set(reclaimers.map((row) => row.token)).size, 2);
  for (const row of reclaimers) {
    assert.match(row.token, /^[0-9a-f]{64}$/);
  }

  assert.equal(existsSync(`${events}.active`), false);
  assert.equal(existsSync(provisioningLockPath(brainstemHome)), false);
  assert.deepEqual(
    readdirSync(root).filter((name) => name.includes(".stale-")),
    [],
  );
});

test("owner write failure removes the newly-created lock", async () => {
  const root = scratch("owner-write");
  const brainstemHome = path.join(root, "brainstem");
  await assert.rejects(
    acquireProvisioningLock({
      brainstemHome,
      token: "a".repeat(64),
      writeOwner: () => {
        throw new Error("disk full");
      },
    }),
    /disk full/,
  );
  assert.equal(existsSync(provisioningLockPath(brainstemHome)), false);
});

test("release token cannot delete a replacement owner's lock", async () => {
  const root = scratch("release-token");
  const brainstemHome = path.join(root, "brainstem");
  const lease = await acquireProvisioningLock({
    brainstemHome,
    token: "b".repeat(64),
  });
  const lockPath = provisioningLockPath(brainstemHome);
  writeFileSync(
    path.join(lockPath, "owner.json"),
    `${JSON.stringify({
      token: "c".repeat(64),
      pid: process.pid,
      startedAtMs: Date.now(),
    })}\n`,
  );
  assert.equal(lease.release(), false);
  assert.equal(existsSync(lockPath), true);
  rmSync(lockPath, { recursive: true, force: true });
});
