---
schema: rapp-skill/1.0
name: @cat-agent-skills/eu_greenwashing_analysis
version: 1.0.0
display_name: "EU Greenwashing Analysis"
description: "Detect greenwashing in product descriptions, marketing copy, and catalog entries against EU Directive 2024/825 and the Green Claims Directive. Returns a structured per-claim findings report with risk levels, regulation references, and recommended corrections."
author: "Remi Dyon"
tags: ["compliance", "sustainability", "greenwashing", "eu-regulation", "marketing-review", "esg"]
category: it_management
requires_env: []
source_ref: @cat-agent-skills/eu_greenwashing_analysis
source_url: https://microsoft.github.io/cat-agent-skills/#eu-greenwashing-analysis
source_license: MIT
converted_from: CAT Agent Skills
converted_on: 2026-08-05
---

# EU Greenwashing Analysis

> **Converted skill.** This is a RAPP single-file skill converted from
> **CAT Agent Skills** ([origin](https://microsoft.github.io/cat-agent-skills/#eu-greenwashing-analysis)), redistributed under
> **MIT** with attribution. Original author: Remi Dyon.
> Upstream license text: https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/LICENSE
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

Use this skill whenever the user submits a product description, marketing text, catalog entry, packaging copy, or advertising claim and asks to check it for greenwashing, environmental claim compliance, sustainability wording risks, or alignment with EU Directive 2024/825 or the Green Claims Directive. Produces a structured per-claim findings report with risk levels, regulation references, and recommended corrections.

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

# EU Greenwashing Analysis

Run this procedure whenever a user submits a product description, marketing
text, or catalog entry for review against EU rules on environmental claims
(Directive 2024/825 amending 2005/29/EC, and the proposed Green Claims
Directive COM/2023/166).

The output is always a structured findings report: one block per flagged
claim plus a summary. Do not editorialize outside that structure.

---

## Step 1 — Extract all environmental claims

Read the full text and list every statement that references environmental
benefit, sustainability, ecological impact, or climate performance. Examples
include: "eco-friendly", "carbon neutral", "100% natural", "sustainable",
"green", "biodegradable", "zero emissions", "climate positive", "recycled",
"plastic-free", "low carbon", "environmentally safe".

If no such claims exist → output: **"No environmental claims detected — Out of Scope."** and stop.

---

## Step 2 — Assess each claim against EU greenwashing criteria

For each extracted claim, check ALL of the following:

1. **Vagueness / Generic claim** — Is the claim broad or unsubstantiated
   (e.g., "eco", "green", "sustainable") with no measurable indicator,
   certification, or evidence cited? → High risk flag.
2. **Incomplete life-cycle scope** — Does the claim highlight one phase of
   the product life cycle (e.g., recyclable packaging) while ignoring other
   high-impact phases (manufacturing, transport, end-of-life)? → Medium to
   High risk flag.
3. **Unverifiable / No third-party certification** — Is there no independent
   verification, recognized EU certification, or scientific reference to
   support the claim? → Medium to High risk flag.
4. **Misleading comparison** — Does the claim compare the product favorably
   against an irrelevant benchmark, obsolete product, or omit material
   information that would change the consumer's perception? → High risk flag.
5. **Carbon offset reliance** — Does the claim (e.g., "carbon neutral", "net
   zero") rely primarily on carbon offsetting schemes rather than actual
   emission reductions? If offsets are not independently verified under
   EU-recognized standards → Medium to High risk flag.
6. **Unsupported label or logo** — Does the product display an environmental
   label, badge, or logo that is not officially recognized in the EU, or
   whose criteria have not been verified? → High risk flag.
7. **Forward-looking claim presented as current** — Is a future commitment
   (e.g., "will be carbon neutral by 2030") presented in a way that implies
   a current state? → Medium risk flag.

---

## Step 3 — Assign a risk level per claim

- 🔴 **High** — Claim is clearly unsubstantiated, misleading, or likely
  non-compliant with EU Directive 2024/825 or the Green Claims Directive.
  Immediate corrective action required.
- 🟡 **Medium** — Claim is partially substantiated but lacks full
  verification, life-cycle scope, or specificity. Corrective action
  recommended before publication.
- 🟢 **Low** — Claim is specific and plausible but should be reviewed for
  formal certification before final catalog inclusion.

---

## Step 4 — Fill the standard findings template

For EACH flagged claim, output one block in this exact format:

---
**Product Claim:** [exact quote of the claim as it appears in the text]
**Risk Level:** 🔴 High / 🟡 Medium / 🟢 Low
**Regulation Reference:** [e.g., "EU Directive 2024/825, Art. 3 — Prohibition of misleading environmental claims" or "Green Claims Directive COM/2023/166, Art. 5 — Substantiation requirements"]
**Issue:** [1–2 sentences explaining what makes this claim problematic under EU regulation]
**Recommended Correction:** [suggested compliant rewrite or specific action the team should take, e.g., "Replace with a specific, verified figure: 'Made with 40% recycled ocean plastic, certified by [recognized body]'"]
---

---

## Step 5 — Summary assessment

After all per-claim blocks, output a summary in this format:

**Greenwashing Findings Summary**
- Total environmental claims reviewed: [N]
- 🔴 High risk: [N]
- 🟡 Medium risk: [N]
- 🟢 Low risk: [N]
- ✅ Compliant (no action needed): [N]
- **Overall compliance posture:** Compliant / Needs Review / Non-Compliant
- **Top priority action:** [single most urgent corrective step]

---

*Converted for the AIBAST Agents Library from CAT Agent Skills.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
