"""
Cross-Channel Engagement Agent — B2C Sales Stack

Assembles a single, unified view of a customer's cross-channel interactions —
marketing touchpoints and support contacts on one timeline — and backs it with
channel performance, mapped customer journeys, support-contact quality, and
campaign attribution.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent

__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/omnichannel-engagement",
    "version": "1.0.0",
    "display_name": "Cross-Channel Engagement Agent",
    "description": "Cross-channel engagement analytics: a unified per-customer interaction timeline, support-contact quality, channel performance, journey mapping, optimization, and campaign attribution.",
    "author": "AIBAST",
    "tags": ["omnichannel", "engagement", "journey", "attribution", "campaign", "support", "b2c"],
    "category": "b2c_sales",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}

# ---------------------------------------------------------------------------
# Synthetic domain data
# ---------------------------------------------------------------------------

CHANNELS = {
    "email": {"sessions_30d": 145000, "conversions_30d": 4350, "revenue_30d": 870000, "cost_30d": 12500, "avg_order_value": 200.0, "bounce_rate": 18.5},
    "sms": {"sessions_30d": 62000, "conversions_30d": 1860, "revenue_30d": 325500, "cost_30d": 8200, "avg_order_value": 175.0, "bounce_rate": 5.2},
    "social_media": {"sessions_30d": 230000, "conversions_30d": 2760, "revenue_30d": 552000, "cost_30d": 45000, "avg_order_value": 200.0, "bounce_rate": 42.0},
    "web_organic": {"sessions_30d": 480000, "conversions_30d": 9600, "revenue_30d": 1920000, "cost_30d": 18000, "avg_order_value": 200.0, "bounce_rate": 35.0},
    "web_paid": {"sessions_30d": 185000, "conversions_30d": 5550, "revenue_30d": 1110000, "cost_30d": 95000, "avg_order_value": 200.0, "bounce_rate": 28.0},
    "mobile_app": {"sessions_30d": 310000, "conversions_30d": 12400, "revenue_30d": 2480000, "cost_30d": 22000, "avg_order_value": 200.0, "bounce_rate": 12.0},
    "in_store": {"sessions_30d": 95000, "conversions_30d": 28500, "revenue_30d": 5700000, "cost_30d": 180000, "avg_order_value": 200.0, "bounce_rate": 0},
}

CUSTOMER_JOURNEYS = {
    "journey_discovery": {
        "name": "Discovery to Purchase",
        "touchpoints": ["social_media_ad", "website_browse", "email_signup", "email_promo", "website_purchase"],
        "avg_days": 14,
        "conversion_rate": 3.2,
        "avg_touchpoints": 5,
    },
    "journey_repeat": {
        "name": "Repeat Purchase",
        "touchpoints": ["email_promo", "mobile_app_browse", "mobile_app_purchase"],
        "avg_days": 3,
        "conversion_rate": 18.5,
        "avg_touchpoints": 3,
    },
    "journey_winback": {
        "name": "Win-Back",
        "touchpoints": ["email_winback", "sms_offer", "website_browse", "website_purchase"],
        "avg_days": 21,
        "conversion_rate": 8.4,
        "avg_touchpoints": 4,
    },
    "journey_impulse": {
        "name": "Impulse Purchase",
        "touchpoints": ["social_media_ad", "website_purchase"],
        "avg_days": 0,
        "conversion_rate": 1.8,
        "avg_touchpoints": 2,
    },
}

CAMPAIGN_RESULTS = {
    "CAMP-301": {"name": "Spring Collection Launch", "channel": "email", "sent": 250000, "opens": 62500, "clicks": 18750, "conversions": 2250, "revenue": 450000, "cost": 5000},
    "CAMP-302": {"name": "Flash Sale — 48 Hours", "channel": "sms", "sent": 120000, "opens": 115200, "clicks": 24000, "conversions": 3600, "revenue": 540000, "cost": 6000},
    "CAMP-303": {"name": "Influencer Partnership", "channel": "social_media", "sent": 0, "opens": 0, "clicks": 85000, "conversions": 1700, "revenue": 340000, "cost": 35000},
    "CAMP-304": {"name": "Google Shopping Ads", "channel": "web_paid", "sent": 0, "opens": 0, "clicks": 45000, "conversions": 2700, "revenue": 540000, "cost": 42000},
    "CAMP-305": {"name": "App Push — Loyalty Members", "channel": "mobile_app", "sent": 85000, "opens": 42500, "clicks": 17000, "conversions": 5100, "revenue": 765000, "cost": 2000},
}

# Record-level interaction histories. These are individual customer records, not
# a roll-up: they are never summed into the channel or campaign totals above.
CUSTOMER_INTERACTIONS = {
    "CUST-401": {
        "segment": "Loyalty - repeat purchaser",
        "journey": "Repeat Purchase",
        "touchpoints": [
            {"date": "2026-07-06", "channel": "email", "interaction": "Opened promo email", "reference": "CAMP-301"},
            {"date": "2026-07-06", "channel": "mobile_app", "interaction": "Browsed three product pages", "reference": ""},
            {"date": "2026-07-08", "channel": "mobile_app", "interaction": "Placed order", "reference": ""},
            {"date": "2026-07-09", "channel": "email", "interaction": "Received order confirmation", "reference": ""},
            {"date": "2026-07-11", "channel": "in_store", "interaction": "Collected order at store pickup desk", "reference": ""},
        ],
    },
    "CUST-402": {
        "segment": "Lapsed - win-back target",
        "journey": "Win-Back",
        "touchpoints": [
            {"date": "2026-06-24", "channel": "email", "interaction": "Opened win-back offer", "reference": ""},
            {"date": "2026-06-27", "channel": "sms", "interaction": "Clicked offer link", "reference": "CAMP-302"},
            {"date": "2026-07-01", "channel": "web_organic", "interaction": "Browsed site, no cart created", "reference": ""},
            {"date": "2026-07-05", "channel": "web_paid", "interaction": "Returned to site from shopping ad", "reference": "CAMP-304"},
            {"date": "2026-07-06", "channel": "web_organic", "interaction": "Placed order", "reference": ""},
        ],
    },
    "CUST-403": {
        "segment": "New - discovery",
        "journey": "Discovery to Purchase",
        "touchpoints": [
            {"date": "2026-07-03", "channel": "social_media", "interaction": "Engaged with influencer post", "reference": "CAMP-303"},
            {"date": "2026-07-03", "channel": "web_organic", "interaction": "Browsed site", "reference": ""},
            {"date": "2026-07-04", "channel": "email", "interaction": "Signed up for newsletter", "reference": ""},
            {"date": "2026-07-10", "channel": "email", "interaction": "Clicked promo email", "reference": "CAMP-301"},
            {"date": "2026-07-17", "channel": "in_store", "interaction": "Completed purchase in store", "reference": ""},
        ],
    },
}

# Support contacts. Contacts are not sessions and are never added to the
# channel session, conversion, or revenue figures. `csat` of None means no
# score was recorded, not a score of zero.
SUPPORT_INTERACTIONS = {
    "CASE-501": {"customer_id": "CUST-401", "date": "2026-07-12", "channel": "mobile_app", "intent": "Order status", "handle_time_min": 6, "resolution_status": "Resolved", "csat": 5},
    "CASE-502": {"customer_id": "CUST-402", "date": "2026-07-02", "channel": "sms", "intent": "Promo code not applying", "handle_time_min": 11, "resolution_status": "Resolved", "csat": 4},
    "CASE-503": {"customer_id": "CUST-403", "date": "2026-07-19", "channel": "email", "intent": "Delivery delay", "handle_time_min": 34, "resolution_status": "Resolved", "csat": 3},
    "CASE-504": {"customer_id": "CUST-403", "date": "2026-07-22", "channel": "in_store", "intent": "Return or exchange", "handle_time_min": 18, "resolution_status": "Resolved", "csat": 5},
    "CASE-505": {"customer_id": "CUST-401", "date": "2026-07-15", "channel": "web_organic", "intent": "Account login", "handle_time_min": 22, "resolution_status": "Escalated", "csat": 2},
    "CASE-506": {"customer_id": "CUST-402", "date": "2026-07-09", "channel": "social_media", "intent": "Damaged item", "handle_time_min": 47, "resolution_status": "Open", "csat": None},
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _channel_conversion_rate(channel):
    """Calculate conversion rate for a channel."""
    if channel["sessions_30d"] == 0:
        return 0
    return round((channel["conversions_30d"] / channel["sessions_30d"]) * 100, 2)


def _channel_roas(channel):
    """Calculate return on ad spend."""
    if channel["cost_30d"] == 0:
        return 0
    return round(channel["revenue_30d"] / channel["cost_30d"], 2)


def _campaign_roi(campaign):
    """Calculate campaign ROI."""
    if campaign["cost"] == 0:
        return 0
    return round(((campaign["revenue"] - campaign["cost"]) / campaign["cost"]) * 100, 1)


def _label(value):
    """Render a recorded snake_case name in title case."""
    return value.replace("_", " ").title()


def _cases_for(customer_id):
    """Return this customer's support cases, in recorded case-id order."""
    return [(cid, c) for cid, c in SUPPORT_INTERACTIONS.items() if c["customer_id"] == customer_id]


