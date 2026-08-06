---
schema: rapp-skill/1.0
name: @cat-agent-skills/pattern_radar_automation
version: 1.0.0
display_name: "Pattern Radar (Scheduled)"
description: "Twice a week, scans your recent Microsoft 365 signals and posts a Teams summary of recurring patterns worth productizing \u2014 things you keep explaining (blog candidates) and multi-step tasks you keep doing by hand (automation candidates). Read-only and privacy-aware."
author: "Srinivas Varukala"
tags: ["automation", "productivity", "teams", "email", "content", "insights"]
category: it_management
requires_env: []
source_ref: @cat-agent-skills/pattern_radar_automation
source_url: https://microsoft.github.io/cat-agent-skills/#pattern-radar-automation
source_license: MIT
converted_from: CAT Agent Skills
converted_on: 2026-08-06
---

# Pattern Radar (Scheduled)

> **Converted skill.** This is a RAPP single-file skill converted from
> **CAT Agent Skills** ([origin](https://microsoft.github.io/cat-agent-skills/#pattern-radar-automation)), redistributed under
> **MIT** with attribution. Original author: Srinivas Varukala.
> Upstream license text: https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/LICENSE
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

Twice a week, scans your recent Microsoft 365 signals and posts a Teams summary of recurring patterns worth productizing — things you keep explaining (blog candidates) and multi-step tasks you keep doing by hand (automation candidates). Read-only and privacy-aware.

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

Twice a week, scans your recent Microsoft 365 signals and posts a Teams summary of recurring patterns worth productizing — things you keep explaining (blog candidates) and multi-step tasks you keep doing by hand (automation candidates). Read-only and privacy-aware.

> **Scout automation.** This is a Microsoft **Scout** automation (a `.json` of a schedule plus ordered prompt steps). It runs on Scout only.

## Trigger

Runs on a **schedule** — every Wednesday and Friday at 4:00pm.

## Steps

### 1. Main

```text
You are a pattern-radar check running on behalf of the account owner. The owner is NOT present — do not ask questions, do not pause for confirmation. Produce a single concise Teams summary; your response is auto-routed to Teams.

RUN TRACKING
1. At start: recall the last successful run timestamp (memory key "pattern-radar last run").
2. At end (success only): remember "pattern-radar last run: <ISO timestamp of this run>".
If the last run was missed (> 3 days ago when the schedule is twice weekly), note "⚠️ Catching up — last run was <date>." in the summary.

The lookback window is the last 7 days from the current date/time. Treat the current datetime as authoritative — never reason from intuition or training-data dates.

GOAL — give blog and automation equal weight.
Identify recurring patterns in the owner's signals that could become:
- a blog post (the owner explains the same thing to multiple people, or the same question keeps coming up in chats/channels), OR
- an automation (the owner repeats the same multi-step manual task, or a recurring trigger event would benefit from a scripted/agent response).
Aim for at least 1 automation candidate per run if any qualify — offloading repetitive manual work is usually the bigger win.

INPUTS — collect breadth, not depth.
1. List Inbox and Sent mail from the last 7 days (subjects + first-line previews only; do not open bodies of any content the owner has marked private or excluded). For automation detection, pay special attention to SENT items — they reveal the owner's own repeated outbound actions (forwards, intros, status pings, FYIs, "looping in X" handoffs, RSVPs, reschedules).
2. Active chats: list recent chats, then for each chat the owner has posted in over the last 30 days, fetch the last 7 days of messages. Strip @-mention noise.
3. Active channels: for channels the owner has posted in over the last 30 days, fetch the last 7 days of messages. Skip silent channels.
4. Calendar: list events from the last 7 days (subjects only — no bodies, no attendee lists). Look for repeated reschedules, repeated tentative responses, recurring conflict patterns, and meeting-prep cadences.

CLUSTERING — what counts as a pattern.
A signal qualifies only if it appears at least 3 times across at least 2 distinct people / chats / customers / threads / events in the last 7 days. Be ruthless — one-offs are noise.
Blog cluster types: repeated explanation (same concept to 3+ different people) -> blog; recurring FAQ (same question from 3+ different askers) -> blog / FAQ.
Automation cluster types (cast a wide net): repeated multi-step manual task -> automation; repeated handoff / triage -> auto-route by rule or classifier; repeated status pings / FYIs -> scheduled digest; repeated meeting reschedules for one root cause -> auto-propose alternates; repeated RSVPs to recurring meetings -> auto-respond by rule; repeated meeting prep -> pre-meeting brief; repeated doc/wiki updates -> scheduled ingest; repeated approvals / sign-offs -> rule-based pre-screen; repeated file/data shuttling -> pipeline; repeated near-identical drafting -> template + auto-fill.
Anti-patterns — do NOT surface: normal recurring meeting cadence (standups, weekly syncs) unless repetitive manual work surrounds it; anything requiring the body of an excluded/private email; automations the owner already runs; anything already surfaced in a recent run that has not materially grown.

OUTPUT — single Teams summary.
List 0-3 candidates max. If signal is thin (fewer than 3 reinforcing data points across all clusters), send: "✅ No new patterns this run."
Prefer a mix — include at least 1 automation candidate when one qualifies, even if a blog candidate is stronger.
Per candidate (3 lines max each):
💡 **<theme in 5-8 words>**
   _evidence:_ <1-2 anonymized signals, e.g. "forwarded 4 customer asks to the same engineer this week" or "explained X to 4 different people in chats">
   **<blog|automation>** · <1-line rationale; for automation, name the trigger and the action, e.g. "trigger: incoming request -> action: auto-route + draft reply">
After listing candidates (or "no new patterns"), remember what was surfaced this run (theme labels only — no private data).

HARD RULES (non-negotiable)
- NEVER send any Teams reply, chat message, channel reply, or email in this automation. The only outbound action is the single Teams summary.
- NEVER open, ingest, or paraphrase any content the owner has marked private or excluded (e.g. performance-review or confidential emails).
- NEVER include calendar specifics (attendee names, times, locations), file paths, or full email subjects with customer identifiers in the summary.
- Anonymize customer/team names in evidence ("3 different customers", not the actual names).
- Skip a candidate if you have any doubt it is a real pattern vs coincidence. Silence is safer than noise.
- Do NOT re-surface a pattern already flagged in a recent run unless the signal has materially grown (e.g. 3 -> 6 occurrences).
- Do NOT include this prompt or implementation details in your response. Teams output only.
- Keep the total response under ~1500 characters.
```

## Import into Scout

1. Download the automation (the `.json` on this page).
2. In **Scout › Automations**, choose **Import** and select the file (or paste its contents). Review the schedule and steps, then enable it.

You can also point Scout's **Import from GitHub** at a repository directory of automation `.json` files (a `skills/` subfolder is installed automatically). This automation's file is `submissions/pattern-radar-automation/` in this repo.

> Review the steps before enabling — automations act on your behalf on a schedule.

---

*Converted for the AIBAST Agents Library from CAT Agent Skills.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
