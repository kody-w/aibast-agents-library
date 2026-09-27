---
name: credit-analysis
description: Use for eligibility and ratio analysis questions in the Loan Origination Assistant synthetic pilot.
---
<!-- bic:source=blank -->
# Eligibility and ratio analysis

Read the records with the SharePoint list tools, and the rules and controls knowledge.

Calculates transparent DTI, LTV, credit, and DSCR comparisons for human underwriting.

## Procedure

1. Identify the exact fictional record or report scope; do not substitute a different record.
2. Use the synthetic operating snapshot and return the source-backed evidence required by the request.
3. Separate observed evidence, calculated or heuristic output, and proposed next steps.
4. State that the result is not legal, regulatory, insurance, lending, tax, investment, or financial advice.
5. State that no approval, communication, filing, account change, payment, order, transaction, or external action occurred.
6. Name the authorized human review required before action.

## Locked example

Persona: Underwriter

Prompt: Pre-analyze Kevin Nguyen’s ratios and show every stated eligibility exception.

Expected synthetic evidence: LA-2025-4002, DTI.

Apply the following phrase requirements only to the matching request below; do not include evidence from unrelated cases.

## Required evidence

Include each phrase below in the answer exactly as written (same words, same order):

For: Pre-analyze Kevin Nguyen’s ratios and show every stated eligibility exception.

- LA-2025-4002
- DTI

Report only figures and conclusions found in the list records, the rules knowledge or this operation's canonical output, or simple arithmetic on those figures that you label as computed. Beyond what the canonical output itself states, do not say or imply that one amount covers, closes, exceeds, offsets or is sufficient for another, and do not rank or recommend options; those judgements belong to the authorized reviewer.
