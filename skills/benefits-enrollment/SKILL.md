---
name: "benefits-enrollment"
description: "Answers benefits enrollment questions for fictional Tailwind Traders employees from a fixed synthetic snapshot (Nov 10, 2026; 2027 plan year). Use it for when open enrollment closes and what can change, what to do after a life event such as a new baby, marriage, loss of other coverage or divorce, comparing the three medical plans' costs, whether a doctor or clinic is in network, which documents are still missing, drafting election changes without submitting them, and benefits deadlines. The demo employee is Jamie Patel. Call it first: every operation has demo defaults. It uses only life events the employee states, never decides eligibility or recommends a plan, and never submits an election."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "benefits_enrollment_assistant_agent.py"
  tool-name: "BenefitsEnrollmentAgent"
  agent-sha256: "61bfddee0e6d9127da21b9fea2888fe15777a6364e3d9e5fc919eaf9a2ad653b"
  version: "1.0.0"
  author: "AIBAST"
  tags: "hr, benefits, open-enrollment, life-events, human-resources"
---

# Benefits Enrollment

Answers benefits enrollment questions for fictional Tailwind Traders employees from a fixed synthetic snapshot (Nov 10, 2026; 2027 plan year). Use it for when open enrollment closes and what can change, what to do after a life event such as a new baby, marriage, loss of other coverage or divorce, comparing the three medical plans' costs, whether a doctor or clinic is in network, which documents are still missing, drafting election changes without submitting them, and benefits deadlines. The demo employee is Jamie Patel. Call it first: every operation has demo defaults. It uses only life events the employee states, never decides eligibility or recommends a plan, and never submits an election.

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "enrollment_window",
        "life_event_change",
        "compare_plans",
        "provider_network",
        "document_checklist",
        "election_draft",
        "deadline_reminders"
      ],
      "description": "enrollment_window for open enrollment dates or what can change; life_event_change when the employee mentions a baby, adoption, marriage, lost coverage or divorce; compare_plans for plan costs or a plan comparison; provider_network for doctors, clinics or network checks; document_checklist for documents still needed; election_draft to draft or preview election changes; deadline_reminders for deadlines or dates to remember."
    },
    "employee_name": {
      "type": "string",
      "description": "Employee name (default 'Jamie Patel')"
    },
    "event_type": {
      "type": "string",
      "enum": [
        "birth_adoption",
        "marriage",
        "loss_of_coverage",
        "divorce_separation"
      ],
      "description": "Life event the employee stated (life_event_change only; defaults to the event the employee reported)"
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
   python3 scripts/run.py --json '{"operation": "<string>", "employee_name": "<string>", "event_type": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=61bfddee0e6d9127da21b9fea2888fe15777a6364e3d9e5fc919eaf9a2ad653b -->
```python
"""
Benefits Enrollment Agent

Benefits enrollment assistant for employees and benefits specialists: the open
enrollment window, life-event change rules, side-by-side medical plan costs,
provider network checks, document checklists, a draft election summary, and a
personal deadline list.

Where a real deployment would call the benefits administration system, carrier
provider directories, and the document intake queue, this agent uses a fixed
synthetic snapshot for the fictional employer Tailwind Traders so it runs anywhere
without credentials. It never submits an election, decides eligibility, or
recommends a plan; it returns reviewable drafts.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))

from basic_agent import BasicAgent

# ═══════════════════════════════════════════════════════════════
# RAPP AGENT MANIFEST
# ═══════════════════════════════════════════════════════════════
__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/benefits-enrollment-assistant",
    "version": "1.0.0",
    "display_name": "Benefits Enrollment Agent",
    "description": "Guide employees through open enrollment and life-event benefit changes by explaining the enrollment window and change rules, comparing plan costs for their coverage tier, checking whether their providers are in network, tracking required documents, and preparing a draft election, while eligibility decisions and submissions stay with the employee and benefits staff.",
    "author": "AIBAST",
    "tags": ["hr", "benefits", "open-enrollment", "life-events", "human-resources"],
    "category": "human_resources",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ═══════════════════════════════════════════════════════════════
# SYNTHETIC DATA LAYER (fixed snapshot: Tailwind Traders, Nov 10, 2026)
# ═══════════════════════════════════════════════════════════════

_EMPLOYER = "Tailwind Traders"
_TODAY = (2026, 11, 10)
_OE = {"opens": (2026, 11, 2), "closes": (2026, 11, 20), "effective": "Jan 1, 2027", "plan_year": 2027}
_PAYCHECKS = 26
_TIERS = ["Employee only", "Employee + spouse", "Employee + child(ren)", "Family"]

_PLANS = {
    "Core HMO": {"cost": [38.00, 96.00, 84.00, 142.00], "deductible": (500, 1000),
                 "oop_max": (3500, 7000), "network": "Core network", "seed": (0, 0)},
    "Choice PPO": {"cost": [64.00, 152.00, 131.00, 218.00], "deductible": (750, 1500),
                   "oop_max": (4000, 8000), "network": "Broad network", "seed": (0, 0)},
    "Saver HDHP": {"cost": [21.00, 58.00, 50.00, 89.00], "deductible": (1700, 3400),
                   "oop_max": (5000, 10000), "network": "Broad network", "seed": (750, 1500)},
}

_PROVIDERS = {
    "Lakeside Family Clinic": {"type": "Primary care", "networks": ["Core network", "Broad network"]},
    "Riverbend Pediatrics": {"type": "Pediatrics", "networks": ["Broad network"]},
    "Harborview Imaging": {"type": "Imaging", "networks": ["Core network"]},
}

_EVENTS = {
    "birth_adoption": {
        "label": "Birth or adoption of a child", "window_days": 30,
        "documents": ["Birth certificate or adoption decree", "Dependent details (name, date of birth)"],
        "changes": ["Add the child to medical, dental, and vision", "Move to a higher coverage tier",
                    "Start or change a dependent care spending account", "Update life insurance beneficiaries"],
        "form": "Life Event Change Request (form LE-1, fictional)",
    },
    "marriage": {
        "label": "Marriage or registered partnership", "window_days": 30,
        "documents": ["Marriage or partnership certificate"],
        "changes": ["Add a spouse or partner", "Move to a higher coverage tier", "Update beneficiaries"],
        "form": "Life Event Change Request (form LE-1, fictional)",
    },
    "loss_of_coverage": {
        "label": "Loss of other group coverage", "window_days": 30,
        "documents": ["Letter confirming the other coverage end date"],
        "changes": ["Enroll in medical, dental, and vision", "Add dependents who also lost coverage"],
        "form": "Life Event Change Request (form LE-1, fictional)",
    },
    "divorce_separation": {
        "label": "Divorce or legal separation", "window_days": 30,
        "documents": ["Divorce decree or separation order"],
        "changes": ["Remove a former spouse", "Move to a lower coverage tier", "Update beneficiaries"],
        "form": "Life Event Change Request (form LE-1, fictional)",
    },
}

_EMPLOYEES = {
    "jamie": {
        "id": "TWT-20418", "name": "Jamie Patel", "department": "Store Operations",
        "plan": "Core HMO", "tier": 1,
        "reported_event": {"type": "birth_adoption", "date": (2026, 10, 28)},
        "target_tier": 3,
        "providers": ["Lakeside Family Clinic", "Riverbend Pediatrics"],
        "documents": {"Dependent details (name, date of birth)": "Received Nov 3, 2026",
                      "Birth certificate or adoption decree": "Not received"},
        "fsa": "Not enrolled for 2027",
    },
    "morgan": {
        "id": "TWT-18872", "name": "Morgan Ellis", "department": "Finance",
        "plan": "Choice PPO", "tier": 0,
        "reported_event": None, "target_tier": 0,
        "providers": ["Harborview Imaging"],
        "documents": {},
        "fsa": "Health care account elected for 2027",
    },
}

_GATE = (
    "Synthetic benefits guidance only. This agent does not decide eligibility, "
    "recommend a plan, infer a personal circumstance, or submit an election; the "
    "employee and authorized benefits staff make every decision."
)
_SOURCE = "Source: [Synthetic Tailwind Traders Benefits Snapshot]\nAgents: BenefitsEnrollmentAgent"

_OPERATIONS = [
    "enrollment_window", "life_event_change", "compare_plans", "provider_network",
    "document_checklist", "election_draft", "deadline_reminders",
]


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _date(t):
    import datetime
    return datetime.date(*t)


def _fmt(d):
    return f"{d:%b} {d.day}, {d.year}"


def _plus_days(t, n):
    import datetime
    return _date(t) + datetime.timedelta(days=n)


def _days_between(a, b):
    return (_date(b) - _date(a)).days if isinstance(b, tuple) else (b - _date(a)).days


def _usd(x):
    return f"${x:,.2f}"


def _resolve_employee(query):
    """Profile key, full name or a unique name part; None when no profile matches (never another person)."""
    if not query:
        return "jamie"
    q = str(query).lower().strip()
    for key in _EMPLOYEES:
        if key in q or q in _EMPLOYEES[key]["name"].lower():
            return key
    return None


# ═══════════════════════════════════════════════════════════════
# AGENT CLASS
# ═══════════════════════════════════════════════════════════════

class BenefitsEnrollmentAgent(BasicAgent):
    """
    Benefits enrollment assistant over a fixed synthetic snapshot.

    Operations:
        enrollment_window   - open enrollment dates, days left, what can change
        life_event_change   - change window, documents and allowed changes for a life event
        compare_plans       - per-paycheck and annual cost of each medical plan for a tier
        provider_network    - whether the employee's providers are in each plan's network
        document_checklist  - required documents and what is still missing
        election_draft      - draft election summary (Not Submitted)
        deadline_reminders  - the employee's personal deadline list
    """

    def __init__(self):
        self.name = "BenefitsEnrollmentAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                "Answers benefits enrollment questions for fictional Tailwind Traders employees "
                "from a fixed synthetic snapshot (Nov 10, 2026; 2027 plan year). Use it for when "
                "open enrollment closes and what can change, what to do after a life event such as "
                "a new baby, marriage, loss of other coverage or divorce, comparing the three "
                "medical plans' costs, whether a doctor or clinic is in network, which documents "
                "are still missing, drafting election changes without submitting them, and "
                "benefits deadlines. The demo employee is Jamie Patel. Call it first: every "
                "operation has demo defaults. It uses only life events the employee states, never "
                "decides eligibility or recommends a plan, and never submits an election."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": list(_OPERATIONS),
                        "description": (
                            "enrollment_window for open enrollment dates or what can change; "
                            "life_event_change when the employee mentions a baby, adoption, "
                            "marriage, lost coverage or divorce; compare_plans for plan costs or "
                            "a plan comparison; provider_network for doctors, clinics or network "
                            "checks; document_checklist for documents still needed; "
                            "election_draft to draft or preview election changes; "
                            "deadline_reminders for deadlines or dates to remember."
                        ),
                    },
                    "employee_name": {
                        "type": "string",
                        "description": "Employee name (default 'Jamie Patel')",
                    },
                    "event_type": {
                        "type": "string",
                        "enum": list(_EVENTS),
                        "description": "Life event the employee stated (life_event_change only; defaults to the event the employee reported)",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation") or "enrollment_window"
        handlers = {
            "enrollment_window": self._enrollment_window,
            "life_event_change": self._life_event_change,
            "compare_plans": self._compare_plans,
            "provider_network": self._provider_network,
            "document_checklist": self._document_checklist,
            "election_draft": self._election_draft,
            "deadline_reminders": self._deadline_reminders,
        }
        handler = handlers.get(op)
        if not handler:
            return f"Unknown operation: {op}. Choose one of: {', '.join(_OPERATIONS)}."
        key = _resolve_employee(kwargs.get("employee_name"))
        if key is None:
            names = ", ".join(e["name"] for e in _EMPLOYEES.values())
            return (
                f"No synthetic profile matches '{kwargs.get('employee_name')}'. "
                f"Fictional profiles: {names}.\n\n{_GATE}\n\n{_SOURCE}"
            )
        if op == "life_event_change":
            return handler(key, kwargs.get("event_type"))
        return handler(key)

    # ── enrollment_window ─────────────────────────────────────
    def _enrollment_window(self, key):
        emp = _EMPLOYEES[key]
        left = _days_between(_TODAY, _OE["closes"])
        return (
            f"**Open Enrollment {_OE['plan_year']}: {_EMPLOYER}**\n\n"
            f"| Detail | Value |\n|---|---|\n"
            f"| Window | {_fmt(_date(_OE['opens']))} to {_fmt(_date(_OE['closes']))} |\n"
            f"| Days left (from {_fmt(_date(_TODAY))}) | {left} |\n"
            f"| New elections effective | {_OE['effective']} |\n"
            f"| {emp['name']}'s current medical | {emp['plan']}, {_TIERS[emp['tier']]} |\n\n"
            f"**During open enrollment you can:**\n"
            f"- Switch between Core HMO, Choice PPO, and Saver HDHP\n"
            f"- Add or remove dependents and change your coverage tier\n"
            f"- Elect health care or dependent care spending accounts for {_OE['plan_year']}\n"
            f"- Update life insurance beneficiaries\n\n"
            f"If you make no changes, your current medical, dental, and vision elections continue; "
            f"spending account elections do not carry over.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── life_event_change ─────────────────────────────────────
    def _life_event_change(self, key, event_type):
        emp = _EMPLOYEES[key]
        reported = emp["reported_event"]
        if event_type not in _EVENTS:
            event_type = reported["type"] if reported else "birth_adoption"
        ev = _EVENTS[event_type]
        dated = reported and reported["type"] == event_type
        if dated:
            deadline = _plus_days(reported["date"], ev["window_days"])
            timing = (f"| Event date (employee-reported) | {_fmt(_date(reported['date']))} |\n"
                      f"| Change request due | {_fmt(deadline)} ({_days_between(_TODAY, deadline)} days from today) |\n"
                      f"| Coverage for the change starts | {_fmt(_date(reported['date']))} (event date) |\n")
        else:
            timing = "| Change request due | Within 30 days of the event date |\n"
        changes = "\n".join(f"- {c}" for c in ev["changes"])
        docs = "\n".join(f"- {d}" for d in ev["documents"])
        return (
            f"**Life Event Change: {ev['label']} ({emp['name']})**\n\n"
            f"| Detail | Value |\n|---|---|\n"
            f"| Change window | {ev['window_days']} days from the event |\n{timing}"
            f"| Form | {ev['form']} |\n\n"
            f"**Changes this event allows:**\n{changes}\n\n"
            f"**Documents to provide:**\n{docs}\n\n"
            f"This uses only the event the employee stated. Benefits staff confirm eligibility "
            f"when they review the request.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── compare_plans ─────────────────────────────────────────
    def _compare_plans(self, key):
        emp = _EMPLOYEES[key]
        tier = emp["target_tier"]
        family = 1 if tier > 0 else 0
        rows, lowest = [], None
        for name, p in _PLANS.items():
            per = p["cost"][tier]
            annual = per * _PAYCHECKS
            ded = p["deductible"][family]
            seed = p["seed"][family]
            exposure = annual + ded - seed
            rows.append(f"| {name} | {_usd(per)} | {_usd(annual)} | {_usd(ded)} | {_usd(p['oop_max'][family])} | "
                        f"{_usd(seed) if seed else '-'} | {_usd(exposure)} | {p['network']} |")
            if lowest is None or annual < lowest[1]:
                lowest = (name, annual)
        return (
            f"**Medical Plan Comparison {_OE['plan_year']}: {_TIERS[tier]} ({emp['name']})**\n\n"
            f"| Plan | Per Paycheck | Annual Premium | Deductible | Out-of-Pocket Max | Employer HSA Seed | "
            f"Premium + Deductible - Seed | Network |\n|---|---|---|---|---|---|---|---|\n"
            + "\n".join(rows) + "\n\n"
            f"Annual premium = per-paycheck cost x {_PAYCHECKS} paychecks. Lowest annual premium: "
            f"{lowest[0]} ({_usd(lowest[1])}). Lower premiums can mean higher costs when care is used, "
            f"so compare the deductible and network too.\n\n"
            f"This is a cost comparison, not a plan recommendation.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── provider_network ──────────────────────────────────────
    def _provider_network(self, key):
        emp = _EMPLOYEES[key]
        plans = list(_PLANS)
        header = "| Provider | Type | " + " | ".join(plans) + " |\n|---|---|" + "---|" * len(plans)
        rows, gaps = [], []
        for prov in emp["providers"]:
            info = _PROVIDERS[prov]
            cells = []
            for plan in plans:
                ok = _PLANS[plan]["network"] in info["networks"]
                cells.append("In network" if ok else "Out of network")
                if not ok:
                    gaps.append(f"{prov} is out of network on {plan}")
            rows.append(f"| {prov} | {info['type']} | " + " | ".join(cells) + " |")
        gap_lines = "\n".join(f"- {g}" for g in gaps) or "- None"
        return (
            f"**Provider Network Check: {emp['name']}**\n\n{header}\n" + "\n".join(rows) + "\n\n"
            f"**Network gaps:**\n{gap_lines}\n\n"
            f"Confirm with the carrier's directory before choosing; networks can change for {_OE['plan_year']}.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── document_checklist ────────────────────────────────────
    def _document_checklist(self, key):
        emp = _EMPLOYEES[key]
        reported = emp["reported_event"]
        if not reported:
            return (
                f"**Document Checklist: {emp['name']}**\n\nNo life event is on file, so no supporting "
                f"documents are required for open enrollment changes.\n\n{_GATE}\n\n{_SOURCE}"
            )
        ev = _EVENTS[reported["type"]]
        due = _plus_days(reported["date"], ev["window_days"])
        rows = "\n".join(f"| {d} | {emp['documents'].get(d, 'Not received')} |" for d in ev["documents"])
        missing = [d for d in ev["documents"] if emp["documents"].get(d, "Not received") == "Not received"]
        return (
            f"**Document Checklist: {emp['name']} ({ev['label']})**\n\n"
            f"| Document | Status |\n|---|---|\n{rows}\n"
            f"| {ev['form']} | Draft ready for employee review |\n\n"
            f"**Still missing ({len(missing)}):** {', '.join(missing) or 'None'}\n"
            f"**Due with the change request by:** {_fmt(due)}\n\n"
            f"Upload documents only through the approved benefits portal; do not paste them into chat.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── election_draft ────────────────────────────────────────
    def _election_draft(self, key):
        emp = _EMPLOYEES[key]
        plan = _PLANS[emp["plan"]]
        before = plan["cost"][emp["tier"]]
        after = plan["cost"][emp["target_tier"]]
        reported = emp["reported_event"]
        if reported:
            ev = _EVENTS[reported["type"]]
            change = (f"| Life event change | {emp['plan']}: {_TIERS[emp['tier']]} -> {_TIERS[emp['target_tier']]}, "
                      f"effective {_fmt(_date(reported['date']))} |\n"
                      f"| Per-paycheck cost | {_usd(before)} -> {_usd(after)} ({_usd(after - before)} more) |\n"
                      f"| Request due | {_fmt(_plus_days(reported['date'], ev['window_days']))} |\n")
        else:
            change = f"| Life event change | None on file |\n| Per-paycheck cost | {_usd(before)} (no change) |\n"
        return (
            f"**Election Draft: {emp['name']} - Not Submitted**\n\n"
            f"| Item | Draft |\n|---|---|\n{change}"
            f"| {_OE['plan_year']} medical plan | Employee to choose during open enrollment (see plan comparison) |\n"
            f"| Spending accounts {_OE['plan_year']} | {emp['fsa']} |\n"
            f"| Beneficiaries | Review recommended after any life event |\n\n"
            f"Status: Draft for employee review. No election was submitted and no record was changed. "
            f"Submit through the benefits portal; benefits staff confirm eligibility.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── deadline_reminders ────────────────────────────────────
    def _deadline_reminders(self, key):
        emp = _EMPLOYEES[key]
        items = []
        reported = emp["reported_event"]
        if reported:
            ev = _EVENTS[reported["type"]]
            due = _plus_days(reported["date"], ev["window_days"])
            items.append((due, f"Life event change request and documents ({ev['label'].lower()})"))
        closes = _date(_OE["closes"])
        items.append((closes, f"Open enrollment closes: {_OE['plan_year']} medical plan choice"))
        items.append((closes, f"Spending account elections for {_OE['plan_year']}"))
        items.sort(key=lambda x: x[0])
        rows = "\n".join(f"| {_fmt(d)} | {_days_between(_TODAY, d)} | {what} |" for d, what in items)
        return (
            f"**Benefits Deadlines: {emp['name']} (as of {_fmt(_date(_TODAY))})**\n\n"
            f"| Date | Days Left | Deadline |\n|---|---|---|\n{rows}\n"
            f"| {_OE['effective']} | - | New elections take effect |\n\n"
            f"**First up:** {_fmt(items[0][0])} - {items[0][1]}.\n\n"
            f"Add these to your own calendar; no reminder or invitation was sent.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )


if __name__ == "__main__":
    agent = BenefitsEnrollmentAgent()
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
