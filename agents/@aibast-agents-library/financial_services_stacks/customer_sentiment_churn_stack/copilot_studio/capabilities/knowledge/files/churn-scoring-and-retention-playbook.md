# Churn Scoring and Retention Playbook

> SYNTHETIC — DEMO DATA. Every weight, threshold, cost, and success rate in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real churn model and offer catalog (see the README's production
> section).

## Churn indicators

| Indicator | Threshold | Weight | Description | Scored |
|-----------|-----------|--------|-------------|--------|
| low_nps | 5 | 25 | NPS score below 5 indicates detractor status | yes |
| declining_transactions | 10 | 20 | Monthly transactions below segment average | yes |
| high_complaints | 3 | 20 | 3+ complaints in last 12 months | yes |
| low_engagement | 30 | 15 | Digital engagement score below 30 | yes |
| single_product | 1 | 10 | Only one active product | yes |
| stale_survey | 90 | 10 | Last survey response over 90 days ago | reference only |

Scoring conditions, applied strictly:

- `nps_score < 5` adds 25
- `monthly_transactions < 10` adds 20
- `complaint_count_12m >= 3` adds 20
- `digital_engagement_score < 30` adds 15
- `product count <= 1` adds 10
- `score = min(100, total)`

`stale_survey` is published in the indicator reference but is not added to the
score.

## Risk bands

| Band | Score |
|------|-------|
| High | 50 and above |
| Medium | 25 to 49 |
| Low | below 25 |

Only High-risk customers (50+) get a detail block in the churn report. Only
customers at 25 or above receive retention recommendations.

## Retention action catalog

| Action | Description | Cost | Success Rate |
|--------|-------------|------|--------------|
| fee_waiver | Waive monthly maintenance fees for 6 months | $72 | 45% |
| rate_upgrade | Offer premium savings rate for 12 months | $150 | 35% |
| personal_outreach | Schedule call with relationship manager | $25 | 55% |
| product_bundle | Offer discounted product bundle with waived fees | $200 | 60% |
| loyalty_bonus | Credit loyalty bonus to account | $100 | 50% |
| complaint_resolution | Escalate to service recovery team | $50 | 65% |

## Recommendation rules

Applied to customers scoring 25 or above. The item number is bound to the rule,
so a customer who fails rule 1 starts at item 2.

| Item | Condition | Action |
|------|-----------|--------|
| 1 | complaint_count_12m >= 3 | Complaint Resolution |
| 2 | nps_score < 5 | Personal Outreach |
| 3 | product count <= 2 | Product Bundle |
| 3 | product count > 2 | Loyalty Bonus |

Item 3 always emits one branch or the other. Fee Waiver and Rate Upgrade are in
the catalog but no rule selects them; they are available for a human to choose,
not recommended automatically.

Every action here is a proposal. The agent never executes, credits, waives,
schedules, or escalates anything.
