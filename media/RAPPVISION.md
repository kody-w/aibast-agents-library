# RAPPVision — the demo walkthrough format

> **Schema:** `rappvision-walkthrough/1.0` · **Status:** v1 (storyboard stage)

Every industry agent in the AIBAST catalog has a demo recording, and they are
all the same film. That consistency is not an accident of production — it is a
**format**, and a format can be generated.

This document is that format, derived from the shipped recordings rather than
invented: `media/videos/*.mp4`, ~135 seconds each, five acts in fixed order.

## Why write it down

An aggregated skill arrives as a paragraph of instructions and a link. Left
alone, that is all it ever is. Run it through this format and it comes out with
the same one-pager and the same walkthrough as an agent we authored — which is
the entire argument for aggregating into the library instead of linking out of
it. We are not a directory of other people's work. We are the pipeline that
makes other people's work usable, and the format is the pipeline's output
contract.

## The five acts

Timings are the median of the shipped recordings. A generated walkthrough
targets them and may drift ±15% on narration length.

| # | Act | Duration | What is on screen |
|---|---|---|---|
| 1 | **Title card** | 0:00–0:05 | Microsoft logo, white field, silence into the first line of narration |
| 2 | **The problem** | 0:05–0:22 | Industry b-roll. Narration states the job to be done in the operator's language — never the technology's |
| 3 | **Agent overview** | 0:22–0:42 | Dark card, three gradient panels: **Sources** → **Flow of work** → **Actions**, each with its product glyph |
| 4 | **The walkthrough** | 0:42–2:00 | Laptop-framed Copilot chat. Operator prompt → agent response with structured findings → visible `Agent Calls: <tool>` line → one follow-up turn |
| 5 | **Close** | 2:00–2:17 | Dark card, gradient CTA panel |

Act 3 is the load-bearing one. Sources / Flow of work / Actions is the whole
value proposition in one frame, and it is exactly the three things a RAPP
manifest already declares — which is why it can be generated rather than
written.

## What the generator reads

Every field comes from data the library already holds. Nothing is invented, and
where a field cannot be derived the storyboard says so rather than inventing a
plausible-sounding claim.

| Act element | Derived from |
|---|---|
| Title | `display_name` |
| Industry b-roll cue | `category`, `industries` |
| Problem narration | `description`, one-pager `lede` |
| Sources | `requires_env`, `featured_tools`, declared integrations |
| Flow of work | surface the agent runs on (brainstem / Teams / Copilot Studio) |
| Actions | `business_value`, else the verbs in the description |
| Prompt | `description` recast as an operator's first message |
| `Agent Calls:` line | the tool name the entry actually registers |
| Findings block | parameter schema and stated outputs |
| Close CTA | fixed |

## Honesty rules

The recordings show synthetic data, and a generated walkthrough must be at
least as honest as the ones it imitates.

1. **No invented numbers.** The template recordings show figures because a
   human authored them against a scenario. A generated storyboard marks every
   numeric slot `[operator supplies]` rather than fabricating a KPI. A demo
   that fabricates a metric teaches the viewer something false about the agent.
2. **The `Agent Calls:` line must name a tool that exists.** It is the one
   frame that claims something checkable, so it is generated from the
   registered tool name and from nothing else.
3. **Aggregated entries are labelled.** A walkthrough for a redistributed skill
   names its origin in act 1 and carries its licence in the close.
4. **Storyboard is not footage.** A generated walkthrough is a script and a
   shot list. Publishing it as a rendered video requires a human to approve the
   script first — see the pipeline stage below.

## Pipeline

```
entry (agent.py | skill.md)
  → scripts/build_walkthrough.py      # deterministic: manifest → storyboard
  → media/walkthroughs/<slug>.json    # rappvision-walkthrough/1.0
  → one-pager renders it as a storyboard         [today]
  → human approves the script                    [gate]
  → render to video against the act timings      [next]
```

The generator is deterministic and holds no model: the same entry produces the
same storyboard, so a review of the script is a review of what will be filmed.
Where a model helps — sharpening narration, choosing b-roll — it runs as a
Sentinel interpretive resident, with its answer recorded and attributed, the
same as any other review in this library.
