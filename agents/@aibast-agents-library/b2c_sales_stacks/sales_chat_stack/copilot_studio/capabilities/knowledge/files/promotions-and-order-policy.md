# Promotions and Order Policy

> SYNTHETIC - DEMO DATA. Every promotion, code, shipping rate, and policy term
> in this document is fictional. This file exists so the agent has a working
> world to answer from on day one. In production, replace this file with tools
> that read your real promotion engine and order management system (see the
> README's production section).

## Active promotions

| Promo | Name | Discount | Code | Valid From | Valid Through | Applies To | Min Purchase | Stackable |
|-------|------|----------|------|------------|---------------|------------|--------------|-----------|
| PROMO-SP25 | Spring Tech Sale | 15% off | SPRING15 | 2025-03-01 | 2025-03-31 | electronics | $200 | No |
| PROMO-BUNDLE | Smart Home Bundle | $75 off | SMARTHOME75 | 2025-03-10 | 2025-04-10 | electronics, home | $500 | No |
| PROMO-SHIP | Free Shipping Weekend | Free shipping | FREESHIP | 2025-03-14 | 2025-03-16 | all | $50 | Yes |
| PROMO-CHAIR | Home Office Upgrade | 20% off | OFFICE20 | 2025-03-05 | 2025-03-25 | furniture | None | Yes |

## Best applicable offer per product

An offer applies only when its categories cover the product AND the product's
price is at or above the offer's minimum purchase. Percentage savings are
`price * value / 100`; fixed savings are the value; free shipping contributes
$0 of product savings and therefore never wins the comparison.

| ID | Product | List Price | Winning Offer | Code | Savings | Sale Price |
|----|---------|-----------|---------------|------|---------|------------|
| PROD-101 | Ultra-Slim Laptop 14-inch | $999.99 | PROMO-SP25 (15%) | SPRING15 | $150.00 | $849.99 |
| PROD-102 | Wireless Noise-Canceling Headphones | $279.99 | PROMO-SP25 (15%) | SPRING15 | $42.00 | $237.99 |
| PROD-103 | Smart Fitness Watch Series 5 | $349.99 | PROMO-SP25 (15%) | SPRING15 | $52.50 | $297.49 |
| PROD-104 | Ergonomic Office Chair | $599.99 | PROMO-CHAIR (20%) | OFFICE20 | $120.00 | $479.99 |
| PROD-105 | Robot Vacuum & Mop Combo | $449.99 | None - $449.99 is below the $500 minimum for PROMO-BUNDLE | - | $0.00 | $449.99 |

Non-stackable promotions cannot be combined with other offers.

## Shipping options

| Method | Delivery Time | Cost |
|--------|---------------|------|
| Standard Shipping | 5-7 business days | $8.95 |
| Express Shipping | 2-3 business days | $14.95 |
| Next Day | Next business day | $24.95 |
| Store Pickup | Same day (if in stock) | Free |

## Order support topics

| Topic | Policy |
|-------|--------|
| Order Tracking | Provide order number for real-time tracking updates |
| Order Modification | Changes can be made within 1 hour of placement |
| Cancellation | Full refund if cancelled before shipment |
| Price Match | We match verified competitor prices within 14 days of purchase |
| Gift Wrapping | Available for $5.99 per item at checkout |
| International Shipping | Available to 40+ countries; duties calculated at checkout |

## Payment methods accepted

| Method |
|--------|
| Visa |
| Mastercard |
| Amex |
| Discover |
| PayPal |
| Apple Pay |
| Google Pay |
| Affirm (Buy Now, Pay Later) |
