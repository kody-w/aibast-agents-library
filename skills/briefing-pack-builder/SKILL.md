---
name: "briefing-pack-builder"
description: "Briefing desk for the fictional City of Contoso Budget Office. Always use this tool to list briefing formats, scan the content set, check figures, draft a brief, find gaps and look up the approval route. Routing: 'what formats/templates' -> list_templates; 'what do we hold/have on <topic>' -> content_scan; 'do any figures disagree/conflict' -> figure_check; 'draft/prepare/build the <format> brief' -> draft_brief; 'which sections need input/are missing' -> gap_report; 'who signs off/how long' -> approval_route. Topics: elm_street_bridge (Elm Street Bridge Replacement, the default) and library_renovation (Central Library Renovation). Templates: budget_hearing (default), council_question, rapid_response, executive, decision_memo. Every operation has a demo default, so call it right away. Never approves, files, sends or publishes a brief."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "briefing_pack_builder_agent.py"
  tool-name: "BriefingPackBuilderAgent"
  agent-sha256: "66db05eb81c8f9ccb170ccd3a501a77a49672f96fb126025bec1a63c8ddac4b3"
  version: "1.0.0"
  author: "AIBAST"
  tags: "government, state-and-local, briefing, budget-hearing, document-drafting"
---

# Briefing Pack Builder

