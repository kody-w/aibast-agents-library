#!/usr/bin/env python3
"""Render a RAPPVision storyboard into a finished demo film.

The catalog has 48 professional recordings and 183 entries. This produces the
missing films from the storyboard each entry already has, at the reference's
own specification — measured from `#1-Product Line Optimization Agent.mp4`:

    1920x1080 · 30 fps · H.264 ~6 Mbps · AAC 192k 48kHz stereo · -18.6 LUFS

How each act is made:

    1 title       rendered from vision.html, held
    2 problem     licensed b-roll from a recording in the SAME industry,
                  under generated narration (see cut_broll.py)
    3 overview    rendered from vision.html, held
    4 walkthrough rendered from vision.html frame by frame — the only act that
                  animates, so the only one that costs frames
    5 close       rendered from vision.html, held

Nothing but act 2's footage is borrowed. Framing, cards, conversation and close
are drawn from that entry's own manifest, and the narration is synthesised from
its own storyboard.

Requires: ffmpeg, and Playwright in a Python that has it (PLAYWRIGHT_PYTHON, or
~/.playwright-venv). Narration uses the system speech synthesiser.

Usage:
    python3 scripts/render_film.py --agent art-generator
    python3 scripts/render_film.py --skill chart_builder --fps 10
    python3 scripts/render_film.py --agent x --no-audio     # picture only
"""
from __future__ import annotations

import argparse
import http.server
import json
import os
import shutil
import socketserver
import subprocess
import re
import sys
import tempfile
import threading
from functools import partial
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WALKTHROUGHS = REPO_ROOT / "media" / "walkthroughs"
BROLL_INDEX = REPO_ROOT / "media" / "broll" / "index.json"
PLATES_INDEX = REPO_ROOT / "media" / "plates" / "index.json"
OUT_DIR = REPO_ROOT / "media" / "videos" / "generated"
PLACEHOLDER = "[operator supplies]"
# The reference carries a music bed from 3.3s, which is why it measures 6%
# silent while a speech-only cut measures 40%. Without it every gap between
# narration lines is true digital silence and the film reads as broken.
BED = REPO_ROOT / "media" / "audio" / "bed.wav"
BED_GAIN = "1.0"   # the bed is already levelled at -28 LUFS
# Disabled. The reference carries a scored bed, but it only has ~9s of
# speech-free music (0->9.37s), and looping that to 132s produced a seam every
# 5.4s that reads as a second voice competing with the narration. Silence
# between lines is honest; a stuttering loop is not. Re-enable when a licensed
# continuous bed exists.
# Re-enabled. The looped 5.4s corpus clip is gone; the bed is now
# synthesised continuous by RAPPtranscript2Prototype's score.py — royalty-free,
# deterministic, deliberately featureless, and written at -28 LUFS so it sits
# under narration rather than competing with it.
USE_BED = os.environ.get("RAPPVISION_BED", "1") == "1"
# Absolute second each act's narration may begin, measured from the reference.
VO_ENTRY = {"problem": 9.4}

# The reference specification, measured — not chosen.
W, H, FPS = 1920, 1080, 30
V_BITRATE = "6000k"
A_BITRATE = "192k"
TARGET_LUFS = -18.6
TARGET_TP = -3.2

VOICE = os.environ.get("RAPPVISION_VOICE", "Samantha")
WPM = int(os.environ.get("RAPPVISION_WPM", "168"))
# Kokoro-82M, via the HyperFrames CLI. af_nova reads as a measured
# corporate narrator, which is the register the reference recordings use.
KOKORO_VOICE = os.environ.get("RAPPVISION_KOKORO_VOICE", "af_nova")
# 0.86 delivers 2.10 words/sec, measured against the reference's own rate.
# 0.95 read at 2.36 and sounded rushed beside it.
KOKORO_SPEED = os.environ.get("RAPPVISION_KOKORO_SPEED", "0.86")
# The reference reads 254 words across 120.7 seconds of narration. Speed is a
# knob; this is the thing the knob is turned to reach.
TARGET_WPS = 2.10


def run(cmd: list[str], why: str = "", check: bool = True, **kw):
    """Run a tool and SHOW its error. A render pipeline that swallows ffmpeg's
    stderr cannot be iterated on — the failure just reappears as a missing
    file three steps later."""
    r = subprocess.run(cmd, capture_output=True, **kw)
    if check and r.returncode != 0:
        err = r.stderr.decode(errors="replace").strip().splitlines()
        tail = "\n    ".join(err[-6:]) if err else "(no stderr)"
        print(f"  [ffmpeg] {why or cmd[0]} failed:\n    {tail}", file=sys.stderr)
    return r


