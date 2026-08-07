# Maintenance Operations Data

> SYNTHETIC — DEMO DATA. Every asset, sensor reading, failure probability,
> technician, and maintenance record in this document is fictional. This file
> exists so the agent has a working world to answer from on day one. In
> production, replace this file with tools that read your real CMMS, historian,
> and reliability model (see the README's production section).

## Equipment master

| ID | Equipment | Type | Install Date | Last Service | Runtime (hrs) | MTBF (hrs) | Status |
|----|-----------|------|--------------|--------------|---------------|------------|--------|
| EQ-CNC-01 | CNC Milling Center #1 | CNC Mill | 2019-03-14 | 2025-11-02 | 18,420 | 4,200 | running |
| EQ-CNC-02 | CNC Milling Center #2 | CNC Mill | 2021-07-22 | 2026-01-18 | 9,840 | 4,200 | running |
| EQ-PRS-01 | Hydraulic Press 400T | Press | 2017-11-05 | 2025-09-30 | 26,100 | 5,500 | warning |
| EQ-WLD-01 | Robotic Welder Cell A | Welder | 2022-01-10 | 2026-02-05 | 7,200 | 3,800 | running |
| EQ-INJ-01 | Injection Molder 220T | Injection Molder | 2018-06-18 | 2025-08-12 | 22,800 | 4,800 | critical |
| EQ-ASM-01 | Assembly Line Conveyor | Conveyor | 2020-04-01 | 2026-01-05 | 14,600 | 7,000 | running |

Status labels render as `OK` (running), `WARN` (warning), `CRIT` (critical).

## Current sensor readings

Sensor channels differ by equipment type. Only the channels listed for an asset
exist for that asset.

| ID | Vibration (mm/s) | Temp (C) | Other channels |
|----|------------------|----------|----------------|
| EQ-CNC-01 | 4.2 | 62 | oil_pressure_bar 48; spindle_load_pct 78 |
| EQ-CNC-02 | 2.1 | 55 | oil_pressure_bar 51; spindle_load_pct 64 |
| EQ-PRS-01 | 7.8 | 74 | oil_pressure_bar 38; hydraulic_level_pct 62 |
| EQ-WLD-01 | 1.9 | 48 | arc_stability_pct 96; wire_feed_mpm 8.4 |
| EQ-INJ-01 | 9.3 | 88 | barrel_pressure_bar 1420; cycle_time_s 34.7 |
| EQ-ASM-01 | 1.4 | 38 | belt_tension_n 620; motor_current_a 12.3 |

## Failure probability model

| ID | Failure Mode | 30-Day | 60-Day | 90-Day |
|----|--------------|-------:|-------:|-------:|
| EQ-CNC-01 | Spindle bearing wear | 0.12 | 0.28 | 0.41 |
| EQ-CNC-02 | Normal wear | 0.03 | 0.08 | 0.14 |
| EQ-PRS-01 | Hydraulic seal degradation | 0.35 | 0.58 | 0.74 |
| EQ-WLD-01 | Wire feed mechanism | 0.05 | 0.11 | 0.19 |
| EQ-INJ-01 | Barrel heater band failure | 0.62 | 0.84 | 0.93 |
| EQ-ASM-01 | Belt splice fatigue | 0.02 | 0.06 | 0.10 |

## Technician roster

| ID | Name | Shift | Certifications | Avail Hrs/Wk | Committed | Free |
|----|------|-------|----------------|-------------:|----------:|-----:|
| TECH-201 | Marcus Rivera | Day | CNC Mill, Press, General | 40 | 24 | 16 |
| TECH-202 | Karen Oduya | Day | Welder, Conveyor, General | 40 | 16 | 24 |
| TECH-203 | James Whitfield | Night | Injection Molder, Press, CNC Mill | 40 | 30 | 10 |
| TECH-204 | Lin Zhao | Day | CNC Mill, Welder, Injection Molder, General | 40 | 20 | 20 |

`Free` is `Avail Hrs/Wk - Committed`. `General` is a wildcard certification: a
technician who holds it is eligible for any equipment type.

## Maintenance history (last 12 months)

| Date | ID | Equipment | Type | Hours | Cost | Notes |
|------|----|-----------|------|------:|-----:|-------|
| 2025-08-12 | EQ-INJ-01 | Injection Molder 220T | Preventive | 6 | $2,400.00 | Replaced heater bands 3 and 4, calibrated barrel sensors |
| 2025-09-30 | EQ-PRS-01 | Hydraulic Press 400T | Corrective | 12 | $8,750.00 | Emergency hydraulic seal replacement, fluid flush |
| 2025-11-02 | EQ-CNC-01 | CNC Milling Center #1 | Preventive | 4 | $1,200.00 | Spindle bearing inspection, oil change, alignment check |
| 2026-01-05 | EQ-ASM-01 | Assembly Line Conveyor | Preventive | 3 | $650.00 | Belt tension adjustment, roller lubrication |
| 2026-01-18 | EQ-CNC-02 | CNC Milling Center #2 | Preventive | 4 | $1,100.00 | Tool holder inspection, coolant system flush |
| 2026-02-05 | EQ-WLD-01 | Robotic Welder Cell A | Preventive | 5 | $1,800.00 | Wire feed calibration, torch tip replacement, gas flow test |

Totals: **$15,900.00** spend, **5** preventive, **1** corrective — a **5:1**
preventive-to-corrective ratio against a target of 5:1.

The schedule overview shows only the **last five** records, oldest of the five
first — the 2025-08-12 injection molder record falls outside that window.

## Downtime cost rates

| Equipment Type | Cost per Downtime Hour |
|----------------|-----------------------:|
| CNC Mill | $850 |
| Press | $1,200 |
| Welder | $600 |
| Injection Molder | $1,400 |
| Conveyor | $2,200 |

Any equipment type not listed falls back to **$500** per hour.
