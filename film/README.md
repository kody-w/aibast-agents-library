# Showcase films

> **Schema:** `aibast-showcase-film/1.0` · **Status:** v1 · **Output:** drafts,
> pending human approval before publication

The catalog ships 48 professional demo recordings and they are all the same
film. That is a format, and a format can be produced rather than commissioned.
This directory produces one — at the grammar, pacing and audio standard of the
recordings themselves — from a config file and nothing else.

Everything it needs is in this repository. No asset, script or credential it
requires lives on the machine that built it. That claim is a gate:

```bash
python3 film/kit/gate.py --cold-start
```

## Make a film

```bash
# 1. compose a config from a description the repo already holds
python3 film/kit/compose.py --walkthrough supplier-risk-monitoring \
    --bucket manufacturing --batch library

# 2. run it
python3 film/kit/make.py --project supplier-risk-monitoring

# 3. read the contact sheets. Every one of them.
open film/projects/supplier-risk-monitoring/work/watch/sheet_00.jpg
```

Film eleven is step 1 with a different slug. There is no per-film code.

## What you need

| Requirement | Why | Check |
|---|---|---|
| `ffmpeg` and `ffprobe`, 6.0 or later | every cut, mix and measurement | `ffmpeg -version` |
| Python 3.11 | the kit | `python3 --version` |
| Pillow | cards and screens are drawn, not captured | `python3 -c "import PIL"` |

The kit is otherwise standard library. Pillow is the one dependency, and it is
the only one — `python3 -m pip install --user Pillow`.

**Narration is optional in the sense that the cloud is optional.** With
`FILM_SPEECH_RESOURCE_ID` set, narration is an Azure Speech neural voice. With
nothing set, it is the macOS `say` voice. Both paths use the same slots, the
same offsets and the same fit-gate, so the cut is identical and only the timbre
differs. A film with a lesser voice ships; a film with no voice does not.

```bash
export FILM_SPEECH_RESOURCE_ID="/subscriptions/…/accounts/<speech-account>"
export FILM_SPEECH_REGION=eastus            # optional, defaults to eastus
export FILM_SPEECH_VOICE=en-US-AndrewMultilingualNeural   # optional
az login                                    # Entra only; local keys are off
```

The resource id is an Azure resource path, so it lives in the environment and
never in a tracked config file — `film/kit/gate.py` rejects one on sight.

## The stages, and why the order is fixed

```
compose  ->  narrate  ->  plan  ->  cards  ->  screens  ->  build  ->  gate  ->  watch
```

| Stage | Module | What it does |
|---|---|---|
| compose | `kit/compose.py` | a source description becomes `projects/<slug>/project.json` |
| narrate | `kit/narrate.py` | one wav per narration slot, and its measured length |
| plan | `kit/plan.py` | the beatmap, computed **from those lengths** |
| cards | `kit/cards.py` | title, overview, benefit, disclaimer and chyron stills |
| screens | `kit/screens.py` | the demo segment, revealed one step at a time |
| build | `kit/build.py` | the cut and the mix |
| gate | `kit/gate.py` | text, picture, audio and cold-start gates |
| watch | `kit/watch.py` | contact sheets at 1 Hz across the whole timeline |

`make.py` runs all seven. The order is not a preference: **the beatmap is
derived from the reads**, so narration has to exist before a beat can be
sized. That inversion is the single most useful thing in this kit. It makes
the fit-gate green by construction, and it removes the knob that tempts you to
speed a read up when the copy will not fit.

## Where things live

```
film/
  README.md          this
  GRAMMAR.md         the measured grammar, and what is still unverified
  AUDIO.md           the mix contract and the three traps in it
  CAPTURE.md         filming a live product surface instead of drawing one
  brand/brand.json   palette, type, geometry - data, not prose
  assets/broll/      harvested industry footage, by bucket, with provenance
  assets/stings/     the logo top and tail
  assets/audio/      the music bed
  kit/               the eight modules above
  projects/<slug>/   project.json in, work/ and dist/ out
  out/<batch>/       the finished drafts, plus a batch manifest
  corpus/            the source recordings (see below)
```

