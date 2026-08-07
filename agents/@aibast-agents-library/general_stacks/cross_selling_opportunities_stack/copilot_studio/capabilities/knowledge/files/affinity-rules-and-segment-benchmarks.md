# Affinity Rules and Segment Benchmarks

> SYNTHETIC — DEMO DATA. Every affinity score, success rate, and benchmark in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real affinity engine and historical win/loss data (see the README's
> production section).

## Product affinity rules

An opportunity exists only where a rule fires: the customer owns the trigger
product AND does not already own the recommended product.

| If Customer Owns | Recommend | Affinity | Success Rate | Avg Close |
|---|---|---|---|---|
| Core Platform (PLAT-100) | Analytics Standard (ANLYT-100) | 85% | 42% | 35d |
| Core Platform (PLAT-100) | Integration Hub (INTGR-100) | 72% | 38% | 45d |
| Enterprise Platform (PLAT-200) | Analytics Pro (ANLYT-200) | 91% | 55% | 28d |
| Enterprise Platform (PLAT-200) | Security Suite (SECUR-100) | 78% | 48% | 30d |
| Analytics Standard (ANLYT-100) | Analytics Pro (ANLYT-200) | 88% | 62% | 21d |
| Integration Hub (INTGR-100) | Security Suite (SECUR-100) | 67% | 35% | 40d |
| Enterprise Platform (PLAT-200) | Premium Support (SUPRT-100) | 82% | 65% | 14d |
| Core Platform (PLAT-100) | Premium Support (SUPRT-100) | 70% | 50% | 21d |

Reading the matrix:

- Strongest fit: Enterprise Platform to Analytics Pro, 91% affinity.
- Best converting and fastest: Enterprise Platform to Premium Support, 65%
  success rate, 14-day average close.
- Weakest: Integration Hub to Security Suite, 67% affinity and 35% success
  over 40 days.
- Two rules point at Analytics Pro (from PLAT-200 and from ANLYT-100). A
  customer owning both trigger products produces two rows for one product,
  each carrying its own score, win rate, and close time.

## Segment benchmarks

| Segment | Avg Success | Avg Cycle | Avg Expansion |
|---|---|---|---|
| Enterprise | 52% | 28d | 35% |
| Mid-Market | 38% | 42d | 25% |
| SMB | 28% | 55d | 18% |

Benchmarks are a comparison baseline for a segment, not a prediction for a
specific rule. When a rule carries its own success rate, use the rule's rate.

## Arithmetic used in every projection

- `weighted_value = annual_price x success_rate`
- `total_potential_ARR = sum(annual_price)` over the opportunities in scope
- `weighted_pipeline = sum(annual_price x success_rate)`
- `projected_margin = sum(annual_price x margin_pct / 100)`

Projected margin is computed on the unweighted price, so it can exceed the
weighted pipeline. It is not expected profit.
