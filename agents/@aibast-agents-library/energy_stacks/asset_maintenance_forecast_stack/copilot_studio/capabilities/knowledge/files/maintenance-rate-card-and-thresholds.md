# Maintenance Rate Card and Thresholds

> SYNTHETIC - DEMO DATA. Every rate and threshold in this document is fictional.
> This file exists so the agent has a working world to answer from on day one.
> In production, replace this file with tools that read your real rate card,
> contract pricing, and reliability thresholds (see the README's production
> section).

## Rate card

Forward-looking cost per event, by work type and asset type. These rates drive
every estimate in the budget projection and the work order plan.

| Work Type | wind_turbine | transformer | pipeline | gas_turbine |
|-----------|--------------|-------------|----------|-------------|
| major | $52,000 | $135,000 | $225,000 | $360,000 |
| minor | $9,000 | $20,000 | $12,000 | $25,000 |
| inspection | $4,000 | $7,000 | $16,000 | $15,000 |

There is no rate for any asset type outside these four columns.

## Condition-score thresholds

| Band | Condition score | Meaning |
|------|-----------------|---------|
| CRITICAL | below 50 | Urgent major service gated in; budget uplift applies |
| WARNING | 50 to 69 | Detailed condition assessment gated in |
| GOOD | 70 and above | Preventive maintenance only |

The same threshold of 50 drives both the CRITICAL band and the budget uplift.
The same threshold of 70 drives both the WARNING band and the inspection gate.

## Annual budget formula

```
annual_budget = major_rate + (minor_rate x 2) + inspection_rate
if condition_score < 50:
    annual_budget = round(annual_budget x 1.5)
```

Applied to the current register:

| Asset | Type | Condition | Base | Uplift | Annual Budget |
|-------|------|-----------|------|--------|---------------|
| AST-T004 Gas Turbine GT-3A | gas_turbine | 88 | $425,000 | none | $425,000 |
| AST-X002 Substation Transformer B-12 | transformer | 42 | $182,000 | x 1.5 | $273,000 |
| AST-P003 Gas Pipeline Segment NE-14 | pipeline | 75 | $265,000 | none | $265,000 |
| AST-T001 Wind Turbine Alpha-7 | wind_turbine | 68 | $74,000 | none | $74,000 |

Fleet total annual budget: **$1,037,000**.

## Work order gates

Assets are processed worst condition first, with a single global priority
counter. Gates are cumulative.

| Gate | Condition | Work type emitted | Target |
|------|-----------|-------------------|--------|
| Urgent service | below 50 | MAJOR | 2026-Q2 |
| Condition assessment | below 70 | INSPECTION | 2026-Q2 |
| Preventive | always | MINOR | 2026-Q3 |

Fleet total planned work order cost under these gates: **$212,000** across seven
orders.

## Approval boundary

Every figure here is an estimate from the rate card. Nothing in this document
authorizes spend, raises a work order, books an outage, or approves a budget. A
maintenance planner takes the recommendation and decides.
