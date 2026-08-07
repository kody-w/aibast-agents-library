# Medication and Referral Data

> SYNTHETIC — DEMO DATA. Every patient, medication, provider, and referral in
> this document is fictional. No real protected health information appears
> here. This file exists so the agent has a working world to answer from on
> day one. In production, replace this file with tools that read your real
> medication list and referral/order systems (see the README's production
> section).

## Medication list — PT-10045 (Margaret Sullivan)

| Medication | Dose | Frequency | Route | Indication | Status | Start Date | Peri-op Class |
|------------|------|-----------|-------|------------|--------|------------|---------------|
| Metformin | 1000mg | BID | oral | Type 2 Diabetes | active | 2022-05-10 | biguanide |
| Lisinopril | 20mg | daily | oral | Hypertension | active | 2021-03-15 | ace-inhibitor |
| Atorvastatin | 40mg | daily | oral | Hyperlipidemia | active | 2023-01-20 | statin |
| Aspirin | 81mg | daily | oral | Cardiovascular prevention | active | 2023-01-20 | antiplatelet |
| Meloxicam | 15mg | daily | oral | Osteoarthritis | new | 2026-03-12 | nsaid |

Total medications: 5 (4 active, 1 new).

## Medication list — PT-10078 (Robert Kim)

| Medication | Dose | Frequency | Route | Indication | Status | Start Date | Peri-op Class |
|------------|------|-----------|-------|------------|--------|------------|---------------|
| Omeprazole | 20mg | daily | oral | GERD | active | 2024-08-05 | ppi |
| Sertraline | 100mg | daily | oral | Anxiety | active | 2023-11-12 | ssri |
| Atorvastatin | 80mg | daily | oral | Hyperlipidemia | new | 2026-03-14 | statin |
| Aspirin | 81mg | daily | oral | Cardiovascular prevention | new | 2026-03-14 | antiplatelet |

Total medications: 4 (2 active, 2 new).

## Polypharmacy threshold

A patient is flagged for polypharmacy when their total medication count —
active plus new, no other filter — is **5 or more**. On this data set only
PT-10045 (5 medications) meets the threshold; PT-10078 (4 medications) does
not. The threshold is a count, not a clinical judgment.

## Peri-operative review classes

Every medication carries a recorded `Peri-op Class`. The record set marks four
of those classes for peri-operative review:

| Peri-op Class | In review set? |
|---------------|----------------|
| antiplatelet | yes |
| nsaid | yes |
| ace-inhibitor | yes |
| biguanide | yes |
| statin | no |
| ppi | no |
| ssri | no |

A medication appears in the pre-operative summary if and only if its recorded
class is in the review set. Membership is a documented property of this record
set — the agent never classifies a drug itself, never infers a class from the
indication, and never reads inclusion as an instruction to hold, stop, or
adjust a medication. On this data set that selects 4 medications for PT-10045
(Metformin, Lisinopril, Aspirin, Meloxicam) and 1 for PT-10078 (Aspirin).

## Referral queue

| Referral ID | Patient ID | Patient | From Provider | To Specialty | To Provider | Urgency | Encounter ID | Reason |
|-------------|------------|---------|---------------|--------------|-------------|---------|--------------|--------|
| REF-3001 | PT-10045 | Margaret Sullivan | Dr. Anita Patel | Orthopedics | Dr. Michael Torres | routine | ENC-2001 | Left knee osteoarthritis evaluation - possible injection or surgical consult |
| REF-3002 | PT-10078 | Robert Kim | Dr. James Wright | Cardiology | Dr. Sarah Lin | urgent | ENC-2002 | Stress test and cardiac risk stratification - chest pain with cardiac risk factors |
| REF-3003 | PT-10078 | Robert Kim | Dr. James Wright | Pulmonology | Dr. David Huang | routine | ENC-2002 | Smoking cessation program and pulmonary function evaluation |

Total referrals: 3 — one urgent (REF-3002), two routine (REF-3001, REF-3003).
