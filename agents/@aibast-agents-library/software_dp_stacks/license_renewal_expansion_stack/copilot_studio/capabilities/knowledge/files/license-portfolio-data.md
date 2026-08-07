# License Portfolio Data

> SYNTHETIC — DEMO DATA. Every customer, contract, score, and signal in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that read
> your real CRM, subscription billing, and customer success platforms.

## License agreements

| ID | Customer | Plan | ARR | Seats | Seats Used | Seat Utilization | Renewal Date | Contract Start | Usage Trend | NPS | Tickets (90d) | Health Score | CSM |
|----|----------|------|-----|-------|------------|------------------|--------------|----------------|-------------|-----|---------------|--------------|-----|
| LIC-3001 | Pinnacle Insurance Corp | Enterprise | $288,000 | 150 | 142 | 94.7% | 2026-04-30 | 2025-04-30 | increasing | 72 | 4 | 88 | Dana Reeves |
| LIC-3002 | ClearView Analytics | Professional | $72,000 | 30 | 18 | 60.0% | 2026-05-15 | 2025-05-15 | declining | 34 | 18 | 29 | James Okafor |
| LIC-3003 | Redwood Supply Chain | Enterprise | $192,000 | 80 | 79 | 98.8% | 2026-06-01 | 2025-06-01 | stable | 65 | 7 | 62 | Dana Reeves |
| LIC-3004 | Skyline Hospitality Group | Enterprise | $360,000 | 250 | 248 | 99.2% | 2026-04-15 | 2025-04-15 | increasing | 85 | 2 | 94 | James Okafor |
| LIC-3005 | Granite Construction Co | Professional | $54,000 | 20 | 12 | 60.0% | 2026-07-01 | 2025-07-01 | declining | 41 | 11 | 35 | Dana Reeves |

Portfolio ARR: $966,000 across 5 agreements - 3 Enterprise ($840,000) and
2 Professional ($126,000). Every contract is a 12-month term starting on the
same day of the prior year as its renewal date. Seat utilization is derived
(`seats_used / seats`), not stored.

## Expansion signals

| ID | Customer | Signals |
|----|----------|---------|
| LIC-3001 | Pinnacle Insurance Corp | API usage +45% QoQ; Requested SSO for 3 subsidiaries |
| LIC-3003 | Redwood Supply Chain | Inquired about analytics add-on |
| LIC-3004 | Skyline Hospitality Group | Opening 12 new locations; Requested bulk seat pricing; Custom integration POC |

LIC-3002 ClearView Analytics and LIC-3005 Granite Construction Co carry no
expansion signals and are excluded from the expansion ranking entirely.

## Churn signals

| ID | Customer | Signals |
|----|----------|---------|
| LIC-3002 | ClearView Analytics | Usage down 32%; Executive sponsor departed; Competitor eval detected |
| LIC-3003 | Redwood Supply Chain | Budget freeze mentioned in QBR |
| LIC-3005 | Granite Construction Co | Primary admin inactive 45 days; Missed last 2 QBRs |

LIC-3001 Pinnacle Insurance Corp and LIC-3004 Skyline Hospitality Group carry no
churn signals and are excluded from the churn assessment entirely.
LIC-3003 Redwood Supply Chain carries both an expansion signal and a churn
signal, and legitimately appears on both lists.

## CSM ownership

| CSM | Accounts | ARR Owned |
|-----|----------|-----------|
| Dana Reeves | LIC-3001, LIC-3003, LIC-3005 | $534,000 |
| James Okafor | LIC-3002, LIC-3004 | $432,000 |

## What this data does not contain

There is no invoice or payment history, no stored renewal probability, no
per-account discount history, no named competitor beyond the phrase "Competitor
eval detected" on LIC-3002, no contact-level records, and no data for any
customer outside LIC-3001 through LIC-3005.
