"""
Permit and License Management Agent for Energy sector.

Tracks permits and licenses across energy facilities, manages renewal
calendars, identifies compliance gaps, monitors application status, and
assembles renewal work packets for a human to execute.
"""

import sys
import os
import datetime
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/permit-license-management",
    "version": "1.0.0",
    "display_name": "Permit & License Management Agent",
    "description": "Tracks permits and licenses across energy facilities, manages renewal calendars, identifies compliance gaps, monitors applications, and assembles renewal work packets for a person to execute.",
    "author": "AIBAST",
    "tags": ["permits", "licenses", "compliance", "regulatory", "energy", "renewals"],
    "category": "energy",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Synthetic domain data
# ---------------------------------------------------------------------------

PERMITS = {
    "PRM-6001": {
        "name": "Title V Air Operating Permit",
        "facility": "Riverside Generating Station",
        "issuing_authority": "CA Air Resources Board",
        "permit_number": "AOP-CA-2024-1847",
        "issued_date": "2024-06-15",
        "expiration_date": "2029-06-15",
        "status": "active",
        "type": "air_quality",
        "renewal_lead_days": 365,
        "conditions": 24,
        "last_inspection": "2025-09-22",
    },
    "PRM-6002": {
        "name": "NPDES Stormwater Discharge Permit",
        "facility": "Riverside Generating Station",
        "issuing_authority": "CA State Water Board",
        "permit_number": "NPDES-CA-0052841",
        "issued_date": "2023-03-01",
        "expiration_date": "2026-03-01",
        "status": "expired",
        "type": "water_discharge",
        "renewal_lead_days": 180,
        "conditions": 18,
        "last_inspection": "2025-07-14",
    },
    "PRM-6003": {
        "name": "RCRA Hazardous Waste Generator",
        "facility": "Bayshore Refinery",
        "issuing_authority": "EPA Region 6",
        "permit_number": "TXD-0489-2215",
        "issued_date": "2022-01-10",
        "expiration_date": "2027-01-10",
        "status": "active",
        "type": "waste_management",
        "renewal_lead_days": 270,
        "conditions": 32,
        "last_inspection": "2025-11-05",
    },
    "PRM-6004": {
        "name": "Pipeline Operating License",
        "facility": "Northeast Corridor Pipeline",
        "issuing_authority": "PHMSA",
        "permit_number": "PHMSA-NE-7742",
        "issued_date": "2021-08-20",
        "expiration_date": "2026-08-20",
        "status": "active",
        "type": "pipeline_operation",
        "renewal_lead_days": 365,
        "conditions": 28,
        "last_inspection": "2025-10-30",
    },
    "PRM-6005": {
        "name": "Coal Combustion Residuals Permit",
        "facility": "Ridgeline Coal Station",
        "issuing_authority": "CO Dept of Public Health",
        "permit_number": "CCR-CO-2023-0091",
        "issued_date": "2023-04-01",
        "expiration_date": "2026-04-01",
        "status": "active",
        "type": "waste_management",
        "renewal_lead_days": 180,
        "conditions": 21,
        "last_inspection": "2025-08-18",
    },
    "PRM-6006": {
        "name": "Spill Prevention Control Plan",
        "facility": "Bayshore Refinery",
        "issuing_authority": "EPA Region 6",
        "permit_number": "SPCC-TX-2024-3340",
        "issued_date": "2024-02-15",
        "expiration_date": "2029-02-15",
        "status": "active",
        "type": "spill_prevention",
        "renewal_lead_days": 365,
        "conditions": 15,
        "last_inspection": "2025-06-02",
    },
}

APPLICATIONS = {
    "APP-7001": {
        "permit_name": "NPDES Stormwater Discharge Permit Renewal",
        "facility": "Riverside Generating Station",
        "submitted_date": "2025-09-01",
        "authority": "CA State Water Board",
        "status": "under_review",
        "expected_decision": "2026-04-15",
        "comments_received": 3,
    },
    "APP-7002": {
        "permit_name": "New Source Review - Gas Turbine Expansion",
        "facility": "Riverside Generating Station",
        "submitted_date": "2026-01-20",
        "authority": "CA Air Resources Board",
        "status": "public_comment",
        "expected_decision": "2026-06-30",
        "comments_received": 12,
    },
    "APP-7003": {
        "permit_name": "Pipeline Integrity Management Plan Update",
        "facility": "Northeast Corridor Pipeline",
        "submitted_date": "2026-02-10",
        "authority": "PHMSA",
        "status": "submitted",
        "expected_decision": "2026-05-15",
        "comments_received": 0,
    },
}

