# Abandoned Cart Data

> SYNTHETIC — DEMO DATA. Every customer, cart, SKU, and metric in this document
> is fictional. This file exists so the agent has a working world to answer
> from on day one. In production, replace this file with tools that read your
> real commerce platform, cart service, and marketing automation system (see
> the README's production section).

## Abandoned carts

| Cart ID | Customer | Email | Segment | Cart Value | Abandoned At | Exit Page | Device | Prior Purchases | Recovery Status |
|---------|----------|-------|---------|------------|--------------|-----------|--------|-----------------|-----------------|
| CART-20001 | Emily Rodriguez | e.rodriguez@example.com | loyal_shopper | $284.98 | 2025-03-04T14:22:00 | shipping_options | mobile | 8 | email_1_sent |
| CART-20002 | Michael Tang | m.tang@example.com | new_visitor | $299.97 | 2025-03-05T09:15:00 | account_creation | desktop | 0 | not_contacted |
| CART-20003 | Sarah Kim | s.kim@example.com | high_value | $1,779.96 | 2025-03-05T18:45:00 | payment | desktop | 12 | not_contacted |
| CART-20004 | Guest User | (none) | guest | $129.99 | 2025-03-06T11:30:00 | cart_page | mobile | 0 | unrecoverable |

Total abandoned value across these 4 carts: **$2,494.90**.

CART-20004 has no email address on file. It is unrecoverable: it is excluded
from the pending-recovery list and from incentive recommendations.

## Cart line items

| Cart ID | Item | SKU | Unit Price | Qty | Line Total |
|---------|------|-----|------------|-----|------------|
| CART-20001 | Wireless Noise-Canceling Headphones | ELEC-4421 | $249.99 | 1 | $249.99 |
| CART-20001 | Premium Headphone Case | ACC-1102 | $34.99 | 1 | $34.99 |
| CART-20002 | Smart Home Hub Pro | SMRT-3305 | $179.99 | 1 | $179.99 |
| CART-20002 | Smart Bulb 4-Pack | SMRT-1140 | $59.99 | 2 | $119.98 |
| CART-20003 | 4K OLED Smart TV 65-inch | TV-7720 | $1,299.99 | 1 | $1,299.99 |
| CART-20003 | Soundbar System | AUD-5501 | $449.99 | 1 | $449.99 |
| CART-20003 | HDMI Cable 6ft | ACC-0042 | $14.99 | 2 | $29.98 |
| CART-20004 | Running Shoes Pro X | SHOE-2201 | $129.99 | 1 | $129.99 |

## Exit page breakdown

| Exit Page | Carts |
|-----------|-------|
| shipping_options | 1 |
| account_creation | 1 |
| payment | 1 |
| cart_page | 1 |

## 30-day conversion metrics

| Metric | Value |
|--------|-------|
| Overall abandonment rate | 71.4% |
| Recovery rate | 12.8% |
| Average recovered order value | $187.50 |
| Total abandoned carts (30d) | 4,250 |
| Total recovered (30d) | 544 |
| Recovered revenue (30d) | $102,000 |

These are period totals for the whole business. They are not derived from the
four open cart records above, which are a live snapshot.

## Customer segments in use

| Segment | Meaning |
|---------|---------|
| high_value | Large basket, extensive purchase history |
| loyal_shopper | Repeat customer with prior purchases on record |
| new_visitor | Identified customer with zero prior purchases |
| guest | Unidentified checkout, no email captured |
