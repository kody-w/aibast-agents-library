---
name: "staffing-territory-planning"
description: "Territory planning desk for the fictional Contoso Staffing North Valley territory (metros Harbor City, Millbrook, Granite Ridge, Ashford Junction). Always use this tool for territory, market, coverage, competitor, labor-trend and territory-plan questions. Routing: snapshot or 'how does my territory look' -> territory_snapshot; 'how big is the market' (optionally for one metro) -> market_sizing; 'where are our gaps' -> coverage_gaps; 'who are we up against' -> competitive_landscape; labor or hiring trends -> labor_trends; 'draft my quarterly/territory plan' -> territory_plan. Every operation has a demo default, so call it right away. Never changes headcount, quotas, account assignments or CRM records."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "staffing_territory_planning_agent.py"
  tool-name: "StaffingTerritoryPlanningAgent"
  agent-sha256: "b60864abd74fe4ec9f498528c18b4b6dada06c3aa805de22246dee6fa0fe6a84"
  version: "1.0.0"
  author: "AIBAST"
  tags: "professional-services, staffing, territory-planning, market-sizing, sales-planning"
---

# Staffing Territory Planning

Territory planning desk for the fictional Contoso Staffing North Valley territory (metros Harbor City, Millbrook, Granite Ridge, Ashford Junction). Always use this tool for territory, market, coverage, competitor, labor-trend and territory-plan questions. Routing: snapshot or 'how does my territory look' -> territory_snapshot; 'how big is the market' (optionally for one metro) -> market_sizing; 'where are our gaps' -> coverage_gaps; 'who are we up against' -> competitive_landscape; labor or hiring trends -> labor_trends; 'draft my quarterly/territory plan' -> territory_plan. Every operation has a demo default, so call it right away. Never changes headcount, quotas, account assignments or CRM records.

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "territory_snapshot",
        "market_sizing",
        "coverage_gaps",
        "competitive_landscape",
        "labor_trends",
        "territory_plan"
      ],
      "description": "territory_snapshot for the overview; market_sizing for addressable spend; coverage_gaps for under-served lines; competitive_landscape for competitors; labor_trends for market trends; territory_plan for the draft quarterly plan."
    },
    "metro": {
      "type": "string",
      "enum": [
        "all",
        "Harbor City",
        "Millbrook",
        "Granite Ridge",
        "Ashford Junction"
      ],
      "description": "Metro for market_sizing: 'all' (default) or one of Harbor City, Millbrook, Granite Ridge, Ashford Junction"
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
   python3 scripts/run.py --json '{"operation": "<string>", "metro": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=b60864abd74fe4ec9f498528c18b4b6dada06c3aa805de22246dee6fa0fe6a84 -->
```python
"""
Staffing Territory Planning Agent

Territory planning assistant for a staffing firm's regional sales leader:
territory snapshot, market sizing, coverage gaps, competitive position, labor
trends and a draft quarterly territory plan.

Where a real deployment would read CRM accounts, placement history and labor
market feeds, this agent uses a fixed synthetic snapshot so it runs anywhere
without credentials. It never changes headcount, quotas, account assignments or
CRM records: it returns analysis and a draft plan for sales leadership to decide.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))

from basic_agent import BasicAgent

# ═══════════════════════════════════════════════════════════════
# RAPP AGENT MANIFEST
# ═══════════════════════════════════════════════════════════════
__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/staffing-territory-planning",
    "version": "1.0.0",
    "display_name": "Staffing Territory Planning Agent",
    "description": "Help staffing sales leaders size their territory, find where demand outruns recruiter coverage, read the competition and labor trends, and walk into the quarter with a draft plan grounded in the numbers.",
    "author": "AIBAST",
    "tags": ["professional-services", "staffing", "territory-planning", "market-sizing", "sales-planning"],
    "category": "professional_services",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ═══════════════════════════════════════════════════════════════
# SYNTHETIC DATA LAYER (fixed snapshot, Q3 planning cycle)
# ═══════════════════════════════════════════════════════════════

_FIRM = "Contoso Staffing"
_TERRITORY = "North Valley territory"
_LEADER = "Dana Whitfield, regional sales director"
_SNAPSHOT = "trailing 12 months to June 30"

_LINES = ["Light Industrial", "Office and Admin", "IT and Engineering", "Healthcare Support"]

# Annual addressable temporary-labor spend and our revenue, in $ millions, per metro and service line.
_METROS = {
    "Harbor City": {
        "addressable": [48.0, 22.0, 31.0, 14.0], "ours": [6.2, 2.9, 1.1, 0.4],
        "recruiters": 9, "clients": 64,
    },
    "Millbrook": {
        "addressable": [26.0, 9.0, 6.0, 11.0], "ours": [4.1, 1.2, 0.0, 0.9],
        "recruiters": 5, "clients": 38,
    },
    "Granite Ridge": {
        "addressable": [18.0, 7.0, 12.0, 9.0], "ours": [0.8, 0.6, 0.0, 0.0],
        "recruiters": 1, "clients": 9,
    },
    "Ashford Junction": {
        "addressable": [14.0, 5.0, 3.0, 6.0], "ours": [2.0, 0.7, 0.0, 0.5],
        "recruiters": 2, "clients": 17,
    },
}

# Competitor share of addressable spend, per metro (fictional firms).
_COMPETITORS = {
    "Fabrikam Workforce": {"Harbor City": 0.18, "Millbrook": 0.12, "Granite Ridge": 0.21, "Ashford Junction": 0.09},
    "Northwind Staffing": {"Harbor City": 0.11, "Millbrook": 0.15, "Granite Ridge": 0.06, "Ashford Junction": 0.14},
    "Litware Talent": {"Harbor City": 0.07, "Millbrook": 0.04, "Granite Ridge": 0.17, "Ashford Junction": 0.03},
}

# Labor trends per service line (synthetic market feed).
_TRENDS = {
    "Light Industrial": {"postings_yoy": 6, "wage_yoy": 4.2, "time_to_fill": 9},
    "Office and Admin": {"postings_yoy": -3, "wage_yoy": 2.1, "time_to_fill": 12},
    "IT and Engineering": {"postings_yoy": 11, "wage_yoy": 5.8, "time_to_fill": 31},
    "Healthcare Support": {"postings_yoy": 8, "wage_yoy": 4.9, "time_to_fill": 18},
}

_GAP_SHARE = 0.05          # a line is a coverage gap when our share is under 5%...
_GAP_MIN_SPEND = 9.0       # ...of at least $9.0M addressable spend
_METRO_KEYS = ["all"] + list(_METROS)

_GATE = (
    "Synthetic planning snapshot only. This agent does not change headcount, quotas, "
    "account assignments or CRM records; the plan is a draft for sales leadership to decide."
)
_SOURCE = "Source: [Synthetic Territory + Labor Market Snapshot]\nAgents: StaffingTerritoryPlanningAgent"


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _m(x):
    return f"${x:,.1f}M"


def _pct(x):
    return f"{x * 100:.1f}%"


def _metro_totals(name):
    m = _METROS[name]
    return round(sum(m["addressable"]), 1), round(sum(m["ours"]), 1)


def _territory_totals():
    addr = round(sum(sum(m["addressable"]) for m in _METROS.values()), 1)
    ours = round(sum(sum(m["ours"]) for m in _METROS.values()), 1)
    recruiters = sum(m["recruiters"] for m in _METROS.values())
    clients = sum(m["clients"] for m in _METROS.values())
    return addr, ours, recruiters, clients


def _gaps():
    """(metro, line, addressable, ours, share, open_spend) for every gap, largest open spend first."""
    out = []
    for name, m in _METROS.items():
        for i, line in enumerate(_LINES):
            a, o = m["addressable"][i], m["ours"][i]
            share = o / a
            if a >= _GAP_MIN_SPEND and share < _GAP_SHARE:
                out.append((name, line, a, o, share, round(a - o, 1)))
    out.sort(key=lambda g: -g[5])
    return out


def _resolve_metro(metro):
    if not metro:
        return "all"
    q = str(metro).strip().lower()
    if q in ("all", "territory", "north valley", "north valley territory"):
        return "all"
    for name in _METROS:
        if name.lower() in q or q in name.lower():
            return name
    return None


# ═══════════════════════════════════════════════════════════════
# AGENT CLASS
# ═══════════════════════════════════════════════════════════════

_OPERATIONS = [
    "territory_snapshot", "market_sizing", "coverage_gaps",
    "competitive_landscape", "labor_trends", "territory_plan",
]


class StaffingTerritoryPlanningAgent(BasicAgent):
    """
    Staffing territory planning assistant.

    Operations:
        territory_snapshot     - territory at a glance: spend, revenue, share, recruiters, clients per metro
        market_sizing          - addressable spend by service line for the territory or one metro
        coverage_gaps          - lines where demand outruns our share and recruiter coverage
        competitive_landscape  - fictional competitor share and our rank per metro
        labor_trends           - postings, wage and time-to-fill trends by service line
        territory_plan         - draft quarterly plan: opportunities, risks, recommendations, priority action
    """

    def __init__(self):
        self.name = "StaffingTerritoryPlanningAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                "Territory planning desk for the fictional Contoso Staffing North Valley territory "
                "(metros Harbor City, Millbrook, Granite Ridge, Ashford Junction). Always use this tool "
                "for territory, market, coverage, competitor, labor-trend and territory-plan questions. "
                "Routing: snapshot or 'how does my territory look' -> territory_snapshot; 'how big is "
                "the market' (optionally for one metro) -> market_sizing; 'where are our gaps' -> "
                "coverage_gaps; 'who are we up against' -> competitive_landscape; labor or hiring "
                "trends -> labor_trends; 'draft my quarterly/territory plan' -> territory_plan. Every "
                "operation has a demo default, so call it right away. Never changes headcount, quotas, "
                "account assignments or CRM records."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": list(_OPERATIONS),
                        "description": (
                            "territory_snapshot for the overview; market_sizing for addressable "
                            "spend; coverage_gaps for under-served lines; competitive_landscape for "
                            "competitors; labor_trends for market trends; territory_plan for the "
                            "draft quarterly plan."
                        ),
                    },
                    "metro": {
                        "type": "string",
                        "enum": list(_METRO_KEYS),
                        "description": "Metro for market_sizing: 'all' (default) or one of Harbor City, Millbrook, Granite Ridge, Ashford Junction",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation") or "territory_snapshot"
        dispatch = {
            "territory_snapshot": self._territory_snapshot,
            "coverage_gaps": self._coverage_gaps,
            "competitive_landscape": self._competitive_landscape,
            "labor_trends": self._labor_trends,
            "territory_plan": self._territory_plan,
        }
        if op == "market_sizing":
            metro = _resolve_metro(kwargs.get("metro"))
            if metro is None:
                return (
                    f"No metro named '{kwargs.get('metro')}' is in the {_TERRITORY}. "
                    f"Metros: {', '.join(_METROS)}.\n\n{_GATE}\n\n{_SOURCE}"
                )
            return self._market_sizing(metro)
        handler = dispatch.get(op)
        if not handler:
            return f"Unknown operation: {op}. Available: {', '.join(_OPERATIONS)}."
        return handler()

    # ── territory_snapshot ────────────────────────────────────
    def _territory_snapshot(self):
        addr, ours, rec, cli = _territory_totals()
        rows = []
        for name, m in _METROS.items():
            a, o = _metro_totals(name)
            rows.append(
                f"| {name} | {_m(a)} | {_m(o)} | {_pct(o / a)} | {m['recruiters']} | "
                f"{_m(round(a / m['recruiters'], 1))} | {m['clients']} |"
            )
        return (
            f"**Territory Snapshot: {_FIRM} {_TERRITORY}**\n\n"
            f"Prepared for {_LEADER} | Data: {_SNAPSHOT}\n\n"
            f"| Metro | Addressable spend | Our revenue | Our share | Recruiters | Spend per recruiter | Active clients |\n"
            f"|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n"
            f"| **Territory** | **{_m(addr)}** | **{_m(ours)}** | **{_pct(ours / addr)}** | **{rec}** | "
            f"**{_m(round(addr / rec, 1))}** | **{cli}** |\n\n"
            f"**Read:** Granite Ridge carries {_m(46.0)} of spend with 1 recruiter, more than three times "
            f"the territory's spend per recruiter.\n\n"
            f"**Next step:** size the Granite Ridge market, then review coverage gaps.\n\n{_GATE}\n\n{_SOURCE}"
        )

    # ── market_sizing ─────────────────────────────────────────
    def _market_sizing(self, metro):
        if metro == "all":
            addr_by_line = [round(sum(m["addressable"][i] for m in _METROS.values()), 1) for i in range(4)]
            ours_by_line = [round(sum(m["ours"][i] for m in _METROS.values()), 1) for i in range(4)]
            title = _TERRITORY
        else:
            addr_by_line, ours_by_line = _METROS[metro]["addressable"], _METROS[metro]["ours"]
            title = metro
        a_tot, o_tot = round(sum(addr_by_line), 1), round(sum(ours_by_line), 1)
        rows = "\n".join(
            f"| {line} | {_m(addr_by_line[i])} | {_m(ours_by_line[i])} | {_pct(ours_by_line[i] / addr_by_line[i])} | "
            f"{_m(round(addr_by_line[i] - ours_by_line[i], 1))} |"
            for i, line in enumerate(_LINES)
        )
        big = max(range(4), key=lambda i: addr_by_line[i] - ours_by_line[i])
        return (
            f"**Market Sizing: {title}**\n\n"
            f"| Service line | Addressable spend | Our revenue | Our share | Open spend |\n|---|---|---|---|---|\n"
            f"{rows}\n"
            f"| **Total** | **{_m(a_tot)}** | **{_m(o_tot)}** | **{_pct(o_tot / a_tot)}** | **{_m(round(a_tot - o_tot, 1))}** |\n\n"
            f"**Largest open spend:** {_LINES[big]} ({_m(round(addr_by_line[big] - ours_by_line[big], 1))}).\n\n"
            f"Addressable spend is the synthetic annual temporary-labor spend; open spend is addressable "
            f"spend not yet won by {_FIRM}.\n\n{_GATE}\n\n{_SOURCE}"
        )

    # ── coverage_gaps ─────────────────────────────────────────
    def _coverage_gaps(self):
        gaps = _gaps()
        rows = "\n".join(
            f"| {i + 1} | {g[0]} | {g[1]} | {_m(g[2])} | {_m(g[3])} | {_pct(g[4])} | {_m(g[5])} |"
            for i, g in enumerate(gaps)
        )
        open_total = round(sum(g[5] for g in gaps), 1)
        return (
            f"**Coverage Gaps: {_TERRITORY}**\n\n"
            f"Rule: a service line with at least {_m(_GAP_MIN_SPEND)} addressable spend where our share is under 5%.\n\n"
            f"| Rank | Metro | Service line | Addressable | Our revenue | Our share | Open spend |\n"
            f"|---|---|---|---|---|---|---|\n{rows}\n\n"
            f"**{len(gaps)} gaps, {_m(open_total)} open spend.** The two largest are IT and Engineering in "
            f"Harbor City and Light Industrial in Granite Ridge.\n\n"
            f"**Next step:** check who holds these markets today before deciding where to add recruiters.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── competitive_landscape ─────────────────────────────────
    def _competitive_landscape(self):
        rows = []
        for name in _METROS:
            a, o = _metro_totals(name)
            shares = [(c, s[name]) for c, s in _COMPETITORS.items()] + [(_FIRM, round(o / a, 3))]
            shares.sort(key=lambda x: -x[1])
            rank = [c for c, _ in shares].index(_FIRM) + 1
            leader = shares[0]
            rows.append(
                f"| {name} | {leader[0]} ({_pct(leader[1])}) | {_pct(o / a)} | {rank} of {len(shares)} |"
            )
        return (
            f"**Competitive Landscape: {_TERRITORY}**\n\n"
            f"| Metro | Share leader | {_FIRM} share | Our rank |\n|---|---|---|---|\n"
            + "\n".join(rows) + "\n\n"
            f"**Competitor profiles (synthetic):**\n"
            f"- Fabrikam Workforce: volume light-industrial player; leads Harbor City and Granite Ridge.\n"
            f"- Northwind Staffing: strongest in Millbrook and Ashford Junction office and admin.\n"
            f"- Litware Talent: IT and engineering specialist; 17.0% of Granite Ridge.\n\n"
            f"**Read:** we rank last in Granite Ridge, where Litware Talent's IT focus meets our zero IT revenue.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── labor_trends ──────────────────────────────────────────
    def _labor_trends(self):
        rows = "\n".join(
            f"| {line} | {t['postings_yoy']:+d}% | {t['wage_yoy']:+.1f}% | {t['time_to_fill']} days |"
            for line, t in _TRENDS.items()
        )
        return (
            f"**Labor Trends: {_TERRITORY}**\n\n"
            f"| Service line | Job postings (YoY) | Median wage (YoY) | Time to fill |\n|---|---|---|---|\n"
            f"{rows}\n\n"
            f"**Read:** IT and Engineering postings are up 11% with a 31-day time to fill, the slowest "
            f"fill and fastest growth; Office and Admin postings are down 3%.\n\n"
            f"**Planning implication:** recruiter capacity for IT and Engineering is the constraint; "
            f"bill rates should reflect the 5.8% wage movement.\n\n{_GATE}\n\n{_SOURCE}"
        )

    # ── territory_plan ────────────────────────────────────────
    def _territory_plan(self):
        gaps = _gaps()[:3]
        addr, ours, rec, _cli = _territory_totals()
        opps = "\n".join(
            f"{i + 1}. {g[0]} {g[1]}: {_m(g[5])} open spend at {_pct(g[4])} share." for i, g in enumerate(gaps)
        )
        return (
            f"**Draft Quarterly Territory Plan: {_TERRITORY}** (draft for sales leadership review)\n\n"
            f"**Territory snapshot:** {_m(addr)} addressable spend, {_m(ours)} our revenue "
            f"({_pct(ours / addr)} share), {rec} recruiters.\n\n"
            f"**Top 3 opportunities:**\n{opps}\n\n"
            f"**Top 2 risks:**\n"
            f"1. Granite Ridge has 1 recruiter for {_m(46.0)} of spend; Fabrikam Workforce and Litware Talent hold 38.0% of it.\n"
            f"2. Office and Admin postings are down 3%; Harbor City office revenue ({_m(2.9)}) is exposed.\n\n"
            f"**3 recommendations:**\n"
            f"1. Add 2 IT and Engineering recruiters split across Harbor City and Granite Ridge (31-day time to fill).\n"
            f"2. Move 1 light-industrial recruiter from Harbor City to Granite Ridge to work its {_m(17.2)} open spend.\n"
            f"3. Re-price IT and Engineering bill rates for the 5.8% wage movement before Q3 renewals.\n\n"
            f"**Priority action:** approve the 2 IT and Engineering recruiter requisitions this quarter.\n\n"
            f"Status: Draft - no headcount, quota or account change was made.\n\n{_GATE}\n\n{_SOURCE}"
        )


if __name__ == "__main__":
    agent = StaffingTerritoryPlanningAgent()
    story = [
        {"operation": "territory_snapshot"},
        {"operation": "market_sizing", "metro": "Granite Ridge"},
        {"operation": "coverage_gaps"},
        {"operation": "competitive_landscape"},
        {"operation": "labor_trends"},
        {"operation": "territory_plan"},
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
