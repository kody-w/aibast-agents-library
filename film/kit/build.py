#!/usr/bin/env python3
"""Assemble the film: cut the picture, mix the audio, mux, and write a beatmap.

Picture is hard cuts and short dips only. Nothing is motion-interpolated and no
read is ever sped up. `minterpolate` between two frames of different text warps
pixels along estimated motion vectors and produces unreadable soup; it shipped
once and the rule exists because of it. Card and screen stages therefore hard-
cut to each other, and only the boundary between beats dips, for 0.35s.

Audio is the contract in film/AUDIO.md and every clause of it is load-bearing:

  * every stem is trimmed onto one reference level before the +6 dB bus gain,
    because per-take level varies by about 2 dB and one quiet slot fails the
    -19 dB floor on its own;
  * `aformat=...:stereo` is applied to every input BEFORE any amix, because
    amix adopts the FIRST input's layout and a mono voice bus silently
    collapses a stereo bed to mono;
  * the bed is mixed against a half-loop-offset copy of itself, because the
    loop has a 20 dB trough four seconds in and a cut landing there reads as
    dead audio;
  * `alimiter` carries `level=disabled`, because its default `level=true`
    makes it a normaliser that lifts peaks to the ceiling - lowering the
    ceiling then makes clipping worse, not better;
  * loudnorm is never used.

Output: film/projects/<slug>/dist/<output>.mp4, dist/voice.json
        (+ _NOBED.mp4 with --voice-only)
        film/projects/<slug>/work/beatmap.json
Usage:
    python3 film/kit/build.py --project supplier-risk-watch
    python3 film/kit/build.py --project supplier-risk-watch --voice-only
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (BED, BRAND, BROLL, FPS, H, STINGS, VENC, W,  # noqa: E402
                    load_project, mean_db, probe_duration, require_tools, run)

M = BRAND["motion"]
GRADE = M["broll_grade"]
NAVY = "0x%02X%02X%02X" % tuple(BRAND["palette"]["navy_stage"])

# Per-take level varies; every stem is trimmed onto this reference before the
# bus gain. This is per-take balancing, not loudness normalisation.
STEM_REF = -20.6
STEM_TRIM_LIMIT = 2.5
BED_LOOP = 19.0099          # measured, film/AUDIO.md
BED_HALF = BED_LOOP / 2


# --------------------------------------------------------------------- picture
def seg_clip(dst: Path, src: Path, seconds: float, grade: bool = False) -> None:
    g = "," + GRADE if grade else ""
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-filter_complex",
         f"[0:v]trim=0:{seconds:.3f},setpts=PTS-STARTPTS,"
         f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
         f"fps={FPS},setsar=1{g}[out]", "-map", "[out]"] + VENC + [str(dst)])


def seg_broll(dst: Path, clips: list) -> None:
    """Hard-cut montage. Shots run 2.5-5.5s in the reference; keep them there."""
    args = ["ffmpeg", "-y", "-v", "error"]
    for name, _ in clips:
        args += ["-i", str(BROLL / name)]
    parts, labels = [], []
    for i, (_, d) in enumerate(clips):
        parts.append(f"[{i}:v]trim=0:{d:.3f},setpts=PTS-STARTPTS,"
                     f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                     f"crop={W}:{H},fps={FPS},setsar=1,{GRADE}[v{i}]")
        labels.append(f"[v{i}]")
    parts.append("".join(labels) + f"concat=n={len(clips)}:v=1:a=0[out]")
    args += ["-filter_complex", ";".join(parts), "-map", "[out]"] + VENC + [str(dst)]
    run(args)


def seg_title(dst: Path, clip: str, seconds: float, overlay: Path) -> None:
    """Title lozenge over b-roll washed back behind a scrim."""
    run(["ffmpeg", "-y", "-v", "error", "-i", str(BROLL / clip),
         "-loop", "1", "-framerate", str(FPS), "-t", f"{seconds:.3f}",
         "-i", str(overlay), "-filter_complex",
         f"color=c={NAVY}:s={W}x{H}:r={FPS}:d={seconds:.3f}[scrim];"
         f"[0:v]trim=0:{seconds:.3f},setpts=PTS-STARTPTS,"
         f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
         f"fps={FPS},setsar=1,eq=contrast=1.02:saturation=0.60:brightness=-0.04[bg];"
         f"[bg][scrim]blend=all_mode=normal:all_opacity={M['title_scrim_opacity']}[dark];"
         f"[1:v]format=rgba,fps={FPS},"
         f"fade=in:st=0.20:d={M['title_overlay_fade_in']}:alpha=1[ov];"
         f"[dark][ov]overlay=0:0:shortest=1,"
         f"fade=out:st={seconds - 0.35:.3f}:d=0.35[out]",
         "-map", "[out]"] + VENC + [str(dst)])


def seg_stills(dst: Path, pngs: list, total: float, overlay: Path | None = None,
               fade: float | None = None) -> None:
    """Hold a sequence of stills across one beat, hard-cutting between them.

    Stage lengths are equal by default. The gate fails any frame held longer
    than five seconds, so a long beat needs more stages, not a longer hold.
    """
    fade = M["card_fade_seconds"] if fade is None else fade
    n = len(pngs)
    each = total / n
    args = ["ffmpeg", "-y", "-v", "error"]
    for p in pngs:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{each:.3f}", "-i", str(p)]
    parts, labels = [], []
    for i in range(n):
        parts.append(f"[{i}:v]scale={W}:{H},fps={FPS},setsar=1,format=yuv420p[s{i}]")
        labels.append(f"[s{i}]")
    parts.append("".join(labels) + f"concat=n={n}:v=1:a=0[cat]")
    tail = "[cat]"
    if overlay is not None:
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{total:.3f}",
                 "-i", str(overlay)]
        parts.append(f"[{n}:v]format=rgba,fps={FPS},"
                     f"fade=in:st=0.35:d={M['chyron_fade_in']}:alpha=1,"
                     f"fade=out:st={total - 0.9:.3f}:d={M['chyron_fade_out']}:alpha=1[cy]")
        parts.append("[cat][cy]overlay=0:0:shortest=1[ov]")
        tail = "[ov]"
    parts.append(f"{tail}fade=in:st=0:d={fade},"
                 f"fade=out:st={total - fade:.3f}:d={fade}[out]")
    args += ["-filter_complex", ";".join(parts), "-map", "[out]"] + VENC + [str(dst)]
    run(args)


def build_picture(project: dict, reuse: bool = False) -> tuple:
    seg_dir = project["_work"] / "seg"
    seg_dir.mkdir(parents=True, exist_ok=True)
    cards = project["_work"] / "cards"
    screens = project["_work"] / "screens"
    card_idx = json.loads((cards / "index.json").read_text())
    screen_idx = json.loads((screens / "index.json").read_text())

    files, t, plan = [], 0.0, []
    for beat in project["beats"]:
        dst = seg_dir / f"{beat['id']}.mp4"
        kind = beat["kind"]
        if reuse and dst.exists():
            pass
        elif kind == "sting":
            seg_clip(dst, STINGS / beat["clip"], beat["dur"])
        elif kind == "broll":
            seg_broll(dst, [(c["file"], c["dur"]) for c in beat["clips"]])
        elif kind == "title":
            seg_title(dst, beat["clip"], beat["dur"],
                      cards / card_idx[beat["card"]][0])
        elif kind == "card":
            pngs = [cards / p for p in card_idx[beat["card"]]]
            seg_stills(dst, pngs, beat["dur"])
        elif kind == "demo":
            pngs = [screens / p for p in screen_idx[beat["question"]]]
            ov = cards / card_idx[beat["chyron"]][0] if beat.get("chyron") else None
            seg_stills(dst, pngs, beat["dur"], overlay=ov, fade=0.25)
        else:
            raise SystemExit(f"beat {beat['id']}: unknown kind {kind!r}")
        actual = probe_duration(dst)
        plan.append(dict(beat, t0=round(t, 3), actual=round(actual, 3)))
        t += actual
        files.append(dst)
        print(f"  {beat['id']:5s} {t - actual:7.2f} +{actual:6.2f}  {beat['note']}")

    lst = seg_dir / "concat.txt"
    lst.write_text("\n".join(f"file '{f.name}'" for f in files))
    picture = seg_dir / "picture.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(lst), "-c", "copy", str(picture)])
    return picture, round(t, 3), plan


# ----------------------------------------------------------------------- audio
def bed_chain(total: float, bed_db: float) -> list:
    """Two copies of the loop, half a loop apart, then compressed and set.

    The loop is 19.01s long and drops about 20 dB four to six seconds in. One
    copy of it means any beat that lands in that window reads as dead audio.
    Offsetting a second copy by half a loop takes the measured range from
    20.8 dB to 7.6 dB across a minute.
    """
    return [
        f"[0:a]aformat=fltp:48000:stereo,atrim=0:{total:.3f},asetpts=N/SR/TB[bedA]",
        f"[1:a]aformat=fltp:48000:stereo,atrim={BED_HALF:.4f}:{BED_HALF + total:.3f},"
        f"asetpts=N/SR/TB[bedB]",
        "[bedA][bedB]amix=inputs=2:normalize=0:duration=first,volume=-4dB,"
        "acompressor=threshold=0.03:ratio=4:attack=20:release=500:makeup=1,"
        f"volume={bed_db}dB[bedraw]",
    ]


def build_audio(project: dict, plan: list, total: float, dst: Path) -> list:
    vo_dir = project["_work"] / "vo"
    slots = [b for b in plan if b.get("vo")]
    bed_db = project.get("bed_db", 0.0)
    args = ["ffmpeg", "-y", "-v", "error",
            "-stream_loop", "-1", "-i", str(BED),
            "-stream_loop", "-1", "-i", str(BED)]
    for b in slots:
        args += ["-i", str(vo_dir / f"{b['vo']}.wav")]

    parts, labels, marks = [], [], []
    for i, b in enumerate(slots, start=2):
        at = b["t0"] + b.get("off", 0.0)
        ms = int(round(at * 1000))
        raw = mean_db(vo_dir / f"{b['vo']}.wav")
        trim = 0.0 if raw is None else max(-STEM_TRIM_LIMIT,
                                           min(STEM_TRIM_LIMIT, STEM_REF - raw))
        # stereo BEFORE amix - see the module docstring
        parts.append(f"[{i}:a]aformat=fltp:48000:stereo,volume={trim:.2f}dB,"
                     f"volume=6dB,adelay={ms}|{ms}[n{i}]")
        labels.append(f"[n{i}]")
        d = probe_duration(vo_dir / f"{b['vo']}.wav")
        marks.append([b["vo"], round(at, 2), round(d, 2)])
        print(f"    {b['vo']:6s} stem {raw:6.1f} dB  trim {trim:+.2f} dB  @ {at:6.2f}s")

    parts.append("".join(labels) +
                 f"amix=inputs={len(slots)}:normalize=0:duration=longest,"
                 f"apad,atrim=0:{total:.3f},asetpts=N/SR/TB[vo]")
    parts += bed_chain(total, bed_db)
    parts.append("[vo]asplit=2[vo1][vo2]")
    parts.append("[bedraw][vo1]sidechaincompress=threshold=0.015:ratio=8:"
                 "attack=25:release=450:makeup=1[duck]")
    parts.append(f"[duck][vo2]amix=inputs=2:normalize=0:duration=first,"
                 f"alimiter=limit=0.95:level=disabled,"
                 f"afade=in:st=0:d=1.2,afade=out:st={total - 2.2:.3f}:d=2.0,"
                 f"apad,atrim=0:{total:.3f},asetpts=N/SR/TB[mix]")
    args += ["-filter_complex", ";".join(parts), "-map", "[mix]",
             "-c:a", "pcm_s16le", str(dst)]
    run(args)
    return marks


def build_nobed(project: dict, marks: list, video: Path, out: Path) -> None:
    """Voice-only variant, in two steps, with the video not an input to step 1.

    A single-command version indexed the stems as [0:a], [1:a]... while ffmpeg
    input 0 was the VIDEO, so the finished film's own audio was mixed back in
    as if it were a stem and the last stem was dropped. It sounded like two
    tracks talking over each other while every measurement said it was clean.
    """
    vo_dir = project["_work"] / "vo"
    total = probe_duration(video)
    target = -16.0
    inputs, filters, labels = [], [], []
    for i, (slot, at, _dur) in enumerate(marks):
        src = vo_dir / f"{slot}.wav"
        gain = target - (mean_db(src) or target)
        delay = int(at * 1000)
        inputs += ["-i", str(src)]
        filters.append(
            f"[{i}:a]aformat=fltp:48000:stereo,"
            f"afftdn=nr=24:nf=-48,"                       # room tone out first
            f"agate=threshold=0.0025:ratio=9:attack=5:release=90:knee=2,"
            f"volume={gain:.2f}dB,afade=t=in:st=0:d=0.04,"
            f"adelay={delay}|{delay}[a{i}]")
        labels.append(f"[a{i}]")
    graph = (";".join(filters) + ";" + "".join(labels) +
             f"amix=inputs={len(labels)}:normalize=0,"
             f"alimiter=limit=0.95:level=disabled,apad,atrim=0:{total:.3f}[out]")
    narr = project["_work"] / "narration.wav"
    run(["ffmpeg", "-y", "-v", "error"] + inputs +
        ["-filter_complex", graph, "-map", "[out]", "-ac", "2", "-ar", "48000",
         str(narr)])
    run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-i", str(narr),
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
         "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(out)])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", required=True)
    ap.add_argument("--reuse", action="store_true",
                    help="keep picture segments that already exist")
    # Renamed from --nobed, which read as "build this film without a bed" and
    # was written into the handoff as exactly that. It never meant it: the
    # delivered mp4 always carries the bed at project.bed_db, and the flag only
    # asks for an EXTRA voice-only file alongside it. Measured on the 2026-08-05
    # build, whose bed-only gaps sat at -26.6 to -28.0 dB with the flag on.
    ap.add_argument("--voice-only", dest="voice_only", action="store_true",
                    help="ALSO write <slug>_NOBED.mp4, the same picture with "
                         "the narration and no bed. The main film is unchanged "
                         "and still carries the bed.")
    args = ap.parse_args()
    require_tools()
    project = load_project(args.project)
    project["_dist"].mkdir(parents=True, exist_ok=True)

    print(f"[{project['slug']}] picture:")
    picture, total, plan = build_picture(project, reuse=args.reuse)
    print(f"[{project['slug']}] picture total {total:.2f}s")

    print(f"[{project['slug']}] audio:")
    wav = project["_work"] / "seg" / "mix.wav"
    marks = build_audio(project, plan, total, wav)

    out = project["_dist"] / project["output"]
    run(["ffmpeg", "-y", "-v", "error", "-i", str(picture), "-i", str(wav),
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
         "-b:a", "192k", "-movflags", "+faststart", str(out)])

    beatmap = {"schema": "aibast-showcase-film-beatmap/1.0",
               "slug": project["slug"], "total": total,
               "bed_db": project.get("bed_db", 0.0),
               "beats": plan, "vo_marks": marks}
    if args.voice_only:
        nobed = out.with_name(out.stem + "_NOBED.mp4")
        build_nobed(project, marks, out, nobed)
        beatmap["nobed"] = nobed.name
        print(f"[OK] wrote {nobed}")
    (project["_work"] / "beatmap.json").write_text(json.dumps(beatmap, indent=1))

    # Voice provenance travels with the film. The gate refuses a film that
    # cannot prove which voice spoke it, because no measurement of the audio
    # can tell macOS `say` from a neural voice.
    src = project["_work"] / "vo" / "voice.json"
    if not src.exists():
        raise SystemExit("no work/vo/voice.json - narrate.py did not record "
                         "which voice it used. Re-run narrate.py; the film "
                         "cannot be gated without it.")
    (project["_dist"] / "voice.json").write_text(src.read_text())
    print(f"[OK] wrote {out}  {total:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
