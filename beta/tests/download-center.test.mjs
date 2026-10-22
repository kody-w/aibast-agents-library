import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const betaRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (name) => readFileSync(path.join(betaRoot, name), "utf8").replace(/\r\n/g, "\n");

const message =
  "RAPP Brainstem Frontier has been retired. To build from scratch on your own device, install the Brainstem:";
const bashOneLiner =
  "curl -fsSL https://microsoft.github.io/aibast-agents-library/install.sh | bash";
const powershellOneLiner =
  "irm https://microsoft.github.io/aibast-agents-library/install.ps1 | iex";

const expectedBash = `#!/usr/bin/env bash

printf '%s\\n' \\
    "${message}" \\
    "${bashOneLiner}"
exit 1
`;

const expectedPowerShell = `Write-Output "${message}"
Write-Output "${powershellOneLiner}"
exit 1
`;

test("the Unix Frontier alias only explains retirement and exits 1", () => {
  const source = read("frontier.sh");
  assert.equal(source, expectedBash);

  const result = spawnSync("bash", [path.join(betaRoot, "frontier.sh")], {
    encoding: "utf8",
  });
  assert.equal(result.status, 1);
  assert.equal(result.signal, null);
  assert.equal(result.stdout, `${message}\n${bashOneLiner}\n`);
  assert.equal(result.stderr, "");
});

test("the PowerShell Frontier alias only explains retirement and exits 1", () => {
  assert.equal(read("frontier.ps1"), expectedPowerShell);
});

test("retired aliases contain no installer, release resolver, or network execution", () => {
  const unix = read("frontier.sh");
  const windows = read("frontier.ps1");

  assert.doesNotMatch(unix, /api\.github\.com|beta\/install\.sh|RAPP_FRONTIER_REPO|BRAINSTEM_BETA_/);
  assert.doesNotMatch(windows, /Invoke-(?:WebRequest|RestMethod)|beta\/install\.cmd|RAPP_FRONTIER_REPO|BRAINSTEM_BETA_/);
  assert.equal((unix.match(/\bexit 1\b/g) || []).length, 1);
  assert.equal((windows.match(/\bexit 1\b/g) || []).length, 1);
});
