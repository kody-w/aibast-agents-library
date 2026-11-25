---
name: "campaign-delivery-optimizer"
description: "Help ad sales and ad operations teams keep advertiser campaigns on plan from a synthetic weekly delivery snapshot: each campaign's delivered reach against plan with the gap explained, the placements with extra reach available this week, and the drafted recommendation for the sales lead to approve. The agent never books inventory, changes a campaign or placement, or shares anything with an advertiser; the sales lead approves every recommendation through future authenticated tools. Always call this tool for an advertiser campaign's delivery: whether it is at risk this week and why, which placements have extra reach to close the gap, and the recommendation drafted for the sales lead. Call it right away; every operation has demo defaults."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "campaign_delivery_optimizer_agent.py"
  tool-name: "CampaignDeliveryOptimizerAgent"
  agent-sha256: "817dea94625d6a15dda95fc418d3041f058c3ae12de0d406af7fa50878956c67"
  version: "1.0.0"
  author: "AIBAST"
  tags: "media, advertising, ad-sales, ad-operations, campaign-delivery"
---

# Campaign Delivery Optimizer

Help ad sales and ad operations teams keep advertiser campaigns on plan from a synthetic weekly delivery snapshot: each campaign's delivered reach against plan with the gap explained, the placements with extra reach available this week, and the drafted recommendation for the sales lead to approve. The agent never books inventory, changes a campaign or placement, or shares anything with an advertiser; the sales lead approves every recommendation through future authenticated tools. Always call this tool for an advertiser campaign's delivery: whether it is at risk this week and why, which placements have extra reach to close the gap, and the recommendation drafted for the sales lead. Call it right away; every operation has demo defaults.

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "campaign_risk",
        "available_reach",
        "approval_recommendation"
      ],
      "description": "campaign_risk for delivered reach against the weekly plan and the reason a campaign is or is not at risk; available_reach for placements with extra reach this week and their inventory status; approval_recommendation for the drafted recommendation, its approval status, the sales lead and anything missing."
    },
    "campaign": {
      "type": "string",
      "description": "Campaign such as Harborlight Streaming Campaign (the default) or Cedar View."
    }
  },
  "required": [
    "operation"
  ]
}
```

## How to run it

Pass what it needs as one JSON object. This file is complete on its own: everything
needed to run it is below.

1. If `scripts/run.py` exists beside this file, run from this skill's directory:

   ```bash
   python3 scripts/run.py --json '{"operation": "<string>", "campaign": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=817dea94625d6a15dda95fc418d3041f058c3ae12de0d406af7fa50878956c67 -->
