# FY27 priority agents — intake record

What was added to the library from the FY27 cross-customer scenario analysis,
what was deliberately left out, and the evidence that the additions sit at the
same level as the agents already here.

This is also the first end-to-end test of adding new material: manifest →
registry → storyboard → one-pager → architecture → static API → film. Every
defect that surfaced in the pipeline is recorded below rather than quietly
fixed, because the next intake will hit the same ones.

---

## 1. The boundary that governed everything

**The source analysis names real organisations against every scenario. None of
them are in this repository, in any form.**

Not in a manifest, not in a docstring, not in provenance, not in a comment, not
in a film. What transferred is the *industry* and the *shape of the work*. Every
entity in the synthetic data is invented.

This is enforced, not asserted: `tests/check_no_customer_names.py` sweeps every
tracked and untracked text file against the organisation list and fails the
build on a single hit.

```
$ python3 tests/check_no_customer_names.py
[pii] scanned 1238 text files against 14 names
[pii] PASS — no customer name from an ingested analysis is in the repo
```

Two false positives shaped how it matches, and both are worth knowing about:
one three-letter name matched inside hex digests in vendored JavaScript, and
another matched as a substring of an invented account name in an existing
agent's synthetic data. The gate is therefore case-sensitive and word-bounded,
and skips binaries and `vendor/`. A gate that cries wolf is a gate everyone
learns to ignore.

It also caught this document: an earlier draft named those two organisations
while explaining their false positives, and the gate failed the build. The
denylist is the one place a name may appear.

## 2. Consolidation: 61 → 14 → 7

The source report had already clustered 61 customer-named agent variants into 14
priority scenarios. Adding all 14 would have put five near-identical sellers'
agents into a catalog that already had five, so each was scored against the
existing 105 by token overlap on name and description.

**Six were dropped as already covered:**

| FY27 scenario | Covered by |
|---|---|
| Seller / Account Executive Productivity | `account-intelligence`, `deal-progression`, `cross-selling`, `pipeline-velocity`, `account-messaging` |
| Public Sector Citizen / Civil Service | `citizen-service-request`, `ai-customer-assistant` |
| Customer Service / Case Intelligence (D365) | `ai-customer-assistant`, `support-ticket-resolution`, `customer-escalations` — highest overlap measured (0.14) |
| Sales Manager / Marketing Ops Analytics | `pipeline-velocity`, `deal-progression` |
| Procurement / Tender / Vendor-Spend | `procurement-agent` (0.12); the public-tender angle folds into multi-entity finance |
| Industry Compliance & Risk Monitoring | `supplier-risk-monitoring`, `fs-regulatory-compliance` |

**Two were merged into one:** *R&D / Scientific Discovery* and *Requirements &
Innovation Authoring* are the same job — find what has already been tried, then
write it up in the structure the review board expects. Shipping both would have
been exactly the duplication this exercise was meant to avoid.

**Seven were added:**

| Agent | Category | Job |
|---|---|---|
| `regulated-document-drafting` | slg_government | Legislative text, legal opinions, tender packs — drafted against the regime's taxonomy and tone |
| `asset-reliability-standards` | manufacturing | Asset history read against the engineering standard that governs it |
| `multi-entity-finance-ops` | financial_services | Close across entities, currencies and ledgers; reconciles intercompany |
| `frontline-coaching` | human_resources | Observed interactions → a coaching record a manager can run a 1:1 from |
| `editorial-market-intelligence` | general | Story and market signals across a watched source set, corroborated vs single-sourced |
| `rd-discovery-requirements` | professional_services | Prior art, then the requirement in the house structure |
| `clinical-documentation-ring` | healthcare | Clinical record assembled for review, each entry traced to its source |

Registry: **105 → 112 agents.**

### Thin evidence, named rather than hidden

`clinical-documentation-ring` derives from a single customer in the source
analysis. It is included because the scenario is coherent on its own terms, but
it has the weakest demand signal of the seven and should be the first cut if the
list needs shortening.

## 3. Quality evidence

Every agent went through the same pipeline as the existing library, and every
film is gated by the same tool.

```
$ python3 .claude/skills/showcase-film/agent.py gate <film>
regulated-document-drafting      PASS  160.7s
asset-reliability-standards      PASS  164.2s
multi-entity-finance-ops         PASS  159.4s
frontline-coaching               PASS  161.5s
editorial-market-intelligence    PASS  160.1s
rd-discovery-requirements        PASS  164.2s
clinical-documentation-ring      PASS  163.2s
```

Each film: 1920x1080, stereo, peak −0.4 to −0.5 dB, speech-shaped dynamics,
narrated by `en-US-AndrewMultilingualNeural` via Azure, longest unchanged frame
under 4.6s, closes on the logo, demo act 46–50% of runtime.

