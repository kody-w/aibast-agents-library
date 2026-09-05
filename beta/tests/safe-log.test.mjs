import assert from "node:assert/strict";
import { PassThrough } from "node:stream";
import { test } from "node:test";
import {
  closeSync,
  mkdirSync,
  openSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

import {
  attachScrubbedLog,
  sanitizeTelemetryValue,
  scrubSecrets,
} from "../electron/safe-log.mjs";

const betaDir = path.resolve(import.meta.dirname, "..");
const scratchRoot = path.join(betaDir, ".test-tmp", "safe-log");

test("launcher log boundary recursively redacts JSON and chunked canaries", async () => {
  rmSync(scratchRoot, { recursive: true, force: true });
  mkdirSync(scratchRoot, { recursive: true });
  const logPath = path.join(scratchRoot, "launcher.log");
  const fd = openSync(logPath, "w", 0o600);
  const stream = new PassThrough();
  const cleanup = attachScrubbedLog(stream, fd);
  const canaries = {
    access: "accessJsonCanary",
    api: "apiJsonCanary",
    client: "clientJsonCanary",
    github: "githubJsonCanary",
    password: "passwordJsonCanary",
    quoted: "quotedAssignmentCanary",
    refresh: "refreshJsonCanary",
  };
  stream.write("GITHUB_TOKEN=ghp_Chunked");
  stream.write("Canary123456\nAuthorization: Bearer bearerCanary123456\n");
  stream.write("https://alice:urlPasswordCanary@example.test/path\n");
  stream.write(
    `{"api_key": "${canaries.api}", "password": "${canaries.password}", `
    + `"client_secret": "${canaries.client}", "nested": `
    + `{"access_token": "${canaries.access}"}, "items": `
    + `[{"refresh_token": "${canaries.refresh}"}, `
    + `{"github_token": "${canaries.github}"}]}\n`,
  );
  stream.end(`CLIENT_SECRET="${canaries.quoted}"`);
  await new Promise((resolve) => stream.once("end", resolve));
  cleanup();
  closeSync(fd);

  const log = readFileSync(logPath, "utf8");
  for (const secret of [
    "ghp_ChunkedCanary123456",
    "bearerCanary123456",
    "alice",
    "urlPasswordCanary",
    ...Object.values(canaries),
  ]) {
    assert.doesNotMatch(log, new RegExp(secret));
  }
  assert.match(log, /\[REDACTED\]/);
  assert.doesNotMatch(
    scrubSecrets('CLIENT_SECRET="topsecretvalue"'),
    /topsecretvalue/,
  );
  const telemetry = sanitizeTelemetryValue({
    args: {
      api_key: canaries.api,
      nested: [{ password: canaries.password }],
    },
  });
  assert.doesNotMatch(JSON.stringify(telemetry), /JsonCanary/);
  rmSync(scratchRoot, { recursive: true, force: true });
});

test("JSON redaction gate kills a sensitive-key mutation", async () => {
  mkdirSync(scratchRoot, { recursive: true });
  const literalJsonDump =
    '{"client_secret": "jsonMutationCanary", "nested": '
    + '{"password": "nestedMutationCanary"}}';
  const gate = (scrub) => {
    const sanitized = scrub(literalJsonDump);
    assert.doesNotMatch(sanitized, /jsonMutationCanary|nestedMutationCanary/);
    assert.match(sanitized, /\[REDACTED\]/);
  };
  gate(scrubSecrets);

  const sourcePath = path.join(betaDir, "electron", "safe-log.mjs");
  const original = readFileSync(sourcePath, "utf8").replace(/\r\n/g, "\n");
  const target = `function sensitiveKey(key) {
  return SENSITIVE_KEYS.has(
    String(key || "").toLowerCase().replace(/[^a-z0-9]/g, ""),
  );
}`;
  const mutant = original.replace(
    target,
    "function sensitiveKey(_key) {\n  return false;\n}",
  );
  assert.notEqual(mutant, original, "JSON sensitive-key mutation must apply");
  const mutantPath = path.join(scratchRoot, "safe-log-mutant.mjs");
  writeFileSync(mutantPath, mutant);
  const mutated = await import(
    `${pathToFileURL(mutantPath).href}?mutation=${Date.now()}`
  );
  assert.throws(
    () => gate(mutated.scrubSecrets),
    /expected to not match/i,
  );
  rmSync(scratchRoot, { recursive: true, force: true });
});
