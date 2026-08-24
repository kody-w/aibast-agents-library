import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync, chmodSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";

import {
  anchorSha,
  criesMuted,
  hatchCitizen,
  loadRoster,
  muteFlagPath,
  rappidAnchor,
  resolveRappidEngine,
  rosterFor,
  setCriesMuted,
} from "../electron/rappid-species.mjs";

// These tests exercise the BRIDGE contract only. The engine below is a stub
// that stands in for species/rappidex.py inside a throwaway home — no rite is
// bypassed and no record ever lands in a real rapp home.

function writeRecord(rappHome, dir, record) {
  const home = path.join(rappHome, "rappids", dir);
  mkdirSync(home, { recursive: true });
  writeFileSync(path.join(home, "rappid.json"), JSON.stringify(record));
}

test("rappidAnchor is stable per citizen and refuses unknown kinds", () => {
  assert.equal(rappidAnchor("twin", "json-doctor"), "frontier-twin:json-doctor");
  assert.equal(
    rappidAnchor("rapplication", "abc"),
    "frontier-rapplication:abc",
  );
  assert.equal(anchorSha(rappidAnchor("twin", "x")), anchorSha("frontier-twin:x"));
  assert.throws(() => rappidAnchor("estate", "x"), /Unknown rappid kind/);
});

test("resolveRappidEngine honors RAPPID_DIR and degrades to null", () => {
  const temporary = mkdtempSync(path.join(tmpdir(), "rappid-engine-"));
  mkdirSync(path.join(temporary, "species"), { recursive: true });
  writeFileSync(path.join(temporary, "species", "rappidex.py"), "# stub\n");
  const found = resolveRappidEngine({ env: { RAPPID_DIR: temporary }, home: "/nonexistent" });
  assert.equal(found.dir, temporary);
  assert.equal(
    resolveRappidEngine({ env: {}, home: path.join(temporary, "empty") }),
    null,
  );
});

test("loadRoster keeps only sealed anchored records", () => {
  const temporary = mkdtempSync(path.join(tmpdir(), "rappid-roster-"));
  const sealedSha = anchorSha(rappidAnchor("twin", "json-doctor"));
  writeRecord(temporary, "twin-json-doctor", {
    rappid: "rappid:@kody-w/twin-json-doctor:aa",
    species: "twin",
    display_name: "Twin of “JSON Doctor”",
    rarity: "rare",
    genome_id: "abc123def456",
    birth: { seal: "s".repeat(64), anchor: { sha256: sealedSha, title: "JSON Doctor" } },
  });
  writeRecord(temporary, "unsealed", {
    rappid: "rappid:@kody-w/unsealed:bb",
    birth: { anchor: { sha256: anchorSha("frontier-twin:unsealed") } },
  });
  writeRecord(temporary, "unanchored", {
    rappid: "rappid:@kody-w/claude:cc",
    birth: { seal: "s".repeat(64) },
  });
  const roster = loadRoster({ env: { RAPP_HOME: temporary } });
  assert.equal(roster.size, 1);
  assert.equal(roster.get(sealedSha).genome_id, "abc123def456");
});

test("rosterFor answers by kind:id and skips malformed keys", () => {
  const temporary = mkdtempSync(path.join(tmpdir(), "rappid-for-"));
  const sha = anchorSha(rappidAnchor("rapplication", "seer"));
  writeRecord(temporary, "rapplication-seer", {
    rappid: "rappid:@kody-w/rapplication-seer:dd",
    rarity: "epic",
    genome_id: "eeff00112233",
    birth: { seal: "s".repeat(64), anchor: { sha256: sha } },
  });
  const previous = process.env.RAPP_HOME;
  process.env.RAPP_HOME = temporary;
  try {
    const out = rosterFor([
      { kind: "rapplication", id: "seer" },
      { kind: "twin", id: "absent" },
      { kind: "estate", id: "nope" },
      { kind: "twin" },
    ]);
    assert.equal(out["rapplication:seer"].rarity, "epic");
    assert.equal(out["twin:absent"], null);
    assert.equal("estate:nope" in out, false);
  } finally {
    if (previous === undefined) delete process.env.RAPP_HOME;
    else process.env.RAPP_HOME = previous;
  }
});

