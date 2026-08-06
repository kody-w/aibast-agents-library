#!/usr/bin/env python3
"""Transcode every extracted demo recording into the repo, so all of them play.

The solutions catalog said "48 one-pagers, 7 demos hosted". The other 41
recordings were sitting on a desktop. Nothing was wrong with them — nobody had
transcoded them, because the first six were done by hand and there was no step
that did the rest. A catalog that promises the recording is "playable here
rather than behind a request for access" and then withholds forty of them is
worse than one that never made the promise.

The profile is not chosen, it is read off the six that already shipped:
960x540, H.264, a low target bitrate, AAC audio. Matching them matters — a
catalog where six demos are crisp and forty-two are soft looks unfinished in a
different way.

Skips anything already present and identical in duration, so a rerun is cheap.

Output: media/videos/<slug>.mp4

Usage:
    python3 scripts/host_demos.py
    python3 scripts/host_demos.py --force        # re-encode everything
    python3 scripts/host_demos.py --only account
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path.home() / "Desktop" / "aibast_bible" / "videos"
OUT_DIR = REPO_ROOT / "media" / "videos"

# QUALITY-TARGETED, not bitrate-targeted. The first version of this matched the
# six files that had already shipped: 960x540 at a fixed 110 kbps. The masters
# are 1920x1080 at 5.6 Mbps, so that was a fiftyfold reduction, and the result
# looked soft on every card. No amount of buffering fixes a soft encode.
#
# These recordings are graphics and screen capture — large flat areas, which
# CRF compresses extremely well. Measured on a real file: 1080p at CRF 22 is
# 10.9 MB and 550 kbps; 720p at CRF 21 is 7.0 MB. Full source resolution at
# five times the bitrate costs three times the bytes, and the bytes live on a
# branch that never enters an install clone.
LADDER = [
    ("1080p", 1920, 1080, 22),   # source resolution, the default
    ("720p", 1280, 720, 21),     # the lighter rung for a slow connection
]
A_BITRATE = "128k"
MAX_MB = 24.0         # a demo far over this is a mistake, not a demo


def slugify(name: str) -> str:
    stem = re.sub(r"^[#0-9]+(-[0-9]+)?-", "", Path(name).stem.lstrip("#"))
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", stem.lower())).strip("-")


def duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def transcode(src: Path, dest: Path, w: int, h: int, crf: int) -> bool:
    """Single pass at a constant quality target.

    Two-pass exists to spend a fixed bitrate well. There is no fixed bitrate
    here: CRF asks for a quality and spends whatever that costs, which is the
    right instrument when the content varies from flat graphics to b-roll
    within one file. `faststart` puts the moov atom first so the player can
    begin without fetching the whole file.
    """
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(src),
         "-vf", f"scale={w}:{h}:flags=lanczos",
         "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
         "-pix_fmt", "yuv420p", "-g", "60",
         "-c:a", "aac", "-b:a", A_BITRATE, "-ar", "48000", "-ac", "2",
         "-movflags", "+faststart", str(dest)], capture_output=True)
    if r.returncode != 0:
        print(f"    encode failed: {r.stderr.decode()[-200:]}", file=sys.stderr)
        return False
    return dest.is_file()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if not SOURCE.is_dir():
        print(f"[demos] no recordings at {SOURCE}", file=sys.stderr)
        return 1

    files = sorted(SOURCE.glob("*.mp4"))
    if args.only:
        files = [f for f in files if args.only.lower() in f.name.lower()]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    done, skipped, failed, total_mb = 0, 0, [], 0.0
    manifest = {}

    for f in files:
        slug = slugify(f.name)
        src_dur = duration(f)
        print(f"  {slug[:40]:42} {src_dur:6.1f}s", flush=True)
        rungs = []
        for label, w, h, crf in LADDER:
            # The top rung keeps the plain path so existing links stay valid;
            # lower rungs sit in their own directory.
            dest = (OUT_DIR / f"{slug}.mp4" if label == LADDER[0][0]
                    else OUT_DIR / label / f"{slug}.mp4")
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.is_file() and not args.force and abs(duration(dest) - src_dur) < 0.5:
                skipped += 1
            elif not transcode(f, dest, w, h, crf):
                failed.append(f"{slug}/{label}")
                continue
            else:
                done += 1
            mb = dest.stat().st_size / 1048576
            total_mb += mb
            rungs.append({"label": label, "height": h,
                          "path": f"media/videos/{dest.relative_to(OUT_DIR)}".replace("\\", "/"),
                          "size_mb": round(mb, 2)})
            print(f"      {label:6} {mb:6.2f} MB" + ("  OVERSIZE" if mb > MAX_MB else ""))
        if rungs:
            manifest[f"media/videos/{slug}.mp4"] = rungs

    # The renditions manifest the player reads to offer a resolution choice.
    (OUT_DIR.parent / "renditions.json").write_text(json.dumps({
        "schema": "rapp-media-renditions/1.0",
        "note": ("Quality-targeted encodes from the 1920x1080 masters. The "
                 "first rung is the default and keeps the original path so "
                 "existing links stay valid."),
        "videos": manifest,
    }, indent=2) + "\n", encoding="utf-8")

    print(f"[demos] {done} encoded, {skipped} already current, "
          f"{len(failed)} failed · {total_mb:.0f} MB hosted in total")
    if failed:
        print(f"[demos] failed: {', '.join(failed)}", file=sys.stderr)
    print("[demos] now run: python3 scripts/ingest_onepagers.py")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
