# Routing and SLA Policy

> SYNTHETIC — DEMO DATA. Every department, SLA, and response standard in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real routing configuration and SLA policy (see the README's production
> section).

## Category routing table

Ten categories are routed. A category outside this table has no department and
no SLA — it is routed manually, never inferred from a similar category.

| Category | Department | SLA (days) | Default Priority |
|---|---|---|---|
| Pothole Repair | Public Works — Streets Division | 7 | High |
| Streetlight Outage | Public Works — Electrical | 14 | Medium |
| Trash Collection Missed | Sanitation Services | 2 | Medium |
| Graffiti Removal | Parks & Recreation | 14 | Low |
| Water Main Break | Water & Sewer — Emergency | 1 | Critical |
| Sidewalk Damage | Public Works — Streets Division | 21 | Low |
| Noise Complaint | Code Enforcement | 3 | Medium |
| Abandoned Vehicle | Police — Non-Emergency | 7 | Low |
| Tree Hazard | Public Works — Urban Forestry | 5 | High |
| Illegal Dumping | Sanitation Services | 7 | Medium |

Departments are shared across categories with different SLAs: Public Works —
Streets Division owns both Pothole Repair (7 days) and Sidewalk Damage (21
days); Sanitation Services owns both Trash Collection Missed (2 days) and
Illegal Dumping (7 days). The SLA belongs to the category, not the department.

## SLA response standards by priority

| Priority | Response Time | Resolution Target |
|---|---|---|
| Critical | 4 hours | 1 day |
| High | 24 hours | 7 days |
| Medium | 48 hours | 14 days |
| Low | 72 hours | 21 days |

The priority resolution target and the category SLA can differ (Tree Hazard is
default High, whose priority target is 7 days, while the category SLA is 5
days). When routing a specific report, quote the category SLA and name the
priority standard separately.

## Assignment state

Routing a request to a department is not the same as assigning it to a crew. A
request can carry a department and still show `Unassigned`. In the current
queue, SR-2025-10004 is the only request awaiting assignment; it is routed to
Parks & Recreation with an SLA target of 2025-03-19.