def playwright_python() -> str:
    alt = os.environ.get("PLAYWRIGHT_PYTHON")
    if alt:
        return alt
    for cand in (Path.home() / ".playwright-venv" / "bin" / "python",
                 REPO_ROOT / ".venv" / "bin" / "python"):
        if cand.is_file():
            return str(cand)
    return sys.executable


def serve() -> tuple[socketserver.TCPServer, int]:
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(REPO_ROOT))
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    srv.allow_reuse_address = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


CAPTURE = r'''
import json, sys
from playwright.sync_api import sync_playwright

url, out_dir, spec = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
W, H = spec["w"], spec["h"]

with sync_playwright() as p:
    b = p.chromium.launch(args=["--force-device-scale-factor=1",
                                "--hide-scrollbars", "--disable-lcd-text"])
    # vision.html needs headroom for its transport; screen.html is the frame
    # itself and must be EXACTLY the box, or its composer falls off the bottom
    # and the capture gets squashed into the plate.
    pad = 0 if (spec.get("ready") or spec.get("region")) else 260
    pg = b.new_page(viewport={"width": W, "height": H + pad},
                    device_scale_factor=1)
    if spec.get("radius"):
        # Round the surface to the screen it replaces. A square patch over a
        # rounded display fills the bezel's radius and reads as bursting out of
        # the frame; these corners come out transparent, so the bezel shows.
        pg.add_init_script("""
          window.addEventListener('DOMContentLoaded', function(){
            var st = document.createElement('style');
            // html transparent, body still WHITE. Making both transparent
            // rounded the patch and hollowed it out at the same time: every
            // pixel our own elements did not paint showed the reference's UI
            // straight through, including its scrollbar at x=1780.
            st.textContent = 'html{background:transparent!important}' +
              'body{border-radius:__R__px;overflow:hidden;background:#fff}';
            document.head.appendChild(st);
          });
        """.replace("__R__", str(spec["radius"])))
    pg.goto(url, wait_until="load")
    if spec.get("ready"):
        pg.wait_for_function("() => " + spec["ready"].replace("window.", "window."),
                             timeout=30000)
    else:
        pg.wait_for_selector("#stage", timeout=30000)
    # The stage is the frame. Force it to exactly the output size so a rendered
    # pixel is an output pixel — scaling text after the fact is what makes a
    # generated film look generated.
    if not spec.get("ready"):
      pg.evaluate("""(d) => {
        const s = document.getElementById('stage');
        s.style.width = d.w + 'px';
        s.style.height = d.h + 'px';
        s.style.aspectRatio = 'auto';
        s.style.borderRadius = '0';
        document.querySelectorAll('.scene').forEach(function(e){
            e.style.transition = 'none';
        });
      }""", {"w": W, "h": H})
    pg.wait_for_timeout(400)

    stage = None if spec.get("ready") else pg.locator("#stage")
    for i, t in enumerate(spec["times"]):
        # Not every overlay page has a timeline: the lozenge is static, the
        # screen and the overview seek. Drive whichever exists.
        pg.evaluate("""(t) => {
            if (typeof paint === 'function') { T = t; paint(); }
        }""", t)
        pg.wait_for_timeout(spec["settle"])
        if stage is not None:
            stage.screenshot(path=f"{out_dir}/f{i:05d}.png", animations="disabled")
        else:
            pg.screenshot(path=f"{out_dir}/f{i:05d}.png", animations="disabled",
                          omit_background=bool(spec.get("transparent")))
    b.close()
print("captured", len(spec["times"]))
'''


CALIBRATION = REPO_ROOT / "media" / "plates" / "calibration.json"
OVERLAYS = REPO_ROOT / "media" / "plates" / "overlays.json"
BASE_SOURCE = Path.home() / "Desktop" / "aibast_bible" / "videos"


