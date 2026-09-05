import { randomBytes } from "node:crypto";
import {
  existsSync,
  mkdirSync,
  readFileSync,
  renameSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function randomToken() {
  return randomBytes(32).toString("hex");
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

function readSnapshot(directory) {
  let raw = null;
  let owner = null;
  let mtimeMs = 0;
  try {
    mtimeMs = statSync(directory).mtimeMs;
  } catch {
    return null;
  }
  try {
    raw = readFileSync(path.join(directory, "owner.json"), "utf8");
    owner = JSON.parse(raw);
  } catch {}
  return { directory, mtimeMs, owner, raw };
}

function validOwner(snapshot) {
  return Boolean(
    snapshot?.owner
    && typeof snapshot.owner.token === "string"
    && /^[0-9a-f]{64}$/.test(snapshot.owner.token)
    && Number.isInteger(snapshot.owner.pid)
    && snapshot.owner.pid > 0,
  );
}

function sameOwner(left, right) {
  if (!left || !right) return false;
  if (validOwner(left) && validOwner(right)) {
    return (
      left.owner.token === right.owner.token
      && left.owner.pid === right.owner.pid
    );
  }
  return left.raw === right.raw && left.mtimeMs === right.mtimeMs;
}

function reclaimable(snapshot, {
  invalidOwnerGraceMs,
  isProcessAlive,
  now,
}) {
  if (!snapshot) return false;
  if (validOwner(snapshot)) {
    return !isProcessAlive(snapshot.owner.pid);
  }
  return now() - snapshot.mtimeMs >= invalidOwnerGraceMs;
}

function writeOwnerAtomically(
  directory,
  owner,
  {
    writeOwner = writeFileSync,
  } = {},
) {
  const temporary = path.join(directory, `owner.${owner.token}.tmp`);
  const ownerPath = path.join(directory, "owner.json");
  try {
    writeOwner(
      temporary,
      `${JSON.stringify(owner)}\n`,
      { flag: "wx", mode: 0o600 },
    );
    renameSync(temporary, ownerPath);
  } catch (error) {
    rmSync(temporary, { force: true });
    throw error;
  }
}

function createOwnedDirectory(
  directory,
  {
    now,
    pid,
    token,
    writeOwner,
  },
) {
  mkdirSync(directory, { mode: 0o700 });
  try {
    writeOwnerAtomically(directory, {
      token,
      pid,
      startedAt: new Date(now()).toISOString(),
      startedAtMs: now(),
    }, { writeOwner });
  } catch (error) {
    rmSync(directory, { recursive: true, force: true });
    throw error;
  }
}

function restoreUnexpectedTakeover(lockPath, tombstonePath, token) {
  const ownedPath = `${lockPath}.aborted-${token}`;
  try {
    renameSync(lockPath, ownedPath);
    renameSync(tombstonePath, lockPath);
  } finally {
    rmSync(ownedPath, { recursive: true, force: true });
  }
}

function releaseOwnedLock(lockPath, token) {
  const before = readSnapshot(lockPath);
  if (!validOwner(before) || before.owner.token !== token) return false;
  const tombstonePath = `${lockPath}.release-${token}`;
  try {
    renameSync(lockPath, tombstonePath);
  } catch (error) {
    if (["ENOENT", "EEXIST", "ENOTEMPTY"].includes(error?.code)) return false;
    throw error;
  }
  const moved = readSnapshot(tombstonePath);
  if (!validOwner(moved) || moved.owner.token !== token) {
    if (!existsSync(lockPath)) {
      renameSync(tombstonePath, lockPath);
    }
    return false;
  }
  rmSync(tombstonePath, { recursive: true, force: true });
  return true;
}

function removeReclaimableDirectory(
  directory,
  observed,
  {
    invalidOwnerGraceMs,
    isProcessAlive,
    now,
    token,
  },
) {
  const tombstonePath = `${directory}.stale-${token}`;
  try {
    renameSync(directory, tombstonePath);
  } catch (error) {
    if (["ENOENT", "EEXIST", "ENOTEMPTY"].includes(error?.code)) return false;
    throw error;
  }
  const moved = readSnapshot(tombstonePath);
  if (
    !sameOwner(observed, moved)
    || !reclaimable(moved, {
      invalidOwnerGraceMs,
      isProcessAlive,
      now,
    })
  ) {
    if (!existsSync(directory)) renameSync(tombstonePath, directory);
    return false;
  }
  rmSync(tombstonePath, { recursive: true, force: true });
  return true;
}

function atomicTakeover(
  lockPath,
  observed,
  {
    invalidOwnerGraceMs,
    isProcessAlive,
    now,
    pid,
    token,
    writeOwner,
  },
) {
  const tombstonePath = `${lockPath}.stale-${token}`;
  try {
    renameSync(lockPath, tombstonePath);
  } catch (error) {
    if (["ENOENT", "EEXIST", "ENOTEMPTY"].includes(error?.code)) return null;
    throw error;
  }

  try {
    createOwnedDirectory(lockPath, { now, pid, token, writeOwner });
  } catch (error) {
    if (error?.code === "EEXIST") {
      const moved = readSnapshot(tombstonePath);
      if (
        sameOwner(observed, moved)
        && reclaimable(moved, {
          invalidOwnerGraceMs,
          isProcessAlive,
          now,
        })
      ) {
        rmSync(tombstonePath, { recursive: true, force: true });
        return null;
      }
    }
    if (!existsSync(lockPath)) {
      try {
        renameSync(tombstonePath, lockPath);
      } catch {}
    }
    throw error;
  }

  const moved = readSnapshot(tombstonePath);
  const validTakeover = sameOwner(observed, moved)
    && reclaimable(moved, {
      invalidOwnerGraceMs,
      isProcessAlive,
      now,
    });
  if (!validTakeover) {
    restoreUnexpectedTakeover(lockPath, tombstonePath, token);
    return null;
  }
  rmSync(tombstonePath, { recursive: true, force: true });
  return {
    lockPath,
    reclaimed: true,
    token,
    release: () => releaseOwnedLock(lockPath, token),
  };
}

export function provisioningLockPath(brainstemHome) {
  const resolved = path.resolve(brainstemHome);
  const basename = path.basename(resolved);
  const prefix = basename.startsWith(".") ? basename : `.${basename}`;
  return path.join(
    path.dirname(resolved),
    `${prefix}.frontier-provision.lock`,
  );
}

export async function acquireProvisioningLock({
  brainstemHome,
  invalidOwnerGraceMs = 2_000,
  isProcessAlive = processExists,
  lockPath = provisioningLockPath(brainstemHome),
  now = Date.now,
  onWait = () => {},
  pid = process.pid,
  pollIntervalMs = 100,
  sleep = wait,
  timeoutMs = 10 * 60_000,
  token = randomToken(),
  writeOwner = writeFileSync,
} = {}) {
  mkdirSync(path.dirname(lockPath), { recursive: true, mode: 0o700 });
  const reclaimGuard = `${lockPath}.reclaim`;
  const deadline = now() + timeoutMs;
  while (now() < deadline) {
    const guardSnapshot = readSnapshot(reclaimGuard);
    if (guardSnapshot) {
      if (reclaimable(guardSnapshot, {
        invalidOwnerGraceMs,
        isProcessAlive,
        now,
      })) {
        removeReclaimableDirectory(reclaimGuard, guardSnapshot, {
          invalidOwnerGraceMs,
          isProcessAlive,
          now,
          token,
        });
        continue;
      }
      onWait({ lockPath, owner: guardSnapshot.owner || null });
      await sleep(pollIntervalMs);
      continue;
    }

    try {
      createOwnedDirectory(lockPath, {
        now,
        pid,
        token,
        writeOwner,
      });
      return {
        lockPath,
        reclaimed: false,
        token,
        release: () => releaseOwnedLock(lockPath, token),
      };
    } catch (error) {
      if (error?.code !== "EEXIST") throw error;
    }

    const observed = readSnapshot(lockPath);
    if (reclaimable(observed, {
      invalidOwnerGraceMs,
      isProcessAlive,
      now,
    })) {
      try {
        createOwnedDirectory(reclaimGuard, {
          now,
          pid,
          token,
          writeOwner,
        });
      } catch (error) {
        if (error?.code !== "EEXIST") throw error;
        await sleep(pollIntervalMs);
        continue;
      }
      try {
        const guarded = readSnapshot(lockPath);
        if (reclaimable(guarded, {
          invalidOwnerGraceMs,
          isProcessAlive,
          now,
        })) {
          const lease = atomicTakeover(lockPath, guarded, {
            invalidOwnerGraceMs,
            isProcessAlive,
            now,
            pid,
            token,
            writeOwner,
          });
          if (lease) return lease;
        }
      } finally {
        releaseOwnedLock(reclaimGuard, token);
      }
    }
    onWait({ lockPath, owner: observed?.owner || null });
    await sleep(pollIntervalMs);
  }
  throw new Error(
    `Timed out waiting for the Brainstem provisioning lock at ${lockPath}.`,
  );
}

export const provisionLockInternals = {
  readSnapshot,
  releaseOwnedLock,
};
