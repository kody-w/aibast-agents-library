#!/usr/bin/env python3
"""Synthesise the narration slots and fit-gate every one of them.

Two engines, in order. Azure Speech neural voice is the default and sounds
like the shipped recordings. It is reached with Entra auth only — every Speech
resource on this subscription has local keys disabled, so there is no key to
find and looking for one wastes an afternoon.

The macOS `say` voice is the fallback for a local dry run, and `--engine azure`
switches the fallback off entirely: it raises rather than quietly producing a
robotic film. That silent fallback is not hypothetical. It shipped a `say`
film that was rejected on sight, and no measurement caught it, because a level
meter cannot tell `say` from neural TTS — both read as "speech". So the engine
that actually spoke is written to `vo/voice.json`, build.py copies it next to
the delivered mp4, and the gate reads it. Provenance, not inference.

The fit-gate is the part that matters. A read must land inside its window with
air at the tail. When it does not, widen the window or re-punctuate the line.
Never speed the read up: over about 2.6 words per second the delivery is
audibly rushed and the film stops sounding like the reference.

Output: film/projects/<slug>/work/vo/<slot>.wav, vo/manifest.json, vo/voice.json
Usage:
    python3 film/kit/narrate.py --project supplier-risk-watch
    python3 film/kit/narrate.py --project supplier-risk-watch --engine say
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (REPO_ROOT, load_project, probe_duration,  # noqa: E402
                    require_tools, run)

# Fast-fail rather than hang. An unreachable endpoint cost 25 seconds a call
# before this cap existed, which is 5 minutes of nothing on an 11-slot film.
PROBE_TIMEOUT = 3.0
SYNTH_TIMEOUT = 60.0
# Above this the delivery is audibly hurried. The band between the two is
# reported but not failed: the local `say` voice quantises its rate, so a
# tenth over is the engine, not the copy.
RUSHED_WPS = 2.6
RUSHED_HARD = 2.9


def az_token() -> str | None:
    try:
        proc = subprocess.run(
            ["az", "account", "get-access-token", "--resource",
             "https://cognitiveservices.azure.com", "--query", "accessToken",
             "-o", "tsv"],
            capture_output=True, text=True, timeout=45)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    tok = proc.stdout.strip()
    return tok if proc.returncode == 0 and len(tok) > 100 else None


def reachable(host: str, port: int = 443) -> bool:
    try:
        with socket.create_connection((host, port), timeout=PROBE_TIMEOUT):
            return True
    except OSError:
        return False


def azure_synth(cfg: dict, token: str, text: str, dst: Path) -> None:
    # SSML is XML. A bare "&" in the copy — "asset reliability & standards" —
    # makes the document malformed and Azure answers 400 for that slot only,
    # which reads like a token problem and is not one.
    text = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    ssml = (f"<speak version='1.0' xml:lang='en-US'>"
            f"<voice name='{cfg['azure_voice']}'>"
            f"<prosody rate='{cfg.get('rate', '-6%')}'>{text}</prosody>"
            f"</voice></speak>")
    req = urllib.request.Request(
        f"https://{cfg['azure_region']}.tts.speech.microsoft.com"
        f"/cognitiveservices/v1",
        data=ssml.encode("utf-8"),
        headers={
            "Authorization": f"aad#{cfg['azure_resource_id']}#{token}",
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "riff-48khz-16bit-mono-pcm",
            "User-Agent": "aibast-showcase-film",
        })
    with urllib.request.urlopen(req, timeout=SYNTH_TIMEOUT) as r:
        dst.write_bytes(r.read())


def say_synth(cfg: dict, text: str, dst: Path) -> None:
    """macOS `say`. Rate is words per minute; the default 175 is too brisk."""
    aiff = dst.with_suffix(".aiff")
    subprocess.run(["say", "-v", cfg.get("say_voice", "Daniel"),
                    "-r", str(cfg.get("say_wpm", 142)), "-o", str(aiff), text],
                   check=True)
    run(["ffmpeg", "-y", "-v", "error", "-i", str(aiff),
         "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(dst)])
    aiff.unlink(missing_ok=True)


def windows(project: dict) -> dict:
    """The seconds each slot has, from the beatmap: beat length minus offset."""
    out = {}
    for beat in project["beats"]:
        if beat.get("vo"):
            out[beat["vo"]] = round(beat["dur"] - beat.get("off", 0.0), 2)
    return out


def resolve(cfg: dict) -> dict:
    """Environment wins over the config file.

    The Speech resource id is an Azure resource path and resource paths do not
    belong in a tracked config file - the gate rejects them on sight. Set
    FILM_SPEECH_RESOURCE_ID (and optionally FILM_SPEECH_REGION,
    FILM_SPEECH_VOICE) in the shell. With none of them set the kit uses the
    local voice, which is a supported way to build, not a degraded one.
    """
    out = dict(cfg)
    for key, var in (("azure_resource_id", "FILM_SPEECH_RESOURCE_ID"),
                     ("azure_region", "FILM_SPEECH_REGION"),
                     ("azure_voice", "FILM_SPEECH_VOICE")):
        if os.environ.get(var):
            out[key] = os.environ[var]
    return out


def synthesise(project: dict, engine: str) -> tuple:
    cfg = resolve(project["voice"])
    if not cfg.get("azure_resource_id") and engine != "say":
        if engine == "azure":
            raise SystemExit("azure engine requested but FILM_SPEECH_RESOURCE_ID "
                             "is not set - see film/README.md")
        print("[OK] no FILM_SPEECH_RESOURCE_ID set - using the local voice")
        engine = "say"
    out_dir = project["_work"] / "vo"
    out_dir.mkdir(parents=True, exist_ok=True)
    token = None
    if engine in ("auto", "azure"):
        host = f"{cfg['azure_region']}.tts.speech.microsoft.com"
        if reachable(host):
            token = az_token()
        if token is None:
            if engine == "azure":
                raise SystemExit("azure engine requested but unreachable or "
                                 "unauthenticated - run `az login`, or use "
                                 "--engine say")
            print("[WARN] Azure Speech unreachable or unauthenticated - "
                  "falling back to the local voice")
    used = "azure" if token else "say"
    print(f"[OK] narration engine: {used}")

    meta = {}
    for slot, text in project["script"].items():
        dst = out_dir / f"{slot}.wav"
        words = len(text.split())
        # Slow the read rather than shorten it, then slow it again. Copy that
        # is dense in short words comes back near 3 w/s at the house rate, and
        # that is audibly hurried against a corpus that sits at 2.17.
        rates = [cfg.get("rate", "-6%"), "-14%", "-22%"]
        used_rate, d = rates[0], None
        for rate in rates:
            attempt = dict(cfg, rate=rate)
            slot_engine = "azure" if token else "say"
            if token:
                try:
                    azure_synth(attempt, token, text, dst)
                except (urllib.error.URLError, TimeoutError, OSError) as exc:
                    # Under --engine azure this is fatal. Half a film in the
                    # neural voice and half in `say` is not a blemish, it is a
                    # film nobody can ship, and the only trace it ever left was
                    # one manifest field reading "mixed".
                    if engine == "azure":
                        raise SystemExit(
                            f"{slot}: azure synthesis failed ({exc}). "
                            f"--engine azure does not fall back to the local "
                            f"voice. Renew the token (`source "
                            f"film/.env.local`) and run it again.")
                    print(f"[WARN] {slot}: azure failed ({exc}); local voice")
                    say_synth(cfg, text, dst)
                    slot_engine, used = "say", "mixed"
            else:
                say_synth(dict(cfg, say_wpm=cfg.get("say_wpm", 132)), text, dst)
            d = probe_duration(dst)
            used_rate = rate
            if words / d <= RUSHED_WPS or not token:
                break
        meta[slot] = {"dur": round(d, 2), "words": words,
                      "wps": round(words / d, 2), "engine": slot_engine,
                      "rate": used_rate, "text": text}
    return meta, used


def write_provenance(project: dict, meta: dict, used: str, cfg: dict) -> Path:
    """Record which voice actually spoke, beside the narration it spoke.

    The gate reads this file and refuses a film without it. That is not
    bureaucracy: `volumedetect` cannot tell macOS `say` from a neural voice -
    both read as speech at the same level - so provenance is the only evidence
    that exists. build.py copies this next to the delivered mp4.
    """
    path = project["_work"] / "vo" / "voice.json"
    path.write_text(json.dumps({
        "provider": used,
        "voice": cfg["azure_voice"] if used == "azure" else cfg.get("say_voice"),
        "region": cfg.get("azure_region") if used == "azure" else None,
        "slots": len(meta),
        "engine_per_slot": {k: v.get("engine") for k, v in meta.items()},
        "rate_per_slot": {k: v.get("rate") for k, v in meta.items()},
        "written_by": "film/kit/narrate.py",
    }, indent=1) + "\n")
    return path


def fit_gate(project: dict, meta: dict) -> list:
    """Every read must land inside its window with air at the tail."""
    win = windows(project)
    tail = project.get("fit_tail_seconds", 0.35)
    problems = []
    print("\n  slot     read     window   spare   w/s   verdict")
    for slot, m in meta.items():
        w = win.get(slot)
        if w is None:
            problems.append(f"{slot}: synthesised but no beat claims it")
            continue
        spare = round(w - m["dur"], 2)
        verdict = "ok"
        if spare < tail:
            verdict = "OVERRUNS"
            problems.append(
                f"{slot}: read {m['dur']:.2f}s does not fit its {w:.2f}s window "
                f"(need {tail:.2f}s tail) - widen the beat or shorten the copy")
        elif m["wps"] > RUSHED_WPS:
            verdict = "brisk" if m["wps"] <= RUSHED_HARD else "RUSHED"
            if m["wps"] > RUSHED_HARD:
                # DO NOT change this back to "shorten the copy". Words per
                # second measures the VOICE'S SPEAKING RATE, not how much copy
                # the window holds, and the two are not the same lever:
                #
                #     w/s = words / read      and     window = read + lead + tail
                #
                # so deleting words shrinks the read by roughly the same
                # fraction and w/s barely moves. Measured on this project:
                # 30 words -> 25 words took a slot from 2.99 to 3.01 w/s, i.e.
                # WORSE. What lowers w/s is more pauses at the same word count
                # - a comma, an em dash, a full stop - because the synthesiser
                # lengthens the read without changing `words`. 3.01 -> 2.95 and
                # green, on a line of identical length. narrate.py also retries
                # at a slower prosody rate for the same reason.
                problems.append(
                    f"{slot}: {m['wps']:.2f} w/s is above {RUSHED_HARD} - "
                    "break the line into shorter sentences (commas, em dashes, "
                    "full stops) so the read lengthens at the same word count. "
                    "Shortening the copy does NOT lower w/s, and speeding the "
                    "read is never the answer")
        print(f"  {slot:7s} {m['dur']:6.2f}s  {w:6.2f}s  {spare:+6.2f}  "
              f"{m['wps']:4.2f}  {verdict}")
    for slot in win:
        if slot not in meta:
            problems.append(f"{slot}: a beat claims this slot but the script "
                            "has no line for it")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", required=True)
    ap.add_argument("--engine", choices=("auto", "azure", "say"), default="auto")
    args = ap.parse_args()
    require_tools()
    project = load_project(args.project)
    meta, used = synthesise(project, args.engine)
    if project.get("beats"):
        problems = fit_gate(project, meta)
    else:
        problems = []
        print("[OK] no beatmap yet - film/kit/plan.py computes the windows "
              "from these reads, so the fit gate runs there")
    (project["_work"] / "vo" / "manifest.json").write_text(
        json.dumps({"engine": used, "slots": meta}, indent=1))
    prov = write_provenance(project, meta, used, resolve(project["voice"]))
    total = sum(m["dur"] for m in meta.values())
    print(f"\n[OK] {len(meta)} slots, {total:.1f}s of narration, engine {used}")
    print(f"[OK] voice provenance -> {prov.relative_to(REPO_ROOT)}")
    if problems:
        print(f"[WARN] {len(problems)} fit problem(s):")
        for p in problems:
            print("  ", p)
        return 1
    print("[OK] fit gate green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
