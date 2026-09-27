<!-- Generated from the original workshop knowledge; edit the source and regenerate. -->
> Retained synthetic knowledge. Listed entity fields come from the SharePoint list tools; unlisted records and rules below remain authoritative knowledge. Email omissions are explicit.

# Care Gap Closure Agent — complete synthetic records

> **Fictional aggregate demonstration data only.** These records reproduce the deterministic `CareGapClosureAgent`. They do not establish individual eligibility, exclusions, compliance, risk, or outreach permission.

## Synthetic quality measures

Entity rows from this section are now read with the SharePoint list tools from **Care Gap Closure Quality Measures**. Other context below remains knowledge.

Calculation rules:

- `Records requiring evidence review = source population - source-recorded closed`.
- `Source-recorded closed rate = round(source-recorded closed / source population × 100, 1)`.
- The largest evidence-review queue is **SYN-COL — 182 records**.

## Synthetic operational cohorts

Entity rows from this section are now read with the SharePoint list tools from **Care Gap Closure Operational Cohorts**. Other context below remains knowledge.

Ordering is operational triage only, not clinical risk scoring.

## Canonical unsent outreach draft

For each selected synthetic measure, the deterministic draft is:

- `Draft: We are reviewing our records and invite you to contact the care team if you have questions.`
- `Do not state that care is overdue or that the recipient is eligible until a reviewer validates the record.`
- `Approval route: quality reviewer → clinician when needed → authorized outreach operator.`

No message is sent.

## Fixed source facts used by the locked cases

- CG-01 must identify `SYN-COL — 182 records` as the largest queue and include `Records requiring evidence review` for all three measures.
- CG-02 must include `Multiple Source Gaps` and `Ordering is operational triage only, not clinical risk scoring.`
- CG-03 uses SYN-BCS and must include `No message is sent` plus the prohibition on stating overdue care or eligibility.
- CG-04 must reproduce the three rates, evidence date 2026-07-31, and exact reviewer limitations.
