# Federal Workforce Clearance Data

> SYNTHETIC — DEMO DATA. Every employee, clearance, investigation, and system
> in this document is fictional. This file exists so the agent has a working
> world to answer from on day one. In production, replace this file with tools
> that read your real HR system, DCSA investigation feed, and identity and
> access management platform (see the README's production section).

All elapsed-day figures in this world are computed against a fixed evaluation
date of **2025-03-15**.

## Employee roster

| ID | Name | Position | Office | Hire Date | Clearance Level | Clearance Status | Investigation | Investigation Opened | Interim | EOD Date |
|----|------|----------|--------|-----------|-----------------|------------------|---------------|----------------------|---------|----------|
| EMP-5001 | Sarah Mitchell | Cybersecurity Analyst (GS-13) | Office of the CISO | 2025-03-01 | Top Secret/SCI | pending_adjudication | T5 | 2024-11-15 | Yes | 2025-03-15 |
| EMP-5002 | James Thornton | Program Analyst (GS-12) | Office of Acquisition Management | 2025-02-01 | Secret | active | T3 | 2024-09-01 | No | 2025-02-10 |
| EMP-5003 | Priya Desai | Data Scientist (GS-14) | Office of Data Analytics | 2025-04-01 | Top Secret | investigation_in_progress | T5 | 2025-01-10 | No | TBD |
| EMP-5004 | Robert Chen | IT Specialist (GS-11) | Office of Information Technology | 2025-01-15 | Public Trust (MBI) | active | T2 | 2024-10-01 | No | 2025-01-20 |

## Onboarding status board

Phase values are `complete`, `in_progress`, or `pending`. Completion counts
only phases marked `complete`, over four phases.

| Employee | Pre Arrival | Day One | First Week | First 30 Days | Completion |
|----------|-------------|---------|------------|---------------|------------|
| Sarah Mitchell (EMP-5001) | complete | complete | in_progress | pending | 50.0% |
| James Thornton (EMP-5002) | complete | complete | complete | complete | 100.0% |
| Priya Desai (EMP-5003) | in_progress | pending | pending | pending | 0.0% |
| Robert Chen (EMP-5004) | complete | complete | complete | in_progress | 75.0% |

## Clearance-to-access matrix

Access is keyed on clearance level only. A level with no additional
requirements has an empty Additional cell.

| Clearance Level | Network Access | Physical Access | Systems | Additional |
|-----------------|----------------|-----------------|---------|------------|
| Top Secret/SCI | JWICS, SIPRNet, NIPRNet | SCIF, Classified Workspace, General Building | XKEYSCORE-SIM, SIGINT-Portal, IC-Cloud | SCI indoctrination briefing, Polygraph (if CI) |
| Top Secret | SIPRNet, NIPRNet | Classified Workspace, General Building | SIPR-Email, Classified-SharePoint | TS indoctrination briefing |
| Secret | SIPRNet, NIPRNet | General Building | SIPR-Email | (none) |
| Public Trust (MBI) | NIPRNet | General Building | Agency-Email, Agency-VPN, SharePoint | (none) |
