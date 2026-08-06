# The grammar of the demo recordings

Every number here was measured, and the tool that measured it is named so it
can be re-run. Nothing is inferred from a style guide, and nothing that has not
been measured is stated as if it had been.

```bash
python3 film/kit/harvest.py --scan film/corpus/videos/ask-hr-agent.mp4
```

## What was measured, and on what

19 of the 48 recordings, at full resolution, on 2026-08-05. Frames sampled at
1 Hz, each classified by the colour signature of its **border** and coalesced
into segments. Border, not full frame: the overview card sits on a near-black
bed but carries large bright panels, so its mean luma reads mid-grey while its
border is flat navy. The border separates the four segment types cleanly.

| Class | Border | Reads as |
|---|---|---|
| `logo-card` | flat, luma > 200 | white logo sting |
| `motion-graphic` | flat, luma < 60, blue-dominant | a full-screen card |
| `demo` | violet-dominant, mid luma | the device-framed product shot |
| `broll` | photographic, high variance | industry footage |

**Do not reach for `select='gt(scene,N)'`.** The encodes carry no usable scene
metadata — every threshold tested returns zero matches on every recording.
All boundary detection here is explicit frame differencing.

## The segment order is identical in all 19

```
logo  ->  b-roll  ->  overview card  ->  demo  ->  close card  ->  logo
```

Six of the 19 place a short b-roll beat between the demo and the close card.
One (a four-agent suite, 201.6 s) alternates card and demo four times; it is a
different format and is excluded from the averages below.

| | S1 open | S2 overview | S3 demo | S4 close |
|---|---|---|---|---|
| mean of 18 | **18.1 %** | **12.2 %** | **56.4 %** | **12.9 %** |
| median | 18.8 % | 11.9 % | 56.4 % | 12.7 % |
| range | 15.1–23.1 % | 9.5–16.5 % | 51.0–60.0 % | 10.8–16.1 % |

Duration: n = 19, min 142.1 s, median 159.6 s, mean 161.3 s, max 201.6 s.
Frame 1920×1080, 30 fps. Audio AAC 48 kHz **stereo, and narrated** — mean
−18.6 to −21.2 dB with the level swinging across 3 s windows, which is the
signature of speech with sentence pauses rather than a flat bed.

**Absolute lengths vary by about ±13 %; the proportions hold to a few points.**
That is what transfers to a new film.

## S1, beat for beat

| Beat | Measured |
|---|---|
| logo sting, opens already on white | 0.00 – 3.0 s in all 19 |
| hard cut to b-roll, title lozenge fades up | ≈ 2.8 s |
| title lozenge clears | 6.1 – 7.4 s, varies per recording |
| narration first word | ≈ 7 s |

**The lozenge clear time must be measured per recording, never assumed.** A
fixed 7.0 s in-point put another agent's title in the first frame of nine
harvested b-roll clips before this was caught by eye.
`film/kit/harvest.py` measures it: the magenta-to-violet fraction of the centre
band reads 0.3–0.7 while the lozenge is up and drops to 0.00 within a tenth of
a second, so the transition is unambiguous. The harvester adds 0.35 s of safety
on top.

The intro sting in `film/assets/stings/` is trimmed to **2.40 s**, not 2.57 s,
because the recording it was cut from begins fading its own agent title up over
the white field at 2.45 s.

## Cadence

Measured over the reference build's own transcripts: **2.17 words per second
across the film, 2.23 while actually speaking.** Delivery is calm, declarative
and unhurried. Sentences are short. There are no questions to the audience
except one rhetorical pivot, and no exclamations.

The film-level average hides the real rhythm. Bucketed by segment:

| Segment | words/sec | share of all words |
|---|---|---|
| S1 open + problem | 1.59 | 12 % |
| S2 overview card | 2.34 | 13 % |
| S3 demo | 2.36 | 64 % |
| S4 close | 1.89 | 12 % |

**The open and the close breathe; the middle is dense.** A script that spends
its words evenly across the runtime hits the right total and still feels wrong
— rushed over the problem, airless through the demo.

Above about **2.6 words per second** the delivery is audibly hurried. When a
read does not fit, widen the window or shorten the copy. `film/kit/plan.py`
removes the temptation by computing each beat from the read that already
exists.

## The narration skeleton

Match the structure; the words must come from the source, not from you.

1. **Industry pressure.** Present tense, plural subject.
2. **The manual status quo.** Names the drudgery, blames nobody.
3. **The capability triplet**, in the same order as the overview card: what it
   reads (Sources), where it lives (Flow of work), what it does (Actions).
4. **Persona setup.** A role, never a name.
5. **Demo beats.** Repeated *operator asks X → agent does Y → value line*.
6. **Payoff triplet**, mapping one-to-one onto the three benefit tiles.
7. **The call to action, verbatim and locked**, spoken and on screen together:
   *"Get started on your agentic journey today. Talk to your Microsoft
   representative to learn more."* Treat it as fixed text.

## Cards

**Title lozenge** (S1, ≈ 2.8 s to ≈ 6.5 s). A wide rounded panel about 65 % of
frame width, vertically centred, left-to-right gradient, white bold text,
centred, wrapping to two lines. It fades; it does not slide.

**Full-screen cards** (S2 and S4). This kit renders them on the Fluent paper
stage — white ground, brand spine, footer rule and mark — rather than the
corpus's dark navy, which is a deliberate departure to match the deck kit these
films travel with.

The **overview card** is the load-bearing frame: three panels, **Sources / Flow
of work / Actions**, revealed left to right with chevron connectors and the
product glyphs from `media/jewels/`. It is the whole value proposition in one
frame and it is exactly the three things a manifest already declares.

The **close card** reveals three benefit tiles one at a time, the active tile
at full saturation and the others dimmed — a spotlight, not a build-up. That
build is what keeps a static card alive for fifteen seconds, and it is why
`film/kit/cards.py` returns a list of stills rather than one.

## Transitions — the part that is easy to get wrong

**Inside a montage: hard cuts.** Shots run 2.1–5.5 s, typically about 2.5 s.

**Between segments: a two-stage dissolve, and it is not a plain cross-fade.**

1. The incoming card's heading and icon **fade up on top of the outgoing
   footage, which is still at full strength.** For about half a second you see
   white glyphs over a completely normal, unfaded shot.
2. *Then* the picture cross-dissolves to the card over a further 1–2 s.

This matters enormously when harvesting. During stage 1 nothing about the
footage changes — not its colour, not its luminance, not its edge energy — so
every colour-based purity test passes while agent-specific text is already
legible on screen. The only test that catches it is a person reading the
frames. `film/kit/harvest.py --verify` renders first, middle and last frame of
every clip for exactly that.

**Logo stings: hard cut on both sides.** The intro opens already on white.

**Never motion-interpolate, and never speed-ramp text.** See
`film/CAPTURE.md`.

## Where this kit deliberately departs

Named, so the difference is a decision rather than a drift.

| | Corpus | This kit | Why |
|---|---|---|---|
| Card stage | dark navy | Fluent paper | matches the deck the films travel with |
| Demo segment | screen recording | drawn surface, badged illustrative | no live agent, and the scenario is illustrative by construction |
| Demo share | 56.4 % | see the batch manifest | the beatmap is sized by the source's own narration, and the storyboards weight the opening more heavily than the corpus does |
| Held frames | up to 23 s on one card | ≤ 5.0 s, gated | a static card for a whole beat is dead air |
