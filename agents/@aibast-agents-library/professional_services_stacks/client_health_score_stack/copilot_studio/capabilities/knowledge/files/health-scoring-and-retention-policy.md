# Health Scoring and Retention Policy

> SYNTHETIC -- DEMO DATA. These thresholds mirror the demo agent's rules exactly
> and are fictional policy. In production, replace this file with tools that
> read your real scoring model and account governance policy (see the README's
> production section).

## Health score and risk label

`health_score` (0-100) and `risk_label` arrive with the client record. The agent
reads them; it never recomputes, adjusts, or estimates either one.

Risk membership has one definition:

| Risk label | Meaning | Clients in this data |
|------------|---------|----------------------|
| CRITICAL | Active churn threat, executive escalation warranted | CL-301 TechCorp Industries (42/100) |
| AT_RISK | Deteriorating, save plan warranted | CL-302 Global Finance Corp (58/100), CL-303 Healthcare Solutions Inc (61/100) |
| HEALTHY | No save plan required | CL-304, CL-305, CL-306, CL-307, CL-308 |

"At risk" means CRITICAL or AT_RISK and nothing else. A negative NPS, a falling
satisfaction trend, or a thin margin does not by itself move a client into the
at-risk set.

## Churn probability bands

Derived from the health score alone. Report the band; never interpolate between
bands and never present the number as a modeled forecast.

| Health score | Churn probability |
|--------------|-------------------|
| <= 45 | 78% |
| 46 - 60 | 45% |
| 61 - 70 | 20% |
| 71 - 80 | 10% |
| 81 - 100 | 3% |

Applied to this data: TechCorp Industries 78%, Global Finance Corp 45%,
Healthcare Solutions Inc 20%.

## Satisfaction trend rule

Computed from the first and last of the four quarterly scores only.

| Condition | Trend | Rendered |
|-----------|-------|----------|
| fewer than 2 scores | insufficient_data | `-` |
| last > first + 0.3 | improving | **UP** |
| last < first - 0.3 | declining | **DOWN** |
| otherwise | stable | **FLAT** |

The band is exactly 0.3. A move of 0.3 or less either way is FLAT.

## Engagement red flags

Each flag fires only on its exact condition.

| Flag | Condition | Text |
|------|-----------|------|
| No executive contact | `exec_meetings_90d == 0` | No executive contact in 90 days |
| Escalation load | `escalations_90d >= 3` | N escalations in 90 days |
| Low utilization | `utilization_pct < 60` | Low utilization (N%) -- may not see value |
| Billing decline | `billing_trend == "declining"` | Declining billing trend |

The dashboard's `**LOW**` marker on the exec-meetings cell is a separate,
narrower rule: it appears only when `exec_meetings_90d == 0` **and** the client
is not HEALTHY.

## Retention action playbook

Actions are conditional on the same thresholds, evaluated in this order. The
final action always applies.

| Order | Condition | Recommended action |
|-------|-----------|--------------------|
| 1 | `exec_meetings_90d == 0` | Schedule executive sponsor meeting within 7 days |
| 2 | `escalations_90d >= 3` | Deploy SWAT team to resolve open issues |
| 3 | `utilization_pct < 60` | Review scope alignment; client may not be extracting full value |
| 4 | `nps < 0` | Conduct root-cause analysis on negative NPS drivers |
| 5 | always | Prepare value-delivered summary (ROI documentation) |

## Approval boundary

Every action above is a recommendation to the account lead. The agent does not
schedule meetings, deploy teams, open escalations, notify executives, issue
credits, or change contract terms, and never reports that any of those has
happened.
