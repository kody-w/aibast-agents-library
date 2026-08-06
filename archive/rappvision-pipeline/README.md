# RAPPVision film pipeline — archived

Parked on 2026-08-05. This generated demo films by compositing our own content
over three boxes on a professional recording. It is kept because the *findings*
are expensive and the *code* is not — a replacement pipeline should not have to
rediscover any of what is written down here.

Nothing in this folder runs from where it now sits: paths inside these files are
relative to the repository root, not to this directory. Read them, do not
resurrect them.

## What is still live, and is not here

Do not move these into the archive; the site serves them.

| Path | Why it stays |
|---|---|
| `media/videos/*.mp4` | The 48 professional demo recordings the solution catalog plays. Nothing here produced them. |
| `scripts/host_demos.py` | Transcodes those 48 into the repo. Works; unrelated to film generation. |
| `scripts/build_walkthrough.py` | Generates the storyboards the one-pager renders. Run by CI. |
| `media/walkthroughs/` | Those storyboards. |
| `media/jewels/` | Brand marks cropped from the corpus, used by `vision.html`. |
| `vision.html` | The storyboard player, linked as "Film" in the site nav. |

## What is here

```
scripts/render_film.py         the compositor: base track + three overlay regions
scripts/measure_base.py        measures each recording — act windows, geometry, audio
scripts/probe_base.py          earlier, coarser act detection (superseded by measure_base)
scripts/make_bed.py            synthesises a non-tonal music bed
scripts/harvest_jewels.py      crops brand marks out of the corpus, keyed by unpremultiplying
scripts/cut_broll.py           selects b-roll by industry
tests/check_film_fidelity.py   16 gates comparing a render against the base it sits on
tools/align.html               visual calibration of overlay rects and windows
tools/edit.html                cutting room: scrub, mark in/out, speed, volume
tools/screen.html              the Copilot surface composited into the laptop
tools/lozenge.html             the gradient title lozenge
media/plates/                  base tracks, measured geometry, calibration
media/audio/                   music beds
media/broll/                   licensed b-roll by industry
media/generated-films/         the films this produced (git-ignored)
```

## Read this before building the replacement

Every item below cost hours and is invisible until someone looks at the right
thing. They are ordered by how badly each one bites.

**Gate on the base recording, not on a specification.** The original checks
measured the container — resolution, frame rate, bitrate, loudness, silent
spans. All of them stayed green while a patch sat 66px inside the screen it was
replacing, leaving the reference's own navigation rail visible for 78 seconds.
A container statistic cannot see geometry. `check_film_fidelity.py` compares
candidate against base at the pixel and at the second: every patch must *cover*
what it replaces and must not *spill* past it, and must leave when its shot
leaves.

**Measure the base; never hand-set a rect or a window.** Hand calibration
describes one laptop. `media/plates/calibration.json` was set against our own
plate (`laptop-copilot.png`) — a different and smaller screen than the one in
the recordings — and using it on the base composite leaked the reference's UI
down the left edge. The measured extent for that cut is `x122 y46 w1670 h1006`.

**A square patch over a rounded display bursts its frame.** The screen's corner
inset runs 29px over 30px of height. Round the patch to a 30px radius so the
corners are transparent and the bezel shows through. Then teach the coverage
check about the radius, or it reports the rounding as a 30px gap.

**Scene detection misses cross-dissolves.** `ffmpeg scdet` reports no cut where
the professional cuts dissolve between the card and the laptop, so a window
built from cuts ran the chat panel from 17s to the end of the film. Classify
every frame by what is on it instead; a half-dissolved frame satisfies no
signature, so boundaries land after the dissolve resolves — exactly where an
overlay should start.

**Loudness is not the same as tonality.** The first music bed was four sustained
sine partials at 55, 82, 131 and 165 Hz. It measured correctly at -28 LUFS the
entire time it was ruining the film, because the problem was held narrow-band
energy, not level. It measured 51 dB above its spectral neighbours; the
professional reference measures none. `make_bed.py` builds moving band-limited
noise instead, and `T-FILM-NO-HUM` fails anything with a tone that persists at
one frequency across many windows.

**Never hit a speaking rate by slowing the voice.** Kokoro's speed knob had to
drop to 0.61 to reach the reference's 2.10 words/second on a long line, which
stretches phonemes and sounds drunk. A narrator reaching a slower rate leaves
more air between sentences. Synthesise per sentence at one natural speed and
pace with silence.

**Do not retime footage.** B-roll slowed with `setpts` to fill an act reads as
slow motion.

**Overlay frame rate is per region.** Capturing overlays at 6fps into a 30fps
film holds every frame five times, and the only act that moves — the chat —
judders. Held cards cost nothing at a low rate; the conversation needs every
frame.

