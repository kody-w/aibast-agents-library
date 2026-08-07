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

These programs are reference context for reporting scope and deadlines. No
operation in this agent computes compliance against these program thresholds --
the compliance test uses each facility's own `regulatory_threshold_co2` from
the facility inventory. Say so if a user assumes otherwise.

| Key | Program | Program Threshold CO2 (t) | Deadline |
|-----|---------|---------------------------|----------|
| EPA_GHGRP | EPA GHG Reporting Program | 25,000 | 2026-03-31 |
| CA_CAPANDTRADE | California Cap-and-Trade | 25,000 | 2026-04-01 |
| EPA_NSPS | EPA New Source Performance Standards | 0 | 2026-06-30 |

## How offsets relate to the gap

- The emission gap is the sum of every facility's
  `max(0, scope_1_co2 - target_co2)`, where
  `target_co2 = round(baseline_co2 * (1 - reduction_target_pct / 100))`.
- Credits are compared with that gap; they are never subtracted from a
  facility's Scope 1 figure, its threshold test, or its target progress.
- If available credits fall short of the gap, the shortfall is reported in
  tonnes. Coverage is never claimed without the arithmetic.
