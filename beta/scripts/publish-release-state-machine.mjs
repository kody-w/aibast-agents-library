import { execFile } from "node:child_process";
import { promisify } from "node:util";
import {
  closeSync,
  fsyncSync,
  openSync,
  readFileSync,
  renameSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

import {
  releaseContentFingerprint,
  verifyReleaseSnapshot,
} from "./release-race-guard.mjs";

const execFileAsync = promisify(execFile);

export class ReleaseTransitionError extends Error {
  constructor(message, code, state) {
    super(message);
    this.name = "ReleaseTransitionError";
    this.code = code;
    this.state = state;
  }
}

class StatePersistenceError extends Error {
  constructor(message) {
    super(message);
    this.name = "StatePersistenceError";
  }
}

export function mergeDurableState(state, patch) {
  return {
    ...(state && typeof state === "object" ? state : {}),
    ...(patch && typeof patch === "object" ? patch : {}),
    history: [
      ...(Array.isArray(state?.history) ? state.history : []),
      ...(Array.isArray(patch?.history) ? patch.history : []),
    ],
    integrityViolation:
      state?.integrityViolation === true
      || patch?.integrityViolation === true,
    integrityDetail:
      state?.integrityDetail
      || patch?.integrityDetail
      || null,
    persistenceFailure:
      state?.persistenceFailure === true
      || patch?.persistenceFailure === true,
    persistenceDetail:
      state?.persistenceDetail
      || patch?.persistenceDetail
      || null,
  };
}

export function createAtomicStateWriter(filePath, operations = {}) {
  const fs = {
    openSync,
    writeFileSync,
    fsyncSync,
    closeSync,
    renameSync,
    rmSync,
    ...operations,
  };
  let sequence = 0;
  let failed = false;
  let failure = null;
  return (state) => {
    if (failed) return { ok: false, error: failure };
    const temporaryPath =
      `${filePath}.${process.pid}.${sequence += 1}.state.tmp`;
    let descriptor = null;
    try {
      descriptor = fs.openSync(temporaryPath, "wx", 0o600);
      fs.writeFileSync(
        descriptor,
        `${JSON.stringify(state, null, 2)}\n`,
        "utf8",
      );
      fs.fsyncSync(descriptor);
      fs.closeSync(descriptor);
      descriptor = null;
      fs.renameSync(temporaryPath, filePath);
      return { ok: true };
    } catch (error) {
      failed = true;
      failure = error;
      if (descriptor !== null) {
        try {
          fs.closeSync(descriptor);
        } catch {}
      }
      try {
        fs.rmSync(temporaryPath, { force: true });
      } catch {}
      return { ok: false, error };
    }
  };
}

function createStateRecorder(state, onState) {
  return (phase, detail = "") => {
    state.phase = phase;
    state.history.push({ phase, detail });
    if (state.persistenceFailure) return false;
    try {
      const result = onState(structuredClone(state));
      if (result === false || result?.ok === false) {
        throw result?.error || new Error("state writer returned failure");
      }
      return true;
    } catch (error) {
      state.persistenceFailure = true;
      state.persistenceDetail = String(error.message || error);
      state.history.push({
        phase: "state-persistence-failed",
        detail: state.persistenceDetail,
      });
      return false;
    }
  };
}

export function recoveryRequiredFromState(state) {
  return Boolean(
    state
    && typeof state === "object"
    && state.transitionAttempted === true,
  );
}

export async function recoverFromDurableState(durableState, options) {
  if (!recoveryRequiredFromState(durableState)) {
    return { status: "no-transition", release: null, state: durableState };
  }
  return recoverInterruptedRelease({
    ...options,
    initialState: durableState,
  });
}

function wait(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

export async function runReleaseTransition({
  getRelease,
  publishRelease,
  rollbackRelease,
  verifySnapshot,
  maxPolls = 10,
  maxRollbackAttempts = 5,
  pollDelayMs = 3000,
  sleep = wait,
  onState = () => {},
  initialState = null,
}) {
  const state = mergeDurableState({
    phase: "ready",
    transitionAttempted: false,
    observedMutable: false,
    integrityViolation: false,
    integrityDetail: null,
    persistenceFailure: false,
    persistenceDetail: null,
    history: [],
  }, initialState);
  const record = createStateRecorder(state, onState);
  const latchIntegrity = (phase, error) => {
    state.integrityViolation = true;
    state.integrityDetail ||= String(error.message || error);
    record(`${phase}-integrity-violation`, String(error.message || error));
  };
  const inspect = async (
    release,
    phase,
    allowPersistenceFailure = false,
  ) => {
    const proof = await verifySnapshot(release);
    if (proof !== true) {
      throw new Error("Release snapshot verifier did not return an explicit true proof.");
    }
    if (release.immutable === true && release.draft !== false) {
      throw new Error("Immutable release metadata is internally inconsistent.");
    }
    if (release.draft === false && release.immutable !== true) {
      state.observedMutable = true;
    }
    if (!record(
      phase,
      `draft=${release.draft}; immutable=${release.immutable}`,
    ) && !allowPersistenceFailure) {
      throw new StatePersistenceError(state.persistenceDetail);
    }
    return release;
  };
  const read = async (phase, allowPersistenceFailure = false) => {
    let release;
    try {
      release = await getRelease();
    } catch (error) {
      if (
        !record(`${phase}-transport-failed`, String(error.message || error))
        && !allowPersistenceFailure
      ) {
        throw new StatePersistenceError(state.persistenceDetail);
      }
      return null;
    }
    try {
      return await inspect(release, phase, allowPersistenceFailure);
    } catch (error) {
      if (!(error instanceof StatePersistenceError)) {
        latchIntegrity(phase, error);
      }
      throw error;
    }
  };
  const completed = (release, phase) => {
    if (state.integrityViolation || state.persistenceFailure) {
      throw new ReleaseTransitionError(
        state.integrityViolation
          ? "An integrity violation was observed before immutable publication."
          : "Release state persistence failed before immutable publication.",
        "INCIDENT",
        state,
      );
    }
    record(phase, "release is immutable");
    return { release, state };
  };
  const draftFailure = () => new ReleaseTransitionError(
    state.integrityViolation
      ? "Integrity violation was latched and release rollback was verified."
      : state.persistenceFailure
        ? "State persistence failed and release rollback was verified."
      : "Release rollback was verified in draft state.",
    state.integrityViolation
      ? "INTEGRITY_ROLLED_BACK"
      : state.persistenceFailure
        ? "PERSISTENCE_ROLLED_BACK"
        : "ROLLED_BACK",
    state,
  );
  const recover = async (reason) => {
    record("rollback-required", reason);
    for (let attempt = 1; attempt <= maxRollbackAttempts; attempt += 1) {
      let before = null;
      try {
        before = await read(`rollback-${attempt}-initial-read`, true);
      } catch {
        // Integrity is sticky; continue directly to the ID-bound rollback.
      }
      if (before?.immutable === true) {
        return completed(before, "immutable-during-recovery");
      }

      try {
        const response = await rollbackRelease();
        if (response) {
          try {
            const inspected = await inspect(
              response,
              `rollback-${attempt}-response`,
              true,
            );
            if (inspected.immutable === true) {
              return completed(inspected, "immutable-during-recovery");
            }
          } catch (error) {
            if (error instanceof ReleaseTransitionError) throw error;
            if (!(error instanceof StatePersistenceError)) {
              latchIntegrity(`rollback-${attempt}-response`, error);
            }
          }
        }
      } catch (error) {
        if (error instanceof ReleaseTransitionError) throw error;
        record(`rollback-${attempt}-transport-failed`, String(error.message || error));
      }

      let after = null;
      try {
        after = await read(`rollback-${attempt}-verification`, true);
      } catch {
        // Integrity remains latched and cannot be cleared by a later response.
      }
      if (after?.immutable === true) {
        return completed(after, "immutable-during-recovery");
      }
      if (after?.draft === true) {
        await sleep(pollDelayMs);
        let confirmed = null;
        try {
          confirmed = await read(
            `rollback-${attempt}-draft-confirmation`,
            true,
          );
        } catch {
          // Continue recovery; one draft observation is never terminal.
        }
        if (confirmed?.immutable === true) {
          return completed(confirmed, "immutable-during-recovery");
        }
        if (confirmed?.draft === true) throw draftFailure();
      }
      if (attempt < maxRollbackAttempts) await sleep(pollDelayMs);
    }
    record("incident-unproven-state");
    throw new ReleaseTransitionError(
      "Release state could not be proven immutable or draft after retries.",
      "INCIDENT",
      state,
    );
  };

  let prepublish;
  try {
    prepublish = await read("immediately-before-publication");
  } catch (error) {
    throw new ReleaseTransitionError(
      `${
        error instanceof StatePersistenceError
          ? "Release state persistence"
          : "Release integrity"
      } failed before publication: ${String(error.message || error)}`,
      error instanceof StatePersistenceError ? "PERSISTENCE" : "INTEGRITY",
      state,
    );
  }
  if (!prepublish) {
    throw new ReleaseTransitionError(
      "Release state could not be proven immediately before publication.",
      "INCIDENT",
      state,
    );
  }
  if (prepublish.draft !== true || prepublish.immutable === true) {
    throw new ReleaseTransitionError(
      "Release was not a mutable draft immediately before publication.",
      "NOT_PUBLISHED",
      state,
    );
  }

  state.transitionAttempted = true;
  if (!record("publishing")) {
    state.transitionAttempted = false;
    throw new ReleaseTransitionError(
      "Release transition marker could not be persisted before publication.",
      "PERSISTENCE",
      state,
    );
  }
  let publishResponse = null;
  try {
    publishResponse = await publishRelease();
  } catch (error) {
    record("publish-transport-failed", String(error.message || error));
  }
  if (publishResponse) {
    try {
      const inspected = await inspect(publishResponse, "publish-response");
      if (inspected.immutable === true) return completed(inspected, "immutable");
    } catch (error) {
      if (error instanceof StatePersistenceError) {
        return recover("State persistence failed after publication response.");
      }
      latchIntegrity("publish-response", error);
      return recover("Integrity violation in publication response.");
    }
  }

  for (let attempt = 1; attempt <= maxPolls; attempt += 1) {
    let release = null;
    try {
      release = await read(`poll-${attempt}`);
    } catch {
      return recover("Integrity violation during publication polling.");
    }
    if (release?.immutable === true) return completed(release, "immutable");
    if (release?.draft === true) {
      return recover(
        "Draft was observed after publication began; an ID-bound rollback "
        + "must quiesce any in-flight PATCH.",
      );
    }
    if (attempt < maxPolls) await sleep(pollDelayMs);
  }

  return recover("Release did not become immutable during publication polling.");
}

export async function recoverInterruptedRelease({
  getRelease,
  rollbackRelease,
  verifySnapshot,
  maxAttempts = 5,
  pollDelayMs = 3000,
  sleep = wait,
  onState = () => {},
  initialState = null,
}) {
  const state = mergeDurableState({
    phase: "recovery-started",
    transitionAttempted: true,
    observedMutable: false,
    integrityViolation: false,
    integrityDetail: null,
    persistenceFailure: false,
    persistenceDetail: null,
    history: [],
  }, initialState);
  state.transitionAttempted = true;
  const record = createStateRecorder(state, onState);
  const inspect = async (release, phase) => {
    const proof = await verifySnapshot(release);
    if (proof !== true) {
      throw new Error("Release snapshot verifier did not return an explicit true proof.");
    }
    if (release.draft === false && release.immutable !== true) {
      state.observedMutable = true;
    }
    record(phase, `draft=${release.draft}; immutable=${release.immutable}`);
    return release;
  };
  const observe = async (phase) => {
    let release;
    try {
      release = await getRelease();
    } catch (error) {
      record(`${phase}-transport-failed`, String(error.message || error));
      return null;
    }
    try {
      return await inspect(release, phase);
    } catch (error) {
      state.integrityViolation = true;
      state.integrityDetail ||= String(error.message || error);
      record(`${phase}-integrity-violation`, String(error.message || error));
      return null;
    }
  };
  const immutableResult = (release) => {
    if (state.integrityViolation || state.persistenceFailure) {
      throw new ReleaseTransitionError(
        state.integrityViolation
          ? "Integrity violation preceded immutable recovery."
          : "State persistence failed before immutable recovery.",
        "INCIDENT",
        state,
      );
    }
    record("recovery-verified-immutable");
    return { status: "immutable", release, state };
  };
  const draftResult = (release) => {
    if (state.integrityViolation) {
      throw new ReleaseTransitionError(
        "Integrity violation was latched and recovery verified draft state.",
        "INTEGRITY_ROLLED_BACK",
        state,
      );
    }
    if (state.persistenceFailure) {
      throw new ReleaseTransitionError(
        "State persistence failed and recovery verified draft state.",
        "PERSISTENCE_ROLLED_BACK",
        state,
      );
    }
    record("recovery-verified-draft");
    return { status: "draft", release, state };
  };

  record("recovery-started");
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const before = await observe(`recovery-${attempt}-initial-read`);
    if (before?.immutable === true && before.draft === false) {
      return immutableResult(before);
    }

    try {
      const response = await rollbackRelease();
      if (response) {
        const inspected = await inspect(
          response,
          `recovery-${attempt}-rollback-response`,
        ).catch((error) => {
          state.integrityViolation = true;
          state.integrityDetail ||= String(error.message || error);
          record(
            `recovery-${attempt}-rollback-integrity-violation`,
            String(error.message || error),
          );
          return null;
        });
        if (inspected?.immutable === true && inspected.draft === false) {
          return immutableResult(inspected);
        }
      }
    } catch (error) {
      record(
        `recovery-${attempt}-rollback-transport-failed`,
        String(error.message || error),
      );
    }

    const first = await observe(`recovery-${attempt}-verification-1`);
    if (first?.immutable === true && first.draft === false) {
      return immutableResult(first);
    }
    if (first?.draft === true) {
      await sleep(pollDelayMs);
      const second = await observe(`recovery-${attempt}-verification-2`);
      if (second?.immutable === true && second.draft === false) {
        return immutableResult(second);
      }
      if (second?.draft === true) return draftResult(second);
    }
    if (attempt < maxAttempts) await sleep(pollDelayMs);
  }
  record("recovery-incident-unproven-state");
  throw new ReleaseTransitionError(
    "Interrupted release state could not be proven draft or immutable.",
    "INCIDENT",
    state,
  );
}

function parseArguments(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--recover-only") {
      values.recoverOnly = true;
      continue;
    }
    const value = argv[index + 1];
    if (
      ![
        "--repository",
        "--release-id",
        "--tag",
        "--tag-object",
        "--commit",
        "--release-fingerprint",
        "--state-file",
        "--output",
      ].includes(argument)
    ) {
      throw new Error(`Unsupported argument: ${argument}`);
    }
    if (!value || value.startsWith("--")) {
      throw new Error(`Missing value for ${argument}.`);
    }
    values[argument.slice(2)] = value;
    index += 1;
  }
  return values;
}

