# One solution through four doors, by hand (2026-11-18)

Solution: deal-progression. Host: a real GitHub Copilot, given the recipe's test question.
A hand run, kept as the record a generator must reproduce. Not part of the library yet.

| Door | What was loaded | Result |
|---|---|---|
| Plugin, as shipped | the Cowork plugin `.zip` we build today | **Failed.** The skill sent the host to load sub-skills that are not in the package. |
| Plugin, hand-fixed | same, routing map pointed at sections in the file | Right numbers. |
| Plugin, pointer | `plugin.json` plus the pointer skill | Right numbers. 8 KB instead of 64 KB. |
| Skill | the pointer `SKILL.md` alone | Right numbers. |
| Agent | the pointer `.agent.md` (see `../agent-md-by-hand`) | Right numbers. |
| MCP server | `mcp/agent_mcp.py` around the same `agent.py` | Right numbers. |

Every pointer door runs the one `agent.py`, fetched by pinned link and checked by SHA-256
(the MCP server ran a local copy of the same file).

Findings:
1. 64 of 72 shipped plugins carry the routing map that names missing sub-skills.
2. The host shortened answers when the question asked for under 100 words. Numbers stayed the same; the fixed headings did not always survive.
3. The MCP tool takes its name, description and inputs from the agent's own metadata. Nothing is restated.
4. None of these has been through a real AI Accelerator import.
