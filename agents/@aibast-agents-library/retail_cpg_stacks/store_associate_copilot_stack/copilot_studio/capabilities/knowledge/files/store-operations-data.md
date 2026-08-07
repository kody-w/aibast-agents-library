# Store Operations Data

> SYNTHETIC — DEMO DATA. Every script, task, and associate figure in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real training content, task management system, and POS/workforce
> reporting (see the README's production section).

## Customer interaction scripts

Five scenarios, and only these five. The scenario id is what the agent matches
on; the script is quoted verbatim to the associate.

| Scenario ID | Applies when | Suggested script |
|-------------|--------------|------------------|
| greeting | Customer enters the store | Welcome to our store! Is there anything specific I can help you find today? |
| upsell | Customer is ready to purchase a single item | Great choice! Did you know that pairs perfectly with our {complementary_product}? Many customers love the combination. |
| complaint_handling | Customer has a complaint or issue | I am sorry to hear about that. Let me make sure I understand the issue so I can help resolve it right away. |
| size_help | Customer needs sizing assistance | I would be happy to help you find the right fit. What size do you typically wear in this type of item? |
| return_at_counter | Customer wants to make a return at the register | Of course, I can help with that. Do you have your receipt or order confirmation? |

The `{complementary_product}` placeholder in the upsell script is filled from
the complementary pairings in the product catalog document, never invented.

### Follow-up moves and coaching tips

| Scenario ID | Follow-up | Tips |
|-------------|-----------|------|
| greeting | If they mention a product category, guide them to the correct aisle. | Make eye contact; Smile genuinely; Keep a comfortable distance |
| upsell | If interested, walk them to the complementary item. If not, respect their decision. | Suggest only relevant items; Limit to one upsell attempt; Focus on value not price |
| complaint_handling | Listen fully, repeat back the issue, offer a concrete solution within your authority. | Never argue; Acknowledge their frustration; Offer alternatives if first solution is declined |
| size_help | Check fitting room availability. Bring two sizes if customer is between sizes. | Be sensitive about sizing; Suggest trying multiple sizes; Check stock for requested size first |
| return_at_counter | Verify return eligibility per policy. Process efficiently and offer exchange if applicable. | Stay positive and empathetic; Explain policy clearly; Thank them regardless of outcome |

## Daily task checklists

Three shifts: opening, midday, closing. Tasks are listed in the running order
of the shift, not in priority order. Priority levels in use are CRITICAL, HIGH,
and MEDIUM.

### Opening shift — 6 tasks, 57 min, 83.3% completion

| # | Task | Priority | Est. Time |
|---|------|----------|-----------|
| 1 | Unlock entrance doors and disable alarm | CRITICAL | 2 min |
| 2 | Power on POS terminals and verify connectivity | CRITICAL | 5 min |
| 3 | Walk floor to check overnight display condition | HIGH | 10 min |
| 4 | Restock fitting rooms with hangers | MEDIUM | 5 min |
| 5 | Review daily promotions and update signage | HIGH | 15 min |
| 6 | Check inventory alerts and pull items for floor replenishment | HIGH | 20 min |

### Midday shift — 5 tasks, 60 min, 80.0% completion

| # | Task | Priority | Est. Time |
|---|------|----------|-----------|
| 1 | Restock high-traffic areas and end caps | HIGH | 20 min |
| 2 | Process online pickup orders (BOPIS) | CRITICAL | 15 min |
| 3 | Clean fitting rooms and return abandoned items | MEDIUM | 10 min |
| 4 | Rotate break schedule for floor coverage | HIGH | 5 min |
| 5 | Check and respond to customer service queue | HIGH | 10 min |

### Closing shift — 5 tasks, 78 min, 80.0% completion

| # | Task | Priority | Est. Time |
|---|------|----------|-----------|
| 1 | Process remaining BOPIS orders for next-day pickup | CRITICAL | 15 min |
| 2 | Reconcile POS drawers and prepare deposit | CRITICAL | 20 min |
| 3 | Tidy all displays and return misplaced merchandise | HIGH | 25 min |
| 4 | Vacuum high-traffic aisles | MEDIUM | 15 min |
| 5 | Set alarm and lock all entrances | CRITICAL | 3 min |

**How completion is derived:** it is the share of a shift's tasks that are
CRITICAL or HIGH, rounded to one decimal — opening 5/6 = 83.3%, midday 4/5 =
80.0%, closing 4/5 = 80.0%. It is a projection that assumes the CRITICAL and
HIGH work is done and the MEDIUM work is not. It is not a live task feed.

## Associate performance — today

| ID | Name | Role | Shift | Units | Revenue | Txns | Avg Basket | Upsell | CSAT | Tasks | Hours This Week |
|----|------|------|-------|-------|---------|------|------------|--------|------|-------|-----------------|
| ASC-101 | Taylor Brooks | Senior Associate | opening | 23 | $1,847.50 | 14 | $131.96 | 35% | 4.8/5.0 | 11/12 (92%) | 32.5 |
| ASC-102 | Jordan Kim | Associate | midday | 17 | $1,295.80 | 11 | $117.80 | 22% | 4.5/5.0 | 8/10 (80%) | 28.0 |
| ASC-103 | Morgan Lee | Associate | closing | 12 | $985.40 | 9 | $109.49 | 18% | 4.3/5.0 | 7/9 (78%) | 24.0 |
| ASC-104 | Casey Rivera | Lead Associate | opening | 29 | $2,410.30 | 18 | $133.91 | 40% | 4.9/5.0 | 12/12 (100%) | 36.0 |

### Store totals — today

| Metric | Value | How it is computed |
|--------|-------|--------------------|
| Total revenue | $6,539.00 | 1847.50 + 1295.80 + 985.40 + 2410.30 |
| Total transactions | 52 | 14 + 11 + 9 + 18 |
| Average basket | $125.75 | 6539.00 / 52 |

### Top performer highlights — today

| Highlight | Associate | Figure |
|-----------|-----------|--------|
| Highest Revenue | Casey Rivera (ASC-104) | $2,410.30 |
| Best CSAT | Casey Rivera (ASC-104) | 4.9/5.0 |
| Top Upsell Rate | Casey Rivera (ASC-104) | 40% |

These are three independent maxima over the same four associates. There is no
combined score and no overall ranking. `Hours This Week` is roster context, not
a dashboard column — it is never blended into a rate.

## Receipt archive — transaction support

The business date is fixed at **2026-07-24**. Every day count below is measured
against that date, never against the clock.

The archive holds exactly eight orders, ORD-5001 through ORD-5008. It is a
lookup sample for register-side questions — it is **not** the store transaction
log, and it does not reconcile with the 52 transactions on today's performance
dashboard. Never total it into a sales figure or compare it with the dashboard.

### Return window policy

| Category | Return window |
|----------|---------------|
| Electronics | 15 days |
| Apparel | 30 days |
| Footwear | 30 days |
| Accessories | 30 days |
| Fitness | 30 days |
| Home | 30 days |

The window opens on the purchase date for an in-store order and on the pickup
date for an online pickup (BOPIS) order. An order still awaiting pickup has no
window yet.

### Orders on file

| Order | Date | SKU | Item | Qty | Price Paid | Order Total | Tender | Channel | Rung By | Status |
|-------|------|-----|------|-----|------------|-------------|--------|---------|---------|--------|
| ORD-5001 | 2026-07-22 | SKU-1005 | Premium Running Shoes | 1 | $149.99 | $149.99 | Credit Card | In-store | ASC-101 | Completed |
| ORD-5002 | 2026-07-05 | SKU-1002 | Wireless Earbuds Pro | 1 | $59.99 | $59.99 | Debit Card | Online pickup (BOPIS) | ASC-102 | Completed |
| ORD-5003 | 2026-06-28 | SKU-1001 | Classic Denim Jacket | 1 | $89.99 | $89.99 | Cash | In-store | ASC-103 | Completed |
| ORD-5004 | 2026-07-19 | SKU-1003 | Organic Cotton T-Shirt | 2 | $23.99 | $47.98 | Credit Card | In-store | ASC-101 | Completed |
| ORD-5005 | 2026-07-23 | SKU-1004 | Smart Fitness Tracker | 1 | $129.99 | $129.99 | Gift Card | Online pickup (BOPIS) | ASC-104 | Awaiting pickup |
| ORD-5006 | 2026-07-10 | SKU-1007 | Leather Crossbody Bag | 1 | $79.99 | $79.99 | Store Credit | In-store | ASC-102 | Completed |
| ORD-5007 | 2026-06-15 | SKU-1009 | Performance Yoga Mat | 1 | $54.99 | $54.99 | Credit Card | In-store | ASC-103 | Completed |
| ORD-5008 | 2026-07-23 | SKU-1010 | Aromatherapy Candle Set | 1 | $34.99 | $34.99 | Mobile Wallet | Online pickup (BOPIS) | ASC-104 | Completed |

Price paid equals the catalog retail price on every order except ORD-5004,
which carries the **Summer Basics promotion, $6.00 off each** ($29.99 → $23.99).
Order total is quantity × price paid.

### Return eligibility as of 2026-07-24

| Order | Category | Window | Window Opens | Window Closes | Eligibility |
|-------|----------|--------|--------------|---------------|-------------|
| ORD-5001 | Footwear | 30 days | 2026-07-22 | 2026-08-21 | Eligible — 28 days left |
| ORD-5002 | Electronics | 15 days | 2026-07-05 | 2026-07-20 | Expired — closed 4 days ago |
| ORD-5003 | Apparel | 30 days | 2026-06-28 | 2026-07-28 | Eligible — 4 days left |
| ORD-5004 | Apparel | 30 days | 2026-07-19 | 2026-08-18 | Eligible — 25 days left |
| ORD-5005 | Electronics | 15 days | not started | not started | Not started — awaiting pickup |
| ORD-5006 | Accessories | 30 days | 2026-07-10 | 2026-08-09 | Eligible — 16 days left |
| ORD-5007 | Fitness | 30 days | 2026-06-15 | 2026-07-15 | Expired — closed 9 days ago |
| ORD-5008 | Home | 30 days | 2026-07-23 | 2026-08-22 | Eligible — 29 days left |

Eligibility is a policy read against the archived record. Refunds go back to the
original tender and are rung by an associate at the register — the agent never
processes a return, issues a refund or store credit, adjusts a price, or
approves an exception to the window.
