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
     "keywords": ["night shift", "short", "staffing", "rn"],
     "unit_tried": "Offered the open shift to the unit float list.",
     "impact": "Ratio rises to 1:6 on nights if the shift stays open."},
    {"id": "HB-2038", "tier": "unit", "unit": "4 West Med-Surg", "category": "Safety",
     "title": "Bed exit alarm in room 412 failing intermittently",
     "status": "Mitigated - awaiting originator confirmation", "owner": "Elena Brooks", "originator": "Jordan Pike",
     "waiting_on": "Jordan Pike", "hours_in_tier": 18, "hours_open": 18,
     "keywords": ["bed alarm", "bed exit", "412", "alarm"],
     "mitigation": "Biomedical engineering replaced the sensor pad; the fall-risk patient stays in room 409 "
                   "until the alarm holds for a full shift.",
     "hold_hours_required": 24, "hold_hours_done": 16,
     "unit_tried": "Moved the fall-risk patient to room 409.",
     "impact": "A fall-risk patient cannot use room 412 until the alarm is proven."},
    {"id": "HB-2033", "tier": "department", "unit": "2 North Surgical", "category": "Safety",
     "title": "Call light system dropped calls from four rooms",
     "status": "Mitigated - awaiting originator confirmation", "owner": "Rachel Ng", "originator": "Amir Sadeghi",
     "waiting_on": "Amir Sadeghi", "hours_in_tier": 14, "hours_open": 21,
     "keywords": ["call light", "nurse call", "2 north"],
     "mitigation": "The vendor reset the room controllers; hourly rounding stays in place until the system holds "
                   "for a full shift.",
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
     "keywords": ["boarding", "emergency", "ed", "surge"],
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


def _resolve_issue(value, default):
    """Issue id or words from its title; empty -> the default issue; no match -> None."""
    if not value:
        return next(i for i in _issues() if i["id"] == default)
    q = str(value).lower().strip()
    for issue in _issues():
        if q == issue["id"].lower():
            return issue
    for issue in _issues():
        if any(k in q for k in issue["keywords"]) or q in issue["title"].lower():
            return issue
    return None


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
                        "description": "Person asking, for 'waiting on me'. Optional; defaults to Elena Brooks, "
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
        viewer = (kwargs.get("viewer") or DEFAULT_VIEWER).strip()
        now = _now()
        live = _open(_issues())
        past = sorted([i for i in live if _past_target(i)], key=_remaining)
        mine = [i for i in live if i["waiting_on"].lower() == viewer.lower()]
        lines = [
            f"# Huddle Board - {HOSPITAL}",
            "",
            f"**As of:** {now:%A %d %B, %H:%M} | **Open items:** {len(live)} | "
            f"**Past target:** {len(past)} | **Waiting on {viewer}:** {len(mine)}",
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
        if mine:
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
        current = _tier(issue["tier"])
        target = _next_tier(issue["tier"])
        if _is_closed(issue):
            return (f"# Escalation Draft - {issue['id']}\n\n{issue['id']} is closed; there is nothing to escalate."
                    f"\n\n{BOUNDARY}")
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
