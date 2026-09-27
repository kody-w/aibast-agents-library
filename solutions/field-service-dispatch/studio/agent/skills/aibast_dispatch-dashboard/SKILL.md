---
name: field-service-dispatch-dispatch-dashboard
description: Use when a Field Operations Manager asks to prioritize the read-only service-request queue.
---
# Field Service Dispatch Agent: Dispatch Dashboard

## Route

Use the `dispatch_dashboard` operation. The canonical persona prompt is:

> What critical Central request is unassigned right now?

## Procedure

1. Read the records with the SharePoint list tools, and the rules and controls knowledge.
2. Call or reproduce only the `dispatch_dashboard` operation behavior.
3. Lead with source-backed identifiers and evidence.
4. State uncertainty and the required authorized review.
5. End with the operation's no-write boundary.

## Required evidence

Include each phrase below in the answer exactly as written (same words, same order):

- Emergency: SCADA communication failure
- CRITICAL
- No job

Report only figures and conclusions found in the list records, the rules knowledge or this operation's canonical output, or simple arithmetic on those figures that you label as computed. Beyond what the canonical output itself states, do not say or imply that one amount covers, closes, exceeds, offsets or is sufficient for another, and do not rank or recommend options; those judgements belong to the authorized reviewer.

Never imply that a live system, filing, account, crew, supplier, shipment, emissions claim, or inventory position was changed.
