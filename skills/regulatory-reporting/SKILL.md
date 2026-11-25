---
name: "regulatory-reporting"
description: "Review synthetic energy regulatory-report status, data-validation exceptions, submission tracking, and audit-readiness findings. Use for EPA, FERC, PHMSA, or state reporting preparation. The agent never files, certifies, signs, or transmits a report; an authorized regulatory owner must approve a source-backed package through future authenticated tools. Always use this tool for the quarterly EPA emissions report: 'prepare our quarterly EPA emissions report, pull the data' uses emissions_summary; 'generate the submission file and show me any compliance risks' uses prepare_submission (a draft package; nothing is uploaded or filed)."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "regulatory_reporting_agent.py"
  tool-name: "RegulatoryReportingAgent"
  agent-sha256: "c0045a249275152acee2683de879c34a478c52544868e0a592a7f7536c05a3e5"
  version: "1.1.0"
  author: "AIBAST"
  tags: "regulatory, reporting, epa, ferc, audit, compliance, energy"
---

# Regulatory Reporting

Review synthetic energy regulatory-report status, data-validation exceptions, submission tracking, and audit-readiness findings. Use for EPA, FERC, PHMSA, or state reporting preparation. The agent never files, certifies, signs, or transmits a report; an authorized regulatory owner must approve a source-backed package through future authenticated tools. Always use this tool for the quarterly EPA emissions report: 'prepare our quarterly EPA emissions report, pull the data' uses emissions_summary; 'generate the submission file and show me any compliance risks' uses prepare_submission (a draft package; nothing is uploaded or filed).

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "report_status",
        "data_validation",
        "submission_tracker",
        "audit_readiness",
        "emissions_summary",
        "prepare_submission"
      ],
      "description": "Choose emissions_summary to pull the quarterly emissions data for the EPA report (pollutant totals vs annual limits across all facilities), prepare_submission to generate the draft EPA CAMD submission file and list compliance risks, report_status for the reporting portfolio, data_validation for source-quality exceptions, submission_tracker for read-only filing state, or audit_readiness for open evidence gaps."
    },
    "report_id": {
      "type": "string",
      "description": "Optional synthetic report ID such as RPT-9006. Unknown IDs return a not-found message."
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
   python3 scripts/run.py --json '{"operation": "<string>", "report_id": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=c0045a249275152acee2683de879c34a478c52544868e0a592a7f7536c05a3e5 -->
```python
"""
Energy Regulatory Reporting Agent.

Manages regulatory report status tracking, data validation, submission
workflows, and audit readiness assessments for EPA, FERC, and state
regulatory filings.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/energy-regulatory-reporting",
    "version": "1.1.0",
    "display_name": "Regulatory Reporting Agent",
    "description": "Review synthetic energy regulatory-report status, data-validation exceptions, submission tracking, and audit-readiness findings. Use for EPA, FERC, PHMSA, or state reporting preparation. The agent never files, certifies, signs, or transmits a report; an authorized regulatory owner must approve a source-backed package through future authenticated tools.",
    "author": "AIBAST",
    "tags": ["regulatory", "reporting", "epa", "ferc", "audit", "compliance", "energy"],
    "category": "energy",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Synthetic domain data
# ---------------------------------------------------------------------------

REGULATORY_REPORTS = {
    "RPT-9001": {
        "name": "EPA GHG Reporting Program (Subpart C)",
        "authority": "EPA",
        "facility": "Riverside Generating Station",
        "reporting_period": "CY 2025",
        "deadline": "2026-03-31",
        "status": "in_progress",
        "data_quality_score": 87,
        "completeness_pct": 78,
        "assignee": "Environmental Compliance Team",
        "last_updated": "2026-03-10",
    },
    "RPT-9002": {
        "name": "FERC Form 1 Annual Report",
        "authority": "FERC",
        "facility": "Corporate (All Facilities)",
        "reporting_period": "CY 2025",
        "deadline": "2026-04-18",
        "status": "in_progress",
        "data_quality_score": 92,
        "completeness_pct": 65,
        "assignee": "Regulatory Affairs",
        "last_updated": "2026-03-12",
    },
    "RPT-9003": {
        "name": "TCEQ Annual Emissions Inventory",
        "authority": "State - Texas",
        "facility": "Bayshore Refinery",
        "reporting_period": "CY 2025",
        "deadline": "2026-03-31",
        "status": "submitted",
        "data_quality_score": 95,
        "completeness_pct": 100,
        "assignee": "Environmental Compliance Team",
        "last_updated": "2026-03-05",
    },
    "RPT-9004": {
        "name": "Colorado Air Quality Control Division Report",
        "authority": "State - Colorado",
        "facility": "Ridgeline Coal Station",
        "reporting_period": "CY 2025",
        "deadline": "2026-04-30",
        "status": "not_started",
        "data_quality_score": 0,
        "completeness_pct": 0,
        "assignee": "Environmental Compliance Team",
        "last_updated": None,
    },
    "RPT-9005": {
        "name": "EPA Toxics Release Inventory (TRI)",
        "authority": "EPA",
        "facility": "Bayshore Refinery",
        "reporting_period": "CY 2025",
        "deadline": "2026-07-01",
        "status": "in_progress",
        "data_quality_score": 74,
        "completeness_pct": 42,
        "assignee": "Health & Safety Team",
        "last_updated": "2026-02-28",
    },
    "RPT-9006": {
        "name": "PHMSA Annual Pipeline Safety Report",
        "authority": "PHMSA",
        "facility": "Northeast Corridor Pipeline",
        "reporting_period": "CY 2025",
        "deadline": "2026-03-15",
        "status": "overdue",
        "data_quality_score": 81,
        "completeness_pct": 90,
        "assignee": "Pipeline Operations",
        "last_updated": "2026-03-14",
    },
    "RPT-9007": {
        "name": "EPA CAMD Quarterly Emissions Report (Part 75) Q1",
        "authority": "EPA",
        "facility": "All 14 facilities",
        "reporting_period": "Q1 2026",
        "deadline": "2026-04-30",
        "status": "in_progress",
        "data_quality_score": 99.7,
        "completeness_pct": 100,
        "assignee": "Environmental Compliance Team",
        "last_updated": "2026-03-19",
    },
}

# Demo date for deadline arithmetic (no current-date dependence).
DEMO_DATE = "2026-03-19"

EMISSIONS_QUARTER = {
    "quarter": "Q1",
    "period": "Last Quarter (Q1 2026)",
    "facilities": 14,
    "facilities_within_limits": 14,
    "cems_data_availability_pct": 99.7,
    "pollutants": [
        {"pollutant": "CO2", "total": 8240000, "annual_limit": 35200000, "unit": "tons", "prior_year_quarter": 8890000},
        {"pollutant": "NOx", "total": 4187, "annual_limit": 18500, "unit": "tons", "prior_year_quarter": 4402},
        {"pollutant": "SO2", "total": 2943, "annual_limit": 12800, "unit": "tons", "prior_year_quarter": 3105},
        {"pollutant": "Mercury", "total": 142, "annual_limit": 620, "unit": "lbs", "prior_year_quarter": 151},
    ],
}

SUBMISSION_PACKAGE = {
    "report_id": "RPT-9007",
    "file_name": "EPA_Q1_Emissions_Report.xml",
    "schema": "EPA CAMD schema",
    "schema_check": "passed (synthetic validation)",
    "location": "SharePoint > Regulatory Filings",
    "manual_hours": 85,
    "agent_hours": 6,
    "labor_rate_per_hour": 105,
}

COMPLIANCE_RISKS = [
    {"item": "FERC Form 1", "report": "RPT-9002", "detail": "6 sections incomplete", "sections_incomplete": 6},
    {"item": "OSHA 300A Posting", "report": None, "detail": "3 facilities missing annual summaries", "facilities_missing": 3},
    {"item": "State Air Permits", "report": None, "detail": "2 renewals needed next quarter", "renewals_next_quarter": 2},
]

DATA_VALIDATION_RULES = {
    "emissions_data": {
        "rules": ["Non-negative values", "Year-over-year variance < 25%", "Mass balance check", "Unit conversion validation"],
        "source_systems": ["CEMS", "Fuel metering", "Production logs"],
    },
    "financial_data": {
        "rules": ["Reconciliation to GL", "Rate base validation", "Depreciation schedule check", "Intercompany elimination"],
        "source_systems": ["SAP", "PowerPlan", "Hyperion"],
    },
    "safety_data": {
        "rules": ["Incident classification verification", "Mileage data reconciliation", "Leak survey completeness"],
        "source_systems": ["PIMS", "GIS", "Inspection database"],
    },
}

AUDIT_FINDINGS = {
    "AUD-001": {"report": "RPT-9001", "finding": "Missing CEMS calibration records for Q3", "severity": "medium", "status": "open", "due_date": "2026-03-25"},
    "AUD-002": {"report": "RPT-9002", "finding": "Depreciation schedule mismatch with PowerPlan", "severity": "high", "status": "remediated", "due_date": "2026-03-15"},
    "AUD-003": {"report": "RPT-9005", "finding": "Threshold calculation methodology not documented", "severity": "low", "status": "open", "due_date": "2026-05-01"},
    "AUD-004": {"report": "RPT-9006", "finding": "Pipeline mileage discrepancy between GIS and PIMS", "severity": "high", "status": "open", "due_date": "2026-03-20"},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _days_until(deadline):
    """Days from the fixed demo date to a YYYY-MM-DD deadline."""
    import datetime
    return (datetime.date.fromisoformat(deadline) - datetime.date.fromisoformat(DEMO_DATE)).days


def _short_amount(value):
    """8240000 -> '8.24M'; 4187 -> '4,187'."""
    if value >= 1000000 and value % 100000 == 0:
        return f"{value / 1000000:.1f}M"
    if value >= 1000000:
        return f"{value / 1000000:.2f}M"
    return f"{value:,}"


def _selected_reports(report_id=None):
    if report_id:
        return {report_id: REGULATORY_REPORTS[report_id]} if report_id in REGULATORY_REPORTS else {}
    return REGULATORY_REPORTS


def _report_status(report_id=None):
    reports = []
    for rid, r in _selected_reports(report_id).items():
        reports.append({
            "id": rid, "name": r["name"], "authority": r["authority"],
            "facility": r["facility"], "deadline": r["deadline"],
            "status": r["status"], "completeness_pct": r["completeness_pct"],
            "data_quality": r["data_quality_score"], "assignee": r["assignee"],
        })
    reports.sort(key=lambda x: x["deadline"])
    overdue = sum(1 for r in reports if r["status"] == "overdue")
    submitted = sum(1 for r in reports if r["status"] == "submitted")
    return {"reports": reports, "total": len(reports), "overdue": overdue, "submitted": submitted}


def _data_validation(report_id=None):
    validations = []
    for rid, r in _selected_reports(report_id).items():
        if r["status"] in ("not_started",):
            continue
        issues = []
        if r["data_quality_score"] < 80:
            issues.append(f"Data quality score below threshold ({r['data_quality_score']}/100)")
        if r["completeness_pct"] < 100 and r["status"] != "submitted":
            issues.append(f"Data collection incomplete ({r['completeness_pct']}%)")
        validations.append({
            "report_id": rid, "name": r["name"],
            "quality_score": r["data_quality_score"],
            "completeness": r["completeness_pct"],
            "issues": issues, "passed": len(issues) == 0,
        })
    return {"validations": validations, "pass_rate": round(sum(1 for v in validations if v["passed"]) / len(validations) * 100, 1) if validations else 0}


def _submission_tracker(report_id=None):
    tracker = []
    for rid, r in _selected_reports(report_id).items():
        tracker.append({
            "id": rid, "name": r["name"], "authority": r["authority"],
            "deadline": r["deadline"], "status": r["status"],
            "last_updated": r["last_updated"] or "N/A",
            "assignee": r["assignee"],
        })
    tracker.sort(key=lambda x: x["deadline"])
    return {"submissions": tracker}


def _audit_readiness(report_id=None):
    findings_by_report = {}
    for aid, af in AUDIT_FINDINGS.items():
        rid = af["report"]
        if report_id and rid != report_id:
            continue
        if rid not in findings_by_report:
            findings_by_report[rid] = []
        findings_by_report[rid].append({
            "id": aid, "finding": af["finding"],
            "severity": af["severity"], "status": af["status"],
            "due_date": af["due_date"],
        })
    selected_findings = [af for af in AUDIT_FINDINGS.values() if not report_id or af["report"] == report_id]
    open_findings = sum(1 for af in selected_findings if af["status"] == "open")
    high_sev = sum(1 for af in selected_findings if af["severity"] == "high" and af["status"] == "open")
    return {"findings_by_report": findings_by_report, "total_findings": len(selected_findings),
            "open_findings": open_findings, "high_severity_open": high_sev}


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class RegulatoryReportingAgent(BasicAgent):
    """Regulatory reporting status and audit readiness agent."""

    def __init__(self):
        self.name = "RegulatoryReportingAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                __manifest__["description"]
                + " Always use this tool for the quarterly EPA emissions report: 'prepare our quarterly EPA "
                "emissions report, pull the data' uses emissions_summary; 'generate the submission file and show "
                "me any compliance risks' uses prepare_submission (a draft package; nothing is uploaded or filed)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "report_status",
                            "data_validation",
                            "submission_tracker",
                            "audit_readiness",
                            "emissions_summary",
                            "prepare_submission",
                        ],
                        "description": (
                            "Choose emissions_summary to pull the quarterly emissions data for the EPA report "
                            "(pollutant totals vs annual limits across all facilities), prepare_submission to "
                            "generate the draft EPA CAMD submission file and list compliance risks, report_status "
                            "for the reporting portfolio, data_validation for source-quality exceptions, "
                            "submission_tracker for read-only filing state, or audit_readiness for open evidence gaps."
                        ),
                    },
                    "report_id": {
                        "type": "string",
                        "description": "Optional synthetic report ID such as RPT-9006. Unknown IDs return a not-found message.",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation", "report_status")
        report_id = kwargs.get("report_id")
        if report_id and report_id not in REGULATORY_REPORTS:
            return (f"No synthetic report found for `{report_id}`. Known reports: "
                    + ", ".join(REGULATORY_REPORTS) + ".")
        if op == "emissions_summary":
            return self._emissions_summary()
        if op == "prepare_submission":
            return self._prepare_submission()
        if op == "report_status":
            return self._report_status(report_id)
        elif op == "data_validation":
            return self._data_validation(report_id)
        elif op == "submission_tracker":
            return self._submission_tracker(report_id)
        elif op == "audit_readiness":
            return self._audit_readiness(report_id)
        return f"**Error:** Unknown operation `{op}`."

    def _report_status(self, report_id=None) -> str:
        data = _report_status(report_id)
        lines = [
            "# Regulatory Report Status",
            "",
            f"**Total Reports:** {data['total']} | **Submitted:** {data['submitted']} | **Overdue:** {data['overdue']}",
            "",
            "| Report | Authority | Facility | Owner | Deadline | Status | Complete | Quality |",
            "|--------|-----------|----------|-------|----------|--------|---------|---------|",
        ]
        for r in data["reports"]:
            lines.append(
                f"| {r['name']} | {r['authority']} | {r['facility']} | {r['assignee']} "
                f"| {r['deadline']} | {r['status'].upper()} | {r['completeness_pct']}% | {r['data_quality']}/100 |"
            )
        lines.append("")
        lines.append("> Synthetic status snapshot. Confirm deadlines and filing state in the system of record.")
        return "\n".join(lines)

    def _data_validation(self, report_id=None) -> str:
        data = _data_validation(report_id)
        lines = [
            "# Data Validation Results",
            "",
            f"**Validation Pass Rate:** {data['pass_rate']}%",
            "",
            "| Report | Quality Score | Completeness | Issues | Passed |",
            "|--------|-------------|-------------|--------|--------|",
        ]
        for v in data["validations"]:
            passed = "YES" if v["passed"] else "NO"
            issue_str = "; ".join(v["issues"]) if v["issues"] else "None"
            lines.append(
                f"| {v['name']} | {v['quality_score']}/100 | {v['completeness']}% | {issue_str} | {passed} |"
            )
        lines.append("")
        lines.append("> Validation screening only. An authorized report owner must resolve and attest source evidence.")
        return "\n".join(lines)

    def _submission_tracker(self, report_id=None) -> str:
        data = _submission_tracker(report_id)
        lines = [
            "# Submission Tracker",
            "",
            "| Report | Authority | Owner | Deadline | Status | Last Updated |",
            "|--------|-----------|-------|----------|--------|-------------|",
        ]
        for s in data["submissions"]:
            lines.append(
                f"| {s['name']} | {s['authority']} | {s['assignee']} | {s['deadline']} "
                f"| {s['status'].upper()} | {s['last_updated']} |"
            )
        lines.append("")
        lines.append("> Read-only tracking. No regulator filing, certification, signature, or transmission has occurred.")
        return "\n".join(lines)

    def _audit_readiness(self, report_id=None) -> str:
        data = _audit_readiness(report_id)
        lines = [
            "# Audit Readiness Assessment",
            "",
            f"**Total Findings:** {data['total_findings']} | "
            f"**Open:** {data['open_findings']} | "
            f"**High Severity Open:** {data['high_severity_open']}",
            "",
        ]
        for rid, findings in data["findings_by_report"].items():
            rpt_name = REGULATORY_REPORTS.get(rid, {}).get("name", rid)
            lines.append(f"## {rpt_name}")
            lines.append("")
            lines.append("| Finding | Severity | Status | Due Date |")
            lines.append("|---------|----------|--------|----------|")
            for f in findings:
                lines.append(f"| {f['finding']} | {f['severity'].upper()} | {f['status'].upper()} | {f['due_date']} |")
            lines.append("")
        lines.append("> Readiness triage is not legal advice and cannot predict an audit outcome.")
        return "\n".join(lines)


    def _emissions_summary(self) -> str:
        q = EMISSIONS_QUARTER
        within = all(p["total"] <= p["annual_limit"] for p in q["pollutants"])
        compliant = "All plants are compliant with permit limits" if within and \
            q["facilities_within_limits"] == q["facilities"] else "Some plants exceed a permit limit"
        lines = [
            "# Emissions Summary - " + q["period"],
            "",
            f"I've compiled your quarterly emissions data across all {q['facilities']} facilities. {compliant} "
            f"and data quality is strong at {q['cems_data_availability_pct']}% uptime (CEMS data availability).",
            "",
            "| Pollutant | Total | Annual Limit | % of Limit |",
            "|-----------|-------|--------------|------------|",
        ]
        for p in q["pollutants"]:
            pct = round(p["total"] * 100 / p["annual_limit"], 1)
            lines.append(f"| {p['pollutant']} | {_short_amount(p['total'])} {p['unit']} | "
                         f"{_short_amount(p['annual_limit'])} {p['unit']} | {pct}% |")
        co2 = q["pollutants"][0]
        change = round((co2["total"] - co2["prior_year_quarter"]) * 100 / co2["prior_year_quarter"], 1)
        direction = "down" if change < 0 else "up"
        lines += [
            "",
            f"**Key Highlight:** CO2 emissions {direction} {abs(change)}% vs same quarter last year while "
            "maintaining generation capacity.",
            "",
            "Source: [Azure Compliance Manager + CEMS] (synthetic)",
            "",
            "> Synthetic emissions snapshot for report preparation; not a certified submission.",
            "",
            "Next: should I generate the EPA CAMD submission file?",
        ]
        return "\n".join(lines)

    def _prepare_submission(self) -> str:
        pkg = SUBMISSION_PACKAGE
        saved_hours = pkg["manual_hours"] - pkg["agent_hours"]
        saved = saved_hours * pkg["labor_rate_per_hour"]
        lines = [
            "# Draft EPA Submission Package",
            "",
            f"The EPA submission file is ready for your upload, and I've identified {len(COMPLIANCE_RISKS)} "
            "compliance risks that need attention in the next 30 days.",
            "",
            "**Submission Ready (draft):**",
            f"- {pkg['file_name']} generated (draft for {REGULATORY_REPORTS[pkg['report_id']]['name']})",
            f"- Validated against {pkg['schema']}: {pkg['schema_check']}",
            f"- Location: {pkg['location']} (pending your authorized upload)",
            "",
            "**Compliance Risks Identified:**",
        ]
        for r in COMPLIANCE_RISKS:
            due = ""
            if r["report"]:
                due = f", {_days_until(REGULATORY_REPORTS[r['report']]['deadline'])} days until deadline"
            lines.append(f"- {r['item']} - {r['detail']}{due}")
        lines += [
            "",
            f"**Automation Value:** This report took {pkg['agent_hours']} hours vs {pkg['manual_hours']} hours "
            f"manually, saving ${saved:,} in labor costs ({saved_hours} hours x ${pkg['labor_rate_per_hour']}/hour, "
            "synthetic estimate).",
            "",
            "Source: [Azure Compliance + SharePoint] (synthetic)",
            "",
            "> Draft package only. No regulator filing, certification, signature, upload, or transmission has occurred.",
            "",
            "Next: would you like me to assess what's needed to complete the FERC filing?",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = RegulatoryReportingAgent()
    for op in ["emissions_summary", "prepare_submission", "report_status", "data_validation",
               "submission_tracker", "audit_readiness"]:
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
