# Pricing and Scoring Rules

> SYNTHETIC — DEMO DATA. Every price, discount rule, and scoring weight in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real product catalog, deal desk rules, and win/loss model (see the
> README's production section).

## Product catalog

| Component | Category | List Price | Margin Floor |
|-----------|----------|------------|--------------|
| Platform Core License | Software | $420,000 | 38% |
| Integration Suite | Software | $180,000 | 40% |
| Analytics & Reporting | Software | $80,000 | 45% |
| Implementation Services | Services | $380,000 | 35% |
| Training Program | Services | $120,000 | 50% |
| 3-Year Premium Support | Support | $180,000 | 55% |

Component cost is derived, not quoted: `cost = int(list_price * (1 - margin_floor))`.

## Solution configurations by industry

| Industry | Components |
|----------|------------|
| Healthcare | Platform Core License, Integration Suite, Analytics & Reporting, Implementation Services, Training Program, 3-Year Premium Support |
| Technology | Platform Core License, Integration Suite, Implementation Services, Training Program, 3-Year Premium Support |
| Financial Services | Platform Core License, Integration Suite, Analytics & Reporting, Implementation Services, Training Program, 3-Year Premium Support |

Any industry not listed falls back to the Technology configuration.

## Discount rules

| Category | Base Discount | Volume Threshold | Volume Bonus | Maximum |
|----------|---------------|------------------|--------------|---------|
| Software | 8% | $600,000 | +3% | 15% |
| Services | 10% | $400,000 | +4% | 18% |
| Support | 25% | $150,000 | +5% | 35% |

Applied per line: `discount = min(base + (volume_bonus if list_price >=
volume_threshold else 0), maximum)`, then `proposed = int(list_price * (1 -
discount))`. On the current catalog only 3-Year Premium Support clears its
threshold, so it prices at 30%.

Budget guard: if the sum of proposed prices exceeds the RFP's budget ceiling,
every line is scaled by `ceiling / proposed_total` and margins are recomputed.

Blended margin floor for the deal: **35%**.

## Implementation phases (12 weeks total)

| Phase | Name | Weeks | Activities |
|-------|------|-------|------------|
| 1 | Foundation | 1-4 | Infrastructure assessment, connector deployment, security configuration, core team training |
| 2 | Rollout | 5-10 | Phased facility deployment, workflow integration, staff certification, go-live support |
| 3 | Optimization | 11-12 | Performance tuning, advanced training, success metrics validation, handoff to support |

## Capability fit keyword map

A requirement scores the highest-scoring keyword its text contains
(case-insensitive). Requirements matching nothing score the 75% baseline with
the evidence "Addressed through standard platform capabilities".

| Keyword | Fit Score | Evidence |
|---------|-----------|----------|
| EHR integration | 95% | Native Epic & Cerner connectors, certified |
| HIPAA compliance | 100% | SOC 2 Type II + HIPAA certified |
| 24/7 support | 98% | 24/7/365 with 15-min response SLA |
| 15-min response | 98% | Industry-leading 15-min SLA |
| Implementation under | 90% | 12-week methodology with accelerators |
| staff training | 92% | Role-based curriculum with certification |
| Data migration | 88% | Automated migration toolkit, 50+ connectors |
| Multi-cloud | 91% | AWS + Azure + GCP orchestration layer |
| Zero-downtime | 93% | Blue-green deployment with automated rollback |
| SOC 2 | 100% | SOC 2 Type II audit current |
| managed services | 90% | Dedicated SRE team, 99.99% uptime track record |
| Knowledge transfer | 85% | Structured runbook and shadowing program |
| Real-time transaction | 87% | Sub-30ms processing demonstrated at Atlantic CU |
| PCI-DSS | 100% | PCI-DSS Level 1 certified |
| 99.999% | 88% | 99.99% historical, architecture supports five-nines |
| Phased rollout | 92% | Proven branch-by-branch methodology |
| certification | 90% | LMS-integrated certification tracks |

Overall fit: `round(sum(fit_score * weight) / sum(weight), 1)`.

## Reference relevance scoring

| Condition | Relevance |
|-----------|-----------|
| Reference industry matches RFP industry | 100 |
| Reference industry differs | 30 |
| Contact ready | +10 (capped at 100) |

Sort descending, take the top four.

## Win probability model

| Factor | Maximum | Rule |
|--------|---------|------|
| Capability fit | 30 | `min(30, overall_fit * 0.3)` |
| Pricing strength | 25 | 20 within budget, 10 if over; +5 when budget headroom > $30,000 |
| Reference strength | 20 | `min(20, in-industry references * 7)` |
| Competitive position | 25 | `max(5, 25 - competitors * 7)`; +5 when every shortlisted competitor is slower than our 12-week implementation |

Total: `min(95, max(15, int(sum of factors)))`.

## Pipeline roll-up

The portfolio view re-uses the single-deal computations without re-scoring
anything, then aggregates across every RFP in the pipeline.

| Roll-up figure | Rule |
|----------------|------|
| Win-weighted value, per deal | `int(proposed_total * win_pct / 100)` |
| Win-weighted value, pipeline | Sum of the per-deal weighted values |
| Proposed total | Sum of each deal's proposed total |
| Discount given | `list_total - proposed_total`, and `round((1 - proposed_total / list_total) * 100, 1)` as a percent |
| Blended pipeline margin | `round((proposed_total - cost_total) / proposed_total * 100, 1)` against the same 35% floor |
| Ranking | Win probability descending |

Computed from the three RFPs on file: $3,500,000 stated deal value, $4,000,000
list, $3,253,196 proposed, $746,804 discount given (18.7%), 27.5% blended margin,
$2,696,636 win-weighted. All three deals sit below the 35% margin floor.

There is no historical win/loss record, close date, or quota in this data, so the
roll-up is arithmetic on the win model and never a forecast or a commit number.

## Proposal page count

`page_count = 12 + (requirements * 2) + (references * 2) + (competitors * 3) + 4`
