import { execFile } from "node:child_process";
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

const DEFAULT_RECONCILE_DEADLINE_MS = 60000;
const MAX_ABORT_SETTLEMENT_RESERVE_MS = 2000;

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
    readFileSync,
    renameSync,
    rmSync,
    ...operations,
  };
  const parentDirectory = path.dirname(filePath);
  let sequence = 0;
  let failure = null;
  const syncParentDirectory = () => {
    const descriptor = fs.openSync(parentDirectory, "r");
    let syncError = null;
    try {
      fs.fsyncSync(descriptor);
    } catch (error) {
      syncError = error;
    }
    try {
      fs.closeSync(descriptor);
    } catch (error) {
      syncError ||= error;
    }
    if (syncError) throw syncError;
  };
  return (state) => {
    if (failure) return { ok: false, error: failure };
    const temporaryPath =
      `${filePath}.${process.pid}.${sequence += 1}.state.tmp`;
    let descriptor = null;
    let renamed = false;
    let previousMarker = null;
    let previousMarkerExists = false;
    try {
      try {
        previousMarker = fs.readFileSync(filePath);
        previousMarkerExists = true;
      } catch (error) {
        if (error?.code !== "ENOENT") throw error;
      }
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
      renamed = true;
      syncParentDirectory();
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
      if (renamed) {
        if (!previousMarkerExists) {
          try {
            fs.rmSync(filePath, { force: true });
          } catch {}
        } else {
          const restorePath =
            `${filePath}.${process.pid}.${sequence}.restore.tmp`;
          let restoreDescriptor = null;
          try {
            restoreDescriptor = fs.openSync(restorePath, "wx", 0o600);
            fs.writeFileSync(restoreDescriptor, previousMarker);
            fs.fsyncSync(restoreDescriptor);
            fs.closeSync(restoreDescriptor);
            restoreDescriptor = null;
            fs.renameSync(restorePath, filePath);
            try {
              syncParentDirectory();
            } catch {}
          } catch {
            if (restoreDescriptor !== null) {
              try {
                fs.closeSync(restoreDescriptor);
              } catch {}
            }
          } finally {
            try {
              fs.rmSync(restorePath, { force: true });
            } catch {}
          }
        }
      }
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

function abortReason(signal, label) {
  if (signal.reason instanceof Error) return signal.reason;
  return new OperationTimeoutError(`${label} was aborted.`);
}

function wait(milliseconds, { signal } = {}) {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(abortReason(signal, "publication delay"));
      return;
    }
    let timer;
    const onAbort = () => {
      clearTimeout(timer);
      reject(abortReason(signal, "publication delay"));
    };
    timer = setTimeout(() => {
      signal?.removeEventListener("abort", onAbort);
      resolve();
    }, milliseconds);
    signal?.addEventListener("abort", onAbort, { once: true });
  });
}

export function createDeadlineScope({
  overallDeadlineMs = DEFAULT_RECONCILE_DEADLINE_MS,
  signal: parentSignal = null,
} = {}) {
  if (!Number.isFinite(overallDeadlineMs) || overallDeadlineMs <= 0) {
    throw new Error("overallDeadlineMs must be a positive number.");
  }
  const startedAt = Date.now();
  const hardDeadline = startedAt + overallDeadlineMs;
  const cleanupReserveMs = Math.min(
    MAX_ABORT_SETTLEMENT_RESERVE_MS,
    Math.max(1, Math.floor(overallDeadlineMs / 10)),
  );
  const operationDeadline = hardDeadline - cleanupReserveMs;
  const controller = new AbortController();
  const abortForDeadline = () => {
    controller.abort(
      new OperationTimeoutError(
        "Overall publication reconciliation deadline expired.",
      ),
    );
  };
  const abortForParent = () => {
    controller.abort(
      parentSignal.reason instanceof Error
        ? parentSignal.reason
        : new OperationTimeoutError("Publication operation was cancelled."),
    );
  };
  if (parentSignal?.aborted) abortForParent();
  else {
    parentSignal?.addEventListener("abort", abortForParent, { once: true });
  }
  const deadlineTimer = setTimeout(
    abortForDeadline,
    Math.max(0, operationDeadline - Date.now()),
  );
  return {
    signal: controller.signal,
    deadline: operationDeadline,
    hardDeadline,
    cleanupReserveMs,
    abort(reason) {
      controller.abort(
        reason instanceof Error
          ? reason
          : new OperationTimeoutError(String(reason || "Operation aborted.")),
      );
    },
    dispose() {
      clearTimeout(deadlineTimer);
      parentSignal?.removeEventListener("abort", abortForParent);
    },
  };
}

