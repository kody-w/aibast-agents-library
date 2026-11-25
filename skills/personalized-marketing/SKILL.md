---
name: "personalized-marketing"
description: "Draft privacy-safe customer segment insights, multi-wave campaign plans, personalized content with A/B variants, automation workflows, revenue projections, and executive briefs for human review. Always use this tool for the holiday email campaign: 'analyze our customer segments and recommend the best approach' uses customer_segmentation; 'show me the personalized campaign recommendations' uses campaign_design; 'generate the VIP campaign with personalized content and A/B test variants' uses content_personalization; 'schedule the VIP wave and show me the automation workflow' uses campaign_workflow; 'revenue projection breakdown' uses revenue_projection; 'create the executive brief' uses executive_brief; past test results use performance_analysis. Every operation has demo defaults; call it without asking for details. Outputs are drafts: nothing is sent, scheduled, or issued."
compatibility: "Requires python3 (3.11+)."
metadata:
  source: "agent.py"
  file: "personalized_marketing_agent.py"
  tool-name: "personalized-marketing-agent"
  agent-sha256: "c4d163da8e0e85cf4e84398a16acf5cf16f0fb6d13d157c7c2460f46d1e49eb9"
  version: "1.0.0"
  author: "AIBAST"
  tags: "marketing, personalization, segmentation, campaigns, retail"
---

# Personalized Marketing

Draft privacy-safe customer segment insights, multi-wave campaign plans, personalized content with A/B variants, automation workflows, revenue projections, and executive briefs for human review. Always use this tool for the holiday email campaign: 'analyze our customer segments and recommend the best approach' uses customer_segmentation; 'show me the personalized campaign recommendations' uses campaign_design; 'generate the VIP campaign with personalized content and A/B test variants' uses content_personalization; 'schedule the VIP wave and show me the automation workflow' uses campaign_workflow; 'revenue projection breakdown' uses revenue_projection; 'create the executive brief' uses executive_brief; past test results use performance_analysis. Every operation has demo defaults; call it without asking for details. Outputs are drafts: nothing is sent, scheduled, or issued.

## What it needs

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "customer_segmentation",
        "campaign_design",
        "content_personalization",
        "performance_analysis",
        "campaign_workflow",
        "revenue_projection",
        "executive_brief"
      ],
      "description": "customer_segmentation: segments, sizes, avg order, open rate, holiday potential and recommended strategy. campaign_design: multi-wave campaign recommendations with themes and expected revenue. content_personalization: VIP creative with three A/B test variants (or hero copy for another segment). performance_analysis: past A/B test results and benchmarks. campaign_workflow: schedule the VIP wave (tomorrow 8:00 AM) and the 72-hour automation workflow, as a draft for approval. revenue_projection: conservative / expected / optimistic VIP revenue scenarios and ROI. executive_brief: executive summary of the whole campaign strategy and program economics."
    },
    "segment_id": {
      "type": "string",
      "description": "Optional segment: SEG-VIP, SEG-FREQUENT, SEG-SEASONAL, SEG-LAPSED or SEG-NEW (default VIP for content)"
    },
    "campaign_id": {
      "type": "string",
      "description": "Optional wave: WAVE-1 to WAVE-5 (default: the whole holiday plan)"
    },
    "persona": {
      "type": "string",
      "enum": [
        "Marketing Director",
        "Campaign Manager"
      ]
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
   python3 scripts/run.py --json '{"operation": "<string>", "segment_id": "<string>", "campaign_id": "<string>", "persona": "<string>", "data_source": "<string>"}'
   ```

2. Otherwise save the **code** block below as `agent.py` and the **launcher** block as
   `run.py` in one directory, then run `python3 run.py --json '...'` there.
3. If Python is unavailable, read the code block and do what its `perform`
   method does yourself; it is the exact description of this skill.

Return the printed output to the user as the result.

## The code

The code that does the work, unmodified from its source. Its sha256 is in the marker.

<!-- agent sha256=c4d163da8e0e85cf4e84398a16acf5cf16f0fb6d13d157c7c2460f46d1e49eb9 -->
```python
"""
Personalized Marketing Agent — Retail & CPG Stack

Drives customer segmentation, multi-wave campaign design, content
personalization with A/B variants, automation workflows, revenue projection,
and an executive brief for targeted retail marketing programs.

Demo scenario (the default): a holiday email promotion for 240K active
customers in five segments ($8.4M addressable), a five-wave plan led by VIP
Shoppers ($8.12M expected from a $47K investment), three VIP A/B variants,
a 72-hour automation workflow, and conservative / expected / optimistic VIP
revenue scenarios. Everything is a draft for approval: nothing is sent,
scheduled, or issued.
"""

import sys
import os

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"),
)
from basic_agent import BasicAgent

