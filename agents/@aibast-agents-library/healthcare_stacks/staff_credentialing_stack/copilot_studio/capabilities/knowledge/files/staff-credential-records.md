# Staff Credential Records

> SYNTHETIC — DEMO DATA. Every staff member, license number, DEA registration,
> NPI, and policy number in this document is fictional. This file exists so the
> agent has a working world to answer from on day one. In production, replace
> this file with tools that read your real credentialing system, primary source
> verification service, and CME tracker (see the README's production section).

## Staff roster

| ID | Name | Role | NPI | Hire Date | Credentials | Active | Expired |
|----|------|------|-----|-----------|-------------|--------|---------|
| STAFF-001 | Dr. Anita Patel | Physician - Internal Medicine | 1234567890 | 2019-06-15 | 5 | 5 | 0 |
| STAFF-002 | Dr. James Wright | Physician - Family Medicine | 9876543210 | 2021-01-10 | 4 | 4 | 0 |
| STAFF-003 | Lisa Chen, RN | Registered Nurse | 5551234567 | 2022-08-01 | 4 | 3 | 1 |
| STAFF-004 | Mark Johnson, PA-C | Physician Assistant | 4449876543 | 2023-03-15 | 4 | 3 | 1 |

## Credentials on file

| Staff ID | Staff Member | Credential | Issuer | Number | Issued | Expires | Status | Verified |
|----------|-------------|------------|--------|--------|--------|---------|--------|----------|
| STAFF-001 | Dr. Anita Patel | Medical License | Illinois DFPR | 036-123456 | 2023-07-01 | 2026-06-30 | active | YES |
| STAFF-001 | Dr. Anita Patel | DEA Registration | DEA | AP1234567 | 2024-01-15 | 2027-01-14 | active | YES |
| STAFF-001 | Dr. Anita Patel | Board Certification - Internal Medicine | ABIM | ABIM-884210 | 2020-09-01 | 2030-08-31 | active | YES |
| STAFF-001 | Dr. Anita Patel | BLS Certification | AHA | BLS-29401 | 2025-03-10 | 2027-03-10 | active | YES |
| STAFF-001 | Dr. Anita Patel | ACLS Certification | AHA | ACLS-18822 | 2024-11-05 | 2026-11-05 | active | YES |
| STAFF-002 | Dr. James Wright | Medical License | Illinois DFPR | 036-654321 | 2024-07-01 | 2027-06-30 | active | YES |
| STAFF-002 | Dr. James Wright | DEA Registration | DEA | JW9876543 | 2023-05-20 | 2026-05-19 | active | YES |
| STAFF-002 | Dr. James Wright | Board Certification - Family Medicine | ABFM | ABFM-552104 | 2021-12-01 | 2031-11-30 | active | YES |
| STAFF-002 | Dr. James Wright | BLS Certification | AHA | BLS-30218 | 2024-08-22 | 2026-08-22 | active | YES |
| STAFF-003 | Lisa Chen, RN | RN License | Illinois DFPR | 041-789012 | 2024-05-31 | 2026-05-31 | active | YES |
| STAFF-003 | Lisa Chen, RN | BLS Certification | AHA | BLS-41092 | 2025-01-15 | 2027-01-15 | active | YES |
| STAFF-003 | Lisa Chen, RN | ACLS Certification | AHA | ACLS-22104 | 2024-06-10 | 2026-06-10 | active | YES |
| STAFF-003 | Lisa Chen, RN | PALS Certification | AHA | PALS-15580 | 2023-09-20 | 2025-09-20 | expired | NO |
| STAFF-004 | Mark Johnson, PA-C | PA License | Illinois DFPR | 085-345678 | 2023-03-01 | 2026-02-28 | expired | NO |
| STAFF-004 | Mark Johnson, PA-C | NCCPA Certification | NCCPA | NCCPA-778410 | 2023-01-01 | 2033-12-31 | active | YES |
| STAFF-004 | Mark Johnson, PA-C | DEA Registration | DEA | MJ3456789 | 2023-04-01 | 2026-03-31 | active | YES |
| STAFF-004 | Mark Johnson, PA-C | BLS Certification | AHA | BLS-52201 | 2025-06-20 | 2027-06-20 | active | YES |

17 credentials total, 15 verified — a verification rate of 88.2%.

## Continuing medical education

| Staff ID | Staff Member | Required Hrs | Completed Hrs | Progress |
|----------|-------------|--------------|---------------|----------|
| STAFF-001 | Dr. Anita Patel | 50 | 38 | 76.0% |
| STAFF-002 | Dr. James Wright | 50 | 52 | 104.0% |
| STAFF-003 | Lisa Chen, RN | 20 | 14 | 70.0% |
| STAFF-004 | Mark Johnson, PA-C | 100 | 68 | 68.0% |

## Malpractice coverage

| Staff ID | Staff Member | Carrier | Policy | Expires | Coverage ($MM) |
|----------|-------------|---------|--------|---------|----------------|
| STAFF-001 | Dr. Anita Patel | ProAssurance | PA-2025-44821 | 2026-12-31 | 1.0 |
| STAFF-002 | Dr. James Wright | Coverys | COV-2025-91024 | 2026-12-31 | 1.0 |
| STAFF-003 | Lisa Chen, RN | NSO | NSO-2025-67210 | 2026-06-30 | 0.5 |
| STAFF-004 | Mark Johnson, PA-C | HPSO | HPSO-2025-33104 | 2026-09-30 | 0.5 |

Malpractice policies carry no status field and are never counted as active or
expired credentials. The records hold no premium, deductible, or tail-coverage
cost figures.
