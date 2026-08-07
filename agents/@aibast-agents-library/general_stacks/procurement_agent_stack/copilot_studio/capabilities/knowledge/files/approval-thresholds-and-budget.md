# Approval Thresholds and Category Budget

> SYNTHETIC — DEMO DATA. Every threshold, budget, and spend figure in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that
> read your real approval workflow engine and finance ledger (see the README's
> production section).

## Approval thresholds

A request routes to the **first** band whose amount limit is greater than or
equal to the request amount.

| Amount Limit | Approver | SLA |
|--------------|----------|-----|
| Up to $5,000 | Direct Manager | 4h |
| Up to $25,000 | Department Head | 8h |
| Up to $100,000 | VP Finance | 24h |
| Up to $500,000 | CFO | 48h |
| Up to Unlimited | CEO + Board | 120h |

### Where the open requests land

| ID | Amount | Band | Required Approver | SLA |
|----|--------|------|-------------------|-----|
| PR-5001 | $125,000 | Up to $500,000 | CFO | 48h |
| PR-5002 | $48,500 | Up to $100,000 | VP Finance | 24h |
| PR-5003 | $215,000 | Up to $500,000 | CFO | 48h |
| PR-5004 | $35,000 | Up to $100,000 | VP Finance | 24h |

## Category budget ledger

Utilization is `(spent YTD + committed) / budget`. Status is Over Budget when
available is negative, otherwise At Risk above 85% utilization, otherwise On
Track.

| Category | Budget | Spent YTD | Committed | Available | Utilization | Status | Trend |
|----------|--------|-----------|-----------|-----------|-------------|--------|-------|
| Technology | $2,500,000 | $1,875,000 | $340,000 | $285,000 | 88.6% | At Risk | +12% YoY |
| Software | $800,000 | $645,000 | $215,000 | $-60,000 | 107.5% | Over Budget | +18% YoY |
| Office Supplies | $350,000 | $210,000 | $48,500 | $91,500 | 73.9% | On Track | -5% YoY |
| Professional Services | $500,000 | $325,000 | $35,000 | $140,000 | 72.0% | On Track | +8% YoY |
| Travel | $200,000 | $142,000 | $18,000 | $40,000 | 80.0% | On Track | -15% YoY |

## Portfolio totals

| Metric | Value |
|--------|-------|
| Total Budget | $4,350,000 |
| Spent YTD | $3,197,000 (73%) |
| Committed | $656,500 |
| Available | $496,500 |

## Standing alerts

- Software category over budget by $60,000 - requires reallocation.
- Technology committed spend approaching budget limit.

Source systems: Approval Workflow Engine (thresholds), ERP + Finance System
(budget ledger).
