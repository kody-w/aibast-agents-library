---
title: How to make a showcase film
tags: [ms-rapp, how-to, film, rappvision]
summary: A config file and one command produce a demo film at the grammar and audio standard of the recordings the catalog already ships.
updated: 2026-08-05
---

# How to make a showcase film

The catalog ships 48 professional demo recordings and they are all the same
film. That consistency is a format, and [[concepts/the-vault]] aside, a format
is something a build can produce. `film/` does — from a config file and
nothing else.

```bash
python3 film/kit/compose.py --walkthrough <slug> --bucket <industry> --batch library
python3 film/kit/make.py --project <slug>
open film/projects/<slug>/work/watch/sheet_00.jpg
```

Film eleven is the first command with a different slug. There is no per-film
code, and there is no hand-tuned beatmap.

## Why the order of the stages is fixed

`narrate` runs before `plan`, because **the beatmap is computed from the reads
that were actually synthesised**. A beat is exactly as long as its narration
plus a lead-in and a tail of air.

That inversion removes the loop that makes a film expensive — write, guess a
window, build, discover the read overruns, nudge, rebuild — and it removes the
knob that the loop tempts you to reach for. There is no rate control, so a read
can never be sped up to fit; the window widens instead.

## What it will not do

- **It will not invent a figure.** The storyboards it composes from are
  qualitative by construction, and the brief adapter leaves a field empty
  rather than filling it with something plausible.
- **It will not publish.** Every config carries
  `approval.required_before_publishing`. A rendered film lands in `film/out/`
  as a draft with its measurements attached; promoting one into what the site
  serves is a person reading the script.
- **It will not reach outside the repository.** Assets, bed, corpus, brand
  values and grammar are all in-repo. `python3 film/kit/gate.py --cold-start`
  fails on any path that leaves it.

## What it needs

`ffmpeg`, Python 3.11 and Pillow. Narration is an Azure Speech neural voice
when `FILM_SPEECH_RESOURCE_ID` is set and the local `say` voice when it is
not — same slots, same offsets, same fit-gate, so the cut is identical either
way.

## Read the frames

`make.py` finishes by writing contact sheets at 1 Hz across the whole
timeline. Read them. Two cuts went out of this pipeline's ancestor with every
measurement green and a defect visible in the first frame anyone looked at: a
smeared interpolated cut, and a panel showing raw reference tokens. Neither is
detectable from a number.

See [[concepts/rapp-data-exhaust]] for why that lesson is written down here
rather than remembered.

## Deeper

- `film/README.md` — the whole workflow
- `film/GRAMMAR.md` — what the recordings actually do, measured
- `film/AUDIO.md` — the mix contract and the three traps in it
- `film/CAPTURE.md` — before filming a live product surface
- `media/RAPPVISION.md` — the format the catalog already declares
