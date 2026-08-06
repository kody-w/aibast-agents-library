#!/usr/bin/env python3
"""Gate a generated film against the professional recording it is built on.

This exists because the checks that came before it were the wrong checks. They
measured the CONTAINER — duration, frame rate, bitrate, loudness, silence — and
all of them stayed green while the picture was wrong in ways an executive
audience sees in the first pass: sixty-six pixels of the reference's own
Copilot nav rail showing down the left edge of our patch for seventy-eight
seconds, a chat panel still on screen almost seven seconds after the shot it
belonged to had dissolved away, a title lozenge a hundred and seventy pixels
left of frame centre.

None of that is visible in a container statistic. All of it is visible in a
comparison against the base recording's own measured geometry. So every check
here is relational — candidate against base, at the pixel and at the second —
plus the copy checks, because "the agent can rais margin" also passed a green
build.

Exit code is the number of failures.

Usage:
    python3 tests/check_film_fidelity.py --agent account-intelligence
    python3 tests/check_film_fidelity.py --all-copy      # copy gates only
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GEOMETRY = REPO_ROOT / "media" / "plates" / "base-geometry.json"
OVERLAYS = REPO_ROOT / "media" / "plates" / "overlays.json"
WALK = REPO_ROOT / "media" / "walkthroughs"
FILMS = REPO_ROOT / "media" / "videos" / "generated"
BASE_SOURCE = Path.home() / "Desktop" / "aibast_bible" / "videos"

FAILS: list[str] = []
PASSES: list[str] = []


def check(ok: bool, gate: str, detail: str) -> bool:
    (PASSES if ok else FAILS).append(f"{gate}: {detail}")
    print(f"  {'PASS' if ok else 'FAIL'}  {gate}  {detail}")
    return ok


# --------------------------------------------------------------------------
# Copy gates: what the film says, in the storyboard it says it from.
# --------------------------------------------------------------------------

# A third-person verb dropped into an infinitive slot. Every instance of this
# shipped to screen at least once: "needs to handles account intelligence",
# "It can improves conversion", "I'll handles account intelligence".
BAD_INFINITIVE = re.compile(
    r"\b(?:needs? to|can|could|will|should|must|to|I'll|we'll|let's)\s+"
    r"(?!is\b|has\b|its\b|this\b|thus\b|less\b|analysis\b|business\b|"
    r"process\b|access\b|address\b|progress\b|status\b|focus\b|bias\b)"
    r"([a-z]+(?:ies|es|s))\b")

# Text that describes the rig rather than the work, or names our own internals
# in a Microsoft-branded customer film.
LEAKED_INTERNALS = re.compile(
    r"\[operator supplies\]|described above|local brainstem|brainstem chat|"
    r"\bGPT-[0-9.]+\b|lorem ipsum|TODO|TBD|\bXX\b|\{[a-z_]+\}", re.I)

# A figure we cannot substantiate. The films are qualitative by instruction.
INVENTED_FIGURE = re.compile(
    r"\b\d[\d,.]*\s*(?:%|percent|units?/day|hours?/week|x faster|"
    r"bps|basis points)\b|\bOEE\s*\d|\$\s?\d[\d,.]*(?:\s?[kmb]\b)?", re.I)

# Fields that are prose the viewer reads or hears. Notes and provenance are not.
SPOKEN_KEYS = {"narration", "intro", "text", "headline", "items", "steps",
               "caption", "label", "title", "subtitle", "body", "question",
               "prompt", "panels", "sections"}


def spoken_strings(node, key=None, out=None):
    """Every string that reaches a viewer's eye or ear, and nothing else."""
    out = [] if out is None else out
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("note", "provenance", "approval", "source", "schema",
                     "remix", "_meta"):
                continue
            spoken_strings(v, k, out)
    elif isinstance(node, list):
        for v in node:
            spoken_strings(v, key, out)
    elif isinstance(node, str) and key in SPOKEN_KEYS:
        out.append(node)
    return out


def copy_gates(paths: list[Path]) -> None:
    bad_gram, leaked, figures = {}, {}, {}
    for p in paths:
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            check(False, "T-FILM-JSON", f"{p.name} is not valid JSON: {e}")
            continue
        for s in spoken_strings(doc):
            for m in BAD_INFINITIVE.finditer(s):
                bad_gram.setdefault(m.group(0), p.name)
            for m in LEAKED_INTERNALS.finditer(s):
                leaked.setdefault(m.group(0), p.name)
            for m in INVENTED_FIGURE.finditer(s):
                figures.setdefault(m.group(0), p.name)

    def report(gate, found, what):
        if found:
            sample = "; ".join(f"{k!r} ({v})" for k, v in list(found.items())[:4])
            check(False, gate, f"{len(found)} distinct {what}: {sample}")
        else:
            check(True, gate, f"no {what} across {len(paths)} storyboard(s)")

    report("T-FILM-GRAMMAR", bad_gram, "third-person verbs in infinitive slots")
    report("T-FILM-INTERNALS", leaked, "leaked internals or placeholders")
    report("T-FILM-FIGURES", figures, "unsubstantiated figures")


