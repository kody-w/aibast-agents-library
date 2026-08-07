# Loyalty Program Data

> SYNTHETIC — DEMO DATA. Every member, balance, and reward in this document is
> fictional. This file exists so the agent has a working world to answer from
> on day one. In production, replace this file with tools that read your real
> loyalty platform and redemption catalog (see the README's production
> section).

## Member roster

| ID | Name | Tier | Points Balance | Earned YTD | Redeemed YTD | Spend YTD | Engagement | Member Since | Birthday Month | Preferred Reward Categories |
|----|------|------|----------------|------------|--------------|-----------|------------|--------------|----------------|------------------------------|
| LM-10001 | Katherine Brooks | platinum | 48,250 | 12,400 | 8,000 | $6,200 | 92 | 2018-03-15 | 5 | travel, dining |
| LM-10002 | Antonio Vasquez | gold | 22,100 | 6,800 | 2,500 | $3,400 | 75 | 2020-08-22 | 11 | merchandise, gift_cards |
| LM-10003 | Rachel Nguyen | silver | 8,450 | 3,200 | 0 | $1,600 | 58 | 2023-01-10 | 3 | discounts |
| LM-10004 | Derek Washington | bronze | 2,100 | 900 | 0 | $450 | 32 | 2024-06-05 | 8 | discounts, free_shipping |

Program totals: 4 members, 80,900 points outstanding ($1,618.00), $11,650
total member spend YTD. Tier distribution: Platinum 1, Gold 1, Silver 1,
Bronze 1.

## Redemption catalog

| Reward ID | Reward | Points Cost | Category | Cash Value |
|-----------|--------|-------------|----------|------------|
| travel_voucher_500 | $500 Travel Voucher | 25,000 | travel | $500 |
| dining_card_100 | $100 Dining Gift Card | 5,000 | dining | $100 |
| merch_headphones | Premium Wireless Headphones | 15,000 | merchandise | $249 |
| gift_card_50 | $50 Store Gift Card | 2,500 | gift_cards | $50 |
| discount_20pct | 20% Off Next Purchase | 3,000 | discounts | Discount (no fixed cash value) |
| free_shipping_3mo | Free Shipping for 3 Months | 1,500 | free_shipping | $30 |

## Earning activities

| Activity | Points | Frequency |
|----------|--------|-----------|
| Purchase | 2 per $1 spent | per_transaction |
| Product Review | 100 bonus | per_review |
| Referral Signup | 500 bonus | per_referral |
| Birthday | Double points for birthday month | annual |
| Social Share | 50 bonus | per_share |
| App Download | 250 one-time bonus | once |