__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/personalized-marketing",
    "version": "1.0.0",
    "display_name": "Personalized Marketing Agent",
    "description": (
        "Draft privacy-safe customer segment insights, multi-wave campaign plans, personalized content with A/B variants, automation workflows, revenue projections, and executive briefs for human review."
    ),
    "author": "AIBAST",
    "tags": [
        "marketing",
        "personalization",
        "segmentation",
        "campaigns",
        "retail",
    ],
    "category": "retail_cpg",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}

# ---------------------------------------------------------------------------
# Synthetic Data — Customer Segments (aggregate, no personal attributes)
# holiday_potential = modeled holiday revenue potential for the segment
# ---------------------------------------------------------------------------

CUSTOMER_SEGMENTS = {
    "SEG-VIP": {
        "name": "VIP Shoppers",
        "short": "VIPs",
        "size": 12400,
        "avg_order": 340,
        "open_rate": 68,
        "conversion_rate": 12.4,
        "holiday_potential": 1480000,
        "top_categories": ["Premium Apparel", "Footwear", "Accessories"],
    },
    "SEG-FREQUENT": {
        "name": "Frequent Buyers",
        "short": "frequent buyers",
        "size": 38200,
        "avg_order": 185,
        "open_rate": 52,
        "conversion_rate": 9.6,
        "holiday_potential": 2260000,
        "top_categories": ["Apparel", "Home", "Beauty"],
    },
    "SEG-SEASONAL": {
        "name": "Seasonal Shoppers",
        "short": "seasonal shoppers",
        "size": 67800,
        "avg_order": 210,
        "open_rate": 44,
        "conversion_rate": 7.2,
        "holiday_potential": 2060000,
        "top_categories": ["Gifts", "Toys", "Electronics"],
    },
    "SEG-LAPSED": {
        "name": "Lapsed Customers",
        "short": "lapsed customers",
        "size": 84300,
        "avg_order": 165,
        "open_rate": 28,
        "conversion_rate": 3.1,
        "holiday_potential": 1320000,
        "top_categories": ["Home", "Electronics"],
    },
    "SEG-NEW": {
        "name": "New Subscribers",
        "short": "new subscribers",
        "size": 37300,
        "avg_order": 0,
        "open_rate": 71,
        "conversion_rate": 15.8,
        "holiday_potential": 1280000,
        "top_categories": ["Apparel", "Beauty", "Accessories"],
    },
}

# Multi-wave holiday plan. expected_revenue = predictive-model season revenue for the wave.
HOLIDAY_WAVES = {
    "WAVE-1": {
        "segment": "SEG-VIP",
        "day": 0,
        "day_label": "Launch Day",
        "theme": "Early Access - 30% Off Everything",
        "personalization": "Past purchase categories featured",
        "expected_revenue": 1420000,
    },
    "WAVE-2": {
        "segment": "SEG-FREQUENT",
        "day": 2,
        "day_label": "Day 2",
        "theme": "Your Favorites Are On Sale",
        "personalization": "AI-recommended products based on browsing",
        "expected_revenue": 2170000,
    },
    "WAVE-3": {
        "segment": "SEG-SEASONAL",
        "day": 5,
        "day_label": "Day 5",
        "theme": "Holiday Gifts - Free Shipping",
        "personalization": "Gift guides by top category",
        "expected_revenue": 1980000,
    },
    "WAVE-4": {
        "segment": "SEG-NEW",
        "day": 7,
        "day_label": "Day 7",
        "theme": "Welcome Gift - 40% Off First Purchase",
        "personalization": "Signup-preference categories",
        "expected_revenue": 1240000,
    },
    "WAVE-5": {
        "segment": "SEG-LAPSED",
        "day": 10,
        "day_label": "Day 10",
        "theme": "We Saved You a Gift - Free Shipping",
        "personalization": "Last purchased category",
        "expected_revenue": 1310000,
    },
}

