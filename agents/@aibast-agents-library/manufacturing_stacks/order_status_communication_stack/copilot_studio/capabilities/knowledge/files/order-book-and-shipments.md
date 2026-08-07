# Order Book and Shipments

> SYNTHETIC — DEMO DATA. Every order, customer, contact, and tracking number in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real ERP order book and carrier tracking feeds (see the README's
> production section).

## Order book

| Order | Customer | Contact | Contact Email | Product | Qty | Unit Price | Order Value | Order Date | Promised Date | Status | Complete |
|-------|----------|---------|---------------|---------|-----|------------|-------------|------------|---------------|--------|----------|
| ORD-7810 | Ford Motor Company | James Mitchell | j.mitchell@ford.example.com | 6R140 Transmission Housing | 2,500 | $168.00 | $420,000.00 | 2026-02-01 | 2026-03-20 | in_production | 74% |
| ORD-7811 | Caterpillar Inc. | Rita Vasquez | r.vasquez@cat.example.com | D11 Track Frame Weldment | 40 | $12,450.00 | $498,000.00 | 2026-01-15 | 2026-04-10 | in_production | 45% |
| ORD-7812 | Tesla Inc. | Derek Chung | d.chung@tesla.example.com | Model Y Rocker Panel Stamping | 8,000 | $42.50 | $340,000.00 | 2026-02-10 | 2026-03-15 | shipped | 100% |
| ORD-7813 | John Deere | Angela Torres | a.torres@deere.example.com | Hydraulic Cylinder Barrel | 600 | $385.00 | $231,000.00 | 2026-02-18 | 2026-03-28 | delayed | 30% |

Order value is `quantity x unit_price`, rounded to two decimals. Total order
book value is $1,489,000.00. At-risk value (orders that are `delayed` or carry
a delay record) is $231,000.00 -- ORD-7813 only.

## Days remaining against the promised date

Days remaining is computed against a fixed reference date of **2026-03-17**
using `(year - 2026) * 365 + (month - 3) * 30 + (day - 17)`. A negative value
means the promised date has already passed.

| Order | Promised Date | Days Left |
|-------|---------------|-----------|
| ORD-7810 | 2026-03-20 | 3 |
| ORD-7811 | 2026-04-10 | 23 |
| ORD-7812 | 2026-03-15 | -2 |
| ORD-7813 | 2026-03-28 | 11 |

## Shipments

Only orders listed here have shipment data. An order marked `shipped` in the
order book without a row in this table has no carrier or tracking number on
file.

| Order | Carrier | Tracking | Ship Date | Est Delivery | Origin | Destination | Weight | Status |
|-------|---------|----------|-----------|--------------|--------|-------------|--------|--------|
| ORD-7812 | XPO Logistics | XPO-884291047 | 2026-03-12 | 2026-03-15 | Detroit, MI | Fremont, CA | 4,200 kg | in_transit |

### Shipped order detail

- **ORD-7812** (Tesla Inc.): Model Y Rocker Panel Stamping -- 8,000 units,
  $340,000.00

## Order statuses in use

| Status | Meaning |
|--------|---------|
| in_production | On the floor, progressing against the promised date |
| shipped | Released to a carrier; tracking detail lives in the shipment table |
| delayed | Will miss the promised date; a delay record carries the revised date |
