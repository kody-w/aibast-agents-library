---
schema: rapp-skill/1.0
name: @cat-agent-skills/copilot_studio_test_planner
version: 1.0.0
display_name: "Copilot Studio Test Planner"
description: "Reads an exported Copilot Studio agent and generates a graded, runnable test suite (happy-path, paraphrase, disambiguation, negative, knowledge-grounding, multilingual, and safety cases) plus a regression set, ready to run in the free Copilot Studio test panel."
author: "Elliot Margot"
tags: ["qa", "eval", "regression", "agent"]
category: human_resources
requires_env: []
source_ref: @cat-agent-skills/copilot_studio_test_planner
source_url: https://microsoft.github.io/cat-agent-skills/#copilot-studio-test-planner
source_license: MIT
converted_from: CAT Agent Skills
converted_on: 2026-08-05
---

# Copilot Studio Test Planner

> **Converted skill.** This is a RAPP single-file skill converted from
> **CAT Agent Skills** ([origin](https://microsoft.github.io/cat-agent-skills/#copilot-studio-test-planner)), redistributed under
> **MIT** with attribution. Original author: Elliot Margot.
> Upstream license text: https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/LICENSE
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

Reads an exported Copilot Studio agent and generates a graded, runnable test suite (happy-path, paraphrase, disambiguation, negative, knowledge-grounding, multilingual, and safety cases) plus a regression set, ready to run in the free Copilot Studio test panel.

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

Copilot Studio Test Planner reads an exported Copilot Studio agent (solution ZIP, topic YAML, or pasted definition) and generates a full, graded test plan: happy-path, paraphrase, disambiguation, slot-filling, negative, knowledge-grounding, multilingual, and safety cases, plus a regression subset. It emits a coverage summary, a test matrix with expected topics or tools, and step-by-step instructions to run the suite in the free Copilot Studio test panel. It produces tests only and never modifies your tenant.

> **Cowork plugin.** This is a Microsoft 365 Copilot **Cowork** app package (a `.zip` bundling the skills and connectors below). It installs on Cowork only.

## Skills in this plugin

- **copilot-studio-test-planner** — Generates a full test plan and eval set for a Microsoft Copilot Studio agent.
Use when the user asks to "create a test plan for my Copilot Studio agent",
"generate test cases for an agent", "build an eval set", "write regression
tests for my agent", "how do I test my agent", or shares an exported agent
definition, topic YAML, or solution and wants tests to run before shipping.

## Install

1. Download the plugin package (the `.zip` on this page).
2. Upload it to your tenant via **M365 admin center › Manage apps › Upload custom app**, or sideload it for testing with the [Microsoft 365 Agents Toolkit CLI](https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/microsoft-365-agents-toolkit-cli) (`atk install --file-path <zip> --scope Personal`).
3. Open **Cowork › Sources & Skills › Plugins** and enable it from the **Discover** section.

See [Build plugins for Copilot Cowork](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development) for details.

---

*Converted for the AIBAST Agents Library from CAT Agent Skills.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
