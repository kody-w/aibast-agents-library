# Skill Aggregation — outside skills into the RAPP ecosystem

The ecosystem's problem is not a shortage of skill libraries — it is that
every group builds its own, each with a different shape, no shared quality
bar, and no way to tell which entries are good. The AIBAST Agents Library
aggregates them the way a front page aggregates the web: **index everything,
gate for quality, and surface the best entry for each use case.**

## The pipeline

```
outside repos ──1 index──▶ state/aggregated.json ──2 convert──▶ skill.md / agent.py
                                                        │
                                          3 quality gates (verdicts in
                                             state/gate_verdicts.json)
                                                        │
                                     4 front-page ranking on the gallery
                                                        │
                                5 graduate: publisher PR into agents/@…/
```

### 1. Index (shipping now)

`scripts/crawl_skills.py` reads `sources.json` and runs daily via
`.github/workflows/metrics.yml`. It **indexes, it does not mirror**: catalog
metadata only (name, description, tags, author, origin link, and any counts
the source itself publishes as `source_signal`). Every entry is normalized to
`@namespace/slug` so the Discussions rating machinery and metrics dashboard
work on aggregated entries with no special case. Adding a source is a config
edit — one entry in `sources.json` plus (if the shape is new) one adapter
function.

First source: **CAT Agent Skills** (`microsoft/cat-agent-skills`), indexed
from its public `skills.json`.

License posture: `license_verified: false` means treat the origin as
all-rights-reserved — index and link only; conversion requires a verified
compatible license or the author's permission, recorded in the conversion PR.

### 2. Convert (next phase; manual today, assisted tomorrow)

A raw skill becomes RAPP-compliant in whichever format the converter (or the
original author) prefers — **both options are first-class**:

- **`agent.py`** — single-file `BasicAgent` subclass with `__manifest__`,
  runnable on the brainstem as-is.
- **`skill.md`** — single file with YAML frontmatter and the **RAPP
  deterministic layer embedded**: explicit numbered steps, declared inputs
  and outputs, pause points, and a verification section, so two runs of the
  same skill do the same thing.

Conversion is traceable: the manifest carries `source_ref`
(`@cat-agent-skills/<slug>`), `source_url`, and `converted_from` attribution.
The aggregation crawler links the converted entry back to its indexed record
so the gallery shows one card, best version on top.

### 3. Quality gates (next phase — the enterprise tomato meter)

RAR's critic pattern, refocused for enterprise use. Three gates, each scored
independently by a model panel plus deterministic checks, verdicts pinned to
the SHA-256 of the exact file reviewed and re-earned on every republish:

| Gate | Question | Deterministic floor |
|------|----------|--------------------|
| **Quality** | Is the code/skill sound — valid manifest, no secrets, error handling, single-file discipline? | `build_registry.py` validation + secret scan must pass |
| **Usability** | Can a stranger run it — env vars declared, instructions complete, works on a clean brainstem? | manifest `requires_env` complete; smoke-load on the brainstem |
| **Effectiveness** | Does it actually serve the stated use case better than doing nothing — and better than the duplicates? | demo/eval transcript attached to the verdict |

Verdicts land in `state/gate_verdicts.json` keyed by ref:

```json
{"verdicts": {"@cat-agent-skills/accessibility_pass": {
  "converted": true, "sha256": "…",
  "gates": {"quality": {"passed": true, "score": 82},
             "usability": {"passed": true, "score": 74},
             "effectiveness": {"passed": false, "score": 55}}}}}
```

### 4. Surface the best (shipping now, sharpens as gates land)

Several sources will solve the same use case. `front_page_score` ranks them:
raw source signal (downloads, ratings, featured) contributes at most
hundreds; **conversion contributes 500 and each passed gate 1,000** — so a
gated, converted skill always outranks a merely popular raw one. The gallery
shows the winner prominently and the rest behind it, with each entry linking
to its origin.

### 5. Graduate

A converted, gate-passed skill enters the library through the normal
[publisher flow](PUBLISHING.md) — a PR under the converter's
`@<github-username>/` track (or an `@aibast-agents-library/` community PR),
carrying attribution and the license record. From that moment it is a native
library citizen: registry entry, Discussions rating thread, metrics
leaderboards, and one-file install onto any brainstem.
