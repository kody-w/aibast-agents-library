---
name: "care-gap-closure"
description: "Prioritizes synthetic Medicare Advantage care gaps before the HEDIS deadline: panel status, top gaps by revenue and reachability, diabetes risk tiers and barriers, a barrier-specific outreach strategy, campaign projection, and monitoring alerts, plus source-evidence views (gap_analysis, cohort_review, outreach_draft, quality_dashboard). Human clinical and quality review is required; it never determines eligibility, launches campaigns, or contacts patients."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "care_gap_closure_agent.py"
  tool-name: "CareGapClosureAgent"
  agent-sha256: "110f062d29d782d0a2eb8032b9c9c468112975997fc4d3d7d2eb0d3097998508"
  version: "1.1.0"
  author: "AIBAST"
  tags: "care-gaps, quality-measures, outreach-draft, healthcare, human-review"
---

# Care Gap Closure

Prioritizes synthetic Medicare Advantage care gaps before the HEDIS deadline: panel status, top gaps by revenue and reachability, diabetes risk tiers and barriers, a barrier-specific outreach strategy, campaign projection, and monitoring alerts, plus source-evidence views (gap_analysis, cohort_review, outreach_draft, quality_dashboard). Human clinical and quality review is required; it never determines eligibility, launches campaigns, or contacts patients.

