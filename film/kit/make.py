#!/usr/bin/env python3
"""Run one project through the whole pipeline, in the only order that works.

narrate first, because the beatmap is computed from the reads. plan second.
cards and screens third - they need the stage counts the plan settled. build
fourth. gate and watch last, and the watch step is not optional: a green gate
is not a watched film.

    narrate -> plan -> cards -> screens -> build -> gate -> watch

Output: film/projects/<slug>/dist/<slug>.mp4 and work/watch/sheet_NN.jpg
Usage:
    python3 film/kit/make.py --project supplier-risk-monitoring
    python3 film/kit/make.py --all --batch library
    python3 film/kit/make.py --project X --engine say --skip narrate
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import KIT, PROJECTS, REPO_ROOT  # noqa: E402

STAGES = ["narrate", "plan", "cards", "screens", "build", "gate", "watch"]


def run_stage(stage: str, slug: str, engine: str) -> tuple:
    cmd = ["python3", str(KIT / f"{stage}.py"), "--project", slug]
    if stage == "narrate":
        cmd += ["--engine", engine]
    if stage == "build":
        # Asks for the EXTRA voice-only file, nothing more. It was called
        # --nobed, which read as "build the film without a bed" and was written
        # into the handoff as a defect on that reading. The delivered mp4 has
        # always carried the bed at project.bed_db - measured -26.6 to -28.0 dB
        # in the gaps on the 2026-08-05 build, with this flag on.
        cmd += ["--voice-only"]
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    return proc, round(time.time() - t0, 1)


def make(slug: str, engine: str, skip: set, verbose: bool) -> dict:
    result = {"slug": slug, "stages": {}, "ok": True}
    for stage in STAGES:
        if stage in skip:
            result["stages"][stage] = "skipped"
            continue
        proc, secs = run_stage(stage, slug, engine)
        tail = (proc.stdout or proc.stderr).strip().splitlines()
        result["stages"][stage] = {"rc": proc.returncode, "seconds": secs,
                                   "tail": tail[-3:]}
        mark = "[OK]" if proc.returncode == 0 else "[WARN]"
        print(f"  {mark} {stage:8s} {secs:6.1f}s  "
              f"{tail[-1][:88] if tail else ''}")
        if verbose:
            for line in tail[-25:]:
                print("        " + line)
        # gate failing is a finding, not a crash - keep going so the sheets
        # still get written and the failure can be read alongside them.
        if proc.returncode != 0:
            result["ok"] = False
            if stage not in ("gate", "narrate", "plan"):
                print(proc.stdout[-2500:] or proc.stderr[-2500:])
                break
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project")
    ap.add_argument("--all", action="store_true", help="every project")
    ap.add_argument("--batch", help="with --all, only this batch")
    ap.add_argument("--engine", choices=("auto", "azure", "say"), default="auto")
    ap.add_argument("--skip", default="", help="comma-separated stage names")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    skip = {s for s in args.skip.split(",") if s}

    if args.all:
        slugs = []
        for d in sorted(PROJECTS.iterdir()):
            f = d / "project.json"
            if not f.exists():
                continue
            if args.batch and json.loads(f.read_text()).get("batch") != args.batch:
                continue
            slugs.append(d.name)
    elif args.project:
        slugs = [args.project]
    else:
        ap.print_help()
        return 1

    results = []
    for slug in slugs:
        print(f"\n=== {slug} ===")
        results.append(make(slug, args.engine, skip, args.verbose))
    bad = [r["slug"] for r in results if not r["ok"]]
    print(f"\n[OK] {len(results) - len(bad)}/{len(results)} clean")
    if bad:
        print(f"[WARN] needs attention: {', '.join(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
