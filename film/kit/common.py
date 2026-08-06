#!/usr/bin/env python3
"""Shared paths, brand data and ffmpeg helpers for the showcase film kit.

Everything the kit touches is resolved from REPO_ROOT. Nothing in film/ may
read a path outside the repository — that rule is checked by
`python3 film/kit/gate.py --cold-start`, which greps the whole of film/ for
absolute paths and fails on any hit. A pipeline that silently reaches back to
someone's Desktop is not a pipeline anyone else can run.

The one deliberate exception is the font file. Pillow needs a real TTF on
disk, and macOS system fonts are not ours to redistribute, so brand.json names
a primary and a list of fallbacks and `font()` takes the first that exists.

Output: nothing - this is a library module.

Usage:
    from common import BRAND, BROLL, run, probe_duration, mean_db
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

KIT = Path(__file__).resolve().parent
FILM = KIT.parent
REPO_ROOT = FILM.parent

BRAND_FILE = FILM / "brand" / "brand.json"
BROLL = FILM / "assets" / "broll"
STINGS = FILM / "assets" / "stings"
BED = FILM / "assets" / "audio" / "bed-slow-drift.caf"
PROJECTS = FILM / "projects"
CORPUS = FILM / "corpus" / "videos"
# The 48 shipped recordings are also served from media/videos at 960x540.
# Grammar can be re-derived from those; b-roll cannot - it would upscale.
CORPUS_WEB = REPO_ROOT / "media" / "videos"

BRAND = json.loads(BRAND_FILE.read_text())
W = BRAND["frame"]["width"]
H = BRAND["frame"]["height"]
FPS = BRAND["frame"]["fps"]

VENC = ["-c:v", "libx264", "-preset", BRAND["frame"]["preset"],
        "-crf", str(BRAND["frame"]["crf"]), "-pix_fmt", BRAND["frame"]["pix_fmt"],
        "-r", str(FPS), "-an"]


def rgb(name: str) -> tuple:
    """Look a colour up in brand.json by name."""
    return tuple(BRAND["palette"][name])


def require_tools() -> None:
    """Fail early and by name rather than deep inside a filter graph."""
    missing = [t for t in ("ffmpeg", "ffprobe") if shutil.which(t) is None]
    if missing:
        raise SystemExit(f"missing required tool(s): {', '.join(missing)} - "
                         "install ffmpeg (brew install ffmpeg)")
    try:
        import PIL  # noqa: F401
    except ImportError:
        raise SystemExit("Pillow is required for card and screen rendering - "
                         "python3 -m pip install --user Pillow")


# The one thing the kit cannot carry. Pillow needs a real font file on disk
# and system faces are not ours to redistribute, so brand.json names families
# and this list says where to look for them. A missing face degrades to the
# next candidate; nothing breaks. This is the single deliberate exception to
# "no path leaves the repository", and film/kit/gate.py exempts it by name.
FONT_DIRS = [
    Path("/System/Library/Fonts"),
    Path("/System/Library/Fonts/Supplemental"),
    Path("/Library/Fonts"),
    Path.home() / "Library" / "Fonts",
    Path("/usr/share/fonts/truetype/dejavu"),
    Path("/usr/share/fonts/truetype/liberation"),
    Path("/usr/share/fonts"),
]


def _find_face(candidates: list) -> Path | None:
    """First candidate that exists. Accepts absolute paths and bare names.

    brand.json states absolute system font paths; joining those onto FONT_DIRS
    produced paths like ".../fonts//System/Library/Fonts/Avenir Next.ttc",
    which never exist, so every face silently fell back to PIL's default
    bitmap font.
    """
    for name in candidates:
        if not name:
            continue
        p = Path(name)
        if p.is_absolute() and p.exists():
            return p
        for d in FONT_DIRS:
            q = d / name
            if q.exists():
                return q
    return None


def font(size: int, weight: str = "demi"):
    """Load the brand face at `size`, falling down brand.json's candidates."""
    from PIL import ImageFont
    idx = BRAND["type"]["index"][weight]
    # brand.json describes the face as a primary file plus fallbacks; this read
    # an older "family_candidates" key that no longer exists, so every card
    # render died on KeyError. Accept both shapes.
    t = BRAND["type"]
    path = _find_face(t.get("family_candidates")
                      or ([t["family_file"]] + list(t.get("family_fallbacks") or [])))
    if path is None:
        return ImageFont.load_default()
    try:
        return ImageFont.truetype(str(path), size, index=idx)
    except OSError:
        try:
            return ImageFont.truetype(str(path), size)
        except OSError:
            return ImageFont.load_default()


def mono(size: int):
    from PIL import ImageFont
    t = BRAND["type"]
    path = _find_face(t.get("mono_candidates")
                      or ([t["mono_file"]] + list(t.get("family_fallbacks") or [])))
    if path is None:
        return font(size, "regular")
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return font(size, "regular")


def run(args) -> subprocess.CompletedProcess:
    """Run ffmpeg/ffprobe and surface its stderr on failure, not a bare code."""
    proc = subprocess.run([str(a) for a in args], capture_output=True, text=True)
    if proc.returncode:
        print(" ".join(str(a) for a in args))
        print(proc.stderr[-4000:])
        raise SystemExit(f"command failed ({proc.returncode})")
    return proc


def probe_duration(path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def probe_size(path) -> tuple:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True).stdout.strip()
    w, h = out.split(",")[:2]
    return int(w), int(h)


def levels(path, start: float | None = None, end: float | None = None) -> tuple:
    """(mean_dB, peak_dB) over a window, measured with volumedetect.

    Measured on the delivered file, never on an intermediate stem, so the
    numbers describe exactly what ships.
    """
    args = ["ffmpeg", "-v", "info"]
    if start is not None:
        args += ["-ss", f"{start:.3f}"]
    if end is not None:
        args += ["-to", f"{end:.3f}"]
    args += ["-i", str(path), "-af", "volumedetect", "-f", "null", "-"]
    err = subprocess.run(args, capture_output=True, text=True).stderr
    m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", err)
    x = re.search(r"max_volume:\s*(-?[\d.]+) dB", err)
    return (float(m.group(1)) if m else None, float(x.group(1)) if x else None)


def mean_db(path) -> float | None:
    return levels(path)[0]


def load_project(slug: str) -> dict:
    """Read a project definition and resolve its own directory onto it."""
    path = PROJECTS / slug / "project.json"
    if not path.exists():
        have = sorted(p.name for p in PROJECTS.iterdir() if p.is_dir())
        raise SystemExit(f"no project '{slug}' - projects present: {have}")
    project = json.loads(path.read_text())
    project["_dir"] = PROJECTS / slug
    project["_work"] = PROJECTS / slug / "work"
    project["_dist"] = PROJECTS / slug / "dist"
    return project


def wrap(draw, text: str, fnt, maxw: int) -> list:
    """Greedy word wrap against a real text-metrics measurement."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines
