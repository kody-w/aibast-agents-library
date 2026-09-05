import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { writeFileSync } from "node:fs";
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
    history: [],
  };
  const record = (phase, detail = "") => {
    state.phase = phase;
    state.history.push({ phase, detail });
    onState(structuredClone(state));
  };
  const inspect = async (release, phase) => {
    await verifySnapshot(release);
    if (release.immutable === true && release.draft !== false) {
      throw new ReleaseTransitionError(
        "Immutable release metadata is internally inconsistent.",
        "INCIDENT",
        state,
      );
    }
    if (release.draft === false && release.immutable !== true) {
      state.observedMutable = true;
    }
    record(phase, `draft=${release.draft}; immutable=${release.immutable}`);
    return release;
  };
  const read = async (phase) => {
    try {
      return await inspect(await getRelease(), phase);
    } catch (error) {
      record(`${phase}-failed`, String(error.message || error));
      return null;
    }
  };
  const completed = (release, phase) => {
    record(phase, "release is immutable");
    return { release, state };
  };

  const prepublish = await read("immediately-before-publication");
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
  try {
    const response = await inspect(
      await publishRelease(),
      "publish-response",
    );
    if (response.immutable === true) return completed(response, "immutable");
  } catch (error) {
    record("publish-response-lost-or-failed", String(error.message || error));
  }

  for (let attempt = 1; attempt <= maxPolls; attempt += 1) {
    const release = await read(`poll-${attempt}`);
    if (release?.immutable === true) return completed(release, "immutable");
    if (release?.draft === true) {
      const code = state.observedMutable ? "ROLLED_BACK" : "NOT_PUBLISHED";
      throw new ReleaseTransitionError(
        state.observedMutable
          ? "Release returned to draft during publication polling."
          : "Release publication was not observed.",
        code,
        state,
      );
    }
    if (attempt < maxPolls) await sleep(pollDelayMs);
  }

  record("rollback-required");
  for (let attempt = 1; attempt <= maxRollbackAttempts; attempt += 1) {
    const before = await read(`rollback-${attempt}-initial-read`);
    if (before?.immutable === true) return completed(before, "immutable");
    if (before?.draft === true) {
      throw new ReleaseTransitionError(
        "Release rollback was verified in draft state.",
        "ROLLED_BACK",
        state,
      );
    }
    try {
      const response = await rollbackRelease();
      if (response) {
        const inspected = await inspect(
          response,
          `rollback-${attempt}-response`,
        );
        if (inspected.immutable === true) {
          return completed(inspected, "immutable");
        }
        if (inspected.draft === true) {
          throw new ReleaseTransitionError(
            "Release rollback was verified in draft state.",
            "ROLLED_BACK",
            state,
          );
        }
      }
    } catch (error) {
      if (error instanceof ReleaseTransitionError) throw error;
      record(`rollback-${attempt}-request-failed`, String(error.message || error));
    }
    const after = await read(`rollback-${attempt}-verification`);
    if (after?.immutable === true) return completed(after, "immutable");
    if (after?.draft === true) {
      throw new ReleaseTransitionError(
        "Release rollback was verified in draft state.",
        "ROLLED_BACK",
        state,
      );
    }
    if (attempt < maxRollbackAttempts) await sleep(pollDelayMs);
  }

  record("incident-unproven-state");
  throw new ReleaseTransitionError(
    "Release state could not be proven immutable or draft after retries.",
    "INCIDENT",
    state,
  );
}

function parseArguments(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
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
  for (const signal of ["SIGINT", "SIGTERM"]) {
    process.once(signal, () => {
      onState({
        phase: "interrupted",
        signal,
        transitionAttempted: true,
      });
      process.exit(130);
    });
  }
  const verifySnapshot = async (release) => verifyReleaseSnapshot(expected, {
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
  try {
    const result = await runReleaseTransition({
      getRelease: () => ghJson(
        args.repository,
        args["release-id"],
      ),
      publishRelease: () => ghJson(
        args.repository,
        args["release-id"],
        "PATCH",
        ["-F", "draft=false", "-F", "prerelease=true", "-f", "make_latest=false"],
      ),
      rollbackRelease: () => ghJson(
        args.repository,
        args["release-id"],
        "PATCH",
        ["-F", "draft=true"],
      ),
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

if (
  process.argv[1]
  && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href
) {
  publishReleaseWithStateMachine()
    .then(({ release }) => {
      process.stdout.write(
        `Published immutable release ${release.id} at ${release.tag_name}.\n`,
      );
    })
    .catch((error) => {
      process.stderr.write(
        `Release publication state machine failed [${error.code || "ERROR"}]: `
        + `${String(error.stack || error)}\n`,
      );
      process.exit(1);
    });
}