CAMPAIGN_ECONOMICS = {
    "campaign": "Holiday Promotion",
    "investment": 47000,
    "investment_note": "creative + platform + labor",
    "personalization_lift_pct": 15.8,
}

VIP_VARIANTS = {
    "A": {
        "focus": "Product Focus",
        "hero_image": "Best-selling items from the customer's purchase history",
        "subject_line": "{FirstName}, Your Favorites Are 30% Off (VIP Early Access)",
        "cta": "Shop My Picks",
    },
    "B": {
        "focus": "Urgency Focus",
        "hero_image": "Countdown timer + exclusive badge",
        "subject_line": "24-Hour VIP Access Starts Now - 30% Off",
        "cta": "Activate My VIP Access",
    },
    "C": {
        "focus": "Rewards Focus",
        "hero_image": "Double points badge + tier benefits",
        "subject_line": "Earn 3X Points + 30% Off (VIP Exclusive)",
        "cta": "Claim VIP Rewards",
    },
}

AB_TEST_SETUP = {
    "campaign_name": "Early Access VIP - 30% Off Everything",
    "split": [33, 33, 34],
    "duration_hours": 12,
    "winner_metric": "open rate + revenue",
    "sample_first_name": "Sarah",
}

AUTOMATION_WORKFLOW = {
    "launch_label": "Tomorrow",
    "launch_hour": 8,
    "timezone": "PST",
    "follow_up_hours": 48,
    "steps": [
        {"hour": 0, "step": "Initial send with variant testing"},
        {"hour": 12, "step": "Winner declared, send winning variant to remaining audience"},
        {"hour": 24, "step": "Browse abandonment email (personalized products)"},
        {"hour": 48, "step": "Cart abandonment email (10% additional discount)"},
        {"hour": 72, "step": "Final call email (last chance messaging)"},
    ],
    "tracking": [
        "Real-time dashboard monitoring open/click/revenue",
        "Milestone alerts to the campaign channel",
        "Optimization recommendations based on early performance",
    ],
}

# VIP wave revenue scenarios. Rates are percentages; revenue = predictive-model season revenue.
REVENUE_SCENARIOS = [
    {"name": "Conservative (Baseline)", "open_rate": 68, "click_rate": 24, "conversion_rate": 12.4,
     "avg_order": 340, "avg_order_note": "", "revenue": 1420000},
    {"name": "Expected (Hit Benchmarks)", "open_rate": 72, "click_rate": 28, "conversion_rate": 14.2,
     "avg_order": 380, "avg_order_note": " (upsell success)", "revenue": 1780000},
    {"name": "Optimistic (Beat Benchmarks)", "open_rate": 78, "click_rate": 32, "conversion_rate": 16.8,
     "avg_order": 420, "avg_order_note": " (premium mix)", "revenue": 2110000},
]

AB_TEST_RESULTS = {
    "ABT-001": {
        "campaign": "Last year's VIP early access",
        "variant_a": {"subject": "VIP Only: private sale starts now", "open_rate": 0.58, "click_rate": 0.24, "conversions": 215},
        "variant_b": {"subject": "Your favorites, VIP early access", "open_rate": 0.64, "click_rate": 0.27, "conversions": 248},
        "winner": "B",
        "confidence": 0.94,
        "sample_size": 11800,
    },
    "ABT-002": {
        "campaign": "Last year's frequent-buyer sale",
        "variant_a": {"subject": "Your favorites are on sale", "open_rate": 0.49, "click_rate": 0.15, "conversions": 341},
        "variant_b": {"subject": "Holiday deals picked for you", "open_rate": 0.46, "click_rate": 0.13, "conversions": 298},
        "winner": "A",
        "confidence": 0.91,
        "sample_size": 36000,
    },
    "ABT-003": {
        "campaign": "Generic vs personalized holiday email",
        "variant_a": {"subject": "Holiday sale: shop now", "open_rate": 0.31, "click_rate": 0.08, "conversions": 190},
        "variant_b": {"subject": "Gifts picked from your favorite categories", "open_rate": 0.36, "click_rate": 0.10, "conversions": 220},
        "winner": "B",
        "confidence": 0.88,
        "sample_size": 24000,
    },
}

