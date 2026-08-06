#!/usr/bin/env python3
"""Measure, per base recording, the exact geometry and timing of every box we replace.

Everything that went wrong in the composited films came from the same root
cause: the rects and windows were hand-set once in align.html and then reused.
A hand-set rect is a guess about someone else's cut, and the cost of the guess
is measurable — 66 pixels of the reference's own Copilot nav rail leaking down
the left edge of our patch for 78 straight seconds, and a chat panel still on
screen 6.7 seconds after the shot it belonged to had cross-dissolved away.

So nothing here is set by hand. Each recording is measured:

  cuts       ffmpeg scene detection, so overlay windows can be clamped to the
             base's OWN shot boundaries instead of to a typed number
  title      the lozenge's bounding box PER FRAME. It is not static: it scales
             up as it fades out, and a fixed patch cannot cover a growing
             thing, which is why the reference's title ghosted around ours
             during the exit. The per-frame track is the fix.
  screen     the laptop display's bright rectangle, taken as the union across
             the act so no strip of their UI is left showing at any frame
  overview   the card act, clamped to the cuts either side of it

The output is consumed directly by render_film.py. If a track is not measured,
the renderer refuses rather than falling back to a guess.

Output: media/plates/base-geometry.json

Usage:
    python3 scripts/measure_base.py                 # every recording
    python3 scripts/measure_base.py --only account  # one
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path.home() / "Desktop" / "aibast_bible" / "videos"
OUT = REPO_ROOT / "media" / "plates" / "base-geometry.json"

try:
    import numpy as np
    from PIL import Image
except ImportError:  # pragma: no cover
    np = None

SCALE = 2          # measured at half resolution, reported at full
LOZENGE_STEP = 1 / 30.0


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


def cuts(path: Path) -> list[float]:
    """The base's own shot boundaries. Overlay windows are clamped to these."""
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(path),
                        "-vf", "scdet=threshold=12", "-f", "null", "-"],
                       capture_output=True, text=True)
    found = re.findall(r"lavfi\.scd\.time: ([0-9.]+)", r.stderr)
    return sorted({round(float(t), 3) for t in found})


def frames(path: Path, start: float, end: float, step: float, work: Path):
    """Decode a window to half-resolution frames, yielded as (t, array)."""
    d = work / f"s{start:.2f}"
    d.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start),
                    "-i", str(path), "-t", str(max(0.05, end - start)),
                    "-vf", f"fps=1/{step},scale=960:540",
                    str(d / "f%05d.png")], capture_output=True)
    for i, f in enumerate(sorted(d.glob("*.png"))):
        yield round(start + i * step, 3), np.array(Image.open(f).convert("RGB")).astype(int)


def bbox(mask) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if len(xs) < 40:
        return None
    return (int(xs.min()) * SCALE, int(ys.min()) * SCALE,
            (int(xs.max()) - int(xs.min()) + 1) * SCALE,
            (int(ys.max()) - int(ys.min()) + 1) * SCALE)


def lozenge_mask(f):
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    # The pill is warm pink into violet: red and blue both high, green pulled
    # well below them. That holds across the whole gradient and nothing else in
    # the b-roll satisfies it.
    return (r > 130) & (b > 130) & (g < r - 30) & (g < b - 20)


def display_bbox(f):
    """The laptop's app surface, found by PROFILE rather than by mask extent.

    A mask of "bright pixels" is useless here: the laptop sits on a near-white
    desk, so the bright mask covers the whole frame and reports a rect wider
    than the display. The app surface is instead the block of COLUMNS that are
    bright down most of their height, and the ROWS bright across most of their
    width — a shape only a large solid rectangle produces.
    """
    m = f.mean(axis=2) > 200
    cols, rows = m.mean(axis=0), m.mean(axis=1)
    xs, ys = np.where(cols > 0.5)[0], np.where(rows > 0.5)[0]
    if len(xs) < 20 or len(ys) < 20:
        return None
    return (int(xs.min()) * SCALE, int(ys.min()) * SCALE,
            (int(xs.max()) - int(xs.min()) + 1) * SCALE,
            (int(ys.max()) - int(ys.min()) + 1) * SCALE)


