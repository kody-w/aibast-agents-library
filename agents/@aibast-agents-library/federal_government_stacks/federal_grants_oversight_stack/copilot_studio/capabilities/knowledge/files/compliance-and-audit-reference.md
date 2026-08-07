# Compliance and Audit Reference

> SYNTHETIC — DEMO DATA. Every audit finding and corrective action in this
> document is fictional; the regulatory citations are included as the demo
> world's framework. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real audit findings log and corrective action tracker.

## Regulatory framework

### 2 CFR 200 — Uniform Administrative Requirements

| Section | Requirement | Frequency |
|---------|-------------|-----------|
| 200.302 | Financial Management | continuous |
| 200.303 | Internal Controls | continuous |
| 200.328 | Financial Reporting | quarterly |
| 200.329 | Performance Reporting | semi-annual |
| 200.344 | Closeout | end_of_grant |

### Single Audit — Single Audit Act (A-133)

| Requirement | Detail | Frequency |
|-------------|--------|-----------|
| threshold | Expenditure Threshold ($750K) | annual |
| findings | Prior Year Findings Follow-up | annual |
| schedule | Schedule of Expenditures (SEFA) | annual |

## Audit findings log

| Finding ID | Grant | Severity | Finding | Status | Corrective Action |
|------------|-------|----------|---------|--------|-------------------|
| AF-2024-01 | GRT-2025-4401 | low | Late submission of SF-425 Q2 report by 8 days | resolved | Automated reminders implemented |
| AF-2024-02 | GRT-2025-4402 | moderate | Cost allocation methodology not documented for shared personnel | in_progress | Cost allocation plan under review |
| AF-2024-03 | GRT-2025-4403 | low | Equipment inventory tags missing on 3 of 47 items | resolved | Physical inventory completed and reconciled |
| AF-2023-07 | GRT-2025-4404 | high | Supplanting concern — state funding reduced concurrent with federal award | in_progress | MOE documentation being compiled by finance office |

Findings resolved: 2 of 4.

## Compliance scoring rule

A grant starts at 100. Only findings whose status is not `resolved` deduct.

| Severity | Deduction |
|----------|-----------|
| low | 5 |
| moderate | 15 |
| high | 30 |

Score = max(0, 100 - sum of deductions). A grant with no findings scores 100.

| Grant ID | Unresolved Findings | Deduction | Compliance Score |
|----------|---------------------|-----------|------------------|
| GRT-2025-4401 | none (AF-2024-01 resolved) | 0 | 100% |
| GRT-2025-4402 | AF-2024-02 (moderate) | 15 | 85% |
| GRT-2025-4403 | none (AF-2024-03 resolved) | 0 | 100% |
| GRT-2025-4404 | AF-2023-07 (high) | 30 | 70% |

## Single Audit threshold analysis

- Total federal expenditures (sum of funds drawn): $4,962,500
- Single Audit threshold: $750,000
- Audit required (expenditures >= threshold): Yes

## Audit readiness checklist

- [ ] Schedule of Expenditures of Federal Awards (SEFA) prepared
- [ ] Cost allocation plans current and documented
- [ ] Subrecipient monitoring documentation complete
- [ ] Equipment inventory reconciled
- [ ] Time-and-effort certifications on file
- [ ] Procurement documentation meets federal standards
- [ ] Financial reconciliation between GL and drawdowns
- [ ] Prior year corrective action plans implemented
