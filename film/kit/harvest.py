#!/usr/bin/env python3
"""Derive b-roll and the grammar from the shipped recordings.

The recordings are produced pieces with a fixed grammar - logo card, business
b-roll, the Agent overview card, a device-framed demo, a gradient close - and
each segment type has its own colour signature at the frame border. Border,
not full frame: the overview card sits on a near-black bed but carries big
bright panels, so its average luma reads mid-grey while its border is flat
navy. Classifying the border separates the four cleanly.

Do not reach for `select='gt(scene,N)'`. The encodes carry no usable scene
metadata - every threshold tested returns zero matches on every recording.
Everything here is explicit frame differencing.

Two rules are burned in because breaking either one ruins the harvest:

  * The b-roll window opens at 7.0s, never 5.5s. The recording's own title
    lozenge is in the picture until about 6.5s, and cutting from 5.5s splices
    another agent's name into your film.
  * The window closes before the next card's heading begins to fade up over
    still-full-strength footage. That ghost-in changes no colour, no
    histogram and no edge energy, so every automatic purity test passes while
    the text is already legible. `--verify` renders the first, middle and last
    frame of every cut so it can be checked by eye, which is the only test
    that has ever caught it.

Output: film/assets/broll/<bucket>/*.mp4 and film/assets/broll/index.json
Usage:
    python3 film/kit/harvest.py --scan media/videos/ask-hr-agent.mp4
    python3 film/kit/harvest.py --cut ask-hr-agent --bucket cross_industry
    python3 film/kit/harvest.py --verify
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (BROLL, CORPUS, CORPUS_WEB, FPS, H, REPO_ROOT, VENC,  # noqa: E402
                    W, probe_duration, require_tools, run)

# Fallbacks only. The real in and out points are MEASURED per recording by
# title_clear() and card_in() below, because a fixed 7.0s in-point put another
# agent's title lozenge in the first frame of nine harvested clips. The
# lozenge clears anywhere between 6.1s and 7.4s across the corpus.
SAFE_IN = 7.6
SAFE_OUT = 21.0
TITLE_SAFETY = 0.35         # after the lozenge clears
CARD_SAFETY = 1.5           # before the next card starts ghosting in
MIN_SHOT = 2.2
MAX_SHOT = 5.6
CUT_THRESHOLD = 11.0        # mean abs luma diff at 96x54 that reads as a cut


def source(slug: str) -> Path:
    """Prefer the full-resolution corpus; fall back to the served transcodes.

    The 960x540 transcodes are fine for deriving timings and useless for
    cutting b-roll - a 1080p film built from them is visibly soft.
    """
    for root, note in ((CORPUS, "corpus"), (CORPUS_WEB, "served transcode")):
        p = root / f"{slug}.mp4"
        if p.exists():
            if note != "corpus":
                print(f"[WARN] {slug}: using the {note} at 960x540 - b-roll cut "
                      "from it will upscale. Populate film/corpus/videos for "
                      "full resolution.")
            return p
    raise SystemExit(f"no recording for {slug!r} in film/corpus/videos or "
                     f"media/videos")


def classify(frame) -> str:
    """logo-card / motion-graphic / demo / broll, from the border signature."""
    from PIL import ImageStat
    w, h = frame.size
    top = ImageStat.Stat(frame.crop((0, 0, w, max(1, int(h * 0.06)))))
    left = ImageStat.Stat(frame.crop((0, 0, max(1, int(w * 0.05)), h)))
    br, bg, bb = ((t + l) / 2 for t, l in zip(top.mean, left.mean))
    bsd = (sum(top.stddev) + sum(left.stddev)) / 6.0
    luma = 0.299 * br + 0.587 * bg + 0.114 * bb
    if bsd < 8.0 and luma > 200:
        return "logo-card"
    if bsd < 8.0 and luma < 60 and bb > br:
        return "motion-graphic"
    if bb > br * 1.5 and bb > bg * 1.5 and 30 < luma < 200:
        return "demo"
    return "broll"


def _lozenge_fraction(frame) -> float:
    """How much of the centre band is the magenta-to-violet title lozenge."""
    import colorsys
    w, h = frame.size
    c = frame.crop((int(w * .15), int(h * .33), int(w * .85), int(h * .67)))
    c = c.convert("RGB").resize((120, 45))
    hits = 0
    for r, g, b in list(c.getdata()):
        hue, sat, val = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if sat > 0.30 and val > 0.35 and 0.72 < hue < 0.95:
            hits += 1
    return hits / (120 * 45)


def title_clear(video: Path, work: Path) -> float:
    """The second the recording's own title lozenge leaves the picture.

    This must be measured, never assumed. The lozenge carries the name of the
    agent the recording was made for, and one frame of it in your b-roll puts
    another product's title in your film. It reads as a clean on/off - the
    magenta fraction goes from 0.3-0.7 to 0.00 within a tenth of a second.
    """
    from PIL import Image
    d = work / "loz"
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("*.jpg"):
        old.unlink()
    # One extraction, not one per sample. Ten frames a second from 4s to 12s.
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "4", "-to", "12",
                    "-i", str(video), "-vf", "fps=10,scale=320:-1", "-q:v", "5",
                    str(d / "l%04d.jpg")], check=True)
    last_seen = None
    for f in sorted(d.glob("*.jpg")):
        t = 4.0 + (int(f.stem[1:]) - 1) / 10.0
        if _lozenge_fraction(Image.open(f)) > 0.06:
            last_seen = t
        elif last_seen is not None:
            break
    if last_seen is None:
        return SAFE_IN
    return round(last_seen + 0.1 + TITLE_SAFETY, 2)


def card_in(video: Path, work: Path, after: float) -> float:
    """The last safe second before the overview card starts ghosting in.

    The incoming card's heading fades up on top of footage that is still at
    full strength, so nothing about the picture changes until well after the
    text is legible. Back off a second and a half from the first frame whose
    border has gone flat navy.
    """
    from PIL import Image
    d = work / "card"
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("*.jpg"):
        old.unlink()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{after:.2f}",
                    "-to", f"{after + 26:.2f}", "-i", str(video), "-vf",
                    "fps=2,scale=320:-1", "-q:v", "5", str(d / "c%04d.jpg")],
                   check=True)
    for f in sorted(d.glob("*.jpg")):
        t = after + (int(f.stem[1:]) - 1) / 2.0
        if classify(Image.open(f).convert("RGB")) != "broll":
            return round(max(after + MIN_SHOT, t - CARD_SAFETY), 2)
    return round(after + 14.0, 2)


def scan(video: Path, work: Path) -> list:
    """One label per second, coalesced into segments."""
    from PIL import Image
    work.mkdir(parents=True, exist_ok=True)
    for old in work.glob("*.jpg"):
        old.unlink()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vf",
                    "fps=1,scale=320:-1", "-q:v", "4", str(work / "s_%04d.jpg")],
                   check=True)
    segs = []
    for f in sorted(work.glob("*.jpg")):
        t = int(f.stem.split("_")[1]) - 1
        kind = classify(Image.open(f).convert("RGB"))
        if segs and segs[-1]["kind"] == kind:
            segs[-1]["end"] = t + 1
        else:
            segs.append({"kind": kind, "start": t, "end": t + 1})
    return [s | {"duration": s["end"] - s["start"]} for s in segs
            if s["end"] - s["start"] >= 2]


def shot_bounds(video: Path, t0: float, t1: float, work: Path) -> list:
    """Hard cuts inside a window, by frame differencing at 10 fps."""
    from PIL import Image, ImageChops, ImageStat
    d = work / "shots"
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("*.png"):
        old.unlink()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t0:.3f}",
                    "-to", f"{t1:.3f}", "-i", str(video), "-vf",
                    "fps=10,scale=96:54,format=gray", str(d / "s%05d.png")],
                   check=True)
    files = sorted(d.glob("*.png"))
    cuts, prev = [t0], None
    for i, f in enumerate(files):
        img = Image.open(f)
        if prev is not None:
            m = ImageStat.Stat(ImageChops.difference(img, prev)).mean[0]
            if m > CUT_THRESHOLD:
                cuts.append(round(t0 + i / 10.0, 2))
        prev = img
    cuts.append(t1)
    # Merge anything too short to read into its neighbour, then split anything
    # too long to hold. A 0.5s flash of a shot reads as a mistake, not a cut.
    spans, start = [], cuts[0]
    for edge in cuts[1:]:
        if edge - start >= MIN_SHOT:
            spans.append([round(start, 2), round(edge, 2)])
            start = edge
    if spans and t1 - start > 0.4:
        spans[-1][1] = round(t1, 2)          # absorb the short tail
    elif not spans:
        spans = [[round(t0, 2), round(t1, 2)]]
    out = []
    for a, b in spans:
        while b - a > MAX_SHOT:
            out.append((round(a, 2), round(a + MAX_SHOT, 2)))
            a = round(a + MAX_SHOT, 2)
        if b - a >= MIN_SHOT:
            out.append((round(a, 2), round(b, 2)))
        elif out:
            out[-1] = (out[-1][0], round(b, 2))
    return out


def cut(slug: str, bucket: str, t0: float | None, t1: float | None,
        work: Path) -> list:
    video = source(slug)
    if t0 is None:
        t0 = title_clear(video, work / slug)
    if t1 is None:
        t1 = card_in(video, work / slug, t0)
    print(f"[OK] {slug}: safe window {t0:.2f}-{t1:.2f}s (measured)")
    dest = BROLL / bucket
    dest.mkdir(parents=True, exist_ok=True)
    shots = shot_bounds(video, t0, t1, work)
    written = []
    for n, (a, b) in enumerate(shots, 1):
        out = dest / f"{slug}-{n:02d}.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}",
             "-i", str(video), "-filter_complex",
             f"[0:v]setpts=PTS-STARTPTS,scale={W}:{H}:"
             f"force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
             f"setsar=1[out]", "-map", "[out]"] + VENC +
            ["-movflags", "+faststart", str(out)])
        written.append({"file": f"{bucket}/{out.name}", "bucket": bucket,
                        "seconds": round(probe_duration(out), 2),
                        "from": slug, "in": a, "out": b})
        print(f"[OK] {out.relative_to(REPO_ROOT)}  {b - a:.2f}s  ({a:.2f}-{b:.2f})")
    return written


def verify(work: Path) -> Path:
    """First, middle and last frame of every harvested clip, on one sheet.

    Read it. A colour test cannot see a card heading ghosting in over
    full-strength footage, and that is the failure mode that matters.
    """
    from PIL import Image, ImageDraw
    from common import mono
    clips = sorted(BROLL.rglob("*.mp4"))
    tw, th = 320, 180
    sheet = Image.new("RGB", (3 * (tw + 6) + 6, len(clips) * (th + 6) + 6),
                      (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    f = mono(16)
    tmp = work / "verify"
    tmp.mkdir(parents=True, exist_ok=True)
    for row, clip in enumerate(clips):
        dur = probe_duration(clip)
        for col, t in enumerate((0.05, dur / 2, max(0.05, dur - 0.12))):
            p = tmp / f"v{row}_{col}.jpg"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}",
                            "-i", str(clip), "-frames:v", "1", "-vf",
                            f"scale={tw}:{th}", str(p)], check=True)
            if p.exists():
                sheet.paste(Image.open(p), (6 + col * (tw + 6), 6 + row * (th + 6)))
        d.text((10, 8 + row * (th + 6)), clip.name, font=f, fill=(255, 230, 0))
    out = work / "broll-verify.jpg"
    sheet.save(out, quality=88)
    print(f"[OK] {out} - {len(clips)} clips, read every row")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scan", type=Path, help="print the segment map of a recording")
    ap.add_argument("--cut", help="slug of a recording to cut b-roll from")
    ap.add_argument("--bucket", default="cross_industry")
    ap.add_argument("--in", dest="t0", type=float, default=None,
                    help="override the measured in-point (seconds)")
    ap.add_argument("--out", dest="t1", type=float, default=None,
                    help="override the measured out-point (seconds)")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--work", type=Path, default=REPO_ROOT / "film" / ".work")
    args = ap.parse_args()
    require_tools()
    args.work.mkdir(parents=True, exist_ok=True)

    if args.scan:
        print(json.dumps(scan(args.scan, args.work / "scan"), indent=2))
    if args.cut:
        written = cut(args.cut, args.bucket, args.t0, args.t1, args.work)
        idx_path = BROLL / "harvested.json"
        idx = json.loads(idx_path.read_text()) if idx_path.exists() else {"clips": []}
        idx["schema"] = "aibast-showcase-film-broll/1.0"
        idx["clips"] = [c for c in idx["clips"] if c["from"] != args.cut] + written
        idx_path.write_text(json.dumps(idx, indent=1))
    if args.verify:
        verify(args.work)
    if not (args.scan or args.cut or args.verify):
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
