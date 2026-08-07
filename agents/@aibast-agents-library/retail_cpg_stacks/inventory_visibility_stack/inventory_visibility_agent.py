"""
Inventory Visibility Agent — Retail & CPG Stack

Provides real-time inventory visibility across stores, warehouses, and channels.
Surfaces stock alerts, reviews overstock exposure, generates replenishment
plans, and optimizes channel allocation for omni-channel retail operations.
Dashboard, alert, and overstock views can be scoped to a merchandise category
for category managers.
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
    "name": "@aibast-agents-library/inventory-visibility",
    "version": "1.0.0",
    "display_name": "Inventory Visibility Agent",
    "description": (
        "Delivers real-time inventory dashboards, stock-out alerts, "
        "overstock review, replenishment planning, and channel allocation "
        "optimization for omni-channel retail and CPG operations, with "
        "category-level rollups for category managers."
    ),
    "author": "AIBAST",
    "tags": [
        "inventory",
        "stock-management",
        "replenishment",
        "overstock",
        "omni-channel",
        "retail",
    ],
    "category": "retail_cpg",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}

# ---------------------------------------------------------------------------
# Synthetic Data — Stores & Warehouses
# ---------------------------------------------------------------------------

STORES = {
    "STR-001": {
        "name": "Downtown Flagship",
        "city": "Chicago",
        "state": "IL",
        "type": "flagship",
        "capacity_sqft": 42000,
    },
    "STR-002": {
        "name": "Northshore Mall",
        "city": "Evanston",
        "state": "IL",
        "type": "mall",
        "capacity_sqft": 18500,
    },
    "STR-003": {
        "name": "Oakbrook Center",
        "city": "Oak Brook",
        "state": "IL",
        "type": "outlet",
        "capacity_sqft": 12000,
    },
    "STR-004": {
        "name": "Michigan Ave Express",
        "city": "Chicago",
        "state": "IL",
        "type": "express",
        "capacity_sqft": 6500,
    },
}

WAREHOUSES = {
    "WH-CENTRAL": {
        "name": "Central Distribution Center",
        "city": "Romeoville",
        "state": "IL",
        "capacity_pallets": 22000,
    },
    "WH-EAST": {
        "name": "East Regional Warehouse",
        "city": "Indianapolis",
        "state": "IN",
        "capacity_pallets": 14000,
    },
}

SKUS = {
    "SKU-1001": {"name": "Classic Denim Jacket", "category": "Apparel", "unit_cost": 34.50, "retail_price": 89.99},
    "SKU-1002": {"name": "Wireless Earbuds Pro", "category": "Electronics", "unit_cost": 18.75, "retail_price": 59.99},
    "SKU-1003": {"name": "Organic Cotton T-Shirt", "category": "Apparel", "unit_cost": 8.20, "retail_price": 29.99},
    "SKU-1004": {"name": "Smart Fitness Tracker", "category": "Electronics", "unit_cost": 42.00, "retail_price": 129.99},
    "SKU-1005": {"name": "Premium Running Shoes", "category": "Footwear", "unit_cost": 55.00, "retail_price": 149.99},
    "SKU-1006": {"name": "Stainless Water Bottle", "category": "Accessories", "unit_cost": 6.80, "retail_price": 24.99},
    "SKU-1007": {"name": "Leather Crossbody Bag", "category": "Accessories", "unit_cost": 27.50, "retail_price": 79.99},
    "SKU-1008": {"name": "UV Protection Sunglasses", "category": "Accessories", "unit_cost": 12.30, "retail_price": 44.99},
}

# Current on-hand quantities per location per SKU
INVENTORY = {
    "STR-001": {"SKU-1001": 74, "SKU-1002": 132, "SKU-1003": 210, "SKU-1004": 45, "SKU-1005": 38, "SKU-1006": 195, "SKU-1007": 61, "SKU-1008": 88},
    "STR-002": {"SKU-1001": 35, "SKU-1002": 67, "SKU-1003": 98, "SKU-1004": 22, "SKU-1005": 14, "SKU-1006": 110, "SKU-1007": 29, "SKU-1008": 53},
    "STR-003": {"SKU-1001": 18, "SKU-1002": 41, "SKU-1003": 65, "SKU-1004": 9, "SKU-1005": 7, "SKU-1006": 72, "SKU-1007": 15, "SKU-1008": 30},
    "STR-004": {"SKU-1001": 12, "SKU-1002": 28, "SKU-1003": 44, "SKU-1004": 6, "SKU-1005": 5, "SKU-1006": 55, "SKU-1007": 8, "SKU-1008": 19},
    "WH-CENTRAL": {"SKU-1001": 1450, "SKU-1002": 2300, "SKU-1003": 3800, "SKU-1004": 780, "SKU-1005": 620, "SKU-1006": 4100, "SKU-1007": 950, "SKU-1008": 1700},
    "WH-EAST": {"SKU-1001": 820, "SKU-1002": 1100, "SKU-1003": 2200, "SKU-1004": 410, "SKU-1005": 350, "SKU-1006": 2600, "SKU-1007": 530, "SKU-1008": 900},
}

SAFETY_STOCK = {
    "STR-001": {"SKU-1001": 30, "SKU-1002": 50, "SKU-1003": 80, "SKU-1004": 20, "SKU-1005": 15, "SKU-1006": 70, "SKU-1007": 25, "SKU-1008": 35},
    "STR-002": {"SKU-1001": 15, "SKU-1002": 30, "SKU-1003": 45, "SKU-1004": 10, "SKU-1005": 8, "SKU-1006": 40, "SKU-1007": 12, "SKU-1008": 20},
    "STR-003": {"SKU-1001": 10, "SKU-1002": 20, "SKU-1003": 30, "SKU-1004": 5, "SKU-1005": 5, "SKU-1006": 25, "SKU-1007": 8, "SKU-1008": 12},
    "STR-004": {"SKU-1001": 8, "SKU-1002": 15, "SKU-1003": 20, "SKU-1004": 4, "SKU-1005": 3, "SKU-1006": 20, "SKU-1007": 5, "SKU-1008": 10},
}

LEAD_TIMES_DAYS = {
    "WH-CENTRAL": {"STR-001": 1, "STR-002": 1, "STR-003": 2, "STR-004": 1},
    "WH-EAST": {"STR-001": 2, "STR-002": 2, "STR-003": 3, "STR-004": 2},
}

CHANNEL_DEMAND = {
    "in_store": {"weight": 0.45, "daily_units_avg": 320},
    "online_ship": {"weight": 0.30, "daily_units_avg": 215},
    "bopis": {"weight": 0.15, "daily_units_avg": 108},
    "marketplace": {"weight": 0.10, "daily_units_avg": 72},
}

DAILY_SELL_THROUGH = {
    "SKU-1001": 6.2, "SKU-1002": 9.8, "SKU-1003": 14.5, "SKU-1004": 3.1,
    "SKU-1005": 2.7, "SKU-1006": 12.0, "SKU-1007": 4.4, "SKU-1008": 7.3,
}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _total_network_inventory(sku_id):
    """Sum on-hand across all locations for a given SKU."""
    return sum(loc.get(sku_id, 0) for loc in INVENTORY.values())


def _days_of_supply(sku_id, location_id):
    """Estimate days-of-supply at a location."""
    on_hand = INVENTORY.get(location_id, {}).get(sku_id, 0)
    daily = DAILY_SELL_THROUGH.get(sku_id, 1.0)
    return round(on_hand / daily, 1) if daily > 0 else 999.0


def _stock_status(sku_id, location_id):
    """Return stock status label for a SKU at a location."""
    on_hand = INVENTORY.get(location_id, {}).get(sku_id, 0)
    safety = SAFETY_STOCK.get(location_id, {}).get(sku_id, 0)
    if on_hand == 0:
        return "OUT_OF_STOCK"
    if on_hand <= safety:
        return "CRITICAL"
    if on_hand <= safety * 1.5:
        return "LOW"
    return "HEALTHY"


def _categories():
    """Merchandise categories present in the SKU catalog, alphabetical."""
    return sorted({sku["category"] for sku in SKUS.values()})


def _resolve_category(raw):
    """Map a user-supplied category string to its catalog spelling, or None."""
    if not raw:
        return None
    wanted = str(raw).strip().lower()
    for category in _categories():
        if category.lower() == wanted:
            return category
    return None


def _skus_in_scope(category=None):
    """SKU ids in ascending id order, optionally restricted to one category."""
    if category is None:
        return sorted(SKUS.keys())
    return sorted(s for s in SKUS if SKUS[s]["category"] == category)


def _target_qty(sku_id, target_days=14):
    """Truncated N-day supply target for a SKU."""
    return int(DAILY_SELL_THROUGH.get(sku_id, 1.0) * target_days)


def _category_rollup(category, location_ids):
    """On-hand, sell-through, days of supply, and unit-cost value for a category."""
    sku_ids = _skus_in_scope(category)
    on_hand = sum(
        INVENTORY.get(loc, {}).get(sku_id, 0)
        for loc in location_ids
        for sku_id in sku_ids
    )
    daily = sum(DAILY_SELL_THROUGH.get(sku_id, 0.0) for sku_id in sku_ids)
    value = sum(
        INVENTORY.get(loc, {}).get(sku_id, 0) * SKUS[sku_id]["unit_cost"]
        for loc in location_ids
        for sku_id in sku_ids
    )
    return {
        "sku_ids": sku_ids,
        "on_hand": on_hand,
        "daily": round(daily, 1),
        "days_of_supply": round(on_hand / daily, 1) if daily > 0 else 999.0,
        "value": round(value, 2),
    }


def _overstock_position(sku_id, location_id, target_days=14):
    """Excess above the N-day target at a store, or None when at/below target."""
    on_hand = INVENTORY.get(location_id, {}).get(sku_id, 0)
    target = _target_qty(sku_id, target_days)
    if on_hand <= target:
        return None
    excess = on_hand - target
    daily = DAILY_SELL_THROUGH.get(sku_id, 1.0)
    return {
        "on_hand": on_hand,
        "target": target,
        "excess": excess,
        "days_over": round(excess / daily, 1) if daily > 0 else 999.0,
        "capital": round(excess * SKUS[sku_id]["unit_cost"], 2),
    }


def _replenishment_qty(sku_id, location_id, target_days=14):
    """Calculate replenishment quantity targeting N days of supply."""
    on_hand = INVENTORY.get(location_id, {}).get(sku_id, 0)
    needed = max(0, _target_qty(sku_id, target_days) - on_hand)
    return needed


def _channel_allocation_units(sku_id, total_available):
    """Allocate available inventory across channels by demand weight."""
    allocations = {}
    for channel, info in CHANNEL_DEMAND.items():
        allocations[channel] = int(total_available * info["weight"])
    remainder = total_available - sum(allocations.values())
    allocations["in_store"] += remainder
    return allocations


# ---------------------------------------------------------------------------
# Agent Class
# ---------------------------------------------------------------------------

class InventoryVisibilityAgent(BasicAgent):
    """Agent providing omni-channel inventory visibility and planning."""

    def __init__(self):
        self.name = "inventory-visibility-agent"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "inventory_dashboard",
                            "stock_alerts",
                            "overstock_review",
                            "replenishment_plan",
                            "channel_allocation",
                        ],
                    },
                    "sku_id": {"type": "string"},
                    "location_id": {"type": "string"},
                    "category": {
                        "type": "string",
                        "description": (
                            "Optional merchandise category scope for "
                            "inventory_dashboard, stock_alerts, and "
                            "overstock_review: Accessories, Apparel, "
                            "Electronics, or Footwear."
                        ),
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    # ---- operations -------------------------------------------------------

    def _unknown_category(self, raw):
        return (
            f"`{raw}` is not a merchandise category in the SKU catalog. "
            f"Valid categories: {', '.join(_categories())}."
        )

    def _inventory_dashboard(self, **kwargs):
        raw_category = kwargs.get("category")
        category = _resolve_category(raw_category)
        if raw_category and category is None:
            return self._unknown_category(raw_category)
        sku_ids = _skus_in_scope(category)

        location_id = kwargs.get("location_id")
        locations = [location_id] if location_id and location_id in INVENTORY else list(STORES.keys())
        lines = ["# Inventory Dashboard", ""]
        if category:
            lines.append(
                f"**Category filter:** {category} ({', '.join(sku_ids)}) — "
                "this view is filtered; the network total below is not."
            )
            lines.append("")
        for loc_id in locations:
            loc_info = STORES.get(loc_id, WAREHOUSES.get(loc_id, {}))
            lines.append(f"## {loc_info.get('name', loc_id)} (`{loc_id}`)")
            lines.append("")
            lines.append("| SKU | Product | Category | On-Hand | Safety Stock | Status | Days of Supply |")
            lines.append("|-----|---------|----------|---------|--------------|--------|----------------|")
            for sku_id in sku_ids:
                sku = SKUS[sku_id]
                on_hand = INVENTORY[loc_id].get(sku_id, 0)
                safety = SAFETY_STOCK.get(loc_id, {}).get(sku_id, "N/A")
                status = _stock_status(sku_id, loc_id)
                dos = _days_of_supply(sku_id, loc_id)
                lines.append(
                    f"| {sku_id} | {sku['name']} | {sku['category']} | {on_hand} | {safety} | {status} | {dos} |"
                )
            lines.append("")

        lines.append("## Category Rollup")
        lines.append("")
        lines.append(
            f"Covers the {len(locations)} location(s) in view: "
            f"{', '.join(locations)}."
        )
        lines.append("")
        lines.append("| Category | SKUs | On-Hand | Daily Sell-Through | Days of Supply | Value at Unit Cost |")
        lines.append("|----------|------|---------|--------------------|----------------|--------------------|")
        for cat in ([category] if category else _categories()):
            roll = _category_rollup(cat, locations)
            lines.append(
                f"| {cat} | {len(roll['sku_ids'])} | {roll['on_hand']:,} | "
                f"{roll['daily']} | {roll['days_of_supply']} | ${roll['value']:,.2f} |"
            )
        lines.append("")

        total_units = sum(sum(v.values()) for v in INVENTORY.values())
        lines.append(f"**Total Network Inventory:** {total_units:,} units across {len(INVENTORY)} locations")
        return "\n".join(lines)

    def _stock_alerts(self, **kwargs):
        raw_category = kwargs.get("category")
        category = _resolve_category(raw_category)
        if raw_category and category is None:
            return self._unknown_category(raw_category)
        sku_ids = _skus_in_scope(category)

        lines = ["# Stock Alerts", ""]
        if category:
            lines.append(
                f"**Category filter:** {category} ({', '.join(sku_ids)}) — "
                "every count below covers this category only."
            )
            lines.append("")
        lines.extend(["## Critical & Out-of-Stock Items", ""])
        lines.append("| Location | SKU | Product | Category | On-Hand | Safety Stock | Status | Action Required |")
        lines.append("|----------|-----|---------|----------|---------|--------------|--------|-----------------|")
        alert_count = 0
        by_category = {cat: {"critical": 0, "low": 0} for cat in ([category] if category else _categories())}
        for loc_id in sorted(STORES.keys()):
            for sku_id in sku_ids:
                status = _stock_status(sku_id, loc_id)
                if status in ("CRITICAL", "OUT_OF_STOCK"):
                    sku = SKUS[sku_id]
                    on_hand = INVENTORY[loc_id].get(sku_id, 0)
                    safety = SAFETY_STOCK[loc_id].get(sku_id, 0)
                    action = "Emergency replenish" if status == "OUT_OF_STOCK" else "Expedite transfer"
                    loc_name = STORES[loc_id]["name"]
                    lines.append(
                        f"| {loc_name} | {sku_id} | {sku['name']} | {sku['category']} | "
                        f"{on_hand} | {safety} | {status} | {action} |"
                    )
                    alert_count += 1
                    by_category[sku["category"]]["critical"] += 1
        lines.append("")
        lines.append(f"**Total Alerts:** {alert_count}")
        lines.append("")
        lines.append("## Low-Stock Warnings")
        lines.append("")
        low_count = 0
        for loc_id in sorted(STORES.keys()):
            for sku_id in sku_ids:
                status = _stock_status(sku_id, loc_id)
                if status == "LOW":
                    dos = _days_of_supply(sku_id, loc_id)
                    lines.append(
                        f"- **{STORES[loc_id]['name']}** / {SKUS[sku_id]['name']} "
                        f"({SKUS[sku_id]['category']}): {dos} days remaining"
                    )
                    low_count += 1
                    by_category[SKUS[sku_id]["category"]]["low"] += 1
        lines.append(f"\n**Low-Stock Warnings:** {low_count}")
        lines.append("")
        lines.append("## By Category")
        lines.append("")
        lines.append("| Category | Critical & Out-of-Stock | Low |")
        lines.append("|----------|-------------------------|-----|")
        for cat in sorted(by_category.keys()):
            counts = by_category[cat]
            lines.append(f"| {cat} | {counts['critical']} | {counts['low']} |")
        return "\n".join(lines)

    def _overstock_review(self, **kwargs):
        target_days = 14
        raw_category = kwargs.get("category")
        category = _resolve_category(raw_category)
        if raw_category and category is None:
            return self._unknown_category(raw_category)
        sku_ids = _skus_in_scope(category)

        lines = [
            "# Overstock Review",
            "",
            f"**Target:** {target_days}-day supply at each store; on-hand above "
            "that target is excess.",
            "",
        ]
        if category:
            lines.append(
                f"**Category filter:** {category} ({', '.join(sku_ids)}) — "
                "every count below covers this category only."
            )
            lines.append("")
        lines.append(
            "| Location | SKU | Product | Category | On-Hand | 14-Day Target | "
            "Excess Units | Days Over Target | Capital Tied Up |"
        )
        lines.append(
            "|----------|-----|---------|----------|---------|---------------|"
            "--------------|------------------|-----------------|"
        )
        position_count = 0
        total_excess = 0
        total_capital = 0.0
        by_category = {cat: {"units": 0, "capital": 0.0} for cat in ([category] if category else _categories())}
        for loc_id in sorted(STORES.keys()):
            for sku_id in sku_ids:
                pos = _overstock_position(sku_id, loc_id, target_days)
                if not pos:
                    continue
                sku = SKUS[sku_id]
                lines.append(
                    f"| {STORES[loc_id]['name']} | {sku_id} | {sku['name']} | {sku['category']} | "
                    f"{pos['on_hand']} | {pos['target']} | {pos['excess']} | "
                    f"{pos['days_over']} | ${pos['capital']:,.2f} |"
                )
                position_count += 1
                total_excess += pos["excess"]
                total_capital += pos["capital"]
                by_category[sku["category"]]["units"] += pos["excess"]
                by_category[sku["category"]]["capital"] += pos["capital"]
        lines.append("")
        lines.append(f"**Positions Above Target:** {position_count}")
        lines.append(f"**Total Excess Units:** {total_excess:,}")
        lines.append(f"**Capital Tied Up:** ${total_capital:,.2f}")
        lines.append("")
        lines.append("## By Category")
        lines.append("")
        lines.append("| Category | Excess Units | Capital Tied Up |")
        lines.append("|----------|--------------|-----------------|")
        for cat in sorted(by_category.keys()):
            entry = by_category[cat]
            lines.append(f"| {cat} | {entry['units']:,} | ${entry['capital']:,.2f} |")
        lines.append("")
        lines.append("## How to read this")
        lines.append("")
        lines.append("- Stores only. The two distribution centers hold network cover, "
                     "so the 14-day store target does not apply to them and they are out of scope.")
        lines.append("- Excess is reported, never resolved by drawing a store below its "
                     "safety-stock floor. Safety stock is a floor, not a source.")
        lines.append("- This is a finding, not a markdown, a transfer, or a write-off. "
                     "A planner decides what happens to the excess.")
        return "\n".join(lines)

    def _replenishment_plan(self, **kwargs):
        target_days = 14
        lines = [
            "# Replenishment Plan",
            "",
            f"**Target:** {target_days}-day supply at each store",
            "",
        ]
        total_cost = 0.0
        for loc_id in sorted(STORES.keys()):
            store = STORES[loc_id]
            lines.append(f"## {store['name']} (`{loc_id}`)")
            lines.append("")
            lines.append("| SKU | Product | Current | Target | Replenish Qty | Source | Lead Time | Est. Cost |")
            lines.append("|-----|---------|---------|--------|---------------|--------|-----------|-----------|")
            for sku_id in sorted(SKUS.keys()):
                qty = _replenishment_qty(sku_id, loc_id, target_days)
                if qty > 0:
                    sku = SKUS[sku_id]
                    on_hand = INVENTORY[loc_id][sku_id]
                    target_qty = on_hand + qty
                    wh_central = INVENTORY["WH-CENTRAL"].get(sku_id, 0)
                    source = "WH-CENTRAL" if wh_central >= qty else "WH-EAST"
                    lt = LEAD_TIMES_DAYS.get(source, {}).get(loc_id, 3)
                    cost = round(qty * sku["unit_cost"], 2)
                    total_cost += cost
                    lines.append(
                        f"| {sku_id} | {sku['name']} | {on_hand} | {target_qty} | {qty} | {source} | {lt}d | ${cost:,.2f} |"
                    )
            lines.append("")
        lines.append(f"**Estimated Total Replenishment Cost:** ${total_cost:,.2f}")
        return "\n".join(lines)

    def _channel_allocation(self, **kwargs):
        sku_id = kwargs.get("sku_id", "SKU-1001")
        sku = SKUS.get(sku_id, SKUS["SKU-1001"])
        total = _total_network_inventory(sku_id)
        allocations = _channel_allocation_units(sku_id, total)
        lines = [
            "# Channel Allocation",
            "",
            f"**SKU:** {sku_id} — {sku['name']}",
            f"**Total Network Inventory:** {total:,} units",
            "",
            "| Channel | Weight | Allocated Units | Daily Demand Avg | Days Coverage |",
            "|---------|--------|-----------------|------------------|---------------|",
        ]
        for channel, units in allocations.items():
            info = CHANNEL_DEMAND[channel]
            daily = info["daily_units_avg"]
            coverage = round(units / daily, 1) if daily > 0 else 0
            lines.append(
                f"| {channel.replace('_', ' ').title()} | {info['weight']*100:.0f}% | {units:,} | {daily} | {coverage} |"
            )
        lines.append("")
        lines.append("## Allocation Recommendations")
        lines.append("")
        lines.append("- **In-Store Priority:** Flagship and mall locations receive 60% of in-store allocation")
        lines.append("- **Online Buffer:** Maintain 3-day safety stock for e-commerce fulfillment")
        lines.append("- **BOPIS Reserve:** Hold 10% buffer for same-day pickup surges")
        lines.append("- **Marketplace Cap:** Limit marketplace allocation to prevent channel conflict")
        return "\n".join(lines)

    # ---- dispatch ----------------------------------------------------------

    def perform(self, **kwargs):
        operation = kwargs.get("operation", "inventory_dashboard")
        dispatch = {
            "inventory_dashboard": self._inventory_dashboard,
            "stock_alerts": self._stock_alerts,
            "overstock_review": self._overstock_review,
            "replenishment_plan": self._replenishment_plan,
            "channel_allocation": self._channel_allocation,
        }
        handler = dispatch.get(operation)
        if not handler:
            return f"Unknown operation `{operation}`. Valid: {', '.join(dispatch.keys())}"
        return handler(**kwargs)


# ---------------------------------------------------------------------------
# Main — exercise all operations
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    agent = InventoryVisibilityAgent()
    print("=" * 80)
    print(agent.perform(operation="inventory_dashboard", location_id="STR-001"))
    print("\n" + "=" * 80)
    print(agent.perform(operation="stock_alerts"))
    print("\n" + "=" * 80)
    print(agent.perform(operation="overstock_review"))
    print("\n" + "=" * 80)
    print(agent.perform(operation="inventory_dashboard", category="Apparel"))
    print("\n" + "=" * 80)
    print(agent.perform(operation="replenishment_plan"))
    print("\n" + "=" * 80)
    print(agent.perform(operation="channel_allocation", sku_id="SKU-1003"))
    print("=" * 80)