REGULATORY_REQUIREMENTS = {
    "air_quality": ["Continuous emissions monitoring", "Annual stack testing", "Quarterly compliance reports"],
    "water_discharge": ["Monthly effluent sampling", "Annual DMR submission", "Stormwater pollution prevention plan"],
    "waste_management": ["Biennial hazardous waste report", "Manifest tracking", "Land disposal restrictions compliance"],
    "pipeline_operation": ["Integrity management program", "Operator qualification records", "Emergency response plan"],
    "spill_prevention": ["Annual SPCC plan review", "Integrity testing of containers", "Discharge prevention briefings"],
}

# Accountable role for renewal work, set by permit type (policy, not per permit).
OWNER_ROLES = {
    "air_quality": "Sustainability Lead",
    "water_discharge": "Compliance Manager",
    "waste_management": "Compliance Manager",
    "pipeline_operation": "Plant Manager / Reliability Engineer",
    "spill_prevention": "Plant Manager / Reliability Engineer",
}

# Draft submission checklist. Identical for every permit; the person named as
# owner executes it. Nothing here is performed by the agent.
RENEWAL_CHECKLIST = [
    "Confirm the issuing authority's current renewal form, fee, and filing channel",
    "Assemble the compliance record since issuance, including the last inspection date",
    "Attach current evidence for every recurring requirement of this permit type",
    "Route the draft package for internal environmental and legal review",
    "Hand the signed package to the accountable owner for submission before expiration",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _matches_facility(name, facility):
    """True when no filter is set, or when the filter text appears in the name."""
    if not facility or not str(facility).strip():
        return True
    return str(facility).strip().lower() in name.lower()


def _filtered_permits(facility=None):
    return [(pid, p) for pid, p in PERMITS.items() if _matches_facility(p["facility"], facility)]


def _filtered_applications(facility=None):
    return [(aid, a) for aid, a in APPLICATIONS.items() if _matches_facility(a["facility"], facility)]


def _renewal_start(expiration_date, lead_days):
    """renewal start = expiration_date - renewal_lead_days (ISO in, ISO out)."""
    expires = datetime.date.fromisoformat(expiration_date)
    return (expires - datetime.timedelta(days=int(lead_days))).isoformat()


def _filter_lines(facility):
    """Filter banner lines, or an empty list when no filter is applied."""
    if not facility or not str(facility).strip():
        return []
    return [
        f"**Filter:** facility = {str(facility).strip()} - this view is filtered; "
        "counts cover the filtered rows only.",
        "",
    ]


def _empty_filter_block(heading, facility, kind):
    return "\n".join([
        heading,
        "",
        f"No {kind} match facility filter \"{str(facility).strip()}\". "
        "Nothing else was withheld - the filter produced an empty view.",
    ])


def _permit_inventory(facility=None):
    inventory = []
    rows = _filtered_permits(facility)
    for pid, p in rows:
        inventory.append({
            "id": pid, "name": p["name"], "facility": p["facility"],
            "authority": p["issuing_authority"], "permit_number": p["permit_number"],
            "status": p["status"], "type": p["type"],
            "expiration": p["expiration_date"], "conditions": p["conditions"],
        })
    active = sum(1 for _, p in rows if p["status"] == "active")
    expired = sum(1 for _, p in rows if p["status"] == "expired")
    return {"permits": inventory, "total": len(inventory), "active": active, "expired": expired}


def _renewal_calendar(facility=None):
    calendar = []
    for pid, p in _filtered_permits(facility):
        calendar.append({
            "id": pid, "name": p["name"], "facility": p["facility"],
            "expiration": p["expiration_date"], "status": p["status"],
            "renewal_lead_days": p["renewal_lead_days"],
        })
    calendar.sort(key=lambda x: x["expiration"])
    return {"calendar": calendar}


def _compliance_gaps(facility=None):
    gaps = []
    for pid, p in _filtered_permits(facility):
        if p["status"] == "expired":
            gaps.append({
                "id": pid, "name": p["name"], "facility": p["facility"],
                "gap_type": "expired_permit", "severity": "critical",
                "detail": f"Permit {p['permit_number']} expired on {p['expiration_date']}",
            })
        reqs = REGULATORY_REQUIREMENTS.get(p["type"], [])
        if p["type"] == "water_discharge" and p["status"] == "expired":
            for req in reqs:
                gaps.append({
                    "id": pid, "name": p["name"], "facility": p["facility"],
                    "gap_type": "requirement_at_risk", "severity": "high",
                    "detail": f"Requirement '{req}' at risk due to expired permit",
                })
    return {"gaps": gaps, "total": len(gaps), "critical": sum(1 for g in gaps if g["severity"] == "critical")}


def _application_status(facility=None):
    statuses = []
    for aid, a in _filtered_applications(facility):
        statuses.append({
            "id": aid, "name": a["permit_name"], "facility": a["facility"],
            "authority": a["authority"], "submitted": a["submitted_date"],
            "status": a["status"], "expected_decision": a["expected_decision"],
            "comments": a["comments_received"],
        })
    return {"applications": statuses, "total": len(statuses)}


def _renewal_work_packet(facility=None):
    """Assemble the renewal packet for each permit. Preparation only - no filing."""
    packets = []
    for pid, p in _filtered_permits(facility):
        packets.append({
            "id": pid, "name": p["name"], "facility": p["facility"],
            "authority": p["issuing_authority"], "permit_number": p["permit_number"],
            "type": p["type"], "status": p["status"],
            "expiration": p["expiration_date"],
            "renewal_lead_days": p["renewal_lead_days"],
            "renewal_start": _renewal_start(p["expiration_date"], p["renewal_lead_days"]),
            "owner": f"{OWNER_ROLES.get(p['type'], 'Compliance Manager')}, {p['facility']}",
            "evidence": REGULATORY_REQUIREMENTS.get(p["type"], []),
        })
    packets.sort(key=lambda x: x["renewal_start"])
    return {
        "packets": packets,
        "total": len(packets),
        "expired": sum(1 for k in packets if k["status"] == "expired"),
        "checklist": RENEWAL_CHECKLIST,
    }


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class PermitLicenseManagementAgent(BasicAgent):
    """Permit and license tracking and compliance management agent."""

    def __init__(self):
        self.name = "@aibast-agents-library/permit-license-management"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "permit_inventory",
                            "renewal_calendar",
                            "compliance_gaps",
                            "application_status",
                            "renewal_work_packet",
                        ],
                        "description": "The permit management operation to perform.",
                    },
                    "facility": {
                        "type": "string",
                        "description": "Optional facility name to filter results (Riverside Generating Station, Bayshore Refinery, Northeast Corridor Pipeline, Ridgeline Coal Station). Applied to every row and every count.",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation", "permit_inventory")
        facility = kwargs.get("facility")
        if op == "permit_inventory":
            return self._permit_inventory(facility)
        elif op == "renewal_calendar":
            return self._renewal_calendar(facility)
        elif op == "compliance_gaps":
            return self._compliance_gaps(facility)
        elif op == "application_status":
            return self._application_status(facility)
        elif op == "renewal_work_packet":
            return self._renewal_work_packet(facility)
        return f"**Error:** Unknown operation `{op}`."

    def _permit_inventory(self, facility=None) -> str:
        data = _permit_inventory(facility)
        if data["total"] == 0:
            return _empty_filter_block("# Permit & License Inventory", facility, "permits")
        lines = [
            "# Permit & License Inventory",
            "",
        ]
        lines.extend(_filter_lines(facility))
        lines.extend([
            f"**Total Permits:** {data['total']} | **Active:** {data['active']} | **Expired:** {data['expired']}",
            "",
            "| ID | Permit | Facility | Authority | Status | Expiration | Conditions |",
            "|----|--------|----------|-----------|--------|-----------|-----------|",
        ])
        for p in data["permits"]:
            lines.append(
                f"| {p['id']} | {p['name']} | {p['facility']} "
                f"| {p['authority']} | {p['status'].upper()} | {p['expiration']} | {p['conditions']} |"
            )
        return "\n".join(lines)

    def _renewal_calendar(self, facility=None) -> str:
        data = _renewal_calendar(facility)
        if not data["calendar"]:
            return _empty_filter_block("# Permit Renewal Calendar", facility, "permits")
        lines = [
            "# Permit Renewal Calendar",
            "",
        ]
        lines.extend(_filter_lines(facility))
        lines.extend([
            "| Permit | Facility | Expiration | Status | Lead Time |",
            "|--------|----------|-----------|--------|-----------|",
        ])
        for c in data["calendar"]:
            lines.append(
                f"| {c['name']} | {c['facility']} | {c['expiration']} "
                f"| {c['status'].upper()} | {c['renewal_lead_days']} days |"
            )
        return "\n".join(lines)

    def _compliance_gaps(self, facility=None) -> str:
        if not _filtered_permits(facility):
            return _empty_filter_block("# Compliance Gaps", facility, "permits")
        data = _compliance_gaps(facility)
        if data["total"] == 0:
            head = ["# Compliance Gaps", ""]
            head.extend(_filter_lines(facility))
            head.append("No compliance gaps identified.")
            return "\n".join(head)
        lines = [
            "# Compliance Gap Analysis",
            "",
        ]
        lines.extend(_filter_lines(facility))
        lines.extend([
            f"**Total Gaps:** {data['total']} | **Critical:** {data['critical']}",
            "",
            "| Permit | Facility | Gap Type | Severity | Detail |",
            "|--------|----------|----------|----------|--------|",
        ])
        for g in data["gaps"]:
            lines.append(
                f"| {g['name']} | {g['facility']} | {g['gap_type']} "
                f"| {g['severity'].upper()} | {g['detail']} |"
            )
        return "\n".join(lines)

    def _application_status(self, facility=None) -> str:
        data = _application_status(facility)
        if data["total"] == 0:
            return _empty_filter_block("# Permit Application Status", facility, "applications")
        lines = [
            "# Permit Application Status",
            "",
        ]
        lines.extend(_filter_lines(facility))
        lines.extend([
            f"**Active Applications:** {data['total']}",
            "",
            "| ID | Application | Facility | Authority | Submitted | Status | Decision Date | Comments |",
            "|----|-------------|----------|-----------|-----------|--------|--------------|----------|",
        ])
        for a in data["applications"]:
            lines.append(
                f"| {a['id']} | {a['name']} | {a['facility']} "
                f"| {a['authority']} | {a['submitted']} | {a['status']} "
                f"| {a['expected_decision']} | {a['comments']} |"
            )
        return "\n".join(lines)

    def _renewal_work_packet(self, facility=None) -> str:
        data = _renewal_work_packet(facility)
        if data["total"] == 0:
            return _empty_filter_block("# Renewal Work Packet", facility, "permits")
        lines = [
            "# Renewal Work Packet",
            "",
        ]
        lines.extend(_filter_lines(facility))
        lines.extend([
            f"**Packets:** {data['total']} | **Expired (act now):** {data['expired']}",
            "",
            "| Permit | ID | Facility | Authority | Permit Number | Expiration | Lead Time | Renewal Start | Owner | Status |",
            "|--------|----|----------|-----------|---------------|-----------|-----------|--------------|-------|--------|",
        ])
        for k in data["packets"]:
            lines.append(
                f"| {k['name']} | {k['id']} | {k['facility']} | {k['authority']} "
                f"| {k['permit_number']} | {k['expiration']} | {k['renewal_lead_days']} days "
                f"| {k['renewal_start']} | {k['owner']} | {k['status'].upper()} |"
            )
        lines.extend(["", "## Draft submission checklist (same for every packet)", ""])
        for i, step in enumerate(data["checklist"], start=1):
            lines.append(f"{i}. {step}")
        lines.extend([
            "",
            "## Evidence to attach, by permit",
            "",
            "| Permit | Type | Evidence required |",
            "|--------|------|-------------------|",
        ])
        for k in data["packets"]:
            evidence = "; ".join(k["evidence"]) if k["evidence"] else "None listed for this type"
            lines.append(f"| {k['id']} | {k['type']} | {evidence} |")
        lines.extend([
            "",
            "Nothing in this packet has been filed, submitted, or scheduled. Each packet is "
            "prepared for the named owner to execute.",
        ])
        return "\n".join(lines)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = PermitLicenseManagementAgent()
    for op in ["permit_inventory", "renewal_calendar", "compliance_gaps",
               "application_status", "renewal_work_packet"]:
        print(f"\n{'='*60}")
        print(f"Operation: {op}")
        print("=" * 60)
        print(agent.perform(operation=op))
