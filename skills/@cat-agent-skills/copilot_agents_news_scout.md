---
schema: rapp-skill/1.0
name: @cat-agent-skills/copilot_agents_news_scout
version: 1.0.0
display_name: "Copilot & Agents News Scout"
description: "A Monday-morning Scout automation that scans authoritative Microsoft sources for the past week's Copilot, Copilot Studio, and agent news and posts a concise, linked digest to Teams."
author: "Elliot Margot"
tags: ["news", "copilot", "agent", "digest", "automation", "weekly", "teams"]
category: it_management
requires_env: []
source_ref: @cat-agent-skills/copilot_agents_news_scout
source_url: https://microsoft.github.io/cat-agent-skills/#copilot-agents-news-scout
source_license: MIT
converted_from: CAT Agent Skills
converted_on: 2026-08-06
---

# Copilot & Agents News Scout

> **Converted skill.** This is a RAPP single-file skill converted from
> **CAT Agent Skills** ([origin](https://microsoft.github.io/cat-agent-skills/#copilot-agents-news-scout)), redistributed under
> **MIT** with attribution. Original author: Elliot Margot.
> Upstream license text: https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/LICENSE
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

A Monday-morning Scout automation that scans authoritative Microsoft sources for the past week's Copilot, Copilot Studio, and agent news and posts a concise, linked digest to Teams.

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

A Monday-morning Scout automation that scans authoritative Microsoft sources for the past week's Copilot, Copilot Studio, and agent news and posts a concise, linked digest to Teams.

> **Scout automation.** This is a Microsoft **Scout** automation (a `.json` of a schedule plus ordered prompt steps). It runs on Scout only.

## Trigger

Runs on a **schedule** — every Monday at 8:00 AM.

## Steps

### 1. Gather the week's updates

```text
Search authoritative Microsoft sources published or updated in the last 7 days for news about Microsoft 365 Copilot, Copilot Studio, Copilot agents, and Microsoft Scout. Prioritize: the Microsoft 365 and Copilot blogs (microsoft.com/blog), Microsoft Learn 'what's new' and release pages, the Message Center and Microsoft 365 roadmap, and the Power Platform / Copilot Studio release plans. For each item, capture the title, the canonical URL, the publish or update date, and a one-sentence summary in your own words. Collect everything relevant now; do not filter yet.
```

### 2. Filter to what matters

```text
From the items gathered, keep only material changes a Copilot Studio maker or M365 admin would act on: general availability, public preview, deprecations and breaking changes, pricing or Copilot Credits changes, new connectors or capabilities, and roadmap dates. Drop marketing recaps, opinion pieces, and anything older than 7 days. Deduplicate items that cover the same announcement, keeping the most authoritative source. If nothing material shipped this week, note that plainly rather than padding the list.
```

### 3. Write and post the Teams digest

```text
Write a concise digest titled 'Copilot & Agents - week of <date>'. Group items under headings: Microsoft 365 Copilot, Copilot Studio, Agents & Scout, and Governance & Admin (omit any empty group). For each item give the title as a link, the date, and a one-line 'why it matters'. Keep the whole digest scannable in under two minutes. Post it to Teams. Do not invent items, dates, or links; include only what the previous step verified. Do not use the em dash character.
```

## Import into Scout

1. Download the automation (the `.json` on this page).
2. In **Scout › Automations**, choose **Import** and select the file (or paste its contents). Review the schedule and steps, then enable it.

You can also point Scout's **Import from GitHub** at a repository directory of automation `.json` files (a `skills/` subfolder is installed automatically). This automation's file is `submissions/copilot-agents-news-scout/` in this repo.

> Review the steps before enabling — automations act on your behalf on a schedule.

---

*Converted for the AIBAST Agents Library from CAT Agent Skills.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
