# Procurement Records Data

> SYNTHETIC — DEMO DATA. Every requisition, contract, requester, and supplier
> reference in this document is fictional. This file exists so the agent has a
> working world to answer from on day one. In production, replace this file with
> tools that read your real ERP requisition register and contract management
> system (see the README's production section).

## Requisition register

| ID | Title | Requester | Department | Amount | Status | Created | PO# | Supplier | Delivery Date | Received % |
|----|-------|-----------|------------|--------|--------|---------|-----|----------|---------------|------------|
| REQ-7001 | Q1 Marketing Collateral Print Run | Angela Martinez | Marketing | $18,500 | Approved | 2025-10-28 | PO-44201 | PrintPro Services | 2025-12-05 | 0 |
| REQ-7002 | Server Room UPS Replacement | Frank O'Brien | IT | $42,000 | In Transit | 2025-10-15 | PO-44189 | APC by Schneider Electric | 2025-11-20 | 0 |
| REQ-7003 | Annual Compliance Audit Services | Carla Dubois | Finance | $65,000 | Under Review | 2025-11-10 | Pending | Deloitte | not yet scheduled | 0 |
| REQ-7004 | Ergonomic Office Chairs (50 units) | Derek Washington | HR | $27,500 | Delivered | 2025-09-20 | PO-44102 | Herman Miller | 2025-10-25 | 100 |
| REQ-7005 | Cloud Security Assessment Tool | Frank O'Brien | IT | $35,000 | Pending Approval | 2025-11-12 | Pending | CrowdStrike | not yet scheduled | 0 |

Combined value of the register: $188,000. This is the same figure that appears
as total Committed in the budget position.

Status buckets used in the dashboard summary:

| Bucket | Test | Count |
|--------|------|-------|
| Delivered | status is exactly `Delivered` | 1 |
| In Transit | status is exactly `In Transit` | 1 |
| Approved | status is exactly `Approved` | 1 |
| Pending | status contains `Pending` or contains `Review` | 2 |

## Contract portfolio

| ID | Supplier | Title | Category | Start | End | Total Value | Annual Value | Status | Auto-Renew | Notice Period |
|----|----------|-------|----------|-------|-----|-------------|--------------|--------|------------|---------------|
| CTR-3001 | AWS | Enterprise Cloud Services Agreement | Technology | 2024-01-01 | 2026-12-31 | $2,670,000 | $890,000 | Active | Yes | 90 days |
| CTR-3002 | Salesforce | CRM Enterprise License Agreement | Software | 2024-04-01 | 2025-03-31 | $430,000 | $430,000 | Renewal Due | No | 60 days |
| CTR-3003 | Deloitte | Professional Services MSA | Professional Services | 2023-06-01 | 2025-05-31 | $195,000 | $97,500 | Active | Yes | 30 days |
| CTR-3004 | Herman Miller | Furniture Supply Agreement | Office Supplies | 2024-07-01 | 2025-06-30 | $125,000 | $125,000 | Active | Yes | 30 days |
| CTR-3005 | CrowdStrike | Endpoint Security Subscription | Security | 2025-01-01 | 2025-12-31 | $78,000 | $78,000 | Active | Yes | 60 days |

Portfolio summary: 5 contracts on file, total annual value $1,620,500,
1 renewal due (CTR-3002). Four contracts carry status `Active`; the dashboard
label `Active contracts` reports the portfolio count of 5.
