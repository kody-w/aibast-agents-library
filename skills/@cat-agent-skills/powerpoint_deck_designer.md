---
schema: rapp-skill/1.0
name: @cat-agent-skills/powerpoint_deck_designer
version: 1.0.0
display_name: "PowerPoint Deck Designer"
description: "Creates polished PowerPoint decks from a JSON specification using python-pptx. Designed as a Copilot Studio Skill that runs natively inside the agent's Python container (no Azure Function or custom connector required). Supports 8 layouts plus native charts (bar, column, line, pie, donut with stacked / 100% stacked variants)."
author: "Ferran Chopo"
tags: ["powerpoint", "presentations", "python", "charts"]
category: general
requires_env: []
source_ref: @cat-agent-skills/powerpoint_deck_designer
source_url: https://microsoft.github.io/cat-agent-skills/#powerpoint-deck-designer
source_license: MIT
converted_from: CAT Agent Skills
converted_on: 2026-08-06
---

# PowerPoint Deck Designer

> **Converted skill.** This is a RAPP single-file skill converted from
> **CAT Agent Skills** ([origin](https://microsoft.github.io/cat-agent-skills/#powerpoint-deck-designer)), redistributed under
> **MIT** with attribution. Original author: Ferran Chopo.
> Upstream license text: https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/LICENSE
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

Creates polished PowerPoint decks from a JSON specification using python-pptx. Designed as a Copilot Studio Skill that runs natively inside the agent container.

## The deterministic layer

RAPP skills state their contract explicitly, so two runs of the same skill do
the same thing:

- **Inputs** — whatever the steps below name. If an input is missing, say so
  and stop rather than guessing.
- **Outputs** — the artifact the steps produce, named where it is written.
- **Verification** — before reporting success, confirm the output exists and
  matches what was asked. A silent partial result is a failure.
- **Configuration** — never hardcode an endpoint, key, or tenant. Read them
  from the environment (`requires_env` above lists what this skill needs).

## Skill

# PowerPoint Deck Designer

## When to activate this skill
Activate whenever the user asks to build, generate, draft, improve or restyle any kind of slide deck or PowerPoint file. Typical triggers include: "create a deck about X", "build me a pitch deck", "draft a training presentation", "make a proposal in PowerPoint", "restyle these slides with our brand", "visualise these numbers as a slide".

Do NOT activate for:
- Word documents or PDF reports (use the doc skill instead)
- Editing an existing uploaded .pptx (unless the user explicitly wants a full rebuild)

## How this skill runs
This agent runs inside a Copilot Studio **Skills container** with a Python interpreter. `python-pptx` is available out of the box. To use the skill:

1. Build a JSON deck specification (see `references/input_schema.md`).
2. Pick a theme slug from `assets/themes.json` (see `references/layouts.md` for available layouts).
3. Save the JSON as `/tmp/spec.json` and run the renderer:
   ```bash
   python scripts/generate_presentation.py \
       --input /tmp/spec.json \
       --output /tmp/deck.pptx \
       --theme <theme-slug> \
       --validate
   ```
4. Return `/tmp/deck.pptx` to the user as a downloadable artifact.

## Design principles the agent must follow
- Consider the subject matter: audience, tone, industry, mood.
- Check for branding: prefer official brand colours when the user names an organisation. If none, pick a theme whose palette matches the topic.
- Use web-safe fonts only (already baked into the themes): Arial, Calibri, Verdana, Georgia, Trebuchet MS, Tahoma.
- Clear hierarchy: title -> section -> content -> closing.
- Readability: minimum body font 14 pt, minimum title 28 pt, contrast >= 4.5:1.

## Charts
This skill can generate native PowerPoint charts (real, editable Office charts - not images). Supported types:
- `column` and `bar` - category comparisons (multiple series allowed). Set `stacked: true` or `stacked: "100"` for stacked / 100% stacked variants.
- `line` - trends over time (multiple series supported; up to ~12 points recommended).
- `pie` and `donut` - parts of a whole (single series only).

Series and slices are colour-coded from the active theme palette (primary, secondary, accent, muted). See `references/input_schema.md` for the JSON shape.

## Colour palette selection
- Corporate / executive briefing -> `executive-blue`
- Tech / product launch on dark background -> `modern-slate`
- Sustainability / environmental -> `sustain-green`
- Startup / creative pitch -> `vibrant-pitch`
- Editorial / minimalist -> `minimal-mono`

## Workflow the agent must follow
1. Understand the objective, audience, tone, and source material.
2. Draft a short storyline (3-15 slides) *before* writing JSON.
3. State your theme choice and reasoning to the user in one line.
4. Build a JSON deck spec following `references/input_schema.md`.
5. Run the script in the container with `--validate`.
6. If validation warnings appear, shorten text or switch to a layout with more room (see `references/layouts.md`), then re-render.
7. Return the .pptx to the user; offer to iterate on colours, wording, layout or chart type.

## Quality rules
- One main message per slide.
- <= 6 bullets per slide, <= 14 words per bullet.
- Use `agenda` for agendas, `cards` for short concepts, `chart` for numeric data.
- Do not invent numbers. Mark assumptions in `notes` (speaker notes).

## Activation examples
- "Create a 10-slide investor pitch for our KONE modernisation offering" -> theme `executive-blue`
- "Draft an internal training deck on Power Platform governance" -> theme `minimal-mono`
- "Build a bold launch deck for our new sustainability product" -> theme `sustain-green`
- "Visualise Q1-Q4 backlog progression as a stacked column chart" -> `chart` layout, `stacked: true`

## Run example (executes inside the Copilot Studio Skills container)
```bash
python scripts/generate_presentation.py \
    --input assets/example_request.json \
    --output /tmp/kone_adoption.pptx \
    --theme executive-blue \
    --validate
```

---

*Converted for the AIBAST Agents Library from CAT Agent Skills.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
