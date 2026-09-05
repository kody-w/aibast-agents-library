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
const DEFAULT_OPERATION_TIMEOUT_MS = 15000;
const DEFAULT_RECONCILE_DEADLINE_MS = 60000;
const DEFAULT_SETTLEMENT_TIMEOUT_MS = 15000;

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

class OperationTimeoutError extends Error {
  constructor(message) {
    super(message);
    this.name = "OperationTimeoutError";
  }
}

export function mergeDurableState(state, patch) {
  const history = [];
  const seenHistory = new Set();
  for (const entry of [
    ...(Array.isArray(state?.history) ? state.history : []),
    ...(Array.isArray(patch?.history) ? patch.history : []),
  ]) {
    const key = JSON.stringify(entry);
    if (seenHistory.has(key)) continue;
    seenHistory.add(key);
    history.push(entry);
  }
  return {
    ...(state && typeof state === "object" ? state : {}),
    ...(patch && typeof patch === "object" ? patch : {}),
    history,
    transitionAttempted:
      state?.transitionAttempted === true
      || patch?.transitionAttempted === true,
    publishIntent:
      state?.publishIntent === true
      || patch?.publishIntent === true,
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
    publishSettlementUnproven:
      state?.publishSettlementUnproven === true
      || patch?.publishSettlementUnproven === true,
    intentIdentity:
      state?.intentIdentity
      || patch?.intentIdentity
      || null,
  };
}

function initialState(seed = null) {
  return mergeDurableState({
    phase: "ready",
    transitionAttempted: false,
    publishIntent: false,
    observedMutable: false,
    integrityViolation: false,
    integrityDetail: null,
    persistenceFailure: false,
    persistenceDetail: null,
    publishSettlementUnproven: false,
    publishSettled: false,
    history: [],
  }, seed);
}

