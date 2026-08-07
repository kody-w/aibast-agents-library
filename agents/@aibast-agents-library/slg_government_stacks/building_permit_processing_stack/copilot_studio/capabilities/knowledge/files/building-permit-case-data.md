# Building Permit Case Data

> SYNTHETIC — DEMO DATA. Every applicant, parcel, address, permit, inspector,
> and inspection date in this document is fictional. This file exists so the
> agent has a working world to answer from on day one. In production, replace
> this file with tools that read your real permitting system and inspection
> calendar (see the README's production section).

## Permit applications

| Permit ID | Applicant | Property Address | Parcel ID | Type | Submitted | Valuation | Zoning District | Status | Assigned Reviewer | Review Cycle |
|---|---|---|---|---|---|---|---|---|---|---|
| BP-2025-0101 | Greenfield Development LLC | 4520 Oak Ridge Blvd | 045-221-009 | new_construction | 2025-01-15 | $4,200,000 | MU-2 (Mixed Use) | plan_review | Karen Whitfield | 2 |
| BP-2025-0102 | Johnson Family Trust | 812 Maple Street | 023-114-003 | residential_addition | 2025-02-03 | $185,000 | R-1 (Single Family Residential) | approved | Tom Delgado | 1 |
| BP-2025-0103 | Sunrise Solar Inc. | 1100 Industrial Pkwy | 067-340-015 | commercial_alteration | 2025-02-20 | $320,000 | I-1 (Light Industrial) | inspection_scheduled | Karen Whitfield | 1 |
| BP-2025-0104 | Metro School District | 2200 Education Way | 034-502-001 | institutional | 2025-01-28 | $6,800,000 | PF (Public Facilities) | corrections_required | Tom Delgado | 3 |

Total applications on file: 4. Total valuation: $11,505,000.

## Project descriptions

| Permit ID | Description |
|---|---|
| BP-2025-0101 | 3-story mixed-use building — 12 residential units, ground floor retail |
| BP-2025-0102 | 650 sq ft second-story addition to single-family residence |
| BP-2025-0103 | Rooftop solar installation — 240 panel array on warehouse |
| BP-2025-0104 | New gymnasium and cafeteria wing — 18,000 sq ft |

## Status values

| Status | Rendered | Meaning |
|---|---|---|
| plan_review | Plan Review | Under examination by the assigned reviewer |
| corrections_required | Corrections Required | Returned to the applicant; a plans examiner must clear it |
| approved | Approved | Plan review complete |
| inspection_scheduled | Inspection Scheduled | Approved and on the inspection calendar |

## Inspector roster

| Inspector | Specialty | Available Slots | Zone |
|---|---|---|---|
| Dave Martinez | Electrical | 3 | East |
| Lisa Park | Structural | 2 | East |
| Carlos Reyes | Plumbing/Mechanical | 4 | West |
| Ann Kowalski | Fire/Life Safety | 2 | All |

`Available Slots` is remaining capacity, not work already booked. Zone `All`
means the inspector is not zone-restricted.

## Scheduled inspections

### BP-2025-0103 — 1100 Industrial Pkwy

| Type | Inspector | Date | Status |
|---|---|---|---|
| Electrical Rough-In | Dave Martinez | 2025-03-20 | Scheduled |
| Structural Mounting | Lisa Park | 2025-03-22 | Scheduled |
| Final Electrical | Dave Martinez | 2025-04-05 | Pending |

BP-2025-0103 is the only permit with inspections on the calendar. BP-2025-0101,
BP-2025-0102, and BP-2025-0104 have none scheduled.
