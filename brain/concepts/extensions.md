---
title: Extensions
tags: [ms-rapp, extension, concept]
summary: What this distribution originates, and why it can never block a kernel update.
updated: 2026-08-05
---

# Extensions

Most of `rapp/` is mirrored from the kernel. `rapp/ext/` is the opposite: work
this distribution **originates** because an enterprise need had no kernel
answer.

Today:

- **ms-rapp-badge/1.0** — publicly verifiable achievement badges from static
  files. See [[how-to/earn-a-badge]].
- **ms-rapp-brain/1.0** — this vault. See [[concepts/the-vault]].

Every extension follows one pattern: it lives in a single directory, declares
the output namespaces it may write, is **discovered** rather than registered,
and can be deleted with no edit anywhere else. A gate proves it by removing all
extensions and checking the core endpoints are byte-identical.

Why that matters: [[decisions/why-extensions-are-discovered]].
