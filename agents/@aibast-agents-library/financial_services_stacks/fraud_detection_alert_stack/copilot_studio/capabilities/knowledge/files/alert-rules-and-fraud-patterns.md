# Alert Rules and Fraud Patterns

> SYNTHETIC — DEMO DATA. These rules, thresholds, and pattern definitions are
> fictional and exist so the agent has a working world to answer from on day
> one. In production, replace this file with tools that read your real detection
> rule engine and typology library (see the README's production section).

## Alert rules

| Rule ID | Name | Description | Threshold | Severity |
|---------|------|-------------|-----------|----------|
| RULE-001 | Velocity Check | Multiple high-value transactions within 1 hour | 2+ transactions over $1,000 within 60 minutes | high |
| RULE-002 | Geographic Anomaly | Transaction in country with no prior history | First transaction in high-risk country | high |
| RULE-003 | Crypto Purchase Spike | Unusual crypto exchange activity | Crypto transactions exceeding 3x normal volume | medium |
| RULE-004 | Wire to High-Risk Country | Wire transfer to FATF grey/black list country | Any wire to listed jurisdiction | critical |
| RULE-005 | Card-Not-Present Velocity | Rapid online purchases across merchants | 5+ online transactions within 30 minutes | medium |
| RULE-006 | Account Takeover Pattern | Password change followed by high-value transaction | Transaction within 2 hours of credential change | critical |

## Risk scoring bands

Every monitored transaction carries a numeric risk score from 0 to 100. The band
is a direct function of the score and is never adjusted:

| Score | Level |
|-------|-------|
| 80 and above | Critical |
| 60 to 79 | High |
| 40 to 59 | Medium |
| Below 40 | Low |

**Alert flagging threshold:** a transaction enters the alert queue only when its
risk score is **70 or above**. The headline flagged amount is the sum of amounts
across flagged transactions only.

**Open case statuses:** `open`, `under_review`, and `escalated` all count as
open workload. Any other status does not.

## Fraud patterns

| Pattern | Description | Frequency |
|---------|-------------|-----------|
| card_cloning | Physical card duplicated; used at multiple locations simultaneously | common |
| account_takeover | Unauthorized access to account via compromised credentials | increasing |
| bust_out | Deliberate credit line exhaustion before default | moderate |
| synthetic_identity | Fictitious identity created using mixed real and fake data | increasing |

### Pattern indicators

| Pattern | Indicators |
|---------|------------|
| card_cloning | Transactions in geographically distant locations within short timeframe; Card-present transactions after reported card-not-present use |
| account_takeover | Login from new device/IP; Immediate password and contact info change; Large transfer or purchase within hours |
| bust_out | Rapid utilization increase to near-limit; Cash advance activity; Payments stop after utilization spike |
| synthetic_identity | SSN with no credit history prior to 2 years ago; Authorized user on multiple unrelated accounts; Address inconsistencies |

Indicators describe what a pattern looks like. They are not a determination of
fraud and do not establish intent.
