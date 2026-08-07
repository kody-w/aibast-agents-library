# Tax Rates and Rebalance Policy

> SYNTHETIC — DEMO DATA. The rates and thresholds below are fictional demo
> values, not current tax law or a real firm's investment policy statement. This
> file exists so the agent has a working world to answer from on day one. In
> production, replace this file with tools that read your firm's tax engine and
> investment policy statements (see the README's production section).

## Tax rate reference

| Rate | Value |
|------|-------|
| Short Term Capital Gains | 37.0% |
| Long Term Capital Gains | 20.0% |
| Qualified Dividends | 20.0% |
| Ordinary Income | 37.0% |
| Net Investment Income Tax | 3.8% |

The rebalancing tax estimate applies **long-term capital gains + net investment
income tax = 23.8%**. The short-term and ordinary income rates are reference
only and are not applied by the estimate.

## Rebalance policy

| Portfolio | Drift Threshold | Rebalance Frequency |
|-----------|-----------------|---------------------|
| PORT-5001 Growth Allocation Fund | 3.0% | quarterly |
| PORT-5002 Conservative Income Portfolio | 2.0% | semi-annual |

- A holding trades only when `abs(current_pct - target_pct) >= drift_threshold`.
  The comparison is greater-than-or-equal.
- Trade size is `abs((total_value * target_pct / 100) - current_value)`. It
  returns the holding to target exactly, not to the edge of the threshold band.
- A holding inside its threshold is never traded, even to fund the buy side.

## Tax estimate method

For each SELL trade, on the holding being sold:

1. `gain_pct = (current_value - cost_basis) / current_value`
2. `unrealized_gain = sell_amount * gain_pct`
3. If `unrealized_gain <= 0`, estimated tax is `$0`. Losses are not netted
   across holdings.
4. Otherwise `estimated_tax = unrealized_gain * 0.238`

Assumptions baked into this method, which must be stated whenever a tax number
is given: every lot is treated as long-term; there is no lot-level selection;
wash sale rules, state and local tax, and account type (taxable versus
tax-advantaged) are ignored. The result is a planning estimate, not tax advice.

## Tax-efficient alternatives to selling

- Direct new contributions to underweight asset classes.
- Use tax-loss positions to offset gains.
- Rebalance within tax-advantaged accounts first.
- Consider charitable donation of appreciated shares.

## Execution sequence

1. Execute sells.
2. Settle cash — T+1. Sell proceeds must settle before purchasing.
3. Execute buys.
4. Verification: confirm post-trade allocations match targets, update portfolio
   records, generate client notification, document compliance review.

The agent produces this plan for a person to execute. It does not place,
route, settle, or approve trades.
