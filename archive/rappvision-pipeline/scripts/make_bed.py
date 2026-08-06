#!/usr/bin/env python3
"""Synthesise a music bed that is not a hum.

The previous bed was built from sustained sine partials — 55, 82, 131 and 165 Hz
held for the whole film. Arithmetically that is a chord; audibly it is a hum,
and it measured correctly at -28 LUFS the entire time it was ruining the film.
Loudness was never the problem. Held narrow-band energy was.

So this bed has no sustained partials at all. It is filtered noise, shaped:

  * a wide low-mid band, so it reads as room rather than as pitch
  * slow amplitude movement from several incommensurate LFOs, so it never
    settles into a texture the ear can lock onto and start hearing as a tone
  * a gentle high shelf rolled off, so nothing competes with speech sibilance
  * measured for tonal prominence before it is written, using the same test the
    film gate uses — if it reads as tonal, it does not get saved

The result sits under narration the way a score does and fills the gaps between
lines, which is what the reference does and what silence cannot do.

Output: media/audio/bed.wav

Usage:
    python3 scripts/make_bed.py
    python3 scripts/make_bed.py --seconds 140 --lufs -30
"""
from __future__ import annotations

import argparse
import sys
import wave
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / "media" / "audio" / "bed.wav"
SR = 48000
SEED = 20260805          # deterministic: the same bed every build


def tonal_prominence(a, sr):
    """Highest narrow-band peak above its local median, in dB. The gate's test."""
    import numpy as np
    seg = sr * 4
    worst = 0.0
    for st in range(sr * 2, max(sr * 2 + 1, len(a) - seg), seg * 3):
        chunk = a[st:st + seg]
        if len(chunk) < seg:
            break
        sp = np.abs(np.fft.rfft(chunk * np.hanning(seg)))
        fr = np.fft.rfftfreq(seg, 1 / sr)
        band = (fr > 35) & (fr < 2000)
        db = 20 * np.log10(np.maximum(sp[band], 1e-12))
        k = max(3, len(db) // 40)
        med = np.array([np.median(db[max(0, i - k):i + k]) for i in range(len(db))])
        worst = max(worst, float((db - med).max()))
    return worst


def build(seconds: float, lufs: float):
    import numpy as np
    rng = np.random.default_rng(SEED)
    n = int(seconds * SR)
    t = np.arange(n) / SR

    noise = rng.normal(0.0, 1.0, n)

    # Two one-pole low-passes in series give a gentle 12 dB/oct roll-off with no
    # resonant peak — a biquad here would put a bump at its corner, which is
    # exactly the kind of thing that starts to read as pitch.
    def onepole(x, fc):
        a = np.exp(-2 * np.pi * fc / SR)
        y = np.empty_like(x)
        acc = 0.0
        for i in range(len(x)):
            acc = (1 - a) * x[i] + a * acc
            y[i] = acc
        return y

    try:
        from scipy.signal import lfilter                 # noqa: F401
        import scipy.signal as sig

        def lp(x, fc):
            b, a = sig.butter(2, fc / (SR / 2), btype="low")
            return sig.filtfilt(b, a, x)

        def hp(x, fc):
            b, a = sig.butter(2, fc / (SR / 2), btype="high")
            return sig.filtfilt(b, a, x)

        body = lp(hp(noise, 90), 900)
        air = lp(hp(noise, 1800), 6000) * 0.14
    except ImportError:
        body = onepole(noise, 900)
        body = body - onepole(body, 90)
        air = (noise - onepole(noise, 1800)) * 0.06

    bed = body + air

    # Slow movement from incommensurate periods, so the envelope never repeats
    # inside the film and the ear never settles.
    env = np.ones(n) * 0.72
    for period, depth in ((17.3, 0.16), (26.9, 0.11), (41.7, 0.08), (7.1, 0.05)):
        env += depth * np.sin(2 * np.pi * t / period + period)
    bed *= env

    # Normalise to an approximate integrated loudness. This bed sits under
    # narration; it is not meant to be noticed, only missed when absent.
    rms = float(np.sqrt(np.mean(bed ** 2)))
    bed *= (10 ** (lufs / 20)) / max(rms, 1e-9)

    fade = int(SR * 1.5)
    bed[:fade] *= np.linspace(0, 1, fade)
    bed[-fade:] *= np.linspace(1, 0, fade)
    return np.clip(bed, -0.95, 0.95)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seconds", type=float, default=140.0)
    ap.add_argument("--lufs", type=float, default=-30.0,
                    help="approximate level; the bed sits under narration")
    args = ap.parse_args()

    try:
        import numpy as np
    except ImportError:
        print("[bed] needs numpy", file=sys.stderr)
        return 1

    bed = build(args.seconds, args.lufs)
    prom = tonal_prominence(bed, SR)
    print(f"[bed] tonal prominence {prom:.1f} dB "
          f"(the drone this replaces measured 51.2 dB; the gate fails above 14)")
    if prom >= 12.0:
        print("[bed] refusing to write a bed that reads as tonal", file=sys.stderr)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pcm = (bed * 32767).astype("<i2")
    stereo = np.repeat(pcm[:, None], 2, axis=1).tobytes()
    with wave.open(str(OUT), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo)
    print(f"[bed] {OUT.relative_to(REPO_ROOT)} · {args.seconds:.0f}s · "
          f"~{args.lufs} dB, no sustained partials")
    return 0


if __name__ == "__main__":
    sys.exit(main())
