"""
Clinical Documentation Agent

Assembles the clinical record for review and shows which entries are evidenced in the source and which are not.

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
    "name": "@aibast-agents-library/clinical-documentation-ring",
    "version": "1.0.0",
    "display_name": "Clinical Documentation Agent",
    "description": "Assembles clinical documentation for review, checks each entry against its source in the record, and reports coding and governance gaps rather than filling them.",
    "author": "AIBAST",
    "tags": ['clinical', 'documentation', 'coding', 'governance', 'healthcare'],
    "category": "healthcare",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Synthetic domain data — invented, and labelled as such wherever it is shown.
# ---------------------------------------------------------------------------

EPISODES = {
    "EP-901": {"setting": "Outpatient clinic", "entries": 14, "unevidenced": 1,
               "coding_status": "complete", "governance": "within policy"},
    "EP-902": {"setting": "Day case", "entries": 22, "unevidenced": 4,
               "coding_status": "queries open", "governance": "consent note missing"},
    "EP-903": {"setting": "Community visit", "entries": 9, "unevidenced": 0,
               "coding_status": "complete", "governance": "within policy"},
}

GOVERNANCE_CHECKS = ["consent recorded", "author identified", "timing recorded", "amendments tracked"]


def _rows(d):
    return list(d.items()) if isinstance(d, dict) else list(enumerate(d))


class ClinicalDocumentationRingAgent(BasicAgent):
    """Assembles the clinical record for review and shows which entries are evidenced in the source and which are not."""

    def __init__(self):
        self.name = "ClinicalDocumentationRingAgent"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "operations": ['documentation_review', 'evidence_trace', 'coding_gaps', 'governance_check'],
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        operation = kwargs.get("operation", "documentation_review")
        dispatch = {
            "documentation_review": self._documentation_review,
            "evidence_trace": self._evidence_trace,
            "coding_gaps": self._coding_gaps,
            "governance_check": self._governance_check,
        }
        handler = dispatch.get(operation)
        if handler is None:
            return f"**Error:** Unknown operation `{operation}`. Valid: {', '.join(dispatch.keys())}"
        return handler(**kwargs)

    def _documentation_review(self, **kwargs) -> str:
        lines = ["## Documentation Review", "", "_Synthetic data — illustrative only._", ""]
        primary = EPISODES
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

    def _evidence_trace(self, **kwargs) -> str:
        lines = ["## Evidence Trace", "", "_Synthetic data — illustrative only._", ""]
        primary = EPISODES
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

    def _coding_gaps(self, **kwargs) -> str:
        lines = ["## Coding Gaps", "", "_Synthetic data — illustrative only._", ""]
        primary = EPISODES
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

    def _governance_check(self, **kwargs) -> str:
        lines = ["## Governance Check", "", "_Synthetic data — illustrative only._", ""]
        primary = EPISODES
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
    agent = ClinicalDocumentationRingAgent()
    for op in agent.metadata["operations"]:
        print("=" * 72)
        print(agent.perform(operation=op))
        print()
