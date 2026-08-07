# Pipeline and Deal Data

> SYNTHETIC — DEMO DATA. Every account, deal, rep, contact and activity in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real CRM, activity logs and forecast submissions (see the README's
> production section).

## Coverage — which data set answers which question

Each analysis reads its own deal set. Never blend the totals.

| Data set | Deals covered |
|----------|---------------|
| Full pipeline (health, stalled deals, action plans, acceleration, tasks, exec summary) | 47 opportunities, 43 in active stages |
| Deal health / risk / win probability / next best action | 6 deals |
| Pipeline velocity | 8 deals |
| Revenue forecast | 10 deals |
| Stakeholder engagement | 5 deals |
| Activity gaps | 6 deals |
| Competitive intelligence | 5 deals |
| Stall detection | 7 deals |

## Sales team

| Rep | Title | Active Deals | Capacity | Available Slots | Specialty | Avg Close Rate |
|-----|-------|--------------|----------|-----------------|-----------|----------------|
| Mike Chen | Sr. Account Executive | 11 | 14 | 3 | executive alignment | 34% |
| Lisa Torres | Account Executive | 9 | 12 | 3 | contract negotiation | 38% |
| James Park | Sr. Account Executive | 12 | 14 | 2 | technical sales | 31% |
| Sarah Kim | Account Executive | 8 | 12 | 4 | executive alignment | 36% |
| Ryan Davis | Account Executive | 7 | 12 | 5 | mid-market | 42% |

## Full pipeline — 47 opportunities

