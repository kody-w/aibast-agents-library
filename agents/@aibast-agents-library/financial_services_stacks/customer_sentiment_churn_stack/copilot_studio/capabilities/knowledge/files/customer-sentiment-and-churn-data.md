# Customer Sentiment and Churn Data

> SYNTHETIC — DEMO DATA. Every customer, interaction, and score in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real CRM, survey platform, and interaction history (see the README's
> production section).

## Customer profiles

| ID | Name | Segment | Tenure (yrs) | Products | Product Count | NPS | Last Survey | Monthly Transactions | Digital Engagement | Complaints (12m) |
|----|------|---------|--------------|----------|---------------|-----|-------------|----------------------|--------------------|------------------|
| CUST-8001 | Elizabeth Warren-Hayes | affluent | 12 | checking, savings, mortgage, investment | 4 | 9 | 2025-02-01 | 48 | 72 | 0 |
| CUST-8002 | Marcus Johnson | mass_market | 3 | checking, credit_card | 2 | 4 | 2025-01-15 | 15 | 35 | 5 |
| CUST-8003 | Priya Sharma | emerging_affluent | 5 | checking, savings, credit_card, auto_loan | 4 | 7 | 2025-02-20 | 32 | 88 | 1 |
| CUST-8004 | Gerald Thompson | mass_market | 8 | checking | 1 | 3 | 2024-11-01 | 4 | 12 | 2 |
| CUST-8005 | Diana Castellano | small_business | 6 | business_checking, business_credit, merchant_services | 3 | 6 | 2025-01-10 | 120 | 55 | 3 |

## Interaction log

Ten logged interactions across the five customers. Each customer's entries are
stored newest first.

| Customer | Date | Channel | Type | Sentiment |
|----------|------|---------|------|-----------|
| CUST-8001 | 2025-02-15 | branch | inquiry | positive |
| CUST-8001 | 2025-01-20 | phone | account_service | neutral |
| CUST-8002 | 2025-03-01 | phone | complaint | negative |
| CUST-8002 | 2025-02-10 | chat | fee_dispute | negative |
| CUST-8002 | 2025-01-25 | phone | complaint | negative |
| CUST-8003 | 2025-02-28 | mobile | transfer | neutral |
| CUST-8003 | 2025-02-05 | email | inquiry | positive |
| CUST-8004 | 2024-12-15 | branch | withdrawal | neutral |
| CUST-8005 | 2025-02-20 | phone | fee_dispute | negative |
| CUST-8005 | 2025-01-30 | branch | inquiry | neutral |

Distribution: positive 2, neutral 4, negative 4, of 10 total.

## Segment benchmarks

| Segment | Avg NPS | Avg Products | Avg Tenure | Avg Transactions |
|---------|---------|--------------|------------|------------------|
| affluent | 8.2 | 4.1 | 10 yrs | 55/mo |
| emerging_affluent | 7.0 | 3.2 | 5 yrs | 35/mo |
| mass_market | 6.5 | 2.0 | 4 yrs | 20/mo |
| small_business | 6.8 | 3.0 | 5 yrs | 90/mo |

Only NPS and product depth are compared against benchmark in the segment
analysis. Tenure and transaction benchmarks are published for reference.
