# Transfer Lanes and Cost Model

> SYNTHETIC — DEMO DATA. Every lane rate, threshold, and coefficient in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that
> read your real freight rate cards, carrier tenders, and finance-owned
> holding cost model (see the README's production section).

## Inter-warehouse lane rates (USD per kilogram)

Rates are directional. There are 12 directed lanes among the four warehouses;
no other lane exists.

| From \ To | WH-ATL | WH-ORD | WH-DFW | WH-SEA |
|-----------|--------|--------|--------|--------|
| WH-ATL | — | 0.28 | 0.22 | 0.41 |
| WH-ORD | 0.28 | — | 0.25 | 0.34 |
| WH-DFW | 0.22 | 0.25 | — | 0.38 |
| WH-SEA | 0.41 | 0.34 | 0.38 | — |

Transfer cost for a move:
`round(qty * lane_rate_per_kg * unit_weight_kg, 2)`.

If a lane is not in the matrix, the fallback rate is `0.30` per kilogram. All
12 lanes above are defined, so the fallback does not apply to the current
data.

## Classification thresholds

| Test | Rule | Applies to |
|------|------|------------|
| Deficit | `on_hand - forecast < -200` | Rebalance table (counts as critical) |
| Surplus | `on_hand - forecast > 500` | Rebalance table |
| Balanced | anything between, inclusive of -200 and +500 | Rebalance table (row suppressed) |
| Transfer source | `on_hand - forecast > 200` | Transfer matching |
| Transfer destination | `on_hand - forecast < -200` | Transfer matching |
| Over-capacity flag | `utilization > 90.0%` | Inventory snapshot |
| Below reorder | `on_hand < reorder_point` | Snapshot note and value at risk |
| Covered | `coverage_months <= 3.0` | Waste exposure (row suppressed, no excess) |
| Excess | `3.0 < coverage_months <= 6.0` | Waste exposure (write-off factor 0.10) |
| Aging | `coverage_months > 6.0` | Waste exposure (write-off factor 0.25) |
| Buy required | `network_on_hand < forecast + reorder_point` | Replenishment plan |

The surplus band for reporting (+500) is stricter than the surplus band for
transfer matching (+200). A position between +201 and +500 is reported
Balanced but can still ship.

## Planning coefficients — estimates, not quotes

| Coefficient | Value | Used for |
|-------------|-------|----------|
| Pallet factor | `0.02` pallets per inbound unit, truncated | Projected post-transfer utilization |
| Expedite premium multiplier | `3.2` x total transfer cost | Avoided expedited-shipping premium |
| Risk realization factor | `0.6` x total value at risk | Net annual benefit calculation |
| Transit window | 2-5 business days, ground freight | Transfer plan transit estimate |
| Forecast horizon | 90 days = `3` months | Coverage, months of supply, network target |
| Excess write-off factor | `0.10` x excess value | Waste exposure, Excess band |
| Aging write-off factor | `0.25` x excess value | Waste exposure, Aging band |
| Network safety stock | one reorder point per SKU | Replenishment target |

Net annual benefit = `(total_value_at_risk * 0.6) - total_transfer_cost`.
Avoided expedited-shipping premium = `total_transfer_cost * 3.2`.
Projected pallets = `used_pallets + int(inbound_units * 0.02)` — inbound only;
outbound units are not deducted.

## Waste exposure model

`coverage_months = round(on_hand / forecast * 3, 1)`.
`excess_units = on_hand - forecast`, counted only where positive.
`write_off_exposure = round(excess_units * unit_cost * band_factor, 2)`, with
the band factor 0.10 for Excess and 0.25 for Aging. The total is the sum of
the rounded rows.

`exposure_removed = round(min(excess_units, units_shipped_out_by_the_transfer
_plan) * unit_cost * band_factor, 2)` per position. Relocated units are excess
only at the shipping site; the receiving site is in deficit, so those units get
consumed instead of written off. Whatever the transfer plan does not relocate
stays exposed.

Both band factors are fixed planning coefficients. Neither is a booked
write-off, an inventory reserve, or a finance-approved impairment.

## Replenishment model

`network_on_hand` and `network_forecast` are the four-warehouse sums for a SKU.
`network_target = network_forecast + reorder_point` — one reorder point held as
network safety stock.
`buy_qty = max(0, network_target - network_on_hand)`.
`estimated_spend = round(buy_qty * unit_cost, 2)`.

Redistribution and replenishment answer different questions. A transfer fixes
where the stock is; a buy fixes how much of it exists. Residual buy at a
below-reorder position = `max(0, reorder_point - (on_hand + inbound units from
the transfer plan))`. On the current data every one of those residuals is zero,
so no buy is justified by a local gap — the recommended buys exist purely to
restore network coverage.

Every figure in this section is a fixed-coefficient planning heuristic. None
of them is a carrier quote, a booked saving, or a finance-approved number.