## What it needs

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "gap_analysis",
        "cohort_review",
        "outreach_draft",
        "quality_dashboard",
        "hedis_status",
        "top_gaps",
        "risk_stratification",
        "outreach_strategy",
        "campaign_projection",
        "monitoring_plan"
      ],
      "description": "Medicare Advantage HEDIS demo flow: hedis_status for 'prioritize care gaps for our Medicare Advantage population' / current status; top_gaps for the top gaps and which are most actionable; risk_stratification for the diabetes cohort analysis; outreach_strategy to design (and launch) the outreach strategy; campaign_projection for campaign deployment and projected impact; monitoring_plan to configure monitoring and alerts. Source-evidence views: gap_analysis for the 'largest evidence-review queue' across SYN- measures; cohort_review for organizing review cohorts without clinical risk scoring; outreach_draft for drafting but not sending a measure letter; quality_dashboard for a qualitative source-completeness dashboard."
    },
    "measure_id": {
      "type": "string",
      "enum": [
        "SYN-BCS",
        "SYN-CDC",
        "SYN-COL"
      ],
      "description": "Optional synthetic measure identifier."
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
   python3 scripts/run.py --json '{"operation": "<string>", "measure_id": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=110f062d29d782d0a2eb8032b9c9c468112975997fc4d3d7d2eb0d3097998508 -->
```python
"""Read-only, synthetic care-gap operations support."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/care-gap-closure",
    "version": "1.1.0",
    "display_name": "Care Gap Closure Agent",
    "description": (
        "Prioritizes synthetic Medicare Advantage care gaps before the HEDIS deadline: panel status, "
        "top gaps by revenue and reachability, diabetes risk tiers and barriers, a barrier-specific "
        "outreach strategy, campaign projection, and monitoring alerts, plus source-evidence views "
        "(gap_analysis, cohort_review, outreach_draft, quality_dashboard). Human clinical and quality "
        "review is required; it never determines eligibility, launches campaigns, or contacts patients."
    ),
    "author": "AIBAST",
    "tags": ["care-gaps", "quality-measures", "outreach-draft", "healthcare", "human-review"],
    "category": "healthcare",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}

SAFETY = (
    "Synthetic aggregate data only. Measure eligibility, exclusions, clinical interpretation, "
    "and outreach approval remain with authorized quality and clinical reviewers. This agent "
    "does not diagnose, contact patients, schedule care, or change records."
)

MEASURES = {
    "SYN-BCS": {
        "name": "Synthetic Breast Screening Measure",
        "source_population": 400,
        "source_closed": 292,
        "evidence_as_of": "2026-07-31",
        "limitations": "Eligibility and exclusions are unvalidated synthetic source fields.",
    },
    "SYN-COL": {
        "name": "Synthetic Colorectal Screening Measure",
        "source_population": 520,
        "source_closed": 338,
        "evidence_as_of": "2026-07-31",
        "limitations": "Clinical exclusions and external claims may be incomplete.",
    },
    "SYN-CDC": {
        "name": "Synthetic Diabetes Monitoring Measure",
        "source_population": 310,
        "source_closed": 257,
        "evidence_as_of": "2026-07-31",
        "limitations": "Recent labs and measure-year attribution require reviewer validation.",
    },
}

COHORTS = {
    "multiple_source_gaps": {"count": 42, "barrier": "mixed evidence completeness", "draft_channel": "staff review queue"},
    "single_source_gap": {"count": 117, "barrier": "recent evidence may be missing", "draft_channel": "portal draft"},
    "contact_data_review": {"count": 19, "barrier": "contact preference not confirmed", "draft_channel": "privacy review queue"},
}

# Medicare Advantage panel (synthetic) for the HEDIS prioritization demo.
PANEL = {
    "population": "Medicare Advantage",
    "patients": 2847,
    "hedis_score": 72.3,
    "hedis_target": 75.0,
    "star_impact": -0.5,
    "days_to_deadline": 23,
}

HEDIS_MEASURES = [
    {"measure": "Diabetes A1C test", "patients": 387, "revenue_risk": 189450, "reachable_pct": 76},
    {"measure": "Breast cancer screen", "patients": 243, "revenue_risk": 94170, "reachable_pct": 89},
    {"measure": "Colorectal screen", "patients": 198, "revenue_risk": 76890, "reachable_pct": 62},
    {"measure": "Statin therapy", "patients": 176, "revenue_risk": 43120, "reachable_pct": 91},
    {"measure": "Blood pressure control", "patients": 138, "revenue_risk": 25270, "reachable_pct": 84},
]

A1C_TIERS = [
    {"tier": "A1C >9.0 (Critical)", "avg_gap": "8.7 months", "priority": "Immediate"},
    {"tier": "A1C 7-9 (Moderate)", "avg_gap": "7.2 months", "priority": "High"},
    {"tier": "Never tested", "avg_gap": "New diagnosis", "priority": "High"},
]

A1C_BARRIERS = [
    {"barrier": "Transportation", "patients": 132},
    {"barrier": "No-show history", "patients": 108},
    {"barrier": "Language (Spanish)", "patients": 70},
    {"barrier": "Insurance lapsed", "patients": 46},
]

A1C_COMPLEXITY = 4.2

INTERVENTIONS = [
    {"barrier": "Transportation barriers", "intervention": "Mobile clinic slots + ride vouchers"},
    {"barrier": "No-show history", "intervention": "SMS reminders (48h, 24h, 2h intervals)"},
    {"barrier": "Language barriers", "intervention": "Spanish-speaking MA staff + translated materials"},
    {"barrier": "High-risk A1C", "intervention": "Direct RN outreach within 48 hours"},
]

CHANNEL_PLAN = {
    "valid_mobile_pct": 76,
    "voicemail": 387,
    "portal": 312,
    "rn_callbacks": 94,
    "response": {"SMS": 42, "Patient portal": 28, "Voice calls": 35, "RN outreach": 78},
    "mobile_clinic_slots": 47,
    "ride_vouchers": 132,
    "close_rate_pct": 68,
}

MONITORING = {
    "features": [
        "Daily 8 AM summary via Teams",
        "Real-time close rate tracking",
        "Weekly trend vs last HEDIS cycle",
        "Barrier analysis by patient cohort",
    ],
    "alerts": [
        "Close rate drops below 60%",
        "3 failed contact attempts",
        "Critical patient non-response >48h",
        "Campaign budget variance >15%",
    ],
}

OPERATIONS = [
    "gap_analysis",
    "cohort_review",
    "outreach_draft",
    "quality_dashboard",
    "hedis_status",
    "top_gaps",
    "risk_stratification",
    "outreach_strategy",
    "campaign_projection",
    "monitoring_plan",
]

ALIASES = {
    "patient_prioritization": "cohort_review",
    "outreach_campaign": "outreach_draft",
    "hedis_dashboard": "quality_dashboard",
}


def _notice(title):
    return [f"# {title}", "", f"> {SAFETY}", ""]


def _gap_totals():
    patients, revenue = 0, 0
    for row in HEDIS_MEASURES:
        patients += row["patients"]
        revenue += row["revenue_risk"]
    return patients, revenue


def _a1c():
    return HEDIS_MEASURES[0]


def _sms_count():
    return _a1c()["patients"] * CHANNEL_PLAN["valid_mobile_pct"] // 100


def _projected_saved():
    """Closed patients = close rate x A1C gap patients; saved = closed x per-patient incentive, to the nearest $100."""
    a1c = _a1c()
    closed = a1c["patients"] * CHANNEL_PLAN["close_rate_pct"] // 100
    return closed, int(round(closed * a1c["revenue_risk"] / a1c["patients"], -2))


def _selected_measure(measure_id):
    if not measure_id:
        return MEASURES.items()
    if measure_id not in MEASURES:
        return []
    return [(measure_id, MEASURES[measure_id])]


class CareGapClosureAgent(BasicAgent):
    """Summarize aggregate source evidence without making clinical decisions."""

    def __init__(self):
        self.name = "CareGapClosureAgent"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": list(OPERATIONS),
                        "description": (
                            "Medicare Advantage HEDIS demo flow: hedis_status for 'prioritize care gaps "
                            "for our Medicare Advantage population' / current status; top_gaps for the "
                            "top gaps and which are most actionable; risk_stratification for the diabetes "
                            "cohort analysis; outreach_strategy to design (and launch) the outreach "
                            "strategy; campaign_projection for campaign deployment and projected impact; "
                            "monitoring_plan to configure monitoring and alerts. Source-evidence views: "
                            "gap_analysis for the 'largest evidence-review queue' across SYN- measures; "
                            "cohort_review for organizing review cohorts without clinical risk scoring; "
                            "outreach_draft for drafting but not sending a measure letter; "
                            "quality_dashboard for a qualitative source-completeness dashboard."
                        ),
                    },
                    "measure_id": {
                        "type": "string",
                        "enum": sorted(MEASURES),
                        "description": "Optional synthetic measure identifier.",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        operation = ALIASES.get(kwargs.get("operation", ""), kwargs.get("operation", ""))
        routes = {
            "gap_analysis": self._gap_analysis,
            "cohort_review": self._cohort_review,
            "outreach_draft": self._outreach_draft,
            "quality_dashboard": self._quality_dashboard,
            "hedis_status": self._hedis_status,
            "top_gaps": self._top_gaps,
            "risk_stratification": self._risk_stratification,
            "outreach_strategy": self._outreach_strategy,
            "campaign_projection": self._campaign_projection,
            "monitoring_plan": self._monitoring_plan,
        }
        if operation not in routes:
            return f"**Error:** Unknown operation `{operation}`. No action was taken."
        return routes[operation](kwargs.get("measure_id"))

    def _gap_analysis(self, measure_id=None):
        rows = list(_selected_measure(measure_id))
        if not rows:
            return f"# Gap Analysis\n\n> {SAFETY}\n\nNo synthetic measure matched `{measure_id}`."
        lines = _notice("Source-Evidence Gap Analysis")
        largest_id, largest = max(
            rows,
            key=lambda item: item[1]["source_population"] - item[1]["source_closed"],
        )
        largest_queue = largest["source_population"] - largest["source_closed"]
        lines.extend([
            f"**Largest evidence-review queue:** {largest_id} — {largest_queue} records.",
            "",
        ])
        for mid, measure in rows:
            source_gap = measure["source_population"] - measure["source_closed"]
            lines.extend([
                f"## {measure['name']} ({mid})",
                f"- Source population: {measure['source_population']}",
                f"- Source-recorded closed: {measure['source_closed']}",
                f"- Records requiring evidence review: {source_gap}",
                f"- Limitation: {measure['limitations']}",
                "",
            ])
        return "\n".join(lines)

    def _cohort_review(self, _measure_id=None):
        lines = _notice("Aggregate Cohort Review")
        lines.append("Ordering is operational triage only, not clinical risk scoring.")
        lines.append("")
        for cohort, data in COHORTS.items():
            lines.extend([
                f"## {cohort.replace('_', ' ').title()}",
                f"- Synthetic count: {data['count']}",
                f"- Evidence barrier: {data['barrier']}",
                f"- Draft handling route: {data['draft_channel']}",
                "",
            ])
        return "\n".join(lines)

    def _outreach_draft(self, measure_id=None):
        rows = list(_selected_measure(measure_id))
        if not rows:
            return f"# Outreach Draft\n\n> {SAFETY}\n\nNo synthetic measure matched `{measure_id}`."
        lines = _notice("Outreach Draft")
        lines.append("No message is sent. Privacy, consent, accessibility, and clinical content require approval.")
        lines.append("")
        for mid, measure in rows:
            lines.extend([
                f"## {measure['name']} ({mid})",
                "- Draft: We are reviewing our records and invite you to contact the care team if you have questions.",
                "- Do not state that care is overdue or that the recipient is eligible until a reviewer validates the record.",
                "- Approval route: quality reviewer → clinician when needed → authorized outreach operator.",
                "",
            ])
        return "\n".join(lines)

    def _quality_dashboard(self, measure_id=None):
        rows = list(_selected_measure(measure_id))
        if not rows:
            return f"# Quality Dashboard\n\n> {SAFETY}\n\nNo synthetic measure matched `{measure_id}`."
        lines = _notice("Qualitative Quality Dashboard")
        lines.extend([
            "| Measure | Source completeness signal | Evidence date | Reviewer note |",
            "|---|---:|---|---|",
        ])
        for mid, measure in rows:
            rate = round(measure["source_closed"] / measure["source_population"] * 100, 1)
            lines.append(f"| {mid} | {rate}% source-recorded closed | {measure['evidence_as_of']} | {measure['limitations']} |")
        return "\n".join(lines)

    # ── Medicare Advantage HEDIS demo flow (video turns 1-6) ───
    def _hedis_status(self, _measure_id=None):
        patients, revenue = _gap_totals()
        a1c = _a1c()
        pct = round(patients * 100 / PANEL["patients"], 1)
        lines = _notice("HEDIS Performance Summary")
        lines.extend([
            f"I've analyzed your {PANEL['population']} panel across the synthetic HEDIS quality measures. "
            "You have significant gaps affecting your Star Rating and revenue.",
            "",
            "| Metric | Current | Impact |",
            "|---|---|---|",
            f"| Total MA patients | {PANEL['patients']:,} | Active panel |",
            f"| Patients with gaps | {patients:,} ({pct}%) | Action needed |",
            f"| HEDIS score | {PANEL['hedis_score']}% | Target: {PANEL['hedis_target']:g}% |",
            f"| Star rating impact | {PANEL['star_impact']} stars | Below threshold |",
            f"| Revenue at risk | ${revenue:,} | {PANEL['days_to_deadline']} days to deadline |",
            "",
            f"**Top Concern:** {a1c['measure']} gaps affecting {a1c['patients']} patients and "
            f"${a1c['revenue_risk']:,} in quality incentives.",
            "",
            "Source: [EHR + HEDIS Analytics (synthetic)]",
            "",
            "Should I break down the top gaps by measure?",
        ])
        return "\n".join(lines)

    def _top_gaps(self, _measure_id=None):
        a1c = _a1c()
        lines = _notice("Top 5 Care Gap Measures")
        lines.extend([
            "Ranked by revenue impact and patient reachability:",
            "",
            "| Measure | Patients | Revenue Risk | Reachable |",
            "|---|---|---|---|",
        ])
        for row in HEDIS_MEASURES:
            lines.append(f"| {row['measure']} | {row['patients']} | ${row['revenue_risk']:,} | {row['reachable_pct']}% |")
        patients, revenue = _gap_totals()
        lines.extend([
            f"| **Total** | **{patients:,}** | **${revenue:,}** | |",
            "",
            f"**Best Opportunity:** {a1c['measure']} group - {a1c['patients']} patients with high closure "
            "potential and the largest revenue impact.",
            "",
            "Source: [HEDIS Engine + Patient Engagement Data (synthetic)]",
            "",
            "Want to see the diabetes cohort analysis?",
        ])
        return "\n".join(lines)

    def _risk_stratification(self, _measure_id=None):
        a1c = _a1c()
        lines = _notice("Diabetes Cohort Risk Stratification")
        lines.extend([
            f"Analysis of {a1c['patients']} diabetic patients shows clear risk tiers and addressable "
            "barriers (stratification from synthetic source fields for reviewer prioritization; not a diagnosis).",
            "",
            "| Risk Level | Avg Gap | Priority |",
            "|---|---|---|",
        ])
        for tier in A1C_TIERS:
            lines.append(f"| {tier['tier']} | {tier['avg_gap']} | {tier['priority']} |")
        lines.extend(["", "**Engagement Barriers:**"])
        for b in A1C_BARRIERS:
            pct = round(b["patients"] * 100 / a1c["patients"])
            lines.append(f"- {b['barrier']}: {pct}% ({b['patients']} patients)")
        lines.extend([
            f"- Complexity: Average {A1C_COMPLEXITY} chronic conditions per patient",
            "",
            "Source: [EHR Clinical Data + Social Determinants (synthetic)]",
            "",
            "Shall I design a targeted outreach campaign?",
        ])
        return "\n".join(lines)

    def _outreach_strategy(self, _measure_id=None):
        plan = CHANNEL_PLAN
        lines = _notice("Outreach Strategy Draft")
        lines.extend([
            "Multi-channel campaign designed with barrier-specific interventions. It is ready for your "
            "approval to launch; no message is sent until an authorized outreach operator launches it.",
            "",
            "**Personalized Interventions:**",
        ])
        for i in INTERVENTIONS:
            lines.append(f"- {i['barrier']}: {i['intervention']}")
        lines.extend([
            "",
            "**Campaign Scope (drafted):**",
            f"- {_sms_count()} SMS ({plan['valid_mobile_pct']}% valid mobile)",
            f"- {plan['voicemail']} voicemails (next 3 days)",
            f"- {plan['portal']} patient portal messages",
            f"- {plan['rn_callbacks']} RN callbacks prioritized",
            "",
            "Source: [Patient Engagement Platform (synthetic)]",
            "",
            "Want to see the campaign deployment plan and projected impact?",
        ])
        return "\n".join(lines)

    def _campaign_projection(self, _measure_id=None):
        plan = CHANNEL_PLAN
        a1c = _a1c()
        closed, saved = _projected_saved()
        volumes = {
            "SMS": f"{_sms_count()} patients",
            "Patient portal": f"{plan['portal']} messages",
            "Voice calls": f"{plan['voicemail']} queued",
            "RN outreach": f"{plan['rn_callbacks']} scheduled",
        }
        lines = _notice("Campaign Deployment Plan and Projected Impact")
        lines.extend([
            "Deployment plan across all channels (ready to launch on approval) with projected outcomes.",
            "",
            "| Channel | Planned Volume | Response Rate |",
            "|---|---|---|",
        ])
        for channel, rate in plan["response"].items():
            lines.append(f"| {channel} | {volumes[channel]} | {rate}% expected |")
        lines.extend([
            "",
            "**Resource Allocation (requests for approval):**",
            f"- Mobile clinic slots: {plan['mobile_clinic_slots']} to reserve (next 2 weeks)",
            f"- Ride vouchers: {plan['ride_vouchers']} to issue",
            "- Appointment capacity: next-day Tue/Thu slots to open",
            "",
            "**Projected Outcomes:**",
            f"- Close rate: {plan['close_rate_pct']}% (based on historical campaigns) = {closed} of {a1c['patients']} patients",
            f"- Revenue saved: ${saved:,} of ${a1c['revenue_risk']:,} at risk",
            "",
            "Source: [Campaign Management + Historical Analytics (synthetic)]",
            "",
            "Want to set up monitoring?",
        ])
        return "\n".join(lines)

    def _monitoring_plan(self, _measure_id=None):
        lines = _notice("Monitoring and Alert Configuration")
        lines.extend([
            "Recommended monitoring dashboard and alerting, ready for your team to turn on.",
            "",
            "**Dashboard Features:**",
        ])
        lines += [f"- {f}" for f in MONITORING["features"]]
        lines.extend(["", "**Alert Triggers:**"])
        lines += [f"- {a}" for a in MONITORING["alerts"]]
        lines.extend([
            "",
            "Data flow: data lake -> Power BI -> Teams notifications.",
            "",
            "Source: [Power BI + Teams (synthetic)]",
            "",
            "Want a full campaign summary?",
        ])
        return "\n".join(lines)


if __name__ == "__main__":
    agent = CareGapClosureAgent()
    for op in agent.metadata["parameters"]["properties"]["operation"]["enum"]:
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
