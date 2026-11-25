---
name: "patient-intake"
description: "Prepares synthetic new-patient intake, coverage evidence, provider availability, appointment request drafts, specialty intake packets, and reminder plans for patient-access staff; it never determines eligibility, books appointments, sends messages, or changes records. Always use this tool for patient intake and scheduling. The demo patient is Sarah Martinez (SYN-PT-003, new patient, chronic migraines, Blue Cross Blue Shield, Dr. James Anderson, Neurology); call it without asking for IDs. Demo flow: a new patient called requesting a consultation -> new_patient_intake; provider availability and insurance coverage -> appointment_availability and coverage_evidence; book her for a slot -> appointment_hold_draft; what forms are in the intake packet -> intake_packet; set up reminders / reduce no-shows -> reminder_plan."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "patient_intake_agent.py"
  tool-name: "PatientIntakeAgent"
  agent-sha256: "c94a5ac17c924c4f9e37a23dcd00a55eecb269394daee23810e82c9a53157496"
  version: "1.2.0"
  author: "AIBAST"
  tags: "intake, scheduling, coverage-evidence, reminders, healthcare, human-review"
---

# Patient Intake

Prepares synthetic new-patient intake, coverage evidence, provider availability, appointment request drafts, specialty intake packets, and reminder plans for patient-access staff; it never determines eligibility, books appointments, sends messages, or changes records. Always use this tool for patient intake and scheduling. The demo patient is Sarah Martinez (SYN-PT-003, new patient, chronic migraines, Blue Cross Blue Shield, Dr. James Anderson, Neurology); call it without asking for IDs. Demo flow: a new patient called requesting a consultation -> new_patient_intake; provider availability and insurance coverage -> appointment_availability and coverage_evidence; book her for a slot -> appointment_hold_draft; what forms are in the intake packet -> intake_packet; set up reminders / reduce no-shows -> reminder_plan.

