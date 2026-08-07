# Field Service Operations Data

> SYNTHETIC — DEMO DATA. Every technician, request, and asset in this document
> is fictional. This file exists so the agent has a working world to answer
> from on day one. In production, replace this file with tools that read your
> real roster and work order system (see the README's production section).

## Technician roster

| ID | Name | Certifications | Zone | Status | Current Location | Jobs Today | Max Jobs | Efficiency | Years Exp |
|----|------|----------------|------|--------|------------------|------------|----------|------------|-----------|
| TECH-201 | Carlos Rivera | electrical_high_voltage, transformer_maintenance, confined_space | West | available | Sacramento, CA | 1 | 4 | 94 | 12 |
| TECH-202 | Amy Blackwell | wind_turbine, electrical_high_voltage, crane_operation | Central | on_job | Sweetwater, TX | 2 | 4 | 91 | 8 |
| TECH-203 | Raj Patel | gas_turbine, combustion_systems, electrical_high_voltage | West | available | Bakersfield, CA | 0 | 4 | 97 | 15 |
| TECH-204 | Sarah Johansson | pipeline_inspection, welding_api1104, hazmat | Northeast | available | Scranton, PA | 1 | 4 | 88 | 6 |
| TECH-205 | Marcus Thompson | electrical_high_voltage, transformer_maintenance, scada_systems | Central | on_break | Denver, CO | 2 | 4 | 92 | 10 |

## Service request queue

| ID | Title | Priority | Type | Required Certifications | Zone | Location | Equipment | Est. Hours | Status |
|----|-------|----------|------|-------------------------|------|----------|-----------|-----------|--------|
| SR-4001 | Transformer oil leak - Ridgeline Substation | high | corrective | transformer_maintenance, electrical_high_voltage | Central | Moffat County, CO | Substation Transformer B-12 | 6 | unassigned |
| SR-4002 | Quarterly turbine blade inspection - Sweetwater | medium | preventive | wind_turbine | Central | Nolan County, TX | Wind Turbine Alpha-7 | 4 | assigned |
| SR-4003 | Gas turbine fuel nozzle replacement | high | corrective | gas_turbine, combustion_systems | West | Sacramento, CA | Gas Turbine GT-3A | 8 | unassigned |
| SR-4004 | Pipeline cathodic protection survey | medium | preventive | pipeline_inspection | Northeast | Lackawanna County, PA | Gas Pipeline Segment NE-14 | 5 | unassigned |
| SR-4005 | Emergency: SCADA communication failure | critical | emergency | scada_systems, electrical_high_voltage | Central | Denver, CO | Ridgeline Substation SCADA | 3 | unassigned |

## Geographic zones

| Zone | States |
|------|--------|
| West | CA, NV, OR, WA |
| Central | TX, CO, OK, KS, NM |
| Northeast | PA, NY, NJ, CT, MA |
