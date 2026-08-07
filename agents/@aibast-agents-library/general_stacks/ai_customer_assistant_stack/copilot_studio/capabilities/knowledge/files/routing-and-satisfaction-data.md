# Routing Matrix and Satisfaction Data

> SYNTHETIC — DEMO DATA. Every team, SLA, score, and survey comment in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real routing configuration and survey platform (see the README's
> production section).

## Routing matrix

Route is the intersection of the inquiry's category and priority. The matrix
covers exactly three categories and four priorities. An unknown category falls
back to the Technical Issue rows; an unknown priority falls back to Medium.

| Category | Priority | Team | SLA | Auto-Escalate |
|----------|----------|------|-----|---------------|
| Technical Issue | Critical | Tier 2 Engineering | 2h | Yes |
| Technical Issue | High | Tier 1 Technical Support | 4h | No |
| Technical Issue | Medium | General Support | 8h | No |
| Technical Issue | Low | General Support | 24h | No |
| Billing & Pricing | Critical | Billing Escalations | 2h | Yes |
| Billing & Pricing | High | Account Management | 4h | No |
| Billing & Pricing | Medium | Account Management | 8h | No |
| Billing & Pricing | Low | Self-Service Billing | 24h | No |
| Feature Request | Critical | Product Management | 8h | No |
| Feature Request | High | Product Management | 24h | No |
| Feature Request | Medium | Product Backlog | 72h | No |
| Feature Request | Low | Product Backlog | 168h | No |

Auto-escalate is on in exactly two cells: Technical Issue / Critical and
Billing & Pricing / Critical.

### Resolved routes for the open queue

| Inquiry | Category | Priority | Team | SLA | Auto-Escalate |
|---------|----------|----------|------|-----|---------------|
| INQ-4001 | Technical Issue | High | Tier 1 Technical Support | 4 hours | No |
| INQ-4002 | Billing & Pricing | Medium | Account Management | 8 hours | No |
| INQ-4003 | Technical Issue | Critical | Tier 2 Engineering | 2 hours | Yes |
| INQ-4004 | Feature Request | Low | Product Backlog | 168 hours | No |

## Satisfaction headline metrics

| Metric | Value |
|--------|-------|
| Overall CSAT | 4.3/5.0 |
| NPS Score | 42 |
| Avg Response Time | 12 minutes |
| First Contact Resolution | 78% |
| Trend, week over week | +0.2 |
| Trend, month over month | +0.1 |

## Recent surveys

| Inquiry | Score | Comment | Date |
|---------|-------|---------|------|
| INQ-3990 | 5 | Resolved quickly, great experience. | 2025-11-13 |
| INQ-3988 | 4 | Helpful but took a while to connect. | 2025-11-13 |
| INQ-3985 | 3 | Issue resolved but had to explain problem multiple times. | 2025-11-12 |
| INQ-3982 | 5 | Agent was knowledgeable and proactive. | 2025-11-12 |
| INQ-3979 | 2 | Still waiting for follow-up on my SSO issue. | 2025-11-11 |
| INQ-3975 | 4 | Good resolution, would prefer faster initial response. | 2025-11-11 |

Comments are truncated to their first 50 characters when displayed in the
dashboard, so the INQ-3985 and INQ-3975 rows end mid-word.

## Score distribution

Counted across the six surveys above; percent is count divided by 6.

| Rating | Count | Percent |
|--------|-------|---------|
| 5 Star | 2 | 33% |
| 4 Star | 2 | 33% |
| 3 Star | 1 | 17% |
| 2 Star | 1 | 17% |
| 1 Star | 0 | 0% |

Promoters (score 4 or higher): 4 of 6. Detractors (score 2 or lower): 1 of 6.
These are derived from the survey rows and are not the NPS, which is the stored
value 42.
