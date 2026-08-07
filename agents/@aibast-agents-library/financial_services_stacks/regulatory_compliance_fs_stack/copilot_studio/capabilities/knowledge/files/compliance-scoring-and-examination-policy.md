# Compliance Scoring and Examination Policy

> SYNTHETIC — DEMO DATA. The weights, thresholds, and checklist below mirror
> the demo rules this agent computes with. This file exists so the agent has a
> working world to answer from on day one. In production, replace this file
> with tools that read your real scoring model, findings taxonomy, and
> examination readiness process (see the README's production section).

## Overall compliance score

The overall score is a fixed weighted average of the five regulation scores,
rounded to one decimal place.

| Regulation | Weight |
|------------|--------|
| SOX | 0.25 |
| Dodd-Frank | 0.20 |
| BSA-AML | 0.25 |
| GLBA | 0.15 |
| FCRA | 0.15 |

`overall = 0.25*SOX + 0.20*Dodd-Frank + 0.25*BSA-AML + 0.15*GLBA + 0.15*FCRA`

Worked against the current register:
`0.25*92.0 + 0.20*87.5 + 0.25*84.0 + 0.15*95.0 + 0.15*89.0 = 89.1`

The weights are fixed. Remediation progress does not change a score; only a
new assessment does.

## Finding status vocabulary

| Status | Meaning | Counts as open |
|--------|---------|----------------|
| open | Identified, no remediation underway | Yes |
| remediation_in_progress | Plan active, not yet validated closed | Yes |
| closed | Remediated and accepted | No |

Open findings count = every finding whose status is not `closed`. Current
count: 3 (EF-2024-01, EF-2024-02, EF-2024-03).

## Severity ladder

| Severity | Findings at this level |
|----------|------------------------|
| significant | EF-2024-02 |
| moderate | EF-2024-01, EF-2024-03 |
| low | EF-2024-04, EF-2024-05 |

Severity is assigned by the examiner and is never re-graded by this agent.

## Remediation progress

`average progress = sum of plan percentages / number of plans`

Current: `(60 + 35 + 70) / 3 = 55%`. Progress is reported with no decimal
places. Progress is not closure.

## Regulatory thresholds cited in findings

| Threshold | Source finding |
|-----------|----------------|
| SAR filing timeliness must meet a 90% threshold | EF-2024-01 |
| CDD refresh for high-risk customers must not exceed 24 months | EF-2024-02 |
| Consumer complaint response within 15 days | EF-2024-04 |

Report these as written. This agent does not interpret whether an obligation
applies to a given case.

## Pre-examination checklist

Fixed, ten items, always presented unchecked. Completion state is not tracked
in this data.

1. Board and committee minutes prepared and indexed
2. Policies and procedures current with regulatory changes
3. Internal audit reports available for last 3 years
4. Compliance testing results documented
5. Prior MRA/MRIA status updates prepared
6. Capital adequacy and stress test results available
7. BSA/AML independent testing report current
8. Consumer complaint log updated
9. IT risk assessment and SOC reports available
10. Organizational chart and key personnel list current

## Action boundary

This agent reports. It does not close findings, change statuses, move
milestones, file regulatory reports, notify owners, or correspond with
examiners. Every output ends with the compliance officer deciding.
