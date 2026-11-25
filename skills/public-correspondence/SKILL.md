---
name: "public-correspondence"
description: "Use this tool for a public-works correspondence team working through resident letters, emails, web forms and phone notes in a fictional snapshot. It lists what is waiting to be answered (inbox_queue), splits one letter into its separate questions (break_down_enquiry), finds the approved past responses that answer each question (find_precedents), names the owning team and writes the referral question for any part with no approved answer (route_and_refer), drafts the cited reply for officer review (draft_response), and proposes adding newly approved wording to the precedent library so the question is never re-asked (library_update). Pass item_id as the item number: COR-2042 is the scanned letter from E. Okafor (the default), COR-2041 the email from Hannah Cole, COR-2043 the web form from Dan Whitfield, COR-2044 the phone note from Rosa Martinez. Every output is a draft or recommendation: nothing is sent, no one is contacted and no record changes."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "public_correspondence_response_agent.py"
  tool-name: "PublicCorrespondenceAgent"
  agent-sha256: "45564b5071ed5c0d1577e8a82d49b969f2d96a23615d505bbbaa29d4c2b7d09e"
  version: "1.0.0"
  author: "AIBAST"
  tags: "government, correspondence, constituent-services, public-works, drafting, knowledge-reuse"
---

# Public Correspondence

