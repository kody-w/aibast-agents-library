# Production Line Operations Data

> SYNTHETIC — DEMO DATA. Every line, product, station, and defect figure in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real MES, historian, and quality system (see the README's production
> section).

## Production lines

| Line ID | Name | Product | Design Capacity (uph) | Actual Output (uph) | Availability | Performance | Quality |
|---------|------|---------|-----------------------|---------------------|--------------|-------------|---------|
| LINE-A | Electronics Assembly Line A | Industrial Control Module ICM-400 | 180 | 142 | 87.0% | 82.0% | 99.4% |
| LINE-B | Metal Fabrication Line B | Structural Bracket SB-220 | 300 | 261 | 92.0% | 94.5% | 98.7% |
| LINE-C | Polymer Molding Line C | Enclosure Housing EH-150 | 240 | 168 | 78.0% | 89.7% | 97.2% |

OEE is the product of the three components divided by 10000:
`OEE = availability x performance x quality / 10000`. A line is flagged
**BELOW TARGET** when its OEE is under 75%.

## Stations — LINE-A (Electronics Assembly Line A), takt 20.0s

| Station | Name | Cycle Time (s) | Takt (s) | Defect Rate |
|---------|------|----------------|----------|-------------|
| A1 | SMT Placement | 18.5 | 20.0 | 0.12% |
| A2 | Reflow Soldering | 22.1 | 20.0 | 0.08% |
| A3 | AOI Inspection | 15.0 | 20.0 | 0.01% |
| A4 | Through-Hole Insert | 19.8 | 20.0 | 0.15% |
| A5 | Functional Test | 25.3 | 20.0 | 0.04% |
| A6 | Conformal Coating | 16.2 | 20.0 | 0.02% |
| A7 | Final Assembly | 19.0 | 20.0 | 0.18% |

## Stations — LINE-B (Metal Fabrication Line B), takt 12.0s

| Station | Name | Cycle Time (s) | Takt (s) | Defect Rate |
|---------|------|----------------|----------|-------------|
| B1 | Laser Cutting | 10.8 | 12.0 | 0.05% |
| B2 | CNC Bending | 11.4 | 12.0 | 0.22% |
| B3 | Robotic Welding | 14.2 | 12.0 | 0.30% |
| B4 | Grinding/Deburr | 9.5 | 12.0 | 0.06% |
| B5 | Powder Coating | 11.0 | 12.0 | 0.10% |
| B6 | QC Measurement | 8.2 | 12.0 | 0.00% |

## Stations — LINE-C (Polymer Molding Line C), takt 15.0s

| Station | Name | Cycle Time (s) | Takt (s) | Defect Rate |
|---------|------|----------------|----------|-------------|
| C1 | Material Drying | 12.0 | 15.0 | 0.02% |
| C2 | Injection Molding | 18.4 | 15.0 | 0.45% |
| C3 | Trim/Deflash | 10.5 | 15.0 | 0.08% |
| C4 | Ultrasonic Weld | 13.8 | 15.0 | 0.12% |
| C5 | Dimensional Check | 9.0 | 15.0 | 0.00% |
| C6 | Packaging | 7.5 | 15.0 | 0.05% |

The bottleneck of a line is the station with the longest cycle time: A5
Functional Test on LINE-A, B3 Robotic Welding on LINE-B, C2 Injection Molding on
LINE-C.

## Defect categories by line

Shares of the line's total defects.

| Line | Category | Share |
|------|----------|-------|
| LINE-A | solder_bridge | 38% |
| LINE-A | component_shift | 22% |
| LINE-A | missing_part | 15% |
| LINE-A | cosmetic | 14% |
| LINE-A | functional | 11% |
| LINE-B | weld_porosity | 42% |
| LINE-B | dimensional_oor | 28% |
| LINE-B | surface_scratch | 18% |
| LINE-B | bend_angle | 12% |
| LINE-C | short_shot | 35% |
| LINE-C | flash | 25% |
| LINE-C | sink_mark | 20% |
| LINE-C | weld_line | 12% |
| LINE-C | warpage | 8% |
