# Resolution Playbooks & Return Policy

> SYNTHETIC — DEMO DATA. These playbooks, windows, and steps are fictional.
> This file exists so the agent has a working world to answer from on day one.
> In production, replace this file with tools that read your real returns
> policy and resolution playbook system (see the README's production section).

## Playbook summary

| Playbook | ID | Window | Cost Impact | CSAT Impact |
|----------|----|--------|-------------|-------------|
| Full Refund | full_refund | 90 days | high | high |
| Product Exchange | exchange | 60 days | medium | very_high |
| Store Credit | store_credit | 45 days | low | moderate |
| Warranty Replacement | warranty_replacement | 365 days | medium | high |
| Partial Refund | partial_refund | 30 days | medium | moderate |

## Eligibility gates

A playbook applies to a return only when all three gates pass. None is waived.

| Playbook | Applicable Reasons | Applicable Conditions | Max Days Since Purchase |
|----------|--------------------|-----------------------|-------------------------|
| full_refund | defective, wrong_item, not_as_described | non_functional, unopened, damaged | 90 |
| exchange | wrong_size, wrong_item, not_as_described | unworn_tags_attached, unopened, opened_unused | 60 |
| store_credit | changed_mind, wrong_size | opened_unused, lightly_used, unworn_tags_attached | 45 |
| warranty_replacement | defective | non_functional, damaged | 365 |
| partial_refund | not_as_described, changed_mind | lightly_used | 30 |

## Selection rule

Evaluate playbooks in the table order above. Hold the first candidate that
passes all three gates. Any later candidate whose CSAT impact is `very_high` or
`high` replaces the one being held. If no playbook passes, fall back to
`store_credit` and label it a fallback, not a match.

Worked outcomes against the current queue:

| Return ID | Reason | Condition | Days | Candidates | Selected |
|-----------|--------|-----------|------|------------|----------|
| RET-4001 | wrong_size | unworn_tags_attached | 18 | exchange, store_credit | Product Exchange |
| RET-4002 | defective | non_functional | 50 | full_refund, warranty_replacement | Warranty Replacement |
| RET-4003 | not_as_described | lightly_used | 10 | partial_refund | Partial Refund |
| RET-4004 | changed_mind | opened_unused | 11 | store_credit | Store Credit |
| RET-4005 | defective | damaged | 91 | warranty_replacement (full_refund fails the 90-day window) | Warranty Replacement — already escalated |
| RET-4006 | wrong_item | unopened | 10 | full_refund, exchange | Product Exchange |

## Playbook steps

### Full Refund (`full_refund`)

1. Verify purchase and return eligibility
2. Approve full refund to original payment method
3. Generate prepaid return shipping label
4. Send confirmation email with refund timeline
5. Process refund within 3-5 business days

### Product Exchange (`exchange`)

1. Confirm desired replacement item and availability
2. Generate prepaid return label for original item
3. Ship replacement item with expedited shipping
4. Send tracking information for both shipments
5. Follow up after delivery to confirm satisfaction

### Store Credit (`store_credit`)

1. Verify item condition meets return standards
2. Issue store credit for full purchase amount plus 10% bonus
3. Credit applied to customer loyalty account
4. Send email with credit balance and expiration date

### Warranty Replacement (`warranty_replacement`)

1. Verify product is within warranty period
2. Collect defect documentation and photos
3. Submit warranty claim to manufacturer
4. Ship replacement from warranty stock
5. Allow customer to keep defective unit or provide return label

### Partial Refund (`partial_refund`)

1. Assess item condition and determine refund percentage
2. Apply restocking fee if applicable (15% for opened items)
3. Process partial refund to original payment method
4. Notify customer of refund amount and timeline

## Policy notes

- Store Credit pays the full purchase amount plus a 10% bonus; Partial Refund
  applies a 15% restocking fee to opened items. These are the only monetary
  adjustments defined here.
- Status values in the queue are `pending_review`, `approved`, and `escalated`.
  A return outside every playbook window is a supervisor exception, not an
  agent decision.
- Every step above is executed by a person or a downstream system. The agent
  recommends the playbook and lists the steps; it never performs them.