Corpus grammar for comparison, re-measured over 19 films at 1Hz by border
signature — the order `logo → b-roll → card → demo → card → logo` holds in 18 of
19 (the exception is a multi-scenario suite film with four demo blocks):

| segment | measured median | previously reported | |
|---|---|---|---|
| logo in | 3s | 3 | reproduced |
| b-roll | 25s | 23 | reproduced |
| card (open) | 21s | 23 | reproduced |
| demo | 90s | 81 | **not reproduced** (+9s) |
| card (close) | 16s | 22 | **not reproduced** (−6s) |
| logo out | 3s | 3 | reproduced |
| total | 159.6s | 155 | **not reproduced** (+4.6s) |

Frames were read at ~1Hz across the whole timeline, not just gated. The gate
cannot see pixels.

## 4. Defects the intake surfaced

Five real bugs, all in the shared pipeline rather than in the new agents, which
is the point of running a new intake end to end.

1. **`common.py` read a font key that no longer exists.** It wanted
   `family_candidates`; `brand.json` provides `family_file` +
   `family_fallbacks`. Every card render died on `KeyError`. Both shapes are now
   accepted.
2. **`_find_face` joined absolute paths onto font directories**, producing
   `.../fonts//System/Library/Fonts/...`, which never exists — so every face
   silently fell back to PIL's default bitmap font.
3. **SSML was built from raw text.** A bare `&` in *"asset reliability &
   standards"* makes the document malformed, and Azure returns HTTP 400 for that
   slot only — which reads exactly like an expired token and is not one. Text is
   now XML-escaped.
4. **Narration caches per slot but does not invalidate on engine change.** A run
   reported `engine: azure` while `voice.json` recorded all nine slots as `say`.
   The workaround is to clear `work/vo` when switching engines. **Still open** —
   the cache key should include the engine.
5. **Answers taller than the pane were clipped under the composer.** The
   renderer bottom-anchored but clamped at the top, so the *oldest* content
   stayed pinned and the newest was cut mid-sentence. It now scrolls: the newest
   line stays against the composer and the oldest leaves the top, which is what
   the product does.

### Two content changes the films forced

The demo act has to carry 45%+ of the runtime and was landing at 42–44%. The
cause was not pacing: the demo carried 52% of the script's words against the
grammar's 63.7%. Fixed at the source rather than by stretching holds —

- the walkthrough narration budget went from 78s to 100s, buying the ~207 demo
  words the grammar asks for;
- three sections were added to every agent answer — **What I did not check**,
  **What this needs from you**, **What would change my answer**.

Those sections are not padding. They are the parts a briefing is weaker without,
and the narration now describes them because they are on screen.

## 5. Known gaps

- **No b-roll bucket exists for `human_resources` or `general`.** Those two
  films use `cross_industry` and carry a `broll_note` saying so. Source footage
  for those domains before either is shown externally.
- **`film/projects/` contains ten projects built from the raw, un-consolidated
  FY27 names.** Four are scenarios deliberately dropped as already covered
  (`seller-account-executive-productivity`,
  `sales-manager-marketing-ops-analytics`, `public-sector-citizen-civil-service`,
  `procurement-tender-vendor-spend`); two are the pair that was merged
  (`rd-scientific-discovery-and-innovation`,
  `requirements-and-innovation-authoring`); four duplicate agents that WERE added
  under consolidated names (`frontline-coaching-1-1-documentation`,
  `healthcare-clinical-documentation-and-data-ring`,
  `industrial-asset-reliability-and-engineering-standards`,
  `industry-specific-finance-operations`). They predate the consolidation and are
  precisely the duplication this intake set out to avoid. **Left in place rather
  than deleted** — removing another session's output is not a call to make
  unasked — but they should be reconciled before anything ships.
- **A skill and its agent disagree.** `SKILL.md` §4 says *"A film with a lesser
  voice ships; a film with no voice does not."* `agent.py gate` hard-fails
  `say`-narrated films as *"robotic and NOT shippable"*. The agent is the
  deterministic layer and wins; `SKILL.md` needs correcting.
- **`FILM_SPEECH_RESOURCE_ID` is named in neither `SKILL.md` nor
  `agent.py facts`,** only in `narrate.py`. Without it every build silently
  falls back to the local voice and then fails the gate.

## 6. Reproducing this

```bash
python3 build_registry.py
python3 scripts/build_walkthrough.py
python3 scripts/build_architecture.py
python3 scripts/build_api.py
python3 tests/check_no_customer_names.py

export FILM_SPEECH_RESOURCE_ID=<speech resource id>
python3 film/kit/compose.py --walkthrough <slug> --bucket <bucket> --batch fy27
python3 film/kit/make.py --project <slug> --engine azure
python3 .claude/skills/showcase-film/agent.py gate film/projects/<slug>/dist/<slug>.mp4
```

Storyboards carry `approval.required_before_render: true`. A rendered film is a
draft until a human has read the script.
