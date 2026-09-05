import assert from "node:assert/strict";
import { PassThrough } from "node:stream";
import { test } from "node:test";
import {
  closeSync,
  mkdirSync,
  openSync,
  readFileSync,
  rmSync,
} from "node:fs";
import path from "node:path";

import { attachScrubbedLog, scrubSecrets } from "../electron/safe-log.mjs";

const scratchRoot = path.join(
  path.resolve(import.meta.dirname, ".."),
  ".test-tmp",
  "safe-log",
);

test("launcher log boundary redacts credential canaries across chunks", async () => {
  rmSync(scratchRoot, { recursive: true, force: true });
  mkdirSync(scratchRoot, { recursive: true });
  const logPath = path.join(scratchRoot, "launcher.log");
  const fd = openSync(logPath, "w", 0o600);
  const stream = new PassThrough();
  const cleanup = attachScrubbedLog(stream, fd);
  stream.write("GITHUB_TOKEN=ghp_Chunked");
  stream.write("Canary123456\nAuthorization: Bearer bearerCanary123456\n");
  stream.end("https://alice:password@example.test/path");
  await new Promise((resolve) => stream.once("end", resolve));
  cleanup();
  closeSync(fd);

  const log = readFileSync(logPath, "utf8");
  for (const secret of [
    "ghp_ChunkedCanary123456",
    "bearerCanary123456",
    "alice",
    "password",
  ]) {
    assert.doesNotMatch(log, new RegExp(secret));
  }
  assert.match(log, /\[REDACTED\]/);
  assert.doesNotMatch(
    scrubSecrets("CLIENT_SECRET=topsecretvalue"),
    /topsecretvalue/,
  );
  rmSync(scratchRoot, { recursive: true, force: true });
});
