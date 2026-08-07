# Utility Accounts and Usage Data

> SYNTHETIC — DEMO DATA. Every account, customer, address, balance, and meter
> read in this document is fictional. This file exists so the agent has a
> working world to answer from on day one. In production, replace this file
> with tools that read your real customer information system and metering
> platform (see the README's production section).

## Utility account ledger

| Account | Customer | Address | Type | Services | Status | Current Charges | Past Due | Total Due | Auto-Pay | Last Payment |
|---|---|---|---|---|---|---|---|---|---|---|
| ACCT-90001 | Patricia Hernandez | 1245 Cedar Lane | Residential | Water, Sewer, Stormwater | Active | $127.45 | $0.00 | $127.45 | Yes | $118.90 on 2025-02-15 |
| ACCT-90002 | Green Valley Shopping Center | 5600 Commerce Blvd | Commercial | Water, Sewer, Stormwater, Fire Line | Active | $2,845.60 | $1,420.30 | $4,265.90 | No | $2,650.00 on 2025-01-20 |
| ACCT-90003 | Robert & Linda Thompson | 887 Willow Creek Dr | Residential | Water, Sewer, Stormwater, Trash | Delinquent | $245.80 | $489.20 | $735.00 | No | $135.00 on 2024-11-18 |
| ACCT-90004 | Sunnyvale Elementary School | 300 Education Way | Institutional | Water, Sewer, Stormwater, Irrigation | Active | $1,890.25 | $0.00 | $1,890.25 | Yes | $1,756.00 on 2025-02-28 |

**Total Accounts Receivable:** $7,018.60

Total due is `current charges + past due`. Total accounts receivable is the sum
of that figure across all four accounts.

## Meter usage history

Usage history is on file for **ACCT-90001 and ACCT-90003 only**. ACCT-90002 and
ACCT-90004 have no meter history in this data set; the agent reports that as a
gap rather than estimating it. The `Amount` column is the full billed amount
for the period and includes every service on the account, not water alone.

### ACCT-90001 — Patricia Hernandez (Residential)

| Period | Water (gal) | Sewer (gal) | Amount |
|---|---|---|---|
| 2024-09 | 4,200 | 3,780 | $98.50 |
| 2024-10 | 3,800 | 3,420 | $92.10 |
| 2024-11 | 3,100 | 2,790 | $84.30 |
| 2024-12 | 2,900 | 2,610 | $81.20 |
| 2025-01 | 3,000 | 2,700 | $82.90 |
| 2025-02 | 3,200 | 2,880 | $86.45 |

- Average monthly water usage: **3,367 gallons** (20,200 / 6)
- Average monthly bill: **$87.58** ($525.45 / 6)
- Trend: **Slightly Decreasing** — 3,200 gal against a prior five-month average
  of 3,400 gal, which is below the 0.95 threshold of 3,230 gal.

### ACCT-90003 — Robert & Linda Thompson (Residential)

| Period | Water (gal) | Sewer (gal) | Amount |
|---|---|---|---|
| 2024-09 | 8,500 | 7,650 | $145.20 |
| 2024-10 | 9,200 | 8,280 | $152.80 |
| 2024-11 | 12,400 | 11,160 | $198.50 |
| 2024-12 | 14,800 | 13,320 | $232.10 |
| 2025-01 | 13,200 | 11,880 | $215.40 |
| 2025-02 | 11,500 | 10,350 | $189.80 |

- Average monthly water usage: **11,600 gallons** (69,600 / 6)
- Average monthly bill: **$188.97** ($1,133.80 / 6)
- Trend: **Stable** — 11,500 gal against a prior five-month average of 11,620
  gal, inside the 0.95 to 1.05 band (11,039 to 12,201 gal), even though the
  account peaked at 14,800 gal in 2024-12.

## Trend classification thresholds

Let `recent` be the latest period's water gallons and `prior_avg` the mean of
every earlier period.

| Condition | Classification |
|---|---|
| Fewer than 2 periods on file | Insufficient Data |
| `recent > prior_avg * 1.20` | Significantly Increasing |
| `recent > prior_avg * 1.05` | Slightly Increasing |
| `recent < prior_avg * 0.80` | Significantly Decreasing |
| `recent < prior_avg * 0.95` | Slightly Decreasing |
| otherwise | Stable |

Conditions are evaluated in this order; the first match wins.
