# Grants Portfolio Data

> SYNTHETIC — DEMO DATA. Every grant, grantor, award amount, and reporting
> deadline in this document is fictional. This file exists so the agent has a
> working world to answer from on day one. In production, replace this file with
> tools that read your real grants module, ERP fund ledger, and reporting
> tracker (see the README's production section).

## Grants portfolio

| Grant ID | Title | Grantor | Amount | Match Required | Local Match | Start Date | End Date | Status | Department | Spent | Encumbered |
|----------|-------|---------|--------|----------------|-------------|------------|----------|--------|------------|-------|------------|
| LG-2025-001 | Community Policing Initiative Grant | State Dept. of Justice | $475,000 | 25% | $118,750 | 2024-07-01 | 2026-06-30 | active | Police Department | $198,000 | $52,000 |
| LG-2025-002 | Clean Water Infrastructure Improvement | EPA — State Revolving Fund | $2,800,000 | 20% | $560,000 | 2025-01-01 | 2027-12-31 | active | Public Works | $140,000 | $825,000 |
| LG-2025-003 | Youth Employment Summer Program | State Dept. of Labor | $165,000 | 10% | $16,500 | 2025-04-01 | 2025-09-30 | pending_award | Parks & Recreation | $0 | $0 |
| LG-2025-004 | Broadband Expansion — Underserved Areas | NTIA — BEAD Program | $1,250,000 | 25% | $312,500 | 2025-03-01 | 2028-02-28 | application_submitted | IT Department | $0 | $0 |
| LG-2025-005 | Historic Downtown Revitalization | State Historic Preservation Office | $380,000 | 50% | $190,000 | 2024-10-01 | 2026-09-30 | active | Community Development | $142,500 | $67,000 |

### Portfolio totals

Derived from the table above; `available = total awards - spent - encumbered`.

| Measure | Amount |
|---------|--------|
| Total Awards | $5,070,000 |
| Local Match Committed | $1,197,750 |
| Spent | $480,500 |
| Encumbered | $944,000 |
| Available | $3,645,500 |

### Derived per-grant balances

`available = amount - spent - encumbered`;
`burn rate = (spent + encumbered) / amount`.

| Grant ID | Amount | Spent | Encumbered | Available | Burn Rate | Status |
|----------|--------|-------|------------|-----------|-----------|--------|
| LG-2025-001 | $475,000 | $198,000 | $52,000 | $225,000 | 52.6% | active |
| LG-2025-002 | $2,800,000 | $140,000 | $825,000 | $1,835,000 | 34.5% | active |
| LG-2025-003 | $165,000 | $0 | $0 | $165,000 | 0.0% | pending_award |
| LG-2025-004 | $1,250,000 | $0 | $0 | $1,250,000 | 0.0% | application_submitted |
| LG-2025-005 | $380,000 | $142,500 | $67,000 | $170,500 | 55.1% | active |

LG-2025-003 and LG-2025-004 have not been awarded. Their $0 spend is an
un-started award, not missing data.

## Reporting requirements

Reporting requirements exist for three grants only. LG-2025-003 and LG-2025-004
have no reporting schedule on file.

### LG-2025-001 — Community Policing Initiative Grant

| Report | Due Date | Status |
|--------|----------|--------|
| Quarterly Financial Report | 2025-04-15 | upcoming |
| Semi-Annual Performance Report | 2025-07-31 | upcoming |
| Annual Single Audit (if applicable) | 2025-12-31 | upcoming |

### LG-2025-002 — Clean Water Infrastructure Improvement

| Report | Due Date | Status |
|--------|----------|--------|
| Monthly Draw Request | 2025-04-10 | upcoming |
| Quarterly Progress Report | 2025-04-30 | upcoming |
| Davis-Bacon Certified Payroll | 2025-04-07 | upcoming |

### LG-2025-005 — Historic Downtown Revitalization

| Report | Due Date | Status |
|--------|----------|--------|
| Quarterly Expenditure Report | 2025-04-15 | upcoming |
| Photo Documentation Update | 2025-06-30 | upcoming |
| Historic Preservation Compliance Review | 2025-09-30 | upcoming |

### All reports, sorted by due date

Nine reports across three grants. Ties on 2025-04-15 keep source order
(LG-2025-001 before LG-2025-005).

| Due Date | Grant | Report |
|----------|-------|--------|
| 2025-04-07 | LG-2025-002 | Davis-Bacon Certified Payroll |
| 2025-04-10 | LG-2025-002 | Monthly Draw Request |
| 2025-04-15 | LG-2025-001 | Quarterly Financial Report |
| 2025-04-15 | LG-2025-005 | Quarterly Expenditure Report |
| 2025-04-30 | LG-2025-002 | Quarterly Progress Report |
| 2025-06-30 | LG-2025-005 | Photo Documentation Update |
| 2025-07-31 | LG-2025-001 | Semi-Annual Performance Report |
| 2025-09-30 | LG-2025-005 | Historic Preservation Compliance Review |
| 2025-12-31 | LG-2025-001 | Annual Single Audit (if applicable) |
