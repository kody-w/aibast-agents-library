# AIBAST Agents Library — Static API

The whole library is queryable as a static, CORS-open, CDN-cached JSON API —
no server, no key, no rate-limit anxiety. It conforms to
the `rapp-static-api/1.0` convention: one build
step (`scripts/build_api.py`), schema-tagged documents, versioned endpoints,
stable-write (scheduled rebuilds never commit timestamp noise).

Integrate it into any application with a plain `fetch()`.

## Base URLs

| Host | Base |
|------|------|
| GitHub Pages | `https://microsoft.github.io/aibast-agents-library/api/v1/` |
| Raw (CDN-cached, CORS-open) | `https://raw.githubusercontent.com/microsoft/aibast-agents-library/main/api/v1/` |

## Endpoints

| Endpoint | Contents |
|----------|----------|
| `index.json` | API root — endpoint directory + base URLs |
| `agents.json` | Every agent: manifest summary, `raw_url`, engagement counts |
| `agents/<publisher>/<slug>.json` | One agent in full (manifest + URLs + engagement) — publisher without the `@` |
| `categories.json` | Industries with their agent refs |
| `publishers.json` | Publisher directory |
| `metrics.json` | Latest public metrics snapshot |
| `aggregated.json` | Aggregated outside skills, ranked by `front_page_score` |
| `status.json` | Heartbeat: counts + generated timestamp |
| `badge.json` | [shields.io endpoint](https://shields.io/badges/endpoint-badge) format |
| `../../registry.json` | The full raw registry (`rapp-registry/1.0`) |

## Examples

```bash
BASE=https://microsoft.github.io/aibast-agents-library/api/v1

# list every financial-services agent
curl -s $BASE/agents.json | jq '.agents[] | select(.category=="financial_services") | .name'

# one agent, in full
curl -s $BASE/agents/aibast-agents-library/art-generator.json | jq .manifest

# download an agent file straight into a brainstem
curl -s $(curl -s $BASE/agents.json | jq -r '.agents[0].raw_url') -o my_agent.py

# README badge
# ![agents](https://img.shields.io/endpoint?url=https%3A%2F%2Fmicrosoft.github.io%2Faibast-agents-library%2Fapi%2Fv1%2Fbadge.json)
```

```js
// browser — CORS is open on both hosts
const { agents } = await (await fetch(
  'https://microsoft.github.io/aibast-agents-library/api/v1/agents.json')).json();
```

The [in-browser vBrainstem](../vbrainstem/) is a first-class consumer of this
API: its agent-library panel and one-click installs read these endpoints.
The repository is also the reference for the **ms-rapp/1** distribution —
the pinned RAPP/1 protocol corpus lives in [`rapp/`](../rapp/README.md).

## Freshness

`agents.json`, `categories.json` and `publishers.json` rebuild on every push
that touches an agent; `metrics.json` and `aggregated.json` refresh on the
daily metrics run. Each document carries `schema` and `generated`.
