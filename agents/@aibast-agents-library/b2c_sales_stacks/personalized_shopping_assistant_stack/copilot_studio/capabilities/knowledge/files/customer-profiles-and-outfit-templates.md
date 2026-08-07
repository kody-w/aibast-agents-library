# Customer Profiles and Outfit Templates

> SYNTHETIC — DEMO DATA. Every customer, preference, and purchase in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real CRM, clienteling, and order history systems (see the README's
> production section).

## Customer profiles

Exactly two customers exist in this data. Any other SHOP- id is unknown.

| Customer ID | Name | Size Top | Size Bottom | Size Shoe | Budget Range |
|-------------|------|----------|-------------|-----------|--------------|
| SHOP-001 | Daniel Reeves | L | 34 | 10 | $50 - $250 |
| SHOP-002 | Olivia Chen | S | 30 | 8 | $30 - $175 |

### Preferences

| Customer ID | Style Preference | Brand Affinity | Color Preference |
|-------------|------------------|----------------|------------------|
| SHOP-001 | classic, smart_casual | Heritage Co., Alpine Knits | navy, charcoal, white |
| SHOP-002 | casual, outdoor, athletic | Northfield, Stride Labs | olive, black, white_grey |

### Purchase history

Everything listed here is excluded from that customer's recommendations.

| Customer ID | SKU | Product | Price |
|-------------|-----|---------|-------|
| SHOP-001 | SKU-1001 | Classic Oxford Shirt — White | $68.00 |
| SHOP-001 | SKU-1002 | Slim Fit Chinos — Navy | $79.00 |
| SHOP-001 | SKU-1006 | Silk Pocket Square | $35.00 |
| SHOP-002 | SKU-1005 | Quilted Vest | $110.00 |
| SHOP-002 | SKU-1007 | Performance Running Shoe | $145.00 |

## Match score formula

The score is deterministic arithmetic, capped at 100.

| Term | Points |
|------|--------|
| Style tag overlap between product `style_tags` and customer `style_preference` | 20 per overlapping tag |
| Product brand appears in customer `brand_affinity` | 25 |
| Color overlap between product `colors` and customer `color_preference` | 10 per overlapping color |
| Product price falls inside `budget_range` (inclusive on both ends) | 15 |

`score = min(100, style_points + brand_points + color_points + budget_points)`

Worked example — SHOP-001 scoring SKU-1003 (Merino Wool Crew Sweater):
classic and smart_casual both overlap (2 x 20 = 40), brand Alpine Knits is in
brand affinity (+25 = 65), color charcoal overlaps (+10 = 75), $125.00 sits
inside $50 - $250 (+15 = 90). Reported as **90%**.

## Outfit templates

Four templates, always built in this order. Each slot is a
`category:subcategory` pair and is filled by the highest-scoring catalog item
matching both.

| Template ID | Display Name | Slots |
|-------------|--------------|-------|
| business_casual | Business Casual | tops:shirts, bottoms:pants, footwear:boots, accessories:pocket_squares |
| weekend_smart | Weekend Smart | tops:sweaters, bottoms:pants, footwear:boots |
| active_weekend | Active Weekend | outerwear:vests, footwear:athletic |
| evening_out | Evening Out | outerwear:blazers, tops:shirts, bottoms:pants, footwear:boots |

Outfit totals are the plain sum of the chosen pieces. There is no bundle
discount, tax, or shipping in this data.
