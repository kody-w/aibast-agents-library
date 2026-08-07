# Warehouse and Inventory Data

> SYNTHETIC — DEMO DATA. Every warehouse, SKU, level, and forecast in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that
> read your real WMS, ERP inventory positions, and demand planning system
> (see the README's production section).

## Warehouse master

| ID | Name | Region | Capacity (pallets) | Used (pallets) | Annual Holding Cost / Pallet |
|----|------|--------|--------------------|----------------|------------------------------|
| WH-ATL | Atlanta Distribution Center | Southeast | 12,000 | 10,450 | $142.00 |
| WH-ORD | Chicago Regional Hub | Midwest | 18,000 | 9,200 | $158.00 |
| WH-DFW | Dallas Fulfillment Center | South Central | 15,000 | 14,100 | $135.00 |
| WH-SEA | Seattle West Coast Depot | Pacific Northwest | 10,000 | 4,300 | $172.00 |

Warehouses are always processed in this order: WH-ATL, WH-ORD, WH-DFW,
WH-SEA. Utilization is `used / capacity`; a site is flagged only above 90.0%.

## SKU catalog

| SKU | Description | Unit Cost | Unit Weight (kg) | Reorder Point |
|-----|-------------|-----------|------------------|---------------|
| SKU-4401 | Brushless DC Motor 48V | $87.50 | 3.2 | 1,200 |
| SKU-4402 | Planetary Gearbox PG-20 | $214.00 | 5.8 | 500 |
| SKU-4403 | Linear Actuator LA-150 | $162.30 | 4.1 | 600 |
| SKU-4404 | Servo Controller SC-800 | $345.00 | 1.4 | 350 |
| SKU-4405 | Encoder Module EM-512 | $58.75 | 0.6 | 2,000 |
| SKU-4406 | Harmonic Drive HD-25 | $489.00 | 7.3 | 150 |

SKUs are always processed in this order, SKU-4401 through SKU-4406.

## Sourcing master (supplier and replenishment lead time)

One supplier and one lead time per SKU. Four suppliers cover the catalog. No
other supplier attribute exists in this data — no price breaks, no contract
terms, no quality history, no second source.

| SKU | Supplier ID | Supplier | Lead Time (days) |
|-----|-------------|----------|------------------|
| SKU-4401 | SUP-210 | Meridian Drive Systems | 21 |
| SKU-4402 | SUP-114 | Northwind Gearworks | 35 |
| SKU-4403 | SUP-338 | Caldera Motion Components | 28 |
| SKU-4404 | SUP-402 | Vantage Control Electronics | 42 |
| SKU-4405 | SUP-338 | Caldera Motion Components | 14 |
| SKU-4406 | SUP-114 | Northwind Gearworks | 56 |

Lead time is a duration only. This data carries no calendar, so no order date
and no arrival date is ever asserted.

## On-hand levels by warehouse

| SKU | WH-ATL | WH-ORD | WH-DFW | WH-SEA |
|-----|--------|--------|--------|--------|
| SKU-4401 | 3,200 | 1,800 | 4,100 | 600 |
| SKU-4402 | 750 | 2,400 | 300 | 1,100 |
| SKU-4403 | 1,900 | 500 | 2,600 | 200 |
| SKU-4404 | 400 | 1,200 | 950 | 1,800 |
| SKU-4405 | 5,000 | 3,100 | 4,800 | 900 |
| SKU-4406 | 180 | 620 | 90 | 340 |

A SKU with no level recorded at a warehouse is read as 0. There are no such
gaps in the current data.

## Demand forecast by warehouse

| SKU | WH-ATL | WH-ORD | WH-DFW | WH-SEA |
|-----|--------|--------|--------|--------|
| SKU-4401 | 2,800 | 2,600 | 3,000 | 1,500 |
| SKU-4402 | 1,100 | 900 | 1,200 | 800 |
| SKU-4403 | 800 | 1,400 | 1,100 | 900 |
| SKU-4404 | 700 | 600 | 800 | 500 |
| SKU-4405 | 3,500 | 4,200 | 3,800 | 2,300 |
| SKU-4406 | 300 | 250 | 400 | 280 |

The forecast covers one 90-day planning horizon — three months. Every
coverage, months-of-supply, and network-target figure is read against that
horizon.

`delta = on-hand - forecast` at each pair. That delta drives the
surplus/deficit classification and the transfer matching; the reorder point in
the SKU catalog is a separate, absolute floor used for value-at-risk.

## Months of coverage by warehouse (excess and aging)

`coverage_months = round(on_hand / forecast * 3, 1)` at each pair. A position
over 3.0 months carries stock beyond the horizon's demand; that surplus is the
excess exposed to write-off. Band: `E` = Excess (over 3.0, up to and including
6.0 months), `A` = Aging (over 6.0 months). Unmarked pairs are Covered and
carry no excess.

| SKU | WH-ATL | WH-ORD | WH-DFW | WH-SEA |
|-----|--------|--------|--------|--------|
| SKU-4401 | 3.4 (E) | 2.1 | 4.1 (E) | 1.2 |
| SKU-4402 | 2.0 | 8.0 (A) | 0.8 | 4.1 (E) |
| SKU-4403 | 7.1 (A) | 1.1 | 7.1 (A) | 0.7 |
| SKU-4404 | 1.7 | 6.0 (E) | 3.6 (E) | 10.8 (A) |
| SKU-4405 | 4.3 (E) | 2.2 | 3.8 (E) | 1.2 |
| SKU-4406 | 1.8 | 7.4 (A) | 0.7 | 3.6 (E) |

`excess_units = on_hand - forecast` where that is positive; it is zero for
every Covered pair. Thirteen of the twenty-four pairs carry excess, 10,880
units in total. SKU-4404 at WH-ORD sits at exactly 6.0 months and is therefore
Excess, not Aging — the aging test is strictly greater than 6.0.

## Network position by SKU

Sums across all four warehouses, used for replenishment rather than
redistribution. `network_target = 90-day forecast + reorder point`;
`buy_qty = max(0, network_target - network_on_hand)`.

| SKU | Network On-Hand | 90-Day Forecast | Safety Floor | Target | Buy Qty |
|-----|-----------------|-----------------|--------------|--------|---------|
| SKU-4401 | 9,700 | 9,900 | 1,200 | 11,100 | 1,400 |
| SKU-4402 | 4,550 | 4,000 | 500 | 4,500 | 0 |
| SKU-4403 | 5,200 | 4,200 | 600 | 4,800 | 0 |
| SKU-4404 | 4,350 | 2,600 | 350 | 2,950 | 0 |
| SKU-4405 | 13,800 | 13,800 | 2,000 | 15,800 | 2,000 |
| SKU-4406 | 1,230 | 1,230 | 150 | 1,380 | 150 |

A SKU can be long at the network level and still short at a warehouse. The
warehouse gap is closed by a transfer; only a network gap justifies a buy.
