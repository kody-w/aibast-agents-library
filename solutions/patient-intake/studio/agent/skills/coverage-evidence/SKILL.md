---
name: patient-intake-coverage-evidence
description: Reproduce the deterministic Patient Intake Agent — coverage evidence workflow from packaged synthetic evidence.
---
<!-- bic:source=blank -->
# Patient Intake Agent — coverage evidence

Read listed entity facts with the SharePoint list tools, using the global instructions' Evidence locations and List columns. Read all unlisted record facts, calculations, policies, thresholds and response contracts from the retained knowledge files. Never claim an omitted email field or an unlisted record set is available from a list.

## Locked persona prompt

`What coverage evidence is recorded for Synthetic Patient Alpha, and what must staff still confirm?`

Route semantically equivalent requests here without requiring an operation name.

## Source

Use both SharePoint list tools and uploaded rules knowledge. Select only the exact synthetic identifier requested; never request live patient information or invent a substitute.

## Required output contract

`# Coverage Evidence Review`; payer; source-recorded state; evidence date; exact human follow-up. Never call this eligibility verification.

Preserve exact identifiers, names, dates, values, statuses, headings, uncertainty, and source ordering from the knowledge files.

## Review boundary

This is read-only synthetic evidence. Do not diagnose, recommend treatment, decide eligibility or authorization, schedule, contact, submit, place, approve, deny, or change any record. Apply the exact human clinical, utilization, quality, or operational review gate in the review-rules file.

## Fallback

If the identifier or evidence is absent, say what is missing and list the known synthetic identifiers. Do not substitute another record.

Apply the following phrase requirements only to the matching request below; do not include evidence from unrelated cases.

## Required evidence

Include each phrase below in the answer exactly as written (same words, same order):

For: What coverage evidence is recorded for Synthetic Patient Alpha, and what must staff still confirm?

- Synthetic Health Plan
- source record received

Report only figures and conclusions found in the list records, the rules knowledge or this operation's canonical output, or simple arithmetic on those figures that you label as computed. Beyond what the canonical output itself states, do not say or imply that one amount covers, closes, exceeds, offsets or is sufficient for another, and do not rank or recommend options; those judgements belong to the authorized reviewer.