async function ghJson(repository, releaseId, method = "GET", fields = []) {
  const args = [
    "api",
    "--method",
    method,
    "-H",
    "X-GitHub-Api-Version: 2026-03-10",
    `repos/${repository}/releases/${releaseId}`,
    ...fields,
  ];
  const { stdout } = await execFileAsync("gh", args, {
    encoding: "utf8",
    maxBuffer: 20 * 1024 * 1024,
  });
  return JSON.parse(stdout);
}

async function remoteRef(repository, ref) {
  const { stdout } = await execFileAsync(
    "git",
    ["ls-remote", "--exit-code", "origin", ref],
    { encoding: "utf8" },
  );
  const sha = stdout.trim().split(/\s+/)[0];
  if (!/^[0-9a-f]{40}$/i.test(sha || "")) {
    throw new Error(`Remote ref ${ref} did not resolve in ${repository}.`);
  }
  return sha.toLowerCase();
}

export async function publishReleaseWithStateMachine(argv = process.argv.slice(2)) {
  const args = parseArguments(argv);
  const expected = {
    tag: args.tag,
    tagObject: args["tag-object"],
    commit: args.commit,
    releaseId: args["release-id"],
    releaseFingerprint: args["release-fingerprint"],
  };
  const stateFile = path.resolve(args["state-file"]);
  const output = path.resolve(args.output);
  const writeState = createAtomicStateWriter(stateFile);
  let latestState = {
    phase: "not-started",
    transitionAttempted: false,
    integrityViolation: false,
    persistenceFailure: false,
    history: [],
  };
  const onState = (state) => {
    latestState = structuredClone(state);
    return writeState(state);
  };
  const verifySnapshot = async (release) => {
    verifyReleaseSnapshot(expected, {
      tag: release.tag_name,
      tagObject: await remoteRef(
        args.repository,
        `refs/tags/${args.tag}`,
      ),
      commit: await remoteRef(
        args.repository,
        `refs/tags/${args.tag}^{}`,
      ),
      releaseId: String(release.id),
      releaseFingerprint: releaseContentFingerprint(release),
    });
    return true;
  };
  const getRelease = () => ghJson(
    args.repository,
    args["release-id"],
  );
  const rollbackRelease = () => ghJson(
    args.repository,
    args["release-id"],
    "PATCH",
    ["-F", "draft=true"],
  );
  let signalRecoveryStarted = false;
  for (const signal of ["SIGINT", "SIGTERM"]) {
    process.once(signal, async () => {
      if (signalRecoveryStarted) return;
      signalRecoveryStarted = true;
      const interruptedState = mergeDurableState(latestState, {
        phase: "interrupted-recovery-started",
        signal,
        transitionAttempted: latestState.transitionAttempted === true,
        history: [{
          phase: "interrupted-recovery-started",
          detail: signal,
        }],
      });
      onState(interruptedState);
      if (!recoveryRequiredFromState(interruptedState)) {
        process.exit(130);
        return;
      }
      try {
        const recovery = await recoverInterruptedRelease({
          getRelease,
          rollbackRelease,
          verifySnapshot,
          maxAttempts: 2,
          pollDelayMs: 1000,
          onState,
          initialState: interruptedState,
        });
        writeFileSync(
          output,
          `${JSON.stringify(recovery.release, null, 2)}\n`,
          "utf8",
        );
      } catch (error) {
        onState(error.state || mergeDurableState(interruptedState, {
          phase: "interrupted-recovery-incident",
          signal,
          history: [{
            phase: "interrupted-recovery-incident",
            detail: String(error.message || error),
          }],
        }));
      }
      process.exit(130);
    });
  }
  try {
    const result = await runReleaseTransition({
      getRelease,
      publishRelease: () => ghJson(
        args.repository,
        args["release-id"],
        "PATCH",
        ["-F", "draft=false", "-F", "prerelease=true", "-f", "make_latest=false"],
      ),
      rollbackRelease,
      verifySnapshot,
      onState,
    });
    writeFileSync(output, `${JSON.stringify(result.release, null, 2)}\n`, "utf8");
    return result;
  } catch (error) {
    onState(error.state || mergeDurableState(latestState, {
      phase: "incident",
      history: [{
        phase: "incident",
        detail: String(error.message || error),
      }],
    }));
    throw error;
  }
}

