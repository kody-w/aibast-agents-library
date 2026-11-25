---
name: "asset-maintenance-forecast"
description: "Analyze a synthetic wind-farm telemetry snapshot for turbine risk, failure forecasting, maintenance budgets, and a draft bundled maintenance plan. Use for reliability and maintenance-planning questions only. The agent never creates work orders, schedules crews, or directs field work; a qualified asset owner must approve any action through future authenticated tools. Always call it first for wind farm or turbine analysis: 'I need immediate analysis on our wind farm turbines' uses maintenance_forecast; 'show the bundled maintenance plan' or 'yes, bundle them' uses work_order_plan."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "asset_maintenance_forecast_agent.py"
  tool-name: "AssetMaintenanceForecastAgent"
  agent-sha256: "08edd95089a4da0c81b3ec203a72424b30aeb3b80ff5110611f4102343787c09"
  version: "1.2.0"
  author: "AIBAST"
  tags: "maintenance, asset-health, energy, predictive, work-orders, budget, wind"
---

# Asset Maintenance Forecast

Analyze a synthetic wind-farm telemetry snapshot for turbine risk, failure forecasting, maintenance budgets, and a draft bundled maintenance plan. Use for reliability and maintenance-planning questions only. The agent never creates work orders, schedules crews, or directs field work; a qualified asset owner must approve any action through future authenticated tools. Always call it first for wind farm or turbine analysis: 'I need immediate analysis on our wind farm turbines' uses maintenance_forecast; 'show the bundled maintenance plan' or 'yes, bundle them' uses work_order_plan.

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "maintenance_forecast",
        "asset_health",
        "budget_projection",
        "work_order_plan"
      ],
      "description": "maintenance_forecast: the default; immediate fleet analysis with the critical alert, additional risks and the bundling recommendation. asset_health: condition triage by risk score. budget_projection: planned versus emergency repair funding. work_order_plan: the bundled maintenance plan for the low-wind window as a draft approval queue (cost comparison, savings, ROI, fleet availability)."
    },
    "asset_id": {
      "type": "string",
      "description": "Optional turbine such as 'Unit 12'. Unknown names return an empty result, never invented data."
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
   python3 scripts/run.py --json '{"operation": "<string>", "asset_id": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=08edd95089a4da0c81b3ec203a72424b30aeb3b80ff5110611f4102343787c09 -->
```python
"""
Asset Maintenance Forecast Agent for Energy sector.

Provides predictive maintenance forecasting, asset health monitoring,
budget projections, and draft work-order planning for a wind-farm fleet:
risk scores from synthetic IoT telemetry, failure windows, planned versus
emergency repair cost, and a bundled maintenance plan for a low-wind window.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/asset-maintenance-forecast",
    "version": "1.2.0",
    "display_name": "Asset Maintenance Forecast Agent",
    "description": "Analyze a synthetic wind-farm telemetry snapshot for turbine risk, failure forecasting, maintenance budgets, and a draft bundled maintenance plan. Use for reliability and maintenance-planning questions only. The agent never creates work orders, schedules crews, or directs field work; a qualified asset owner must approve any action through future authenticated tools.",
    "author": "AIBAST",
    "tags": ["maintenance", "asset-health", "energy", "predictive", "work-orders", "budget", "wind"],
    "category": "energy",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Synthetic domain data (the demo default: one wind farm)
# ---------------------------------------------------------------------------

FLEET = {
    "site": "wind farm",
    "turbines": 45,
    "model": "GE 2.5MW",
    "telemetry": "Azure IoT Hub",
    "other_units_offline": 1,
    "other_offline_note": "Unit 41 in a scheduled blade inspection",
}

# Turbines flagged by the synthetic telemetry model; the other 41 online turbines score below 3.0.
ASSETS = {
    "Unit 12": {
        "risk_score": 8.7,
        "risk_label": "Failure Imminent",
        "failure_mode": "Main bearing end-of-life wear",
        "repair": "bearing",
        "days_to_failure": "18-30",
        "emergency_cost": 227000,
        "labor_cost": 30250,
        "parts_cost": 28000,
        "duration_days": 3,
        "crew": "Crew A",
        "dates": "March 18-20",
    },
    "Unit 23": {
        "risk_score": 6.2,
        "risk_label": "Elevated",
        "failure_mode": "Gearbox oil contamination",
        "repair": "oil",
        "days_to_failure": "45",
        "emergency_cost": 98000,
        "labor_cost": 1500,
        "parts_cost": 5000,
        "duration_days": 2,
        "crew": "Crew A",
        "dates": "March 21-22",
    },
    "Unit 37": {
        "risk_score": 3.8,
        "risk_label": "Watch",
        "failure_mode": "Generator slip ring wear",
        "repair": "slip ring",
        "days_to_failure": "90",
        "emergency_cost": 41000,
        "labor_cost": 1000,
        "parts_cost": 3000,
        "duration_days": 1,
        "crew": "Crew B",
        "dates": "March 22",
    },
}

# Per-mobilization costs: every separate job rents its own crane and pays crew travel.
MOBILIZATION = {
    "crane_per_job": 6000,
    "crew_travel_per_job": 850,
    "bulk_parts_discount_pct": 15,
}

BUNDLE_WINDOW = {
    "dates": "March 18-22",
    "days": 5,
    "forecast": "low-wind forecast",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _selected_assets(asset_id=None):
    """All flagged turbines, or the one named ('Unit 12' or '12'); an unknown name returns none."""
    if not asset_id:
        return ASSETS
    q = str(asset_id).lower().strip()
    if q.isdigit():
        q = "unit " + q
    return {k: v for k, v in ASSETS.items() if k.lower() in q}


def _status(score):
    if score >= 8:
        return "CRITICAL"
    if score >= 5:
        return "WARNING"
    return "WATCH"


def _k(value):
    """$227K / $1.7K style."""
    if value % 1000 == 0:
        return f"${value // 1000}K"
    return f"${value / 1000:.1f}K"


def _planned_cost(unit):
    """Stand-alone planned repair: labor + parts + one crane and one crew mobilization."""
    a = ASSETS[unit]
    return a["labor_cost"] + a["parts_cost"] + MOBILIZATION["crane_per_job"] + MOBILIZATION["crew_travel_per_job"]


def _bundle_numbers():
    m = MOBILIZATION
    jobs = len(ASSETS)
    labor = sum(a["labor_cost"] for a in ASSETS.values())
    parts = sum(a["parts_cost"] for a in ASSETS.values())
    separate = sum(_planned_cost(u) for u in ASSETS)
    crane_saving = (jobs - 1) * m["crane_per_job"]
    travel_saving = (jobs - 1) * m["crew_travel_per_job"]
    parts_saving = parts * m["bulk_parts_discount_pct"] // 100
    bundled = labor + parts - parts_saving + m["crane_per_job"] + m["crew_travel_per_job"]
    savings = separate - bundled
    lead = ASSETS["Unit 12"]
    avoided = lead["emergency_cost"] - _planned_cost("Unit 12")
    total_value = avoided + savings
    roi = round(total_value * 100 / bundled)
    before = round((FLEET["turbines"] - jobs) * 100 / FLEET["turbines"], 1)
    after = round((FLEET["turbines"] - FLEET["other_units_offline"]) * 100 / FLEET["turbines"], 1)
    return {"separate": separate, "bundled": bundled, "savings": savings, "crane": crane_saving,
            "travel": travel_saving, "parts": parts_saving, "avoided": avoided, "total_value": total_value,
            "roi": roi, "before": before, "after": after}


_GATE = ("> Synthetic planning evidence only. Draft approval queue only: no work order, schedule, crew "
         "assignment, or field instruction has been created in Dynamics or any other system.")


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class AssetMaintenanceForecastAgent(BasicAgent):
    """Predictive maintenance and asset health agent for a wind-farm fleet."""

    def __init__(self):
        self.name = "AssetMaintenanceForecastAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                __manifest__["description"] + " Always call it first for wind farm or turbine analysis: "
                "'I need immediate analysis on our wind farm turbines' uses maintenance_forecast; "
                "'show the bundled maintenance plan' or 'yes, bundle them' uses work_order_plan."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "maintenance_forecast",
                            "asset_health",
                            "budget_projection",
                            "work_order_plan",
                        ],
                        "description": (
                            "maintenance_forecast: the default; immediate fleet analysis with the critical "
                            "alert, additional risks and the bundling recommendation. asset_health: condition "
                            "triage by risk score. budget_projection: planned versus emergency repair funding. "
                            "work_order_plan: the bundled maintenance plan for the low-wind window as a draft "
                            "approval queue (cost comparison, savings, ROI, fleet availability)."
                        ),
                    },
                    "asset_id": {
                        "type": "string",
                        "description": "Optional turbine such as 'Unit 12'. Unknown names return an empty result, never invented data.",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation") or "maintenance_forecast"
        asset_id = kwargs.get("asset_id")
        if op == "maintenance_forecast":
            return self._maintenance_forecast(asset_id)
        elif op == "asset_health":
            return self._asset_health(asset_id)
        elif op == "budget_projection":
            return self._budget_projection(asset_id)
        elif op == "work_order_plan":
            return self._work_order_plan(asset_id)
        return f"**Error:** Unknown operation `{op}`."

    def _maintenance_forecast(self, asset_id=None) -> str:
        selected = _selected_assets(asset_id)
        lines = [
            "# Maintenance Forecast",
            "",
            f"Analyzing your {FLEET['turbines']} {FLEET['model']} turbines through {FLEET['telemetry']} (synthetic telemetry snapshot).",
            "",
        ]
        if not selected:
            lines.append("No matching synthetic asset was found.")
            lines.append("")
            lines.append(_GATE)
            return "\n".join(lines)
        ranked = sorted(selected.items(), key=lambda x: x[1]["risk_score"], reverse=True)
        unit, lead = ranked[0]
        lines.append(f"## Critical Alert - {unit}")
        lines.append(f"- **Risk Score:** {lead['risk_score']}/10 ({lead['risk_label']})")
        lines.append(f"- **Issue:** {lead['failure_mode']}")
        lines.append(f"- **Timeline:** {lead['days_to_failure']} days to failure")
        lines.append(f"- **Impact:** {_k(lead['emergency_cost'])} emergency cost vs {_k(_planned_cost(unit) // 1000 * 1000)} planned repair")
        if len(ranked) > 1:
            lines.append("")
            lines.append("## Additional Risks")
            for u, a in ranked[1:]:
                lines.append(f"- {u} ({a['risk_score']}/10) - {a['failure_mode']}, {a['days_to_failure']} days")
        if not asset_id:
            b = _bundle_numbers()
            lines.append("")
            lines.append(f"**Recommendation:** Bundle all {len(ASSETS)} units during the {BUNDLE_WINDOW['dates']} low-wind window")
            lines.append(f"- Save {_k(b['savings'] // 1000 * 1000)} on mobilization")
            lines.append(f"- Avoid {_k(lead['emergency_cost'])} catastrophic failure")
            lines.append(f"- Total investment: {_k(b['bundled'] // 1000 * 1000)}")
            lines.append("")
            lines.append("**Next step:** See the detailed bundled maintenance plan?")
        lines.append("")
        lines.append("> Synthetic planning evidence only. Confirm against live telemetry and engineering review before maintenance or field action.")
        return "\n".join(lines)

    def _asset_health(self, asset_id=None) -> str:
        selected = _selected_assets(asset_id)
        lines = [
            "# Asset Health Dashboard",
            "",
            f"**Fleet:** {FLEET['turbines']} {FLEET['model']} turbines; {len(ASSETS)} flagged by the synthetic risk model.",
            "",
            "| Turbine | Risk Score | Status | Failure Mode | Days to Failure |",
            "|---------|-----------|--------|--------------|-----------------|",
        ]
        for u, a in sorted(selected.items(), key=lambda x: x[1]["risk_score"], reverse=True):
            lines.append(f"| {u} | {a['risk_score']}/10 | {_status(a['risk_score'])} | {a['failure_mode']} | {a['days_to_failure']} |")
        if not selected:
            lines.append("| - | - | - | No matching synthetic asset was found. | - |")
        lines.append("")
        lines.append("Status rule: CRITICAL at 8.0 or above, WARNING from 5.0, WATCH below 5.0.")
        lines.append("")
        lines.append("> Advisory condition screening only; it is not a safety determination or authorization to operate.")
        return "\n".join(lines)

    def _budget_projection(self, asset_id=None) -> str:
        selected = _selected_assets(asset_id)
        lines = [
            "# Maintenance Budget Projection",
            "",
            "| Turbine | Planned Repair (stand-alone) | Emergency Cost if It Fails |",
            "|---------|------------------------------|----------------------------|",
        ]
        for u, a in sorted(selected.items(), key=lambda x: x[1]["risk_score"], reverse=True):
            lines.append(f"| {u} | ${_planned_cost(u):,} | ${a['emergency_cost']:,} |")
        if not selected:
            lines.append("| - | No matching synthetic asset was found. | - |")
        if not asset_id:
            b = _bundle_numbers()
            lines.append("")
            lines.append(f"**Reserve (bundled plan):** ${b['bundled']:,} versus ${b['separate']:,} as separate jobs.")
            lines.append(f"**Emergency exposure avoided on Unit 12:** ${b['avoided']:,}.")
        lines.append("")
        lines.append("> Synthetic planning estimate; finance and asset owners must validate and approve any commitment.")
        return "\n".join(lines)

    def _work_order_plan(self, asset_id=None) -> str:
        b = _bundle_numbers()
        work = " + ".join(f"{u} {a['repair']} ({a['duration_days']}d)" for u, a in ASSETS.items())
        lines = [
            f"Bundling saves {_k(b['savings'] // 1000 * 1000)} and maximizes efficiency.",
            "",
            "# Bundled Maintenance Plan",
            "",
            f"**Window:** {BUNDLE_WINDOW['dates']} ({BUNDLE_WINDOW['days']} days, {BUNDLE_WINDOW['forecast']})",
            f"**Work:** {work}",
            "",
            "| Turbine | Work | Crew | Dates |",
            "|---------|------|------|-------|",
        ]
        for u, a in ASSETS.items():
            lines.append(f"| {u} | {a['failure_mode']} repair ({a['duration_days']}d) | {a['crew']} | {a['dates']} |")
        lines += [
            "",
            "## Cost Comparison",
            "",
            "| Approach | Total Cost | Savings |",
            "|----------|-----------|---------|",
            f"| Separate Jobs | ${b['separate']:,} | - |",
            f"| Bundled Job | ${b['bundled']:,} | -${b['savings']:,} |",
            "",
            "## Savings Sources",
            f"- Single crane rental vs {len(ASSETS)} separate: -{_k(b['crane'])}",
            f"- Shared crew travel: -{_k(b['travel'])}",
            f"- Bulk parts discount ({MOBILIZATION['bulk_parts_discount_pct']}%): -{_k(b['parts'])}",
            "",
            "## ROI Summary",
            f"- Investment: ${b['bundled']:,}",
            f"- Avoided failure: ${b['avoided']:,}",
            f"- Bundling savings: ${b['savings']:,}",
            f"- Total value: ${b['total_value']:,}",
            f"- ROI: {b['roi']}%",
            "",
            f"**Outcome:** Fleet availability {b['before']}% -> {b['after']}%",
            "",
            "Ready for the asset owner to approve and schedule in Dynamics.",
            "",
            _GATE,
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = AssetMaintenanceForecastAgent()
    for op in ["maintenance_forecast", "asset_health", "budget_projection", "work_order_plan"]:
        print(f"\n{'='*60}")
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
