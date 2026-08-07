# Customer Ownership and Product Catalog

> SYNTHETIC — DEMO DATA. Every customer, contact, price, and ARR figure in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real CRM and product database (see the README's production section).

## Product catalog

| ID | Product | Category | Annual Price | Margin % |
|----|---------|----------|--------------|----------|
| PLAT-100 | Core Platform | Platform | $24,000 | 72 |
| PLAT-200 | Enterprise Platform | Platform | $60,000 | 75 |
| ANLYT-100 | Analytics Standard | Analytics | $12,000 | 82 |
| ANLYT-200 | Analytics Pro | Analytics | $28,000 | 85 |
| INTGR-100 | Integration Hub | Integration | $18,000 | 78 |
| SECUR-100 | Security Suite | Security | $15,000 | 80 |
| SUPRT-100 | Premium Support | Support | $8,000 | 90 |
| TRAIN-100 | Training Package | Services | $5,000 | 65 |

TRAIN-100 Training Package is in the catalog but is not the target of any
affinity rule, so it never appears as a cross-sell recommendation.

## Customer ownership

| ID | Customer | Segment | Current ARR | Products Owned | Tenure (months) | Health Score | Contact |
|----|----------|---------|-------------|----------------|-----------------|--------------|---------|
| CUST-001 | Meridian Corp | Enterprise | $84,000 | PLAT-200, ANLYT-100, SUPRT-100 | 24 | 92 | Sandra Lee |
| CUST-002 | Atlas Digital | Mid-Market | $42,000 | PLAT-100, INTGR-100 | 18 | 78 | Marco Torres |
| CUST-003 | Pinnacle Health | Enterprise | $60,000 | PLAT-200 | 6 | 85 | Dr. Amy Patel |
| CUST-004 | Greenleaf Retail | Mid-Market | $24,000 | PLAT-100 | 12 | 65 | Kevin O'Neill |
| CUST-005 | Beacon Financial | Enterprise | $113,000 | PLAT-200, ANLYT-200, INTGR-100, SECUR-100 | 36 | 96 | Rachel Kim |

These five customers are the complete book. Any account not listed here has no
data - say so rather than reporting another customer's numbers.

## Ownership notes

- Beacon Financial (CUST-005) owns four of the eight catalog products and is
  the most saturated account: only Premium Support remains reachable by rule.
- Pinnacle Health (CUST-003) owns a single product (PLAT-200) at 6 months
  tenure - the newest account and the widest open surface among Enterprise
  customers.
- Greenleaf Retail (CUST-004) carries the lowest health score (65/100); its
  potential cross-sell ARR ($38,000) exceeds its current ARR ($24,000).
