# Prior Authorization Requests

> SYNTHETIC — DEMO DATA. Every patient, provider, authorization number, and
> payer record in this document is fictional. No real patient information
> appears here. This file exists so the agent has a working world to answer
> from on day one. In production, replace this file with tools that read your
> real authorization system and payer portals (see the README's production
> section).

## Authorization queue

| ID | Patient | Patient ID | Procedure | CPT | Diagnosis | Requesting Provider | Payer | Plan |
|----|---------|------------|-----------|-----|-----------|---------------------|-------|------|
| AUTH-4001 | Margaret Sullivan | PT-10045 | Left Knee MRI without Contrast | 73721 | M17.12 - Primary osteoarthritis, left knee | Dr. Anita Patel | Blue Cross Blue Shield of Illinois | PPO Gold |
| AUTH-4002 | Robert Kim | PT-10078 | Cardiac Stress Test (Nuclear) | 78452 | R07.9 - Chest pain, unspecified | Dr. James Wright | Aetna | HMO Select |
| AUTH-4003 | Maria Gonzalez | PT-20003 | Total Hip Arthroplasty | 27130 | M16.11 - Primary osteoarthritis, right hip | Dr. Michael Torres | Medicare Part B | Original Medicare |
| AUTH-4004 | David Nguyen | PT-20002 | Lumbar Spine MRI with Contrast | 72149 | M54.5 - Low back pain | Dr. James Wright | Aetna | HMO Select |

## Status, dates, and authorization numbers

| ID | Status | Submitted | Decision | Auth # | Valid Through |
|----|--------|-----------|----------|--------|---------------|
| AUTH-4001 | approved | 2026-03-13 | 2026-03-14 | BCBS-AUTH-884210 | 2026-06-14 |
| AUTH-4002 | pending_review | 2026-03-15 | (none) | (none) | (none) |
| AUTH-4003 | approved | 2026-03-10 | 2026-03-11 | MCR-AUTH-THA-99201 | 2026-09-11 |
| AUTH-4004 | denied | 2026-03-08 | 2026-03-12 | (none) | (none) |

Status counts across the queue: approved 2, pending_review 1, denied 1.
A field recorded as `(none)` has no value on the record. Render it as
`Pending` / `Awaiting` for a missing decision date and `N/A` for a missing
authorization number or valid-through date. Never infer a value.

## Reviewer notes (verbatim)

| ID | Notes |
|----|-------|
| AUTH-4001 | Auto-approved based on clinical criteria match. |
| AUTH-4002 | Requires peer-to-peer review. Additional documentation requested. |
| AUTH-4003 | Medicare LCD criteria met. Pre-op clearance required. |
| AUTH-4004 | Denied: Conservative therapy requirement not met. Minimum 6 weeks PT required. |

## Payer performance

| Payer | Overall Approval % | Avg Decision Days | Appeal Success % |
|-------|--------------------|-------------------|------------------|
| Blue Cross Blue Shield of Illinois | 88 | 1.8 | 62 |
| Aetna | 72 | 4.1 | 48 |
| Medicare Part B | 94 | 1.2 | 71 |

These are historical averages across the payer's volume. They are not
predictions for any individual authorization and are never added to a
submission date to produce an expected decision date.