| ID | Deal | Account | Value | Stage | Days in Stage | Owner | Last Contact | Champion | Champion Status | Blocker |
|----|------|---------|-------|-------|---------------|-------|--------------|----------|-----------------|---------|
| OPP-001 | TechCorp Industries | TechCorp Industries | $890,000 | Proposal | 34 | Mike Chen | 18d | VP IT - Mark Reynolds | Silent | executive_change |
| OPP-002 | Global Manufacturing | Global Manufacturing | $720,000 | Negotiation | 28 | Lisa Torres | 5d | Dir. Ops - Rachel Green | Active frustrated | legal_review |
| OPP-003 | Apex Financial | Apex Financial Group | $580,000 | Discovery | 25 | James Park | 12d | CTO - David Liu | Disengaged | competitor_eval |
| OPP-004 | Metro Healthcare | Metro Health Systems | $440,000 | Proposal | 22 | Mike Chen | 9d | VP Digital - Sandra Patel | Active | budget_hold |
| OPP-005 | Pinnacle Logistics | Pinnacle Logistics Inc. | $360,000 | Qualification | 20 | James Park | 14d | IT Dir - Tom Bradley | Silent | no_champion |
| OPP-006 | Summit Retail Group | Summit Retail Group | $310,000 | Discovery | 24 | Sarah Kim | 11d | COO - Angela Morris | Lukewarm | competitor_eval |
| OPP-007 | Vanguard Energy | Vanguard Energy Corp | $270,000 | Proposal | 21 | Ryan Davis | 16d | VP Eng - Carlos Reyes | Silent | executive_change |
| OPP-008 | Cascade Media | Cascade Media Holdings | $220,000 | Negotiation | 18 | Lisa Torres | 7d | Dir. Tech - Nina Chow | Active | legal_review |
| OPP-009 | Atlas Construction | Atlas Construction Co. | $180,000 | Qualification | 19 | James Park | 20d | None identified | None | no_champion |
| OPP-010 | Horizon Pharma | Horizon Pharmaceuticals | $150,000 | Discovery | 22 | Sarah Kim | 13d | VP R&D - Greg Foster | Disengaged | budget_hold |
| OPP-011 | Sterling Insurance | Sterling Insurance Co. | $130,000 | Proposal | 20 | Mike Chen | 15d | CIO - Barbara Wells | Lukewarm | competitor_eval |
| OPP-012 | Redwood Education | Redwood Education Group | $110,000 | Qualification | 18 | Ryan Davis | 10d | Dir. IT - Paul Simmons | Active | budget_hold |
| OPP-013 | Pacific Telecom | Pacific Telecom Inc. | $780,000 | Negotiation | 14 | Lisa Torres | 3d | SVP Ops - Diana Cruz | Active | procurement_process |
| OPP-014 | Northstar Aerospace | Northstar Aerospace | $650,000 | Proposal | 17 | Mike Chen | 4d | VP IT - Kyle Jensen | Active | technical_validation |
| OPP-015 | Beacon Financial | Beacon Financial Corp | $520,000 | Discovery | 19 | James Park | 6d | CTO - Amy Nakamura | Active | stakeholder_alignment |
| OPP-016 | Crestline Hotels | Crestline Hospitality | $480,000 | Qualification | 15 | Sarah Kim | 5d | Dir. Digital - Frank Russo | Active | timeline_uncertainty |
| OPP-017 | Ironbridge Steel | Ironbridge Steel Corp | $410,000 | Proposal | 17 | Ryan Davis | 4d | VP Mfg - Helen Park | Active | stakeholder_alignment |
| OPP-018 | Emerald Biotech | Emerald Biotech Ltd. | $370,000 | Negotiation | 13 | Lisa Torres | 2d | CIO - Roger Tran | Active | procurement_process |
| OPP-019 | Sapphire Analytics | Sapphire Analytics Inc. | $290,000 | Discovery | 19 | James Park | 7d | VP Data - Megan Lowe | Active | technical_validation |
| OPP-020 | DataFlow Corp | DataFlow Corp | $340,000 | Contract | 3 | Lisa Torres | 1d | VP Eng - Steve Hall | Active | none |
| OPP-021 | Summit Industries | Summit Industries Inc. | $280,000 | Contract | 5 | Mike Chen | 1d | CTO - Laura Adams | Active | none |
| OPP-022 | Tech Dynamics | Tech Dynamics LLC | $190,000 | Contract | 2 | Sarah Kim | 0d | IT Dir - Ben Wright | Active | none |
| OPP-023 | Orion Software | Orion Software Inc. | $420,000 | Negotiation | 5 | James Park | 1d | VP Prod - Jill Carter | Active | none |
| OPP-024 | Vertex Solutions | Vertex Solutions Corp | $380,000 | Proposal | 8 | Ryan Davis | 2d | CIO - Dan Mitchell | Active | none |
| OPP-025 | Phoenix Consulting | Phoenix Consulting Grp | $310,000 | Discovery | 10 | Mike Chen | 3d | CEO - Tina Brooks | Active | none |
| OPP-026 | Cirrus Cloud Services | Cirrus Cloud Services | $540,000 | Proposal | 7 | Lisa Torres | 2d | VP Infra - Raj Patel | Active | none |
| OPP-027 | Quantum Analytics | Quantum Analytics LLC | $290,000 | Discovery | 9 | Sarah Kim | 4d | CTO - Eric Saunders | Active | none |
| OPP-028 | Bluewave Telecom | Bluewave Telecom Inc. | $460,000 | Negotiation | 6 | James Park | 1d | SVP Tech - Maria Gonzalez | Active | none |
| OPP-029 | Granite Capital | Granite Capital Mgmt | $350,000 | Qualification | 7 | Mike Chen | 3d | Dir. IT - Jake Morton | Active | none |
| OPP-030 | Silverline Media | Silverline Media Group | $230,000 | Proposal | 6 | Ryan Davis | 2d | VP Tech - Olivia Hart | Active | none |
| OPP-031 | Trident Manufacturing | Trident Mfg Corp | $510,000 | Negotiation | 4 | Lisa Torres | 1d | COO - William Chen | Active | none |
| OPP-032 | Falcon Logistics | Falcon Logistics Inc. | $270,000 | Discovery | 11 | Sarah Kim | 3d | VP Ops - Christine Lee | Active | none |
| OPP-033 | Prism Technologies | Prism Technologies LLC | $390,000 | Proposal | 9 | James Park | 2d | CTO - Derek Nash | Active | none |
| OPP-034 | Keystone Health | Keystone Health Corp | $320,000 | Qualification | 8 | Mike Chen | 4d | VP Digital - Susan Park | Active | none |
| OPP-035 | Neptune Shipping | Neptune Shipping Co. | $180,000 | Discovery | 6 | Ryan Davis | 2d | CIO - Alan Foster | Active | none |
| OPP-036 | Ember Software | Ember Software Inc. | $450,000 | Proposal | 5 | Lisa Torres | 1d | VP Eng - Kevin Zhao | Active | none |
| OPP-037 | Ridgeline Capital | Ridgeline Capital Grp | $260,000 | Negotiation | 3 | Sarah Kim | 1d | Dir. Tech - Nancy White | Active | none |
| OPP-038 | Aurora Aerospace | Aurora Aerospace Ltd. | $530,000 | Discovery | 8 | James Park | 3d | SVP Eng - Robert Kim | Active | none |
| OPP-039 | Cobalt Chemicals | Cobalt Chemical Corp | $200,000 | Qualification | 5 | Mike Chen | 2d | VP IT - Dorothy Mills | Active | none |
| OPP-040 | Zenith Insurance | Zenith Insurance Group | $340,000 | Proposal | 4 | Ryan Davis | 1d | CTO - Philip Grant | Active | none |
| OPP-041 | Legacy Healthcare | Legacy Health Systems | $280,000 | Negotiation | 7 | Lisa Torres | 2d | Dir. Digital - Kelly Young | Active | none |
| OPP-042 | Pinnacle Software | Pinnacle Software Inc. | $410,000 | Discovery | 7 | Sarah Kim | 3d | VP Prod - Brian Hughes | Active | none |
| OPP-043 | Titan Energy | Titan Energy Corp | $370,000 | Proposal | 10 | James Park | 2d | CIO - Martha Clark | Active | none |
| OPP-044 | Axiom Partners | Axiom Partners LLC | $520,000 | Closed Won | 0 | Mike Chen | 0d | CEO - Janet Rivera | Won | none |
| OPP-045 | Delta Dynamics | Delta Dynamics Corp | $310,000 | Closed Won | 0 | Lisa Torres | 0d | VP Ops - Scott Morgan | Won | none |
| OPP-046 | Vector Analytics | Vector Analytics Inc. | $190,000 | Closed Won | 0 | Sarah Kim | 0d | CTO - Lisa Brown | Won | none |
| OPP-047 | Omega Systems | Omega Systems Inc. | $430,000 | Closed Lost | 0 | James Park | 0d | VP IT - Chris Taylor | Lost | competitor_won |

