#!/usr/bin/env python3
"""Harvest the real brand marks out of the Agent overview card.

I drew these by hand twice and both times they read as approximations, because
they were. The marks exist in the corpus at full resolution; the only work is
cutting them out cleanly.

Two things make the difference between a cut-out and an asset:

  * Find the mark by its BOUNDING BOX, not a hand-typed rectangle. Each search
    region is generous; the exact crop is wherever the non-background pixels
    actually are.
  * Key the bed out by UNPREMULTIPLYING rather than thresholding alpha. A
    partially transparent edge pixel still contains the background it sat on,
    so C = (P - bg(1-a)) / a. Skip that and every mark keeps a dark halo, which
    is exactly what survives a projector and reads as cheap.

Method and measured bed values follow RAPPtranscript2Prototype's
director/key_assets.py, which had already solved this.

Output: media/jewels/*.png + index.json

Usage:
    python3 scripts/harvest_jewels.py
    python3 scripts/harvest_jewels.py --frame path/to/overview.png
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / "media" / "jewels"
SOURCE = Path.home() / "Desktop" / "aibast_bible" / "videos"
DEFAULT_RECORDING = "#3-Customer Onboarding Agent.mp4"
DEFAULT_AT = 34.0

# Measured, not guessed: the card bed and the panel fill it sits on.
BED = (7, 15, 38)
PANEL = (26, 29, 63)

# Generous search regions in the 1920x1080 frame; the crop is the bounding box
# of whatever is actually in them.
REGIONS = {
    "copilot":       {"box": (580, 80, 730, 200), "bg": BED,
                      "match": ["copilot", "brainstem", "m365 copilot"]},
    "ic-sources":    {"box": (130, 330, 225, 415), "bg": PANEL, "match": []},
    "ic-flow":       {"box": (735, 330, 830, 415), "bg": PANEL, "match": []},
    "ic-actions":    {"box": (1340, 330, 1440, 415), "bg": PANEL, "match": []},
    "dynamics-365":  {"box": (250, 795, 360, 900), "bg": PANEL,
                      "match": ["dynamics", "d365", "erp", "crm", "ccaas"]},
    "sharepoint":    {"box": (360, 800, 470, 895), "bg": PANEL,
                      "match": ["sharepoint", "onedrive"]},
    "teams":         {"box": (910, 810, 1025, 895), "bg": PANEL,
                      "match": ["teams"]},
    "chevron":       {"box": (620, 500, 722, 670), "bg": BED, "match": []},
}

SOFT = 26.0   # distance at which a pixel is fully opaque
FLOOR = 8.0   # distance below which a pixel is pure background


def harvest(frame, name, spec):
    import numpy as np
    from PIL import Image

    x0, y0, x1, y1 = spec["box"]
    crop = np.array(frame.crop((x0, y0, x1, y1)).convert("RGB")).astype(float)
    bg = np.array(spec["bg"], dtype=float)

    dist = np.sqrt(((crop - bg) ** 2).sum(axis=2))
    alpha = np.clip((dist - FLOOR) / (SOFT - FLOOR), 0.0, 1.0)
    if alpha.max() < 0.35:
        return None, "nothing found in that region"

    ys, xs = np.where(alpha > 0.30)
    ty0, ty1 = max(0, ys.min() - 2), min(alpha.shape[0], ys.max() + 3)
    tx0, tx1 = max(0, xs.min() - 2), min(alpha.shape[1], xs.max() + 3)
    crop, alpha = crop[ty0:ty1, tx0:tx1], alpha[ty0:ty1, tx0:tx1]

    # Unpremultiply the bed out of every partially transparent pixel.
    a = alpha[..., None]
    with np.errstate(divide="ignore", invalid="ignore"):
        colour = np.where(a > 0.02, (crop - bg * (1 - a)) / np.maximum(a, 1e-6), crop)
    colour = np.clip(colour, 0, 255)

    rgba = np.dstack([colour, alpha * 255]).astype("uint8")
    img = Image.fromarray(rgba, "RGBA")
    dest = OUT / f"{name}.png"
    img.save(dest)
    return (img.width, img.height), None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--frame", help="an existing 1920x1080 overview frame")
    ap.add_argument("--at", type=float, default=DEFAULT_AT)
    args = ap.parse_args()

    try:
        from PIL import Image
        import numpy  # noqa: F401
    except ImportError:
        print("[jewels] needs pillow and numpy (PLAYWRIGHT_PYTHON has them)",
              file=sys.stderr)
        return 1

    tmp = None
    if args.frame:
        frame_path = Path(args.frame)
    else:
        rec = SOURCE / DEFAULT_RECORDING
        if not rec.is_file():
            print(f"[jewels] no recording at {rec}", file=sys.stderr)
            return 1
        tmp = Path(tempfile.mkdtemp()) / "ov.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(args.at),
                        "-i", str(rec), "-frames:v", "1", str(tmp)],
                       capture_output=True)
        frame_path = tmp
    if not frame_path.is_file():
        print("[jewels] could not obtain an overview frame", file=sys.stderr)
        return 1

    frame = Image.open(frame_path)
    if frame.size != (1920, 1080):
        print(f"[jewels] frame is {frame.size}, expected 1920x1080", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    jewels, failed = [], []
    for name, spec in REGIONS.items():
        size, err = harvest(frame, name, spec)
        if err:
            failed.append((name, err))
            print(f"  MISS {name}: {err}", file=sys.stderr)
            continue
        jewels.append({
            "id": name,
            "file": f"media/jewels/{name}.png",
            "raw_url": ("https://raw.githubusercontent.com/microsoft/"
                        f"aibast-agents-library/main/media/jewels/{name}.png"),
            "size": {"w": size[0], "h": size[1]},
            "match": spec["match"],
            "provenance": f"cropped from {DEFAULT_RECORDING} at {args.at}s, bed keyed out",
        })
        print(f"  {name:14} {size[0]:3}x{size[1]:<3} keyed")

    (OUT / "index.json").write_text(json.dumps({
        "schema": "aibast-jewels/2.0",
        "note": ("The real marks, cropped from the Agent overview card in the "
                 "corpus and keyed by unpremultiplying the bed out, so no mark "
                 "carries a halo. Header icons (ic-*) and the chevron have no "
                 "match terms — they are structural, one per panel."),
        "source": {"recording": DEFAULT_RECORDING, "at_seconds": args.at,
                   "bed": list(BED), "panel": list(PANEL)},
        "count": len(jewels),
        "jewels": jewels,
    }, indent=2) + "\n", encoding="utf-8")

    print(f"[jewels] harvested {len(jewels)}, {len(failed)} missed")
    if tmp:
        tmp.unlink(missing_ok=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
