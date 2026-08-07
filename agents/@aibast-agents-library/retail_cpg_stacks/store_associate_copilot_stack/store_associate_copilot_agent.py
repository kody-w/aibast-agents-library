"""
Store Associate Copilot Agent — Retail & CPG Stack

Empowers store associates with product lookup, customer assistance
scripts, daily task management, receipt and return-eligibility lookup,
and performance dashboards.
"""

import sys
import os
from datetime import date, timedelta

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"),
)
from basic_agent import BasicAgent

__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/store-associate-copilot",
    "version": "1.0.0",
    "display_name": "Store Associate Copilot Agent",
    "description": (
        "Provides store associates with instant product lookup, guided "
        "customer assistance scripts, daily task checklists, receipt and "
        "return-eligibility lookup, and real-time performance dashboards to "
        "improve in-store operations."
    ),
    "author": "AIBAST",
    "tags": [
        "store-operations",
        "associate",
        "copilot",
        "product-lookup",
        "transaction-support",
        "retail",
    ],
    "category": "retail_cpg",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}

# ---------------------------------------------------------------------------
# Synthetic Data — Product Catalog
# ---------------------------------------------------------------------------

PRODUCT_CATALOG = {
    "SKU-1001": {
        "name": "Classic Denim Jacket",
        "category": "Apparel",
        "brand": "Heritage Line",
        "retail_price": 89.99,
        "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
        "colors": ["Indigo Wash", "Light Blue", "Black"],
        "materials": "100% cotton denim, brass buttons",
        "care": "Machine wash cold, tumble dry low",
        "location_aisle": "A3",
        "location_shelf": "Top rack",
        "on_hand": 74,
        "upc": "0-12345-67890-1",
        "features": ["Adjustable waist tabs", "Two chest pockets", "Vintage fade finish"],
    },
    "SKU-1002": {
        "name": "Wireless Earbuds Pro",
        "category": "Electronics",
        "brand": "SoundWave",
        "retail_price": 59.99,
        "sizes": ["One Size"],
        "colors": ["Matte Black", "Pearl White", "Navy"],
        "materials": "ABS plastic, silicone ear tips",
        "care": "Wipe with dry cloth. Do not submerge.",
        "location_aisle": "E1",
        "location_shelf": "Locked case",
        "on_hand": 132,
        "upc": "0-12345-67890-2",
        "features": ["Active noise cancellation", "8-hour battery", "IPX4 water resistant", "Bluetooth 5.3"],
    },
    "SKU-1003": {
        "name": "Organic Cotton T-Shirt",
        "category": "Apparel",
        "brand": "EcoBasics",
        "retail_price": 29.99,
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["White", "Heather Grey", "Black", "Sage Green", "Dusty Rose"],
        "materials": "100% GOTS-certified organic cotton",
        "care": "Machine wash cold with like colors",
        "location_aisle": "A1",
        "location_shelf": "Mid rack",
        "on_hand": 210,
        "upc": "0-12345-67890-3",
        "features": ["Pre-shrunk", "Tagless comfort label", "Reinforced shoulder seams"],
    },
    "SKU-1004": {
        "name": "Smart Fitness Tracker",
        "category": "Electronics",
        "brand": "FitPulse",
        "retail_price": 129.99,
        "sizes": ["S/M Band", "L/XL Band"],
        "colors": ["Midnight Black", "Arctic White", "Forest Green"],
        "materials": "Aluminum case, fluoroelastomer band",
        "care": "Rinse with fresh water after swimming",
        "location_aisle": "E2",
        "location_shelf": "Display stand",
        "on_hand": 45,
        "upc": "0-12345-67890-4",
        "features": ["Heart rate monitor", "GPS tracking", "Sleep analysis", "7-day battery", "5ATM water resistant"],
    },
    "SKU-1005": {
        "name": "Premium Running Shoes",
        "category": "Footwear",
        "brand": "StrideMax",
        "retail_price": 149.99,
        "sizes": ["7", "7.5", "8", "8.5", "9", "9.5", "10", "10.5", "11", "12", "13"],
        "colors": ["Cloud White/Grey", "Black/Volt", "Navy/Orange"],
        "materials": "Engineered mesh upper, EVA foam midsole, rubber outsole",
        "care": "Spot clean with damp cloth. Air dry only.",
        "location_aisle": "F1",
        "location_shelf": "Wall display",
        "on_hand": 38,
        "upc": "0-12345-67890-5",
        "features": ["Responsive cushioning", "Breathable knit upper", "Reflective accents", "Carbon fiber plate"],
    },
    "SKU-1006": {
        "name": "Stainless Water Bottle",
        "category": "Accessories",
        "brand": "HydroKeep",
        "retail_price": 24.99,
        "sizes": ["20oz", "32oz"],
        "colors": ["Brushed Steel", "Matte Black", "Ocean Blue", "Coral"],
        "materials": "18/8 stainless steel, BPA-free lid",
        "care": "Hand wash recommended. Dishwasher safe (top rack).",
        "location_aisle": "C2",
        "location_shelf": "End cap",
        "on_hand": 195,
        "upc": "0-12345-67890-6",
        "features": ["Double-wall vacuum insulation", "24h cold / 12h hot", "Leak-proof lid", "Wide mouth"],
    },
    "SKU-1007": {
        "name": "Leather Crossbody Bag",
        "category": "Accessories",
        "brand": "UrbanCraft",
        "retail_price": 79.99,
        "sizes": ["One Size"],
        "colors": ["Cognac", "Black", "Olive"],
        "materials": "Full-grain leather, brass hardware",
        "care": "Condition with leather balm quarterly",
        "location_aisle": "B2",
        "location_shelf": "Display hooks",
        "on_hand": 61,
        "upc": "0-12345-67890-7",
        "features": ["Adjustable strap", "RFID-blocking pocket", "Three compartments", "YKK zippers"],
    },
    "SKU-1008": {
        "name": "UV Protection Sunglasses",
        "category": "Accessories",
        "brand": "ClearView",
        "retail_price": 44.99,
        "sizes": ["Standard", "Wide"],
        "colors": ["Tortoise", "Matte Black", "Crystal Clear"],
        "materials": "Acetate frame, polarized CR-39 lenses",
        "care": "Clean with included microfiber cloth. Store in case.",
        "location_aisle": "B1",
        "location_shelf": "Rotating display",
        "on_hand": 88,
        "upc": "0-12345-67890-8",
        "features": ["100% UV400 protection", "Polarized lenses", "Spring hinges", "Scratch-resistant coating"],
    },
    "SKU-1009": {
        "name": "Performance Yoga Mat",
        "category": "Fitness",
        "brand": "ZenGrip",
        "retail_price": 54.99,
        "sizes": ["68x24 in", "72x26 in"],
        "colors": ["Midnight Purple", "Sage", "Charcoal"],
        "materials": "Natural rubber base, polyurethane top layer",
        "care": "Wipe with damp cloth after use. Air dry flat.",
        "location_aisle": "F2",
        "location_shelf": "Standing rack",
        "on_hand": 42,
        "upc": "0-12345-67890-9",
        "features": ["Non-slip grip", "6mm thickness", "Alignment lines", "Carrying strap included"],
    },
    "SKU-1010": {
        "name": "Aromatherapy Candle Set",
        "category": "Home",
        "brand": "Luminary",
        "retail_price": 34.99,
        "sizes": ["3-pack (4oz each)"],
        "colors": ["Lavender/Eucalyptus/Vanilla"],
        "materials": "Soy wax, cotton wicks, essential oils",
        "care": "Trim wick to 1/4 inch before lighting. Burn max 4 hours.",
        "location_aisle": "D1",
        "location_shelf": "Feature table",
        "on_hand": 67,
        "upc": "0-12345-67891-0",
        "features": ["Clean-burning soy wax", "40-hour burn time per candle", "Reusable glass jars", "No synthetic fragrances"],
    },
}

