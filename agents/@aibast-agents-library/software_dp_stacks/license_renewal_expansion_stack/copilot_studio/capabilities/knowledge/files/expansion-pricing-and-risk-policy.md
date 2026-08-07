# Expansion Pricing and Risk Policy

> SYNTHETIC — DEMO DATA. Every price, threshold, and weighting in this document
> is fictional. This file exists so the agent has a working world to answer from
> on day one. In production, replace this file with tools that read your real
> price book, health-scoring model, and forecast policy.

## Expansion pricing catalog

| Key | Description | Price | Notes |
|-----|-------------|-------|-------|
| additional_seats | Incremental seat licence | $120 per seat | Recorded min_qty is 10, but the model always prices a fixed block of 50 seats = $6,000 |
| analytics_addon | Advanced analytics module | $24,000 | Flat, per account |
| api_premium | Premium API tier with higher rate limits | $18,000 | Priced but never modeled - no signal rule attaches it |
| sso_subsidiary | SSO extension per subsidiary | $12,000 | Model applies a fixed multiplier of 3 = $36,000 |
| custom_integration | Custom integration package | $36,000 | Flat, per account |

## Risk banding from health score

| Band | Rule | Accounts |
|------|------|----------|
| LOW | health_score >= 70 | LIC-3004 (94), LIC-3001 (88) |
| MEDIUM | 50 <= health_score < 70 | LIC-3003 (62) |
| HIGH | health_score < 50 | LIC-3002 (29), LIC-3005 (35) |

At-Risk ARR in the renewal pipeline counts HIGH rows only: $72,000 + $54,000 =
$126,000. MEDIUM never counts.

## Two different "at risk" numbers

They are computed from different gates and must never be conflated.

| Figure | Gate | Value |
|--------|------|-------|
| Pipeline At-Risk ARR | health_score < 50 | $126,000 |
| Churn-Risk ARR | account has one or more churn signals | $318,000 |

The gap is LIC-3003 Redwood Supply Chain at $192,000: a MEDIUM band (62) that
still carries a churn signal.

## Expansion qualification rules

1. No expansion signals means the account is excluded outright, regardless of
   ARR, health, or seat utilization.
2. Seat headroom line fires only when `seats_used / seats * 100 > 90`. It fires
   for LIC-3001 (94.7%), LIC-3003 (98.8%), and LIC-3004 (99.2%), and prices the
   same $6,000 in every case.
3. Signal text is matched case-insensitively for three keywords only:
   `analytics` -> $24,000, `sso` -> $36,000, `integration` -> $36,000.
4. Signals with no matching keyword add $0 and are still shown - for example
   "Opening 12 new locations", "Requested bulk seat pricing", and
   "API usage +45% QoQ".

Resulting modeled potential: LIC-3001 $42,000, LIC-3004 $42,000, LIC-3003
$30,000; total $114,000.

## Forecast weightings

| Scenario | Formula | Value |
|----------|---------|-------|
| Best case | base + expansion = 966,000 + 114,000 | $1,080,000 |
| Expected | base + round(expansion * 0.4) - round(churn * 0.3) = 966,000 + 45,600 - 95,400 | $916,200 |
| Worst case | base - churn = 966,000 - 318,000 | $648,000 |

The 40% expansion and 30% churn weightings are fixed constants applied to the
portfolio totals. They are never re-weighted per account.

## Standing recommendations

These are a fixed list, reported as recorded guidance rather than derived per
run.

- Prioritize executive engagement for high-churn-risk accounts.
- Fast-track expansion proposals for Skyline Hospitality and Pinnacle Insurance.
- Assign dedicated CSM resources to ClearView Analytics and Granite
  Construction.

## Action boundary

Nothing in this policy authorizes the agent to renew a contract, issue a quote,
apply a discount, add or remove a SKU, change a price, or notify a CSM or
executive. Every figure here supports a human decision.
