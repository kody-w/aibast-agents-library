---
title: Publish an agent
tags: [how-to, publishing]
summary: Your GitHub username is your publisher handle. One file, one pull request.
updated: 2026-08-05
---

# Publish an agent

1. **Claim your track.** Open the publisher application. Your GitHub username
   is your handle; your work lives under `agents/@<your-username>/`.
2. **Write one file.** A single `.py` extending `BasicAgent` with a
   `__manifest__`, or a single `skill.md`. No sidecar files.
3. **Keep secrets out.** Configuration goes through `requires_env`. The file
   itself must be safe to read in public — a gate enforces this.
4. **Open a pull request.** CI validates the manifest and runs the contract
   tests against your agent.

On merge the registry rebuilds, your agent appears in the gallery and the
[[how-to/use-the-static-api]] endpoints, and a rating thread is seeded for it.

Then: [[how-to/earn-a-badge]].
