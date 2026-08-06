# Film pipeline — state and handoff

Written 2026-08-01, revised 2026-08-05. Everything below is either measured or
explicitly flagged as unverified.

## Where things stand

**The kit is ported and works, and a film built by it now passes its own gate
with zero findings.** `film/kit/` (make · plan · narrate · cards · screens ·
compose · build · gate · watch · harvest · publish), assets in `film/assets/`,
corpus in `film/corpus/`, per-film configs in `film/projects/`.
`make.py --project <slug> --engine azure` runs the whole chain in the only
order that works.

**Three batches:**
- ~48 library films in `media/videos/` — done
- FY27 batch — extracted and scaffolded (`film/.work/fy27-agents.json`,
  `film/projects/_batches/fy27-source.json`, ~12 project dirs), **not rendered**
  with the current renderer; they predate the navy palette and the outro logo
- `film/projects/public-sector-citizen-civil-service/` — built 2026-08-05,
  **172.7s, gate PASS with zero findings**, watched at 1Hz end to end

**Everything is committed locally and UNPUSHED.** This repo is a fork of a
public Microsoft repo.

## Credentials

`film/.env.local` (gitignored via `*.env.local`). `source film/.env.local`
before any build. It holds the Speech resource id and **mints a fresh Entra
token each time** — tokens expire in ~1h, so a stored one is a stale secret.
Never commit the subscription GUID.

Verify with `python3 .claude/skills/showcase-film/agent.py preflight`.

## The three defects from 2026-08-01 — all closed

1. **`narrate.py` did not write `voice.json`.** It does now:
   `work/vo/voice.json` carries provider, voice, region, slot count and the
   engine and prosody rate of every slot; `build.py` copies it to `dist/` and
   refuses to finish without it. `--engine azure` no longer falls back — a
   mid-run synthesis failure raises instead of quietly swapping in `say`, and
   the gate treats a provider of `mixed` as forbidden alongside `say`.

2. **`plan.py`'s rushed-read advice could not work.** The message now says to
   break the line into shorter sentences, and the arithmetic is in a comment
   above it so nobody "simplifies" it back: `w/s = words / read` and
   `window = read + lead + tail`, so cutting words shrinks the read by the same
   fraction and the ratio barely moves (30 -> 25 words took a slot from 2.99 to
   **3.01**). More pauses at the same word count is the lever. `narrate.py`
   also retries at -14% and -22% prosody for the same reason.

3. **Card beats were not hold-capped.** `plan.py` now sizes every card beat
   against `cards.card_capacity(spec) x MAX_HOLD`, the same arithmetic the demo
   beats always used, and warns by name when a read needs more stages than the
   card can make.

## The thing that made defect 3 hard, and the rule that came out of it

`freezedetect=n=-60dB` calls two frames identical below about **0.001 mean
absolute luma difference**. One extra line of body text is about **0.0012** —
right on the floor. So a build step that reveals one more line is caught on
some cards and missed on others, and a missed one silently doubles the hold.
That is what produced both over-limit freezes in the 2026-08-04 build: 7.7s
across two overview stages differing by one line of tile copy, and 8.2s across
two demo stages differing by one bullet.

**A reveal step must change a REGION, not a line.** Implemented as:
- tile cards light or dim a whole gradient panel per stage (~150k px)
- statement cards grow the lozenge to admit the supporting line, top edge fixed
  so the title never moves
- the demo transcript is bottom-anchored against the composer and slides up as
  the answer grows — which is also what the product does when it scrolls

Measured on the current build, the weakest consecutive stage pair is 0.0103,
ten times the detector floor. `film/kit/cards.py` and `film/kit/screens.py`
carry the reasoning.

## The 5.0s hold ceiling is OURS, not the reference's

Measured with `freezedetect=n=-60dB:d=2` over whole corpus films:

| film | longest freeze |
|---|---|
| financial-advisor-agent | 22.1s |
| supply-risk-monitoring-agent | 17.5s |
| ask-hr-agent | 16.4s |
| building-permit-processing-agent | 15.4s |
| underwriting-support-agent | 12.1s |

**Every reference recording would fail our gate.** Keep the ceiling — a film
that never dies for five seconds is better than the reference — but never
describe it as derived from the corpus, because it is not.

## Grammar — measured over 19 corpus films, 1Hz, border signature

Order `logo -> b-roll -> card -> demo -> card -> logo` holds **18/19**. The
exception, `energy-operations-suite`, alternates four demo blocks with cards — a
legitimate suite variant.

