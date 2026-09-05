# RAPP native Copilot Studio plugin

Select a group of RAPP agents. This plugin extracts their behavior contract,
delegates native authoring to Microsoft's Copilot Studio plugin, and checks
operation-level parity before calling the conversion complete.

It is an orchestration plugin, **not a second compiler or hosted RAPP bridge**.
It accepts any selected agent group; unsupported native behavior is reported
as a blocker, not silently omitted.

## Prerequisites

- Claude Code or GitHub Copilot CLI with plugin support, and Microsoft Power
  Platform CLI.
- `mcs-assistant@copilot-studio-plugin`, installed separately.
- A user-selected Copilot Studio environment and authorized native connections.

Both this workflow and Microsoft's new agentic-loop plugin are experimental.
Package/schema acceptance does not establish that a tenant can execute every
capability.

## Install

Install Microsoft's authoring dependency first:

```text
/plugin marketplace add microsoft/copilot-studio-plugin
/plugin install mcs-assistant@copilot-studio-plugin
```

Load this plugin from a local checkout while developing:

```bash
copilot --plugin-dir ./plugins/rapp-studio
```

The release marketplace is shared by Claude Code and Copilot CLI:

```text
/plugin marketplace add kody-w/rapp-copilot-studio-plugin
/plugin install rapp-studio@aibast-rapp
```

Run the plugin's `convert` command with source paths/group and a target project
or environment. It also provides the `rapp-to-studio` skill:

```text
Convert these RAPP agents to one native Copilot Studio Draft:
  ./agents/manage_memory_agent.py
  ./agents/context_memory_agent.py
  ./agents/hacker_news_agent.py
  ./agents/rar_rapp_learn_new_agent.py
Use the environment I select interactively. Use Dataverse for durable state.
```

The four OOTB agents are an example, not hardcoded scope.

## Default integration test

The plugin's `test` command (or `test-ootb` skill) defaults to **actually
deploying and testing those four OOTB agents**. It pins the source version in
`examples/ootb/scenario.json`, starts an isolated local Brainstem baseline,
uses Microsoft's plugin to author and push a native Draft, and runs the shared
headless response-parity suite. Dataverse supplies native memory and learned-capability
storage.

The suite covers memory persistence/isolation/per-turn context, live HN,
input/error boundaries, and LearnNew's preview, create, list, later invocation,
new-conversation invocation, duplicate handling, swarm, submit preparation, and
delete lifecycle. Functional differences trigger the repair loop.

The resulting source-to-native map, actual paired responses, receipts, and
repair history form the user-facing worked example. Static checks are separate;
they cannot stand in for this live default test. Missing prerequisites or a
source/native limitation leave an explicit blocked result.

## Response parity

The `parity` command sends shared cases to the real local Brainstem and the
exact deployed native Studio API, then uses the read-only response-parity reviewer.
It compares meaning and outcomes rather than requiring identical wording.
Facts, calculations, error behavior, durable state, and side effects still need
real evidence. Results retain both responses and a per-case
`pass`/`fail`/`blocked` verdict. **API testing is the default; browser testing
is optional.** CLI agents use Microsoft's Direct-to-Engine client. Direct
Line is an alternative only where the selected harness/channel supports it.

The runtime API can require a published agent and invocation authorization
separate from PAC authoring sign-in. Publication of a dedicated test agent
and its repair iterations needs explicit user permission; the workflow keeps
Integrated authentication and checks the actual published revision.

Functional differences trigger an automatic **compare -> Microsoft-plugin
repair -> target update -> retest** loop on the same target. The source and case
expectations stay fixed. Completion requires zero failed and zero blocked
required cases on the latest revision; genuine platform/auth blockers are
checkpointed rather than hidden or bypassed with external hosting.

## Responsibility split

| RAPP plugin | Microsoft plugin |
|---|---|
| Read source contracts, dependencies, and operation semantics | Initialize and author native Studio artifacts |
| Keep a complete source-to-target ledger | Implement native skills, supporting code, tools, and flows |
| Enforce native-only scope and preserve the source | Resolve supported native platform bindings |
| Compare real source and Draft behavior | Repair its authored artifacts using the parity evidence |

State, memory, and learned capabilities belong in native Dataverse-backed
implementations. Azure Functions, external Python/RAPP runtimes, localhost
bridges, and new MCP servers are not conversion fallbacks. A knowledge file is
not executable logic or mutable memory.

The workflow keeps agents unpublished unless the user authorizes publishing
the dedicated test target. It never treats a generated YAML file, a saved code record,
or a successful package command as proof of full native execution.

This is a community, experimental plugin, not an officially supported
Microsoft, GitHub, or Anthropic product. A Git-backed marketplace is directly
installable in both clients; inclusion in either vendor's curated directory
is a separate review process.
