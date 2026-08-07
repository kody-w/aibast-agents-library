"""
Utility Billing Assistance Agent — SLG Government Stack

Provides utility billing support including account inquiries, usage
analysis, suspected-leak flagging from interval-meter evidence, payment
plan management, and assistance program eligibility for municipal utility
departments.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent

__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/utility-billing-assistance",
    "version": "1.0.0",
    "display_name": "Utility Billing Assistance Agent",
    "description": "Municipal utility billing support with account inquiries, usage analysis, suspected-leak flagging, payment plans, and assistance program eligibility.",
    "author": "AIBAST",
    "tags": ["utility", "billing", "water", "leak", "payment", "assistance", "municipal"],
    "category": "slg_government",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}

# ---------------------------------------------------------------------------
# Synthetic domain data
# ---------------------------------------------------------------------------

UTILITY_ACCOUNTS = {
    "ACCT-90001": {
        "customer": "Patricia Hernandez",
        "address": "1245 Cedar Lane",
        "account_type": "residential",
        "services": ["water", "sewer", "stormwater"],
        "status": "active",
        "balance_current": 127.45,
        "balance_past_due": 0.00,
        "autopay": True,
        "last_payment": {"date": "2025-02-15", "amount": 118.90},
    },
    "ACCT-90002": {
        "customer": "Green Valley Shopping Center",
        "address": "5600 Commerce Blvd",
        "account_type": "commercial",
        "services": ["water", "sewer", "stormwater", "fire_line"],
        "status": "active",
        "balance_current": 2845.60,
        "balance_past_due": 1420.30,
        "autopay": False,
        "last_payment": {"date": "2025-01-20", "amount": 2650.00},
    },
    "ACCT-90003": {
        "customer": "Robert & Linda Thompson",
        "address": "887 Willow Creek Dr",
        "account_type": "residential",
        "services": ["water", "sewer", "stormwater", "trash"],
        "status": "delinquent",
        "balance_current": 245.80,
        "balance_past_due": 489.20,
        "autopay": False,
        "last_payment": {"date": "2024-11-18", "amount": 135.00},
    },
    "ACCT-90004": {
        "customer": "Sunnyvale Elementary School",
        "address": "300 Education Way",
        "account_type": "institutional",
        "services": ["water", "sewer", "stormwater", "irrigation"],
        "status": "active",
        "balance_current": 1890.25,
        "balance_past_due": 0.00,
        "autopay": True,
        "last_payment": {"date": "2025-02-28", "amount": 1756.00},
    },
}

USAGE_HISTORY = {
    "ACCT-90001": [
        {"period": "2024-09", "water_gallons": 4200, "sewer_gallons": 3780, "amount": 98.50},
        {"period": "2024-10", "water_gallons": 3800, "sewer_gallons": 3420, "amount": 92.10},
        {"period": "2024-11", "water_gallons": 3100, "sewer_gallons": 2790, "amount": 84.30},
        {"period": "2024-12", "water_gallons": 2900, "sewer_gallons": 2610, "amount": 81.20},
        {"period": "2025-01", "water_gallons": 3000, "sewer_gallons": 2700, "amount": 82.90},
        {"period": "2025-02", "water_gallons": 3200, "sewer_gallons": 2880, "amount": 86.45},
    ],
    "ACCT-90003": [
        {"period": "2024-09", "water_gallons": 8500, "sewer_gallons": 7650, "amount": 145.20},
        {"period": "2024-10", "water_gallons": 9200, "sewer_gallons": 8280, "amount": 152.80},
        {"period": "2024-11", "water_gallons": 12400, "sewer_gallons": 11160, "amount": 198.50},
        {"period": "2024-12", "water_gallons": 14800, "sewer_gallons": 13320, "amount": 232.10},
        {"period": "2025-01", "water_gallons": 13200, "sewer_gallons": 11880, "amount": 215.40},
        {"period": "2025-02", "water_gallons": 11500, "sewer_gallons": 10350, "amount": 189.80},
    ],
}

# Interval-meter diagnostics. Only accounts with metered history carry interval
# telemetry; the other accounts are reported as not assessed rather than guessed.
METER_DIAGNOSTICS = {
    "ACCT-90001": {
        "interval_meter": True,
        "window_nights": 30,
        "min_nightly_flow_gph": 0.0,
        "continuous_flow_nights": 0,
        "last_read": "2025-02-28",
    },
    "ACCT-90003": {
        "interval_meter": True,
        "window_nights": 30,
        "min_nightly_flow_gph": 5.0,
        "continuous_flow_nights": 30,
        "last_read": "2025-02-28",
    },
}

# Published leak-flag rule. A flag is a suspected leak pending field verification,
# never a confirmed leak and never a billing adjustment.
LEAK_THRESHOLDS = {
    "min_nightly_flow_gph": 0.5,
    "window_nights": 30,
    "trend_flag": "significantly_increasing",
}

RATE_STRUCTURES = {
    "water_residential": {
        "base_charge": 18.50,
        "tiers": [
            {"range": "0-3,000 gal", "rate_per_1000": 4.25},
            {"range": "3,001-6,000 gal", "rate_per_1000": 6.50},
            {"range": "6,001-10,000 gal", "rate_per_1000": 9.75},
            {"range": "Over 10,000 gal", "rate_per_1000": 14.00},
        ],
    },
    "water_commercial": {
        "base_charge": 45.00,
        "tiers": [
            {"range": "0-10,000 gal", "rate_per_1000": 5.80},
            {"range": "10,001-50,000 gal", "rate_per_1000": 5.25},
            {"range": "Over 50,000 gal", "rate_per_1000": 4.90},
        ],
    },
    "sewer": {"base_charge": 12.75, "rate_per_1000": 5.10},
    "stormwater": {"residential": 8.50, "commercial_per_eru": 8.50},
    "trash": {"residential": 22.00},
}

ASSISTANCE_PROGRAMS = {
    "LIHWAP": {
        "name": "Low-Income Household Water Assistance Program",
        "income_limit_pct_fpl": 150,
        "max_benefit": 1500,
        "eligibility": "Household income at or below 150% FPL",
        "documents_required": ["Proof of income", "Utility bill", "ID", "Household size verification"],
        "status": "accepting_applications",
    },
    "senior_discount": {
        "name": "Senior Citizen Rate Discount",
        "income_limit_pct_fpl": 200,
        "max_benefit": 0,
        "eligibility": "Age 65+ and income at or below 200% FPL",
        "documents_required": ["Proof of age", "Proof of income", "Utility account number"],
        "status": "accepting_applications",
        "discount_pct": 25,
    },
    "arrearage_forgiveness": {
        "name": "COVID-19 Arrearage Forgiveness Program",
        "income_limit_pct_fpl": 200,
        "max_benefit": 3000,
        "eligibility": "Past-due balance accrued during March 2020 - December 2023",
        "documents_required": ["Utility account statement", "Income verification"],
        "status": "limited_funds",
    },
    "payment_plan": {
        "name": "Extended Payment Arrangement",
        "income_limit_pct_fpl": 0,
        "max_benefit": 0,
        "eligibility": "Any customer with past-due balance over $100",
        "documents_required": ["Signed payment agreement"],
        "status": "always_available",
        "max_installments": 12,
    },
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _calculate_water_bill(gallons, account_type):
    """Calculate water charges based on tiered rate structure."""
    if account_type == "commercial":
        rate_info = RATE_STRUCTURES["water_commercial"]
    else:
        rate_info = RATE_STRUCTURES["water_residential"]
    total = rate_info["base_charge"]
    remaining = gallons
    for tier in rate_info["tiers"]:
        range_str = tier["range"]
        if range_str.startswith("Over"):
            total += (remaining / 1000) * tier["rate_per_1000"]
            remaining = 0
        else:
            parts = range_str.replace(",", "").replace(" gal", "").split("-")
            low = int(parts[0])
            high = int(parts[1])
            tier_volume = min(remaining, high - low + 1)
            if tier_volume > 0:
                total += (tier_volume / 1000) * tier["rate_per_1000"]
                remaining -= tier_volume
        if remaining <= 0:
            break
    return round(total, 2)


def _usage_trend(account_id):
    """Analyze usage trend for an account."""
    history = USAGE_HISTORY.get(account_id, [])
    if len(history) < 2:
        return "insufficient_data"
    recent = history[-1]["water_gallons"]
    previous_avg = sum(h["water_gallons"] for h in history[:-1]) / (len(history) - 1)
    if recent > previous_avg * 1.20:
        return "significantly_increasing"
    elif recent > previous_avg * 1.05:
        return "slightly_increasing"
    elif recent < previous_avg * 0.80:
        return "significantly_decreasing"
    elif recent < previous_avg * 0.95:
        return "slightly_decreasing"
    return "stable"


def _leak_assessment(account_id):
    """Flag an account as a suspected leak from interval-meter evidence.

    Two published conditions, either of which flags the account:
      1. minimum nightly flow above the threshold on every night of the window
         (continuous flow - water moving when nobody is drawing it)
      2. a Significantly Increasing consumption trend

    A flag is a suspected leak pending field verification by the utility.
    """
    diag = METER_DIAGNOSTICS.get(account_id)
    trend = _usage_trend(account_id)
    result = {
        "status": "not_assessed",
        "trend": trend,
        "reasons": [],
        "estimated_loss_gallons": 0,
    }
    if not diag:
        return result
    result["status"] = "no_indicator"
    if (
        diag["min_nightly_flow_gph"] > LEAK_THRESHOLDS["min_nightly_flow_gph"]
        and diag["continuous_flow_nights"] >= LEAK_THRESHOLDS["window_nights"]
    ):
        result["reasons"].append(
            f"Continuous flow: minimum nightly flow {diag['min_nightly_flow_gph']:,.1f} gal/hr "
            f"on {diag['continuous_flow_nights']} of {diag['window_nights']} nights "
            f"(threshold {LEAK_THRESHOLDS['min_nightly_flow_gph']:,.1f} gal/hr)"
        )
        result["estimated_loss_gallons"] = int(
            round(diag["min_nightly_flow_gph"] * 24 * diag["window_nights"])
        )
    if trend == LEAK_THRESHOLDS["trend_flag"]:
        result["reasons"].append(
            "Consumption trend: Significantly Increasing (latest period above 1.20x the prior-period average)"
        )
    if result["reasons"]:
        result["status"] = "suspected_leak"
    return result


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------

class UtilityBillingAssistanceAgent(BasicAgent):
    """Municipal utility billing assistance agent."""

    def __init__(self):
        self.name = "@aibast-agents-library/utility-billing-assistance"
        self.metadata = {
            "name": self.name,
            "display_name": "Utility Billing Assistance Agent",
            "description": __manifest__["description"],
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "billing_inquiry",
                            "usage_analysis",
                            "leak_detection",
                            "payment_plan",
                            "assistance_programs",
                        ],
                    },
                    "account_id": {"type": "string"},
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        operation = kwargs.get("operation", "billing_inquiry")
        dispatch = {
            "billing_inquiry": self._billing_inquiry,
            "usage_analysis": self._usage_analysis,
            "leak_detection": self._leak_detection,
            "payment_plan": self._payment_plan,
            "assistance_programs": self._assistance_programs,
        }
        handler = dispatch.get(operation)
        if not handler:
            return f"**Error:** Unknown operation `{operation}`."
        return handler(**kwargs)

    def _billing_inquiry(self, **kwargs) -> str:
        account_id = kwargs.get("account_id")
        if account_id and account_id in UTILITY_ACCOUNTS:
            acct = UTILITY_ACCOUNTS[account_id]
            total_due = acct["balance_current"] + acct["balance_past_due"]
            lines = [f"# Billing Inquiry: {account_id}\n"]
            lines.append(f"- **Customer:** {acct['customer']}")
            lines.append(f"- **Address:** {acct['address']}")
            lines.append(f"- **Account Type:** {acct['account_type'].title()}")
            lines.append(f"- **Services:** {', '.join(s.replace('_', ' ').title() for s in acct['services'])}")
            lines.append(f"- **Status:** {acct['status'].title()}")
            lines.append(f"- **Current Charges:** ${acct['balance_current']:,.2f}")
            lines.append(f"- **Past Due:** ${acct['balance_past_due']:,.2f}")
            lines.append(f"- **Total Due:** ${total_due:,.2f}")
            lines.append(f"- **Auto-Pay:** {'Yes' if acct['autopay'] else 'No'}")
            lines.append(f"- **Last Payment:** ${acct['last_payment']['amount']:,.2f} on {acct['last_payment']['date']}")
            return "\n".join(lines)

        lines = ["# Utility Accounts Summary\n"]
        lines.append("| Account | Customer | Type | Current | Past Due | Status |")
        lines.append("|---|---|---|---|---|---|")
        for aid, acct in UTILITY_ACCOUNTS.items():
            lines.append(
                f"| {aid} | {acct['customer']} | {acct['account_type'].title()} "
                f"| ${acct['balance_current']:,.2f} | ${acct['balance_past_due']:,.2f} | {acct['status'].title()} |"
            )
        total_ar = sum(a["balance_current"] + a["balance_past_due"] for a in UTILITY_ACCOUNTS.values())
        lines.append(f"\n**Total Accounts Receivable:** ${total_ar:,.2f}")
        return "\n".join(lines)

    def _usage_analysis(self, **kwargs) -> str:
        account_id = kwargs.get("account_id", "ACCT-90001")
        history = USAGE_HISTORY.get(account_id, [])
        acct = UTILITY_ACCOUNTS.get(account_id, {})
        trend = _usage_trend(account_id)
        lines = [f"# Usage Analysis: {account_id}\n"]
        lines.append(f"**Customer:** {acct.get('customer', 'Unknown')}")
        lines.append(f"**Usage Trend:** {trend.replace('_', ' ').title()}\n")
        if history:
            lines.append("| Period | Water (gal) | Sewer (gal) | Amount |")
            lines.append("|---|---|---|---|")
            for h in history:
                lines.append(f"| {h['period']} | {h['water_gallons']:,} | {h['sewer_gallons']:,} | ${h['amount']:,.2f} |")
            avg_water = sum(h["water_gallons"] for h in history) / len(history)
            avg_bill = sum(h["amount"] for h in history) / len(history)
            lines.append(f"\n**Avg Monthly Water Usage:** {avg_water:,.0f} gallons")
            lines.append(f"**Avg Monthly Bill:** ${avg_bill:,.2f}")
        lines.append("\n## Rate Structure\n")
        for rate_name, rate_info in RATE_STRUCTURES.items():
            lines.append(f"### {rate_name.replace('_', ' ').title()}\n")
            if isinstance(rate_info, dict) and "tiers" in rate_info:
                lines.append(f"Base Charge: ${rate_info['base_charge']:,.2f}\n")
                for tier in rate_info["tiers"]:
                    lines.append(f"- {tier['range']}: ${tier['rate_per_1000']:,.2f}/1,000 gal")
            elif isinstance(rate_info, dict) and "base_charge" in rate_info:
                lines.append(f"Base: ${rate_info['base_charge']:,.2f}, Rate: ${rate_info.get('rate_per_1000', 0):,.2f}/1,000 gal")
            lines.append("")
        return "\n".join(lines)

    def _leak_detection(self, **kwargs) -> str:
        account_id = kwargs.get("account_id")
        label = {
            "suspected_leak": "Suspected Leak",
            "no_indicator": "No Leak Indicator",
            "not_assessed": "Not Assessed - no interval data on file",
        }

        if account_id and account_id in UTILITY_ACCOUNTS:
            acct = UTILITY_ACCOUNTS[account_id]
            diag = METER_DIAGNOSTICS.get(account_id)
            assessment = _leak_assessment(account_id)
            lines = [f"# Leak Assessment: {account_id}\n"]
            lines.append(f"**Customer:** {acct['customer']}")
            lines.append(f"**Assessment:** {label[assessment['status']]}")
            lines.append(f"**Usage Trend:** {assessment['trend'].replace('_', ' ').title()}\n")
            if not diag:
                lines.append(
                    "No interval-meter data is on file for this account, so no leak "
                    "assessment can be made. Interval data is on file for "
                    f"{', '.join(sorted(METER_DIAGNOSTICS))} only."
                )
                return "\n".join(lines)
            lines.append("## Meter Evidence\n")
            lines.append(f"- **Minimum Nightly Flow:** {diag['min_nightly_flow_gph']:,.1f} gal/hr")
            lines.append(
                f"- **Continuous-Flow Nights:** {diag['continuous_flow_nights']} of {diag['window_nights']}"
            )
            lines.append(f"- **Last Meter Read:** {diag['last_read']}")
            lines.append(
                f"- **Flag Threshold:** minimum nightly flow above "
                f"{LEAK_THRESHOLDS['min_nightly_flow_gph']:,.1f} gal/hr on all "
                f"{LEAK_THRESHOLDS['window_nights']} nights, or a Significantly Increasing trend"
            )
            if assessment["reasons"]:
                lines.append("\n## Why It Is Flagged\n")
                for reason in assessment["reasons"]:
                    lines.append(f"- {reason}")
                if assessment["estimated_loss_gallons"]:
                    est = assessment["estimated_loss_gallons"]
                    lines.append(
                        f"- **Estimated loss at the continuous-flow rate:** {est:,} gallons "
                        f"over {diag['window_nights']} days "
                        f"({diag['min_nightly_flow_gph']:,.1f} gal/hr x 24 x {diag['window_nights']})"
                    )
                    history = USAGE_HISTORY.get(account_id, [])
                    if history:
                        latest = history[-1]
                        pct = est / latest["water_gallons"] * 100
                        lines.append(
                            f"- That is about {pct:,.0f}% of the {latest['water_gallons']:,} gallons "
                            f"billed in {latest['period']}."
                        )
                lines.append(
                    "\n**Suspected, not confirmed.** This is a meter reading, not a "
                    "diagnosis. The utility must verify in the field before any repair "
                    "order or billing adjustment. The dollar impact crosses rate tiers "
                    "and is quantified by a billing clerk."
                )
            else:
                lines.append(
                    "\nNo flag condition is met: nightly flow stays at or below the "
                    "threshold and the trend is not Significantly Increasing."
                )
            return "\n".join(lines)

        lines = ["# Leak Detection Scan\n"]
        lines.append("| Account | Customer | Min Nightly Flow (gal/hr) | Continuous-Flow Nights | Trend | Assessment |")
        lines.append("|---|---|---|---|---|---|")
        flagged = []
        for aid, acct in UTILITY_ACCOUNTS.items():
            diag = METER_DIAGNOSTICS.get(aid)
            assessment = _leak_assessment(aid)
            if assessment["status"] == "suspected_leak":
                flagged.append(aid)
            if diag:
                flow = f"{diag['min_nightly_flow_gph']:,.1f}"
                nights = f"{diag['continuous_flow_nights']} of {diag['window_nights']}"
            else:
                flow = "No interval data"
                nights = "No interval data"
            lines.append(
                f"| {aid} | {acct['customer']} | {flow} | {nights} "
                f"| {assessment['trend'].replace('_', ' ').title()} | {label[assessment['status']]} |"
            )
        lines.append(
            f"\n**Accounts Flagged as Suspected Leaks:** {len(flagged)}"
            + (f" ({', '.join(flagged)})" if flagged else "")
        )
        lines.append(
            "\nA flag is a suspected leak pending field verification by the utility, "
            "not a confirmed leak and not a billing adjustment."
        )
        return "\n".join(lines)

    def _payment_plan(self, **kwargs) -> str:
        account_id = kwargs.get("account_id", "ACCT-90003")
        acct = UTILITY_ACCOUNTS.get(account_id, list(UTILITY_ACCOUNTS.values())[2])
        past_due = acct["balance_past_due"]
        lines = [f"# Payment Plan Options: {account_id}\n"]
        lines.append(f"**Customer:** {acct['customer']}")
        lines.append(f"**Past Due Balance:** ${past_due:,.2f}\n")
        if past_due > 0:
            lines.append("## Installment Options\n")
            lines.append("| Installments | Monthly Payment | Total |")
            lines.append("|---|---|---|")
            for months in [3, 6, 9, 12]:
                monthly = round(past_due / months, 2)
                lines.append(f"| {months} months | ${monthly:,.2f} | ${past_due:,.2f} |")
            lines.append("\n*Note: Current charges continue to accrue during payment plan.*\n")
        lines.append("## Payment Plan Requirements\n")
        pp = ASSISTANCE_PROGRAMS["payment_plan"]
        lines.append(f"- {pp['eligibility']}")
        lines.append(f"- Maximum installments: {pp['max_installments']}")
        lines.append(f"- Documents required: {', '.join(pp['documents_required'])}")
        return "\n".join(lines)

    def _assistance_programs(self, **kwargs) -> str:
        lines = ["# Utility Assistance Programs\n"]
        for prog_id, prog in ASSISTANCE_PROGRAMS.items():
            lines.append(f"## {prog['name']}\n")
            lines.append(f"- **Eligibility:** {prog['eligibility']}")
            if prog["max_benefit"] > 0:
                lines.append(f"- **Maximum Benefit:** ${prog['max_benefit']:,.0f}")
            if prog.get("discount_pct"):
                lines.append(f"- **Discount:** {prog['discount_pct']}%")
            lines.append(f"- **Status:** {prog['status'].replace('_', ' ').title()}")
            lines.append(f"- **Documents Required:**")
            for doc in prog["documents_required"]:
                lines.append(f"  - {doc}")
            lines.append("")
        lines.append("## Federal Poverty Level Reference (2025)\n")
        fpl_table = {1: 15650, 2: 21150, 3: 26650, 4: 32150, 5: 37650}
        lines.append("| Household Size | 100% FPL | 150% FPL | 200% FPL |")
        lines.append("|---|---|---|---|")
        for size, fpl in fpl_table.items():
            lines.append(f"| {size} | ${fpl:,} | ${int(fpl * 1.5):,} | ${fpl * 2:,} |")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    agent = UtilityBillingAssistanceAgent()
    print(agent.perform(operation="billing_inquiry"))
    print("\n" + "=" * 80 + "\n")
    print(agent.perform(operation="billing_inquiry", account_id="ACCT-90002"))
    print("\n" + "=" * 80 + "\n")
    print(agent.perform(operation="usage_analysis", account_id="ACCT-90003"))
    print("\n" + "=" * 80 + "\n")
    print(agent.perform(operation="leak_detection"))
    print("\n" + "=" * 80 + "\n")
    print(agent.perform(operation="leak_detection", account_id="ACCT-90003"))
    print("\n" + "=" * 80 + "\n")
    print(agent.perform(operation="payment_plan", account_id="ACCT-90003"))
    print("\n" + "=" * 80 + "\n")
    print(agent.perform(operation="assistance_programs"))