export function recoveryRequiredFromState(state) {
  return Boolean(
    state
    && typeof state === "object"
    && state.transitionAttempted === true
    && state.publishIntent === true,
  );
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
  let failure = null;
  return (state) => {
    if (failure) return { ok: false, error: failure };
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

function createRecorder(state, onState) {
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

function wait(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

export async function withOperationTimeout(
  promise,
  timeoutMs,
  label = "operation",
) {
  let timer;
  try {
    return await Promise.race([
      Promise.resolve(promise),
      new Promise((_, reject) => {
        timer = setTimeout(() => {
          reject(
            new OperationTimeoutError(
              `${label} timed out after ${timeoutMs}ms.`,
            ),
          );
        }, timeoutMs);
      }),
    ]);
  } finally {
    if (timer) clearTimeout(timer);
  }
}

function remainingTimeout(deadline, operationTimeoutMs) {
  const remaining = deadline - Date.now();
  if (remaining <= 0) {
    throw new OperationTimeoutError(
      "Overall publication reconciliation deadline expired.",
    );
  }
  return Math.max(1, Math.min(operationTimeoutMs, remaining));
}

function isTransportInability(error) {
  const diagnostic = [
    error?.message,
    error?.stderr,
  ].filter(Boolean).join(" ").toLowerCase();
  return error instanceof OperationTimeoutError
    || error?.killed === true
    || typeof error?.signal === "string"
    || [
      "ECONNABORTED",
      "ECONNREFUSED",
      "ECONNRESET",
      "EHOSTUNREACH",
      "ENETDOWN",
      "ENETUNREACH",
      "ETIMEDOUT",
    ].includes(error?.code)
    || [
      "could not resolve host",
      "failed to connect",
      "connection reset",
      "connection timed out",
      "network is unreachable",
      "remote end hung up",
      "the requested url returned error: 5",
    ].some((fragment) => diagnostic.includes(fragment));
}

function normalizedIntentIdentity(identity) {
  if (identity === null || identity === undefined) return null;
  if (!identity || typeof identity !== "object") {
    throw new Error("Publication intent identity must be an object.");
  }
  const normalized = {};
  for (const field of [
    "repository",
    "releaseId",
    "tag",
    "tagObject",
    "commit",
    "releaseFingerprint",
  ]) {
    const value = String(identity[field] || "").trim();
    if (!value) {
      throw new Error(`Publication intent identity is missing ${field}.`);
    }
    normalized[field] = value;
  }
  return normalized;
}

function normalizePublishHandle(handle) {
  if (
    !handle
    || typeof handle !== "object"
    || !Object.hasOwn(handle, "response")
  ) {
    throw new Error(
      "startPublishRelease must return a cancellable publication handle.",
    );
  }
  const response = Promise.resolve(handle.response);
  return {
    response,
    settled: handle.settled
      ? Promise.resolve(handle.settled)
      : response.then(() => undefined, () => undefined),
    cancel: typeof handle.cancel === "function"
      ? handle.cancel
      : async () => {},
  };
}

export async function quiescePublishOperation(handle, timeoutMs) {
  const operation = normalizePublishHandle(handle);
  operation.response.catch(() => {});
  const deadline = Date.now() + timeoutMs;
  try {
    await withOperationTimeout(
      operation.cancel(),
      remainingTimeout(deadline, timeoutMs),
      "publication cancellation",
    );
  } catch {
    // The separate settlement promise remains authoritative.
  }
  await withOperationTimeout(
    operation.settled,
    remainingTimeout(deadline, timeoutMs),
    "publication operation settlement",
  );
}

function integrityIncident(state, record, phase, error) {
  state.integrityViolation = true;
  state.integrityDetail ||= String(error.message || error);
  record(`${phase}-integrity-incident`, String(error.message || error));
  throw new ReleaseTransitionError(
    `Release integrity failed during ${phase}.`,
    "INTEGRITY_INCIDENT",
    state,
  );
}

function settlementIncident(state, record, phase, error) {
  state.publishSettlementUnproven = true;
  const detail = String(error.message || error);
  const persisted = record(`${phase}-settlement-unproven`, detail);
  throw new ReleaseTransitionError(
    persisted
      ? `Release settlement is unproven during ${phase}.`
      : `Release settlement and incident persistence failed during ${phase}.`,
    persisted ? "SETTLEMENT_UNPROVEN" : "PERSISTENCE_INCIDENT",
    state,
  );
}

function persistenceIncident(state, message) {
  throw new ReleaseTransitionError(
    message,
    "PERSISTENCE_INCIDENT",
    state,
  );
}

function assertLocalOperationActive(shouldAbort, state) {
  if (shouldAbort()) {
    throw new ReleaseTransitionError(
      "Local publication operation was interrupted for signal reconciliation.",
      "LOCAL_OPERATION_INTERRUPTED",
      state,
    );
  }
}

async function verifyExactRelease({
  release,
  phase,
  state,
  record,
  verifySnapshot,
  timeoutMs,
}) {
  let proof;
  try {
    proof = await withOperationTimeout(
      verifySnapshot(release),
      timeoutMs,
      "release snapshot verification",
    );
  } catch (error) {
    if (isTransportInability(error)) throw error;
    return integrityIncident(state, record, phase, error);
  }
  if (proof !== true) {
    return integrityIncident(
      state,
      record,
      phase,
      new Error("Release snapshot verifier did not return explicit true proof."),
    );
  }
  const validState = (
    (release.immutable === true && release.draft === false)
    || (release.immutable !== true && release.draft === true)
    || (release.immutable !== true && release.draft === false)
  );
  if (!validState) {
    return integrityIncident(
      state,
      record,
      phase,
      new Error("Release draft/immutable state is internally inconsistent."),
    );
  }
  if (release.draft === false && release.immutable !== true) {
    state.observedMutable = true;
  }
  if (!record(
    phase,
    `draft=${release.draft}; immutable=${release.immutable}`,
  )) {
    throw new StatePersistenceError(state.persistenceDetail);
  }
  return release;
}

async function persistImmutableTerminal(state, record, release) {
  if (state.integrityViolation || state.persistenceFailure) {
    return persistenceIncident(
      state,
      state.integrityViolation
        ? "Integrity incident forbids immutable terminal success."
        : "Persistence incident forbids immutable terminal success.",
    );
  }
  if (!record("terminal-immutable", "exact immutable release verified")) {
    return persistenceIncident(
      state,
      "Immutable release was verified but terminal state did not persist.",
    );
  }
  return { release, state, status: "immutable" };
}

export async function reconcileReleasePublication({
  getRelease,
  startPublishRelease,
  verifySnapshot,
  initialState: seed,
  onState = () => {},
  onPublishHandle = () => {},
  maxCycles = 20,
  operationTimeoutMs = DEFAULT_OPERATION_TIMEOUT_MS,
  overallDeadlineMs = DEFAULT_RECONCILE_DEADLINE_MS,
  settlementTimeoutMs = DEFAULT_SETTLEMENT_TIMEOUT_MS,
  pollDelayMs = 3000,
  deferredQuiescenceMs = 15000,
  sleep = wait,
  intentIdentity = null,
  shouldAbort = () => false,
}) {
  const state = initialState(seed);
  const record = createRecorder(state, onState);
  const expectedIntentIdentity = normalizedIntentIdentity(intentIdentity);
  if (
    expectedIntentIdentity
    && JSON.stringify(state.intentIdentity) !== JSON.stringify(
      expectedIntentIdentity,
    )
  ) {
    return integrityIncident(
      state,
      record,
      "durable-publish-intent",
      new Error("Durable publication intent identity does not match recovery."),
    );
  }
  const deadline = Date.now() + overallDeadlineMs;
  const timeout = () => {
    try {
      return remainingTimeout(deadline, operationTimeoutMs);
    } catch (error) {
      return settlementIncident(
        state,
        record,
        "overall-deadline",
        error,
      );
    }
  };
  const boundedSleep = async (milliseconds, label) => {
    try {
      const available = timeout();
      const duration = Math.max(0, Math.min(milliseconds, available));
      await withOperationTimeout(
        sleep(duration),
        available,
        label,
      );
      if (duration < milliseconds) {
        throw new OperationTimeoutError(
          `${label} exceeded the overall reconciliation deadline.`,
        );
      }
    } catch (error) {
      return settlementIncident(state, record, label, error);
    }
  };
  const readRelease = async (phase) => {
    let release;
    try {
      release = await withOperationTimeout(
        getRelease(),
        timeout(),
        "GitHub release GET",
      );
    } catch (error) {
      return settlementIncident(state, record, phase, error);
    }
    try {
      return await verifyExactRelease({
        release,
        phase,
        state,
        record,
        verifySnapshot,
        timeoutMs: timeout(),
      });
    } catch (error) {
      if (error instanceof StatePersistenceError) {
        return persistenceIncident(
          state,
          `Release read succeeded during ${phase}, but state persistence failed.`,
        );
      }
      if (isTransportInability(error)) {
        return settlementIncident(state, record, `${phase}-verification`, error);
      }
      throw error;
    }
  };
  const requestPublish = async (phase) => {
    let handle;
    try {
      handle = normalizePublishHandle(startPublishRelease());
      onPublishHandle(handle);
    } catch (error) {
      return settlementIncident(state, record, phase, error);
    }

    let response;
    try {
      response = await withOperationTimeout(
        handle.response,
        timeout(),
        "GitHub publication PATCH",
      );
    } catch (error) {
      try {
        await quiescePublishOperation(
          handle,
          Math.min(settlementTimeoutMs, timeout()),
        );
      } catch (settlementError) {
        return settlementIncident(
          state,
          record,
          `${phase}-operation`,
          settlementError,
        );
      }
      return settlementIncident(state, record, phase, error);
    }
    try {
      await withOperationTimeout(
        handle.settled,
        Math.min(settlementTimeoutMs, timeout()),
        "publication operation settlement",
      );
    } catch (error) {
      return settlementIncident(
        state,
        record,
        `${phase}-operation`,
        error,
      );
    }
    state.publishSettled = true;
    state.publishSettlementUnproven = false;
    if (!record(`${phase}-operation-settled`)) {
      return persistenceIncident(
        state,
        "Publication settled but settlement state did not persist.",
      );
    }
    try {
      return await verifyExactRelease({
        release: response,
        phase: `${phase}-response`,
        state,
        record,
        verifySnapshot,
        timeoutMs: timeout(),
      });
    } catch (error) {
      if (error instanceof StatePersistenceError) {
        return persistenceIncident(
          state,
          "Publication response was exact, but state persistence failed.",
        );
      }
      if (isTransportInability(error)) {
        return settlementIncident(
          state,
          record,
          `${phase}-response-verification`,
          error,
        );
      }
      throw error;
    }
  };

  if (!recoveryRequiredFromState(state)) {
    throw new ReleaseTransitionError(
      "Durable publication intent is missing.",
      "NO_PUBLISH_INTENT",
      state,
    );
  }
  if (state.integrityViolation) {
    throw new ReleaseTransitionError(
      "Durable integrity incident forbids publication success.",
      "INTEGRITY_INCIDENT",
      state,
    );
  }
  if (state.persistenceFailure) {
    throw new ReleaseTransitionError(
      "Durable persistence incident forbids publication success.",
      "PERSISTENCE_INCIDENT",
      state,
    );
  }
  if (state.publishSettlementUnproven) {
    if (deferredQuiescenceMs > 0) {
      await boundedSleep(
        deferredQuiescenceMs,
        "deferred publication quiescence",
      );
    }
    state.publishSettlementUnproven = false;
    if (!record(
      "deferred-publication-quiescence-complete",
      `${deferredQuiescenceMs}ms`,
    )) {
      return persistenceIncident(
        state,
        "Deferred quiescence state did not persist.",
      );
    }
  }

  for (let cycle = 1; cycle <= maxCycles; cycle += 1) {
    assertLocalOperationActive(shouldAbort, state);
    let release = await readRelease(`reconcile-${cycle}-read`);
    assertLocalOperationActive(shouldAbort, state);
    if (release.immutable === true) {
      return persistImmutableTerminal(state, record, release);
    }

    if (release.draft === true || cycle % 3 === 0) {
      assertLocalOperationActive(shouldAbort, state);
      await requestPublish(`reconcile-${cycle}-publish`);
      assertLocalOperationActive(shouldAbort, state);
      release = await readRelease(`reconcile-${cycle}-postpublish-read`);
      assertLocalOperationActive(shouldAbort, state);
      if (release.immutable === true) {
        return persistImmutableTerminal(state, record, release);
      }
    }

    if (cycle < maxCycles) {
      assertLocalOperationActive(shouldAbort, state);
      await boundedSleep(pollDelayMs, `reconcile-${cycle}-poll-delay`);
    }
  }
  return settlementIncident(
    state,
    record,
    "reconcile-cycle-limit",
    new Error("Exact release did not become immutable within bounded cycles."),
  );
}

export async function runReleaseTransition({
  getRelease,
  startPublishRelease,
  verifySnapshot,
  onState = () => {},
  onPublishHandle = () => {},
  operationTimeoutMs = DEFAULT_OPERATION_TIMEOUT_MS,
  overallDeadlineMs = DEFAULT_RECONCILE_DEADLINE_MS,
  settlementTimeoutMs = DEFAULT_SETTLEMENT_TIMEOUT_MS,
  pollDelayMs = 3000,
  maxCycles = 20,
  sleep = wait,
  intentIdentity = null,
  shouldAbort = () => false,
}) {
  const state = initialState({
    intentIdentity: normalizedIntentIdentity(intentIdentity),
  });
  const record = createRecorder(state, onState);
  let release;
  try {
    release = await withOperationTimeout(
      getRelease(),
      operationTimeoutMs,
      "prepublication GitHub release GET",
    );
  } catch (error) {
    return settlementIncident(
      state,
      record,
      "prepublication-read",
      error,
    );
  }
  try {
    release = await verifyExactRelease({
      release,
      phase: "prepublication-exact-release",
      state,
      record,
      verifySnapshot,
      timeoutMs: operationTimeoutMs,
    });
  } catch (error) {
    if (error instanceof StatePersistenceError) {
      return persistenceIncident(
        state,
        "Prepublication state persistence failed before publish intent.",
      );
    }
    throw error;
  }
  assertLocalOperationActive(shouldAbort, state);
  if (release.immutable === true) {
    return persistImmutableTerminal(state, record, release);
  }
  if (release.draft !== true) {
    return integrityIncident(
      state,
      record,
      "prepublication-state",
      new Error(
        "Release became public-mutable before durable local publish intent.",
      ),
    );
  }

  state.transitionAttempted = true;
  state.publishIntent = true;
  if (!record(
    "publish-intent-recorded",
    "monotonic exact immutable publication requested",
  )) {
    state.transitionAttempted = false;
    state.publishIntent = false;
    return persistenceIncident(
      state,
      "Durable publish intent could not be recorded before dispatch.",
    );
  }
  return reconcileReleasePublication({
    getRelease,
    startPublishRelease,
    verifySnapshot,
    initialState: state,
    onState,
    onPublishHandle,
    operationTimeoutMs,
    overallDeadlineMs,
    settlementTimeoutMs,
    pollDelayMs,
    maxCycles,
    sleep,
    intentIdentity,
    shouldAbort,
  });
}

export async function recoverFromDurableState(durableState, options) {
  if (!recoveryRequiredFromState(durableState)) {
    return { status: "no-intent", release: null, state: durableState };
  }
  return reconcileReleasePublication({
    ...options,
    initialState: durableState,
  });
}

export async function recoverInterruptedRelease(options) {
  return recoverFromDurableState(options.initialState, options);
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

async function ghJson(repository, releaseId) {
  const { stdout } = await execFileAsync("gh", [
    "api",
    "--method",
    "GET",
    "-H",
    "X-GitHub-Api-Version: 2026-03-10",
    `repos/${repository}/releases/${releaseId}`,
  ], {
    encoding: "utf8",
    maxBuffer: 20 * 1024 * 1024,
    timeout: DEFAULT_OPERATION_TIMEOUT_MS,
    killSignal: "SIGTERM",
  });
  return JSON.parse(stdout);
}

function startGhPublishOperation(repository, releaseId) {
  const args = [
    "api",
    "--method",
    "PATCH",
    "-H",
    "X-GitHub-Api-Version: 2026-03-10",
    `repos/${repository}/releases/${releaseId}`,
    "-F",
    "draft=false",
    "-F",
    "prerelease=true",
    "-f",
    "make_latest=false",
  ];
  let child;
  let settle;
  const settled = new Promise((resolve) => { settle = resolve; });
  const response = new Promise((resolve, reject) => {
    child = execFile("gh", args, {
      encoding: "utf8",
      maxBuffer: 20 * 1024 * 1024,
      timeout: DEFAULT_OPERATION_TIMEOUT_MS,
      killSignal: "SIGTERM",
    }, (error, stdout) => {
      settle();
      if (error) {
        reject(error);
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (parseError) {
        reject(parseError);
      }
    });
  });
  return {
    response,
    settled,
    cancel: async () => {
      if (child && child.exitCode === null && child.signalCode === null) {
        child.kill("SIGTERM");
      }
    },
  };
}

async function remoteRef(repository, ref) {
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository)) {
    throw new Error("GitHub repository identity is invalid.");
  }
  const { stdout } = await execFileAsync(
    "git",
    [
      "ls-remote",
      "--exit-code",
      `https://github.com/${repository}.git`,
      ref,
    ],
    {
      encoding: "utf8",
      timeout: DEFAULT_OPERATION_TIMEOUT_MS,
      killSignal: "SIGTERM",
    },
  );
  const sha = stdout.trim().split(/\s+/)[0];
  if (!/^[0-9a-f]{40}$/i.test(sha || "")) {
    throw new Error(`Remote ref ${ref} did not resolve in ${repository}.`);
  }
  return sha.toLowerCase();
}

function expectedSnapshot(args) {
  return {
    tag: args.tag,
    tagObject: args["tag-object"],
    commit: args.commit,
    releaseId: args["release-id"],
    releaseFingerprint: args["release-fingerprint"],
  };
}

function intentIdentityFromArgs(args) {
  return normalizedIntentIdentity({
    repository: args.repository,
    releaseId: args["release-id"],
    tag: args.tag,
    tagObject: args["tag-object"],
    commit: args.commit,
    releaseFingerprint: args["release-fingerprint"],
  });
}

function createSnapshotVerifier(args) {
  const expected = expectedSnapshot(args);
  return async (release) => {
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
}

function createCliState(stateFile) {
  const writeState = createAtomicStateWriter(stateFile);
  let latest = initialState();
  return {
    get latest() {
      return latest;
    },
    persist(state) {
      latest = structuredClone(state);
      return writeState(state);
    },
    merge(patch) {
      latest = mergeDurableState(latest, patch);
      return writeState(latest);
    },
  };
}

function writeOutput(output, release) {
  writeFileSync(output, `${JSON.stringify(release, null, 2)}\n`, "utf8");
}

export async function reconcileInterruptedSignal({
  signal,
  cliState,
  getRelease,
  startPublishRelease,
  verifySnapshot,
  intentIdentity = null,
  getActiveHandle = () => null,
  waitForMain = async () => {},
  overallDeadlineMs = DEFAULT_RECONCILE_DEADLINE_MS,
}) {
  const deadline = Date.now() + overallDeadlineMs;
  cliState.merge({
    phase: "signal-reconciliation-started",
    signal,
    history: [{
      phase: "signal-reconciliation-started",
      detail: signal,
    }],
  });
  const handle = getActiveHandle();
  if (handle) {
    try {
      await quiescePublishOperation(
        handle,
        Math.max(1, Math.min(
          DEFAULT_SETTLEMENT_TIMEOUT_MS,
          deadline - Date.now(),
        )),
      );
      cliState.merge({
        phase: "signal-local-operation-settled",
        publishSettled: true,
        publishSettlementUnproven: false,
        history: [{
          phase: "signal-local-operation-settled",
          detail: signal,
        }],
      });
    } catch (error) {
      cliState.merge({
        phase: "signal-settlement-unproven",
        publishSettlementUnproven: true,
        history: [{
          phase: "signal-settlement-unproven",
          detail: String(error.message || error),
        }],
      });
      return null;
    }
  }
  try {
    await withOperationTimeout(
      waitForMain(),
      Math.max(1, deadline - Date.now()),
      "interrupted publication operation",
    );
  } catch (error) {
    cliState.merge({
      phase: "signal-main-operation-unproven",
      publishSettlementUnproven: true,
      history: [{
        phase: "signal-main-operation-unproven",
        detail: String(error.message || error),
      }],
    });
    return null;
  }
  if (!recoveryRequiredFromState(cliState.latest)) return null;
  try {
    return await reconcileReleasePublication({
      getRelease,
      startPublishRelease,
      verifySnapshot,
      initialState: cliState.latest,
      onState: (state) => cliState.persist(state),
      overallDeadlineMs: Math.max(1, deadline - Date.now()),
      onPublishHandle: () => {},
      intentIdentity,
    });
  } catch (error) {
    cliState.persist(error.state || mergeDurableState(cliState.latest, {
      phase: "signal-reconciliation-incident",
      history: [{
        phase: "signal-reconciliation-incident",
        detail: String(error.message || error),
      }],
    }));
    return null;
  }
}

function installSignalReconciler({
  cliState,
  getRelease,
  startPublishRelease,
  verifySnapshot,
  intentIdentity,
  getActiveHandle,
  waitForMain,
}) {
  let handling = false;
  let signalPromise = null;
  for (const signal of ["SIGINT", "SIGTERM"]) {
    process.once(signal, () => {
      if (handling) return;
      handling = true;
      process.exitCode = 130;
      signalPromise = reconcileInterruptedSignal({
        signal,
        cliState,
        getRelease,
        startPublishRelease,
        verifySnapshot,
        intentIdentity,
        getActiveHandle,
        waitForMain,
      });
    });
  }
  return {
    get handling() {
      return handling;
    },
    async wait() {
      return signalPromise ? signalPromise : null;
    },
  };
}

export async function publishReleaseWithStateMachine(
  argv = process.argv.slice(2),
) {
  const args = parseArguments(argv);
  const stateFile = path.resolve(args["state-file"]);
  const output = path.resolve(args.output);
  const cliState = createCliState(stateFile);
  const getRelease = () => ghJson(args.repository, args["release-id"]);
  const startPublishRelease = () => startGhPublishOperation(
    args.repository,
    args["release-id"],
  );
  const verifySnapshot = createSnapshotVerifier(args);
  const intentIdentity = intentIdentityFromArgs(args);
  let activeHandle = null;
  let finishMain;
  const mainFinished = new Promise((resolve) => {
    finishMain = resolve;
  });
  const signalController = installSignalReconciler({
    cliState,
    getRelease,
    startPublishRelease,
    verifySnapshot,
    intentIdentity,
    getActiveHandle: () => activeHandle,
    waitForMain: () => mainFinished,
  });
  let result = null;
  let operationError = null;
  try {
    result = await runReleaseTransition({
      getRelease,
      startPublishRelease,
      verifySnapshot,
      onState: (state) => signalController.handling
        ? cliState.merge(state)
        : cliState.persist(state),
      onPublishHandle: (handle) => {
        activeHandle = handle;
      },
      intentIdentity,
      shouldAbort: () => signalController.handling,
    });
  } catch (error) {
    operationError = error;
    const incidentState = error.state || mergeDurableState(cliState.latest, {
      phase: "publication-incident",
      history: [{
        phase: "publication-incident",
        detail: String(error.message || error),
      }],
    });
    if (signalController.handling) cliState.merge(incidentState);
    else cliState.persist(incidentState);
  } finally {
    finishMain();
  }
  if (signalController.handling) {
    const signalResult = await signalController.wait();
    if (signalResult?.release) {
      writeOutput(output, signalResult.release);
      return signalResult;
    }
    throw new ReleaseTransitionError(
      "Signal reconciliation did not prove the exact immutable release.",
      "SIGNAL_RECONCILIATION_INCIDENT",
      cliState.latest,
    );
  }
  if (operationError) throw operationError;
  writeOutput(output, result.release);
  return result;
}

export async function recoverReleaseFromStateFile(
  argv = process.argv.slice(2),
) {
  const args = parseArguments(argv);
  const stateFile = path.resolve(args["state-file"]);
  const output = path.resolve(args.output);
  const durableState = JSON.parse(readFileSync(stateFile, "utf8"));
  if (!recoveryRequiredFromState(durableState)) {
    return { status: "no-intent", release: null, state: durableState };
  }
  const cliState = createCliState(stateFile);
  cliState.persist(durableState);
  const getRelease = () => ghJson(args.repository, args["release-id"]);
  const startPublishRelease = () => startGhPublishOperation(
    args.repository,
    args["release-id"],
  );
  const verifySnapshot = createSnapshotVerifier(args);
  const intentIdentity = intentIdentityFromArgs(args);
  let activeHandle = null;
  let finishMain;
  const mainFinished = new Promise((resolve) => {
    finishMain = resolve;
  });
  const signalController = installSignalReconciler({
    cliState,
    getRelease,
    startPublishRelease,
    verifySnapshot,
    intentIdentity,
    getActiveHandle: () => activeHandle,
    waitForMain: () => mainFinished,
  });
  let result = null;
  let operationError = null;
  try {
    result = await recoverFromDurableState(durableState, {
      getRelease,
      startPublishRelease,
      verifySnapshot,
      onState: (state) => signalController.handling
        ? cliState.merge(state)
        : cliState.persist(state),
      onPublishHandle: (handle) => {
        activeHandle = handle;
      },
      intentIdentity,
      shouldAbort: () => signalController.handling,
    });
  } catch (error) {
    operationError = error;
    const incidentState = error.state || mergeDurableState(cliState.latest, {
      phase: "recovery-incident",
      history: [{
        phase: "recovery-incident",
        detail: String(error.message || error),
      }],
    });
    if (signalController.handling) cliState.merge(incidentState);
    else cliState.persist(incidentState);
  } finally {
    finishMain();
  }
  if (signalController.handling) {
    const signalResult = await signalController.wait();
    if (signalResult?.release) {
      writeOutput(output, signalResult.release);
      return signalResult;
    }
    throw new ReleaseTransitionError(
      "Signal recovery did not prove the exact immutable release.",
      "SIGNAL_RECONCILIATION_INCIDENT",
      cliState.latest,
    );
  }
  if (operationError) throw operationError;
  writeOutput(output, result.release);
  return result;
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
      if (release) {
        process.stdout.write(
          `Exact immutable release ${release.id} reconciled at `
          + `${release.tag_name}.\n`,
        );
      } else {
        process.stdout.write("No durable publication intent required reconciliation.\n");
      }
    })
    .catch((error) => {
      process.stderr.write(
        `Release reconciliation failed [${error.code || "ERROR"}]: `
        + `${String(error.stack || error)}\n`,
      );
      if (!process.exitCode) process.exitCode = 1;
    });
}
