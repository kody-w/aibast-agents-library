# Return Policy and Refund Reference

> SYNTHETIC — DEMO DATA. These policies, windows, fees, and processing times
> are fictional demo values. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real policy service and payment processor SLAs (see the README's
> production section).

## Return policies

| Policy | Window | Condition | Refund Method | Restocking Fee | Categories |
|---|---|---|---|---|---|
| standard | 30 days | unworn_with_tags | original_payment | 0% | apparel, accessories |
| footwear | 30 days | unworn_original_box | original_payment | 0% | footwear |
| electronics | 15 days | unopened_or_defective | original_payment | 15% | electronics |
| final_sale | No returns (0 days) | no_returns | none | 0% | clearance, intimates |

## SKU prefix to policy map

The policy for an item is chosen by the text before the first hyphen in its
SKU. Any prefix not listed falls back to `standard`.

| Prefix | Policy | Window |
|---|---|---|
| DRS | standard | 30 days |
| SHL | standard | 30 days |
| SNK | footwear | 30 days |
| JKT | standard | 30 days |
| BT | footwear | 30 days |
| UM | standard | 30 days |
| ELEC | electronics | 15 days |

## Eligibility arithmetic

Days elapsed are measured from the delivery date to a fixed reference date of
2025-03-10, using fixed-length months and years:

`day = year * 365 + month * 30 + day_of_month`
`days_since = reference_day - delivered_day`

An item is eligible when `days_since` is less than or equal to the policy
window. A 0-day window (final sale) is never eligible.

| Order | Delivered | Days Since | Item Policies | Eligible |
|---|---|---|---|---|
| ORD-55001 | 2025-02-20 | 20 | standard (30), standard (30) | 2 of 2 |
| ORD-55002 | 2025-02-02 | 38 | footwear (30) | 0 of 1 — window expired |
| ORD-55003 | 2025-03-01 | 9 | standard (30), footwear (30), standard (30) | 3 of 3 |
| ORD-55004 | 2024-12-15 | 90 | electronics (15) | 0 of 1 — window expired |

## Refund calculation

`fee = item_price * restocking_fee_pct / 100`
`refund = round(item_price - fee, 2)`

Shipping paid on the original order is not included in the refund amount.

## Refund processing times

| Payment Method | Processing Time | Description |
|---|---|---|
| credit_card | 5 days | Refund to original credit card |
| paypal | 3 days | Refund to PayPal account |
| store_credit | 1 day | Instant store credit issued |
| gift_card | 1 day | Refund to gift card balance |

## Return process

1. Customer initiates return request (online or in-store)
2. System checks eligibility against return policy
3. RMA number generated and prepaid label sent
4. Customer ships item back within 7 days
5. Warehouse receives and inspects item
6. Refund or exchange processed
