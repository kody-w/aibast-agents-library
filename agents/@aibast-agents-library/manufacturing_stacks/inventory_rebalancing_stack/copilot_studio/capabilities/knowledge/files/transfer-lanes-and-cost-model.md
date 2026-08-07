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

Net annual benefit = `(total_value_at_risk * 0.6) - total_transfer_cost`.
Avoided expedited-shipping premium = `total_transfer_cost * 3.2`.
Projected pallets = `used_pallets + int(inbound_units * 0.02)` — inbound only;
outbound units are not deducted.

Every figure in this section is a fixed-coefficient planning heuristic. None
of them is a carrier quote, a booked saving, or a finance-approved number.
