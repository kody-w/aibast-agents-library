#!/usr/bin/env python3
"""Extract the film at 1 Hz and tile it into labelled contact sheets.

This exists because a green build is not a watched film. Two separate cuts
went out of this pipeline's ancestor with every gate passing and a defect
visible in the first frame anyone looked at: once a smeared, unreadable
interpolated cut, once a panel showing raw citation tokens. Neither is
detectable from a measurement. Both are obvious in a contact sheet.

Read the sheets. Every one of them, across the whole timeline.

Output: film/projects/<slug>/work/watch/sheet_NN.jpg
Usage:
    python3 film/kit/watch.py --project supplier-risk-watch
    python3 film/kit/watch.py --video any.mp4 --out film/.work/sheets
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_project, mono, require_tools  # noqa: E402

COLS, ROWS, TILE_W = 5, 5, 384


def sheets(video: Path, out_dir: Path, hz: float = 1.0) -> list:
    from PIL import Image, ImageDraw
    frames = out_dir / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    for old in list(frames.glob("*.jpg")) + list(out_dir.glob("sheet_*.jpg")):
        old.unlink()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vf",
                    f"fps={hz},scale=640:-1", "-q:v", "4",
                    str(frames / "f_%04d.jpg")], check=True)
    files = sorted(frames.glob("*.jpg"))
    tile_h = int(TILE_W * 9 / 16)
    font = mono(26)
    written = []
    per = COLS * ROWS
    for n in range(0, len(files), per):
        chunk = files[n:n + per]
        sheet = Image.new("RGB", (COLS * (TILE_W + 6) + 6, ROWS * (tile_h + 6) + 6),
                          (24, 24, 24))
        d = ImageDraw.Draw(sheet)
        for i, fp in enumerate(chunk):
            im = Image.open(fp).resize((TILE_W, tile_h))
            x = 6 + (i % COLS) * (TILE_W + 6)
            y = 6 + (i // COLS) * (tile_h + 6)
            sheet.paste(im, (x, y))
            secs = int((int(fp.stem.split("_")[1]) - 1) / hz)
            d.rectangle([x, y, x + 74, y + 30], fill=(0, 0, 0))
            d.text((x + 5, y + 1), f"{secs}s", font=font, fill=(255, 230, 0))
        dst = out_dir / f"sheet_{n // per:02d}.jpg"
        sheet.save(dst, quality=88)
        written.append(dst)
        print(f"[OK] {dst}  ({len(chunk)} frames)")
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project")
    ap.add_argument("--video", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--hz", type=float, default=1.0)
    args = ap.parse_args()
    require_tools()
    if args.project:
        project = load_project(args.project)
        video = project["_dist"] / project["output"]
        out = args.out or project["_work"] / "watch"
    elif args.video:
        video = args.video
        out = args.out or video.parent / "watch"
    else:
        raise SystemExit("give --project or --video")
    out.mkdir(parents=True, exist_ok=True)
    made = sheets(video, out, args.hz)
    print(f"[OK] {len(made)} sheet(s) - now read them")
    return 0


if __name__ == "__main__":
    sys.exit(main())