export async function recoverReleaseFromStateFile(argv = process.argv.slice(2)) {
  const args = parseArguments(argv);
  const stateFile = path.resolve(args["state-file"]);
  const output = path.resolve(args.output);
  const durableState = JSON.parse(readFileSync(stateFile, "utf8"));
  const expected = {
    tag: args.tag,
    tagObject: args["tag-object"],
    commit: args.commit,
    releaseId: args["release-id"],
    releaseFingerprint: args["release-fingerprint"],
  };
  const writeState = createAtomicStateWriter(stateFile);
  let latestState = structuredClone(durableState);
  const onState = (state) => {
    latestState = structuredClone(state);
    return writeState(state);
  };
  const verifySnapshot = async (release) => {
    verifyReleaseSnapshot(expected, {
      tag: release.tag_name,
      tagObject: await remoteRef(args.repository, `refs/tags/${args.tag}`),
      commit: await remoteRef(args.repository, `refs/tags/${args.tag}^{}`),
      releaseId: String(release.id),
      releaseFingerprint: releaseContentFingerprint(release),
    });
    return true;
  };
  const getRelease = () => ghJson(args.repository, args["release-id"]);
  const rollbackRelease = () => ghJson(
    args.repository,
    args["release-id"],
    "PATCH",
    ["-F", "draft=true"],
  );
  let signalRecoveryStarted = false;
  for (const signal of ["SIGINT", "SIGTERM"]) {
    process.once(signal, async () => {
      if (signalRecoveryStarted) return;
      signalRecoveryStarted = true;
      const interruptedState = mergeDurableState(latestState, {
        phase: "recovery-only-interrupted",
        signal,
        history: [{
          phase: "recovery-only-interrupted",
          detail: signal,
        }],
      });
      onState(interruptedState);
      try {
        await recoverInterruptedRelease({
          getRelease,
          rollbackRelease,
          verifySnapshot,
          maxAttempts: 2,
          pollDelayMs: 1000,
          onState,
          initialState: interruptedState,
        });
      } catch (error) {
        onState(error.state || mergeDurableState(interruptedState, {
          phase: "recovery-only-signal-incident",
          history: [{
            phase: "recovery-only-signal-incident",
            detail: String(error.message || error),
          }],
        }));
      }
      process.exit(130);
    });
  }
  const recovery = await recoverFromDurableState(durableState, {
    getRelease,
    rollbackRelease,
    verifySnapshot,
    onState,
  });
  writeFileSync(
    output,
    `${JSON.stringify(recovery.release, null, 2)}\n`,
    "utf8",
  );
  return recovery;
}

if (
  process.argv[1]
  && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  const recoverOnly = process.argv.includes("--recover-only");
  const operation = recoverOnly
    ? recoverReleaseFromStateFile()
    : publishReleaseWithStateMachine();
  operation
    .then(({ release }) => {
      if (!recoverOnly && release) {
        process.stdout.write(
          `Published immutable release ${release.id} at ${release.tag_name}.\n`,
        );
      } else if (release) {
        process.stdout.write(
          `Release recovery proved ${release.immutable ? "immutable" : "draft"} `
          + `state for ${release.id}.\n`,
        );
      } else {
        process.stdout.write("No release transition required recovery.\n");
      }
    })
    .catch((error) => {
      process.stderr.write(
        `Release publication state machine failed [${error.code || "ERROR"}]: `
        + `${String(error.stack || error)}\n`,
      );
      process.exit(1);
    });
}
