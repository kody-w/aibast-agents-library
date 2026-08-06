#!/usr/bin/env python3
"""Hard gates for a built film, plus the cold-start check on the kit itself.

A gate that cannot fail is decoration, so every check here has failed at least
once on a real build. The gates are grouped:

  text        customer-facing vocabulary, real identifiers, PII shapes, over
              narration, every card and chyron string, and every clip filename
  picture     duration window, frame size, and the longest unchanged frame
  audio       per-slot mean level, bed audibility in the gaps, programme peak,
              and whether the mix is genuinely stereo
  cold-start  no path anywhere under film/ reaches outside the repository

What the text gate cannot see is the pixels of a captured shot. Internal tool
identifiers on screen for most of a take passed a green vocabulary gate once.
Run `python3 film/kit/watch.py` and read the frames.

Output: film/projects/<slug>/work/gate.json
Usage:
    python3 film/kit/gate.py --project supplier-risk-watch
    python3 film/kit/gate.py --cold-start
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (FILM, REPO_ROOT, levels, load_project,  # noqa: E402
                    probe_duration, probe_size, require_tools)

# Vocabulary a customer-facing cut may not use. The customer has never heard
# of any of it, and naming our own build machinery in a Microsoft-branded film
# is the defect this list exists to stop.
FORBIDDEN_WORDS = [
    "RAPP", "RAPPlication", "Factory", "brainstem", "egg", "prototype", "MVP",
    "pipeline", "muscle", "Fable", "Claude", "Copilot Studio", "MCP",
    "connector", "Dataverse", "BlastBox",
]
FORBIDDEN_SUBSTRINGS = ["kowildfe", "wildfeuer", "mngenv", "workiq"]
FORBIDDEN_PATTERNS = [
    (r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
     "GUID (tenant / subscription / resource identifier)"),
    (r"/subscriptions/", "Azure subscription resource path"),
    (r"\bBearer\s+[A-Za-z0-9._-]{20,}", "bearer token"),
]
# Overclaims this distribution does not get to make.
OVERCLAIMS = ["production-ready", "guaranteed", "enterprise-grade"]

VO_FLOOR_DB = -19.0          # every narration slot must be louder than this
BED_CEILING_DB = -22.0       # a gap louder than this means the bed is not ducking
BED_FLOOR_DB = -34.0         # a gap quieter than this means the bed is inaudible
MAX_HOLD_SECONDS = 5.0
# The reference films are narrated wall to wall. A gap longer than this reads
# as the film having stopped, and level alone cannot detect it.
MAX_SILENT_GAP_S = 6.0
HOLD_SAMPLE_HZ = 4
PEAK_CEILING_DB = -0.1

# Absolute paths that must never appear under film/. Each one is a way the
# workflow could silently reach back to the machine that built it.
# Assembled from fragments on purpose: written out whole, this table would
# match itself and the gate would fail on its own source.
ESCAPES = [
    ("~/" + "Desktop", "someone's Desktop"),
    ("/User" + "s/", "a home directory"),
    ("/Librar" + "y/Audio", "a macOS system audio asset"),
    ("MSFTAIBAST" + "RAPP", "another repository this was ported from"),
    ("/tm" + "p/", "a temporary directory"),
    ("/privat" + "e/tmp", "a temporary directory"),
]
# The font is the one allowed outside reference: Pillow needs a real TTF and
# system fonts are not ours to redistribute. brand.json holds the candidates
# and common.font() falls through them, so a missing font degrades, never
# breaks.
ESCAPE_EXEMPT = ["/System/Library/Fonts", "/Library/Fonts"]


def scan_text(label: str, text: str) -> list:
    bad = []
    lines = text.splitlines() or [text]
    for word in FORBIDDEN_WORDS:
        rx = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        for n, line in enumerate(lines, 1):
            if rx.search(line):
                bad.append(f"{label}:{n}: forbidden word {word!r} -> {line.strip()[:80]}")
    low = text.lower()
    for sub in FORBIDDEN_SUBSTRINGS:
        if sub in low:
            bad.append(f"{label}: forbidden identifier {sub!r}")
    for claim in OVERCLAIMS:
        if claim in low:
            bad.append(f"{label}: overclaim {claim!r}")
    for pat, why in FORBIDDEN_PATTERNS:
        if re.search(pat, text):
            bad.append(f"{label}: {why}")
    return bad


def gate_text(project: dict) -> tuple:
    bad, log = [], ["--- text ---"]
    corpus = {}
    for slot, line in project["script"].items():
        corpus[f"narration:{slot}"] = line
    cardtext = json.loads((project["_work"] / "cardtext.json").read_text())
    for name, text in cardtext.items():
        corpus[f"card:{name}"] = text
    for q in project["demo"]["questions"]:
        corpus[f"prompt:{q['id']}"] = q["prompt"]
        for i, b in enumerate(q["answer"]):
            corpus[f"answer:{q['id']}:{i}"] = json.dumps(b)
        for c in q.get("citations", []):
            corpus[f"citation:{q['id']}"] = c
    for beat in project["beats"]:
        for c in beat.get("clips", []):
            corpus[f"clip:{beat['id']}"] = c["file"]
        if beat.get("clip"):
            corpus[f"clip:{beat['id']}"] = beat["clip"]
    for key, text in corpus.items():
        bad += scan_text(key, text)
    log.append(f"  scanned {len(corpus)} strings "
               f"(narration, card and chyron copy, prompts, answers, clip names)")
    log.append(f"  [{'PASS' if not bad else 'FAIL'}] vocabulary and identifiers")
    return bad, log


def longest_hold(mp4: Path, work: Path) -> tuple:
    """Longest run of visually identical frames, in seconds, and where."""
    from PIL import Image, ImageChops, ImageStat
    frames = work / "hold"
    frames.mkdir(parents=True, exist_ok=True)
    for old in frames.glob("*.png"):
        old.unlink()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp4), "-vf",
                    f"fps={HOLD_SAMPLE_HZ},scale=192:108,format=gray",
                    str(frames / "h%05d.png")], check=True)
    files = sorted(frames.glob("*.png"))
    prev, run_start, best, best_at = None, 0, 0, 0.0
    for i, f in enumerate(files):
        img = Image.open(f)
        same = False
        if prev is not None:
            diff = ImageChops.difference(img, prev)
            st = ImageStat.Stat(diff)
            same = st.mean[0] < 0.45 and max(diff.getextrema()) < 6
        if not same:
            length = i - run_start
            if length > best:
                best, best_at = length, run_start / HOLD_SAMPLE_HZ
            run_start = i
        prev = img
    length = len(files) - run_start
    if length > best:
        best, best_at = length, run_start / HOLD_SAMPLE_HZ
    return round(best / HOLD_SAMPLE_HZ, 2), round(best_at, 2)


def gate_picture(project: dict, mp4: Path) -> tuple:
    bad, log = [], ["--- picture ---"]
    d = probe_duration(mp4)
    w, h = probe_size(mp4)
    lo, hi = project.get("duration_window", [140, 175])
    ok = lo <= d <= hi
    log.append(f"  duration {d:.2f}s  frame {w}x{h}  "
               f"[{'PASS' if ok else 'FAIL'}] window {lo}-{hi}s")
    if not ok:
        bad.append(f"duration {d:.2f}s outside the {lo}-{hi}s window")
    if (w, h) != (1920, 1080):
        bad.append(f"frame is {w}x{h}, not 1920x1080")
    hold, at = longest_hold(mp4, project["_work"])
    ok = hold <= MAX_HOLD_SECONDS
    log.append(f"  longest unchanged frame {hold:.2f}s at {at:.2f}s  "
               f"[{'PASS' if ok else 'FAIL'}] max {MAX_HOLD_SECONDS}s")
    if not ok:
        bad.append(f"held one frame for {hold:.2f}s at {at:.2f}s - add a build "
                   f"stage or shorten the beat")
    return bad, log


def gate_audio(project: dict, mp4: Path, beatmap: dict) -> tuple:
    bad, log = [], ["--- audio ---"]
    total = beatmap["total"]
    log.append(f"  per-slot mean, measured on the delivered file "
               f"(floor {VO_FLOOR_DB} dB)")
    cover = []
    for slot, at, dur in beatmap["vo_marks"]:
        m, x = levels(mp4, at, at + dur)
        ok = m is not None and m > VO_FLOOR_DB
        log.append(f"    {'ok ' if ok else 'BAD'} {slot:6s} {at:7.2f}-{at + dur:7.2f}s"
                   f"  mean {m:6.2f} dB  peak {x:6.2f} dB")
        if not ok:
            bad.append(f"narration slot {slot} mean {m} dB is not above {VO_FLOOR_DB}")
        cover.append((at, at + dur))
    cover.sort()
    gaps, t = [], 0.0
    for a, b in cover:
        if a - t > 1.6:
            gaps.append((t, a))
        t = max(t, b)
    if total - t > 1.6:
        gaps.append((t, total))
    log.append(f"  bed-only gaps (audible band {BED_FLOOR_DB} to {BED_CEILING_DB} dB)")
    for a, b in gaps:
        m, _ = levels(mp4, a + 0.5, b - 0.5)
        # The head and tail of the film are deliberately silent - the logo
        # sting plays on nothing and the film ends on nothing.
        silent_by_design = a < 1.0 or b > total - 1.0
        if silent_by_design:
            log.append(f"    ok  gap {a:6.2f}-{b:6.2f}s  mean {m:6.2f} dB  "
                       f"(silent by design)")
            continue
        level_ok = m is not None and BED_FLOOR_DB < m < BED_CEILING_DB
        length_ok = (b - a) <= MAX_SILENT_GAP_S
        ok = level_ok and length_ok
        log.append(f"    {'ok ' if ok else 'BAD'} gap {a:6.2f}-{b:6.2f}s "
                   f"({b - a:5.2f}s)  mean {m:6.2f} dB")
        if not level_ok:
            why = "inaudible" if (m or -99) <= BED_FLOOR_DB else "not ducking"
            bad.append(f"bed-only gap {a:.1f}-{b:.1f}s mean {m} dB is {why}")
        if not length_ok:
            bad.append(f"un-narrated gap {a:.1f}-{b:.1f}s runs {b - a:.1f}s, over "
                       f"the {MAX_SILENT_GAP_S}s limit - the film stops")
    pm, pk = levels(mp4)
    log.append(f"  programme mean {pm:6.2f} dB  peak {pk:6.2f} dB")
    if pk is not None and pk > PEAK_CEILING_DB:
        bad.append(f"programme peak {pk} dB is above the limiter ceiling")
    # amix adopts the FIRST input's channel layout. A mono voice bus silently
    # collapses a stereo bed, and nothing else in the gate notices.
    err = subprocess.run(["ffmpeg", "-v", "info", "-i", str(mp4), "-af",
                          "pan=mono|c0=0.5*c0-0.5*c1,volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", err)
    side = float(m.group(1)) if m else -99.0
    ok = side > -70.0
    log.append(f"  side-channel energy {side:6.2f} dB  "
               f"[{'PASS' if ok else 'FAIL'}] genuinely stereo")
    if not ok:
        bad.append("mix is mono - amix took the voice bus layout; aformat every "
                   "input to stereo before any amix")
    return bad, log


def gate_cold_start() -> tuple:
    """No file under film/ may name a path outside the repository."""
    bad, log = [], ["--- cold start ---"]
    exts = {".py", ".md", ".json", ".txt", ".sh", ".html"}
    checked = 0
    for path in sorted(FILM.rglob("*")):
        if not path.is_file() or path.suffix not in exts:
            continue
        rel_parts = path.relative_to(FILM).parts
        # Intermediates and scratch are gitignored and are not the port.
        if {"work", "dist", ".work", "corpus"} & set(rel_parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        checked += 1
        rel = path.relative_to(REPO_ROOT)
        for n, line in enumerate(text.splitlines(), 1):
            if any(x in line for x in ESCAPE_EXEMPT):
                continue
            for pat, why in ESCAPES:
                if re.search(re.escape(pat), line):
                    bad.append(f"{rel}:{n}: reaches {why} -> {line.strip()[:90]}")
    log.append(f"  scanned {checked} files under film/ for absolute paths")
    # Every script the documented workflow calls must exist in the repository.
    required = ["common.py", "compose.py", "narrate.py", "plan.py", "cards.py",
                "screens.py", "build.py", "gate.py", "watch.py", "harvest.py",
                "publish.py"]
    for name in required:
        p = FILM / "kit" / name
        if not p.exists():
            bad.append(f"film/kit/{name} is named by the workflow but missing")
    log.append(f"  {len(required)} kit modules required, "
               f"{sum((FILM / 'kit' / n).exists() for n in required)} present")
    for asset in [FILM / "assets" / "audio" / "bed-slow-drift.caf",
                  FILM / "assets" / "stings" / "sting-intro-logo.mp4",
                  FILM / "assets" / "broll" / "index.json",
                  FILM / "brand" / "brand.json",
                  FILM / "README.md", FILM / "GRAMMAR.md", FILM / "AUDIO.md",
                  FILM / "CAPTURE.md"]:
        if not asset.exists():
            bad.append(f"{asset.relative_to(REPO_ROOT)} is missing")
    log.append(f"  [{'PASS' if not bad else 'FAIL'}] self-contained")
    return bad, log


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project")
    ap.add_argument("--cold-start", action="store_true",
                    help="only check that the kit reaches nothing outside the repo")
    args = ap.parse_args()

    violations, log = [], []
    if args.cold_start or not args.project:
        v, l = gate_cold_start()
        violations += v
        log += l
    if args.project:
        require_tools()
        project = load_project(args.project)
        mp4 = project["_dist"] / project["output"]
        if not mp4.exists():
            print(f"FAIL - {mp4} has not been built")
            return 1
        beatmap = json.loads((project["_work"] / "beatmap.json").read_text())
        for fn in (lambda: gate_text(project),
                   lambda: gate_picture(project, mp4),
                   lambda: gate_audio(project, mp4, beatmap)):
            v, l = fn()
            violations += v
            log += l
        if not args.cold_start:
            v, l = gate_cold_start()
            violations += v
            log += l
        (project["_work"] / "gate.json").write_text(json.dumps(
            {"violations": violations, "log": log}, indent=1))

    print("\n".join(log))
    print("=" * 70)
    if violations:
        print(f"FAIL - {len(violations)} violation(s):")
        for v in violations:
            print("  ", v)
        return 1
    print("PASS - all gates green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