Active stages are Qualification, Discovery, Proposal, Negotiation and Contract.
Closed Won (3 deals) and Closed Lost (1 deal) are excluded from active counts.

## Deal health metrics — 6 scored deals

| Deal | ID | Value | Stage | Owner | Emails Sent | Emails Opened | Meetings | Calls | Days Since Touch |
|------|----|-------|-------|-------|-------------|---------------|----------|-------|------------------|
| TechCorp Industries | OPP-001 | $890,000 | Proposal | Mike Chen | 24 | 18 | 6 | 8 | 18 |
| Global Manufacturing | OPP-002 | $720,000 | Negotiation | Lisa Torres | 31 | 28 | 9 | 12 | 5 |
| Apex Financial | OPP-003 | $580,000 | Discovery | James Park | 12 | 6 | 2 | 3 | 12 |
| Metro Healthcare | OPP-004 | $440,000 | Proposal | Mike Chen | 18 | 15 | 5 | 7 | 9 |
| Pacific Telecom | OPP-013 | $780,000 | Negotiation | Lisa Torres | 35 | 32 | 11 | 14 | 3 |
| Pinnacle Logistics | OPP-005 | $360,000 | Qualification | James Park | 8 | 3 | 1 | 2 | 14 |

| Deal | Stakeholders Total | Engaged | Champion Active | Exec Sponsor | Days in Stage | Benchmark | Stage Entries | Regressions |
|------|--------------------|---------|-----------------|--------------|---------------|-----------|---------------|-------------|
| TechCorp Industries | 5 | 2 | no | no | 34 | 16 | 4 | 1 |
| Global Manufacturing | 4 | 3 | yes | no | 28 | 12 | 5 | 0 |
| Apex Financial | 6 | 1 | no | no | 25 | 18 | 2 | 0 |
| Metro Healthcare | 4 | 3 | yes | yes | 22 | 16 | 4 | 0 |
| Pacific Telecom | 5 | 4 | yes | yes | 14 | 12 | 5 | 0 |
| Pinnacle Logistics | 3 | 1 | no | no | 20 | 14 | 1 | 0 |

