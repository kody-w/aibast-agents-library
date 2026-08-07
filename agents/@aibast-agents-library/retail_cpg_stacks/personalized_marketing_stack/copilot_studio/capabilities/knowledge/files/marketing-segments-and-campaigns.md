# Marketing Segments and Campaigns

> SYNTHETIC — DEMO DATA. Every segment, campaign, offer, subject line, and
> product name in this document is fictional. This file exists so the agent has
> a working world to answer from on day one. In production, replace this file
> with tools that read your real CDP segments, campaign platform, and content
> management system (see the README's production section).

## Customer segments

| ID | Name | Size | Avg Age | Gender Split F/M/O | Avg Annual Spend | Orders/Yr | Avg Basket | LTV | Churn Risk | Engagement |
|----|------|------|---------|--------------------|------------------|-----------|------------|-----|------------|------------|
| SEG-LOYAL | Loyal Advocates | 42,850 | 38 | 56% / 42% / 2% | $1,875.00 | 18.3 | $102.46 | $11,250.00 | 4% | 92/100 |
| SEG-ATRISK | At-Risk Churners | 18,420 | 44 | 48% / 50% / 2% | $620.00 | 5.1 | $121.57 | $3,720.00 | 38% | 31/100 |
| SEG-NEW | New Explorers | 27,600 | 26 | 51% / 45% / 4% | $340.00 | 3.8 | $89.47 | $2,040.00 | 22% | 58/100 |
| SEG-HIGHVAL | High-Value VIPs | 8,750 | 47 | 60% / 38% / 2% | $4,200.00 | 24.6 | $170.73 | $33,600.00 | 6% | 97/100 |
| SEG-DORMANT | Dormant Lapsed | 34,200 | 41 | 47% / 51% / 2% | $85.00 | 0.8 | $106.25 | $510.00 | 72% | 9/100 |

Base totals: **131,820** total addressable customers; **$6,966.55**
size-weighted average LTV.

### Channel and category preferences

| ID | Preferred Channels (in preference order) | Top Categories |
|----|------------------------------------------|----------------|
| SEG-LOYAL | in_store, mobile_app | Apparel, Footwear, Accessories |
| SEG-ATRISK | email, desktop_web | Electronics, Home |
| SEG-NEW | social_media, mobile_app | Apparel, Beauty, Accessories |
| SEG-HIGHVAL | in_store, mobile_app, email | Premium Apparel, Footwear, Jewelry |
| SEG-DORMANT | email | Home, Electronics |

### Annual revenue contribution

`size x avg annual spend`

| Segment | Contribution |
|---------|--------------|
| Loyal Advocates | $80,343,750.00 |
| At-Risk Churners | $11,420,400.00 |
| New Explorers | $9,384,000.00 |
| High-Value VIPs | $36,750,000.00 |
| Dormant Lapsed | $2,907,000.00 |

## Campaign templates

| ID | Name | Type | Target Segment | Stages | Duration (days) | Offer | Open | Click | Convert |
|----|------|------|----------------|--------|-----------------|-------|------|-------|---------|
| CAMP-WINBACK | Win-Back Journey | automated_email | SEG-DORMANT | 4 | 28 | 20% off next purchase | 18% | 4% | 1.2% |
| CAMP-LOYALTY | Loyalty Tier Upgrade | multi_channel | SEG-LOYAL | 3 | 14 | Early access + double points | 42% | 15% | 8.0% |
| CAMP-NEWWELCOME | New Customer Welcome | automated_email | SEG-NEW | 5 | 30 | 15% off first order over $50 | 35% | 11% | 5.5% |
| CAMP-VIP | VIP Exclusive Preview | multi_channel | SEG-HIGHVAL | 2 | 7 | Private sale — 30% off new collection | 58% | 24% | 14.0% |

Open, click, and convert are historical rates from prior sends, not forecasts.
SEG-ATRISK has no campaign template in this library.

### Email sequences

**CAMP-WINBACK — Win-Back Journey (4 stages)**

1. We miss you — here is 20% off
2. Your favorites are waiting
3. Last chance: exclusive offer inside
4. Final reminder: your 20% expires tomorrow

**CAMP-LOYALTY — Loyalty Tier Upgrade (3 stages)**

1. You are almost Gold status!
2. Earn double points this weekend
3. Congratulations on your tier upgrade

**CAMP-NEWWELCOME — New Customer Welcome (5 stages)**

1. Welcome! Here is 15% off your first order
2. Discover our best sellers
3. Complete your look — curated picks
4. Your style profile is ready
5. Join our rewards program today

**CAMP-VIP — VIP Exclusive Preview (2 stages)**

1. VIP Only: private sale starts now
2. Your exclusive early access ends tonight

## Activation handoff reference

The activation package is assembled from the rows above - it adds no new facts.
Contact cost is `audience size x $0.35`, the only cost input in the model
(no creative, discount margin, or platform fees). Projected revenue is
`audience size x convert rate x segment avg basket`. Est. ROAS is projected
revenue divided by contact cost.

| Campaign | Type | Sequence channel | Segment preferred channels | Audience | Contact cost @ $0.35 | Projected revenue | Est. ROAS |
|----------|------|------------------|----------------------------|----------|----------------------|-------------------|-----------|
| CAMP-WINBACK | automated_email | email | email | 34,200 | $11,970.00 | $43,605.00 | 3.64x |
| CAMP-LOYALTY | multi_channel | email | in_store, mobile_app | 42,850 | $14,997.50 | $351,232.88 | 23.42x |
| CAMP-NEWWELCOME | automated_email | email | social_media, mobile_app | 27,600 | $9,660.00 | $135,815.46 | 14.06x |
| CAMP-VIP | multi_channel | email | in_store, mobile_app, email | 8,750 | $3,062.50 | $209,144.25 | 68.29x |

The sequence channel is email for every template because the stored sequences
are subject lines. Non-email channels for the two multi_channel campaigns are
not specified in this data. Email is not a stored preferred channel for
SEG-LOYAL or SEG-NEW - that mismatch is reported in the package, not resolved
by the agent.

Not in this data, and therefore never filled in by the agent: the destination
campaign platform, send dates and times, the human owner, and any offer,
audience, or channel that does not appear above. A package is always marked
`PREPARED - not sent`; execution is a person's action in the campaign platform
of record.

## Content blocks

### Hero banner

| Segment | Headline | CTA |
|---------|----------|-----|
| SEG-LOYAL | Thank You for Being a Loyal Customer | Shop Your Rewards |
| SEG-ATRISK | We Have Something Special for You | Rediscover Your Favorites |
| SEG-NEW | Welcome to the Family | Start Shopping |
| SEG-HIGHVAL | Exclusive Access Just for You | View Private Collection |
| SEG-DORMANT | It Has Been a While — Come Back | See What Is New |

### Product recommendations

| Segment | Recommendations |
|---------|-----------------|
| SEG-LOYAL | Classic Denim Jacket, Premium Running Shoes, Leather Crossbody Bag |
| SEG-ATRISK | Wireless Earbuds Pro, Smart Fitness Tracker |
| SEG-NEW | Organic Cotton T-Shirt, Stainless Water Bottle, UV Protection Sunglasses |
| SEG-HIGHVAL | Limited Edition Blazer, Designer Handbag, Artisan Watch |
| SEG-DORMANT | Best Sellers Bundle, Gift Card |
