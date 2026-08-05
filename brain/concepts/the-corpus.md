---
title: The corpus
tags: [ms-rapp, governance, concept]
summary: Pinned, hash-verified mirrors of the protocol documents.
updated: 2026-08-05
---

# The corpus

`rapp/` holds byte-exact mirrors of the canonical RAPP documents at **pinned
commits**: the RAPP/1 specification, the ecosystem specification, the handbook,
and the companion standards.

Two properties make the mirrors trustworthy rather than decorative:

1. **Every file's provenance is recorded** — upstream repo, pinned commit,
   SHA-256, license — in the mirror manifest.
2. **A check verifies all of it**: that local files still match their hashes,
   that upstream still serves those bytes at the pinned commit, and that the
   kernel's own authority file still cites the revision we pin. If the kernel
   re-pins, the check fails with "pin-bump needed" rather than passing quietly.

A pin never moves on its own. Advancing one is a reviewed pull request.

Related: [[concepts/kernel-and-distribution]], [[concepts/extensions]].
