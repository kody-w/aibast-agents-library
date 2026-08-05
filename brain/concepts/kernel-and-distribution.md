---
title: Kernel and distribution
tags: [ms-rapp, governance, concept]
summary: The Linux model — a fast upstream kernel, a deliberate downstream build.
updated: 2026-08-05
---

# Kernel and distribution

The pattern is the one that has kept Linux healthy: an open-source **kernel**
that moves fast, and a **distribution** that adopts deliberately.

- The kernel develops on a release train (canary → nightly → alpha → beta →
  stable) and ratifies RAPP/1 protocol revisions.
- ms-rapp ships only what is pinned, gated, and verified.

**RAPP/1 is the standard both sides implement.** Neither renames it; the shared
standard is what keeps them interoperable while their cadences differ.

Changes flow **down** through sync pull requests and **up** as issues and pull
requests against the kernel — never as a downstream patch that quietly
diverges. See [[how-to/sync-from-the-kernel]] and
[[decisions/why-extensions-are-discovered]] for the mechanism that keeps a
sync from ever colliding with work originated here.
