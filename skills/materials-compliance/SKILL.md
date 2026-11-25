---
name: "materials-compliance"
description: "Weekly materials compliance assistant for grant-funded construction projects at Tailspin Civil Works (fixed synthetic snapshot). Always use this tool, with its demo defaults, for: what changed on the approved bills of materials this week (weekly_changes); which items are out of compliance or newly non-compliant and why (compliance_check); a compliant replacement or alternate part with the same spec (compliant_alternates, optional item, default the gate valve GV-08); vendor certificates that expired or expire soon (vendor_watch); whether the audit evidence package is ready (audit_evidence); and preparing the hold notice, renewal, substitution and document requests a person approved (action_drafts). It never orders, sends, changes master data or certifies compliance."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "build_materials_compliance_agent.py"
  tool-name: "MaterialsComplianceAgent"
  agent-sha256: "974728e68dd164dbf119b3a5c9a6179e085024561f1a28496308bd616ecd113c"
  version: "1.0.0"
  author: "AIBAST"
  tags: "manufacturing, construction, materials, compliance, procurement, bill-of-materials"
---

# Materials Compliance

Weekly materials compliance assistant for grant-funded construction projects at Tailspin Civil Works (fixed synthetic snapshot). Always use this tool, with its demo defaults, for: what changed on the approved bills of materials this week (weekly_changes); which items are out of compliance or newly non-compliant and why (compliance_check); a compliant replacement or alternate part with the same spec (compliant_alternates, optional item, default the gate valve GV-08); vendor certificates that expired or expire soon (vendor_watch); whether the audit evidence package is ready (audit_evidence); and preparing the hold notice, renewal, substitution and document requests a person approved (action_drafts). It never orders, sends, changes master data or certifies compliance.

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "weekly_changes",
        "compliance_check",
        "compliant_alternates",
        "vendor_watch",
        "audit_evidence",
        "action_drafts"
      ],
      "description": "weekly_changes for BOM changes; compliance_check for compliance status; compliant_alternates for replacements; vendor_watch for certificates; audit_evidence for audit readiness; action_drafts to prepare approved drafts."
    },
    "item": {
      "type": "string",
      "description": "compliant_alternates only: item code or name, e.g. 'GV-08' or 'copper' (default GV-08)"
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
   python3 scripts/run.py --json '{"operation": "<string>", "item": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=974728e68dd164dbf119b3a5c9a6179e085024561f1a28496308bd616ecd113c -->
```python
"""
Build Materials Compliance Agent

Keeps the approved bills of materials on grant-funded construction projects in line
with the program's materials sourcing rule: scan what changed this week, check every
covered item against vendor certifications, content attestations and questionnaire
answers, find compliant alternates with the same specification, watch vendor
certificates before they lapse, show audit-evidence readiness, and prepare the drafts
a person sends once they approve the next steps.

Where a real deployment would read the project BOM system, product master data and
vendor certificate library, this agent uses a fixed synthetic snapshot so it runs
anywhere without credentials. It never places orders, changes master data, sends a
request, or certifies compliance.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))

from basic_agent import BasicAgent

# ═══════════════════════════════════════════════════════════════
# RAPP AGENT MANIFEST
# ═══════════════════════════════════════════════════════════════
__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/build-materials-compliance",
    "version": "1.0.0",
    "display_name": "Build Materials Compliance Agent",
    "description": "Keep grant-funded construction bills of materials compliant every week: flag items that newly fall out of the program's materials sourcing rule with cited evidence, find same-specification compliant alternates, watch vendor certificates, and keep the audit evidence package ready.",
    "author": "AIBAST",
    "tags": ["manufacturing", "construction", "materials", "compliance", "procurement", "bill-of-materials"],
    "category": "manufacturing",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ═══════════════════════════════════════════════════════════════
# SYNTHETIC DATA LAYER (fixed snapshot; every name and value is invented)
# ═══════════════════════════════════════════════════════════════

_ORG = "Tailspin Civil Works"
_AS_OF = "2026-10-05"
_LAST_SCAN = "2026-09-28"
_WATCH_UNTIL = "2027-01-03"   # vendor certificates expiring inside the next 90 days

_PROJECTS = {
    "P-101": "Riverside Main Replacement",
    "P-102": "Hillcrest Pump Station",
    "P-103": "Lakeview Service Lines",
}

_VENDORS = {
    "contoso": {"name": "Contoso Pipe & Valve", "cert_expires": "2027-03-31", "contact": "Avery Brooks"},
    "fabrikam": {"name": "Fabrikam Castings", "cert_expires": "2026-09-30", "contact": "Jamie Ortiz"},
    "litware": {"name": "Litware Fittings", "cert_expires": "2026-12-01", "contact": "Riley Chen"},
    "adatum": {"name": "Adatum Steel", "cert_expires": "2026-11-15", "contact": "Casey Morgan"},
    "wingtip": {"name": "Wingtip Supply", "cert_expires": "2027-06-30", "contact": "Drew Patel"},
}

# Product master data. covered = falls under the program's materials sourcing rule.
_ITEMS = {
    "DI-08": {"name": "8-inch ductile iron pipe", "spec": "DIP-8-C52", "vendor": "contoso", "covered": True,
              "price": 42.00, "unit": "ft", "attestation": "On file", "datasheet": True,
              "questionnaire": "Answered: qualifies", "cert_part_match": True},
    "GV-08": {"name": "8-inch resilient wedge gate valve", "spec": "GV-8-RW", "vendor": "fabrikam", "covered": True,
              "price": 1150.00, "unit": "ea", "attestation": "On file", "datasheet": True,
              "questionnaire": "Answered: qualifies", "cert_part_match": True},
    "CP-02": {"name": "1-inch copper service tubing", "spec": "CU-1-K", "vendor": "litware", "covered": True,
              "price": 3.10, "unit": "ft", "attestation": "On file", "datasheet": True,
              "questionnaire": "Answered Oct 2: final assembly moved to a non-qualifying plant", "cert_part_match": True},
    "CF-06": {"name": "6-inch restraint coupling", "spec": "RC-6-DI", "vendor": "litware", "covered": True,
              "price": 186.00, "unit": "ea", "attestation": "On file", "datasheet": True,
              "questionnaire": "Answered: qualifies", "cert_part_match": False},
    "RB-04": {"name": "No. 4 reinforcing bar", "spec": "RB-4-G60", "vendor": "adatum", "covered": True,
              "price": 0.95, "unit": "ft", "attestation": "On file", "datasheet": False,
              "questionnaire": "Answered: qualifies", "cert_part_match": True},
    "MB-12": {"name": "Polymer meter box", "spec": "MB-12-P", "vendor": "wingtip", "covered": False,
              "price": 64.00, "unit": "ea", "attestation": "Not required", "datasheet": True,
              "questionnaire": "Not required", "cert_part_match": True},
}

# Approved bill-of-materials lines: (project, item, quantity this week, quantity at last scan; 0 = not on the BOM).
_BOM = [
    ("P-101", "DI-08", 2400, 2000),
    ("P-101", "GV-08", 12, 0),
    ("P-101", "RB-04", 800, 800),
    ("P-102", "GV-08", 6, 6),
    ("P-102", "CF-06", 40, 40),
    ("P-103", "CP-02", 3000, 3000),
    ("P-103", "CF-06", 20, 12),
    ("P-103", "MB-12", 150, 0),
]

# Same-specification alternates in the approved catalog.
_ALTERNATES = {
    "GV-08": [
        {"part": "GV-08B", "vendor": "contoso", "price": 1210.00, "datasheet": True, "lead_days": 14},
        {"part": "GV-08C", "vendor": "wingtip", "price": 1185.00, "datasheet": False, "lead_days": 21},
    ],
    "CP-02": [
        {"part": "CP-02B", "vendor": "contoso", "price": 3.40, "datasheet": True, "lead_days": 10},
    ],
}

_GATE = (
    "Synthetic decision support only. This agent recommends first: it does not place "
    "orders, change master data, send a request, or certify compliance. A person "
    "approves every next step."
)
_SOURCE = "Source: [Synthetic BOM + Master Data + Vendor Certificate Snapshot]\nAgents: MaterialsComplianceAgent"


# ═══════════════════════════════════════════════════════════════
# HELPERS (plain dicts, lists and arithmetic)
# ═══════════════════════════════════════════════════════════════

def _money(v):
    v = round(v, 2)
    return f"${v:,.2f}" if v != int(v) else f"${v:,.0f}"


def _vendor(item_code):
    return _VENDORS[_ITEMS[item_code]["vendor"]]


def _finding(code):
    """The compliance finding for one item: status, reason, evidence; newly = changed since the last scan."""
    item, vendor = _ITEMS[code], _vendor(code)
    if not item["covered"]:
        return {"status": "Not covered", "reason": "Outside the covered materials list", "newly": False}
    if vendor["cert_expires"] < _AS_OF:
        return {"status": "Non-compliant", "newly": vendor["cert_expires"] >= _LAST_SCAN,
                "reason": f"Vendor certificate expired {vendor['cert_expires']}",
                "evidence": f"{vendor['name']} certificate library entry"}
    if "non-qualifying" in item["questionnaire"]:
        return {"status": "Non-compliant", "newly": True,
                "reason": "Vendor questionnaire answer: final assembly moved to a non-qualifying plant",
                "evidence": f"{vendor['name']} questionnaire, answered Oct 2"}
    if not item["cert_part_match"]:
        return {"status": "Conflict", "newly": False,
                "reason": "Master data says attestation on file; certificate letter lists a different part revision",
                "evidence": f"{vendor['name']} certificate letter vs product master data"}
    if not item["datasheet"]:
        return {"status": "Evidence gap", "newly": False, "reason": "Product data sheet missing",
                "evidence": "Product master data"}
    return {"status": "Compliant", "newly": False, "reason": "Certificate, attestation and data sheet current"}


def _lines_for(code):
    return [(p, q) for p, c, q, _ in _BOM if c == code and q > 0]


def _resolve_item(query):
    """Item code, part of the code or part of the item name; None when nothing matches (never another item)."""
    if not query:
        return "GV-08"
    q = query.lower().strip()
    for key in _ITEMS:
        if key.lower() in q or q in _ITEMS[key]["name"].lower():
            return key
    return None


# ═══════════════════════════════════════════════════════════════
# AGENT CLASS
# ═══════════════════════════════════════════════════════════════

_OPERATIONS = [
    "weekly_changes", "compliance_check", "compliant_alternates",
    "vendor_watch", "audit_evidence", "action_drafts",
]


class MaterialsComplianceAgent(BasicAgent):
    """
    Construction materials compliance assistant.

    Operations:
        weekly_changes       - what is new or changed on the approved BOMs since last week's scan
        compliance_check     - covered items checked against certificates, attestations, questionnaires
        compliant_alternates - same-specification compliant alternates for a flagged item, with cost impact
        vendor_watch         - vendor certificates expired or expiring in the next 90 days
        audit_evidence       - audit evidence readiness per project
        action_drafts        - drafts for the next steps a person approved (never sent)
    """

    def __init__(self):
        self.name = "MaterialsComplianceAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                "Weekly materials compliance assistant for grant-funded construction projects at "
                "Tailspin Civil Works (fixed synthetic snapshot). Always use this tool, with its demo "
                "defaults, for: what changed on the approved bills of materials this week "
                "(weekly_changes); which items are out of compliance or newly non-compliant and why "
                "(compliance_check); a compliant replacement or alternate part with the same spec "
                "(compliant_alternates, optional item, default the gate valve GV-08); vendor "
                "certificates that expired or expire soon (vendor_watch); whether the audit evidence "
                "package is ready (audit_evidence); and preparing the hold notice, renewal, "
                "substitution and document requests a person approved (action_drafts). It never "
                "orders, sends, changes master data or certifies compliance."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": list(_OPERATIONS),
                        "description": (
                            "weekly_changes for BOM changes; compliance_check for compliance status; "
                            "compliant_alternates for replacements; vendor_watch for certificates; "
                            "audit_evidence for audit readiness; action_drafts to prepare approved drafts."
                        ),
                    },
                    "item": {
                        "type": "string",
                        "description": "compliant_alternates only: item code or name, e.g. 'GV-08' or 'copper' (default GV-08)",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation") or "weekly_changes"
        dispatch = {
            "weekly_changes": self._weekly_changes,
            "compliance_check": self._compliance_check,
            "compliant_alternates": self._compliant_alternates,
            "vendor_watch": self._vendor_watch,
            "audit_evidence": self._audit_evidence,
            "action_drafts": self._action_drafts,
        }
        handler = dispatch.get(op)
        if not handler:
            return f"Unknown operation: {op}. Available: {', '.join(_OPERATIONS)}.\n\n{_GATE}\n\n{_SOURCE}"
        if op == "compliant_alternates":
            code = _resolve_item(kwargs.get("item", ""))
            if code is None:
                items = ", ".join(k + " " + v["name"] for k, v in _ITEMS.items())
                return (f"No synthetic item matches '{kwargs.get('item')}'. Items: "
                        f"{items}.\n\n{_GATE}\n\n{_SOURCE}")
            return handler(code)
        return handler()

    # ── weekly_changes ────────────────────────────────────────
    def _weekly_changes(self):
        rows, new_n, chg_n = [], 0, 0
        for p, c, q, prev in _BOM:
            if prev == 0:
                change, new_n = "New this week", new_n + 1
            elif q != prev:
                change, chg_n = f"Quantity {prev:,} -> {q:,}", chg_n + 1
            else:
                continue
            rows.append(f"| {p} {_PROJECTS[p]} | {c} {_ITEMS[c]['name']} | {q:,} {_ITEMS[c]['unit']} | "
                        f"{_vendor(c)['name']} | {change} |")
        return (
            f"**Approved BOM Changes: week of {_AS_OF} (vs scan of {_LAST_SCAN})**\n\n"
            f"| Project | Item | Quantity | Vendor | Change |\n|---|---|---|---|---|\n" + "\n".join(rows) + "\n\n"
            f"**Scan:** {len(_PROJECTS)} projects, {len(_BOM)} BOM lines; {new_n} new lines and "
            f"{chg_n} quantity changes since last week.\n"
            f"**Next step:** check every covered item against the materials sourcing rule.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── compliance_check ──────────────────────────────────────
    def _compliance_check(self):
        rows, newly, covered, exposure = [], [], 0, 0.0
        for code, item in _ITEMS.items():
            f = _finding(code)
            if item["covered"]:
                covered += 1
            if f["status"] in ("Compliant", "Not covered"):
                continue
            lines = _lines_for(code)
            qty = sum(q for _, q in lines)
            projects = ", ".join(p for p, _ in lines)
            flag = "NEW " if f["newly"] else ""
            rows.append(f"| {code} {item['name']} | {flag}{f['status']} | {f['reason']} | {f['evidence']} | "
                        f"{projects} ({qty:,} {item['unit']}) |")
            if f["status"] == "Non-compliant":
                exposure += qty * item["price"]
                newly.append(code)
        ok = len([c for c in _ITEMS if _finding(c)["status"] == "Compliant"])
        conflicts = len([c for c in _ITEMS if _finding(c)["status"] == "Conflict"])
        gaps = len([c for c in _ITEMS if _finding(c)["status"] == "Evidence gap"])
        return (
            f"**Materials Compliance Check: {_AS_OF}**\n\n"
            f"| Item | Status | Reason | Cited Evidence | Projects Affected |\n|---|---|---|---|---|\n"
            + "\n".join(rows) + "\n\n"
            f"**Result:** {covered} covered items checked; {ok} compliant, {len(newly)} newly non-compliant "
            f"this week ({', '.join(newly)}), {conflicts} certificate conflict and {gaps} evidence gap. Non-compliant "
            f"material on approved BOMs: {_money(exposure)}.\n"
            f"**Next step:** review compliant alternates for {newly[0]} and {newly[1]} before ordering.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── compliant_alternates ──────────────────────────────────
    def _compliant_alternates(self, code):
        item = _ITEMS[code]
        f = _finding(code)
        if code not in _ALTERNATES:
            return (
                f"**Compliant Alternates: {code} {item['name']}**\n\n"
                f"Status: {f['status']} ({f['reason']}). No alternate is needed or none is listed in the "
                f"approved catalog for spec {item['spec']}.\n\n{_GATE}\n\n{_SOURCE}"
            )
        qty = sum(q for _, q in _lines_for(code))
        rows, best = [], None
        for a in _ALTERNATES[code]:
            v = _VENDORS[a["vendor"]]
            delta = (a["price"] - item["price"]) * qty
            ready = "Ready" if a["datasheet"] and v["cert_expires"] > _AS_OF else "Data sheet missing"
            rows.append(f"| {a['part']} | {v['name']} | {item['spec']} | {_money(a['price'])} | "
                        f"{v['cert_expires']} | {a['lead_days']} days | +{_money(delta)} | {ready} |")
            if best is None and ready == "Ready":
                best = (a, v, delta)
        projects = ", ".join(f"{p} ({q:,})" for p, q in _lines_for(code))
        rec = (f"**Recommended:** {best[0]['part']} from {best[1]['name']}: same spec, certificate current "
               f"to {best[1]['cert_expires']}, cost impact +{_money(best[2])} across {qty:,} {item['unit']}.\n"
               if best else "")
        return (
            f"**Compliant Alternates: {code} {item['name']} (spec {item['spec']})**\n\n"
            f"Current: {_vendor(code)['name']} at {_money(item['price'])}/{item['unit']} - {f['status']}: "
            f"{f['reason']}. On approved BOMs: {projects}.\n\n"
            f"| Alternate | Vendor | Spec | Unit Price | Certificate To | Lead Time | Cost Impact | Evidence |\n"
            f"|---|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n\n"
            f"{rec}"
            f"**Next step:** approve the substitution so a change request draft can be prepared.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── vendor_watch ──────────────────────────────────────────
    def _vendor_watch(self):
        rows = []
        for key in sorted(_VENDORS, key=lambda k: _VENDORS[k]["cert_expires"]):
            v = _VENDORS[key]
            if v["cert_expires"] > _WATCH_UNTIL:
                continue
            status = "Expired" if v["cert_expires"] < _AS_OF else "Expires within 90 days"
            items = [c for c in _ITEMS if _ITEMS[c]["vendor"] == key and _ITEMS[c]["covered"]]
            rows.append(f"| {v['name']} | {v['cert_expires']} | {status} | {', '.join(items)} | {v['contact']} |")
        open_q = [c for c in _ITEMS if "non-qualifying" in _ITEMS[c]["questionnaire"]]
        return (
            f"**Vendor Certificate Watch: as of {_AS_OF} (window to {_WATCH_UNTIL})**\n\n"
            f"| Vendor | Certificate Expires | Status | Covered Items | Contact |\n|---|---|---|---|---|\n"
            + "\n".join(rows) + "\n\n"
            f"**Watch list:** {len(rows)} vendors need a certificate renewal; "
            f"{len(open_q)} questionnaire answer changed this week ({', '.join(open_q)}).\n"
            f"**Next step:** request renewals before the next scan; expired certificates hold their items.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── audit_evidence ────────────────────────────────────────
    def _audit_evidence(self):
        rows, total, complete = [], 0, 0
        for p, pname in _PROJECTS.items():
            lines = [c for pp, c, q, _ in _BOM if pp == p and q > 0 and _ITEMS[c]["covered"]]
            done = [c for c in lines if _finding(c)["status"] == "Compliant"]
            missing = [f"{c} ({_finding(c)['status'].lower()})" for c in lines if c not in done]
            total, complete = total + len(lines), complete + len(done)
            state = "Ready" if not missing else "Not ready"
            rows.append(f"| {p} {pname} | {len(lines)} | {len(done)} | {', '.join(missing) or '-'} | {state} |")
        return (
            f"**Audit Evidence Readiness: {_AS_OF}**\n\n"
            f"| Project | Covered Lines | Evidence Complete | Open Items | Package |\n|---|---|---|---|---|\n"
            + "\n".join(rows) + "\n\n"
            f"**Package:** evidence is complete for {complete} of {total} covered BOM lines (current certificate, "
            f"attestation and data sheet). Every open item cites the record it depends on.\n"
            f"**Next step:** close the open items before the evidence package goes to the program reviewer.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── action_drafts ─────────────────────────────────────────
    def _action_drafts(self):
        gv, cp, cf, rb = _ITEMS["GV-08"], _ITEMS["CP-02"], _ITEMS["CF-06"], _ITEMS["RB-04"]
        drafts = [
            ("Hold notice", "Project buyers, P-101 and P-102",
             f"Hold GV-08 {gv['name']} ({sum(q for _, q in _lines_for('GV-08'))} ea): vendor certificate expired."),
            ("Certificate renewal request", f"{_VENDORS['fabrikam']['contact']}, {_VENDORS['fabrikam']['name']}",
             "Please send a renewed compliance certificate; GV-08 is on hold until it arrives."),
            ("Substitution change request", "Engineering of record, P-101 and P-102",
             f"Replace GV-08 with GV-08B ({_VENDORS['contoso']['name']}), same spec {gv['spec']}."),
            ("Attestation follow-up", f"{_VENDORS['litware']['contact']}, {_VENDORS['litware']['name']}",
             "Your Oct 2 answer moves CP-02 final assembly; please confirm the plant and send an updated "
             "attestation, and correct the part revision on the CF-06 certificate letter."),
            ("Data sheet request", f"{_VENDORS['adatum']['contact']}, {_VENDORS['adatum']['name']}",
             f"Please send the product data sheet for RB-04 {rb['name']}."),
        ]
        rows = "\n".join(f"| {i} | {t} | {to} | {body} |" for i, (t, to, body) in enumerate(drafts, 1))
        return (
            f"**Approved Next Steps: Drafts Ready for Review - Not Sent**\n\n"
            f"| # | Draft | To | Content |\n|---|---|---|---|\n{rows}\n\n"
            f"**Status:** {len(drafts)} drafts prepared. Nothing was sent, no order was placed, and master "
            f"data is unchanged; a person sends each draft and records the change.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )


if __name__ == "__main__":
    agent = MaterialsComplianceAgent()
    for op in _OPERATIONS:
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
