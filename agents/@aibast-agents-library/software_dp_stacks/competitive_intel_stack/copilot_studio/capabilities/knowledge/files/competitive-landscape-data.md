# Competitive Landscape Data

> SYNTHETIC — DEMO DATA. Every company, share figure, feature flag, and price in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real market intelligence, win/loss, and pricing systems (see the
> README's production section).

## Our company

| Field | Value |
|-------|-------|
| Name | IntelliStack Technologies |
| Market Share | 18.0% |
| Revenue | $228.0M |
| Growth Rate | 32.0% |
| Model Accuracy | 94.2% |
| Average Deal Size | $127,000 |
| Enterprise Win Rate | 67% |
| Mid-Market Win Rate | 31% |
| Overall Win Rate | 38% |
| Data Residency Regions | 12 |

Model accuracy, deal size, win rates, and data residency regions are recorded on
the company profile but are not surfaced by any of the four operations. Quote
them only from this document, and only when asked.

## Tracked competitors

Three competitors are tracked. There are no others.

| ID | Name | Segment | Market Share | Revenue | Growth | Founded | Headcount | Funding | HQ | Threat Level |
|----|------|---------|--------------|---------|--------|---------|-----------|---------|----|--------------|
| COMP-001 | DataFlow AI | Enterprise AI/ML Platform | 24.3% | $312.0M | 41.2% | 2017 | 1,420 | $285.0M | San Francisco, CA | high |
| COMP-002 | NeuralStack | Vertical AI Solutions | 15.8% | $198.0M | 28.5% | 2018 | 870 | $195.0M | Boston, MA | medium |
| COMP-003 | Quantum ML | Open Core ML Platform | 11.2% | $142.0M | 55.8% | 2019 | 540 | $120.0M | Austin, TX | medium |

## Market sizing

| Field | Value |
|-------|-------|
| Tracked revenue (three competitors + us) | $880.0M |
| Coverage assumption (divisor) | 0.692 |
| Total addressable market | $1,271.7M, reported as $1272M |
| Our reported position | #2 |
| Our reported share | 18.0% |

Note: the four profiled shares sum to 69.3%, while the sizing divisor is 0.692.
The divisor is authoritative for the TAM figure; do not re-derive it.

## Feature matrix

Eight tracked features. Coverage is always reported out of 8.

| Feature | Us | DataFlow AI | NeuralStack | Quantum ML |
|---------|----|-------------|-------------|------------|
| AutoML | YES | YES | YES | YES |
| No-Code UI | NO | YES | NO | YES |
| Model Monitoring | YES | YES | YES | NO |
| Explainability | YES | NO | YES | YES |
| On-Prem Deployment | YES | NO | YES | YES |
| SOC2 Type II | YES | YES | YES | NO |
| HIPAA Compliance | YES | NO | YES | NO |
| FedRAMP Authorization | YES | NO | NO | NO |
| **Coverage** | **7/8** | **4/8** | **6/8** | **4/8** |

## Pricing tiers (USD per month)

| Tier | Us | DataFlow AI | NeuralStack | Quantum ML |
|------|----|-------------|-------------|------------|
| Starter | $1,499 | $999 | $1,299 | $0 |
| Professional | $3,499 | $2,999 | $3,299 | $1,999 |
| Enterprise | $6,999 | $4,999 | $5,999 | $3,999 |

### Computed gaps

`gap_pct = round(((our_price - their_price) / their_price) * 100, 1)`, with
`gap_pct = 0` when the competitor price is $0.

| Tier | Competitor | Our Price | Their Price | Gap |
|------|-----------|-----------|-------------|-----|
| Starter | DataFlow AI | $1,499/mo | $999/mo | +50.1% |
| Starter | NeuralStack | $1,499/mo | $1,299/mo | +15.4% |
| Starter | Quantum ML | $1,499/mo | $0/mo | +0.0% |
| Professional | DataFlow AI | $3,499/mo | $2,999/mo | +16.7% |
| Professional | NeuralStack | $3,499/mo | $3,299/mo | +6.1% |
| Professional | Quantum ML | $3,499/mo | $1,999/mo | +75.0% |
| Enterprise | DataFlow AI | $6,999/mo | $4,999/mo | +40.0% |
| Enterprise | NeuralStack | $6,999/mo | $5,999/mo | +16.7% |
| Enterprise | Quantum ML | $6,999/mo | $3,999/mo | +75.0% |

Average price gap across the nine comparisons: **32.8% above competitors**. The
Quantum ML starter row is a divide-by-zero guard reported as +0.0%; it is not
price parity.
