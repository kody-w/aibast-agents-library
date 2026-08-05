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
KOKORO_SPEED = os.environ.get("RAPPVISION_KOKORO_SPEED", "0.95")


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
    pg = b.new_page(viewport={"width": W, "height": H + 260},
                    device_scale_factor=1)
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
        pg.evaluate("(t) => { T = t; paint(); }", t)
        pg.wait_for_timeout(spec["settle"])
        if stage is not None:
            stage.screenshot(path=f"{out_dir}/f{i:05d}.png", animations="disabled")
        else:
            pg.screenshot(path=f"{out_dir}/f{i:05d}.png", animations="disabled")
    b.close()
print("captured", len(spec["times"]))
'''


def load_plate() -> dict | None:
    if not PLATES_INDEX.is_file():
        return None
    plates = json.loads(PLATES_INDEX.read_text(encoding="utf-8")).get("plates", [])
    for p in plates:
        if (REPO_ROOT / p["file"]).is_file():
            return p
    return None


def capture(url: str, times: list[float], out_dir: Path, settle: int = 30,
            width: int | None = None, height: int | None = None,
            ready: str | None = None) -> int:
    script = Path(tempfile.mkdtemp()) / "cap.py"
    script.write_text(CAPTURE, encoding="utf-8")
    spec = json.dumps({"w": width or W, "h": height or H, "times": times,
                       "settle": settle, "ready": ready})
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
    r = run(["npx", "hyperframes", "tts", text, "-v", KOKORO_VOICE,
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--agent")
    ap.add_argument("--skill")
    ap.add_argument("--fps", type=int, default=10,
                    help="capture rate for the animated act (output is always 30)")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--keep", action="store_true", help="keep the working directory")
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

    work = Path(tempfile.mkdtemp(prefix="rappvision-"))
    frames = work / "frames"
    frames.mkdir()
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
                     "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                            f"crop={W}:{H},fps={FPS},"
                            f"tpad=stop_mode=clone:stop_duration={span}",
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
                    mid = scene["start"] + span / 2
                    capture(url, [mid], sub, settle=250)
                    run(["ffmpeg", "-v", "error", "-y", "-loop", "1",
                         "-i", str(sub / "f00000.png"), "-t", f"{span}",
                         "-vf", f"fps={FPS}", "-c:v", "libx264", "-preset", "slow",
                         "-crf", "18", "-pix_fmt", "yuv420p", str(seg)])

            if not seg.is_file():
                raise SystemExit(f"act {act} produced no video")
            parts.append(seg)

            if not args.no_audio and scene.get("narration"):
                vo = work / f"vo-{act}.m4a"
                dur = narrate(scene["narration"], vo)
                if dur:
                    # Start narration a beat into the act so it does not clip the cut.
                    audio_parts.append((vo, clock + 0.6, dur))
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