CONTENT_BLOCKS = {
    "hero_banner": {
        "SEG-VIP": {"headline": "VIP Early Access - 30% Off Everything", "cta": "Shop My Picks"},
        "SEG-FREQUENT": {"headline": "Your Favorites Are On Sale", "cta": "See My Favorites"},
        "SEG-SEASONAL": {"headline": "Holiday Gifts - Free Shipping", "cta": "Shop Gift Guides"},
        "SEG-LAPSED": {"headline": "We Saved You a Gift", "cta": "See What Is New"},
        "SEG-NEW": {"headline": "Welcome Gift - 40% Off First Purchase", "cta": "Start Shopping"},
    },
    "product_recs": {
        "SEG-VIP": ["Limited Edition Blazer", "Designer Handbag", "Artisan Watch"],
        "SEG-FREQUENT": ["Classic Denim Jacket", "Premium Running Shoes", "Cozy Throw Blanket"],
        "SEG-SEASONAL": ["Holiday Gift Set", "Wireless Earbuds Pro", "Board Game Bundle"],
        "SEG-LAPSED": ["Best Sellers Bundle", "Gift Card"],
        "SEG-NEW": ["Organic Cotton T-Shirt", "Stainless Water Bottle", "UV Protection Sunglasses"],
    },
}

APPROVED_PERSONAS = {
    "Marketing Director": "portfolio priorities, governance, and qualitative business value",
    "Campaign Manager": "review-ready campaign details, sequencing, and measurement",
}

SAFETY_NOTICE = (
    "> Synthetic aggregate planning data. Drafts and recommendations only; "
    "no audience is profiled with sensitive attributes, and no message, offer, "
    "campaign, reward, or purchase is created or sent."
)


def _response_header(persona):
    role = persona if persona in APPROVED_PERSONAS else "Marketing Director"
    return [
        f"**Prepared for:** {role}",
        f"**Role focus:** {APPROVED_PERSONAS[role]}",
        "",
        SAFETY_NOTICE,
        "",
    ]


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _millions(amount):
    """1420000 -> '$1.42M'; 8400000 -> '$8.4M'."""
    if amount % 100000 == 0:
        return f"${amount / 1000000:.1f}M"
    return f"${amount / 1000000:.2f}M"


def _total_customers():
    return sum(seg["size"] for seg in CUSTOMER_SEGMENTS.values())


def _total_addressable():
    return sum(seg["holiday_potential"] for seg in CUSTOMER_SEGMENTS.values())


def _total_wave_revenue():
    return sum(w["expected_revenue"] for w in HOLIDAY_WAVES.values())


def _roi(revenue):
    """Revenue to investment ratio, rounded to a whole number."""
    return int(revenue / CAMPAIGN_ECONOMICS["investment"] + 0.5)


def _scenario_funnel(scenario, audience):
    """Opens, clicks and orders from the audience and the scenario rates (rounded to whole people)."""
    opens = int(audience * scenario["open_rate"] / 100 + 0.5)
    clicks = int(opens * scenario["click_rate"] / 100 + 0.5)
    orders = int(clicks * scenario["conversion_rate"] / 100 + 0.5)
    return opens, clicks, orders


def _launch_time(hours_after):
    """Clock time of a workflow step on the 12-hour clock, e.g. 12 -> '8:00 PM'."""
    hour = (AUTOMATION_WORKFLOW["launch_hour"] + hours_after) % 24
    suffix = "AM" if hour < 12 else "PM"
    shown = hour % 12
    if shown == 0:
        shown = 12
    return f"{shown}:00 {suffix}"


# ---------------------------------------------------------------------------
# Agent Class
# ---------------------------------------------------------------------------