CUSTOMER_INTERACTION_SCRIPTS = {
    "greeting": {
        "scenario": "Customer enters the store",
        "script": "Welcome to our store! Is there anything specific I can help you find today?",
        "follow_up": "If they mention a product category, guide them to the correct aisle.",
        "tips": ["Make eye contact", "Smile genuinely", "Keep a comfortable distance"],
    },
    "upsell": {
        "scenario": "Customer is ready to purchase a single item",
        "script": "Great choice! Did you know that pairs perfectly with our {complementary_product}? Many customers love the combination.",
        "follow_up": "If interested, walk them to the complementary item. If not, respect their decision.",
        "tips": ["Suggest only relevant items", "Limit to one upsell attempt", "Focus on value not price"],
    },
    "complaint_handling": {
        "scenario": "Customer has a complaint or issue",
        "script": "I am sorry to hear about that. Let me make sure I understand the issue so I can help resolve it right away.",
        "follow_up": "Listen fully, repeat back the issue, offer a concrete solution within your authority.",
        "tips": ["Never argue", "Acknowledge their frustration", "Offer alternatives if first solution is declined"],
    },
    "size_help": {
        "scenario": "Customer needs sizing assistance",
        "script": "I would be happy to help you find the right fit. What size do you typically wear in this type of item?",
        "follow_up": "Check fitting room availability. Bring two sizes if customer is between sizes.",
        "tips": ["Be sensitive about sizing", "Suggest trying multiple sizes", "Check stock for requested size first"],
    },
    "return_at_counter": {
        "scenario": "Customer wants to make a return at the register",
        "script": "Of course, I can help with that. Do you have your receipt or order confirmation?",
        "follow_up": "Verify return eligibility per policy. Process efficiently and offer exchange if applicable.",
        "tips": ["Stay positive and empathetic", "Explain policy clearly", "Thank them regardless of outcome"],
    },
}

