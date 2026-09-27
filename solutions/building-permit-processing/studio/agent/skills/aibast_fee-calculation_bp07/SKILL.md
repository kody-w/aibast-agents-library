---
name: synthetic-permit-fee-estimate
description: Use for permit cost, fee breakdown, or formula questions to calculate all seven synthetic fee categories from declared valuation and label the result as an estimate.
---
<!-- bic:source=blank -->
# Synthetic permit fee estimate

Read listed entity facts with the SharePoint list tools, using the global instructions' Evidence locations and List columns. Read all unlisted record facts, calculations, policies, thresholds and response contracts from the retained knowledge files. Never claim an omitted email field or an unlisted record set is available from a list.

Use this skill for permit cost, fee estimate, breakdown, or formula
questions.

## Fixed formula

For every category:
`amount = base + (valuation / 1000) × rate`, rounded to cents.

Use all seven categories in schedule order: Plan Review, Building Permit,
Electrical, Plumbing, Mechanical, Fire Review, Technology Surcharge.
Their bases total $850 and rates total $19.25 per $1,000.

## Precomputed totals

- BP-2025-0101: $81,700.00
- BP-2025-0102: $4,411.25
- BP-2025-0103: $7,010.00
- BP-2025-0104: $131,750.00
- BP-2025-0105: $81,700.00
- BP-2025-0106: $11,245.00

## Output

Lead with the estimated total, then show the seven line items when the user
asks for a breakdown or how the total was calculated. For a hypothetical
valuation, apply the same formula and label it hypothetical. For an unknown
permit ID, ask for the valuation or list the known IDs; never silently
calculate all permits.

Always label the result a synthetic estimate from declared valuation, not
an invoice, charge, balance, or payment record. Never waive or alter a fee.

Apply the following phrase requirements only to the matching request below; do not include evidence from unrelated cases.

## Required evidence

Include each phrase below in the answer exactly as written (same words, same order):

For: Every fee estimate

- synthetic estimate

Report only figures and conclusions found in the list records, the rules knowledge or this operation's canonical output, or simple arithmetic on those figures that you label as computed. Beyond what the canonical output itself states, do not say or imply that one amount covers, closes, exceeds, offsets or is sufficient for another, and do not rank or recommend options; those judgements belong to the authorized reviewer.
