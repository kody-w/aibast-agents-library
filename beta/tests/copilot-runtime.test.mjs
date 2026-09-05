import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";

import {
  copilotPackageName,
  copilotRuntimeInternals,
  readGitHubTokenFile,
  resolveCopilotCliPath,
  withTimeout,
} from "../electron/copilot-runtime.mjs";

test("Copilot package selection follows platform and architecture", () => {
  assert.equal(
    copilotPackageName("darwin", "arm64"),
    "@github/copilot-darwin-arm64",
  );
  assert.equal(
    copilotPackageName("win32", "x64"),
    "@github/copilot-win32-x64",
  );
  assert.equal(
    copilotPackageName("linux", "x64"),
    "@github/copilot-linux-x64",
  );
});

test("packaged Copilot CLI resolves through app.asar.unpacked", () => {
  const logical = "/Applications/Frontier.app/Contents/Resources/app.asar/"
    + "node_modules/@github/copilot-darwin-arm64/copilot";
  const unpacked = "/Applications/Frontier.app/Contents/Resources/"
    + "app.asar.unpacked/node_modules/@github/copilot-darwin-arm64/copilot";
  assert.equal(
    copilotRuntimeInternals.asarUnpackedPath(
      logical,
      "/Applications/Frontier.app/Contents/Resources",
    ),
    unpacked,
  );
  assert.equal(
    resolveCopilotCliPath("darwin", "arm64", {
      fileExists: (candidate) => candidate === unpacked,
      requireResolve: () => logical,
      resourcesPath: "/Applications/Frontier.app/Contents/Resources",
    }),
    unpacked,
  );
});

test("Windows packaged Copilot CLI resolves outside app.asar", () => {
  const logical = String.raw`C:\Frontier\resources\app.asar\node_modules\@github\copilot-win32-x64\copilot.exe`;
  const unpacked = String.raw`C:\Frontier\resources\app.asar.unpacked\node_modules\@github\copilot-win32-x64\copilot.exe`;
  assert.equal(
    resolveCopilotCliPath("win32", "x64", {
      fileExists: (candidate) => candidate === unpacked,
      requireResolve: () => logical,
      resourcesPath: String.raw`C:\Frontier\resources`,
    }),
    unpacked,
  );
});

test("logical app.asar Copilot paths never fall through to spawn", () => {
  const logical = "/Frontier/Resources/app.asar/node_modules/copilot";
  assert.equal(
    resolveCopilotCliPath("darwin", "arm64", {
      fileExists: (candidate) => candidate === logical,
      requireResolve: () => logical,
      resourcesPath: "/Frontier/Resources",
    }),
    undefined,
  );
});

test("Copilot startup timeout rejects a hung runtime", async () => {
  await assert.rejects(
    withTimeout(new Promise(() => {}), "test runtime", 5),
    /test runtime did not start within 5ms/,
  );
});

test("Copilot startup timeout preserves successful results", async () => {
  assert.equal(await withTimeout(Promise.resolve("ready"), "test runtime", 50), "ready");
});

test("Copilot runtime reads the protected Brainstem device token", () => {
  const directory = mkdtempSync(path.join(tmpdir(), "brainstem-token-"));
  const tokenFile = path.join(directory, ".copilot_token");
  try {
    writeFileSync(tokenFile, JSON.stringify({
      access_token: "ghu_example",
      refresh_token: "hidden",
    }));
    assert.equal(readGitHubTokenFile(tokenFile), "ghu_example");
    writeFileSync(tokenFile, "{not json");
    assert.equal(readGitHubTokenFile(tokenFile), null);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});
