---
schema: rapp-skill/1.0
name: @cat-agent-skills/style_analyzer
version: 1.0.0
display_name: "Communication Style Analyzer"
description: "Analyzes your Teams chats and emails to build a reusable profile of your writing voice \u2014 greetings, tone, length, punctuation, sign-offs, common phrases, and quirks \u2014 and saves it to memory for other assistants to use."
author: "Srinivas Varukala"
tags: ["writing", "style", "teams", "email", "memory", "productivity"]
category: it_management
requires_env: []
source_ref: @cat-agent-skills/style_analyzer
source_url: https://microsoft.github.io/cat-agent-skills/#style-analyzer
source_license: MIT
converted_from: CAT Agent Skills
converted_on: 2026-08-05
---

# Communication Style Analyzer

> **Converted skill.** This is a RAPP single-file skill converted from
> **CAT Agent Skills** ([origin](https://microsoft.github.io/cat-agent-skills/#style-analyzer)), redistributed under
> **MIT** with attribution. Original author: Srinivas Varukala.
> Upstream license text: https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/LICENSE
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

Analyze the user's communication style across their Teams chats and emails to build a reusable mimicry profile — greetings, tone, length, punctuation, sign-offs, common phrases, and quirks. Use this skill when the user asks to capture or analyze their writing style, or before configuring an assistant (e.g. an OOO auto-responder) that should write in their voice.

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

# Style Analyzer

Analyze the user's communication patterns across Teams and Outlook and build a
style profile that other skills or automations (e.g. an out-of-office
auto-responder) can use to write in the user's voice. Save the profile to memory
so it's available across sessions.

> **Tool names.** This skill refers to Microsoft 365 tools as `m365_*` and to
> memory as remember/recall tools. If your host exposes these under different
> names, map them to the equivalent capability.

## Data collection

### 1. Gather sent emails (20–30 samples)

- List the last ~30 emails in the **Sent** folder.
- For emails with real body content (not just meeting accepts/declines), fetch
  the full text body.

### 2. Gather Teams chat messages

- List recent chats (~50).
- For each relevant chat (prioritize active 1:1 and group chats), fetch the last
  ~30 messages.
- Filter to messages **from the current user** (match the `from` field to the
  user's display name).

### 3. Sample diversity

Aim for:

- 10+ sent emails with body content
- 50+ Teams messages across **20–25 different chats**
- A mix of 1:1, group, and meeting chats
- Both internal and external conversations where available

## Analysis framework

Analyze the collected messages across these dimensions:

- **A. Greetings** — how they address people (first name, "Hi [Name]", "Hey",
  formal titles); patterns by relationship type (internal vs external).
- **B. Tone & formality** — professional/casual/mixed; direct vs hedging; warmth
  indicators.
- **C. Message length** — average sentence count; frequency of one-word replies;
  when they write longer messages.
- **D. Punctuation & grammar** — consistency; common typos (e.g. lowercase "i");
  emoji usage (none / occasional / frequent).
- **E. Sign-offs** — email signature style; Teams message endings; closing
  phrases ("Thanks", "Regards", etc.).
- **F. Common phrases** — frequently used expressions for agreement ("sounds
  good", "makes sense"), requests ("can you", "would you mind"), availability,
  and FYI/context-setting.
- **G. Technical communication** — how they explain technical concepts; level of
  detail; hedging vs confidence.
- **H. Action patterns** — how they delegate, loop others in, and schedule
  meetings.

## Output

### 1. Display a summary

Present findings as a formatted table:

```markdown
## Communication Style Profile for [Name]

| Dimension | Pattern |
|-----------|---------|
| Greetings | ... |
| Tone | ... |
| Length | ... |
| Emojis | ... |
| Sign-offs | ... |
| Technical | ... |

### Common phrases
- "..."
- "..."

### Quirks & notes
- ...
```

### 2. Save to memory

Store the style guide in memory. Use two entries to stay within any per-fact
length limits:

- **Entry 1** — greetings, tone, brevity, punctuation, emojis.
- **Entry 2** — common phrases, delegation style, technical communication,
  quirks.

Tag both as a preference so they persist and can be recalled later.

### 3. Confirm storage

Tell the user:

- The style profile has been saved to memory.
- It can be recalled with a query like "writing style".
- It's available to other assistants and automations that write in their voice.

## Usage notes

- Re-run periodically (e.g. quarterly) to keep the profile current.
- Pairs well with an OOO / auto-responder skill that should mimic the user's
  voice.

## Privacy

All analysis happens inside the user's own agent environment against their own
Microsoft 365 data. No communication content is sent to any third party. The
saved profile describes *how* the user writes, not *what* they wrote — do not
store verbatim private message content in the profile.

---

*Converted for the AIBAST Agents Library from CAT Agent Skills.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
