---
title: Earn a badge
tags: [how-to, certification]
summary: Do the thing, get it approved in public, and it is verifiable by anyone.
updated: 2026-08-05
---

# Earn a badge

Badges record something you actually did. Each one names its criteria, and the
award is approved in a public thread where others can congratulate or contest
it — not in a private ledger.

1. Do the thing — publish an agent ([[how-to/publish-an-agent]]), run the
   brainstem end to end, convert an outside skill, and so on.
2. Open the claim. A maintainer approves it and adds you to the roster.
3. You are now verifiable: anyone can check your username against the API, and
   you get a live badge to put in your own README.

The badge reflects your **current** status, because it reads the endpoint every
time it renders. If an award is withdrawn the badge flips rather than breaking
— [[decisions/why-revocation-retains-the-entry]].

Specification: `ms-rapp-badge/1.0` ([[concepts/extensions]]).
