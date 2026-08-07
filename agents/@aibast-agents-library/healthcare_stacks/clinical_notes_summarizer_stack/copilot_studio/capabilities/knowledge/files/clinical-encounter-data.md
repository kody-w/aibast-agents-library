# Clinical Encounter Data

> SYNTHETIC — DEMO DATA. Every patient, provider, encounter, and lab value in
> this document is fictional. No real protected health information appears
> here. This file exists so the agent has a working world to answer from on
> day one. In production, replace this file with tools that read your real EHR
> encounter, vitals, and results feeds (see the README's production section).

## Encounter index

| Encounter ID | Patient ID | Patient | Age | Gender | Date | Type | Provider |
|--------------|------------|---------|-----|--------|------|------|----------|
| ENC-2001 | PT-10045 | Margaret Sullivan | 68 | Female | 2026-03-12 | Office Visit | Dr. Anita Patel |
| ENC-2002 | PT-10078 | Robert Kim | 52 | Male | 2026-03-14 | Urgent Care | Dr. James Wright |

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
