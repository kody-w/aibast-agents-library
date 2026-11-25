---
name: "reporting-package-validation"
description: "Always call this tool for the fictional Proseware Holdings June 2026 month-end reporting package: what files were received and where each came from, integrity checks before anyone looks at the numbers, how each division did against budget and which variances need an explanation, whether the driver bridge reconciles from budget to actual, routing the exceptions to their owners, and drafting the executive summary for the leadership pack. Call it right away; the package is already loaded and every operation has demo defaults. It never posts journals, edits submissions, releases the package, or sends commentary."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "reporting_package_validation_agent.py"
  tool-name: "ReportingPackageValidationAgent"
  agent-sha256: "3c507a1c59259594931f9ba26214ed7241297cf77ea64c5ee948590293373c50"
  version: "1.0.0"
  author: "AIBAST"
  tags: "finance, fp-and-a, month-end-close, variance-analysis, reporting-validation"
---

# Reporting Package Validation

Always call this tool for the fictional Proseware Holdings June 2026 month-end reporting package: what files were received and where each came from, integrity checks before anyone looks at the numbers, how each division did against budget and which variances need an explanation, whether the driver bridge reconciles from budget to actual, routing the exceptions to their owners, and drafting the executive summary for the leadership pack. Call it right away; the package is already loaded and every operation has demo defaults. It never posts journals, edits submissions, releases the package, or sends commentary.

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "package_intake",
        "integrity_checks",
        "variance_analysis",
        "driver_reconciliation",
        "exception_queue",
        "executive_summary"
      ],
      "description": "package_intake for the files received and their source lineage; integrity_checks for completeness, missing versus zero, tie-out and formula checks; variance_analysis for division actual versus budget and which variances need an explanation; driver_reconciliation for the budget-to-actual driver bridge; exception_queue to route the exceptions to owners; executive_summary for the draft leadership commentary."
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
   python3 scripts/run.py --json '{"operation": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=3c507a1c59259594931f9ba26214ed7241297cf77ea64c5ee948590293373c50 -->
