---
schema: rapp-skill/1.0
name: @cat-agent-skills/iterative_file_editing
version: 1.0.0
display_name: "Iterative File Editing"
description: "In Copilot Studio, re-sending an edited file under the same name fails to deliver it \u2014 the change is made but never reaches the user. This skill gives each iteration a new version-numbered filename (report_v1.docx, report_v2.docx\u2026) so every update actually lands in the chat as its own attachment."
author: "Adi Leibowitz"
tags: ["files", "iteration", "workflow", "collaboration", "productivity"]
category: general
requires_env: []
source_ref: @cat-agent-skills/iterative_file_editing
source_url: https://microsoft.github.io/cat-agent-skills/#iterative-file-editing
source_license: MIT
converted_from: CAT Agent Skills
converted_on: 2026-08-06
---

# Iterative File Editing

> **Converted skill.** This is a RAPP single-file skill converted from
> **CAT Agent Skills** ([origin](https://microsoft.github.io/cat-agent-skills/#iterative-file-editing)), redistributed under
> **MIT** with attribution. Original author: Adi Leibowitz.
> Upstream license text: https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/LICENSE
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

Use this skill whenever you create or edit ANY file for the user in the Copilot Studio container — a document, spreadsheet, slide deck, code file, data export, anything. It keeps your work-in-progress durable and shows the user an updated version after every change, so the two of you refine the same file together across turns — the user sees real progress each round, earlier work is never lost, and neither of you has to start over. Apply it from the very first file you make.

## The deterministic layer

RAPP skills state their contract explicitly, so two runs of the same skill do
the same thing:

- **Inputs** — whatever the steps below name. If an input is missing, say so
  and stop rather than guessing.
- **Outputs** — the artifact the steps produce, named where it is written.
- **Verification** — before reporting success, confirm the output exists and
  matches what was asked. A silent partial result is a failure.
- **Configuration** — never hardcode an endpoint, key, or tenant. Read them
  from the environment (`requires_env` above lists what this skill needs).

## Skill

When you send the user an updated version of a file you've **already** sent them,
give it a new filename with an incremented version number — `report_v2.docx`,
`report_v3.docx`, and so on. If you reuse the filename the user has already
received, the delivery event won't fire and they'll never get the update, even
though the file changed. A filename they haven't seen before is what triggers the
send.

So annotate each iteration with the next version number, and the user receives
every version as its own attachment.

## Example
```
report_v1.docx   first version sent to the user
report_v2.docx   the same file after "make the timeline more detailed"
report_v3.docx   after "also add a budget table"
```

---

*Converted for the AIBAST Agents Library from CAT Agent Skills.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
