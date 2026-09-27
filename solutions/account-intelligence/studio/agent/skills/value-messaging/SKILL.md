---
name: account-intelligence-value-messaging
description: Draft persona-specific talking points for human review; do not send messages.
---

# Account Intelligence Agent — Value Messaging

Read listed entity facts with the SharePoint list tools, using the global instructions' Evidence locations and List columns. Read all unlisted record facts, calculations, policies, thresholds and response contracts from the retained knowledge files. Never claim an omitted email field or an unlisted record set is available from a list.

## Persona
Account Executive

## Input contract
- Operation: `value_messaging`
- Data source: `synthetic` only
- Use only the workshop's SharePoint list tools and the uploaded rules knowledge.

## Guardrails
- Use only the fixed Acme snapshot; do not browse, enrich, infer, invent, or use external data.
- Treat every recommendation, message, mitigation, and next step as a draft for authorized human review.
- Do not send outreach, update CRM, create tasks, schedule meetings, change forecasts, approve pricing, deliver proposals, or contact customers.

## Procedure
1. Confirm that the request matches `value_messaging`.
2. Read the synthetic records and operating rules before analyzing.
3. Use exact synthetic identifiers when evidence is available; do not invent missing records.
4. Return the exact Acme stakeholder drafts with the `Draft Meeting Talking Points` and `Objection Handling` headings.
5. End with the evidence boundary below.

## Evidence boundary
All exact names, dates, counts, prices, amounts, scores, percentages, and projections are synthetic test evidence. The response is read-only decision support. Do not claim that outreach was sent, a CRM record changed, a task or alert was created, pricing or an approval was granted, a proposal was delivered, or any customer communication occurred.

## Locked demo prompt
Draft persona-specific talking points for the synthetic Acme meeting; do not send messages.

## Expected evidence marker
The response must include `Draft Meeting Talking Points`, `Objection Handling`, and an explicit synthetic evidence boundary.

Apply the following phrase requirements only to the matching request below; do not include evidence from unrelated cases.

## Required evidence

Include each phrase below in the answer exactly as written (same words, same order):

For: Draft persona-specific talking points for the synthetic Acme meeting; do not send messages.

- Draft Meeting Talking Points
- Objection Handling
- Evidence boundary

Report only figures and conclusions found in the list records, the rules knowledge or this operation's canonical output; do not add comparisons, rankings or coverage claims of your own.
