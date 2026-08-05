#!/usr/bin/env python3
"""RAPP Sentinel — the review runtime for a neighborhood of residents.

A **neighborhood** (``sentinel/NEIGHBORHOOD.json``) is data: a roster of
residents, each with one lens and one job. It is inert. This script is one
runtime that can wake it up, and it is deliberately not the only possible one —
anyone can pull the neighborhood out of this repository and run it themselves.

Two kinds of resident, one runner:

  * **deterministic** — has a ``module``. Runs here, under Python, with no AI
    and no network. Same input, same output, forever. This is what makes a run
    reproducible: a third party re-running it on the same commit gets the same
    digest or the run was not honest.
  * **interpretive** — has a ``prompt``. The runner does not answer these; it
    emits a *packet* containing the prompt and the exact source under review.
    Any model can execute the packet. Feed the answers back with ``--absorb``
    and they join the run with their model attribution attached.

Traceability is the product. Every run records the commit, the neighborhood
digest, the rubric version, the inputs digest, and which residents actually
answered — so a verdict can always be traced to what produced it, and a stale
verdict announces itself instead of quietly aging.

Machine review only. Nothing this script produces is a human opinion, and the
output is never merged with community ratings. See the neighborhood's
``separation`` block.

Usage:
    python3 scripts/sentinel.py run                       # whole library
    python3 scripts/sentinel.py run --agent art-generator # one submission
    python3 scripts/sentinel.py run --packets-only        # emit AI work, run nothing
    python3 scripts/sentinel.py absorb --run <id> --answers answers.json
    python3 scripts/sentinel.py verify --run <id>         # reproduce and compare
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SENTINEL_DIR = REPO_ROOT / "sentinel"
NEIGHBORHOOD = SENTINEL_DIR / "NEIGHBORHOOD.json"
RUNS_DIR = SENTINEL_DIR / "runs"
LATEST = SENTINEL_DIR / "latest.json"
AGENTS_ROOT = REPO_ROOT / "agents"
SKILLS_ROOT = REPO_ROOT / "skills"

SCHEMA = "rapp-sentinel-run/1.0"
sys.path.insert(0, str(Path(__file__).resolve().parent))


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def commit_sha() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip()[:12] if out.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def load_neighborhood() -> tuple[dict, str]:
    raw = NEIGHBORHOOD.read_text(encoding="utf-8")
    return json.loads(raw), digest(raw)


def subjects(only: str | None, subject_set: str = "all") -> list[Path]:
    """The files a resident reviews.

    An aggregated skill is held to the same standard as one we wrote — that is
    the point of aggregating it into the library rather than linking to it. The
    rubric differs because a skill fails differently, but the review, the
    thread, and the published finding are the same shape.
    """
    files: list[Path] = []
    if subject_set in ("agents", "all"):
        files += [p for p in sorted(AGENTS_ROOT.rglob("*.py")) if "__pycache__" not in p.parts]
    if subject_set in ("skills", "all") and SKILLS_ROOT.is_dir():
        files += sorted(SKILLS_ROOT.rglob("*.md"))
    return [p for p in files if only in p.stem] if only else files


def run_deterministic(resident: dict, paths: list[Path]) -> dict:
    """Wake a deterministic resident: import its module and call its reviewer."""
    mod = importlib.import_module(resident["module"])
    reviews = [mod.review_one(p) for p in paths]
    return {
        "resident": resident["id"],
        "kind": "deterministic",
        "subjects": resident.get("subjects", "agents"),
        "authority": resident.get("authority", "advisory"),
        "rubric_version": getattr(mod, "RUBRIC_VERSION", "unknown"),
        "answered_by": f"{resident['module']} (local, no model)",
        "results": {r["slug"]: r for r in reviews},
    }


def build_packet(resident: dict, paths: list[Path]) -> dict:
    """Emit the work an interpretive resident needs. Any model can execute it."""
    return {
        "schema": "rapp-sentinel-packet/1.0",
        "resident": resident["id"],
        "kind": "interpretive",
        "subjects": resident.get("subjects", "agents"),
        "authority": resident.get("authority", "advisory"),
        "lens": resident["lens"],
        "subject_slugs": [p.stem for p in paths],
        "instructions": (
            "Execute the prompt once per subject below. Return a JSON object mapping "
            "each subject's `slug` to that subject's answer object, exactly in the "
            "shape the prompt specifies. Add nothing else. Then hand the file to "
            "`sentinel.py absorb`."
        ),
        "prompt": resident["prompt"],
        "subjects_ref": "run.subjects",
    }


def subject_records(paths: list[Path]) -> list[dict]:
    """The subject list every packet shares — recorded once, not per resident."""
    return [
        {"slug": p.stem, "file": p.relative_to(REPO_ROOT).as_posix(),
         "source_digest": digest(p.read_text(encoding="utf-8", errors="replace")),
         "source_url": ("https://raw.githubusercontent.com/microsoft/"
                        f"aibast-agents-library/main/{p.relative_to(REPO_ROOT).as_posix()}")}
        for p in paths
    ]


def verdict_for(slug: str, findings: list[dict], policy: dict) -> str:
    blocking_defect, static_score = False, None
    for f in findings:
        res = (f.get("results") or {}).get(slug)
        if res is None:
            continue
        if f["kind"] == "deterministic":
            static_score = res.get("overall")
            if res.get("error_count"):
                blocking_defect = True
        elif f.get("authority") == "blocking":
            flagged = any(v is True for k, v in res.items()
                          if k in ("misrepresents", "irreversible_actions", "spends_money"))
            if flagged or res.get("irreversible_actions"):
                blocking_defect = True

    if blocking_defect or (static_score is not None and static_score < 60):
        return "changes-requested"
    if static_score is not None and static_score >= 85:
        return "approved"
    return "advisory-only"


def cmd_run(args) -> int:
    hood, hood_digest = load_neighborhood()
    paths = subjects(args.agent)
    if not paths:
        print(f"[sentinel] no agent matched {args.agent!r}", file=sys.stderr)
        return 1

    inputs_digest = digest("".join(
        p.relative_to(REPO_ROOT).as_posix() + digest(p.read_text(encoding="utf-8", errors="replace"))
        for p in paths))
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{inputs_digest[:8]}"

    findings, packets = [], []
    for resident in hood["residents"]:
        scoped = [p for p in paths
                  if p in set(subjects(args.agent, resident.get("subjects", "agents")))]
        if not scoped:
            continue
        if resident["kind"] == "deterministic" and not args.packets_only:
            findings.append(run_deterministic(resident, scoped))
        elif resident["kind"] == "interpretive":
            packets.append(build_packet(resident, scoped))

    run = {
        "schema": SCHEMA,
        "run_id": run_id,
        "started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "review_type": "machine",
        "neighborhood": {"name": hood["name"], "digest": hood_digest, "file": "sentinel/NEIGHBORHOOD.json"},
        "commit": commit_sha(),
        "inputs_digest": inputs_digest,
        "subject_count": len(paths),
        "subjects": subject_records(paths),
        "residents_awake": [f["resident"] for f in findings],
        "residents_pending": [p["resident"] for p in packets],
        "findings": findings,
        "packets": packets,
        "verdicts": {p.stem: verdict_for(p.stem, findings, hood.get("verdict_policy", {})) for p in paths},
        "separation_notice": hood["separation"]["rule"],
        "reproduce": (
            "python3 scripts/sentinel.py verify --run " + run_id +
            " — re-runs every deterministic resident on the recorded commit and "
            "compares digests. Interpretive answers carry their model attribution "
            "and are not expected to reproduce byte for byte."
        ),
    }

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out = RUNS_DIR / f"{run_id}.json"
    out.write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
    LATEST.write_text(json.dumps({
        "schema": "rapp-sentinel-latest/1.0",
        "run_id": run_id, "commit": run["commit"], "started": run["started"],
        "subject_count": run["subject_count"], "verdicts": run["verdicts"],
        "residents_awake": run["residents_awake"], "residents_pending": run["residents_pending"],
        "run_file": f"sentinel/runs/{run_id}.json",
    }, indent=2) + "\n", encoding="utf-8")

    tally: dict[str, int] = {}
    for v in run["verdicts"].values():
        tally[v] = tally.get(v, 0) + 1
    print(f"[sentinel] run {run_id} · {len(paths)} subjects · "
          + ", ".join(f"{k} {v}" for k, v in sorted(tally.items())))
    print(f"[sentinel] awake: {', '.join(run['residents_awake']) or 'none'}"
          f" · asleep (need a model): {', '.join(run['residents_pending']) or 'none'}")
    print(f"[sentinel] wrote {out.relative_to(REPO_ROOT)}")
    return 0


def cmd_absorb(args) -> int:
    """Fold an AI's answers into a recorded run, with attribution attached."""
    run_file = RUNS_DIR / f"{args.run}.json"
    if not run_file.is_file():
        print(f"[sentinel] no run {args.run}", file=sys.stderr)
        return 1
    run = json.loads(run_file.read_text(encoding="utf-8"))
    answers = json.loads(Path(args.answers).read_text(encoding="utf-8"))

    packet = next((p for p in run["packets"] if p["resident"] == args.resident), None)
    if packet is None:
        print(f"[sentinel] run has no pending resident {args.resident!r}", file=sys.stderr)
        return 1

    run["findings"].append({
        "resident": args.resident,
        "kind": "interpretive",
        "authority": packet["authority"],
        "answered_by": args.model,
        "answered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "results": answers,
    })
    run["packets"] = [p for p in run["packets"] if p["resident"] != args.resident]
    run["residents_awake"].append(args.resident)
    run["residents_pending"] = [p["resident"] for p in run["packets"]]

    hood, _ = load_neighborhood()
    run["verdicts"] = {slug: verdict_for(slug, run["findings"], hood.get("verdict_policy", {}))
                       for slug in run["verdicts"]}
    run_file.write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
    print(f"[sentinel] absorbed {args.resident} from {args.model} into {args.run}")
    return 0