# --------------------------------------------------------------------------
# Geometry and timing gates: the candidate against the base it sits on.
# --------------------------------------------------------------------------

def probe(path: Path, stream: str, fields: str) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", stream,
                        "-show_entries", fields, "-of", "json", str(path)],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {}


def find_base(track_id: str) -> Path | None:
    if not BASE_SOURCE.is_dir():
        return None
    want = re.sub(r"[^a-z0-9]+", "", track_id.lower())
    for f in sorted(BASE_SOURCE.glob("*.mp4")):
        stem = re.sub(r"^[#0-9-]+", "", f.stem)
        if re.sub(r"[^a-z0-9]+", "", stem.lower()) == want:
            return f
    return None


def region_diff(base: Path, cand: Path, t: float):
    """Where the candidate differs from the base at time t, as a bounding box."""
    import numpy as np
    from PIL import Image
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        a, b = Path(td) / "a.png", Path(td) / "b.png"
        for src, dst in ((base, a), (cand, b)):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t),
                            "-i", str(src), "-frames:v", "1", str(dst)],
                           capture_output=True)
        if not (a.is_file() and b.is_file()):
            return None
        fa = np.array(Image.open(a).convert("RGB")).astype(int)
        fb = np.array(Image.open(b).convert("RGB")).astype(int)
        d = np.abs(fa - fb).sum(axis=2) > 60
        if d.sum() < 500:
            return None
        ys, xs = np.where(d)
        # Percentiles, not extremes. The candidate is re-encoded, so a moving
        # b-roll plate differs from the original by a few sparse macroblocks
        # nowhere near the patch — and a min/max bbox reports those as a 355px
        # spill that is not on screen.
        lo, hi = 0.2, 99.8
        return {
            # Coverage asks how far the patch REACHES, so it uses the extremes:
            # a rounded corner contributes few differing pixels and a percentile
            # would clip the patch's own edge and report it as a gap.
            "extent": (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())),
            # Spill asks what is differing in BULK, so it uses percentiles: the
            # candidate is re-encoded and a moving b-roll plate differs by sparse
            # macroblocks nowhere near the patch.
            "bulk": (int(np.percentile(xs, lo)), int(np.percentile(ys, lo)),
                     int(np.percentile(xs, hi)), int(np.percentile(ys, hi))),
        }