DAILY_TASK_LIST = {
    "opening": [
        {"task": "Unlock entrance doors and disable alarm", "priority": "critical", "est_minutes": 2},
        {"task": "Power on POS terminals and verify connectivity", "priority": "critical", "est_minutes": 5},
        {"task": "Walk floor to check overnight display condition", "priority": "high", "est_minutes": 10},
        {"task": "Restock fitting rooms with hangers", "priority": "medium", "est_minutes": 5},
        {"task": "Review daily promotions and update signage", "priority": "high", "est_minutes": 15},
        {"task": "Check inventory alerts and pull items for floor replenishment", "priority": "high", "est_minutes": 20},
    ],
    "midday": [
        {"task": "Restock high-traffic areas and end caps", "priority": "high", "est_minutes": 20},
        {"task": "Process online pickup orders (BOPIS)", "priority": "critical", "est_minutes": 15},
        {"task": "Clean fitting rooms and return abandoned items", "priority": "medium", "est_minutes": 10},
        {"task": "Rotate break schedule for floor coverage", "priority": "high", "est_minutes": 5},
        {"task": "Check and respond to customer service queue", "priority": "high", "est_minutes": 10},
    ],
    "closing": [
        {"task": "Process remaining BOPIS orders for next-day pickup", "priority": "critical", "est_minutes": 15},
        {"task": "Reconcile POS drawers and prepare deposit", "priority": "critical", "est_minutes": 20},
        {"task": "Tidy all displays and return misplaced merchandise", "priority": "high", "est_minutes": 25},
        {"task": "Vacuum high-traffic aisles", "priority": "medium", "est_minutes": 15},
        {"task": "Set alarm and lock all entrances", "priority": "critical", "est_minutes": 3},
    ],
}

ASSOCIATE_PERFORMANCE = {
    "ASC-101": {
        "name": "Taylor Brooks",
        "role": "Senior Associate",
        "shift": "opening",
        "units_sold_today": 23,
        "revenue_today": 1847.50,
        "transactions_today": 14,
        "avg_basket": 131.96,
        "upsell_rate": 0.35,
        "csat_score": 4.8,
        "tasks_completed": 11,
        "tasks_total": 12,
        "hours_this_week": 32.5,
    },
    "ASC-102": {
        "name": "Jordan Kim",
        "role": "Associate",
        "shift": "midday",
        "units_sold_today": 17,
        "revenue_today": 1295.80,
        "transactions_today": 11,
        "avg_basket": 117.80,
        "upsell_rate": 0.22,
        "csat_score": 4.5,
        "tasks_completed": 8,
        "tasks_total": 10,
        "hours_this_week": 28.0,
    },
    "ASC-103": {
        "name": "Morgan Lee",
        "role": "Associate",
        "shift": "closing",
        "units_sold_today": 12,
        "revenue_today": 985.40,
        "transactions_today": 9,
        "avg_basket": 109.49,
        "upsell_rate": 0.18,
        "csat_score": 4.3,
        "tasks_completed": 7,
        "tasks_total": 9,
        "hours_this_week": 24.0,
    },
    "ASC-104": {
        "name": "Casey Rivera",
        "role": "Lead Associate",
        "shift": "opening",
        "units_sold_today": 29,
        "revenue_today": 2410.30,
        "transactions_today": 18,
        "avg_basket": 133.91,
        "upsell_rate": 0.40,
        "csat_score": 4.9,
        "tasks_completed": 12,
        "tasks_total": 12,
        "hours_this_week": 36.0,
    },
}

