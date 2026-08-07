# Pricing Templates and Competitive Intelligence

> SYNTHETIC — DEMO DATA. Every template percentage and competitor record in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real pricing desk templates and competitor intelligence system.

## Pricing templates

| Template | Phase | Percent of Client Budget |
|----------|-------|--------------------------|
| digital_transformation | Assessment | 8% |
| digital_transformation | Implementation | 55% |
| digital_transformation | Data Analytics | 18% |
| digital_transformation | Change Mgmt | 12% |
| digital_transformation | Project Mgmt | 7% |
| clinical_optimization | Discovery | 10% |
| clinical_optimization | Redesign | 30% |
| clinical_optimization | Technology | 25% |
| clinical_optimization | Training | 20% |
| clinical_optimization | Project Mgmt | 15% |

## Template gates

| Template | Target Margin | Discount Threshold | Applied To |
|----------|---------------|--------------------|------------|
| digital_transformation | 32% | 15% | RFP-2026-047 (GlobalManufacture Corp) |
| clinical_optimization | 28% | 10% | RFP-2026-048 (Summit Health Network) |

The discount threshold sets the proposed price:
`our_price = budget x (100 - discount_threshold_pct) / 100`.

- RFP-2026-047: $10,000,000 x 85% = **$8,500,000** ($1,500,000 below budget)
- RFP-2026-048: $4,500,000 x 90% = **$4,050,000** ($450,000 below budget)

Phase allocations are computed against the **client budget**, so the phase
column totals 100% of budget while the Total row carries the discounted
proposed price. A discount deeper than the threshold is outside the model and
requires approval outside this agent.

## Worked phase allocations

| RFP ID | Phase | Allocation |
|--------|-------|-----------|
| RFP-2026-047 | Assessment | $800,000 |
| RFP-2026-047 | Implementation | $5,500,000 |
| RFP-2026-047 | Data Analytics | $1,800,000 |
| RFP-2026-047 | Change Mgmt | $1,200,000 |
| RFP-2026-047 | Project Mgmt | $700,000 |
| RFP-2026-048 | Discovery | $450,000 |
| RFP-2026-048 | Redesign | $1,350,000 |
| RFP-2026-048 | Technology | $1,125,000 |
| RFP-2026-048 | Training | $900,000 |
| RFP-2026-048 | Project Mgmt | $675,000 |

## Competitor intelligence

INTERNAL ONLY -- never quoted in client-facing material.

| Competitor | Our Win Rate Against | Their Price Premium | Their Typical Margin |
|------------|----------------------|---------------------|----------------------|
| BigFour Consulting | 67% | +25% vs us | 40% |
| Global Advisory Group | 60% | +18% vs us | 35% |
| HealthTech Solutions | 50% | +5% vs us | 30% |
| MedConsult Group | 55% | +10% vs us | 32% |

| Competitor | Strengths to Counter | Weaknesses to Exploit |
|------------|----------------------|-----------------------|
| BigFour Consulting | Brand recognition; Global reach; Deep bench | High cost; Junior staff on projects; Slow to mobilize |
| Global Advisory Group | Strong analytics practice; Government relationships | Limited manufacturing experience; High turnover |
| HealthTech Solutions | Clinical domain expertise; EHR certifications | Small team; Limited scalability; No change management practice |
| MedConsult Group | Strong physician network; CMIO relationships | Technology integration gaps; Limited data analytics capability |

The "key differentiator" in a positioning summary is always the **first** listed
weakness for that competitor. No firm outside these four has an intelligence
record; there is no basis for a premium, margin, or win rate against them.
