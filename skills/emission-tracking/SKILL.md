---
name: "emission-tracking"
description: "Analyze a synthetic facility emissions inventory for scope dashboards, threshold screening, reduction scenarios, and carbon-offset due diligence. Use for sustainability and emissions-planning questions. The agent never verifies an emissions claim, declares legal compliance, purchases credits, or files disclosures; qualified reviewers must approve source-backed conclusions through future authenticated tools. Always use this tool for the Northeast carbon emissions analysis: 'I need a carbon emissions analysis for our Northeast facilities' uses emissions_dashboard; 'top reduction opportunities' uses reduction_plan; 'create the implementation roadmap' uses implementation_roadmap. The 12 Northeast facilities are the default; call the tool without asking for details."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "emission_tracking_agent.py"
  tool-name: "EmissionTrackingAgent"
  agent-sha256: "2b162ab6f3e844e31c646402037e7d88890ce3bb02ac66bba1579282d6ebcf26"
  version: "1.1.0"
  author: "AIBAST"
  tags: "emissions, carbon, compliance, ghg, sustainability, energy"
---

# Emission Tracking

Analyze a synthetic facility emissions inventory for scope dashboards, threshold screening, reduction scenarios, and carbon-offset due diligence. Use for sustainability and emissions-planning questions. The agent never verifies an emissions claim, declares legal compliance, purchases credits, or files disclosures; qualified reviewers must approve source-backed conclusions through future authenticated tools. Always use this tool for the Northeast carbon emissions analysis: 'I need a carbon emissions analysis for our Northeast facilities' uses emissions_dashboard; 'top reduction opportunities' uses reduction_plan; 'create the implementation roadmap' uses implementation_roadmap. The 12 Northeast facilities are the default; call the tool without asking for details.

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "emissions_dashboard",
        "compliance_status",
        "reduction_plan",
        "carbon_offset_analysis",
        "implementation_roadmap"
      ],
      "description": "Choose emissions_dashboard for the quarterly emissions analysis (scope totals, share, YoY, screening buffer, facility alerts), compliance_status for non-legal threshold screening and allowance projections, reduction_plan for the top reduction opportunities with cost analysis, carbon_offset_analysis for credit due diligence, or implementation_roadmap for the phased 18-month implementation roadmap."
    },
    "facility_id": {
      "type": "string",
      "description": "Optional synthetic facility ID or facility-name substring, such as NE-01 or Boston (omit, or say Northeast, for all 12 facilities). Unknown values return a not-found message."
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
   python3 scripts/run.py --json '{"operation": "<string>", "facility_id": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=2b162ab6f3e844e31c646402037e7d88890ce3bb02ac66bba1579282d6ebcf26 -->
```python
"""
Emission Tracking Agent for Energy sector.

Monitors greenhouse gas emissions across facilities, tracks regulatory
compliance, develops reduction plans, and analyzes carbon offset opportunities.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/emission-tracking",
    "version": "1.1.0",
    "display_name": "Emissions Tracking Agent",
    "description": "Analyze a synthetic facility emissions inventory for scope dashboards, threshold screening, reduction scenarios, and carbon-offset due diligence. Use for sustainability and emissions-planning questions. The agent never verifies an emissions claim, declares legal compliance, purchases credits, or files disclosures; qualified reviewers must approve source-backed conclusions through future authenticated tools.",
    "author": "AIBAST",
    "tags": ["emissions", "carbon", "compliance", "ghg", "sustainability", "energy"],
    "category": "energy",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Synthetic domain data
# ---------------------------------------------------------------------------

FACILITIES = {
    "NE-01": {
        "name": "Boston Hub",
        "location": "Boston, MA",
        "region": "Northeast",
        "type": "gas_distribution_hub",
        "quarter_mt_co2e": {"scope_1": 4200, "scope_2": 1900, "scope_3": 600},
        "ch4_mt_co2e": 1180,
        "ch4_prior_year_mt_co2e": 1000,
        "alert_cause": "aging infrastructure",
        "next_quarter_allowance_mt": 4300,
        "projected_next_quarter_scope_1_mt": 4640,
    },
    "NE-02": {
        "name": "Hartford Generating Station",
        "location": "Hartford, CT",
        "region": "Northeast",
        "type": "natural_gas_plant",
        "quarter_mt_co2e": {"scope_1": 5100, "scope_2": 1600, "scope_3": 520},
        "ch4_mt_co2e": 0,
        "ch4_prior_year_mt_co2e": 0,
        "alert_cause": "",
        "next_quarter_allowance_mt": 5500,
        "projected_next_quarter_scope_1_mt": 5100,
    },
    "NE-03": {
        "name": "Providence Peaker Plant",
        "location": "Providence, RI",
        "region": "Northeast",
        "type": "peaker_plant",
        "quarter_mt_co2e": {"scope_1": 3600, "scope_2": 900, "scope_3": 300},
        "ch4_mt_co2e": 0,
        "ch4_prior_year_mt_co2e": 0,
        "alert_cause": "",
        "next_quarter_allowance_mt": 4000,
        "projected_next_quarter_scope_1_mt": 3600,
    },
    "NE-04": {
        "name": "Portland Fuel Terminal",
        "location": "Portland, ME",
        "region": "Northeast",
        "type": "fuel_terminal",
        "quarter_mt_co2e": {"scope_1": 2300, "scope_2": 1100, "scope_3": 410},
        "ch4_mt_co2e": 0,
        "ch4_prior_year_mt_co2e": 0,
        "alert_cause": "",
        "next_quarter_allowance_mt": 2700,
        "projected_next_quarter_scope_1_mt": 2300,
    },
    "NE-05": {
        "name": "Albany Substation Campus",
        "location": "Albany, NY",
        "region": "Northeast",
        "type": "substation_campus",
        "quarter_mt_co2e": {"scope_1": 1900, "scope_2": 2400, "scope_3": 380},
        "ch4_mt_co2e": 0,
        "ch4_prior_year_mt_co2e": 0,
        "alert_cause": "",
        "next_quarter_allowance_mt": 2300,
        "projected_next_quarter_scope_1_mt": 1900,
    },
    "NE-06": {
        "name": "Burlington Operations Center",
        "location": "Burlington, VT",
        "region": "Northeast",
        "type": "operations_center",
        "quarter_mt_co2e": {"scope_1": 800, "scope_2": 600, "scope_3": 200},
        "ch4_mt_co2e": 0,
        "ch4_prior_year_mt_co2e": 0,
        "alert_cause": "",
        "next_quarter_allowance_mt": 1200,
        "projected_next_quarter_scope_1_mt": 800,
    },
    "NE-07": {
        "name": "Manchester Service Center",
        "location": "Manchester, NH",
        "region": "Northeast",
        "type": "service_center",
        "quarter_mt_co2e": {"scope_1": 1150, "scope_2": 1000, "scope_3": 290},
        "ch4_mt_co2e": 0,
        "ch4_prior_year_mt_co2e": 0,
        "alert_cause": "",
        "next_quarter_allowance_mt": 1550,
        "projected_next_quarter_scope_1_mt": 1150,
    },
    "NE-08": {
        "name": "Worcester Compressor Station",
        "location": "Worcester, MA",
        "region": "Northeast",
        "type": "compressor_station",
        "quarter_mt_co2e": {"scope_1": 3400, "scope_2": 700, "scope_3": 330},
        "ch4_mt_co2e": 0,
        "ch4_prior_year_mt_co2e": 0,
        "alert_cause": "",
        "next_quarter_allowance_mt": 3800,
        "projected_next_quarter_scope_1_mt": 3400,
    },
    "NE-09": {
        "name": "Springfield Fleet Depot",
        "location": "Springfield, MA",
        "region": "Northeast",
        "type": "fleet_depot",
        "quarter_mt_co2e": {"scope_1": 1250, "scope_2": 1200, "scope_3": 360},
        "ch4_mt_co2e": 0,
        "ch4_prior_year_mt_co2e": 0,
        "alert_cause": "",
        "next_quarter_allowance_mt": 1650,
        "projected_next_quarter_scope_1_mt": 1250,
    },
    "NE-10": {
        "name": "New Haven Plant",
        "location": "New Haven, CT",
        "region": "Northeast",
        "type": "natural_gas_plant",
        "quarter_mt_co2e": {"scope_1": 2700, "scope_2": 1300, "scope_3": 450},
        "ch4_mt_co2e": 0,
        "ch4_prior_year_mt_co2e": 0,
        "alert_cause": "",
        "next_quarter_allowance_mt": 3100,
        "projected_next_quarter_scope_1_mt": 2700,
    },
    "NE-11": {
        "name": "Syracuse Operations Center",
        "location": "Syracuse, NY",
        "region": "Northeast",
        "type": "operations_center",
        "quarter_mt_co2e": {"scope_1": 950, "scope_2": 1280, "scope_3": 270},
        "ch4_mt_co2e": 0,
        "ch4_prior_year_mt_co2e": 0,
        "alert_cause": "",
        "next_quarter_allowance_mt": 1350,
        "projected_next_quarter_scope_1_mt": 950,
    },
    "NE-12": {
        "name": "Nashua Fleet Yard",
        "location": "Nashua, NH",
        "region": "Northeast",
        "type": "fleet_depot",
        "quarter_mt_co2e": {"scope_1": 800, "scope_2": 700, "scope_3": 400},
        "ch4_mt_co2e": 0,
        "ch4_prior_year_mt_co2e": 0,
        "alert_cause": "",
        "next_quarter_allowance_mt": 1200,
        "projected_next_quarter_scope_1_mt": 800,
    },
}

# Same quarter last year, portfolio totals (MT CO2e) for the YoY change.
PRIOR_YEAR_QUARTER = {"scope_1": 26017, "scope_2": 16701, "scope_3": 4362}

SCOPE_LABELS = {"scope_1": "Scope 1 (Direct)", "scope_2": "Scope 2 (Electricity)", "scope_3": "Scope 3 (Supply Chain)"}

# EPA regional screening threshold for the Northeast portfolio (quarterly MT CO2e).
REGIONAL_SCREENING = {"region": "Northeast", "quarterly_threshold_mt": 51450, "audit_in_days": 14}

CARBON_CREDIT_PRICE_PER_MT = 39.2

# Reduction opportunities, phased into the 18-month roadmap.
REDUCTION_ACTIONS = [
    {"phase": 1, "window": "Next 90 days", "start": "Next month", "action": "Boston Hub LDAR",
     "detail": "Accelerate leak detection and repair at Boston Hub", "facility": "NE-01",
     "cost": 85000, "reduction_mt": 3240, "annual_savings": 102000, "note": "compliance secured"},
    {"phase": 2, "window": "Months 4-9", "start": "Month 4", "action": "CHP + LED",
     "detail": "Combined heat and power at Hartford plus LED retrofits", "facility": "NE-02",
     "cost": 810000, "reduction_mt": 6260, "annual_savings": 607500, "note": "combined"},
    {"phase": 3, "window": "Months 10-15", "start": "Month 10", "action": "Fleet electrification",
     "detail": "Electrify Springfield and Nashua fleet vehicles", "facility": "NE-09",
     "cost": 520000, "reduction_mt": 3230, "annual_savings": 195000, "note": ""},
    {"phase": 4, "window": "Month 16+", "start": "Month 16", "action": "Renewable PPA",
     "detail": "50 MW solar power purchase agreement", "facility": "",
     "cost": 0, "reduction_mt": 0, "annual_savings": 0, "note": "Revenue neutral | 50MW solar"},
]

ROADMAP_BENCHMARK = "top 8% industry performance (synthetic benchmark)"
ROADMAP_MONTHS = 18

CARBON_OFFSETS = {
    "OFF-001": {"project": "Appalachian Reforestation", "type": "forestry", "credits_available": 45000, "price_per_tonne": 18.50, "vintage": 2025, "verified_by": "Verra VCS"},
    "OFF-002": {"project": "Texas Wind REC Bundle", "type": "renewable_energy", "credits_available": 120000, "price_per_tonne": 12.75, "vintage": 2026, "verified_by": "Green-e"},
    "OFF-003": {"project": "Montana Methane Capture", "type": "methane_capture", "credits_available": 28000, "price_per_tonne": 24.00, "vintage": 2025, "verified_by": "ACR"},
    "OFF-004": {"project": "Iowa Agricultural Soil Carbon", "type": "soil_carbon", "credits_available": 35000, "price_per_tonne": 22.00, "vintage": 2026, "verified_by": "Gold Standard"},
}

REGULATIONS = {
    "EPA_GHGRP": {"name": "EPA GHG Reporting Program", "threshold_co2": 25000, "deadline": "2026-03-31"},
    "CA_CAPANDTRADE": {"name": "California Cap-and-Trade", "threshold_co2": 25000, "deadline": "2026-04-01"},
    "EPA_NSPS": {"name": "EPA New Source Performance Standards", "threshold_co2": 0, "deadline": "2026-06-30"},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _selected_facilities(facility_id=None):
    """All facilities, or those whose ID equals / name contains the query (may be empty)."""
    if facility_id:
        query = facility_id.lower().strip()
        if query == "all" or REGIONAL_SCREENING["region"].lower() in query:
            return FACILITIES
        return {
            fid: facility
            for fid, facility in FACILITIES.items()
            if query == fid.lower() or query in facility["name"].lower()
        }
    return FACILITIES


def _not_found(facility_id):
    return (f"No synthetic facility matches `{facility_id}`. Facilities: "
            + ", ".join(f["name"] for f in FACILITIES.values()) + ".")


def _scope_totals(facilities):
    totals = {"scope_1": 0, "scope_2": 0, "scope_3": 0}
    for f in facilities.values():
        for k in totals:
            totals[k] += f["quarter_mt_co2e"][k]
    return totals


def _share(part, whole):
    """Share of total, truncated to one decimal so the shares never add to more than 100%."""
    return int(part * 1000 / whole) / 10


def _yoy(current, prior):
    return round((current - prior) * 100 / prior, 1)


def _facility_alerts(facilities):
    """Facilities whose methane rose year over year or whose projection exceeds next quarter's allowance."""
    alerts = []
    for fid, f in facilities.items():
        over = f["projected_next_quarter_scope_1_mt"] - f["next_quarter_allowance_mt"]
        ch4 = 0
        if f["ch4_prior_year_mt_co2e"]:
            ch4 = int((f["ch4_mt_co2e"] - f["ch4_prior_year_mt_co2e"]) * 100 / f["ch4_prior_year_mt_co2e"] + 0.5)
        if over > 0 or ch4 > 0:
            alerts.append({"id": fid, "name": f["name"], "ch4_yoy_pct": ch4, "over_allowance_mt": over,
                           "cause": f["alert_cause"]})
    return alerts


def _payback_months(action):
    if not action["annual_savings"]:
        return 0
    return int(action["cost"] * 12 / action["annual_savings"] + 0.5)


def _money(amount):
    """85000 -> '$85K'; 1200000 -> '$1.2M'."""
    if amount >= 1000000:
        return f"${amount / 1000000:.1f}M"
    return f"${amount // 1000}K"


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

_OPERATIONS = [
    "emissions_dashboard",
    "compliance_status",
    "reduction_plan",
    "carbon_offset_analysis",
    "implementation_roadmap",
]


class EmissionTrackingAgent(BasicAgent):
    """GHG emission monitoring and compliance tracking agent."""

    def __init__(self):
        self.name = "EmissionTrackingAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                __manifest__["description"]
                + " Always use this tool for the Northeast carbon emissions analysis: 'I need a carbon emissions "
                "analysis for our Northeast facilities' uses emissions_dashboard; 'top reduction opportunities' "
                "uses reduction_plan; 'create the implementation roadmap' uses implementation_roadmap. The 12 "
                "Northeast facilities are the default; call the tool without asking for details."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": list(_OPERATIONS),
                        "description": (
                            "Choose emissions_dashboard for the quarterly emissions analysis (scope totals, share, "
                            "YoY, screening buffer, facility alerts), compliance_status for non-legal threshold "
                            "screening and allowance projections, reduction_plan for the top reduction opportunities "
                            "with cost analysis, carbon_offset_analysis for credit due diligence, or "
                            "implementation_roadmap for the phased 18-month implementation roadmap."
                        ),
                    },
                    "facility_id": {
                        "type": "string",
                        "description": "Optional synthetic facility ID or facility-name substring, such as NE-01 or Boston (omit, or say Northeast, for all 12 facilities). Unknown values return a not-found message.",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation", "emissions_dashboard")
        facility_id = kwargs.get("facility_id")
        facilities = _selected_facilities(facility_id)
        if not facilities:
            return _not_found(facility_id)
        if op == "emissions_dashboard":
            return self._emissions_dashboard(facilities)
        elif op == "compliance_status":
            return self._compliance_status(facilities)
        elif op == "reduction_plan":
            return self._reduction_plan(facilities)
        elif op == "carbon_offset_analysis":
            return self._carbon_offset_analysis(facilities)
        elif op == "implementation_roadmap":
            return self._implementation_roadmap()
        return f"**Error:** Unknown operation `{op}`."

    def _emissions_dashboard(self, facilities) -> str:
        totals = _scope_totals(facilities)
        total = totals["scope_1"] + totals["scope_2"] + totals["scope_3"]
        whole = len(facilities) == len(FACILITIES)
        alerts = _facility_alerts(facilities)
        lines = ["# Emissions Dashboard", ""]
        if whole:
            buffer = round((REGIONAL_SCREENING["quarterly_threshold_mt"] - total) * 100
                           / REGIONAL_SCREENING["quarterly_threshold_mt"])
            focus = f", but {alerts[0]['name']} needs attention" if alerts else ""
            lines += [f"I've analyzed emissions across your {len(facilities)} {REGIONAL_SCREENING['region']} facilities. "
                      f"You're within the screening threshold with an {buffer}% buffer{focus}.", ""]
        lines += [f"**Quarterly Emissions ({total:,} MT CO2e)**", "",
                  "| Scope | Emissions | % Total | YoY Change |",
                  "|-------|-----------|---------|------------|"]
        for k, label in SCOPE_LABELS.items():
            yoy = f"{_yoy(totals[k], PRIOR_YEAR_QUARTER[k]):+}%" if whole else "n/a"
            lines.append(f"| {label} | {totals[k]:,} MT | {_share(totals[k], total)}% | {yoy} |")
        if whole:
            lines += ["", f"**Compliance:** EPA {REGIONAL_SCREENING['region']} regional requirements met "
                          f"({total:,} of {REGIONAL_SCREENING['quarterly_threshold_mt']:,} MT screening threshold; "
                          "screening, not a legal determination)."]
        for a in alerts:
            lines.append(f"\n**Alert:** {a['name']} methane emissions up {a['ch4_yoy_pct']}% due to {a['cause']}. "
                         f"Current trajectory exceeds next-quarter allowances by {a['over_allowance_mt']} MT.")
            for act in REDUCTION_ACTIONS:
                if act["facility"] == a["id"]:
                    avoided = int(act["reduction_mt"] * CARBON_CREDIT_PRICE_PER_MT / 1000 + 0.5) * 1000
                    lines.append(f"**Action:** {act['detail']} - {_money(act['cost'])} cost avoids "
                                 f"{_money(avoided)} in carbon credits.")
        lines += ["", "| Facility | Location | Scope 1 | Scope 2 | Scope 3 | Total |",
                  "|----------|----------|---------|---------|---------|-------|"]
        for f in facilities.values():
            e = f["quarter_mt_co2e"]
            lines.append(f"| {f['name']} | {f['location']} | {e['scope_1']:,} | {e['scope_2']:,} | {e['scope_3']:,} "
                         f"| {e['scope_1'] + e['scope_2'] + e['scope_3']:,} |")
        lines += ["", "Source: [Azure IoT Hub + MS Cloud for Sustainability] (synthetic)", "",
                  "> Synthetic inventory, not verified emissions evidence. Validate boundaries, factors, units, and source records before making a claim.",
                  "", "Next: want to see the top reduction opportunities?"]
        return "\n".join(lines)

    def _compliance_status(self, facilities) -> str:
        totals = _scope_totals(facilities)
        total = totals["scope_1"] + totals["scope_2"] + totals["scope_3"]
        lines = ["# Compliance Status", ""]
        if len(facilities) == len(FACILITIES):
            threshold = REGIONAL_SCREENING["quarterly_threshold_mt"]
            buffer = round((threshold - total) * 100 / threshold)
            state = "BELOW SCREENING THRESHOLD" if total <= threshold else "ABOVE SCREENING THRESHOLD"
            lines += [f"**{REGIONAL_SCREENING['region']} portfolio:** {total:,} of {threshold:,} MT CO2e - {state} "
                      f"({buffer}% buffer). EPA audit in {REGIONAL_SCREENING['audit_in_days']} days.", ""]
        lines += ["| Facility | Scope 1 (quarter) | Next-Quarter Projection | Allowance | Status |",
                  "|----------|-------------------|-------------------------|-----------|--------|"]
        for f in facilities.values():
            over = f["projected_next_quarter_scope_1_mt"] - f["next_quarter_allowance_mt"]
            status = f"AT RISK (+{over} MT)" if over > 0 else "BELOW SCREENING THRESHOLD"
            lines.append(f"| {f['name']} | {f['quarter_mt_co2e']['scope_1']:,} | "
                         f"{f['projected_next_quarter_scope_1_mt']:,} | {f['next_quarter_allowance_mt']:,} | {status} |")
        lines += ["", "> Screening result only; it is not a legal compliance determination or an emissions claim."]
        return "\n".join(lines)

    def _reduction_plan(self, facilities) -> str:
        total = 0
        for k, v in _scope_totals(FACILITIES).items():
            total += v
        lines = ["# Emission Reduction Plans", "",
                 "Top reduction opportunities for the Northeast portfolio, ranked by payback:", "",
                 "| Opportunity | Cost | Reduction (MT) | Annual Savings | Payback | Carbon Credits Avoided |",
                 "|-------------|------|----------------|----------------|---------|------------------------|"]
        cut = 0
        for a in REDUCTION_ACTIONS:
            if a["cost"] == 0:
                lines.append(f"| {a['action']} ({a['detail']}) | Revenue neutral | - | - | - | - |")
                continue
            cut += a["reduction_mt"]
            avoided = int(a["reduction_mt"] * CARBON_CREDIT_PRICE_PER_MT / 1000 + 0.5) * 1000
            lines.append(f"| {a['action']} ({a['detail']}) | {_money(a['cost'])} | {a['reduction_mt']:,} | "
                         f"{_money(a['annual_savings'])} | {_payback_months(a)} months | {_money(avoided)} |")
        lines += ["", f"**Combined reduction:** {cut:,} MT of {total:,} MT per quarter "
                      f"({int(cut * 100 / total + 0.5)}%), at a carbon credit price of ${CARBON_CREDIT_PRICE_PER_MT}/MT.",
                  "", "> Scenario estimates require engineering, finance, environmental, and executive review before action.",
                  "", "Next: want me to create the implementation roadmap?"]
        return "\n".join(lines)

    def _carbon_offset_analysis(self, facilities) -> str:
        gap = 0
        for f in facilities.values():
            over = f["projected_next_quarter_scope_1_mt"] - f["next_quarter_allowance_mt"]
            if over > 0:
                gap += over
        lines = ["# Carbon Offset Analysis", "",
                 f"**Emission Gap to Cover:** {gap:,} MT (projected next-quarter overage)", "",
                 "| Project | Type | Credits Available | Price/t | Cost to Cover Gap | Verified By |",
                 "|---------|------|-------------------|---------|-------------------|-------------|"]
        for o in CARBON_OFFSETS.values():
            cover = min(gap, o["credits_available"])
            lines.append(f"| {o['project']} | {o['type']} | {o['credits_available']:,} | ${o['price_per_tonne']:.2f} "
                         f"| ${int(cover * o['price_per_tonne'] + 0.5):,} | {o['verified_by']} |")
        lines += ["", "Reducing at the source (Boston Hub LDAR) closes the gap without buying credits.", "",
                  "> Due-diligence shortlist only. No credit purchase, retirement, disclosure, or offset claim has been made."]
        return "\n".join(lines)

    def _implementation_roadmap(self) -> str:
        total = 0
        for v in _scope_totals(FACILITIES).values():
            total += v
        cut = 0
        lines = ["# Implementation Roadmap", ""]
        for a in REDUCTION_ACTIONS:
            cut += a["reduction_mt"]
        lines += [f"I've created an {ROADMAP_MONTHS}-month phased roadmap sequenced for quick wins and risk mitigation.", "",
                  "## Implementation Timeline", ""]
        for a in REDUCTION_ACTIONS:
            lines.append(f"**Phase {a['phase']} ({a['window']}) - {a['action']}**")
            if a["cost"] == 0:
                lines.append(f"- {a['note']}")
            else:
                lines.append(f"- Start: {a['start']} | Cost: {_money(a['cost'])}" + (f" {a['note']}" if a["note"] == "combined" else ""))
                impact = f"- Impact: {a['reduction_mt']:,} MT reduction"
                if a["note"] and a["note"] != "combined":
                    impact += f", {a['note']}"
                lines.append(impact)
                lines.append(f"- Payback: {_payback_months(a)} months")
            lines.append("")
        lines += [f"**Projected Outcome:** {int(cut * 100 / total + 0.5)}% emissions reduction "
                  f"({cut:,} of {total:,} MT per quarter), {ROADMAP_BENCHMARK}.", "",
                  "Source: [Project Planning + Financial Modeling] (synthetic)", "",
                  "> Draft roadmap. Scenario estimates require engineering, finance, environmental, and executive review before action; nothing is purchased or committed.",
                  "", "Next: want to prepare your EPA audit package?"]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = EmissionTrackingAgent()
    for op in ["emissions_dashboard", "implementation_roadmap", "reduction_plan", "compliance_status",
               "carbon_offset_analysis"]:
        print(f"\n{'='*60}")
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
