# Shift Schedule and Planning Model

> SYNTHETIC — DEMO DATA. The shift schedule, headcount, premiums, and every
> planning constant below are fictional. This file exists so the agent has a
> working world to answer from on day one. In production, replace this file with
> tools that read your real workforce management, costing, and capital planning
> systems (see the README's production section).

## Shift schedule

| Shift | Start | End | Hours | Operators | Premium |
|-------|-------|-----|-------|-----------|---------|
| Day | 06:00 | 14:00 | 8 | 24 | 1.0x |
| Swing | 14:00 | 22:00 | 8 | 22 | 1.0x |
| Night | 22:00 | 06:00 | 8 | 18 | 1.15x |

Total operators across shifts: 64. Lines running: 3. Total scheduled hours per
day: 24.

## Planning constants

| Constant | Value | Where it is used |
|----------|-------|------------------|
| OEE target | 75% | Lines below it are flagged **BELOW TARGET** |
| Operating days per year | 250 | Annual quality cost |
| Scrap and rework cost per defective unit | $12.50 | Annual quality cost |
| Night shift efficiency factor | 0.9 | Night shift output only |
| Option 1 gain factor (cycle time reduction) | 0.6 x gap | Throughput options |
| Option 1 target cycle time | 0.95 x takt | Throughput options |
| Option 2 gain factor (parallel station) | 0.85 x gap | Throughput options |
| Option 2 investment estimate | $45,000 - $120,000 | Throughput options |
| Option 3 gain factor (quality improvement) | 0.2 x gap | Throughput options |
| Combined OEE uplift | 1.12 x current OEE | Throughput options |

The gain factors, the investment range, and the 1.12 uplift are model
assumptions, not measured results.

## Formulas

- `OEE = availability_pct x performance_pct x quality_pct / 10000`
- `throughput_gap_uph = design_capacity_per_hour - actual_output_per_hour`
- `daily_output_flat = actual_output_per_hour x 24`
- `annual_quality_cost = daily_output_flat x 250 x ((100 - quality_pct) / 100) x 12.50`
- `night_shift_output = round(actual_output_per_hour x 8 x 0.9)`
- `shift_plan_daily_total = day_output + swing_output + night_shift_output`
- `weekly_output_N_days = daily_output_flat x N` for N of 5, 6, 7

Note that two daily figures exist by design: `daily_output_flat` (used by the
efficiency report and the weekly capacity table) and `shift_plan_daily_total`
(used by the planned-output-by-shift table, which applies the 0.9 night factor).
They are not the same number and must not be averaged or reconciled.
