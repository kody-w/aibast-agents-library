---
name: "permit-license-management"
description: "Review a synthetic renewables permit portfolio: status, permits expiring soon, renewal calendar, the emergency renewal package, compliance gaps, and application status. Use for permit and license tracking or audit-readiness questions. The agent never submits, renews, amends, or represents approval of a permit, and never sends notices; authorized staff must review and use future authenticated filing tools. Always call it first: 'show me our permit status and any expiring soon' uses permit_inventory; 'start emergency renewals for the critical permits' uses renewal_plan (a prepared package; nothing is submitted or sent)."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "permit_license_management_agent.py"
  tool-name: "PermitLicenseManagementAgent"
  agent-sha256: "40d35799eb84340dd98c5cca3ac896c99401688ebfe2660ab2f7b4ef53ab40e5"
  version: "1.2.0"
  author: "AIBAST"
  tags: "permits, licenses, compliance, regulatory, energy, renewals"
---

# Permit License Management

Review a synthetic renewables permit portfolio: status, permits expiring soon, renewal calendar, the emergency renewal package, compliance gaps, and application status. Use for permit and license tracking or audit-readiness questions. The agent never submits, renews, amends, or represents approval of a permit, and never sends notices; authorized staff must review and use future authenticated filing tools. Always call it first: 'show me our permit status and any expiring soon' uses permit_inventory; 'start emergency renewals for the critical permits' uses renewal_plan (a prepared package; nothing is submitted or sent).

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "permit_inventory",
        "renewal_calendar",
        "compliance_gaps",
        "application_status",
        "renewal_plan"
      ],
      "description": "permit_inventory: the default; permit status, permits expiring soon and the critical permits (<30 days). renewal_calendar: renewal deadlines with days left and lead times. compliance_gaps: evidence requiring review, such as missed renewal lead times. application_status: already-submitted application tracking. renewal_plan: start or prepare emergency renewals for the critical permits (per-permit prepared action, investment, production protected, draft stakeholder alerts)."
    },
    "facility": {
      "type": "string",
      "description": "Optional facility name or substring used to filter the synthetic snapshot, e.g. 'Reno'."
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
   python3 scripts/run.py --json '{"operation": "<string>", "facility": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=40d35799eb84340dd98c5cca3ac896c99401688ebfe2660ab2f7b4ef53ab40e5 -->
```python
"""
Permit and License Management Agent for Energy sector.

Tracks permits and licenses across a renewables portfolio, computes days
left against a fixed snapshot date, flags critical renewals, prepares the
emergency renewal package, identifies compliance gaps, and monitors
application status for regulatory requirements.
"""

import sys
import os
import datetime
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/permit-license-management",
    "version": "1.2.0",
    "display_name": "Permit Management Agent",
    "description": "Review a synthetic renewables permit portfolio: status, permits expiring soon, renewal calendar, the emergency renewal package, compliance gaps, and application status. Use for permit and license tracking or audit-readiness questions. The agent never submits, renews, amends, or represents approval of a permit, and never sends notices; authorized staff must review and use future authenticated filing tools.",
    "author": "AIBAST",
    "tags": ["permits", "licenses", "compliance", "regulatory", "energy", "renewals"],
    "category": "energy",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Synthetic domain data (the demo default: a renewables permit portfolio)
# ---------------------------------------------------------------------------

AS_OF = "2026-03-02"  # fixed snapshot date; days left are computed from it, never from the clock

PORTFOLIO = {
    "active_permits": 240,
    "expiring_120_days": 63,
    "critical_days": 30,
    "renewal_investment_63": 2340000,
    "production_at_risk_63": 47000000,
}

# The critical permits (< 30 days left) in the snapshot. Renewal costs total $685,000; production $13.8M.
PERMITS = {
    "PRM-8101": {"facility": "Imperial Valley Solar", "type": "Air Quality", "authority": "County air pollution control district",
                 "expiration_date": "2026-03-20", "renewal_lead_days": 90, "renewal_cost": 185000,
                 "production_at_risk": 4200000,
                 "renewal_path": "Expedited air quality renewal application prepared, ready for you to submit"},
    "PRM-8102": {"facility": "Reno Wind Farm", "type": "Environmental", "authority": "State environmental protection division",
                 "expiration_date": "2026-03-24", "renewal_lead_days": 120, "renewal_cost": 140000,
                 "production_at_risk": 3100000,
                 "renewal_path": "Environmental permit vendor shortlisted (2-week turnaround); engagement request drafted"},
    "PRM-8103": {"facility": "Phoenix Solar", "type": "Water Use", "authority": "County water resources department",
                 "expiration_date": "2026-03-28", "renewal_lead_days": 60, "renewal_cost": 95000,
                 "production_at_risk": 2200000,
                 "renewal_path": "County approval fast-track request drafted"},
    "PRM-8104": {"facility": "Bakersfield Solar", "type": "Hazmat", "authority": "County environmental health department",
                 "expiration_date": "2026-03-30", "renewal_lead_days": 60, "renewal_cost": 80000,
                 "production_at_risk": 1600000,
                 "renewal_path": "Hazmat documentation compiled, ready to submit"},
    "PRM-8105": {"facility": "Tehachapi Wind", "type": "Avian Protection", "authority": "Federal wildlife agency",
                 "expiration_date": "2026-03-31", "renewal_lead_days": 90, "renewal_cost": 60000,
                 "production_at_risk": 1100000,
                 "renewal_path": "Monitoring report assembled for the renewal filing"},
    "PRM-8106": {"facility": "Palm Springs Wind", "type": "Noise Variance", "authority": "County planning department",
                 "expiration_date": "2026-03-31", "renewal_lead_days": 45, "renewal_cost": 45000,
                 "production_at_risk": 700000,
                 "renewal_path": "Variance renewal letter drafted"},
    "PRM-8107": {"facility": "Yuma Solar", "type": "Grading", "authority": "County building and grading office",
                 "expiration_date": "2026-03-31", "renewal_lead_days": 45, "renewal_cost": 40000,
                 "production_at_risk": 500000,
                 "renewal_path": "Grading plan resubmittal package prepared"},
    "PRM-8108": {"facility": "Mojave Storage", "type": "Fire Code", "authority": "County fire authority",
                 "expiration_date": "2026-03-31", "renewal_lead_days": 45, "renewal_cost": 40000,
                 "production_at_risk": 400000,
                 "renewal_path": "Fire code inspection request drafted"},
}

STAKEHOLDERS = ["Facility managers", "Legal"]

APPLICATIONS = {
    "APP-7101": {
        "permit_name": "Reno Wind Farm Repowering Environmental Review",
        "facility": "Reno Wind Farm",
        "submitted_date": "2025-11-12",
        "authority": "State environmental protection division",
        "status": "under_review",
        "expected_decision": "2026-05-15",
        "comments_received": 4,
    },
    "APP-7102": {
        "permit_name": "Imperial Valley Solar Phase 2 Conditional Use Permit",
        "facility": "Imperial Valley Solar",
        "submitted_date": "2026-01-20",
        "authority": "County planning commission",
        "status": "public_comment",
        "expected_decision": "2026-06-30",
        "comments_received": 12,
    },
    "APP-7103": {
        "permit_name": "Phoenix Solar Battery Storage Building Permit",
        "facility": "Phoenix Solar",
        "submitted_date": "2026-02-10",
        "authority": "County water resources department",
        "status": "submitted",
        "expected_decision": "2026-04-15",
        "comments_received": 0,
    },
}

REGULATORY_REQUIREMENTS = {
    "Air Quality": ["Dust control plan", "Annual emissions inventory", "Quarterly compliance reports"],
    "Environmental": ["Habitat monitoring", "Annual environmental report", "Mitigation plan updates"],
    "Water Use": ["Monthly water use reporting", "Annual allocation review", "Conservation plan"],
    "Hazmat": ["Hazardous materials business plan", "Annual inventory certification", "Emergency response plan"],
    "Avian Protection": ["Post-construction fatality monitoring", "Annual avian report", "Adaptive management plan"],
    "Noise Variance": ["Quarterly noise monitoring", "Community complaint log"],
    "Grading": ["Erosion control inspection", "Grading completion certification"],
    "Fire Code": ["Annual fire inspection", "Battery hazard mitigation analysis"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _days_left(expiration):
    as_of = datetime.date.fromisoformat(AS_OF)
    return (datetime.date.fromisoformat(expiration) - as_of).days


def _selected_permits(facility=None):
    if not facility:
        return PERMITS
    query = facility.casefold()
    return {pid: permit for pid, permit in PERMITS.items() if query in permit["facility"].casefold()}


def _by_days(selected):
    return sorted(selected.items(), key=lambda x: _days_left(x[1]["expiration_date"]))


def _m(value):
    return f"${value / 1_000_000:.1f}M"


def _risk(days):
    if days < PORTFOLIO["critical_days"]:
        return "CRITICAL"
    return "AT RISK"


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class PermitLicenseManagementAgent(BasicAgent):
    """Permit and license tracking and compliance management agent."""

    def __init__(self):
        self.name = "PermitLicenseManagementAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                __manifest__["description"] + " Always call it first: 'show me our permit status and any "
                "expiring soon' uses permit_inventory; 'start emergency renewals for the critical permits' "
                "uses renewal_plan (a prepared package; nothing is submitted or sent)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "permit_inventory",
                            "renewal_calendar",
                            "compliance_gaps",
                            "application_status",
                            "renewal_plan",
                        ],
                        "description": (
                            "permit_inventory: the default; permit status, permits expiring soon and the critical "
                            "permits (<30 days). renewal_calendar: renewal deadlines with days left and lead times. "
                            "compliance_gaps: evidence requiring review, such as missed renewal lead times. "
                            "application_status: already-submitted application tracking. renewal_plan: start or "
                            "prepare emergency renewals for the critical permits (per-permit prepared action, "
                            "investment, production protected, draft stakeholder alerts)."
                        ),
                    },
                    "facility": {
                        "type": "string",
                        "description": "Optional facility name or substring used to filter the synthetic snapshot, e.g. 'Reno'.",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation") or "permit_inventory"
        facility = kwargs.get("facility")
        if op == "permit_inventory":
            return self._permit_inventory(facility)
        elif op == "renewal_calendar":
            return self._renewal_calendar(facility)
        elif op == "compliance_gaps":
            return self._compliance_gaps(facility)
        elif op == "application_status":
            return self._application_status(facility)
        elif op == "renewal_plan":
            return self._renewal_plan(facility)
        return f"**Error:** Unknown operation `{op}`."

    def _permit_inventory(self, facility=None) -> str:
        p = PORTFOLIO
        selected = _selected_permits(facility)
        critical = [(pid, x) for pid, x in _by_days(selected) if _days_left(x["expiration_date"]) < p["critical_days"]]
        lines = [
            "# Permit & License Inventory",
            "",
            f"I've analyzed all {p['active_permits']} active permits across your facilities. You have "
            f"{p['expiring_120_days']} permits expiring in the next 120 days, including {len(PERMITS)} critical ones "
            "needing immediate attention.",
            "",
            f"## Critical Permits (<{p['critical_days']} Days) as of {AS_OF}",
            "",
            "| ID | Facility | Permit Type | Days Left | Risk |",
            "|----|----------|-------------|-----------|------|",
        ]
        for pid, x in critical:
            d = _days_left(x["expiration_date"])
            lines.append(f"| {pid} | {x['facility']} | {x['type']} | {d} | {_risk(d)} |")
        if not critical:
            lines.append("| - | No matching synthetic permit was found. | - | - | - |")
        lines.append("")
        lines.append(f"**Total Renewal Investment:** ${p['renewal_investment_63'] / 1_000_000:.2f}M across {p['expiring_120_days']} permits")
        lines.append(f"**Production at Risk:** ${p['production_at_risk_63'] // 1_000_000}M if permits lapse")
        lines.append("")
        lines.append("Source: [Synthetic D365 + SharePoint permit register]")
        lines.append("")
        lines.append("**Next step:** Should I prepare the emergency renewal package for the critical permits?")
        lines.append("")
        lines.append("> Synthetic register only. Verify status with the issuing authority before relying on it.")
        return "\n".join(lines)

    def _renewal_calendar(self, facility=None) -> str:
        lines = [
            "# Permit Renewal Calendar",
            "",
            f"Days left are computed from the snapshot date {AS_OF}.",
            "",
            "| Permit | Facility | Expiration | Days Left | Lead Time | Lead Time Status |",
            "|--------|----------|-----------|-----------|-----------|------------------|",
        ]
        for pid, x in _by_days(_selected_permits(facility)):
            d = _days_left(x["expiration_date"])
            status = "MISSED" if d < x["renewal_lead_days"] else "On track"
            lines.append(
                f"| {pid} {x['type']} | {x['facility']} | {x['expiration_date']} | {d} "
                f"| {x['renewal_lead_days']} days | {status} |"
            )
        lines.append("")
        lines.append("> Planning reminders only. No renewal, notice, or authority submission has been initiated.")
        return "\n".join(lines)

    def _compliance_gaps(self, facility=None) -> str:
        gaps = []
        for pid, x in _by_days(_selected_permits(facility)):
            d = _days_left(x["expiration_date"])
            if d < x["renewal_lead_days"]:
                gaps.append((pid, x, "renewal_lead_time_missed", "CRITICAL" if d < PORTFOLIO["critical_days"] else "HIGH",
                             f"{d} days left vs {x['renewal_lead_days']}-day lead time; at risk: "
                             + ", ".join(REGULATORY_REQUIREMENTS.get(x["type"], []))))
        if not gaps:
            return "# Compliance Gaps\n\nNo gaps appear in the selected synthetic records; this is not a legal compliance determination."
        lines = [
            "# Compliance Gap Analysis",
            "",
            f"**Total Gaps:** {len(gaps)} | **Critical:** {sum(1 for g in gaps if g[3] == 'CRITICAL')}",
            "",
            "| Permit | Facility | Gap Type | Severity | Detail |",
            "|--------|----------|----------|----------|--------|",
        ]
        for pid, x, gap, sev, detail in gaps:
            lines.append(f"| {pid} {x['type']} | {x['facility']} | {gap} | {sev} | {detail} |")
        lines.append("")
        lines.append("> Triage evidence only, not legal advice. Authorized permit staff must validate obligations and approve remediation.")
        return "\n".join(lines)

    def _application_status(self, facility=None) -> str:
        query = facility.casefold() if facility else None
        rows = [(aid, a) for aid, a in APPLICATIONS.items() if not query or query in a["facility"].casefold()]
        lines = [
            "# Permit Application Status",
            "",
            f"**Active Applications:** {len(rows)}",
            "",
            "| ID | Application | Facility | Authority | Submitted | Status | Decision Date | Comments |",
            "|----|-------------|----------|-----------|-----------|--------|--------------|----------|",
        ]
        for aid, a in rows:
            lines.append(
                f"| {aid} | {a['permit_name']} | {a['facility']} | {a['authority']} | {a['submitted_date']} "
                f"| {a['status']} | {a['expected_decision']} | {a['comments_received']} |"
            )
        lines.append("")
        lines.append("> Read-only synthetic tracking. The agent cannot submit, amend, withdraw, or approve an application.")
        return "\n".join(lines)

    def _renewal_plan(self, facility=None) -> str:
        selected = _selected_permits(facility)
        critical = [(pid, x) for pid, x in _by_days(selected) if _days_left(x["expiration_date"]) < PORTFOLIO["critical_days"]]
        invest = sum(x["renewal_cost"] for _, x in critical)
        protected = sum(x["production_at_risk"] for _, x in critical)
        lines = [
            f"Emergency renewal package prepared for all {len(critical)} critical permits, ready for your approval. "
            "Expedited processing requests and stakeholder alerts are drafted, not sent.",
            "",
            "# Emergency Renewal Plan",
            "",
            "| ID | Facility | Permit Type | Days Left | Prepared Action | Renewal Cost |",
            "|----|----------|-------------|-----------|-----------------|--------------|",
        ]
        for pid, x in critical:
            lines.append(
                f"| {pid} | {x['facility']} | {x['type']} | {_days_left(x['expiration_date'])} "
                f"| {x['renewal_path']} | ${x['renewal_cost']:,} |"
            )
        lines += [
            "",
            f"**Investment Required:** ${invest:,} for critical renewals",
            f"**Production Protected:** {_m(protected)} (combined facility capacity)",
            f"**Stakeholder Alerts (drafts for Teams and Outlook):** {', '.join(STAKEHOLDERS)}",
            "",
            "Draft alert: \"Critical permit renewals: " + str(len(critical)) + " permits expire within "
            + str(PORTFOLIO["critical_days"]) + " days. The renewal package is ready for approval; please confirm "
            "owners today.\"",
            "",
            "**Monitoring:** daily status review with executive escalation if a renewal slips (recommended cadence).",
            "",
            "Source: [Synthetic D365 vendor management + SharePoint]",
            "",
            "**Next step:** Would you like me to analyze the Reno Wind Farm permit to see what's needed?",
            "",
            "> Prepared for approval only. No application was submitted, no vendor was engaged, and no Teams or "
            "Outlook message was sent.",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = PermitLicenseManagementAgent()
    for op in ["permit_inventory", "renewal_plan", "renewal_calendar", "compliance_gaps", "application_status"]:
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
