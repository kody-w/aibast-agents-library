# SLA and Escalation Policy

> SYNTHETIC — DEMO DATA. Every threshold, benchmark, team, and manager in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real SLA policy, analytics warehouse, and on-call escalation directory
> (see the README's production section).

## SLA thresholds by severity

| Severity | First Response (hrs) | Resolution (hrs) |
|----------|----------------------|------------------|
| P1 | 1 | 4 |
| P2 | 4 | 24 |
| P3 | 8 | 72 |
| P4 | 24 | 168 |

These are the only SLA targets. A severity outside P1-P4 has no threshold and
must be reported as unrecorded, not estimated.

## Resolution benchmarks by category

| Category | Avg Resolution (hrs) | First-Contact Resolution |
|----------|----------------------|--------------------------|
| performance | 18.4 | 32% |
| authentication | 3.2 | 45% |
| api | 12.6 | 58% |
| data_export | 22.1 | 28% |
| user_management | 6.8 | 65% |

`data_export` is the slowest category (22.1h average) and has the lowest
first-contact resolution rate (28%). `authentication` resolves fastest at 3.2h.
`user_management` has the highest first-contact resolution rate at 65%.

## Escalation matrix

| Current Team | Escalates To | Manager |
|--------------|--------------|---------|
| Tier 1 - General | Tier 2 - Specialist | Rachel Torres |
| Tier 2 - Backend | Tier 3 - Engineering | David Kim |
| Tier 2 - Data | Tier 3 - Engineering | David Kim |
| Tier 3 - Security | VP Engineering | Samira Patel |
| Tier 3 - Engineering | VP Engineering | Samira Patel |

`Tier 2 - Specialist` appears only as a destination and has no route of its
own. A team with no row here has an undefined route and is reported as `N/A`.

## Triage ordering rule

Tickets rank by severity first (P1, P2, P3, P4), then by ARR descending within
the same severity. ARR never promotes a ticket across severity boundaries.

## Knowledge base ranking rule

Articles rank by helpfulness descending. View count is reported but never used
to rank.
