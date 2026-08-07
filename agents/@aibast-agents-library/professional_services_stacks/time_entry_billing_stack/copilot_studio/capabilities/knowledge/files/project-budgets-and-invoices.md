# Project Budgets and Invoice History

> SYNTHETIC — DEMO DATA. Every project, client, budget figure, and invoice in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real project accounting and accounts receivable systems (see the
> README's production section).

## Project budgets

Catalog order. `Budget Used` is `Billed to Date / Total Budget`; `Status` uses
the fixed thresholds CRITICAL at 95% or above, WARNING at 80% or above,
otherwise OK.

| Project | Client | Contract Type | Total Budget | Billed to Date | Remaining | Budget Used | Status |
|---------|--------|---------------|--------------|----------------|-----------|-------------|--------|
| TechCorp Transformation | TechCorp Industries | T&M | $850,000 | $682,400 | $167,600 | 80.3% | WARNING |
| Apex Analytics Platform | Apex Manufacturing | T&M | $520,000 | $398,000 | $122,000 | 76.5% | OK |
| Pinnacle Energy ERP | Pinnacle Energy | Fixed Fee | $1,200,000 | $744,000 | $456,000 | 62.0% | OK |
| Atlas Security Audit | Atlas Financial Group | T&M | $185,000 | $156,600 | $28,400 | 84.6% | WARNING |
| Metro Transit Portal | Metro Transit Authority | T&M | $340,000 | $218,000 | $122,000 | 64.1% | OK |

Pinnacle Energy ERP is the only Fixed Fee engagement; hours-times-rate on that
project is work value, not an automatically invoiceable amount.

## Invoice history — cycle dated 2026-02-28

| Invoice | Client | Amount | Date | Status | Days Outstanding |
|---------|--------|--------|------|--------|------------------|
| INV-2026-201 | TechCorp Industries | $142,500.00 | 2026-02-28 | paid | 0 |
| INV-2026-202 | Apex Manufacturing | $98,800.00 | 2026-02-28 | paid | 0 |
| INV-2026-203 | Pinnacle Energy | $186,000.00 | 2026-02-28 | outstanding | 17 |
| INV-2026-204 | Atlas Financial Group | $52,200.00 | 2026-02-28 | outstanding | 17 |
| INV-2026-205 | Metro Transit Authority | $46,200.00 | 2026-02-28 | overdue | 45 |

- Total billed last cycle: **$525,700.00**
- Total collected (status `paid`): **$241,300.00**
- Collection rate: **45.9%**
- Total outstanding (every status other than `paid`): **$284,400.00**

INV-2026-205 is the only overdue invoice at 45 days.
