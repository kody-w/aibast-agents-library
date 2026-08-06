---
schema: rapp-skill/1.0
name: @cat-agent-skills/commenting_content
version: 1.0.0
display_name: "Commenting Content"
description: "Comments Word or PowerPoint files with Comments."
author: "AndrewHessMSFT"
tags: ["documents", "productivity"]
category: general
requires_env: []
source_ref: @cat-agent-skills/commenting_content
source_url: https://microsoft.github.io/cat-agent-skills/#commenting-content
source_license: MIT
converted_from: CAT Agent Skills
converted_on: 2026-08-05
---

# Commenting Content

> **Converted skill.** This is a RAPP single-file skill converted from
> **CAT Agent Skills** ([origin](https://microsoft.github.io/cat-agent-skills/#commenting-content)), redistributed under
> **MIT** with attribution. Original author: AndrewHessMSFT.
> Upstream license text: https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/LICENSE
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

Analyzes a .docx or .pptx file, researches the topic using internal documents, emails, Microsoft Teams messages, and web sources, then adds native comments throughout the file authored by \"Copilot Studio AI\" — without modifying the original content.

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

# Comment Content

When this skill is activated:

1. Check the file extension of the attached document.
   - If `.docx` → follow the instructions in `REFERENCE-DOCX.md`
   - If `.pptx` → follow the instructions in `REFERENCE-PPTX.md`
   - If any other format → ask the user to convert to `.docx` or `.pptx` first.
2. Execute the full commenting workflow defined in the appropriate reference file.
3. Return the updated file with native comments embedded and a short chat summary of findings.

## Guidelines

- Never modify the original document content — add comments only.
- Set the comment author to `Copilot Studio AI` on every comment added.
- Research using any available sources: internal documents, emails, Microsoft Teams messages, approved knowledge sources, and web research tools.
- Only comment where it genuinely helps — do not comment on every sentence.
- The chat summary must include: comment count, main research findings, and top 1–3 priority issues for the author to review.

## Reference Files

- [`REFERENCE-DOCX.md`](./REFERENCE-DOCX.md) — Word document commenting instructions
- [`REFERENCE-PPTX.md`](./REFERENCE-PPTX.md) — PowerPoint presentation commenting instructions

## Examples

**Example 1: Word document**
- User request: "Add research comments to this report." (attaches report.docx)
- Expected behavior: Detect .docx, follow REFERENCE-DOCX.md, return commented .docx with summary.

**Example 2: PowerPoint presentation**
- User request: "Review this deck and add comments." (attaches deck.pptx)
- Expected behavior: Detect .pptx, follow REFERENCE-PPTX.md, return commented .pptx with summary.

## Notes

- If multiple files are attached, process them one at a time and produce a separate summary for each.
- If the file type is ambiguous, ask the user to confirm before proceeding.

---

*Converted for the AIBAST Agents Library from CAT Agent Skills.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
