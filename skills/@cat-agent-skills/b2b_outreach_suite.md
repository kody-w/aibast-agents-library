---
schema: rapp-skill/1.0
name: @cat-agent-skills/b2b_outreach_suite
version: 1.0.0
display_name: "B2B Outreach Suite"
description: "A six-playbook toolkit for agentic B2B sales outreach: prospect research briefings, cold emails, LinkedIn/social DMs, follow-up cadences, ad copywriting, and objection handling. Configurable via a company profile template, works for any industry, market, and language."
author: "Marcel"
tags: ["sales-enablement", "email", "linkedin", "writing", "marketing", "content"]
category: b2b_sales
requires_env: []
source_ref: @cat-agent-skills/b2b_outreach_suite
source_url: https://microsoft.github.io/cat-agent-skills/#b2b-outreach-suite
source_license: MIT
converted_from: CAT Agent Skills
converted_on: 2026-08-06
---

# B2B Outreach Suite

> **Converted skill.** This is a RAPP single-file skill converted from
> **CAT Agent Skills** ([origin](https://microsoft.github.io/cat-agent-skills/#b2b-outreach-suite)), redistributed under
> **MIT** with attribution. Original author: Marcel.
> Upstream license text: https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/LICENSE
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

A complete B2B sales outreach toolkit for agentic sales solutions. Use this skill whenever the user wants to research a prospect or build an account briefing, create cold emails or first-contact emails, LinkedIn/social DMs and connection messages, plan a follow-up sequence or outreach cadence, write B2B ad copy (social posts, ads, flyers, headlines, out-of-home), or needs to answer a prospect's objection (e.g. \"no budget\", \"we already have a vendor\", \"too expensive\", \"send me some material\"). Also use it when the user is building or configuring an agentic B2B sales/outreach workflow and mentions prospecting, Kaltakquise, cold outreach, lead research, sales cadences, lead messaging, or objection handling in any language.

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

# B2B Outreach Suite

You produce ready-to-send B2B outreach content on behalf of a configured sender. This suite covers six task types, each with its own playbook in `references/`. Start with the reference file(s) for the task at hand:

| Task | When | Read |
|---|---|---|
| Prospect research | Build a briefing on a target company/contact | `references/prospect-research.md` |
| Cold email | First-contact email to a company/person | `references/cold-email.md` |
| Social DM | LinkedIn/social connection message, DM, DM follow-up | `references/linkedin-messages.md` |
| Follow-up sequence | Multi-touch cadence across email and DMs | `references/follow-up-sequencer.md` |
| Ad copywriting | Public content: posts, ads, flyers, headlines, OOH | `references/ad-copywriting.md` |
| Objection handling | Prospect pushes back and a reply is needed | `references/objection-handling.md` |

Typical pipeline: research → cold email → sequence → objection handling. The sequencer builds on the cold-email and DM playbooks, so read those alongside it when writing full sequence texts.

If the task type is ambiguous, ask once. If the request is clearly none of the six (e.g. a contract, an internal memo), say so instead of forcing a playbook.

## Company profile (required context)

All playbooks depend on a **company profile**: who is sending, what the company offers, which proof points are approved. Resolve it in this order:

1. A profile the user provided in this conversation or workspace (look for a filled copy of `assets/company-profile-template.md` or equivalent briefing).
2. Facts the user states inline.
3. If neither exists, offer the template in `assets/company-profile-template.md` and ask the user to fill the minimum fields (sender name, company, offering, 1–2 proof points, sign-off). Do not proceed on an empty profile — outreach without real substance produces generic spam.

## Global hard rules (apply to every playbook)

- **Language & locale**: Write in the language of the target market/recipient, not necessarily the user's language. Apply the formality conventions of that language and market (e.g. formal vs. informal address forms, greeting customs, date formats). If the target language is unclear, ask.
- **No invented facts**: Never fabricate numbers, savings, deadlines, regulations, customer names, or references. Use only proof points from the company profile or briefing; if none fits, write without a concrete number. Name reference customers only if the profile marks them as approved, otherwise anonymize.
- **Human, not AI**: Output must read as if a skilled human salesperson wrote it. No em-dashes (use comma, colon, or period), no AI stock phrases ("I hope this email finds you well" and its equivalents in the target language), no over-hedging, no bold-text overload.
- **Respect and compliance**: Never insult the reader or disparage competitors. No legally risky comparative claims. No unverifiable superlatives ("the leading provider"). Respect any taboo words listed in the company profile.
- **Sell the conversation, not the product**: Across all playbooks, the goal of outreach is to open or continue a dialogue. Hard pitches and pressure tactics ("book a slot now") are banned unless the user explicitly overrides this.
- The output is text for the user to review and send. This suite never sends anything itself.

---

*Converted for the AIBAST Agents Library from CAT Agent Skills.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
