# Citizen Service Request Data

> SYNTHETIC — DEMO DATA. Every request, resident, address, ward, and crew in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real 311 / service request system (see the README's production
> section).

## Service request queue

| SR ID | Category | Location | Ward | Priority | Status | Department | Assigned To | SLA Target |
|---|---|---|---|---|---|---|---|---|
| SR-2025-10001 | Pothole Repair | 142 Main Street | 3 | High | Assigned | Public Works — Streets Division | Crew 7-B | 2025-03-07 |
| SR-2025-10002 | Streetlight Outage | Pine St & Oak Ave | 5 | Medium | In Progress | Public Works — Electrical | Tech Unit 3 | 2025-03-15 |
| SR-2025-10003 | Trash Collection Missed | 2847 Elm Drive | 2 | Medium | Resolved | Sanitation Services | Route 12-A | 2025-03-06 |
| SR-2025-10004 | Graffiti Removal | Riverside Park — east entrance | 4 | Low | Pending | Parks & Recreation | Unassigned | 2025-03-19 |
| SR-2025-10005 | Water Main Break | 600 block of Washington Blvd | 1 | Critical | In Progress | Water & Sewer — Emergency | Emergency Crew Alpha | 2025-03-07 |

## Intake detail

| SR ID | Submitted | Submitter | Channel | Description |
|---|---|---|---|---|
| SR-2025-10001 | 2025-02-28 | Maria Gonzalez | Web Portal | Large pothole on Main St between 3rd and 4th Ave, approximately 18 inches wide |
| SR-2025-10002 | 2025-03-01 | David Kim | Phone 311 | Streetlight at intersection of Pine and Oak has been out for 2 weeks |
| SR-2025-10003 | 2025-03-04 | Linda Park | Mobile App | Missed residential trash pickup on scheduled collection day (Tuesday) |
| SR-2025-10004 | 2025-03-05 | Anonymous | Web Portal | Graffiti on retaining wall along Riverside Park walking path |
| SR-2025-10005 | 2025-03-06 | James Walker | Phone 311 | Water bubbling up from street surface near fire hydrant, flooding sidewalk |

## Resolutions

| SR ID | Resolved Date | SLA Target | SLA Met | Resolution |
|---|---|---|---|---|
| SR-2025-10003 | 2025-03-05 | 2025-03-06 | Yes | Special pickup completed. Route schedule updated to prevent recurrence. |

No other request in the queue carries a resolved date or a resolution text.

## Queue metrics

| Metric | Value | How it is computed |
|---|---|---|
| Total requests | 5 | count of the queue |
| Resolved | 1 | status is exactly `resolved` |
| Resolution rate | 20.0% | resolved / total, one decimal |
| SLA compliance | 100.0% | resolved requests closed on or before their SLA target, over resolved |

## Volume by category

| Category | Requests |
|---|---|
| Pothole Repair | 1 |
| Streetlight Outage | 1 |
| Trash Collection Missed | 1 |
| Graffiti Removal | 1 |
| Water Main Break | 1 |

## Volume by ward

| Ward | Requests |
|---|---|
| Ward 1 | 1 |
| Ward 2 | 1 |
| Ward 3 | 1 |
| Ward 4 | 1 |
| Ward 5 | 1 |
