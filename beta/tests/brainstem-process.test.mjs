import assert from "node:assert/strict";
import http from "node:http";
import path from "node:path";
import test from "node:test";

import {
  assessBrainstemHealth,
  buildBrainstemEnvironment,
  isBrainstemHealth,
  MINIMUM_BRAINSTEM_VERSION,
  probeHealthEvidence,
  resolveBrainstemConfig,
  versionAtLeast,
  waitForHealth,
} from "../electron/brainstem-process.mjs";

test("beta launcher resolves the shared global Brainstem", () => {
  const config = resolveBrainstemConfig({
    env: {},
    platform: "linux",
    home: "/tmp/example-home",
  });
  assert.equal(config.brainstemHome, "/tmp/example-home/.brainstem");
  assert.equal(
    config.brainstemDir,
    path.posix.join("/tmp/example-home/.brainstem", "src", "rapp_brainstem"),
  );
  assert.equal(
    config.python,
    path.posix.join("/tmp/example-home/.brainstem", "venv", "bin", "python"),
  );
  assert.equal(
    config.logFile,
    path.posix.join("/tmp/example-home/.brainstem", "logs", "beta-brainstem.log"),
  );
  assert.equal(config.port, 7071);
});

test("beta launcher resolves Windows Brainstem paths on every host", () => {
  const home = String.raw`C:\Users\example`;
  const brainstemHome = path.win32.join(home, ".brainstem");
  const config = resolveBrainstemConfig({
    env: {},
    platform: "win32",
    home,
  });
  assert.equal(config.brainstemHome, brainstemHome);
  assert.equal(
    config.brainstemDir,
    path.win32.join(brainstemHome, "src", "rapp_brainstem"),
  );
  assert.equal(
    config.python,
    path.win32.join(brainstemHome, "venv", "Scripts", "python.exe"),
  );
  assert.equal(
    config.logFile,
    path.win32.join(brainstemHome, "logs", "beta-brainstem.log"),
  );
});

test("beta launcher respects an explicit isolated BRAINSTEM_HOME", () => {
  const config = resolveBrainstemConfig({
    env: { BRAINSTEM_HOME: "/workspace/isolated-brainstem" },
    platform: "linux",
    home: "/real-home-must-not-be-used",
  });
  assert.equal(config.brainstemHome, "/workspace/isolated-brainstem");
  assert.equal(
    config.brainstemDir,
    "/workspace/isolated-brainstem/src/rapp_brainstem",
  );
  assert.equal(
    config.python,
    "/workspace/isolated-brainstem/venv/bin/python",
  );
});

test("spawned Brainstem receives authoritative home distinct from HOME", () => {
  const environment = buildBrainstemEnvironment({
    brainstemHome: "/workspace/isolated-brainstem",
    port: 7444,
    env: {
      BRAINSTEM_HOME: "/must-not-win",
      USERPROFILE: String.raw`C:\Users\developer`,
    },
  }, {
    HOME: "/Users/developer",
    BRAINSTEM_HOME: "/developer/.brainstem",
  });
  assert.equal(environment.HOME, "/Users/developer");
  assert.equal(environment.USERPROFILE, String.raw`C:\Users\developer`);
  assert.equal(environment.BRAINSTEM_HOME, "/workspace/isolated-brainstem");
  assert.equal(environment.PORT, "7444");
});

test("beta launcher accepts authenticated and unauthenticated health", () => {
  const base = {
    version: MINIMUM_BRAINSTEM_VERSION,
    soul: "/isolated/soul.md",
    agents: ["ContextMemory"],
    quarantined: [],
  };
  assert.equal(isBrainstemHealth({ ...base, status: "ok" }), true);
  assert.equal(isBrainstemHealth({ ...base, status: "unauthenticated" }), true);
  assert.equal(
    isBrainstemHealth({ ...base, status: "ok", agents: [] }),
    false,
  );
  assert.equal(
    isBrainstemHealth({ ...base, status: "ok", version: "0.6.15" }),
    false,
  );
  assert.equal(
    isBrainstemHealth({ ...base, status: "ok", quarantined: [{}] }),
    false,
  );
  assert.equal(isBrainstemHealth({ status: "ok", version: "0.6.16" }), false);
  assert.equal(isBrainstemHealth({ status: "other", ...base }), false);
});

test("health compatibility reports expected-agent and load-error evidence", () => {
  const assessment = assessBrainstemHealth({
    status: "unauthenticated",
    version: MINIMUM_BRAINSTEM_VERSION,
    soul: "/isolated/soul.md",
    agents: ["OtherAgent"],
    quarantined: [{
      file: "broken_agent.py",
      reason: "missing dependency",
    }],
  }, {
    expectedAgents: ["ContextMemory", "ManageMemory"],
    minimumAgentCount: 2,
  });
  assert.equal(assessment.ok, false);
  assert.match(assessment.issues.join("\n"), /Expected agents did not load/);
  assert.match(assessment.issues.join("\n"), /broken_agent\.py/);
});

test("runtime version compatibility is semantic, not lexical", () => {
  assert.equal(versionAtLeast("0.6.16", "0.6.16"), true);
  assert.equal(versionAtLeast("0.10.0", "0.6.16"), true);
  assert.equal(versionAtLeast("0.6.15", "0.6.16"), false);
  assert.equal(versionAtLeast("moving-main", "0.6.16"), false);
});

test("reachable incompatible health returns concrete failure evidence", async () => {
  const server = http.createServer((_request, response) => {
    response.writeHead(200, { "Content-Type": "application/json" });
    response.end(JSON.stringify({
      status: "unauthenticated",
      version: "0.6.15",
      soul: "missing",
      agents: [],
      quarantined: [{ file: "broken_agent.py", reason: "load failed" }],
    }));
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    const address = server.address();
    const evidence = await probeHealthEvidence(
      `http://127.0.0.1:${address.port}`,
    );
    assert.equal(evidence.reachable, true);
    assert.equal(evidence.health, null);
    assert.match(evidence.issues.join("\n"), /compatible minimum/);
    assert.match(evidence.issues.join("\n"), /loaded 0 agents/);
    assert.match(evidence.issues.join("\n"), /broken_agent\.py/);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test("health wait stops when the child exits", async () => {
  let calls = 0;
  const result = await waitForHealth("http://127.0.0.1:7071", {
    timeoutMs: 5_000,
    intervalMs: 1,
    probe: async () => {
      calls += 1;
      return null;
    },
    exited: () => calls >= 2,
  });
  assert.equal(result, null);
  assert.equal(calls, 2);
});

test("health wait returns the first valid response", async () => {
  const health = {
    status: "unauthenticated",
    version: "0.6.16",
    soul: "/isolated/soul.md",
    agents: ["ContextMemory"],
    quarantined: [],
  };
  let calls = 0;
  const result = await waitForHealth("http://127.0.0.1:7071", {
    timeoutMs: 100,
    intervalMs: 1,
    probe: async () => {
      calls += 1;
      return calls === 2 ? health : null;
    },
  });
  assert.deepEqual(result, health);
});
