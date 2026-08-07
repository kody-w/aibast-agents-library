# Customer Onboarding Data

> SYNTHETIC — DEMO DATA. Every applicant, application, screening result, and
> account balance in this document is fictional. This file exists so the agent
> has a working world to answer from on day one. In production, replace this
> file with tools that read your real onboarding system, KYC vendor results,
> and core banking product catalog (see the README's production section).

## Customer applications

| App ID | Applicant | Type | Account Requested | Submitted | Status | Risk Rating | Relationship Manager | Est. Assets |
|--------|-----------|------|-------------------|-----------|--------|-------------|----------------------|-------------|
| APP-6001 | Sarah Chen | individual | premium_checking | 2025-02-20 | kyc_in_progress | low | Michael Torres | $250,000 |
| APP-6002 | Blackwood Capital Partners LLC | business | commercial_checking | 2025-02-25 | document_review | medium | Jessica Nguyen | $2,400,000 |
| APP-6003 | Ahmed Al-Rashid | individual | wealth_management | 2025-03-01 | enhanced_due_diligence | high | Jessica Nguyen | $5,800,000 |
| APP-6004 | Maria Fontaine | individual | basic_savings | 2025-03-05 | approved | low | Michael Torres | $15,000 |

Pipeline totals: 4 applications, $8,465,000 total estimated assets, one
application in each of the four statuses.

## KYC verification results

Each application carries only the checks listed for it. The completion
percentage counts the checks recorded as `complete` or `clear` over the total
checks on file for that application.

### APP-6001 — Sarah Chen (5 of 6 = 83.3%)

| Check | Status |
|-------|--------|
| id_verification | complete |
| ssn_verification | complete |
| address_verification | pending |
| ofac_screening | clear |
| pep_screening | clear |
| adverse_media | clear |

### APP-6002 — Blackwood Capital Partners LLC (5 of 6 = 83.3%)

| Check | Status |
|-------|--------|
| id_verification | complete |
| ein_verification | complete |
| beneficial_ownership | in_progress |
| ofac_screening | clear |
| pep_screening | clear |
| adverse_media | clear |

### APP-6003 — Ahmed Al-Rashid (4 of 7 = 57.1%)

| Check | Status |
|-------|--------|
| id_verification | complete |
| ssn_verification | complete |
| address_verification | complete |
| ofac_screening | clear |
| pep_screening | flagged |
| adverse_media | review_needed |
| source_of_wealth | pending |

APP-6003 is rated high risk, so enhanced due diligence applies: source of
wealth verification, PEP relationship documentation, and enhanced transaction
monitoring parameters.

### APP-6004 — Maria Fontaine (6 of 6 = 100.0%)

| Check | Status |
|-------|--------|
| id_verification | complete |
| ssn_verification | complete |
| address_verification | complete |
| ofac_screening | clear |
| pep_screening | clear |
| adverse_media | clear |

## Account product catalog

| Account Type | Min Deposit | Monthly Fee | APY | Features |
|--------------|-------------|-------------|-----|----------|
| basic_savings | $25 | $0 | 0.50% | Online banking, Mobile deposit, ATM access |
| premium_checking | $1,000 | $12 | 0.15% | No ATM fees, Overdraft protection, Bill pay, Cashback rewards |
| commercial_checking | $5,000 | $25 | 0.10% | Treasury management, ACH origination, Wire transfers, Merchant services |
| wealth_management | $250,000 | $0 | 1.25% | Dedicated advisor, Investment management, Trust services, Concierge banking |

## Pipeline statuses

| Status | Meaning | Cleared for account setup |
|--------|---------|---------------------------|
| kyc_in_progress | Identity and screening checks still running | No |
| document_review | Submitted documents under review | No |
| enhanced_due_diligence | High-risk review; EDD items outstanding | No |
| approved | Cleared to open the requested account | Yes |
