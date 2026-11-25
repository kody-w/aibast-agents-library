---
name: "live-event-launch-planner"
description: "Help live operations, community and marketing teams launch a seasonal in-game event from one plan built on a synthetic snapshot: the launch timeline with every milestone to launch day, the readiness checklist across teams with owners and status, the player announcement with its approval and publishing permission, and a summary of late, missing and blocked work. The agent never publishes an announcement, changes a task, sends a reminder or changes the event; the event owners approve every step through future authenticated tools. Always call this tool for a seasonal event launch: the milestones to launch day, which team tasks are open and who owns them, whether the player announcement is approved and may be published, and what is late, missing or blocked. Call it right away; every operation has demo defaults."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "live_event_launch_planner_agent.py"
  tool-name: "LiveEventLaunchPlannerAgent"
  agent-sha256: "9503f99b9605e77a3b07af943712d434c67b085b0e48d858c2ff7b5424c2a50b"
  version: "1.0.0"
  author: "AIBAST"
  tags: "gaming, live-operations, community, event-launch, readiness"
---

# Live Event Launch Planner

Help live operations, community and marketing teams launch a seasonal in-game event from one plan built on a synthetic snapshot: the launch timeline with every milestone to launch day, the readiness checklist across teams with owners and status, the player announcement with its approval and publishing permission, and a summary of late, missing and blocked work. The agent never publishes an announcement, changes a task, sends a reminder or changes the event; the event owners approve every step through future authenticated tools. Always call this tool for a seasonal event launch: the milestones to launch day, which team tasks are open and who owns them, whether the player announcement is approved and may be published, and what is late, missing or blocked. Call it right away; every operation has demo defaults.

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "launch_timeline",
        "readiness_checklist",
        "announcement_check",
        "launch_summary"
      ],
      "description": "launch_timeline for the milestones from communications approval to launch day and the first milestone; readiness_checklist for every team task with owner, status and source; announcement_check for the player messaging, its approval and publishing permission; launch_summary for late, missing and blocked work with draft owner reminders."
    },
    "event": {
      "type": "string",
      "description": "Seasonal event such as Frostveil Festival (the default) or Moonlit Market."
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
   python3 scripts/run.py --json '{"operation": "<string>", "event": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=9503f99b9605e77a3b07af943712d434c67b085b0e48d858c2ff7b5424c2a50b -->
```python
"""
Live Event Launch Planner Agent for Gaming.

Read-only launch planning support for a game studio's live operations, community and marketing teams, built on a
synthetic snapshot of four seasonal in-game events: the launch timeline from communications approval to launch
day, the cross-team readiness checklist with owners and status, the approved player announcement with its
publishing permission, and a launch summary of late, missing and blocked work. Every announcement and reminder is
a draft; nothing is published or sent.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/live-event-launch-planner",
    "version": "1.0.0",
    "display_name": "Live Event Launch Planner Agent",
    "description": "Help live operations, community and marketing teams launch a seasonal in-game event from one plan built on a synthetic snapshot: the launch timeline with every milestone to launch day, the readiness checklist across teams with owners and status, the player announcement with its approval and publishing permission, and a summary of late, missing and blocked work. The agent never publishes an announcement, changes a task, sends a reminder or changes the event; the event owners approve every step through future authenticated tools.",
    "author": "AIBAST",
    "tags": ["gaming", "live-operations", "community", "event-launch", "readiness"],
    "category": "telecom_media_gaming",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Synthetic domain data (fixed demo day: four seasonal events in planning)
# ---------------------------------------------------------------------------

EVENTS = {
    "frostveil-festival": {
        "name": "Frostveil Festival", "plan": "PLN-FVF Launch", "launch_pack": "SP-FVF-LaunchPack-Approved",
        "launch_day": "In 12 days", "missing": "No",
        "milestones": [("In 2 days", "Launch communications approval"), ("In 7 days", "Readiness review"),
                       ("In 9 days", "Player announcement scheduling"), ("In 12 days", "Launch day")],
        "latest_update": "Yesterday: Live operations confirmed server-event configuration is on track.",
    },
    "emberline-expedition": {
        "name": "Emberline Expedition", "plan": "PLN-EE Launch", "launch_pack": "SP-EE-LaunchPack-Approved",
        "launch_day": "In 8 days", "missing": "No",
        "milestones": [("Tomorrow", "Final event rewards sign-off"), ("In 6 days", "Readiness review"),
                       ("In 8 days", "Launch day")],
        "latest_update": "2 days ago: Marketing confirmed key art delivery.",
    },
    "moonlit-market": {
        "name": "Moonlit Market", "plan": "PLN-MM Launch", "launch_pack": "SP-MM-LaunchPack-Draft",
        "launch_day": "In 11 days", "missing": "Yes - approved player announcement brief",
        "milestones": [("In 3 days", "Community moderation coverage confirmation"), ("In 8 days", "Readiness review"),
                       ("In 11 days", "Launch day")],
        "latest_update": "Yesterday: Community team still needs the approved announcement brief.",
    },
    "cindercrest-trials": {
        "name": "Cindercrest Trials", "plan": "PLN-CT Launch", "launch_pack": "SP-CT-LaunchPack-Approved",
        "launch_day": "In 14 days", "missing": "No",
        "milestones": [("In 4 days", "Localization handoff"), ("In 9 days", "Readiness review"),
                       ("In 14 days", "Launch day")],
        "latest_update": "Today: All launch dependencies have owners.",
    },
}

TASKS = [
    {"id": "TSK-101", "event": "frostveil-festival", "task": "Confirm server-event configuration",
     "team": "Live operations", "owner": "Elena Voss", "status": "Complete", "reminder": "No", "source": "Planner"},
    {"id": "TSK-102", "event": "frostveil-festival", "task": "Confirm community moderation coverage",
     "team": "Community", "owner": "Priya Nair", "status": "Blocked", "reminder": "Yes", "source": "Planner"},
    {"id": "TSK-103", "event": "frostveil-festival", "task": "Submit final store assets",
     "team": "Marketing", "owner": "Mateo Silva", "status": "Late", "reminder": "Yes", "source": "Planner"},
    {"id": "TSK-104", "event": "frostveil-festival", "task": "Review launch communications",
     "team": "Community", "owner": "Jon Bell", "status": "In progress", "reminder": "No", "source": "Teams"},
    {"id": "TSK-201", "event": "emberline-expedition", "task": "Approve event reward table",
     "team": "Live operations", "owner": "Hana Cho", "status": "In progress", "reminder": "Yes", "source": "Planner"},
    {"id": "TSK-301", "event": "moonlit-market", "task": "Provide approved player announcement brief",
     "team": "Marketing", "owner": "Quinn Harper", "status": "Missing", "reminder": "Yes", "source": "SharePoint"},
    {"id": "TSK-401", "event": "cindercrest-trials", "task": "Complete localization handoff",
     "team": "Live operations", "owner": "Ravi Mehta", "status": "In progress", "reminder": "No",
     "source": "Planner"},
    {"id": "TSK-402", "event": "cindercrest-trials", "task": "Approve player announcement brief",
     "team": "Marketing", "owner": "Quinn Harper", "status": "In progress", "reminder": "Yes", "source": "SharePoint"},
]

ANNOUNCEMENTS = {
    "frostveil-festival": {"messaging": "Join the Frostveil Festival from launch day for limited-time quests, "
                                        "rewards, and community challenges.",
                           "approval": "Approved", "permission": "Not granted - marketing lead sign-off required",
                           "brief": "SP-FVF-AnnouncementBrief-Approved", "missing": "Publishing sign-off"},
    "emberline-expedition": {"messaging": "Emberline Expedition arrives on launch day with new expedition rewards "
                                          "and timed objectives.",
                             "approval": "Approved", "permission": "Granted",
                             "brief": "SP-EE-AnnouncementBrief-Approved", "missing": "Nothing missing"},
    "moonlit-market": {"messaging": "Moonlit Market returns with rotating vendor rewards.",
                       "approval": "Pending review", "permission": "Not granted",
                       "brief": "SP-MM-AnnouncementBrief-Draft", "missing": "Approved player announcement brief"},
    "cindercrest-trials": {"messaging": "Cindercrest Trials opens on launch day with competitive trials and "
                                        "seasonal rewards.",
                           "approval": "Missing approval", "permission": "Not granted",
                           "brief": "SP-CT-AnnouncementBrief-Review", "missing": "Messaging approval"},
}

OPEN_STATUSES = ("Late", "Missing", "Blocked")

BOUNDARY = ("> Read-only synthetic snapshot. No announcement was published, no task or event was changed and no "
            "reminder was sent; every announcement and reminder is a draft for the event owners to approve.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_event(value):
    """Event key or part of its name; empty -> frostveil-festival (the demo event); no match -> None."""
    if not value:
        return "frostveil-festival"
    q = str(value).lower().strip()
    for key, e in EVENTS.items():
        if q in (key, key.replace("-", " ")) or q in e["name"].lower():
            return key
    return None


def _tasks(key):
    return [t for t in TASKS if t["event"] == key]


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

OPERATIONS = ["launch_timeline", "readiness_checklist", "announcement_check", "launch_summary"]


class LiveEventLaunchPlannerAgent(BasicAgent):
    """Seasonal in-game event launch planning agent (read-only, synthetic)."""

    def __init__(self):
        self.name = "LiveEventLaunchPlannerAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                __manifest__["description"] + " Always call this tool for a seasonal event launch: the milestones "
                "to launch day, which team tasks are open and who owns them, whether the player announcement is "
                "approved and may be published, and what is late, missing or blocked. Call it right away; every "
                "operation has demo defaults."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": list(OPERATIONS),
                        "description": (
                            "launch_timeline for the milestones from communications approval to launch day and the "
                            "first milestone; readiness_checklist for every team task with owner, status and source; "
                            "announcement_check for the player messaging, its approval and publishing permission; "
                            "launch_summary for late, missing and blocked work with draft owner reminders."
                        ),
                    },
                    "event": {
                        "type": "string",
                        "description": "Seasonal event such as Frostveil Festival (the default) or Moonlit Market.",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation", "launch_timeline")
        key = _resolve_event(kwargs.get("event"))
        if key is None:
            return (f"# Unknown Event\n\nNo synthetic seasonal event matches `{kwargs.get('event')}`; no substitute "
                    f"event was used. Events: {', '.join(e['name'] for e in EVENTS.values())}.\n\n{BOUNDARY}")
        handlers = {
            "launch_timeline": self._launch_timeline,
            "readiness_checklist": self._readiness_checklist,
            "announcement_check": self._announcement_check,
            "launch_summary": self._launch_summary,
        }
        handler = handlers.get(op)
        if not handler:
            return f"**Error:** Unknown operation `{op}`."
        return handler(key)

    def _launch_timeline(self, key) -> str:
        e = EVENTS[key]
        first_when, first_what = e["milestones"][0]
        lines = [
            f"# Launch Timeline - {e['name']}",
            "",
            f"**Launch day:** {e['launch_day']} | **Plan:** {e['plan']} | **Launch pack:** {e['launch_pack']}",
            f"**First milestone:** {first_what} - {first_when.lower()}",
            "",
            "| When | Milestone |",
            "|------|-----------|",
        ]
        lines += [f"| {when} | {what} |" for when, what in e["milestones"]]
        lines += [
            "",
            f"**Latest team update:** {e['latest_update']}",
            f"**Anything missing:** {e['missing']}",
            "",
            BOUNDARY,
        ]
        return "\n".join(lines)

    def _readiness_checklist(self, key) -> str:
        e = EVENTS[key]
        tasks = _tasks(key)
        done = sum(1 for t in tasks if t["status"] == "Complete")
        lines = [f"# Readiness Checklist - {e['name']}", "",
                 f"**Launch day:** {e['launch_day']} | **Tasks complete:** {done} of {len(tasks)}", "",
                 "| Task | Team | Owner | Status | Reminder needed | Source |",
                 "|------|------|-------|--------|-----------------|--------|"]
        lines += [f"| {t['id']} {t['task']} | {t['team']} | {t['owner']} | {t['status']} | {t['reminder']} | "
                  f"{t['source']} |" for t in tasks]
        lines += ["", BOUNDARY]
        return "\n".join(lines)

    def _announcement_check(self, key) -> str:
        e = EVENTS[key]
        a = ANNOUNCEMENTS[key]
        can_publish = a["approval"] == "Approved" and a["permission"] == "Granted"
        lines = [
            f"# Announcement Check - {e['name']}",
            "",
            f"**Messaging approval:** {a['approval']} | **Publish permission:** {a['permission']}",
            f"**Ready to publish:** {'Yes, once launch day scheduling is confirmed' if can_publish else 'No - hold'}",
            f"**Announcement brief:** {a['brief']} | **Anything missing:** {a['missing']}",
            "",
            "## Draft player announcement",
            f"> {a['messaging']}",
            "",
            "> Draft only: the announcement was not published. " + BOUNDARY[2:],
        ]
        return "\n".join(lines)

    def _launch_summary(self, key) -> str:
        e = EVENTS[key]
        tasks = _tasks(key)
        open_items = [t for t in tasks if t["status"] in OPEN_STATUSES]
        counts = {s: sum(1 for t in tasks if t["status"] == s) for s in OPEN_STATUSES}
        lines = [
            f"# Launch Summary - {e['name']}",
            "",
            f"**Launch day:** {e['launch_day']} | **Late:** {counts['Late']} | **Missing:** {counts['Missing']} "
            f"| **Blocked:** {counts['Blocked']}",
            f"**Announcement:** {ANNOUNCEMENTS[key]['approval']}; publish permission "
            f"{ANNOUNCEMENTS[key]['permission'].lower()}",
            "",
        ]
        if open_items:
            lines += ["## Needs attention", "| Task | Owner | Status |", "|------|-------|--------|"]
            lines += [f"| {t['task']} | {t['owner']} ({t['team']}) | {t['status']} |" for t in open_items]
            lines += ["", "## Draft reminders"]
            lines += [f"- To {t['owner']}: \"{t['task']}\" is {t['status'].lower()} for {e['name']}; launch day is "
                      f"{e['launch_day'].lower()}." for t in open_items if t["reminder"] == "Yes"]
        else:
            lines.append("**No late, missing or blocked work** is recorded for this event.")
        lines += ["", "> Draft only: no reminder was sent. " + BOUNDARY[2:]]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = LiveEventLaunchPlannerAgent()
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