```python
"""
Campaign Delivery Optimizer Agent for Media Ad Sales.

Read-only campaign delivery support for a media company's ad sales and ad operations teams, built on a synthetic
snapshot of four active advertiser campaigns in the current week: each campaign's delivered reach against its
weekly plan with the delivery gap explained, the placements with extra reach available this week, and the drafted
recommendation waiting for the sales lead's approval. Every recommendation is a draft; nothing is booked or shared
with an advertiser.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/campaign-delivery-optimizer",
    "version": "1.0.0",
    "display_name": "Campaign Delivery Optimizer Agent",
    "description": "Help ad sales and ad operations teams keep advertiser campaigns on plan from a synthetic weekly delivery snapshot: each campaign's delivered reach against plan with the gap explained, the placements with extra reach available this week, and the drafted recommendation for the sales lead to approve. The agent never books inventory, changes a campaign or placement, or shares anything with an advertiser; the sales lead approves every recommendation through future authenticated tools.",
    "author": "AIBAST",
    "tags": ["media", "advertising", "ad-sales", "ad-operations", "campaign-delivery"],
    "category": "telecom_media_gaming",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Synthetic domain data (fixed demo week: four active advertiser campaigns)
# ---------------------------------------------------------------------------

CAMPAIGNS = {
    "harborlight": {
        "name": "Harborlight Streaming Campaign", "id": "CMP-2041", "sales_lead": "Maya Chen",
        "planned_weekly_reach": "235,000", "delivered_reach": "192,700", "variance": "18% below plan",
        "at_risk": "Yes", "delivery_status": "At risk", "missing": "No",
        "reason": "Delivered reach is 18% below planned weekly reach as of this week's delivery read.",
    },
    "northfield": {
        "name": "Northfield Culture Campaign", "id": "CMP-2038", "sales_lead": "Jon Bell",
        "planned_weekly_reach": "120,000", "delivered_reach": "124,800", "variance": "4% above plan",
        "at_risk": "No", "delivery_status": "On track", "missing": "No",
        "reason": "Delivered reach is tracking 4% above planned weekly reach as of this week's delivery read.",
    },
    "cedar-view": {
        "name": "Cedar View Campaign", "id": "CMP-2045", "sales_lead": "Priya Nair",
        "planned_weekly_reach": "80,000", "delivered_reach": "Incomplete", "variance": "Cannot be compared",
        "at_risk": "Yes", "delivery_status": "Pending review", "missing": "Yes - current-week delivery data",
        "reason": "Delivery data for the current week is incomplete; planned weekly reach cannot be fully compared.",
    },
    "ridgeway-audio": {
        "name": "Ridgeway Audio Campaign", "id": "CMP-2033", "sales_lead": "Elena Ruiz",
        "planned_weekly_reach": "150,000", "delivered_reach": "147,000", "variance": "2% below plan",
        "at_risk": "No", "delivery_status": "On track", "missing": "No",
        "reason": "Delivered reach is within 2% of planned weekly reach as of this week's delivery read.",
    },
}

PLACEMENTS = [
    {"id": "INV-501", "campaign": "harborlight", "placement": "Streaming Home Screen Takeover",
     "extra_reach": "42,000", "status": "Available"},
    {"id": "INV-502", "campaign": "harborlight", "placement": "Weekend Premium Video Pre-roll",
     "extra_reach": "0", "status": "Sold out"},
    {"id": "INV-511", "campaign": "northfield", "placement": "Culture Newsletter Sponsorship",
     "extra_reach": "15,500", "status": "Available"},
    {"id": "INV-520", "campaign": "cedar-view", "placement": "Local News Mid-roll",
     "extra_reach": "8,200", "status": "Pending confirmation"},
    {"id": "INV-531", "campaign": "ridgeway-audio", "placement": "Podcast Network Host-read",
     "extra_reach": "27,000", "status": "Available"},
]

RECOMMENDATIONS = {
    "harborlight": {"draft": "Propose Streaming Home Screen Takeover for an estimated 42,000 additional reach this "
                             "week to address the 18% weekly reach gap.",
                    "approval_status": "Pending sales lead approval", "missing": "Nothing missing"},
    "northfield": {"draft": "No additional reach recommendation is needed because delivery is on track.",
                   "approval_status": "Approved", "missing": "Nothing missing"},
    "cedar-view": {"draft": "Recommendation cannot be finalized until current-week delivery data is provided.",
                   "approval_status": "Blocked - missing delivery data", "missing": "Current-week delivery data"},
    "ridgeway-audio": {"draft": "Keep the current placement mix because delivery is within the planned weekly range.",
                       "approval_status": "Pending sales lead approval", "missing": "Nothing missing"},
}

BOUNDARY = ("> Read-only synthetic snapshot. No inventory was booked, no campaign or placement was changed and "
            "nothing was shared with an advertiser; every recommendation is a draft for the sales lead to approve.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_campaign(value):
    """Campaign key, id or part of its name; empty -> harborlight (the demo campaign); no match -> None."""
    if not value:
        return "harborlight"
    q = str(value).lower().strip().replace(" campaign", "")
    for key, c in CAMPAIGNS.items():
        if q in (key, key.replace("-", " "), c["id"].lower()) or q in c["name"].lower():
            return key
    return None


def _placements(key):
    return [p for p in PLACEMENTS if p["campaign"] == key]


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

OPERATIONS = ["campaign_risk", "available_reach", "approval_recommendation"]


class CampaignDeliveryOptimizerAgent(BasicAgent):
    """Weekly campaign delivery agent for media ad sales (read-only, synthetic)."""

    def __init__(self):
        self.name = "CampaignDeliveryOptimizerAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                __manifest__["description"] + " Always call this tool for an advertiser campaign's delivery: "
                "whether it is at risk this week and why, which placements have extra reach to close the gap, and "
                "the recommendation drafted for the sales lead. Call it right away; every operation has demo "
                "defaults."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": list(OPERATIONS),
                        "description": (
                            "campaign_risk for delivered reach against the weekly plan and the reason a campaign is "
                            "or is not at risk; available_reach for placements with extra reach this week and their "
                            "inventory status; approval_recommendation for the drafted recommendation, its approval "
                            "status, the sales lead and anything missing."
                        ),
                    },
                    "campaign": {
                        "type": "string",
                        "description": "Campaign such as Harborlight Streaming Campaign (the default) or Cedar View.",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation", "campaign_risk")
        key = _resolve_campaign(kwargs.get("campaign"))
        if key is None:
            return (f"# Unknown Campaign\n\nNo synthetic campaign matches `{kwargs.get('campaign')}`; no substitute "
                    f"campaign was used. Campaigns: {', '.join(c['name'] for c in CAMPAIGNS.values())}."
                    f"\n\n{BOUNDARY}")
        handlers = {
            "campaign_risk": self._campaign_risk,
            "available_reach": self._available_reach,
            "approval_recommendation": self._approval_recommendation,
        }
        handler = handlers.get(op)
        if not handler:
            return f"**Error:** Unknown operation `{op}`."
        return handler(key)

    def _campaign_risk(self, key) -> str:
        c = CAMPAIGNS[key]
        at_risk = sum(1 for x in CAMPAIGNS.values() if x["at_risk"] == "Yes")
        lines = [
            f"# Campaign Risk - {c['name']}",
            "",
            f"**Campaign:** {c['id']} | **Sales lead:** {c['sales_lead']} | **Delivery status:** "
            f"{c['delivery_status']} | **At risk this week:** {c['at_risk']}",
            "",
            "| Planned weekly reach | Delivered reach | Variance |",
            "|----------------------|-----------------|----------|",
            f"| {c['planned_weekly_reach']} | {c['delivered_reach']} | {c['variance']} |",
            "",
            f"**Why:** {c['reason']}",
            f"**Anything missing:** {c['missing']}",
            f"**Across all {len(CAMPAIGNS)} active campaigns:** {at_risk} at risk this week.",
            "",
            BOUNDARY,
        ]
        return "\n".join(lines)

    def _available_reach(self, key) -> str:
        c = CAMPAIGNS[key]
        rows = _placements(key)
        lines = [f"# Available Reach - {c['name']}", "",
                 f"**Delivery gap:** {c['variance']} | **Delivery status:** {c['delivery_status']}", ""]
        if rows:
            lines += ["| Inventory | Placement | Extra reach this week | Inventory status |",
                      "|-----------|-----------|-----------------------|------------------|"]
            lines += [f"| {p['id']} | {p['placement']} | {p['extra_reach']} | {p['status']} |" for p in rows]
        else:
            lines.append("**No placements** with extra reach are recorded for this campaign this week.")
        lines += ["", BOUNDARY]
        return "\n".join(lines)

    def _approval_recommendation(self, key) -> str:
        c = CAMPAIGNS[key]
        r = RECOMMENDATIONS[key]
        lines = [
            f"# Approval Recommendation - {c['name']}",
            "",
            f"**Sales lead:** {c['sales_lead']} | **Approval status:** {r['approval_status']}",
            f"**Anything missing:** {r['missing']}",
            "",
            "## Draft recommendation",
            f"- {r['draft']}",
            f"- Basis: {c['reason']}",
            "",
            "> Draft only: nothing was booked or shared with the advertiser. " + BOUNDARY[2:],
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = CampaignDeliveryOptimizerAgent()
    for op in OPERATIONS:
        print(f"\n{'=' * 60}")
        print(f"Operation: {op}")
        print("=" * 60)
        print(agent.perform(operation=op))
```
<!-- /agent -->

