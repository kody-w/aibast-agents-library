# Fraud Scoring and Settlement Policy

> SYNTHETIC — DEMO DATA. The indicator weights and settlement rules below are
> fictional and exist so the agent has a working world to answer from on day
> one. In production, replace this file with tools that read your real fraud
> model and settlement authority matrix (see the README's production section).

## Fraud indicator reference

| Indicator | Weight | Description |
|-----------|--------|-------------|
| Financial Stress | 15 | Claimant shows signs of recent financial distress |
| Claim Timing | 12 | Claim filed shortly after policy inception or increase in coverage |
| Excessive Amount | 20 | Claimed amount significantly exceeds typical loss for category |
| Inconsistent Narrative | 18 | Inconsistencies between claimant statement and evidence |
| Prior Claims History | 10 | Multiple prior claims on same or similar policies |
| Delayed Reporting | 8 | Significant delay between loss event and claim filing |
| Witness Issues | 12 | Lack of independent witnesses or corroborating evidence |
| Documentation Gaps | 15 | Missing or incomplete supporting documentation |

Excessive Amount (20) is the heaviest indicator; Delayed Reporting (8) is the
lightest. The stored `fraud_score` on each claim is the score of record — the
table above explains what drives scores and is not re-summed per claim.

## Fraud score bands

| Band | Range | Flagged | SIU referral | Settlement effect |
|------|-------|---------|--------------|-------------------|
| Low | 0-29 | No | No | Full net amount |
| Flagged | 30-59 | Yes | No | Net amount reduced to 75% |
| High risk | 60-100 | Yes | Yes | Settlement recommendation $0, hold pending SIU |

## Settlement calculation

Applied in this order for every claim:

1. If `fraud_score >= 60` the recommended settlement is `$0`. No further
   arithmetic.
2. `net = min(claimed_amount, coverage_limit) - deductible`.
3. If `fraud_score >= 30`, `net = net * 0.75` (rounded to 2 decimals).
4. Recommended settlement = `max(0, net)`.

A missing policy record means coverage limit and deductible are both treated as
0, which forces the recommendation to $0 — that is a data gap, not a fraud
decision.

## Current settlement position

| Claim ID | Claimant | Claimed | Deductible | Fraud Score | Rule applied | Recommended |
|----------|----------|---------|------------|-------------|--------------|-------------|
| CLM-2025-7001 | Margaret Sullivan | $28,500 | $1,500 | 12 | Low band, full net | $27,000 |
| CLM-2025-7002 | David Park | $14,200 | $500 | 5 | Low band, full net | $13,700 |
| CLM-2025-7003 | Apex Commercial Properties | $485,000 | $10,000 | 68 | High risk, hold pending SIU | $0 |
| CLM-2025-7004 | Jennifer Liu | $42,000 | $2,000 | 45 | Flagged, 75% of net | $30,000 |

- Total Claimed: $569,700
- Total Recommended Settlement: $70,700
- Savings from Adjustments: $499,000

## Authority boundary

The agent recommends. Approving, denying, closing, referring to SIU, and
issuing payment are adjuster and SIU actions performed in the claims system —
never by the agent, and never described by the agent as already done.
