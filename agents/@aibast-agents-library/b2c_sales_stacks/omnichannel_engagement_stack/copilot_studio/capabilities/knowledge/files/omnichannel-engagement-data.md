# Cross-Channel Engagement Data

> SYNTHETIC — DEMO DATA. Every channel figure, journey, campaign, customer
> interaction record, and support case in this document is fictional. This file
> exists so the agent has a working world to answer from on day one. In
> production, replace this file with tools that read your real web/app
> analytics, CDP journey and interaction data, campaign platform, and service
> case system (see the README's production section).

This data set has two levels, and they are never mixed:

- **Roll-ups** — channel performance, mapped journeys, campaign results. These
  are aggregates over the trailing 30 days.
- **Record-level interactions** — per-customer interaction histories
  (CUST-401 to CUST-403) and support cases (CASE-501 to CASE-506). These are
  individual records. They are never summed into the roll-ups, and the roll-ups
  are never used to describe one customer.

All channel figures cover the trailing 30 days. There is no other period in
this data set.

## Channel performance (trailing 30 days)

| Channel | Sessions | Conversions | Revenue | Cost | Avg Order Value | Bounce Rate |
|---------|----------|-------------|---------|------|-----------------|-------------|
| Email | 145,000 | 4,350 | $870,000 | $12,500 | $200.00 | 18.5% |
| Sms | 62,000 | 1,860 | $325,500 | $8,200 | $175.00 | 5.2% |
| Social Media | 230,000 | 2,760 | $552,000 | $45,000 | $200.00 | 42.0% |
| Web Organic | 480,000 | 9,600 | $1,920,000 | $18,000 | $200.00 | 35.0% |
| Web Paid | 185,000 | 5,550 | $1,110,000 | $95,000 | $200.00 | 28.0% |
| Mobile App | 310,000 | 12,400 | $2,480,000 | $22,000 | $200.00 | 12.0% |
| In Store | 95,000 | 28,500 | $5,700,000 | $180,000 | $200.00 | 0% |

Mix totals: **$12,957,500 revenue**, **65,020 conversions**, **$380,700
marketing spend**. The rows above are the complete channel set — Email, Sms,
Social Media, Web Organic, Web Paid, Mobile App, In Store. Any other channel
has no data here.

## Mapped customer journeys

| Journey | Avg Duration | Avg Touchpoints | Conversion Rate |
|---------|--------------|-----------------|-----------------|
| Discovery to Purchase | 14 days | 5 | 3.2% |
| Repeat Purchase | 3 days | 3 | 18.5% |
| Win-Back | 21 days | 4 | 8.4% |
| Impulse Purchase | 0 days | 2 | 1.8% |

Touchpoint sequences, in order:

| Journey | Touchpoint sequence |
|---------|---------------------|
| Discovery to Purchase | Social Media Ad -> Website Browse -> Email Signup -> Email Promo -> Website Purchase |
| Repeat Purchase | Email Promo -> Mobile App Browse -> Mobile App Purchase |
| Win-Back | Email Winback -> Sms Offer -> Website Browse -> Website Purchase |
| Impulse Purchase | Social Media Ad -> Website Purchase |

The journey set carries no revenue, cost, or volume figures. Journey
touchpoint labels are not the same records as the seven performance channels
and must not be joined to them.

### Recorded journey optimization opportunities

- **Discovery:** Shorten path by enabling social commerce checkout
- **Repeat:** Leverage push notifications for faster re-engagement
- **Win-Back:** Test earlier SMS touchpoint (day 7 vs day 14)
- **Impulse:** Optimize social ad creative for direct conversion

## Campaign results

| ID | Campaign | Channel | Sent | Opens | Clicks | Conversions | Revenue | Cost |
|----|----------|---------|------|-------|--------|-------------|---------|------|
| CAMP-301 | Spring Collection Launch | email | 250,000 | 62,500 | 18,750 | 2,250 | $450,000 | $5,000 |
| CAMP-302 | Flash Sale — 48 Hours | sms | 120,000 | 115,200 | 24,000 | 3,600 | $540,000 | $6,000 |
| CAMP-303 | Influencer Partnership | social_media | 0 | 0 | 85,000 | 1,700 | $340,000 | $35,000 |
| CAMP-304 | Google Shopping Ads | web_paid | 0 | 0 | 45,000 | 2,700 | $540,000 | $42,000 |
| CAMP-305 | App Push — Loyalty Members | mobile_app | 85,000 | 42,500 | 17,000 | 5,100 | $765,000 | $2,000 |

Portfolio totals: **$2,635,000 revenue** on **$90,000 cost** across the five
campaigns. Campaign revenue is a subset of the 30-day channel revenue; the two
totals are never added together.

`sent` and `opens` of 0 for CAMP-303 and CAMP-304 mean those channels do not
send — not that engagement was zero.

## Customer interaction records

Three customers have a recorded interaction history. Each row is one
touchpoint. These records carry no revenue, cost, session, or conversion
figures and are never added to the channel or campaign roll-ups above.

### CUST-401 — Loyalty - repeat purchaser (mapped journey: Repeat Purchase)

| Date | Channel | Interaction | Reference |
|------|---------|-------------|-----------|
| 2026-07-06 | email | Opened promo email | CAMP-301 |
| 2026-07-06 | mobile_app | Browsed three product pages | - |
| 2026-07-08 | mobile_app | Placed order | - |
| 2026-07-09 | email | Received order confirmation | - |
| 2026-07-11 | in_store | Collected order at store pickup desk | - |

### CUST-402 — Lapsed - win-back target (mapped journey: Win-Back)

| Date | Channel | Interaction | Reference |
|------|---------|-------------|-----------|
| 2026-06-24 | email | Opened win-back offer | - |
| 2026-06-27 | sms | Clicked offer link | CAMP-302 |
| 2026-07-01 | web_organic | Browsed site, no cart created | - |
| 2026-07-05 | web_paid | Returned to site from shopping ad | CAMP-304 |
| 2026-07-06 | web_organic | Placed order | - |

### CUST-403 — New - discovery (mapped journey: Discovery to Purchase)

| Date | Channel | Interaction | Reference |
|------|---------|-------------|-----------|
| 2026-07-03 | social_media | Engaged with influencer post | CAMP-303 |
| 2026-07-03 | web_organic | Browsed site | - |
| 2026-07-04 | email | Signed up for newsletter | - |
| 2026-07-10 | email | Clicked promo email | CAMP-301 |
| 2026-07-17 | in_store | Completed purchase in store | - |

CUST-401, CUST-402, and CUST-403 are the complete set of interaction
histories. A campaign reference on a touchpoint records where the touchpoint
came from; it never changes that campaign's recorded conversions, revenue, or
cost. The mapped journey named for a customer is a label on the record, not a
claim that this customer produced the journey's conversion rate.

## Support interactions

Support contacts use the same channel vocabulary as the performance set, but a
contact is not a session. Support contacts are never added to channel
sessions, conversions, or revenue.

| Case | Customer | Date | Channel | Intent | Handle Time | Resolution | CSAT |
|------|----------|------|---------|--------|-------------|------------|------|
| CASE-501 | CUST-401 | 2026-07-12 | mobile_app | Order status | 6 min | Resolved | 5 |
| CASE-502 | CUST-402 | 2026-07-02 | sms | Promo code not applying | 11 min | Resolved | 4 |
| CASE-503 | CUST-403 | 2026-07-19 | email | Delivery delay | 34 min | Resolved | 3 |
| CASE-504 | CUST-403 | 2026-07-22 | in_store | Return or exchange | 18 min | Resolved | 5 |
| CASE-505 | CUST-401 | 2026-07-15 | web_organic | Account login | 22 min | Escalated | 2 |
| CASE-506 | CUST-402 | 2026-07-09 | social_media | Damaged item | 47 min | Open | no CSAT recorded |

Contact totals: **6 contacts**, **23.0 min average handle time**, **66.7%
resolution rate** (4 of 6 Resolved), **3.8 average CSAT** across the 5 scored
contacts. CASE-506 has no CSAT because the case is still Open — that is a
missing score, not a score of zero, and it is excluded from the CSAT average.

CASE-501 through CASE-506 are the complete case set. Web Paid records no
support contacts. Contacts whose resolution status is not "Resolved"
(CASE-505 Escalated, CASE-506 Open) are the ones a supervisor still owns.
