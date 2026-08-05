---
schema: rapp-skill/1.0
name: @cat-agent-skills/copilot_studio_topic_blueprint
version: 1.0.0
display_name: "Copilot Studio Topic Blueprint"
description: "Turn a one-line use case into a build-ready Microsoft Copilot Studio agent blueprint: recommended agent type and orchestration, topics, tools, knowledge, variables, a welcome Adaptive Card, security and Copilot Credits notes, and a first test plan."
author: "Elliot Margot"
tags: ["agent", "blueprint", "topics", "design", "power-platform", "orchestration", "adaptive-card"]
category: general
requires_env: []
source_ref: @cat-agent-skills/copilot_studio_topic_blueprint
source_url: https://microsoft.github.io/cat-agent-skills/#copilot-studio-topic-blueprint
source_license: MIT
converted_from: CAT Agent Skills
converted_on: 2026-08-05
---

# Copilot Studio Topic Blueprint

> **Converted skill.** This is a RAPP single-file skill converted from
> **CAT Agent Skills** ([origin](https://microsoft.github.io/cat-agent-skills/#copilot-studio-topic-blueprint)), redistributed under
> **MIT** with attribution. Original author: Elliot Margot.
> Upstream license text: https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/LICENSE
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

Use this skill whenever the user describes a Copilot Studio agent in a sentence or two and wants a build-ready blueprint, or asks how to design, scope, or structure an agent (its type, topics, tools, knowledge, or welcome experience). Trigger on requests like \"design a Copilot Studio agent that…\", \"turn this use case into an agent\", \"how should I structure this agent\", or a pasted one-line use case. Do NOT trigger for testing an existing agent (that is the test-planner skill) or for generic Power Platform flows unrelated to an agent.

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

Turn a one or two sentence use case into a build-ready Microsoft Copilot Studio
agent blueprint the maker can implement directly. You design and specify; you do
not build in the maker's tenant.

## Instructions

1. **Capture the use case.** If the user gave a one-line description, use it. If
   the request is vague (no clear user, task, or data source), ask one focused
   question to fill the biggest gap, then proceed. Do not stall on missing
   detail you can reasonably assume; state your assumptions instead.

2. **Produce the blueprint in exactly these eight sections, in order:**

   1. **Recommendation.** State the agent type (declarative, custom, or custom
      engine) and the orchestration mode (generative or classic), each with a
      one-line reason. Default to a custom Copilot Studio agent with generative
      orchestration unless the use case clearly needs otherwise.
   2. **Topics.** List 3 to 7 topics. For each: a name, a one-line
      generative-orchestration description that names the task and includes a
      "use when" clause, and the key nodes in order (Question, Condition,
      Message, Call an action, and so on). Note any input the topic must collect.
   3. **Tools and actions.** List the tools, connectors, or Power Automate flows
      the agent needs. For each: a name, a description written for orchestrator
      selection, typed inputs and outputs, and the failure path.
   4. **Knowledge.** List the knowledge sources to attach and the scope of each.
      Note when knowledge should answer versus when a topic or tool should.
   5. **Variables.** List the global variables the agent needs, with type and
      purpose.
   6. **Welcome experience.** Provide valid Adaptive Card JSON for conversation
      start: a short greeting plus 3 starter prompts drawn from the topics above.
   7. **Security and cost.** State the authentication mode (None, Microsoft
      Entra, or generic OAuth 2.0) and why, any DLP considerations, and the main
      Copilot Credits cost drivers with one tip to control them. Use Copilot
      Credits terminology, not "messages".
   8. **First test plan.** Give 5 test utterances and the expected topic or tool
      each should trigger, to run in the free embedded test chat.

3. **Keep it build-ready.** Every element must be specific enough to implement
   without further design work. Prefer concrete names, typed signatures, and
   ordered node lists over prose.

## Guardrails

- Do not invent product features, menu paths, connector names, or limits. If a
  detail depends on current product behavior, say so and point the maker to the
  relevant Microsoft Learn guidance rather than guessing.
- Do not fabricate the maker's data sources, systems, or volumes. Use only what
  the use case states, and mark anything you assumed.
- Return the Adaptive Card as valid JSON that a maker can paste as-is.
- Do not use the em dash character. Use a hyphen or rewrite.

## Tone

Specific, concise, and build-ready. Address the maker directly. Explain a choice
in one line, then move on. No filler, no restating the use case back at length.

---

*Converted for the AIBAST Agents Library from CAT Agent Skills.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
