"""
Procurement Agent

Manages purchase requests, purchase orders, vendor comparisons, approval
routing, and spend analysis for organizational procurement workflows.

Where a real deployment would connect to ERP and procurement platforms,
this agent uses a synthetic data layer so it runs anywhere without credentials.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))

from basic_agent import BasicAgent

# ═══════════════════════════════════════════════════════════════
# RAPP AGENT MANIFEST
# ═══════════════════════════════════════════════════════════════
__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/procurement-agent",
    "version": "1.0.0",
    "display_name": "Procurement Agent",
    "description": "Procurement management for purchase requests, vendor comparison, approval routing, and spend analysis.",
    "author": "AIBAST",
    "tags": ["procurement", "purchasing", "vendor", "approval", "spend-analysis"],
    "category": "general",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ═══════════════════════════════════════════════════════════════
# SYNTHETIC DATA LAYER
# ═══════════════════════════════════════════════════════════════

_PURCHASE_REQUESTS = {
    "PR-5001": {"id": "PR-5001", "title": "Cloud Infrastructure Upgrade", "requester": "Sarah Chen", "department": "IT", "category": "Technology", "amount": 125000, "priority": "High", "status": "Pending Approval", "vendor_preferred": "AWS", "justification": "Current infrastructure at 92% capacity, scaling needed for Q1 growth", "budget_code": "IT-INFRA-2025"},
    "PR-5002": {"id": "PR-5002", "title": "Office Furniture - New Floor Build-Out", "requester": "Tom Rivera", "department": "Facilities", "category": "Office Supplies", "amount": 48500, "priority": "Medium", "status": "Vendor Selection", "vendor_preferred": "Steelcase", "justification": "5th floor build-out for 30 new employees starting Q2", "budget_code": "FAC-CAPEX-2025"},
    "PR-5003": {"id": "PR-5003", "title": "Annual Software License Renewal - Salesforce", "requester": "Mike Torres", "department": "Sales", "category": "Software", "amount": 215000, "priority": "High", "status": "Approved", "vendor_preferred": "Salesforce", "justification": "Annual enterprise license renewal, 200 seats", "budget_code": "SALES-SW-2025"},
    "PR-5004": {"id": "PR-5004", "title": "Employee Training Program - Leadership Development", "requester": "Lisa Park", "department": "HR", "category": "Professional Services", "amount": 35000, "priority": "Low", "status": "Draft", "vendor_preferred": "FranklinCovey", "justification": "Q2 leadership development program for 25 managers", "budget_code": "HR-TRAIN-2025"},
}

_VENDOR_CATALOG = {
    "VND-001": {"name": "AWS", "category": "Cloud Infrastructure", "contract_status": "Active", "tier": "Strategic", "rating": 4.7, "annual_spend": 890000, "payment_terms": "Net 30", "contact": "Enterprise Account Manager"},
    "VND-002": {"name": "Salesforce", "category": "CRM Software", "contract_status": "Active", "tier": "Strategic", "rating": 4.5, "annual_spend": 430000, "payment_terms": "Annual Prepay", "contact": "Customer Success Manager"},
    "VND-003": {"name": "Steelcase", "category": "Office Furniture", "contract_status": "Active", "tier": "Preferred", "rating": 4.3, "annual_spend": 125000, "payment_terms": "Net 45", "contact": "Account Representative"},
    "VND-004": {"name": "Herman Miller", "category": "Office Furniture", "contract_status": "Active", "tier": "Approved", "rating": 4.6, "annual_spend": 85000, "payment_terms": "Net 30", "contact": "Regional Sales"},
    "VND-005": {"name": "Azure", "category": "Cloud Infrastructure", "contract_status": "Active", "tier": "Strategic", "rating": 4.6, "annual_spend": 650000, "payment_terms": "Net 30", "contact": "Technical Account Manager"},
    "VND-006": {"name": "FranklinCovey", "category": "Training Services", "contract_status": "Active", "tier": "Approved", "rating": 4.2, "annual_spend": 45000, "payment_terms": "Net 30", "contact": "Program Director"},
}

_PURCHASE_ORDERS = {
    "PO-7001": {"id": "PO-7001", "source_pr": "PR-5003", "vendor": "Salesforce", "vendor_id": "VND-002", "amount": 215000, "terms": "Annual Prepay", "issue_status": "Issued", "receipt_status": "Not Received", "blocked_by": ""},
    "PO-7002": {"id": "PO-7002", "source_pr": "PR-5002", "vendor": "Steelcase", "vendor_id": "VND-003", "amount": 48500, "terms": "Net 45", "issue_status": "Draft", "receipt_status": "Not Received", "blocked_by": "PR-5002 is in Vendor Selection - vendor not yet selected"},
    "PO-7003": {"id": "PO-7003", "source_pr": "PR-5001", "vendor": "AWS", "vendor_id": "VND-001", "amount": 125000, "terms": "Net 30", "issue_status": "Draft", "receipt_status": "Not Received", "blocked_by": "PR-5001 is Pending Approval - CFO sign-off outstanding"},
}

_APPROVAL_THRESHOLDS = [
    {"max_amount": 5000, "approver": "Direct Manager", "sla_hours": 4},
    {"max_amount": 25000, "approver": "Department Head", "sla_hours": 8},
    {"max_amount": 100000, "approver": "VP Finance", "sla_hours": 24},
    {"max_amount": 500000, "approver": "CFO", "sla_hours": 48},
    {"max_amount": 999999999, "approver": "CEO + Board", "sla_hours": 120},
]

_SPEND_CATEGORIES = {
    "Technology": {"budget": 2500000, "spent_ytd": 1875000, "committed": 340000, "available": 285000, "trend": "+12% YoY"},
    "Software": {"budget": 800000, "spent_ytd": 645000, "committed": 215000, "available": -60000, "trend": "+18% YoY"},
    "Office Supplies": {"budget": 350000, "spent_ytd": 210000, "committed": 48500, "available": 91500, "trend": "-5% YoY"},
    "Professional Services": {"budget": 500000, "spent_ytd": 325000, "committed": 35000, "available": 140000, "trend": "+8% YoY"},
    "Travel": {"budget": 200000, "spent_ytd": 142000, "committed": 18000, "available": 40000, "trend": "-15% YoY"},
}


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _get_approval_level(amount):
    for threshold in _APPROVAL_THRESHOLDS:
        if amount <= threshold["max_amount"]:
            return threshold
    return _APPROVAL_THRESHOLDS[-1]


def _orders_for_request(req_id):
    return [o for o in _PURCHASE_ORDERS.values() if o["source_pr"] == req_id]


def _find_competing_vendors(category):
    return [v for v in _VENDOR_CATALOG.values() if category.lower() in v["category"].lower()]


def _total_spend_summary():
    total_budget = sum(c["budget"] for c in _SPEND_CATEGORIES.values())
    total_spent = sum(c["spent_ytd"] for c in _SPEND_CATEGORIES.values())
    total_committed = sum(c["committed"] for c in _SPEND_CATEGORIES.values())
    return total_budget, total_spent, total_committed


# ═══════════════════════════════════════════════════════════════
# AGENT CLASS
# ═══════════════════════════════════════════════════════════════

class ProcurementAgent(BasicAgent):
    """
    Procurement management agent.

    Operations:
        purchase_request   - create and view purchase requests
        purchase_order     - draft and track purchase orders against requests
        vendor_comparison  - compare vendors for a category
        approval_routing   - determine approval path for a request
        spend_analysis     - analyze spend by category and budget
    """

    def __init__(self):
        self.name = "ProcurementAgent"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "purchase_request", "purchase_order",
                            "vendor_comparison", "approval_routing",
                            "spend_analysis",
                        ],
                        "description": "The procurement operation to perform",
                    },
                    "request_id": {
                        "type": "string",
                        "description": "Purchase request ID (e.g. 'PR-5001')",
                    },
                    "order_id": {
                        "type": "string",
                        "description": "Purchase order ID (e.g. 'PO-7001')",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation", "purchase_request")
        dispatch = {
            "purchase_request": self._purchase_request,
            "purchase_order": self._purchase_order,
            "vendor_comparison": self._vendor_comparison,
            "approval_routing": self._approval_routing,
            "spend_analysis": self._spend_analysis,
        }
        handler = dispatch.get(op)
        if not handler:
            return f"Unknown operation: {op}"
        return handler(kwargs)

    # ── purchase_request ───────────────────────────────────────
    def _purchase_request(self, params):
        req_id = params.get("request_id", "PR-5001")
        if req_id in _PURCHASE_REQUESTS:
            pr = _PURCHASE_REQUESTS[req_id]
            approval = _get_approval_level(pr["amount"])
            return (
                f"**Purchase Request: {pr['id']}**\n\n"
                f"| Field | Detail |\n|---|---|\n"
                f"| Title | {pr['title']} |\n"
                f"| Requester | {pr['requester']} ({pr['department']}) |\n"
                f"| Category | {pr['category']} |\n"
                f"| Amount | ${pr['amount']:,} |\n"
                f"| Priority | {pr['priority']} |\n"
                f"| Status | {pr['status']} |\n"
                f"| Preferred Vendor | {pr['vendor_preferred']} |\n"
                f"| Budget Code | {pr['budget_code']} |\n"
                f"| Required Approver | {approval['approver']} |\n\n"
                f"**Justification:** {pr['justification']}\n\n"
                f"Source: [Procurement System]\nAgents: ProcurementAgent"
            )
        rows = ""
        for pr in _PURCHASE_REQUESTS.values():
            rows += f"| {pr['id']} | {pr['title'][:35]} | ${pr['amount']:,} | {pr['status']} | {pr['priority']} |\n"
        return (
            f"**Purchase Requests**\n\n"
            f"| ID | Title | Amount | Status | Priority |\n|---|---|---|---|---|\n"
            f"{rows}\n\n"
            f"Source: [Procurement System]\nAgents: ProcurementAgent"
        )

    # ── purchase_order ─────────────────────────────────────────
    def _purchase_order(self, params):
        po_id = params.get("order_id")
        if not po_id:
            matches = _orders_for_request(params.get("request_id", ""))
            po_id = matches[0]["id"] if matches else None
        if po_id in _PURCHASE_ORDERS:
            po = _PURCHASE_ORDERS[po_id]
            pr = _PURCHASE_REQUESTS.get(po["source_pr"], {})
            cat = _SPEND_CATEGORIES.get(pr.get("category", ""), {})
            note = po["blocked_by"] or "None - the buyer has issued this order."
            flag = ""
            if cat and cat.get("available", 0) < 0:
                flag = (
                    f"\n**Budget flag:** {pr['category']} is over budget by "
                    f"${abs(cat['available']):,}; this order is inside that "
                    f"category's committed spend.\n"
                )
            return (
                f"**Purchase Order: {po['id']}**\n\n"
                f"| Field | Detail |\n|---|---|\n"
                f"| Source Request | {po['source_pr']} - {pr.get('title', 'unknown')} |\n"
                f"| Vendor | {po['vendor']} ({po['vendor_id']}) |\n"
                f"| Amount | ${po['amount']:,} |\n"
                f"| Payment Terms | {po['terms']} |\n"
                f"| Issue Status | {po['issue_status']} |\n"
                f"| Receipt Status | {po['receipt_status']} |\n\n"
                f"**Blocked by:** {note}\n"
                f"{flag}\n"
                f"Source: [Procurement System]\nAgents: ProcurementAgent"
            )
        rows = ""
        for po in _PURCHASE_ORDERS.values():
            rows += (
                f"| {po['id']} | {po['source_pr']} | {po['vendor']} "
                f"({po['vendor_id']}) | ${po['amount']:,} | {po['terms']} | "
                f"{po['issue_status']} | {po['receipt_status']} |\n"
            )
        no_po = [p["id"] for p in _PURCHASE_REQUESTS.values() if not _orders_for_request(p["id"])]
        tail = f"No purchase order drafted yet for: {', '.join(no_po)}.\n\n" if no_po else ""
        return (
            f"**Purchase Orders**\n\n"
            f"| ID | Source PR | Vendor | Amount | Terms | Issue Status | Receipt Status |\n"
            f"|---|---|---|---|---|---|---|\n"
            f"{rows}\n"
            f"{tail}"
            f"A person issues and receives every order; this view reports where\n"
            f"each one stands.\n\n"
            f"Source: [Procurement System]\nAgents: ProcurementAgent"
        )

    # ── vendor_comparison ──────────────────────────────────────
    def _vendor_comparison(self, params):
        rows = ""
        for vid, v in _VENDOR_CATALOG.items():
            rows += f"| {vid} | {v['name']} | {v['category']} | {v['tier']} | {v['rating']}/5 | ${v['annual_spend']:,} | {v['payment_terms']} |\n"
        return (
            f"**Vendor Comparison**\n\n"
            f"| ID | Vendor | Category | Tier | Rating | Annual Spend | Terms |\n|---|---|---|---|---|---|---|\n"
            f"{rows}\n"
            f"**Vendor Tiers:**\n"
            f"- Strategic: Long-term partners, best pricing, dedicated support\n"
            f"- Preferred: Competitive pricing, standard support, pre-approved\n"
            f"- Approved: Vetted and available, standard terms\n\n"
            f"Source: [Vendor Management System]\nAgents: ProcurementAgent"
        )

    # ── approval_routing ───────────────────────────────────────
    def _approval_routing(self, params):
        req_id = params.get("request_id", "PR-5001")
        pr = _PURCHASE_REQUESTS.get(req_id, list(_PURCHASE_REQUESTS.values())[0])
        approval = _get_approval_level(pr["amount"])
        threshold_rows = ""
        for t in _APPROVAL_THRESHOLDS:
            limit = f"${t['max_amount']:,}" if t["max_amount"] < 999999999 else "Unlimited"
            marker = " <-- This request" if t == approval else ""
            threshold_rows += f"| Up to {limit} | {t['approver']} | {t['sla_hours']}h |{marker}\n"
        return (
            f"**Approval Routing: {pr['id']}**\n\n"
            f"| Field | Detail |\n|---|---|\n"
            f"| Request | {pr['title']} |\n"
            f"| Amount | ${pr['amount']:,} |\n"
            f"| Required Approver | {approval['approver']} |\n"
            f"| Approval SLA | {approval['sla_hours']} hours |\n"
            f"| Current Status | {pr['status']} |\n\n"
            f"**Approval Thresholds:**\n\n"
            f"| Amount Limit | Approver | SLA |\n|---|---|---|\n"
            f"{threshold_rows}\n\n"
            f"Source: [Approval Workflow Engine]\nAgents: ProcurementAgent"
        )

    # ── spend_analysis ─────────────────────────────────────────
    def _spend_analysis(self, params):
        total_budget, total_spent, total_committed = _total_spend_summary()
        total_available = total_budget - total_spent - total_committed
        cat_rows = ""
        for cat, data in _SPEND_CATEGORIES.items():
            utilization = (data["spent_ytd"] + data["committed"]) / data["budget"] * 100
            status = "Over Budget" if data["available"] < 0 else ("At Risk" if utilization > 85 else "On Track")
            cat_rows += f"| {cat} | ${data['budget']:,} | ${data['spent_ytd']:,} | ${data['committed']:,} | ${data['available']:,} | {status} | {data['trend']} |\n"
        return (
            f"**Spend Analysis**\n\n"
            f"| Metric | Value |\n|---|---|\n"
            f"| Total Budget | ${total_budget:,} |\n"
            f"| Spent YTD | ${total_spent:,} ({total_spent/total_budget*100:.0f}%) |\n"
            f"| Committed | ${total_committed:,} |\n"
            f"| Available | ${total_available:,} |\n\n"
            f"**By Category:**\n\n"
            f"| Category | Budget | Spent YTD | Committed | Available | Status | Trend |\n|---|---|---|---|---|---|---|\n"
            f"{cat_rows}\n"
            f"**Alerts:**\n"
            f"- Software category over budget by $60,000 - requires reallocation\n"
            f"- Technology committed spend approaching budget limit\n\n"
            f"Source: [ERP + Finance System]\nAgents: ProcurementAgent"
        )


if __name__ == "__main__":
    agent = ProcurementAgent()
    for op in ["purchase_request", "purchase_order", "vendor_comparison", "approval_routing", "spend_analysis"]:
        print("=" * 60)
        print(agent.perform(operation=op, request_id="PR-5001"))
        print()
