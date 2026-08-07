# Returns and Exchange Data

> SYNTHETIC — DEMO DATA. Every customer, order, return, and stock figure in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real order management, RMA, and inventory systems (see the README's
> production section).

## Orders

| Order | Customer | Order Date | Delivered | Order Total | Shipping Paid | Payment Method |
|---|---|---|---|---|---|---|
| ORD-55001 | Amanda Collins | 2025-02-15 | 2025-02-20 | $217.00 | $0.00 | credit_card |
| ORD-55002 | James Lee | 2025-01-28 | 2025-02-02 | $185.00 | $8.95 | paypal |
| ORD-55003 | Sophie Martin | 2025-02-25 | 2025-03-01 | $372.00 | $0.00 | credit_card |
| ORD-55004 | Derek Patel | 2024-12-10 | 2024-12-15 | $159.00 | $5.95 | credit_card |

## Order line items

| Order | SKU | Item | Size | Price | Qty |
|---|---|---|---|---|---|
| ORD-55001 | DRS-4420 | Midi Wrap Dress — Emerald | M | $128.00 | 1 |
| ORD-55001 | SHL-2201 | Cashmere Scarf — Charcoal | — | $89.00 | 1 |
| ORD-55002 | SNK-7710 | Premium Leather Sneakers — White | 10 | $185.00 | 1 |
| ORD-55003 | JKT-3315 | Quilted Puffer Jacket — Black | S | $245.00 | 1 |
| ORD-55003 | BT-1190 | Ankle Rain Boots | 7 | $95.00 | 1 |
| ORD-55003 | UM-0050 | Compact Umbrella — Navy | — | $32.00 | 1 |
| ORD-55004 | ELEC-8820 | Wireless Earbuds Pro | — | $159.00 | 1 |

## Active returns

| Return ID | Order | Items | Reason | Type | Status | RMA Issued | Label Sent |
|---|---|---|---|---|---|---|---|
| RET-8001 | ORD-55001 | DRS-4420 | wrong_size | exchange | awaiting_return | 2025-03-02 | Yes |
| RET-8002 | ORD-55002 | SNK-7710 | defective | refund | received_inspecting | 2025-03-04 | Yes |

## Exchange inventory

Only these SKUs carry exchange inventory. A SKU that does not appear here has
no exchange options on file.

| SKU | Size | Stock | Status |
|---|---|---|---|
| DRS-4420 | XS | 2 | Available |
| DRS-4420 | S | 5 | Available |
| DRS-4420 | M | 0 | Out of Stock |
| DRS-4420 | L | 8 | Available |
| DRS-4420 | XL | 3 | Available |
| SNK-7710 | 8 | 4 | Available |
| SNK-7710 | 9 | 6 | Available |
| SNK-7710 | 10 | 2 | Available |
| SNK-7710 | 11 | 5 | Available |
| SNK-7710 | 12 | 3 | Available |
| JKT-3315 | XS | 1 | Available |
| JKT-3315 | S | 0 | Out of Stock |
| JKT-3315 | M | 4 | Available |
| JKT-3315 | L | 3 | Available |
| JKT-3315 | XL | 2 | Available |

| SKU | Product | Available Colors |
|---|---|---|
| DRS-4420 | Midi Wrap Dress — Emerald | emerald, navy, burgundy |
| SNK-7710 | Premium Leather Sneakers — White | white, black |
| JKT-3315 | Quilted Puffer Jacket — Black | black, olive |

Sizes currently out of stock: DRS-4420 size M, JKT-3315 size S.
