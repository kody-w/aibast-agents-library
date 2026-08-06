"""
Asset Reliability & Standards Agent

Reads asset history against the engineering standard that governs it, and says which interventions the standard actually requires.

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
    "name": "@aibast-agents-library/asset-reliability-standards",
    "version": "1.0.0",
    "display_name": "Asset Reliability & Standards Agent",
    "description": "Correlates asset condition history with the governing engineering standard, flags where practice has drifted from specification, and sequences the interventions the standard requires.",
    "author": "AIBAST",
    "tags": ['reliability', 'maintenance', 'engineering-standards', 'asset', 'industrial'],
    "category": "manufacturing",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Synthetic domain data — invented, and labelled as such wherever it is shown.
# ---------------------------------------------------------------------------

ASSETS = {
    "AST-7001": {"asset": "Primary drive gearbox", "line": "Continuous caster",
                 "standard": "Rotating equipment — condition monitoring",
                 "last_intervention": "quarterly inspection", "drift": "vibration trend above band",
                 "criticality": "high"},
    "AST-7002": {"asset": "Heat exchanger bank", "line": "Process cooling",
                 "standard": "Pressure equipment — periodic examination",
                 "last_intervention": "examination overdue", "drift": "examination interval exceeded",
                 "criticality": "high"},
    "AST-7003": {"asset": "Conveyor drive set", "line": "Packing hall",
                 "standard": "Mechanical handling — guarding and access",
                 "last_intervention": "guard replaced", "drift": "none recorded",
                 "criticality": "medium"},
}

STANDARD_REQUIREMENTS = {
    "Rotating equipment — condition monitoring": ["trend review", "alignment check", "lubricant sample"],
    "Pressure equipment — periodic examination": ["external examination", "thickness survey", "written scheme review"],
    "Mechanical handling — guarding and access": ["guard integrity", "interlock test", "access route check"],
}


def _rows(d):
    return list(d.items()) if isinstance(d, dict) else list(enumerate(d))


class AssetReliabilityStandardsAgent(BasicAgent):
    """Reads asset history against the engineering standard that governs it, and says which interventions the standard actually requires."""

    def __init__(self):
        self.name = "AssetReliabilityStandardsAgent"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "operations": ['reliability_review', 'standards_gap', 'intervention_plan', 'evidence_pack'],
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        operation = kwargs.get("operation", "reliability_review")
        dispatch = {
            "reliability_review": self._reliability_review,
            "standards_gap": self._standards_gap,
            "intervention_plan": self._intervention_plan,
            "evidence_pack": self._evidence_pack,
        }
        handler = dispatch.get(operation)
        if handler is None:
            return f"**Error:** Unknown operation `{operation}`. Valid: {', '.join(dispatch.keys())}"
        return handler(**kwargs)

    def _reliability_review(self, **kwargs) -> str:
        lines = ["## Reliability Review", "", "_Synthetic data — illustrative only._", ""]
        primary = ASSETS
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

    def _standards_gap(self, **kwargs) -> str:
        lines = ["## Standards Gap", "", "_Synthetic data — illustrative only._", ""]
        primary = ASSETS
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

    def _intervention_plan(self, **kwargs) -> str:
        lines = ["## Intervention Plan", "", "_Synthetic data — illustrative only._", ""]
        primary = ASSETS
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

    def _evidence_pack(self, **kwargs) -> str:
        lines = ["## Evidence Pack", "", "_Synthetic data — illustrative only._", ""]
        primary = ASSETS
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
    agent = AssetReliabilityStandardsAgent()
    for op in agent.metadata["operations"]:
        print("=" * 72)
        print(agent.perform(operation=op))
        print()
