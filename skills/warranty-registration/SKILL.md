---
name: "warranty-registration"
description: "Dealer warranty desk for the fictional Fabrikam Tool Supply branch and its Northwind Equipment units. Always use this tool for warranty coverage, repair coverage questions, unit warranty records, serial checks, product registrations and extended-coverage offers. Routing: how coverage looks overall -> coverage_overview; 'is this repair covered' or 'can we claim' for a serial -> claim_precheck; 'full record' or claim history for a serial -> unit_record; 'check the serial' before registering a sold unit -> validate_serial; 'prepare/draft the registration' -> registration_draft (never submitted); 'who should we offer extended coverage to' -> extension_offers. Serial numbers look like WS-25-4471. Every operation has a demo default, so call it right away. Never files a claim, submits a registration, sells an extension or contacts a customer."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "warranty_registration_agent.py"
  tool-name: "WarrantyRegistrationAgent"
  agent-sha256: "9b198a7bfdd59b5c94c2504fc984d79100b57de2393dce80d4ae69dd90c4a71e"
  version: "1.0.0"
  author: "AIBAST"
  tags: "manufacturing, warranty, product-registration, dealer-service, aftermarket"
---

# Warranty Registration

Dealer warranty desk for the fictional Fabrikam Tool Supply branch and its Northwind Equipment units. Always use this tool for warranty coverage, repair coverage questions, unit warranty records, serial checks, product registrations and extended-coverage offers. Routing: how coverage looks overall -> coverage_overview; 'is this repair covered' or 'can we claim' for a serial -> claim_precheck; 'full record' or claim history for a serial -> unit_record; 'check the serial' before registering a sold unit -> validate_serial; 'prepare/draft the registration' -> registration_draft (never submitted); 'who should we offer extended coverage to' -> extension_offers. Serial numbers look like WS-25-4471. Every operation has a demo default, so call it right away. Never files a claim, submits a registration, sells an extension or contacts a customer.

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "coverage_overview",
        "claim_precheck",
        "unit_record",
        "validate_serial",
        "registration_draft",
        "extension_offers"
      ],
      "description": "coverage_overview for the dealer-wide picture; claim_precheck for whether a repair is covered; unit_record for one unit's full record; validate_serial before registering; registration_draft to prepare a registration; extension_offers for extended-coverage candidates."
    },
    "serial_number": {
      "type": "string",
      "enum": [
        "HP-40-1182",
        "WS-25-4471",
        "BG-08-2290",
        "PW-30-0615",
        "TC-90-3307",
        "CR-12-0950",
        "WS-25-4520",
        "HP-40-1207"
      ],
      "description": "Unit serial, e.g. 'WS-25-4471' (claim_precheck, unit_record, validate_serial, registration_draft)"
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
   python3 scripts/run.py --json '{"operation": "<string>", "serial_number": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=9b198a7bfdd59b5c94c2504fc984d79100b57de2393dce80d4ae69dd90c4a71e -->
```python
"""
Warranty and Registration Agent

Dealer-facing assistant for equipment warranty coverage, claim pre-checks,
serial validation, registration drafts and extended-coverage offers.

Where a real deployment would call an ERP warranty module, a product catalog
and a dealer registration service, this agent uses a fixed synthetic snapshot
so it runs anywhere without credentials. It never files a claim, submits a
registration, sells an extension or contacts a customer: it returns drafts and
pre-checks for an authorized person to act on.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))

from basic_agent import BasicAgent

# ═══════════════════════════════════════════════════════════════
# RAPP AGENT MANIFEST
# ═══════════════════════════════════════════════════════════════
__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/warranty-registration",
    "version": "1.0.0",
    "display_name": "Warranty and Registration Agent",
    "description": "Give equipment dealers one place to check warranty coverage, pre-check claims, validate serials and prepare product registrations, so covered repairs move faster and no unit misses its registration window.",
    "author": "AIBAST",
    "tags": ["manufacturing", "warranty", "product-registration", "dealer-service", "aftermarket"],
    "category": "manufacturing",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ═══════════════════════════════════════════════════════════════
# SYNTHETIC DATA LAYER (fixed snapshot, as of 2026-03-02)
# ═══════════════════════════════════════════════════════════════

_AS_OF = "2026-03-02"
_AS_OF_ORDINAL = 739677          # date(2026, 3, 2).toordinal(), fixed so no clock is read

_DEALER = {
    "name": "Fabrikam Tool Supply (Riverside branch)",
    "account": "DLR-4100",
    "manufacturer": "Northwind Equipment",
    "service_manager": "Priya Raman",
    "warranty_desk": "Northwind warranty desk",
}

_COVERAGE = {
    "full": {"label": "Full parts and labor", "parts": "Yes", "labor": "Yes", "on_site": "Yes"},
    "parts_only": {"label": "Parts only", "parts": "Yes", "labor": "No", "on_site": "No"},
    "limited": {"label": "Limited (wear items excluded)", "parts": "Yes", "labor": "No", "on_site": "No"},
}

# Registered units. Day counts are precomputed against the snapshot date.
_UNITS = {
    "HP-40-1182": {
        "product": "Hydraulic Press HP-40", "family": "Shop presses",
        "purchased": "2024-04-10", "registered": "2024-04-12", "warranty_end": "2027-04-10",
        "end_ordinal": 740081, "coverage": "full", "extension_price": 420.00,
        "claims": [],
    },
    "WS-25-4471": {
        "product": "Welding Station WS-250", "family": "Welding",
        "purchased": "2025-01-22", "registered": "2025-01-24", "warranty_end": "2027-01-22",
        "end_ordinal": 740003, "coverage": "full", "extension_price": 260.00,
        "claims": [
            {"claim": "CLM-25-0318", "date": "2025-08-14", "issue": "Torch cable replaced", "status": "Resolved"},
        ],
    },
    "BG-08-2290": {
        "product": "Bench Grinder BG-8", "family": "Grinding",
        "purchased": "2024-03-28", "registered": "2024-04-02", "warranty_end": "2026-03-28",
        "end_ordinal": 739703, "coverage": "parts_only", "extension_price": 85.00,
        "claims": [],
    },
    "PW-30-0615": {
        "product": "Parts Washer PW-30", "family": "Cleaning",
        "purchased": "2024-05-05", "registered": "2024-05-07", "warranty_end": "2026-05-05",
        "end_ordinal": 739741, "coverage": "full", "extension_price": 140.00,
        "claims": [],
    },
    "TC-90-3307": {
        "product": "Tire Changer TC-900", "family": "Tire service",
        "purchased": "2023-02-14", "registered": "2023-02-15", "warranty_end": "2026-02-14",
        "end_ordinal": 739661, "coverage": "full", "extension_price": 0.00,
        "claims": [
            {"claim": "CLM-24-0127", "date": "2024-06-03", "issue": "Bead breaker cylinder resealed", "status": "Resolved"},
            {"claim": "CLM-25-0044", "date": "2025-02-11", "issue": "Turntable motor replaced", "status": "Resolved"},
        ],
    },
    "CR-12-0950": {
        "product": "Coolant Recovery Unit CR-12", "family": "Fluid service",
        "purchased": "2025-06-30", "registered": "2025-07-01", "warranty_end": "2027-06-30",
        "end_ordinal": 740162, "coverage": "limited", "extension_price": 110.00,
        "claims": [],
    },
}

# Units sold but not yet registered (shipment snapshot). Registration window: 30 days from sale.
_PENDING = {
    "WS-25-4520": {
        "product": "Welding Station WS-250", "sold": "2026-02-20", "registration_due": "2026-03-22",
        "due_ordinal": 739697, "term_months": 24, "warranty_end": "2028-02-20", "coverage": "full",
        "buyer": "Contoso Fleet Services (shop account C-2207)",
    },
    "HP-40-1207": {
        "product": "Hydraulic Press HP-40", "sold": "2026-02-26", "registration_due": "2026-03-28",
        "due_ordinal": 739703, "term_months": 36, "warranty_end": "2029-02-26", "coverage": "full",
        "buyer": "Adatum Auto Body (shop account C-2241)",
    },
}

_SERIALS = list(_UNITS) + list(_PENDING)
_EXTENSION_WINDOW_DAYS = 90
_EXTENSION_DISCOUNT = 0.15

_GATE = (
    "Synthetic dealer snapshot only. This agent does not file a claim, submit a "
    "registration, sell an extension, contact a customer or change a warranty record; "
    "it prepares drafts and pre-checks for an authorized person to act on."
)
_SOURCE = "Source: [Synthetic Warranty + Registration Snapshot, as of 2026-03-02]\nAgents: WarrantyRegistrationAgent"


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _days_left(unit):
    return unit["end_ordinal"] - _AS_OF_ORDINAL


def _status(unit):
    d = _days_left(unit)
    if d < 0:
        return "Expired"
    if d <= _EXTENSION_WINDOW_DAYS:
        return "Expiring soon"
    return "Active"


def _money(x):
    return f"${x:,.2f}"


def _resolve_serial(serial, default):
    """Exact serial (case-insensitive) or a serial contained in the text; None when nothing matches."""
    if not serial:
        return default
    q = str(serial).strip().upper()
    for s in _SERIALS:
        if s == q or s in q:
            return s
    return None


def _miss(serial):
    return (
        f"No unit with serial '{serial}' is in the synthetic snapshot. "
        f"Known serials: {', '.join(_SERIALS)}.\n\n{_GATE}\n\n{_SOURCE}"
    )


# ═══════════════════════════════════════════════════════════════
# AGENT CLASS
# ═══════════════════════════════════════════════════════════════

_OPERATIONS = [
    "coverage_overview", "claim_precheck", "unit_record",
    "validate_serial", "registration_draft", "extension_offers",
]


class WarrantyRegistrationAgent(BasicAgent):
    """
    Dealer warranty and registration assistant.

    Operations:
        coverage_overview  - dealer-wide coverage: active, expiring, expired, awaiting registration
        claim_precheck     - is a repair on this unit covered? (pre-check, never files a claim)
        unit_record        - full warranty record and claim history for one serial
        validate_serial    - catalog, format and duplicate check before registering
        registration_draft - Not Submitted registration draft for a sold unit
        extension_offers   - extended-coverage offers for units expiring within 90 days
    """

    def __init__(self):
        self.name = "WarrantyRegistrationAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                "Dealer warranty desk for the fictional Fabrikam Tool Supply branch and its "
                "Northwind Equipment units. Always use this tool for warranty coverage, repair "
                "coverage questions, unit warranty records, serial checks, product registrations "
                "and extended-coverage offers. Routing: how coverage looks overall -> "
                "coverage_overview; 'is this repair covered' or 'can we claim' for a serial -> "
                "claim_precheck; 'full record' or claim history for a serial -> unit_record; "
                "'check the serial' before registering a sold unit -> validate_serial; "
                "'prepare/draft the registration' -> registration_draft (never submitted); "
                "'who should we offer extended coverage to' -> extension_offers. Serial numbers "
                "look like WS-25-4471. Every operation has a demo default, so call it right away. "
                "Never files a claim, submits a registration, sells an extension or contacts a "
                "customer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": list(_OPERATIONS),
                        "description": (
                            "coverage_overview for the dealer-wide picture; claim_precheck for "
                            "whether a repair is covered; unit_record for one unit's full record; "
                            "validate_serial before registering; registration_draft to prepare a "
                            "registration; extension_offers for extended-coverage candidates."
                        ),
                    },
                    "serial_number": {
                        "type": "string",
                        "enum": list(_SERIALS),
                        "description": "Unit serial, e.g. 'WS-25-4471' (claim_precheck, unit_record, validate_serial, registration_draft)",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation") or "coverage_overview"
        serial = kwargs.get("serial_number") or ""
        if op == "coverage_overview":
            return self._coverage_overview()
        if op == "extension_offers":
            return self._extension_offers()
        defaults = {
            "claim_precheck": "WS-25-4471", "unit_record": "TC-90-3307",
            "validate_serial": "WS-25-4520", "registration_draft": "WS-25-4520",
        }
        if op not in defaults:
            return f"Unknown operation: {op}. Available: {', '.join(_OPERATIONS)}."
        key = _resolve_serial(serial, defaults[op])
        if key is None:
            return _miss(serial)
        if op == "claim_precheck":
            return self._claim_precheck(key)
        if op == "unit_record":
            return self._unit_record(key)
        if op == "validate_serial":
            return self._validate_serial(key)
        return self._registration_draft(key)

    # ── coverage_overview ─────────────────────────────────────
    def _coverage_overview(self):
        rows, active, expiring, expired = [], 0, 0, 0
        for serial, u in _UNITS.items():
            st = _status(u)
            if st == "Active":
                active += 1
            elif st == "Expiring soon":
                expiring += 1
            else:
                expired += 1
            d = _days_left(u)
            left = f"{d} days" if d >= 0 else f"ended {-d} days ago"
            rows.append(f"| {serial} | {u['product']} | {_COVERAGE[u['coverage']]['label']} | {u['warranty_end']} | {left} | {st} |")
        pending = "\n".join(
            f"| {s} | {p['product']} | sold {p['sold']} | due {p['registration_due']} ({p['due_ordinal'] - _AS_OF_ORDINAL} days) |"
            for s, p in _PENDING.items()
        )
        return (
            f"**Warranty Coverage Overview: {_DEALER['name']}**\n\n"
            f"Dealer account {_DEALER['account']} | Manufacturer {_DEALER['manufacturer']} | As of {_AS_OF}\n\n"
            f"| Measure | Count |\n|---|---|\n"
            f"| Registered units | {len(_UNITS)} |\n"
            f"| Active | {active} |\n"
            f"| Expiring within {_EXTENSION_WINDOW_DAYS} days | {expiring} |\n"
            f"| Expired | {expired} |\n"
            f"| Sold, awaiting registration | {len(_PENDING)} |\n\n"
            f"| Serial | Product | Coverage | Ends | Remaining | Status |\n|---|---|---|---|---|---|\n"
            + "\n".join(rows) + "\n\n"
            f"**Awaiting registration (30-day window):**\n\n"
            f"| Serial | Product | Sale | Registration |\n|---|---|---|---|\n{pending}\n\n"
            f"**Next step:** register the 2 sold units before their windows close and review "
            f"extended-coverage offers for the {expiring} expiring units.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── claim_precheck ────────────────────────────────────────
    def _claim_precheck(self, serial):
        if serial in _PENDING:
            p = _PENDING[serial]
            return (
                f"**Claim Pre-Check: {serial} ({p['product']})**\n\n"
                f"Result: **Not ready for claim review** - this unit is not registered yet "
                f"(registration due {p['registration_due']}). Register it first; coverage starts from the "
                f"sale date {p['sold']} once registration is confirmed.\n\n{_GATE}\n\n{_SOURCE}"
            )
        u = _UNITS[serial]
        cov = _COVERAGE[u["coverage"]]
        d = _days_left(u)
        active = d >= 0
        if not active:
            result = "Not eligible - warranty ended"
            path = (f"Coverage ended {u['warranty_end']} ({-d} days ago). Offer the customer a paid "
                    f"repair quote; an exception request goes to the {_DEALER['warranty_desk']}.")
        elif cov["labor"] == "No":
            result = "Eligible for parts only"
            path = "Parts are covered; labor is billable to the customer. Quote labor before the repair."
        else:
            result = "Eligible for claim review"
            path = (f"Parts and labor are covered. Prepare the claim with the failure description, "
                    f"photos and hours for the {_DEALER['warranty_desk']} to approve.")
        claims = len(u["claims"])
        return (
            f"**Claim Pre-Check: {serial} ({u['product']})**\n\n"
            f"| Check | Result |\n|---|---|\n"
            f"| Registration | Confirmed {u['registered']} |\n"
            f"| Warranty active | {'Yes' if active else 'No'} (ends {u['warranty_end']}) |\n"
            f"| Days remaining | {d if active else 0} |\n"
            f"| Coverage | {cov['label']} |\n"
            f"| Parts covered | {cov['parts'] if active else 'No'} |\n"
            f"| Labor covered | {cov['labor'] if active else 'No'} |\n"
            f"| Prior claims | {claims} |\n\n"
            f"**Pre-check result: {result}**\n\n"
            f"**Next step:** {path}\n\n"
            f"No claim was filed. The {_DEALER['warranty_desk']} makes the coverage decision.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── unit_record ───────────────────────────────────────────
    def _unit_record(self, serial):
        if serial in _PENDING:
            p = _PENDING[serial]
            return (
                f"**Warranty Record: {serial} ({p['product']})**\n\n"
                f"No warranty record yet - sold {p['sold']} to {p['buyer']}, registration due "
                f"{p['registration_due']}.\n\n{_GATE}\n\n{_SOURCE}"
            )
        u = _UNITS[serial]
        cov = _COVERAGE[u["coverage"]]
        d = _days_left(u)
        claims = "\n".join(
            f"| {c['claim']} | {c['date']} | {c['issue']} | {c['status']} |" for c in u["claims"]
        ) or "| - | - | No claims on record | - |"
        if d < 0:
            nxt = (f"Warranty ended {-d} days ago. Repairs are customer-paid; quote the repair and, if "
                   f"the customer asks, route an exception request to the {_DEALER['warranty_desk']}.")
        elif d <= _EXTENSION_WINDOW_DAYS:
            nxt = f"Coverage ends in {d} days; this unit qualifies for an extended-coverage offer."
        else:
            nxt = "Coverage is active; no action needed."
        status = f"{_status(u)} ({d} days remaining)" if d >= 0 else f"Expired (ended {-d} days ago)"
        return (
            f"**Warranty Record: {serial} ({u['product']})**\n\n"
            f"| Field | Value |\n|---|---|\n"
            f"| Product family | {u['family']} |\n"
            f"| Purchased | {u['purchased']} |\n"
            f"| Registered | {u['registered']} |\n"
            f"| Warranty ends | {u['warranty_end']} |\n"
            f"| Status | {status} |\n"
            f"| Coverage | {cov['label']} |\n"
            f"| Parts / Labor / On-site | {cov['parts']} / {cov['labor']} / {cov['on_site']} |\n\n"
            f"**Claim history ({len(u['claims'])}):**\n\n"
            f"| Claim | Date | Issue | Status |\n|---|---|---|---|\n{claims}\n\n"
            f"**Next step:** {nxt}\n\n{_GATE}\n\n{_SOURCE}"
        )

    # ── validate_serial ───────────────────────────────────────
    def _validate_serial(self, serial):
        if serial in _UNITS:
            u = _UNITS[serial]
            return (
                f"**Serial Check: {serial}**\n\n"
                f"| Check | Result |\n|---|---|\n"
                f"| Format | Valid |\n"
                f"| In catalog | Yes - {u['product']} |\n"
                f"| Already registered | Yes - registered {u['registered']} |\n\n"
                f"**Result: Duplicate - do not register again.** This serial already has a warranty "
                f"record ending {u['warranty_end']}.\n\n{_GATE}\n\n{_SOURCE}"
            )
        p = _PENDING[serial]
        days = p["due_ordinal"] - _AS_OF_ORDINAL
        return (
            f"**Serial Check: {serial}**\n\n"
            f"| Check | Result |\n|---|---|\n"
            f"| Format | Valid |\n"
            f"| In catalog | Yes - {p['product']} |\n"
            f"| Already registered | No |\n"
            f"| Sold | {p['sold']} to {p['buyer']} |\n"
            f"| Registration window | Due {p['registration_due']} ({days} days left) |\n\n"
            f"**Result: Ready to register.** Ask me to prepare the registration draft.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── registration_draft ────────────────────────────────────
    def _registration_draft(self, serial):
        if serial in _UNITS:
            u = _UNITS[serial]
            return (
                f"**Registration Draft: {serial}**\n\n"
                f"No draft prepared - {u['product']} {serial} is already registered "
                f"({u['registered']}). Registering it again would create a duplicate.\n\n{_GATE}\n\n{_SOURCE}"
            )
        p = _PENDING[serial]
        cov = _COVERAGE[p["coverage"]]
        days = p["due_ordinal"] - _AS_OF_ORDINAL
        return (
            f"**Product Registration Draft - Not Submitted**\n\n"
            f"| Field | Value |\n|---|---|\n"
            f"| Draft ID | REG-DRAFT-{serial} |\n"
            f"| Serial | {serial} |\n"
            f"| Product | {p['product']} |\n"
            f"| Dealer | {_DEALER['name']} ({_DEALER['account']}) |\n"
            f"| End customer | {p['buyer']} |\n"
            f"| Sale date (warranty start) | {p['sold']} |\n"
            f"| Warranty term | {p['term_months']} months |\n"
            f"| Warranty would end | {p['warranty_end']} |\n"
            f"| Coverage | {cov['label']} |\n"
            f"| Registration due | {p['registration_due']} ({days} days left) |\n"
            f"| Status | Draft for dealer review |\n\n"
            f"**Before submitting:** confirm the sale date on the invoice and the end customer's "
            f"contact with {_DEALER['service_manager']}, then submit it in the manufacturer's "
            f"registration portal. Nothing was submitted and no warranty was activated.\n\n"
            f"{_GATE}\n\n{_SOURCE}"
        )

    # ── extension_offers ──────────────────────────────────────
    def _extension_offers(self):
        rows, total, count = [], 0.0, 0
        for serial, u in _UNITS.items():
            d = _days_left(u)
            if 0 <= d <= _EXTENSION_WINDOW_DAYS:
                net = round(u["extension_price"] * (1 - _EXTENSION_DISCOUNT), 2)
                total += net
                count += 1
                rows.append(
                    f"| {serial} | {u['product']} | {u['warranty_end']} | {d} days | "
                    f"{_money(u['extension_price'])} | {_money(net)} |"
                )
        lapsed = [s for s, u in _UNITS.items() if _days_left(u) < 0]
        return (
            f"**Extended-Coverage Offers: {count} units ending within {_EXTENSION_WINDOW_DAYS} days**\n\n"
            f"| Serial | Product | Coverage ends | Remaining | List price | Offer (15% off list) |\n"
            f"|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n\n"
            f"**Offer total:** {_money(total)} across {count} units.\n"
            f"**Not offered:** {', '.join(lapsed)} - coverage already ended; extensions must start "
            f"before the warranty ends.\n\n"
            f"**Next step:** review the offer drafts and send them to the customers yourself. "
            f"No offer was sent and nothing was sold.\n\n{_GATE}\n\n{_SOURCE}"
        )


if __name__ == "__main__":
    agent = WarrantyRegistrationAgent()
    story = [
        {"operation": "coverage_overview"},
        {"operation": "claim_precheck", "serial_number": "WS-25-4471"},
        {"operation": "unit_record", "serial_number": "TC-90-3307"},
        {"operation": "validate_serial", "serial_number": "WS-25-4520"},
        {"operation": "registration_draft", "serial_number": "WS-25-4520"},
        {"operation": "extension_offers"},
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
