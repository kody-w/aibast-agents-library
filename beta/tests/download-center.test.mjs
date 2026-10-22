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
# throw, not exit: under "irm ... | iex" exit would close the window before the message can be read.
throw "RAPP Brainstem Frontier has been retired."
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

test("the PowerShell Frontier alias explains retirement, fails, and keeps the window open", (t) => {
  assert.equal(read("frontier.ps1"), expectedPowerShell);
  const probe = spawnSync("pwsh", ["-NoProfile", "-Command", "$PSVersionTable.PSVersion.Major"], { encoding: "utf8" });
  if (probe.error) {
    t.skip("pwsh is not installed");
    return;
  }
  // Run it the way the published one-liner does (piped into Invoke-Expression).
  const script = path.join(betaRoot, "frontier.ps1").replace(/'/g, "''");
  const result = spawnSync("pwsh", [
    "-NoProfile", "-Command",
    `try { Get-Content -Raw '${script}' | Invoke-Expression } catch { 'failed: ' + $_.Exception.Message }; 'session still open'`,
  ], { encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
  assert.equal(
    result.stdout.replace(/\r\n/g, "\n"),
    `${message}\n${powershellOneLiner}\nfailed: RAPP Brainstem Frontier has been retired.\nsession still open\n`,
  );
});

test("retired aliases contain no installer, release resolver, or network execution", () => {
  const unix = read("frontier.sh");
  const windows = read("frontier.ps1");

  assert.doesNotMatch(unix, /api\.github\.com|beta\/install\.sh|RAPP_FRONTIER_REPO|BRAINSTEM_BETA_/);
  assert.doesNotMatch(windows, /Invoke-(?:WebRequest|RestMethod)|beta\/install\.cmd|RAPP_FRONTIER_REPO|BRAINSTEM_BETA_/);
  assert.equal((unix.match(/\bexit 1\b/g) || []).length, 1);
  assert.doesNotMatch(windows, /^\s*exit\b/m);
});
