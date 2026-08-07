# Support Operations Data

> SYNTHETIC — DEMO DATA. Every customer, ticket, and knowledge base article in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real ticketing system and knowledge base (see the README's
> production section).

## Support ticket queue

| ID | Customer | Subject | Severity | Category | Status | Created | SLA Deadline | Assigned To | ARR |
|----|----------|---------|----------|----------|--------|---------|--------------|-------------|-----|
| TKT-8001 | Meridian Healthcare Systems | Dashboard loading timeout on large datasets | P2 | performance | open | 2026-03-15T09:22:00 | 2026-03-16T09:22:00 | Tier 2 - Backend | $186,000 |
| TKT-8002 | ClearView Analytics | SSO login failure after IdP certificate rotation | P1 | authentication | in_progress | 2026-03-16T06:15:00 | 2026-03-16T10:15:00 | Tier 3 - Security | $72,000 |
| TKT-8003 | Skyline Hospitality Group | API rate limit exceeded during bulk import | P3 | api | open | 2026-03-14T14:30:00 | 2026-03-17T14:30:00 | Tier 1 - General | $360,000 |
| TKT-8004 | BrightPath Education | Report export generates corrupted CSV files | P2 | data_export | waiting_customer | 2026-03-13T11:00:00 | 2026-03-14T11:00:00 | Tier 2 - Data | $96,000 |
| TKT-8005 | Granite Construction Co | Cannot add new users to workspace | P2 | user_management | open | 2026-03-16T08:45:00 | 2026-03-17T08:45:00 | Tier 1 - General | $54,000 |

## Ticket detail

| ID | Description |
|----|-------------|
| TKT-8001 | Dashboard takes 45+ seconds to load when filtering by date ranges exceeding 90 days. |
| TKT-8002 | All users unable to authenticate via Okta SSO after certificate rotation. Entire org locked out. |
| TKT-8003 | Bulk import process hitting 429 errors. Need temporary rate limit increase or batch guidance. |
| TKT-8004 | CSV exports for enrollment reports contain malformed UTF-8 characters. Affects downstream systems. |
| TKT-8005 | Admin portal returns 500 error when attempting to invite new users. Seat count shows 12/20. |

## Knowledge base index

| ID | Title | Category | Views | Helpfulness |
|----|-------|----------|-------|-------------|
| KB-101 | Optimizing Dashboard Performance for Large Datasets | performance | 1,842 | 87% |
| KB-102 | SSO Certificate Rotation Guide | authentication | 956 | 92% |
| KB-103 | API Rate Limits and Bulk Import Best Practices | api | 2,103 | 78% |
| KB-104 | Troubleshooting CSV Export Encoding Issues | data_export | 634 | 81% |
| KB-105 | User Management and Invitation Troubleshooting | user_management | 1,247 | 74% |
| KB-106 | SAML 2.0 Configuration Reference | authentication | 712 | 89% |

Category coverage: `authentication` is the only category with two articles
(KB-102 and KB-106). `performance`, `api`, `data_export`, and
`user_management` have exactly one each. No other category exists.