## The launcher

Loads the code above and calls `perform` with your JSON input.

<!-- runner sha256=8d6cc7c145c772a5f9ac580f38cf28d5ca2b2a76c57813b5409a606115a6cff5 -->
```python
import hashlib as _hashlib, json as _json, os as _os, sys as _sys, types as _types
from pathlib import Path as _Path


class BasicAgent:
    """BasicAgent contract: name, metadata, perform(**kwargs), to_tool()."""

    def __init__(self, name=None, metadata=None):
        if name is not None:
            self.name = name
        elif not hasattr(self, "name"):
            self.name = "BasicAgent"
        if metadata is not None:
            self.metadata = metadata
        elif not hasattr(self, "metadata"):
            self.metadata = {
                "name": self.name,
                "description": "Base agent -- override this.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            }

    def perform(self, **kwargs):
        return "Not implemented."

    def system_context(self):
        return None

    def to_tool(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.metadata.get("description", ""),
                "parameters": self.metadata.get("parameters", {"type": "object", "properties": {}}),
            },
        }


class AzureFileStorageManager:
    """Local stand-in for the cloud storage helper some agents import.

    Used only if the agent itself saves something. Everything goes under one
    folder, $AGENT_STORAGE (default ~/.agent-storage); delete it to erase all of it.
    Nothing can be read or written outside that folder: a path that would leave it
    (".." or an absolute path) is refused, the same as on a real server. A share
    name never becomes a path either: each named share gets its own folder under
    shares/, named by the sha256 of the name (lower-cased, trimmed), as on a server.
    """

    DEFAULT_MARKER_GUID = "c0p110t0-aaaa-bbbb-cccc-123456789abc"
    _RESERVED_STEMS = {"CON", "PRN", "AUX", "NUL", *("COM%d" % i for i in range(1, 10)), *("LPT%d" % i for i in range(1, 10))}

    def __init__(self, share_name=None, **kwargs):
        root = _os.environ.get("AGENT_STORAGE") or str(_Path.home() / ".agent-storage")
        self.base = _Path(root)
        share = str(share_name or "").strip().lower()
        self.share_name = share or None
        if share:
            self.root = self.base / "shares" / _hashlib.sha256(share.encode("utf-8")).hexdigest()
        else:
            self.root = self.base / "default"
        self.root.mkdir(parents=True, exist_ok=True)
        # What agents read off the helper, named as on a server: the share's folder,
        # the shared memory folder, the memory file name, and the current context.
        self.storage_root = self.root
        self.shared_memory_path = self.root
        self.default_file_name = "memory.json"
        self.current_guid = None
        self.current_memory_path = self.shared_memory_path

    def set_memory_context(self, user_guid=None):
        """One sub-folder per user. None, "" or the marker guid means the shared folder. Returns True."""
        if user_guid is None or user_guid == "" or user_guid == self.DEFAULT_MARKER_GUID:
            self.current_guid = None
            self.current_memory_path = self.shared_memory_path
            return True
        self._folder_name(user_guid)
        self.current_guid = user_guid
        self.current_memory_path = self.root / user_guid
        return True

    def _folder_name(self, user_guid):
        """user_guid when it is one literal folder name; ValueError otherwise (the server's rule)."""
        if not isinstance(user_guid, str):
            raise ValueError("user_guid must be a string")
        if (user_guid in ("", ".", "..") or user_guid.endswith((".", " "))
                or any(ch in '<>:"/\\|?*' or ord(ch) < 32 for ch in user_guid)
                or user_guid.split(".", 1)[0].upper() in self._RESERVED_STEMS):
            raise ValueError("user_guid must be a single path component")
        return user_guid

    def _inside(self, *parts):
        """The resolved path of root/parts; refuses anything that leaves this share's folder.

        The folder checked against is always a fixed child of self.base (the
        $AGENT_STORAGE folder), never anything a caller chose, so nothing an agent
        passes in can move the boundary.
        """
        base = self.root.resolve()
        p = self.root.joinpath(*parts).resolve()
        if p != base and base not in p.parents:
            raise ValueError("path escapes data directory: " + "/".join(str(x) for x in parts if str(x)))
        return p

    def _path(self, file_path):
        p = self._inside(self.current_guid or "", file_path or self.default_file_name)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def ensure_directory_exists(self, directory_path=""):
        """Create a folder inside the store, under the current memory context, and return its path."""
        d = self._inside(self.current_guid or "", directory_path or "")
        d.mkdir(parents=True, exist_ok=True)
        return d

    def read_json(self, file_path=None):
        p = self._path(file_path)
        return _json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    def write_json(self, data, file_path=None):
        self._path(file_path).write_text(_json.dumps(data, indent=2), encoding="utf-8")
        return True

    def update_json(self, update_fn, file_path=None):
        data = update_fn(self.read_json(file_path))
        self.write_json(data, file_path)
        return data

    def read_file(self, file_path):
        p = self._path(file_path)
        return p.read_text(encoding="utf-8") if p.exists() else None

    def write_file(self, file_path, content):
        self._path(file_path).write_text(content, encoding="utf-8")
        return True

    def list_files(self, directory=""):
        d = self._inside(self.current_guid or "", directory)
        return [x.name for x in d.iterdir()] if d.exists() else []

    def delete_file(self, file_path):
        p = self._path(file_path)
        if p.exists():
            p.unlink()
            return True
        return False

    def file_exists(self, file_path):
        return self._path(file_path).exists()


def get_storage_manager(*args, **kwargs):
    """What utils.storage_factory hands out on a server: the one storage helper."""
    return AzureFileStorageManager(*args, **kwargs)


# Every module name a RAPP agent may import, and what each must hold. This is
# exactly what a server exposes: BasicAgent under three names (a bare import works
# there because the agents folder is on sys.path), and one local storage helper
# under the three names cloud agents use for it.
_BASIC_AGENT_ALIASES = ("basic_agent", "agents.basic_agent", "openrappter.agents.basic_agent")
_STORAGE_ALIASES = {
    "utils.azure_file_storage": {"AzureFileStorageManager": AzureFileStorageManager},
    "utils.dynamics_storage": {"DynamicsStorageManager": AzureFileStorageManager},
    "utils.storage_factory": {"get_storage_manager": get_storage_manager},
}


def _shim_table():
    """{module name: {attribute: value}} for install_shims, from the alias tables above.

    Every BasicAgent alias exposes one class: the one an already-present alias
    holds (a real server's, when running inside one), else the stand-in above.
    """
    base = BasicAgent
    for name in _BASIC_AGENT_ALIASES:
        present = _sys.modules.get(name)
        if isinstance(getattr(present, "BasicAgent", None), type):
            base = present.BasicAgent
            break
    table = {name: {"BasicAgent": base} for name in _BASIC_AGENT_ALIASES}
    table.update(_STORAGE_ALIASES)
    return table


def _register_module(dotted, attrs):
    """Put a module holding attrs in sys.modules under dotted, creating parent packages as needed.

    A module already present under any of those names is left exactly as it is;
    a parent only gains a __path__ (so it counts as a package) and an attribute
    for the child when it has neither.
    """
    parts = dotted.split(".")
    parent = None
    for depth in range(1, len(parts) + 1):
        name = ".".join(parts[:depth])
        module = _sys.modules.get(name)
        if module is None:
            module = _types.ModuleType(name)
            if depth == len(parts):
                for attr, value in attrs.items():
                    setattr(module, attr, value)
            _sys.modules[name] = module
        if depth < len(parts) and not hasattr(module, "__path__"):
            module.__path__ = []
        if parent is not None and not hasattr(parent, parts[depth - 1]):
            setattr(parent, parts[depth - 1], module)
        parent = module


def install_shims():
    """Make every module name in the alias tables importable; never replace one already imported."""
    for dotted, attrs in _shim_table().items():
        _register_module(dotted, attrs)


def _import_agent_module(path):
    install_shims()
    path = _Path(path).resolve()
    util = __import__("importlib.util").util
    spec = util.spec_from_file_location("skill_agent_" + path.stem, path)
    module = util.module_from_spec(spec)
    _sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _agent_name(agent):
    return str(agent.metadata.get("name") or agent.name)


def _agents_in(module):
    """[(attribute name, instance), ...] for every agent the module defines, in definition order.

    An agent is a class defined in that module that subclasses BasicAgent (not
    BasicAgent itself), has a callable perform, and whose name does not start
    with "_". This is what a server serves from the file, so it is what a skill
    sees too.
    """
    base = _sys.modules["agents.basic_agent"].BasicAgent
    agents = []
    for attr, obj in list(vars(module).items()):
        if attr.startswith("_") or not isinstance(obj, type):
            continue
        if obj is base or not issubclass(obj, base) or obj.__module__ != module.__name__:
            continue
        if not callable(getattr(obj, "perform", None)):
            continue
        agents.append((attr, obj()))
    return agents


def load_agents(path):
    """Import an agent file by path and return [(attribute name, agent instance), ...]."""
    agents = _agents_in(_import_agent_module(path))
    if not agents:
        raise RuntimeError(f"{_Path(path).name}: no BasicAgent subclass found")
    return agents


def load_agent(path, tool_name=None):
    """Import an agent file by path and return (module, agent instance).

    The file's only agent when it defines one. When it defines several, the one
    whose tool name equals tool_name; without a match, an error naming them all.
    """
    module = _import_agent_module(path)
    agents = _agents_in(module)
    if not agents:
        raise RuntimeError(f"{_Path(path).name}: no BasicAgent subclass found")
    if len(agents) == 1:
        return module, agents[0][1]
    names = [_agent_name(agent) for _, agent in agents]
    if tool_name is not None:
        for name, (_, agent) in zip(names, agents):
            if name == tool_name:
                return module, agent
        raise RuntimeError(f"{_Path(path).name} has no agent named {tool_name!r}; it defines: {', '.join(names)}")
    raise RuntimeError(f"{_Path(path).name} defines {len(agents)} agents ({', '.join(names)}); choose one by its tool name")


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Run this skill's agent locally.")
    ap.add_argument("--json", default=None, help="arguments as a JSON object")
    ap.add_argument("--tool", default=None, help="which agent to run when agent.py defines several (its tool name)")
    ap.add_argument("--describe", action="store_true", help="print the agent's tool definition")
    ap.add_argument("pairs", nargs="*", help="key=value arguments (alternative to --json)")
    args = ap.parse_args(argv)
    here = _Path(__file__).resolve().parent
    try:
        module, agent = load_agent(here / "agent.py", args.tool)
    except RuntimeError as exc:
        hint = " (run again with --tool <name>)" if args.tool is None and "choose one" in str(exc) else ""
        print(f"error: {exc}{hint}", file=_sys.stderr)
        return 2
    if args.describe:
        print(_json.dumps(agent.to_tool(), indent=2))
        return 0
    kwargs = _json.loads(args.json) if args.json else {}
    for pair in args.pairs:
        key, _, value = pair.partition("=")
        kwargs[key] = value
    result = agent.perform(**kwargs)
    if isinstance(result, (dict, list)):
        print(_json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result if result is not None else "")
    return 0


if __name__ == "__main__":
    _sys.exit(main())
```
<!-- /runner -->