def tonal_peak(path: Path):
    """The strongest narrow-band tone that holds across the whole film.

    A tone is not loudness: the bed measured correctly at -28 LUFS and still
    read as a hum, because its energy sat in a few held partials rather than
    spread across a spectrum. So look for a bin that stands far above its
    neighbours in EVERY window sampled, which is what "sustained" means.
    """
    import numpy as np
    import tempfile, wave
    with tempfile.TemporaryDirectory() as td:
        w = Path(td) / "a.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path),
                        "-ac", "1", "-ar", "8000", "-c:a", "pcm_s16le", str(w)],
                       capture_output=True)
        if not w.is_file():
            return None
        wf = wave.open(str(w))
        sr, n = wf.getframerate(), wf.getnframes()
        a = np.frombuffer(wf.readframes(n), dtype=np.int16).astype(float)
    if len(a) < sr * 10:
        return None
    # Sample windows spread across the film, skipping the silent head and tail.
    seg = sr * 4
    starts = [int(x) for x in np.linspace(sr * 6, len(a) - seg - sr * 6, 8)]
    prominences = {}
    for st in starts:
        chunk = a[st:st + seg] * np.hanning(seg)
        sp = np.abs(np.fft.rfft(chunk))
        fr = np.fft.rfftfreq(seg, 1 / sr)
        band = (fr > 35) & (fr < 400)
        sp, fr = sp[band], fr[band]
        if sp.max() <= 0:
            continue
        db = 20 * np.log10(np.maximum(sp, 1e-9))
        # Prominence against a wide local median, so speech formants — which
        # move — do not register the way a held partial does.
        k = max(3, len(db) // 40)
        med = np.array([np.median(db[max(0, i - k):i + k]) for i in range(len(db))])
        i = int(np.argmax(db - med))
        prominences.setdefault(round(fr[i] / 4) * 4, []).append(float(db[i] - med[i]))
    # Sustained = present in most windows at the same frequency.
    best = None
    for f, vals in prominences.items():
        if len(vals) >= max(3, len(starts) * 0.6):
            m = float(np.median(vals))
            if best is None or m > best[1]:
                best = (f, m)
    return best


def geometry_gates(agent: str) -> None:
    film = FILMS / f"agent-{agent}.mp4"
    if not film.is_file():
        check(False, "T-FILM-EXISTS", f"no rendered film at {film}")
        return
    if not (GEOMETRY.is_file() and OVERLAYS.is_file()):
        check(False, "T-FILM-MEASURED", "base geometry has not been measured")
        return

    track_id = json.loads(OVERLAYS.read_text(encoding="utf-8"))["base_track"]
    g = json.loads(GEOMETRY.read_text(encoding="utf-8"))["tracks"].get(track_id)
    base_profile = (g or {}).get("audio") or {}
    base = find_base(track_id)
    if not (g and base):
        check(False, "T-FILM-MEASURED", f"{track_id} unmeasured or base missing")
        return

    # 1. The container still has to match — necessary, just never sufficient.
    pb = probe(base, "v:0", "stream=width,height,r_frame_rate:format=duration")
    pc = probe(film, "v:0", "stream=width,height,r_frame_rate:format=duration")
    sb, sc = pb.get("streams", [{}])[0], pc.get("streams", [{}])[0]
    check(sb.get("width") == sc.get("width") and sb.get("height") == sc.get("height"),
          "T-FILM-FRAME", f"{sc.get('width')}x{sc.get('height')} vs base "
                          f"{sb.get('width')}x{sb.get('height')}")
    db = float(pb.get("format", {}).get("duration", 0))
    dc = float(pc.get("format", {}).get("duration", 0))
    check(abs(db - dc) < 0.1, "T-FILM-DURATION", f"{dc:.2f}s vs base {db:.2f}s")

    # 2. Every patch must land INSIDE the thing it replaces and COVER it.
    #    This is the gate that was missing. A patch inset by 66px passes every
    #    container check ever written and shows the reference's own UI.
    # A patch rounded to the display's own corner radius cannot differ from the
    # base out at its extreme corners — that is the point of rounding it — so
    # coverage is allowed to fall short by the radius and no more.
    radii = {r["id"]: r.get("corner_radius", 0)
             for r in json.loads(OVERLAYS.read_text(encoding="utf-8"))["regions"]}
    radii["screen"] = 30
    for rid, tol_in, tol_out in (("title", 12, 0), ("screen", 6, 0)):
        tol_in = max(tol_in, radii.get(rid, 0) + 4)
        act = g.get(rid)
        if not act:
            continue
        # Gate against the MEASURED box, because that is the screen the patch
        # is laid over. calibration.json describes our own plate
        # (media/plates/laptop-copilot.png), a different and smaller laptop;
        # gating the base composite against it passed a film that showed the
        # reference's own nav rail beside ours for seventy seconds.
        want = act.get("rect") or act.get("envelope")
        mid = (act["start"] + act["end"]) / 2
        bb = region_diff(base, film, mid)
        if not bb:
            check(False, f"T-FILM-{rid.upper()}-RECT",
                  f"nothing is composited at t={mid:.2f}s")
            continue
        x0, y0, x1, y1 = bb["extent"]
        wx0, wy0 = want["x"], want["y"]
        wx1, wy1 = want["x"] + want["w"], want["y"] + want["h"]
        # Covers: our patch must reach at least to the measured extent.
        gap = max(x0 - wx0, y0 - wy0, wx1 - x1, wy1 - y1)
        check(gap <= tol_in, f"T-FILM-{rid.upper()}-COVERS",
              f"patch [{x0},{y0}..{x1},{y1}] vs measured "
              f"[{wx0},{wy0}..{wx1},{wy1}], largest uncovered edge {gap}px")
        # Contains: and must not spill outside it onto the base's own frame.
        bx0, by0, bx1, by1 = bb["bulk"]
        spill = max(wx0 - bx0, wy0 - by0, bx1 - wx1, by1 - wy1)
        check(spill <= 24 + tol_out, f"T-FILM-{rid.upper()}-CONTAINED",
              f"largest spill beyond the measured box {spill}px")

    # 3. Every patch must leave when the shot under it leaves.
    for rid in ("title", "overview", "screen"):
        act = g.get(rid)
        if not act:
            continue
        after = act["end"] + 1.0
        if after > dc - 0.5:
            continue
        # Another act may legitimately own that second — the card ends at 42.75
        # and the laptop begins at 43.0, so a second later the laptop patch is
        # correctly on screen. Only an UNCLAIMED second proves an overstay.
        if any(o["start"] <= after <= o["end"]
               for k, o in g.items()
               if k != rid and isinstance(o, dict) and "start" in o):
            continue
        bb = region_diff(base, film, after)
        e = bb["bulk"] if bb else None
        area = 0 if not e else (e[2] - e[0]) * (e[3] - e[1])
        check(area < 120_000, f"T-FILM-{rid.upper()}-WINDOW",
              f"1s after the act ends (t={after:.2f}s) the frame differs over "
              f"{area:,}px² — a patch outliving its shot")

    # 4. The base's silent head and tail must stay silent.
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(film),
                        "-af", "silencedetect=n=-40dB:d=0.6", "-f", "null", "-"],
                       capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: (-?[0-9.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r.stderr)]
    spans = list(zip(starts, ends + [dc] * (len(starts) - len(ends))))
    prof = base_profile
    # Silence must COVER the base's quiet head and tail. Asking that it begin at
    # the same second was wrong twice over: starting earlier is not a defect,
    # and it failed a film whose tail was silent for three and a third seconds.
    want_head = float(prof.get("head_silent_until") or 0.0)
    want_tail = float(prof.get("tail_silent_from") or dc)
    head = any(a <= 0.15 and b >= want_head - 0.35 for a, b in spans)
    tail = any(a <= want_tail + 0.35 and b >= dc - 0.35 for a, b in spans)
    check(head, "T-FILM-HEAD-SILENT",
          "audio runs under the opening Microsoft logo" if not head
          else "silent under the opening logo, as the base is")
    check(tail, "T-FILM-TAIL-SILENT",
          "audio runs under the closing logo" if not tail
          else "silent under the closing logo, as the base is")

    # 5. Narration must cover the acts it narrates, not stop a third of the way.
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(film), "-af",
                        "highpass=f=300,lowpass=f=3400,"
                        "silencedetect=n=-33dB:d=4.0", "-f", "null", "-"],
                       capture_output=True, text=True)
    holes = []
    for s, e in zip(re.findall(r"silence_start: ([0-9.]+)", r.stderr),
                    re.findall(r"silence_end: ([0-9.]+)", r.stderr)):
        s, e = float(s), float(e)
        if s > 4.0 and e < dc - 4.0:
            holes.append((s, e))
    worst = max((e - s for s, e in holes), default=0.0)
    check(worst < 8.0, "T-FILM-NARRATION-COVERAGE",
          f"longest gap in narration {worst:.1f}s"
          + (f" at {holes[0][0]:.1f}s" if holes else ""))

    # 5b. No sustained tone. The synthesised "music bed" was four held sine
    #     partials at 55, 82, 131 and 165 Hz — arithmetically a score, audibly a
    #     hum, and it ran under the entire film before anyone measured it.
    hum = tonal_peak(film)
    check(hum is None or hum[1] < 14.0, "T-FILM-NO-HUM",
          "no sustained tone" if hum is None else
          f"sustained tone at {hum[0]:.0f} Hz, {hum[1]:.1f} dB above its "
          f"neighbours — a hum, not a bed")

    # 6. A held frame is not a walkthrough. The reference plays six exchanges
    #    across this act; a single frame held for half of it reads as a stall.
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(film),
                        "-vf", "freezedetect=n=-55dB:d=6", "-f", "null", "-"],
                       capture_output=True, text=True)
    durs = [float(x) for x in re.findall(r"freeze_duration: ([0-9.]+)", r.stderr)]
    longest = max(durs, default=0.0)
    check(longest < 14.0, "T-FILM-MOTION",
          f"longest frozen picture {longest:.1f}s")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--agent")
    ap.add_argument("--all-copy", action="store_true",
                    help="run the copy gates across every storyboard")
    args = ap.parse_args()

    print("Film fidelity gates")
    if args.all_copy or not args.agent:
        copy_gates(sorted(WALK.glob("*.json")))
    if args.agent:
        p = WALK / f"agent-{args.agent}.json"
        if p.is_file():
            copy_gates([p])
        geometry_gates(args.agent)

    print(f"\n{len(PASSES)} passed, {len(FAILS)} failed")
    for f in FAILS:
        print(f"  ✗ {f}")
    return len(FAILS)


if __name__ == "__main__":
    sys.exit(main())
