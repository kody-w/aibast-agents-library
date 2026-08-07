# Onboarding Risk Thresholds and Scoring Rules

> SYNTHETIC — DEMO DATA. These thresholds and the worked results below are
> fictional and exist so the agent has a working world to answer from on day
> one. In production, replace this file with tools that read your real customer
> success policy and scoring configuration (see the README's production
> section).

## Risk thresholds

| Threshold | Value | Applied by risk flags |
|-----------|-------|-----------------------|
| health_score_critical | 40 | Yes — health score below 40 raises CRITICAL |
| health_score_warning | 60 | Yes — health score below 60 raises WARNING |
| training_min_pct | 50 | Yes — training completion below 50% raises a flag |
| adoption_min_pct | 30 | No — defined but not evaluated by the flag rule |
| user_activation_min_pct | 40 | Yes — activation below 40% raises a flag |

## Health score bands

Used by the pipeline summary. The bands are exclusive and exhaustive.

| Band | Rule |
|------|------|
| On Track | health_score >= 70 |
| At Risk | 40 <= health_score < 70 |
| Critical | health_score < 40 |

Current split: On Track 4, At Risk 0, Critical 1.

## Computation rules

| Metric | Formula |
|--------|---------|
| Pipeline ARR | sum of every customer's ARR |
| Milestone completion | count of milestones with status `complete`, out of 6 |
| Milestone progress | round(completed / 6 * 100, 1) |
| Next milestone | first milestone in sequence with status `in_progress` or `not_started`; `blocked` is skipped |
| Average adoption | round(sum of the 5 feature percentages / 5, 1) |
| User activation | round(active_users / licensed_users * 100, 1); 0 when licensed_users is 0 |
| Risk flag sort | ascending health_score, worst first |

## Flag evaluation order

1. CRITICAL (health below 40) or, if not critical, WARNING (health below 60).
   The two are mutually exclusive.
2. Low training completion (training below 50%).
3. Low user activation (activation below 40%).
4. Blocked milestones, listing the milestone keys.

A customer with no flags is omitted from the risk output entirely.

## Current flagged accounts

Sorted ascending by health score.

| ID | Customer | ARR | Health | Flags |
|----|----------|-----|--------|-------|
| CUST-1003 | Vanguard Logistics | $84,000 | 38 | CRITICAL: Health score below threshold; Low training completion; Low user activation; Blocked milestones: data_migration |
| CUST-1001 | Meridian Healthcare Systems | $186,000 | 72 | Low training completion; Low user activation |
| CUST-1004 | BrightPath Education | $96,000 | 81 | Low training completion |
| CUST-1005 | Orion Manufacturing | $312,000 | 91 | Low training completion; Low user activation |

CUST-1002 Apex Financial Group is not flagged: health 89, training 73% (at or
above 50), activation 76.7% (at or above 40), no blocked milestones.

## Action boundary

Every operation in this stack is read-only. The agent reports and recommends;
changing a health score, moving a go-live date, closing or unblocking a
milestone, assigning training, reclaiming a license, or notifying a CSM is a
human action taken outside the agent.
