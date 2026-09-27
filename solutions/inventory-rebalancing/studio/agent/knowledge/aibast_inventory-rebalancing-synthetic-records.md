<!-- Generated from the original workshop knowledge; edit the source and regenerate. -->
> Retained synthetic knowledge. Listed entity fields come from the SharePoint list tools; unlisted records and rules below remain authoritative knowledge. Email omissions are explicit.

# Inventory Rebalancing Pilot — Facility & SKU Synthetic Snapshot

> SYNTHETIC PILOT DATA. Every warehouse, SKU, quantity, forecast, and reorder
> point below is fictional. No live ERP or warehouse-management system was
> queried to produce this snapshot; treat it strictly as a fixed reference
> data set for the pilot.

## Facility snapshot

| Facility ID | Facility name | Region | Capacity (pallets) | Used (pallets) | Utilization |
|---|---|---|---|---|---|
| WH-ATL | Atlanta Distribution Center | Southeast | 12,000 | 10,450 | 87.1% |
| WH-ORD | Chicago Regional Hub | Midwest | 18,000 | 9,200 | 51.1% |
| WH-DFW | Dallas Fulfillment Center | South Central | 15,000 | 14,100 | 94.0% |
| WH-SEA | Seattle West Coast Depot | Pacific Northwest | 10,000 | 4,300 | 43.0% |

Facilities above 90% synthetic utilization (currently WH-DFW, Dallas
Fulfillment Center) represent the highest facility-pressure review priority.
Facilities with available capacity (WH-ORD, WH-SEA) are candidate receiving
locations for inbound transfers.

## SKU on-hand levels by facility

Entity rows from this section are now read with the SharePoint list tools from **Inventory Rebalancing SKU On Hand Levels By Facility**. Other context below remains knowledge.

`SKU-4406` (Harmonic Drive HD-25) has a fixed synthetic reorder point of
150 units. On-hand at WH-DFW (90 units) is below this reorder point and
should be reviewed first; on-hand at WH-ATL (180), WH-ORD (620), and WH-SEA
(340) remain above the reorder point. Apply this same below-reorder-point
check to every SKU and facility in the table above.

## Demand forecast by facility (synthetic, forecast period unspecified)

Entity rows from this section are now read with the SharePoint list tools from **Inventory Rebalancing Demand Forecast By Facility**. Other context below remains knowledge.

Compare on-hand minus forecast to identify a forecast-relative surplus
(positive delta) or shortage (negative delta). Treat any delta beyond ±200
units as material; treat deltas within ±200 units as balanced within
tolerance. This delta is a planning signal, not a live available-to-promise
value.

## Synthetic portfolio classification

Entity rows from this section are now read with the SharePoint list tools from **Inventory Rebalancing Portfolio Classification**. Other context below remains knowledge.

`SKU-4402`, `SKU-4403`, and `SKU-4406` are classified SLOW-MOVING in this
fixed pilot profile. `SKU-4403` and `SKU-4406` also carry ELEVATED synthetic
lifecycle risk. A lifecycle-risk signal is a review flag, not an
obsolescence declaration — vendor return, controlled disposition, or any
portfolio-policy change requires source-system evidence and authorized
review.

All facility names, SKU identifiers, quantities, forecasts, reorder points,
and classifications above are synthetic pilot evidence, not production data.
