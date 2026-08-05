#!/usr/bin/env python3
"""Generate a reference architecture for every entry in the library.

The AIBAST architecture slide is as much a format as the demo recording is:
four columns — Knowledge, Processing, User Interface, Reporting — over a Tools
band and a Supporting Features band, with a numbered request flow running
through them. Every solution gets one drawn by hand today.

It does not have to be drawn by hand. The four columns are exactly the four
things a RAPP manifest already declares: what it reads, what it does, where the
operator meets it, and what it leaves behind. So the architecture is derived,
the same way the one-pager and the walkthrough are.

Deterministic. No model, no network. Where a system cannot be classified from
its name it lands in Knowledge with its own name rather than being invented
into a category it may not belong to — a wrong box on an architecture is worse
than an unsorted one, because it looks decided.

Output: data/architectures.json  (aibast-architecture/1.0)

Usage:
    python3 scripts/build_architecture.py
    python3 scripts/build_architecture.py --only contract-review-agent
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_FILE = REPO_ROOT / "data" / "architectures.json"

SCHEMA = "aibast-architecture/1.0"
FORMAT_VERSION = "1.0.0"

# Which column a named system belongs in. Matching is on the name because that
# is all the manifest gives us; anything unmatched is reported, never guessed.
SURFACE = {
    "teams": ("Microsoft Teams", "teams"),
    "outlook": ("Copilot in Outlook", "outlook"),
    "word": ("Office Agent with Word", "word"),
    "excel": ("Office Agent with Excel", "excel"),
    "powerpoint": ("Office Agent with PowerPoint", "powerpoint"),
    "copilot studio": ("Microsoft Copilot Studio", "copilot"),
    "m365 copilot": ("Microsoft 365 Copilot", "copilot"),
    "microsoft 365": ("Microsoft 365", "copilot"),
    "power apps": ("Power Apps", "powerapps"),
}
KNOWLEDGE = {
    "dynamics 365": ("Dynamics 365", "d365"),
    "dataverse": ("Dataverse", "dataverse"),
    "sharepoint": ("SharePoint", "sharepoint"),
    "onedrive": ("OneDrive", "sharepoint"),
    "sap": ("SAP", "generic"),
    "workday": ("Workday", "generic"),
    "servicenow": ("ServiceNow", "generic"),
    "salesforce": ("Salesforce", "generic"),
    "sql": ("Azure SQL", "azure"),
    "cosmos": ("Azure Cosmos DB", "azure"),
    "fabric": ("Microsoft Fabric", "fabric"),
    "azure ai search": ("Azure AI Search", "azure"),
    "blob": ("Azure Blob Storage", "azure"),
    "iot": ("Azure IoT Hub", "azure"),
    "graph": ("Microsoft Graph", "graph"),
    "viva": ("Viva", "generic"),
    "erp": ("ERP system", "d365"),
    "crm": ("CRM system", "d365"),
}
REPORTING = {
    "power bi": ("Power BI", "powerbi"),
    "powerbi": ("Power BI", "powerbi"),
    "purview": ("Purview", "purview"),
    "application insights": ("Application Insights", "azure"),
}
AUTOMATION = {
    "power automate": ("Power Automate", "flow"),
    "logic apps": ("Azure Logic Apps", "azure"),
    "functions": ("Azure Functions", "azure"),
}

# The request flow, in the order the reference slide numbers it.
FLOW = [
    "Natural language input",
    "Preliminary checks including responsible AI checks and security measures",
    ("Formulates a plan comprised of multiple actions including context and "
     "tool selection, function matching and parameter determination, tool "
     "initiation, then result analysis and response formulation."),
    "NL response after guideline checks",
    "Action taken in the system of record",
    "Feedback",
]


def classify(name: str):
    low = name.lower()
    for table, column in ((SURFACE, "interface"), (REPORTING, "reporting"),
                          (AUTOMATION, "automation"), (KNOWLEDGE, "knowledge")):
        for key, (label, glyph) in table.items():
            if key in low:
                return column, label, glyph
    return None, name, "generic"


def build(entry: dict) -> dict:
    systems = list(dict.fromkeys(
        (entry.get("featured_tools") or []) + (entry.get("requires") or [])
        + (entry.get("built_with") or [])))

    knowledge, interface, reporting, automation, unclassified = [], [], [], [], []
    for s in systems:
        column, label, glyph = classify(s)
        item = {"label": label, "glyph": glyph, "from": s}
        if column == "knowledge":
            knowledge.append(item)
        elif column == "interface":
            interface.append(item)
        elif column == "reporting":
            reporting.append(item)
        elif column == "automation":
            automation.append(item)
        else:
            # Named but unrecognised. It goes in Knowledge under its own name
            # and is listed as unclassified, because a confidently wrong box is
            # worse than an honest one.
            knowledge.append(item)
            unclassified.append(s)

    if not interface:
        interface = [{"label": "Microsoft Teams", "glyph": "teams", "from": "default surface"}]
    if not knowledge:
        knowledge = [{"label": "The operator's own working context",
                      "glyph": "generic", "from": "no declared systems"}]

    actors = (entry.get("personas") or entry.get("audience") or [])[:2] or ["Operator"]
    actions = (entry.get("business_value") or [])[:3]
    if not actions:
        actions = ["Runs the task described in the manifest"]

    env = entry.get("requires_env") or []

    return {
        "slug": entry["slug"],
        "kind": entry.get("kind", "solution"),
        "ref": entry.get("ref"),
        "display_name": entry.get("display_name") or entry["slug"],
        "industries": entry.get("industries") or [],
        "columns": {
            "knowledge": {
                "title": "Knowledge",
                "grounding": knowledge,
                "connectors": ([a["label"] for a in automation]
                               or ["Power Platform connectors and actions"]),
                "note": ("Grounding data the agent reads. It is not copied — the "
                         "agent reads it in place, under the caller's permissions."),
            },
            "processing": {
                "title": "Processing",
                "orchestration": "Multi-agent orchestration",
                "plan": FLOW[2],
                "actions": actions,
            },
            "interface": {
                "title": "User Interface",
                "surfaces": interface,
                "actors": actors,
                "checks": FLOW[1],
            },
            "reporting": {
                "title": "Reporting",
                "systems": reporting or [{"label": "Copilot Control System",
                                          "glyph": "purview", "from": "platform default"}],
                "governance": ("Reviews audit logs, sensitivity labels, data "
                               "policies, CMK, DLP"),
                "insights": "Logs and telemetry data for analysis and monitoring",
            },
        },
        "flow": [{"step": i + 1, "text": t} for i, t in enumerate(FLOW)],
        "tools_band": ("Automatic orchestration using prompts, agent flows, computer "
                       "use, custom connectors, Model Context Protocol and REST API"),
        "foundation_band": {"identity": "Entra ID",
                            "label": "Supporting features and foundation models"},
        "configuration": env,
        "derivation": {
            "systems_declared": systems,
            "unclassified": unclassified,
            "note": ("Every box is derived from what the entry declares. Systems "
                     "whose name did not match a known platform are placed in "
                     "Knowledge under their own name and listed here rather than "
                     "sorted into a category they may not belong to."),
        },
    }


def entries() -> list[dict]:
    out = []
    op = REPO_ROOT / "data" / "onepagers.json"
    if op.is_file():
        for s in json.loads(op.read_text(encoding="utf-8"))["onepagers"]:
            out.append({**s, "kind": "solution", "ref": s["slug"]})

    reg = REPO_ROOT / "api" / "v1" / "agents.json"
    if reg.is_file():
        for a in json.loads(reg.read_text(encoding="utf-8")).get("agents", []):
            out.append({
                "slug": a["name"].split("/")[-1], "kind": "agent", "ref": a["name"],
                "display_name": a.get("display_name"),
                "lede": a.get("description"),
                "requires_env": a.get("requires_env") or [],
                "built_with": ["Microsoft Copilot Studio"],
                "industries": [a.get("category", "general").replace("_", " ").title()],
            })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only")
    args = ap.parse_args()

    items = entries()
    if args.only:
        items = [e for e in items if args.only in e["slug"]]
    if not items:
        print(f"[architecture] nothing matched {args.only!r}", file=sys.stderr)
        return 1

    built = [build(e) for e in items]
    doc = {
        "schema": SCHEMA,
        "format_version": FORMAT_VERSION,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": ("Reference architectures, derived from what each entry declares. "
                 "They describe the shape of a working deployment, not a deployment "
                 "anyone has made — nothing here is a statement about a customer "
                 "environment."),
        "count": len(built),
        "architectures": built,
    }
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    unc = sum(1 for b in built if b["derivation"]["unclassified"])
    print(f"[architecture] {len(built)} architectures "
          f"({unc} with a system left unclassified rather than guessed)")
    print(f"[architecture] wrote {OUT_FILE.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
