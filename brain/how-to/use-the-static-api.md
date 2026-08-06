---
title: Use the static API
tags: [how-to, api]
summary: Every endpoint is a CDN-cached JSON file. No key, no quota.
updated: 2026-08-05
---

# Use the static API

The whole library is queryable as static JSON under `api/v1/`. There is no
server: the repository *is* the API, so there is nothing to authenticate
against and nothing to rate-limit.

```bash
BASE=https://microsoft.github.io/aibast-agents-library/api/v1
curl -s $BASE/agents.json | jq '.agents[] | select(.category=="healthcare") | .name'
curl -s $BASE/status.json | jq .
```

Endpoints are CORS-open on both GitHub Pages and raw, so a browser page can
call them directly — the API explorer does exactly that, which is why a green
response there is proof rather than documentation.

Pin what you ship: swap `main` for a commit SHA in a raw URL and the response
is immutable forever.

Why it is built this way: [[decisions/why-static-api]].
