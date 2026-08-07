# Underwriting Guidelines and Pricing Models

> SYNTHETIC — DEMO DATA. These guidelines, thresholds, and rating factors are
> fictional and do not reflect any carrier's filed program. This file exists so
> the agent has a working world to answer from on day one. In production,
> replace this file with tools that read your real underwriting manual and
> rating engine (see the README's production section).

## Risk tier bands

| Band | Tier | Meaning |
|------|------|---------|
| 0-30 | Preferred | Best rates, minimal restrictions |
| 31-55 | Standard | Standard rates and terms |
| 56-75 | Substandard | Rate surcharge or coverage restrictions |
| 76+ | Decline | Outside risk appetite |

## Underwriting guidelines by line of business

### commercial_property

| Guideline | Value |
|-----------|-------|
| Max coverage | $25,000,000 |
| Min protection class | 8 |
| Max building age | 50 |
| Max loss ratio | 60 |
| Required inspections | fire_protection, electrical, roof_condition |
| Prohibited risks | cannabis_operations, fireworks_storage |

### commercial_auto

| Guideline | Value |
|-----------|-------|
| Max coverage | $5,000,000 |
| Max fleet size | 250 |
| Max violations (3 yr) | 3 |
| Max accidents (3 yr) | 2 |
| Min years operating | 2 |
| Required documents | MVR_summary, vehicle_schedule, loss_runs |

### professional_liability

| Guideline | Value |
|-----------|-------|
| Max coverage | $10,000,000 |
| High-risk specialties | neurosurgery, orthopedic_surgery, obstetrics |
| Max claims (5 yr) | 3 |
| Min years in practice | 3 |
| Required documents | CV, board_certifications, claims_history |

### general_liability

| Guideline | Value |
|-----------|-------|
| Max coverage | $5,000,000 |
| Max loss ratio | 65 |
| Min years in business | 2 |
| Required documents | financial_statements, safety_program, certificates_of_insurance |

Only four of these are machine-tested today: the coverage ceiling on every
line, the professional liability high-risk specialty list, the professional
liability 5-year claims maximum, and the commercial auto 3-year fleet
violation maximum. The remaining guidelines are published for the underwriter
and are not evaluated automatically.

## Pricing models

### commercial_property

| Factor | Value |
|--------|-------|
| Base rate per $100 | 0.85 |

| Construction | Factor |
|--------------|--------|
| fire_resistive | 0.80 |
| masonry | 1.00 |
| frame | 1.35 |

| Protection class | Factor |
|------------------|--------|
| 1 | 0.75 |
| 2 | 0.80 |
| 3 | 0.90 |
| 4 | 1.00 |
| 5 | 1.10 |

### commercial_auto

| Factor | Value |
|--------|-------|
| Base rate per vehicle | $2,800 |

| Vehicle class | Factor |
|---------------|--------|
| light_truck | 0.95 |
| medium_truck | 1.20 |
| heavy_truck | 1.55 |

| Radius of operation | Factor |
|---------------------|--------|
| local | 0.90 |
| intermediate | 1.15 |
| long_haul | 1.45 |

### professional_liability

| Factor | Value |
|--------|-------|
| Base rate per practitioner | $8,500 |

| Specialty | Factor |
|-----------|--------|
| family_medicine | 0.60 |
| orthopedic_surgery | 2.10 |
| neurosurgery | 2.80 |
| obstetrics | 2.40 |

### general_liability

| Factor | Value |
|--------|-------|
| Base rate per $1,000 revenue | 2.15 |

| Industry | Factor |
|----------|--------|
| restaurant_chain | 1.35 |
| office | 0.70 |
| retail | 1.10 |
| construction | 1.80 |

The indicated premium on each application is a stored value. These factors are
published so an underwriter can do their own rating work; the agent reports
them but does not multiply them into a new premium.
