"""
R&D Discovery & Requirements Agent

Searches prior work for what has already been tried, then drafts the requirement in the house structure.

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
    "name": "@aibast-agents-library/rd-discovery-requirements",
    "version": "1.0.0",
    "display_name": "R&D Discovery & Requirements Agent",
    "description": "Searches prior internal work and published literature for what has already been attempted, then drafts the requirement or innovation record in the structure the review board expects.",
    "author": "AIBAST",
    "tags": ['research', 'requirements', 'innovation', 'discovery', 'authoring'],
    "category": "professional_services",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Synthetic domain data — invented, and labelled as such wherever it is shown.
# ---------------------------------------------------------------------------

ENQUIRIES = {
    "RQ-501": {"topic": "Alternative binder chemistry", "prior_internal": 3, "prior_published": 11,
               "status": "prior work found — narrow the question", "structure": "innovation record"},
    "RQ-502": {"topic": "Sensor placement for early fault detection", "prior_internal": 0,
               "prior_published": 6, "status": "no internal prior work", "structure": "requirement"},
    "RQ-503": {"topic": "Claims triage decision support", "prior_internal": 5, "prior_published": 2,
               "status": "duplicate of an open programme", "structure": "requirement"},
}

REVIEW_STRUCTURE = {
    "innovation record": ["problem", "prior art", "proposed approach", "evidence needed"],
    "requirement": ["need", "scope", "acceptance criteria", "out of scope", "open questions"],
}


def _rows(d):
    return list(d.items()) if isinstance(d, dict) else list(enumerate(d))


class RdDiscoveryRequirementsAgent(BasicAgent):
    """Searches prior work for what has already been tried, then drafts the requirement in the house structure."""

    def __init__(self):
        self.name = "RdDiscoveryRequirementsAgent"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "operations": ['prior_art_scan', 'gap_analysis', 'requirement_draft', 'review_readiness'],
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        operation = kwargs.get("operation", "prior_art_scan")
        dispatch = {
            "prior_art_scan": self._prior_art_scan,
            "gap_analysis": self._gap_analysis,
            "requirement_draft": self._requirement_draft,
            "review_readiness": self._review_readiness,
        }
        handler = dispatch.get(operation)
        if handler is None:
            return f"**Error:** Unknown operation `{operation}`. Valid: {', '.join(dispatch.keys())}"
        return handler(**kwargs)

    def _prior_art_scan(self, **kwargs) -> str:
        lines = ["## Prior Art Scan", "", "_Synthetic data — illustrative only._", ""]
        primary = ENQUIRIES
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

    def _gap_analysis(self, **kwargs) -> str:
        lines = ["## Gap Analysis", "", "_Synthetic data — illustrative only._", ""]
        primary = ENQUIRIES
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

    def _requirement_draft(self, **kwargs) -> str:
        lines = ["## Requirement Draft", "", "_Synthetic data — illustrative only._", ""]
        primary = ENQUIRIES
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

    def _review_readiness(self, **kwargs) -> str:
        lines = ["## Review Readiness", "", "_Synthetic data — illustrative only._", ""]
        primary = ENQUIRIES
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
    agent = RdDiscoveryRequirementsAgent()
    for op in agent.metadata["operations"]:
        print("=" * 72)
        print(agent.perform(operation=op))
        print()
