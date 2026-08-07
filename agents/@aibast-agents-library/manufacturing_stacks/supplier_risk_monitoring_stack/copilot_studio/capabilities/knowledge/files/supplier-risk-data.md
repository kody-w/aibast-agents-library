# Supplier Risk Data

> SYNTHETIC — DEMO DATA. Every supplier, incident, and alternative source in
> this document is fictional. This file exists so the agent has a working
> world to answer from on day one. In production, replace this file with tools
> that read your real supplier master, quality/incident system, and approved
> vendor list (see the README's production section).

## Supplier master

| ID | Supplier | Category | Region | Country | Annual Spend | Tier | Quality | Delivery | Financial | Geopolitical | Overall Risk |
|----|----------|----------|--------|---------|--------------|------|---------|----------|-----------|--------------|--------------|
| SUP-101 | TechnoCore Semiconductor (Taiwan) | Microcontrollers | Asia-Pacific | Taiwan | $4,800,000 | 1 | 82 | 74 | 68 | 42 | 8.2 |
| SUP-102 | Shenzhen Electronics Co. | Passive Components | Asia-Pacific | China | $3,200,000 | 1 | 71 | 78 | 55 | 58 | 6.5 |
| SUP-103 | Malaysia Semicon Pte Ltd | Power ICs | Asia-Pacific | Malaysia | $2,100,000 | 1 | 91 | 88 | 84 | 82 | 3.8 |
| SUP-104 | Midwest Casting & Forge | Aluminum Castings | North America | USA | $5,600,000 | 1 | 88 | 65 | 72 | 95 | 4.9 |
| SUP-105 | Rheinmetall Precision GmbH | CNC Machined Parts | Europe | Germany | $3,800,000 | 2 | 95 | 91 | 89 | 88 | 2.4 |

Dimension scores are 0-100, higher is healthier. Overall risk is 0-10, higher
is riskier. Total annual spend across the five suppliers is $19,500,000.

## Incident log

| Supplier ID | Date | Severity | Description |
|-------------|------|----------|-------------|
| SUP-101 | 2026-02-28 | HIGH | Cross-strait military exercises caused 5-day port closure; delayed 3 shipments |
| SUP-102 | 2026-03-05 | MEDIUM | Quality excursion: capacitor lot C-4410 failed incoming inspection (2.3% defect rate vs 0.5% spec) |
| SUP-104 | 2026-03-10 | HIGH | Equipment failure at foundry; force majeure declared, 7-day production halt |
| SUP-102 | 2026-03-12 | LOW | New export control regulations announced; compliance review underway |

SUP-103 and SUP-105 have no incidents on file.

## Alternative sources

| Incumbent | Alternative Supplier | Lead Time | Qual Status | Est. Cost Premium |
|-----------|---------------------|-----------|-------------|-------------------|
| SUP-101 TechnoCore Semiconductor (Taiwan) | Samsung Foundry (Korea) | 12 weeks | In Progress | +8% |
| SUP-101 TechnoCore Semiconductor (Taiwan) | GlobalFoundries (USA) | 16 weeks | Not Started | +15% |
| SUP-102 Shenzhen Electronics Co. | Murata Electronics (Japan) | 6 weeks | Qualified | +5% |
| SUP-102 Shenzhen Electronics Co. | Vishay Intertechnology (USA) | 4 weeks | Qualified | +12% |
| SUP-104 Midwest Casting & Forge | Alcoa Precision Castings (USA) | 8 weeks | In Progress | +6% |

SUP-103 and SUP-105 have no alternative sources identified.