## What it needs

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "intake_readiness",
        "coverage_evidence",
        "appointment_availability",
        "pre_visit_summary",
        "new_patient_intake",
        "appointment_hold_draft",
        "intake_packet",
        "reminder_plan"
      ],
      "description": "new_patient_intake: register a new patient who called for a consultation. appointment_availability: the provider's open slots. coverage_evidence: verify insurance coverage, copay, deductible, prior auth, network. appointment_hold_draft: book her for a slot (returns a booking request for staff). intake_packet: which forms a new patient's digital intake packet contains (HIPAA consent, medication history). reminder_plan: automated reminders and no-show reduction. intake_readiness: what is still missing from a patient's intake (e.g. Patient Alpha, SYN-PT-001). pre_visit_summary: pre-visit readiness summary for a patient."
    },
    "patient_id": {
      "type": "string",
      "description": "Optional patient ID or name (default SYN-PT-003, Sarah Martinez)."
    },
    "provider": {
      "type": "string",
      "description": "Optional provider (default the patient's requested provider, Dr. James Anderson)."
    },
    "slot": {
      "type": "string",
      "description": "Requested slot for appointment_hold_draft / reminder_plan, e.g. 'Tuesday 2:30 PM'."
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
   python3 scripts/run.py --json '{"operation": "<string>", "patient_id": "<string>", "provider": "<string>", "slot": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=c94a5ac17c924c4f9e37a23dcd00a55eecb269394daee23810e82c9a53157496 -->
```python
"""Synthetic patient intake and scheduling support: new-patient registration drafts, coverage evidence,
provider availability, appointment request drafts, specialty intake packets, and reminder plans."""

import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/patient-intake",
    "version": "1.2.0",
    "display_name": "Patient Intake and Scheduling Agent",
    "description": (
        "Prepares synthetic new-patient intake, coverage evidence, provider availability, appointment "
        "request drafts, specialty intake packets, and reminder plans for patient-access staff; it never "
        "determines eligibility, books appointments, sends messages, or changes records."
    ),
    "author": "AIBAST",
    "tags": ["intake", "scheduling", "coverage-evidence", "reminders", "healthcare", "human-review"],
    "category": "healthcare",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}

SAFETY = (
    "Synthetic demonstration data only. Read-only draft for authorized patient-access staff. "
    "Confirm coverage and appointment details in approved source systems; do not use this output "
    "to determine eligibility, schedule care, or change a patient record. Human review is required."
)

PATIENTS = {
    "SYN-PT-001": {
        "label": "Synthetic Patient Alpha",
        "language": "English",
        "forms": ["contact details", "consent acknowledgement", "medication list"],
        "missing": ["emergency contact confirmation"],
        "coverage": {
            "payer": "Synthetic Health Plan",
            "recorded_status": "source record received",
            "evidence_date": "2026-07-30",
            "follow_up": "Confirm active coverage and network status in the payer portal.",
        },
        "visit": {"service": "new patient consultation", "provider": "Clinician A", "date": "2026-08-15"},
    },
    "SYN-PT-002": {
        "label": "Synthetic Patient Beta",
        "language": "Spanish",
        "forms": ["contact details", "consent acknowledgement"],
        "missing": ["preferred-language packet", "medication list"],
        "coverage": {
            "payer": "Synthetic Community Plan",
            "recorded_status": "referral evidence missing",
            "evidence_date": "2026-07-29",
            "follow_up": "Ask authorized staff to confirm referral and coverage evidence.",
        },
        "visit": {"service": "follow-up consultation", "provider": "Clinician B", "date": "2026-08-18"},
    },
    "SYN-PT-003": {
        "label": "Sarah Martinez",
        "patient_type": "New Patient",
        "language": "English",
        "chief_complaint": "Chronic migraines",
        "timeframe_days": 14,
        "request_date": "2024-01-23",
        "forms": [],
        "missing": ["intake packet not yet completed"],
        "coverage": {
            "payer": "Blue Cross Blue Shield",
            "recorded_status": "Active",
            "evidence_date": "2024-01-23",
            "follow_up": "Confirm active coverage and network status in the payer portal.",
            "policy_number": "XXX-XX-7392",
            "group_number": "84721",
            "specialist_copay": 35,
            "deductible_met": 450,
            "deductible": 1500,
            "prior_auth": "No (initial consult exempt)",
            "network": "In-network, Tier 1",
        },
        "visit": {"service": "New Patient Consultation", "provider": "Dr. James Anderson", "date": "2024-01-30"},
    },
}

PROVIDERS = {
    "Dr. James Anderson": {"credential": "MD", "specialty": "Neurology", "location": "Neurology Clinic - Suite 405"},
}

AVAILABILITY = {
    "Clinician A": [
        {"date": "2026-08-20", "time": "10:30", "service": "new patient consultation"},
        {"date": "2026-08-22", "time": "14:00", "service": "follow-up consultation"},
    ],
    "Clinician B": [
        {"date": "2026-08-21", "time": "09:00", "service": "follow-up consultation"},
    ],
    "Dr. James Anderson": [
        {"date": "2024-01-30", "time": "14:30", "service": "new patient consultation", "label": "Tuesday 2:30 PM"},
        {"date": "2024-02-01", "time": "10:00", "service": "new patient consultation", "label": "Thursday 10:00 AM"},
    ],
}

PROVIDER_KEYS = {
    "anderson": "Dr. James Anderson",
    "clinician a": "Clinician A",
    "clinician b": "Clinician B",
}

NEW_PATIENT_VISIT_MINUTES = 60

INTAKE_PACKETS = {
    "base": [
        "Demographics Form: Name, DOB, contact info, emergency contact",
        "Insurance Verification: Photo upload for card front/back",
        "Medical History: Current medications, allergies, prior surgeries",
        "HIPAA Authorization: Digital signature required",
        "Financial Policy: Payment terms and copay acknowledgment",
    ],
    "Neurology": ["Migraine Questionnaire: HIT-6 headache impact assessment"],
}

REMINDER_PROTOCOL = {
    "touchpoints": [
        {"name": "72-Hour Reminder", "hours_before": 72, "channel": "SMS + Email"},
        {"name": "24-Hour Reminder", "hours_before": 24, "channel": "SMS + Voice call option"},
        {"name": "2-Hour Reminder", "hours_before": 2, "channel": "Final SMS"},
    ],
    "forms_alert_days_before": 1,
    "reschedule_keyword": "RESCHEDULE",
    "waitlist_rule": "Auto-fill the slot if she cancels with >24hr notice",
    "historical_no_show_rate": "8% for new patients with this protocol",
    "protocol_name": "40% no-show reduction protocol",
}

ALIASES = {
    "intake_form": "intake_readiness",
    "insurance_verification": "coverage_evidence",
    "appointment_scheduling": "appointment_availability",
}

OPERATIONS = [
    "intake_readiness",
    "coverage_evidence",
    "appointment_availability",
    "pre_visit_summary",
    "new_patient_intake",
    "appointment_hold_draft",
    "intake_packet",
    "reminder_plan",
]

DEFAULT_PATIENT = "SYN-PT-003"


def _notice(title):
    return [f"# {title}", "", f"> {SAFETY}", ""]


def _resolve_patient(query):
    """Patient ID, label or part of it ('Alpha', 'Sarah Martinez'); default the demo patient; None on a miss."""
    if not query:
        return DEFAULT_PATIENT
    q = str(query).lower().strip()
    for pid, patient in PATIENTS.items():
        if pid.lower() in q or q in patient["label"].lower():
            return pid
    return None


def _resolve_provider(query, pid):
    """Provider name or part of it; default the patient's requested provider; None on a miss."""
    if not query:
        return PATIENTS[pid]["visit"]["provider"]
    q = str(query).lower().strip()
    for key, name in PROVIDER_KEYS.items():
        if key in q or q in name.lower():
            return name
    return None


def _pick_slot(provider, slot_text):
    """'Tuesday 2:30' / 'Thursday' / '2024-02-01' picks that slot; default the first slot."""
    slots = AVAILABILITY[provider]
    q = str(slot_text or "").lower()
    for slot in slots:
        label = slot.get("label", "").lower()
        if q and (slot["date"] in q or (label and label.split()[0][:3] in q)):
            return slot
    return slots[0]


def _slot_datetime(slot):
    return datetime.datetime.strptime(f"{slot['date']} {slot['time']}", "%Y-%m-%d %H:%M")


def _fmt_day_time(moment):
    hour = moment.hour % 12 or 12
    return f"{moment:%A} {hour}:{moment:%M} {'AM' if moment.hour < 12 else 'PM'}"


def _fmt_long(moment):
    hour = moment.hour % 12 or 12
    return f"{moment:%A, %B} {moment.day}, {moment.year}", f"{hour}:{moment:%M} {'AM' if moment.hour < 12 else 'PM'}"


def _slot_label(slot):
    return slot.get("label") or f"{slot['date']} {slot['time']}"


class PatientIntakeAgent(BasicAgent):
    """Prepare intake and scheduling drafts for human review."""

    def __init__(self):
        self.name = "PatientIntakeAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                __manifest__["description"] + " Always use this tool for patient intake and "
                "scheduling. The demo patient is Sarah Martinez (SYN-PT-003, new patient, chronic "
                "migraines, Blue Cross Blue Shield, Dr. James Anderson, Neurology); call it without "
                "asking for IDs. Demo flow: a new patient called requesting a consultation -> "
                "new_patient_intake; provider availability and insurance coverage -> "
                "appointment_availability and coverage_evidence; book her for a slot -> "
                "appointment_hold_draft; what forms are in the intake packet -> intake_packet; set "
                "up reminders / reduce no-shows -> reminder_plan."
            ),
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": list(OPERATIONS),
                        "description": (
                            "new_patient_intake: register a new patient who called for a "
                            "consultation. appointment_availability: the provider's open slots. "
                            "coverage_evidence: verify insurance coverage, copay, deductible, prior "
                            "auth, network. appointment_hold_draft: book her for a slot (returns a "
                            "booking request for staff). intake_packet: which forms a new patient's "
                            "digital intake packet contains (HIPAA consent, medication history). "
                            "reminder_plan: automated reminders and no-show reduction. "
                            "intake_readiness: what is still missing from a patient's intake (e.g. "
                            "Patient Alpha, SYN-PT-001). pre_visit_summary: pre-visit readiness "
                            "summary for a patient."
                        ),
                    },
                    "patient_id": {
                        "type": "string",
                        "description": "Optional patient ID or name (default SYN-PT-003, Sarah Martinez).",
                    },
                    "provider": {
                        "type": "string",
                        "description": "Optional provider (default the patient's requested provider, Dr. James Anderson).",
                    },
                    "slot": {
                        "type": "string",
                        "description": "Requested slot for appointment_hold_draft / reminder_plan, e.g. 'Tuesday 2:30 PM'.",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        operation = ALIASES.get(kwargs.get("operation", ""), kwargs.get("operation", ""))
        routes = {
            "intake_readiness": self._intake_readiness,
            "coverage_evidence": self._coverage_evidence,
            "appointment_availability": self._appointment_availability,
            "pre_visit_summary": self._pre_visit_summary,
            "new_patient_intake": self._new_patient_intake,
            "appointment_hold_draft": self._appointment_hold_draft,
            "intake_packet": self._intake_packet,
            "reminder_plan": self._reminder_plan,
        }
        if operation not in routes:
            return f"**Error:** Unknown operation `{operation}`. No action was taken."
        pid = _resolve_patient(kwargs.get("patient_id"))
        if pid is None:
            return f"# Patient Lookup\n\n> {SAFETY}\n\nNo synthetic patient matched `{kwargs.get('patient_id')}`."
        provider = _resolve_provider(kwargs.get("provider"), pid)
        if provider is None:
            return f"# Appointment Availability\n\n> {SAFETY}\n\nNo synthetic provider matched `{kwargs.get('provider')}`."
        return routes[operation](pid, provider, kwargs.get("slot"))

    # ── existing-patient readiness ─────────────────────────────
    def _intake_readiness(self, pid, _provider, _slot):
        patient = PATIENTS[pid]
        lines = _notice("Intake Readiness Draft")
        lines.extend([
            f"## {patient['label']} ({pid})",
            f"- Preferred language recorded: {patient['language']}",
            f"- Forms present: {', '.join(patient['forms']) or 'none yet'}",
            f"- Items for staff confirmation: {', '.join(patient['missing']) or 'none recorded'}",
            "",
        ])
        return "\n".join(lines)

    def _pre_visit_summary(self, pid, _provider, _slot):
        patient = PATIENTS[pid]
        visit = patient["visit"]
        lines = _notice("Pre-Visit Readiness Summary")
        lines.extend([
            f"## {patient['label']} ({pid})",
            f"- Source-recorded visit: {visit['service']} with {visit['provider']} on {visit['date']}",
            f"- Intake items requiring confirmation: {', '.join(patient['missing']) or 'none recorded'}",
            f"- Coverage follow-up: {patient['coverage']['follow_up']}",
            "- Required reviewer: authorized patient-access staff",
            "",
        ])
        return "\n".join(lines)

    # ── video turn 1 ───────────────────────────────────────────
    def _new_patient_intake(self, pid, provider, _slot):
        patient = PATIENTS[pid]
        info = PROVIDERS.get(provider, {"specialty": "General", "credential": ""})
        lines = _notice("New Patient Registration Draft")
        lines.extend([
            f"I'll prepare {patient['label']}'s new-patient registration and check {provider}'s "
            f"{info['specialty'].lower()} schedule and her {patient['coverage']['payer']} coverage.",
            "",
            "**Patient Registration - Draft (ready for staff to create in the registration system)**",
            f"- Patient Name: {patient['label']} ({pid})",
            f"- Type: {patient.get('patient_type', 'Existing Patient')}",
            f"- Requested Provider: {provider}, {info['specialty']}",
            f"- Chief Complaint: {patient.get('chief_complaint', 'See visit record')}",
            f"- Insurance: {patient['coverage']['payer']}",
            f"- Timeframe: Within {patient.get('timeframe_days', 14)} days",
            "- Source System: Registration module (synthetic)",
            "",
            f"Next: check {provider}'s availability and verify her insurance coverage for this visit.",
        ])
        return "\n".join(lines)

    # ── video turn 2 ───────────────────────────────────────────
    def _coverage_lines(self, patient):
        cov = patient["coverage"]
        lines = [
            f"- Payer recorded in synthetic source: {cov['payer']}",
            f"- Source-recorded state: {cov['recorded_status']}",
            f"- Evidence date: {cov['evidence_date']}",
        ]
        if "specialist_copay" in cov:
            lines.extend([
                f"- Policy Number: {cov['policy_number']} | Group Number: {cov['group_number']}",
                f"- Copay: ${cov['specialist_copay']} specialist visit",
                f"- Deductible: ${cov['deductible_met']:,} met of ${cov['deductible']:,}",
                f"- Prior Auth Required: {cov['prior_auth']}",
                f"- Network: {cov['network']}",
            ])
        lines.append(f"- Human follow-up: {cov['follow_up']}")
        return lines

    def _coverage_evidence(self, pid, provider, _slot):
        patient = PATIENTS[pid]
        lines = _notice("Coverage Evidence Review")
        lines.append(f"## {patient['label']} ({pid})")
        lines.extend(self._coverage_lines(patient))
        slots = ", ".join(_slot_label(s) for s in AVAILABILITY.get(provider, []))
        lines.extend(["", f"**{provider} availability:** {slots}", ""])
        return "\n".join(lines)

    def _appointment_availability(self, pid, provider, _slot):
        patient = PATIENTS[pid]
        lines = _notice("Appointment Availability Review")
        lines.append("These are candidate source slots for staff review; nothing has been reserved or booked.")
        lines.append("")
        lines.append(f"## {provider}")
        for slot in AVAILABILITY[provider]:
            when = f" ({slot['date']} {slot['time']})" if slot.get("label") else ""
            lines.append(f"- {_slot_label(slot)}{when} — {slot['service']}")
        if "specialist_copay" in patient["coverage"]:
            cov = patient["coverage"]
            lines.extend([
                "",
                f"**Coverage snapshot for {patient['label']}:** {cov['recorded_status']} {cov['payer']}, "
                f"${cov['specialist_copay']} specialist copay, deductible ${cov['deductible_met']:,} met of "
                f"${cov['deductible']:,}, prior auth {cov['prior_auth']}, {cov['network']}.",
            ])
        lines.append("")
        return "\n".join(lines)

    # ── video turn 3 ───────────────────────────────────────────
    def _appointment_hold_draft(self, pid, provider, slot_text):
        patient = PATIENTS[pid]
        slot = _pick_slot(provider, slot_text)
        day, time = _fmt_long(_slot_datetime(slot))
        info = PROVIDERS.get(provider, {"credential": "", "location": "See scheduling system", "specialty": ""})
        packet = INTAKE_PACKETS["base"] + INTAKE_PACKETS.get(info.get("specialty", ""), [])
        names = ", ".join(item.split(":")[0] for item in packet)
        lines = _notice("Appointment Request Draft")
        lines.extend([
            f"Appointment request prepared for {patient['label']} — ready for staff to book and confirm "
            "in the scheduling system; nothing has been reserved or booked yet.",
            "",
            f"- Date: {day}",
            f"- Time: {time}",
            f"- Duration: {NEW_PATIENT_VISIT_MINUTES} minutes (new patient)",
            f"- Provider: {provider}, {info['credential']}".rstrip(", "),
            f"- Location: {info['location']}",
            f"- Visit Type: {slot['service'].title()}",
            "- Confirmation: SMS & email confirmation drafted for staff to send after booking",
            "",
            f"**Intake forms she needs before the visit:** {names}.",
            "",
        ])
        return "\n".join(lines)

    # ── video turn 4 ───────────────────────────────────────────
    def _intake_packet(self, pid, provider, _slot):
        patient = PATIENTS[pid]
        specialty = PROVIDERS.get(provider, {}).get("specialty", "")
        packet = INTAKE_PACKETS["base"][:3] + INTAKE_PACKETS.get(specialty, []) + INTAKE_PACKETS["base"][3:]
        lines = _notice("Digital Intake Packet Draft")
        lines.append(
            f"Packet tailored to {specialty or 'the visit'} for {patient['label']}: it includes HIPAA "
            "authorization and medication history. Ready for staff to send to her patient portal; "
            "she can complete it on her phone."
        )
        lines.append("")
        for item in packet:
            lines.append(f"- {item}")
        lines.extend(["- Portal Link: ready to send via SMS to the mobile number on file", ""])
        return "\n".join(lines)

    # ── video turn 5 ───────────────────────────────────────────
    def _reminder_plan(self, pid, provider, slot_text):
        patient = PATIENTS[pid]
        proto = REMINDER_PROTOCOL
        slot = _pick_slot(provider, slot_text)
        visit = _slot_datetime(slot)
        lines = _notice("No-Show Prevention Reminder Plan")
        lines.append(
            f"Recommended multi-channel reminder sequence for {patient['label']}'s {_slot_label(slot)} "
            f"visit, based on the {proto['protocol_name']} (ready for staff to activate):"
        )
        lines.append("")
        for tp in proto["touchpoints"]:
            when = visit - datetime.timedelta(hours=tp["hours_before"])
            lines.append(f"- {tp['name']}: {tp['channel']} ({_fmt_day_time(when)})")
        alert = visit - datetime.timedelta(days=proto["forms_alert_days_before"])
        lines.extend([
            f"- Forms Completion Alert: Reminder if not completed by {alert:%A}",
            f"- Easy Reschedule: Reply {proto['reschedule_keyword']} to SMS anytime",
            f"- Waitlist Automation: {proto['waitlist_rule']}",
            f"- Historical No-Show Rate: {proto['historical_no_show_rate']}",
            "",
        ])
        return "\n".join(lines)


if __name__ == "__main__":
    agent = PatientIntakeAgent()
    print(agent.perform(operation="new_patient_intake"))
    print(agent.perform(operation="appointment_availability"))
    print(agent.perform(operation="coverage_evidence"))
    print(agent.perform(operation="appointment_hold_draft", slot="Tuesday at 2:30"))
    print(agent.perform(operation="intake_packet"))
    print(agent.perform(operation="reminder_plan"))
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
