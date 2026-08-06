---
schema: rapp-skill/1.0
name: @cat-agent-skills/anonymised_case_study_writer
version: 0.1.0
display_name: "Anonymised Case Study Writer"
description: "Turn engagement notes into anonymised, publishable case studies without exposing client-confidential details."
author: "Simon Owen"
tags: ["writing", "case-study", "marketing", "documents", "content", "privacy"]
category: general
requires_env: []
source_ref: @cat-agent-skills/anonymised_case_study_writer
source_url: https://microsoft.github.io/cat-agent-skills/#anonymised-case-study-writer
source_license: MIT
converted_from: CAT Agent Skills
converted_on: 2026-08-05
---

# Anonymised Case Study Writer

> **Converted skill.** This is a RAPP single-file skill converted from
> **CAT Agent Skills** ([origin](https://microsoft.github.io/cat-agent-skills/#anonymised-case-study-writer)), redistributed under
> **MIT** with attribution. Original author: Simon Owen.
> Upstream license text: https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/LICENSE
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

Use this skill when the user asks to create, improve, anonymise, structure, or publish a client case study, success story, engagement summary, or transformation story.

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

# Anonymised Case Study Writer

Use this skill to create credible, anonymised case studies from engagement notes, interview notes, project summaries, outcomes, or source documents.

## Core rules

1. **Protect confidentiality.** Remove or generalise names, client identifiers, locations, internal programme names, system names, and commercially sensitive details unless the user explicitly says they are public.
2. **Do not invent outcomes.** Only include outcomes, metrics, timelines, and benefits that appear in the source material or are supplied by the user.
3. **Preserve credibility.** Prefer specific operational detail over vague marketing claims, while keeping the client anonymised.
4. **Make the story reusable.** Structure the case study so it can be used in proposals, webpages, thought leadership, sales conversations, and internal learning.
5. **Separate unknowns.** If outcomes or proof points are missing, include a short "Evidence gaps" section rather than fabricating.

## Default anonymisation pattern

Use neutral descriptors such as:

- A large public sector organisation.
- A global consumer goods company.
- A regulated financial services organisation.
- A national healthcare provider.
- A multinational energy business.

Only describe sector, scale, geography, and technology where the source material supports it and doing so does not identify the client.

## Workflow

1. Read all supplied source material.
2. Extract the engagement context, problem, constraints, intervention, outcomes, and lessons.
3. Identify any confidential or identifying details and replace them with safe descriptors.
4. Draft the case study using the structure below.
5. Check every claim against the source material.
6. Add evidence gaps or suggested follow-up questions only where needed.
7. Return copy-ready Markdown.

## Default structure

```markdown
# [Case study title]

## At a glance

| Field | Summary |
|---|---|
| Client type | [Anonymised descriptor] |
| Sector | [Sector if known] |
| Challenge | [One-sentence challenge] |
| Work delivered | [One-sentence intervention] |
| Outcome | [Evidence-backed outcome or "Outcome evidence not provided"] |

## Context

[What was happening and why it mattered.]

## The challenge

[The specific business, operating, adoption, governance, delivery, or technology problem.]

## What we did

[Practical work performed. Use bullets only where they improve clarity.]

## What changed

[Evidence-backed outcomes, capability shifts, decisions enabled, delivery improvements, or learning generated.]

## Why it mattered

[Business relevance and wider lesson.]

## Reusable insight

[The portable lesson other organisations can learn from this case.]

## Evidence gaps

- [Only include if relevant.]
```

## Style guidance

- Write in a human, experienced, consultancy-literate voice.
- Avoid exaggerated sales language.
- Avoid implying certainty where the source only suggests possibility.
- Make the piece useful even if formal metrics are unavailable.
- Keep paragraphs short enough for web reading.


## References

This skill includes supporting reference material. Read the relevant reference file when the task needs additional structure, rubric detail, examples, or checklist support.

- `references/anonymisation-checklist.md` - use this when additional structure, examples, or checks are useful for the task.

## Quality checklist

Before responding, check:

- No client-confidential detail has leaked.
- Every outcome is backed by supplied evidence.
- The case study has a clear before / intervention / after shape.
- The writing is credible and not generic.
- Evidence gaps are visible rather than hidden.

---

*Converted for the AIBAST Agents Library from CAT Agent Skills.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
