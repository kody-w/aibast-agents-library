# RAPP Agent Library — Public Skill Interface

> **The RAPP Agent Library is open source.**
> Repo: [github.com/microsoft/aibast-agents-library](https://github.com/microsoft/aibast-agents-library)
> Browse online: [microsoft.github.io/aibast-agents-library/agents.html](https://microsoft.github.io/aibast-agents-library/agents.html)

---

## Repo Identity

```
library_repo: microsoft/aibast-agents-library (public)
public_gateway: microsoft/aibast-agents-library (this repo)
type: agent-library
compatible_with: microsoft/aibast-agents-library, microsoft/aibast-agents-library
agent_base_class: BasicAgent
manifest: manifest.json (auto-generated)
```

---

## How It Works

The agent library is a public GitHub repo with a `manifest.json` at the root. CommunityRAPP's `AgentLibraryManager` agent reads this manifest to let users browse, search, and install agents through the chat UI.

### Install an agent via chat:

```
User: "Show me available agents"
→ AgentLibraryManager fetches manifest.json, lists 17 agents + 83 stacks

User: "Install the calendar agent"
→ Downloads calendar_agent.py from the library into agents/
→ Restart to load
```

### Direct download:

```
Manifest: https://raw.githubusercontent.com/microsoft/aibast-agents-library/main/registry.json
Agent:    https://raw.githubusercontent.com/microsoft/aibast-agents-library/main/agents/@aibast-agents-library/templates/{filename}
```

---

## Agent Catalog

17 individual agents and 83 agent stacks (multi-agent compositions).

Agents are auto-discovered `*_agent.py` files that extend `BasicAgent` and implement `perform()`. Drop one in `agents/`, restart, and it's live.

---

## Agent Format

Every agent is a single `.py` file:

```python
from basic_agent import BasicAgent

class MyAgent(BasicAgent):
    def __init__(self):
        self.name = "MyAgent"
        self.metadata = {
            "name": self.name,
            "description": "What this agent does.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Input"}
                },
                "required": ["input"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        return f"Result: {kwargs.get('input', '')}"
```

---

## Version

```
library_repo: microsoft/aibast-agents-library
agents: 17
stacks: 83
last_updated: 2026-03-25
```
