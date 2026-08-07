# ICP Scoring, Routing, and SLA Policy

> SYNTHETIC — DEMO DATA. The ICP weights, AE roster, and SLA rules below are a
> fictional configuration. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real scoring model, territory rules, and SLA engine.

## ICP fit score (0-100)

Five weighted components. The weights are fixed and sum to 1.00.

| Component | Weight |
|-----------|--------|
| Company size | 0.20 |
| Industry | 0.25 |
| Tech fit | 0.20 |
| Budget | 0.20 |
| Authority | 0.15 |

`icp_score = size*0.20 + industry*0.25 + tech*0.20 + budget*0.20 + authority*0.15`,
clamped to 0-100 and truncated to an integer.

### Size sub-score

- Ideal band is 200-10,000 employees inclusive: score 100.
- Below 200: `max(10, int(employees / 200 * 100))`.
- Above 10,000: `max(40, 100 - int((employees - 10000) / 200))`.

### Industry sub-score

100 if the industry is one of Technology, Financial Services, Healthcare,
Manufacturing, SaaS. Otherwise 30. Logistics, Energy, Education, Professional
Services, and Retail all score 30.

### Tech fit sub-score

Ideal tech list: Salesforce, AWS, Snowflake, Kubernetes, Databricks, Azure (6 items).

`tech = min(100, int(overlap / 6 * 150))`

| Overlapping tools | Tech sub-score |
|-------------------|----------------|
| 0 | 0 |
| 1 | 25 |
| 2 | 50 |
| 3 | 75 |
| 4 or more | 100 |

### Budget and authority sub-scores (ICP)

| Budget status | ICP sub-score |
|---------------|---------------|
| confirmed | 100 |
| planned | 70 |
| exploring | 40 |
| tbd | 20 |

| Authority level | ICP sub-score |
|-----------------|---------------|
| C-Level | 100 |
| VP | 85 |
| Director | 70 |
| Manager | 50 |
| Individual | 30 |

## BANT composite (0-100)

Each dimension is scored independently, then combined:

`bant_composite = int(B*0.30 + A*0.25 + N*0.25 + T*0.20)`

| Budget status | B |
|---------------|---|
| confirmed | 95 |
| planned | 70 |
| exploring | 40 |
| tbd | 15 |

| Authority level | A |
|-----------------|---|
| C-Level | 95 |
| VP | 80 |
| Director | 60 |
| Manager | 40 |
| Individual | 20 |

Need: `N = min(100, 50 + len(need_text) // 3 + count(engagement_signals) * 8)`

| Timeline text | T |
|---------------|---|
| contains "60" or "Q1" | 90 |
| contains "90" | 70 |
| contains "Q2" | 55 |
| anything else (Q3) | 25 |

## Tier thresholds

`combined_score = int(icp_score * 0.55 + bant_composite * 0.45)`

| Combined score | Tier | Recommended action |
|----------------|------|--------------------|
| 88-100 | Hot | Immediate AE handoff |
| 73-87 | Warm | SDR qualification call |
| 55-72 | Nurture | Automated email sequence |
| 0-54 | Disqualified | Marketing nurture list |

Leads are always ranked by `combined_score` descending.

## Account executive team

| AE | Territory | Specialty | Current capacity | Max leads |
|----|-----------|-----------|------------------|-----------|
| Mike Rodriguez | West | Enterprise Tech | 62% | 12 |
| Sarah Kim | East | Healthcare / FinServ | 55% | 14 |
| James Chen | Central | Manufacturing / Industrial | 70% | 10 |
| Lisa Park | West | Mid-Market SaaS | 48% | 15 |
| David Okafor | East | Enterprise FinServ | 58% | 12 |

These five are the entire team. Never route a lead to anyone else.

## SLA and escalation rules

| Lead tier | Response SLA | Escalation | Sequence |
|-----------|--------------|------------|----------|
| Hot | 4h | Manager alert + Slack DM | Immediate call + personalized email |
| Warm | 24h | Team channel alert | Personalized email day 0, call day 1 |
| Nurture | 48h | Weekly digest flag | 3-email drip over 10 days |
| Disqualified | N/A (0h) | None — routed to marketing | Marketing nurture list |

## Pipeline value convention

Estimated pipeline value for a lead is `int(company_revenue * 0.001)`. Only Hot
and Warm leads count toward qualified pipeline.
