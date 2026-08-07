# Provider Schedules and Intake Questionnaires

> SYNTHETIC - DEMO DATA. Every provider, location, and open slot in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that
> read your real scheduling system and questionnaire library (see the README's
> production section).

## Providers

| Provider | Specialty | Location | Open Slots |
|----------|-----------|----------|------------|
| Dr. Anita Patel | Internal Medicine | Main Clinic - Suite 200 | 4 |
| Dr. James Wright | Family Medicine | Main Clinic - Suite 105 | 3 |
| Dr. Sarah Lin | Cardiology | Cardiology Center - Suite 400 | 2 |

## Open appointment slots

9 slots total, sorted by date then time - the order the agent presents them in.

| Date | Time | Provider | Specialty | Location | Duration | Type |
|------|------|----------|-----------|----------|----------|------|
| 2026-03-18 | 09:00 | Dr. Anita Patel | Internal Medicine | Main Clinic - Suite 200 | 30min | follow_up |
| 2026-03-18 | 10:30 | Dr. Anita Patel | Internal Medicine | Main Clinic - Suite 200 | 60min | new_patient |
| 2026-03-18 | 11:00 | Dr. James Wright | Family Medicine | Main Clinic - Suite 105 | 30min | follow_up |
| 2026-03-19 | 09:30 | Dr. James Wright | Family Medicine | Main Clinic - Suite 105 | 60min | new_patient |
| 2026-03-19 | 14:00 | Dr. Anita Patel | Internal Medicine | Main Clinic - Suite 200 | 30min | follow_up |
| 2026-03-19 | 15:00 | Dr. James Wright | Family Medicine | Main Clinic - Suite 105 | 30min | follow_up |
| 2026-03-20 | 08:30 | Dr. Anita Patel | Internal Medicine | Main Clinic - Suite 200 | 60min | new_patient |
| 2026-03-20 | 10:00 | Dr. Sarah Lin | Cardiology | Cardiology Center - Suite 400 | 45min | consultation |
| 2026-03-21 | 13:00 | Dr. Sarah Lin | Cardiology | Cardiology Center - Suite 400 | 45min | consultation |

Slot types and their fixed durations in this schedule: `follow_up` 30min,
`new_patient` 60min, `consultation` 45min (Cardiology only).

## Intake questionnaires

Section lists and expected completion time. These are the sections a patient
would be asked to complete - this file holds no patient responses.

| Questionnaire | Sections | Section Count | Estimated Time |
|---------------|----------|---------------|----------------|
| new_patient | Demographics; Medical History; Surgical History; Family History; Social History; Medications; Allergies; Review of Systems | 8 | 15 min |
| follow_up | Medication Changes; New Symptoms; Vital Signs Update | 3 | 5 min |
| annual_wellness | Demographics Update; Health Risk Assessment; PHQ-9 Depression Screen; Fall Risk Assessment; Advance Directives; Preventive Services Review | 6 | 20 min |

## What this data does not contain

There are no completed questionnaire responses, medication lists, allergy
lists, diagnoses, lab results, vital signs, booked appointments, or visit
history anywhere in this demo world. A question about any of those is
answered by saying the data is not available.