function operationContext(scope) {
  return {
    signal: scope.signal,
    deadline: scope.deadline,
    hardDeadline: scope.hardDeadline,
  };
}

function ensureScopeActive(scope, label) {
  if (scope.signal.aborted) throw abortReason(scope.signal, label);
  if (Date.now() >= scope.deadline) {
    scope.abort(
      new OperationTimeoutError(
        "Overall publication reconciliation deadline expired.",
      ),
    );
    throw abortReason(scope.signal, label);
  }
}

function waitForResultOrAbort(promise, scope, label) {
  return new Promise((resolve, reject) => {
    if (scope.signal.aborted) {
      reject(abortReason(scope.signal, label));
      return;
    }
    let completed = false;
    const onAbort = () => {
      if (completed) return;
      completed = true;
      reject(abortReason(scope.signal, label));
    };
    scope.signal.addEventListener("abort", onAbort, { once: true });
    Promise.resolve(promise).then(
      (value) => {
        if (completed) return;
        completed = true;
        scope.signal.removeEventListener("abort", onAbort);
        resolve(value);
      },
      (error) => {
        if (completed) return;
        completed = true;
        scope.signal.removeEventListener("abort", onAbort);
        reject(error);
      },
    );
  });
}

function settleBeforeCleanupDeadline(promise, scope, label) {
  const cleanupDeadline = scope.hardDeadline;
  return new Promise((resolve, reject) => {
    let completed = false;
    const timer = setTimeout(() => {
      if (completed) return;
      completed = true;
      reject(
        new OperationTimeoutError(
          `${label} did not settle before the overall deadline.`,
        ),
      );
    }, Math.max(1, cleanupDeadline - Date.now()));
    Promise.resolve(promise).then(
      (value) => {
        if (completed) return;
        completed = true;
        clearTimeout(timer);
        resolve(value);
      },
      (error) => {
        if (completed) return;
        completed = true;
        clearTimeout(timer);
        reject(error);
      },
    );
  });
}

async function awaitAbortableOperation({
  result,
  settled = null,
  cancel = async () => {},
}, scope, label) {
  ensureScopeActive(scope, label);
  const resultPromise = Promise.resolve(result);
  const settledPromise = settled
    ? Promise.resolve(settled)
    : resultPromise.then(() => undefined, () => undefined);
  try {
    return await waitForResultOrAbort(resultPromise, scope, label);
  } catch (error) {
    if (!scope.signal.aborted) throw error;
    try {
      await settleBeforeCleanupDeadline(cancel(), scope, `${label} cancellation`);
    } catch {}
    await settleBeforeCleanupDeadline(
      settledPromise,
      scope,
      `${label} operation`,
    );
    throw abortReason(scope.signal, label);
  }
}

function normalizeAbortableResult(value) {
  return value
    && typeof value === "object"
    && Object.hasOwn(value, "result")
    ? value
    : { result: value };
}