def load_plate() -> dict | None:
    """The plate and where the screen sits on it.

    A hand-measured rect was close but not right — the overlay overflowed the
    bezel. align.html lets the framing be set visually against the plate and
    exported; when that file is present it WINS, because an eye on the actual
    frame beats a bright-pixel heuristic.
    """
    plate = None
    if PLATES_INDEX.is_file():
        for p in json.loads(PLATES_INDEX.read_text(encoding="utf-8")).get("plates", []):
            if (REPO_ROOT / p["file"]).is_file():
                plate = dict(p)
                break
    if CALIBRATION.is_file():
        cal = json.loads(CALIBRATION.read_text(encoding="utf-8"))
        rect = cal.get("screen_rect")
        if rect:
            plate = plate or {"file": cal.get("plate", "media/plates/laptop-copilot.png")}
            if cal.get("plate"):
                plate["file"] = cal["plate"]
            plate["screen_rect"] = rect
            plate["corner_radius"] = cal.get("corner_radius", 0)
            plate["calibrated"] = True
    if plate and not (REPO_ROOT / plate["file"]).is_file():
        return None
    return plate


def capture(url: str, times: list[float], out_dir: Path, settle: int = 30,
            width: int | None = None, height: int | None = None,
            ready: str | None = None, transparent: bool = False,
            radius: int = 0) -> int:
    script = Path(tempfile.mkdtemp()) / "cap.py"
    script.write_text(CAPTURE, encoding="utf-8")
    spec = json.dumps({"w": width or W, "h": height or H, "times": times,
                       "settle": settle, "ready": ready,
                       "region": bool(width or height),
                       "transparent": bool(transparent),
                       "radius": int(radius)})
    r = run([playwright_python(), str(script), url, str(out_dir), spec])
    if r.returncode != 0:
        raise SystemExit("frame capture failed:\n" + r.stderr.decode()[-1500:])
    return len(times)


def narrate(text: str, out: Path) -> float:
    """Synthesise one narration line. Returns its duration in seconds.

    Kokoro-82M through the HyperFrames CLI, which is a neural voice and the
    single biggest perceptual difference between a generated film and the
    professional recordings. The platform synthesiser is the fallback so the
    pipeline still runs where the model is not installed — it is audibly
    worse, and the run says so rather than quietly shipping it.
    """
    if not text.strip():
        return 0.0
    wav = out.with_suffix(".wav")
    env = {**os.environ, "HYPERFRAMES_PYTHON": os.environ.get(
        "HYPERFRAMES_PYTHON", str(Path.home() / ".playwright-venv" / "bin" / "python"))}

    # A fixed speed constant does not give a fixed speaking RATE. Kokoro shortens
    # its inter-sentence pauses on longer input, so one setting produced 2.30
    # words per second on the short line and 2.96 on the long one — and the long
    # one is the seventy-second walkthrough, which finished thirty-two seconds
    # early and left the act playing to silence. So aim at the reference's
    # measured rate and correct against what actually came back.
    # Pace with PAUSES, never by slowing the voice.
    #
    # Reaching the reference's 2.10 words/sec by turning Kokoro's speed knob
    # down worked arithmetically and sounded drunk — a long line needed 0.61,
    # which stretches the phonemes themselves. A narrator hitting a slower rate
    # does not slur; they leave more air between sentences. So: synthesise each
    # sentence at one natural speed, then space them.
    sentences = [x.strip() for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x.strip()]
    words = len(text.split())
    target = words / TARGET_WPS
    pieces, spoken = [], 0.0
    for n, sent in enumerate(sentences):
        part = out.parent / f"{out.stem}-s{n}.wav"
        run(["npx", "hyperframes", "tts", sent, "-v", KOKORO_VOICE,
             "-s", str(KOKORO_SPEED), "-o", str(part)],
            why="neural narration", check=False, env=env, cwd=str(REPO_ROOT))
        if not part.is_file():
            pieces = []
            break
        d = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(part)], check=False)
        try:
            spoken += float(d.stdout.decode().strip())
        except ValueError:
            pass
        pieces.append(part)

    if pieces:
        # Spread the shortfall evenly across the gaps, within what reads as a
        # breath rather than a stall.
        gaps = max(1, len(pieces) - 1)
        gap = min(1.6, max(0.28, (target - spoken) / gaps))
        sil = out.parent / f"{out.stem}-gap.wav"
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
             f"anullsrc=r=24000:cl=mono:d={gap:.3f}", str(sil)], check=False)
        listing = out.parent / f"{out.stem}-list.txt"
        joined = []
        for n, part in enumerate(pieces):
            if n:
                joined.append(sil)
            joined.append(part)
        listing.write_text("".join(f"file '{p}'\n" for p in joined), encoding="utf-8")
        run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
             "-i", str(listing), "-c:a", "pcm_s16le", "-ar", "48000",
             str(wav)], why="join narration", check=False)
        for f in pieces + [sil, listing]:
            f.unlink(missing_ok=True)
    else:
        run(["npx", "hyperframes", "tts", text, "-v", KOKORO_VOICE,
             "-s", str(KOKORO_SPEED), "-o", str(wav)],
            why="neural narration", check=False, env=env, cwd=str(REPO_ROOT))

    if not wav.is_file():
        print("  [voice] neural TTS unavailable — falling back to the platform "
              "voice, which is audibly worse", file=sys.stderr)
        aiff = out.with_suffix(".aiff")
        r = run(["say", "-v", VOICE, "-r", str(WPM), "-o", str(aiff), text],
                check=False)
        if r.returncode != 0 or not aiff.is_file():
            return 0.0
        wav = aiff

    run(["ffmpeg", "-v", "error", "-y", "-i", str(wav),
         "-ac", "2", "-ar", "48000", "-c:a", "aac", "-b:a", A_BITRATE, str(out)],
        why="encode narration")
    wav.unlink(missing_ok=True)
    probe = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(out)])
    try:
        return float(probe.stdout.decode().strip())
    except ValueError:
        return 0.0


