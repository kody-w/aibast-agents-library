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

`delta = on-hand - forecast` at each pair. That delta drives the
surplus/deficit classification and the transfer matching; the reorder point in
the SKU catalog is a separate, absolute floor used for value-at-risk.
