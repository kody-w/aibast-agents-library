<!-- Generated from the original workshop knowledge; edit the source and regenerate. -->
> Retained synthetic knowledge. Listed entity fields come from the SharePoint list tools; unlisted records and rules below remain authoritative knowledge. Email omissions are explicit.

# Clinical Notes Summarizer Agent — complete synthetic records

> **Fictional demonstration data only.** These records reproduce the deterministic `ClinicalNotesSummarizerAgent`. Never combine them with live patient information or treat them as diagnosis, treatment, clearance, urgency, or a record update.

Entity rows from this section are now read with the SharePoint list tools from **Clinical Notes Summarizer Encounter**. Other context below remains knowledge.


## Fixed source facts used by the locked cases

- CN-01 must preserve SYN-ENC-001, 2026-07-28, the exact source note, both exact observations, and `Clinical interpretation: not performed; clinician review required.`
- CN-02 must preserve `Metformin 1000 mg twice daily`, `Lisinopril 20 mg daily`, and clinician/pharmacist reconciliation review.
- CN-03 must preserve `source-coded type 2 diabetes`, `source-coded hypertension`, `knee discomfort`, and `No diagnosis was added, confirmed, or changed.`
- CN-04 must preserve `Orthopedics referral draft recorded; status not confirmed.`, `No referral was placed, scheduled, or changed.`, and authorized clinician/staff review.
