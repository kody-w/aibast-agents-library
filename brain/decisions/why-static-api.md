---
title: Why a static API
tags: [decision, api]
summary: The failure mode of a documentation API is downtime. Static files have none.
updated: 2026-08-05
---

# Why a static API

**Decision.** Serve every machine-readable surface as static JSON generated
into the repository, rather than running a service.

**Why.** The consumers are installers, agents, dashboards, and READMEs — things
that must work on someone else's schedule, years from now, without anyone
paying for uptime. A service adds a dependency whose most likely failure is
being switched off.

Static files inherit the CDN, are CORS-open, cost nothing, and can be pinned to
an immutable commit. The repository's history is the audit log.

**What it costs.** Freshness is build-cadence, not real-time; anything needing
live truth must recompute from the sources the index points at. That trade is
acceptable for a catalog and unacceptable for, say, a payments API — which is
why this convention is scoped to catalogs.

Convention: `rapp-static-api/1.0`. See [[how-to/use-the-static-api]].
