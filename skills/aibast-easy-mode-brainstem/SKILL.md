---
name: aibast-easy-mode-brainstem
description: Run supported AIBAST workshops through Brainstem, the learner's personal on-device training AI working alongside GitHub Copilot.
---

# AIBAST Easy Mode — with Brainstem

Once this file is dragged into GitHub Copilot Chat in VS Code, use the
Brainstem personless harness for every Easy Mode request. The user never needs
to say “with Brainstem”; this skill selection already made that choice.

Brainstem is the learner's personal, on-device training AI. Copilot remains the
familiar work surface while Brainstem persists workshop state, hot-loads
specialized instructors, and returns the final evidence verdict.

## Public source

- Repository: `microsoft/aibast-agents-library`
- Workshop branch: `main`
- Registry path: `registry.json`

Resolve the branch through the GitHub API and pin one immutable commit SHA
before downloading anything.

## Start from what you need

When the user describes a business need in their own words instead of naming a
workshop (for example `Our team leads build monthly PowerPoint reports from
Excel and our finance system`):

1. Fetch `registry.json` from the pinned commit and read the `solution`
   entries' names and descriptions.
2. Pick up to three that come closest to the need. Show each as one plain
   line: the name and why it fits. Say clearly when none is an exact match.
3. Let the user choose, then continue as
   `Give me <solution> using Easy Mode and test it for me`.
4. After the test passes, offer to adapt it to their exact need, using the
   playbook below.
5. When nothing comes close, say so and offer two routes: build it yourself
   with `skills/playbooks/build-it-yourself.md`, or adapt the nearest
   workshop with `skills/playbooks/adapt-and-connect.md`. The user can also
   ask the AIBAST team to consider it at
   `https://microsoft.github.io/aibast-agents-library/request-use-case.html`;
   never promise that a requested workshop will be built.

## Playbooks

Before each stage, fetch `skills/playbooks/README.md` from the pinned commit
and follow any playbook whose "use it when" matches the user's situation. The
playbooks hold the up-to-date, step-by-step guidance; this file only routes to
them.

## Choose from the library

When the user asks what is available, or asks for a workshop without naming
one (for example `Show me the AIBAST library, then give me the workshop I pick
using Easy Mode and test it for me`):

1. Fetch `registry.json` from the pinned commit.
2. List every entry whose `_catalog_kind` is `solution`, grouped by
   `category` written as a plain industry name, one line per workshop:
   `display_name — description`. Do not paste JSON or file paths.
3. Ask one question: which workshop they want. Accept a number, a name, or a
   description, resolve it to exactly one registry entry, and confirm the
   `display_name` back to them.
4. Continue as `Give me <solution> using Easy Mode and test it for me` with
   that entry.

Never choose for the user, and never download a workshop before they choose.

## Build and test

When the user says `Give me <solution> using Easy Mode and test it for me`:

1. Check `http://localhost:7071/health`.
2. If Brainstem is not running, start it yourself:
   - prefer `~/.copilot/bin/brainstem start`
   - otherwise use the public Brainstem installer and start it
3. Resolve `@aibast-agents-library/workshop` from the immutable registry.
4. Download its exact `_file`, verify `_sha256`, and import it through
   `POST http://localhost:7071/agents/import`.
5. Send the user's request to `POST http://localhost:7071/chat`.
6. Continue executing every Brainstem handoff without asking the user to steer.
7. Brainstem's generic workshop engine must discover the requested package,
   hot-load the business agent, and run every locked local case.
8. Return the verdict and:
   `Deploy it into Copilot Studio for me.`

## Adapt it (optional)

When the user says `Adapt it to <what I need>`, describes a different process,
data, report, or system after a successful test, or asks how to connect live
systems such as Dynamics 365 Field Service, Excel, or a finance system: follow
`skills/playbooks/adapt-and-connect.md` from the same pinned commit, step by
step. It covers adapting the template on fictional data, then the
optional move to live systems in Copilot Studio. Never accept real customer
records or credentials.

## Deploy

When the user says `Deploy it into Copilot Studio for me`:

1. Send that exact request to Brainstem `/chat`.
2. Resolve `it` from Brainstem's persisted active workshop.
3. Continue every returned handoff.
4. Use the real Copilot Studio front door for Preview validation.
5. Return captured evidence to Brainstem using its callback schema.
6. Do not stop until Brainstem reports `status: complete`.
7. Report exact case totals and `published: false`.

## Rules

- Own all terminal, file, PAC CLI, browser, and evidence work.
- Never ask the user for URLs, environment IDs, commands, or test markers.
- Never mix assets from different Git revisions.
- Never invent a missing result or success-shaped fallback.
- Never retry until a response happens to pass.
- Stop at Draft. Never publish.