| Deal | Last Meeting Tone | Email Responsiveness | Objections Raised | Positive Signals |
|------|-------------------|----------------------|-------------------|------------------|
| TechCorp Industries | neutral | 0.42 | 3 | 1 |
| Global Manufacturing | positive | 0.78 | 2 | 4 |
| Apex Financial | cautious | 0.35 | 4 | 0 |
| Metro Healthcare | positive | 0.72 | 1 | 3 |
| Pacific Telecom | very_positive | 0.91 | 0 | 6 |
| Pinnacle Logistics | neutral | 0.25 | 2 | 0 |

## Risk factor scores — 6 deals, 6 factors (0-100, higher is worse)

| Deal | Champion | Budget | Timeline | Competitive | Technical | Decision |
|------|----------|--------|----------|-------------|-----------|----------|
| TechCorp Industries | 85 | 40 | 65 | 70 | 30 | 75 |
| Global Manufacturing | 25 | 35 | 70 | 45 | 15 | 50 |
| Apex Financial | 90 | 60 | 55 | 80 | 45 | 70 |
| Metro Healthcare | 20 | 65 | 50 | 30 | 35 | 40 |
| Pacific Telecom | 10 | 20 | 35 | 15 | 10 | 25 |
| Pinnacle Logistics | 80 | 70 | 60 | 40 | 50 | 85 |

Recorded factor notes:

| Deal | Factor | Note |
|------|--------|------|
| TechCorp Industries | champion_risk | Champion silent for 18 days, new VP joined org |
| TechCorp Industries | budget_risk | Budget approved in Q3 planning, still allocated |
| TechCorp Industries | timeline_risk | 34 days in Proposal, 2.1x benchmark |
| TechCorp Industries | competitive_risk | Nextera Platform in active evaluation |
| TechCorp Industries | technical_risk | POC completed successfully, positive feedback |
| TechCorp Industries | decision_risk | Executive change, new decision maker not engaged |
| Global Manufacturing | champion_risk | Champion active and frustrated with legal delays |
| Global Manufacturing | budget_risk | Budget confirmed, procurement process slow |
| Global Manufacturing | timeline_risk | 28 days in Negotiation, 2.3x benchmark |
| Global Manufacturing | competitive_risk | Vendara offering 25% discount, we lead on features |
| Global Manufacturing | technical_risk | Technical validation complete, no concerns |
| Global Manufacturing | decision_risk | Legal review creating bottleneck, not relationship issue |
| Apex Financial | champion_risk | CTO disengaged, no response in 12 days |
| Apex Financial | budget_risk | Budget not yet allocated, fiscal year change pending |
| Apex Financial | timeline_risk | 25 days in Discovery, 1.4x benchmark |
| Apex Financial | competitive_risk | Three competitors in evaluation, RFP coming |
| Apex Financial | technical_risk | Security compliance concerns in financial services |
| Apex Financial | decision_risk | No executive sponsor, buying committee not mapped |
| Metro Healthcare | champion_risk | VP Digital actively championing internally |
| Metro Healthcare | budget_risk | Budget on hold pending board approval next month |
| Metro Healthcare | timeline_risk | 22 days in Proposal, 1.4x benchmark |
| Metro Healthcare | competitive_risk | Nextera struggling with HIPAA requirements |
| Metro Healthcare | technical_risk | HIPAA compliance validated, minor integration work |
| Metro Healthcare | decision_risk | Decision maker identified and engaged |
| Pacific Telecom | champion_risk | SVP Ops strong advocate, weekly check-ins |
| Pacific Telecom | budget_risk | Budget approved, PO in procurement queue |
| Pacific Telecom | timeline_risk | 14 days in Negotiation, 1.2x benchmark |
| Pacific Telecom | competitive_risk | CloudFirst eliminated in technical evaluation |
| Pacific Telecom | technical_risk | Full technical sign-off obtained |
| Pacific Telecom | decision_risk | Procurement process standard, no blockers |
| Pinnacle Logistics | champion_risk | IT Director silent, no internal advocate found |
| Pinnacle Logistics | budget_risk | No budget discussion, unclear funding source |
| Pinnacle Logistics | timeline_risk | 20 days in Qualification, 1.4x benchmark |
| Pinnacle Logistics | competitive_risk | No known competitors, but early stage |
| Pinnacle Logistics | technical_risk | Requirements not fully scoped |
| Pinnacle Logistics | decision_risk | No champion, no exec sponsor, single contact only |

