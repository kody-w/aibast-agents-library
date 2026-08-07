# Underwriting Applications Data

> SYNTHETIC — DEMO DATA. Every applicant, application, loss, and underwriter in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real policy administration and submission clearance systems (see
> the README's production section).

## Application file

| App ID | Applicant | Line of Business | Coverage Requested | Indicated Premium | Risk Score | Tier | Status | Underwriter |
|--------|-----------|------------------|--------------------|-------------------|------------|------|--------|-------------|
| UW-2025-101 | Riverside Manufacturing Inc. | commercial_property | $5,000,000 | $42,500 | 62 | Substandard | under_review | Patricia Graham |
| UW-2025-102 | Cascade Freight Logistics LLC | commercial_auto | $2,000,000 | $55,000 | 22 | Preferred | approved | James Chen |
| UW-2025-103 | Downtown Medical Associates | professional_liability | $3,000,000 | $67,000 | 75 | Substandard | exception_review | Patricia Graham |
| UW-2025-104 | Harbor View Restaurant Group | general_liability | $2,000,000 | $18,500 | 48 | Standard | pending_info | James Chen |

Tier is derived from the risk score, not stored: 0-30 Preferred, 31-55
Standard, 56-75 Substandard, 76+ Decline.

## Risk characteristics by application

### UW-2025-101 — Riverside Manufacturing Inc. (commercial property)

| Attribute | Value |
|-----------|-------|
| Property type | manufacturing_facility |
| Construction | fire_resistive |
| Year built | 1998 |
| Square footage | 85,000 |
| Protection class | 3 |

### UW-2025-102 — Cascade Freight Logistics LLC (commercial auto)

| Attribute | Value |
|-----------|-------|
| Fleet size | 18 |
| Vehicle class | light_truck |
| Radius of operation | intermediate |
| DOT safety rating | satisfactory |
| Fleet violations | 0 |
| Fleet accidents | 0 |
| Years operating | 9 |

### UW-2025-103 — Downtown Medical Associates (professional liability)

| Attribute | Value |
|-----------|-------|
| Specialty | orthopedic_surgery |
| Practitioners | 6 |
| Years in practice | 12 |

### UW-2025-104 — Harbor View Restaurant Group (general liability)

| Attribute | Value |
|-----------|-------|
| Business type | restaurant_chain |
| Locations | 4 |
| Annual revenue | $8,500,000 |
| Employees | 120 |

## Loss and claims history

| App ID | Year | Type / Allegation | Amount | Status |
|--------|------|-------------------|--------|--------|
| UW-2025-101 | 2022 | fire | $125,000 | closed |
| UW-2025-101 | 2023 | water_damage | $18,500 | closed |
| UW-2025-103 | 2021 | surgical_complication | $450,000 | settled |
| UW-2025-103 | 2023 | misdiagnosis | $0 | dismissed |
| UW-2025-104 | 2024 | slip_and_fall | $35,000 | open |

UW-2025-102 has no loss history. UW-2025-103 carries claims history rather than
loss history because it is a professional liability submission.
