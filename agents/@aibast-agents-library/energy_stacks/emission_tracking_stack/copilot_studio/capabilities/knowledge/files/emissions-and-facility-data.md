# Emissions and Facility Data

> SYNTHETIC -- DEMO DATA. Every facility, emissions figure, threshold, and
> baseline in this document is fictional. This file exists so the agent has a
> working world to answer from on day one. In production, replace this file
> with tools that read your real emissions inventory, CEMS feeds, and
> regulatory threshold register.

## Facility inventory

| ID | Name | Location | Type | Capacity (MW) | Regulatory Threshold CO2 (t) | Reduction Target | Baseline Year | Baseline CO2 (t) |
|----|------|----------|------|---------------|------------------------------|------------------|---------------|------------------|
| FAC-E01 | Riverside Generating Station | Sacramento, CA | natural_gas_plant | 340 | 500,000 | 15% | 2022 | 545,000 |
| FAC-E02 | Sweetwater Wind Farm | Nolan County, TX | wind_farm | 180 | 25,000 | 5% | 2022 | 14,200 |
| FAC-E03 | Ridgeline Coal Station | Moffat County, CO | coal_plant | 520 | 1,500,000 | 30% | 2022 | 1,780,000 |
| FAC-E04 | Bayshore Refinery | Beaumont, TX | refinery | 0 | 1,000,000 | 20% | 2022 | 1,050,000 |

## Emissions by scope and gas (tonnes)

CO2 is the only gas aggregated by the dashboard, compliance, plan, and offset
calculations. CH4 and N2O are recorded here for reference; no CO2e conversion
factor exists in this data set, so they are never rolled into a total.

| ID | Facility | Scope | CO2 | CH4 | N2O |
|----|----------|-------|-----|-----|-----|
| FAC-E01 | Riverside Generating Station | Scope 1 | 482,000 | 1,240 | 85 |
| FAC-E01 | Riverside Generating Station | Scope 2 | 12,400 | 0 | 0 |
| FAC-E01 | Riverside Generating Station | Scope 3 | 38,500 | 280 | 15 |
| FAC-E02 | Sweetwater Wind Farm | Scope 1 | 0 | 0 | 0 |
| FAC-E02 | Sweetwater Wind Farm | Scope 2 | 3,200 | 0 | 0 |
| FAC-E02 | Sweetwater Wind Farm | Scope 3 | 8,400 | 12 | 2 |
| FAC-E03 | Ridgeline Coal Station | Scope 1 | 1,420,000 | 3,800 | 420 |
| FAC-E03 | Ridgeline Coal Station | Scope 2 | 18,200 | 0 | 0 |
| FAC-E03 | Ridgeline Coal Station | Scope 3 | 95,000 | 1,200 | 85 |
| FAC-E04 | Bayshore Refinery | Scope 1 | 890,000 | 5,600 | 210 |
| FAC-E04 | Bayshore Refinery | Scope 2 | 42,000 | 0 | 0 |
| FAC-E04 | Bayshore Refinery | Scope 3 | 2,100,000 | 8,400 | 320 |

## Abatement action catalog

Actions are defined per facility **type**, not per facility. Tonnage and cost
are catalog constants; they are not scaled to a facility's gap. A facility type
absent from this table has no reduction plan in this data set -- `wind_farm` is
absent, so Sweetwater Wind Farm is omitted from reduction plan output.

| Facility Type | Action | Reduction (tonnes) | Cost ($M) |
|---------------|--------|--------------------|-----------|
| coal_plant | Fuel switching to natural gas | 400,000 | 85.0 |
| coal_plant | Carbon capture retrofit | 300,000 | 120.0 |
| coal_plant | Efficiency upgrades | 50,000 | 12.0 |
| natural_gas_plant | Heat recovery optimization | 25,000 | 4.5 |
| natural_gas_plant | Turbine efficiency upgrade | 18,000 | 8.0 |
| natural_gas_plant | Methane leak detection and repair | 8,000 | 1.2 |
| refinery | Process electrification | 120,000 | 45.0 |
| refinery | Flare gas recovery | 35,000 | 6.0 |
| refinery | Hydrogen integration | 80,000 | 55.0 |
