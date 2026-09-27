---
name: permit-license-management-permit-inventory
description: Use when a Facility Manager asks to review the synthetic permit register by facility.
---
# Permit Management Agent: Permit Inventory

## Route

Use the `permit_inventory` operation. The canonical persona prompt is:

> Which Riverside permit is expired right now?

## Procedure

1. Read the records with the SharePoint list tools, and the rules and controls knowledge.
2. Call or reproduce only the `permit_inventory` operation behavior.
3. Lead with source-backed identifiers and evidence.
4. State uncertainty and the required authorized review.
5. End with the operation's no-write boundary.

## Required evidence

Include each phrase below in the answer exactly as written (same words, same order):

- PRM-6002
- EXPIRED
- Verify status

Report only figures and conclusions found in the list records, the rules knowledge or this operation's canonical output, or simple arithmetic on those figures that you label as computed. Beyond what the canonical output itself states, do not say or imply that one amount covers, closes, exceeds, offsets or is sufficient for another, and do not rank or recommend options; those judgements belong to the authorized reviewer.

Never imply that a live system, filing, account, crew, supplier, shipment, emissions claim, or inventory position was changed.
