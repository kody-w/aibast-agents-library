<!-- Generated from the original workshop knowledge; edit the source and regenerate. -->
> Retained synthetic knowledge. Listed entity fields come from the SharePoint list tools; unlisted records and rules below remain authoritative knowledge. Email omissions are explicit.

# Building Permit Pilot — Synthetic Records

> SYNTHETIC PILOT DATA. All entities and dates are fictional. The fixed snapshot
> date is 2026-08-07. Do not recalculate relative dates from the current date.

## Permit applications

Entity rows from this section are now read with the SharePoint list tools from **Building Permit Processing Permit Applications**. Other context below remains knowledge.

There are 6 applications totaling $16,245,000 in declared valuation. Five are
open; BP-2025-0102 is approved and excluded from the open backlog.

## Fixed review-clock state

Entity rows from this section are now read with the SharePoint list tools from **Building Permit Processing Fixed Review Clock State**. Other context below remains knowledge.

The complaint-risk formula represented by this fixed result is:
`max(0, days_over) × 2 + review_cycle × 15`, plus 20 when the status is
`corrections_required`, capped at 100. Approved permits score 0.

## BPP-01 Locked Response

For the exact prompt `Which permit applications have been sitting too long,
and which resident is going to complain first?`, reproduce only the following
reviewed response:

### Permit Backlog and Complaint Risk

**First intervention:** BP-2025-0104 — Metro School District. It is the
highest-priority backlog item and the applicant most likely to call first. The
application is 63 days old against a 45-day target, 18 days overdue, in
correction cycle 3, assigned to Tom Delgado, with complaint risk 100/100.

**Recommended next step:** An authorized reviewer drafts the cycle-3 correction
list and chooses a specific re-review date. This is a recommendation only; no
message, permit update, assignment, or system action occurred.

| Priority | Permit | Applicant | Snapshot state |
|---:|---|---|---|
| 1 | BP-2025-0104 | Metro School District | 18 days overdue |
| 2 | BP-2025-0101 | Greenfield Development LLC | 18 days overdue |
| 3 | BP-2025-0103 | Sunrise Solar Inc. | 5 days overdue |

> Synthetic pilot data as of 2026-08-07; no live municipal system was accessed or changed.

## Intake records and duplicate finding

BP-2025-0105 has `site_plan` and `structural_calcs`. It is missing
`mep_drawings` and `title_report`. It is a duplicate of BP-2025-0101 because
the applicant and parcel match an application already in plan review.

BP-2025-0106 has `site_plan`, `structural_calcs`, `mep_drawings`, and
`title_report`. It is complete for commercial-alteration intake. It routes in
this order: Zoning → Building → Fire/Life Safety. Its fixed 21-day target date
is 2026-08-28.

## Applicant update state

- BP-2025-0104 — Metro School District: correction cycle 3; outstanding items
  are with Tom Delgado; 18 days overdue.
- BP-2025-0101 — Greenfield Development LLC: plan review with Karen Whitfield;
  18 days overdue.
- BP-2025-0103 — Sunrise Solar Inc.: next inspection is Electrical Rough-In on
  2026-08-17 with Dave Martinez; 5 days overdue against the review target.
- BP-2025-0105 — Greenfield Development LLC: MEP drawings and title report are
  missing; the review clock has not started.
- BP-2025-0106 — Ridgeline Restaurants Inc.: intake is complete and it is ready
  to enter review; 21-day target date 2026-08-28.

## Inspector roster

Entity rows from this section are now read with the SharePoint list tools from **Building Permit Processing Inspector Roster**. Other context below remains knowledge.

## Inspection board

BP-2025-0103 at 1100 Industrial Pkwy is the solar job.

Entity rows from this section are now read with the SharePoint list tools from **Building Permit Processing Inspection Board**. Other context below remains knowledge.

No other permit has an inspection in this synthetic schedule.
