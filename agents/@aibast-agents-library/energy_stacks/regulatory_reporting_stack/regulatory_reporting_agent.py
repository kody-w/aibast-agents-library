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
    "version": "1.0.0",
    "display_name": "Energy Regulatory Reporting Agent",
    "description": "Manages regulatory report status, data validation, submission tracking, and audit readiness for EPA, FERC, and state filings.",
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
}

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

def _report_status():
    reports = []
    for rid, r in REGULATORY_REPORTS.items():
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


def _data_validation():
    validations = []
    for rid, r in REGULATORY_REPORTS.items():
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


def _submission_tracker():
    tracker = []
    for rid, r in REGULATORY_REPORTS.items():
        tracker.append({
            "id": rid, "name": r["name"], "authority": r["authority"],
            "deadline": r["deadline"], "status": r["status"],
            "last_updated": r["last_updated"] or "N/A",
        })
    tracker.sort(key=lambda x: x["deadline"])
    return {"submissions": tracker}


def _audit_readiness():
    findings_by_report = {}
    for aid, af in AUDIT_FINDINGS.items():
        rid = af["report"]
        if rid not in findings_by_report:
            findings_by_report[rid] = []
        findings_by_report[rid].append({
            "id": aid, "finding": af["finding"],
            "severity": af["severity"], "status": af["status"],
            "due_date": af["due_date"],
        })
    open_findings = sum(1 for af in AUDIT_FINDINGS.values() if af["status"] == "open")
    high_sev = sum(1 for af in AUDIT_FINDINGS.values() if af["severity"] == "high" and af["status"] == "open")
    return {"findings_by_report": findings_by_report, "total_findings": len(AUDIT_FINDINGS),
            "open_findings": open_findings, "high_severity_open": high_sev}


def _remediation_package():
    """Assemble the routable remediation work list.

    Read-only: every item is derived from an OPEN audit finding or a failed
    validation gate already in the data. Nothing is filed, assigned, or closed.
    """
    items = []
    for aid, af in AUDIT_FINDINGS.items():
        if af["status"] != "open":
            continue
        rid = af["report"]
        rpt = REGULATORY_REPORTS.get(rid, {})
        items.append({
            "owner": rpt.get("assignee", "Unassigned"),
            "item_id": aid,
            "report_id": rid,
            "report": rpt.get("name", rid),
            "source": "Audit finding",
            "action": af["finding"],
            "severity": af["severity"],
            "due_date": af["due_date"],
        })
    for v in _data_validation()["validations"]:
        if v["passed"]:
            continue
        rid = v["report_id"]
        rpt = REGULATORY_REPORTS.get(rid, {})
        for issue in v["issues"]:
            items.append({
                "owner": rpt.get("assignee", "Unassigned"),
                "item_id": rid,
                "report_id": rid,
                "report": rpt.get("name", rid),
                "source": "Validation gate",
                "action": issue,
                "severity": "n/a",
                "due_date": rpt.get("deadline", "N/A"),
            })

    packages = {}
    for it in items:
        packages.setdefault(it["owner"], []).append(it)
    for owner in packages:
        packages[owner].sort(key=lambda x: (x["due_date"], 0 if x["source"] == "Audit finding" else 1))
    ordered = sorted(
        packages.items(),
        key=lambda kv: (min(i["due_date"] for i in kv[1]), kv[0]),
    )
    return {
        "packages": ordered,
        "total_items": len(items),
        "owners": len(ordered),
        "open_findings": sum(1 for i in items if i["source"] == "Audit finding"),
        "failed_gates": sum(1 for i in items if i["source"] == "Validation gate"),
        "earliest_due": min((i["due_date"] for i in items), default="N/A"),
    }


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class RegulatoryReportingAgent(BasicAgent):
    """Regulatory reporting status and audit readiness agent."""

    def __init__(self):
        self.name = "@aibast-agents-library/energy-regulatory-reporting"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
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
                            "remediation_package",
                        ],
                        "description": "The regulatory reporting operation to perform.",
                    },
                    "report_id": {
                        "type": "string",
                        "description": "Optional report ID to filter results.",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation", "report_status")
        if op == "report_status":
            return self._report_status()
        elif op == "data_validation":
            return self._data_validation()
        elif op == "submission_tracker":
            return self._submission_tracker()
        elif op == "audit_readiness":
            return self._audit_readiness()
        elif op == "remediation_package":
            return self._remediation_package()
        return f"**Error:** Unknown operation `{op}`."

    def _report_status(self) -> str:
        data = _report_status()
        lines = [
            "# Regulatory Report Status",
            "",
            f"**Total Reports:** {data['total']} | **Submitted:** {data['submitted']} | **Overdue:** {data['overdue']}",
            "",
            "| Report | Authority | Facility | Deadline | Status | Complete | Quality |",
            "|--------|-----------|----------|----------|--------|---------|---------|",
        ]
        for r in data["reports"]:
            lines.append(
                f"| {r['name']} | {r['authority']} | {r['facility']} "
                f"| {r['deadline']} | {r['status'].upper()} | {r['completeness_pct']}% | {r['data_quality']}/100 |"
            )
        return "\n".join(lines)

    def _data_validation(self) -> str:
        data = _data_validation()
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
        return "\n".join(lines)

    def _submission_tracker(self) -> str:
        data = _submission_tracker()
        lines = [
            "# Submission Tracker",
            "",
            "| Report | Authority | Deadline | Status | Last Updated |",
            "|--------|-----------|----------|--------|-------------|",
        ]
        for s in data["submissions"]:
            lines.append(
                f"| {s['name']} | {s['authority']} | {s['deadline']} "
                f"| {s['status'].upper()} | {s['last_updated']} |"
            )
        return "\n".join(lines)

    def _audit_readiness(self) -> str:
        data = _audit_readiness()
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
        return "\n".join(lines)

    def _remediation_package(self) -> str:
        data = _remediation_package()
        lines = [
            "# Remediation Package",
            "",
            f"**Work Items:** {data['total_items']} | "
            f"**Owners:** {data['owners']} | "
            f"**Open Findings:** {data['open_findings']} | "
            f"**Failed Gates:** {data['failed_gates']} | "
            f"**Earliest Due:** {data['earliest_due']}",
            "",
        ]
        for owner, work in data["packages"]:
            noun = "item" if len(work) == 1 else "items"
            lines.append(f"## {owner} ({len(work)} {noun})")
            lines.append("")
            lines.append("| Item | Report | Source | Action | Severity | Due Date |")
            lines.append("|------|--------|--------|--------|----------|----------|")
            for it in work:
                lines.append(
                    f"| {it['item_id']} | {it['report']} | {it['source']} "
                    f"| {it['action']} | {it['severity'].upper()} | {it['due_date']} |"
                )
            lines.append("")
        lines.append(
            "Routing, assignment, and closure are the named owner's action. "
            "This package is a read-only work list assembled from the open audit "
            "findings and failed validation gates already on record."
        )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = RegulatoryReportingAgent()
    for op in ["report_status", "data_validation", "submission_tracker", "audit_readiness", "remediation_package"]:
        print(f"\n{'='*60}")
        print(f"Operation: {op}")
        print("=" * 60)
        print(agent.perform(operation=op))