def cmd_verify(args) -> int:
    """Re-run the deterministic residents and prove the recorded run reproduces."""
    run_file = RUNS_DIR / f"{args.run}.json"
    if not run_file.is_file():
        print(f"[sentinel] no run {args.run}", file=sys.stderr)
        return 1
    run = json.loads(run_file.read_text(encoding="utf-8"))
    hood, hood_digest = load_neighborhood()

    problems = []
    if hood_digest != run["neighborhood"]["digest"]:
        problems.append("the neighborhood changed since this run — its verdicts describe a different rubric")

    for finding in run["findings"]:
        if finding["kind"] != "deterministic":
            continue
        resident = next(r for r in hood["residents"] if r["id"] == finding["resident"])
        paths = [REPO_ROOT / rec["file"] for rec in finding["results"].values()]
        fresh = run_deterministic(resident, [p for p in paths if p.is_file()])
        for slug, was in finding["results"].items():
            now = fresh["results"].get(slug)
            if now is None:
                problems.append(f"{slug}: subject no longer exists")
            elif now.get("overall") != was.get("overall") or now.get("verdict") != was.get("verdict"):
                problems.append(
                    f"{slug}: was {was.get('verdict')}/{was.get('overall')}, "
                    f"now {now.get('verdict')}/{now.get('overall')}")

    if problems:
        print(f"[sentinel] run {args.run} does NOT reproduce against the working tree:")
        for p in problems[:20]:
            print(f"  - {p}")
        print("  (expected if the tree moved on; run it on the recorded commit to compare like for like)")
        return 1
    print(f"[sentinel] run {args.run} reproduces exactly: same neighborhood, same verdicts")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="wake the neighborhood over the library")
    r.add_argument("--agent", help="review one submission by file stem "
                   "(an agent .py or an aggregated skill .md)")
    r.add_argument("--packets-only", action="store_true", help="emit AI work without running local residents")
    r.set_defaults(fn=cmd_run)

    a = sub.add_parser("absorb", help="fold a model's answers into a recorded run")
    a.add_argument("--run", required=True)
    a.add_argument("--resident", required=True)
    a.add_argument("--answers", required=True, help="JSON file: {slug: answer}")
    a.add_argument("--model", required=True, help="what answered, recorded as attribution")
    a.set_defaults(fn=cmd_absorb)

    v = sub.add_parser("verify", help="reproduce a run and compare")
    v.add_argument("--run", required=True)
    v.set_defaults(fn=cmd_verify)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
