# Regulatory Reporting Data

> SYNTHETIC — DEMO DATA. Every report, facility, finding, and score in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real regulatory report register and audit finding log.

## Regulatory report register

| ID | Report | Authority | Facility | Reporting Period | Deadline | Status | Quality | Complete | Assignee | Last Updated |
|----|--------|-----------|----------|------------------|----------|--------|---------|----------|----------|--------------|
| RPT-9001 | EPA GHG Reporting Program (Subpart C) | EPA | Riverside Generating Station | CY 2025 | 2026-03-31 | in_progress | 87/100 | 78% | Environmental Compliance Team | 2026-03-10 |
| RPT-9002 | FERC Form 1 Annual Report | FERC | Corporate (All Facilities) | CY 2025 | 2026-04-18 | in_progress | 92/100 | 65% | Regulatory Affairs | 2026-03-12 |
| RPT-9003 | TCEQ Annual Emissions Inventory | State - Texas | Bayshore Refinery | CY 2025 | 2026-03-31 | submitted | 95/100 | 100% | Environmental Compliance Team | 2026-03-05 |
| RPT-9004 | Colorado Air Quality Control Division Report | State - Colorado | Ridgeline Coal Station | CY 2025 | 2026-04-30 | not_started | 0/100 | 0% | Environmental Compliance Team | N/A |
| RPT-9005 | EPA Toxics Release Inventory (TRI) | EPA | Bayshore Refinery | CY 2025 | 2026-07-01 | in_progress | 74/100 | 42% | Health & Safety Team | 2026-02-28 |
| RPT-9006 | PHMSA Annual Pipeline Safety Report | PHMSA | Northeast Corridor Pipeline | CY 2025 | 2026-03-15 | overdue | 81/100 | 90% | Pipeline Operations | 2026-03-14 |

Status values in use: `not_started`, `in_progress`, `submitted`, `overdue`.
Only these six filings are tracked. Anything outside this table is not on file.

## Audit findings

| ID | Report | Finding | Severity | Status | Due Date |
|----|--------|---------|----------|--------|----------|
| AUD-001 | RPT-9001 | Missing CEMS calibration records for Q3 | medium | open | 2026-03-25 |
| AUD-002 | RPT-9002 | Depreciation schedule mismatch with PowerPlan | high | remediated | 2026-03-15 |
| AUD-003 | RPT-9005 | Threshold calculation methodology not documented | low | open | 2026-05-01 |
| AUD-004 | RPT-9006 | Pipeline mileage discrepancy between GIS and PIMS | high | open | 2026-03-20 |

RPT-9003 and RPT-9004 have no recorded audit findings.
