# Permit and License Data

> SYNTHETIC — DEMO DATA. Every permit, license, facility, application, and
> authority-issued number in this document is fictional. This file exists so
> the agent has a working world to answer from on day one. In production,
> replace this file with tools that read your real permit register and
> application tracking system (see the README's production section).

## Permit register

| ID | Permit | Facility | Issuing Authority | Permit Number | Type | Issued | Expires | Status | Renewal Lead (days) | Conditions | Last Inspection |
|----|--------|----------|-------------------|---------------|------|--------|---------|--------|---------------------|------------|-----------------|
| PRM-6001 | Title V Air Operating Permit | Riverside Generating Station | CA Air Resources Board | AOP-CA-2024-1847 | air_quality | 2024-06-15 | 2029-06-15 | active | 365 | 24 | 2025-09-22 |
| PRM-6002 | NPDES Stormwater Discharge Permit | Riverside Generating Station | CA State Water Board | NPDES-CA-0052841 | water_discharge | 2023-03-01 | 2026-03-01 | expired | 180 | 18 | 2025-07-14 |
| PRM-6003 | RCRA Hazardous Waste Generator | Bayshore Refinery | EPA Region 6 | TXD-0489-2215 | waste_management | 2022-01-10 | 2027-01-10 | active | 270 | 32 | 2025-11-05 |
| PRM-6004 | Pipeline Operating License | Northeast Corridor Pipeline | PHMSA | PHMSA-NE-7742 | pipeline_operation | 2021-08-20 | 2026-08-20 | active | 365 | 28 | 2025-10-30 |
| PRM-6005 | Coal Combustion Residuals Permit | Ridgeline Coal Station | CO Dept of Public Health | CCR-CO-2023-0091 | waste_management | 2023-04-01 | 2026-04-01 | active | 180 | 21 | 2025-08-18 |
| PRM-6006 | Spill Prevention Control Plan | Bayshore Refinery | EPA Region 6 | SPCC-TX-2024-3340 | spill_prevention | 2024-02-15 | 2029-02-15 | active | 365 | 15 | 2025-06-02 |

`Conditions` is the number of conditions attached to the permit. The text of
those conditions is not held in this register.

## Facilities in the register

| Facility | Permits |
|----------|---------|
| Riverside Generating Station | PRM-6001, PRM-6002 |
| Bayshore Refinery | PRM-6003, PRM-6006 |
| Northeast Corridor Pipeline | PRM-6004 |
| Ridgeline Coal Station | PRM-6005 |

## Pending application log

| ID | Application | Facility | Authority | Submitted | Status | Expected Decision | Comments Received |
|----|-------------|----------|-----------|-----------|--------|-------------------|-------------------|
| APP-7001 | NPDES Stormwater Discharge Permit Renewal | Riverside Generating Station | CA State Water Board | 2025-09-01 | under_review | 2026-04-15 | 3 |
| APP-7002 | New Source Review - Gas Turbine Expansion | Riverside Generating Station | CA Air Resources Board | 2026-01-20 | public_comment | 2026-06-30 | 12 |
| APP-7003 | Pipeline Integrity Management Plan Update | Northeast Corridor Pipeline | PHMSA | 2026-02-10 | submitted | 2026-05-15 | 0 |

APP-7001 is the renewal application for PRM-6002. It is under review; PRM-6002
is expired. Both statements are true at the same time.