Use this tool for a public-works correspondence team working through resident letters, emails, web forms and phone notes in a fictional snapshot. It lists what is waiting to be answered (inbox_queue), splits one letter into its separate questions (break_down_enquiry), finds the approved past responses that answer each question (find_precedents), names the owning team and writes the referral question for any part with no approved answer (route_and_refer), drafts the cited reply for officer review (draft_response), and proposes adding newly approved wording to the precedent library so the question is never re-asked (library_update). Pass item_id as the item number: COR-2042 is the scanned letter from E. Okafor (the default), COR-2041 the email from Hannah Cole, COR-2043 the web form from Dan Whitfield, COR-2044 the phone note from Rosa Martinez. Every output is a draft or recommendation: nothing is sent, no one is contacted and no record changes.

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "inbox_queue",
        "break_down_enquiry",
        "find_precedents",
        "route_and_refer",
        "draft_response",
        "library_update"
      ],
      "description": "inbox_queue for 'what do I need to answer' or the day's queue; break_down_enquiry to split a letter into separate questions; find_precedents for which approved past responses cover each question; route_and_refer for who owns each part and what to ask about the unanswered part; draft_response to draft or write the reply; library_update when a team will supply or has supplied approved wording and the user asks how to add it to the precedent library or make sure nobody has to ask again."
    },
    "item_id": {
      "type": "string",
      "enum": [
        "COR-2041",
        "COR-2042",
        "COR-2043",
        "COR-2044"
      ],
      "description": "Correspondence item: COR-2042 E. Okafor letter (default), COR-2041 Hannah Cole, COR-2043 Dan Whitfield, COR-2044 Rosa Martinez."
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
   python3 scripts/run.py --json '{"operation": "<string>", "item_id": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=45564b5071ed5c0d1577e8a82d49b969f2d96a23615d505bbbaa29d4c2b7d09e -->
```python
"""
Public Correspondence Agent

Helps a public-sector correspondence team answer letters, emails, web forms and
phone notes from residents: see the day's queue, split a multi-part enquiry into
its separate questions, find the approved past responses that already answer
each one, route the parts nobody has answered yet to the owning team, and
assemble a cited draft reply that a correspondence officer reviews and sends.

Where a real deployment would read a correspondence system, a document library
of approved responses and a team directory, this agent uses a fixed synthetic
snapshot so it runs anywhere without credentials.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))

from basic_agent import BasicAgent

# ═══════════════════════════════════════════════════════════════
# RAPP AGENT MANIFEST
# ═══════════════════════════════════════════════════════════════
__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/public-correspondence-response",
    "version": "1.0.0",
    "display_name": "Public Correspondence Agent",
    "description": "Answer every part of every resident enquiry from approved precedent: triage the correspondence queue, break multi-part letters into separate questions, cite approved past responses, route unanswered points to the owning team, and prepare a reviewable draft reply.",
    "author": "AIBAST",
    "tags": ["government", "correspondence", "constituent-services", "public-works", "drafting", "knowledge-reuse"],
    "category": "slg_government",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ═══════════════════════════════════════════════════════════════
# SYNTHETIC DATA LAYER (fixed snapshot: Monday 9 March 2026)
# ═══════════════════════════════════════════════════════════════

_SNAPSHOT = "Mon 9 Mar 2026"
_ORG = "Northwind County Public Works"
_OFFICER = "Alex Rivera"
_APPROVER = "Jamie Lee, Director of Community Relations"
_TARGET_DAYS = 15
_MATCH_THRESHOLD = 0.50

_TEAMS = {
    "project": "Project Delivery",
    "traffic": "Traffic Operations",
    "noise": "Environment and Noise",
    "trees": "Landscape and Urban Forestry",
    "property": "Property and Land",
    "community": "Community Engagement",
}

_PRECEDENTS = {
    "APR-102": {
        "title": "Driveway and property access during construction",
        "team": "project", "approved": "12 Nov 2025",
        "text": ("Access to every driveway is kept open throughout the works. Where a driveway must close "
                 "for concrete work, residents receive at least 48 hours' notice and the closure lasts no "
                 "longer than 8 hours."),
    },
    "APR-103": {
        "title": "Resident parking during works",
        "team": "traffic", "approved": "20 Nov 2025",
        "text": ("Kerbside parking is suspended only on the block being worked that day; temporary resident "
                 "permits for the next street are issued free of charge on request."),
    },
    "APR-104": {
        "title": "Harbor Road night works schedule and noise limits",
        "team": "noise", "approved": "3 Dec 2025",
        "text": ("Night works on Harbor Road run from 8 pm to 5 am, Monday to Thursday, for no more than 12 "
                 "nights in total. Noise is monitored on site and the loudest activities finish before 11 pm."),
    },
    "APR-105": {
        "title": "Business loading access near the bus interchange",
        "team": "traffic", "approved": "15 Jan 2026",
        "text": ("A dedicated loading bay stays open on the side street from 6 am to 10 am every weekday "
                 "while the interchange is built."),
    },
    "APR-106": {
        "title": "Street tree removal and replacement planting",
        "team": "trees", "approved": "28 Jan 2026",
        "text": ("Two street trees on Harbor Road are removed because the new footpath sits over their root "
                 "zones. Each removed tree is replaced with two advanced trees in the autumn planting season."),
    },
    "APR-107": {
        "title": "Mill Creek Bridge detour routes",
        "team": "traffic", "approved": "4 Feb 2026",
        "text": ("Cyclists and pedestrians use the signed detour over the Station Street crossing, adding about "
                 "600 metres; the detour is lit and stays open around the clock."),
    },
    "APR-108": {
        "title": "Mill Creek Bridge program timeline",
        "team": "project", "approved": "4 Feb 2026",
        "text": ("The bridge renewal is scheduled to finish in late October 2026, weather permitting; "
                 "the published program is updated monthly."),
    },
}

_ITEMS = {
    "cor-2041": {
        "id": "COR-2041", "sender": "Hannah Cole", "channel": "Email",
        "project": "Harbor Road Upgrade", "received": "Mon 23 Feb 2026", "due": "Mon 16 Mar 2026",
        "days_left": 5, "primary": "noise",
        "summary": "Night works noise, weekend hours and resident parking",
        "elements": [
            {"q": "When do the night works happen and how loud will they be?", "topic": "Noise and hours",
             "match": "APR-104", "score": 0.88, "team": "noise"},
            {"q": "Will crews work on weekends?", "topic": "Work hours",
             "match": "APR-104", "score": 0.74, "team": "noise"},
            {"q": "Where can residents park while the street is closed?", "topic": "Parking",
             "match": "APR-103", "score": 0.69, "team": "traffic"},
        ],
    },
    "cor-2042": {
        "id": "COR-2042", "sender": "E. Okafor", "channel": "Scanned letter",
        "project": "Harbor Road Upgrade", "received": "Thu 26 Feb 2026", "due": "Thu 19 Mar 2026",
        "days_left": 8, "primary": "project",
        "summary": "Night works, driveway access, tree removal and a property-value concern",
        "elements": [
            {"q": "When will the night works outside my house happen, and how loud will they be?",
             "topic": "Noise and hours", "match": "APR-104", "score": 0.86, "team": "noise"},
            {"q": "Will I still be able to use my driveway during the works?",
             "topic": "Property access", "match": "APR-102", "score": 0.81, "team": "project"},
            {"q": "Why are the two street trees being removed, and will they be replaced?",
             "topic": "Street trees", "match": "APR-106", "score": 0.78, "team": "trees"},
            {"q": "Will the upgrade reduce my property value, and can I claim compensation?",
             "topic": "Compensation", "match": "APR-102", "score": 0.22, "team": "property"},
        ],
        "referral": ("Please provide approved wording on how property-value concerns are handled on the "
                     "Harbor Road Upgrade and whether, and how, an owner can lodge a compensation claim."),
        "input_by": "Tue 17 Mar 2026",
        "proposal": {"id": "APR-109", "title": "Property value and compensation enquiries"},
    },
    "cor-2043": {
        "id": "COR-2043", "sender": "Dan Whitfield", "channel": "Web form",
        "project": "Mill Creek Bridge Renewal", "received": "Mon 2 Mar 2026", "due": "Mon 23 Mar 2026",
        "days_left": 10, "primary": "project",
        "summary": "Cyclist detour and completion date",
        "elements": [
            {"q": "What is the detour route for cyclists while the bridge is closed?", "topic": "Detours",
             "match": "APR-107", "score": 0.83, "team": "traffic"},
            {"q": "When will the bridge reopen?", "topic": "Timeline",
             "match": "APR-108", "score": 0.79, "team": "project"},
        ],
    },
    "cor-2044": {
        "id": "COR-2044", "sender": "Rosa Martinez", "channel": "Phone note",
        "project": "Central Station Bus Interchange", "received": "Wed 4 Mar 2026", "due": "Wed 25 Mar 2026",
        "days_left": 12, "primary": "community",
        "summary": "Delivery loading access and support for a small business during works",
        "elements": [
            {"q": "Where can suppliers unload deliveries for my shop during construction?", "topic": "Loading access",
             "match": "APR-105", "score": 0.80, "team": "traffic"},
            {"q": "Is there any support for small businesses that lose trade during the works?",
             "topic": "Business support", "match": "APR-105", "score": 0.31, "team": "community"},
        ],
        "referral": ("Please provide approved wording on what support, if any, is offered to small businesses "
                     "near the Central Station Bus Interchange works."),
        "input_by": "Mon 23 Mar 2026",
        "proposal": {"id": "APR-110", "title": "Small-business support during construction"},
    },
}

_ORDER = ["cor-2041", "cor-2042", "cor-2043", "cor-2044"]

_GATE = (
    "Synthetic correspondence support only. This agent drafts and recommends; it does not send a reply, "
    "contact a resident or team, change a record, or approve wording. A correspondence officer reviews, "
    "edits and sends every response."
)


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _resolve_item(query):
    """Item ID (case-insensitive); default COR-2042; None when no item has that ID (never another item)."""
    if not query:
        return "cor-2042"
    q = str(query).lower().strip()
    return q if q in _ITEMS else None


def _covered(el):
    return el["score"] >= _MATCH_THRESHOLD


def _footer(source):
    return f"{_GATE}\n\nSource: [{source}]\nAgents: PublicCorrespondenceAgent"


# ═══════════════════════════════════════════════════════════════
# AGENT CLASS
# ═══════════════════════════════════════════════════════════════

_OPERATIONS = [
    "inbox_queue", "break_down_enquiry", "find_precedents",
    "route_and_refer", "draft_response", "library_update",
]


class PublicCorrespondenceAgent(BasicAgent):
    """
    Public correspondence response assistant.

    Operations:
        inbox_queue         - the correspondence waiting for a response, soonest due first
        break_down_enquiry  - split one item into its separate questions
        find_precedents     - match each question to an approved past response, or flag a gap
        route_and_refer     - owning team per question and a referral note for each gap
        draft_response      - cited draft reply that answers every question (never sent)
        library_update      - proposal to add newly approved wording to the precedent library
    """

    def __init__(self):
        self.name = "PublicCorrespondenceAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                "Use this tool for a public-works correspondence team working through resident letters, "
                "emails, web forms and phone notes in a fictional snapshot. It lists what is waiting to be "
                "answered (inbox_queue), splits one letter into its separate questions (break_down_enquiry), "
                "finds the approved past responses that answer each question (find_precedents), names the "
                "owning team and writes the referral question for any part with no approved answer "
                "(route_and_refer), drafts the cited reply for officer review (draft_response), and proposes "
                "adding newly approved wording to the precedent library so the question is never re-asked "
                "(library_update). Pass item_id as the item number: COR-2042 is the scanned letter from E. Okafor "
                "(the default), COR-2041 the email from Hannah Cole, COR-2043 the web form from Dan Whitfield, COR-2044 "
                "the phone note from Rosa Martinez. Every output is a "
                "draft or recommendation: nothing is sent, no one is contacted and no record changes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": list(_OPERATIONS),
                        "description": (
                            "inbox_queue for 'what do I need to answer' or the day's queue; break_down_enquiry "
                            "to split a letter into separate questions; find_precedents for which approved past "
                            "responses cover each question; route_and_refer for who owns each part and what to "
                            "ask about the unanswered part; draft_response to draft or write the reply; "
                            "library_update when a team will supply or has supplied approved wording and the user asks how to add it "
                            "to the precedent library or make sure nobody has to ask again."
                        ),
                    },
                    "item_id": {
                        "type": "string",
                        "enum": ["COR-2041", "COR-2042", "COR-2043", "COR-2044"],
                        "description": "Correspondence item: COR-2042 E. Okafor letter (default), COR-2041 Hannah Cole, COR-2043 Dan Whitfield, COR-2044 Rosa Martinez.",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation", "inbox_queue")
        dispatch = {
            "inbox_queue": self._inbox_queue,
            "break_down_enquiry": self._break_down,
            "find_precedents": self._find_precedents,
            "route_and_refer": self._route_and_refer,
            "draft_response": self._draft_response,
            "library_update": self._library_update,
        }
        handler = dispatch.get(op)
        if not handler:
            return f"Unknown operation: {op}"
        if op == "inbox_queue":
            return handler()
        key = _resolve_item(kwargs.get("item_id", ""))
        if key is None:
            known = ", ".join(f"{_ITEMS[k]['id']} ({_ITEMS[k]['sender']})" for k in _ORDER)
            return (
                f"No synthetic correspondence item matches '{kwargs.get('item_id')}'. "
                f"Items in the snapshot: {known}.\n\n{_footer('Synthetic Correspondence Snapshot')}"
            )
        return handler(key)

    # ── inbox_queue ───────────────────────────────────────────
    def _inbox_queue(self):
        rows, total_q, total_gaps = [], 0, 0
        for key in _ORDER:
            it = _ITEMS[key]
            gaps = sum(1 for el in it["elements"] if not _covered(el))
            total_q += len(it["elements"])
            total_gaps += gaps
            rows.append(
                f"| {it['id']} | {it['sender']} | {it['channel']} | {it['project']} | "
                f"{len(it['elements'])} | {gaps} | {it['due']} ({it['days_left']} business days) |"
            )
        first = _ITEMS[_ORDER[0]]
        return (
            f"**Correspondence Queue: {_ORG}** (snapshot {_SNAPSHOT})\n\n"
            f"| Item | Sender | Channel | Project | Questions | No precedent | Due |\n"
            f"|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n\n"
            f"**Totals:** {len(_ORDER)} items waiting, {total_q} separate questions, {total_gaps} with no "
            f"approved precedent. Response target: {_TARGET_DAYS} business days from receipt.\n\n"
            f"**Due soonest:** {first['id']} from {first['sender']} ({first['days_left']} business days).\n"
            f"**Recommended next:** COR-2042 from E. Okafor is the most complex item: 4 questions, one with "
            f"no approved precedent. Break it down first.\n\n"
            f"{_footer('Synthetic Correspondence Snapshot')}"
        )

    # ── break_down_enquiry ────────────────────────────────────
    def _break_down(self, key):
        it = _ITEMS[key]
        rows = "\n".join(
            f"| Q{i} | {el['q']} | {el['topic']} |" for i, el in enumerate(it["elements"], 1)
        )
        return (
            f"**Enquiry Breakdown: {it['id']} from {it['sender']}**\n\n"
            f"| Detail | Value |\n|---|---|\n"
            f"| Channel | {it['channel']} |\n"
            f"| Project | {it['project']} |\n"
            f"| Received | {it['received']} |\n"
            f"| Response due | {it['due']} ({it['days_left']} business days left) |\n"
            f"| Overall intent | {it['summary']} |\n\n"
            f"**{len(it['elements'])} separate questions** (every one must be answered in the reply):\n\n"
            f"| # | Question | Topic |\n|---|---|---|\n{rows}\n\n"
            f"**Next step:** match each question to an approved past response.\n\n"
            f"{_footer('Synthetic Correspondence Snapshot')}"
        )

    # ── find_precedents ───────────────────────────────────────
    def _find_precedents(self, key):
        it = _ITEMS[key]
        rows, covered = [], 0
        for i, el in enumerate(it["elements"], 1):
            if _covered(el):
                covered += 1
                p = _PRECEDENTS[el["match"]]
                rows.append(f"| Q{i} | {el['topic']} | {el['match']}: {p['title']} | {el['score']:.2f} | Covered |")
            else:
                rows.append(f"| Q{i} | {el['topic']} | None above threshold (best {el['score']:.2f}) | "
                            f"{el['score']:.2f} | No approved precedent |")
        gaps = len(it["elements"]) - covered
        return (
            f"**Approved Precedent Match: {it['id']}**\n\n"
            f"| # | Topic | Closest approved response | Match | Result |\n|---|---|---|---|---|\n"
            + "\n".join(rows) + "\n\n"
            f"**Coverage:** {covered} of {len(it['elements'])} questions covered by approved precedent; "
            f"{gaps} with no approved precedent. Match threshold {_MATCH_THRESHOLD:.2f}.\n\n"
            + ("**Next step:** route the uncovered question to its owning team for approved wording.\n\n"
               if gaps else "**Next step:** every question has approved wording; draft the reply.\n\n")
            + f"{_footer('Synthetic Approved Response Library')}"
        )

    # ── route_and_refer ───────────────────────────────────────
    def _route_and_refer(self, key):
        it = _ITEMS[key]
        rows = "\n".join(
            f"| Q{i} | {el['topic']} | {_TEAMS[el['team']]} | "
            f"{'Covered by ' + el['match'] if _covered(el) else 'Needs team input'} |"
            for i, el in enumerate(it["elements"], 1)
        )
        gaps = [(i, el) for i, el in enumerate(it["elements"], 1) if not _covered(el)]
        if gaps:
            i, el = gaps[0]
            referral = (
                f"**Referral note (draft, not sent)**\n\n"
                f"| Field | Value |\n|---|---|\n"
                f"| To | {_TEAMS[el['team']]} |\n"
                f"| About | {it['id']} Q{i}: {el['topic']} |\n"
                f"| Question | {it['referral']} |\n"
                f"| Input needed by | {it['input_by']} (2 business days before the response is due) |\n\n"
            )
        else:
            referral = "**Referral:** none needed; every question is covered by approved precedent.\n\n"
        return (
            f"**Routing: {it['id']} from {it['sender']}**\n\n"
            f"**Coordinating team:** {_TEAMS[it['primary']]} (owns the {it['project']} response)\n\n"
            f"| # | Topic | Owning team | Status |\n|---|---|---|---|\n{rows}\n\n"
            f"{referral}"
            f"The referral note is a draft for the officer to send through the approved channel. "
            f"No team was contacted.\n\n"
            f"{_footer('Synthetic Team Directory + Approved Response Library')}"
        )

    # ── draft_response ────────────────────────────────────────
    def _draft_response(self, key):
        it = _ITEMS[key]
        paras, cited, flagged = [], 0, 0
        for i, el in enumerate(it["elements"], 1):
            if _covered(el):
                cited += 1
                paras.append(f"**{i}. {el['topic']}.** {_PRECEDENTS[el['match']]['text']} [Source: {el['match']}]")
            else:
                flagged += 1
                paras.append(
                    f"**{i}. {el['topic']}.** [OFFICER TO DEVELOP: no approved precedent for this question. "
                    f"Suggested approach: acknowledge the concern, confirm it has been referred to "
                    f"{_TEAMS[el['team']]}, and insert their approved wording before sign-off.]"
                )
        body = "\n\n".join(paras)
        return (
            f"**Draft Reply: {it['id']} (DRAFT, NOT SENT)**\n\n"
            f"| Detail | Value |\n|---|---|\n"
            f"| To | {it['sender']} |\n"
            f"| Re | {it['project']}: your {it['channel'].lower()} received {it['received']} |\n"
            f"| Prepared for | {_OFFICER}, correspondence officer |\n"
            f"| Sign-off | {_APPROVER} |\n"
            f"| Status | Draft for officer review |\n\n"
            f"Dear {it['sender']},\n\nThank you for writing to {_ORG} about the {it['project']}. "
            f"You raised {len(it['elements'])} questions, and we answer each one below.\n\n"
            f"{body}\n\nYours sincerely,\n{_ORG}\n\n"
            f"**Coverage:** {len(it['elements'])} of {len(it['elements'])} questions addressed; "
            f"{cited} cited from approved precedent; {flagged} flagged for officer development.\n\n"
            f"Review the wording, complete any flagged section, and send through the approved channel. "
            f"No email was sent.\n\n"
            f"{_footer('Synthetic Approved Response Library')}"
        )

    # ── library_update ────────────────────────────────────────
    def _library_update(self, key):
        it = _ITEMS[key]
        gaps = [(i, el) for i, el in enumerate(it["elements"], 1) if not _covered(el)]
        if not gaps:
            return (
                f"**Precedent Library Update: {it['id']}**\n\n"
                f"Every question in {it['id']} is already covered by approved precedent, so there is "
                f"nothing new to add to the library.\n\n"
                f"{_footer('Synthetic Approved Response Library')}"
            )
        i, el = gaps[0]
        prop = it["proposal"]
        same_topic = sum(
            1 for k in _ORDER for e in _ITEMS[k]["elements"] if e["topic"] == el["topic"] and not _covered(e)
        )
        return (
            f"**Precedent Library Update Proposal: {prop['id']}**\n\n"
            f"| Field | Value |\n|---|---|\n"
            f"| Proposed entry | {prop['id']}: {prop['title']} |\n"
            f"| Fills gap | {it['id']} Q{i} ({el['topic']}) |\n"
            f"| Wording owner | {_TEAMS[el['team']]} |\n"
            f"| Status | Proposed, pending knowledge-owner approval |\n"
            f"| Library size | {len(_PRECEDENTS)} approved responses, {len(_PRECEDENTS) + 1} once approved |\n\n"
            f"**How it works:** when {_TEAMS[el['team']]} returns approved wording, the knowledge owner "
            f"reviews it and adds it as {prop['id']}. From then on, questions on this topic match it like "
            f"any other approved response and are cited in drafts instead of being referred again "
            f"({same_topic} open question on this topic in today's queue).\n\n"
            f"Nothing was added to the library; the knowledge owner approves every new entry.\n\n"
            f"{_footer('Synthetic Approved Response Library')}"
        )


if __name__ == "__main__":
    agent = PublicCorrespondenceAgent()
    for op in _OPERATIONS:
        print("=" * 60)
        print(agent.perform(operation=op, item_id="COR-2042"))
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
