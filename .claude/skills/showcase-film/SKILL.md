---
name: showcase-film
description: >
  Produce a catalog-quality showcase film from any source — an agent, an app, a
  portal, a process. The full pipeline: derive grammar from reference films,
  write the beatmap, capture, narrate, mix, gate. Trigger on any request for a
  showcase, demo film, sizzle reel, walkthrough or customer-facing video.
---

# Making a showcase film that holds up

**In this repository the whole capability is ported and self-contained.** Start
at `film/README.md`; the grammar is `film/GRAMMAR.md`, the mix contract is
`film/AUDIO.md`, live capture is `film/CAPTURE.md`, and the eleven modules are
`film/kit/`. The source recordings are `film/corpus/videos/` (full resolution)
and `media/videos/` (960x540, what the site serves). Nothing the pipeline needs
lives outside the repository — `python3 film/kit/gate.py --cold-start` proves it.

Reference bar: `film/corpus/reference/` if present, otherwise any recording in
`film/corpus/videos/`. The bar to match is 1920x1080, 30fps, stereo 48kHz,
programme peak at or under -0.1dB, every narration slot above -19dB.

## 0. Verify claims about the reference, including mine

Everything in this file that is a measurement carries the measurement. Where it
does not, it is flagged UNVERIFIED. Honour that distinction and extend it:
when a subagent reports a finding about the corpus, **re-measure it yourself
before acting on it**. A wrong belief about the reference propagates into every
film you build from it.

Verified, reproducible — these are `agent.py facts`, and if this file and that
file ever disagree, **the agent is right and this file is wrong**:
- corpus audio: stereo 48kHz, mean -19.4 to -23.1dB, peaks -1.7 to -6.1dB
  (8 films; an earlier "-1.1 to -3.2dB" here came from a 3-film sample)
- bed `film/assets/audio/bed-slow-drift.caf`: 19.009909s long, trough -36.7dB
  at 4s and -38.4dB at 5s against -18 to -24.1dB elsewhere
