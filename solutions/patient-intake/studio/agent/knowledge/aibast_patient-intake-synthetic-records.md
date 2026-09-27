<!-- Generated from the original workshop knowledge; edit the source and regenerate. -->
> Retained synthetic knowledge. Listed entity fields come from the SharePoint list tools; unlisted records and rules below remain authoritative knowledge. Email omissions are explicit.

# Patient Intake and Scheduling Agent — complete synthetic records

> **Fictional demonstration data only.** These records reproduce the deterministic `PatientIntakeAgent`. Never combine them with live patient information or treat them as current eligibility, appointment, or clinical data.

Entity rows from this section are now read with the SharePoint list tools from **Patient Intake and Scheduling Patient Record**. Other context below remains knowledge.


## Candidate source availability

These are candidate source slots only. Nothing is held, reserved, booked, rescheduled, or changed.

| Provider | Date | Time | Service |
| --- | --- | --- | --- |
| Clinician A | 2026-08-20 | 10:30 | new patient consultation |
| Clinician A | 2026-08-22 | 14:00 | follow-up consultation |
| Clinician B | 2026-08-21 | 09:00 | follow-up consultation |

## Fixed source facts used by the locked cases

- PI-01 uses SYN-PT-001 and must preserve `emergency contact confirmation`.
- PI-02 uses SYN-PT-001 and must preserve `Synthetic Health Plan`, `source record received`, `2026-07-30`, and the exact payer-portal follow-up.
- PI-03 filters to Clinician A and must preserve both Clinician A slots and the statement that nothing has been reserved or booked.
- PI-04 uses SYN-PT-001 and must preserve the new patient consultation with Clinician A on 2026-08-15 plus the authorized patient-access reviewer.
