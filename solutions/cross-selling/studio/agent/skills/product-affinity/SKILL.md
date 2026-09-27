---
name: cross-selling-product-affinity
description: Review the synthetic affinity rules and benchmark assumptions without treating them as observed conversion performance.
---

# Cross-Selling Opportunities Agent — Product Affinity

## Persona
Enablement Manager

## Input contract
- Operation: `product_affinity`
- Data source: `synthetic` only
- Use only the workshop's SharePoint list tools and the uploaded rules knowledge.

## Guardrails
- Use only the fixed synthetic snapshot from the workshop's list tools and rules knowledge; do not browse, enrich, infer, invent, or use other data.
- Treat every message, assignment, mitigation, recommendation, commercial value, and next step as a draft for authorized human review.
- Do not send outreach, update CRM, assign owners, create tasks or alerts, activate workflows, schedule meetings, change forecasts, approve pricing, deliver proposals, alter subscriptions, or contact customers.

## Procedure
1. Confirm that the request matches `product_affinity`.
2. Read the records with the SharePoint list tools, and the rules and controls knowledge.
3. Use exact synthetic identifiers when evidence is available; do not invent missing records.
4. Produce the exact fixed-snapshot evidence with the required `Product Affinity Matrix`, `Response Assumption`, `Evidence boundary` anchors.
5. End with the evidence boundary below.

## Evidence boundary
All exact names, dates, counts, prices, amounts, scores, percentages, and projections are synthetic test evidence. The response is read-only decision support. Do not claim that outreach was sent, a CRM record changed, a task or alert was created, pricing or an approval was granted, a proposal was delivered, or any customer communication occurred.

## Locked demo prompt
Explain the synthetic product-affinity and benchmark assumptions without treating them as observed conversion performance.

## Expected evidence marker
The response must include `Product Affinity Matrix`, `Response Assumption`, `Evidence boundary` and preserve the explicit synthetic evidence boundary.

Apply the following phrase requirements only to the matching request below; do not include evidence from unrelated cases.

## Required evidence

Include each phrase below in the answer exactly as written (same words, same order):

For: Explain the synthetic product-affinity and benchmark assumptions without treating them as observed conversion performance.

- Product Affinity Matrix
- Response Assumption
- Evidence boundary

Report only figures and conclusions found in the list records, the rules knowledge or this operation's canonical output, or simple arithmetic on those figures that you label as computed. Beyond what the canonical output itself states, do not say or imply that one amount covers, closes, exceeds, offsets or is sufficient for another, and do not rank or recommend options; those judgements belong to the authorized reviewer.