COMPLEMENTARY_PRODUCTS = {
    "SKU-1001": ["SKU-1003", "SKU-1008"],
    "SKU-1002": ["SKU-1004", "SKU-1006"],
    "SKU-1003": ["SKU-1001", "SKU-1008"],
    "SKU-1004": ["SKU-1005", "SKU-1009"],
    "SKU-1005": ["SKU-1006", "SKU-1009"],
    "SKU-1006": ["SKU-1009", "SKU-1005"],
    "SKU-1007": ["SKU-1008", "SKU-1001"],
    "SKU-1008": ["SKU-1007", "SKU-1001"],
    "SKU-1009": ["SKU-1006", "SKU-1004"],
    "SKU-1010": ["SKU-1009", "SKU-1006"],
}

# ---------------------------------------------------------------------------
# Synthetic Data — Receipt Archive (transaction support)
# ---------------------------------------------------------------------------
#
# Fixed demo business date. Every return-window figure is measured against it so
# the answers stay reproducible. The archive is a lookup sample of eight prior
# orders — it is NOT the store transaction log and does not reconcile with the
# 52 transactions on today's performance dashboard.

STORE_BUSINESS_DATE = "2026-07-24"

# Return window by product category, in days. Policy of record for this store.
RETURN_WINDOW_DAYS = {
    "Apparel": 30,
    "Footwear": 30,
    "Accessories": 30,
    "Fitness": 30,
    "Home": 30,
    "Electronics": 15,
}

ORDER_HISTORY = {
    "ORD-5001": {
        "order_date": "2026-07-22",
        "sku_id": "SKU-1005",
        "quantity": 1,
        "unit_price_paid": 149.99,
        "promo": None,
        "tender": "Credit Card",
        "channel": "In-store",
        "associate_id": "ASC-101",
        "status": "Completed",
        "window_start": "2026-07-22",
    },
    "ORD-5002": {
        "order_date": "2026-07-05",
        "sku_id": "SKU-1002",
        "quantity": 1,
        "unit_price_paid": 59.99,
        "promo": None,
        "tender": "Debit Card",
        "channel": "Online pickup (BOPIS)",
        "associate_id": "ASC-102",
        "status": "Completed",
        "window_start": "2026-07-05",
    },
    "ORD-5003": {
        "order_date": "2026-06-28",
        "sku_id": "SKU-1001",
        "quantity": 1,
        "unit_price_paid": 89.99,
        "promo": None,
        "tender": "Cash",
        "channel": "In-store",
        "associate_id": "ASC-103",
        "status": "Completed",
        "window_start": "2026-06-28",
    },
    "ORD-5004": {
        "order_date": "2026-07-19",
        "sku_id": "SKU-1003",
        "quantity": 2,
        "unit_price_paid": 23.99,
        "promo": "Summer Basics promotion, $6.00 off each",
        "tender": "Credit Card",
        "channel": "In-store",
        "associate_id": "ASC-101",
        "status": "Completed",
        "window_start": "2026-07-19",
    },
    "ORD-5005": {
        "order_date": "2026-07-23",
        "sku_id": "SKU-1004",
        "quantity": 1,
        "unit_price_paid": 129.99,
        "promo": None,
        "tender": "Gift Card",
        "channel": "Online pickup (BOPIS)",
        "associate_id": "ASC-104",
        "status": "Awaiting pickup",
        "window_start": None,
    },
    "ORD-5006": {
        "order_date": "2026-07-10",
        "sku_id": "SKU-1007",
        "quantity": 1,
        "unit_price_paid": 79.99,
        "promo": None,
        "tender": "Store Credit",
        "channel": "In-store",
        "associate_id": "ASC-102",
        "status": "Completed",
        "window_start": "2026-07-10",
    },
    "ORD-5007": {
        "order_date": "2026-06-15",
        "sku_id": "SKU-1009",
        "quantity": 1,
        "unit_price_paid": 54.99,
        "promo": None,
        "tender": "Credit Card",
        "channel": "In-store",
        "associate_id": "ASC-103",
        "status": "Completed",
        "window_start": "2026-06-15",
    },
    "ORD-5008": {
        "order_date": "2026-07-23",
        "sku_id": "SKU-1010",
        "quantity": 1,
        "unit_price_paid": 34.99,
        "promo": None,
        "tender": "Mobile Wallet",
        "channel": "Online pickup (BOPIS)",
        "associate_id": "ASC-104",
        "status": "Completed",
        "window_start": "2026-07-23",
    },
}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _search_products(query):
    """Search products by name, category, or SKU."""
    query_lower = query.lower()
    results = []
    for sku_id, prod in PRODUCT_CATALOG.items():
        if (query_lower in prod["name"].lower()
                or query_lower in prod["category"].lower()
                or query_lower in sku_id.lower()):
            results.append((sku_id, prod))
    return results


