# Product Catalog and Inventory Data

> SYNTHETIC — DEMO DATA. Every product, brand, price, and stock number in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real product master and inventory system (see the README's production
> section).

## Product catalog

| SKU | Product | Category | Subcategory | Brand | Price | Rating | Style Tags |
|-----|---------|----------|-------------|-------|-------|--------|------------|
| SKU-1001 | Classic Oxford Shirt — White | tops | shirts | Heritage Co. | $68.00 | 4.7 | classic, business, smart_casual |
| SKU-1002 | Slim Fit Chinos — Navy | bottoms | pants | Heritage Co. | $79.00 | 4.5 | classic, smart_casual, weekend |
| SKU-1003 | Merino Wool Crew Sweater | tops | sweaters | Alpine Knits | $125.00 | 4.8 | classic, smart_casual, layering |
| SKU-1004 | Leather Chelsea Boots | footwear | boots | Cobblestone | $195.00 | 4.6 | classic, smart_casual, evening |
| SKU-1005 | Quilted Vest | outerwear | vests | Northfield | $110.00 | 4.4 | casual, outdoor, layering |
| SKU-1006 | Silk Pocket Square | accessories | pocket_squares | Heritage Co. | $35.00 | 4.9 | classic, business, evening |
| SKU-1007 | Performance Running Shoe | footwear | athletic | Stride Labs | $145.00 | 4.7 | athletic, casual, performance |
| SKU-1008 | Linen Blazer — Unstructured | outerwear | blazers | Riviera Style | $225.00 | 4.3 | smart_casual, evening, summer |

## Sizes and colors

| SKU | Sizes | Colors |
|-----|-------|--------|
| SKU-1001 | S, M, L, XL | white, blue, pink |
| SKU-1002 | 30, 32, 34, 36 | navy, khaki, olive |
| SKU-1003 | S, M, L, XL | charcoal, burgundy, forest |
| SKU-1004 | 8, 9, 10, 11, 12 | brown, black |
| SKU-1005 | S, M, L, XL | navy, olive, black |
| SKU-1006 | OS | navy_paisley, burgundy_dot, green_stripe |
| SKU-1007 | 8, 9, 10, 11, 12 | white_grey, black_red |
| SKU-1008 | S, M, L, XL | tan, light_blue |

## Stock ledger by size

| SKU | Per-size stock | Total Units |
|-----|----------------|-------------|
| SKU-1001 | S 12, M 25, L 18, XL 8 | 63 |
| SKU-1002 | 30: 6, 32: 15, 34: 20, 36: 10 | 51 |
| SKU-1003 | S 4, M 10, L 8, XL 3 | 25 |
| SKU-1004 | 8: 5, 9: 8, 10: 12, 11: 7, 12: 3 | 35 |
| SKU-1005 | S 2, M 7, L 5, XL 9 | 23 |
| SKU-1006 | OS 30 | 30 |
| SKU-1007 | 8: 10, 9: 15, 10: 20, 11: 12, 12: 6 | 63 |
| SKU-1008 | S 3, M 6, L 4, XL 2 | 15 |

## Stock status thresholds

Two thresholds apply at two different levels. They are not interchangeable.

| Level | In Stock | Low Stock | Out of Stock |
|-------|----------|-----------|--------------|
| Per size | more than 5 units | 1 to 5 units | 0 units |
| Per SKU (total across sizes) | more than 10 units | 1 to 10 units | 0 units |

At the totals above, all eight SKUs read **In Stock** at catalog level. At size
level several sizes read Low Stock — for example SKU-1005 size S (2 units),
SKU-1008 size XL (2 units), SKU-1003 size XL (3 units), and SKU-1004 size 12
(3 units).