## Win probability factor scores — 6 deals, 8 factors (0-100%)

| Factor | Pacific Telecom | Metro Healthcare | Global Manufacturing | TechCorp Industries | Apex Financial | Pinnacle Logistics |
|--------|-----------------|------------------|----------------------|---------------------|----------------|--------------------|
| Stage Progression | 80% | 55% | 80% | 55% | 30% | 15% |
| Champion Strength | 95% | 85% | 70% | 20% | 15% | 10% |
| Stakeholder Coverage | 85% | 65% | 60% | 40% | 20% | 15% |
| Activity Momentum | 90% | 60% | 55% | 25% | 15% | 20% |
| Competitive Position | 90% | 80% | 70% | 40% | 25% | 50% |
| Deal Velocity | 75% | 50% | 35% | 30% | 45% | 40% |
| Budget Confidence | 90% | 40% | 75% | 65% | 30% | 20% |
| Executive Access | 85% | 70% | 45% | 15% | 10% | 5% |

Recorded factor detail strings include "3 of 5 stages completed" (TechCorp
stage progression), "SVP Ops strong advocate, weekly calls" (Pacific Telecom
champion strength), "1 of 6 stakeholders engaged" (Apex Financial stakeholder
coverage) and "No executive contact at all" (Pinnacle Logistics executive
access).

## Six-week trend histories

| Deal | Health W-5 | W-4 | W-3 | W-2 | W-1 | Current |
|------|-----------|-----|-----|-----|-----|---------|
| TechCorp Industries | 72 | 68 | 61 | 55 | 48 | 42 |
| Global Manufacturing | 45 | 52 | 58 | 62 | 65 | 63 |
| Apex Financial | 55 | 50 | 44 | 38 | 35 | 32 |
| Metro Healthcare | 58 | 62 | 65 | 68 | 70 | 67 |
| Pacific Telecom | 60 | 65 | 72 | 78 | 82 | 85 |
| Pinnacle Logistics | 40 | 38 | 35 | 33 | 30 | 28 |

| Deal | Risk W-5 | W-4 | W-3 | W-2 | W-1 | Current |
|------|----------|-----|-----|-----|-----|---------|
| TechCorp Industries | 52 | 55 | 60 | 64 | 68 | 72 |
| Global Manufacturing | 30 | 32 | 35 | 38 | 42 | 44 |
| Apex Financial | 40 | 48 | 55 | 60 | 65 | 70 |
| Metro Healthcare | 35 | 33 | 36 | 38 | 40 | 42 |
| Pacific Telecom | 28 | 25 | 22 | 20 | 18 | 16 |
| Pinnacle Logistics | 50 | 55 | 58 | 62 | 65 | 68 |

| Deal | Win Prob W-5 | W-4 | W-3 | W-2 | W-1 | Current |
|------|--------------|-----|-----|-----|-----|---------|
| TechCorp Industries | 52% | 48% | 42% | 38% | 35% | 32% |
| Global Manufacturing | 40% | 45% | 50% | 52% | 55% | 56% |
| Apex Financial | 35% | 30% | 25% | 22% | 20% | 18% |
| Metro Healthcare | 38% | 42% | 45% | 48% | 50% | 52% |
| Pacific Telecom | 50% | 58% | 65% | 72% | 78% | 82% |
| Pinnacle Logistics | 20% | 18% | 15% | 14% | 12% | 11% |

## Next-best-action deal context — 6 deals

