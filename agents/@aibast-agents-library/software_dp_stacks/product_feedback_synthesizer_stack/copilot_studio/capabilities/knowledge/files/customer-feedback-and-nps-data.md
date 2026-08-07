# Customer Feedback and NPS Data

> SYNTHETIC — DEMO DATA. Every customer, feedback entry, score, and NPS figure
> in this document is fictional. This file exists so the agent has a working
> world to answer from on day one. In production, replace this file with tools
> that read your real support, survey, and CRM systems (see the README's
> production section).

## Feedback entries

| ID | Customer | Channel | Date | Category | Sentiment | Score | ARR Impact |
|----|----------|---------|------|----------|-----------|-------|------------|
| FB-5001 | Meridian Healthcare Systems | support_ticket | 2026-02-14 | usability | negative | 2 | $186,000 |
| FB-5002 | Apex Financial Group | nps_survey | 2026-02-20 | feature_gap | neutral | 6 | $240,000 |
| FB-5003 | Skyline Hospitality Group | qbr | 2026-03-01 | praise | positive | 9 | $360,000 |
| FB-5004 | Vanguard Logistics | support_ticket | 2026-01-28 | bug_report | negative | 1 | $84,000 |
| FB-5005 | BrightPath Education | in_app | 2026-03-05 | feature_gap | neutral | 5 | $96,000 |
| FB-5006 | Orion Manufacturing | sales_call | 2026-03-10 | feature_gap | positive | 8 | $312,000 |

Six entries. Average satisfaction score 5.2 of 10. Total ARR represented
$1,278,000.

## Feedback text

| ID | Verbatim |
|----|----------|
| FB-5001 | The dashboard takes too many clicks to get to key metrics. We need a customizable home view. |
| FB-5002 | Product is solid but missing real-time alerting capabilities that competitors offer. |
| FB-5003 | Integration with our POS system has been seamless. Would love to see mobile app improvements. |
| FB-5004 | Data export fails consistently for reports over 10K rows. This is blocking our migration. |
| FB-5005 | Need role-based access controls for student data. Currently everyone sees everything. |
| FB-5006 | Great product overall. If you add workflow automation we would double our seat count. |

Reports quote the **first 80 characters** of the verbatim followed by `...`.

## NPS trend

| Quarter | Promoters | Passives | Detractors | NPS |
|---------|-----------|----------|------------|-----|
| 2025-Q4 | 142 | 88 | 45 | 35 |
| 2026-Q1 | 158 | 91 | 51 | 36 |

The NPS value is recorded per quarter, not derived from the promoter and
detractor counts at read time.

## Vocabularies

| Field | Allowed values |
|-------|----------------|
| sentiment | positive, neutral, negative |
| category | usability, feature_gap, praise, bug_report |
| channel | support_ticket, nps_survey, qbr, in_app, sales_call |
| score | 1-10, recorded per entry |
