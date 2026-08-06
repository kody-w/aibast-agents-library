---
schema: rapp-skill/1.0
name: @cat-agent-skills/gantt_chart_generator
version: 1.0.0
display_name: "Gantt Chart Builder"
description: "Generate clean, consistently-styled matplotlib Gantt charts from a schedule CSV or DataFrame \u2014 with group colours, completion overlays, and a today line."
author: "Nazish Qasim"
tags: ["gantt", "timeline", "project-management", "matplotlib", "charts", "scripts"]
category: general
requires_env: []
source_ref: @cat-agent-skills/gantt_chart_generator
source_url: https://microsoft.github.io/cat-agent-skills/#gantt-chart-generator
source_license: MIT
converted_from: CAT Agent Skills
converted_on: 2026-08-06
---

# Gantt Chart Builder

> **Converted skill.** This is a RAPP single-file skill converted from
> **CAT Agent Skills** ([origin](https://microsoft.github.io/cat-agent-skills/#gantt-chart-generator)), redistributed under
> **MIT** with attribution. Original author: Nazish Qasim.
> Upstream license text: https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/LICENSE
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

Use this skill whenever the user asks to visualize a project schedule, timeline, Gantt chart, or phase/task breakdown over time. It gives the agent a prebuilt, parameterized gantt() function so Gantt charts are produced instantly and consistently — with colour-coded groups, completion overlays, a today reference line, and auto-scaled date axes — instead of hand-writing matplotlib each time.

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

Generate horizontal Gantt charts from schedule data via the bundled `scripts/gantt.py` toolkit.
The `gantt()` function accepts a DataFrame or file path plus column names, and saves a PNG (returning the path).
It handles theming, date parsing, bar colour-coding, completion overlays, today-line, legend, and saving.

## Instructions

1. Provide the data source: a pandas DataFrame, or a path to a `.csv` / `.tsv` / `.json` file.
   - One row = one task / phase.
   - Required columns: a **phase/task name** column, a **start date** column, and either an **end date** column OR a **duration-in-days** column.

2. Import and call `gantt()`:

```python
import sys
sys.path.insert(0, "scripts")   # adjust path to where gantt.py is deployed
from gantt import gantt

# Basic — start + end columns
gantt("schedule.csv", phase="Phase", start="Start", end="End",
      title="Project Schedule", out="gantt.png")

# Group colour-coding + today line
gantt(df, phase="phase", start="planned_start", end="planned_end",
      group="project", today=True, out="schedule.png")

# Duration instead of end date
gantt(df, phase="task", start="start_date", duration="days",
      out="schedule.png")

# Completion % hatch overlay
gantt(df, phase="Phase", start="Start", end="End",
      completion="PctDone", out="gantt.png")
```

3. See `references/cheatsheet.md` for full parameter reference and CLI examples.

## Bundled files
- `scripts/gantt.py`      — the full toolkit (load_data, apply_theme, save_fig, gantt, CLI)
- `references/cheatsheet.md` — parameter quick-reference and copy-paste examples
- `assets/sample_schedule.csv` — demo dataset that exercises every feature

## Defaults & behaviour
- Colorblind-friendly palette (matches chart-builder skill for visual consistency).
- Date axis auto-scales: weekly ticks ≤90 days, monthly ≤365 days, bi-monthly beyond.
- Bars ordered top-to-bottom matching input row order.
- Rows with missing phase or start values are silently dropped before drawing.
- Output PNG at 150 DPI by default.
- Provide `end` OR `duration` — not both; `end` takes priority if both are present.

---

*Converted for the AIBAST Agents Library from CAT Agent Skills.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
