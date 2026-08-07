# Supplier Scorecard and Budget Data

> SYNTHETIC — DEMO DATA. Every supplier score, risk rating, and budget line in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real supplier management system and finance/ERP budget ledger (see
> the README's production section).

## Supplier performance scorecard

Sorted by overall score, descending — the only order used in the scorecard.

| Supplier | Overall | Quality | Delivery | Response | Pricing | Innovation | Risk | Total Orders | On-Time |
|----------|---------|---------|----------|----------|---------|------------|------|--------------|---------|
| AWS | 94 | 96 | 92 | 93 | 88 | 97 | Low | 47 | 98.2% |
| CrowdStrike | 92 | 95 | 94 | 91 | 83 | 96 | Low | 6 | 100.0% |
| Deloitte | 91 | 94 | 89 | 90 | 82 | 88 | Low | 8 | 96.5% |
| Herman Miller | 89 | 95 | 85 | 88 | 80 | 85 | Low | 15 | 92.0% |
| Salesforce | 87 | 90 | 88 | 82 | 78 | 92 | Low | 12 | 95.0% |
| PrintPro Services | 78 | 80 | 72 | 75 | 85 | 65 | Medium | 22 | 82.0% |

Scoring methodology: weighted composite — Quality 30%, Delivery 25%,
Responsiveness 20%, Pricing 15%, Innovation 10%. The recorded overall score is
the authority and is reported as-is.

Threshold: overall below 80 is below threshold. PrintPro Services (78) is the
only supplier under it — alert `Below 80 overall - consider alternative
suppliers`. AWS and Salesforce are the strategic accounts and are maintaining
87+ scores.

## Departmental budget allocations

| Department | Annual Budget | Spent | Committed | Remaining | Utilization | Status | Q4 Forecast |
|------------|---------------|-------|-----------|-----------|-------------|--------|-------------|
| IT | $1,800,000 | $1,245,000 | $77,000 | $478,000 | 73% | On Track | $320,000 |
| Marketing | $650,000 | $482,000 | $18,500 | $149,500 | 77% | On Track | $125,000 |
| Finance | $400,000 | $275,000 | $65,000 | $60,000 | 85% | On Track | $80,000 |
| HR | $350,000 | $245,000 | $27,500 | $77,500 | 78% | On Track | $55,000 |
| Sales | $500,000 | $380,000 | $0 | $120,000 | 76% | On Track | $90,000 |

Company position:

| Metric | Value |
|--------|-------|
| Total Budget | $3,700,000 |
| Spent YTD | $2,627,000 (71%) |
| Committed | $188,000 |
| Remaining | $885,000 |

Utilization is `(spent + committed) / annual_budget`. Status is `Over` when
remaining is below zero, `At Risk` when utilization is strictly greater than
85%, otherwise `On Track` — so Finance at exactly 85% computes as On Track.

Standing alerts:

- Finance department at risk: Q4 forecast ($80K) exceeds remaining ($60K).
- IT has sufficient budget for planned Q4 purchases.
