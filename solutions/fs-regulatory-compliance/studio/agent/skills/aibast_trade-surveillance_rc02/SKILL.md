---
name: trade-reporting-and-execution-surveillance
description: Use for regulator-rejection, missing-field, venue, late-reporting, slippage, best-execution, or trade-level exception questions.
---
<!-- bic:source=blank -->
# Trade reporting and execution surveillance

Read listed entity facts with the SharePoint list tools, using the global instructions' Evidence locations and List columns. Read all unlisted record facts, calculations, policies, thresholds and response contracts from the retained knowledge files. Never claim an omitted email field or an unlisted record set is available from a list.

## Scope

Scan the fixed synthetic trade snapshot for RTS 22 completeness, venue
admission, submission state, and execution-quality outliers.

## Deterministic findings

- TRD-88117: missing field 57.
- TRD-88129: reported venue XETR conflicts with reference data.
- TRD-88133: missing fields 59 and 7, no ARM submission, execution-quality
  outlier, and stale ALGO-IS-DE documentation.
- TRD-88150: reported venue TQEX conflicts with reference data and is an
  execution-quality outlier.
- TRD-88162: report is complete, but ALGO-IS-DE documentation is expired.

## Procedure

1. Lead with TRD-88133 when the user asks which report is most exposed.
2. Name the exact field number and label for missing-field findings.
3. Keep reporting rejection evidence separate from best-execution and
   algorithm-documentation evidence.
4. Do not claim that every exception is a regulator rejection.
5. Label all exact values as synthetic.

Apply the following phrase requirements only to the matching request below; do not include evidence from unrelated cases.

## Required evidence

Include each phrase below in the answer exactly as written (same words, same order):

For: We executed a few hundred trades this week. Which ones will the regulator reject, and why exactly?

- TRD-88133
- field

Report only figures and conclusions found in the list records, the rules knowledge or this operation's canonical output; do not add comparisons, rankings or coverage claims of your own.
