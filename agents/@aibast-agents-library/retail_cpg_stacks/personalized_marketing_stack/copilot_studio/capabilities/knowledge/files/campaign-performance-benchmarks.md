# Campaign Performance Benchmarks

> SYNTHETIC — DEMO DATA. Every experiment, conversion count, and revenue figure
> in this document is fictional. This file exists so the agent has a working
> world to answer from on day one. In production, replace this file with tools
> that read your real experimentation platform and marketing finance system
> (see the README's production section).

## A/B test archive

| Test | Campaign | Variant A Subject | A Open | A Click | A Conv. | Variant B Subject | B Open | B Click | B Conv. | Winner | Confidence | Sample |
|------|----------|-------------------|--------|---------|---------|-------------------|--------|---------|---------|--------|------------|--------|
| ABT-001 | CAMP-WINBACK | We miss you — here is 20% off | 18% | 4% | 82 | Come back for something special | 21% | 5% | 107 | B | 94% | 8,500 |
| ABT-002 | CAMP-LOYALTY | You are almost Gold status! | 42% | 15% | 341 | Unlock Gold rewards today | 39% | 13% | 298 | A | 91% | 6,200 |
| ABT-003 | CAMP-VIP | VIP Only: private sale starts now | 58% | 24% | 215 | Your private collection awaits | 61% | 27% | 248 | B | 88% | 3,400 |

CAMP-NEWWELCOME has no test in this archive.

### Conversion lift

`lift = (max(A, B) conversions - min(A, B) conversions) / min(A, B) conversions x 100`

| Test | Campaign | Winner | Confidence | Sample | Lift |
|------|----------|--------|------------|--------|------|
| ABT-001 | Win-Back Journey | Variant B | 94% | 8,500 | +30.5% |
| ABT-002 | Loyalty Tier Upgrade | Variant A | 91% | 6,200 | +14.4% |
| ABT-003 | VIP Exclusive Preview | Variant B | 88% | 3,400 | +15.3% |

No test reaches 95% confidence. Report every winner with its confidence and
sample size.

## Campaign ROI model

Two formulas, no others:

- `Projected Revenue = audience size x historical conversion rate x segment average basket size`
- `Estimated ROAS = Projected Revenue / (audience size x $0.35 contact cost)`

The $0.35 per contact is the only cost input. It excludes creative production,
discount margin, and platform fees, so estimated ROAS is not profit.

| Campaign | Audience | Conv. Rate | Avg Basket | Proj. Revenue | Contact Cost | Est. ROAS |
|----------|----------|------------|------------|---------------|--------------|-----------|
| Win-Back Journey | 34,200 | 1.2% | $106.25 | $43,605.00 | $11,970.00 | 3.64x |
| Loyalty Tier Upgrade | 42,850 | 8.0% | $102.46 | $351,232.88 | $14,997.50 | 23.42x |
| New Customer Welcome | 27,600 | 5.5% | $89.47 | $135,815.46 | $9,660.00 | 14.06x |
| VIP Exclusive Preview | 8,750 | 14.0% | $170.73 | $209,144.25 | $3,062.50 | 68.29x |

**Total Projected Campaign Revenue: $739,797.59**

Highest absolute revenue is CAMP-LOYALTY at $351,232.88; highest efficiency is
CAMP-VIP at 68.29x; lowest on both is CAMP-WINBACK at $43,605.00 and 3.64x.