- `ffmpeg -h filter=alimiter` -> `level <boolean> auto level (default true)`
- cards are navy **#070E27** with pink->violet gradient tiles (#E9608C ->
  #C64BC4 -> #8880F5) and a magenta->violet title lozenge; the demo pane sits
  on a violet stage (#8300F4 -> #150951). Sampled from ask-hr-agent at t=50s
  and t=130s, 2026-08-05, and held in `film/brand/brand.json`. A kit build
  once shipped WHITE cards and passed every gate.

## 1. Derive the grammar — never assume it

If a catalog of reference films exists (here: `film/corpus/videos/`, 48
recordings), **measure it**: sample 5+ films at 1Hz across their whole timelines,
classify every frame by border signature, and check the segment order agrees
across all of them. Measure cross-dissolves off the luma ramp.

**VERIFIED 2026-08-05 across 19 recordings** by `film/kit/harvest.py --scan`,
which is the reproducible measurement — border-signature classification at 1Hz,
coalesced into segments. The order is identical in all 19:

`logo -> b-roll -> overview card -> demo -> close card -> logo`

Proportions, mean of 18 (the one four-agent suite is an outlier and excluded):
**S1 18.1% · S2 12.2% · S3 56.4% · S4 12.9%**. Duration median 159.6s, range
142.1-178.3s. The logo head is 3s in every one of the 19.

An earlier version of this skill carried a different segment claim from a
subagent report and flagged it UNVERIFIED. It was close on order and wrong on
proportion. The numbers above are measured; re-run the scan rather than trust
either.

**The AIBAST catalog films ARE narrated.** Measured across eight of them:
stereo 48kHz, mean -19.4 to -23.1dB, peaks -1.7 to -6.1dB, with the level
swinging 8.2dB (-17.3 to -25.5) across **1-second windows taken from t=20s** —
the signature of speech with sentence pauses, not a flat music bed.

**Measure it with 1-second windows, and skip the head.** Three-second windows
average speech back to flat: a narrated film measured a 2.3dB spread that way
and read as "bed", which reproduces the exact false conclusion below. And
measuring from t=0 samples the silent head, so the dramatic -58 -> -39 -> -18
ramp once cited here as proof of speech was only the fade-in and would look
identical on a music-only film. `agent.py verify-reference` does it correctly.

An earlier version of this skill claimed the corpus had "no voiceover at all".
That was a subagent's assertion I wrote down without measuring, and it was
WRONG. It nearly caused another session to tear out a working TTS pipeline.
**Measure the reference audio yourself before you believe anything about it** —
`volumedetect` over the whole file, then per-3s windows to see whether the level
moves. Flat means bed; swinging means voice.

## 2. Freeze the beatmap before capturing anything

One row per beat: what is on screen, what the VO says, the window length, and
**the visible proof**. A beat without visible proof is a claim, and claims get
cut. Parallel work before the beatmap is frozen produces pieces that don't cut
together.

## 3. Capture

**Tab-only, always.** Desktop screen capture leaked private windows three
separate ways on this machine — see `/tab-film`. Use the browser extension's
recorder and drive frames with `wait` actions, not `screenshot` (same frames,
without flooding your context).

Product capture rules learned the expensive way:
- Citations resolve only when a message **completes**, and never inside a
  markdown table cell — only in prose. Mid-stream frames carry raw
  `[doc:turnNdocN]` tokens.
- A follow-up in an existing thread answers from history without re-calling
  tools, so it has **no citations at all**. Fresh chat every time.
- Show the user's prompt in frame. Three "ask it for…" VO lines over answers
  with no visible question is a reviewer's first finding.

## 4. Narrate

Voice `en-US-AndrewMultilingualNeural`. Azure Speech is **Entra-only** here —
local keys are disabled on every Speech resource:

```
Authorization: aad#<resourceId>#<token>
resourceId  $AZURE_SPEECH_RESOURCE_ID   # NOT in this repo — see below
token       az account get-access-token --resource https://cognitiveservices.azure.com
```

**Azure neural voice is REQUIRED. There is no acceptable fallback.**
macOS `say` was tried on 2026-08-01 and rejected on sight — it sounds robotic
and no amount of mixing saves it. If Speech is unreachable, **stop and fix the
credential**; do not build a film you will have to throw away.

Run `python3 agent.py preflight` BEFORE building. It fails if the token is
missing and tells you how to mint one. `narrate.py` must write a `voice.json`
beside the output recording provider and voice, and the gate rejects any film
narrated by `say`. A level meter cannot tell `say` from neural TTS — both read
as "speech" — so provenance is the only honest check.

**Fit-gate every slot.** Read must land inside its window with air at the tail.
If it does not fit, widen the window — **never speed up the read**. Over
~2.6 words/sec reads rushed; name the slot and fix it.

**Shortening the copy does NOT lower words per second.** `w/s = words / read`
and `window = read + lead + tail`, so deleting words shrinks the read by about
the same fraction and the ratio barely moves: 30 words -> 25 words took a slot
from 2.99 to **3.01** w/s, i.e. worse. w/s measures the voice's speaking rate,
not how much copy the window holds. What works is **more pauses at the same
word count** — break the sentence with commas, em dashes, full stops — which
lengthens the read without changing `words`: 3.01 -> 2.95 and green.
`narrate.py` also retries at a slower prosody rate (-6% -> -14% -> -22%) for the
same reason.

`--engine azure` hard-fails rather than falling back. A mid-run failure that
quietly swapped in `say` for one slot used to leave one manifest field reading
"mixed" as its only trace; the gate now treats "mixed" as a forbidden provider.

## 5. Mix — three traps that each cost a rebuild

Contract: VO +6dB · bed at a level that is actually audible · `sidechaincompress=
threshold=0.015:ratio=8:attack=25:release=450:makeup=1` · `alimiter` ·
**NEVER loudnorm**.

1. **`alimiter` has `level=true` by default**, which makes it a *normaliser* that
   lifts the mix until peaks hit the ceiling. Lowering the ceiling makes clipping
   WORSE. Use `alimiter=level=disabled:limit=0.891` (-1.0 dBFS).
2. **`amix` adopts the FIRST input's channel layout.** A mono VO bus silently
   collapses a stereo bed to mono. Check `side` channel energy in the output.
3. **The Apple Loops bed loops every 19.0s with a -37dB trough 4-6s in.** If a
   segment cut lands on it, it reads as dead audio. Mix the bed against a
   half-loop-offset copy of itself — same material, range drops from 12dB to
   under 3dB.

Gate: VO slots mean > -19dB; bed audible in every gap (target -27dB, -32dB is
the fail line and not the goal); peak at or under -0.3dB with nothing pinned at
full scale; genuinely stereo.

`build.py --voice-only` writes an EXTRA voice-only file; it does not build the
film without a bed. It used to be called `--nobed` and was written into a
handoff as a defect on that misreading.

## 6. Never motion-interpolate text

`minterpolate` with motion compensation warps pixels along estimated motion
vectors. Between frames of *different text* it produces unreadable ghosted soup.
Hard cuts, or crossfades <=0.3s. This shipped once.

## 7. Customer-facing versus internal

Two cuts, two vocabularies. Internal may name the build system. **Customer-facing
must not** — no RAPP, Factory, RAPPlication, MVP, prototype, pipeline, brainstem,
egg. Put a vocabulary gate in the build script that hard-fails on those in
narration and card strings, and know it **cannot see the pixels of captured
shots** — check frames by eye.

Synthetic data: badge on every data frame, and the disclaimer card lands
**before** the first data frame, not after. Show roles, never invented person
names.

## 8. B-roll must argue the scenario

Harvested stock that would drop unchanged into any other film is filler. If the
corpus has nothing that fits the domain, **cut the block short rather than pad
it** — and say so, so someone can source real footage. Never let b-roll carry
another agent's product UI, customer name or scenario.

## 9. The gate

Run `python3 agent.py gate <film.mp4>`. It measures resolution, channels, peak,
audio shape, **voice provenance**, longest unchanged frame, **whether the film
closes on the logo**, and **what fraction of it is demo**. Everything it cannot
measure it prints under "NOT covered" — read that list, do not skip it.

- Longest unchanged frame <= 5.0s. **This ceiling is ours, not the
  reference's**: measured with `freezedetect=n=-60dB`, the corpus films hold
  12-22s, so every one of them would fail it. Keep the ceiling — a film that
  never dies for five seconds is better than the reference — but never claim it
  came from the corpus.
- **A reveal step must change a REGION, not a line.** freezedetect calls two
  frames identical below ~0.001 mean absolute luma difference, and one extra
  line of body text is about 0.0012 — right on the floor. Two card stages that
  differed by a single line of tile copy read as one 7.7s freeze, and two demo
  stages differing by one bullet read as one 8.2s freeze. So: tile cards light
  a whole gradient panel per stage, statement cards grow the lozenge, and the
  demo transcript is bottom-anchored so the whole thing slides.
- **Demo proportion is gated at 45%** against the reference's 56.4%. A demo
  beat can never be longer than its reveal states x the hold ceiling, so the
  lever for more is richer answers, not a longer hold.
- **The film closes on 2-3s of logo**, not on a text card.
- **Watch it.** Frames at ~1Hz across the whole timeline, READ them. A green
  build is not a watched film — this failed repeatedly, once shipping a smeared
  unwatchable cut and once a frame with raw citation tokens.
- Then a **separate blind adversarial reviewer** against the reference film, on
  grammar, pacing, legibility, audio and claim-vs-proof. Fix blockers, rebuild,
  re-review. Loop until PASS with zero blockers — **and if you stop short, name
  exactly what is still wrong.** A known flaw named is fine; one the customer
  finds is not.

## Related

`/tab-film` (capture detail) · `/cs-agent-live` (get the agent presentable
first) · `/msft-deck` (the deck that travels with it)


## The Azure resource id is NOT in this repo, deliberately

It contains a subscription GUID and **this repo is a fork of a public
Microsoft repository**. Never commit it. Supply it at run time:

```
export AZURE_SPEECH_RESOURCE_ID='/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<account>'
export AZURE_SPEECH_TOKEN=$(az account get-access-token \
  --resource https://cognitiveservices.azure.com --query accessToken -o tsv)
```

`agent.py preflight` fails loudly if either is missing. Local keys are
disabled on these resources — Entra only.
