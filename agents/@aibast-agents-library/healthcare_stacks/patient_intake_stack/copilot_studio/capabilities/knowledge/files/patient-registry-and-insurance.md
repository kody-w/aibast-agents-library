# Patient Registry and Insurance Coverage

> SYNTHETIC - DEMO DATA. Every patient, payer, member ID, and phone number in
> this document is fictional. No real person is represented. This file exists
> so the agent has a working world to answer from on day one. In production,
> replace this file with tools that read your real practice management system,
> registration records, and payer eligibility service (see the README's
> production section).

## Patient registry

| Patient ID | Name | DOB | Gender | Phone | Email | Address | Primary Language | Race | Ethnicity |
|------------|------|-----|--------|-------|-------|---------|------------------|------|-----------|
| PT-20001 | Jennifer Walsh | 1978-04-22 | Female | 555-0142 | j.walsh@email.com | 142 Oak Street, Springfield, IL 62701 | English | White | Non-Hispanic |
| PT-20002 | David Nguyen | 1992-11-08 | Male | 555-0255 | d.nguyen@email.com | 88 Maple Avenue, Springfield, IL 62702 | English | Asian | Non-Hispanic |
| PT-20003 | Maria Gonzalez | 1965-07-15 | Female | 555-0388 | m.gonzalez@email.com | 305 Elm Drive, Springfield, IL 62703 | Spanish | White | Hispanic |

## Emergency contacts

| Patient ID | Patient | Contact Name | Relation | Phone |
|------------|---------|--------------|----------|-------|
| PT-20001 | Jennifer Walsh | Michael Walsh | Spouse | 555-0143 |
| PT-20002 | David Nguyen | Linh Nguyen | Mother | 555-0256 |
| PT-20003 | Maria Gonzalez | Carlos Gonzalez | Son | 555-0389 |

## Primary insurance plans

| Patient ID | Payer | Plan | Member ID | Group | Effective | Office Copay | Specialist Copay | Deductible | Deductible Met | Coinsurance | Status | Last Verified |
|------------|-------|------|-----------|-------|-----------|--------------|------------------|------------|----------------|-------------|--------|---------------|
| PT-20001 | Blue Cross Blue Shield of Illinois | PPO Gold | BCBS-884721 | GRP-44210 | 2025-01-01 | $25 | $50 | $1,500 | $875 | 20% | verified | 2026-03-10 |
| PT-20002 | Aetna | HMO Select | AET-552190 | GRP-88104 | 2025-07-01 | $20 | $40 | $2,000 | $320 | 25% | verified | 2026-03-12 |
| PT-20003 | Medicare Part B | Original Medicare | 1EG4-TE5-MK72 | N/A | 2025-07-15 | $0 | $0 | $257 | $257 | 20% | verified | 2026-03-14 |

Remaining deductible is `deductible - deductible_met`, floored at zero:

| Patient ID | Patient | Arithmetic | Remaining |
|------------|---------|------------|-----------|
| PT-20001 | Jennifer Walsh | 1500 - 875 | $625 |
| PT-20002 | David Nguyen | 2000 - 320 | $1,680 |
| PT-20003 | Maria Gonzalez | 257 - 257 | $0 |

## Secondary insurance plans

Only one patient carries a secondary policy. PT-20001 and PT-20002 have none.

| Patient ID | Payer | Plan | Member ID | Group | Effective | Status | Last Verified |
|------------|-------|------|-----------|-------|-----------|--------|---------------|
| PT-20003 | AARP Medigap Plan F | Supplemental | AARP-MG-88421 | N/A | 2025-07-15 | pending | none |

The PT-20003 secondary is unverified. It contributes nothing to the copay or
remaining-deductible figures, which are primary-only.
