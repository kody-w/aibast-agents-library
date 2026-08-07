# Recovery Campaigns and Incentive Policy

> SYNTHETIC — DEMO DATA. Every campaign, subject line, incentive, and rate in
> this document is fictional. This file exists so the agent has a working world
> to answer from on day one. In production, replace this file with tools that
> read your real marketing automation platform, offer catalog, and margin
> policy (see the README's production section).

## Recovery campaign sequence

Delay is measured in hours from the moment of abandonment.

| Campaign | Delay | Subject | Incentive | Avg Open Rate | Avg Conversion |
|----------|-------|---------|-----------|---------------|----------------|
| Reminder Email | 1h | You left something behind! | None | 45.2% | 8.5% |
| Urgency Email | 24h | Your cart is waiting — items selling fast | None | 38.1% | 5.2% |
| Incentive Email | 72h | Here's 10% off to complete your order | 10% discount | 42.8% | 12.1% |
| SMS Reminder | 2h | Complete your order at [Store] | None | 98.0% | 4.8% |
| Retargeting Display Ad | 6h | Dynamic product ad on social/display | None | 0% | 2.1% |

The Retargeting Display Ad's 0% open rate is a structural zero — display ads
have no open event. It is not a missing value.

## Incentive catalog

| Incentive | Description | Margin Impact | Conversion Lift |
|-----------|-------------|---------------|-----------------|
| percent_off_10 | 10% off cart total | 10.0% | +35.0% |
| percent_off_15 | 15% off cart total | 15.0% | +48.0% |
| free_shipping | Free standard shipping | 5.5% | +28.0% |
| dollar_off_20 | $20 off orders over $150 | 8.0% | +22.0% |
| gift_with_purchase | Free accessory with order | 6.0% | +18.0% |

## Incentive selection policy

Evaluate in this order and stop at the first match:

1. Segment is `high_value` AND cart value is greater than $500 -> percent_off_10
2. Segment is `loyal_shopper` -> free_shipping
3. Segment is `new_visitor` -> percent_off_15
4. Otherwise -> dollar_off_20

A cart whose recovery status is `unrecoverable` gets no incentive — there is no
contact channel to attach an offer to.

Net recovery value = cart value x (1 - margin impact / 100).

## Recovery eligibility policy

A cart is pending recovery only if both hold:

- Recovery status is not `unrecoverable`, and
- An email address is on file.

Under the current records that yields 3 pending carts (CART-20001, CART-20002,
CART-20003) and 1 unrecoverable cart (CART-20004).

## Estimated campaign recovery

Estimated recovered revenue per campaign, against the full 30-day abandoned
population:

est_recovered = total abandoned carts (30d) x avg conversion / 100 x average
recovered order value

| Campaign | Conversion | Est. Recovered |
|----------|------------|----------------|
| Reminder Email | 8.5% | $67,734 |
| Urgency Email | 5.2% | $41,438 |
| Incentive Email | 12.1% | $96,422 |
| SMS Reminder | 4.8% | $38,250 |
| Retargeting Display Ad | 2.1% | $16,734 |

These estimates overlap — each assumes the campaign runs against the whole
abandoned population. They must not be summed, and they are not reconciled
against the $102,000 actual recovered revenue.
