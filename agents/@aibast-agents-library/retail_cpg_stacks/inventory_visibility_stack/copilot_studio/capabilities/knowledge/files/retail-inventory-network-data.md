# Retail Inventory Network Data

> SYNTHETIC — DEMO DATA. Every store, warehouse, SKU, quantity, and cost in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real item master, warehouse management system, and store inventory
> feed (see the README's production section).

## Store locations

| ID | Name | City | State | Type | Capacity (sqft) |
|----|------|------|-------|------|-----------------|
| STR-001 | Downtown Flagship | Chicago | IL | flagship | 42,000 |
| STR-002 | Northshore Mall | Evanston | IL | mall | 18,500 |
| STR-003 | Oakbrook Center | Oak Brook | IL | outlet | 12,000 |
| STR-004 | Michigan Ave Express | Chicago | IL | express | 6,500 |

## Distribution centers

| ID | Name | City | State | Capacity (pallets) |
|----|------|------|-------|--------------------|
| WH-CENTRAL | Central Distribution Center | Romeoville | IL | 22,000 |
| WH-EAST | East Regional Warehouse | Indianapolis | IN | 14,000 |

## SKU catalog

| SKU | Product | Category | Unit Cost | Retail Price |
|-----|---------|----------|-----------|--------------|
| SKU-1001 | Classic Denim Jacket | Apparel | $34.50 | $89.99 |
| SKU-1002 | Wireless Earbuds Pro | Electronics | $18.75 | $59.99 |
| SKU-1003 | Organic Cotton T-Shirt | Apparel | $8.20 | $29.99 |
| SKU-1004 | Smart Fitness Tracker | Electronics | $42.00 | $129.99 |
| SKU-1005 | Premium Running Shoes | Footwear | $55.00 | $149.99 |
| SKU-1006 | Stainless Water Bottle | Accessories | $6.80 | $24.99 |
| SKU-1007 | Leather Crossbody Bag | Accessories | $27.50 | $79.99 |
| SKU-1008 | UV Protection Sunglasses | Accessories | $12.30 | $44.99 |

## Merchandise categories

Four categories partition the eight SKUs. Category managers own these
groupings; every dashboard, alert, and overstock view can be filtered to one.

| Category | SKUs | Count |
|----------|------|-------|
| Accessories | SKU-1006, SKU-1007, SKU-1008 | 3 |
| Apparel | SKU-1001, SKU-1003 | 2 |
| Electronics | SKU-1002, SKU-1004 | 2 |
| Footwear | SKU-1005 | 1 |

## On-hand inventory by location

| Location | SKU-1001 | SKU-1002 | SKU-1003 | SKU-1004 | SKU-1005 | SKU-1006 | SKU-1007 | SKU-1008 |
|----------|----------|----------|----------|----------|----------|----------|----------|----------|
| STR-001 | 74 | 132 | 210 | 45 | 38 | 195 | 61 | 88 |
| STR-002 | 35 | 67 | 98 | 22 | 14 | 110 | 29 | 53 |
| STR-003 | 18 | 41 | 65 | 9 | 7 | 72 | 15 | 30 |
| STR-004 | 12 | 28 | 44 | 6 | 5 | 55 | 8 | 19 |
| WH-CENTRAL | 1,450 | 2,300 | 3,800 | 780 | 620 | 4,100 | 950 | 1,700 |
| WH-EAST | 820 | 1,100 | 2,200 | 410 | 350 | 2,600 | 530 | 900 |

Total network inventory across all 6 locations: **26,315 units**.

## Category rollups

Derived from the tables above, not separately maintained. On-hand is the sum
over the locations named; daily sell-through is the sum of the member SKUs'
rates (a network-level figure); days of supply is on-hand divided by that rate;
value is at unit cost, never retail.

Across the four stores (1,705 units in total):

| Category | SKUs | On-Hand | Daily Sell-Through | Days of Supply | Value at Unit Cost |
|----------|------|---------|--------------------|----------------|--------------------|
| Accessories | 3 | 735 | 23.7 | 31.0 | $8,382.10 |
| Apparel | 2 | 556 | 20.7 | 26.9 | $8,214.90 |
| Electronics | 2 | 350 | 12.9 | 27.1 | $8,469.00 |
| Footwear | 1 | 64 | 2.7 | 23.7 | $3,520.00 |

Across all 6 locations (26,315 units in total):

| Category | SKUs | On-Hand | Daily Sell-Through | Days of Supply | Value at Unit Cost |
|----------|------|---------|--------------------|----------------|--------------------|
| Accessories | 3 | 11,515 | 23.7 | 485.9 | $126,622.10 |
| Apparel | 2 | 8,826 | 20.7 | 426.4 | $135,729.90 |
| Electronics | 2 | 4,940 | 12.9 | 382.9 | $122,199.00 |
| Footwear | 1 | 1,034 | 2.7 | 383.0 | $56,870.00 |

Because the sell-through rates are network-level, a rollup that spans more
locations reads as more days of cover. Always say which locations a category
number covers.

## Safety stock by store

Safety stock is defined for stores only. The two distribution centers have no
safety-stock floor in this data set; report theirs as `N/A`.

| Location | SKU-1001 | SKU-1002 | SKU-1003 | SKU-1004 | SKU-1005 | SKU-1006 | SKU-1007 | SKU-1008 |
|----------|----------|----------|----------|----------|----------|----------|----------|----------|
| STR-001 | 30 | 50 | 80 | 20 | 15 | 70 | 25 | 35 |
| STR-002 | 15 | 30 | 45 | 10 | 8 | 40 | 12 | 20 |
| STR-003 | 10 | 20 | 30 | 5 | 5 | 25 | 8 | 12 |
| STR-004 | 8 | 15 | 20 | 4 | 3 | 20 | 5 | 10 |

## Warehouse-to-store lead times (days)

| Source | STR-001 | STR-002 | STR-003 | STR-004 |
|--------|---------|---------|---------|---------|
| WH-CENTRAL | 1 | 1 | 2 | 1 |
| WH-EAST | 2 | 2 | 3 | 2 |

Any warehouse/store pair not listed above defaults to 3 days, and the agent
must say the value is a fallback.
