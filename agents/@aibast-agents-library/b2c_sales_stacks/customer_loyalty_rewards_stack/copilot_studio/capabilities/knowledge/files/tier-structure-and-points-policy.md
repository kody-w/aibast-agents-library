# Tier Structure and Points Policy

> SYNTHETIC — DEMO DATA. Every threshold, multiplier, and perk in this document
> is fictional. This file exists so the agent has a working world to answer
> from on day one. In production, replace this file with tools that read your
> real program rules and tier engine (see the README's production section).

## Tier structure

| Tier | Min Spend | Points Multiplier | Next Tier | Spend Threshold for Next Tier |
|------|-----------|-------------------|-----------|-------------------------------|
| Bronze | $0 | 1.0x | Silver | $1,000 |
| Silver | $1,000 | 1.25x | Gold | $3,000 |
| Gold | $3,000 | 1.5x | Platinum | $6,000 |
| Platinum | $6,000 | 2.0x | — (top tier) | — |

The "spend threshold for next tier" is an absolute YTD spend figure, not an
incremental amount above the current tier.

## Tier perks

| Tier | Perks (in order) |
|------|------------------|
| Bronze | Birthday bonus points; Member-only sales access |
| Silver | Bronze perks; Free standard shipping; Early access to new products |
| Gold | Silver perks; Free express shipping; Exclusive gold events; Annual gift |
| Platinum | Gold perks; Personal shopping advisor; Free returns; VIP lounge access; Quarterly bonus |

Dashboards and tier tables show only the first two perks per tier. The full
list is given on request.

## Points valuation

1 point = $0.02.

`points_value = round(points x 0.02, 2)`

Applied to the current roster: 48,250 → $965.00; 22,100 → $442.00;
8,450 → $169.00; 2,100 → $42.00. Program-wide: 80,900 → $1,618.00.

The tier multiplier applies to points earned going forward. It is never
applied to an existing balance or to a cash value.

## Tier progress

For a member below Platinum:

`progress_pct = min(100.0, round(spend_ytd / spend_threshold_for_next_tier x 100, 1))`

`spend_remaining = max(0, spend_threshold_for_next_tier - spend_ytd)`

Platinum members have no next tier: progress is reported as
"Top Tier Achieved" with no percentage and no remaining spend.

## Reward eligibility

A catalog reward is eligible for a member only when both conditions hold:

1. The reward's category appears in that member's preferred reward categories.
2. `points_cost <= points_balance`.

Both gates are hard. A reward that fails either one is not a recommendation;
it appears only in the full catalog listing.

## Boundaries

- The agent recommends. Redeeming points, crediting points, changing a tier,
  and contacting a member are all actions a person takes in the loyalty
  platform.
- Every member reference carries the LM- id.
- A member id that is not in this roster does not exist as far as the agent is
  concerned; say so rather than guessing a balance.
