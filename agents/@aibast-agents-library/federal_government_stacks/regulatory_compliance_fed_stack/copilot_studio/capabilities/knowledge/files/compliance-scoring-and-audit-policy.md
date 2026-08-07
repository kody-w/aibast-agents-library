# Compliance Scoring and Audit Policy

> SYNTHETIC — DEMO DATA. These weights, bands, and checklist items are a
> fictional agency policy written to match the demo data. This file exists so
> the agent has a working world to answer from on day one. In production,
> replace this file with tools and policy documents that carry your agency's
> real scoring model and audit procedures (see the README's production section).

## Overall score weighting

The agency compliance posture is a fixed weighted sum of the four framework
scores, rounded to one decimal. The weights never change and are never
renormalized.

| Regulation | Weight | Agency Score | Contribution |
|------------|--------|--------------|--------------|
| FISMA | 0.40 | 82.5 | 33.00 |
| FedRAMP | 0.25 | 78.0 | 19.50 |
| PRIVACT | 0.20 | 91.0 | 18.20 |
| Section508 | 0.15 | 65.0 | 9.75 |
| **Total** | **1.00** | - | **80.45 -> 80.5** |

## Control coverage

Coverage is reported per framework, rounded to one decimal:

`coverage = (controls_implemented / controls_total) * 100`

| Regulation | Implemented | Total | Coverage |
|------------|-------------|-------|----------|
| FISMA | 847 | 1007 | 84.1% |
| FedRAMP | 312 | 421 | 74.1% |
| PRIVACT | 124 | 131 | 94.7% |
| Section508 | 38 | 62 | 61.3% |

A framework with zero total controls reports 0% coverage, not a blank.

## Remediation progress

Overall remediation progress is the unweighted mean of percent complete across
every action in the plan, rounded to one decimal. Planned actions at 0 percent
are included; severity does not weight the mean.

`(35 + 20 + 0 + 0 + 50 + 0 + 70) / 7 = 175 / 7 = 25.0%`

Only actions with status `in_progress` are reported as active. `planned` is not
active, and `target` is a planned date, never evidence of completion.

## Audit readiness bands

Readiness is derived from the weighted posture score alone. The open-finding
count does not move the band.

| Band | Condition | Current |
|------|-----------|---------|
| High | score >= 85 | - |
| Moderate | 70 <= score < 85 | 80.5 -> Moderate |
| Low | score < 70 | - |

## Open-finding rule

A finding counts as open unless its status is exactly `closed`. `in_progress`
counts as open. Current log: FY24-OIG-01 open, FY24-OIG-02 in progress,
FY24-GAO-01 open, FY24-OIG-03 closed - **3 of 4 open**.

## Standing audit readiness checklist

Reported as eight unchecked items every time. The agent never marks one
complete and never attests that the underlying evidence exists.

| # | Item |
|---|------|
| 1 | System Security Plans (SSP) current for all FISMA systems |
| 2 | POA&M items updated with milestones and completion dates |
| 3 | Continuous monitoring data feeds operational |
| 4 | Annual security assessments completed |
| 5 | Incident response plan tested within last 12 months |
| 6 | Privacy impact assessments current |
| 7 | Authority to Operate (ATO) documentation available |
| 8 | Supply chain risk management plan documented |

## Record-change boundary

The agent reads the scorecard, the gap register, the remediation plan, and the
finding log. It does not change any of them. Closing a finding, waiving or
risk-accepting a gap, moving a target date, or updating percent complete is the
named owner's action - IAM Team, SOC, Vulnerability Mgmt, Cloud Ops, Web Team,
Content Team, or Privacy Office for remediations; the ISSO and audit liaison
for findings.
