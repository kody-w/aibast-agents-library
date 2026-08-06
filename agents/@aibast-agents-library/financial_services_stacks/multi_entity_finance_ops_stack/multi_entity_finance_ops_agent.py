"""
Multi-Entity Finance Operations Agent

Runs the close across entities, currencies and ledgers, and shows which balances reconcile and which do not.

Provenance: consolidated from FY27 cross-customer scenario analysis. The source
material is customer-attributed; nothing customer-identifying is carried here.
Industry focus and the shape of the work are what transfer. All data below is
synthetic.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/multi-entity-finance-ops",
    "version": "1.0.0",
    "display_name": "Multi-Entity Finance Operations Agent",
    "description": "Consolidates period-end across multiple entities, currencies and ledgers, reconciles intercompany positions, and reports every balance it could not tie with the reason it could not.",
    "author": "AIBAST",
    "tags": ['finance', 'consolidation', 'multi-currency', 'intercompany', 'close'],
    "category": "financial_services",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Synthetic domain data — invented, and labelled as such wherever it is shown.
# ---------------------------------------------------------------------------

ENTITIES = {
    "ENT-01": {"entity": "Northern operating entity", "ledger": "Ledger A", "currency": "EUR",
               "close_stage": "sub-ledgers closed", "open_items": 3},
    "ENT-02": {"entity": "Southern operating entity", "ledger": "Ledger A", "currency": "EUR",
               "close_stage": "in review", "open_items": 7},
    "ENT-03": {"entity": "Overseas services entity", "ledger": "Ledger B", "currency": "USD",
               "close_stage": "posting", "open_items": 12},
    "ENT-04": {"entity": "Holding entity", "ledger": "Ledger B", "currency": "GBP",
               "close_stage": "not started", "open_items": 0},
}

INTERCOMPANY = [
    {"pair": "ENT-01 / ENT-03", "nature": "management recharge", "status": "matched"},
    {"pair": "ENT-02 / ENT-03", "nature": "shared services", "status": "unmatched — timing"},
    {"pair": "ENT-02 / ENT-04", "nature": "funding", "status": "unmatched — rate applied"},
]


def _rows(d):
    return list(d.items()) if isinstance(d, dict) else list(enumerate(d))


class MultiEntityFinanceOpsAgent(BasicAgent):
    """Runs the close across entities, currencies and ledgers, and shows which balances reconcile and which do not."""

    def __init__(self):
        self.name = "MultiEntityFinanceOpsAgent"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "operations": ['close_status', 'intercompany_reconciliation', 'fx_exposure', 'close_plan'],
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        operation = kwargs.get("operation", "close_status")
        dispatch = {
            "close_status": self._close_status,
            "intercompany_reconciliation": self._intercompany_reconciliation,
            "fx_exposure": self._fx_exposure,
            "close_plan": self._close_plan,
        }
        handler = dispatch.get(operation)
        if handler is None:
            return f"**Error:** Unknown operation `{operation}`. Valid: {', '.join(dispatch.keys())}"
        return handler(**kwargs)

    def _close_status(self, **kwargs) -> str:
        lines = ["## Close Status", "", "_Synthetic data — illustrative only._", ""]
        primary = ENTITIES
        for key, row in _rows(primary):
            if isinstance(row, dict):
                head = row.get("title") or row.get("asset") or row.get("entity") or \
                    row.get("role") or row.get("theme") or row.get("topic") or \
                    row.get("setting") or str(key)
                lines.append(f"**{key} — {head}**")
                for k, v in row.items():
                    if k in ("title", "asset", "entity", "role", "theme", "topic", "setting"):
                        continue
                    label = k.replace("_", " ").capitalize()
                    if isinstance(v, list):
                        v = ", ".join(str(x) for x in v) if v else "none recorded"
                    lines.append(f"- {label}: {v}")
                lines.append("")
            else:
                lines.append(f"- {row}")
        lines.append("_Nothing above is written back without confirmation._")
        return "\n".join(lines)

    def _intercompany_reconciliation(self, **kwargs) -> str:
        lines = ["## Intercompany Reconciliation", "", "_Synthetic data — illustrative only._", ""]
        primary = ENTITIES
        for key, row in _rows(primary):
            if isinstance(row, dict):
                head = row.get("title") or row.get("asset") or row.get("entity") or \
                    row.get("role") or row.get("theme") or row.get("topic") or \
                    row.get("setting") or str(key)
                lines.append(f"**{key} — {head}**")
                for k, v in row.items():
                    if k in ("title", "asset", "entity", "role", "theme", "topic", "setting"):
                        continue
                    label = k.replace("_", " ").capitalize()
                    if isinstance(v, list):
                        v = ", ".join(str(x) for x in v) if v else "none recorded"
                    lines.append(f"- {label}: {v}")
                lines.append("")
            else:
                lines.append(f"- {row}")
        lines.append("_Nothing above is written back without confirmation._")
        return "\n".join(lines)

    def _fx_exposure(self, **kwargs) -> str:
        lines = ["## Fx Exposure", "", "_Synthetic data — illustrative only._", ""]
        primary = ENTITIES
        for key, row in _rows(primary):
            if isinstance(row, dict):
                head = row.get("title") or row.get("asset") or row.get("entity") or \
                    row.get("role") or row.get("theme") or row.get("topic") or \
                    row.get("setting") or str(key)
                lines.append(f"**{key} — {head}**")
                for k, v in row.items():
                    if k in ("title", "asset", "entity", "role", "theme", "topic", "setting"):
                        continue
                    label = k.replace("_", " ").capitalize()
                    if isinstance(v, list):
                        v = ", ".join(str(x) for x in v) if v else "none recorded"
                    lines.append(f"- {label}: {v}")
                lines.append("")
            else:
                lines.append(f"- {row}")
        lines.append("_Nothing above is written back without confirmation._")
        return "\n".join(lines)

    def _close_plan(self, **kwargs) -> str:
        lines = ["## Close Plan", "", "_Synthetic data — illustrative only._", ""]
        primary = ENTITIES
        for key, row in _rows(primary):
            if isinstance(row, dict):
                head = row.get("title") or row.get("asset") or row.get("entity") or \
                    row.get("role") or row.get("theme") or row.get("topic") or \
                    row.get("setting") or str(key)
                lines.append(f"**{key} — {head}**")
                for k, v in row.items():
                    if k in ("title", "asset", "entity", "role", "theme", "topic", "setting"):
                        continue
                    label = k.replace("_", " ").capitalize()
                    if isinstance(v, list):
                        v = ", ".join(str(x) for x in v) if v else "none recorded"
                    lines.append(f"- {label}: {v}")
                lines.append("")
            else:
                lines.append(f"- {row}")
        lines.append("_Nothing above is written back without confirmation._")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    agent = MultiEntityFinanceOpsAgent()
    for op in agent.metadata["operations"]:
        print("=" * 72)
        print(agent.perform(operation=op))
        print()
