# Rate Structures and Assistance Programs

> SYNTHETIC — DEMO DATA. Every rate, tier, program, benefit cap, and threshold
> in this document is fictional. This file exists so the agent has a working
> world to answer from on day one. In production, replace this file with tools
> that read your adopted rate ordinance and your live assistance program
> intake system (see the README's production section).

## Water — residential

Base charge: **$18.50** per billing period.

| Tier | Rate per 1,000 gal |
|---|---|
| 0-3,000 gal | $4.25 |
| 3,001-6,000 gal | $6.50 |
| 6,001-10,000 gal | $9.75 |
| Over 10,000 gal | $14.00 |

## Water — commercial

Base charge: **$45.00** per billing period.

| Tier | Rate per 1,000 gal |
|---|---|
| 0-10,000 gal | $5.80 |
| 10,001-50,000 gal | $5.25 |
| Over 50,000 gal | $4.90 |

## Sewer, stormwater, and trash

| Service | Base charge | Volumetric rate |
|---|---|---|
| Sewer | $12.75 | $5.10 per 1,000 gal |
| Stormwater — residential | $8.50 flat | none |
| Stormwater — commercial | $8.50 per ERU | none |
| Trash — residential | $22.00 flat | none |

A water charge is the base charge plus, for each tier the volume reaches,
`(gallons in that tier / 1,000) * that tier's rate`. Any figure derived this
way covers the **water portion only** — a customer's billed amount also
includes sewer, stormwater, and any other service on the account.

## Assistance programs

| Program | Income gate | Benefit | Status | Documents required |
|---|---|---|---|---|
| Low-Income Household Water Assistance Program (LIHWAP) | At or below 150% FPL | Up to $1,500 | Accepting Applications | Proof of income; Utility bill; ID; Household size verification |
| Senior Citizen Rate Discount | Age 65+ AND at or below 200% FPL | 25% rate discount | Accepting Applications | Proof of age; Proof of income; Utility account number |
| COVID-19 Arrearage Forgiveness Program | At or below 200% FPL AND arrears accrued March 2020 - December 2023 | Up to $3,000 | Limited Funds | Utility account statement; Income verification |
| Extended Payment Arrangement | Past-due balance over $100 (no income test) | Up to 12 installments | Always Available | Signed payment agreement |

Where a program names two conditions, both must hold. Status governs whether
applications are being taken: **Limited Funds** means the money may run out, so
arrearage forgiveness is never presented as guaranteed.

## Federal Poverty Level reference (2025)

| Household Size | 100% FPL | 150% FPL | 200% FPL |
|---|---|---|---|
| 1 | $15,650 | $23,475 | $31,300 |
| 2 | $21,150 | $31,725 | $42,300 |
| 3 | $26,650 | $39,975 | $53,300 |
| 4 | $32,150 | $48,225 | $64,300 |
| 5 | $37,650 | $56,475 | $75,300 |

Thresholds are `100% FPL * 1.5` and `100% FPL * 2`. Household sizes above 5 are
not published here — the agent says so instead of extrapolating.

## Payment arrangement math

Only the **past-due balance** is financed; current charges continue to accrue
during a plan. The four offered terms are fixed:

`monthly_payment = round(past_due / months, 2)` for months in 3, 6, 9, 12

Worked example — ACCT-90003, past due $489.20:

| Installments | Monthly Payment | Total |
|---|---|---|
| 3 months | $163.07 | $489.20 |
| 6 months | $81.53 | $489.20 |
| 9 months | $54.36 | $489.20 |
| 12 months | $40.77 | $489.20 |

There is no interest, fee, or penalty in this rate structure — the total never
exceeds the past-due balance.
