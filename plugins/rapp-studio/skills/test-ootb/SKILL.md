---
name: test-ootb
description: Default real integration test for the RAPP Studio plugin. Deploy ManageMemory, ContextMemory, HackerNews, and LearnNew through Microsoft's plugin, compare with isolated local Brainstem conversations, and repair native differences until functional parity.
---

# Default test: deploy and compare the OOTB agents

Read this plugin's `skills/rapp-to-studio/SKILL.md` and
`examples/ootb/scenario.json`. This is the default integration test for
`rapp-studio`, not an optional demonstration standing in for real testing.

## Source and environment

- Use all four pinned OOTB sources in the scenario: ManageMemory, ContextMemory,
  HackerNews, and LearnNew. This fixed example does not constrain `convert`,
  which accepts any selected RAPP group.
- If the selected checkout matches the recorded revision/hashes, reuse it.
  Otherwise obtain the public source at the pinned revision in the run
  directory. Do not modify the user's installed Brainstem or silently test
  a different version.
- Include the matching BasicAgent, local storage shim, kernel, soul, and
  existing startup/dependency files needed for an isolated local baseline.
  Do not copy `.env`, token caches, memories, or generated user agents.
- Let the user authenticate and select the target Power Platform environment
  if those choices are missing. No hardcoded tenant, account, or connection ID.
- Start the baseline with the repository's existing startup mechanism in an
  isolated directory/port, or use an explicitly approved already-isolated
  Brainstem. Its `/health` and `/chat` must be reachable. Do not modify the
  kernel or count direct Python calls as end-to-end response evidence.
- Authentication for the local Brainstem remains user-owned; if it needs a
  separate GitHub sign-in, present that official flow rather than copying
  credentials from another application.

When a working Brainstem is already installed, this plugin's test helper can
reuse its unchanged kernel and normal authentication while isolating the
selected source agents and memory:

```bash
<brainstem-python> <plugin-root>/scripts/start-baseline.py \
  --runtime-root <installed-brainstem-directory> \
  --source-root <pinned-checkout>/rapp_brainstem \
  --run-dir <new-run-directory>/local-baseline
```

It binds an available loopback port and writes `baseline.json` with the URL,
PID, source hashes, installed kernel hash/version and model. Verify `/health`
and `/chat` before testing. The installed runtime version is recorded
separately from the pinned agent sources, not claimed to be byte-identical
to the checkout. It copies no credentials and does not modify the kernel.
This is test-workspace isolation, not a security sandbox for arbitrary code.

## Real deployment

Use Microsoft Init, Architect, and Manage via `rapp-to-studio` to create or
resume one dedicated native Draft. The plugin must create the required native
skills, tools, connections, and Dataverse-backed persistence; the user should
not have to design those artifacts.

The example mapping must include:

| Source | Required native outcome |
|---|---|
| ManageMemory | Actual scoped Dataverse writes, append-safe persistence, bounded input handling |
| ContextMemory | Actual scoped recall/filter/order/limits plus the source's per-turn context behavior |
| HackerNews | Live calls to the original HN API and equivalent returned stories/links/errors |
| LearnNew | Preview, create, swarm, list, delete, submit preparation, and later native execution of learned capabilities |

Read actual native connector schemas and IDs. Use built-in Dataverse for
storage, not Azure, a RAPP backend, RAG, or transient sandbox files.

## Execute and converge

1. Expand the scenario placeholders once per run. Freeze those cases and source
   hashes, retaining equivalent conversations and state on both sides.
2. Run **every** scenario case against local Brainstem `/chat` and the exact
   deployed native API, using Microsoft's Direct-to-Engine client or a
   supported configured Direct Line channel. Browser testing is optional.
   Follow the main skill's dedicated-test publication approval gate.
   Read each operation's detailed source contract when
   deriving the expected outputs; the scenario lists minimum invariants, not
   canned answers.
3. Supplement with deterministic bound/error/scope checks where needed.
   Observe actual native tool/flow/Dataverse receipts. A created agent record
   or successful PAC command is not proof of a working deployment.
4. Use the response reviewer and the mandatory compare/repair/retest loop.
   Microsoft Architect repairs functional differences; Manage updates the
   same Draft; rerun the cases and regressions.
5. Finish only after the latest native revision has zero failed and zero
   blocked required cases. A source-baseline failure is a real blocker, not
   permission to weaken expectations or silently change the baseline.

If no environment, auth, permission, or native execution capability is
available, preserve the partial run as `blocked`; do not substitute a mock
run and call this default integration test successful.

## Evidence and teaching artifact

Keep, outside the shipped plugin:

- source/PAC/Microsoft-plugin versions and source hashes;
- selected environment, actual agent ID/published revision and native artifact/binding map;
- paired real responses, per-case verdicts and meaningful differences;
- Dataverse and execution receipts, including new-session recall and learned
  capability invocation after creation;
- each repair iteration and final full-suite verdict;
- a short example walkthrough explaining how each RAPP behavior became a
  native Studio capability, with actual screenshots where available.

Clean up only this run's synthetic rows/capabilities, retaining the user's
test agent and evidence unless they request removal. Native test publication
requires its own explicit permission; publishing the plugin marketplace does
not supply that permission.