def measure_title(path, work, upto=16.0):
    """Per-frame lozenge geometry, including its scale-up exit."""
    track = []
    for t, f in frames(path, 0.0, upto, LOZENGE_STEP, work):
        m = lozenge_mask(f)
        if m.mean() < 0.010:
            if track:
                break            # the pill has gone; the act is over
            continue
        bb = bbox(m)
        if bb:
            track.append({"t": t, "x": bb[0], "y": bb[1], "w": bb[2], "h": bb[3]})
    if not track:
        return None
    # Steady size = the modal width, before the exit inflates it.
    widths = sorted(e["w"] for e in track)
    steady = widths[len(widths) // 2]
    env = {
        "x": min(e["x"] for e in track), "y": min(e["y"] for e in track),
        "w": max(e["x"] + e["w"] for e in track) - min(e["x"] for e in track),
        "h": max(e["y"] + e["h"] for e in track) - min(e["y"] for e in track),
    }
    return {"start": track[0]["t"], "end": round(track[-1]["t"] + LOZENGE_STEP, 3),
            "steady_width": steady, "envelope": env, "track": track}


def classify(path, work, dur):
    """One pass over the film, labelling every sampled frame by act signature.

    Scene detection alone is not enough: the professional cuts CROSS-DISSOLVE
    between the card and the laptop, and scdet reports no cut at a dissolve. A
    window built from cuts therefore ran our chat panel from 17s to the end of
    the film. Classifying each frame by what is actually on it finds the true
    act, and a half-dissolved frame satisfies neither signature — so the act
    boundaries land after the dissolve resolves, which is exactly where an
    overlay should start.
    """
    out = []
    for t, f in frames(path, 0.0, dur, 0.25, work):
        disp = display_bbox(f)
        big = bool(disp and disp[2] >= 900 and disp[3] >= 500)
        r, g, b = f[..., 0], f[..., 1], f[..., 2]
        dark = float((f.mean(axis=2) < 60).mean())
        grad = float(((r > 110) & (b > 130) & (g < r - 18)).mean())
        out.append({"t": t, "display": disp if big else None,
                    "card": (not big) and dark > 0.30 and grad > 0.04})
    return out


def longest_run(frames_, ok, step=0.25):
    best = cur = None
    for fr in frames_:
        if ok(fr):
            cur = [fr["t"], fr["t"]] if cur is None else [cur[0], fr["t"]]
        elif cur is not None:
            if best is None or (cur[1] - cur[0]) > (best[1] - best[0]):
                best = cur
            cur = None
    if cur is not None and (best is None or (cur[1] - cur[0]) > (best[1] - best[0])):
        best = cur
    return None if best is None else (round(best[0], 3), round(best[1] + step, 3))


def measure_screen(cls):
    """The laptop act, and the UNION of the display's extent across it.

    Union, not a sample: a strip of their UI showing on any single frame is the
    defect, so the patch must cover the widest the display ever gets.
    """
    run = longest_run(cls, lambda f: f["display"] is not None)
    if not run:
        return None
    inside = [f["display"] for f in cls if run[0] <= f["t"] < run[1] and f["display"]]
    x0 = min(d[0] for d in inside)
    y0 = min(d[1] for d in inside)
    x1 = max(d[0] + d[2] for d in inside)
    y1 = max(d[1] + d[3] for d in inside)
    return {"start": run[0], "end": run[1],
            "rect": {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}}


def measure_overview(cls, before):
    """The three-panel card act: the longest carded run before the laptop act."""
    return_run = longest_run([f for f in cls if f["t"] < before], lambda f: f["card"])
    if not return_run:
        return None
    return {"start": return_run[0], "end": return_run[1]}


def measure_audio(path: Path, dur: float) -> dict:
    """The base's own silent head and tail, and its integrated loudness.

    The professional films open and close on a Microsoft logo in silence. Ours
    ran a music bed under both, which is the first and last thing a viewer
    hears. Both are properties of the recording, so both are read off it.
    """
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(path), "-af",
                        "silencedetect=n=-40dB:d=0.5", "-f", "null", "-"],
                       capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: (-?[0-9.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r.stderr)]
    head = max([e for s, e in zip(starts, ends) if s < 0.35] or [0.0])
    tail = min([s for s in starts if s > dur - 6.0] or [dur])
    lr = subprocess.run(["ffmpeg", "-v", "info", "-i", str(path),
                         "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                        capture_output=True, text=True)
    m = re.search(r"I:\s+(-?[0-9.]+) LUFS", lr.stderr)
    return {"head_silent_until": round(head, 3),
            "tail_silent_from": round(tail, 3),
            "integrated_lufs": float(m.group(1)) if m else None}


def measure(path: Path) -> dict:
    dur = duration(path)
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        cl = cuts(path)
        title = measure_title(path, work)
        cls = classify(path, work, dur)
        screen = measure_screen(cls)
        overview = measure_overview(cls, screen["start"] if screen else dur)
    return {"seconds": round(dur, 3), "cuts": cl,
            "audio": measure_audio(path, dur),
            "title": title, "overview": overview, "screen": screen}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only")
    args = ap.parse_args()

    if np is None:
        print("[measure] needs numpy and pillow", file=sys.stderr)
        return 1
    if not SOURCE.is_dir():
        print(f"[measure] no recordings at {SOURCE}", file=sys.stderr)
        return 1

    files = sorted(SOURCE.glob("*.mp4"))
    if args.only:
        files = [f for f in files if args.only.lower() in f.name.lower()]

    existing = {}
    if OUT.is_file():
        existing = json.loads(OUT.read_text(encoding="utf-8")).get("tracks", {})

    tracks, incomplete = dict(existing), []
    for f in files:
        slug = slugify(f.name)
        m = measure(f)
        tracks[slug] = {**m, "recording": f.name}
        gaps = [k for k in ("title", "overview", "screen") if not m.get(k)]
        if gaps:
            incomplete.append(slug)
        t, s = m.get("title"), m.get("screen")
        tw = "MISS" if not t else "%.2f-%.2f" % (t["start"], t["end"])
        r = s["rect"] if s else None
        sw = "MISS" if not r else "%d,%d %dx%d" % (r["x"], r["y"], r["w"], r["h"])
        note = ("gaps: " + ",".join(gaps)) if gaps else ""
        print(f"  {slug[:34]:36} title {tw:>13}  screen {sw:>20}  {note}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "schema": "aibast-base-geometry/1.0",
        "note": ("Measured from each recording, never hand-set. The title entry "
                 "carries a PER-FRAME track because the reference lozenge scales "
                 "up as it fades and a fixed patch cannot cover a growing thing. "
                 "The screen rect is the UNION of the display's extent across "
                 "the act, so no strip of the reference UI shows on any frame. "
                 "Windows are the base's own scene cuts."),
        "count": len(tracks),
        "tracks": tracks,
    }, indent=2) + "\n", encoding="utf-8")

    print(f"[measure] {len(files)} measured → {OUT.relative_to(REPO_ROOT)}")
    if incomplete:
        print(f"[measure] incomplete: {', '.join(incomplete)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
