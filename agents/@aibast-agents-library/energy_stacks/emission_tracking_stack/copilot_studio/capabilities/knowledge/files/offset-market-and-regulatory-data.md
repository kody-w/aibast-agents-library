# Offset Market and Regulatory Data

> SYNTHETIC -- DEMO DATA. Every offset project, price, credit volume, and
> reporting deadline in this document is fictional. This file exists so the
> agent has a working world to answer from on day one. In production, replace
> this file with tools that read your real offset registry positions and your
> regulatory calendar.

## Carbon offset projects

| ID | Project | Type | Credits Available (t) | Price/t | Total Cost | Vintage | Verified By |
|----|---------|------|-----------------------|---------|------------|---------|-------------|
| OFF-001 | Appalachian Reforestation | forestry | 45,000 | $18.50 | $832,500 | 2025 | Verra VCS |
| OFF-002 | Texas Wind REC Bundle | renewable_energy | 120,000 | $12.75 | $1,530,000 | 2026 | Green-e |
| OFF-003 | Montana Methane Capture | methane_capture | 28,000 | $24.00 | $672,000 | 2025 | ACR |
| OFF-004 | Iowa Agricultural Soil Carbon | soil_carbon | 35,000 | $22.00 | $770,000 | 2026 | Gold Standard |

Totals across all four projects: **228,000 tonnes** of credits at a combined
**$3,804,500**. Total cost per project is `credits_available * price_per_tonne`.

## Reporting program register

These programs carry reporting scope and deadlines. No operation in this agent
computes **compliance** against these program thresholds -- the compliance test
uses each facility's own `regulatory_threshold_co2` from the facility
inventory. Say so if a user assumes otherwise. The program thresholds below are
used for one thing only: deciding which programs a facility must report under
in the reporting package draft.

| Key | Program | Jurisdiction | Program Threshold CO2 (t) | Deadline |
|-----|---------|--------------|---------------------------|----------|
| EPA_GHGRP | EPA GHG Reporting Program | federal (all facilities) | 25,000 | 2026-03-31 |
| CA_CAPANDTRADE | California Cap-and-Trade | CA facilities only | 25,000 | 2026-04-01 |
| EPA_NSPS | EPA New Source Performance Standards | federal (all facilities) | 0 | 2026-06-30 |

## Reporting package applicability

A program is in scope for a facility when **both** conditions hold:

1. **Jurisdiction.** A federal program reaches every facility. A state program
   reaches only facilities whose `location` state matches -- California
   Cap-and-Trade reaches only `Sacramento, CA`.
2. **Threshold.** `scope_1_co2 >= program_threshold_co2`.

Applying both rules to the inventory:

| Facility | Location | Scope 1 CO2 (t) | Programs in Scope | Earliest Deadline |
|----------|----------|-----------------|-------------------|-------------------|
| FAC-E01 Riverside Generating Station | Sacramento, CA | 482,000 | EPA_GHGRP, CA_CAPANDTRADE, EPA_NSPS | 2026-03-31 |
| FAC-E02 Sweetwater Wind Farm | Nolan County, TX | 0 | EPA_NSPS | 2026-06-30 |
| FAC-E03 Ridgeline Coal Station | Moffat County, CO | 1,420,000 | EPA_GHGRP, EPA_NSPS | 2026-03-31 |
| FAC-E04 Bayshore Refinery | Beaumont, TX | 890,000 | EPA_GHGRP, EPA_NSPS | 2026-03-31 |

Sweetwater Wind Farm clears only the zero-threshold program because its Scope 1
CO2 is zero; its package is a nil return, not a full filing.

Two open items stand on every draft package in this data set, because the
inputs are genuinely absent: there is no CO2e conversion factor (so CH4 and N2O
are carried as recorded gases and never rolled into a total), and there is no
third-party verification statement. Draft packages are `DRAFT -- UNSIGNED`;
approver, signature, and filing date are always blank.

## How offsets relate to the gap

- The emission gap is the sum of every facility's
  `max(0, scope_1_co2 - target_co2)`, where
  `target_co2 = round(baseline_co2 * (1 - reduction_target_pct / 100))`.
- Credits are compared with that gap; they are never subtracted from a
  facility's Scope 1 figure, its threshold test, or its target progress.
- If available credits fall short of the gap, the shortfall is reported in
  tonnes. Coverage is never claimed without the arithmetic.
