---
name: supplier-scorecard
description: Use for exact supplier identity, category, geography, spend, tier, risk, health, dimension scores, statuses, and incidents.
---
# Supplier scorecards

Read the records with the SharePoint list tools, and the rules and controls knowledge.

## Required knowledge

Use the SharePoint list tools and the rules file together:

- the SharePoint list tools — complete exact source records.
- `aibast_supplier-risk-monitoring-review-rules.md` — locked-case routing, calculation rules, and exact deterministic outputs.

Do not browse, substitute live-looking facts, or invent missing records.

## Procedure

1. Route this request to `supplier_scorecard`.
2. Read the matching canonical output under **Exact deterministic operation outputs**.
3. Ground the answer in the complete source records and preserve exact identifiers,
   names, measurements, costs, dates, schedules, statuses, and headings needed by
   the question.
4. Separate source facts from derived synthetic analysis and recommendations.
5. State the required human approval and the external action that was not performed.
6. Label every exact value as synthetic pilot evidence, not a customer outcome.

## Locked validation case

- Persona: **Procurement Manager**
- Prompt: “Explain why TechnoCore is elevated and show me the evidence by risk dimension.”
- Required deterministic evidence: `SUP-101`, `Geopolitical`

## Authorization boundary

Never contact a supplier, change an allocation, qualify or disqualify a supplier, select or award a supplier, execute a contract, place an order, or approve sourcing. Authorized procurement owners must use approved procurement and supplier-management tools for any action.

Apply the following phrase requirements only to the matching request below; do not include evidence from unrelated cases.

## Required evidence

Include each phrase below in the answer exactly as written (same words, same order):

For: Explain why TechnoCore is elevated and show me the evidence by risk dimension.

- SUP-101
- Geopolitical

Report only figures and conclusions found in the list records, the rules knowledge or this operation's canonical output, or simple arithmetic on those figures that you label as computed. Beyond what the canonical output itself states, do not say or imply that one amount covers, closes, exceeds, offsets or is sufficient for another, and do not rank or recommend options; those judgements belong to the authorized reviewer.
