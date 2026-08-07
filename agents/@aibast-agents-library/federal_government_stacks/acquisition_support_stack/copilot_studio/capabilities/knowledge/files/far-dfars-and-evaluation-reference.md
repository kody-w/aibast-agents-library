# FAR, DFARS, and Evaluation Reference

> SYNTHETIC — DEMO DATA. The thresholds, provisions, and criterion weights
> below are a fictional demo reference, not the authoritative FAR or DFARS. This
> file exists so the agent has a working world to answer from on day one. In
> production, replace this file with tools that read your agency's current
> clause matrix and source selection plan (see the README's production section).

## FAR requirements and applicability thresholds

A FAR part applies to a procurement when its estimated value is greater than or
equal to the threshold below.

| Reference | Title | Threshold | Description |
|-----------|-------|-----------|-------------|
| FAR 15.3 | Source Selection | $1,000,000 | Policies and procedures for negotiated competitive acquisitions |
| FAR 19.5 | Small Business Set-Asides | $250,000 | Requirements for setting aside acquisitions for small businesses |
| FAR 12.6 | Commercial Item Streamlining | $7,500,000 | Streamlined procedures for acquiring commercial items |
| FAR 8.4 | Federal Supply Schedules | $0 | Ordering procedures under GSA Federal Supply Schedules |

### Key provisions

| Reference | Key provisions |
|-----------|----------------|
| FAR 15.3 | Evaluation factors must be stated in solicitation; Cost/price evaluation required for all competitive acquisitions; Past performance must be evaluated for acquisitions over $1M |
| FAR 19.5 | Acquisitions between $10K-$250K reserved for small business; Market research required to identify small business capability; SBA size standards apply by NAICS code |
| FAR 12.6 | Use of simplified evaluation procedures permitted; Standard commercial warranties acceptable; Reduced documentation requirements for commercial items |
| FAR 8.4 | Three or more quotes required for orders over micro-purchase; Best value determination required; Statement of work required for services |

## DFARS supplements

These are listed on every compliance checklist regardless of acquisition value.

| Reference | Title | Applicability | Compliance Standard | Assessment |
|-----------|-------|---------------|---------------------|------------|
| DFARS 252.204-7012 | Safeguarding Covered Defense Information | All DoD contracts with CDI | NIST SP 800-171 | Required |
| DFARS 252.204-7021 | CMMC Requirements | DoD contracts requiring CMMC certification | CMMC Level 2 | Required |
| DFARS 215.403-1 | Certified Cost or Pricing Data | Acquisitions exceeding $2M threshold | TINA | Not Required |

## Evaluation criteria and weights

Weights sum to 100. Each criterion is scored 0-100 before weighting.

| Criterion | Weight | Max Score |
|-----------|--------|-----------|
| Technical approach | 35 | 100 |
| Past performance | 25 | 100 |
| Cost / price | 20 | 100 |
| Management approach | 10 | 100 |
| Small business plan | 10 | 100 |

### Criterion derivation

| Criterion | How the 0-100 value is derived |
|-----------|--------------------------------|
| Technical approach | The proposal's recorded technical score, used as-is |
| Past performance | Highly Satisfactory = 95, Satisfactory = 80, Neutral = 60, Unsatisfactory = 30, anything else = 50 |
| Cost / price | `max(0, 100 - (proposal_amount / 100000))` |
| Management approach | `min(100, technical_score * 0.9)` |
| Small business plan | 90 for a small business, 60 otherwise |

Weighted composite score = the sum of each criterion value times its weight,
divided by 100, rounded to 2 decimals.

### Worked composite scores for the current proposal set

| Proposal | Technical | Past Perf. | Cost/Price | Mgmt | Small Bus. | Weighted Score |
|----------|-----------|------------|------------|------|------------|----------------|
| VP-2025-002 | 91.2 | 95 | 60.2 | 82.08 | 90 | 84.92 |
| VP-2025-001 | 88.5 | 80 | 52.5 | 79.65 | 60 | 75.44 |
| VP-2025-003 | 85.0 | 80 | 48.8 | 76.5 | 60 | 73.16 |
| VP-2025-004 | 79.8 | 60 | 58.0 | 71.82 | 90 | 70.71 |