def _merged_timeline(customer_id):
    """Merge a customer's marketing touchpoints and support contacts by date."""
    events = []
    for tp in CUSTOMER_INTERACTIONS[customer_id]["touchpoints"]:
        events.append({
            "date": tp["date"],
            "kind": "Marketing touchpoint",
            "channel": tp["channel"],
            "detail": tp["interaction"],
            "reference": tp["reference"],
        })
    for cid, case in _cases_for(customer_id):
        events.append({
            "date": case["date"],
            "kind": "Support contact",
            "channel": case["channel"],
            "detail": f"{case['intent']} ({case['resolution_status']})",
            "reference": cid,
        })
    return sorted(events, key=lambda e: e["date"])


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------

class OmnichannelEngagementAgent(BasicAgent):
    """Cross-channel engagement analytics agent."""

    def __init__(self):
        self.name = "@aibast-agents-library/omnichannel-engagement"
        self.metadata = {
            "name": self.name,
            "display_name": "Cross-Channel Engagement Agent",
            "description": __manifest__["description"],
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "unified_interaction_view",
                            "support_interactions",
                            "channel_performance",
                            "journey_analysis",
                            "engagement_optimization",
                            "campaign_attribution",
                        ],
                    },
                    "channel": {"type": "string"},
                    "campaign_id": {"type": "string"},
                    "customer_id": {"type": "string"},
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        operation = kwargs.get("operation", "channel_performance")
        dispatch = {
            "unified_interaction_view": self._unified_interaction_view,
            "support_interactions": self._support_interactions,
            "channel_performance": self._channel_performance,
            "journey_analysis": self._journey_analysis,
            "engagement_optimization": self._engagement_optimization,
            "campaign_attribution": self._campaign_attribution,
        }
        handler = dispatch.get(operation)
        if not handler:
            return f"**Error:** Unknown operation `{operation}`."
        return handler(**kwargs)

    def _unified_interaction_view(self, **kwargs) -> str:
        requested = (kwargs.get("customer_id") or "").strip().upper()
        if requested and requested not in CUSTOMER_INTERACTIONS:
            return (
                f"**No data:** `{requested}` has no recorded interaction history. "
                f"The recorded customers are {', '.join(CUSTOMER_INTERACTIONS)}."
            )
        customer_ids = [requested] if requested else list(CUSTOMER_INTERACTIONS)
        lines = ["# Unified Interaction View\n"]
        lines.append(
            "One customer's marketing touchpoints and support contacts on a single "
            "timeline. These are record-level interactions and are never added to the "
            "channel or campaign totals.\n"
        )
        for cust_id in customer_ids:
            cust = CUSTOMER_INTERACTIONS[cust_id]
            timeline = _merged_timeline(cust_id)
            cases = _cases_for(cust_id)
            channels = []
            for event in timeline:
                if event["channel"] not in channels:
                    channels.append(event["channel"])
            open_cases = [cid for cid, c in cases if c["resolution_status"] != "Resolved"]
            lines.append(f"## {cust_id}\n")
            lines.append(f"- **Segment:** {cust['segment']}")
            lines.append(f"- **Mapped Journey:** {cust['journey']}")
            lines.append(f"- **Interactions:** {len(timeline)} across {len(channels)} channels")
            lines.append(f"- **Support Contacts:** {len(cases)}")
            if open_cases:
                lines.append(f"- **Not Resolved:** {', '.join(open_cases)}")
            lines.append("")
            lines.append("| Date | Channel | Type | Interaction | Reference |")
            lines.append("|---|---|---|---|---|")
            for event in timeline:
                reference = event["reference"] if event["reference"] else "-"
                lines.append(
                    f"| {event['date']} | {_label(event['channel'])} | {event['kind']} "
                    f"| {event['detail']} | {reference} |"
                )
            lines.append("")
            lines.append(f"**Channels Touched:** {', '.join(_label(c) for c in channels)}\n")
        return "\n".join(lines)

    def _support_interactions(self, **kwargs) -> str:
        requested = (kwargs.get("customer_id") or "").strip().upper()
        if requested and requested not in CUSTOMER_INTERACTIONS:
            return (
                f"**No data:** `{requested}` has no recorded interaction history. "
                f"The recorded customers are {', '.join(CUSTOMER_INTERACTIONS)}."
            )
        rows = [
            (cid, c) for cid, c in SUPPORT_INTERACTIONS.items()
            if not requested or c["customer_id"] == requested
        ]
        lines = ["# Support Interaction Report\n"]
        if requested:
            lines.append(
                f"Rows for {requested} only; the totals below still cover all "
                f"{len(SUPPORT_INTERACTIONS)} recorded contacts.\n"
            )
        lines.append("| Case | Customer | Date | Channel | Intent | Handle Time | Resolution | CSAT |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for cid, case in rows:
            csat = case["csat"] if case["csat"] is not None else "no CSAT recorded"
            lines.append(
                f"| {cid} | {case['customer_id']} | {case['date']} | {_label(case['channel'])} "
                f"| {case['intent']} | {case['handle_time_min']} min | {case['resolution_status']} "
                f"| {csat} |"
            )
        all_cases = list(SUPPORT_INTERACTIONS.values())
        total_contacts = len(all_cases)
        resolved = sum(1 for c in all_cases if c["resolution_status"] == "Resolved")
        scored = [c["csat"] for c in all_cases if c["csat"] is not None]
        avg_handle = round(sum(c["handle_time_min"] for c in all_cases) / total_contacts, 1)
        avg_csat = round(sum(scored) / len(scored), 1) if scored else 0
        resolution_rate = round((resolved / total_contacts) * 100, 1)
        lines.append(f"\n**Total Contacts:** {total_contacts}")
        lines.append(f"**Avg Handle Time:** {avg_handle} min")
        lines.append(f"**Resolution Rate:** {resolution_rate}% ({resolved} of {total_contacts})")
        lines.append(f"**Avg CSAT:** {avg_csat} across {len(scored)} scored contacts")
        lines.append("\n## Contacts Needing an Owner\n")
        unresolved = [(cid, c) for cid, c in SUPPORT_INTERACTIONS.items() if c["resolution_status"] != "Resolved"]
        if not unresolved:
            lines.append("- None: every recorded contact is Resolved.")
        for cid, case in unresolved:
            lines.append(
                f"- {cid} ({case['customer_id']}, {_label(case['channel'])}): "
                f"{case['intent']} - {case['resolution_status']}, {case['handle_time_min']} min handled"
            )
        lines.append(
            "\nA supervisor assigns and works these. This report flags them; it does "
            "not route, reply, or close a case."
        )
        return "\n".join(lines)

    def _channel_performance(self, **kwargs) -> str:
        total_revenue = sum(c["revenue_30d"] for c in CHANNELS.values())
        total_conversions = sum(c["conversions_30d"] for c in CHANNELS.values())
        lines = ["# Channel Performance (30-Day)\n"]
        lines.append(f"**Total Revenue:** ${total_revenue:,.0f}")
        lines.append(f"**Total Conversions:** {total_conversions:,}\n")
        lines.append("| Channel | Sessions | Conversions | CVR | Revenue | Cost | ROAS |")
        lines.append("|---|---|---|---|---|---|---|")
        for ch_name, ch in CHANNELS.items():
            cvr = _channel_conversion_rate(ch)
            roas = _channel_roas(ch)
            lines.append(
                f"| {ch_name.replace('_', ' ').title()} | {ch['sessions_30d']:,} | {ch['conversions_30d']:,} "
                f"| {cvr}% | ${ch['revenue_30d']:,.0f} | ${ch['cost_30d']:,.0f} | {roas}x |"
            )
        lines.append("\n## Revenue Share by Channel\n")
        for ch_name, ch in CHANNELS.items():
            share = round((ch["revenue_30d"] / total_revenue) * 100, 1) if total_revenue else 0
            lines.append(f"- {ch_name.replace('_', ' ').title()}: {share}%")
        return "\n".join(lines)

    def _journey_analysis(self, **kwargs) -> str:
        lines = ["# Customer Journey Analysis\n"]
        for jid, j in CUSTOMER_JOURNEYS.items():
            lines.append(f"## {j['name']}\n")
            lines.append(f"- **Avg Duration:** {j['avg_days']} days")
            lines.append(f"- **Avg Touchpoints:** {j['avg_touchpoints']}")
            lines.append(f"- **Conversion Rate:** {j['conversion_rate']}%\n")
            lines.append("**Touchpoint Sequence:**\n")
            for i, tp in enumerate(j["touchpoints"], 1):
                arrow = " -> " if i < len(j["touchpoints"]) else ""
                lines.append(f"{i}. {tp.replace('_', ' ').title()}{arrow}")
            lines.append("")
        lines.append("## Journey Optimization Opportunities\n")
        lines.append("- **Discovery:** Shorten path by enabling social commerce checkout")
        lines.append("- **Repeat:** Leverage push notifications for faster re-engagement")
        lines.append("- **Win-Back:** Test earlier SMS touchpoint (day 7 vs day 14)")
        lines.append("- **Impulse:** Optimize social ad creative for direct conversion")
        return "\n".join(lines)

    def _engagement_optimization(self, **kwargs) -> str:
        lines = ["# Engagement Optimization Report\n"]
        lines.append("## Channel Efficiency Ranking\n")
        ranked = []
        for ch_name, ch in CHANNELS.items():
            roas = _channel_roas(ch)
            cvr = _channel_conversion_rate(ch)
            ranked.append((ch_name, roas, cvr, ch))
        ranked.sort(key=lambda x: x[1], reverse=True)
        lines.append("| Rank | Channel | ROAS | CVR | Bounce Rate | Recommendation |")
        lines.append("|---|---|---|---|---|---|")
        for i, (name, roas, cvr, ch) in enumerate(ranked, 1):
            if roas > 50:
                rec = "Scale investment"
            elif roas > 10:
                rec = "Optimize spend"
            else:
                rec = "Review ROI"
            lines.append(
                f"| {i} | {name.replace('_', ' ').title()} | {roas}x | {cvr}% "
                f"| {ch['bounce_rate']}% | {rec} |"
            )
        total_cost = sum(c["cost_30d"] for c in CHANNELS.values())
        total_rev = sum(c["revenue_30d"] for c in CHANNELS.values())
        lines.append(f"\n**Total Marketing Spend:** ${total_cost:,.0f}")
        lines.append(f"**Total Revenue:** ${total_rev:,.0f}")
        lines.append(f"**Blended ROAS:** {round(total_rev / total_cost, 1)}x")
        lines.append("\n## Optimization Actions\n")
        lines.append("1. Shift 10% of social media budget to mobile app push campaigns")
        lines.append("2. Implement progressive profiling on email signups")
        lines.append("3. Launch A/B test on checkout flow for web paid traffic")
        lines.append("4. Increase SMS frequency for high-value customer segment")
        return "\n".join(lines)

    def _campaign_attribution(self, **kwargs) -> str:
        lines = ["# Campaign Attribution Report\n"]
        lines.append("| Campaign | Channel | Conversions | Revenue | Cost | ROI |")
        lines.append("|---|---|---|---|---|---|")
        total_rev = 0
        total_cost = 0
        for cid, c in CAMPAIGN_RESULTS.items():
            roi = _campaign_roi(c)
            total_rev += c["revenue"]
            total_cost += c["cost"]
            lines.append(
                f"| {c['name']} ({cid}) | {c['channel'].replace('_', ' ').title()} "
                f"| {c['conversions']:,} | ${c['revenue']:,.0f} | ${c['cost']:,.0f} | {roi}% |"
            )
        lines.append(f"\n**Total Campaign Revenue:** ${total_rev:,.0f}")
        lines.append(f"**Total Campaign Cost:** ${total_cost:,.0f}")
        overall_roi = round(((total_rev - total_cost) / total_cost) * 100, 1) if total_cost else 0
        lines.append(f"**Overall Campaign ROI:** {overall_roi}%")
        lines.append("\n## Campaign Detail\n")
        for cid, c in CAMPAIGN_RESULTS.items():
            lines.append(f"### {c['name']} ({cid})\n")
            if c["sent"] > 0:
                open_rate = round((c["opens"] / c["sent"]) * 100, 1)
                ctr = round((c["clicks"] / c["sent"]) * 100, 1)
                lines.append(f"- Sent: {c['sent']:,} | Opens: {c['opens']:,} ({open_rate}%) | Clicks: {c['clicks']:,} ({ctr}%)")
            else:
                lines.append(f"- Clicks: {c['clicks']:,}")
            conv_rate = round((c["conversions"] / c["clicks"]) * 100, 1) if c["clicks"] else 0
            lines.append(f"- Conversions: {c['conversions']:,} ({conv_rate}% click-to-conversion)")
            lines.append(f"- Revenue: ${c['revenue']:,.0f} | Cost: ${c['cost']:,.0f}\n")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    agent = OmnichannelEngagementAgent()
    print(agent.perform(operation="unified_interaction_view", customer_id="CUST-401"))
    print("\n" + "=" * 80 + "\n")
    print(agent.perform(operation="support_interactions"))
    print("\n" + "=" * 80 + "\n")
    print(agent.perform(operation="channel_performance"))
    print("\n" + "=" * 80 + "\n")
    print(agent.perform(operation="journey_analysis"))
    print("\n" + "=" * 80 + "\n")
    print(agent.perform(operation="engagement_optimization"))
    print("\n" + "=" * 80 + "\n")
    print(agent.perform(operation="campaign_attribution"))
