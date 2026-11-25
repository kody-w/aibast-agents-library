---
name: "first-time-fix"
description: "Help contact center and field service agents resolve a customer's connection issue on the first call from a synthetic broadband snapshot: the service status with the guided connection fix, local network work that could be affecting the service, previous visit outcomes with technician notes, and the recommended technician with the job preparation when a visit is needed. The agent never books, changes or cancels a visit, changes a service, contacts a customer or dispatches a technician; a human agent confirms every booking through future authenticated tools. Always call this tool for a customer's connection issue: the guided fix to use now, whether local network work is affecting the service, what previous visits found, and which technician to book with what job preparation. Call it right away; every operation has demo defaults."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "first_time_fix_agent.py"
  tool-name: "FirstTimeFixAgent"
  agent-sha256: "35c333da8a89eb74aaaebedee0d92840329b02cb0b7e6d31cd29832f26ee86c4"
  version: "1.0.0"
  author: "AIBAST"
  tags: "telecommunications, broadband, contact-center, field-service, first-call-resolution"
---

# First Time Fix

Help contact center and field service agents resolve a customer's connection issue on the first call from a synthetic broadband snapshot: the service status with the guided connection fix, local network work that could be affecting the service, previous visit outcomes with technician notes, and the recommended technician with the job preparation when a visit is needed. The agent never books, changes or cancels a visit, changes a service, contacts a customer or dispatches a technician; a human agent confirms every booking through future authenticated tools. Always call this tool for a customer's connection issue: the guided fix to use now, whether local network work is affecting the service, what previous visits found, and which technician to book with what job preparation. Call it right away; every operation has demo defaults.

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "guided_fix",
        "local_work_check",
        "visit_history",
        "technician_booking"
      ],
      "description": "guided_fix for the service status and the step-by-step fix to use during the call; local_work_check for planned or emergency network work affecting the service; visit_history for previous visit outcomes and technician notes; technician_booking for the recommended technician, the job preparation and the booking status."
    },
    "service": {
      "type": "string",
      "description": "Customer service such as Alder Grove Service (the default) or Meadow Lane."
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
   python3 scripts/run.py --json '{"operation": "<string>", "service": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=35c333da8a89eb74aaaebedee0d92840329b02cb0b7e6d31cd29832f26ee86c4 -->
```python
"""
First-Time Fix Agent for Telecommunications.

Read-only first-call resolution support for a broadband provider's contact center and field service team, built
on a synthetic snapshot of five customer services in one service area: the service status with the guided
connection fix to use during the call, local network work that could be affecting the service, previous visit
outcomes with technician notes, and the recommended technician with the job preparation when a visit is needed.
Every booking is a draft for a human agent to confirm.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/first-time-fix",
    "version": "1.0.0",
    "display_name": "First-Time Fix Agent",
    "description": "Help contact center and field service agents resolve a customer's connection issue on the first call from a synthetic broadband snapshot: the service status with the guided connection fix, local network work that could be affecting the service, previous visit outcomes with technician notes, and the recommended technician with the job preparation when a visit is needed. The agent never books, changes or cancels a visit, changes a service, contacts a customer or dispatches a technician; a human agent confirms every booking through future authenticated tools.",
    "author": "AIBAST",
    "tags": ["telecommunications", "broadband", "contact-center", "field-service", "first-call-resolution"],
    "category": "telecom_media_gaming",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Synthetic domain data (fixed demo day: one service area, five customer services)
# ---------------------------------------------------------------------------

SERVICES = {
    "alder-grove": {
        "name": "Alder Grove Service", "plan": "Fibre 500", "area": "North service area", "cabinet": "Cabinet N-14",
        "status": "Active - intermittent connection", "drops_7_days": 6, "open_case": "CS-48211",
        "guided_fix": [
            "Restart the optical network terminal (ONT).",
            "Wait 2 minutes for it to reconnect.",
            "Confirm the broadband light is solid green.",
        ],
        "visit_rule": "Book a technician if the broadband light stays red after the restart.",
        "flag": "Repeated drops after restart",
    },
    "cedar-reach": {
        "name": "Cedar Reach Service", "plan": "Fibre 300", "area": "East service area", "cabinet": "Cabinet E-03",
        "status": "Active - no fault detected", "drops_7_days": 1, "open_case": "CS-48207",
        "guided_fix": [
            "Check that the router power cable is secure.",
            "Restart the router.",
            "Test one wired device.",
        ],
        "visit_rule": "No visit unless service is still unavailable after the planned maintenance.",
        "flag": "Maintenance window may affect connection",
    },
    "willow-park": {
        "name": "Willow Park Service", "plan": "Fibre 900", "area": "West service area", "cabinet": "Cabinet W-21",
        "status": "Active - connection restored", "drops_7_days": 0, "open_case": "CS-48190",
        "guided_fix": [
            "Confirm the router is powered on.",
            "Run a connection test before taking further action.",
        ],
        "visit_rule": "No visit; no action is required if the connection test passes.",
        "flag": "None",
    },
    "harbour-view": {
        "name": "Harbour View Service", "plan": "Fibre 500", "area": "South service area", "cabinet": "Cabinet S-08",
        "status": "Active - intermittent connection", "drops_7_days": 4, "open_case": "CS-48215",
        "guided_fix": [
            "Check the router indicator lights.",
            "Reseat the broadband cable.",
            "Restart the router once.",
        ],
        "visit_rule": "Book a technician if the broadband indicator stays off.",
        "flag": "Broadband indicator reported off",
    },
    "meadow-lane": {
        "name": "Meadow Lane Service", "plan": "Fibre 300", "area": "North service area", "cabinet": "Cabinet N-09",
        "status": "Active - unavailable", "drops_7_days": 9, "open_case": "CS-48219",
        "guided_fix": [
            "Verify the optical network terminal has power.",
            "Restart it.",
            "Check the broadband light.",
        ],
        "visit_rule": "No premises visit while the emergency cable repair is in progress.",
        "flag": "Local repair expected to complete today",
    },
}

LOCAL_WORK = [
    {"id": "NW-3301", "area": "East service area", "cabinet": "Cabinet E-03", "type": "Planned cabinet maintenance",
     "window": "Today 13:00-16:00", "status": "Scheduled", "affects": ["cedar-reach"]},
    {"id": "NW-3307", "area": "North service area", "cabinet": "Cabinet N-09", "type": "Emergency cable repair",
     "window": "Started 07:40, expected complete 15:30 today", "status": "In progress", "affects": ["meadow-lane"]},
]

VISITS = [
    {"id": "FV-7710", "service": "alder-grove", "when": "22 days ago", "outcome": "Connection restored",
     "note": "Reseated fibre connector; investigate intermittent drops if they recur.", "technician": "Priya Nair"},
    {"id": "FV-7655", "service": "cedar-reach", "when": "40 days ago", "outcome": "No fault found",
     "note": "Service was stable on arrival; customer advised about planned cabinet maintenance.",
     "technician": "Daniel Okafor"},
    {"id": "FV-7702", "service": "willow-park", "when": "24 days ago", "outcome": "Router replaced",
     "note": "New router installed and connection test passed.", "technician": "Marta Lewis"},
    {"id": "FV-7719", "service": "meadow-lane", "when": "20 days ago", "outcome": "External network fault identified",
     "note": "Local cable repair required; no premises work completed.", "technician": "Owen Shah"},
]

TECHNICIANS = {
    "Priya Nair": {"skills": ["Fibre connectors", "ONT replacement"], "area": "North service area",
                   "next_slot": "Tomorrow 09:00-11:00"},
    "Daniel Okafor": {"skills": ["Cabinet work", "Router setup"], "area": "East service area",
                      "next_slot": "Tomorrow 13:00-15:00"},
    "Marta Lewis": {"skills": ["Router diagnostics", "In-home Wi-Fi"], "area": "West service area",
                    "next_slot": "Tomorrow 10:00-12:00"},
    "Owen Shah": {"skills": ["External cable", "ONT replacement"], "area": "North service area",
                  "next_slot": "Tomorrow 14:00-16:00"},
    "Sam Whitley": {"skills": ["Router diagnostics", "Fibre connectors"], "area": "South service area",
                    "next_slot": "Tomorrow 08:00-10:00"},
}

BOOKINGS = {
    "alder-grove": {"technician": "Priya Nair", "status": "Ready to book",
                    "preparation": ["Add the repeated-drop history (6 drops in 7 days).",
                                    "Include the previous fibre-connector visit note (FV-7710).",
                                    "Test the optical network terminal and fibre connector on arrival."]},
    "cedar-reach": {"technician": "Daniel Okafor", "status": "Not required",
                    "preparation": ["Hold the visit until planned cabinet maintenance NW-3301 completes.",
                                    "Include the maintenance reference if service remains unavailable."]},
    "willow-park": {"technician": "Marta Lewis", "status": "No booking needed",
                    "preparation": ["Bring the router diagnostics kit only if a later test fails.",
                                    "Confirm connection test results before any travel."]},
    "harbour-view": {"technician": "Sam Whitley", "status": "Ready to book if the indicator stays off",
                     "preparation": ["Note that the broadband indicator was reported off.",
                                     "Bring a replacement broadband cable and router diagnostics kit."]},
    "meadow-lane": {"technician": "Owen Shah", "status": "Pending local repair",
                    "preparation": ["Do not book a premises visit while emergency cable repair NW-3307 is open.",
                                    "Review repair completion first."]},
}

BOUNDARY = ("> Read-only synthetic snapshot. No visit, service, customer contact, case or technician schedule was "
            "changed; every booking is a draft for the agent to confirm.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_service(value):
    """Service key or part of its name; empty -> alder-grove (the demo service); no match -> None."""
    if not value:
        return "alder-grove"
    q = str(value).lower().strip().replace(" service", "")
    for key, svc in SERVICES.items():
        if q in (key, key.replace("-", " ")) or q in svc["name"].lower():
            return key
    return None


def _local_work(key):
    return [w for w in LOCAL_WORK if key in w["affects"]]


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

OPERATIONS = ["guided_fix", "local_work_check", "visit_history", "technician_booking"]


class FirstTimeFixAgent(BasicAgent):
    """First-call resolution agent for broadband connection issues (read-only, synthetic)."""

    def __init__(self):
        self.name = "FirstTimeFixAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                __manifest__["description"] + " Always call this tool for a customer's connection issue: the guided "
                "fix to use now, whether local network work is affecting the service, what previous visits found, "
                "and which technician to book with what job preparation. Call it right away; every operation has "
                "demo defaults."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": list(OPERATIONS),
                        "description": (
                            "guided_fix for the service status and the step-by-step fix to use during the call; "
                            "local_work_check for planned or emergency network work affecting the service; "
                            "visit_history for previous visit outcomes and technician notes; technician_booking for "
                            "the recommended technician, the job preparation and the booking status."
                        ),
                    },
                    "service": {
                        "type": "string",
                        "description": "Customer service such as Alder Grove Service (the default) or Meadow Lane.",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation", "guided_fix")
        key = _resolve_service(kwargs.get("service"))
        if key is None:
            return (f"# Unknown Service\n\nNo synthetic service matches `{kwargs.get('service')}`; no substitute "
                    f"service was used. Services: {', '.join(s['name'] for s in SERVICES.values())}.\n\n{BOUNDARY}")
        handlers = {
            "guided_fix": self._guided_fix,
            "local_work_check": self._local_work_check,
            "visit_history": self._visit_history,
            "technician_booking": self._technician_booking,
        }
        handler = handlers.get(op)
        if not handler:
            return f"**Error:** Unknown operation `{op}`."
        return handler(key)

    def _guided_fix(self, key) -> str:
        s = SERVICES[key]
        work = _local_work(key)
        lines = [
            f"# Guided Connection Fix - {s['name']}",
            "",
            f"**Plan:** {s['plan']} | **Status:** {s['status']} | **Drops in 7 days:** {s['drops_7_days']} "
            f"| **Open case:** {s['open_case']}",
            "",
            "## Steps to use now",
        ]
        lines += [f"{i}. {step}" for i, step in enumerate(s["guided_fix"], 1)]
        lines += [
            "",
            f"**When to book a visit:** {s['visit_rule']}",
            f"**Local work:** {', '.join(w['type'] + ' (' + w['id'] + ')' for w in work) or 'No confirmed local work'}",
            f"**Flag:** {s['flag']}",
            "",
            BOUNDARY,
        ]
        return "\n".join(lines)

    def _local_work_check(self, key) -> str:
        s = SERVICES[key]
        work = _local_work(key)
        lines = [f"# Local Work Check - {s['name']}", "",
                 f"**Area:** {s['area']} | **Cabinet:** {s['cabinet']}", ""]
        if work:
            lines += ["| Work | Type | Window | Status |", "|------|------|--------|--------|"]
            lines += [f"| {w['id']} | {w['type']} | {w['window']} | {w['status']} |" for w in work]
            lines += ["", f"**Flag for the agent:** {s['flag']}"]
        else:
            lines += [f"**No confirmed local work** on {s['cabinet']} or in the {s['area']}; "
                      f"checked {len(LOCAL_WORK)} open network work records.",
                      f"**Flag for the agent:** {s['flag']}"]
        lines += ["", BOUNDARY]
        return "\n".join(lines)

    def _visit_history(self, key) -> str:
        s = SERVICES[key]
        visits = [v for v in VISITS if v["service"] == key]
        lines = [f"# Previous Visits - {s['name']}", ""]
        if visits:
            lines += ["| Visit | When | Outcome | Technician | Note |", "|-------|------|---------|------------|------|"]
            lines += [f"| {v['id']} | {v['when']} | {v['outcome']} | {v['technician']} | {v['note']} |"
                      for v in visits]
        else:
            lines.append("**No previous visits** are recorded for this service.")
        lines += ["", BOUNDARY]
        return "\n".join(lines)

    def _technician_booking(self, key) -> str:
        s = SERVICES[key]
        b = BOOKINGS[key]
        t = TECHNICIANS[b["technician"]]
        lines = [
            f"# Technician Booking - {s['name']}",
            "",
            f"**Recommended technician:** {b['technician']} ({', '.join(t['skills'])}; {t['area']})",
            f"**Next slot:** {t['next_slot']} | **Booking status:** {b['status']}",
            "",
            "## Job preparation",
        ]
        lines += [f"- {p}" for p in b["preparation"]]
        lines += ["", "> Draft only: no visit was booked. " + BOUNDARY[2:]]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = FirstTimeFixAgent()
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
