# Health Score and Next-Best-Action Policy

> SYNTHETIC -- DEMO DATA. These weights, bands, and playbooks are the fictional
> policy this demo agent scores against. This file exists so the agent has a
> working world to answer from on day one. In production, replace this file with
> tools that read your real customer-success scoring model and play library (see
> the README's production section).

## Component weights

| Component | Weight | Formula |
|-----------|--------|---------|
| Product Adoption | 25% | `min(100, employees_using / licenses_purchased * 100 * 1.2)` |
| Support Satisfaction | 20% | `csat_avg / 5.0 * 100` |
| Engagement Frequency | 20% | `min(100, interaction_count * 20)` |
| Billing Health | 15% | `100` if outstanding balance is `$0`, otherwise `60` |
| Relationship Strength | 20% | `positive_interactions / max(1, interaction_count) * 100` (sentiment exactly `Positive`) |

Overall score is the weighted sum, rounded to the nearest whole number.

## Health bands

| Band | Range | Playbook |
|------|-------|----------|
| Healthy | score >= 80 | high health |
| At Risk | 60 to 79 | medium health |
| Critical | below 60 | low health |

## Current standing

| ID | Name | Score | Band | Adoption | Support | Engagement | Billing | Relationship |
|----|------|-------|------|----------|---------|------------|---------|--------------|
| CUST-3001 | TechVantage Solutions | 90/100 | Healthy | 100 | 92 | 100 | 100 | 60 |
| CUST-3002 | Greenridge Partners | 65/100 | At Risk | 100 | 76 | 80 | 60 | 0 |
| CUST-3003 | BlueHorizon Health | 90/100 | Healthy | 96 | 96 | 60 | 100 | 100 |

Rendering note: the component table produced by the scoring engine shows the
Product Adoption row as `0/100` with a weighted value of `0.0`, even though the
adoption values above are included in the overall score. The weighted column
therefore does not sum to the overall score. The overall score is authoritative.

## Playbook -- high health (score >= 80)

| Action | Priority | Reason |
|--------|----------|--------|
| Schedule expansion discussion | Medium | Strong health score indicates readiness for upsell |
| Invite to customer advisory board | Low | Champion potential for reference program |
| Share product roadmap preview | Medium | Deepen partnership and gather feedback |

## Playbook -- medium health (score 60 to 79)

| Action | Priority | Reason |
|--------|----------|--------|
| Schedule adoption review | High | Usage below potential, identify barriers |
| Offer training session | High | Improve feature utilization |
| CSM check-in call | Medium | Proactive relationship maintenance |

## Playbook -- low health (score below 60)

| Action | Priority | Reason |
|--------|----------|--------|
| Executive escalation meeting | Critical | Churn risk - requires immediate attention |
| Create success plan | Critical | Define clear path to value realization |
| Resolve open support tickets | High | Outstanding issues impacting satisfaction |
