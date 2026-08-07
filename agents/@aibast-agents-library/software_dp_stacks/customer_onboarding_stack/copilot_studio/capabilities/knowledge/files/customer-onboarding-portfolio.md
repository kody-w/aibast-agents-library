# Customer Onboarding Portfolio

> SYNTHETIC — DEMO DATA. Every customer, CSM, ARR figure, and metric in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real CRM, onboarding tracker, and product telemetry (see the README's
> production section).

## Customer master

| ID | Customer | Plan | ARR | CSM | Onboarding Start | Target Go-Live | Health Score |
|----|----------|------|-----|-----|------------------|----------------|--------------|
| CUST-1001 | Meridian Healthcare Systems | Enterprise | $186,000 | Priya Sharma | 2026-01-15 | 2026-03-31 | 72 |
| CUST-1002 | Apex Financial Group | Enterprise | $240,000 | Marcus Chen | 2026-02-01 | 2026-04-15 | 89 |
| CUST-1003 | Vanguard Logistics | Professional | $84,000 | Priya Sharma | 2025-12-10 | 2026-02-28 | 38 |
| CUST-1004 | BrightPath Education | Professional | $96,000 | Marcus Chen | 2026-02-20 | 2026-04-30 | 81 |
| CUST-1005 | Orion Manufacturing | Enterprise | $312,000 | Priya Sharma | 2026-03-01 | 2026-05-15 | 91 |

Total pipeline ARR: $918,000 across 5 customers.

## Milestone matrix

Statuses are `complete`, `in_progress`, `not_started`, or `blocked`. Completion
dates exist only for `complete`. The sequence is fixed: kickoff_complete,
sso_configured, data_migration, integration_setup, user_training, go_live.

| ID | Customer | kickoff_complete | sso_configured | data_migration | integration_setup | user_training | go_live |
|----|----------|------------------|----------------|----------------|-------------------|---------------|---------|
| CUST-1001 | Meridian Healthcare Systems | complete (2026-01-18) | complete (2026-01-25) | complete (2026-02-10) | in_progress | not_started | not_started |
| CUST-1002 | Apex Financial Group | complete (2026-02-03) | complete (2026-02-08) | complete (2026-02-20) | complete (2026-03-05) | in_progress | not_started |
| CUST-1003 | Vanguard Logistics | complete (2025-12-13) | complete (2025-12-20) | blocked | not_started | not_started | not_started |
| CUST-1004 | BrightPath Education | complete (2026-02-22) | complete (2026-03-01) | in_progress | not_started | not_started | not_started |
| CUST-1005 | Orion Manufacturing | complete (2026-03-03) | in_progress | not_started | not_started | not_started | not_started |

### Derived milestone position

| ID | Customer | Completed | Progress | Blocked | Next Milestone |
|----|----------|-----------|----------|---------|----------------|
| CUST-1001 | Meridian Healthcare Systems | 3/6 | 50.0% | None | integration_setup |
| CUST-1002 | Apex Financial Group | 4/6 | 66.7% | None | user_training |
| CUST-1003 | Vanguard Logistics | 2/6 | 33.3% | data_migration | integration_setup |
| CUST-1004 | BrightPath Education | 2/6 | 33.3% | None | data_migration |
| CUST-1005 | Orion Manufacturing | 1/6 | 16.7% | None | sso_configured |

No blocker reason, owner, or ETA is recorded for a blocked milestone.

## Feature adoption

Adoption is a percentage per feature. The average is the unweighted mean of the
five features.

| ID | Customer | Dashboard | Reporting | Api Access | Automation Rules | Custom Fields | Avg Adoption |
|----|----------|-----------|-----------|------------|------------------|---------------|--------------|
| CUST-1001 | Meridian Healthcare Systems | 88% | 62% | 45% | 12% | 33% | 48.0% |
| CUST-1002 | Apex Financial Group | 95% | 81% | 72% | 55% | 68% | 74.2% |
| CUST-1003 | Vanguard Logistics | 55% | 20% | 0% | 0% | 10% | 17.0% |
| CUST-1004 | BrightPath Education | 78% | 45% | 22% | 5% | 30% | 36.0% |
| CUST-1005 | Orion Manufacturing | 40% | 15% | 10% | 0% | 5% | 14.0% |

## Training and seat activation

| ID | Customer | Training Completion | Active Users | Licensed Users | Activation |
|----|----------|---------------------|--------------|----------------|------------|
| CUST-1001 | Meridian Healthcare Systems | 41% | 28 | 75 | 37.3% |
| CUST-1002 | Apex Financial Group | 73% | 92 | 120 | 76.7% |
| CUST-1003 | Vanguard Logistics | 15% | 8 | 40 | 20.0% |
| CUST-1004 | BrightPath Education | 28% | 15 | 35 | 42.9% |
| CUST-1005 | Orion Manufacturing | 8% | 12 | 200 | 6.0% |

## Not in this data set

NPS, support tickets, renewal or contract dates, invoice and payment status,
per-user activity, time-series or trend history, competitor context, and
executive sponsor names. If a question needs any of these, say the data set does
not contain it rather than estimating.
