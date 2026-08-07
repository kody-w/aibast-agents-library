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

## Points liability

Outstanding points are an open program liability: every unredeemed point is
value the program still owes its members.

`points_liability = round(points_outstanding x 0.02, 2)`

Program-wide: 80,900 points outstanding = $1,618.00 liability.

The only levers that reduce the liability are redemptions. A member's
addressable liability is the total points cost of the rewards they are already
eligible for today under the two eligibility gates above:

| Member | Points | Eligible Rewards | Points Redeemable | Liability Addressed |
|--------|--------|------------------|-------------------|---------------------|
| LM-10001 Katherine Brooks | 48,250 | $500 Travel Voucher; $100 Dining Gift Card | 30,000 | $600.00 |
| LM-10002 Antonio Vasquez | 22,100 | Premium Wireless Headphones; $50 Store Gift Card | 17,500 | $350.00 |
| LM-10003 Rachel Nguyen | 8,450 | 20% Off Next Purchase | 3,000 | $60.00 |
| LM-10004 Derek Washington | 2,100 | Free Shipping for 3 Months | 1,500 | $30.00 |

Addressable now: 52,000 points ($1,040.00), 64.3% of points outstanding.
Residual liability if every eligible reward is taken: 28,900 points ($578.00).

A lever is a redemption the member could make, not one the agent makes. There
is no expiry rule in this program, so points never fall off the liability on
their own.

## Engagement bands and retention

Engagement score is a recorded 0-100 field. It maps to exactly three published
bands, and these are the only bands in the program:

| Band | Engagement Score | Retention Meaning |
|------|------------------|-------------------|
| Engaged | 75-100 | No retention action required; standard program communications. |
| Watch | 50-74 | Review for a retention touch; engagement has slipped below Engaged. |
| At Risk | 0-49 | Prioritize for retention outreach by the program team. |

Applied to the current roster: LM-10001 (92) Engaged; LM-10002 (75) Engaged;
LM-10003 (58) Watch; LM-10004 (32) At Risk.

The retention watchlist is every member below the Engaged band, in roster id
order — currently LM-10003 (Watch) and LM-10004 (At Risk), 2 of 4 members.

Points redeemed YTD is a supporting signal, never a band on its own: a member
with 0 redeemed YTD has converted no points to value this year (LM-10003 and
LM-10004 are both at 0). Report it beside the band; do not derive a band from
it.

Bands describe attention, not outcome. The agent never states that a member
has churned, will churn, or has been contacted.

## Boundaries

- The agent recommends. Redeeming points, crediting points, changing a tier,
  and contacting a member are all actions a person takes in the loyalty
  platform.
- Every member reference carries the LM- id.
- A member id that is not in this roster does not exist as far as the agent is
  concerned; say so rather than guessing a balance.
