# Supply Chain Network Data

> SYNTHETIC — DEMO DATA. Every route, carrier, disruption, SKU, and risk score
> in this document is fictional. This file exists so the agent has a working
> world to answer from on day one. In production, replace this file with tools
> that read your real TMS, control tower, and risk feeds (see the README's
> production section).

## Route network

| Route ID | Name | Origin | Destination | Mode | Transit Days | Carriers | Annual TEU | Annual Value (USD) | Categories | Status | Reliability |
|----------|------|--------|-------------|------|--------------|----------|------------|--------------------|------------|--------|-------------|
| RT-APAC-01 | Asia-Pacific Primary | Shenzhen, China | Los Angeles, CA | ocean_freight | 18 | COSCO Shipping, Evergreen Marine | 4,800 | 28,500,000.00 | Electronics, Accessories | disrupted | 0.82 |
| RT-EURO-01 | European Apparel Route | Porto, Portugal | Newark, NJ | ocean_freight | 12 | Maersk Line, MSC | 2,200 | 15,800,000.00 | Apparel | at_risk | 0.91 |
| RT-DOMESTIC-01 | West Coast to Midwest | Los Angeles, CA | Chicago, IL | intermodal_rail | 4 | Union Pacific, BNSF Railway | 6,500 | 42,000,000.00 | Electronics, Accessories, Apparel, Footwear | normal | 0.95 |
| RT-LATAM-01 | Central America Footwear | Leon, Mexico | Dallas, TX | trucking | 3 | J.B. Hunt, Werner Enterprises | 1,800 | 12,400,000.00 | Footwear | normal | 0.93 |
| RT-SEASIA-01 | Southeast Asia Textiles | Ho Chi Minh City, Vietnam | Savannah, GA | ocean_freight | 22 | Yang Ming, ONE Line | 3,100 | 19,200,000.00 | Apparel, Home | disrupted | 0.78 |

## Disruption event log

| ID | Title | Type | Severity | Affected Routes | Start | Est. Resolution | Delay Days | Revenue Impact (USD) | Status |
|----|-------|------|----------|-----------------|-------|-----------------|------------|----------------------|--------|
| DISR-001 | Port Congestion — Los Angeles/Long Beach | port_congestion | high | RT-APAC-01 | 2026-03-05 | 2026-03-28 | 8 | 2,150,000.00 | active |
| DISR-002 | Typhoon Disruption — South China Sea | weather_event | critical | RT-APAC-01, RT-SEASIA-01 | 2026-03-10 | 2026-03-20 | 12 | 3,800,000.00 | active |
| DISR-003 | EU Customs Regulation Change | regulatory | medium | RT-EURO-01 | 2026-03-01 | 2026-04-15 | 5 | 720,000.00 | active |

### Affected SKUs

| ID | Affected SKUs |
|----|---------------|
| DISR-001 | SKU-1002, SKU-1004, SKU-1006, SKU-1008 |
| DISR-002 | SKU-1002, SKU-1003, SKU-1004, SKU-1006, SKU-1008, SKU-1010 |
| DISR-003 | SKU-1001, SKU-1003 |

### Event descriptions

- **DISR-001 — Port Congestion — Los Angeles/Long Beach.** Severe vessel queue
  at LA/LB ports due to labor slowdown and equipment shortages. Average vessel
  wait time is 6 days.
- **DISR-002 — Typhoon Disruption — South China Sea.** Typhoon Mirinae forcing
  rerouting of vessels through northern Pacific corridor. Multiple sailings
  cancelled or delayed.
- **DISR-003 — EU Customs Regulation Change.** New EU sustainability
  documentation requirements adding processing time at origin. Additional
  compliance certificates needed for textiles.

## Risk score matrix

Scores run 0.00 to 1.00. Band thresholds: HIGH at overall >= 0.70, MEDIUM at
>= 0.40 and < 0.70, LOW below 0.40.

| Route ID | Route | Overall | Band | Geopolitical | Weather | Infrastructure | Labor | Regulatory | Financial |
|----------|-------|---------|------|--------------|---------|----------------|-------|------------|-----------|
| RT-APAC-01 | Asia-Pacific Primary | 0.78 | HIGH | 0.65 | 0.82 | 0.70 | 0.75 | 0.40 | 0.35 |
| RT-EURO-01 | European Apparel Route | 0.45 | MEDIUM | 0.30 | 0.20 | 0.25 | 0.35 | 0.72 | 0.28 |
| RT-DOMESTIC-01 | West Coast to Midwest | 0.22 | LOW | 0.05 | 0.30 | 0.20 | 0.25 | 0.10 | 0.15 |
| RT-LATAM-01 | Central America Footwear | 0.35 | LOW | 0.25 | 0.15 | 0.40 | 0.30 | 0.45 | 0.32 |
| RT-SEASIA-01 | Southeast Asia Textiles | 0.72 | HIGH | 0.50 | 0.85 | 0.55 | 0.40 | 0.48 | 0.30 |

### Factor rollup (network-wide, ordered by peak descending)

| Factor | Average | Peak | Peak route |
|--------|---------|------|------------|
| Weather | 0.46 | 0.85 | RT-SEASIA-01 |
| Labor | 0.41 | 0.75 | RT-APAC-01 |
| Regulatory | 0.43 | 0.72 | RT-EURO-01 |
| Infrastructure | 0.42 | 0.70 | RT-APAC-01 |
| Geopolitical | 0.35 | 0.65 | RT-APAC-01 |
| Financial | 0.28 | 0.35 | RT-APAC-01 |
