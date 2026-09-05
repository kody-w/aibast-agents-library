import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { readFileSync, writeFileSync } from "node:fs";
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

export function recoveryRequiredFromState(state) {
  return Boolean(
    state
    && typeof state === "object"
    && state.transitionAttempted === true,
  );
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
}) {
  const state = {
    phase: "ready",
    transitionAttempted: false,
    observedMutable: false,
    integrityViolation: false,
    integrityDetail: null,
    history: [],
  };
  const record = (phase, detail = "") => {
    state.phase = phase;
    state.history.push({ phase, detail });
    onState(structuredClone(state));
  };
  const latchIntegrity = (phase, error) => {
    state.integrityViolation = true;
    state.integrityDetail ||= String(error.message || error);
    record(`${phase}-integrity-violation`, String(error.message || error));
  };
  const inspect = async (release, phase) => {
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
    record(phase, `draft=${release.draft}; immutable=${release.immutable}`);
    return release;
  };
  const read = async (phase) => {
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
      latchIntegrity(phase, error);
      throw error;
    }
  };
  const completed = (release, phase) => {
    if (state.integrityViolation) {
      throw new ReleaseTransitionError(
        "An integrity violation was observed before immutable publication.",
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
      : "Release rollback was verified in draft state.",
    state.integrityViolation ? "INTEGRITY_ROLLED_BACK" : "ROLLED_BACK",
    state,
  );
  const recover = async (reason) => {
    record("rollback-required", reason);
    for (let attempt = 1; attempt <= maxRollbackAttempts; attempt += 1) {
      let before = null;
      try {
        before = await read(`rollback-${attempt}-initial-read`);
      } catch {
        // Integrity is sticky; continue directly to the ID-bound rollback.
      }
      if (before?.immutable === true) {
        return completed(before, "immutable-during-recovery");
      }
      if (before?.draft === true) throw draftFailure();

      try {
        const response = await rollbackRelease();
        if (response) {
          try {
            const inspected = await inspect(
              response,
              `rollback-${attempt}-response`,
            );
            if (inspected.immutable === true) {
              return completed(inspected, "immutable-during-recovery");
            }
            if (inspected.draft === true) throw draftFailure();
          } catch (error) {
            if (error instanceof ReleaseTransitionError) throw error;
            latchIntegrity(`rollback-${attempt}-response`, error);
          }
        }
      } catch (error) {
        if (error instanceof ReleaseTransitionError) throw error;
        record(`rollback-${attempt}-transport-failed`, String(error.message || error));
      }

      let after = null;
      try {
        after = await read(`rollback-${attempt}-verification`);
      } catch {
        // Integrity remains latched and cannot be cleared by a later response.
      }
      if (after?.immutable === true) {
        return completed(after, "immutable-during-recovery");
      }
      if (after?.draft === true) throw draftFailure();
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
      `Release integrity failed before publication: ${String(error.message || error)}`,
      "INTEGRITY",
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
  record("publishing");
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
      if (state.observedMutable) throw draftFailure();
      throw new ReleaseTransitionError(
        "Release publication was not observed.",
        "NOT_PUBLISHED",
        state,
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
}) {
  const state = {
    phase: "recovery-started",
    transitionAttempted: true,
    integrityViolation: false,
    history: [],
  };
  const record = (phase, detail = "") => {
    state.phase = phase;
    state.history.push({ phase, detail });
    onState(structuredClone(state));
  };
  const inspect = async (release, phase) => {
    const proof = await verifySnapshot(release);
    if (proof !== true) {
      throw new Error("Release snapshot verifier did not return an explicit true proof.");
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
      record(`${phase}-integrity-violation`, String(error.message || error));
      return null;
    }
  };
  const stable = (release) => {
    if (release?.immutable === true && release.draft === false) {
      if (state.integrityViolation) {
        throw new ReleaseTransitionError(
          "Integrity violation preceded immutable recovery.",
          "INCIDENT",
          state,
        );
      }
      record("recovery-verified-immutable");
      return { status: "immutable", release, state };
    }
    if (release?.draft === true) {
      record("recovery-verified-draft");
      return { status: "draft", release, state };
    }
    return null;
  };

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const before = await observe(`recovery-${attempt}-initial-read`);
    const beforeStable = stable(before);
    if (beforeStable) return beforeStable;
    try {
      const response = await rollbackRelease();
      if (response) {
        try {
          const responseStable = stable(
            await inspect(response, `recovery-${attempt}-rollback-response`),
          );
          if (responseStable) return responseStable;
        } catch (error) {
          state.integrityViolation = true;
          record(
            `recovery-${attempt}-rollback-integrity-failed`,
            String(error.message || error),
          );
        }
      }
    } catch (error) {
      record(
        `recovery-${attempt}-rollback-transport-failed`,
        String(error.message || error),
      );
    }
    const after = await observe(`recovery-${attempt}-verification`);
    const afterStable = stable(after);
    if (afterStable) return afterStable;
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
  const onState = (state) => {
    writeFileSync(stateFile, `${JSON.stringify(state, null, 2)}\n`, "utf8");
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
      onState({
        phase: "interrupted-recovery-started",
        signal,
        transitionAttempted: true,
      });
      try {
        const recovery = await recoverInterruptedRelease({
          getRelease,
          rollbackRelease,
          verifySnapshot,
          maxAttempts: 2,
          pollDelayMs: 1000,
          onState,
        });
        writeFileSync(
          output,
          `${JSON.stringify(recovery.release, null, 2)}\n`,
          "utf8",
        );
      } catch (error) {
        onState(error.state || {
          phase: "interrupted-recovery-incident",
          signal,
          transitionAttempted: true,
          detail: String(error.message || error),
        });
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
    onState(error.state || {
      phase: "incident",
      detail: String(error.message || error),
    });
    throw error;
  }
}

export async function recoverReleaseFromStateFile(argv = process.argv.slice(2)) {
  const args = parseArguments(argv);
  const stateFile = path.resolve(args["state-file"]);
  const output = path.resolve(args.output);
  const durableState = JSON.parse(readFileSync(stateFile, "utf8"));
  if (!recoveryRequiredFromState(durableState)) {
    return { status: "no-transition", release: null, state: durableState };
  }
  const expected = {
    tag: args.tag,
    tagObject: args["tag-object"],
    commit: args.commit,
    releaseId: args["release-id"],
    releaseFingerprint: args["release-fingerprint"],
  };
  const onState = (state) => {
    writeFileSync(stateFile, `${JSON.stringify(state, null, 2)}\n`, "utf8");
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
  const recovery = await recoverInterruptedRelease({
    getRelease: () => ghJson(args.repository, args["release-id"]),
    rollbackRelease: () => ghJson(
      args.repository,
      args["release-id"],
      "PATCH",
      ["-F", "draft=true"],
    ),
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