**A block reveal is not motion.** Revealing an answer block by block left the
picture identical for seconds at a time: 2 unique frames per 8 seconds against
the reference's ~20. Stream the text in character by character, as the product
does, and let the panel scroll with it.

**Type the slots that feed sentences.** A panel caption dropped into a noun slot
produced "It pulls data from Runs on what the operator already has open" spoken
aloud. And a third-person verb in an infinitive slot produced "needs to handles
account intelligence" and "It can improves conversion" — convert once, at the
source, not at each site. The obvious fix for that (strip a trailing "s") ate a
letter off ordinary verbs and shipped "the agent can rais margin"; only a stem
ending in a sibilant takes "-es".

**A demo may not assert a figure it cannot support.** No percentages, currency,
or unit counts. Qualitative claims only — "improves", "accelerates", "below
target".

**Nothing internal reaches the picture.** "Engages you in the local brainstem
chat" named our own implementation in a Microsoft-branded customer film.

**Never run two renders against one output path.** Two concurrent runs
deadlocked on the output file; one had been muxing a stale picture for 39
minutes on what is a 4-second stream copy.

## Where it stood when it was parked

The last render passed all 16 of its own gates and an independent frame-by-frame
review still returned **NOT RELEASABLE**. That gap is the most useful thing in
this folder: a green suite is evidence that the things you thought to check are
right, and nothing more. Two of the findings below are defects the gates were
structurally incapable of seeing, and one is a fix that reported success without
taking effect.

Confirmed fixed by that review, so the replacement should keep the approach:
the hum is gone (no persistent narrow-band peak at any frequency); narration is
not time-stretched (2.02 Hz modulation, faster than the reference's 1.84); the
streaming reveal works (1229 unique frames across the walkthrough against the
reference's 126); the horizontal patch extent, act boundaries and on-screen copy
are all correct.

Still open, worst first:

1. **The reference's own screen is legible through our patch as it fades out**
   (113.17–113.47s, ~10 frames): `Deal value $2.4M`, `Win probability 68%`,
   `Stakeholders 8 mapped`, a raw function name, and a person's first name. Our
   content is clean; what leaks is theirs. **A fade is a window in which the
   thing underneath is visible, and every content rule the film obeys is
   suspended for its duration.** Cut, or hold opaque to the base's own cut.
2. **The corner radius never took effect.** The render has a hard right angle at
   x122 y46. It was implemented, it was gated, the gate passed, and it is not in
   the picture — the gate measured the coverage shortfall the radius *would*
   cause and read its absence as tolerance. A gate that can pass on the absence
   of the thing it is checking is worse than no gate.
3. **The patch erases the laptop's bottom bezel**: our white runs to y1051 where
   the reference's screen content ends at y≈1030, painting ~28,500px per frame
   over the bezel for the whole 71-second act. The measured extent was taken as
   a union across the act and over-reached vertically; measure the *content*
   edge, not the brightest row.
4. **The bed is broadband but far too hot** — only 8.6–10.7 dB below programme
   peaks in the presence and air bands, against the reference's 38–53 dB. Fixing
   the tonality was necessary and not sufficient; it now reads as hiss. Gate the
   spectral *floor-to-peak* ratio per band, not just tonality and integrated
   loudness.
5. **Both act-2 dissolves superimpose our card on the base's own card** — two
   "Agent overview" titles, two Copilot marks, contradictory panel copy. Same
   root cause as 1.
6. Product logos on the overview card are damaged: the Dynamics mark is severed
   in two, Teams and Outlook are clipped with a stray dark bar beneath each. The
   keying in `harvest_jewels.py` needs a tighter search box per mark.
7. The send control is a blank blue circle with no glyph.
8. "Steps" renders a bullet *and* a number on every line.
9. The answer is circular — `1. Handle account intelligence / 2. Improve
   conversion` restates the agent's job title where the reference delivers an
   actual briefing. It passes every honesty rule and still demonstrates process
   rather than substance. **Qualitative is a constraint on claims, not a licence
   to say nothing.**

## Reference measurements

Taken from `10-Account Intelligence Agent.mp4`, the cut most of this was
calibrated against.

| | |
|---|---|
| Container | 1920x1080, 29.97 fps, 132.366s, ~6 Mbps |
| Loudness | -15.3 LUFS integrated, 4.5 LU range |
| Silence | head to 2.99s, tail from 131.63s |
| Narration | 254 words across ~120s ≈ 2.10 words/sec |
| Title lozenge | 1084x296 at (418,392), on 2.70–7.27s |
| Overview card | 22.0–42.75s; panels at 29.17% of frame height, 55.65% tall, three columns 25.36% wide at 6.25% / 37.86% / 69.43% |
| Laptop screen | 43.0–113.5s; display x122 y46 w1670 h1006, corner radius 30px |
| Walkthrough motion | ~20 unique frames per 8 seconds |
