<!-- Generated from the original workshop knowledge; edit the source and regenerate. -->
> Retained synthetic knowledge. Listed entity fields come from the SharePoint list tools; unlisted records and rules below remain authoritative knowledge. Email omissions are explicit.

# Inventory Rebalancing Pilot — Cost Tables & Review Rules

> SYNTHETIC PILOT DATA. All holding-cost rates, transfer-cost rates, unit
> costs, and weights below are fictional planning estimates, not audited
> financial figures or customer outcomes.

## Annual holding cost rate per pallet

| Facility ID | Facility name | Annual holding cost / pallet |
|---|---|---|
| WH-ATL | Atlanta Distribution Center | $142.00 |
| WH-ORD | Chicago Regional Hub | $158.00 |
| WH-DFW | Dallas Fulfillment Center | $135.00 |
| WH-SEA | Seattle West Coast Depot | $172.00 |

Estimated total annual holding cost for a facility = used pallets × annual
holding cost per pallet. Always present this as the "Total annual holding
cost" and label it as a synthetic planning estimate, never as an audited or
customer-facing figure.

## SKU unit cost and weight (for transfer-cost and value-at-risk estimates)

Entity rows from this section are now read with the SharePoint list tools from **Inventory Rebalancing SKU Unit Cost And Weight**. Other context below remains knowledge.

## Inter-facility transfer cost per kilogram (synthetic ground-freight rate)

| From \ To | WH-ATL | WH-ORD | WH-DFW | WH-SEA |
|---|---|---|---|---|
| WH-ATL | — | $0.28 | $0.22 | $0.41 |
| WH-ORD | $0.28 | — | $0.25 | $0.34 |
| WH-DFW | $0.22 | $0.25 | — | $0.38 |
| WH-SEA | $0.41 | $0.34 | $0.38 | — |

Estimated transfer cost for a proposed move = quantity × SKU weight (kg) ×
per-kg rate for the from/to pair. A typical synthetic planning assumption
for ground-freight transit is 2–5 business days. Always label transfer-cost
and transit-time figures as synthetic planning estimates.

## Classification rule

- Treat on-hand minus forecast as a planning delta, not a live
  available-to-promise value.
- Label a material surplus or deficit only when the delta exceeds the fixed
  ±200-unit tolerance described in the facility & SKU snapshot.
- Always describe the source of every figure as a fixed synthetic snapshot,
  never as a live ERP or warehouse-management query.

## Action boundary (no side effects)

- A transfer plan is a proposal for inventory, warehouse, finance, and
  transportation reviewers — it is not a confirmation that any inventory was
  reserved, picked, shipped, or moved.
- Never state or imply that a reorder, reservation, pick, shipment, transfer,
  vendor return, liquidation, or inventory-policy change has occurred.
- Production use of any recommendation requires approved ERP and
  warehouse-management connectors plus explicit authorization from the
  accountable ERP/WMS system owner. Always name this authorization gate when
  a recommendation implies an action.
