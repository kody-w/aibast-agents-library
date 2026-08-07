# Approval Matrix and Deal Profile

> SYNTHETIC - DEMO DATA. Every approver, SLA, customer, and deal figure in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real deal desk and CRM (see the README's production section).

## Approval matrix

| Discount Range | Approver | SLA | Auto-Approve Criteria |
|----------------|----------|-----|-----------------------|
| Up To 15 Pct | Sales Manager | 4h | Deal size > $50K and health score > 80 |
| 15 To 25 Pct | VP Sales | 8h | None |
| 25 To 35 Pct | CRO | 24h | None |
| Above 35 Pct | CEO | 48h | None |

Band selection uses the best applicable discount: `<= 15` -> Sales Manager,
`<= 25` -> VP Sales, `<= 35` -> CRO, above 35 -> CEO. Any eligible program
carrying `requires_approval` (EDU-001, NPO-001, COMP-001) makes the deal manual
regardless of the band.

## Deal profile on file

| Field | Value |
|-------|-------|
| Customer | Atlas Digital |
| Licenses | 175 |
| List price per license | $100/month |
| Term | 3 years |
| Products | Enterprise Platform, Analytics Pro, Integration Hub, Security Suite |
| Competitive switch | Yes - Competitor B |
| Tenure | 0 years |
| Health score | 0 |
| Education institution | No |
| Non-profit | No |

## Derived figures for this deal

| Metric | Value |
|--------|-------|
| Eligible programs | 4 - VOL-001 (15%), MULTI-001 (20%), COMP-001 (30%), BUNDLE-001 (18%) |
| Volume tier | Tier 2 (100-249 licenses), 15%, $85/license |
| List total | $630,000 (175 x $100 x 3 years x 12 months) |
| Best discount | 30% (COMP-001) |
| Total savings | $189,000 |
| Final price | $441,000 |
| Required approver | CRO (25-35% band), 24-hour SLA |
| Manual approval required | Yes - COMP-001 requires approval |
