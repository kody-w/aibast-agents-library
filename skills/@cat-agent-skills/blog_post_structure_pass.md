---
schema: rapp-skill/1.0
name: @cat-agent-skills/blog_post_structure_pass
version: 0.1.0
display_name: "Blog Post Structure Pass"
description: "Restructure draft or existing blog posts into a stronger narrative without inventing new claims."
author: "Simon Owen"
tags: ["blog", "writing", "authoring", "content", "structure", "productivity"]
category: it_management
requires_env: []
source_ref: @cat-agent-skills/blog_post_structure_pass
source_url: https://microsoft.github.io/cat-agent-skills/#blog-post-structure-pass
source_license: MIT
converted_from: CAT Agent Skills
converted_on: 2026-08-06
---

# Blog Post Structure Pass

> **Converted skill.** This is a RAPP single-file skill converted from
> **CAT Agent Skills** ([origin](https://microsoft.github.io/cat-agent-skills/#blog-post-structure-pass)), redistributed under
> **MIT** with attribution. Original author: Simon Owen.
> Upstream license text: https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/LICENSE
>
> Drop this file into your brainstem's skills folder, or read it and run the
> steps yourself. Everything the skill needs is in this one file.

## When to use this

Use this skill when the user asks to restructure, reorganise, improve, rewrite, tighten, or strengthen a blog post, article, newsletter, essay, or thought-leadership draft.

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

# Blog Post Structure Pass

Use this skill to improve the structure, argument, flow, and readability of a blog post while preserving the source facts and the author's intended point of view.

## Core rules

- Do not invent evidence, examples, client stories, dates, results, or quotes.
- Preserve the author's stance unless asked to change it.
- Improve the shape of the argument before polishing sentences.
- Keep the revised post suitable for the intended audience and channel.
- If important evidence is missing, mark it as a gap rather than filling it in.

## Default post skeleton

Use this skeleton as a guide, not a rigid template:

1. **Hook / tension** - Why this matters now.
2. **Problem** - What people usually misunderstand or struggle with.
3. **Reframe** - The more useful way to think about it.
4. **Practical implications** - What changes in decisions, behaviour, governance, delivery, or operations.
5. **Example or proof** - Evidence from supplied material.
6. **Takeaway** - What the reader should do, question, or remember.

## Workflow

1. Read the source post or draft.
2. Identify the current thesis and intended audience.
3. Diagnose structural issues: weak opening, unclear argument, repetition, missing transitions, unsupported claims, premature solutioning, or weak ending.
4. Create a revised outline.
5. Rewrite the post into the improved structure.
6. Preserve factual claims from the source and avoid adding unsupported material.
7. Provide a short change note only if useful.

## Output format

```markdown
# [Revised title]

[Rewritten post]

---

## Change notes

- [Only include important changes, assumptions, or evidence gaps.]
```

If the user asks for the structure only, use:

```markdown
## Recommended structure

1. [Section]
2. [Section]
3. [Section]

## Rationale

[Short explanation]
```


## References

This skill includes supporting reference material. Read the relevant reference file when the task needs additional structure, rubric detail, examples, or checklist support.

- `references/post-structure-patterns.md` - use this when additional structure, examples, or checks are useful for the task.

## Quality checklist

Before responding, check:

- The revised post has a clear thesis.
- The opening creates relevance quickly.
- The middle develops the argument rather than listing points.
- The ending lands the insight or next action.
- No unsupported facts have been added.
- The copy sounds natural and human.

---

*Converted for the AIBAST Agents Library from CAT Agent Skills.
The original is authoritative; this file adds the RAPP manifest and the
deterministic layer above, and changes nothing else about the instructions.*
