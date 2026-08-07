# Clinical Encounter Data

> SYNTHETIC — DEMO DATA. Every patient, provider, encounter, and lab value in
> this document is fictional. No real protected health information appears
> here. This file exists so the agent has a working world to answer from on
> day one. In production, replace this file with tools that read your real EHR
> encounter, vitals, and results feeds (see the README's production section).

## Encounter index

| Encounter ID | Patient ID | Patient | Age | Gender | Date | Type | Provider |
|--------------|------------|---------|-----|--------|------|------|----------|
| ENC-1990 | PT-10045 | Margaret Sullivan | 68 | Female | 2025-09-18 | Office Visit | Dr. Anita Patel |
| ENC-2001 | PT-10045 | Margaret Sullivan | 68 | Female | 2026-03-12 | Office Visit | Dr. Anita Patel |
| ENC-1991 | PT-10078 | Robert Kim | 52 | Male | 2025-10-02 | Office Visit | Dr. Anita Patel |
| ENC-2002 | PT-10078 | Robert Kim | 52 | Male | 2026-03-14 | Urgent Care | Dr. James Wright |

Each patient has two documented encounters. The record set is grouped by
patient and ordered oldest first within a patient, so the earlier encounter is
the prior visit for the later one.

## ENC-1990 — Margaret Sullivan (PT-10045)

**Chief complaint:** Routine diabetes and hypertension follow-up

**Clinical notes:** Six-month diabetes follow-up. Patient reports good
adherence to Metformin and Lisinopril. No polyuria or polydipsia reported
today. Weight 183 lbs, stable since the prior year. Blood pressure 138/84. No
joint complaints; gait normal, knees without effusion. Trace pedal edema. Labs
drawn today.

### Vital signs

| Measure | Value |
|---------|-------|
| BP systolic | 138 |
| BP diastolic | 84 |
| Heart rate | 76 |
| Temperature (F) | 98.2 |
| Respiratory rate | 16 |
| Weight (lbs) | 183 |
| BMI | 30.5 |
| SpO2 (%) | 98 |

### Diagnoses

| Code | Description | Status |
|------|-------------|--------|
| E11.65 | Type 2 diabetes with hyperglycemia | active |
| I10 | Essential hypertension | active |
| E66.01 | Morbid obesity due to excess calories | active |

### Lab results

| Test | Value | Reference | Flag |
|------|-------|-----------|------|
| HbA1c | 7.4% | <7.0% | high |
| Fasting Glucose | 154 mg/dL | 70-100 mg/dL | high |
| eGFR | 68 mL/min | >60 mL/min | normal |
| Creatinine | 1.0 mg/dL | 0.6-1.2 mg/dL | normal |

## ENC-2001 — Margaret Sullivan (PT-10045)

**Chief complaint:** Follow-up for diabetes management and new onset left knee pain

**Clinical notes:** Patient presents for routine diabetes follow-up. Reports
increased thirst and urination over past 2 weeks. Also complains of left knee
pain, worse with stairs, onset 3 weeks ago. No trauma. HbA1c drawn today.
Blood pressure elevated at 148/92. Weight 187 lbs, up 4 lbs from last visit.
Bilateral pedal edema noted. Left knee with mild effusion, no instability.
ROM slightly decreased.

### Vital signs

| Measure | Value |
|---------|-------|
| BP systolic | 148 |
| BP diastolic | 92 |
| Heart rate | 78 |
| Temperature (F) | 98.4 |
| Respiratory rate | 16 |
| Weight (lbs) | 187 |
| BMI | 31.2 |
| SpO2 (%) | 97 |

### Diagnoses

| Code | Description | Status |
|------|-------------|--------|
| E11.65 | Type 2 diabetes with hyperglycemia | active |
| I10 | Essential hypertension | active |
| M17.12 | Primary osteoarthritis, left knee | new |
| E66.01 | Morbid obesity due to excess calories | active |

### Lab results

| Test | Value | Reference | Flag |
|------|-------|-----------|------|
| HbA1c | 8.2% | <7.0% | high |
| Fasting Glucose | 182 mg/dL | 70-100 mg/dL | high |
| eGFR | 62 mL/min | >60 mL/min | borderline |
| Creatinine | 1.1 mg/dL | 0.6-1.2 mg/dL | normal |

## ENC-1991 — Robert Kim (PT-10078)

**Chief complaint:** Annual preventive visit with lipid screening

**Clinical notes:** Annual preventive visit. GERD controlled on Omeprazole;
anxiety stable on Sertraline. Still smoking 1 PPD, declined cessation referral
today. Denies chest pain, chest tightness, exertional dyspnea, or palpitations.
Cardiac exam normal, lungs clear. Fasting lipid panel drawn. Weight 211 lbs.
BP 132/84.

### Vital signs

| Measure | Value |
|---------|-------|
| BP systolic | 132 |
| BP diastolic | 84 |
| Heart rate | 80 |
| Temperature (F) | 98.4 |
| Respiratory rate | 16 |
| Weight (lbs) | 211 |
| BMI | 29.3 |
| SpO2 (%) | 97 |

### Diagnoses

| Code | Description | Status |
|------|-------------|--------|
| K21.0 | GERD with esophagitis | active |
| F41.1 | Generalized anxiety disorder | active |
| F17.210 | Nicotine dependence, cigarettes | active |

### Lab results

| Test | Value | Reference | Flag |
|------|-------|-----------|------|
| Total Cholesterol | 232 mg/dL | <200 mg/dL | high |
| LDL | 152 mg/dL | <100 mg/dL | high |
| Fasting Glucose | 96 mg/dL | 70-100 mg/dL | normal |

## ENC-2002 — Robert Kim (PT-10078)

**Chief complaint:** Chest tightness and shortness of breath for 2 days

**Clinical notes:** 52-year-old male with history of GERD and anxiety presents
with 2 days of intermittent chest tightness, worse with exertion. Denies
radiation to arm or jaw. Reports occasional SOB climbing stairs. No syncope,
diaphoresis, or palpitations. Family history of MI in father at age 58.
Current smoker, 1 PPD x 20 years. EKG shows normal sinus rhythm, no ST
changes. Troponin negative x2. CXR clear.

### Vital signs

| Measure | Value |
|---------|-------|
| BP systolic | 138 |
| BP diastolic | 86 |
| Heart rate | 92 |
| Temperature (F) | 98.6 |
| Respiratory rate | 18 |
| Weight (lbs) | 215 |
| BMI | 29.8 |
| SpO2 (%) | 96 |

### Diagnoses

| Code | Description | Status |
|------|-------------|--------|
| R07.9 | Chest pain, unspecified | new |
| K21.0 | GERD with esophagitis | active |
| F41.1 | Generalized anxiety disorder | active |
| F17.210 | Nicotine dependence, cigarettes | active |

### Lab results

| Test | Value | Reference | Flag |
|------|-------|-----------|------|
| Troponin I | <0.01 ng/mL | <0.04 ng/mL | normal |
| BNP | 45 pg/mL | <100 pg/mL | normal |
| Total Cholesterol | 248 mg/dL | <200 mg/dL | high |
| LDL | 168 mg/dL | <100 mg/dL | high |

## Flag semantics

| Flag | Treated as abnormal? |
|------|----------------------|
| high | yes |
| borderline | yes |
| normal | no |

Any lab whose flag is not exactly `normal` is abnormal and appears in the
encounter summary's Abnormal Labs table. Normal labs are held in this
document only; they are not surfaced in the summary.

## Prior values available for trending

Each patient has a documented prior encounter, so a value measured at both
encounters has a real prior value in this record set. A trend may be reported
only when both endpoints appear below; nothing else may be trended.

### PT-10045 — Margaret Sullivan (ENC-1990 → ENC-2001)

| Measure | ENC-1990 (2025-09-18) | ENC-2001 (2026-03-12) | Change |
|---------|-----------------------|-----------------------|--------|
| HbA1c | 7.4% | 8.2% | +0.8 |
| Fasting Glucose | 154 mg/dL | 182 mg/dL | +28 mg/dL |
| eGFR | 68 mL/min (normal) | 62 mL/min (borderline) | -6 mL/min |
| Creatinine | 1.0 mg/dL | 1.1 mg/dL | +0.1 mg/dL |
| BP | 138/84 | 148/92 | +10 / +8 |
| Weight (lbs) | 183 | 187 | +4 |
| BMI | 30.5 | 31.2 | +0.7 |

### PT-10078 — Robert Kim (ENC-1991 → ENC-2002)

| Measure | ENC-1991 (2025-10-02) | ENC-2002 (2026-03-14) | Change |
|---------|-----------------------|-----------------------|--------|
| Total Cholesterol | 232 mg/dL | 248 mg/dL | +16 mg/dL |
| LDL | 152 mg/dL | 168 mg/dL | +16 mg/dL |
| BP | 132/84 | 138/86 | +6 / +2 |
| Heart rate | 80 | 92 | +12 |
| Weight (lbs) | 211 | 215 | +4 |
| BMI | 29.3 | 29.8 | +0.5 |

### Measures with no prior value

These were drawn at one encounter only and therefore have no prior value to
trend against: Troponin I (ENC-2002), BNP (ENC-2002), Fasting Glucose for
PT-10078 (ENC-1991 only), and Total Cholesterol / LDL for PT-10045 (drawn at
neither encounter). Say so plainly rather than inferring a direction.