function isTransportInability(error) {
  const diagnostic = [
    error?.message,
    error?.stderr,
  ].filter(Boolean).join(" ").toLowerCase();
  return error instanceof OperationTimeoutError
    || error?.code === "ABORT_ERR"
    || error?.code === "LOCAL_OPERATION_INTERRUPTED"
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

export async function quiescePublishOperation(handle, scopeOrTimeoutMs) {
  const operation = normalizePublishHandle(handle);
  operation.response.catch(() => {});
  const ownsScope = typeof scopeOrTimeoutMs === "number";
  const scope = ownsScope
    ? createDeadlineScope({ overallDeadlineMs: scopeOrTimeoutMs })
    : scopeOrTimeoutMs;
  if (!scope?.signal || !Number.isFinite(scope.hardDeadline)) {
    throw new Error("Publication quiescence requires a deadline scope.");
  }
  try {
    try {
      await settleBeforeCleanupDeadline(
        operation.cancel(),
        scope,
        "publication cancellation",
      );
    } catch {
      // The separate settlement promise remains authoritative.
    }
    await settleBeforeCleanupDeadline(
      operation.settled,
      scope,
      "publication operation",
    );
  } finally {
    if (ownsScope) scope.dispose();
  }
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

function deferredIntegrityIncident(state, phase, error) {
  state.integrityViolation = true;
  state.integrityDetail ||= String(error.message || error);
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

function assertLocalOperationActive(shouldAbort, state, scope = null) {
  if (shouldAbort()) {
    const error = new ReleaseTransitionError(
      "Local publication operation was interrupted for signal reconciliation.",
      "LOCAL_OPERATION_INTERRUPTED",
      state,
    );
    scope?.abort(error);
    throw error;
  }
}

async function verifyExactRelease({
  release,
  phase,
  state,
  record,
  verifySnapshot,
  scope,
  recordResult = true,
  deferIntegrityRecord = false,
}) {
  let proof;
  try {
    proof = await awaitAbortableOperation(
      normalizeAbortableResult(
        verifySnapshot(release, operationContext(scope)),
      ),
      scope,
      "release snapshot verification",
    );
  } catch (error) {
    if (isTransportInability(error)) throw error;
    if (deferIntegrityRecord) {
      return deferredIntegrityIncident(state, phase, error);
    }
    return integrityIncident(state, record, phase, error);
  }
  if (proof !== true) {
    if (deferIntegrityRecord) {
      return deferredIntegrityIncident(
        state,
        phase,
        new Error("Release snapshot verifier did not return explicit true proof."),
      );
    }
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
    if (deferIntegrityRecord) {
      return deferredIntegrityIncident(
        state,
        phase,
        new Error("Release draft/immutable state is internally inconsistent."),
      );
    }
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
  if (!recordResult) return release;
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

async function reconcileReleasePublicationInScope({
  getRelease,
  startPublishRelease,
  verifySnapshot,
  initialState: seed,
  onState = () => {},
  onPublishHandle = () => {},
  maxCycles = 20,
  pollDelayMs = 3000,
  deferredQuiescenceMs = 15000,
  sleep = wait,
  intentIdentity = null,
  shouldAbort = () => false,
}, scope) {
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
  const boundedSleep = async (milliseconds, label) => {
    try {
      ensureScopeActive(scope, label);
      const available = Math.max(0, scope.deadline - Date.now());
      const duration = Math.max(0, Math.min(milliseconds, available));
      await awaitAbortableOperation(
        normalizeAbortableResult(
          sleep(duration, operationContext(scope)),
        ),
        scope,
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
      release = await awaitAbortableOperation(
        normalizeAbortableResult(
          getRelease(operationContext(scope)),
        ),
        scope,
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
        scope,
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
      ensureScopeActive(scope, "GitHub publication PATCH");
      handle = normalizePublishHandle(
        startPublishRelease(operationContext(scope)),
      );
      onPublishHandle(handle);
    } catch (error) {
      return settlementIncident(state, record, phase, error);
    }

    let response;
    try {
      response = await awaitAbortableOperation(
        {
          result: handle.response,
          settled: handle.settled,
          cancel: handle.cancel,
        },
        scope,
        "GitHub publication PATCH",
      );
    } catch (error) {
      try {
        await quiescePublishOperation(handle, scope);
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
      await awaitAbortableOperation(
        {
          result: handle.settled,
          settled: handle.settled,
          cancel: handle.cancel,
        },
        scope,
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
    let responseIntegrityError = null;
    try {
      response = await verifyExactRelease({
        release: response,
        phase: `${phase}-response`,
        state,
        record,
        verifySnapshot,
        scope,
        recordResult: false,
        deferIntegrityRecord: true,
      });
    } catch (error) {
      if (isTransportInability(error)) {
        return settlementIncident(
          state,
          record,
          `${phase}-response-verification`,
          error,
        );
      }
      if (error?.code !== "INTEGRITY_INCIDENT") throw error;
      responseIntegrityError = error;
    }
    state.publishSettled = true;
    state.publishSettlementUnproven = false;
    if (!record(
      `${phase}-operation-settled`,
      responseIntegrityError
        ? `response-integrity=${state.integrityDetail}`
        : "response-integrity=verified",
    )) {
      return persistenceIncident(
        state,
        responseIntegrityError
          ? "Publication response integrity failed and the combined "
            + "settlement/integrity state did not persist."
          : "Publication settled but settlement state did not persist.",
      );
    }
    if (responseIntegrityError) throw responseIntegrityError;
    return response;
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
    assertLocalOperationActive(shouldAbort, state, scope);
    let release = await readRelease(`reconcile-${cycle}-read`);
    assertLocalOperationActive(shouldAbort, state, scope);
    if (release.immutable === true) {
      return persistImmutableTerminal(state, record, release);
    }

    if (release.draft === true || cycle % 3 === 0) {
      assertLocalOperationActive(shouldAbort, state, scope);
      await requestPublish(`reconcile-${cycle}-publish`);
      assertLocalOperationActive(shouldAbort, state, scope);
      release = await readRelease(`reconcile-${cycle}-postpublish-read`);
      assertLocalOperationActive(shouldAbort, state, scope);
      if (release.immutable === true) {
        return persistImmutableTerminal(state, record, release);
      }
    }

    if (cycle < maxCycles) {
      assertLocalOperationActive(shouldAbort, state, scope);
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

export async function reconcileReleasePublication(options) {
  const ownsScope = !options.operationScope;
  const scope = options.operationScope || createDeadlineScope({
    overallDeadlineMs:
      options.overallDeadlineMs ?? DEFAULT_RECONCILE_DEADLINE_MS,
    signal: options.signal,
  });
  try {
    return await reconcileReleasePublicationInScope(options, scope);
  } finally {
    if (ownsScope) scope.dispose();
  }
}

async function runReleaseTransitionInScope({
  getRelease,
  startPublishRelease,
  verifySnapshot,
  onState = () => {},
  onPublishHandle = () => {},
  overallDeadlineMs = DEFAULT_RECONCILE_DEADLINE_MS,
  pollDelayMs = 3000,
  maxCycles = 20,
  sleep = wait,
  intentIdentity = null,
  shouldAbort = () => false,
}, scope) {
  const state = initialState({
    intentIdentity: normalizedIntentIdentity(intentIdentity),
  });
  const record = createRecorder(state, onState);
  let release;
  try {
    release = await awaitAbortableOperation(
      normalizeAbortableResult(
        getRelease(operationContext(scope)),
      ),
      scope,
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
      scope,
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
  assertLocalOperationActive(shouldAbort, state, scope);
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
    overallDeadlineMs,
    pollDelayMs,
    maxCycles,
    sleep,
    intentIdentity,
    shouldAbort,
    operationScope: scope,
  });
}

export async function runReleaseTransition(options) {
  const ownsScope = !options.operationScope;
  const scope = options.operationScope || createDeadlineScope({
    overallDeadlineMs:
      options.overallDeadlineMs ?? DEFAULT_RECONCILE_DEADLINE_MS,
    signal: options.signal,
  });
  try {
    return await runReleaseTransitionInScope(options, scope);
  } finally {
    if (ownsScope) scope.dispose();
  }
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

export function startAbortableExecFile(
  command,
  args,
  options = {},
  operation = {},
  execFileImpl = execFile,
) {
  let child = null;
  let forceKillTimer = null;
  let settle;
  const settled = new Promise((resolve) => {
    settle = () => {
      if (forceKillTimer) clearTimeout(forceKillTimer);
      resolve();
    };
  });
  const result = new Promise((resolve, reject) => {
    if (operation.signal?.aborted) {
      settle();
      reject(abortReason(operation.signal, `${command} subprocess`));
      return;
    }
    try {
      child = execFileImpl(command, args, {
        ...options,
        signal: operation.signal,
        killSignal: "SIGTERM",
      }, (error, stdout, stderr) => {
        settle();
        if (error) {
          if (stderr && !error.stderr) error.stderr = stderr;
          reject(error);
          return;
        }
        resolve({ stdout, stderr });
      });
    } catch (error) {
      settle();
      reject(error);
    }
  });
  return {
    result,
    settled,
    cancel: async () => {
      if (child && child.exitCode === null && child.signalCode === null) {
        child.kill("SIGTERM");
        if (!forceKillTimer && Number.isFinite(operation.hardDeadline)) {
          const remaining = Math.max(1, operation.hardDeadline - Date.now());
          forceKillTimer = setTimeout(() => {
            if (
              child
              && child.exitCode === null
              && child.signalCode === null
            ) {
              child.kill("SIGKILL");
            }
          }, Math.max(1, Math.min(500, Math.floor(remaining / 2))));
        }
      }
    },
  };
}

function ghJson(repository, releaseId, operation = {}) {
  const subprocess = startAbortableExecFile("gh", [
    "api",
    "--method",
    "GET",
    "-H",
    "X-GitHub-Api-Version: 2026-03-10",
    `repos/${repository}/releases/${releaseId}`,
  ], {
    encoding: "utf8",
    maxBuffer: 20 * 1024 * 1024,
  }, operation);
  return {
    result: subprocess.result.then(({ stdout }) => JSON.parse(stdout)),
    settled: subprocess.settled,
    cancel: subprocess.cancel,
  };
}

function startGhPublishOperation(repository, releaseId, operation = {}) {
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
  const subprocess = startAbortableExecFile("gh", args, {
    encoding: "utf8",
    maxBuffer: 20 * 1024 * 1024,
  }, operation);
  return {
    response: subprocess.result.then(({ stdout }) => JSON.parse(stdout)),
    settled: subprocess.settled,
    cancel: subprocess.cancel,
  };
}

function remoteRefOperation(repository, ref, operation = {}) {
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository)) {
    throw new Error("GitHub repository identity is invalid.");
  }
  const subprocess = startAbortableExecFile(
    "git",
    [
      "ls-remote",
      "--exit-code",
      `https://github.com/${repository}.git`,
      ref,
    ],
    {
      encoding: "utf8",
    },
    operation,
  );
  return {
    result: subprocess.result.then(({ stdout }) => {
      const sha = stdout.trim().split(/\s+/)[0];
      if (!/^[0-9a-f]{40}$/i.test(sha || "")) {
        throw new Error(`Remote ref ${ref} did not resolve in ${repository}.`);
      }
      return sha.toLowerCase();
    }),
    settled: subprocess.settled,
    cancel: subprocess.cancel,
  };
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
  return (release, operation = {}) => {
    let activeSubprocess = null;
    const result = (async () => {
      activeSubprocess = remoteRefOperation(
        args.repository,
        `refs/tags/${args.tag}`,
        operation,
      );
      const tagObject = await activeSubprocess.result;
      activeSubprocess = remoteRefOperation(
        args.repository,
        `refs/tags/${args.tag}^{}`,
        operation,
      );
      const commit = await activeSubprocess.result;
      verifyReleaseSnapshot(expected, {
        tag: release.tag_name,
        tagObject,
        commit,
        releaseId: String(release.id),
        releaseFingerprint: releaseContentFingerprint(release),
      });
      return true;
    })();
    return {
      result,
      settled: result.then(() => undefined, () => undefined),
      cancel: async () => activeSubprocess?.cancel(),
    };
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
  const scope = createDeadlineScope({ overallDeadlineMs });
  try {
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
        await quiescePublishOperation(handle, scope);
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
      await awaitAbortableOperation(
        normalizeAbortableResult(
          waitForMain(operationContext(scope)),
        ),
        scope,
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
        onPublishHandle: () => {},
        intentIdentity,
        operationScope: scope,
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
  } finally {
    scope.dispose();
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
  abortMain,
}) {
  let handling = false;
  let signalPromise = null;
  for (const signal of ["SIGINT", "SIGTERM"]) {
    process.once(signal, () => {
      if (handling) return;
      handling = true;
      process.exitCode = 130;
      abortMain(
        new ReleaseTransitionError(
          `${signal} interrupted the local publication operation.`,
          "LOCAL_OPERATION_INTERRUPTED",
          cliState.latest,
        ),
      );
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
  const getRelease = (operation) => ghJson(
    args.repository,
    args["release-id"],
    operation,
  );
  const startPublishRelease = (operation) => startGhPublishOperation(
    args.repository,
    args["release-id"],
    operation,
  );
  const verifySnapshot = createSnapshotVerifier(args);
  const intentIdentity = intentIdentityFromArgs(args);
  let activeHandle = null;
  let finishMain;
  const mainFinished = new Promise((resolve) => {
    finishMain = resolve;
  });
  const mainAbortController = new AbortController();
  const signalController = installSignalReconciler({
    cliState,
    getRelease,
    startPublishRelease,
    verifySnapshot,
    intentIdentity,
    getActiveHandle: () => activeHandle,
    waitForMain: () => mainFinished,
    abortMain: (reason) => mainAbortController.abort(reason),
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
      signal: mainAbortController.signal,
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
  const getRelease = (operation) => ghJson(
    args.repository,
    args["release-id"],
    operation,
  );
  const startPublishRelease = (operation) => startGhPublishOperation(
    args.repository,
    args["release-id"],
    operation,
  );
  const verifySnapshot = createSnapshotVerifier(args);
  const intentIdentity = intentIdentityFromArgs(args);
  let activeHandle = null;
  let finishMain;
  const mainFinished = new Promise((resolve) => {
    finishMain = resolve;
  });
  const mainAbortController = new AbortController();
  const signalController = installSignalReconciler({
    cliState,
    getRelease,
    startPublishRelease,
    verifySnapshot,
    intentIdentity,
    getActiveHandle: () => activeHandle,
    waitForMain: () => mainFinished,
    abortMain: (reason) => mainAbortController.abort(reason),
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
      signal: mainAbortController.signal,
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