test("hatchCitizen is a no-op without an engine and idempotent with one", async () => {
  const off = await hatchCitizen({ engine: null, kind: "twin", id: "x", title: "X" });
  assert.deepEqual(off, { ok: false, error: "no-engine" });

  const temporary = mkdtempSync(path.join(tmpdir(), "rappid-hatch-"));
  const rappHome = path.join(temporary, "rapp-home");
  const engineDir = path.join(temporary, "engine");
  mkdirSync(path.join(engineDir, "species"), { recursive: true });
  const sha = anchorSha(rappidAnchor("twin", "json-doctor"));
  // The stub engine answers the species probe quietly and, on a real hatch,
  // writes one sealed anchored record — the shape the bridge must read back.
  const stub = `#!/usr/bin/env python3
import json, os, sys
if "--attempts" in sys.argv and sys.argv[sys.argv.index("--attempts") + 1] == "0":
    print("the egg stays an egg"); sys.exit(0)
if sys.argv[1] == "hatch":
    home = os.path.join(os.environ["RAPP_HOME"], "rappids", "twin-json-doctor")
    os.makedirs(home, exist_ok=True)
    record = {"rappid": "rappid:@test/twin-json-doctor:ee", "species": "twin",
              "display_name": "Twin of Json Doctor", "rarity": "rare",
              "genome_id": "0123456789ab",
              "birth": {"seal": "s" * 64, "anchor": {"sha256": "__SHA__"}}}
    with open(os.path.join(home, "rappid.json"), "w") as f:
        json.dump(record, f)
    print("hatched")
`.replace("__SHA__", sha);
  const script = path.join(engineDir, "species", "rappidex.py");
  writeFileSync(script, stub);
  chmodSync(script, 0o755);

  const previous = process.env.RAPP_HOME;
  process.env.RAPP_HOME = rappHome;
  try {
    const first = await hatchCitizen({
      engine: { dir: engineDir, script },
      kind: "twin",
      id: "json-doctor",
      title: "JSON Doctor",
    });
    assert.equal(first.ok, true);
    assert.equal(first.hatched, true);
    assert.equal(first.record.genome_id, "0123456789ab");
    const again = await hatchCitizen({
      engine: { dir: engineDir, script },
      kind: "twin",
      id: "json-doctor",
      title: "JSON Doctor",
    });
    assert.equal(again.ok, true);
    assert.equal(again.hatched, false);   // one creature per anchor
  } finally {
    if (previous === undefined) delete process.env.RAPP_HOME;
    else process.env.RAPP_HOME = previous;
  }
});

test("resolveOwner prefers env, else the majority owner of sealed records", async () => {
  const { resolveOwner } = await import("../electron/rappid-species.mjs");
  const temporary = mkdtempSync(path.join(tmpdir(), "rappid-owner-"));
  for (const [dir, owner] of [["a", "kody-w"], ["b", "kody-w"], ["c", "local"]]) {
    writeRecord(temporary, dir, { rappid: `rappid:@${owner}/${dir}:ee` });
  }
  assert.equal(resolveOwner({ env: { RAPP_HOME: temporary } }), "kody-w");
  assert.equal(
    resolveOwner({ env: { RAPP_HOME: temporary, RAPPIDEX_OWNER: "override" } }),
    "override",
  );
  assert.equal(
    resolveOwner({ env: { RAPP_HOME: path.join(temporary, "empty") } }),
    null,
  );
});

test("concurrent hatches of one anchor share a single rite", async () => {
  const temporary = mkdtempSync(path.join(tmpdir(), "rappid-race-"));
  const rappHome = path.join(temporary, "rapp-home");
  const engineDir = path.join(temporary, "engine");
  mkdirSync(path.join(engineDir, "species"), { recursive: true });
  const sha = anchorSha(rappidAnchor("twin", "racer"));
  const stub = `#!/usr/bin/env python3
import json, os, sys, time
time.sleep(0.3)
with open(os.path.join(os.environ["RAPP_HOME"], "runs.log"), "a") as f:
    f.write("run\\n")
home = os.path.join(os.environ["RAPP_HOME"], "rappids", "brainstem-racer")
os.makedirs(home, exist_ok=True)
json.dump({"rappid": "rappid:@test/brainstem-racer:ff", "species": "brainstem",
           "genome_id": "aaaabbbbcccc",
           "birth": {"seal": "s" * 64, "anchor": {"sha256": "__SHA__"}}},
          open(os.path.join(home, "rappid.json"), "w"))
`.replace("__SHA__", sha);
  const script = path.join(engineDir, "species", "rappidex.py");
  mkdirSync(rappHome, { recursive: true });
  writeFileSync(script, stub);
  chmodSync(script, 0o755);
  const previous = process.env.RAPP_HOME;
  process.env.RAPP_HOME = rappHome;
  try {
    const engine = { dir: engineDir, script };
    const [first, second] = await Promise.all([
      hatchCitizen({ engine, kind: "twin", id: "racer", title: "Racer" }),
      hatchCitizen({ engine, kind: "twin", id: "racer", title: "Racer" }),
    ]);
    assert.equal(first.ok, true);
    assert.equal(second.ok, true);
    assert.equal(first.record.genome_id, second.record.genome_id);
    const runs = readFileSync(path.join(rappHome, "runs.log"), "utf8").trim().split("\n");
    assert.equal(runs.length, 1);   // one rite, not two
  } finally {
    if (previous === undefined) delete process.env.RAPP_HOME;
    else process.env.RAPP_HOME = previous;
  }
});

test("mute is one device-wide flag shared with the engine, env-overridable", () => {
  const rappHome = mkdtempSync(path.join(tmpdir(), "rappid-mute-"));
  const env = { RAPP_HOME: rappHome };
  assert.equal(muteFlagPath({ env }), path.join(rappHome, "mute"));
  assert.equal(criesMuted({ env }), false);
  assert.equal(setCriesMuted(true, { env }), true);
  assert.equal(criesMuted({ env }), true);                       // flag written
  assert.equal(setCriesMuted(false, { env }), false);
  assert.equal(criesMuted({ env }), false);                      // flag removed
  assert.equal(setCriesMuted(false, { env }), false);            // idempotent off
  assert.equal(criesMuted({ env: { ...env, RAPPID_MUTE: "1" } }), true);
  assert.equal(criesMuted({ env: { ...env, RAPPID_MUTE: "0" } }), false);
  assert.equal(criesMuted({ env: { ...env, RAPPID_MUTE: "" } }), false);
});
