---
name: "tiered-huddle-board"
description: "Answers questions about the hospital's tiered huddle board: the whole board with every lane and clock, what is past target, what is waiting on me, escalating an issue the unit cannot fix to the next tier and who gets paged, whether a mitigated issue can be closed, and what the 10:30 leadership huddle needs to decide today. Always call this tool for huddle, board, tier, escalation, page, clock or closure questions from nurse managers, charge nurses, directors and executives. Call it right away; every operation has demo defaults. It is read-only: it drafts escalations and pages but cannot send, move or close anything, so never offer to send them; the issue owner confirms on the huddle board itself."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "tiered_huddle_board_agent.py"
  tool-name: "TieredHuddleBoardAgent"
  agent-sha256: "f1d3530dce1bbe426732848af126e76cc4eddbe565d8103d2ddb8197acd97288"
  version: "1.0.0"
  author: "AIBAST"
  tags: "healthcare, tiered-huddles, nursing-operations, escalation, hospital-operations"
---

# Tiered Huddle Board

Answers questions about the hospital's tiered huddle board: the whole board with every lane and clock, what is past target, what is waiting on me, escalating an issue the unit cannot fix to the next tier and who gets paged, whether a mitigated issue can be closed, and what the 10:30 leadership huddle needs to decide today. Always call this tool for huddle, board, tier, escalation, page, clock or closure questions from nurse managers, charge nurses, directors and executives. Call it right away; every operation has demo defaults. It is read-only: it drafts escalations and pages but cannot send, move or close anything, so never offer to send them; the issue owner confirms on the huddle board itself.

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "board_view",
        "escalation_draft",
        "closure_check",
        "leadership_decisions"
      ],
      "description": "board_view for the whole board, every lane and clock, what is past target and what is waiting on the person asking; escalation_draft to move an issue the unit or department cannot fix up one tier, restart its clock and list who to page; closure_check for whether a mitigated or fixed issue can come off the board; leadership_decisions for what the 10:30 leadership huddle must decide today, with reason and clock."
    },
    "issue": {
      "type": "string",
      "description": "Issue id such as HB-2041 or words from it such as 'IV pumps' or 'bed alarm in 412'. Optional; escalation defaults to the 4 West IV pump issue and closure to the room 412 bed alarm."
    },
    "viewer": {
      "type": "string",
      "description": "Person asking, for 'waiting on me': a full name, first or last name, with or without a title, or their role on the paging roster. Optional; defaults to Elena Brooks, Nurse Manager of 4 West."
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
   python3 scripts/run.py --json '{"operation": "<string>", "issue": "<string>", "viewer": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=f1d3530dce1bbe426732848af126e76cc4eddbe565d8103d2ddb8197acd97288 -->
```python
"""
Tiered Huddle Board Agent for Healthcare.

Read-only tiered huddle support for a community hospital's nurse managers, department directors and leadership
team, built on a synthetic snapshot of one live huddle board: every lane from Tier 1 (the unit) through Tier 2
(the department), Tier 3 (hospital operations) and the Executive tier, with each issue's clock against its
tier's target, what is waiting on whom, the escalation path with its paging list, and the items that are
mitigated but not yet confirmed by the person who raised them. Today the snapshot is a set of constants; in
production the same accessors read the Dataverse tables behind the board. Every escalation, page and closure is
a draft for an authorized person to confirm.
"""

import sys
import os
import re
from datetime import datetime, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/tiered-huddle-board",
    "version": "1.0.0",
    "display_name": "Tiered Huddle Board Agent",
    "description": "Run a hospital's daily tiered huddles from one live board built on a synthetic snapshot: every lane from Tier 1 through the Executive tier with each issue's clock against its tier's target, what is past target and what is waiting on the person asking, an escalation draft that restarts the clock at the next tier's target with the reason the next tier reads first and the people to page by name, the closure check that keeps mitigated items open until the person who raised them confirms the fix held, and the decisions the leadership huddle needs today. The agent never escalates, pages, closes or changes an issue; an authorized person confirms every step through future authenticated tools.",
    "author": "AIBAST",
    "tags": ["healthcare", "tiered-huddles", "nursing-operations", "escalation", "hospital-operations"],
    "category": "healthcare",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---- DATA PLANE ------------------------------------------------------------
# Synthetic today; swap this block for the Dataverse tables behind the huddle board (issues, tiers, paging roster).
# Nothing below this block reads the constants directly; it calls _tiers(), _issues() and _roster().

HOSPITAL = "Cedarline Community Hospital"

# Tier order, the huddle each tier meets at, and the target each tier has to resolve or escalate an issue.
TIERS = [
    {"key": "unit", "name": "Tier 1", "scope": "Unit", "huddle": "08:30", "target_hours": 8},
    {"key": "department", "name": "Tier 2", "scope": "Department", "huddle": "09:15", "target_hours": 24},
    {"key": "operations", "name": "Tier 3", "scope": "Hospital operations", "huddle": "09:45", "target_hours": 48},
    {"key": "executive", "name": "Executive", "scope": "Leadership", "huddle": "10:30", "target_hours": 72},
]

# hours_in_tier is how long the issue has been in its current tier; the clock is the tier target minus that.
ISSUES = [
    {"id": "HB-2041", "tier": "unit", "unit": "4 West Med-Surg", "category": "Equipment",
     "title": "Two IV infusion pumps out of service; three scheduled infusions this shift at risk",
     "status": "Open - unit cannot fix", "owner": "Elena Brooks", "originator": "Jordan Pike",
     "waiting_on": "Elena Brooks", "hours_in_tier": 10, "hours_open": 10,
     "keywords": ["iv pump", "infusion pump", "pump", "iv"],
     "unit_tried": "Borrowed one pump from 4 East overnight (returned at 07:00) and opened biomedical ticket BME-5531.",
     "impact": "Three scheduled infusions this shift have no pump; one antibiotic dose is due at 14:00."},
    {"id": "HB-2043", "tier": "unit", "unit": "4 West Med-Surg", "category": "Staffing",
     "title": "Night shift short one registered nurse tonight",
     "status": "In progress", "owner": "Elena Brooks", "originator": "Elena Brooks",
     "waiting_on": "Lena Ford", "hours_in_tier": 3, "hours_open": 3,
     "keywords": ["night shift", "short", "staffing", "rn", "registered nurse"],
     "unit_tried": "Offered the open shift to the unit float list.",
     "impact": "Ratio rises to 1:6 on nights if the shift stays open."},
    {"id": "HB-2038", "tier": "unit", "unit": "4 West Med-Surg", "category": "Safety",
     "title": "Bed exit alarm in room 412 failing intermittently",
     "status": "Mitigated - awaiting originator confirmation", "owner": "Elena Brooks", "originator": "Jordan Pike",
     "waiting_on": "Jordan Pike", "hours_in_tier": 18, "hours_open": 18,
     "keywords": ["bed alarm", "bed exit", "412", "alarm"],
     "mitigation": "Biomedical engineering replaced the sensor pad; the fall-risk patient stays in room 409 "
                   "until the alarm holds for 24 hours (two full shifts).",
     "hold_hours_required": 24, "hold_hours_done": 16,
     "unit_tried": "Moved the fall-risk patient to room 409.",
     "impact": "A fall-risk patient cannot use room 412 until the alarm is proven."},
    {"id": "HB-2033", "tier": "department", "unit": "2 North Surgical", "category": "Safety",
     "title": "Call light system dropped calls from four rooms",
     "status": "Mitigated - awaiting originator confirmation", "owner": "Rachel Ng", "originator": "Amir Sadeghi",
     "waiting_on": "Amir Sadeghi", "hours_in_tier": 14, "hours_open": 21,
     "keywords": ["call light", "nurse call", "2 north"],
     "mitigation": "The vendor reset the room controllers; hourly rounding stays in place until the system holds "
                   "for a full 12-hour shift.",
     "hold_hours_required": 12, "hold_hours_done": 12,
     "unit_tried": "Started hourly rounding on the four rooms.",
     "impact": "Four rooms depend on hourly rounding instead of call lights."},
    {"id": "HB-2035", "tier": "department", "unit": "3 East Telemetry", "category": "Patient flow",
     "title": "Four telemetry beds held by patients waiting for step-down placement",
     "status": "In progress", "owner": "Rachel Ng", "originator": "Tessa Morgan",
     "waiting_on": "Case management", "hours_in_tier": 20, "hours_open": 26,
     "keywords": ["telemetry", "step-down", "beds", "3 east"],
     "unit_tried": "Placed step-down requests for all four patients.",
     "impact": "Telemetry admissions from the emergency department wait for a bed."},
    {"id": "HB-2029", "tier": "department", "unit": "Intensive Care Unit", "category": "Quality",
     "title": "Central line bundle audit at 82% against a 95% goal",
     "status": "In progress", "owner": "Owen Price", "originator": "Owen Price",
     "waiting_on": "Owen Price", "hours_in_tier": 6, "hours_open": 6,
     "keywords": ["central line", "bundle", "audit", "icu"],
     "unit_tried": "Added a second check at the dressing change.",
     "impact": "Infection-prevention risk on lines placed this week."},
    {"id": "HB-2031", "tier": "operations", "unit": "Emergency Department", "category": "Patient flow",
     "title": "Five admitted patients boarding in the emergency department for more than 6 hours",
     "status": "Decision needed", "owner": "Victor Hale", "originator": "Sofia Grant",
     "waiting_on": "Leadership huddle", "hours_in_tier": 52, "hours_open": 70,
     "keywords": ["boarding", "boarder", "emergency", "emergency department", "ed", "surge"],
     "escalation_reason": "Opening the six-bed surge unit on 5 South needs house-wide staffing and overtime that "
                          "exceed hospital operations authority.",
     "decision": "Approve opening the six-bed surge unit on 5 South for 72 hours with agency staffing.",
     "unit_tried": "Expedited discharges before 11:00 on three units.",
     "impact": "Admitted patients wait in emergency bays; ambulance diversion risk rises after 18:00."},
    {"id": "HB-2027", "tier": "executive", "unit": "Pharmacy", "category": "Supplies",
     "title": "Heparin flush supplier backorder; nine days of stock on hand",
     "status": "Decision needed", "owner": "Naomi Carter", "originator": "Felix Osei",
     "waiting_on": "Leadership huddle", "hours_in_tier": 30, "hours_open": 96,
     "keywords": ["heparin", "flush", "backorder", "supplier", "pharmacy"],
     "escalation_reason": "Switching to the alternate supplier changes a contract at a higher unit cost, which "
                          "needs executive approval.",
     "decision": "Approve the alternate heparin flush supplier at the higher unit cost for 60 days.",
     "unit_tried": "Moved to conservation dosing and pooled stock across units.",
     "impact": "Stock runs out in nine days at current use."},
    {"id": "HB-2019", "tier": "department", "unit": "4 West Med-Surg", "category": "Supplies",
     "title": "Wound-care dressing par levels too low on weekends",
     "status": "Closed - originator confirmed the fix held", "owner": "Rachel Ng", "originator": "Jordan Pike",
     "waiting_on": "", "hours_in_tier": 40, "hours_open": 120,
     "keywords": ["dressing", "par level", "wound"],
     "mitigation": "Supply chain raised weekend par levels by 30%.",
     "hold_hours_required": 48, "hold_hours_done": 48,
     "unit_tried": "Borrowed dressings from 4 East on weekends.",
     "impact": "None after the change."},
]

# Who each tier pages in Microsoft Teams, by issue category. The authorized workflow sends the page; the agent drafts it.
ROSTER = {
    "unit": {"default": [("Elena Brooks", "Nurse Manager, 4 West"), ("Jordan Pike", "Charge Nurse, 4 West")]},
    "department": {
        "Equipment": [("Rachel Ng", "Director of Medical-Surgical Nursing"),
                      ("Marcus Bell", "Biomedical Engineering Supervisor")],
        "Staffing": [("Rachel Ng", "Director of Medical-Surgical Nursing"), ("Lena Ford", "Staffing Office Manager")],
        "default": [("Rachel Ng", "Director of Medical-Surgical Nursing")],
    },
    "operations": {
        "Equipment": [("Victor Hale", "Director of Hospital Operations"),
                      ("Grace Holloway", "Administrator on Duty")],
        "default": [("Victor Hale", "Director of Hospital Operations"), ("Grace Holloway", "Administrator on Duty")],
    },
    "executive": {"default": [("Naomi Carter", "Chief Nursing Officer"), ("Daniel Reyes", "Chief Operating Officer")]},
}

DEFAULT_VIEWER = "Elena Brooks"


def _tiers():
    """Replace with the tier configuration table. Everything downstream is unchanged."""
    return TIERS


def _issues():
    """Replace with the huddle-board issue query. Everything downstream is unchanged."""
    return ISSUES


def _roster():
    """Replace with the paging roster table. Everything downstream is unchanged."""
    return ROSTER

# ---- END DATA PLANE --------------------------------------------------------


BOUNDARY = ("> Read-only synthetic snapshot of a fictional hospital. No issue was escalated, closed or changed and "
            "no one was paged; an authorized person confirms every step.")


def _now():
    return datetime.now()


def _tier(key):
    return next(t for t in _tiers() if t["key"] == key)


def _next_tier(key):
    keys = [t["key"] for t in _tiers()]
    index = keys.index(key)
    return _tiers()[index + 1] if index + 1 < len(keys) else None


def _is_closed(issue):
    return issue["status"].startswith("Closed")


def _is_mitigated(issue):
    return issue["status"].startswith("Mitigated")


def _remaining(issue):
    """Hours left on the issue's clock at its current tier (negative means past target)."""
    return _tier(issue["tier"])["target_hours"] - issue["hours_in_tier"]


def _past_target(issue):
    """A mitigated item runs a hold clock instead of its tier clock, so it is never counted as past target."""
    return not _is_closed(issue) and not _is_mitigated(issue) and _remaining(issue) < 0


def _clock(issue):
    if _is_closed(issue):
        return "Closed"
    if _is_mitigated(issue):
        return f"Hold {issue['hold_hours_done']} of {issue['hold_hours_required']} h"
    left = _remaining(issue)
    if left < 0:
        return f"{-left} h past target"
    return f"{left} h left"


def _keyword_hit(keyword, text):
    """Whole-word match, with an optional plural: 'ed' must not hit 'fixed', 'iv' must not hit 'five'. A hyphen or
    space between words is optional, so 'nurse call' meets 'nurse-call'."""
    parts = [re.escape(p) for p in re.split(r"[\s-]+", keyword.strip().lower()) if p]
    return re.search(r"\b" + r"[\s-]*".join(parts) + r"(?:s|es)?\b", text) is not None


def _id_named(item_id, text):
    """True when the id appears anywhere in the text, with its hyphen, a space or nothing: 'HB-2038', 'issue hb 2038'
    and 'hb2038' all name HB-2038."""
    parts = [re.escape(p) for p in str(item_id).lower().split("-") if p]
    return re.search(r"\b" + r"[\s-]?".join(parts) + r"\b", text) is not None


def _resolve_issue(value, default):
    """Issue id or words from its title; empty -> the default issue; no match -> None; a tie -> the tied issues.

    Keywords match whole words only. Each issue scores the words in the keywords it matches, so a specific phrase
    such as 'emergency department' outweighs a single shared word; when two issues score the same, the caller asks
    which one was meant instead of guessing.
    """
    if not value:
        return next(i for i in _issues() if i["id"] == default)
    q = str(value).lower().strip()
    for issue in _issues():
        if q == issue["id"].lower():
            return issue
    named = [issue for issue in _issues() if _id_named(issue["id"], q)]
    if named:
        return named[0] if len(named) == 1 else named
    scores = []
    for issue in _issues():
        score = sum(len(k.split()) for k in issue["keywords"] if _keyword_hit(k, q))
        if q in issue["title"].lower():
            score += 100
        if score:
            scores.append((score, issue))
    if not scores:
        return None
    best = max(score for score, _ in scores)
    tied = [issue for score, issue in scores if score == best]
    return tied[0] if len(tied) == 1 else tied


def _people():
    """Every person on the board or the paging roster, by full name."""
    names = {name for lanes in _roster().values() for people in lanes.values() for name, _ in people}
    names |= {i["owner"] for i in _issues()} | {i["originator"] for i in _issues()}
    return sorted(n for n in names if n)


def _resolve_viewer(value):
    """The person asking: a full name, a first or last name, a name with a title ('Elena', 'Brooks',
    'Elena Brooks, Nurse Manager'), or a role on the paging roster on its own ('Charge Nurse, 4 West', 'charge
    nurse'). Returns a name, a list of names on a tie (a role several people hold, such as Director), or None when
    nobody matches.

    A waiting-on value that is not a person (Case management, Leadership huddle) still matches when it is named in
    full.
    """
    text = str(value).strip()
    low = text.lower()
    for issue in _issues():
        if issue["waiting_on"] and issue["waiting_on"].lower() == low:
            return issue["waiting_on"]
    for name in _people():
        if name.lower() == low:
            return name
    asked = set(re.findall(r"[a-z0-9]+", low))
    scores = []
    for name in _people():
        parts = set(re.findall(r"[a-z]+", name.lower()))
        hit = len(parts & asked)
        if hit:
            scores.append((hit, name))
    if not scores:
        scores = _role_scores(asked)
    if not scores:
        return None
    best = max(hit for hit, _ in scores)
    tied = [name for hit, name in scores if hit == best]
    return tied[0] if len(tied) == 1 else tied


_ROLE_FILLER = {"i", "im", "m", "am", "the", "a", "an", "of", "on", "for", "and", "this", "is", "me", "it", "s"}


def _role_scores(asked):
    """(Words shared, person) for every person whose paging-roster role shares a word with the request, so a viewer
    who gives only their role ('Charge Nurse, 4 West', 'Nurse Manager') is found."""
    words = asked - _ROLE_FILLER
    roles = {}
    for lanes in _roster().values():
        for people in lanes.values():
            for name, role in people:
                roles.setdefault(name, set()).update(re.findall(r"[a-z0-9]+", role.lower()))
    return [(len(parts & words), name) for name, parts in sorted(roles.items()) if parts & words]


def _open(issues):
    return [i for i in issues if not _is_closed(i)]


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

OPERATIONS = ["board_view", "escalation_draft", "closure_check", "leadership_decisions"]


class TieredHuddleBoardAgent(BasicAgent):
    """Tiered huddle board agent for hospital operations (read-only, synthetic)."""

    def __init__(self):
        self.name = "TieredHuddleBoardAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                "Answers questions about the hospital's tiered huddle board: the whole board with every lane and "
                "clock, what is past target, what is waiting on me, escalating an issue the unit cannot fix to the "
                "next tier and who gets paged, whether a mitigated issue can be closed, and what the 10:30 "
                "leadership huddle needs to decide today. Always call this tool for huddle, board, tier, "
                "escalation, page, clock or closure questions from nurse managers, charge nurses, directors and "
                "executives. Call it right away; every operation has demo defaults. It is read-only: it drafts "
                "escalations and pages but cannot send, move or close anything, so never offer to send them; the "
                "issue owner confirms on the huddle board itself."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": list(OPERATIONS),
                        "description": (
                            "board_view for the whole board, every lane and clock, what is past target and what is "
                            "waiting on the person asking; escalation_draft to move an issue the unit or department "
                            "cannot fix up one tier, restart its clock and list who to page; closure_check for "
                            "whether a mitigated or fixed issue can come off the board; leadership_decisions for "
                            "what the 10:30 leadership huddle must decide today, with reason and clock."
                        ),
                    },
                    "issue": {
                        "type": "string",
                        "description": (
                            "Issue id such as HB-2041 or words from it such as 'IV pumps' or 'bed alarm in 412'. "
                            "Optional; escalation defaults to the 4 West IV pump issue and closure to the room 412 "
                            "bed alarm."
                        ),
                    },
                    "viewer": {
                        "type": "string",
                        "description": "Person asking, for 'waiting on me': a full name, first or last name, "
                                       "with or without a title, or their role on the paging roster. Optional; defaults to Elena Brooks, "
                                       "Nurse Manager of 4 West.",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation", "board_view")
        handlers = {
            "board_view": self._board_view,
            "escalation_draft": self._escalation_draft,
            "closure_check": self._closure_check,
            "leadership_decisions": self._leadership_decisions,
        }
        handler = handlers.get(op)
        if not handler:
            return f"**Error:** Unknown operation `{op}`. Operations: {', '.join(OPERATIONS)}."
        return handler(**kwargs)

    # -- board_view ---------------------------------------------------------
    def _board_view(self, **kwargs) -> str:
        asked = (kwargs.get("viewer") or DEFAULT_VIEWER).strip()
        resolved = _resolve_viewer(asked)
        viewer = resolved if isinstance(resolved, str) else asked
        now = _now()
        live = _open(_issues())
        past = sorted([i for i in live if _past_target(i)], key=_remaining)
        mine = [i for i in live if isinstance(resolved, str) and i["waiting_on"] == resolved]
        waiting = f"**Waiting on {viewer}:** {len(mine)}" if isinstance(resolved, str) else \
            f"**Waiting on {viewer}:** not shown (see below)"
        lines = [
            f"# Huddle Board - {HOSPITAL}",
            "",
            f"**As of:** {now:%A %d %B, %H:%M} | **Open items:** {len(live)} | "
            f"**Past target:** {len(past)} | {waiting}",
            "",
        ]
        if past:
            worst = past[0]
            lines.append(f"**Act first:** {worst['id']} ({worst['unit']}) is {_clock(worst)} at "
                         f"{_tier(worst['tier'])['name']}: {worst['title']}.")
            lines.append("")
        lines += ["| Lane | Item | Unit | Issue | Clock | Status | Waiting on |",
                  "|------|------|------|-------|-------|--------|------------|"]
        for tier in _tiers():
            for i in live:
                if i["tier"] == tier["key"]:
                    lines.append(f"| {tier['name']} ({tier['target_hours']} h) | {i['id']} | {i['unit']} | "
                                 f"{i['title']} | {_clock(i)} | {i['status']} | {i['waiting_on']} |")
        lines += ["", f"## Waiting on {viewer}"]
        if resolved is None:
            lines.append(f"- `{asked}` is not a name on this board or its paging roster, nor a role on that roster, "
                         "so this view cannot say what is waiting on them. Ask again with the full name as it "
                         "appears on the board.")
        elif isinstance(resolved, list):
            lines.append(f"- `{asked}` matches more than one person: {', '.join(resolved)}. Ask again with the "
                         "full name.")
        elif mine:
            lines += [f"- {i['id']}: {i['title']} ({_clock(i)})" for i in mine]
        else:
            lines.append(f"- Nothing on the board is waiting on {viewer}.")
        lines += ["", BOUNDARY]
        return "\n".join(lines)

    # -- escalation_draft -----------------------------------------------------
    def _escalation_draft(self, **kwargs) -> str:
        issue = _resolve_issue(kwargs.get("issue"), "HB-2041")
        if issue is None:
            return self._unknown(kwargs.get("issue"))
        if isinstance(issue, list):
            return self._ambiguous(kwargs.get("issue"), issue)
        current = _tier(issue["tier"])
        target = _next_tier(issue["tier"])
        if _is_closed(issue):
            return (f"# Escalation Draft - {issue['id']}\n\n{issue['id']} is closed; there is nothing to escalate."
                    f"\n\n{BOUNDARY}")
        if _is_mitigated(issue):
            done, required = issue["hold_hours_done"], issue["hold_hours_required"]
            hold = (f"its {required}-hour hold is complete" if done >= required
                    else f"it is {done} of {required} hours into its hold period")
            return (f"# Escalation Draft - {issue['id']}\n\n{issue['id']} is mitigated and {hold}, so it is not "
                    f"escalated: a mitigated item runs a hold period instead of its tier clock. Mitigation: "
                    f"{issue['mitigation']}\n\nIt closes when {issue['originator']} (who raised it) confirms the "
                    f"fix held; run a closure check for that. If the fix fails, it goes back on its "
                    f"{current['name']} clock and can be escalated then. No escalation was drafted and no one was "
                    f"paged.\n\n{BOUNDARY}")
        if target is None:
            return (f"# Escalation Draft - {issue['id']}\n\n{issue['id']} is already at the {current['name']} tier, "
                    f"the top of the board. It stays on the {current['huddle']} leadership huddle until decided."
                    f"\n\n{BOUNDARY}")
        roster = _roster()[target["key"]]
        page = roster.get(issue["category"], roster["default"])
        due = _now() + timedelta(hours=target["target_hours"])
        reason = (f"{issue['unit']} cannot resolve this at {current['name']}. Impact: {issue['impact']} "
                  f"Already tried: {issue['unit_tried']}")
        lines = [
            f"# Escalation Draft - {issue['id']}: {current['name']} to {target['name']}",
            "",
            f"**Issue:** {issue['title']} ({issue['unit']}, {issue['category']})",
            f"**Current clock:** {_clock(issue)} at {current['name']} (target {current['target_hours']} h)",
            f"**New clock:** restarts at the {target['name']} target of {target['target_hours']} h, due "
            f"{due:%a %H:%M}; reviewed at the {target['huddle']} {target['scope'].lower()} huddle",
            "",
            "## Reason the next tier reads first",
            reason,
            "",
            "## Page in Microsoft Teams on confirmation",
        ]
        lines += [f"- {name}, {role}" for name, role in page]
        lines += [f"- Copy: {issue['originator']} (raised the issue)", "",
                  "**Status:** Draft - waiting for one confirmation from the issue owner "
                  f"({issue['owner']}) on the huddle board. This agent cannot send it: the board's authorized "
                  "escalation step moves the tier and sends the Teams pages. Nothing has moved tiers and no one "
                  "has been paged.", "", BOUNDARY]
        return "\n".join(lines)

    # -- closure_check --------------------------------------------------------
    def _closure_check(self, **kwargs) -> str:
        issue = _resolve_issue(kwargs.get("issue"), "HB-2038")
        if issue is None:
            return self._unknown(kwargs.get("issue"))
        if isinstance(issue, list):
            return self._ambiguous(kwargs.get("issue"), issue)
        lines = [f"# Closure Check - {issue['id']}", "", f"**Issue:** {issue['title']} ({issue['unit']})",
                 f"**Raised by:** {issue['originator']} | **Owner:** {issue['owner']} | **Status:** {issue['status']}",
                 ""]
        if _is_closed(issue):
            lines.append(f"**Closed.** {issue['originator']} confirmed the fix held after "
                         f"{issue['hold_hours_done']} h. Fix: {issue['mitigation']}")
        elif _is_mitigated(issue):
            left = issue["hold_hours_required"] - issue["hold_hours_done"]
            lines += [
                "**Can it close now? No. Mitigated is not closed.**",
                f"Only {issue['originator']}, who raised it, can confirm the fix held.",
                "",
                f"**Mitigation:** {issue['mitigation']}",
                f"**Hold period:** {issue['hold_hours_done']} of {issue['hold_hours_required']} h done"
                + (f"; {left} h to go before {issue['originator']} is asked to confirm." if left > 0 else
                   f"; complete. Ask {issue['originator']} to confirm the fix held at the next huddle."),
            ]
        else:
            lines += [f"**Can it close now? No.** {issue['id']} is not mitigated yet ({_clock(issue)} at "
                      f"{_tier(issue['tier'])['name']}).",
                      f"Once it is mitigated, {issue['originator']} must confirm the fix held before it closes."]
        waiting = [i for i in _issues() if _is_mitigated(i) and i["id"] != issue["id"]]
        if waiting:
            lines += ["", "**Other mitigated items waiting on their originator:** "
                      + "; ".join(f"{i['id']} ({i['originator']})" for i in waiting)]
        lines += ["", BOUNDARY]
        return "\n".join(lines)

    # -- leadership_decisions -------------------------------------------------
    def _leadership_decisions(self, **kwargs) -> str:
        live = _open(_issues())
        decisions = [i for i in live if i.get("decision")]
        decisions.sort(key=_remaining)
        watch = [i for i in live if not i.get("decision") and _past_target(i)]
        executive = _tier("executive")
        lines = [
            f"# Leadership Huddle - {executive['huddle']}, {_now():%A %d %B}",
            "",
            f"**{len(decisions)} decisions needed today**, most urgent first.",
            "",
            "| Item | Lane | Decision needed | Reason | Clock | Owner |",
            "|------|------|-----------------|--------|-------|-------|",
        ]
        for i in decisions:
            lines.append(f"| {i['id']} | {_tier(i['tier'])['name']} | {i['decision']} | "
                         f"{i['escalation_reason']} | {_clock(i)} | {i['owner']} |")
        if watch:
            lines += ["", "**Past target below this huddle (for awareness):** "
                      + "; ".join(f"{i['id']} {i['unit']} ({_clock(i)} at {_tier(i['tier'])['name']})"
                                  for i in watch)]
        lines += ["", "> Recommendation only: leadership records each decision on the board. " + BOUNDARY[2:]]
        return "\n".join(lines)

    def _ambiguous(self, value, issues) -> str:
        return (f"# Which issue did you mean?\n\n`{value}` matches more than one item on the board equally well, so "
                "none was picked. Name one of these by its id:\n\n"
                + "\n".join(f"- {i['id']}: {i['title']} ({i['unit']})" for i in issues) + f"\n\n{BOUNDARY}")

    def _unknown(self, value) -> str:
        return (f"# Unknown Issue\n\nNo item on the synthetic board matches `{value}`; no substitute issue was used. "
                f"Items: {', '.join(i['id'] for i in _issues())}.\n\n{BOUNDARY}")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = TieredHuddleBoardAgent()
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