def pick_broll(industries: list[str], category: str) -> Path | None:
    if not BROLL_INDEX.is_file():
        return None
    idx = json.loads(BROLL_INDEX.read_text(encoding="utf-8"))
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from cut_broll import bucket_for
    want = bucket_for(industries) if industries else bucket_for([category])
    clips = [c for c in idx["clips"] if c["industry_bucket"] == want] or \
            [c for c in idx["clips"] if c["industry_bucket"] == "cross_industry"] or \
            idx["clips"]
    return (REPO_ROOT / clips[0]["path"]) if clips else None


GEOMETRY = REPO_ROOT / "media" / "plates" / "base-geometry.json"


def load_overlays() -> dict | None:
    """The base track and the boxes we replace on it.

    This is the architecture that made the films work: keep the professional
    recording — its cinematography, transitions, Microsoft intro, b-roll and
    motion — and composite our content only over the boxes that carry
    agent-specific material.

    Which boxes, and when, is MEASURED from the base recording itself
    (scripts/measure_base.py), never hand-set. Hand-set rects are what put a
    chat panel over a presenter's chest for the last seven seconds of the shot
    and left 66px of the reference's own nav rail showing down our left edge
    for seventy-eight. A rect that describes someone else's cut has to be read
    off that cut.
    """
    if not OVERLAYS.is_file():
        return None
    ov = json.loads(OVERLAYS.read_text(encoding="utf-8"))
    if not GEOMETRY.is_file():
        print("  [base] no measured geometry — run scripts/measure_base.py",
              file=sys.stderr)
        return None
    tracks = json.loads(GEOMETRY.read_text(encoding="utf-8"))["tracks"]
    m = tracks.get(ov["base_track"])
    if not m:
        print(f"  [base] {ov['base_track']} is not measured", file=sys.stderr)
        return None

    regions, missing = [], []
    for rid, source in (("title", "lozenge"), ("overview", "overview"),
                        ("screen", "screen")):
        act = m.get(rid)
        if not act:
            missing.append(rid)
            continue
        # The card replaces the whole frame; the other two replace exactly the
        # thing they cover, at the extent it actually reaches.
        # Which rect is right depends on WHICH LAPTOP is underneath.
        #
        # calibration.json was set visually against media/plates/laptop-copilot.png
        # — our own plate. This path composites onto the professional
        # recording's laptop, which is a different and larger screen. Using the
        # plate's rect here leaves the reference's own nav rail showing beside
        # ours, guillotined to single letters. So the base path uses the
        # measured extent of the screen it is actually covering.
        #
        # The measured rect is also why the picture looked like it burst its
        # frame: it is a square rectangle laid over a screen whose corners are
        # rounded, so it filled the bezel's radius. That is fixed by rounding
        # the patch, not by shrinking it — see corner_radius below.
        rect = ({"x": 0, "y": 0, "w": W, "h": H} if rid == "overview"
                else act.get("rect") or act["envelope"])
        regions.append({"id": rid, "source": source, "rect": rect,
                        "window": {"start": act["start"], "end": act["end"]},
                        # Matching the base's own dissolve: our patch has to
                        # leave when the shot under it does, not after.
                        "fade_seconds": 0.25 if rid == "title" else 0.35,
                        # Measured off the reference's own screen: its corner
                        # inset runs 29px over 30px of height.
                        "corner_radius": 30 if rid == "screen" else 0,
                        "measured": True})
    if missing:
        print(f"  [base] unmeasured acts: {', '.join(missing)}", file=sys.stderr)
        return None
    return {**ov, "regions": regions, "geometry_source": "measured"}


