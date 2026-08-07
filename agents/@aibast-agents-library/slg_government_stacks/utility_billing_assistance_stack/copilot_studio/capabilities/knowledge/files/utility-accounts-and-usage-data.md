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

## Meter interval diagnostics

Interval telemetry is on file for **ACCT-90001 and ACCT-90003 only** — the same
two accounts that have meter history. ACCT-90002 and ACCT-90004 have no interval
data, so they are reported as **Not Assessed**, never as leak-free.

`Min Nightly Flow` is the lowest hourly flow observed during the overnight
window. `Continuous-Flow Nights` is the number of nights in the 30-night window
on which that flow never dropped to zero — water moving when nobody is drawing
it.

| Account | Customer | Min Nightly Flow (gal/hr) | Continuous-Flow Nights | Last Meter Read |
|---|---|---|---|---|
| ACCT-90001 | Patricia Hernandez | 0.0 | 0 of 30 | 2025-02-28 |
| ACCT-90002 | Green Valley Shopping Center | No interval data | No interval data | — |
| ACCT-90003 | Robert & Linda Thompson | 5.0 | 30 of 30 | 2025-02-28 |
| ACCT-90004 | Sunnyvale Elementary School | No interval data | No interval data | — |

## Leak flag rule

An account is flagged as a **Suspected Leak** when either published condition
holds. Conditions are independent; either one alone flags the account.

| Condition | Meaning |
|---|---|
| `min_nightly_flow_gph > 0.5` **and** `continuous_flow_nights >= 30` | Continuous flow across the whole 30-night window |
| Trend is `Significantly Increasing` | Consumption above 1.20x the prior-period average |

If neither condition holds and interval data is on file, the assessment is **No
Leak Indicator**. If no interval data is on file, the assessment is **Not
Assessed — no interval data on file**.

Estimated loss at the continuous-flow rate is
`min_nightly_flow_gph * 24 * window_nights`, reported in gallons only.

- **ACCT-90003 — Suspected Leak.** 5.0 gal/hr on 30 of 30 nights, above the 0.5
  gal/hr threshold. Estimated loss `5.0 * 24 * 30 = 3,600 gallons` over the
  window, roughly 31% of the 11,500 gallons billed in 2025-02. The consumption
  trend is Stable, so the meter evidence — not the trend — carries this flag.
- **ACCT-90001 — No Leak Indicator.** 0.0 gal/hr, 0 continuous-flow nights, and
  a Slightly Decreasing trend. Neither condition is met.

A flag is a **suspected** leak pending field verification by the utility. It is
never a confirmed leak, a repair order, or a billing adjustment, and the dollar
impact crosses rate tiers and is quantified by a billing clerk.

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
