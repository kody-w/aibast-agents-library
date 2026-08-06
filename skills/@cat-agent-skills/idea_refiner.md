---
schema: rapp-skill/1.0
name: @cat-agent-skills/idea_refiner
version: 1.0.0
display_name: "Idea Refiner"
description: "Refines an existing plan, decision, or draft through relentless, branch-by-branch questioning. Grouped in batches of 2-5 with recommended answers, pulling facts from Work IQ where possible, until every part has been fully thought through."
author: "Mathias Salomonsen"
tags: ["productivity", "planning", "decision-making", "refinement", "brainstorming"]
category: human_resources
requires_env: []
source_ref: @cat-agent-skills/idea_refiner
source_url: https://microsoft.github.io/cat-agent-skills/#idea-refiner
source_license: MIT
converted_from: CAT Agent Skills
converted_on: 2026-08-06
---

# Idea Refiner

> **Converted skill.** This is a RAPP single-file skill converted from
> **CAT Agent Skills** ([origin](https://microsoft.github.io/cat-agent-skills/#idea-refiner)), redistributed under
> **MIT** with attribution. Original author: Mathias Salomonsen.
> Upstream license text: https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/LICENSE
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

Refine the user's existing plan, decision, or draft through relentless refinement. Use when the user wants to sharpen or stress-test their thinking.

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

Assume a plan, decision, or draft already exists. The job is to sharpen it with questions, not draft one from scratch, and ensure that I have fully thought through the entire plan.

Walk down each branch of the decision tree, resolving dependencies between decisions one-by-one. For each question, give your recommended answer.

Group each turn's questions by branch: 2–5 related questions per turn, sized to what that branch needs. For each question, provide your recommended answer. Wait for my feedback on the whole batch before moving to the next branch.

If Work IQ is available, look through Work IQ for any facts before asking me. Put every decision to me directly and wait for my answer.

Do not act on it until I confirm we have reached a shared understanding.

---

*Converted for the AIBAST Agents Library from CAT Agent Skills.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
