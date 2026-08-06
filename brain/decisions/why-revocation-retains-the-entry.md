---
title: Why revocation retains the entry
tags: [decision, certification]
summary: A 404 cannot be told apart from an outage. An explicit "no" can.
updated: 2026-08-05
---

# Why revocation retains the entry

**Decision.** When a badge is withdrawn, the roster entry is kept with
`status: revoked`. It is never deleted.

**Why.** The obvious implementation deletes the record, so the endpoint 404s.
But a 404 is indistinguishable from a CDN miss, a rename, or an outage. A
verification system whose *"no"* cannot be told apart from its *"unreachable"*
does not verify anything — every consumer has to guess, and consumers guess
generously.

Retaining the entry makes the negative answer explicit and cacheable. A badge
already embedded in someone's README flips to *not certified* on the next
build, with no dead image and no action required from them.

**Consequence.** The roster only grows. That is the intended cost: an audit
trail you cannot quietly edit.

Specification: `ms-rapp-badge/1.0` §6. See [[how-to/earn-a-badge]].
