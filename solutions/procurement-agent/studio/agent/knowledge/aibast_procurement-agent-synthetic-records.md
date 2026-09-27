<!-- Generated from the original workshop knowledge; edit the source and regenerate. -->
> Retained synthetic knowledge. Listed entity fields come from the SharePoint list tools; unlisted records and rules below remain authoritative knowledge. Email omissions are explicit.

# Procurement Agent — Complete Synthetic Records

> FIXED FICTIONAL SNAPSHOT. Every requester, supplier, amount, budget, status,
> term, and approval rule below is invented. Use it exactly and never browse,
> refresh, supplement, or create a transaction.

## Purchase requests

Entity rows from this section are now read with the SharePoint list tools from **Procurement Purchase Requests**. Other context below remains knowledge.

## Vendor catalog

Entity rows from this section are now read with the SharePoint list tools from **Procurement Vendor Catalog**. Other context below remains knowledge.

## Approval thresholds

| Amount up to and including | Required approver | Approval SLA |
|---|---|---|
| $5,000 | Direct Manager | 4 hours |
| $25,000 | Department Head | 8 hours |
| $100,000 | VP Finance | 24 hours |
| $500,000 | CFO | 48 hours |
| Unlimited | CEO + Board | 120 hours |

## Spend categories

| Category | Budget | Spent YTD | Committed | Available | Utilization | Status | Trend |
|---|---|---|---|---|---|---|---|
| Technology | $2,500,000 | $1,875,000 | $340,000 | $285,000 | 88.6% | At Risk | +12% YoY |
| Software | $800,000 | $645,000 | $215,000 | $-60,000 | 107.5% | Over Budget | +18% YoY |
| Office Supplies | $350,000 | $210,000 | $48,500 | $91,500 | 73.9% | On Track | -5% YoY |
| Professional Services | $500,000 | $325,000 | $35,000 | $140,000 | 72.0% | On Track | +8% YoY |
| Travel | $200,000 | $142,000 | $18,000 | $40,000 | 80.0% | On Track | -15% YoY |

## Portfolio totals

| Metric | Exact value |
|---|---|
| Total budget | $4,350,000 |
| Spent YTD | $3,197,000 (73%) |
| Committed | $656,500 |
| Available | $496,500 |

## Locked-case evidence contract

| Case | Persona | Operation | Locked prompt | Required evidence |
|---|---|---|---|---|
| PROC-01 | Procurement Manager | purchase_request | Walk me through the cloud-upgrade request and tell me whose review it needs before anything moves. | PR-5001; $125,000; CFO |
| PROC-02 | Category Buyer | vendor_comparison | Give me a neutral comparison of the approved cloud vendors; do not pick a winner. | AWS; Azure; not a supplier award |
| PROC-03 | Department Approver | approval_routing | This infrastructure request landed in my queue. What is the recommended approval path? | CFO; 48 hours; does not record an approval |
| PROC-04 | Finance Director | spend_analysis | Where is the purchasing budget under pressure, and what should we review before approving more spend? | Software; $60,000; No purchase order is created |

## Required response headings and phrases

- Request: `Purchase Request Review: PR-5001`, `Justification`, and `Approval gate`.
- Vendor review: `Vendor Comparison`, `Vendor Tiers`, and `not a supplier award`.
- Approval: `Approval Routing: PR-5001`, `Approval Thresholds`, `48 hours`,
  and `does not record an approval`.
- Spend: `Spend Analysis`, `By Category`, `Alerts`, `Software category over
  budget by $60,000`, and `No purchase order is created`.
