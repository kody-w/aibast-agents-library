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
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path.home() / "Desktop" / "aibast_bible" / "videos"
OUT_DIR = REPO_ROOT / "media" / "videos"

# Measured from the six that already shipped, not picked.
WIDTH, HEIGHT = 960, 540
V_BITRATE = "110k"
A_BITRATE = "80k"
MAX_MB = 8.0          # a demo that lands far over this is a mistake, not a demo


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


def transcode(src: Path, dest: Path) -> bool:
    """Two-pass, because a demo is watched and a single pass wastes the budget.

    At this bitrate the difference is visible: single-pass spends it on the
    b-roll and starves the screen-recording act, which is the act with the text
    on it.
    """
    log = dest.with_suffix(".2pass")
    common = [
        "-vf", f"scale={WIDTH}:{HEIGHT}:flags=lanczos",
        "-c:v", "libx264", "-preset", "slow", "-b:v", V_BITRATE,
        "-pix_fmt", "yuv420p", "-g", "60",
    ]
    p1 = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), *common,
                         "-pass", "1", "-passlogfile", str(log), "-an",
                         "-f", "mp4", "/dev/null"], capture_output=True)
    if p1.returncode != 0:
        print(f"    pass 1 failed: {p1.stderr.decode()[-200:]}", file=sys.stderr)
        return False
    p2 = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), *common,
                         "-pass", "2", "-passlogfile", str(log),
                         "-c:a", "aac", "-b:a", A_BITRATE, "-ar", "44100",
                         "-ac", "2", "-movflags", "+faststart", str(dest)],
                        capture_output=True)
    for f in log.parent.glob(log.name + "*"):
        f.unlink(missing_ok=True)
    if p2.returncode != 0:
        print(f"    pass 2 failed: {p2.stderr.decode()[-200:]}", file=sys.stderr)
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

    for f in files:
        slug = slugify(f.name)
        dest = OUT_DIR / f"{slug}.mp4"
        src_dur = duration(f)
        if dest.is_file() and not args.force:
            if abs(duration(dest) - src_dur) < 0.5:
                skipped += 1
                total_mb += dest.stat().st_size / 1048576
                continue
        print(f"  {slug[:44]:46} {src_dur:6.1f}s", end="", flush=True)
        if not transcode(f, dest):
            failed.append(slug)
            print("  FAILED")
            continue
        mb = dest.stat().st_size / 1048576
        total_mb += mb
        done += 1
        flag = "  OVERSIZE" if mb > MAX_MB else ""
        print(f"  ->  {mb:5.2f} MB{flag}")

    print(f"[demos] {done} encoded, {skipped} already current, "
          f"{len(failed)} failed · {total_mb:.0f} MB hosted in total")
    if failed:
        print(f"[demos] failed: {', '.join(failed)}", file=sys.stderr)
    print("[demos] now run: python3 scripts/ingest_onepagers.py")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