```python
"""
Reporting Package Validation Agent

Read-only month-end reporting support for a finance (FP&A) team, built on a fixed synthetic June close package for
the fictional Proseware Holdings: file intake with source lineage, integrity checks that tell missing data from a
reported zero, division variance against budget with explanation thresholds, a budget-to-actual driver bridge
reconciliation, an owner-routed exception queue, and a draft executive summary. The agent never posts a journal,
changes a submission, releases the package, or sends commentary; every output is a draft for the finance owner.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/reporting-package-validation",
    "version": "1.0.0",
    "display_name": "Reporting Package Validation Agent",
    "description": "Validate a month-end reporting package before anyone builds the executive pack: file intake with source lineage, integrity checks that separate missing data from a reported zero, division variance against budget with explanation thresholds, driver bridge reconciliation, an owner-routed exception queue, and a draft executive summary. The agent is read-only; it never posts a journal, edits a submission, releases the package, or sends commentary.",
    "author": "AIBAST",
    "tags": ["finance", "fp-and-a", "month-end-close", "variance-analysis", "reporting-validation"],
    "category": "financial_services",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Synthetic data (June 2026 close package; amounts in USD thousands; every figure is fictional)
# ---------------------------------------------------------------------------

PACKAGE = {"id": "PKG-2026-06", "org": "Proseware Holdings", "period": "June 2026", "metric": "Operating income",
           "unit": "$K", "release_target": "Workday 5"}

FILES = [
    {"id": "FILE-01", "name": "Industrial division submission", "source": "General ledger extract", "received": "Jul 2 09:14", "checksum": "a41f09"},
    {"id": "FILE-02", "name": "Consumer division submission", "source": "General ledger extract", "received": "Jul 2 10:02", "checksum": "7c2be1"},
    {"id": "FILE-03", "name": "Services division submission", "source": "Planning system export", "received": "Jul 2 11:40", "checksum": "e90d35"},
    {"id": "FILE-04", "name": "Outdoor division submission", "source": "Planning system export", "received": "Jul 2 13:05", "checksum": "52aa7f"},
    {"id": "FILE-05", "name": "Consolidated summary", "source": "Consolidation workbook", "received": "Jul 2 15:22", "checksum": "b8e613"},
    {"id": "FILE-06", "name": "Driver bridge workbook", "source": "FP&A model", "received": "Jul 2 16:10", "checksum": "0f4c92"},
]

DIVISIONS = ["Industrial", "Consumer", "Services", "Outdoor"]
SCENARIOS = ["Actual", "Budget", "Forecast"]

# None = not submitted (missing); 0 = a reported zero. Values in $K.
CELLS = {
    "Industrial": {"Actual": 4820, "Budget": 4500, "Forecast": 4900},
    "Consumer": {"Actual": 3140, "Budget": 3400, "Forecast": 3200},
    "Services": {"Actual": 1960, "Budget": 1900, "Forecast": 0},
    "Outdoor": {"Actual": 880, "Budget": 1000, "Forecast": None},
}
PRIOR_FORECAST = {"Services": 1950}
SCENARIO_LABELS = [{"raw": "Bud", "normalized": "Budget", "file": "FILE-03"},
                   {"raw": "FCST", "normalized": "Forecast", "file": "FILE-04"}]
CONSOLIDATED_ACTUAL = 10850

BRIDGE = [
    {"driver": "Volume", "amount": 410},
    {"driver": "Price", "amount": 180},
    {"driver": "Mix", "amount": -230},
    {"driver": "Input cost", "amount": -320},
    {"driver": "Foreign exchange", "amount": -80},
]
BRIDGE_TOLERANCE = 25

VARIANCE_ABS = 250   # $K
VARIANCE_PCT = 5     # percent; explanation required when both thresholds are met

OWNERS = {
    "Industrial": "Industrial division controller",
    "Consumer": "Consumer division controller",
    "Services": "Services FP&A analyst",
    "Outdoor": "Outdoor division controller",
    "Consolidation": "Consolidation lead",
    "Bridge": "FP&A manager",
}

_GATE = (
    "Synthetic finance review support only. Every figure is fictional. No journal was posted, no submission was "
    "changed, the package was not released, and no commentary was sent."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _k(v):
    return f"${v:,}K"


def _signed(v):
    return f"+{_k(v)}" if v >= 0 else f"-{_k(-v)}"


def _total(scenario):
    t = 0
    for d in DIVISIONS:
        v = CELLS[d][scenario]
        if v is not None:
            t += v
    return t


def _missing():
    out = []
    for d in DIVISIONS:
        for s in SCENARIOS:
            if CELLS[d][s] is None:
                out.append(f"{d} {s}")
    return out


def _zeros():
    out = []
    for d in DIVISIONS:
        for s in SCENARIOS:
            if CELLS[d][s] == 0:
                out.append({"cell": f"{d} {s}", "division": d, "prior": PRIOR_FORECAST.get(d, 0)})
    return out


def _variances():
    rows = []
    for d in DIVISIONS:
        a = CELLS[d]["Actual"]
        b = CELLS[d]["Budget"]
        v = a - b
        pct = v * 100 / b
        flag = abs(v) >= VARIANCE_ABS and abs(pct) >= VARIANCE_PCT
        rows.append({"division": d, "actual": a, "budget": b, "var": v, "pct": pct, "flag": flag})
    return rows


def _bridge():
    budget = _total("Budget")
    actual = _total("Actual")
    explained = 0
    for b in BRIDGE:
        explained += b["amount"]
    residual = actual - (budget + explained)
    return {"budget": budget, "actual": actual, "explained": explained, "implied": budget + explained, "residual": residual}


def _checks():
    expected = len(DIVISIONS) * len(SCENARIOS)
    missing = _missing()
    zeros = _zeros()
    div_sum = _total("Actual")
    br = _bridge()
    return [
        {"check": "Source lineage stamped on every file", "result": "Pass", "evidence": f"{len(FILES)} of {len(FILES)} files"},
        {"check": "Expected cells received", "result": "Blocking" if missing else "Pass",
         "evidence": f"{expected - len(missing)} of {expected}" + (f"; missing: {', '.join(missing)}" if missing else "")},
        {"check": "Reported zeros confirmed", "result": "Advisory" if zeros else "Pass",
         "evidence": "; ".join(f"{z['cell']} reported as 0 (prior {_k(z['prior'])})" for z in zeros) or "None"},
        {"check": "Division sum ties to consolidated", "result": "Pass" if div_sum == CONSOLIDATED_ACTUAL else "Blocking",
         "evidence": f"{_k(div_sum)} vs {_k(CONSOLIDATED_ACTUAL)} (difference {_k(abs(CONSOLIDATED_ACTUAL - div_sum))})"},
        {"check": "Scenario labels normalized", "result": "Pass",
         "evidence": ", ".join(f"{x['raw']} -> {x['normalized']}" for x in SCENARIO_LABELS)},
        {"check": "Driver bridge reconciles", "result": "Pass" if abs(br["residual"]) <= BRIDGE_TOLERANCE else "Advisory",
         "evidence": f"Residual {_k(br['residual'])} vs tolerance {_k(BRIDGE_TOLERANCE)}"},
        {"check": "Prior-period actuals unchanged", "result": "Pass", "evidence": "May 2026 actuals match the closed period"},
        {"check": "Formula links intact", "result": "Pass", "evidence": "No broken links in FILE-05 or FILE-06"},
    ]


def _exceptions():
    ex = []
    for m in _missing():
        d = m.split(" ")[0]
        ex.append({"type": "Blocking", "item": f"{m} not submitted", "owner": OWNERS[d], "due": "Workday 3"})
    div_sum = _total("Actual")
    if div_sum != CONSOLIDATED_ACTUAL:
        ex.append({"type": "Blocking", "item": f"Consolidated total off by {_k(abs(CONSOLIDATED_ACTUAL - div_sum))}",
                   "owner": OWNERS["Consolidation"], "due": "Workday 3"})
    for z in _zeros():
        ex.append({"type": "Advisory", "item": f"{z['cell']} reported as 0 (prior {_k(z['prior'])}); confirm intended",
                   "owner": OWNERS[z["division"]], "due": "Workday 4"})
    br = _bridge()
    if abs(br["residual"]) > BRIDGE_TOLERANCE:
        ex.append({"type": "Advisory", "item": f"Bridge residual {_k(br['residual'])} unexplained",
                   "owner": OWNERS["Bridge"], "due": "Workday 4"})
    for v in _variances():
        if v["flag"]:
            ex.append({"type": "Explanation", "item": f"{v['division']} {_signed(v['var'])} ({v['pct']:+.1f}%) vs budget",
                       "owner": OWNERS[v["division"]], "due": "Workday 4"})
    return ex


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

OPERATIONS = [
    "package_intake", "integrity_checks", "variance_analysis", "driver_reconciliation", "exception_queue",
    "executive_summary",
]


class ReportingPackageValidationAgent(BasicAgent):
    """Month-end reporting package validation support (read-only, synthetic)."""

    def __init__(self):
        self.name = "ReportingPackageValidationAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                "Always call this tool for the fictional Proseware Holdings June 2026 month-end reporting package: "
                "what files were received and where each came from, integrity checks before anyone looks at the "
                "numbers, how each division did against budget and which variances need an explanation, whether "
                "the driver bridge reconciles from budget to actual, routing the exceptions to their owners, and "
                "drafting the executive summary for the leadership pack. Call it right away; the package is already "
                "loaded and every operation has demo defaults. It never posts journals, edits submissions, releases "
                "the package, or sends commentary."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": list(OPERATIONS),
                        "description": (
                            "package_intake for the files received and their source lineage; integrity_checks for "
                            "completeness, missing versus zero, tie-out and formula checks; variance_analysis for "
                            "division actual versus budget and which variances need an explanation; "
                            "driver_reconciliation for the budget-to-actual driver bridge; exception_queue to route "
                            "the exceptions to owners; executive_summary for the draft leadership commentary."
                        ),
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation", "package_intake")
        handlers = {
            "package_intake": self._package_intake,
            "integrity_checks": self._integrity_checks,
            "variance_analysis": self._variance_analysis,
            "driver_reconciliation": self._driver_reconciliation,
            "exception_queue": self._exception_queue,
            "executive_summary": self._executive_summary,
        }
        handler = handlers.get(op)
        if not handler:
            return f"**Error:** Unknown operation `{op}`. Operations: {', '.join(OPERATIONS)}."
        return handler()

    def _package_intake(self) -> str:
        p = PACKAGE
        expected = len(DIVISIONS) * len(SCENARIOS)
        missing = _missing()
        out = [
            f"# Package Intake - {p['id']} ({p['period']})",
            "",
            f"**Organization:** {p['org']} | **Metric:** {p['metric']} ({p['unit']}) | **Release target:** {p['release_target']}",
            "",
            "| File | Content | Source | Received | Checksum |",
            "|------|---------|--------|----------|----------|",
        ]
        for f in FILES:
            out.append(f"| {f['id']} | {f['name']} | {f['source']} | {f['received']} | {f['checksum']} |")
        out += [
            "",
            f"**{len(FILES)} files received**, lineage frozen for each. Division cells: {expected - len(missing)} of "
            f"{expected} expected ({len(DIVISIONS)} divisions x {len(SCENARIOS)} scenarios).",
            "",
            "Next: run the integrity checks before anyone reads the numbers.",
            "",
            f"> {_GATE}",
        ]
        return "\n".join(out)

    def _integrity_checks(self) -> str:
        checks = _checks()
        n_pass = len([c for c in checks if c["result"] == "Pass"])
        n_block = len([c for c in checks if c["result"] == "Blocking"])
        n_adv = len([c for c in checks if c["result"] == "Advisory"])
        out = [
            f"# Integrity Checks - {PACKAGE['id']}",
            "",
            f"**{n_pass} pass, {n_block} blocking, {n_adv} advisory** of {len(checks)} checks.",
            "",
            "| Check | Result | Evidence |",
            "|-------|--------|----------|",
        ]
        for c in checks:
            out.append(f"| {c['check']} | {c['result']} | {c['evidence']} |")
        out += [
            "",
            "A missing cell is not a zero: Outdoor Forecast was never submitted, while Services Forecast was "
            "reported as 0 and needs confirmation.",
            "The package cannot be released while blocking checks are open.",
            "",
            f"> {_GATE}",
        ]
        return "\n".join(out)

    def _variance_analysis(self) -> str:
        rows = _variances()
        ta = _total("Actual")
        tb = _total("Budget")
        out = [
            f"# Actual vs Budget - {PACKAGE['metric']}, {PACKAGE['period']}",
            "",
            "| Division | Actual | Budget | Variance | Variance % | Explanation |",
            "|----------|--------|--------|----------|------------|-------------|",
        ]
        flagged = []
        for r in rows:
            need = "Required" if r["flag"] else "Not required"
            if r["flag"]:
                flagged.append(r["division"])
            out.append(f"| {r['division']} | {_k(r['actual'])} | {_k(r['budget'])} | {_signed(r['var'])} | "
                       f"{r['pct']:+.1f}% | {need} |")
        out.append(f"| **Total** | **{_k(ta)}** | **{_k(tb)}** | **{_signed(ta - tb)}** | | |")
        out += [
            "",
            f"**Rule:** explanation required when a variance is at least {_k(VARIANCE_ABS)} and {VARIANCE_PCT}% of budget.",
            f"**Read:** the total is on budget, but {len(flagged)} divisions need explanations "
            f"({', '.join(flagged)}); their swings offset each other in the consolidated view.",
            "",
            f"> {_GATE}",
        ]
        return "\n".join(out)

    def _driver_reconciliation(self) -> str:
        br = _bridge()
        out = [
            f"# Driver Bridge - Budget to Actual, {PACKAGE['period']}",
            "",
            "| Step | Amount |",
            "|------|--------|",
            f"| Budget operating income | {_k(br['budget'])} |",
        ]
        for b in BRIDGE:
            out.append(f"| {b['driver']} | {_signed(b['amount'])} |")
        out += [
            f"| Bridge-implied actual | {_k(br['implied'])} |",
            f"| Reported actual (division sum) | {_k(br['actual'])} |",
            f"| **Unexplained residual** | **{_signed(br['residual'])}** |",
            "",
        ]
        if abs(br["residual"]) > BRIDGE_TOLERANCE:
            out.append(f"**Does not reconcile:** the residual of {_k(br['residual'])} exceeds the {_k(BRIDGE_TOLERANCE)} "
                       f"tolerance. Route to the {OWNERS['Bridge']} to find the missing driver.")
        else:
            out.append("**Reconciles** within tolerance.")
        out += ["", f"> {_GATE}"]
        return "\n".join(out)

    def _exception_queue(self) -> str:
        ex = _exceptions()
        out = [
            f"# Exception Queue - {PACKAGE['id']}",
            "",
            "| ID | Type | Exception | Owner | Due |",
            "|----|------|-----------|-------|-----|",
        ]
        n = 0
        for e in ex:
            n += 1
            out.append(f"| EX-{n:02d} | {e['type']} | {e['item']} | {e['owner']} | {e['due']} |")
        n_block = len([e for e in ex if e["type"] == "Blocking"])
        n_adv = len([e for e in ex if e["type"] == "Advisory"])
        n_exp = len([e for e in ex if e["type"] == "Explanation"])
        out += [
            "",
            f"**{len(ex)} exceptions:** {n_block} blocking, {n_adv} advisory, {n_exp} explanations. Release stays on "
            f"hold until the {n_block} blocking items clear.",
            "Owner requests are drafted for review; none has been sent.",
            "",
            f"> {_GATE}",
        ]
        return "\n".join(out)

    def _executive_summary(self) -> str:
        ta = _total("Actual")
        tb = _total("Budget")
        rows = _variances()
        ex = _exceptions()
        n_block = len([e for e in ex if e["type"] == "Blocking"])
        parts = []
        for r in rows:
            parts.append(f"{r['division']} {_signed(r['var'])}")
        out = [
            f"# Executive Summary - DRAFT ({PACKAGE['period']})",
            "",
            f"**Headline:** {PACKAGE['metric'].lower()} of {_k(ta)} against a {_k(tb)} budget "
            f"({_signed(ta - tb)}); on budget overall.",
            f"**Under the surface:** {'; '.join(parts)}. Industrial volume and price gains offset Consumer mix and "
            "input-cost pressure.",
            f"**Watch items:** Outdoor forecast not yet submitted; bridge residual {_k(_bridge()['residual'])} under review.",
            "",
            f"Status: Draft - not released. {n_block} blocking exceptions must clear and the FP&A manager must sign "
            "off before this commentary enters the leadership pack.",
            "",
            f"> {_GATE}",
        ]
        return "\n".join(out)


if __name__ == "__main__":
    agent = ReportingPackageValidationAgent()
    for op in OPERATIONS:
        print("=" * 60)
        print(agent.perform(operation=op))
        print()
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