| Deal | ID | Value | Stage | Owner | Blocker | Days in Stage | Last Contact | Champion Status | Risk | Health |
|------|----|-------|-------|-------|---------|---------------|--------------|-----------------|------|--------|
| TechCorp Industries | OPP-001 | $890,000 | Proposal | Mike Chen | executive_change | 34 | 18d | Silent | 72 | 42 |
| Global Manufacturing | OPP-002 | $720,000 | Negotiation | Lisa Torres | legal_review | 28 | 5d | Active frustrated | 44 | 63 |
| Apex Financial | OPP-003 | $580,000 | Discovery | James Park | competitor_eval | 25 | 12d | Disengaged | 70 | 32 |
| Metro Healthcare | OPP-004 | $440,000 | Proposal | Mike Chen | budget_hold | 22 | 9d | Active | 42 | 67 |
| Pacific Telecom | OPP-013 | $780,000 | Negotiation | Lisa Torres | procurement_process | 14 | 3d | Active | 16 | 85 |
| Pinnacle Logistics | OPP-005 | $360,000 | Qualification | James Park | no_champion | 20 | 14d | Silent | 68 | 28 |

## Stall timelines — 7 deals

| Deal | ID | Value | Stage | Owner | Days in Stage | Last Contact | Last Meeting | Champion | Status | Acts Last 14d | Acts Prior 14d | Blocker | Next Step |
|------|----|-------|-------|-------|---------------|--------------|--------------|----------|--------|---------------|----------------|---------|-----------|
| TechCorp Industries | OPP-001 | $890,000 | Proposal | Mike Chen | 34 | 18d | 22d | VP IT - Mark Reynolds | Silent | 2 | 8 | executive_change | None scheduled |
| Global Manufacturing | OPP-002 | $720,000 | Negotiation | Lisa Torres | 28 | 5d | 8d | Dir. Ops - Rachel Green | Active frustrated | 6 | 9 | legal_review | Legal redline review scheduled |
| Apex Financial | OPP-003 | $580,000 | Discovery | James Park | 25 | 12d | 18d | CTO - David Liu | Disengaged | 1 | 5 | competitor_eval | None scheduled |
| Metro Healthcare | OPP-004 | $440,000 | Proposal | Mike Chen | 22 | 9d | 12d | VP Digital - Sandra Patel | Active | 4 | 6 | budget_hold | Board meeting next month |
| Pinnacle Logistics | OPP-005 | $360,000 | Qualification | James Park | 20 | 14d | 18d | IT Dir - Tom Bradley | Silent | 1 | 3 | no_champion | None scheduled |
| Summit Retail Group | OPP-006 | $310,000 | Discovery | Sarah Kim | 24 | 11d | 15d | COO - Angela Morris | Lukewarm | 2 | 5 | competitor_eval | Competitive comparison pending |
| Vanguard Energy | OPP-007 | $270,000 | Proposal | Ryan Davis | 21 | 16d | 20d | VP Eng - Carlos Reyes | Silent | 1 | 4 | executive_change | None scheduled |

Recorded stage history: TechCorp Qualification 12d advanced, Discovery 16d
advanced, Proposal 34d stalled. Global Manufacturing Qualification 10d,
Discovery 15d, Proposal 14d, Negotiation 28d stalled. Apex Financial
Qualification 11d, Discovery 25d stalled. Metro Healthcare Qualification 9d,
Discovery 14d, Proposal 22d stalled. Pinnacle Logistics Qualification 20d
stalled. Summit Retail Qualification 8d, Discovery 24d stalled. Vanguard
Energy Qualification 10d, Discovery 12d, Proposal 21d stalled.

## Velocity stage timestamps — 8 deals

