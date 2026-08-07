# Asset Register and Maintenance History

> SYNTHETIC - DEMO DATA. Every asset, cost, condition score, and failure date in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real asset register, CMMS work order history, and condition
> monitoring system (see the README's production section).

## Asset register

| ID | Name | Type | Location | Installed | Age | Capacity (MW) | Condition | Status Band | Failure Rate (annual) | Operating Hours | Last Major Service | Predicted Next Failure | Replacement Cost |
|----|------|------|----------|-----------|-----|---------------|-----------|-------------|-----------------------|-----------------|--------------------|------------------------|------------------|
| AST-T001 | Wind Turbine Alpha-7 | wind_turbine | Sweetwater Wind Farm, TX | 2016 | 10yr | 3.2 | 68 | WARNING | 4.2% | 72,480 | 2025-06-15 | 2026-08-15 | $2,400,000 |
| AST-X002 | Substation Transformer B-12 | transformer | Ridgeline Substation, CO | 2008 | 18yr | 120.0 | 42 | CRITICAL | 8.7% | 148,920 | 2024-09-22 | 2026-05-01 | $4,800,000 |
| AST-P003 | Gas Pipeline Segment NE-14 | pipeline | Northeast Corridor, PA | 2012 | 14yr | 0 | 75 | GOOD | 1.8% | N/A | 2025-08-30 | 2027-03-01 | $12,000,000 |
| AST-T004 | Gas Turbine GT-3A | gas_turbine | Riverside Generating Station, CA | 2019 | 7yr | 85.0 | 88 | GOOD | 1.2% | 38,200 | 2025-10-12 | 2027-10-01 | $18,000,000 |

Notes on the register:

- Operating hours are not tracked for pipelines. `AST-P003` shows `N/A`, not
  zero; it is a 2012 asset in continuous service.
- Capacity in MW is not meaningful for a pipeline; `AST-P003` carries 0.
- The status band is derived, not stored: below 50 is CRITICAL, 50 to 69 is
  WARNING, 70 and above is GOOD.
- Fleet average condition score across the four assets is **68.2**.

## Maintenance history

### AST-T001 - Wind Turbine Alpha-7

| Date | Type | Cost | Description |
|------|------|------|-------------|
| 2025-06-15 | major | $48,000 | Gearbox bearing replacement |
| 2025-11-20 | minor | $8,200 | Blade pitch calibration |
| 2026-01-10 | inspection | $3,500 | Annual structural inspection |

### AST-X002 - Substation Transformer B-12

| Date | Type | Cost | Description |
|------|------|------|-------------|
| 2024-09-22 | major | $125,000 | Oil filtration and bushing replacement |
| 2025-04-11 | minor | $18,500 | Cooling fan motor replacement |
| 2025-12-05 | inspection | $6,200 | DGA oil analysis - elevated acetylene |

### AST-P003 - Gas Pipeline Segment NE-14

| Date | Type | Cost | Description |
|------|------|------|-------------|
| 2025-08-30 | major | $210,000 | Corrosion remediation and recoating |
| 2025-11-15 | inspection | $15,000 | Inline inspection pig run |
| 2026-02-20 | minor | $9,800 | Valve actuator servicing |

### AST-T004 - Gas Turbine GT-3A

| Date | Type | Cost | Description |
|------|------|------|-------------|
| 2025-10-12 | major | $340,000 | Hot gas path inspection |
| 2026-01-28 | minor | $22,000 | Fuel nozzle cleaning |

## What is not in this data

There is no live sensor telemetry, no SCADA feed, no vibration or thermal trend
series, no crew or outage calendar, no vendor quote, and no asset outside the
four listed above. Historical costs are actuals for the events shown; forward
costs come from the rate card, not from this table.
