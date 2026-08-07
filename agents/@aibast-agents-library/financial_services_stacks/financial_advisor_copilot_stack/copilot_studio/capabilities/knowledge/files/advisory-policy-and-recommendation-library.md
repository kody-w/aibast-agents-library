# Advisory Policy and Recommendation Library

> SYNTHETIC — DEMO DATA. Every rule text and recommendation in this document
> is fictional and is not legal, tax, or compliance guidance. This file exists
> so the agent has a working world to answer from on day one. In production,
> replace this file with tools that read your firm's real compliance rule set
> and model portfolio guidance (see the README's production section).

## Regulatory requirements

| Rule | Description | Applies To |
|---|---|---|
| Regulation Best Interest | Ensure recommendations are in client's best interest | All |
| Form CRS Delivery | Relationship summary delivered at account opening and annually | All |
| Suitability Obligation | Investment recommendations suitable for client profile | All |
| Concentration Limit | No single position exceeds 10% of portfolio | All |
| Senior Investor Protection | Enhanced protections for clients age 65+ | Seniors |

Reg BI, Form CRS, and Suitability are stated obligations with no automated
per-client test in this data set. List them as applicable; never report them
as passed or failed.

## Automated compliance flags

| Flag | Condition | Flag text |
|---|---|---|
| Concentration risk | any asset class `allocation > 50` | `Concentration risk: <asset class> at <allocation>%` |
| Senior investor | `age >= 65` | `Senior investor protections apply` |
| Allocation drift | `max_drift > 5` (strictly greater) | `Allocation drift of <max_drift>% exceeds threshold` |

Status is `Issues Found` when one or more flags fire, otherwise `Compliant`.

Known gap, stated honestly rather than papered over: the written
Concentration Limit rule says no single **position** exceeds 10% of the
portfolio, but the automated check tests **asset class** allocation above
50%. Report what the check actually fired on; do not claim the 10% rule was
tested.

## Current flag state

| Client | Concentration | Senior (65+) | Drift (>5%) | Status |
|---|---|---|---|---|
| Robert & Susan Whitfield (CLI-3001) | no (max class 35.0%) | no (age 58) | no (max drift 5.0%, at threshold) | Compliant |
| Angela Martinez (CLI-3002) | no (max class 50.0%, not above 50) | no (age 34) | no (max drift 5.0%, at threshold) | Compliant |
| William Chen Trust (CLI-3003) | no (max class 45.0%) | yes (age 72) | no (max drift 0%) | Issues Found |

CLI-3002's US Equities sits at exactly 50.0% — the condition is `> 50`, so it
does not fire. CLI-3001's max drift is exactly 5.0% — the condition is `> 5`,
so it does not fire either.

## Recommendation library, by risk profile

The set is selected by the client's risk profile only. All three items in the
matching set are presented, in this order, with the rationale verbatim.

### moderate

| # | Action | Rationale |
|---|---|---|
| 1 | Rebalance to target allocation | Drift from target exceeds 3% in multiple asset classes |
| 2 | Reduce cash overweight | Excess cash drag on returns; deploy to equities |
| 3 | Increase international exposure | Underweight vs target; diversification benefit |

### aggressive

| # | Action | Rationale |
|---|---|---|
| 1 | Increase emerging markets allocation | Below target; favorable long-term growth outlook |
| 2 | Consider small-cap tilt | Long time horizon supports higher-volatility allocations |
| 3 | Build cash reserve to target 5% | Slightly underweight cash for opportunistic rebalancing |

### conservative

| # | Action | Rationale |
|---|---|---|
| 1 | Maintain current allocation | Portfolio aligned with targets; no rebalancing needed |
| 2 | Review bond duration | Consider shortening duration if rate hikes expected |
| 3 | Tax-loss harvesting review | Identify unrealized losses for year-end tax planning |

## Rebalancing trade rule

For each asset class: `diff_pct = target - allocation`. Emit a trade row only
when `abs(diff_pct) >= 1.0`. Action is `Buy` when `diff_pct > 0`, otherwise
`Sell`. Estimated amount is `abs(diff_pct / 100 * total_assets)`.

Worked example, CLI-3001 (total assets $1,850,000):

| Asset Class | Current | Target | Action | Est. Amount |
|---|---|---|---|---|
| US Equities | 30.0% | 35.0% | Buy | $92,500 |
| International Equities | 10.0% | 15.0% | Buy | $92,500 |
| Fixed Income | 35.0% | 30.0% | Sell | $92,500 |
| Cash & Equivalents | 10.0% | 5.0% | Sell | $92,500 |

Real Estate (REITs) and Alternatives are omitted: both are at 0.0% drift,
below the 1.0 percentage-point threshold. Omitted means absent from the
table — not listed as "no action".

Every trade above is a proposal. Nothing here is an order, and no amount
carries a price or a timing assumption.
