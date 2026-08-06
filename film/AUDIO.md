# The audio contract

Every clause here is load-bearing and three of them exist because a mix
shipped wrong. The contract is implemented in `film/kit/build.py` and checked
in `film/kit/gate.py`; this document is why, not what.

## The chain

```
each narration stem
  -> aformat=fltp:48000:stereo          stereo BEFORE any amix
  -> volume=<trim>dB                    per-take balance onto one reference
  -> volume=6dB                         the bus gain
  -> adelay=<slot start>

the bed, twice
  -> copy A from 0, copy B from 9.5049  half a loop apart
  -> amix, volume=-4dB
  -> acompressor=threshold=0.03:ratio=4:attack=20:release=500:makeup=1
  -> volume=<bed_db>dB

  bed  x  voice -> sidechaincompress=threshold=0.015:ratio=8:attack=25:
                                     release=450:makeup=1
  ducked bed + voice -> amix
                     -> alimiter=limit=0.95:level=disabled
                     -> afade in 1.2s, afade out 2.0s
```

**`loudnorm` is never used.** Not on a stem, not on the bus, not on the
delivered file. It is a two-pass loudness normaliser and it will happily
reshape a mix that was built deliberately.

## Three traps, each of which cost a rebuild

**1. `alimiter` defaults to `level=true`, which makes it a normaliser.** In
that mode it lifts the whole mix until peaks reach the ceiling, so lowering
the ceiling makes clipping *worse*, not better. That is the opposite of what a
limiter is for and it is the default. Always `level=disabled`.

**2. `amix` adopts the FIRST input's channel layout.** A mono narration bus
therefore collapses a stereo bed to mono, silently, with no warning and no
change in any level measurement. Every input is `aformat`-ed to stereo before
it reaches an `amix`. The gate proves it by measuring side-channel energy
(`pan=mono|c0=0.5*c0-0.5*c1`); a genuinely stereo programme sits well above
−70 dB, a collapsed one is at the noise floor.

**3. The bed loops every 19.0099 s and has a 20 dB trough four seconds in.**
Measured per second across one loop:

| s | 0 | 1 | 2 | 3 | **4** | **5** | **6** | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dB | −21.2 | −22.3 | −23.2 | −31.2 | **−36.6** | **−38.4** | **−35.1** | −19.9 | −18.4 | −19.8 | −18.1 |

A segment cut that lands in that window reads as dead audio. Mixing the bed
against a copy of itself offset by half a loop takes the measured range over a
minute from **20.8 dB to 7.6 dB** using the same material — no new asset, no
crossfade, no ducking artefact.

## Levels

| Measurement | Target | Enforced by |
|---|---|---|
| narration slot mean | > −19.0 dB | `gate.py` per slot, on the delivered file |
| bed-only gap mean | −34 to −22 dB | `gate.py` per gap |
| programme peak | ≤ −0.1 dB | `gate.py` |
| head and tail | true silence | grammar; the logo plays on nothing |

Both bounds on the gap matter. A bed at −50 dB passes a "quieter than −22"
test by a mile while being completely inaudible, which is how a film ends up
with silence under its montage and a green gate. The floor is there to catch
that.

**Per-take balance is not normalisation.** Speech synthesis returns each read
at a slightly different level — a spread of about 2 dB across a script. Each
stem is trimmed onto one reference (−20.6 dB, clamped to ±2.5 dB) *before* the
+6 dB bus gain, so no single slot can fall under the floor on its own. That is
a fader move on a take, not a loudness process on a programme.

## Fit, and the knob that does not exist

A read must land inside its window with air at the tail. When it does not
there are two fixes — widen the window, or shorten the copy — and speeding the
read up is not one of them. Above about 2.6 words per second the delivery is
audibly hurried and stops sounding like the corpus, whose measured cadence is
2.17 words per second over the film and 2.23 while actually speaking.

This kit removes the temptation structurally: `plan.py` computes each beat's
length **from the read that was already synthesised**, so the window is always
wide enough and there is no rate to reach for.

## The voice-only variant

`build.py --voice-only` **also** writes `<slug>_NOBED.mp4`: the same picture
with narration only, so a bed can be laid underneath by hand. The delivered
film is unaffected and still carries the bed — the flag was called `--nobed`,
which read as "build this one without a bed", and it was written into a handoff
as exactly that defect. It never meant it. `make.py` passes it on every build,
and the bed-only gaps of the film it produced on 2026-08-05 measured −26.6 to
−28.0 dB, inside the audible band.

It is built in **two ffmpeg steps, and the video is not an input to the
first**. A single-command version indexed the stems as `[0:a]`, `[1:a]`… while
ffmpeg input 0 was the video — so the finished film's own audio, the same
narration at its own timing plus the bed, was mixed back in as if it were a
stem, and the last stem was silently dropped. Every measurement said the mix
was clean. It sounded like two people reading the same script a second apart.

Per stem, in this order: `afftdn` then `agate` then gain. Denoise and gate
before any gain — gating afterwards does nothing, because the boosted noise
floor clears the threshold.

`dynaudnorm` is the wrong tool here. With a high maximum gain it lifts every
inter-word silence into a constant wash that reads as a second track.

## The bed asset

`film/assets/audio/bed-slow-drift.caf` — 19.009909 s, 44.1 kHz stereo.

It is a copy of a bed that used to be referenced from a macOS system audio
directory, which meant the pipeline only worked on one machine. It now lives
in the repository and is addressed repo-relative. Swapping it is a one-line
change in `film/kit/common.py`, but re-measure the loop length and the trough
first — `BED_LOOP` and `BED_HALF` in `build.py` are that specific file's
numbers, and the half-loop trick only cancels a trough it is aligned to.
