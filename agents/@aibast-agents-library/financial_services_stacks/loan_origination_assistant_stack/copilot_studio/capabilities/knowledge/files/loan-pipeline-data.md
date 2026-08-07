# Loan Origination Pipeline Data

> SYNTHETIC — DEMO DATA. Every applicant, property, and loan file in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real loan origination system and pricing engine (see the README's
> production section).

## Loan application pipeline

| App ID | Applicant | Loan Type | Purpose | Property Address | Property Value | Loan Amount | Credit Score | Annual Income | Monthly Debt | Employment Yrs | Down Payment % | Status | Loan Officer |
|--------|-----------|-----------|---------|------------------|----------------|-------------|--------------|---------------|--------------|----------------|----------------|--------|--------------|
| LA-2025-4001 | Thomas & Rebecca Harper | conventional_30yr | purchase | 742 Evergreen Terrace, Springfield | $485,000 | $388,000 | 762 | $142,000 | $1,850 | 8 | 20.0 | underwriting | Diana Cruz |
| LA-2025-4002 | Kevin Nguyen | fha_30yr | purchase | 1200 Oak Park Ave, Unit 4B | $275,000 | $265,375 | 648 | $68,000 | $890 | 3 | 3.5 | document_review | Mark Peterson |
| LA-2025-4003 | Westfield Properties LLC | commercial_5yr | refinance | 8800 Industrial Blvd | $2,400,000 | $1,680,000 | 0 (N/A, commercial) | $580,000 | $22,000 | 0 | 30.0 | credit_review | Diana Cruz |
| LA-2025-4004 | Sandra Blake | va_30yr | purchase | 555 Freedom Way | $340,000 | $340,000 | 710 | $95,000 | $650 | 12 | 0.0 | approved | Mark Peterson |

Pipeline volume (sum of loan amounts): **$2,673,375** across **4** applications.

LA-2025-4003 is the only file carrying a DSCR: **1.42**.

## Derived metrics

Computed from the fields above using the credit-analysis formulas — LTV from
loan amount over property value, P&I from the product rate at 360 payments
(60 for `commercial_5yr`), DTI from monthly debt plus P&I over monthly income.

| App ID | Monthly Income | Term (payments) | Monthly P&I | DTI | LTV |
|--------|----------------|-----------------|-------------|-----|-----|
| LA-2025-4001 | $11,833.33 | 360 | $2,548.88 | 37.2% | 80.0% |
| LA-2025-4002 | $5,666.67 | 360 | $1,677.35 | 45.3% | 96.5% |
| LA-2025-4003 | $48,333.33 | 60 | $33,663.75 | 115.2% | 70.0% |
| LA-2025-4004 | $7,916.67 | 360 | $2,093.44 | 34.7% | 100.0% |

DTI for `commercial_5yr` is informational only — commercial files carry no DTI
gate. See the underwriting criteria document.

## Rate sheet

| Product | Rate | APR | Points |
|---------|------|-----|--------|
| conventional_30yr | 6.875% | 7.012% | 0.5 |
| fha_30yr | 6.500% | 7.250% | 0.0 |
| va_30yr | 6.250% | 6.485% | 0.0 |
| commercial_5yr | 7.500% | 7.750% | 1.0 |

Product-specific fees recorded alongside the rate sheet, not shown as rate
table columns:

| Product | Fee | Value |
|---------|-----|-------|
| fha_30yr | Upfront MIP | 1.75% |
| fha_30yr | Annual MIP | 0.55% |
| va_30yr | Funding fee | 2.15% |

## Statuses in use

`underwriting`, `document_review`, `credit_review`, `approved`. Status is the
recorded state of the file; the agent never changes it.
