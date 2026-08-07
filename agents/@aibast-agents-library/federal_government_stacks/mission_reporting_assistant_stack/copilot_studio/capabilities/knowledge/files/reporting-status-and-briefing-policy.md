# Reporting Status and Briefing Policy

> SYNTHETIC — DEMO DATA. These bands, formulas, and cadences are the rules the
> demo agent computes with; they are not any agency's actual performance
> management policy. In production, replace this file with tools and policy
> documents from your performance management office (see the README's
> production section).

## KPI attainment and status bands

Attainment is computed per KPI, then banded. The formula depends on the unit,
because some measures are better when lower.

| Unit | Direction | Attainment formula | Guard |
|------|-----------|--------------------|-------|
| days, minutes | lower is better | `pct = (target / current) * 100` | `current` of 0 yields `pct = 100` |
| all other units | higher is better | `pct = (current / target) * 100` | `target` of 0 yields `pct = 0` |

| Band | Condition |
|------|-----------|
| On Target | `pct >= 95` |
| Near Target | `pct >= 75` and `pct < 95` |
| Below Target | `pct < 75` |

Worked results for the current register:

| KPI | Arithmetic | pct | Band |
|-----|------------|-----|------|
| KPI-101 | 87.3 / 95.0 | 91.9 | Near Target |
| KPI-102 | 15 / 22 | 68.2 | Below Target |
| KPI-103 | 4.8 / 3.0 | 160.0 | On Target |
| KPI-201 | 68.5 / 80.0 | 85.6 | Near Target |
| KPI-202 | 52.1 / 70.0 | 74.4 | Below Target |
| KPI-203 | 5.0 / 8.3 | 60.2 | Below Target |
| KPI-301 | 72.0 / 90.0 | 80.0 | Near Target |
| KPI-302 | 69.4 / 75.0 | 92.5 | Near Target |
| KPI-303 | 61.5 / 85.0 | 72.4 | Below Target |

**Known limitation of the rule.** Inversion is keyed on the unit, not on the
measure's intent. Phishing Click Rate (KPI-103) is a lower-is-better measure
carried in `%`, so the rule scores it higher-is-better and it reads On Target
at 4.8% against a 3.0% target. The agent reports the computed status and
explains the unit-based rule rather than silently correcting it.

## Budget utilization

`utilization = round((budget_spent / budget_allocated) * 100, 1)`, and `0.0`
when nothing is allocated. Utilization is reported, never projected — no burn
rate, no schedule variance, no year-end forecast.

| Mission | Arithmetic | Utilization |
|---------|------------|-------------|
| MO-001 | 7,250,000 / 14,500,000 | 50.0% |
| MO-002 | 4,920,000 / 8,200,000 | 60.0% |
| MO-003 | 840,000 / 5,600,000 | 15.0% |

## Trend direction

Direction is computed from the **last two observed values only**, with a 2%
dead band. It is not a regression over the series.

| Condition | Direction |
|-----------|-----------|
| fewer than 2 values | insufficient_data |
| `recent > previous * 1.02` | improving |
| `recent < previous * 0.98` | declining |
| otherwise | stable |

Net change is `round(last - first, 1)`, signed, reported over the count of
observed quarters. A KPI can therefore show a positive net change and still be
Stable (KPI-301: +7.0% net, Stable), or fall every quarter and still be Stable
(KPI-201: -3.5% net, Stable), because the last step sits inside the dead band.
The register's `trend` label is a separate, stored field and may disagree with
the computed direction — KPI-201 is labeled `declining` but computes as Stable.

## Executive brief selection rule

The executive brief carries only the two extreme bands:

| Computed band | Brief line |
|---------------|------------|
| Below Target | `**Action Needed:** <name> at <current><unit> vs target <target><unit>` |
| On Target | `**On Track:** <name> at <current><unit>` |
| Near Target | omitted |

Under this rule the current brief is: MO-001 one Action Needed (Mean Time to
Remediate at 22days) and one On Track (Phishing Click Rate at 4.8%); MO-002 two
Action Needed (Digital Service Adoption, Average Transaction Time) and nothing
On Track; MO-003 one Action Needed (Training Completion Rate at 61.5%).

## Briefing cadence

| Cadence | Stakeholders |
|---------|--------------|
| bi-weekly | SH-03 CIO |
| monthly | SH-01 Deputy Secretary, SH-04 CHCO |
| quarterly | SH-02 CFO, SH-05 OMB Desk Officer |
| as needed | SH-06 Congressional Liaison |

Cadence describes when a briefing is due. The agent produces briefing material;
it never schedules, sends, or logs a briefing, and it never reports that a
stakeholder has been notified.
