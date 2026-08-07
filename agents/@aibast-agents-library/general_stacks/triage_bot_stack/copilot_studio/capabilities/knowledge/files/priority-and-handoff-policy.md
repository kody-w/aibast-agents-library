# Priority and Handoff Policy

> SYNTHETIC - DEMO DATA. This matrix, these clocks, and these templates are
> fictional demo policy. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real SLA policy and escalation templates.

## Priority matrix

Priority is a lookup on the (impact, urgency) pair. There is no other input -
not customer tier, not account value, not tone.

| Impact | Urgency | Priority | Response | Resolution | Auto-Escalate |
|--------|---------|----------|----------|------------|---------------|
| High | High | P1-Critical | 15m | 1h | Yes |
| High | Medium | P2-High | 30m | 4h | No |
| High | Low | P3-Medium | 60m | 8h | No |
| Medium | High | P2-High | 30m | 4h | No |
| Medium | Medium | P3-Medium | 60m | 8h | No |
| Medium | Low | P4-Low | 120m | 24h | No |
| Low | High | P3-Medium | 60m | 8h | No |
| Low | Medium | P4-Low | 120m | 24h | No |
| Low | Low | P5-Informational | 240m | 72h | No |

Fallback: if the pair does not resolve to a row - a value is missing or is not
one of high / medium / low - use the Medium/Medium row (P3-Medium, 60m response,
8h resolution, no auto-escalate) and state that the fallback was applied.

## Priority applied to the current queue

| ID | Impact | Urgency | Priority | Response Time |
|----|--------|---------|----------|---------------|
| INQ-T001 | High | High | P1-Critical | 15m |
| INQ-T002 | Low | Medium | P4-Low | 120m |
| INQ-T003 | Medium | Low | P4-Low | 120m |
| INQ-T004 | High | High | P1-Critical | 15m |

## Handoff templates

| Key | Template Name | Sections |
|-----|---------------|----------|
| technical_escalation | Technical Escalation | Customer Information; Issue Description; Steps Taken; Environment Details; Business Impact; Recommended Next Steps |
| management_escalation | Management Escalation | Customer Information; Account Value; Issue History; Customer Sentiment; Risk Assessment; Recommended Action |
| cross_team | Cross-Team Handoff | Customer Information; Original Category; Reason for Transfer; Context Summary; Outstanding Questions |

Every section of the chosen template is listed in the handoff, in template
order. A section that cannot be filled from the data is listed and marked as
not recorded - it is never dropped and never invented.