| Deal | ID | Value | Owner | Qualification | Discovery | Proposal | Negotiation | Contract | Current Stage | Total Age | Probability |
|------|----|-------|-------|---------------|-----------|----------|-------------|----------|---------------|-----------|-------------|
| TechCorp Industries | OPP-001 | $890,000 | Mike Chen | 12 | 16 | 34 | - | - | Proposal | 62 | 35% |
| Global Manufacturing | OPP-002 | $720,000 | Lisa Torres | 10 | 15 | 14 | 28 | - | Negotiation | 67 | 55% |
| Apex Financial | OPP-003 | $580,000 | James Park | 11 | 25 | - | - | - | Discovery | 36 | 20% |
| Metro Healthcare | OPP-004 | $440,000 | Mike Chen | 9 | 14 | 22 | - | - | Proposal | 45 | 45% |
| Pacific Telecom | OPP-013 | $780,000 | Lisa Torres | 8 | 12 | 11 | 14 | - | Negotiation | 45 | 75% |
| Pinnacle Logistics | OPP-005 | $360,000 | James Park | 20 | - | - | - | - | Qualification | 20 | 10% |
| Northstar Aerospace | OPP-014 | $650,000 | Mike Chen | 10 | 13 | 17 | - | - | Proposal | 40 | 50% |
| DataFlow Corp | OPP-020 | $340,000 | Lisa Torres | 7 | 10 | 9 | 8 | 3 | Contract | 37 | 90% |

## Forecast deal attributes — 10 deals

| Deal | ID | Value | Stage | Probability | Close Date | Category | Owner | Forecast Override |
|------|----|-------|-------|-------------|------------|----------|-------|-------------------|
| TechCorp Industries | OPP-001 | $890,000 | Proposal | 35% | 2026-04-15 | upside | Mike Chen | - |
| Pacific Telecom | OPP-013 | $780,000 | Negotiation | 75% | 2026-03-28 | commit | Lisa Torres | $780,000 |
| Global Manufacturing | OPP-002 | $720,000 | Negotiation | 55% | 2026-03-31 | commit | Lisa Torres | $720,000 |
| Northstar Aerospace | OPP-014 | $650,000 | Proposal | 50% | 2026-04-10 | best_case | Mike Chen | $650,000 |
| Apex Financial | OPP-003 | $580,000 | Discovery | 20% | 2026-05-30 | pipeline | James Park | - |
| Beacon Financial | OPP-015 | $520,000 | Discovery | 25% | 2026-05-15 | upside | James Park | - |
| Metro Healthcare | OPP-004 | $440,000 | Proposal | 45% | 2026-04-20 | best_case | Mike Chen | - |
| Orion Software | OPP-023 | $420,000 | Negotiation | 65% | 2026-04-05 | best_case | James Park | $420,000 |
| Pinnacle Logistics | OPP-005 | $360,000 | Qualification | 10% | 2026-06-15 | pipeline | James Park | - |
| DataFlow Corp | OPP-020 | $340,000 | Contract | 90% | 2026-03-22 | commit | Lisa Torres | $340,000 |

## Stakeholders — 5 deals, 21 contacts

| Deal | Contact | Title | Role | Emails | Meetings | Last Touch | Sentiment | Influence | Support |
|------|---------|-------|------|--------|----------|------------|-----------|-----------|---------|
| TechCorp Industries | Mark Reynolds | VP of IT | Economic Buyer | 8 | 2 | 18d | neutral | high | unknown |
| TechCorp Industries | Jennifer Walsh | Director of Engineering | Technical Evaluator | 12 | 3 | 22d | positive | medium | supporter |
| TechCorp Industries | Robert Kim | CIO | Executive Sponsor | 2 | 0 | 45d | unknown | very_high | unknown |
| TechCorp Industries | Amanda Chen | Procurement Manager | Procurement | 4 | 1 | 12d | neutral | medium | neutral |
| TechCorp Industries | David Park | IT Manager | End User | 6 | 2 | 8d | positive | low | champion |
| Global Manufacturing | Rachel Green | Dir. Operations | Champion | 18 | 5 | 5d | frustrated | high | champion |
| Global Manufacturing | Tom Bennett | CFO | Economic Buyer | 4 | 1 | 14d | cautious | very_high | neutral |
| Global Manufacturing | Lisa Park | Legal Counsel | Legal | 10 | 2 | 3d | neutral | medium | blocker |
| Global Manufacturing | James Miller | VP Manufacturing | Executive Sponsor | 3 | 1 | 20d | positive | very_high | supporter |
| Apex Financial | David Liu | CTO | Technical Buyer | 5 | 1 | 12d | cautious | very_high | neutral |
| Apex Financial | Sarah Kim | VP Compliance | Compliance | 2 | 0 | 30d | unknown | high | unknown |
| Apex Financial | Mike Torres | IT Director | Technical Evaluator | 3 | 1 | 15d | neutral | medium | neutral |
| Metro Healthcare | Sandra Patel | VP Digital | Champion | 14 | 4 | 9d | positive | high | champion |
| Metro Healthcare | Dr. Karen Lee | CMO | Executive Sponsor | 3 | 1 | 14d | positive | very_high | supporter |
| Metro Healthcare | Brian Walsh | IT Security Manager | Technical Evaluator | 8 | 2 | 7d | positive | medium | supporter |
| Metro Healthcare | Nancy Drew | Finance Director | Budget Holder | 2 | 0 | 28d | unknown | high | unknown |
| Pacific Telecom | Diana Cruz | SVP Operations | Executive Sponsor | 16 | 5 | 3d | very_positive | very_high | champion |
| Pacific Telecom | Alex Huang | VP Engineering | Technical Buyer | 12 | 4 | 5d | positive | high | supporter |
| Pacific Telecom | Maria Santos | Procurement Director | Procurement | 8 | 2 | 2d | neutral | medium | neutral |
| Pacific Telecom | Kevin O'Brien | CTO | Economic Buyer | 6 | 2 | 7d | positive | very_high | supporter |
| Pacific Telecom | Priya Sharma | Data Analytics Lead | End User | 10 | 3 | 4d | very_positive | low | champion |