def _store_total_revenue():
    return sum(a["revenue_today"] for a in ASSOCIATE_PERFORMANCE.values())


def _store_total_transactions():
    return sum(a["transactions_today"] for a in ASSOCIATE_PERFORMANCE.values())


def _order_total(order):
    return round(order["quantity"] * order["unit_price_paid"], 2)


def _return_eligibility(order):
    """Return (status_label, detail) for an order's return window.

    Every figure is measured against STORE_BUSINESS_DATE, never the clock.
    """
    product = PRODUCT_CATALOG.get(order["sku_id"], {})
    window_days = RETURN_WINDOW_DAYS.get(product.get("category", ""), 30)
    if not order["window_start"]:
        return (
            "Not started",
            f"{window_days}-day window starts at pickup; this order is "
            f"{order['status'].lower()}",
        )
    today = date.fromisoformat(STORE_BUSINESS_DATE)
    start = date.fromisoformat(order["window_start"])
    expires = start + timedelta(days=window_days)
    days_left = (expires - today).days
    if days_left >= 0:
        return (
            "Eligible",
            f"{window_days}-day window closes {expires.isoformat()} "
            f"({days_left} days left)",
        )
    return (
        "Expired",
        f"{window_days}-day window closed {expires.isoformat()} "
        f"({abs(days_left)} days ago)",
    )


def _task_completion_rate(shift):
    tasks = DAILY_TASK_LIST.get(shift, [])
    total = len(tasks)
    # Simulate that critical and high tasks are done
    done = sum(1 for t in tasks if t["priority"] in ("critical", "high"))
    return round(done / total * 100, 1) if total > 0 else 0


# ---------------------------------------------------------------------------
# Agent Class
# ---------------------------------------------------------------------------

