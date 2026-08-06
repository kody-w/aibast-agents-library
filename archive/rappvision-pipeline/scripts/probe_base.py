#!/usr/bin/env python3
"""Measure every professional recording's act structure, so nobody hand-times it.

Each recording is the same five-act film, but the exact seconds differ per cut.
Hand-calibrating one and reusing its numbers is what put our title lozenge on
screen 2.8s after theirs and 1.5s after theirs had gone.

So: detect the acts. Each has a signature that survives at thumbnail scale, and
each is measured rather than assumed:

  intro     near-white full frame (the Microsoft card)
  title     a saturated pink/violet block in the middle band (the lozenge)
  overview  very dark frame carrying saturated gradient panels
  screen    a large bright rectangle (the laptop display) on a dark surround
  close     dark frame with a gradient block and no bright display

The output is per-track windows the compositor reads directly, so a generated
film lands its overlays on the same frames the original used.

Output: media/plates/base-timings.json

Usage:
    python3 scripts/probe_base.py                 # every recording
    python3 scripts/probe_base.py --only account  # one
    python3 scripts/probe_base.py --step 0.2      # finer sampling
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path.home() / "Desktop" / "aibast_bible" / "videos"
OUT = REPO_ROOT / "media" / "plates" / "base-timings.json"

try:
    import numpy as np
    from PIL import Image
except ImportError:  # pragma: no cover - the probe needs them, the build does not
    np = None


def slugify(name: str) -> str:
    stem = re.sub(r"^[#0-9]+(-[0-9]+)?-", "", Path(name).stem.lstrip("#"))
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", stem.lower())).strip("-")


def duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def sample(path: Path, step: float, work: Path) -> list[tuple[float, dict]]:
    """One low-resolution frame every `step` seconds, reduced to five signals."""
    grid = work / "g.png"
    dur = duration(path)
    n = max(1, int(dur / step))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path),
                    "-vf", f"fps=1/{step},scale=160:90,tile={n}x1",
                    "-frames:v", "1", str(grid)], capture_output=True)
    if not grid.is_file():
        return []
    img = np.array(Image.open(grid).convert("RGB")).astype(int)
    out = []
    for i in range(n):
        f = img[:, i * 160:(i + 1) * 160]
        if f.shape[1] < 160:
            break
        r, g, b = f[..., 0], f[..., 1], f[..., 2]
        lum = f.mean(axis=2)
        mid = f[27:63]                      # the band a lozenge sits in
        mr, mg, mb = mid[..., 0], mid[..., 1], mid[..., 2]
        out.append((round(i * step, 2), {
            "white": float((lum > 225).mean()),
            "dark": float((lum < 60).mean()),
            "bright_block": float((lum > 200).mean()),
            "lozenge": float(((mr > 150) & (mb > 150) &
                              (mg < mr - 25) & (mg < mb - 15)).mean()),
            "gradient": float(((r > 120) & (b > 140) & (g < r - 20)).mean()),
        }))
    grid.unlink(missing_ok=True)
    return out


def span(frames, predicate, step) -> dict | None:
    """The longest continuous run where a signal holds."""
    best = cur = None
    for t, s in frames:
        if predicate(s):
            cur = [t, t] if cur is None else [cur[0], t]
        elif cur is not None:
            if best is None or (cur[1] - cur[0]) > (best[1] - best[0]):
                best = cur
            cur = None
    if cur is not None and (best is None or (cur[1] - cur[0]) > (best[1] - best[0])):
        best = cur
    if best is None:
        return None
    return {"start": round(best[0], 2), "end": round(best[1] + step, 2)}


def probe(path: Path, step: float) -> dict:
    with tempfile.TemporaryDirectory() as td:
        frames = sample(path, step, Path(td))
    if not frames:
        return {"error": "no frames"}

    dur = duration(path)

    def within(a, b):
        return [f for f in frames if a <= f[0] <= b]

    # The five acts always run in the same ORDER, so each is searched in its own
    # region. Without that the overview's gradient panels register as a lozenge
    # and the laptop's white display registers as the Microsoft card — both of
    # which happened before this constraint existed.
    acts = {}
    acts["intro"] = span(within(0, 12),
                         lambda s: s["white"] > 0.55 and s["lozenge"] < 0.05, step)
    acts["title"] = span(within(0, 15),
                         lambda s: s["lozenge"] > 0.10 and s["dark"] < 0.35, step)

    after_title = acts["title"]["end"] if acts["title"] else 8.0
    acts["overview"] = span(within(after_title, min(dur, after_title + 55)),
                            lambda s: s["dark"] > 0.35 and s["gradient"] > 0.06
                            and s["bright_block"] < 0.25, step)

    after_ov = acts["overview"]["end"] if acts["overview"] else after_title
    acts["screen"] = span(within(after_ov, dur),
                          lambda s: s["bright_block"] > 0.35, step)

    after_screen = acts["screen"]["end"] if acts["screen"] else dur - 20
    acts["close"] = span(within(after_screen, dur),
                         lambda s: s["dark"] > 0.45 and s["bright_block"] < 0.10, step)

    return {"seconds": round(dur, 2), "acts": acts}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", help="substring of the recording name")
    ap.add_argument("--step", type=float, default=0.25)
    args = ap.parse_args()

    if np is None:
        print("[probe] needs numpy and pillow "
              "(PLAYWRIGHT_PYTHON has them)", file=sys.stderr)
        return 1
    if not SOURCE.is_dir():
        print(f"[probe] no recordings at {SOURCE}", file=sys.stderr)
        return 1

    files = sorted(SOURCE.glob("*.mp4"))
    if args.only:
        files = [f for f in files if args.only.lower() in f.name.lower()]

    tracks, missing = {}, []
    for f in files:
        slug = slugify(f.name)
        result = probe(f, args.step)
        tracks[slug] = {**result, "recording": f.name}
        gaps = [k for k, v in (result.get("acts") or {}).items() if not v]
        if gaps:
            missing.append((slug, gaps))
        acts = result.get("acts", {})
        t = acts.get("title")
        print(f"  {slug[:38]:40} title "
              f"{(str(t['start'])+'-'+str(t['end'])) if t else 'not found':>12}"
              f"   undetected: {','.join(gaps) or 'none'}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "schema": "aibast-base-timings/1.0",
        "note": ("Act windows measured per recording, not assumed. Every cut is "
                 "the same five acts but the seconds differ, and reusing one "
                 "track's numbers on another lands the overlays on the wrong "
                 "frames. An act listed as null was not detected confidently — "
                 "it is reported rather than guessed."),
        "sample_step_seconds": args.step,
        "signals": {
            "intro": "near-white full frame (the Microsoft card)",
            "title": "saturated pink/violet block in the middle band",
            "overview": "dark frame carrying saturated gradient panels",
            "screen": "large bright rectangle (the laptop display)",
            "close": "last dark run with no bright display",
        },
        "count": len(tracks),
        "tracks": tracks,
    }, indent=2) + "\n", encoding="utf-8")

    print(f"[probe] measured {len(tracks)} recording(s) → "
          f"{OUT.relative_to(REPO_ROOT)}")
    if missing:
        print(f"[probe] {len(missing)} track(s) have an undetected act; "
              "those are reported as null rather than guessed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
