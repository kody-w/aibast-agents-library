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

// A twin or rapplication is not a species — it is a creature OF the AI that
// animates it. Everything Frontier hatches runs on the Brainstem kernel, so
// its citizens are brainstem-species rappids; the anchor (one creature per
// anchor) is what makes each twin/rapplication its OWN creature. A future
// host running citizens on a different AI passes that species instead.
export const RAPPID_KINDS = Object.freeze({
  twin: {},
  rapplication: {},
});
export const HOST_SPECIES = "brainstem";

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

// Hatch (or find) the one creature anchored to this citizen. Idempotent: an
// existing sealed record for the anchor is returned without a new rite. The
// species is the HOST AI running the citizen (brainstem here), so the species
// itself attests the birth — no stand-in midwife.
export async function hatchCitizen({ engine, kind, id, title, species = HOST_SPECIES }) {
  if (!engine) return { ok: false, error: "no-engine" };
  if (!RAPPID_KINDS[kind]) throw new Error(`Unknown rappid kind: ${kind}`);
  const anchor = rappidAnchor(kind, id);
  const sha = anchorSha(anchor);
  const existing = loadRoster().get(sha);
  if (existing) return { ok: true, record: existing, hatched: false };
  const result = await runEngine(engine, [
    "hatch", species,
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
