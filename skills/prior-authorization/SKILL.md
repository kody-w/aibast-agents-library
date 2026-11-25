---
name: "prior-authorization"
description: "Assembles synthetic payer and clinical evidence for human utilization review: the patient request, payer-criteria match, a ready-to-submit packet, documentation strengths and appeal strategy, a proposed tracking plan, the authorization portfolio and denial reviews; it never predicts, grants, denies, submits, or changes an authorization and never sends a notification."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "prior_authorization_agent.py"
  tool-name: "PriorAuthorizationAgent"
  agent-sha256: "474c2429fae7cf94c1e625b6a99092e329b606e81dd29c58f1dbf1d5d4c3a05b"
  version: "1.2.0"
  author: "AIBAST"
  tags: "prior-auth, evidence-packet, payer-criteria, healthcare, human-review"
---

# Prior Authorization

Assembles synthetic payer and clinical evidence for human utilization review: the patient request, payer-criteria match, a ready-to-submit packet, documentation strengths and appeal strategy, a proposed tracking plan, the authorization portfolio and denial reviews; it never predicts, grants, denies, submits, or changes an authorization and never sends a notification.

## What it needs

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "request_evidence",
        "criteria_evidence",
        "status_summary",
        "appeal_evidence_packet",
        "patient_auth_request",
        "payer_requirements_check",
        "submission_packet",
        "approval_outlook",
        "tracking_plan",
        "portfolio_status",
        "denial_review"
      ],
      "description": "Read-only utilization-review evidence operation. The demo patient is Robert Chen (lumbar MRI, PA-2024-892741); call right away, no ID is needed. patient_auth_request: a patient needs prior auth / 'can you submit this' - verify the request details. payer_requirements_check: check payer or insurance requirements. submission_packet: 'submit it now' / confirmation details - returns the ready-to-submit packet (never submits). approval_outlook: likelihood of approval and appeal strategy if denied. tracking_plan: configure automatic tracking / notify everyone when approved. portfolio_status: all pending prior auths and their status. denial_review: the denied Medicare case / why a request was denied and the appeal. request_evidence, criteria_evidence, status_summary and appeal_evidence_packet cover the SYN-AUTH evidence-inventory requests."
    },
    "patient": {
      "type": "string",
      "description": "Optional patient name or PA-2024 request ID for the demo operations (default Robert Chen; denial_review always shows the denied Michael Johnson case)."
    },
    "auth_id": {
      "type": "string",
      "enum": [
        "SYN-AUTH-001",
        "SYN-AUTH-002"
      ],
      "description": "Optional synthetic request identifier."
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
   python3 scripts/run.py --json '{"operation": "<string>", "patient": "<string>", "auth_id": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=474c2429fae7cf94c1e625b6a99092e329b606e81dd29c58f1dbf1d5d4c3a05b -->
```python
"""Read-only, synthetic prior-authorization evidence support."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/prior-authorization",
    "version": "1.2.0",
    "display_name": "Prior Authorization Agent",
    "description": (
        "Assembles synthetic payer and clinical evidence for human utilization review: the patient "
        "request, payer-criteria match, a ready-to-submit packet, documentation strengths and appeal "
        "strategy, a proposed tracking plan, the authorization portfolio and denial reviews; it never "
        "predicts, grants, denies, submits, or changes an authorization and never sends a notification."
    ),
    "author": "AIBAST",
    "tags": ["prior-auth", "evidence-packet", "payer-criteria", "healthcare", "human-review"],
    "category": "healthcare",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}

SAFETY = (
    "Synthetic demonstration data only. This output is a read-only evidence draft, not an "
    "authorization, eligibility, medical-necessity, diagnosis, or treatment decision. A qualified "
    "utilization reviewer must verify payer policy and clinical evidence before any submission."
)

REQUESTS = {
    "SYN-AUTH-001": {
        "service": "synthetic knee imaging request",
        "payer": "Synthetic Health Plan",
        "source_status": "additional evidence requested",
        "source_date": "2026-07-30",
        "policy_id": "SYN-POL-IMG-01",
        "evidence": {
            "encounter note": "present",
            "prior imaging report": "present",
            "conservative-care duration": "not found in synthetic source",
        },
    },
    "SYN-AUTH-002": {
        "service": "synthetic outpatient procedure request",
        "payer": "Synthetic Community Plan",
        "source_status": "payer response recorded",
        "source_date": "2026-07-31",
        "policy_id": "SYN-POL-PROC-02",
        "evidence": {
            "encounter note": "present",
            "specialist note": "present",
            "current payer policy confirmation": "requires human review",
        },
    },
}

POLICIES = {
    "SYN-POL-IMG-01": {
        "title": "Synthetic Imaging Evidence Checklist",
        "requirements": ["relevant encounter note", "prior imaging evidence", "documented duration fields"],
        "effective_date": "2026-07-01",
    },
    "SYN-POL-PROC-02": {
        "title": "Synthetic Procedure Evidence Checklist",
        "requirements": ["relevant encounter note", "specialist documentation", "current policy version"],
        "effective_date": "2026-07-01",
    },
}

# Demo authorization portfolio (video scenario). All patients, IDs and numbers are fictional.
PATIENT_REQUESTS = {
    "PA-2024-892741": {"patient": "Robert Chen", "listed_as": "Chen, Robert", "procedure": "Lumbar MRI", "payer": "Insurance", "status": "Ready to submit"},
    "PA-2024-892655": {"patient": "Ana Martinez", "listed_as": "Martinez, Ana", "procedure": "Knee arthroscopy", "payer": "Insurance", "status": "Approved"},
    "PA-2024-892698": {"patient": "David Thompson", "listed_as": "Thompson, David", "procedure": "Cervical MRI", "payer": "Insurance", "status": "Pending"},
    "PA-2024-892712": {"patient": "Sarah Williams", "listed_as": "Williams, Sarah", "procedure": "PT (20 visits)", "payer": "Insurance", "status": "Under review"},
    "PA-2024-891977": {"patient": "Michael Johnson", "listed_as": "Johnson, Michael", "procedure": "Sleep study", "payer": "Medicare", "status": "Denied (appealing)"},
}

OPEN_STATUSES = ["Ready to submit", "Pending", "Under review"]

PORTFOLIO_METRICS = {"avg_approval_days": 2.4, "approval_rate_month_pct": 91, "historical_similar_approval_pct": 94}

CHEN_REQUEST = {
    "auth_id": "PA-2024-892741",
    "patient": "Robert Chen",
    "dob": "05/22/1965",
    "mrn": "MR-489327",
    "insurance": "Insurance PPO #XY4829103",
    "cpt": "72148 - Lumbar MRI w/o contrast",
    "provider": "Dr. James Thompson (Orthopedics)",
    "diagnosis": "M54.5 - Chronic low back pain",
    "indication": "Failed 6 weeks conservative therapy",
    "payer_reference": "Case #4729183",
    "prepared_at": "Today at 3:47 PM",
    "review_type": "Standard (non-urgent)",
    "expected_decision": "Within 2 business days",
    "reviewer": "Automated criteria screening",
}

PAYER_REQUIREMENTS_72148 = [
    ["Clinical notes", "Last 3 office visits attached", "Met"],
    ["Conservative therapy", "PT x6 weeks, NSAIDs documented", "Met"],
    ["Symptom duration", "8 weeks, no improvement", "Met"],
    ["Red flag screening", "Negative (no fever/trauma/cancer)", "Met"],
    ["Provider NPI", "Dr. Thompson #1234567890", "Met"],
    ["Prior imaging", "None on file (first lumbar study)", "Met"],
]

DOCUMENTATION_STRENGTHS = [
    "Conservative therapy well-documented (PT, NSAIDs)",
    "Symptom duration >6 weeks",
    "Clinical notes support medical necessity criteria",
    "No inappropriate imaging red flags",
    "Complete documentation package",
]

APPEAL_STRATEGY = [
    "Peer-to-peer review with radiologist",
    "Additional functional impact documentation",
    "Imaging guidelines citation",
]

PROPOSED_NOTIFICATIONS = [
    "Patient: SMS with tracking link",
    "Dr. Thompson: Inbox message",
    "Radiology: Pending alert for scheduling",
]

TRACKING_PLAN = [
    "Status checks: every 4 hours via portal",
    "Patient notification: SMS when approved (includes auth #)",
    "Radiology alert: scheduling team notified to book slot",
    "Provider update: Dr. Thompson via secure message",
    "Escalation: auto-trigger if no decision in 48 hours",
    "Appeal workflow: ready if denied",
]

JOHNSON_DENIAL = {
    "auth_id": "PA-2024-891977",
    "reason": "Insufficient clinical documentation of daytime symptoms",
    "missing": [
        "Epworth Sleepiness Scale not in records",
        "Work/driving impairment not documented",
        "Failed CPAP trial not clearly stated",
    ],
    "appeal_actions": [
        "Peer-to-peer review scheduled - tomorrow 2 PM",
        "Additional symptom questionnaire completed",
        "Employer letter documenting work issues",
        "Prior CPAP compliance data retrieved",
    ],
    "timeline": "Decision expected within 5 business days",
}

DEMO_OPERATIONS = [
    "patient_auth_request", "payer_requirements_check", "submission_packet", "approval_outlook",
    "tracking_plan", "portfolio_status", "denial_review",
]

ALIASES = {
    "auth_request": "request_evidence",
    "clinical_criteria_check": "criteria_evidence",
    "status_tracking": "status_summary",
    "appeal_preparation": "appeal_evidence_packet",
}


def _notice(title):
    return [f"# {title}", "", f"> {SAFETY}", ""]


def _resolve_patient(query):
    """Patient name or PA-2024 ID (e.g. 'Robert Chen', 'Johnson'); default Robert Chen; None when nothing matches."""
    if not query:
        return "PA-2024-892741"
    q = query.lower().strip()
    for key in PATIENT_REQUESTS:
        if key.lower() in q or q in PATIENT_REQUESTS[key]["patient"].lower():
            return key
    return None


def _no_patient(query):
    names = ", ".join(r["patient"] + " (" + pid + ")" for pid, r in PATIENT_REQUESTS.items())
    return f"# Prior Authorization\n\n> {SAFETY}\n\nNo synthetic request matched `{query}`. Known requests: {names}."


def _selected_request(auth_id):
    if not auth_id:
        return REQUESTS.items()
    if auth_id not in REQUESTS:
        return []
    return [(auth_id, REQUESTS[auth_id])]


class PriorAuthorizationAgent(BasicAgent):
    """Assemble evidence without making an authorization outcome."""

    def __init__(self):
        self.name = "PriorAuthorizationAgent"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["request_evidence", "criteria_evidence", "status_summary", "appeal_evidence_packet"] + DEMO_OPERATIONS,
                        "description": (
                            "Read-only utilization-review evidence operation. The demo patient is Robert "
                            "Chen (lumbar MRI, PA-2024-892741); call right away, no ID is needed. "
                            "patient_auth_request: a patient needs prior auth / 'can you submit this' - "
                            "verify the request details. payer_requirements_check: check payer or "
                            "insurance requirements. submission_packet: 'submit it now' / confirmation "
                            "details - returns the ready-to-submit packet (never submits). "
                            "approval_outlook: likelihood of approval and appeal strategy if denied. "
                            "tracking_plan: configure automatic tracking / notify everyone when approved. "
                            "portfolio_status: all pending prior auths and their status. denial_review: "
                            "the denied Medicare case / why a request was denied and the appeal. "
                            "request_evidence, criteria_evidence, status_summary and appeal_evidence_packet "
                            "cover the SYN-AUTH evidence-inventory requests."
                        ),
                    },
                    "patient": {
                        "type": "string",
                        "description": "Optional patient name or PA-2024 request ID for the demo operations (default Robert Chen; denial_review always shows the denied Michael Johnson case).",
                    },
                    "auth_id": {
                        "type": "string",
                        "enum": sorted(REQUESTS),
                        "description": "Optional synthetic request identifier.",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        operation = ALIASES.get(kwargs.get("operation", ""), kwargs.get("operation", ""))
        routes = {
            "request_evidence": self._request_evidence,
            "criteria_evidence": self._criteria_evidence,
            "status_summary": self._status_summary,
            "appeal_evidence_packet": self._appeal_evidence_packet,
        }
        demo = {
            "patient_auth_request": self._patient_auth_request,
            "payer_requirements_check": self._payer_requirements_check,
            "submission_packet": self._submission_packet,
            "approval_outlook": self._approval_outlook,
            "tracking_plan": self._tracking_plan,
            "portfolio_status": self._portfolio_status,
            "denial_review": self._denial_review,
        }
        if operation in demo:
            pid = _resolve_patient(kwargs.get("patient"))
            if pid is None:
                return _no_patient(kwargs.get("patient"))
            return demo[operation](pid)
        if operation not in routes:
            return f"**Error:** Unknown operation `{operation}`. No action was taken."
        return routes[operation](kwargs.get("auth_id"))

    def _chen_only(self, pid, title):
        r = PATIENT_REQUESTS[pid]
        return (f"# {title}\n\n> {SAFETY}\n\nThe detailed packet in this synthetic set is for Robert Chen "
                f"(PA-2024-892741). {r['patient']} ({pid}): {r['procedure']}, {r['payer']}, {r['status']}.")

    def _patient_auth_request(self, pid):
        if pid != CHEN_REQUEST["auth_id"]:
            return self._chen_only(pid, "Prior Authorization Request")
        c = CHEN_REQUEST
        lines = _notice("Prior Authorization Request")
        lines.append("Patient demographics, insurance coverage and clinical documentation verified against the "
                     "synthetic EHR record. Ready to prepare for submission.")
        lines.append("")
        lines.append("| Detail | Value |")
        lines.append("|---|---|")
        lines.append(f"| Patient | {c['patient']}, DOB {c['dob']} |")
        lines.append(f"| MRN | {c['mrn']} |")
        lines.append(f"| Insurance | {c['insurance']} |")
        lines.append(f"| CPT code | {c['cpt']} |")
        lines.append(f"| Provider | {c['provider']} |")
        lines.append(f"| Diagnosis | {c['diagnosis']} (source-coded; no diagnosis added) |")
        lines.append(f"| Clinical indication | {c['indication']} |")
        lines.append("")
        lines.append("**Status:** All patient data verified from the synthetic EHR record.")
        lines.append("**Next:** check payer requirements?")
        return "\n".join(lines)

    def _payer_requirements_check(self, pid):
        if pid != CHEN_REQUEST["auth_id"]:
            return self._chen_only(pid, "Insurance Requirements")
        met = 0
        for r in PAYER_REQUIREMENTS_72148:
            if r[2] == "Met":
                met += 1
        total = len(PAYER_REQUIREMENTS_72148)
        lines = _notice("Insurance Requirements")
        lines.append(f"Payer requirements for CPT 72148 matched against {CHEN_REQUEST['patient']}'s documentation.")
        lines.append("")
        lines.append("| Requirement | Evidence found | Status |")
        lines.append("|---|---|---|")
        for r in PAYER_REQUIREMENTS_72148:
            lines.append(f"| {r[0]} | {r[1]} | {r[2]} |")
        lines.append("")
        lines.append("**Assessment:**")
        if met == total:
            lines.append(f"- All required criteria met ({met} of {total} have matching evidence)")
            lines.append("- No missing documentation")
        else:
            lines.append(f"- {met} of {total} criteria have matching evidence")
        lines.append("- Estimated payer turnaround: 24-48 hours (standard review)")
        lines.append("- A utilization reviewer confirms the match; this is not a medical-necessity decision.")
        lines.append("**Next:** prepare the authorization for submission?")
        return "\n".join(lines)

    def _submission_packet(self, pid):
        if pid != CHEN_REQUEST["auth_id"]:
            return self._chen_only(pid, "Submission Packet")
        c = CHEN_REQUEST
        lines = _notice("Submission Packet — Ready for You to Submit")
        lines.append("The authorization request is complete and ready for the coordinator to submit in the payer portal.")
        lines.append("")
        lines.append("| Detail | Value |")
        lines.append("|---|---|")
        lines.append(f"| Auth request # | {c['auth_id']} |")
        lines.append(f"| Prepared | {c['prepared_at']} |")
        lines.append(f"| Payer reference | {c['payer_reference']} |")
        lines.append(f"| Review type | {c['review_type']} |")
        lines.append(f"| Expected decision | {c['expected_decision']} |")
        lines.append(f"| Reviewer | {c['reviewer']} |")
        lines.append("")
        lines.append("**Notifications drafted (sent only when you submit):**")
        for n in PROPOSED_NOTIFICATIONS:
            lines.append(f"- {n}")
        lines.append("")
        lines.append("Not submitted: no payer submission was made and no notification was sent.")
        lines.append("**Next:** review documentation strength and appeal readiness?")
        return "\n".join(lines)

    def _approval_outlook(self, pid):
        if pid != CHEN_REQUEST["auth_id"]:
            return self._chen_only(pid, "Approval Outlook")
        m = PORTFOLIO_METRICS
        lines = _notice("Approval Outlook and Appeal Strategy")
        lines.append(f"**Historical approval rate:** {m['historical_similar_approval_pct']}% for similar cases "
                     "(synthetic historical statistic; no prediction is made for this request).")
        lines.append("")
        lines.append("**Documentation strengths:**")
        for s_ in DOCUMENTATION_STRENGTHS:
            lines.append(f"- {s_}")
        lines.append("")
        lines.append("**If denied - appeal strategy:**")
        for a in APPEAL_STRATEGY:
            lines.append(f"- {a}")
        lines.append("")
        lines.append("**Proposed escalation:** alert within 2 hours of the payer decision.")
        lines.append("**Next:** set up tracking and notifications?")
        return "\n".join(lines)

    def _tracking_plan(self, pid):
        r = PATIENT_REQUESTS[pid]
        lines = _notice("Tracking and Notification Plan (Proposed)")
        lines.append(f"Proposed monitoring for {pid} ({r['patient']}, {r['procedure']}), ready for you to switch on:")
        lines.append("")
        for t in TRACKING_PLAN:
            lines.append(f"- {t}")
        lines.append("")
        lines.append("**Tracking dashboard:** Teams channel post drafted (not posted); real-time status updates "
                     f"once enabled; expected decision {CHEN_REQUEST['expected_decision'].lower()}.")
        lines.append("Nothing is scheduled or sent until you enable it.")
        lines.append("**Next:** see all pending prior auths?")
        return "\n".join(lines)

    def _portfolio_status(self, pid):
        m = PORTFOLIO_METRICS
        open_count = 0
        for r in PATIENT_REQUESTS.values():
            if r["status"] in OPEN_STATUSES:
                open_count += 1
        lines = _notice("Active Prior Authorizations")
        lines.append("| Auth # | Patient | Procedure | Payer | Status |")
        lines.append("|---|---|---|---|---|")
        for k, r in PATIENT_REQUESTS.items():
            lines.append(f"| {k} | {r['listed_as']} | {r['procedure']} | {r['payer']} | {r['status']} |")
        lines.append("")
        lines.append("**Portfolio metrics:**")
        lines.append(f"- Pending: {open_count} authorizations")
        lines.append(f"- Avg approval time: {m['avg_approval_days']} days")
        lines.append(f"- Approval rate: {m['approval_rate_month_pct']}% this month")
        lines.append("Statuses are source-recorded for human review, not agent determinations.")
        lines.append("**Next:** check the denied Medicare case?")
        return "\n".join(lines)

    def _denial_review(self, pid):
        # Only one request in this synthetic set is denied; the review always shows it.
        d = JOHNSON_DENIAL
        pid = d["auth_id"]
        r = PATIENT_REQUESTS[pid]
        lines = _notice(f"Denial Details - {r['listed_as']} - {r['procedure']}")
        lines.append(f"**Request:** {pid}, {r['patient']}, {r['procedure']}, {r['payer']} - {r['status']}")
        lines.append(f"**Reason:** {d['reason']}")
        lines.append("")
        lines.append("**Missing elements:**")
        for x in d["missing"]:
            lines.append(f"- {x}")
        lines.append("")
        lines.append("**Appeal actions recorded:**")
        for x in d["appeal_actions"]:
            lines.append(f"- {x}")
        lines.append("")
        lines.append(f"**Timeline:** {d['timeline']}")
        lines.append("A qualified reviewer owns the appeal; this summary makes no authorization decision.")
        lines.append("**Next:** return to the Chen authorization?")
        return "\n".join(lines)

    def _request_evidence(self, auth_id=None):
        rows = list(_selected_request(auth_id))
        if not rows:
            return f"# Request Evidence\n\n> {SAFETY}\n\nNo synthetic request matched `{auth_id}`."
        lines = _notice("Prior-Authorization Evidence Inventory")
        for rid, request in rows:
            lines.extend([
                f"## {rid}: {request['service']}",
                f"- Payer in synthetic source: {request['payer']}",
                f"- Source-recorded workflow state: {request['source_status']} ({request['source_date']})",
                f"- Referenced policy: {request['policy_id']}",
                "",
            ])
            for item, state in request["evidence"].items():
                lines.append(f"- {item}: {state}")
            lines.append("")
        return "\n".join(lines)

    def _criteria_evidence(self, auth_id=None):
        rows = list(_selected_request(auth_id))
        if not rows:
            return f"# Criteria Evidence\n\n> {SAFETY}\n\nNo synthetic request matched `{auth_id}`."
        lines = _notice("Criteria-to-Evidence Crosswalk")
        for rid, request in rows:
            policy = POLICIES[request["policy_id"]]
            lines.extend([
                f"## {rid} — {policy['title']}",
                f"- Synthetic policy effective date: {policy['effective_date']}",
                "- Checklist only; presence does not establish medical necessity or authorization.",
            ])
            for requirement in policy["requirements"]:
                lines.append(f"- Reviewer check: {requirement}")
            lines.append("")
        return "\n".join(lines)

    def _status_summary(self, auth_id=None):
        rows = list(_selected_request(auth_id))
        if not rows:
            return f"# Status Summary\n\n> {SAFETY}\n\nNo synthetic request matched `{auth_id}`."
        lines = _notice("Source-Recorded Status Summary")
        for rid, request in rows:
            lines.extend([
                f"- {rid}: {request['source_status']} as recorded on {request['source_date']}",
                "  - This is a source transcription, not an agent determination.",
            ])
        return "\n".join(lines)

    def _appeal_evidence_packet(self, auth_id=None):
        rows = list(_selected_request(auth_id))
        if not rows:
            return f"# Appeal Evidence Packet\n\n> {SAFETY}\n\nNo synthetic request matched `{auth_id}`."
        lines = _notice("Reconsideration Evidence Draft")
        lines.append("A reviewer must confirm that reconsideration or appeal is appropriate and permitted.")
        lines.append("")
        for rid, request in rows:
            lines.extend([
                f"## {rid}",
                f"- Source workflow state: {request['source_status']}",
                f"- Policy reference to verify: {request['policy_id']}",
                "- Include only authorized, minimum-necessary evidence.",
                "- Human utilization reviewer owns rationale, completeness, and submission.",
                "",
            ])
        return "\n".join(lines)


if __name__ == "__main__":
    agent = PriorAuthorizationAgent()
    for op in DEMO_OPERATIONS:
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