Briefing desk for the fictional City of Contoso Budget Office. Always use this tool to list briefing formats, scan the content set, check figures, draft a brief, find gaps and look up the approval route. Routing: 'what formats/templates' -> list_templates; 'what do we hold/have on <topic>' -> content_scan; 'do any figures disagree/conflict' -> figure_check; 'draft/prepare/build the <format> brief' -> draft_brief; 'which sections need input/are missing' -> gap_report; 'who signs off/how long' -> approval_route. Topics: elm_street_bridge (Elm Street Bridge Replacement, the default) and library_renovation (Central Library Renovation). Templates: budget_hearing (default), council_question, rapid_response, executive, decision_memo. Every operation has a demo default, so call it right away. Never approves, files, sends or publishes a brief.

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "list_templates",
        "content_scan",
        "figure_check",
        "draft_brief",
        "gap_report",
        "approval_route"
      ],
      "description": "list_templates for formats; content_scan for what the content set holds; figure_check for conflicting figures; draft_brief to draft; gap_report for missing sections; approval_route for sign-off."
    },
    "template": {
      "type": "string",
      "enum": [
        "budget_hearing",
        "council_question",
        "rapid_response",
        "executive",
        "decision_memo"
      ],
      "description": "Briefing format (default budget_hearing)"
    },
    "topic": {
      "type": "string",
      "enum": [
        "elm_street_bridge",
        "library_renovation"
      ],
      "description": "Brief topic (default elm_street_bridge)"
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
   python3 scripts/run.py --json '{"operation": "<string>", "template": "<string>", "topic": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=66db05eb81c8f9ccb170ccd3a501a77a49672f96fb126025bec1a63c8ddac4b3 -->
```python
"""
Briefing Pack Builder Agent

Builds draft government briefs (budget hearing brief, council question brief,
rapid response brief, executive brief, council decision memo) from a single
synthetic document library. Each draft cites the document behind every
statement, lists any measure whose value differs between documents for a
person to settle, and marks uncovered sections as needing input.

Where a real deployment would search an approved document library, this agent
uses a fixed synthetic content set so it runs anywhere without credentials. It
never approves, files, sends or publishes a brief: it returns drafts for the
responsible officers to check and route for sign-off.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))

from basic_agent import BasicAgent

# ═══════════════════════════════════════════════════════════════
# RAPP AGENT MANIFEST
# ═══════════════════════════════════════════════════════════════
__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/briefing-pack-builder",
    "version": "1.0.0",
    "display_name": "Briefing Pack Builder Agent",
    "description": "Turn a government team's source documents into cited, template-ready briefs in minutes, with conflicting figures flagged and missing content named, so specialists verify instead of rebuild.",
    "author": "AIBAST",
    "tags": ["government", "state-and-local", "briefing", "budget-hearing", "document-drafting"],
    "category": "slg_government",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ═══════════════════════════════════════════════════════════════
# SYNTHETIC DATA LAYER (fixed content set, indexed 2026-04-06)
# ═══════════════════════════════════════════════════════════════

_ORG = "City of Contoso"
_TEAM = "Budget Office briefing team"
_INDEXED = "2026-04-06"

_TEMPLATES = {
    "budget_hearing": {
        "title": "Budget Hearing Brief", "audience": "Mayor and council members, for the annual budget hearing",
        "sections": ["Summary", "Key figures", "Budget status", "Cost change explanation",
                     "Staffing", "Talking points", "Likely questions", "Risks"],
        "route": ("Deputy City Manager", "City Manager", 8),
    },
    "council_question": {
        "title": "Council Question Brief", "audience": "Mayor, for a council question session",
        "sections": ["Likely question", "Proposed answer", "Facts to cite", "Follow-up lines"],
        "route": ("Department Director", "Mayor's Office", 2),
    },
    "rapid_response": {
        "title": "Rapid Response Brief", "audience": "Mayor and City Manager",
        "sections": ["Situation", "Where things stand", "Recent changes", "Public and press interest", "Suggested lines"],
        "route": ("City Manager", "Mayor's Office", 1),
    },
    "executive": {
        "title": "Executive Brief", "audience": "City Manager",
        "sections": ["Why this brief", "Context", "Progress", "Cost picture", "Recommended action"],
        "route": ("Deputy City Manager", "City Manager", 4),
    },
    "decision_memo": {
        "title": "Council Decision Memo", "audience": "City Council",
        "sections": ["Decision sought", "Context", "Issues to weigh", "Cost picture", "Recommended action", "Sign-off"],
        "route": ("City Manager", "City Council", 6),
    },
}

_TOPICS = {
    "elm_street_bridge": "Elm Street Bridge Replacement",
    "library_renovation": "Central Library Renovation",
}

_DOCS = {
    "DOC-01": "FY27 Adopted Capital Budget - Transportation",
    "DOC-02": "Elm Street Bridge Project Fact Sheet (January)",
    "DOC-03": "Quarterly Capital Status Report (Q2 FY27)",
    "DOC-04": "Public Works Staffing Workbook",
    "DOC-05": "Council Meeting Transcript (February 10)",
    "DOC-06": "Community Engagement Summary - Elm Street Bridge",
    "DOC-07": "Central Library Renovation Scope Note",
    "DOC-08": "Briefing Approval Route Guide",
}

# Passages: (doc, topic, section tags, text). Sections are tagged when the content set was indexed.
_PASSAGES = [
    ("DOC-01", "elm_street_bridge", ["Summary", "Context", "Why this brief", "Situation", "Decision sought"],
     "The Elm Street Bridge Replacement replaces the 1962 two-lane bridge with a four-lane structure and a shared path."),
    ("DOC-01", "elm_street_bridge", ["Key figures", "Budget status", "Cost picture", "Facts to cite"],
     "Approved budget $48.6 million; $19.2 million expended to date; completion forecast Q3 FY28."),
    ("DOC-02", "elm_street_bridge", ["Key figures", "Progress", "Where things stand"],
     "Approved budget $48.6 million. Foundations complete; deck works 40 percent complete."),
    ("DOC-03", "elm_street_bridge", ["Budget status", "Cost change explanation", "Recent changes", "Cost picture", "Issues to weigh", "Follow-up lines"],
     "Revised approved budget $51.3 million after change order CO-7; $21.7 million expended to date. The $2.7 million increase reflects steel price escalation and utility relocation."),
    ("DOC-03", "elm_street_bridge", ["Risks", "Issues to weigh", "Follow-up lines"],
     "Utility relocation is two months behind schedule; the Q3 FY28 completion date is at risk if it slips further."),
    ("DOC-04", "elm_street_bridge", ["Staffing"],
     "Project team establishment 16 FTE; 14 FTE filled after 2 engineer vacancies in December."),
    ("DOC-05", "elm_street_bridge", ["Likely questions", "Likely question"],
     "Council members asked how long the Elm Street detour will last and whether the project will exceed its budget."),
    ("DOC-06", "elm_street_bridge", ["Public and press interest", "Risks"],
     "312 public comments received; detour length was the top concern, raised in 141 comments."),
    ("DOC-07", "library_renovation", ["Summary", "Context", "Why this brief", "Situation", "Decision sought"],
     "The Central Library Renovation refurbishes the 1978 building and adds a children's learning floor."),
    ("DOC-07", "library_renovation", ["Key figures", "Budget status", "Cost picture", "Facts to cite"],
     "Approved budget $12.4 million; design phase complete; construction tender planned for July."),
]

# Measures cross-checked across documents for each topic.
_FIGURES = {
    "elm_street_bridge": [
        ("Approved budget", [("$48.6 million", ["DOC-01", "DOC-02"]), ("$51.3 million", ["DOC-03"])]),
        ("Expended to date", [("$19.2 million", ["DOC-01"]), ("$21.7 million", ["DOC-03"])]),
        ("Completion forecast", [("Q3 FY28", ["DOC-01", "DOC-03"])]),
    ],
    "library_renovation": [
        ("Approved budget", [("$12.4 million", ["DOC-07"])]),
    ],
}

_GATE = (
    "Synthetic content set only. This agent drafts; it does not approve, file, send or "
    "publish a brief. Responsible officers verify every figure and route the brief for sign-off."
)
_SOURCE = "Source: [Synthetic Briefing Content Set, indexed 2026-04-06]\nAgents: BriefingPackBuilderAgent"
_GAP_TEXT = "Not covered by the content set - input needed from the owning department."


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _resolve(value, options, default):
    if not value:
        return default
    q = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    for key in options:
        if key == q or key in q:
            return key
    return None


def _topic_passages(topic):
    return [p for p in _PASSAGES if p[1] == topic]


def _section_sources(topic, section):
    return [p for p in _topic_passages(topic) if section in p[2]]


def _conflicts(topic):
    return [(m, vals) for m, vals in _FIGURES[topic] if len(vals) > 1]


# ═══════════════════════════════════════════════════════════════
# AGENT CLASS
# ═══════════════════════════════════════════════════════════════

_OPERATIONS = [
    "list_templates", "content_scan", "figure_check",
    "draft_brief", "gap_report", "approval_route",
]


class BriefingPackBuilderAgent(BasicAgent):
    """
    Briefing pack builder.

    Operations:
        list_templates - available briefing formats, audiences and sections
        content_scan   - what the content set holds on a topic, by document
        figure_check   - measures that carry different values in different documents
        draft_brief    - cited draft of a template on a topic, gaps named, never approved
        gap_report     - sections of a template with no supporting content
        approval_route - reviewer, approver and turnaround for a template
    """

    def __init__(self):
        self.name = "BriefingPackBuilderAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                "Briefing desk for the fictional City of Contoso Budget Office. Always use this tool to "
                "list briefing formats, scan the content set, check figures, draft a brief, find gaps and "
                "look up the approval route. Routing: 'what formats/templates' -> list_templates; 'what do "
                "we hold/have on <topic>' -> content_scan; 'do any figures disagree/conflict' -> "
                "figure_check; 'draft/prepare/build the <format> brief' -> draft_brief; 'which sections "
                "need input/are missing' -> gap_report; 'who signs off/how long' -> approval_route. Topics: "
                "elm_street_bridge (Elm Street Bridge Replacement, the default) and library_renovation "
                "(Central Library Renovation). Templates: budget_hearing (default), council_question, "
                "rapid_response, executive, decision_memo. Every operation has a demo default, so call it "
                "right away. Never approves, files, sends or publishes a brief."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": list(_OPERATIONS),
                        "description": (
                            "list_templates for formats; content_scan for what the content set holds; "
                            "figure_check for conflicting figures; draft_brief to draft; gap_report for "
                            "missing sections; approval_route for sign-off."
                        ),
                    },
                    "template": {
                        "type": "string",
                        "enum": list(_TEMPLATES),
                        "description": "Briefing format (default budget_hearing)",
                    },
                    "topic": {
                        "type": "string",
                        "enum": list(_TOPICS),
                        "description": "Brief topic (default elm_street_bridge)",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation") or "list_templates"
        if op not in _OPERATIONS:
            return f"Unknown operation: {op}. Available: {', '.join(_OPERATIONS)}."
        template = _resolve(kwargs.get("template"), _TEMPLATES, "budget_hearing")
        if template is None:
            return (f"No briefing template named '{kwargs.get('template')}'. Templates: "
                    f"{', '.join(_TEMPLATES)}.\n\n{_GATE}\n\n{_SOURCE}")
        topic = _resolve(kwargs.get("topic"), _TOPICS, "elm_street_bridge")
        if topic is None:
            return (f"The content set holds nothing on '{kwargs.get('topic')}'. Topics: "
                    f"{', '.join(_TOPICS.values())}.\n\n{_GATE}\n\n{_SOURCE}")
        if op == "list_templates":
            return self._list_templates()
        if op == "content_scan":
            return self._content_scan(topic)
        if op == "figure_check":
            return self._figure_check(topic)
        if op == "draft_brief":
            return self._draft_brief(template, topic)
        if op == "gap_report":
            return self._gap_report(template, topic)
        return self._approval_route(template)

    # ── list_templates ────────────────────────────────────────
    def _list_templates(self):
        rows = "\n".join(
            f"| {key} | {t['title']} | {t['audience']} | {len(t['sections'])}: {', '.join(t['sections'])} |"
            for key, t in _TEMPLATES.items()
        )
        return (
            f"**Briefing Templates: {_ORG} {_TEAM}**\n\n"
            f"| Key | Format | Audience | Sections |\n|---|---|---|---|\n{rows}\n\n"
            f"Each format is a template entry, so adding a format needs no code change. "
            f"Content set: {len(_DOCS)} documents indexed {_INDEXED}.\n\n"
            f"**Next step:** name a topic and I will show what the content set holds on it.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── content_scan ──────────────────────────────────────────
    def _content_scan(self, topic):
        passages = _topic_passages(topic)
        counts = {}
        for p in passages:
            counts[p[0]] = counts.get(p[0], 0) + 1
        rows = "\n".join(f"| {d} | {_DOCS[d]} | {n} |" for d, n in counts.items())
        conflicts = len(_conflicts(topic))
        return (
            f"**Content Scan: {_TOPICS[topic]}**\n\n"
            f"Searched {len(_DOCS)} indexed documents ({len(_PASSAGES)} passages); {len(passages)} passages "
            f"on topic across {len(counts)} documents.\n\n"
            f"| Document | Title | Passages on topic |\n|---|---|---|\n{rows}\n\n"
            f"**Measures with conflicting values:** {conflicts}. Run a figure check before drafting.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── figure_check ──────────────────────────────────────────
    def _figure_check(self, topic):
        lines = []
        for measure, vals in _FIGURES[topic]:
            shown = "; ".join(f"{v} ({', '.join(d)})" for v, d in vals)
            status = "Conflict - confirm before use" if len(vals) > 1 else "Consistent"
            lines.append(f"| {measure} | {shown} | {status} |")
        n = len(_conflicts(topic))
        note = (
            "**Figures needing confirmation:** the content set carries two values for these measures. The later "
            "status report reflects change order CO-7, but the brief owner must confirm which is current; "
            "this agent does not choose between them."
            if n else "**No conflicting figures** for this topic in the content set."
        )
        return (
            f"**Figure Check: {_TOPICS[topic]}**\n\n"
            f"| Measure | Values found (documents) | Status |\n|---|---|---|\n" + "\n".join(lines) + "\n\n"
            f"{n} conflicting measures.\n\n{note}\n\n{_GATE}\n\n{_SOURCE}"
        )

    # ── draft_brief ───────────────────────────────────────────
    def _draft_brief(self, template, topic):
        t = _TEMPLATES[template]
        body, gaps, cited = [], [], []
        for section in t["sections"]:
            sources = _section_sources(topic, section)
            if not sources:
                gaps.append(section)
                body.append(f"### {section}\n{_GAP_TEXT}")
                continue
            text = " ".join(f"{p[3]} [{p[0]}]" for p in sources)
            for p in sources:
                if p[0] not in cited:
                    cited.append(p[0])
            body.append(f"### {section}\n{text}")
        conflicts = _conflicts(topic)
        confirm = ""
        if conflicts:
            confirm = "### Figures needing confirmation\n" + "\n".join(
                f"- {m}: " + " vs ".join(f"{v} ({', '.join(d)})" for v, d in vals) for m, vals in conflicts
            ) + "\n\n"
        reviewer, approver, days = t["route"]
        return (
            f"**{t['title']} - {_TOPICS[topic]}** (DRAFT - not approved)\n\n"
            f"Audience: {t['audience']}. Drafted from {len(_DOCS)} indexed documents "
            f"({len(_topic_passages(topic))} passages on topic).\n\n"
            + "\n\n".join(body) + "\n\n" + confirm +
            f"**Sources:** " + "; ".join(f"{d} {_DOCS[d]}" for d in cited) + "\n\n"
            f"**Gaps:** {len(gaps)} ({', '.join(gaps) if gaps else 'none'}).\n"
            f"**Approval route:** {reviewer} reviews, {approver} approves, {days} working days.\n\n"
            f"Status: Draft for officer review - not approved, filed or sent.\n\n{_GATE}\n\n{_SOURCE}"
        )

    # ── gap_report ────────────────────────────────────────────
    def _gap_report(self, template, topic):
        t = _TEMPLATES[template]
        rows, gaps = [], 0
        for section in t["sections"]:
            n = len(_section_sources(topic, section))
            if n == 0:
                gaps += 1
            rows.append(f"| {section} | {n} | {'Gap - needs input' if n == 0 else 'Covered'} |")
        owner = "Communications and the project director" if template == "budget_hearing" else "the owning department"
        return (
            f"**Gap Report: {t['title']} - {_TOPICS[topic]}**\n\n"
            f"| Section | Cited passages | Status |\n|---|---|---|\n" + "\n".join(rows) + "\n\n"
            f"**{gaps} of {len(t['sections'])} sections need input.** Gap sections are left as \"{_GAP_TEXT}\" "
            f"and are never filled from general knowledge.\n\n"
            f"**Next step:** request the missing content from {owner} before the brief goes for review.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── approval_route ────────────────────────────────────────
    def _approval_route(self, template):
        t = _TEMPLATES[template]
        reviewer, approver, days = t["route"]
        rows = "\n".join(
            f"| {x['title']} | {x['route'][0]} | {x['route'][1]} | {x['route'][2]} |" for x in _TEMPLATES.values()
        )
        return (
            f"**Approval Route: {t['title']}**\n\n"
            f"| Step | Owner |\n|---|---|\n"
            f"| 1. Draft and cite | {_TEAM} (this agent prepares the draft) |\n"
            f"| 2. Verify figures and fill gaps | Owning department |\n"
            f"| 3. Review | {reviewer} |\n"
            f"| 4. Approve | {approver} |\n\n"
            f"**Turnaround:** {days} working days from a complete draft.\n\n"
            f"| Format | Reviewer | Approver | Working days |\n|---|---|---|---|\n{rows}\n\n"
            f"Sign-off stays with people: the agent never marks a draft as approved, and the briefing "
            f"log stays the record of status. No brief was sent for approval.\n\n{_GATE}\n\n{_SOURCE}"
        )


if __name__ == "__main__":
    agent = BriefingPackBuilderAgent()
    story = [
        {"operation": "list_templates"},
        {"operation": "content_scan", "topic": "elm_street_bridge"},
        {"operation": "figure_check", "topic": "elm_street_bridge"},
        {"operation": "draft_brief", "template": "budget_hearing", "topic": "elm_street_bridge"},
        {"operation": "gap_report", "template": "budget_hearing", "topic": "elm_street_bridge"},
        {"operation": "approval_route", "template": "budget_hearing"},
    ]
    for kw in story:
        print("=" * 60)
        print(agent.perform(**kw))
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
