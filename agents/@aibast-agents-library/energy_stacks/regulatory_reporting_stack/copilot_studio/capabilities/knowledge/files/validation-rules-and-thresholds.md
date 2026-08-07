# Validation Rules and Thresholds

> SYNTHETIC — DEMO DATA. The rule sets, source systems, and thresholds below are
> fictional stand-ins. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real data-governance rule set and source-system lineage.

## Validation gates applied to every report

| Gate | Condition that raises an issue | Issue text |
|------|-------------------------------|------------|
| Data quality | `data_quality_score < 80` | Data quality score below threshold (N/100) |
| Completeness | `completeness_pct < 100` and status is not `submitted` | Data collection incomplete (N%) |

- A report passes validation only when it raises no issue.
- Reports with status `not_started` are excluded from validation entirely — they
  are not counted as passes or failures and do not appear in the pass rate.
- Pass rate = passed reports / validated reports x 100, rounded to one decimal.

## Rule sets by data type

| Data type | Validation rules | Source systems |
|-----------|------------------|----------------|
| Emissions data | Non-negative values; Year-over-year variance < 25%; Mass balance check; Unit conversion validation | CEMS, Fuel metering, Production logs |
| Financial data | Reconciliation to GL; Rate base validation; Depreciation schedule check; Intercompany elimination | SAP, PowerPlan, Hyperion |
| Safety data | Incident classification verification; Mileage data reconciliation; Leak survey completeness | PIMS, GIS, Inspection database |

## Audit readiness counting

| Count | Definition |
|-------|------------|
| Total findings | Every finding in the log, any status |
| Open | Findings with status `open` |
| High severity open | Findings with severity `high` AND status `open` |

Remediated findings stay visible in the per-report tables but are excluded from
the open and high-severity-open counts.
