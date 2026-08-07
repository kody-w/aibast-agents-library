# Client Portfolio Book

> SYNTHETIC — DEMO DATA. Every client, advisor, holding, and balance in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that
> read your real CRM and portfolio accounting system (see the README's
> production section).

## Book of business

| ID | Client | Advisor | Risk Profile | Age | Retirement Target | Years to Retirement | Total Assets | Annual Income | Annual Contributions | Last Review |
|----|--------|---------|--------------|-----|-------------------|---------------------|--------------|---------------|----------------------|-------------|
| CLI-3001 | Robert & Susan Whitfield | James Morrison, CFP | moderate | 58 | 67 | 9 yrs | $1,850,000 | $285,000 | $45,000 | 2024-12-15 |
| CLI-3002 | Angela Martinez | James Morrison, CFP | aggressive | 34 | 60 | 26 yrs | $420,000 | $145,000 | $24,000 | 2025-01-20 |
| CLI-3003 | William Chen Trust | Patricia Lane, CFA | conservative | 72 | — | Retired | $4,200,000 | $0 | $0 | 2025-02-10 |

**Total AUM:** $6,470,000 — **Clients:** 3

A retirement target of 0 means the client is already retired; render the cell
as `Retired`, never as `0 yrs`.

## CLI-3001 — Robert & Susan Whitfield (moderate)

Max allocation drift: **5.0%** (at the compliance threshold, not over it).

| Asset Class | Value | Current % | Target % | Drift |
|---|---|---|---|---|
| US Equities | $555,000 | 30.0% | 35.0% | -5.0% |
| International Equities | $185,000 | 10.0% | 15.0% | -5.0% |
| Fixed Income | $647,500 | 35.0% | 30.0% | +5.0% |
| Real Estate (REITs) | $185,000 | 10.0% | 10.0% | 0.0% |
| Alternatives | $92,500 | 5.0% | 5.0% | 0.0% |
| Cash & Equivalents | $185,000 | 10.0% | 5.0% | +5.0% |

## CLI-3002 — Angela Martinez (aggressive)

Max allocation drift: **5.0%**.

| Asset Class | Value | Current % | Target % | Drift |
|---|---|---|---|---|
| US Equities | $210,000 | 50.0% | 45.0% | +5.0% |
| International Equities | $84,000 | 20.0% | 20.0% | 0.0% |
| Fixed Income | $42,000 | 10.0% | 10.0% | 0.0% |
| Emerging Markets | $50,400 | 12.0% | 15.0% | -3.0% |
| Alternatives | $21,000 | 5.0% | 5.0% | 0.0% |
| Cash & Equivalents | $12,600 | 3.0% | 5.0% | -2.0% |

## CLI-3003 — William Chen Trust (conservative)

Max allocation drift: **0%** - the portfolio is at target. (The drift
helper starts at integer 0, so a fully on-target portfolio renders as `0%`,
not `0.0%`.)

| Asset Class | Value | Current % | Target % | Drift |
|---|---|---|---|---|
| US Equities | $630,000 | 15.0% | 15.0% | 0.0% |
| International Equities | $210,000 | 5.0% | 5.0% | 0.0% |
| Fixed Income | $1,890,000 | 45.0% | 45.0% | 0.0% |
| Municipal Bonds | $840,000 | 20.0% | 20.0% | 0.0% |
| Real Estate (REITs) | $210,000 | 5.0% | 5.0% | 0.0% |
| Cash & Equivalents | $420,000 | 10.0% | 10.0% | 0.0% |

Asset classes are not uniform across the book: only CLI-3002 holds Emerging
Markets and only CLI-3003 holds Municipal Bonds. Never carry an asset class
from one client's table into another's.

## Client IDs on file

`CLI-3001`, `CLI-3002`, `CLI-3003`. Any other id is not in the book — say so
and list these three rather than substituting a different client.
