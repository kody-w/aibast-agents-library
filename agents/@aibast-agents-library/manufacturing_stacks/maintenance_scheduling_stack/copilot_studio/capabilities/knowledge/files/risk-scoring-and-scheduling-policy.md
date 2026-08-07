# Risk Scoring and Scheduling Policy

> SYNTHETIC — DEMO DATA. A fictional plant's reliability policy, included so the
> agent's thresholds and guardrails are grounded in a citable document rather
> than only in its instructions. In production, replace this file with your own
> reliability standard and the tools that enforce it.

## Why the score is deterministic

Maintenance planning trades unplanned downtime against maintenance spend. Both
sides of that trade are auditable, so the ranking that drives them must be
reproducible: the same telemetry and the same failure model always produce the
same score, the same priority order, and the same cost figure. The agent
computes; it does not judge.

## Risk score

`risk = round(P30 * 60 + min(vibration_mm_s / 10, 1.0) * 25 + min(temp_c / 100, 1.0) * 15, 1)`

Weights: 60 points of 30-day failure probability, 25 points of vibration, 15
points of temperature. Both sensor terms saturate at 1.0, so vibration at or
above 10 mm/s scores the full 25 and temperature at or above 100 C scores the
full 15. A missing vibration channel contributes 0; a missing temperature
channel is treated as 20 C.

Current scores on this data set:

| ID | Equipment | P30 | Vibration term | Temp term | Risk Score |
|----|-----------|----:|---------------:|----------:|-----------:|
| EQ-INJ-01 | Injection Molder 220T | 0.62 | 23.25 | 13.20 | 73.7 |
| EQ-PRS-01 | Hydraulic Press 400T | 0.35 | 19.50 | 11.10 | 51.6 |
| EQ-CNC-01 | CNC Milling Center #1 | 0.12 | 10.50 | 9.30 | 27.0 |
| EQ-CNC-02 | CNC Milling Center #2 | 0.03 | 5.25 | 8.25 | 15.3 |
| EQ-WLD-01 | Robotic Welder Cell A | 0.05 | 4.75 | 7.20 | 14.9 |
| EQ-ASM-01 | Assembly Line Conveyor | 0.02 | 3.50 | 5.70 | 10.4 |

## Thresholds

| Rule | Threshold | Effect |
|------|-----------|--------|
| Alert / plan / cost inclusion gate | `P30 >= 0.10` | Below this, the asset appears only in the schedule overview |
| Severity `CRITICAL` | `P30 >= 0.50` | Highest alert band |
| Severity `WARNING` | `P30 >= 0.25` | Middle alert band |
| Severity `WATCH` | `0.10 <= P30 < 0.25` | Lowest alert band |
| Work order 8 hours | `P30 >= 0.50` | Labor estimate |
| Work order 5 hours | `0.25 <= P30 < 0.50` | Labor estimate |
| Work order 3 hours | `0.10 <= P30 < 0.25` | Labor estimate |
| Work order 2 hours | `P30 < 0.10` | Never reached — the inclusion gate excludes these assets first |

The `status` field on an asset is descriptive only. It never creates an alert,
never sets a severity band, and never changes a rank.

## Technician fit rules

1. A technician is eligible for an asset only if their certifications contain
   that asset's equipment type **or** contain `General`.
2. A technician is eligible only if their free hours
   (`available_hours_week - committed_hours`) are greater than zero.
3. Among eligible technicians, the best fit is the one with the **most free
   hours**. This is a load-balancing rule, not a skill-ranking rule — a
   `General`-certified technician with the most free hours will be the best fit
   for multiple assets at once, which is expected behavior.
4. If no technician clears both gates, the work order is `UNASSIGNED` with shift
   `-`, and the planner escalates. The agent never waives a gate to fill a slot.

## Cost model

- Estimated downtime hours: `round(P30 * 24, 1)`.
- Downtime cost: `downtime hours * per-hour rate for the equipment type`
  (fallback $500/hr for unlisted types).
- Preventive cost: 25% of the downtime cost it avoids.
- Net savings: the remaining 75%.

These are modeled figures for planning, not booked costs.

## Scheduling SLA

| Priority | Complete within |
|----------|-----------------|
| P1 | 7 days |
| P2 | 14 days |
| P3 and below | 30 days |

## Authority boundary

The agent recommends. Only a maintenance planner creates a work order, books a
technician, changes a shift, or takes equipment out of production. The agent
never states or implies that any of those has happened.
