---
name: "customer-loyalty-rewards"
description: "Provide synthetic loyalty insights: churn-risk segments, top at-risk members, win-back offer drafts, launch-ready campaign plans with projected results, program improvements, points summaries, reward options, and tier analysis, without contacting members or issuing or redeeming benefits. Always use this tool for loyalty questions; every operation has demo defaults for the synthetic 450K-member retailer program, so call it right away. Identifying members at risk of churning (even when the same request also asks for win-back offers) uses `churn_risk_segments`; the top at-risk members and their profiles use `top_at_risk_members`; creating personalized win-back offers for each segment uses `winback_offers`; launching the campaigns or showing expected results uses `campaign_plan` (it returns a launch-ready plan for the user to launch, never sends anything); improving the overall loyalty program uses `program_improvements`; summarizing everything accomplished uses `campaign_summary`. Program ..."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "customer_loyalty_rewards_agent.py"
  tool-name: "CustomerLoyaltyRewardsAgent"
  agent-sha256: "b09a5236086a89fbfbfe6b98c1f89f10da7ce5468e3c852a1b56011ad9d7f658"
  version: "1.1.0"
  author: "AIBAST"
  tags: "loyalty, rewards, points, retention, churn, win-back, tier, b2c"
---

# Customer Loyalty Rewards

Provide synthetic loyalty insights: churn-risk segments, top at-risk members, win-back offer drafts, launch-ready campaign plans with projected results, program improvements, points summaries, reward options, and tier analysis, without contacting members or issuing or redeeming benefits. Always use this tool for loyalty questions; every operation has demo defaults for the synthetic 450K-member retailer program, so call it right away. Identifying members at risk of churning (even when the same request also asks for win-back offers) uses `churn_risk_segments`; the top at-risk members and their profiles use `top_at_risk_members`; creating personalized win-back offers for each segment uses `winback_offers`; launching the campaigns or showing expected results uses `campaign_plan` (it returns a launch-ready plan for the user to launch, never sends anything); improving the overall loyalty program uses `program_improvements`; summarizing everything accomplished uses `campaign_summary`. Program-health questions go to `loyalty_dashboard`; member balance, ledger, earned, or redeemed points questions to `points_summary`; reward-option questions to `reward_recommendations`; and tier structure or progress questions to `tier_analysis`.

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "description": "Required routing key. churn_risk_segments for at-risk / churning members; top_at_risk_members for the top at-risk members and their profiles; winback_offers for personalized win-back offers; campaign_plan for 'launch the campaigns and show expected results'; program_improvements for how to improve the loyalty program; campaign_summary for 'summarize everything we accomplished'. Use points_summary for any member balance or ledger explanation, including a Gold member; do not substitute loyalty_dashboard.",
      "enum": [
        "loyalty_dashboard",
        "points_summary",
        "reward_recommendations",
        "tier_analysis",
        "churn_risk_segments",
        "top_at_risk_members",
        "winback_offers",
        "campaign_plan",
        "program_improvements",
        "campaign_summary"
      ]
    },
    "member_id": {
      "type": "string",
      "description": "Optional synthetic member ID or at-risk member name when the prompt identifies a member. Synthetic Gold Member is LM-10002; at-risk members are Linda M. (LM-20001), Kevin R. (LM-20002) and Sarah T. (LM-20003)."
    },
    "persona": {
      "type": "string",
      "enum": [
        "Loyalty Program Director",
        "CRM Manager",
        "Marketing Leader"
      ],
      "description": "Copy the role stated in the request."
    },
    "data_source": {
      "type": "string",
      "enum": [
        "synthetic"
      ]
    }
  },
  "required": [
    "operation"
  ],
  "additionalProperties": false
}
```

## How to run it

Pass what it needs as one JSON object. This file is complete on its own: everything
needed to run it is below.

1. If `scripts/run.py` exists beside this file, run from this skill's directory:

   ```bash
   python3 scripts/run.py --json '{"operation": "<string>", "member_id": "<string>", "persona": "<string>", "data_source": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=b09a5236086a89fbfbfe6b98c1f89f10da7ce5468e3c852a1b56011ad9d7f658 -->
