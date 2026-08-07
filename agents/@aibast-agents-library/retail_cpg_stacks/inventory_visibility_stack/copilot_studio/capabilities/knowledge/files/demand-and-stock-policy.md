# Demand Rates and Stock Policy

> SYNTHETIC — DEMO DATA. Every sell-through rate, channel weight, and threshold
> in this document is fictional. This file exists so the agent has a working
> world to answer from on day one. In production, replace this file with tools
> that read your real demand forecast, channel plan, and inventory policy
> service (see the README's production section).

## Daily sell-through by SKU

Network-level units sold per day. Used for days-of-supply and for the
replenishment target.

| SKU | Product | Units / Day | 14-Day Target Qty |
|-----|---------|-------------|-------------------|
| SKU-1001 | Classic Denim Jacket | 6.2 | 86 |
| SKU-1002 | Wireless Earbuds Pro | 9.8 | 137 |
| SKU-1003 | Organic Cotton T-Shirt | 14.5 | 203 |
| SKU-1004 | Smart Fitness Tracker | 3.1 | 43 |
| SKU-1005 | Premium Running Shoes | 2.7 | 37 |
| SKU-1006 | Stainless Water Bottle | 12.0 | 168 |
| SKU-1007 | Leather Crossbody Bag | 4.4 | 61 |
| SKU-1008 | UV Protection Sunglasses | 7.3 | 102 |

The 14-day target column is `int(units_per_day * 14)` — truncated, not rounded
(6.2 x 14 = 86.8 becomes 86).

## Channel demand weights

| Channel | Display Name | Weight | Daily Units Avg |
|---------|--------------|--------|-----------------|
| in_store | In Store | 45% | 320 |
| online_ship | Online Ship | 30% | 215 |
| bopis | Bopis | 15% | 108 |
| marketplace | Marketplace | 10% | 72 |

Allocation truncates each channel's share; the leftover remainder is added to
`in_store`.

## Stock status thresholds

Evaluated in this order against the store's own safety-stock level.

| Status | Condition |
|--------|-----------|
| OUT_OF_STOCK | on-hand = 0 |
| CRITICAL | on-hand <= safety stock |
| LOW | on-hand <= safety stock x 1.5 |
| HEALTHY | everything above that |

Comparisons are inclusive. On-hand 12 against safety stock 8 is `LOW`, because
8 x 1.5 = 12. On-hand 5 against safety stock 3 is `HEALTHY`, because
3 x 1.5 = 4.5.

## Alert actions

| Status | Action Required |
|--------|-----------------|
| OUT_OF_STOCK | Emergency replenish |
| CRITICAL | Expedite transfer |
| LOW | Warning only — listed with days remaining, no action line |

## Replenishment and sourcing policy

| Rule | Value |
|------|-------|
| Supply target | 14 days at every store, every SKU |
| Replenish quantity | max(0, 14-day target qty - on-hand) |
| Primary source | WH-CENTRAL when its on-hand for the SKU >= the replenish quantity |
| Fallback source | WH-EAST |
| Line cost basis | unit cost (not retail price) |
| Splitting | A replenishment line is never split across warehouses |

## Standing allocation guardrails

- **In-Store Priority:** flagship and mall locations receive 60% of the
  in-store allocation.
- **Online Buffer:** maintain a 3-day safety stock for e-commerce fulfillment.
- **BOPIS Reserve:** hold a 10% buffer for same-day pickup surges.
- **Marketplace Cap:** limit marketplace allocation to prevent channel
  conflict.
