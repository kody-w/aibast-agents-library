# Omnichannel Engagement Data

> SYNTHETIC — DEMO DATA. Every channel figure, journey, and campaign in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that
> read your real web/app analytics, CDP journey data, and campaign platform
> (see the README's production section).

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
