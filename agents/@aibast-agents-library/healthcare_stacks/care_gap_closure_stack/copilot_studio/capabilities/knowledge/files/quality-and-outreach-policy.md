# Quality and Outreach Policy

> SYNTHETIC — DEMO DATA. A fictional health plan's policy, included so the
> agent's guardrails are grounded in a citable document rather than only in its
> instructions. In production, replace this file with your own quality and
> member-contact policy.

## Why the agent recommends and never acts

Member outreach is regulated contact. A call, text, portal message, or mailing
placed without the quality team's sign-off is a member-experience and
compliance event regardless of outcome. The care gap system therefore treats
campaign plans as proposals: the agent produces the plan, a person launches it.
The agent never states that outreach has been sent, scheduled, or queued.

## Why there is no patient-level data

This agent operates on aggregates only — measure populations, gap counts, and
segment counts. Patient identity, contact details, and clinical values are not
in scope for it and are held in the source systems under their own access
controls. When asked for a member list, the agent says it does not have
patient-level data. It never constructs an example patient to illustrate a
point; a fabricated member record is indistinguishable from a real one to
whoever reads the answer next.

## Measures in use

| ID | Measure | Star threshold |
|----|---------|----------------|
| BCS | Breast Cancer Screening | 4-star threshold at 76% |
| CDC-HBA1C | Diabetes HbA1c Testing | 5-star threshold at 90% |
| COL | Colorectal Cancer Screening | 4-star threshold at 68% |
| CBP | Controlling Blood Pressure | 4-star threshold at 64% |
| AWC | Adolescent Well-Care Visits | 3-star threshold at 54% |

The star threshold and the national benchmark are two different bars. A measure
can clear one and miss the other — CDC-HBA1C at 85.0% is below both its 88.5%
benchmark and its 90% 5-star threshold, while CBP at 70.0% clears its 65.8%
benchmark and its 64% threshold. The agent reports both comparisons and
forecasts neither a rating nor a bonus.

## Prioritization rules

1. Gap analysis ranks measures by revenue opportunity, descending. Revenue
   opportunity is gross value at the per-closure rate — it is not net of
   outreach cost.
2. Patient prioritization ranks segments by average risk score, descending.
   Population size never outranks risk.
3. Campaign planning ranks measures by ROI, descending, and uses the single
   highest-converting channel across the channel table for every measure.
4. The HEDIS dashboard is unranked and is presented in measure order: BCS,
   CDC-HBA1C, COL, CBP, AWC.
5. The Recently Compliant segment is excluded from outreach — it closed its
   gaps within the last 90 days and carries a preferred channel of `none`.
6. The Unreachable segment is worked through contact-data remediation before
   outreach spend: an 8% response rate against a 2.9 risk score is a data
   problem, not a targeting problem.

## Projections

Projected closures, cost, revenue, and ROI come from the channel conversion
model. They are planning estimates, not booked results, and every presentation
of them says so. Cost assumes one contact per open gap and excludes repeat
attempts, staff time, and member incentives.
