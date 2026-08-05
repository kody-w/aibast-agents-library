---
title: The three tiers
tags: [ms-rapp, concept, architecture]
summary: Brainstem, RAPP Cloud, Copilot Studio — each self-contained.
updated: 2026-08-05
---

# The three tiers

The platform layers onto the Microsoft AI stack one tier at a time. Each tier
is self-contained: you can stop at any of them.

| Tier | What it is | Where it runs |
|---|---|---|
| **Brainstem** | The core agent loop: soul, agents, chat | Your machine (or your browser) |
| **RAPP Cloud** | The same agents with persistent memory and Entra auth | Azure Functions |
| **Nervous system** | The agents answering in Teams and M365 Copilot | Copilot Studio |

There is also a **tier zero**: the vBrainstem runs the identical engine in the
browser through Pyodide, so a first look costs nothing to install.

The anatomy metaphor is deliberate — a brainstem keeps you alive, a
hippocampus remembers, a nervous system extends reach. It also maps to the
install order.

Related: [[how-to/publish-an-agent]], [[concepts/kernel-and-distribution]].
