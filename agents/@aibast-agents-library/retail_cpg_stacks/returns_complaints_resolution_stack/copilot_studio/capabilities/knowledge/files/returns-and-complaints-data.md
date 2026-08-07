# Returns & Complaints Operations Data

> SYNTHETIC — DEMO DATA. Every return, order, customer, product, and volume in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real order management, returns, and case systems (see the README's
> production section).

## Return request queue

| Return ID | Order | Customer | Customer ID | Product | SKU | Price | Purchase Date | Request Date | Days | Reason | Condition | Channel | Status |
|-----------|-------|----------|-------------|---------|-----|-------|---------------|--------------|------|--------|-----------|---------|--------|
| RET-4001 | ORD-88712 | Sarah Mitchell | CUST-2041 | Classic Denim Jacket | SKU-1001 | $89.99 | 2026-02-14 | 2026-03-02 | 18 | wrong_size | unworn_tags_attached | online | pending_review |
| RET-4002 | ORD-89234 | James Kowalski | CUST-3178 | Smart Fitness Tracker | SKU-1004 | $129.99 | 2026-01-20 | 2026-03-10 | 50 | defective | non_functional | in_store | approved |
| RET-4003 | ORD-87455 | Maria Chen | CUST-1590 | Premium Running Shoes | SKU-1005 | $149.99 | 2026-02-28 | 2026-03-08 | 10 | not_as_described | lightly_used | online | pending_review |
| RET-4004 | ORD-90100 | David Okafor | CUST-4422 | Wireless Earbuds Pro | SKU-1002 | $59.99 | 2026-03-01 | 2026-03-12 | 11 | changed_mind | opened_unused | online | pending_review |
| RET-4005 | ORD-86321 | Linda Park | CUST-0887 | Leather Crossbody Bag | SKU-1007 | $79.99 | 2025-12-18 | 2026-03-14 | 91 | defective | damaged | in_store | escalated |
| RET-4006 | ORD-91005 | Robert Fernandez | CUST-5610 | UV Protection Sunglasses | SKU-1008 | $44.99 | 2026-03-05 | 2026-03-15 | 10 | wrong_item | unopened | online | approved |

Queue totals: 3 pending review, queue value $554.94.

`Days` is computed with a 30-day-month approximation, not a calendar
difference: `days = (yyyy * 365 + mm * 30 + dd)` for the request date minus the
same expression for the purchase date.

### Return notes

| Return ID | Notes |
|-----------|-------|
| RET-4001 | Ordered size M, needs size L. Willing to exchange. |
| RET-4002 | Heart rate sensor stopped working after 3 weeks. Under warranty. |
| RET-4003 | Color shown online was navy but received was dark grey. |
| RET-4004 | Found a better deal elsewhere. Wants full refund. |
| RET-4005 | Strap broke after normal use. Outside 60-day window but claims manufacturing defect. |
| RET-4006 | Received aviator style instead of ordered wayfarer style. |

## Customer 12-month return history

Trailing-twelve-month history for the customers in the queue above. This is
this retailer's own record only — there is no cross-retailer watchlist, device
signal, or real-time fraud feed in this stack.

| Customer ID | Customer | Returns (12mo) | Orders (12mo) | Return Rate | Refunded (12mo) | Prior Denied Claims |
|-------------|----------|----------------|---------------|-------------|-----------------|---------------------|
| CUST-2041 | Sarah Mitchell | 2 | 12 | 16.7% | $164.98 | 0 |
| CUST-3178 | James Kowalski | 1 | 9 | 11.1% | $74.50 | 0 |
| CUST-1590 | Maria Chen | 5 | 12 | 41.7% | $612.45 | 1 |
| CUST-4422 | David Okafor | 4 | 11 | 36.4% | $301.96 | 0 |
| CUST-0887 | Linda Park | 2 | 8 | 25.0% | $158.00 | 0 |
| CUST-5610 | Robert Fernandez | 1 | 6 | 16.7% | $61.25 | 0 |

`Return Rate` is `returns_12mo / orders_12mo`. Refunded dollars are refunds
already paid in the trailing twelve months and exclude the open request in the
queue.

### Return-abuse signals and weights

Signals are additive and each fires at most once per return.

| Signal | Weight | Fires when |
|--------|--------|------------|
| high_return_frequency | 2 | Return rate is 0.40 or higher |
| elevated_return_frequency | 1 | Return rate is 0.25 or higher but below 0.40 |
| prior_denied_claims | 2 | Customer has 1 or more prior denied claims |
| used_item_claim | 1 | Item condition is `lightly_used` or `damaged` |
| out_of_policy_window | 1 | Days since purchase is greater than 90 |

