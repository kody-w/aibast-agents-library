---
schema: rapp-skill/1.0
name: @cat-agent-skills/pov_line_generator
version: 0.1.0
display_name: "POV Line Generator"
description: "Generate sharp, specific point-of-view lines for posts, slides, talks, campaigns, or positioning work."
author: "Simon Owen"
tags: ["writing", "positioning", "marketing", "content", "social-media"]
category: general
requires_env: []
source_ref: @cat-agent-skills/pov_line_generator
source_url: https://microsoft.github.io/cat-agent-skills/#pov-line-generator
source_license: MIT
converted_from: CAT Agent Skills
converted_on: 2026-08-06
---

# POV Line Generator

> **Converted skill.** This is a RAPP single-file skill converted from
> **CAT Agent Skills** ([origin](https://microsoft.github.io/cat-agent-skills/#pov-line-generator)), redistributed under
> **MIT** with attribution. Original author: Simon Owen.
> Upstream license text: https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/LICENSE
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

Use this skill when the user asks for a point of view, punchy line, positioning sentence, provocative statement, headline angle, opinion line, or concise strategic stance.

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

# POV Line Generator

Use this skill to generate concise, distinctive point-of-view lines that help a user frame an argument, post, slide, campaign, or talk.

## What makes a good POV line

A strong POV line should:

- Take a clear stance.
- Be specific enough to be meaningful.
- Avoid generic trend commentary.
- Create useful tension without becoming clickbait.
- Be easy to reuse as a post opener, slide headline, talk premise, campaign angle, or executive summary line.

## Inputs to look for

- Topic or theme.
- Audience.
- Desired stance or tension.
- Channel: LinkedIn, slide, keynote, blog, proposal, campaign, workshop.
- Tone: practical, provocative, premium, accessible, technical, executive, conversational.
- Words to include or avoid.

## Workflow

1. Identify the underlying argument, not just the topic.
2. Look for a tension: common belief vs better belief, adoption vs transformation, activity vs value, tooling vs operating model, speed vs control, scale vs quality.
3. Generate one recommended line first.
4. Provide alternatives grouped by style.
5. Keep each line concise and useful.
6. Do not invent evidence or claims.

## Output format

```markdown
## Recommended POV line

[One strong line]

## Alternatives

### More direct
- [Line]
- [Line]

### More provocative
- [Line]
- [Line]

### More executive
- [Line]
- [Line]

## Why the recommended line works

[One short explanation]
```


## References

This skill includes supporting reference material. Read the relevant reference file when the task needs additional structure, rubric detail, examples, or checklist support.

- `references/pov-patterns.md` - use this when additional structure, examples, or checks are useful for the task.

## Quality checklist

Before responding, check:

- The line has a clear point of view.
- It is not interchangeable with any other topic.
- It avoids empty hype.
- It can plausibly open a post, slide, talk, or section.
- The alternatives are meaningfully different, not minor rewrites.

---

*Converted for the AIBAST Agents Library from CAT Agent Skills.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