def find_base(track_id: str) -> Path | None:
    """The full-resolution recording behind a proxy id."""
    if not BASE_SOURCE.is_dir():
        return None
    want = re.sub(r"[^a-z0-9]+", "", track_id.lower())
    for f in sorted(BASE_SOURCE.glob("*.mp4")):
        stem = re.sub(r"^[#0-9-]+", "", f.stem)
        if re.sub(r"[^a-z0-9]+", "", stem.lower()) == want:
            return f
    return None


def render_over_base(story: dict, subject: dict, ov: dict, work: Path,
                     fps: int, out: Path) -> bool:
    """Composite our regions onto the professional cut."""
    base = find_base(ov["base_track"])
    if not base:
        print(f"  [base] no recording for {ov['base_track']}", file=sys.stderr)
        return False

    srv, port = serve()
    kind = subject["kind"]
    ref = subject["ref"]
    try:
        inputs, filters, prev = ["-i", str(base)], [], "[0:v]"
        idx = 1
        for region in ov["regions"]:
            if not region.get("enabled", True):
                continue
            r, win = region["rect"], region["window"]
            span = win["end"] - win["start"]
            sub = work / f"reg-{region['id']}"
            sub.mkdir(parents=True, exist_ok=True)

            page = {"lozenge": "lozenge.html", "screen": "screen.html",
                    "overview": "vision.html"}[region["source"]]
            q = f"?{'skill' if kind == 'skill' else 'agent'}={ref}"
            if region["source"] == "overview":
                q += "&overlay=overview"
            if region["source"] == "screen":
                # The page schedules its exchanges against the act it is
                # actually laid over, not the storyboard's nominal timeline.
                q += f"&t0={win['start']}&t1={win['end']}"
            url = f"http://127.0.0.1:{port}/{page}{q}"

            # A held card needs a handful of frames; a scrolling conversation
            # needs every one of them, or it plays back as a stutter.
            rfps = FPS if region["source"] == "screen" else max(fps, 2)
            n = max(2, int(span * rfps))
            times = [win["start"] + (i / rfps) for i in range(n)]
            ready = "window.__ready" if region["source"] in ("lozenge", "screen") else None
            capture(url, times, sub, settle=30,
                    width=r["w"], height=r["h"], ready=ready,
                    transparent=region["source"] in ("lozenge", "screen"),
                    radius=region.get("corner_radius") or 0)

            inputs += ["-framerate", str(rfps), "-i", str(sub / "f%05d.png")]
            fade = region.get("fade_seconds", 0.3) or 0.01
            filters.append(
                f"[{idx}:v]format=rgba,fps={FPS},"
                f"fade=t=in:st=0:d={fade}:alpha=1,"
                f"fade=t=out:st={max(0.01, span - fade):.2f}:d={fade}:alpha=1,"
                f"setpts=PTS-STARTPTS+{win['start']}/TB[r{idx}]")
            filters.append(
                f"{prev}[r{idx}]overlay={r['x']}:{r['y']}:"
                f"enable='between(t,{win['start']},{win['end']})'[v{idx}]")
            prev = f"[v{idx}]"
            idx += 1

        picture = work / "picture.mp4"
        run(["ffmpeg", "-v", "error", "-y", *inputs,
             "-filter_complex", ";".join(filters),
             "-map", prev, "-an",
             "-c:v", "libx264", "-preset", "slow",
             # True CBR. A bare -b:v undershot to 1.85 Mbps on this mostly
             # graphic content while the reference sits at 5.95, and mixing a
             # min/max with nal-hrd=cbr is contradictory so x264 ignored it.
             "-b:v", V_BITRATE, "-minrate", V_BITRATE, "-maxrate", V_BITRATE,
             "-bufsize", V_BITRATE, "-x264-params", "nal-hrd=cbr:force-cfr=1",
             "-pix_fmt", "yuv420p", str(picture)], why="composite over base")
        if not picture.is_file():
            return False
        picture.replace(out)
        return True
    finally:
        srv.shutdown()


