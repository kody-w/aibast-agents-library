# Next Best Action Library and Selection Rule

> SYNTHETIC — DEMO DATA. Every action, channel, timing window, and expected
> conversion rate in this document is fictional. This file exists so the agent
> has a working world to answer from on day one. In production, replace this
> file with tools that read your real offer catalog and campaign performance
> system (see the README's production section).

## Action library

| Key | Action | Channel | Timing | Expected Conversion |
|-----|--------|---------|--------|---------------------|
| premium_engagement | Send personalized VIP preview of new collection | email | immediate | 22.5% |
| win_back | Send win-back offer with 20% discount and free shipping | email | immediate | 15.0% |
| loyalty_nurture | Remind of loyalty points balance and redemption options | mobile_push | next_3_days | 18.0% |
| service_recovery | Proactive outreach from manager with apology and store credit | phone | immediate | 35.0% |
| cross_sell | Recommend complementary products based on purchase history | email | next_7_days | 12.0% |
| reactivation_sms | Send SMS with limited-time exclusive offer | sms | next_3_days | 10.5% |

Expected conversion is a library constant, not a per-customer prediction.

## Selection rule

Evaluated top to bottom; the first branch that matches wins.

| Order | Condition | Selected action |
|-------|-----------|-----------------|
| 1 | sentiment label is `negative` AND segment is `at_risk` | service_recovery |
| 2 | segment is `premium` | premium_engagement |
| 3 | segment is `at_risk` | win_back |
| 4 | anything else, including segment `standard` | cross_sell |

Branch 1 requires both conditions. `loyalty_nurture` and `reactivation_sms`
are never produced by this rule; they are available only for a human to select
from the library.

## Current selection for this data set

| ID | Name | Segment | Sentiment | Score | Branch | Selected action | Expected Conversion |
|----|------|---------|-----------|-------|--------|-----------------|---------------------|
| C360-001 | Jessica Alvarez | premium | Neutral | 0.25 | 2 | Send personalized VIP preview of new collection | 22.5% |
| C360-002 | Brian O'Connell | standard | Positive | 0.5 | 4 | Recommend complementary products based on purchase history | 12.0% |
| C360-003 | Mei Lin Zhang | at_risk | Neutral | -0.25 | 3 | Send win-back offer with 20% discount and free shipping | 15.0% |

Mei Lin Zhang is in the `at_risk` segment but her sentiment label is `Neutral`
(-0.25, above the -0.30 threshold), so branch 1 does not fire and she receives
the win-back offer rather than service recovery.

## Execution boundary

The agent recommends. Sending the email, push, or SMS, applying the 20%
discount or store credit, and scheduling the manager call are all human
actions performed in the campaign and care systems.
