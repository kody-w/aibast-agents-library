# Opportunity Signals and Scoring Policy

> SYNTHETIC — DEMO DATA. Every signal, client reference, and planning note in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real CRM opportunity pipeline and your firm's published scoring
> policy (see the README's production section).

## Opportunity signals

Five open signals: two high priority, three medium priority. Groups render high
first; within a group, signals keep the order below.

| Client | Signal Type | Priority | Description | Recommended Action |
|---|---|---|---|---|
| Harrison Family Trust (WM-001) | education_funding | high | 529 plan contribution deadline approaching; daughter's college enrollment Fall 2025 | Schedule meeting to review education funding plan |
| Dr. Anita Rao (WM-002) | liquidity_event | high | Practice sale in 2-3 years; begin pre-sale tax and asset protection planning | Engage tax advisor for sale structuring |
| George & Martha Kensington (WM-003) | estate_planning | medium | Estate plan last updated 2019; tax law changes require revision | Coordinate with estate attorney for plan update |
| George & Martha Kensington (WM-003) | rmd_optimization | medium | Client age 74; review Qualified Charitable Distribution strategy | Model QCD scenarios vs standard RMD |
| Tidewater Ventures LLC (WM-004) | reallocation | medium | Portfolio underperforming benchmark; alternative allocation review needed | Prepare alternative manager review presentation |

Every recommended action belongs to the advisor. The agent never performs one.

## Computed figures

| Figure | Formula | Current value |
|---|---|---|
| Total AUM | sum of `aum` across the book | $29,800,000 |
| Average Alpha | sum of `alpha` / client count, rounded to 2dp | 0.7% |
| AUM-Weighted Alpha | sum of (`alpha` * `aum`) / total AUM, 2dp signed | +0.57% |
| Total Alerts | count of all opportunity signals | 5 |

Worked AUM-weighted alpha: (1.1 x 8,500,000 + 1.6 x 3,200,000 + 0.3 x
12,400,000 + -0.2 x 5,700,000) / 29,800,000 = 17,050,000 / 29,800,000 = +0.57%.

## Relationship health ladder

Evaluated in order; the first match wins.

| Order | Condition | Health |
|---|---|---|
| 1 | `alpha >= 1.0` AND `ytd_return > benchmark_return` | Strong |
| 2 | `alpha >= 0` | Satisfactory |
| 3 | otherwise | Attention Needed |

Current classification: WM-001 Strong, WM-002 Strong, WM-003 Satisfactory,
WM-004 Attention Needed.

## Attribution ladder

Evaluated in order; the first match wins. Tests alpha alone — there is no
second YTD-versus-benchmark condition.

| Order | Condition | Attribution |
|---|---|---|
| 1 | `alpha >= 1.0` | Selection + Allocation |
| 2 | `alpha >= 0` | Allocation |
| 3 | otherwise | Underperformance |

Current classification: WM-001 Selection + Allocation, WM-002 Selection +
Allocation, WM-003 Allocation, WM-004 Underperformance.
