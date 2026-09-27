---
name: asset-maintenance-forecast-asset-health
description: Use when a Reliability Engineer asks to triage condition scores without making a safety determination.
---
# Asset Maintenance Forecast Agent: Asset Health

## Route

Use the `asset_health` operation. The canonical persona prompt is:

> Show me the weakest asset condition and whether this is an operating authorization.

## Procedure

1. Read the records with the SharePoint list tools, and the rules and controls knowledge.
2. Call or reproduce only the `asset_health` operation behavior.
3. Lead with source-backed identifiers and evidence.
4. State uncertainty and the required authorized review.
5. End with the operation's no-write boundary.

## Required evidence

Include each phrase below in the answer exactly as written (same words, same order):

- Substation Transformer B-12
- CRITICAL
- not a safety determination

Report only figures and conclusions found in the list records, the rules knowledge or this operation's canonical output; do not add comparisons, rankings or coverage claims of your own.

Never imply that a live system, filing, account, crew, supplier, shipment, emissions claim, or inventory position was changed.
