# Contract Portfolio Data

> SYNTHETIC -- DEMO DATA. Every client, contract, clause, and date in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real contract lifecycle management system and clause library (see the
> README's production section).

## Contract portfolio

| Contract | Client | Type | Value | Term (months) | Governing Law | Renewal Date | Risk Score | Pages | Status |
|----------|--------|------|-------|---------------|---------------|--------------|------------|-------|--------|
| CTR-5001 | NovaTech Systems | Master Services Agreement | $25,000,000 | 36 | Delaware | 2028-06-30 | 6.5/10 | 47 | under_review |
| CTR-5002 | Meridian Healthcare | Statement of Work | $4,200,000 | 18 | New York | 2027-09-15 | 3.8/10 | 22 | active |
| CTR-5003 | Atlas Financial Group | Master Services Agreement | $12,000,000 | 24 | California | 2027-12-01 | 5.2/10 | 38 | active |
| CTR-5004 | Orion Defense Systems | IDIQ Task Order | $8,500,000 | 60 | Federal (FAR) | 2030-03-31 | 4.1/10 | 64 | active |

Portfolio totals: 4 contracts, $49,700,000 total value. Contracts at elevated
risk (`risk_score >= 5.0`): CTR-5001 and CTR-5003, $37,000,000 combined.

## Clause register -- CTR-5001, NovaTech Systems

3 HIGH, 3 MEDIUM risk clauses.

| Section | Clause | Risk | Issue | Recommendation |
|---------|--------|------|-------|----------------|
| 7.1 | Liability Cap | HIGH | Cap limited to fees paid in preceding 12 months ($2-8M range); no carve-outs for IP or data breach | Increase to annual contract value ($8.3M minimum) with carve-outs |
| 8.2 | IP Ownership | HIGH | All work product assigned to client including improvements and derivatives; no pre-existing IP protection | Carve out pre-existing IP; add license-back for client-specific derivatives |
| 9.4 | Payment Terms | MEDIUM | Net 60 days vs company standard Net 30; creates $1.4M cash-flow delay | Negotiate to Net 30 or Net 45 with early-pay discount |
| 12.1 | Termination | HIGH | Client may terminate immediately for any breach with no cure period | Add 30-day cure period for non-material breaches |
| 14.3 | SLA Penalties | MEDIUM | Penalties uncapped; could exceed monthly fees in extreme scenarios | Cap penalties at 10% of monthly fees |
| 15.2 | Change Orders | MEDIUM | Verbal change approvals accepted; creates scope-creep exposure | Require written change orders signed by authorized representatives |

## Clause register -- CTR-5003, Atlas Financial Group

1 HIGH, 2 MEDIUM risk clauses.

| Section | Clause | Risk | Issue | Recommendation |
|---------|--------|------|-------|----------------|
| 5.1 | Indemnification | HIGH | One-sided indemnification; we indemnify client but no reciprocal obligation | Add mutual indemnification clause |
| 6.3 | Data Handling | MEDIUM | No data destruction timeline after engagement ends; liability lingers | Add 90-day data destruction clause with certification |
| 11.2 | Non-Compete | MEDIUM | 12-month non-compete for similar engagements in financial services sector | Narrow scope to specific sub-sector or reduce to 6 months |

## Contracts with no clause record

CTR-5002 (Meridian Healthcare) and CTR-5004 (Orion Defense Systems) have no
clauses entered in the register. That is unreviewed scope, not a clean review.
Any compliance PASS for these two contracts reflects the absence of records
only.

## Renewal calendar

| Contract | Client | Renewal Date | Days Out | Action |
|----------|--------|--------------|----------|--------|
| CTR-5002 | Meridian Healthcare | 2027-09-15 | 547 | Begin renewal discussions Q1 2027 |
| CTR-5003 | Atlas Financial Group | 2027-12-01 | 624 | Address risk clauses before renewal |
| CTR-5001 | NovaTech Systems | 2028-06-30 | 835 | Renegotiate critical terms at Year-2 review |
| CTR-5004 | Orion Defense Systems | 2030-03-31 | 1474 | Option-year review in 2028 |