class PersonalizedMarketingAgent(BasicAgent):
    """Agent for personalized retail marketing orchestration."""

    def __init__(self):
        self.name = "personalized-marketing-agent"
        self.metadata = {
            "name": self.name,
            "description": (
                __manifest__["description"]
                + " Always use this tool for the holiday email campaign: 'analyze our customer segments "
                "and recommend the best approach' uses customer_segmentation; 'show me the personalized "
                "campaign recommendations' uses campaign_design; 'generate the VIP campaign with personalized "
                "content and A/B test variants' uses content_personalization; 'schedule the VIP wave and show "
                "me the automation workflow' uses campaign_workflow; 'revenue projection breakdown' uses "
                "revenue_projection; 'create the executive brief' uses executive_brief; past test results use "
                "performance_analysis. Every operation has demo defaults; call it without asking for details. "
                "Outputs are drafts: nothing is sent, scheduled, or issued."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "customer_segmentation",
                            "campaign_design",
                            "content_personalization",
                            "performance_analysis",
                            "campaign_workflow",
                            "revenue_projection",
                            "executive_brief",
                        ],
                        "description": (
                            "customer_segmentation: segments, sizes, avg order, open rate, holiday potential and "
                            "recommended strategy. campaign_design: multi-wave campaign recommendations with themes "
                            "and expected revenue. content_personalization: VIP creative with three A/B test "
                            "variants (or hero copy for another segment). performance_analysis: past A/B test "
                            "results and benchmarks. campaign_workflow: schedule the VIP wave (tomorrow 8:00 AM) and "
                            "the 72-hour automation workflow, as a draft for approval. revenue_projection: "
                            "conservative / expected / optimistic VIP revenue scenarios and ROI. executive_brief: "
                            "executive summary of the whole campaign strategy and program economics."
                        ),
                    },
                    "segment_id": {
                        "type": "string",
                        "description": "Optional segment: SEG-VIP, SEG-FREQUENT, SEG-SEASONAL, SEG-LAPSED or SEG-NEW (default VIP for content)",
                    },
                    "campaign_id": {
                        "type": "string",
                        "description": "Optional wave: WAVE-1 to WAVE-5 (default: the whole holiday plan)",
                    },
                    "persona": {
                        "type": "string",
                        "enum": list(APPROVED_PERSONAS),
                    },
                    "data_source": {"type": "string", "enum": ["synthetic"]},
                },
                "required": ["operation"],
                "additionalProperties": False,
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def _customer_segmentation(self, **kwargs):
        segment_id = kwargs.get("segment_id")
        if segment_id and segment_id not in CUSTOMER_SEGMENTS:
            return f"Unknown segment_id `{segment_id}`. Valid: {', '.join(CUSTOMER_SEGMENTS)}"
        segments = {segment_id: CUSTOMER_SEGMENTS[segment_id]} if segment_id else CUSTOMER_SEGMENTS
        total = _total_customers()
        lines = _response_header(kwargs.get("persona")) + [
            "# Customer Segmentation Overview",
            "",
            f"I've analyzed your {total // 1000}K active customers and identified "
            f"{len(CUSTOMER_SEGMENTS)} high-value segments for targeted holiday campaigns.",
            "",
            f"**Total Addressable Customers:** {total:,}",
            "",
            "| Segment | Size | Avg Order | Open Rate | Conversion |",
            "|---------|------|-----------|-----------|------------|",
        ]
        for seg in segments.values():
            lines.append(
                f"| {seg['name']} | {seg['size']:,} | ${seg['avg_order']} | {seg['open_rate']}% | {seg['conversion_rate']}% |"
            )
        top_value = None
        top_growth = None
        for seg in CUSTOMER_SEGMENTS.values():
            if top_value is None or seg["avg_order"] > top_value["avg_order"]:
                top_value = seg
            if top_growth is None or seg["conversion_rate"] > top_growth["conversion_rate"]:
                top_growth = seg
        lines += [
            "",
            "**Holiday Revenue Potential:**",
            f"- Total addressable: {_millions(_total_addressable())} across all segments",
            f"- Highest ROI: {top_value['name']} ({top_value['conversion_rate']}% conversion)",
            f"- Fastest growth: {top_growth['name']} ({top_growth['conversion_rate']}% conversion)",
            "",
            f"**Recommended Strategy:** Multi-wave campaign targeting {top_value['short']} first, "
            "then expanding to other segments.",
            "",
            "Source: [CRM Analytics + Purchase History + Email Platform]",
            "",
            "Next: want to see personalized campaign recommendations?",
        ]
        return "\n".join(lines)

    def _campaign_design(self, **kwargs):
        campaign_id = kwargs.get("campaign_id")
        if campaign_id and campaign_id not in HOLIDAY_WAVES:
            return f"Unknown campaign_id `{campaign_id}`. Valid: {', '.join(HOLIDAY_WAVES)}"
        waves = {campaign_id: HOLIDAY_WAVES[campaign_id]} if campaign_id else HOLIDAY_WAVES
        lines = _response_header(kwargs.get("persona")) + [
            "# Draft Campaign Design Portfolio",
            "",
            f"I've created {len(waves)} personalized campaign drafts optimized for each segment's behavior patterns.",
            "",
            "**Campaign Recommendations:**",
            "",
        ]
        for wid, wave in waves.items():
            seg = CUSTOMER_SEGMENTS[wave["segment"]]
            lines += [
                f"## {wid.replace('WAVE-', 'Wave ')}: {seg['name']} ({wave['day_label']})",
                "",
                f"- **Theme (proposed offer, not issued):** \"{wave['theme']}\"",
                f"- **Personalization:** {wave['personalization']}",
                f"- **Audience:** {seg['size']:,} ({seg['conversion_rate']}% conversion, ${seg['avg_order']} avg order)",
                f"- **Expected revenue:** {_millions(wave['expected_revenue'])}",
                "",
            ]
        total = sum(w["expected_revenue"] for w in waves.values())
        lines += [
            f"**Total Campaign Projection:** {_millions(total)} revenue from "
            f"${CAMPAIGN_ECONOMICS['investment'] // 1000}K campaign investment",
            "",
            "Source: [Predictive Analytics + Historical Performance]",
            "",
            "Next: generate the VIP campaign creative?",
        ]
        return "\n".join(lines)

    def _content_personalization(self, **kwargs):
        segment_id = kwargs.get("segment_id") or "SEG-VIP"
        if segment_id not in CUSTOMER_SEGMENTS:
            return f"Unknown segment_id `{segment_id}`. Valid: {', '.join(CUSTOMER_SEGMENTS)}"
        seg = CUSTOMER_SEGMENTS[segment_id]
        hero = CONTENT_BLOCKS["hero_banner"][segment_id]
        recs = CONTENT_BLOCKS["product_recs"][segment_id]
        lines = _response_header(kwargs.get("persona")) + ["# Draft Content Personalization Matrix", ""]
        if segment_id == "SEG-VIP":
            setup = AB_TEST_SETUP
            lines += [
                f"VIP campaign creative drafted with {len(VIP_VARIANTS)} A/B test variants optimized for engagement.",
                "",
                f"**Campaign:** \"{setup['campaign_name']}\"",
                "",
            ]
            for key, v in VIP_VARIANTS.items():
                lines += [
                    f"## Variant {key}: {v['focus']}",
                    "",
                    f"- Hero image: {v['hero_image']}",
                    f"- Subject line: \"{v['subject_line']}\"",
                    f"- CTA: \"{v['cta']}\"",
                    "",
                ]
            sample = VIP_VARIANTS["A"]["subject_line"].replace("{FirstName}", setup["sample_first_name"])
            lines += [
                f"Preview of Variant A for a sample VIP: \"{sample}\"",
                "",
                "**A/B Test Setup:**",
                f"- Split: {' / '.join(str(s) + '%' for s in setup['split'])}",
                f"- Duration: {setup['duration_hours']} hours",
                f"- Winner auto-selected by {setup['winner_metric']}",
                "",
            ]
        lines += [
            f"## {seg['name']} (`{segment_id}`)",
            "",
            "**Draft Hero Copy:**",
            f"- Headline: \"{hero['headline']}\"",
            f"- CTA: \"{hero['cta']}\"",
            "",
            "**Draft Product Ideas:**",
        ]
        for prod in recs:
            lines.append(f"- {prod}")
        lines += [
            "",
            f"**Top Categories:** {', '.join(seg['top_categories'])}",
            "",
            "Source: [Creative Engine + Testing Framework]",
            "",
            "Next: schedule the campaign launch?",
        ]
        return "\n".join(lines)

    def _performance_analysis(self, **kwargs):
        lines = _response_header(kwargs.get("persona")) + [
            "# Marketing Performance Analysis",
            "",
            "## A/B Test Results",
            "",
            "| Test | Campaign | Winner | Confidence | Sample | Lift |",
            "|------|----------|--------|------------|--------|------|",
        ]
        for test_id, test in AB_TEST_RESULTS.items():
            a_conv = test["variant_a"]["conversions"]
            b_conv = test["variant_b"]["conversions"]
            lift = round((max(a_conv, b_conv) - min(a_conv, b_conv)) * 100 / min(a_conv, b_conv), 1)
            lines.append(
                f"| {test_id} | {test['campaign']} | Variant {test['winner']} "
                f"| {test['confidence'] * 100:.0f}% | {test['sample_size']:,} | +{lift}% |"
            )
        lines += [
            "",
            "## Benchmarks Used for the Holiday Plan",
            "",
            "| Segment | Open Rate | Conversion | Avg Order |",
            "|---------|-----------|------------|-----------|",
        ]
        for seg in CUSTOMER_SEGMENTS.values():
            lines.append(f"| {seg['name']} | {seg['open_rate']}% | {seg['conversion_rate']}% | ${seg['avg_order']} |")
        lines += [
            "",
            f"**Personalization benchmark:** {CAMPAIGN_ECONOMICS['personalization_lift_pct']}% higher conversion "
            "than generic campaigns (synthetic benchmark).",
            "",
            "Measurement limitation: past tests are synthetic samples; confirm significance before any decision.",
        ]
        return "\n".join(lines)

    def _campaign_workflow(self, **kwargs):
        wf = AUTOMATION_WORKFLOW
        setup = AB_TEST_SETUP
        seg = CUSTOMER_SEGMENTS["SEG-VIP"]
        launch = _launch_time(0)
        winner = _launch_time(setup["duration_hours"])
        lines = _response_header(kwargs.get("persona")) + [
            "# Draft VIP Launch Schedule and Automation Workflow",
            "",
            f"VIP wave draft scheduled for {wf['launch_label'].lower()} {launch} with the full automation workflow, "
            "ready for you to approve. Nothing is scheduled or sent until you approve it in the marketing platform.",
            "",
            "**Scheduled Campaign (draft):**",
            f"- Launch: {wf['launch_label']} {launch} {wf['timezone']}",
            f"- Audience: {seg['size']:,} VIP customers",
            f"- A/B Test: {len(VIP_VARIANTS)} variants ({'/'.join(str(s) for s in setup['split'])} split)",
            f"- Winner Selection: Auto-select at {winner} ({setup['duration_hours']} hours)",
            f"- Follow-up: {wf['follow_up_hours']}-hour reminder if no purchase",
            "",
            "**Automation Workflow:**",
            "",
            "| Hour | Step |",
            "|------|------|",
        ]
        for s in wf["steps"]:
            lines.append(f"| Hour {s['hour']} | {s['step']} |")
        lines += ["", "**Performance Tracking:**"]
        for t in wf["tracking"]:
            lines.append(f"- {t}")
        lines += [
            "",
            "Source: [Marketing Automation + Campaign Scheduler]",
            "",
            "Next: want to see the revenue projection breakdown?",
        ]
        return "\n".join(lines)

    def _revenue_projection(self, **kwargs):
        audience = CUSTOMER_SEGMENTS["SEG-VIP"]["size"]
        base = REVENUE_SCENARIOS[0]["revenue"]
        top = REVENUE_SCENARIOS[-1]["revenue"]
        lines = _response_header(kwargs.get("persona")) + [
            "# VIP Revenue Projection Model",
            "",
            f"Revenue projections show {_millions(base)} baseline with {_millions(top)} upside if we beat benchmarks "
            f"(VIP wave, {audience:,} customers).",
            "",
        ]
        for sc in REVENUE_SCENARIOS:
            opens, clicks, orders = _scenario_funnel(sc, audience)
            lines += [
                f"## {sc['name']}",
                "",
                f"- Open rate: {sc['open_rate']}% ({opens:,} opens)",
                f"- Click rate: {sc['click_rate']}% ({clicks:,} clicks)",
                f"- Conversion: {sc['conversion_rate']}% ({orders:,} launch-email orders)",
                f"- Avg order: ${sc['avg_order']}{sc['avg_order_note']}",
                f"- Revenue (season model): {_millions(sc['revenue'])}",
                "",
            ]
        econ = CAMPAIGN_ECONOMICS
        lines += [
            f"**Campaign Investment:** ${econ['investment'] // 1000}K ({econ['investment_note']})",
            f"**ROI Range:** {_roi(base)}:1 (baseline) to {_roi(top)}:1 (optimistic)",
            "",
            "Scenarios are planning estimates, not forecasts or committed results.",
            "",
            "Source: [Predictive Models + Historical Data]",
            "",
            "Next: generate the executive campaign brief?",
        ]
        return "\n".join(lines)

    def _executive_brief(self, **kwargs):
        total = _total_customers()
        econ = CAMPAIGN_ECONOMICS
        vip = CUSTOMER_SEGMENTS["SEG-VIP"]
        waves = list(HOLIDAY_WAVES.values())
        base = REVENUE_SCENARIOS[0]["revenue"]
        expected = REVENUE_SCENARIOS[1]["revenue"]
        top = REVENUE_SCENARIOS[-1]["revenue"]
        program = _total_wave_revenue()
        lines = _response_header(kwargs.get("persona")) + [
            "# Executive Campaign Brief",
            "",
            f"Executive brief prepared. Here's the complete {econ['campaign'].lower()} strategy:",
            "",
            "**Campaign Strategy Summary:**",
            f"- Segment analysis - {total // 1000}K customers > {len(CUSTOMER_SEGMENTS)} targeted segments, "
            f"{_millions(_total_addressable())} revenue potential",
            f"- Multi-wave plan - {len(waves)} waves over {waves[-1]['day']} days, prioritizing VIPs "
            f"({vip['conversion_rate']}% conversion)",
            f"- Creative development - {len(VIP_VARIANTS)} A/B test variants with personalization",
            f"- Automation built - {AUTOMATION_WORKFLOW['steps'][-1]['hour']}-hour nurture workflow with browse/cart abandonment",
            f"- Revenue modeling - {_millions(base)} baseline to {_millions(top)} optimistic ({_millions(expected)} expected)",
            f"- Launch ready for approval - {AUTOMATION_WORKFLOW['launch_label']} {_launch_time(0)}, {vip['size']:,} VIP customers",
            "",
            "**Program Economics:**",
            f"- Total investment: ${econ['investment'] // 1000}K",
            f"- Expected total revenue: {_millions(program)} (all waves)",
            f"- Program ROI: {_roi(program)}:1",
            f"- VIP wave alone: {_roi(base)}-{_roi(top)}:1 ROI",
            "",
            f"**Competitive Advantage:** Personalization creates {econ['personalization_lift_pct']}% higher conversion "
            "vs generic campaigns (synthetic benchmark).",
            "",
            "The brief is a draft you can share with stakeholders (for example in Microsoft Teams); "
            "it has not been sent.",
            "",
            "Source: [All Connected Systems]",
        ]
        return "\n".join(lines)

    def perform(self, **kwargs):
        if kwargs.get("data_source", "synthetic") != "synthetic":
            return "data_source must be `synthetic` for this package."
        operation = kwargs.get("operation", "customer_segmentation")
        dispatch = {
            "customer_segmentation": self._customer_segmentation,
            "campaign_design": self._campaign_design,
            "content_personalization": self._content_personalization,
            "performance_analysis": self._performance_analysis,
            "campaign_workflow": self._campaign_workflow,
            "revenue_projection": self._revenue_projection,
            "executive_brief": self._executive_brief,
        }
        handler = dispatch.get(operation)
        if not handler:
            return f"Unknown operation `{operation}`. Valid: {', '.join(dispatch.keys())}"
        return handler(**kwargs)


# ---------------------------------------------------------------------------
# Main — the demo video's turns in order
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    agent = PersonalizedMarketingAgent()
    for op in ["customer_segmentation", "campaign_design", "content_personalization",
               "campaign_workflow", "revenue_projection", "executive_brief", "performance_analysis"]:
        print("=" * 80)
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
