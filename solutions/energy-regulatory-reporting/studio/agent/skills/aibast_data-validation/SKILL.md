---
name: energy-regulatory-reporting-data-validation
description: Use when a Data Analyst asks to screen source-data quality before certification.
---
# Regulatory Reporting Agent: Data Validation

## Route

Use the `data_validation` operation. The canonical persona prompt is:

> Which report data is incomplete or below quality threshold?

## Procedure

1. Read the records with the SharePoint list tools, and the rules and controls knowledge.
2. Call or reproduce only the `data_validation` operation behavior.
3. Lead with source-backed identifiers and evidence.
4. State uncertainty and the required authorized review.
5. End with the operation's no-write boundary.

## Required evidence

Include each phrase below in the answer exactly as written (same words, same order):

- Data collection incomplete
- Data quality score below threshold
- authorized report owner

Report only figures and conclusions found in the list records, the rules knowledge or this operation's canonical output, or simple arithmetic on those figures that you label as computed. Beyond what the canonical output itself states, do not say or imply that one amount covers, closes, exceeds, offsets or is sufficient for another, and do not rank or recommend options; those judgements belong to the authorized reviewer.

Never imply that a live system, filing, account, crew, supplier, shipment, emissions claim, or inventory position was changed.
