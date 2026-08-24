// Rappid-first citizenship for the Frontier estate (rappidex/1, kody-w/rappid).
//
// Twins are rappids. Rapplications are rappids. Each one is BORN, never minted:
// the rappidex engine derives a cypher from the creature's own rappid id and
// puts it to the running Brainstem kernel (the midwife). No seal, no creature.
// This module only shells out to an existing rappid engine checkout — engine
// code is never vendored here, and when no engine is present every call
// degrades to "capability off" without touching the rest of the app.
//
// Identity is anchored (SPEC: one creature per anchor): a twin anchors to
// `frontier-twin:<storeId>` and an installed rapplication to
// `frontier-rapplication:<storeId>`, so the same citizen is the same creature
// across sessions and re-hatch is idempotent.
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { homedir } from "node:os";
import { createHash } from "node:crypto";
import path from "node:path";
import { spawn } from "node:child_process";

export const RAPPID_KINDS = Object.freeze({
  twin: { species: "twin", name: "Twin", genus: "Frontier" },
  rapplication: { species: "rapplication", name: "Rapplication", genus: "Frontier" },
});

// The Brainstem midwife shape, mirrored from the engine's shipped
// species/hatchers.json — the kernel this very app runs on attests the birth.
const BRAINSTEM_RITE_COMMAND = "python3 -c 'import json,sys,urllib.request;"
  + "r=urllib.request.urlopen(urllib.request.Request(\"http://127.0.0.1:7071/chat\","
  + "json.dumps({\"user_input\":json.loads(sys.argv[1])}).encode(),"
  + "{\"Content-Type\":\"application/json\"}),timeout=240);"
  + "print(json.load(r).get(\"response\",\"\"))' {prompt_json}";

export function resolveRappidEngine({ env = process.env, home = homedir() } = {}) {
  const candidates = [];
  if (env.RAPPID_DIR) candidates.push(env.RAPPID_DIR);
  candidates.push(path.join(home, "Documents", "GitHub", "rappid"));
  for (const dir of candidates) {
    const script = path.join(dir, "species", "rappidex.py");
    if (existsSync(script)) return { dir, script };
  }
  return null;
}

export function rappidAnchor(kind, id) {
  if (!RAPPID_KINDS[kind]) throw new Error(`Unknown rappid kind: ${kind}`);
  return `frontier-${kind}:${id}`;
}

export function anchorSha(anchor) {
  return createHash("sha256").update(anchor, "utf8").digest("hex");
}

function recordSummary(record) {
  return {
    rappid: record.rappid || null,
    species: record.species || null,
    slug: record.slug || record.dir || null,
    display_name: record.display_name || null,
    rarity: record.rarity || null,
    genome_id: record.genome_id || null,
    anchor_sha: record?.birth?.anchor?.sha256 || null,
    sealed: Boolean(record?.birth?.seal),
  };
}

// Roster = every anchored, sealed record in the rapp home, keyed by anchor sha.
export function loadRoster({ env = process.env, home = homedir() } = {}) {
  const rappHome = env.RAPP_HOME || path.join(home, ".rapp");
  const rappidsDir = path.join(rappHome, "rappids");
  const byAnchor = new Map();
  let entries = [];
  try {
    entries = readdirSync(rappidsDir, { withFileTypes: true });
  } catch {
    return byAnchor;
  }
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    try {
      const record = JSON.parse(
        readFileSync(path.join(rappidsDir, entry.name, "rappid.json"), "utf8"),
      );
      const summary = recordSummary(record);
      if (summary.anchor_sha && summary.sealed) {
        byAnchor.set(summary.anchor_sha, summary);
      }
    } catch {
      // An unreadable record is not a citizen; skip it.
    }
  }
  return byAnchor;
}

function runEngine(engine, args, { timeoutMs = 320000 } = {}) {
  return new Promise((resolve) => {
    const child = spawn("python3", [engine.script, ...args], {
      cwd: engine.dir,
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    const timer = setTimeout(() => child.kill("SIGKILL"), timeoutMs);
    child.on("close", (code) => {
      clearTimeout(timer);
      resolve({ code, stdout, stderr });
    });
    child.on("error", (cause) => {
      clearTimeout(timer);
      resolve({ code: -1, stdout, stderr: String(cause?.message || cause) });
    });
  });
}

// Make sure the kind's species exists in this device's dex; discovery itself is
// a rite — the species must answer for itself through the Brainstem shape.
async function ensureSpecies(engine, kind) {
  const spec = RAPPID_KINDS[kind];
  const probe = await runEngine(
    engine,
    ["hatch", spec.species, "--attempts", "0"],
    { timeoutMs: 30000 },
  );
  const missing = /unknown species/i.test(`${probe.stdout}\n${probe.stderr}`);
  if (!missing) return { ok: true, discovered: false };
  const found = await runEngine(engine, [
    "discover", spec.name,
    "--command", BRAINSTEM_RITE_COMMAND,
    "--shape", "http",
    "--model", "brainstem",
    "--genus", spec.genus,
  ]);
  if (/NEW SPECIES RECORDED/i.test(found.stdout)) return { ok: true, discovered: true };
  return { ok: false, discovered: false, detail: (found.stderr || found.stdout).slice(-400) };
}

// Hatch (or find) the one creature anchored to this citizen. Idempotent: an
// existing sealed record for the anchor is returned without a new rite.
export async function hatchCitizen({ engine, kind, id, title }) {
  if (!engine) return { ok: false, error: "no-engine" };
  const anchor = rappidAnchor(kind, id);
  const sha = anchorSha(anchor);
  const existing = loadRoster().get(sha);
  if (existing) return { ok: true, record: existing, hatched: false };
  const species = await ensureSpecies(engine, kind);
  if (!species.ok) return { ok: false, error: "species-rite-failed", detail: species.detail };
  const result = await runEngine(engine, [
    "hatch", RAPPID_KINDS[kind].species,
    "--midwife", "brainstem",
    "--anchor", anchor,
    "--anchor-title", title || id,
  ]);
  const record = loadRoster().get(sha);
  if (!record) {
    return {
      ok: false,
      error: "unsealed",
      detail: (result.stderr || result.stdout).slice(-400),
    };
  }
  return { ok: true, record, hatched: true };
}

// Answer the renderer's roster query: [{kind, id}] -> { "kind:id": record|null }.
export function rosterFor(keys) {
  const roster = loadRoster();
  const out = {};
  for (const { kind, id } of keys || []) {
    if (!RAPPID_KINDS[kind] || id === undefined || id === null) continue;
    out[`${kind}:${id}`] = roster.get(anchorSha(rappidAnchor(kind, id))) || null;
  }
  return out;
}