class StoreAssociateCopilotAgent(BasicAgent):
    """Copilot agent assisting store associates with daily operations."""

    def __init__(self):
        self.name = "store-associate-copilot-agent"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "product_lookup",
                            "customer_assist",
                            "task_checklist",
                            "transaction_support",
                            "performance_dashboard",
                        ],
                    },
                    "query": {"type": "string"},
                    "sku_id": {"type": "string"},
                    "scenario": {"type": "string"},
                    "shift": {"type": "string"},
                    "order_id": {"type": "string"},
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def _product_lookup(self, **kwargs):
        query = kwargs.get("query", "")
        sku_id = kwargs.get("sku_id", "")
        if sku_id and sku_id in PRODUCT_CATALOG:
            results = [(sku_id, PRODUCT_CATALOG[sku_id])]
        elif query:
            results = _search_products(query)
        else:
            results = list(PRODUCT_CATALOG.items())
        lines = ["# Product Lookup", ""]
        if not results:
            lines.append(f"No products found for query: \"{query}\"")
            return "\n".join(lines)
        for sid, prod in results:
            lines.append(f"## {prod['name']} (`{sid}`)")
            lines.append("")
            lines.append(f"- **Brand:** {prod['brand']}")
            lines.append(f"- **Category:** {prod['category']}")
            lines.append(f"- **Price:** ${prod['retail_price']:.2f}")
            lines.append(f"- **Sizes:** {', '.join(prod['sizes'])}")
            lines.append(f"- **Colors:** {', '.join(prod['colors'])}")
            lines.append(f"- **Materials:** {prod['materials']}")
            lines.append(f"- **Care:** {prod['care']}")
            lines.append(f"- **Location:** Aisle {prod['location_aisle']}, {prod['location_shelf']}")
            lines.append(f"- **In Stock:** {prod['on_hand']} units")
            lines.append(f"- **UPC:** {prod['upc']}")
            lines.append("")
            lines.append("**Key Features:**")
            for feat in prod["features"]:
                lines.append(f"  - {feat}")
            lines.append("")
            comp_skus = COMPLEMENTARY_PRODUCTS.get(sid, [])
            if comp_skus:
                comp_names = [PRODUCT_CATALOG[c]["name"] for c in comp_skus if c in PRODUCT_CATALOG]
                lines.append(f"**Pairs Well With:** {', '.join(comp_names)}")
            lines.append("")
        return "\n".join(lines)

    def _customer_assist(self, **kwargs):
        scenario = kwargs.get("scenario", "")
        if scenario and scenario in CUSTOMER_INTERACTION_SCRIPTS:
            scripts = {scenario: CUSTOMER_INTERACTION_SCRIPTS[scenario]}
        else:
            scripts = CUSTOMER_INTERACTION_SCRIPTS
        lines = ["# Customer Assistance Guide", ""]
        for scen_id, scr in scripts.items():
            lines.append(f"## {scen_id.replace('_', ' ').title()}")
            lines.append("")
            lines.append(f"**Scenario:** {scr['scenario']}")
            lines.append("")
            lines.append("**Suggested Script:**")
            lines.append(f"> {scr['script']}")
            lines.append("")
            lines.append(f"**Follow-Up:** {scr['follow_up']}")
            lines.append("")
            lines.append("**Tips:**")
            for tip in scr["tips"]:
                lines.append(f"- {tip}")
            lines.append("")
        return "\n".join(lines)

    def _task_checklist(self, **kwargs):
        shift = kwargs.get("shift", "")
        if shift and shift in DAILY_TASK_LIST:
            shifts = {shift: DAILY_TASK_LIST[shift]}
        else:
            shifts = DAILY_TASK_LIST
        lines = ["# Daily Task Checklist", ""]
        for shift_name, tasks in shifts.items():
            total_minutes = sum(t["est_minutes"] for t in tasks)
            comp_rate = _task_completion_rate(shift_name)
            lines.append(f"## {shift_name.title()} Shift")
            lines.append(f"**Estimated Time:** {total_minutes} min | **Completion:** {comp_rate}%")
            lines.append("")
            lines.append("| # | Task | Priority | Est. Time |")
            lines.append("|---|------|----------|-----------|")
            for i, task in enumerate(tasks, 1):
                lines.append(f"| {i} | {task['task']} | {task['priority'].upper()} | {task['est_minutes']} min |")
            lines.append("")
        return "\n".join(lines)

    def _transaction_support(self, **kwargs):
        order_id = kwargs.get("order_id", "")
        sku_id = kwargs.get("sku_id", "")
        if order_id and order_id in ORDER_HISTORY:
            orders = [(order_id, ORDER_HISTORY[order_id])]
        elif order_id:
            return (
                "# Transaction Support\n\n"
                f"Order `{order_id}` is not in the receipt archive, which holds "
                "8 orders from ORD-5001 to ORD-5008. No purchase, price, tender, "
                "or return window can be confirmed for it. Ask the customer for "
                "another order id or receipt, or hand the return to a lead."
            )
        elif sku_id:
            orders = [(o, r) for o, r in ORDER_HISTORY.items() if r["sku_id"] == sku_id]
            if not orders:
                return (
                    "# Transaction Support\n\n"
                    f"No archived order references `{sku_id}`."
                )
        else:
            orders = list(ORDER_HISTORY.items())
        lines = [
            "# Transaction Support",
            "",
            f"**Business date:** {STORE_BUSINESS_DATE} - every return window is "
            "measured against this date.",
            "",
        ]
        for oid, order in orders:
            product = PRODUCT_CATALOG.get(order["sku_id"], {})
            total = _order_total(order)
            status_label, detail = _return_eligibility(order)
            lines.append(f"## {oid} - {product.get('name', order['sku_id'])}")
            lines.append("")
            lines.append(f"- **Purchased:** {order['order_date']} ({order['channel']})")
            lines.append(f"- **Item:** {product.get('name', 'unknown')} (`{order['sku_id']}`), {product.get('category', 'unknown')}")
            lines.append(f"- **Quantity:** {order['quantity']}")
            lines.append(f"- **Price Paid:** ${order['unit_price_paid']:.2f} each | **Order Total:** ${total:,.2f}")
            if product:
                lines.append(f"- **Current Retail:** ${product['retail_price']:.2f}")
            if order["promo"]:
                lines.append(f"- **Promotion Applied:** {order['promo']}")
            lines.append(f"- **Tender:** {order['tender']}")
            lines.append(f"- **Order Status:** {order['status']}")
            lines.append(f"- **Rung By:** {order['associate_id']}")
            lines.append(f"- **Return Eligibility:** {status_label} - {detail}")
            lines.append("")
        lines.append(
            "Eligibility is a policy read against the archived record, not a "
            "processed return. Refunds go back to the original tender and are "
            "rung by an associate at the register."
        )
        return "\n".join(lines)

    def _performance_dashboard(self, **kwargs):
        total_rev = _store_total_revenue()
        total_txn = _store_total_transactions()
        lines = [
            "# Associate Performance Dashboard",
            "",
            f"**Store Total Revenue Today:** ${total_rev:,.2f}",
            f"**Store Total Transactions:** {total_txn}",
            f"**Store Avg Basket:** ${total_rev / total_txn:.2f}" if total_txn > 0 else "",
            "",
            "| Associate | Role | Shift | Revenue | Units | Txns | Basket | Upsell | CSAT | Tasks |",
            "|-----------|------|-------|---------|-------|------|--------|--------|------|-------|",
        ]
        for asc_id, asc in ASSOCIATE_PERFORMANCE.items():
            task_pct = round(asc["tasks_completed"] / asc["tasks_total"] * 100) if asc["tasks_total"] > 0 else 0
            lines.append(
                f"| {asc['name']} | {asc['role']} | {asc['shift']} "
                f"| ${asc['revenue_today']:,.2f} | {asc['units_sold_today']} "
                f"| {asc['transactions_today']} | ${asc['avg_basket']:.2f} "
                f"| {asc['upsell_rate']*100:.0f}% | {asc['csat_score']}/5.0 "
                f"| {asc['tasks_completed']}/{asc['tasks_total']} ({task_pct}%) |"
            )
        lines.append("")
        lines.append("## Top Performer Highlights")
        lines.append("")
        best_rev = max(ASSOCIATE_PERFORMANCE.values(), key=lambda a: a["revenue_today"])
        best_csat = max(ASSOCIATE_PERFORMANCE.values(), key=lambda a: a["csat_score"])
        best_upsell = max(ASSOCIATE_PERFORMANCE.values(), key=lambda a: a["upsell_rate"])
        lines.append(f"- **Highest Revenue:** {best_rev['name']} — ${best_rev['revenue_today']:,.2f}")
        lines.append(f"- **Best CSAT:** {best_csat['name']} — {best_csat['csat_score']}/5.0")
        lines.append(f"- **Top Upsell Rate:** {best_upsell['name']} — {best_upsell['upsell_rate']*100:.0f}%")
        return "\n".join(lines)

    def perform(self, **kwargs):
        operation = kwargs.get("operation", "product_lookup")
        dispatch = {
            "product_lookup": self._product_lookup,
            "customer_assist": self._customer_assist,
            "task_checklist": self._task_checklist,
            "transaction_support": self._transaction_support,
            "performance_dashboard": self._performance_dashboard,
        }
        handler = dispatch.get(operation)
        if not handler:
            return f"Unknown operation `{operation}`. Valid: {', '.join(dispatch.keys())}"
        return handler(**kwargs)


# ---------------------------------------------------------------------------
# Main — exercise all operations
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    agent = StoreAssociateCopilotAgent()
    print("=" * 80)
    print(agent.perform(operation="product_lookup", sku_id="SKU-1005"))
    print("\n" + "=" * 80)
    print(agent.perform(operation="customer_assist", scenario="upsell"))
    print("\n" + "=" * 80)
    print(agent.perform(operation="task_checklist", shift="opening"))
    print("\n" + "=" * 80)
    print(agent.perform(operation="transaction_support", order_id="ORD-5002"))
    print("\n" + "=" * 80)
    print(agent.perform(operation="performance_dashboard"))
    print("=" * 80)
