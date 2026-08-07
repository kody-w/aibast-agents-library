# Credentialing Policy and Onboarding Checklist

> SYNTHETIC — DEMO DATA. The thresholds and checklist below mirror the demo
> agent's logic exactly; they are not any organization's real bylaws. This file
> exists so the agent has a working world to answer from on day one. In
> production, replace this file with tools that read your real medical staff
> bylaws, credentialing policy, and onboarding workflow (see the README's
> production section).

## Alert severity rules

| Condition | Severity | Action Required |
|-----------|----------|-----------------|
| Credential status is `expired` | CRITICAL | Immediate renewal required |
| Credential expires on or before 2026-06-30 (and is not expired) | WARNING | Renewal due within 90 days |
| Malpractice policy expires on or before 2026-06-30 | WARNING | Policy renewal needed |
| Credential expires after 2026-06-30 | no alert | none |

The cutoff `2026-06-30` is inclusive and fixed, not a rolling window. The
expired and expiring branches are mutually exclusive: an expired credential is
raised once, as CRITICAL. Alerts sort CRITICAL first, then by expiration date
ascending within each severity band.

## Current alert queue

8 alerts, 2 critical.

| Severity | Staff Member | Credential | Expires | Action Required |
|----------|-------------|------------|---------|----------------|
| CRITICAL | Lisa Chen, RN | PALS Certification | 2025-09-20 | Immediate renewal required |
| CRITICAL | Mark Johnson, PA-C | PA License | 2026-02-28 | Immediate renewal required |
| WARNING | Mark Johnson, PA-C | DEA Registration | 2026-03-31 | Renewal due within 90 days |
| WARNING | Dr. James Wright | DEA Registration | 2026-05-19 | Renewal due within 90 days |
| WARNING | Lisa Chen, RN | RN License | 2026-05-31 | Renewal due within 90 days |
| WARNING | Lisa Chen, RN | ACLS Certification | 2026-06-10 | Renewal due within 90 days |
| WARNING | Dr. Anita Patel | Medical License | 2026-06-30 | Renewal due within 90 days |
| WARNING | Lisa Chen, RN | Malpractice Insurance | 2026-06-30 | Policy renewal needed |

## Verification

A credential is verified only when the record's primary source verification
flag is set. The flag is stored, never inferred from the issuer, the credential
type, or how current the expiration date looks. The records carry no
verification date and no verifier identity.

## New staff onboarding checklist

12 items, 5 categories: billing, compliance, credentialing, hr, it.

| # | Item | Category |
|---|------|----------|
| 1 | Background check completed | COMPLIANCE |
| 2 | License verification (primary source) | CREDENTIALING |
| 3 | DEA verification (if applicable) | CREDENTIALING |
| 4 | Board certification verification | CREDENTIALING |
| 5 | Malpractice insurance verification | COMPLIANCE |
| 6 | NPI validation | CREDENTIALING |
| 7 | Payer enrollment initiated | BILLING |
| 8 | EHR access provisioned | IT |
| 9 | HIPAA training completed | COMPLIANCE |
| 10 | Orientation completed | HR |
| 11 | Privileges approved by medical staff committee | CREDENTIALING |
| 12 | Malpractice tail coverage confirmed | COMPLIANCE |

Category distribution: CREDENTIALING 5, COMPLIANCE 4, BILLING 1, IT 1, HR 1.

This is a template. It carries no assignee, no due date, and no completion
state for any individual hire.

## Out of scope

These records cover staff credentialing only. They contain no patient data, no
clinical outcomes, no scheduling or payroll data, no privilege lists, no
disciplinary history, and no renewal fees or policy premiums.
