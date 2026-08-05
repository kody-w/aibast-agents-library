---
title: What ms-rapp is
tags: [ms-rapp, concept]
summary: The enterprise build of RAPP — same protocol, different cadence.
updated: 2026-08-05
---

# What ms-rapp is

RAPP is a platform for building AI agents as **single files**: one `.py` (or
one `skill.md`), a manifest, no framework. An agent dropped into an agents
folder self-registers; there is no build step and no plugin registry.

**ms-rapp** is the build of that platform published from
`microsoft/aibast-agents-library`. It is not a rewrite and not a fork. It
tracks the open-source kernel and pins what it ships — see
[[concepts/kernel-and-distribution]].

What that buys a reader of this repository:

- every agent is legible: open the file, read the whole thing
- every dependency is pinned and hash-verified ([[concepts/the-corpus]])
- every claim the docs make is checked by a gate, not asserted

What it is not: a supported Microsoft product. It is a public preview provided
as is — see the repository disclaimer before deploying anything.

Next: [[concepts/the-three-tiers]].
