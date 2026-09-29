# AIBAST Frontier: the way forward

| | |
|---|---|
| **Status** | Decision record and plan, adopted 29 September 2026 |
| **Owner** | Library maintainers |
| **Review** | Quarterly, with the impact scorecard |
| **Change rule** | Decisions below change only through a reviewed pull request that edits this file |

> *AIBAST Frontier is an open-source learning library published in the Microsoft GitHub organization. It is not a
> Microsoft product, is not part of the Microsoft Frontier program, and does not confer Microsoft AI Cloud Partner
> Program badges or designations.*

## Why the library exists

**Mission.** Turn a customer's idea into a working, verified, Microsoft-native agent faster than the published
path, and keep every scenario evergreen as the platform changes.

**Descriptor.** AIBAST Frontier is an early, experimental learning lane: learn it now, prove it works, land it
native.

**The problem it answers.** Agents are spreading fast, but value isn't keeping pace:

- Active agents in the Microsoft 365 ecosystem grew 15x year over year ([Microsoft Work Trend Index 2026](https://www.microsoft.com/en-us/worklab/work-trend-index/agents-human-agency-and-the-opportunity-for-every-organization)).
- 60% of companies report "hardly any material value" from AI ([BCG, Oct 2025](https://www.bcg.com/publications/2025/are-you-generating-value-from-ai-the-widening-gap)).
- Agent deployment is "in the single digits across nearly all business functions" ([Stanford AI Index 2026](https://hai.stanford.edu/ai-index/2026-ai-index-report/economy)).
- Agents still fail "roughly 1 in 3 attempts on structured benchmarks" ([Stanford AI Index 2026](https://hai.stanford.edu/ai-index/2026-ai-index-report)).
- The skills gap is "the biggest barrier to integration" ([Deloitte, Jan 2026](https://www.deloitte.com/us/en/what-we-do/capabilities/applied-artificial-intelligence/content/state-of-ai-in-the-enterprise.html)).
- 66% of people rely on AI output without evaluating its accuracy ([KPMG, 2025](https://kpmg.com/xx/en/our-insights/ai-and-technology/trust-attitudes-and-use-of-ai.html)).
- Training raised chatbot take-up from 47% to 83%, with "no significant impact on earnings" ([University of Chicago BFI, 2025](https://bfi.uchicago.edu/wp-content/uploads/2025/04/BFI_WP_2025-56-1.pdf)).

Guidance also goes stale. Copilot Studio now has three harnesses: topics run on the standard harness, skills on the
GitHub Copilot harness ([Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-copilot-studio/harnesses-overview)).

**Alignment.** Microsoft describes Frontier Transformation as "the shift from AI pilots to AI embedded as a
repeatable, governed operating capability"
([Microsoft partner blog, Jul 2026](https://partner.microsoft.com/en-us/blog/article/whats-new-for-partners-2026-issue-3)).
This library turns that into practice. Experimentation stays inside the learning lane, and every solution lands as
a governed, Microsoft-native agent.

## Binding decisions

| # | Decision | What it means in practice |
|---|---|---|
| D1 | **Name and label: AIBAST Frontier (experimental)** | Always the full name. Never a bare "Frontier" label, never "(Frontier)" after a display name, never paired with Microsoft program terms (early access, preview, opt-in, release, program, partner, badge, designation, certified, accelerate, suite, tuning, engineer). The disclaimer above appears on every selling surface. Brand and legal review happens before external events |
| D2 | **Sell frontier benefits, not technology** | Selling surfaces talk about learning now, proof and native landing. Technical documentation (the production guide, glossary, patterns, contributor guides) keeps full engine detail for builders and AI assistants. Selling surfaces name the engine once, as a pointer |
| D3 | **A learning lane, not a development platform** | The frontier lane is for learning, teaching and prototyping. It never competes with Microsoft's pro-code stack or runtimes |
| D4 | **Two lanes for every solution** | **AIBAST Frontier (experimental):** one portable agent file you can learn, teach and change immediately. **Runbook lane:** a manual Copilot Studio build that needs no Python or local tooling. **Easy mode** is the assisted middle path. Each runbook shows both lanes side by side, with repository counts |
| D5 | **Microsoft-native out** | Every agent is a Copilot Studio agent on the GitHub Copilot harness with native skills: each operation in the portable file maps to one skill. Production hosting, identity, channels and governance belong to Microsoft services and the customer |
| D6 | **Private tooling in, native artifacts out** | Maintainers may use private tools to build and verify faster. The library never depends on, links to or names personal tools or accounts |
| D7 | **Evergreen aggregation** | Other agent libraries, including outdated ones, are **inputs**. We ingest a scenario at a pinned commit, re-land it as a current, verified agent with a workshop and runbook, and credit the source |
| D8 | **The AI Agent Runbooks structure, generated and enforced by tests** | `00-overview`, `01-solutions`, `02-patterns` and `03-references` are generated from the library's sources and checked in CI. Solution packages are never moved |
| D9 | **Impact is measured on the Frontier Clock** | Time from the customer's idea to a deployed agent, against the published runbook estimates, at three tiers with identical exit criteria. The headline is the production speedup from opt-in customer engagements, n ≥ 3 |
| D10 | **Measured, not claimed** | Qualitative business claims only. Synthetic data is labeled synthetic. External figures need a primary source. Days are never converted into cost or percentages |
| D11 | **Distribute through Microsoft's channels** | Feed verified editions into Microsoft galleries, agent libraries and skills catalogs. Never add another copy of templates Microsoft already publishes |
| D12 | **Hand off to native** | When Microsoft ships a native equivalent (evaluation, batch testing, authoring), adopt it, re-verify, and retire ours |
| D13 | **The staging ring, synced first** | Nothing enters staging until the fork's `main` equals Microsoft `main` and staging contains it. Every change is compared against the Microsoft baseline, and a human opens and merges each promotion |
| D14 | **Good neighbor upstream** | Defects found in AI Agent Runbooks are contributed back upstream, after the corresponding AIBAST work lands |
| D15 | **Workshops need no local install** | Every workshop can be completed with GitHub Copilot and Copilot Studio alone, and GitHub Copilot is the default engine. The local Brainstem runtime is an optional track that learners choose in Workshop settings; it is never a required step |

## How the library stays relevant

1. **Working, importable agents with evidence.** Not documents: agents you can import, each with dated evidence
   and locked acceptance cases.
2. **Evergreen, whatever ships next.** Each new Microsoft capability becomes the next thing we land natively and
   teach. The platform moving forward is the point, not a threat.
3. **Proven on the clock.** Speed is measured against Microsoft's own published baseline, with honest, pre-registered
   rules.
4. **Part of the ecosystem.** We use the AI Agent Runbooks structure, contribute upstream, distribute through
   Microsoft channels, and link to Microsoft's own learning ([Agent Academy](https://microsoft.github.io/agent-academy/)).

## The Frontier Cycle

| Step | What happens | Output |
|---|---|---|
| 1. Explore | Build a working agent for a real industry problem in the experimental lane, with synthetic data | A frontier prototype |
| 2. Prove | Persona prompts, locked cases, captured transcripts, CI | Evidence |
| 3. Land native | A GitHub Copilot harness agent with native skills; a Draft replay passes | An importable Copilot Studio agent |
| 4. Teach | Workshop, manual tutorial, runbook, course | People who can do it themselves |
| 5. Hand off | Adopt Microsoft's native primitive when it ships; retire ours | Nothing maintained twice |

## The Frontier Clock

**Baseline.** Nine AI Agent Runbooks scenarios publish an "Estimated effort". Most fall within 4–10 weeks; for
example, "4–6 weeks end to end, of which the agent build is a few days" (Employee Self-Service).

| Tier | Exit criterion, identical for the runbook path and ours | Role |
|---|---|---|
| T1 Prototype | A working agent answers the scenario's representative prompts end to end on representative data | Leading indicator |
| T2 Verified Draft | Built on the Microsoft target platform; passes an agreed acceptance set that includes the source's boundary tests | Leading indicator |
| T3 Production | Real users in a customer tenant, with real data, identity, connectors and compliance sign-off | **Headline**, measured in opt-in customer engagements only |

**Rules**

- Same start event and exit criteria on both sides, compared against the runbook's best case.
- The acceptance set is frozen before T1, and pairings are fixed at the start.
- Every timestamp needs evidence. A headline needs n ≥ 3.
- Customer-owned stages are never claimed without a measured T3.

**Storage.** Results live in a tested ledger, `state/frontier_clock.json`, where "nothing goes in as a forecast".

**Status.** Nothing is measured yet. The clock is a method until the first trials report.

## The evergreen engine

| Stage | Output |
|---|---|
| Ingest | The source pinned by commit; license, notices, assets, published estimate and tests recorded |
| Normalize | The source's own tests frozen as the acceptance set; the trial pre-registered |
| Explore → Prove → Land native → Teach | The existing library pipeline (agent, locked cases, transcripts, Copilot Studio package, workshop, runbook) |
| Publish | Staging ring, human promotion, cross-link to the source |
| Re-verify | Replays at least every 60 days; earlier evidence archived |
| Hand off | Retired in favor of the native equivalent, with a handoff record |

**Waves**

- **Wave 1:** the three Clock Trials (Email Triage, Meeting Intelligence, Contract & Legal).
- **Wave 2:** the most outdated runbook scenarios.

**Licensing is per asset:**

- MIT sources are re-landed with their notices.
- Content whose terms bar adaptation is linked, not copied.
- Anything of unclear provenance is resolved with its owners first.

## Where we stand (29 September 2026)

| Assets | Impact measurement |
|---|---|
| 51 solutions across 12 industries; 51 of 51 importable Copilot Studio solutions | Workshop completions 0; verified cohorts 0 (`state/metrics.json`, 14 Sep) |
| 51 of 51 on the GitHub Copilot harness with native skills (229 skills) | Manual builds verified live: 1 of 51 (`state/manual_workshop_pilot_2026-09-12.json`) |
| A guided workshop and manual tutorial per solution; 51 courses, 6 paths | The metrics pipeline has been failing since 15 Sep; a fix is in review |
| Dated evidence per solution; automated tests in CI; human-reviewed releases | Evidence freshness expires on 7 Oct (every replay dates from 8 Aug) |

**We count assets today, not impact. The roadmap fixes that first.**

## Roadmap (Microsoft FY27)

| Quarter | Outcomes |
|---|---|
| **Now (P0)** | Restore measurement: a Discussion sync failure can never skip collection, and the dark period is backfilled. Re-verify the replays before 7 Oct, or publish honest "Verified on" dates |
| **FY27 Q2 (Oct–Dec)** | Runbook structure promoted, with the two lanes and naming rules. Brand and legal review before 17 Nov. Clock ledger and test by 31 Oct. Three Clock Trials pre-registered by 15 Nov, with first T1 and T2 results by 31 Dec. Freshness badges and a weekly freshness job. Engine internals and personal environment labels removed from agent knowledge. Honest, CI-adjusted metrics and per-solution downloads. Runbooks for all 51 solutions. At least 2 upstream fixes merged |
| **FY27 Q3 (Jan–Mar)** | Verified editions distributed through Microsoft channels. At least 5 runbook scenarios linking back. n ≥ 3 T1 and T2 results, including a non-author trial. At least 3 opt-in customer engagements pre-registered. Handoff to native evaluation and batch testing. Import-first vs docs-first cohort study designed. Course naming aligned with Microsoft learning |
| **FY27 Q4 (Apr–Jun)** | **T3 production speedup results (n ≥ 3), or "not yet measured" stated.** Evergreen wave 2. A quarterly review and handoff record |

## Scorecard

| Indicator | Green | Red: grounds to reprioritize |
|---|---|---|
| **T3 production speedup** (headline) | n ≥ 3 by 30 Jun 2027, with the median earlier than the paired baseline | Not earlier at n ≥ 3 |
| T1 and T2 speedups | Earlier at n ≥ 3 | Not earlier at n ≥ 3 |
| Measurement uptime | No gap of 3 days or more | Any gap of 7 days or more |
| Freshness | 51 of 51 verified within 60 days | Fewer than 40 of 51 at quarter end |
| Verified practical completions | Growing each quarter | 5 or fewer in two consecutive quarters |
| Distribution through Microsoft channels | Upstream fixes merged; runbook scenarios linking back | None by 31 Mar 2027 |

**The report never claims:**

- revenue attributed to the library;
- days converted into cost or percentages;
- synthetic results presented as customer results;
- estimates presented as measurements;
- "users" derived from clones or views.

## Guardrails

- No one needs anything beyond Microsoft services to use an agent from this library.
- Experimentation stays in the learning lane. Production readiness is claimed only for Microsoft-native agents,
  verified on the clock.
- No proprietary format where a Microsoft-native one exists.
- No dependency on personal tools or accounts in Microsoft-facing assets.
- Link to Microsoft guidance, contribute to it and distribute through it. Never duplicate it.

## Risks

| Risk | Response |
|---|---|
| The clock shows no speedup | Report it. The method is the asset, and the result redirects investment honestly |
| Messaging tension around "experimental" | The label applies to the learning lane only; every solution lands native and is judged on the production clock |
| The name is reserved by Brand or legal | Review before external events; a fallback name is ready |
| Measurement goes dark or is inflated | Resilient pipeline, CI-adjusted counts, outage alerts |
| Maintainer bandwidth | Weekly freshness rotation; native tools replace our own |
| Provenance of ingested content | Pinned commits, per-asset reuse classes, retained notices |

## What we need from leadership

1. A sponsor and a named library owner.
2. Brand and legal review of the name and disclaimer before 17 November 2026.
3. Capacity for the freshness rotation and the Clock Trials.
4. A field program for at least 3 opt-in customer engagements.
5. Agreement with the AI Agent Runbooks maintainers on cross-links.
6. Repository administration for measurement fixes.

## Open decisions

- Whether T3-only tests (those that need real data) count toward the T3 exit. **Proposed: yes**, disclosed per
  engagement.
- A fallback name if review reserves "Frontier". **Ranked options exist.**
- The disclaimer's subject. The descriptor calls AIBAST Frontier a "learning lane", while the mandated disclaimer calls
  it "an open-source learning library". **Proposed:** "The AIBAST Agents Library, including AIBAST Frontier
  (experimental), is an open-source learning library…", decided in the same Brand/CELA review as the name.
- A home for the Clock Trials' public results. **Proposed:** the ledger plus the quarterly report.

---

*Technical documentation: AIBAST Frontier runs on RAPP. See the [production guide](rapp-guide.html),
[RELEASE-PROCESS.md](RELEASE-PROCESS.md) and [ROADMAP.md](ROADMAP.md).*
