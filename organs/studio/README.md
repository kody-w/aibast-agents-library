# Send to Copilot Studio (organ)

Turns a Brainstem's agents into a Copilot Studio agent by one data-driven rule.
The `SendToStudio` agent (`agents/@aibast-agents-library/templates/studio_organ_agent.py`)
installs this folder from the registry (every file checked by SHA-256) and removes it
again; the kernel keeps running and is never changed.

| File | What it is |
| --- | --- |
| `sandbox-profile.json` | What the Copilot Studio skill sandbox can do, dated and sourced. The only input that decides the translation. |
| `studio_organ.py` | Static analyzer (AST; never runs an agent), the plan, and the workspace builder. |
| `skill_run.py` | Shipped in each skill as `scripts/run.py`: stands in for BasicAgent and the storage helper, and routes web calls and saved memory to workflow tools. |
| `send_to_studio.py` | The MCP driver: prints the steps, or runs them through GitHub Copilot CLI with `@microsoft/copilot-studio-mcp`. Stops before publish unless `--publish`. |

## The rule

1. Read each `*_agent.py` and list what it needs: web calls (with the address and method
   it can resolve), saved memory (the kernel's `utils.azure_file_storage` helper),
   subprocesses, libraries, files it writes, environment values.
2. What the profile says the sandbox can do stays in a **skinny skill**: `SKILL.md`
   (when to use it, how to run it, its inputs), `scripts/agent.py` byte for byte,
   `scripts/run.py`, `scripts/routes.json`.
3. Each need the sandbox cannot meet becomes a **workflow tool** (trigger "When an agent
   calls the flow", the action, "Respond to the agent"): a GET becomes Power Automate's
   HTTP action `{"type": "Http", "inputs": {"method": "GET", "uri", "queries"}}` (no
   headers, body or sign-in); saved memory becomes Dataverse list/add/update on a table
   named for the store (both memory agents write the one Brainstem memory, so they share
   `rapp_brainstemmemory`). A need with no workflow-tool route (a POST, a subprocess, a
   secret, an address worked out at run time) holds the agent back and the plan says why.

Every part of the plan names the profile fact that put it there. Change the profile
(say `network.outbound: true`) and the plan changes with no code change. The private
AIBAST RAPP engine should read the same profile file to follow the same rule; this
change does not touch it.

In the sandbox, `run.py` prints `needs` (call this tool, put its answer here, run
again) until the agent finishes, then `done` with the result and any `save` calls.
Each missing answer is asked for one at a time, so an agent that makes N web calls
takes N + 1 runs.

## Formats not confirmed

`workflows/*.json`, `tables/*.json` and `manifest.json` are spec JSON
(`format_confirmed: false`), not confirmed Copilot Studio file formats. The flow
`definition` mirrors the private engine's agent-flow shape; the Dataverse actions use the
standard `shared_commondataserviceforapps` operations (ListRecords, CreateRecord,
UpdateRecord) and need a connection bound in the environment. The skill ZIP holds
`<name>/SKILL.md` and `<name>/scripts/`, per agentskills.io; whether Copilot Studio wants
that folder at the ZIP root or the files directly is unconfirmed. The driver tells the
MCP server to read its own contracts first (`discover_resources action=describe_actions`)
and never guess a field. The Dataverse table must already exist; the driver stops if it
does not.

```bash
python studio_organ.py plan  ~/.brainstem/src/rapp_brainstem/agents
python studio_organ.py build ~/.brainstem/src/rapp_brainstem/agents --out ws --soul ~/.brainstem/src/rapp_brainstem/soul.md
python send_to_studio.py ws            # dry run: prints the steps
```