## Activity completion — 6 deals

| Deal | ID | Value | Stage | Owner | Completed Activity IDs | Skipped |
|------|----|-------|-------|-------|------------------------|---------|
| TechCorp Industries | OPP-001 | $890,000 | Proposal | Mike Chen | Q1-Q5, D1, D2, D4, D5, D6, P1, P2 | D3, P3, P4, P5, P6 |
| Global Manufacturing | OPP-002 | $720,000 | Negotiation | Lisa Torres | Q1-Q5, D1-D6, P1-P6, N1 | N2, N3, N4, N5 |
| Apex Financial | OPP-003 | $580,000 | Discovery | James Park | Q1, Q2, Q3, Q5, D1 | Q4, D2, D3, D4, D5, D6 |
| Metro Healthcare | OPP-004 | $440,000 | Proposal | Mike Chen | Q1-Q5, D1-D6, P1, P2, P3, P5 | P4, P6 |
| Pinnacle Logistics | OPP-005 | $360,000 | Qualification | James Park | Q1, Q2 | Q3, Q4, Q5 |
| Pacific Telecom | OPP-013 | $780,000 | Negotiation | Lisa Torres | Q1-Q5, D1-D6, P1-P6, N1, N2, N4 | N3, N5 |

## Competitive exposure — 5 deals

| Deal | ID | Value | Stage | Competitors in Evaluation | Incumbent | Prospect Priorities | Evaluation Status |
|------|----|-------|-------|---------------------------|-----------|---------------------|-------------------|
| TechCorp Industries | OPP-001 | $890,000 | Proposal | Nextera Platform, CloudFirst Systems | Legacy Corp ERP | AI capabilities, Integration speed, Total cost of ownership | Shortlisted to 2 vendors, final decision in 3 weeks |
| Pacific Telecom | OPP-013 | $780,000 | Negotiation | CloudFirst Systems | Legacy Corp ERP | API-first architecture, Real-time analytics, Scalability | Procurement stage, CloudFirst eliminated in technical eval |
| Global Manufacturing | OPP-002 | $720,000 | Negotiation | Vendara Solutions | None | Price, Manufacturing-specific features, Implementation speed | Verbal preference for us, Vendara offering 25% discount |
| Apex Financial | OPP-003 | $580,000 | Discovery | Nextera Platform, Vendara Solutions, CloudFirst Systems | Legacy Corp ERP | Security compliance, Financial services expertise, Scalability | Early evaluation, RFP expected in 2 weeks |
| Metro Healthcare | OPP-004 | $440,000 | Proposal | Nextera Platform | None | HIPAA compliance, Interoperability, Patient data security | Strong position, Nextera struggling with compliance requirements |
