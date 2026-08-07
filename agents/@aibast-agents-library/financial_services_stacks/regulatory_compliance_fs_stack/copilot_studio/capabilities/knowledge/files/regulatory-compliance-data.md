# Regulatory Compliance Data

> SYNTHETIC — DEMO DATA. Every regulation score, examination finding,
> remediation plan, and examination date in this document is fictional. This
> file exists so the agent has a working world to answer from on day one. In
> production, replace this file with tools that read your real GRC platform,
> findings log, and examination calendar (see the README's production section).

## Regulation register

| Key | Full Name | Regulator | Compliance Score | Last Assessment | Next Assessment |
|-----|-----------|-----------|------------------|-----------------|-----------------|
| SOX | Sarbanes-Oxley Act | SEC | 92.0% | 2025-01-31 | 2025-07-31 |
| Dodd-Frank | Dodd-Frank Wall Street Reform Act | Fed / OCC / CFPB | 87.5% | 2024-12-15 | 2025-06-15 |
| BSA-AML | Bank Secrecy Act / Anti-Money Laundering | FinCEN / OCC | 84.0% | 2025-02-28 | 2025-08-31 |
| GLBA | Gramm-Leach-Bliley Act | FTC / Fed | 95.0% | 2025-01-15 | 2026-01-15 |
| FCRA | Fair Credit Reporting Act | CFPB | 89.0% | 2024-11-30 | 2025-05-31 |

These five keys are the complete tracked set. Any other regulation is not
tracked by this agent.

## Key sections

| Regulation | Section | Section Name |
|------------|---------|--------------|
| SOX | 302 | CEO/CFO Certification |
| SOX | 404 | Internal Controls Assessment |
| SOX | 409 | Real-Time Disclosure |
| Dodd-Frank | Volcker | Proprietary Trading Restrictions |
| Dodd-Frank | Title VII | Derivatives Regulation |
| Dodd-Frank | Title X | Consumer Protection |
| BSA-AML | CDD | Customer Due Diligence |
| BSA-AML | SAR | Suspicious Activity Reporting |
| BSA-AML | CTR | Currency Transaction Reporting |
| GLBA | Privacy | Financial Privacy Rule |
| GLBA | Safeguards | Safeguards Rule |
| GLBA | Pretexting | Pretexting Protection |
| FCRA | Accuracy | Information Accuracy |
| FCRA | Disputes | Consumer Dispute Resolution |
| FCRA | Furnishing | Data Furnisher Requirements |

## Examination findings log

| ID | Regulation | Finding | Severity | Status | Due | Owner |
|----|------------|---------|----------|--------|-----|-------|
| EF-2024-01 | BSA-AML | SAR filing timeliness below 90% threshold | moderate | remediation_in_progress | 2025-06-30 | BSA Officer |
| EF-2024-02 | BSA-AML | CDD refresh cycle exceeding 24-month requirement for high-risk customers | significant | open | 2025-04-30 | BSA Officer |
| EF-2024-03 | SOX | Access control review documentation incomplete for 2 IT systems | moderate | remediation_in_progress | 2025-05-31 | IT Audit Manager |
| EF-2024-04 | Dodd-Frank | Consumer complaint response time exceeded 15-day requirement in 8% of cases | low | closed | 2025-03-31 | Consumer Compliance |
| EF-2024-05 | FCRA | Dispute resolution letters missing required disclosures in 3 cases | low | closed | 2025-02-28 | Operations Manager |

GLBA has no examination findings on record.

## Remediation plan tracker

| Finding | Action | Owner | Milestone | Progress |
|---------|--------|-------|-----------|----------|
| EF-2024-01 | Implement automated SAR filing workflow with deadline alerts | BSA Officer | 2025-05-15 | 60% |
| EF-2024-02 | Accelerate CDD refresh for 142 high-risk customers | BSA Officer | 2025-04-15 | 35% |
| EF-2024-03 | Complete access review documentation for Oracle EBS and Salesforce | IT Audit Manager | 2025-04-30 | 70% |

The milestone date on a plan is distinct from the due date on the finding it
remediates.

## Upcoming examinations

| Examiner | Type | Scheduled | Duration (weeks) | Lead Examiner |
|----------|------|-----------|------------------|---------------|
| OCC | Safety & Soundness | 2025-05-12 | 3 | Regional Examiner — District 4 |
| FinCEN | BSA/AML Targeted Review | 2025-07-01 | 2 | FinCEN Enforcement Division |
| CFPB | Consumer Compliance | 2025-09-15 | 2 | CFPB Supervision — Region III |
