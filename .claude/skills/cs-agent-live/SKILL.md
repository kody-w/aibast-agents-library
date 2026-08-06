---
name: cs-agent-live
description: >
  Take a Copilot Studio agent that was generated and deployed by the RAPP Factory
  and make it actually answer from its data — then make it presentable enough to
  film. Covers the MCP attach, the auth mode that everyone gets wrong, the silent
  name truncation, and the toggle that hides the build machinery. Trigger when a
  deployed agent "has no data", reports 404 from its data server, or looks
  machine-generated on screen.
---

# Making a deployed Copilot Studio agent live

A Factory deploy lands two solutions and publishes them, and the agent still
answers "I don't have access to that data". Nothing is broken. Four things are
missing, and only one of them is in the Factory's own manual steps.

**claude-in-chrome is the law here.** Never launch a separate browser to drive
Copilot Studio.

## The four gates, in order

### 1. Auth mode must be Maker, not User

This is the one that costs hours. Open the agent → **Tools** → click the MCP
server chip → **Edit MCP server** → **Authentication mode**.

It defaults to **User**. Under User auth the tools are attached, they appear in
the maker panel, the solution is published — and they **never reach the agent
runtime**. The agent truthfully reports it has no tools. Switch to **Maker**,
Confirm, publish.

Symptom you will see first: the agent says *"no MCP tools are connected to this
session"*, or it reaches for an unrelated tool (`list_bash`) because it is
pattern-matching your words against a toolset that does not contain what you
asked for.

### 2. Attach the MCP server to EVERY agent, parent and child

The Factory's manual steps say "once per agent" and mean it. A parent that
delegates to a connected child needs it on both — the 404 will surface as the
parent reporting failure when it is actually the child that cannot see the data.

### 3. The attach does not survive a failed publish

If a publish fails ("We couldn't publish your agent"), **go back and check
Tools** — the attach will be gone. Re-attach, then verify by reopening the panel
before publishing again. Do not assume it stuck.

Preview tests the **draft**, so you can verify the attach works before you
publish. Do that: attach → Preview → ask a real question → then publish.

### 4. Individual tool toggles are a red herring

Inside **Edit MCP server** each tool has its own switch, and they render greyed
out. They are `checked: true, disabled: true` — "Enable all tools" at the top is
on and forces them. Do not spend time trying to flip them.

## Making it presentable

### The name is capped at 30 characters and truncates SILENTLY

"Budget Estimates Briefing Agent" is 31 characters. It saves as
**"Budget Estimates Briefing Agen"** with no error and no warning. Count first,
or check the saved value after.

Factory-generated names are also embarrassing on camera —
`Estimatesbriefbuilder Generate Estimates Brief Agent Agent`, with the doubled
suffix. Rename before filming.

### End user preview hides the build machinery

The toggle sits top-right of the Preview pane and defaults **off**. On, it hides
the chain-of-thought rows and the raw tool identifiers
(`get_estimatesbriefbuildergeneratealternativebriefformatsagent`). Off, those
are on screen for the whole take and are instantly disqualifying for anything
customer-facing.

Verify per-response, not once — behaviour can differ between answers.

### Return does not submit

The chat box ignores Return. Click the send arrow at the input's right edge.
A whole take can be lost to this: the text sits in the box looking submitted.

## Verify before you believe it

Ask a question whose answer can only come from the data server, and read the
response for a real record id. "It replied" is not evidence — the agent will
happily explain that it cannot find anything, which is correct behaviour and
looks like success if you only glance.

Good probe: *"List the briefing records you can see for <topic>."*

## Related

`/tab-film` for capturing the result. `/mcs-deploy` for the deploy itself.
