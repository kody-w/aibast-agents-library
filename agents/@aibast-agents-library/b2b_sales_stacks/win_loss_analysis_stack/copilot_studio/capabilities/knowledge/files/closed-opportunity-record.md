# Closed Opportunity Record — Q3 and Q2

> SYNTHETIC — DEMO DATA

This file is the synthetic closed-opportunity record the agent answers from.
In production it is removed and replaced with tools reading the live CRM, Gong
call analysis, and the win/loss survey platform. Nothing here is a real
customer, deal, or competitor.

## Quarter totals

| Metric | Q3 | Q2 |
|---|---|---|
| Closed opportunities | 127 | 118 |
| Won | 49 | 53 |
| Lost | 78 | 65 |
| Win rate | 38.6% | 44.9% |
| Total won value | $8,433,000 | $10,043,000 |
| Total lost value | $23,368,000 | $15,060,000 |
| Average won deal size | $172,102 | $189,490 |

Win rate = `won / total`, rounded to one decimal. Average won deal size =
`int(total won value / won count)`.

## Win rate by segment

| Segment | Q3 total | Q3 won | Q3 win rate | Q2 total | Q2 won | Q2 win rate | Change |
|---|---|---|---|---|---|---|---|
| Enterprise | 40 | 8 | 20.0% | 30 | 12 | 40.0% | -20.0 pts |
| Mid-Market | 57 | 18 | 31.6% | 58 | 18 | 31.0% | +0.6 pts |
| Smb | 30 | 23 | 76.7% | 30 | 23 | 76.7% | +0.0 pts |

## Q3 deal size distribution

| Deal size bucket | Opportunities | Won | Win rate |
|---|---|---|---|
| 500K+ | 15 | 3 | 20.0% |
| 250K-500K | 31 | 7 | 22.6% |
| 100K-250K | 53 | 16 | 30.2% |
| <100K | 28 | 23 | 82.1% |

## Q3 losses by competitor

Losses with no competitor recorded are bucketed as **No Decision**. Percentages
are of all 78 Q3 losses.

| Competitor | Losses | % of Q3 losses | Lost pipeline | Q2 losses | Q2 % of losses | Trend |
|---|---|---|---|---|---|---|
| CompetitorX | 29 | 37.2% | $14,110,000 | 15 | 23.1% | Up 14.1% |
| CompetitorY | 23 | 29.5% | $4,410,000 | 24 | 36.9% | Down 7% |
| No Decision | 17 | 21.8% | $3,415,000 | 17 | 26.2% | Down 4% |
| CompetitorZ | 9 | 11.5% | $1,433,000 | 9 | 13.8% | Down 2% |

Trend rule: share delta above +1 renders `Up <delta>%` to one decimal; below
-1 renders `Down <abs delta>%` to whole numbers; otherwise `Flat`.

## Q3 loss reasons — all 78 losses

| Loss reason | Deals | % of all Q3 losses |
|---|---|---|
| Pricing | 20 | 25.6% |
| No decision | 17 | 21.8% |
| Feature gaps | 13 | 16.7% |
| Security certifications | 12 | 15.4% |
| Enterprise references | 10 | 12.8% |
| Relationship/trust | 6 | 7.7% |

## Q3 loss reasons — CompetitorX only (29 deals)

Root-cause analysis uses this denominator, not the 78-loss total.

| Loss reason | Deals | Frequency | Pipeline | Impact | Addressable? |
|---|---|---|---|---|---|
| Security certifications | 12 | 41.4% | $7,450,000 | High | Yes (6 months) |
| Enterprise references | 7 | 24.1% | $3,205,000 | Medium | Yes (3 months) |
| Pricing/packaging | 5 | 17.2% | $1,830,000 | Medium | Yes (immediate) |
| Feature gaps | 3 | 10.3% | $875,000 | Medium | Roadmap item |
| Relationship/trust | 2 | 6.9% | $750,000 | Low | Yes (engagement plan) |

Impact thresholds: `>= 25%` High, `>= 10%` Medium, below 10% Low.

## Q3 loss reasons — CompetitorY (23) and CompetitorZ (9)

| Competitor | Loss reason | Deals |
|---|---|---|
| CompetitorY | Pricing | 13 |
| CompetitorY | Feature gaps | 5 |
| CompetitorY | Enterprise references | 3 |
| CompetitorY | Relationship/trust | 2 |
| CompetitorZ | Feature gaps | 5 |
| CompetitorZ | Relationship/trust | 2 |
| CompetitorZ | Pricing | 2 |

## The 12 security-certification losses to CompetitorX

Total pipeline $7,450,000. Every one is enterprise segment.

| Opportunity | Account | Value | Deal size bucket |
|---|---|---|---|
| TechCorp Secure Platform | TechCorp Industries | $890,000 | 500K+ |
| GlobalBank Core Upgrade | Global Banking Corp | $780,000 | 500K+ |
| FedFirst Platform | FedFirst Solutions | $720,000 | 500K+ |
| IronClad Security Suite | IronClad Defense | $670,000 | 500K+ |
| SecureHealth Compliance | SecureHealth Inc | $650,000 | 500K+ |
| Fortress Data Vault | Fortress Financial | $600,000 | 500K+ |
| Metro Gov Modernization | Metro Government | $580,000 | 500K+ |
| Radiant Enterprise Suite | Radiant Corp | $560,000 | 500K+ |
| CipherOne Security | CipherOne | $550,000 | 500K+ |
| NexGen Data Suite | NexGen Corp | $510,000 | 500K+ |
| Cobalt Security Platform | Cobalt Inc | $490,000 | 250K-500K |
| Garnet Platform Upgrade | Garnet Solutions | $450,000 | 250K-500K |

## The 7 enterprise-reference losses to CompetitorX

Total pipeline $3,205,000. Every one is enterprise segment.

| Opportunity | Account | Value | Deal size bucket |
|---|---|---|---|
| Sapphire Data Vault | Sapphire Ltd | $620,000 | 500K+ |
| Vantage Cloud Migration | Vantage Ltd | $520,000 | 500K+ |
| PrimeCo Digital Transform | PrimeCo | $440,000 | 250K-500K |
| Titanium Platform Deal | Titanium Holdings | $430,000 | 250K-500K |
| AlphaWave Data | AlphaWave | $420,000 | 250K-500K |
| Beacon ERP Overhaul | Beacon Systems | $390,000 | 250K-500K |
| Onyx Infra Deal | Onyx Industries | $385,000 | 250K-500K |

## Scope limits

The record carries opportunity name, account, value, outcome, competitor,
loss reason, segment, and deal size bucket — for Q3 and Q2 only. It does not
carry close dates, sales reps, regions, open pipeline, or renewal data. Any
question about those fields is answered "not in the record".