def base_audio_profile(track_id: str | None) -> dict:
    """The base recording's own silence and loudness, if it has been measured.

    Constants here were wrong twice — a bed running under the opening and
    closing Microsoft logos where the professional films are silent, and a
    loudness target three decibels under the recording it sits beside. Both are
    properties of the base, so both are read off it.
    """
    if not (track_id and GEOMETRY.is_file()):
        return {}
    t = json.loads(GEOMETRY.read_text(encoding="utf-8"))["tracks"].get(track_id)
    return (t or {}).get("audio") or {}


def mux(picture: Path, audio_parts: list, clock: float, out: Path,
        track_id: str | None = None) -> None:
    """Lay narration and the bed over a finished picture at reference specs."""
    if not audio_parts and not (USE_BED and BED.is_file()):
        run(["ffmpeg", "-v", "error", "-y", "-i", str(picture),
             "-c", "copy", str(out)], why="copy picture")
        return
    inputs, filters, labels = [], [], []
    for i, (f, start, _d) in enumerate(audio_parts):
        inputs += ["-i", str(f)]
        filters.append(f"[{i + 1}:a]adelay={int(start * 1000)}|{int(start * 1000)}[a{i}]")
        labels.append(f"[a{i}]")
    prof = base_audio_profile(track_id)
    head = float(prof.get("head_silent_until") or 0.0)
    tail = float(prof.get("tail_silent_from") or clock)
    target = float(prof.get("integrated_lufs") or TARGET_LUFS)

    if USE_BED and BED.is_file():
        bi = len(audio_parts) + 1
        inputs += ["-i", str(BED)]
        # The bed comes up as the logo clears and is gone before the end card,
        # which is what the base does. It used to start at zero.
        bed_in = max(0.0, head - 0.1)
        bed_out = max(bed_in + 1.0, tail - 1.2)
        filters.append(
            f"[{bi}:a]atrim=0:{clock},volume={BED_GAIN},"
            f"adelay={int(bed_in * 1000)}|{int(bed_in * 1000)},"
            f"afade=t=in:st={bed_in:.2f}:d=1.2,"
            f"afade=t=out:st={bed_out:.2f}:d=1.2[bed]")
        labels.append("[bed]")
    # loudnorm is gated and will lift a quiet passage, so the silences are
    # enforced AFTER it rather than assumed to survive it.
    gate = (f"volume=enable='lt(t,{max(0.0, head - 0.15):.2f})':volume=0,"
            f"volume=enable='gt(t,{tail:.2f})':volume=0")
    mixf = (";".join(filters) + ";" + "".join(labels) +
            f"amix=inputs={len(labels)}:dropout_transition=0:normalize=0[m];"
            f"[m]loudnorm=I={target}:TP={TARGET_TP}:LRA=7,{gate},"
            f"apad,atrim=0:{clock},aresample=48000[a]")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(picture), *inputs,
         "-filter_complex", mixf, "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", A_BITRATE,
         "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(out)],
        why="mux audio")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--agent")
    ap.add_argument("--skill")
    ap.add_argument("--fps", type=int, default=10,
                    help="capture rate for the animated act (output is always 30)")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--keep", action="store_true", help="keep the working directory")
    ap.add_argument("--no-base", action="store_true",
                    help="build the acts instead of compositing over a recording")
    ap.add_argument("--allow-placeholders", action="store_true",
                    help="render an internal review cut with slots unfilled")
    args = ap.parse_args()

    if not (args.agent or args.skill):
        ap.error("give --agent or --skill")
    kind = "skill" if args.skill else "agent"
    slug = args.skill or args.agent

    story_file = WALKTHROUGHS / f"{kind}-{slug}.json"
    if not story_file.is_file():
        raise SystemExit(f"no storyboard at {story_file.relative_to(REPO_ROOT)}")
    story = json.loads(story_file.read_text(encoding="utf-8"))
    subject = story["subject"]

    # An unresolved slot renders the mail-merge field into the picture. The
    # storyboard already says approval is required before rendering; honour it.
    blob = json.dumps(story["scenes"])
    if PLACEHOLDER in blob and not args.allow_placeholders:
        n = blob.count(PLACEHOLDER)
        raise SystemExit(
            f"refusing to render: {n} unresolved '{PLACEHOLDER}' slot(s) would be "
            f"burned into the picture. Fill them via the remix values, or pass "
            f"--allow-placeholders for an internal review cut.")

    work = Path(tempfile.mkdtemp(prefix="rappvision-"))
    frames = work / "frames"
    frames.mkdir()

    # Preferred path: keep the professional cut and replace only our boxes.
    ov = load_overlays()
    if ov and not args.no_base:
        picture = work / "base-picture.mp4"
        if render_over_base(story, subject, ov, work, args.fps, picture):
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            out = OUT_DIR / f"{kind}-{slug}.mp4"
            clock = float(subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(picture)],
                capture_output=True, text=True).stdout.strip() or 137.0)
            audio_parts = []
            if not args.no_audio:
                # The storyboard's act times describe a 137s film we no longer
                # make; the base is 132.4s and its acts are measured. Speaking
                # to the storyboard's clock put narration over the wrong shots.
                acts = {r["id"]: r["window"] for r in ov["regions"]}
                for scene in story["scenes"]:
                    if not scene.get("narration"):
                        continue
                    vo = work / f"vo-{scene['act']}.m4a"
                    dur = narrate(scene["narration"], vo)
                    if not dur:
                        continue
                    win = acts.get({"overview": "overview",
                                    "walkthrough": "screen"}.get(scene["act"], ""))
                    if win:
                        at = win["start"] + 0.5
                    elif scene["act"] == "close" and acts.get("screen"):
                        # The close begins when the laptop shot ends, whatever
                        # second that is on this cut.
                        at = acts["screen"]["end"] + 0.4
                    else:
                        at = max(scene["start"] + 0.6,
                                 VO_ENTRY.get(scene["act"], 0.0))
                    audio_parts.append((vo, at, dur))
            mux(picture, audio_parts, clock, out, ov["base_track"])
            if out.is_file():
                print(f"[film] {out.relative_to(REPO_ROOT)} · "
                      f"{out.stat().st_size / 1048576:.1f} MB · base "
                      f"{ov['base_track']} · {len(ov['regions'])} regions composited")
                shutil.rmtree(work, ignore_errors=True)
                return 0
        print("  [base] compositing failed — falling back to built acts",
              file=sys.stderr)

    srv, port = serve()
    url = (f"http://127.0.0.1:{port}/vision.html?"
           f"{'skill' if kind == 'skill' else 'agent'}={subject['ref']}")

    try:
        acts = {s["act"]: s for s in story["scenes"]}
        parts: list[Path] = []
        audio_parts: list[tuple[Path, float, float]] = []   # file, start, duration
        clock = 0.0

        broll = pick_broll(subject.get("industries") or [], subject.get("category", ""))

        for scene in story["scenes"]:
            act = scene["act"]
            span = scene["end"] - scene["start"]
            seg = work / f"{act}.mp4"

            if act == "problem" and broll:
                # Licensed footage, trimmed or held to the act's exact length.
                # One continuous take, never looped: restarting a 15s clip
                # inside a 17s act produced a jump-cut that read as hectic.
                # If the clip is short, hold the last frame rather than replay.
                run(["ffmpeg", "-v", "error", "-y", "-i", str(broll),
                     # Real time, always. Retiming footage to fill an act is
                     # what made the b-roll read as slow motion.
                     "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                            f"crop={W}:{H},fps={FPS}",
                     "-t", f"{span}",
                     "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                     "-pix_fmt", "yuv420p", str(seg)], why="b-roll act")
            else:
                sub = frames / act
                sub.mkdir()
                if act == "walkthrough":
                    n = max(2, int(span * args.fps))
                    times = [scene["start"] + (i / args.fps) for i in range(n)]
                    plate = load_plate()
                    if plate:
                        # Render the SCREEN only, then composite it into the real
                        # laptop from the professional footage. The bezel, the
                        # desk, the lighting and the gradient are photography;
                        # only what is on the display is generated.
                        r = plate["screen_rect"]
                        screen_url = url.replace("vision.html", "screen.html")
                        capture(screen_url, times, sub, settle=25,
                                width=r["w"], height=r["h"], ready="window.__ready")
                        run(["ffmpeg", "-v", "error", "-y",
                             "-loop", "1", "-i", str(REPO_ROOT / plate["file"]),
                             "-framerate", str(args.fps), "-i", str(sub / "f%05d.png"),
                             "-filter_complex",
                             f"[0:v][1:v]overlay={r['x']}:{r['y']}:shortest=1,fps={FPS}",
                             "-t", f"{span}",
                             "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                             "-pix_fmt", "yuv420p", str(seg)], why="composite screen")
                    else:
                        capture(url, times, sub, settle=25)
                        run(["ffmpeg", "-v", "error", "-y", "-framerate", str(args.fps),
                             "-i", str(sub / "f%05d.png"),
                             "-vf", f"fps={FPS}", "-c:v", "libx264", "-preset", "slow",
                             "-crf", "18", "-pix_fmt", "yuv420p", str(seg)],
                            why="encode walkthrough")
                else:
                    # Every act animates now, so every act is a sequence. A
                    # single held frame is what made 88% of the cut frozen.
                    n = max(2, int(span * args.fps))
                    times = [scene["start"] + (i / args.fps) for i in range(n)]
                    capture(url, times, sub, settle=25)
                    run(["ffmpeg", "-v", "error", "-y", "-framerate", str(args.fps),
                         "-i", str(sub / "f%05d.png"),
                         "-vf", f"fps={FPS}", "-c:v", "libx264", "-preset", "slow",
                         "-crf", "18", "-pix_fmt", "yuv420p", str(seg)],
                        why=f"{act} act")

            if not seg.is_file():
                raise SystemExit(f"act {act} produced no video")
            parts.append(seg)

            if not args.no_audio and scene.get("narration"):
                vo = work / f"vo-{act}.m4a"
                dur = narrate(scene["narration"], vo)
                if dur:
                    # The reference holds the title card and the opening of the
                    # b-roll in silence and enters at 9.4s. Starting every act's
                    # narration 0.6s in put the first line at 5.6s.
                    at = max(clock + 0.6, VO_ENTRY.get(act, 0.0))
                    audio_parts.append((vo, at, dur))
            clock += span

        concat = work / "list.txt"
        concat.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
        picture = work / "picture.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
             "-i", str(concat), "-c", "copy", str(picture)], why="concat acts")

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out = OUT_DIR / f"{kind}-{slug}.mp4"

        if audio_parts:
            # Lay each narration line at its act's start, then normalise the mix
            # to the reference's measured loudness.
            inputs, filters, labels = [], [], []
            for i, (f, start, _d) in enumerate(audio_parts):
                inputs += ["-i", str(f)]
                filters.append(f"[{i + 1}:a]adelay={int(start * 1000)}|{int(start * 1000)}[a{i}]")
                labels.append(f"[a{i}]")
            if BED.is_file():
                # Looped, faded in at 3.2s like the reference, and ducked so it
                # sits under the voice rather than competing with it.
                bed_idx = len(audio_parts) + 1
                # The bed is now a continuous 140s cut with no internal
                # silences, so it is not looped — looping a 6s clip put an
                # audible dropout in the mix roughly 22 times.
                inputs += ["-i", str(BED)]
                filters.append(
                    f"[{bed_idx}:a]atrim=0:{clock},volume={BED_GAIN},"
                    f"adelay=3200|3200,afade=t=in:st=3.2:d=1.2,"
                    f"afade=t=out:st={clock - 2.5}:d=2.5[bed]")
                labels.append("[bed]")
            # Filterchains are ';'-separated. Joining them bare produced one
            # unparseable chain and ffmpeg reported it as "trailing garbage".
            mix = (";".join(filters) + ";" + "".join(labels) +
                   f"amix=inputs={len(labels)}:dropout_transition=0:normalize=0[m];"
                   f"[m]loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA=7,"
                   # Pad to the picture. Without this the narration is the
                   # shorter stream and -shortest cut a 137s film to 48s.
                   f"apad,atrim=0:{clock},aresample=48000[a]")
            run(["ffmpeg", "-v", "error", "-y", "-i", str(picture), *inputs,
                 "-filter_complex", mix, "-map", "0:v", "-map", "[a]",
                 "-c:v", "libx264", "-preset", "slow", "-b:v", V_BITRATE,
                 "-maxrate", "8000k", "-bufsize", "12000k",
                 "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", A_BITRATE,
                 "-ar", "48000", "-ac", "2",
                 "-movflags", "+faststart", str(out)], why="mux with narration")
        else:
            run(["ffmpeg", "-v", "error", "-y", "-i", str(picture),
                 "-c:v", "libx264", "-preset", "slow", "-b:v", V_BITRATE,
                 "-maxrate", "8000k", "-bufsize", "12000k",
                 "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)], why="mux picture only")

        if not out.is_file():
            raise SystemExit("assembly produced no file")
        size = out.stat().st_size / 1048576
        print(f"[film] {out.relative_to(REPO_ROOT)} · {size:.1f} MB · "
              f"{len(parts)} acts · b-roll: {broll.name if broll else 'none'}")
        return 0
    finally:
        srv.shutdown()
        if args.keep:
            print(f"[film] working directory kept at {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
