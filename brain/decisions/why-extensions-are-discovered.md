---
title: Why extensions are discovered
tags: [decision, extension, governance]
summary: If the core knows an extension's name, a kernel sync eventually fights it.
updated: 2026-08-05
---

# Why extensions are discovered

**Decision.** The core build discovers `rapp/ext/*/build.py` and names no
extension anywhere — not in code, not in its docstring.

**Why.** A distribution that adds features by editing shared files slowly
becomes a fork: each kernel sync turns into a merge negotiation, the cost of
staying current climbs, and eventually staying current stops happening. The
fix is not "edit carefully" — care does not survive a busy week. The fix is
making the intersection **empty by construction**.

So an extension owns its own directory, its own output namespace, and its own
version line. A kernel sync replaces kernel files; those sets do not overlap.

The pattern follows two rules the kernel already states: capability arrives at
an established extension point, and unrecognized input is ignored rather than
refused.

**How we know it holds.** A gate moves every extension aside, rebuilds, and
requires the core endpoints to be byte-identical — plus proves a broken
extension cannot fail the build and cannot write outside its namespace.

See [[concepts/extensions]].
