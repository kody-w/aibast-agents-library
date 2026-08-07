# Mitigation Playbooks and Alternative Suppliers

> SYNTHETIC — DEMO DATA. Every playbook, cost figure, and supplier in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real business continuity playbooks and your vendor master (see the
> README's production section).

## Mitigation playbooks

Playbooks are selected by the disruption's `type` field. A disruption whose
type has no playbook gets no plan.

| Type | Playbook | Mitigation Cost (USD) | Expected Risk Reduction |
|------|----------|-----------------------|-------------------------|
| port_congestion | Port Congestion Mitigation | 340,000.00 | 45% |
| weather_event | Weather Event Mitigation | 520,000.00 | 55% |
| regulatory | Regulatory Change Mitigation | 85,000.00 | 70% |

Total investment across the distinct playbook types of the active disruptions:
**$945,000.00** (340,000.00 + 520,000.00 + 85,000.00). Each type counts once
regardless of how many events share it.

### Port Congestion Mitigation

| Horizon | Actions |
|---------|---------|
| Immediate (0-48 hours) | Divert eligible shipments to alternate ports (Oakland, Seattle-Tacoma); Activate premium drayage contracts for priority container retrieval; Convert ocean shipments under 2 TEU to air freight for critical SKUs |
| Short-term (1-2 weeks) | Increase safety stock at distribution centers by 20%; Negotiate priority berthing with carrier partners; Activate cross-dock bypass for pre-cleared containers |
| Long-term (1-3 months) | Diversify port-of-entry strategy across West and East Coast; Invest in inland port relationships for rail-direct receiving; Develop dual-source contracts for top-volume categories |

### Weather Event Mitigation

| Horizon | Actions |
|---------|---------|
| Immediate (0-48 hours) | Activate emergency inventory reserves at regional warehouses; Reroute in-transit vessels through safe corridors; Expedite air freight for high-priority SKUs with less than 7 days supply |
| Short-term (1-2 weeks) | Shift demand to in-stock alternative products via merchandising; Enable backorder with guaranteed delivery dates for affected items; Communicate proactively with B2B customers on revised timelines |
| Long-term (1-3 months) | Integrate real-time weather monitoring into planning systems; Build seasonal safety stock buffers for typhoon/hurricane seasons; Qualify backup suppliers in geographically diverse regions |

### Regulatory Change Mitigation

| Horizon | Actions |
|---------|---------|
| Immediate (0-48 hours) | Engage customs broker to prepare updated documentation templates; Pre-certify next 3 shipments with new compliance requirements; Brief all origin-side partners on updated export procedures |
| Short-term (1-2 weeks) | Conduct compliance audit of all active POs on affected routes; Update vendor manual with new regulatory requirements; Schedule training session for procurement team |
| Long-term (1-3 months) | Subscribe to regulatory change monitoring service; Build compliance buffer time into standard lead times; Develop relationships with in-country compliance consultants |

## Qualified alternative suppliers

8 suppliers across 5 categories. The recommended alternative in a category is
always the one with the lowest lead time.

| Category | Supplier | Location | Lead Time | Quality | Capacity/Mo | Price Premium | MOQ | Certifications | Recommended |
|----------|----------|----------|-----------|---------|-------------|---------------|-----|----------------|-------------|
| Electronics | TechSource Taiwan | Taipei, Taiwan | 21d | 4.5/5.0 | 15,000 | +8.0% | 500 | ISO 9001, ISO 14001 | |
| Electronics | KoreanTech Partners | Incheon, South Korea | 19d | 4.7/5.0 | 10,000 | +12.0% | 300 | ISO 9001, IATF 16949 | fastest |
| Apparel | TurkTex Industries | Istanbul, Turkey | 16d | 4.3/5.0 | 25,000 | +5.0% | 1,000 | GOTS, OEKO-TEX | fastest |
| Apparel | BanglaStitch Ltd | Dhaka, Bangladesh | 25d | 4.0/5.0 | 40,000 | -3.0% | 2,000 | WRAP, BSCI | |
| Footwear | IndoSole Manufacturing | Tangerang, Indonesia | 28d | 4.2/5.0 | 18,000 | +2.0% | 800 | ISO 9001, SA8000 | fastest (only option) |
| Accessories | IndiaGlobal Accessories | Mumbai, India | 24d | 4.1/5.0 | 30,000 | -5.0% | 1,500 | ISO 9001 | |
| Accessories | MediterraneanCraft Co | Florence, Italy | 14d | 4.8/5.0 | 5,000 | +25.0% | 200 | ISO 9001, Made in Italy | fastest |
| Home | ThaiHome Products | Bangkok, Thailand | 20d | 4.3/5.0 | 12,000 | +4.0% | 600 | ISO 9001, FSC | fastest (only option) |

Negative price premiums are discounts, not surcharges: BanglaStitch Ltd at
-3.0% and IndiaGlobal Accessories at -5.0% price below the incumbent.
