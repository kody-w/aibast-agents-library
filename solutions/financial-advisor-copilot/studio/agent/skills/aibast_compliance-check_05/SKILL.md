---
name: compliance-check
description: Use for compliance checkpoints questions in the Financial Advisor Agent synthetic pilot.
---
<!-- bic:source=blank -->
# Compliance checkpoints

Read the records with the SharePoint list tools, and the rules and controls knowledge.

Surfaces rule context, senior-investor controls, concentration, and drift flags for compliance review.

## Procedure

1. Identify the exact fictional record or report scope; do not substitute a different record.
2. Use the synthetic operating snapshot and return the source-backed evidence required by the request.
3. Separate observed evidence, calculated or heuristic output, and proposed next steps.
4. State that the result is not legal, regulatory, insurance, lending, tax, investment, or financial advice.
5. State that no approval, communication, filing, account change, payment, order, transaction, or external action occurred.
6. Name the authorized human review required before action.

## Locked example

Persona: Compliance Officer

Prompt: Which client requires senior-investor controls, and what other checkpoints apply?

Expected synthetic evidence: CLI-3003, Senior investor.

Apply the following phrase requirements only to the matching request below; do not include evidence from unrelated cases.

## Required evidence

Include each phrase below in the answer exactly as written (same words, same order):

For: Which client requires senior-investor controls, and what other checkpoints apply?

- CLI-3003
- Senior investor

Report only figures and conclusions found in the list records, the rules knowledge or this operation's canonical output; do not add comparisons, rankings or coverage claims of your own.
