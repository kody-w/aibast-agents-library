---
name: "content-launch-clearance"
description: "Help programming, distribution and rights teams confirm where, when and on which platform a title can launch from a synthetic rights snapshot: the launch clearance by territory and platform with the exact contract clause cited, the distribution window and any holdback that blocks an earlier date, and whether the request is ready for rights-team approval. The agent never schedules or publishes a title, changes a contract or submits an approval; the rights team approves every launch through future authenticated tools. Always call this tool for a title's launch rights: whether it is cleared in the requested territory and on the owned streaming service, which contract clause says so, which window and holdback apply, and what is still missing before rights approval. Call it right away; every operation has demo defaults."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "content_launch_clearance_agent.py"
  tool-name: "ContentLaunchClearanceAgent"
  agent-sha256: "04793d0bb0e7c6e8f6244bacfd81ae972391e34db6dba5d060ae027da1f36f37"
  version: "1.0.0"
  author: "AIBAST"
  tags: "media, streaming, rights-and-clearances, content-distribution, launch-planning"
---

# Content Launch Clearance

Help programming, distribution and rights teams confirm where, when and on which platform a title can launch from a synthetic rights snapshot: the launch clearance by territory and platform with the exact contract clause cited, the distribution window and any holdback that blocks an earlier date, and whether the request is ready for rights-team approval. The agent never schedules or publishes a title, changes a contract or submits an approval; the rights team approves every launch through future authenticated tools. Always call this tool for a title's launch rights: whether it is cleared in the requested territory and on the owned streaming service, which contract clause says so, which window and holdback apply, and what is still missing before rights approval. Call it right away; every operation has demo defaults.

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "launch_clearance",
        "distribution_window",
        "approval_readiness"
      ],
      "description": "launch_clearance for whether the title is cleared in its territory and on the owned streaming service, with the contract clause cited; distribution_window for the rights window, holdbacks and the earliest open launch date; approval_readiness for what is missing and whether the request is ready for rights-team approval, with a draft request."
    },
    "title": {
      "type": "string",
      "description": "Title such as Silver Harbor (the default), Paper Lantern or Northern Signal."
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
   python3 scripts/run.py --json '{"operation": "<string>", "title": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=04793d0bb0e7c6e8f6244bacfd81ae972391e34db6dba5d060ae027da1f36f37 -->
```python
"""
Content Launch Clearance Agent for Media & Entertainment.

Read-only launch clearance support for a media company's programming, distribution and rights teams, built on a
synthetic snapshot of five titles requested for the company's owned streaming service: whether each title is
cleared in the requested territory with the exact contract clause cited, the distribution window and any holdback
that blocks an earlier launch date, and whether the request is ready for rights-team approval. Every approval
request is a draft for the rights team to review.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/content-launch-clearance",
    "version": "1.0.0",
    "display_name": "Content Launch Clearance Agent",
    "description": "Help programming, distribution and rights teams confirm where, when and on which platform a title can launch from a synthetic rights snapshot: the launch clearance by territory and platform with the exact contract clause cited, the distribution window and any holdback that blocks an earlier date, and whether the request is ready for rights-team approval. The agent never schedules or publishes a title, changes a contract or submits an approval; the rights team approves every launch through future authenticated tools.",
    "author": "AIBAST",
    "tags": ["media", "streaming", "rights-and-clearances", "content-distribution", "launch-planning"],
    "category": "telecom_media_gaming",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Synthetic domain data (fixed demo day: five titles requested for the owned streaming service)
# ---------------------------------------------------------------------------

TITLES = {
    "silver-harbor": {
        "name": "Silver Harbor", "territory": "UK", "platform": "Owned streaming service",
        "requested_launch": "Not yet confirmed",
        "contract": "UK Rights Agreement SH-UK-2026", "clause": "3.1", "contract_status": "Approved",
        "clause_text": "Exclusive UK subscription streaming rights are granted for 24 months from the end of the "
                       "theatrical holdback.",
        "clearance": "Cleared from the end of the theatrical holdback (in 24 days)",
    },
    "paper-lantern": {
        "name": "Paper Lantern", "territory": "Canada", "platform": "Owned streaming service",
        "requested_launch": "In 33 days",
        "contract": "Canada Rights Agreement PL-CA-2026", "clause": "2.4", "contract_status": "Approved",
        "clause_text": "Canadian subscription streaming rights commence at the start of the window; no earlier "
                       "digital launch is permitted.",
        "clearance": "Not cleared until the window opens (in 40 days)",
    },
    "meadow-current": {
        "name": "Meadow Current", "territory": "Australia", "platform": "Owned streaming service",
        "requested_launch": "In 21 days",
        "contract": "ANZ Rights Agreement MC-ANZ-2026", "clause": "4.2", "contract_status": "Approved",
        "clause_text": "Non-exclusive subscription streaming rights in Australia commence at the start of the window.",
        "clearance": "Cleared from the window opening (in 14 days)",
    },
    "northern-signal": {
        "name": "Northern Signal", "territory": "UK", "platform": "Owned streaming service",
        "requested_launch": "Not yet confirmed",
        "contract": "UK Rights Agreement NS-UK-2026", "clause": "3.1", "contract_status": "Pending review",
        "clause_text": "UK subscription streaming rights are subject to an unsigned amendment.",
        "clearance": "Clearance unavailable",
    },
    "driftwood-lane": {
        "name": "Driftwood Lane", "territory": "UK", "platform": "Owned streaming service",
        "requested_launch": "Not yet confirmed",
        "contract": "UK Rights Agreement DL-UK-2026", "clause": "6.1", "contract_status": "Pending review",
        "clause_text": "The licensed territory list excludes the UK until a territory amendment is signed.",
        "clearance": "Clearance unavailable",
    },
}

WINDOWS = {
    "silver-harbor": {"window": "Exclusive subscription streaming", "opens": "In 24 days", "runs": "24 months",
                      "holdback": "Theatrical holdback",
                      "restriction": "UK launch must not occur before the theatrical holdback ends in 24 days.",
                      "earliest_launch": "In 24 days"},
    "paper-lantern": {"window": "Subscription streaming", "opens": "In 40 days", "runs": "Not stated in the clause",
                      "holdback": "No earlier digital launch",
                      "restriction": "Canadian launch must not occur before the window opens in 40 days.",
                      "earliest_launch": "In 40 days"},
    "meadow-current": {"window": "Non-exclusive subscription streaming", "opens": "In 14 days",
                       "runs": "Not stated in the clause", "holdback": "None",
                       "restriction": "No scheduling restriction after the window opens in 14 days.",
                       "earliest_launch": "In 14 days"},
    "northern-signal": {"window": "Subscription streaming (subject to amendment)", "opens": "Not set",
                        "runs": "Not set", "holdback": "Unsigned contract amendment",
                        "restriction": "Launch blocked while contract amendment is unsigned.",
                        "earliest_launch": "None until the amendment is signed"},
    "driftwood-lane": {"window": "Subscription streaming (territory pending)", "opens": "Not set",
                       "runs": "Not set", "holdback": "Territory amendment",
                       "restriction": "Launch is blocked pending a territory amendment.",
                       "earliest_launch": "None until the territory amendment is signed"},
}

READINESS = {
    "silver-harbor": {"missing": ["Confirmed requested UK launch date"], "rights_status": "Pending submission",
                      "reviewer": "Helena Brooks", "next_step": "Programming confirms the UK launch date on or "
                      "after the holdback end, then the request goes to the rights team."},
    "paper-lantern": {"missing": [], "rights_status": "Pending rights approval", "reviewer": "Tomas Reyes",
                      "next_step": "Move the requested launch from 33 days out to the window opening in 40 days "
                      "before the rights team approves."},
    "meadow-current": {"missing": [], "rights_status": "Approved", "reviewer": "Tomas Reyes",
                       "next_step": "No rights action needed; programming may schedule from the window opening."},
    "northern-signal": {"missing": ["Approved contract amendment", "Requested launch date"],
                        "rights_status": "On hold", "reviewer": "Helena Brooks",
                        "next_step": "Rights team obtains the signed amendment before any launch date is set."},
    "driftwood-lane": {"missing": ["Signed territory amendment", "Requested launch date"],
                       "rights_status": "On hold", "reviewer": "Helena Brooks",
                       "next_step": "Rights team obtains the signed territory amendment before any launch date is set."},
}

BOUNDARY = ("> Read-only synthetic snapshot. No title was scheduled or published, no contract was changed and no "
            "approval was submitted; every approval request is a draft for the rights team to review.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_title(value):
    """Title key or part of its name; empty -> silver-harbor (the demo title); no match -> None."""
    if not value:
        return "silver-harbor"
    q = str(value).lower().strip()
    for key, t in TITLES.items():
        if q in (key, key.replace("-", " ")) or q in t["name"].lower():
            return key
    return None


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

OPERATIONS = ["launch_clearance", "distribution_window", "approval_readiness"]


class ContentLaunchClearanceAgent(BasicAgent):
    """Launch clearance agent for owned streaming launches (read-only, synthetic)."""

    def __init__(self):
        self.name = "ContentLaunchClearanceAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                __manifest__["description"] + " Always call this tool for a title's launch rights: whether it is "
                "cleared in the requested territory and on the owned streaming service, which contract clause says "
                "so, which window and holdback apply, and what is still missing before rights approval. Call it "
                "right away; every operation has demo defaults."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": list(OPERATIONS),
                        "description": (
                            "launch_clearance for whether the title is cleared in its territory and on the owned "
                            "streaming service, with the contract clause cited; distribution_window for the rights "
                            "window, holdbacks and the earliest open launch date; approval_readiness for what is "
                            "missing and whether the request is ready for rights-team approval, with a draft request."
                        ),
                    },
                    "title": {
                        "type": "string",
                        "description": "Title such as Silver Harbor (the default), Paper Lantern or Northern Signal.",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation", "launch_clearance")
        key = _resolve_title(kwargs.get("title"))
        if key is None:
            return (f"# Unknown Title\n\nNo synthetic title matches `{kwargs.get('title')}`; no substitute title "
                    f"was used. Titles: {', '.join(t['name'] for t in TITLES.values())}.\n\n{BOUNDARY}")
        handlers = {
            "launch_clearance": self._launch_clearance,
            "distribution_window": self._distribution_window,
            "approval_readiness": self._approval_readiness,
        }
        handler = handlers.get(op)
        if not handler:
            return f"**Error:** Unknown operation `{op}`."
        return handler(key)

    def _launch_clearance(self, key) -> str:
        t = TITLES[key]
        lines = [
            f"# Launch Clearance - {t['name']}",
            "",
            f"**Territory:** {t['territory']} | **Platform:** {t['platform']} | **Requested launch:** "
            f"{t['requested_launch']}",
            "",
            f"**Clearance:** {t['clearance']}",
            "",
            "## Contract term cited",
            f"- **Document:** {t['contract']} (contract status: {t['contract_status']})",
            f"- **Clause {t['clause']}:** \"{t['clause_text']}\"",
            "",
            f"**Restriction:** {WINDOWS[key]['restriction']}",
            "",
            BOUNDARY,
        ]
        return "\n".join(lines)

    def _distribution_window(self, key) -> str:
        t = TITLES[key]
        w = WINDOWS[key]
        lines = [
            f"# Distribution Window - {t['name']}",
            "",
            f"**Territory:** {t['territory']} | **Platform:** {t['platform']}",
            "",
            "| Window | Opens | Runs | Holdback | Earliest launch |",
            "|--------|-------|------|----------|-----------------|",
            f"| {w['window']} | {w['opens']} | {w['runs']} | {w['holdback']} | {w['earliest_launch']} |",
            "",
            f"**Restriction:** {w['restriction']}",
            f"**Source:** {t['contract']}, clause {t['clause']}",
            "",
            BOUNDARY,
        ]
        return "\n".join(lines)

    def _approval_readiness(self, key) -> str:
        t = TITLES[key]
        r = READINESS[key]
        ready = not r["missing"] and t["contract_status"] == "Approved"
        lines = [
            f"# Approval Readiness - {t['name']}",
            "",
            f"**Rights approval status:** {r['rights_status']} | **Rights reviewer:** {r['reviewer']} "
            f"(Rights & Clearances Lead)",
            f"**Ready for rights-team approval:** {'Yes' if ready else 'No'}",
            "",
            "## Still missing",
        ]
        lines += [f"- {m}" for m in r["missing"]] or ["- Nothing missing"]
        lines += [
            "",
            "## Draft approval request",
            f"- Title: {t['name']} | Territory: {t['territory']} | Platform: {t['platform']}",
            f"- Clearance: {t['clearance']} ({t['contract']}, clause {t['clause']})",
            f"- Next step: {r['next_step']}",
            "",
            "> Draft only: no approval was submitted. " + BOUNDARY[2:],
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = ContentLaunchClearanceAgent()
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
