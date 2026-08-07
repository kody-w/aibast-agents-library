# Engagement Metric Policy

> SYNTHETIC — DEMO DATA. A fictional retailer's measurement policy, included
> so the agent's formulas and thresholds are grounded in a citable document
> rather than only in its instructions. In production, replace this file with
> your own measurement standard.

## Why the formulas are fixed

Channel and campaign numbers drive budget decisions across teams that do not
share a definition of "performance". The measurement standard therefore fixes
one formula per metric and one rounding rule. A metric computed any other way
is not comparable and is not reported.

## Metric definitions

| Metric | Formula | Rounding | Suffix |
|--------|---------|----------|--------|
| CVR (channel) | conversions_30d / sessions_30d * 100 | 2 decimals | % |
| ROAS (channel) | revenue_30d / cost_30d | 2 decimals | x |
| Revenue share | revenue_30d / total_revenue * 100 | 1 decimal | % |
| Blended ROAS | total_revenue / total_cost | 1 decimal | x |
| ROI (campaign) | (revenue - cost) / cost * 100 | 1 decimal | % |
| Overall campaign ROI | (total_revenue - total_cost) / total_cost * 100 | 1 decimal | % |
| Open rate | opens / sent * 100 | 1 decimal | % |
| Click rate | clicks / sent * 100 | 1 decimal | % |
| Click-to-conversion | conversions / clicks * 100 | 1 decimal | % |
| Avg handle time | sum(handle_time_min) / total contacts | 1 decimal | min |
| Resolution rate | resolved contacts / total contacts * 100 | 1 decimal | % |
| Avg CSAT | sum(recorded csat) / count of recorded csat | 1 decimal | none |

Click rate uses **sent** as the denominator, never opens. Click-to-conversion
uses **clicks** as the denominator, never sent.

## Zero-denominator rules

1. `sessions_30d == 0` -> CVR is 0, reported as "no sessions recorded".
2. `cost_30d == 0` -> ROAS is 0, reported as "no cost recorded". It is never
   reported as "no return" and never ranked as the worst channel.
3. Campaign `cost == 0` -> ROI is 0, reported as "no cost recorded".
4. Campaign `sent == 0` -> no open rate and no click rate are produced; the
   campaign reports clicks only.
5. Campaign `clicks == 0` -> click-to-conversion is 0.
6. Contact `csat` not recorded -> the contact is excluded from the CSAT
   average and reported as "no CSAT recorded". It is never counted as a 0 and
   never counted in the CSAT denominator.

## Record-level rules

1. Customer interaction histories (CUST- ids) and support contacts (CASE- ids)
   are individual records. They are never summed into the channel, journey, or
   campaign roll-ups, and a roll-up figure is never quoted as a fact about one
   customer.
2. A support contact is not a session and not a conversion. Contact counts,
   handle time, resolution status, and CSAT belong only to the support set.
3. Contact totals — average handle time, resolution rate, average CSAT — always
   cover all recorded contacts. Naming one customer selects rows to read; it
   does not produce a filtered total.
4. Only "Resolved" counts toward the resolution rate. "Escalated" and "Open"
   do not.

## Spend recommendation thresholds

Applied to channel ROAS alone, in this order:

| Condition | Recommendation |
|-----------|----------------|
| ROAS > 50 | Scale investment |
| ROAS > 10 and ROAS <= 50 | Optimize spend |
| ROAS <= 10 | Review ROI |

The boundaries are strict: exactly 50.0x is "Optimize spend"; exactly 10.0x is
"Review ROI". Revenue size, conversion rate, bounce rate, and strategic
importance never change a channel's recommendation.

## Ordering rules

1. The channel performance report holds the recorded channel order — Email,
   Sms, Social Media, Web Organic, Web Paid, Mobile App, In Store — and is
   never re-sorted.
2. The efficiency ranking sorts descending by ROAS, and by nothing else.
3. Campaign attribution walks CAMP-301 through CAMP-305 in id order.
4. Journeys are reported in mapped order: Discovery to Purchase, Repeat
   Purchase, Win-Back, Impulse Purchase.
5. A unified interaction timeline is ordered by date, oldest first, with
   marketing touchpoints and support contacts interleaved. Support contacts
   are listed in case-id order: CASE-501 through CASE-506.

## Reporting boundaries

1. Totals and shares are always all-channel or all-campaign. Naming one
   channel or one campaign selects a row to read; it does not produce a
   filtered total.
2. Campaign revenue and channel revenue are separate roll-ups over the same
   period. They are never summed.
3. The agent reports and recommends. Pausing, launching, retargeting,
   rebudgeting, and sending are executed by the marketing owner, never by the
   agent and never implied as done. Routing, replying to, escalating, and
   closing a support case are executed by the contact center supervisor, on
   the same terms.
4. Anything outside the recorded seven channels, four journeys, five
   campaigns, three customer interaction histories, six support contacts, and
   single 30-day window has no data. The answer is "no data", not an estimate
   or a benchmark.
5. There is no live or real-time feed behind any of this. Every figure and
   record is the recorded set as captured; the agent never claims to be
   watching an interaction as it happens.
