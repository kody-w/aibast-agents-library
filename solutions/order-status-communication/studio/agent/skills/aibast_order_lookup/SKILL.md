---
name: order-lookup
description: Use for exact order, customer, product, quantity, value, status, completion, promise date, days left, and at-risk value.
---
# Order status dashboard

Read the records with the SharePoint list tools, and the rules and controls knowledge.

## Required knowledge

Use the SharePoint list tools and the rules file together:

- the SharePoint list tools — complete exact source records.
- `aibast_order-status-communication-review-rules.md` — locked-case routing, calculation rules, and exact deterministic outputs.

Do not browse, substitute live-looking facts, or invent missing records.

## Procedure

1. Route this request to `order_lookup`.
2. Read the matching canonical output under **Exact deterministic operation outputs**.
3. Ground the answer in the complete source records and preserve exact identifiers,
   names, measurements, costs, dates, schedules, statuses, and headings needed by
   the question.
4. Separate source facts from derived synthetic analysis and recommendations.
5. State the required human approval and the external action that was not performed.
6. Label every exact value as synthetic pilot evidence, not a customer outcome.

## Locked validation case

- Persona: **Customer Service Representative**
- Prompt: “Which orders are on track or delayed, and where should customer service focus its review?”
- Required deterministic evidence: `ORD-7813`, `DELAYED`

## Authorization boundary

Never change an order, production schedule, shipment, sourcing decision, logistics action, or recovery plan. Never send email, EDI, portal, Teams, or any other customer communication. An approved communication tool and authorized sender are required.

Apply the following phrase requirements only to the matching request below; do not include evidence from unrelated cases.

## Required evidence

Include each phrase below in the answer exactly as written (same words, same order):

For: Which orders are on track or delayed, and where should customer service focus its review?

- ORD-7813
- DELAYED

Report only figures and conclusions found in the list records, the rules knowledge or this operation's canonical output, or simple arithmetic on those figures that you label as computed. Beyond what the canonical output itself states, do not say or imply that one amount covers, closes, exceeds, offsets or is sufficient for another, and do not rank or recommend options; those judgements belong to the authorized reviewer.
