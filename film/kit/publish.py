#!/usr/bin/env python3
"""Collect a batch of finished films into film/out/<batch>/ with a manifest.

`projects/<slug>/dist/` is where a build lands and it is an intermediate -
regenerated on every run, ignored by git. `film/out/<batch>/` is what is
finished, and the manifest beside it is the batch's own record: what was
built, from what source, how long it is, what it measures, and whether its
gates were green.

Nothing here promotes a film into `media/videos/`, which is what the site
serves. Every config carries `approval.required_before_publishing` and that
approval is a person reading the script, not a build step. A film in
`film/out/` is a draft with numbers attached.

Output: film/out/<batch>/<slug>.mp4 and film/out/<batch>/manifest.json
Usage:
    python3 film/kit/publish.py --batch library
    python3 film/kit/publish.py --batch fy27 --nobed
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import FILM, PROJECTS, REPO_ROOT, levels, probe_duration  # noqa: E402

OUT = FILM / "out"
SCHEMA = "aibast-showcase-film-batch/1.0"


def stereo_ok(mp4: Path) -> bool:
    err = subprocess.run(["ffmpeg", "-v", "info", "-i", str(mp4), "-af",
                          "pan=mono|c0=0.5*c0-0.5*c1,volumedetect", "-f", "null",
                          "-"], capture_output=True, text=True).stderr
    for line in err.splitlines():
        if "mean_volume" in line:
            return float(line.split("mean_volume:")[1].split("dB")[0]) > -70.0
    return False


def row(slug: str, dst_dir: Path, nobed: bool) -> dict | None:
    project = json.loads((PROJECTS / slug / "project.json").read_text())
    src = PROJECTS / slug / "dist" / project["output"]
    if not src.exists():
        print(f"[WARN] {slug}: not built")
        return None
    dst = dst_dir / project["output"]
    shutil.copy2(src, dst)
    if nobed:
        nb = src.with_name(src.stem + "_NOBED.mp4")
        if nb.exists():
            shutil.copy2(nb, dst_dir / nb.name)

    # Publish the provenance WITH the film. Thirty-two films were published
    # without it and every one failed `agent.py gate` on "no voice.json beside
    # the film" — correctly, because a published film that cannot prove which
    # voice spoke it cannot ship, and the batch manifest is not beside the file
    # when someone hands the .mp4 to a customer. Per-film names, because one
    # shared voice.json in a batch directory would attest to whichever film was
    # published last.
    for name in ("voice.json", "beatmap.json"):
        for origin in (PROJECTS / slug / "dist" / name,
                       PROJECTS / slug / "work" / name,
                       PROJECTS / slug / "work" / "vo" / name):
            if origin.exists():
                shutil.copy2(origin, dst.with_suffix("." + name))
                break

    beatmap = json.loads((PROJECTS / slug / "work" / "beatmap.json").read_text())
    gate = PROJECTS / slug / "work" / "gate.json"
    violations = json.loads(gate.read_text())["violations"] if gate.exists() else None
    vo = json.loads((PROJECTS / slug / "work" / "vo" / "manifest.json").read_text())

    slot_means = []
    for name, at, dur in beatmap["vo_marks"]:
        m, _ = levels(dst, at, at + dur)
        slot_means.append(m)
    gaps = []
    cover = sorted((at, at + d) for _, at, d in beatmap["vo_marks"])
    t = 0.0
    total = beatmap["total"]
    for a, b in cover:
        if a - t > 1.6 and t > 1.0:
            gaps.append(levels(dst, a + 0.5, b - 0.5)[0] if False else
                        levels(dst, t + 0.5, a - 0.5)[0])
        t = max(t, b)
    pm, pk = levels(dst)
    demo = sum(b["actual"] for b in beatmap["beats"] if b["kind"] == "demo")

    return {
        "slug": slug,
        "title": project["title"],
        "industry": project["kicker"].split(" - ")[0],
        "category": project.get("category"),
        "composed_from": project.get("composed_from"),
        "broll_bucket": project["broll_bucket"],
        "file": project["output"],
        "duration_s": round(probe_duration(dst), 2),
        "demo_share_pct": round(demo / total * 100, 1),
        "narration_engine": vo.get("engine"),
        "vo_slots": len(slot_means),
        "vo_slot_mean_db": [round(x, 1) for x in slot_means if x is not None],
        "vo_slot_range_db": [round(min(x for x in slot_means if x is not None), 1),
                             round(max(x for x in slot_means if x is not None), 1)],
        "bed_gap_mean_db": [round(x, 1) for x in gaps if x is not None],
        "programme_mean_db": round(pm, 1),
        "programme_peak_db": round(pk, 1),
        "stereo": stereo_ok(dst),
        "gates": "green" if violations == [] else
                 (f"{len(violations)} violation(s)" if violations else "not run"),
        "approval_required_before_publishing": True,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--batch", required=True)
    ap.add_argument("--nobed", action="store_true",
                    help="also copy the voice-only variants")
    args = ap.parse_args()

    dst_dir = OUT / args.batch
    dst_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for d in sorted(PROJECTS.iterdir()):
        f = d / "project.json"
        if not f.exists():
            continue
        if json.loads(f.read_text()).get("batch") != args.batch:
            continue
        r = row(d.name, dst_dir, args.nobed)
        if r:
            rows.append(r)
            print(f"[OK] {r['slug']:34s} {r['duration_s']:7.2f}s  "
                  f"demo {r['demo_share_pct']:4.1f}%  peak {r['programme_peak_db']:5.1f}  "
                  f"{r['gates']}")
    manifest = {
        "schema": SCHEMA,
        "batch": args.batch,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(rows),
        "status": "draft",
        "note": "Rendered drafts. Publishing any of these requires a human to "
                "read the script first - see film/README.md.",
        "films": rows,
    }
    (dst_dir / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"[OK] {len(rows)} film(s) -> "
          f"{(dst_dir / 'manifest.json').relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
