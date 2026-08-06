---
schema: rapp-skill/1.0
name: @cat-agent-skills/knowledge_source_router
version: 1.0.0
display_name: "Knowledge Source Router"
description: "Route Copilot Studio knowledge searches to the right region-specific source (Americas, EMEA, APAC, or Global) based on where the user is, so answers stay locally accurate."
author: "Adi Leibowitz"
tags: ["knowledge", "routing", "localization", "location", "grounding"]
category: it_management
requires_env: []
source_ref: @cat-agent-skills/knowledge_source_router
source_url: https://microsoft.github.io/cat-agent-skills/#knowledge-source-router
source_license: MIT
converted_from: CAT Agent Skills
converted_on: 2026-08-06
---

# Knowledge Source Router

> **Converted skill.** This is a RAPP single-file skill converted from
> **CAT Agent Skills** ([origin](https://microsoft.github.io/cat-agent-skills/#knowledge-source-router)), redistributed under
> **MIT** with attribution. Original author: Adi Leibowitz.
> Upstream license text: https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/LICENSE
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

Determines which region-specific knowledge source(s) to search based on the user's location. You MUST invoke this skill BEFORE calling the KnowledgeSearch tool, and pass the chosen source(s) as its `sources` parameter.

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

Pick the correct region-specific knowledge source(s) for a query based on the
**user's location**, so answers are grounded in content that is accurate for
where the user is. Always do this BEFORE calling the `KnowledgeSearch` tool, and
pass the chosen source(s) as the `sources` parameter of that call — on every
knowledge-grounded question. Policies, benefits, pricing, legal/compliance,
support hours, and product availability frequently differ by country or region,
so read from the source that matches the user's location before answering.

## Available sources
| Source | Use when the user is located in... |
| --- | --- |
| `Global` | Any location, for content that is the same everywhere (fallback / default). |
| `Americas` | United States, Canada, Mexico, Central & South America. |
| `EMEA` | Europe, the Middle East, and Africa. |
| `APAC` | Asia, Australia, and the Pacific. |

---

*Converted for the AIBAST Agents Library from CAT Agent Skills.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