`projects/*/work/` and `projects/*/dist/` are intermediates and are ignored by
git. `film/out/` holds what is finished.

## The corpus, and building without it

`film/corpus/videos/` holds the source recordings at full resolution. It is
where grammar gets re-derived and b-roll gets re-harvested, and it is large.

**You do not need it to build a film.** Everything production consumes is
already derived and committed: the grammar in `GRAMMAR.md`, the b-roll in
`assets/broll/`, the brand values in `brand/brand.json`. The corpus is
provenance and the input for deriving something new.

`media/videos/` holds the same 48 recordings at 960×540 for the site. Timings
can be re-derived from those. B-roll cannot — cut from a 540-line source it
upscales, and the softness is visible.

## Composing from something that is not a catalog entry

`compose.py --walkthrough` reads `media/walkthroughs/agent-<slug>.json`, the
storyboard CI already generates for every entry. For any other source — a
briefing, a discovery transcript, a one-pager — extract it to JSON first and
use `--brief`:

```json
{
  "agents": [{
    "slug": "…", "name": "…", "industry": "…", "bucket": "healthcare",
    "problem": "2-4 sentences on the job to be done and the manual status quo",
    "sources": ["systems it reads"],
    "surface": "where people reach it",
    "actions": ["3-5 short verb phrases"],
    "value": ["3 qualitative outcomes - never a figure"],
    "example_questions": ["…"],
    "narration": {"vo04": "…", "vo05": "…", "vo06": "…"},
    "payoff": "…", "helps": "…"
  }]
}
```

The adapter leaves a field empty rather than inventing a plausible-sounding
sentence to fill it. An empty `example_questions` produces a prompt built from
the declared actions, and says nothing the extract did not.

## Honesty rules this kit enforces

These follow `media/RAPPVISION.md` and Article XVI, and most of them are
gates rather than reminders.

- **No invented figures.** The storyboards are qualitative by construction and
  a film built from one inherits that. Where a scenario needs data on screen,
  it is synthetic, it is badged on every frame, and the disclaimer card lands
  **before** the first data frame — never after.
- **Roles, never invented person names.**
- **The agent-calls line names a tool that exists.** It is the one frame that
  claims something checkable, so it comes from the registered tool name and
  from nothing else. An invented citation is worse than no citation.
- **Customer-facing vocabulary.** The gate hard-fails on internal vocabulary
  in narration and card copy. It cannot see the pixels of a captured shot,
  which is exactly where leakage lives — so read the contact sheets.
- **A rendered film is a draft.** Every config carries
  `approval.required_before_publishing`. Promotion out of `film/out/` into
  anything the site serves is a human decision on a script a human has read.

## The gates

| Gate | Threshold | Why it exists |
|---|---|---|
| longest unchanged frame | ≤ 5.0 s | a card held for the whole beat is dead air |
| narration slot mean | > −19.0 dB | one quiet slot disappears under the bed |
| bed-only gaps | −34 to −22 dB | quieter is inaudible, louder is not ducking |
| programme peak | ≤ −0.1 dB | anything at full scale is clipping |
| side-channel energy | > −70 dB | proves the mix did not collapse to mono |
| vocabulary and identifiers | zero hits | internal words, GUIDs, resource paths |
| cold start | zero hits | no path under `film/` leaves the repository |

`gate.py` exits non-zero on any violation and writes `work/gate.json`.

**A green gate is not a watched film.** Two cuts went out of this pipeline's
ancestor with every measurement passing and a defect visible in the first
frame anyone looked at. `watch.py` exists for that, and reading its output is
part of the job, not a formality.

## Related

`GRAMMAR.md` for what the recordings actually do · `AUDIO.md` for the mix ·
`CAPTURE.md` before pointing a camera at a live product ·
`.claude/skills/showcase-film/` for the working method ·
`media/RAPPVISION.md` for the format the catalog already declares ·
[`../DISCLAIMER.md`](../DISCLAIMER.md)
