# Portfolio Holdings Data

> SYNTHETIC — DEMO DATA. Every portfolio, manager, holding, value, and cost
> basis in this document is fictional. This file exists so the agent has a
> working world to answer from on day one. In production, replace this file with
> tools that read your real portfolio accounting and custody systems (see the
> README's production section).

## Portfolios

| ID | Name | Manager | Strategy | Total Value | Benchmark | Rebalance Frequency | Drift Threshold |
|----|------|---------|----------|-------------|-----------|---------------------|-----------------|
| PORT-5001 | Growth Allocation Fund | Victoria Reeves, CFA | growth | $12,450,000 | 60/40 Growth Blend | quarterly | 3.0% |
| PORT-5002 | Conservative Income Portfolio | Daniel Kim, CFP | income | $8,200,000 | 30/70 Income Blend | semi-annual | 2.0% |

## PORT-5001 — Growth Allocation Fund holdings

| Asset | Ticker | Value | Current % | Target % | Cost Basis |
|-------|--------|-------|-----------|----------|------------|
| US Large Cap | VTI | $4,357,500 | 35.0% | 30.0% | $3,800,000 |
| US Small Cap | VB | $872,500 | 7.0% | 10.0% | $750,000 |
| Intl Developed | VEA | $1,493,750 | 12.0% | 15.0% | $1,600,000 |
| Emerging Markets | VWO | $622,500 | 5.0% | 5.0% | $680,000 |
| US Aggregate Bond | BND | $3,112,500 | 25.0% | 25.0% | $3,200,000 |
| TIPS | VTIP | $622,500 | 5.0% | 5.0% | $600,000 |
| REITs | VNQ | $622,500 | 5.0% | 5.0% | $550,000 |
| Cash | VMFXX | $746,250 | 6.0% | 5.0% | $746,250 |

## PORT-5002 — Conservative Income Portfolio holdings

| Asset | Ticker | Value | Current % | Target % | Cost Basis |
|-------|--------|-------|-----------|----------|------------|
| US Large Cap Dividend | VYM | $1,312,000 | 16.0% | 15.0% | $1,100,000 |
| Intl Dividend | VYMI | $656,000 | 8.0% | 10.0% | $700,000 |
| US Investment Grade | VCIT | $2,132,000 | 26.0% | 25.0% | $2,250,000 |
| US Treasury | VGIT | $1,640,000 | 20.0% | 20.0% | $1,700,000 |
| Municipal Bonds | VTEB | $1,148,000 | 14.0% | 15.0% | $1,200,000 |
| High Yield | VWEHX | $492,000 | 6.0% | 5.0% | $460,000 |
| Preferred Stock | PFF | $410,000 | 5.0% | 5.0% | $420,000 |
| Cash | VMFXX | $410,000 | 5.0% | 5.0% | $410,000 |

## Notes on the data

- Cost basis is portfolio-level for the whole position. There is no tax lot
  detail, so lot-level selection cannot be modeled from this file.
- Cash (VMFXX) is carried at cost in both portfolios, so it never shows an
  unrealized gain.
- VEA, VWO, BND, VGIT, VTEB, VCIT, and PFF currently sit below their cost
  basis — they are loss positions.
