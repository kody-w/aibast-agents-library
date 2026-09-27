---
name: settlement-recommendation
description: Use for policy-term settlement estimate questions in the Claims Processing Agent synthetic pilot.
---
<!-- bic:source=blank -->
# Policy-term settlement estimate

Read the records with the SharePoint list tools, and the rules and controls knowledge.

Calculates a nonbinding coverage-limit and deductible estimate without approving, denying, reserving, settling, or paying.

## Procedure

1. Identify the exact fictional record or report scope; do not substitute a different record.
2. Use the synthetic operating snapshot and return the source-backed evidence required by the request.
3. Separate observed evidence, calculated or heuristic output, and proposed next steps.
4. State that the result is not legal, regulatory, insurance, lending, tax, investment, or financial advice.
5. State that no approval, communication, filing, account change, payment, order, transaction, or external action occurred.
6. Name the authorized human review required before action.

## Locked example

Persona: Claims Manager

Prompt: Show the policy-term estimates and state clearly whether any claim was approved or paid.

Expected synthetic evidence: CLM-2025-7002, No approval.

Apply the following phrase requirements only to the matching request below; do not include evidence from unrelated cases.

## Required evidence

Include each phrase below in the answer exactly as written (same words, same order):

For: Show the policy-term estimates and state clearly whether any claim was approved or paid.

- CLM-2025-7002
- No approval

Report only figures and conclusions found in the list records, the rules knowledge or this operation's canonical output, or simple arithmetic on those figures that you label as computed. Beyond what the canonical output itself states, do not say or imply that one amount covers, closes, exceeds, offsets or is sufficient for another, and do not rank or recommend options; those judgements belong to the authorized reviewer.
