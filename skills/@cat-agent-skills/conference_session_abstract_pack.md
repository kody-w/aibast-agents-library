---
schema: rapp-skill/1.0
name: @cat-agent-skills/conference_session_abstract_pack
version: 0.1.0
display_name: "Conference Session Abstract Pack"
description: "Create CFP-ready talk titles, abstracts, takeaways, speaker notes, and submission copy from a topic."
author: "Simon Owen"
tags: ["writing", "conference", "abstract", "speaking", "content", "productivity"]
category: it_management
requires_env: []
source_ref: @cat-agent-skills/conference_session_abstract_pack
source_url: https://microsoft.github.io/cat-agent-skills/#conference-session-abstract-pack
source_license: MIT
converted_from: CAT Agent Skills
converted_on: 2026-08-06
---

# Conference Session Abstract Pack

> **Converted skill.** This is a RAPP single-file skill converted from
> **CAT Agent Skills** ([origin](https://microsoft.github.io/cat-agent-skills/#conference-session-abstract-pack)), redistributed under
> **MIT** with attribution. Original author: Simon Owen.
> Upstream license text: https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/LICENSE
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

Use this skill when the user asks to create a conference session proposal, talk abstract, CFP submission, session title, description, learning objectives, takeaways, or speaker bio.

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

# Conference Session Abstract Pack

Use this skill to turn a topic, idea, draft, or talk outline into a submission-ready conference session pack.

## Evidence and positioning rules

- Do not invent speaker credentials, awards, employers, clients, or events.
- Use only the speaker bio information provided by the user or available in connected sources.
- Tailor the submission to the named event, audience, track, format, and session length when supplied.
- If the event constraints are unknown, produce a flexible draft and list assumptions.

## Inputs to look for

- Topic or rough idea.
- Target event or community.
- Audience level: beginner, intermediate, advanced, executive, maker, developer, architect, practitioner.
- Format: session, workshop, lightning talk, panel, keynote, theatre session.
- Desired tone: practical, provocative, technical, strategic, hands-on, story-led.
- Speaker bio or credentials.
- Character or word limits.

## Workflow

1. Identify the central promise of the session.
2. Define the audience and why they should attend.
3. Create several title options with different emphasis.
4. Draft the main abstract in a clear, credible style.
5. Produce learning objectives or takeaways.
6. Add a short audience-fit note and optional speaker notes.
7. If constraints are missing, include a compact assumptions section.

## Output format

```markdown
# Conference session abstract pack

## Recommended title

[Title]

## Alternative titles

1. [Alternative]
2. [Alternative]
3. [Alternative]

## Abstract

[Submission-ready abstract]

## Audience

[Who this is for]

## Key takeaways

- [Takeaway]
- [Takeaway]
- [Takeaway]

## Why this session matters now

[Short positioning paragraph]

## Speaker bio

[Bio if source material is available, otherwise: "Speaker bio not supplied."]

## Optional short version

[Short abstract for tighter submission forms]

## Assumptions or gaps

- [Only include if needed]
```

## Writing guidance

- Make the title specific, not generic.
- Show what the audience will be able to do or understand afterwards.
- Avoid hype and empty trend language.
- Use confident but evidence-led phrasing.
- Keep the abstract readable aloud.


## References

This skill includes supporting reference material. Read the relevant reference file when the task needs additional structure, rubric detail, examples, or checklist support.

- `references/cfp-quality-checklist.md` - use this when additional structure, examples, or checks are useful for the task.

## Quality checklist

Before responding, check:

- The title is memorable and relevant.
- The abstract has a clear promise.
- The takeaways are practical and distinct.
- No credentials or event details have been invented.
- The pack can be pasted into a CFP form with minimal editing.

---

*Converted for the AIBAST Agents Library from CAT Agent Skills.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