```python
"""
Customer Loyalty & Rewards Agent — B2C Sales Stack

Segments a 450K-member synthetic loyalty program by churn risk, profiles the
top at-risk members, drafts win-back offers and a launch-ready campaign plan
with projected results, recommends program improvements, and summarizes the
session. Also keeps the points, reward-option and tier views.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent

__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/customer-loyalty-rewards",
    "version": "1.1.0",
    "display_name": "Customer Loyalty and Rewards Agent",
    "description": "Provide synthetic loyalty insights: churn-risk segments, top at-risk members, win-back offer drafts, launch-ready campaign plans with projected results, program improvements, points summaries, reward options, and tier analysis, without contacting members or issuing or redeeming benefits.",
    "author": "AIBAST",
    "tags": ["loyalty", "rewards", "points", "retention", "churn", "win-back", "tier", "b2c"],
    "category": "b2c_sales",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}

# ---------------------------------------------------------------------------
# Synthetic domain data
# ---------------------------------------------------------------------------

LOYALTY_MEMBERS = {
    "LM-10001": {
        "name": "Synthetic Platinum Member",
        "tier": "platinum",
        "points_balance": 48250,
        "points_earned_ytd": 12400,
        "points_redeemed_ytd": 8000,
        "member_since": "2018-03-15",
        "total_spend_ytd": 6200,
        "engagement_score": 92,
        "preferred_rewards": ["travel", "dining"],
    },
    "LM-10002": {
        "name": "Synthetic Gold Member",
        "tier": "gold",
        "points_balance": 22100,
        "points_earned_ytd": 6800,
        "points_redeemed_ytd": 2500,
        "member_since": "2020-08-22",
        "total_spend_ytd": 3400,
        "engagement_score": 75,
        "preferred_rewards": ["merchandise", "gift_cards"],
    },
    "LM-10003": {
        "name": "Synthetic Silver Member",
        "tier": "silver",
        "points_balance": 8450,
        "points_earned_ytd": 3200,
        "points_redeemed_ytd": 0,
        "member_since": "2023-01-10",
        "total_spend_ytd": 1600,
        "engagement_score": 58,
        "preferred_rewards": ["discounts"],
    },
    "LM-10004": {
        "name": "Synthetic Bronze Member",
        "tier": "bronze",
        "points_balance": 2100,
        "points_earned_ytd": 900,
        "points_redeemed_ytd": 0,
        "member_since": "2024-06-05",
        "total_spend_ytd": 450,
        "engagement_score": 32,
        "preferred_rewards": ["discounts", "free_shipping"],
    },
}

TIER_STRUCTURE = {
    "bronze": {"min_spend": 0, "points_multiplier": 1.0, "perks": ["Birthday bonus points", "Member-only sales access"], "next_tier": "silver", "spend_to_next": 1000},
    "silver": {"min_spend": 1000, "points_multiplier": 1.25, "perks": ["Bronze perks", "Free standard shipping", "Early access to new products"], "next_tier": "gold", "spend_to_next": 3000},
    "gold": {"min_spend": 3000, "points_multiplier": 1.5, "perks": ["Silver perks", "Free express shipping", "Exclusive gold events", "Annual gift"], "next_tier": "platinum", "spend_to_next": 6000},
    "platinum": {"min_spend": 6000, "points_multiplier": 2.0, "perks": ["Gold perks", "Personal shopping advisor", "Free returns", "VIP lounge access", "Quarterly bonus"], "next_tier": None, "spend_to_next": 0},
}

REDEMPTION_CATALOG = {
    "travel_voucher_500": {"name": "$500 Travel Voucher", "points_cost": 25000, "category": "travel", "value": 500},
    "dining_card_100": {"name": "$100 Dining Gift Card", "points_cost": 5000, "category": "dining", "value": 100},
    "merch_headphones": {"name": "Premium Wireless Headphones", "points_cost": 15000, "category": "merchandise", "value": 249},
    "gift_card_50": {"name": "$50 Store Gift Card", "points_cost": 2500, "category": "gift_cards", "value": 50},
    "discount_20pct": {"name": "20% Off Next Purchase", "points_cost": 3000, "category": "discounts", "value": 0},
    "free_shipping_3mo": {"name": "Free Shipping for 3 Months", "points_cost": 1500, "category": "free_shipping", "value": 30},
}

ENGAGEMENT_ACTIVITIES = [
    {"activity": "Purchase", "points": "2 per $1 spent", "frequency": "per_transaction"},
    {"activity": "Product Review", "points": "100 bonus", "frequency": "per_review"},
    {"activity": "Referral Signup", "points": "500 bonus", "frequency": "per_referral"},
    {"activity": "Birthday", "points": "Double points for birthday month", "frequency": "annual"},
    {"activity": "Social Share", "points": "50 bonus", "frequency": "per_share"},
    {"activity": "App Download", "points": "250 one-time bonus", "frequency": "once"},
]

# Program-wide engagement segments (synthetic 450K-member retailer program).
PROGRAM_SEGMENTS = [
    {"segment": "Engaged", "members": 124000, "churn_risk_pct": 5},
    {"segment": "Active", "members": 198000, "churn_risk_pct": 12},
    {"segment": "At-risk", "members": 34000, "churn_risk_pct": 68},
    {"segment": "Dormant", "members": 94000, "churn_risk_pct": 89},
]

AT_RISK_SUMMARY = {
    "rule": "60+ days no purchase",
    "unredeemed_points": 108000000,
    "points_expiring_30_days": 42000000,
    "patterns": [
        "High balances + no redemption",
        "Sudden disengagement",
        "Browse-no-buy",
    ],
}

AT_RISK_MEMBERS = {
    "LM-20001": {
        "name": "Linda M.",
        "tier": "Gold",
        "points_balance": 12400,
        "days_since_purchase": 72,
        "annual_value": 21000,
        "interests": "designer accessories",
        "points_expiring": 8000,
        "expiring_in_days": 21,
        "behavior": "waits for sales",
        "trigger": "Her favorite brand just went on sale - she doesn't know yet",
        "offer": "\"Your favorite bags are 40% off\" + double points + \"8K points expire in 21 days\"",
    },
    "LM-20002": {
        "name": "Kevin R.",
        "tier": "Gold",
        "points_balance": 8900,
        "days_since_purchase": 65,
        "annual_value": 15000,
        "interests": "outdoor gear",
        "points_expiring": 3000,
        "expiring_in_days": 30,
        "behavior": "browses new arrivals without buying",
        "trigger": "Three viewed items are back in stock",
        "offer": "\"Your saved items are back\" + 20% off + free shipping",
    },
    "LM-20003": {
        "name": "Sarah T.",
        "tier": "Silver",
        "points_balance": 7200,
        "days_since_purchase": 81,
        "annual_value": 12000,
        "interests": "home decor",
        "points_expiring": 2500,
        "expiring_in_days": 28,
        "behavior": "high balance, never redeemed",
        "trigger": "Her balance now covers a $100 home reward",
        "offer": "\"Don't lose $50\" + 25% bonus points if redeemed this week",
    },
}

WINBACK_SEGMENTS = [
    {"segment": "High-Value", "campaign": "High-value win-back", "members": 8400, "offer": "VIP early access + 3X points for 14 days", "channel": "Email + app push"},
    {"segment": "Point Expiry", "campaign": "Point expiry alert", "members": 12000, "offer": "\"Don't lose $X\" + 25% bonus if redeemed this week", "channel": "SMS + email"},
    {"segment": "Lapsed Browsers", "campaign": "Lapsed browser", "members": 13600, "offer": "Items they viewed + 20% off + free shipping", "channel": "Email + retargeting"},
]

CAMPAIGN_PROJECTION = {
    "window_days": 14,
    "reengagement_pct": 24,
    "avg_order_value": 60,
    "points_redeemed": 32000000,
    "ltv_protected": 1400000,
    "campaign_cost": 8400,
}

PROGRAM_IMPROVEMENTS = [
    {"improvement": "Dynamic point expiry", "impact": "+$340K/yr", "priority": "High"},
    {"improvement": "Tier advancement alerts", "impact": "+18% engagement", "priority": "High"},
    {"improvement": "Personalized rewards", "impact": "+24% redemption", "priority": "High"},
    {"improvement": "Expiry reminder cadence (30/14/7 days)", "impact": "+12% redemption", "priority": "High"},
]

QUICK_WIN = "Tier alerts this week (\"You're 200 points from Gold!\") - low effort, +18% near-tier purchases"
DYNAMIC_EXPIRY = "Rolling expiry with activity extension -> 40% dormancy reduction"
NEXT_STEPS = "Monitor daily, implement tier alerts this week, plan personalized rewards pilot"

APPROVED_PERSONAS = {
    "Loyalty Program Director": "program health, liability, governance, and structural options",
    "CRM Manager": "aggregate engagement patterns and consented preference quality",
    "Marketing Leader": "review-ready campaign concepts and qualitative value",
}

SAFETY_NOTICE = (
    "> Synthetic loyalty planning data. Informational options only; no member is "
    "contacted or enrolled, and no points, tier, offer, reward, redemption, refund, "
    "order, or purchase is issued or changed."
)

_OPERATIONS = [
    "loyalty_dashboard",
    "points_summary",
    "reward_recommendations",
    "tier_analysis",
    "churn_risk_segments",
    "top_at_risk_members",
    "winback_offers",
    "campaign_plan",
    "program_improvements",
    "campaign_summary",
]


def _response_header(persona, default="Loyalty Program Director"):
    role = persona if persona in APPROVED_PERSONAS else default
    return [
        f"**Prepared for:** {role}",
        f"**Role focus:** {APPROVED_PERSONAS[role]}",
        "",
        SAFETY_NOTICE,
        "",
    ]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _points_value(points):
    """Convert points to dollar value (1 point = $0.02)."""
    return round(points * 0.02, 2)


def _millions(amount):
    """Dollar amount shown in millions to one decimal, rounded down ($2,160,000 -> $2.1M)."""
    return f"${int(amount / 100000) / 10:g}M"


def _thousands(amount):
    """Dollar amount shown in whole thousands, rounded down ($489,600 -> $489K)."""
    return f"${int(amount / 1000)}K"


def _count_k(count):
    return f"{int(count / 1000)}K"


def _program_figures():
    total = sum(s["members"] for s in PROGRAM_SEGMENTS)
    at_risk = 0
    for s in PROGRAM_SEGMENTS:
        if s["segment"] == "At-risk":
            at_risk = s["members"]
    value = _points_value(AT_RISK_SUMMARY["unredeemed_points"])
    expiring = _points_value(AT_RISK_SUMMARY["points_expiring_30_days"])
    return total, at_risk, value, expiring


def _projection():
    p = CAMPAIGN_PROJECTION
    reached = sum(s["members"] for s in WINBACK_SEGMENTS)
    reengaged = int(reached * p["reengagement_pct"] / 100)
    revenue = reengaged * p["avg_order_value"]
    liability = _points_value(p["points_redeemed"])
    roi = int(revenue / p["campaign_cost"])
    return {
        "reached": reached, "reengaged": reengaged, "revenue": revenue,
        "liability": liability, "ltv": p["ltv_protected"], "cost": p["campaign_cost"], "roi": roi,
    }


def _tier_progress(member):
    """Calculate progress toward next tier."""
    tier_info = TIER_STRUCTURE.get(member["tier"], {})
    if tier_info["next_tier"] is None:
        return 100.0
    spend_needed = tier_info["spend_to_next"]
    if spend_needed == 0:
        return 100.0
    current_spend = member["total_spend_ytd"]
    return min(100.0, round((current_spend / spend_needed) * 100, 1))


def _recommended_rewards(member):
    """Recommend rewards based on preferences and points balance."""
    recs = []
    for rid, reward in REDEMPTION_CATALOG.items():
        if reward["category"] in member["preferred_rewards"] and reward["points_cost"] <= member["points_balance"]:
            recs.append((rid, reward))
    return recs


def _resolve_at_risk(member_id):
    """At-risk member ID or name (e.g. 'Linda' or 'LM-20001'); None when nothing matches."""
    if not member_id:
        return "LM-20001"
    q = str(member_id).lower().strip()
    for mid, m in AT_RISK_MEMBERS.items():
        if mid.lower() in q or q in m["name"].lower():
            return mid
    return None


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------

class CustomerLoyaltyRewardsAgent(BasicAgent):
    """Customer loyalty and rewards management agent."""

    def __init__(self):
        self.name = "CustomerLoyaltyRewardsAgent"
        self.metadata = {
            "name": self.name,
            "display_name": "Customer Loyalty & Rewards Agent",
            "description": (
                f"{__manifest__['description']} Always use this tool for loyalty "
                "questions; every operation has demo defaults for the synthetic "
                "450K-member retailer program, so call it right away. Identifying "
                "members at risk of churning (even when the same request also asks "
                "for win-back offers) uses `churn_risk_segments`; the top at-risk "
                "members and their profiles use `top_at_risk_members`; creating "
                "personalized win-back offers for each segment uses `winback_offers`; "
                "launching the campaigns or showing expected results uses "
                "`campaign_plan` (it returns a launch-ready plan for the user to "
                "launch, never sends anything); improving the overall loyalty "
                "program uses `program_improvements`; summarizing everything "
                "accomplished uses `campaign_summary`. Program-health questions go "
                "to `loyalty_dashboard`; member balance, ledger, earned, or redeemed "
                "points questions to `points_summary`; reward-option questions to "
                "`reward_recommendations`; and tier structure or progress questions "
                "to `tier_analysis`."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": (
                            "Required routing key. churn_risk_segments for at-risk / "
                            "churning members; top_at_risk_members for the top at-risk "
                            "members and their profiles; winback_offers for personalized "
                            "win-back offers; campaign_plan for 'launch the campaigns and "
                            "show expected results'; program_improvements for how to "
                            "improve the loyalty program; campaign_summary for 'summarize "
                            "everything we accomplished'. Use points_summary for any "
                            "member balance or ledger explanation, including a Gold "
                            "member; do not substitute loyalty_dashboard."
                        ),
                        "enum": list(_OPERATIONS),
                    },
                    "member_id": {
                        "type": "string",
                        "description": (
                            "Optional synthetic member ID or at-risk member name when the "
                            "prompt identifies a member. Synthetic Gold Member is LM-10002; "
                            "at-risk members are Linda M. (LM-20001), Kevin R. (LM-20002) "
                            "and Sarah T. (LM-20003)."
                        ),
                    },
                    "persona": {
                        "type": "string",
                        "enum": list(APPROVED_PERSONAS),
                        "description": "Copy the role stated in the request.",
                    },
                    "data_source": {"type": "string", "enum": ["synthetic"]},
                },
                "required": ["operation"],
                "additionalProperties": False,
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        if kwargs.get("data_source", "synthetic") != "synthetic":
            return "data_source must be `synthetic` for this package."
        operation = kwargs.get("operation", "loyalty_dashboard")
        member_id = kwargs.get("member_id")
        if operation in ("top_at_risk_members", "winback_offers"):
            if member_id and _resolve_at_risk(member_id) is None:
                return (
                    f"Unknown member_id `{member_id}`. Valid synthetic at-risk members: "
                    f"{', '.join(m['name'] + ' (' + mid + ')' for mid, m in AT_RISK_MEMBERS.items())}"
                )
        elif member_id and member_id not in LOYALTY_MEMBERS:
            return (
                f"Unknown member_id `{member_id}`. Valid synthetic IDs: "
                f"{', '.join(LOYALTY_MEMBERS)}"
            )
        dispatch = {
            "loyalty_dashboard": self._loyalty_dashboard,
            "points_summary": self._points_summary,
            "reward_recommendations": self._reward_recommendations,
            "tier_analysis": self._tier_analysis,
            "churn_risk_segments": self._churn_risk_segments,
            "top_at_risk_members": self._top_at_risk_members,
            "winback_offers": self._winback_offers,
            "campaign_plan": self._campaign_plan,
            "program_improvements": self._program_improvements,
            "campaign_summary": self._campaign_summary,
        }
        handler = dispatch.get(operation)
        if not handler:
            return f"**Error:** Unknown operation `{operation}`."
        return handler(**kwargs)

    def _loyalty_dashboard(self, **kwargs) -> str:
        total, at_risk, value, expiring = _program_figures()
        sample_points = sum(m["points_balance"] for m in LOYALTY_MEMBERS.values())
        lines = _response_header(kwargs.get("persona")) + ["# Synthetic Loyalty Program Dashboard\n"]
        lines.append(f"**Program Members:** {total:,} ({_count_k(total)})")
        lines.append(f"**At-Risk Members:** {at_risk:,} with {_millions(value)} in unredeemed points")
        lines.append(f"**Points Value Expiring in 30 Days:** {_thousands(expiring)}\n")
        lines.append("| Segment | Members | Churn Risk |")
        lines.append("|---|---|---|")
        for s in PROGRAM_SEGMENTS:
            lines.append(f"| {s['segment']} | {_count_k(s['members'])} | {s['churn_risk_pct']}% |")
        lines.append("\n## Sample Member Records\n")
        lines.append(f"Four anonymous sample records ({sample_points:,} points, ${_points_value(sample_points):,.2f}).\n")
        lines.append("| Member | Tier | Points | Spend YTD | Engagement | Since |")
        lines.append("|---|---|---|---|---|---|")
        for mid, m in LOYALTY_MEMBERS.items():
            lines.append(
                f"| {m['name']} ({mid}) | {m['tier'].title()} | {m['points_balance']:,} "
                f"| ${m['total_spend_ytd']:,.0f} | {m['engagement_score']} | {m['member_since']} |"
            )
        return "\n".join(lines)

    def _points_summary(self, **kwargs) -> str:
        member_id = kwargs.get("member_id")
        if member_id and member_id in LOYALTY_MEMBERS:
            m = LOYALTY_MEMBERS[member_id]
            lines = _response_header(kwargs.get("persona")) + [f"# Synthetic Points Summary: {m['name']}\n"]
            lines.append(f"- **Tier:** {m['tier'].title()}")
            lines.append(f"- **Points Balance:** {m['points_balance']:,} (${_points_value(m['points_balance']):,.2f})")
            lines.append(f"- **Earned YTD:** {m['points_earned_ytd']:,}")
            lines.append(f"- **Redeemed YTD:** {m['points_redeemed_ytd']:,}")
            lines.append(f"- **Multiplier:** {TIER_STRUCTURE[m['tier']]['points_multiplier']}x\n")
            lines.append("## Earning Opportunities\n")
            for act in ENGAGEMENT_ACTIVITIES:
                lines.append(f"- **{act['activity']}:** {act['points']}")
            return "\n".join(lines)

        lines = _response_header(kwargs.get("persona")) + ["# Synthetic Points Summary — All Members\n"]
        lines.append("| Member | Tier | Balance | Earned YTD | Redeemed YTD | Value |")
        lines.append("|---|---|---|---|---|---|")
        for mid, m in LOYALTY_MEMBERS.items():
            lines.append(
                f"| {m['name']} ({mid}) | {m['tier'].title()} | {m['points_balance']:,} "
                f"| {m['points_earned_ytd']:,} | {m['points_redeemed_ytd']:,} | ${_points_value(m['points_balance']):,.2f} |"
            )
        return "\n".join(lines)

    def _reward_recommendations(self, **kwargs) -> str:
        lines = _response_header(kwargs.get("persona")) + ["# Draft Reward Option Recommendations\n"]
        member_id = kwargs.get("member_id")
        members = {member_id: LOYALTY_MEMBERS[member_id]} if member_id else LOYALTY_MEMBERS
        for mid, m in members.items():
            recs = _recommended_rewards(m)
            lines.append(f"## {m['name']} ({mid}) — {m['points_balance']:,} points\n")
            if recs:
                lines.append("| Reward | Points Cost | Category | Value |")
                lines.append("|---|---|---|---|")
                for rid, reward in recs:
                    val = f"${reward['value']}" if reward["value"] else "Discount"
                    lines.append(f"| {reward['name']} | {reward['points_cost']:,} | {reward['category'].replace('_', ' ').title()} | {val} |")
            else:
                lines.append("No matching informational reward options at the current synthetic balance.")
            lines.append("")
        lines.append("## Full Redemption Catalog\n")
        lines.append("| Reward | Points | Category | Value |")
        lines.append("|---|---|---|---|")
        for rid, r in REDEMPTION_CATALOG.items():
            val = f"${r['value']}" if r["value"] else "Discount"
            lines.append(f"| {r['name']} | {r['points_cost']:,} | {r['category'].replace('_', ' ').title()} | {val} |")
        return "\n".join(lines)

    def _tier_analysis(self, **kwargs) -> str:
        lines = _response_header(kwargs.get("persona")) + ["# Synthetic Tier Analysis\n"]
        lines.append("## Tier Structure\n")
        lines.append("| Tier | Min Spend | Multiplier | Key Perks |")
        lines.append("|---|---|---|---|")
        for tier, info in TIER_STRUCTURE.items():
            perks = "; ".join(info["perks"][:2])
            lines.append(f"| {tier.title()} | ${info['min_spend']:,.0f} | {info['points_multiplier']}x | {perks} |")
        lines.append("\n## Member Tier Progress\n")
        for mid, m in LOYALTY_MEMBERS.items():
            progress = _tier_progress(m)
            tier_info = TIER_STRUCTURE[m["tier"]]
            lines.append(f"### {m['name']} ({mid}) — {m['tier'].title()}\n")
            lines.append(f"- Spend YTD: ${m['total_spend_ytd']:,.0f}")
            lines.append(f"- Engagement Score: {m['engagement_score']}")
            if tier_info["next_tier"]:
                remaining = max(0, tier_info["spend_to_next"] - m["total_spend_ytd"])
                lines.append(f"- Progress to {tier_info['next_tier'].title()}: {progress}%")
                lines.append(f"- Spend Remaining: ${remaining:,.0f}")
            else:
                lines.append(f"- Status: Top Tier Achieved")
            lines.append("")
        return "\n".join(lines)

    # ── video turn 1 ──────────────────────────────────────────
    def _churn_risk_segments(self, **kwargs) -> str:
        total, at_risk, value, expiring = _program_figures()
        lines = _response_header(kwargs.get("persona"), "Marketing Leader") + ["# Churn Risk Segments\n"]
        lines.append(
            f"Analyzed {_count_k(total)} members - {at_risk:,} at risk with "
            f"{_millions(value)} in unredeemed points.\n"
        )
        lines.append("| Segment | Members | Churn Risk |")
        lines.append("|---|---|---|")
        for s in PROGRAM_SEGMENTS:
            lines.append(f"| {s['segment']} | {_count_k(s['members'])} | {s['churn_risk_pct']}% |")
        lines.append(
            f"\n**At-Risk Details:** {AT_RISK_SUMMARY['rule']}, "
            f"{int(AT_RISK_SUMMARY['unredeemed_points'] / 1000000)}M points ({_millions(value)}), "
            f"{_thousands(expiring)} expiring in 30 days"
        )
        lines.append(f"**Patterns:** {', '.join(AT_RISK_SUMMARY['patterns'])}\n")
        lines.append("**Next:** see the top individual at-risk members and their profiles?")
        return "\n".join(lines)

    # ── video turn 2 ──────────────────────────────────────────
    def _top_at_risk_members(self, **kwargs) -> str:
        focus = AT_RISK_MEMBERS[_resolve_at_risk(kwargs.get("member_id"))]
        annual = sum(m["annual_value"] for m in AT_RISK_MEMBERS.values())
        lines = _response_header(kwargs.get("persona"), "Marketing Leader") + ["# Top At-Risk Members\n"]
        lines.append(f"Top at-risk members ({_thousands(annual)} annual value):\n")
        lines.append("| Member | Tier | Points | Last Purchase |")
        lines.append("|---|---|---|---|")
        for mid, m in AT_RISK_MEMBERS.items():
            lines.append(f"| {m['name']} | {m['tier']} | {m['points_balance']:,} | {m['days_since_purchase']} days |")
        lines.append(
            f"\n**{focus['name']} Profile:** {focus['tier']} status, {focus['interests']}, "
            f"{_count_k(focus['points_expiring'])} points expiring in {focus['expiring_in_days']} days, "
            f"{focus['behavior']}"
        )
        lines.append(f"**Trigger Found:** {focus['trigger']}\n")
        lines.append("**Next:** create personalized win-back offers?")
        return "\n".join(lines)

    # ── video turn 3 ──────────────────────────────────────────
    def _winback_offers(self, **kwargs) -> str:
        focus = AT_RISK_MEMBERS[_resolve_at_risk(kwargs.get("member_id"))]
        lines = _response_header(kwargs.get("persona"), "Marketing Leader") + ["# Personalized Win-Back Offers (Drafts)\n"]
        lines.append(f"**{focus['name']}:** {focus['offer']}\n")
        lines.append("**By Segment:**\n")
        lines.append("| Segment | Members | Offer | Channel |")
        lines.append("|---|---|---|---|")
        for s in WINBACK_SEGMENTS:
            lines.append(f"| {s['segment']} | {s['members']:,} | {s['offer']} | {s['channel']} |")
        lines.append(
            f"\nOffers are drafts for your review; total {sum(s['members'] for s in WINBACK_SEGMENTS):,} "
            "at-risk members across 3 segments. No offer is issued until you approve and launch it.\n"
        )
        lines.append("**Next:** prepare the campaigns for launch?")
        return "\n".join(lines)

    # ── video turn 4 ──────────────────────────────────────────
    def _campaign_plan(self, **kwargs) -> str:
        p = _projection()
        lines = _response_header(kwargs.get("persona"), "Marketing Leader") + ["# Campaign Launch Plan — Ready to Launch\n"]
        lines.append("| Campaign | Members | Channel | Status |")
        lines.append("|---|---|---|---|")
        for s in WINBACK_SEGMENTS:
            lines.append(f"| {s['campaign']} | {s['members']:,} | {s['channel']} | Ready to launch (your approval) |")
        lines.append(
            f"\n**Expected {CAMPAIGN_PROJECTION['window_days']}-Day Results:** "
            f"{CAMPAIGN_PROJECTION['reengagement_pct']}% re-engagement, {_thousands(p['revenue'])} revenue, "
            f"{_thousands(p['liability'])} liability reduced, {_millions(p['ltv'])} LTV protected"
        )
        lines.append(
            f"**ROI:** ${p['cost']:,} cost -> ${p['revenue']:,} revenue ({p['roi']}:1)\n"
        )
        lines.append(
            f"Basis: {p['reached']:,} members reached x {CAMPAIGN_PROJECTION['reengagement_pct']}% = "
            f"{p['reengaged']:,} re-engaged x ${CAMPAIGN_PROJECTION['avg_order_value']} average order; "
            f"{int(CAMPAIGN_PROJECTION['points_redeemed'] / 1000000)}M points redeemed at $0.02.\n"
        )
        lines.append(
            "The campaigns are ready for you to launch in your marketing system; "
            "nothing has been sent and no member has been contacted.\n"
        )
        lines.append("**Next:** want program optimization recommendations?")
        return "\n".join(lines)

    # ── video turn 5 ──────────────────────────────────────────
    def _program_improvements(self, **kwargs) -> str:
        lines = _response_header(kwargs.get("persona"), "Marketing Leader") + ["# Program Improvements\n"]
        lines.append(f"{len(PROGRAM_IMPROVEMENTS)} high-impact program improvements:\n")
        lines.append("| Improvement | Impact | Priority |")
        lines.append("|---|---|---|")
        for i in PROGRAM_IMPROVEMENTS:
            lines.append(f"| {i['improvement']} | {i['impact']} | {i['priority']} |")
        lines.append(f"\n**Quick Win:** {QUICK_WIN}")
        lines.append(f"**Dynamic Expiry:** {DYNAMIC_EXPIRY}\n")
        lines.append("**Next:** generate a summary?")
        return "\n".join(lines)

    # ── video turn 6 ──────────────────────────────────────────
    def _campaign_summary(self, **kwargs) -> str:
        total, at_risk, value, expiring = _program_figures()
        p = _projection()
        lines = _response_header(kwargs.get("persona"), "Marketing Leader") + ["# Loyalty Optimization Summary\n"]
        lines.append("| Result | Value |")
        lines.append("|---|---|")
        lines.append(f"| Members analyzed | {_count_k(total)} |")
        lines.append(f"| At-risk identified | {_count_k(at_risk)} ({_millions(value)} points) |")
        lines.append(f"| Campaigns ready to launch | {len(WINBACK_SEGMENTS)} segments ({_count_k(p['reached'])} members) |")
        lines.append(f"| Expected revenue | ${p['revenue']:,} |")
        lines.append(f"| LTV protected | {_millions(p['ltv'])} |")
        lines.append(f"| ROI | {p['roi']}:1 |")
        lines.append(f"\n**Next:** {NEXT_STEPS}\n")
        lines.append(
            f"**Teams-ready recap (draft for you to post):** Targeting {_millions(value)} at-risk value "
            f"with campaigns projected to generate {_thousands(p['revenue'])} and protect "
            f"{_millions(p['ltv'])} LTV."
        )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    agent = CustomerLoyaltyRewardsAgent()
    for op in ["churn_risk_segments", "top_at_risk_members", "winback_offers",
               "campaign_plan", "program_improvements", "campaign_summary"]:
        print(agent.perform(operation=op))
        print("\n" + "=" * 80 + "\n")
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
