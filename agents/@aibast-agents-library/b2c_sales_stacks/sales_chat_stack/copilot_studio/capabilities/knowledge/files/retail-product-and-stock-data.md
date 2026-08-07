# Retail Product and Stock Data

> SYNTHETIC - DEMO DATA. Every product, price, rating, and stock number in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real product catalog and inventory system (see the README's production
> section).

## Product catalog

| ID | Name | Category | Subcategory | Price | Rating | Reviews | Warranty |
|----|------|----------|-------------|-------|--------|---------|----------|
| PROD-101 | Ultra-Slim Laptop 14-inch | electronics | laptops | $999.99 | 4.6 | 842 | 1 year manufacturer |
| PROD-102 | Wireless Noise-Canceling Headphones | electronics | audio | $279.99 | 4.8 | 1,205 | 2 year manufacturer |
| PROD-103 | Smart Fitness Watch Series 5 | electronics | wearables | $349.99 | 4.5 | 678 | 1 year manufacturer |
| PROD-104 | Ergonomic Office Chair | furniture | chairs | $599.99 | 4.7 | 456 | 5 year manufacturer |
| PROD-105 | Robot Vacuum & Mop Combo | home | cleaning | $449.99 | 4.4 | 892 | 2 year manufacturer |

## Product descriptions and features

| ID | Description | Key Features |
|----|-------------|--------------|
| PROD-101 | 14-inch FHD display, 16GB RAM, 512GB SSD, Intel Core i7, all-day battery | Backlit keyboard; Fingerprint reader; USB-C charging; Wi-Fi 6E |
| PROD-102 | Premium over-ear headphones with adaptive ANC, 30-hour battery, multipoint connection | Adaptive noise canceling; Hi-Res Audio certified; Foldable design; Carrying case included |
| PROD-103 | Advanced fitness tracking, GPS, heart rate, SpO2, sleep analysis, 5ATM water resistance | Always-on display; 7-day battery; 100+ workout modes; Mobile payments |
| PROD-104 | Fully adjustable ergonomic mesh chair with lumbar support, headrest, and armrests | 12-position recline; Adjustable lumbar; Breathable mesh; Weight capacity 300 lbs |
| PROD-105 | LiDAR navigation, auto-empty station, simultaneous vacuum and mop | LiDAR mapping; Auto-empty base; App control; 2-in-1 vacuum/mop |

## Stock levels by location

| ID | Product | Online | Store Downtown | Store Mall | Store Suburban | Warehouse | Total |
|----|---------|--------|----------------|------------|----------------|-----------|-------|
| PROD-101 | Ultra-Slim Laptop 14-inch | 145 | 8 | 12 | 5 | 320 | 490 |
| PROD-102 | Wireless Noise-Canceling Headphones | 230 | 15 | 20 | 10 | 480 | 755 |
| PROD-103 | Smart Fitness Watch Series 5 | 78 | 4 | 6 | 2 | 150 | 240 |
| PROD-104 | Ergonomic Office Chair | 42 | 2 | 3 | 1 | 85 | 133 |
| PROD-105 | Robot Vacuum & Mop Combo | 95 | 5 | 7 | 3 | 200 | 310 |

## Stock status thresholds

Status is evaluated per location, on that location's quantity alone.

| Quantity at location | Status |
|----------------------|--------|
| Greater than 5 | In Stock |
| 1 to 5 | Low Stock |
| 0 | Out of Stock |

A product's overall availability reads `In Stock` when its total across all
five locations is greater than 0.