The two frequency signals are mutually exclusive. Risk tier from the total
score: 4 or more is `high`, 2 to 3 is `elevated`, 0 to 1 is `low`.

### Worked screening outcomes against the current queue

| Return ID | Customer | Return Rate | Signals | Score | Risk |
|-----------|----------|-------------|---------|-------|------|
| RET-4001 | Sarah Mitchell | 16.7% | none | 0 | low |
| RET-4002 | James Kowalski | 11.1% | none | 0 | low |
| RET-4003 | Maria Chen | 41.7% | high_return_frequency, prior_denied_claims, used_item_claim | 5 | high |
| RET-4004 | David Okafor | 36.4% | elevated_return_frequency | 1 | low |
| RET-4005 | Linda Park | 25.0% | elevated_return_frequency, used_item_claim, out_of_policy_window | 3 | elevated |
| RET-4006 | Robert Fernandez | 16.7% | none | 0 | low |

Screening totals: 6 screened, 2 at elevated or higher, refund value under
review $229.98 (RET-4003 $149.99 + RET-4005 $79.99).

The screen is evidence for a loss-prevention reviewer. Nothing here denies a
return, withholds a refund, blocks a customer, or opens a fraud case.

## Complaint categories

| Category | ID | Monthly Volume | Severity Weight | Avg Resolution | Escalation Rate |
|----------|----|----------------|-----------------|----------------|-----------------|
| Product Quality | product_quality | 142 | 0.85 | 36h | 15% |
| Order Fulfillment | order_fulfillment | 98 | 0.70 | 24h | 8% |
| Pricing & Billing | pricing_billing | 67 | 0.65 | 18h | 5% |
| Service Experience | service_experience | 53 | 0.60 | 48h | 22% |

Total monthly complaints: 360.

### Classification keywords

| Category | Keywords |
|----------|----------|
| product_quality | defective, broken, poor quality, fell apart, not durable |
| order_fulfillment | wrong item, missing, late delivery, not received, damaged in shipping |
| pricing_billing | overcharged, wrong price, coupon not applied, double charged |
| service_experience | rude staff, long wait, unhelpful, no response, poor communication |

Classification is a substring keyword count over the lowercased complaint text.
Highest count wins; ties resolve to the earlier category in the table above; a
zero score defaults to `service_experience`.

## Six-month trend series

| Month | Total Returns | Return Rate | Avg Resolution | CSAT | Refund Total |
|-------|--------------|-------------|----------------|------|--------------|
| 2025-10 | 312 | 4.1% | 28.5h | 4.1/5.0 | $18,720.00 |
| 2025-11 | 345 | 4.5% | 30.2h | 4.0/5.0 | $21,450.00 |
| 2025-12 | 498 | 6.2% | 38.7h | 3.6/5.0 | $34,200.00 |
| 2026-01 | 387 | 5.0% | 32.1h | 3.9/5.0 | $24,800.00 |
| 2026-02 | 328 | 4.3% | 27.8h | 4.2/5.0 | $19,650.00 |
| 2026-03 | 360 | 4.7% | 29.4h | 4.1/5.0 | $22,100.00 |

Total refunded across the six months: $140,920.00.

Trend direction rule: compare the mean return rate of the last three months
(4.667) against the mean of the first three (4.933). Below `earlier - 0.3` is
IMPROVING, above `earlier + 0.3` is WORSENING, anything inside the band is
STABLE. This series is STABLE.

### Return reason volumes by month

| Reason | 2025-10 | 2025-11 | 2025-12 | 2026-01 | 2026-02 | 2026-03 | Total | Avg/Month |
|--------|---------|---------|---------|---------|---------|---------|-------|-----------|
| wrong_size | 98 | 112 | 160 | 125 | 105 | 115 | 715 | 119.2 |
| defective | 72 | 68 | 95 | 82 | 71 | 78 | 466 | 77.7 |
| changed_mind | 65 | 78 | 130 | 88 | 70 | 80 | 511 | 85.2 |
| not_as_described | 45 | 52 | 68 | 55 | 48 | 52 | 320 | 53.3 |
| wrong_item | 32 | 35 | 45 | 37 | 34 | 35 | 218 | 36.3 |

Standing insights on this series:

- Holiday season (Dec) drove a 44% spike in returns, primarily changed-mind returns.
- Wrong-size returns consistently highest — consider enhanced size guide implementation.
- Resolution time improved 8% over the period despite volume increases.
- CSAT recovered to 4.1 after post-holiday dip to 3.6.