| segment | reported | measured median | verdict |
|---|---|---|---|
| logo in | 3 | 3 | reproduced |
| b-roll | 23 | 25 | reproduced |
| card (open) | 23 | 21 | reproduced |
| demo | 81 | **90** | not — +9s |
| card (close) | 22 | **16** | not — −6s |
| logo out | 3 | 3 | reproduced |
| total | 155 | **159.6** | not — +4.6s |

## Kit drift from the corpus — closed, and what it cost

| drift | state |
|---|---|
| white cards, flat blue tiles | **fixed** — navy `#070E27`, pink->violet gradient tiles, magenta->violet lozenge, all sampled and held in `brand.json` |
| no outro logo | **fixed** — `plan.py` appends a 3.0s `sting-outro-logo.mp4` beat; `agent.py check_outro_logo()` measures the closing frame's border luma |
| demo proportion 37-42% | **improved to 48.6%** against the reference's 56.4%; `READ_HOLD` 0.85 -> 2.20. Gated at 45% by `agent.py check_demo_share()` |
| demo not device-framed | **partly** — violet stage (`#8300F4` -> `#150951`) and a bezel; not the full laptop-on-a-desk |
| `make.py` forces `--nobed` | **was never a defect** — see below |
| no `b2b_sales` b-roll bucket | still open; `cross_industry` yields contact-centre footage for enterprise-seller agents |

### `--nobed` never meant what the last handoff said

`build.py --nobed` did not disable the bed. It asked for an **extra**
voice-only file beside a delivered film that always carried the bed at
`project.bed_db`. Measured on the 2026-08-05 build with the flag on: bed-only
gaps at −26.6 to −28.0 dB, inside the audible band. The flag is now
`--voice-only`, which is what it does.

That entry is a worked example of the rule at the bottom of this file: it was
written down from reading a flag name, and it survived into a handoff because
nothing measured it.

## Audio facts, all reproducible

- bed `film/assets/audio/bed-slow-drift.caf`: 19.009909s, trough −36.7dB @4s and
  −38.4dB @5s against −18 to −24dB elsewhere. A segment cut landing there reads
  as dead audio; mix against a half-loop-offset copy.
- `alimiter` has `level=true` by DEFAULT — it is a **normaliser**, so lowering
  the ceiling makes clipping worse. Use `level=disabled`.
- `amix` adopts the FIRST input's channel layout; a mono VO bus silently
  collapses a stereo bed to mono.
- Bed target −27dB in gaps; −32dB is the fail line, not the goal.

## Open, named plainly

- **Long wordless stretches in the demo.** Raising the demo to 48.6% on a
  script with only ~36s of demo narration necessarily leaves the rest
  wordless: the gaps now run 14-16s of bed against 5-8s before. The bed is
  audible throughout and the gate is green, but it is a real pacing change and
  the honest fix is more demo copy, not a shorter hold.
- **The demo pane's early stages** have empty space above the prompt, because
  the transcript is pinned to the composer. It reads as a chat scrolled to its
  newest message, which is true, but it is not what M365 Copilot does with a
  short conversation.
- **The FY27 batch has not been rebuilt** on the current renderer.
- **The full laptop device frame** is still a bezel.

## Two mistakes worth not repeating

**A subagent claimed the corpus had "no voiceover at all" and I wrote it into
the skill as fact.** It was false — the corpus is narrated. It nearly caused a
working TTS pipeline to be deleted. Never write down a claim about the reference
without measuring it.

**The test I added to catch that was itself broken.** It used 3-second windows
from t=0. Three-second windows average speech back to flat (a narrated film
measured a 2.3dB spread and read as "bed"), and starting at t=0 samples the
silent head. Now 1-second windows from t=20s. Same class of error, one layer up.

## The rule

`.claude/skills/showcase-film/` holds `SKILL.md` (prose, drifts) beside
`agent.py` (measures, does not). **If they disagree, the agent is right and the
skill gets corrected.** Run `agent.py facts | portability | preflight | gate`.

Applied on 2026-08-05, in both directions: the skill's bed-trough figures, peak
range, 3-second-window method and "shorten the copy" advice were corrected
against the agent — and the agent's own `card_bg` (`#0A1633`) and `--nobed`
claim were corrected against the frames and the flag. Measuring beats
remembering, including when the thing being remembered is this file.
