---
title: Sync from the kernel
tags: [how-to, governance]
summary: How an upstream release arrives, and what must move with it.
updated: 2026-08-05
---

# Sync from the kernel

Kernel content in this repository — the brainstem and the installers — is
**locked**. Its hashes are recorded, and a gate fails on any change, including
an added file.

That is not a prohibition on updating; it is a requirement that updating be
deliberate. A sync pull request must, in one commit:

1. bring the kernel release across,
2. regenerate the lock (the lock moving *is* the record of a sanctioned sync),
3. pass the full gate suite and the corpus check.

Anything else that touches a locked file is a red gate, and a red gate is the
system working: fix it upstream, let it ride down.

Worked example: the brainstem ships a registry browser pointed at the kernel's
own catalog. That is upstream's editorial decision, so it is not patched here.

Related: [[concepts/kernel-and-distribution]], [[concepts/the-corpus]].
