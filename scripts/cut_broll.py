#!/usr/bin/env python3
"""Cut the b-roll act out of the professional recordings, tagged by industry.

Act 2 of every AIBAST recording is industry b-roll — a plant floor, a trading
desk, a clinical workstation. That footage is licensed for this catalog and is
the single hardest part of a demo film to fake, so a generated film for an
agent that has no recording of its own reuses the b-roll from a recording in
the SAME industry. Nothing else is borrowed: the framing, the overview card,
the walkthrough and the close are all generated from that agent's own data.

Measured from the reference, not assumed: act 2 runs 5s–22s, and the internal
cuts in `#1-Product Line Optimization Agent.mp4` fall at 11.9s, 16.6s and 19.2s.
The window taken here is 5.5s–20.5s, which sits inside the act on every
recording checked.

Audio is dropped. The clip carries the generated narration, not the original's.

Output: media/broll/<industry>/<slug>.mp4  + media/broll/index.json

Usage:
    python3 scripts/cut_broll.py --source ~/Desktop/aibast_bible
    python3 scripts/cut_broll.py --source ... --industry manufacturing
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_ROOT = REPO_ROOT / "media" / "broll"
ONEPAGERS = REPO_ROOT / "data" / "onepagers.json"

# The b-roll window, measured from the shipped recordings.
BROLL_START = 5.5
BROLL_LENGTH = 15.0

# Industry names in the catalog collapse to these buckets, which are what a
# generated film matches on.
BUCKETS = {
    "manufacturing": ["manufacturing", "industrial", "automotive", "aerospace"],
    "financial_services": ["financial", "banking", "insurance", "capital", "wealth"],
    "healthcare": ["health", "life sciences", "pharma", "clinical", "patient"],
    "retail": ["retail", "cpg", "consumer", "commerce", "store"],
    "professional_services": ["professional services", "consulting", "legal", "advisory"],
    "energy": ["energy", "utilities", "oil", "power", "sustainability"],
    "public_sector": ["public", "government", "education", "nonprofit"],
    "cross_industry": ["cross-industry", "cross industry", "any", "general"],
}


def bucket_for(industries) -> str:
    hay = " ".join(industries).lower()
    for bucket, words in BUCKETS.items():
        if any(w in hay for w in words):
            return bucket
    return "cross_industry"


def slugify(name: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", name.lower())).strip("-")


def video_slug(filename: str) -> str:
    stem = Path(filename).stem.lstrip("#")
    return slugify(re.sub(r"^[0-9]+(-[0-9]+)?-", "", stem))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", default="~/Desktop/aibast_bible")
    ap.add_argument("--industry", help="only cut this bucket")
    ap.add_argument("--per-industry", type=int, default=3,
                    help="how many clips to keep per bucket")
    args = ap.parse_args()

    source = Path(args.source).expanduser()
    videos = source / "videos"
    if not videos.is_dir():
        raise SystemExit(f"no recordings under {videos}")

    industries_by_slug = {}
    if ONEPAGERS.is_file():
        for s in json.loads(ONEPAGERS.read_text(encoding="utf-8"))["onepagers"]:
            industries_by_slug[slugify(s["display_name"])] = s.get("industries") or []
            industries_by_slug[s["slug"]] = s.get("industries") or []

    by_bucket: dict[str, list] = {}
    for path in sorted(videos.glob("*.mp4")):
        slug = video_slug(path.name)
        inds = industries_by_slug.get(slug, [])
        bucket = bucket_for(inds) if inds else "cross_industry"
        by_bucket.setdefault(bucket, []).append((slug, path, inds))

    index, cut, skipped = [], 0, 0
    for bucket, items in sorted(by_bucket.items()):
        if args.industry and bucket != args.industry:
            continue
        for slug, path, inds in items[:args.per_industry]:
            out = OUT_ROOT / bucket / f"{slug}.mp4"
            out.parent.mkdir(parents=True, exist_ok=True)
            if not out.is_file():
                rc = subprocess.run([
                    "ffmpeg", "-v", "error", "-y",
                    "-ss", str(BROLL_START), "-i", str(path),
                    "-t", str(BROLL_LENGTH),
                    "-an",                         # the film carries its own narration
                    "-vf", "scale=1920:-2,fps=30",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out),
                ], capture_output=True)
                if rc.returncode != 0:
                    print(f"  FAILED {slug}: {rc.stderr.decode()[:120]}", file=sys.stderr)
                    skipped += 1
                    continue
                cut += 1
            index.append({
                "slug": slug, "industry_bucket": bucket, "industries": inds,
                "path": out.relative_to(REPO_ROOT).as_posix(),
                "seconds": BROLL_LENGTH,
                "size_mb": round(out.stat().st_size / 1048576, 2),
                "from_recording": path.name,
            })

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "index.json").write_text(json.dumps({
        "schema": "aibast-broll/1.0",
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window": {"start": BROLL_START, "length": BROLL_LENGTH,
                   "note": "measured from act 2 of the shipped recordings"},
        "licence_note": ("Footage from the AIBAST recordings, reused only within "
                         "this catalog and only for the industry it was shot for. "
                         "Audio is stripped — a generated film carries its own "
                         "narration."),
        "count": len(index),
        "buckets": sorted({i["industry_bucket"] for i in index}),
        "clips": index,
    }, indent=2) + "\n", encoding="utf-8")

    total = sum(i["size_mb"] for i in index)
    print(f"[broll] {len(index)} clip(s) across "
          f"{len({i['industry_bucket'] for i in index})} industries "
          f"({cut} newly cut, {skipped} failed) · {total:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
