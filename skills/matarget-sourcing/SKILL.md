---
name: "matarget-sourcing"
description: "Always call this tool for acquisition and M&A target sourcing on the fictional Fabrikam Information Services thesis: turning an acquisition thesis into screening criteria, running the screen and ranking the targets that pass, a dossier on one target (default: the top-ranked one), checking whether the ranking holds under different weightings, finding thin or out-of-date evidence, and drafting the investment committee screening memo. Call it right away; every operation has demo defaults and the thesis is already loaded, so never ask for filters or weights. It never contacts targets, updates a CRM, shares documents, or makes investment decisions."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "ma_target_sourcing_agent.py"
  tool-name: "MATargetSourcingAgent"
  agent-sha256: "ab4fc7383a270a699507886b6d5dc14a3243a0fc324473538f337c0b58430d0e"
  version: "1.0.0"
  author: "AIBAST"
  tags: "m-and-a, corporate-development, deal-sourcing, target-screening, financial-services"
---

# Matarget Sourcing

Always call this tool for acquisition and M&A target sourcing on the fictional Fabrikam Information Services thesis: turning an acquisition thesis into screening criteria, running the screen and ranking the targets that pass, a dossier on one target (default: the top-ranked one), checking whether the ranking holds under different weightings, finding thin or out-of-date evidence, and drafting the investment committee screening memo. Call it right away; every operation has demo defaults and the thesis is already loaded, so never ask for filters or weights. It never contacts targets, updates a CRM, shares documents, or makes investment decisions.

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "build_thesis",
        "screen_targets",
        "target_dossier",
        "challenge_ranking",
        "evidence_gaps",
        "ic_memo_draft"
      ],
      "description": "build_thesis to turn the acquisition thesis (sector, region, revenue band, profitability) into screening criteria; screen_targets to run the screen and rank the targets that pass; target_dossier for one target's profile, financials, sources and diligence questions; challenge_ranking to test whether the ranking holds with different weightings (for example weighting financial quality more heavily); evidence_gaps for thin, missing or out-of-date evidence and research requests; ic_memo_draft for the investment committee screening memo draft."
    },
    "target": {
      "type": "string",
      "description": "Target ID such as T-01 or part of a company name (target_dossier). Default: the top-ranked target."
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
   python3 scripts/run.py --json '{"operation": "<string>", "target": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=ab4fc7383a270a699507886b6d5dc14a3243a0fc324473538f337c0b58430d0e -->
```python
"""
M&A Target Sourcing Agent

Read-only acquisition screening support for a corporate development team, built on a fixed synthetic market
universe of eight fictional software companies: an acquisition thesis turned into screening criteria, a transparent
weighted ranking, a cited target dossier, a weighting challenge, an evidence-gap review, and an investment committee
screening memo draft. Every company, financial figure, signal and source is invented. The agent never contacts a
target, writes to a CRM, shares a document, or makes an investment decision.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/ma-target-sourcing",
    "version": "1.0.0",
    "display_name": "M&A Target Sourcing Agent",
    "description": "Turn an acquisition thesis into a transparent, cited target shortlist: screening criteria, a weighted ranking of a synthetic market universe, target dossiers with sources and diligence questions, a weighting challenge, evidence-gap review, and an investment committee screening memo draft. The agent is read-only; it never contacts a target, updates a CRM, shares a document, or makes an investment decision.",
    "author": "AIBAST",
    "tags": ["m-and-a", "corporate-development", "deal-sourcing", "target-screening", "financial-services"],
    "category": "financial_services",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Synthetic data (fixed snapshot date 2026-06-30; every company and figure is fictional)
# ---------------------------------------------------------------------------

SNAPSHOT_DATE = "2026-06-30"
STALE_BEFORE = "2025-06-30"   # evidence older than 12 months at the snapshot date is stale

THESIS = {
    "id": "TH-2026-014",
    "acquirer": "Fabrikam Information Services",
    "objective": "Add compliance and regulatory workflow software in Europe",
    "sector": "Compliance and regulatory workflow software",
    "region": "Europe",
    "min_revenue": 20,
    "max_revenue": 120,
    "positive_ebitda": True,
}

WEIGHTS = {"strategy": 40, "financial": 30, "market": 15, "execution": 15}

ALT_WEIGHTINGS = [
    {"name": "Base thesis", "strategy": 40, "financial": 30, "market": 15, "execution": 15},
    {"name": "Financial-first", "strategy": 25, "financial": 45, "market": 15, "execution": 15},
    {"name": "Equal weights", "strategy": 25, "financial": 25, "market": 25, "execution": 25},
]

CRITERIA_LABELS = {
    "strategy": "Strategy fit",
    "financial": "Financial quality",
    "market": "Market signal",
    "execution": "Execution fit",
}

# Revenue and EBITDA in USD millions (synthetic). Scores are 0-100 analyst-calibrated criteria scores.
TARGETS = {
    "T-01": {"name": "Lumenrock Compliance Systems", "focus": "Regulatory change and policy workflow", "region": "Europe",
             "revenue": 64, "ebitda": 14.1, "growth": 18, "recurring": 88,
             "scores": {"strategy": 92, "financial": 84, "market": 78, "execution": 80},
             "risks": ["Top five clients are 31% of revenue", "Founder-led sales motion"],
             "questions": ["How concentrated is renewal exposure in the next 18 months?",
                           "Which product modules are sold standalone versus bundled?",
                           "What would it take to move sales beyond the founders?"],
             "evidence": [{"id": "T-01-S1", "type": "Financials", "title": "FY2025 audited summary (synthetic)", "date": "2026-03-31"},
                          {"id": "T-01-S2", "type": "Product", "title": "Analyst product review (synthetic)", "date": "2026-05-12"},
                          {"id": "T-01-S3", "type": "Customer", "title": "Customer reference notes (synthetic)", "date": "2025-11-04"}]},
    "T-02": {"name": "Veridane Analytics", "focus": "Risk analytics for compliance teams", "region": "Europe",
             "revenue": 38, "ebitda": 6.5, "growth": 24, "recurring": 81,
             "scores": {"strategy": 74, "financial": 80, "market": 86, "execution": 70},
             "risks": ["Partner-dependent distribution"],
             "questions": ["What share of new bookings comes through partners?",
                           "How portable is the analytics engine to our data platform?",
                           "Which retention terms apply to the partner contracts?"],
             "evidence": [{"id": "T-02-S1", "type": "Financials", "title": "Management accounts (synthetic)", "date": "2025-12-31"},
                          {"id": "T-02-S2", "type": "Customer", "title": "Customer survey extract (synthetic)", "date": "2026-04-02"}]},
    "T-03": {"name": "Halverd Audit Cloud", "focus": "Audit and controls workflow", "region": "Europe",
             "revenue": 92, "ebitda": 17.5, "growth": 11, "recurring": 76,
             "scores": {"strategy": 88, "financial": 72, "market": 70, "execution": 62},
             "risks": ["Platform migration underway", "Two-country operating model"],
             "questions": ["When does the platform migration finish, and at what cost?",
                           "How are the two country entities integrated today?",
                           "What is net revenue retention after the migration?"],
             "evidence": [{"id": "T-03-S1", "type": "Financials", "title": "FY2024 filed accounts (synthetic)", "date": "2025-03-31"},
                          {"id": "T-03-S2", "type": "Product", "title": "Product roadmap brief (synthetic)", "date": "2026-01-15"},
                          {"id": "T-03-S3", "type": "Customer", "title": "Customer reference notes (synthetic)", "date": "2026-05-20"}]},
    "T-04": {"name": "Brightquay Reg Data", "focus": "Regulatory data feeds", "region": "North America",
             "revenue": 55, "ebitda": 9.9, "growth": 14, "recurring": 90,
             "scores": {"strategy": 80, "financial": 82, "market": 74, "execution": 72},
             "risks": ["Outside the thesis region"], "questions": [], "evidence": []},
    "T-05": {"name": "Oskarvale Workflow", "focus": "Compliance case management", "region": "Europe",
             "revenue": 21, "ebitda": -1.8, "growth": 32, "recurring": 79,
             "scores": {"strategy": 78, "financial": 40, "market": 80, "execution": 66},
             "risks": ["Loss-making"], "questions": [], "evidence": []},
    "T-06": {"name": "Cindral Risk Labs", "focus": "Enterprise risk platform", "region": "Europe",
             "revenue": 140, "ebitda": 25.2, "growth": 9, "recurring": 83,
             "scores": {"strategy": 70, "financial": 78, "market": 68, "execution": 58},
             "risks": ["Above the revenue band"], "questions": [], "evidence": []},
    "T-07": {"name": "Tessaline Controls", "focus": "Compliance controls testing", "region": "Europe",
             "revenue": 47, "ebitda": 7.1, "growth": 15, "recurring": 84,
             "scores": {"strategy": 84, "financial": 76, "market": 72, "execution": 84},
             "risks": ["Single product line"],
             "questions": ["How much of the pipeline depends on the single product line?",
                           "Which adjacent modules are on the near-term roadmap?",
                           "What does the integration effort look like for our platform?"],
             "evidence": [{"id": "T-07-S1", "type": "Financials", "title": "Management accounts (synthetic)", "date": "2026-02-28"},
                          {"id": "T-07-S2", "type": "Product", "title": "Product review (synthetic)", "date": "2025-04-18"}]},
    "T-08": {"name": "Marrowgate Reporting", "focus": "Regulatory reporting templates", "region": "Europe",
             "revenue": 29, "ebitda": 4.4, "growth": 9, "recurring": 70,
             "scores": {"strategy": 60, "financial": 58, "market": 56, "execution": 78},
             "risks": ["Low growth"],
             "questions": ["What is driving the slower growth?",
                           "How many templates are customer-specific?",
                           "Which renewals are at risk this year?"],
             "evidence": [{"id": "T-08-S1", "type": "Financials", "title": "Management accounts (synthetic)", "date": "2026-01-31"}]},
}

REQUIRED_EVIDENCE = ["Financials", "Product", "Customer"]
SHORTLIST_SIZE = 3

_GATE = (
    "Synthetic screening support only. All companies, financials and sources are fictional. No target was "
    "contacted, no CRM or deal record was changed, nothing was shared, and no investment decision was made."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_target(value):
    """Target ID or part of a company name; empty -> the top-ranked target; no match -> None."""
    if not value:
        return _ranked()[0]["id"]
    q = str(value).lower().strip()
    for key in TARGETS:
        if key.lower() in q or q in TARGETS[key]["name"].lower():
            return key
    return None


def _exclusion(t):
    """Why a target fails the thesis filters ('' when it passes)."""
    if t["region"] != THESIS["region"]:
        return f"Region {t['region']} is outside {THESIS['region']}"
    if t["revenue"] < THESIS["min_revenue"] or t["revenue"] > THESIS["max_revenue"]:
        return f"Revenue ${t['revenue']}M is outside the ${THESIS['min_revenue']}M-${THESIS['max_revenue']}M band"
    if THESIS["positive_ebitda"] and t["ebitda"] <= 0:
        return f"EBITDA ${t['ebitda']}M is not positive"
    return ""


def _score(t, w):
    """Weighted score in hundredths (integer arithmetic), formatted later with one decimal."""
    total = 0
    for k in ["strategy", "financial", "market", "execution"]:
        total += t["scores"][k] * w[k]
    return total


def _fmt(total):
    return f"{total / 100:.1f}"


def _ranked(w=None):
    w = w or WEIGHTS
    rows = []
    for key in TARGETS:
        t = TARGETS[key]
        if _exclusion(t) == "":
            rows.append({"id": key, "name": t["name"], "total": _score(t, w)})
    out = []
    while rows:
        best = rows[0]
        for r in rows:
            if r["total"] > best["total"]:
                best = r
        out.append(best)
        rows.remove(best)
    return out


def _shortlist_stable():
    first = [r["id"] for r in _ranked(ALT_WEIGHTINGS[0])][:SHORTLIST_SIZE]
    for w in ALT_WEIGHTINGS:
        if [r["id"] for r in _ranked(w)][:SHORTLIST_SIZE] != first:
            return False
    return True


def _gaps(key):
    t = TARGETS[key]
    have = {}
    for e in t["evidence"]:
        have[e["type"]] = e
    gaps = []
    for need in REQUIRED_EVIDENCE:
        if need not in have:
            gaps.append({"type": need, "issue": "Missing", "detail": "No source on file"})
        elif have[need]["date"] < STALE_BEFORE:
            gaps.append({"type": need, "issue": "Stale", "detail": f"{have[need]['id']} dated {have[need]['date']}"})
    return gaps


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

OPERATIONS = [
    "build_thesis", "screen_targets", "target_dossier", "challenge_ranking", "evidence_gaps", "ic_memo_draft",
]


class MATargetSourcingAgent(BasicAgent):
    """Acquisition target screening support (read-only, synthetic)."""

    def __init__(self):
        self.name = "MATargetSourcingAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                "Always call this tool for acquisition and M&A target sourcing on the fictional Fabrikam "
                "Information Services thesis: turning an acquisition thesis into screening criteria, running the "
                "screen and ranking the targets that pass, a dossier on one target (default: the top-ranked one), "
                "checking whether the ranking holds under different weightings, finding thin or out-of-date "
                "evidence, and drafting the investment committee screening memo. Call it right away; every "
                "operation has demo defaults and the thesis is already loaded, so never ask for filters or "
                "weights. It never contacts targets, updates a CRM, shares documents, or makes investment decisions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": list(OPERATIONS),
                        "description": (
                            "build_thesis to turn the acquisition thesis (sector, region, revenue band, profitability) "
                            "into screening criteria; screen_targets to run the screen and rank the targets that pass; "
                            "target_dossier for one target's profile, financials, sources and diligence questions; "
                            "challenge_ranking to test whether the ranking holds with different weightings (for "
                            "example weighting financial quality more heavily); evidence_gaps for thin, missing or "
                            "out-of-date evidence and research requests; ic_memo_draft for the investment committee "
                            "screening memo draft."
                        ),
                    },
                    "target": {
                        "type": "string",
                        "description": "Target ID such as T-01 or part of a company name (target_dossier). Default: the top-ranked target.",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation", "build_thesis")
        handlers = {
            "build_thesis": self._build_thesis,
            "screen_targets": self._screen_targets,
            "target_dossier": self._target_dossier,
            "challenge_ranking": self._challenge_ranking,
            "evidence_gaps": self._evidence_gaps,
            "ic_memo_draft": self._ic_memo_draft,
        }
        handler = handlers.get(op)
        if not handler:
            return f"**Error:** Unknown operation `{op}`. Operations: {', '.join(OPERATIONS)}."
        if op == "target_dossier":
            key = _resolve_target(kwargs.get("target"))
            if key is None:
                return (f"# Unknown Target\n\nNo synthetic target matches `{kwargs.get('target')}`; no substitute "
                        f"target was used. Targets: {', '.join(TARGETS)}.\n\n> {_GATE}")
            return handler(key)
        return handler()

    def _build_thesis(self) -> str:
        th = THESIS
        passing = 0
        lines = []
        for key in TARGETS:
            reason = _exclusion(TARGETS[key])
            if reason == "":
                passing += 1
            else:
                lines.append(f"| {key} | {TARGETS[key]['name']} | {reason} |")
        out = [
            f"# Screening Criteria - {th['id']}",
            "",
            f"**Acquirer:** {th['acquirer']} | **Objective:** {th['objective']}",
            "",
            "| Criterion | Setting |",
            "|-----------|---------|",
            f"| Sector focus | {th['sector']} |",
            f"| Region | {th['region']} |",
            f"| Revenue band | ${th['min_revenue']}M-${th['max_revenue']}M |",
            "| Profitability | Positive EBITDA required |",
            f"| Score weights | Strategy fit {WEIGHTS['strategy']}%, financial quality {WEIGHTS['financial']}%, "
            f"market signal {WEIGHTS['market']}%, execution fit {WEIGHTS['execution']}% |",
            "",
            f"**Universe:** {len(TARGETS)} synthetic companies; **{passing} of {len(TARGETS)} pass** the filters.",
            "",
            "| Excluded | Company | Reason |",
            "|----------|---------|--------|",
        ] + lines + [
            "",
            "Next: run the screen and rank the targets that pass.",
            "",
            f"> {_GATE}",
        ]
        return "\n".join(out)

    def _screen_targets(self) -> str:
        ranked = _ranked()
        out = [
            f"# Ranked Longlist - {THESIS['id']}",
            "",
            f"{len(ranked)} targets pass the screen (snapshot {SNAPSHOT_DATE}). Weighted score = strategy fit "
            f"{WEIGHTS['strategy']}% + financial quality {WEIGHTS['financial']}% + market signal {WEIGHTS['market']}% "
            f"+ execution fit {WEIGHTS['execution']}%.",
            "",
            "| Rank | Target | Company | Revenue | EBITDA | Growth | Score |",
            "|------|--------|---------|---------|--------|--------|-------|",
        ]
        rank = 0
        for r in ranked:
            rank += 1
            t = TARGETS[r["id"]]
            out.append(f"| {rank} | {r['id']} | {t['name']} | ${t['revenue']}M | ${t['ebitda']}M | {t['growth']}% | "
                       f"{_fmt(r['total'])} |")
        top = ranked[0]
        out += [
            "",
            f"**Shortlist (top {SHORTLIST_SIZE}):** " + ", ".join(f"{r['id']} {r['name']}" for r in ranked[:SHORTLIST_SIZE]) + ".",
            f"**Leader:** {top['id']} {top['name']} at {_fmt(top['total'])}.",
            "",
            "Next: open the dossier on the top-ranked target.",
            "",
            f"> {_GATE}",
        ]
        return "\n".join(out)

    def _target_dossier(self, key) -> str:
        t = TARGETS[key]
        reason = _exclusion(t)
        if reason:
            return (f"# {key} {t['name']} - Excluded by the Screen\n\n{reason}. No dossier is prepared for "
                    f"excluded targets.\n\n> {_GATE}")
        ranked = _ranked()
        rank = 0
        total = 0
        for i in range(len(ranked)):
            if ranked[i]["id"] == key:
                rank = i + 1
                total = ranked[i]["total"]
        margin = t["ebitda"] / t["revenue"] * 100
        out = [
            f"# Target Dossier - {key} {t['name']}",
            "",
            f"**Focus:** {t['focus']} | **Region:** {t['region']} | **Rank:** {rank} of {len(ranked)} | "
            f"**Weighted score:** {_fmt(total)}",
            "",
            "| Synthetic financials | Value |",
            "|----------------------|-------|",
            f"| Revenue | ${t['revenue']}M |",
            f"| EBITDA | ${t['ebitda']}M ({margin:.1f}% margin) |",
            f"| Revenue growth | {t['growth']}% |",
            f"| Recurring revenue | {t['recurring']}% |",
            "",
            "| Criterion | Score | Weight |",
            "|-----------|-------|--------|",
        ]
        for k in ["strategy", "financial", "market", "execution"]:
            out.append(f"| {CRITERIA_LABELS[k]} | {t['scores'][k]} | {WEIGHTS[k]}% |")
        out += ["", "**Risk flags:** " + "; ".join(t["risks"]) + ".", "", "**Sources:**"]
        for e in t["evidence"]:
            out.append(f"- [{e['id']}] {e['type']}: {e['title']}, {e['date']}")
        out += ["", "**Diligence questions:**"]
        n = 0
        for q in t["questions"]:
            n += 1
            out.append(f"{n}. {q}")
        out += ["", f"> {_GATE}"]
        return "\n".join(out)

    def _challenge_ranking(self) -> str:
        out = [
            "# Ranking Challenge - Three Weightings",
            "",
            "| Target | " + " | ".join(w["name"] for w in ALT_WEIGHTINGS) + " |",
            "|--------|" + "|".join("------" for w in ALT_WEIGHTINGS) + "|",
        ]
        for r in _ranked():
            t = TARGETS[r["id"]]
            cells = []
            for w in ALT_WEIGHTINGS:
                cells.append(_fmt(_score(t, w)))
            out.append(f"| {r['id']} {t['name']} | " + " | ".join(cells) + " |")
        stable = _shortlist_stable()
        base = _ranked(ALT_WEIGHTINGS[0])
        fin = _ranked(ALT_WEIGHTINGS[1])
        gap_base = (base[1]["total"] - base[2]["total"]) / 100
        gap_fin = (fin[1]["total"] - fin[2]["total"]) / 100
        verdict = ("The top 3 holds under all 3 weightings." if stable
                   else "The top 3 changes between weightings; review the criteria before outreach.")
        out += [
            "",
            f"**Verdict:** {verdict}",
            f"**Watch:** the gap between rank 2 ({base[1]['id']}) and rank 3 ({base[2]['id']}) narrows from "
            f"{gap_base:.1f} to {gap_fin:.1f} points under Financial-first, so treat them as close.",
            "",
            "Next: check where the evidence behind the shortlist is thin or out of date.",
            "",
            f"> {_GATE}",
        ]
        return "\n".join(out)

    def _evidence_gaps(self) -> str:
        ranked = _ranked()
        shortlist = [r["id"] for r in ranked[:SHORTLIST_SIZE]]
        out = [
            f"# Evidence Coverage - Snapshot {SNAPSHOT_DATE}",
            "",
            f"Required per target: {', '.join(REQUIRED_EVIDENCE)}. Sources dated before {STALE_BEFORE} are stale.",
            "",
            "| Request | Target | Evidence | Issue | Detail | Shortlist |",
            "|---------|--------|----------|-------|--------|-----------|",
        ]
        total = 0
        on_short = 0
        targets_with = 0
        for r in ranked:
            gaps = _gaps(r["id"])
            if gaps:
                targets_with += 1
            for g in gaps:
                total += 1
                flag = "Yes" if r["id"] in shortlist else "No"
                if r["id"] in shortlist:
                    on_short += 1
                out.append(f"| RR-{total:02d} | {r['id']} | {g['type']} | {g['issue']} | {g['detail']} | {flag} |")
        out += [
            "",
            f"**{total} evidence gaps across {targets_with} targets; {on_short} sit on the shortlist.** "
            f"{shortlist[0]} {TARGETS[shortlist[0]]['name']} has complete, current evidence.",
            "",
            "The research requests above are drafts for the research team; none has been sent.",
            "",
            f"> {_GATE}",
        ]
        return "\n".join(out)

    def _ic_memo_draft(self) -> str:
        ranked = _ranked()
        short = ranked[:SHORTLIST_SIZE]
        revenue = 0
        open_gaps = 0
        for r in short:
            revenue += TARGETS[r["id"]]["revenue"]
            open_gaps += len(_gaps(r["id"]))
        out = [
            "# Investment Committee Screening Memo - DRAFT ICM-2026-07-01",
            "",
            f"**Thesis:** {THESIS['id']} {THESIS['objective']} | **Universe:** {len(TARGETS)} | "
            f"**Passed screen:** {len(ranked)} | **Shortlist:** {len(short)}",
            "",
            "| Rank | Target | Company | Score | Revenue | Key risk |",
            "|------|--------|---------|-------|---------|----------|",
        ]
        rank = 0
        for r in short:
            rank += 1
            t = TARGETS[r["id"]]
            out.append(f"| {rank} | {r['id']} | {t['name']} | {_fmt(r['total'])} | ${t['revenue']}M | {t['risks'][0]} |")
        out += [
            "",
            f"**Combined shortlist revenue:** ${revenue}M. **Ranking check:** "
            + (f"top {SHORTLIST_SIZE} stable under {len(ALT_WEIGHTINGS)} weightings." if _shortlist_stable()
               else "top 3 changes between weightings; review before outreach."),
            f"**Conditions before outreach:** close {open_gaps} open evidence gaps on the shortlist; the corporate "
            "development lead approves any first contact.",
            "**Ask of the committee:** approve the shortlist for confidential management outreach planning.",
            "",
            "Status: Draft for the corporate development lead. Not sent; no target contacted.",
            "",
            f"> {_GATE}",
        ]
        return "\n".join(out)


if __name__ == "__main__":
    agent = MATargetSourcingAgent()
    for op in OPERATIONS:
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
