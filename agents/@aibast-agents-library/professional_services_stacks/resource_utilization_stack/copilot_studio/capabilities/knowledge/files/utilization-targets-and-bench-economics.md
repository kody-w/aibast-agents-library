# Utilization Targets and Bench Economics

> SYNTHETIC — DEMO DATA. These targets, cost figures, and planning assumptions
> are fictional. This file exists so the agent has a working world to answer
> from on day one. In production, replace this file with tools that read your
> real finance and resource management systems (see the README's production
> section).

## Utilization targets by level

| Level | Target Utilization |
|-------|--------------------|
| Senior | 85% |
| Manager | 80% |
| Mid | 80% |
| Junior | 75% |
| Firm (all levels) | 85% |

A level is `On Track` only when its average utilization is greater than or
equal to its target; otherwise it is `Below Target`.

## Fully burdened bench cost by level

| Level | Monthly Bench Cost |
|-------|--------------------|
| Senior | $22,000 |
| Manager | $25,000 |
| Mid | $14,000 |
| Junior | $10,000 |
| Unrecognized level (fallback) | $14,000 |

## Current bench economics

| ID | Consultant | Level | Monthly Cost | Rate/Hr | Days on Bench |
|----|------------|-------|--------------|---------|---------------|
| CON-404 | David Okafor | Mid | $14,000 | $175 | est. 30+ |
| CON-405 | Sarah Kim | Mid | $14,000 | $185 | est. 30+ |
| CON-406 | James Wright | Junior | $10,000 | $125 | est. 30+ |
| CON-408 | Robert Garcia | Mid | $14,000 | $195 | est. 30+ |
| CON-410 | Chen Wei | Senior | $22,000 | $295 | est. 30+ |

Monthly bench cost $74,000. Annualized $888,000. Days on bench is only ever
recorded as `est. 30+` - the data carries no precise bench start date.

## Skill inventory sitting on the bench

| Skill | Available |
|-------|-----------|
| Data Analytics | 1 |
| Power BI | 1 |
| SQL | 1 |
| Cloud Architecture | 1 |
| AWS | 1 |
| Terraform | 1 |
| Business Analysis | 1 |
| Requirements | 1 |
| Jira | 1 |
| ERP | 1 |
| D365 | 1 |
| Integration | 1 |
| AI/ML | 1 |
| Python | 1 |
| Azure ML | 1 |

## Planning assumptions

| Assumption | Value | Used for |
|------------|-------|----------|
| Billable hours per month | 160 | Revenue opportunity if bench is deployed: sum of bench hourly rates x 160 = $156,000/month |
| Weighted utilization factor | 0.87 | Projected firm utilization after deployment: (billable + matches) / headcount x 100 x 0.87 |
| Capacity forecast horizon | 2026-06-30 | Which engagements count as "ending in the next 90 days" |

Both factors are assumptions, not commitments. State them whenever the derived
figure is challenged.
