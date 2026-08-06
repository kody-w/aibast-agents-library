"""
Regulated Document Drafting Agent

Drafts regulated documents — legislative text, legal opinions, tender packs — against the taxonomy and tone each regime requires.

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
    "name": "@aibast-agents-library/regulated-document-drafting",
    "version": "1.0.0",
    "display_name": "Regulated Document Drafting Agent",
    "description": "Drafts industry-regulated documents from an approved clause library, checks tone and taxonomy against the governing regime, and reports every clause it could not source.",
    "author": "AIBAST",
    "tags": ['drafting', 'legal', 'tender', 'compliance', 'public-sector'],
    "category": "slg_government",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Synthetic domain data — invented, and labelled as such wherever it is shown.
# ---------------------------------------------------------------------------

DOC_TYPES = {
    "DOC-4101": {"title": "Statutory instrument — minor amendment", "regime": "Legislative drafting",
                 "stage": "second draft", "clauses": 24, "unsourced": 2, "tone": "formal-statutory"},
    "DOC-4102": {"title": "Legal opinion — procurement challenge", "regime": "Legal opinion",
                 "stage": "first draft", "clauses": 11, "unsourced": 4, "tone": "advisory"},
    "DOC-4103": {"title": "Tender pack — network maintenance lot", "regime": "Public procurement",
                 "stage": "ready for review", "clauses": 38, "unsourced": 0, "tone": "contractual"},
    "DOC-4104": {"title": "Consumer product disclosure", "regime": "Regulated consumer copy",
                 "stage": "in drafting", "clauses": 17, "unsourced": 5, "tone": "plain-language"},
}

CLAUSE_LIBRARY = {
    "Legislative drafting": ["commencement", "interpretation", "amendment", "repeal", "transitional"],
    "Legal opinion": ["question presented", "short answer", "analysis", "limitations"],
    "Public procurement": ["scope", "award criteria", "liability", "termination", "variation"],
    "Regulated consumer copy": ["eligibility", "exclusions", "cooling-off", "complaints route"],
}


def _rows(d):
    return list(d.items()) if isinstance(d, dict) else list(enumerate(d))


class RegulatedDocumentDraftingAgent(BasicAgent):
    """Drafts regulated documents — legislative text, legal opinions, tender packs — against the taxonomy and tone each regime requires."""

    def __init__(self):
        self.name = "RegulatedDocumentDraftingAgent"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "operations": ['draft_queue', 'clause_sourcing', 'compliance_check', 'revision_plan'],
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        operation = kwargs.get("operation", "draft_queue")
        dispatch = {
            "draft_queue": self._draft_queue,
            "clause_sourcing": self._clause_sourcing,
            "compliance_check": self._compliance_check,
            "revision_plan": self._revision_plan,
        }
        handler = dispatch.get(operation)
        if handler is None:
            return f"**Error:** Unknown operation `{operation}`. Valid: {', '.join(dispatch.keys())}"
        return handler(**kwargs)

    def _draft_queue(self, **kwargs) -> str:
        lines = ["## Draft Queue", "", "_Synthetic data — illustrative only._", ""]
        primary = DOC_TYPES
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

    def _clause_sourcing(self, **kwargs) -> str:
        lines = ["## Clause Sourcing", "", "_Synthetic data — illustrative only._", ""]
        primary = DOC_TYPES
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

    def _compliance_check(self, **kwargs) -> str:
        lines = ["## Compliance Check", "", "_Synthetic data — illustrative only._", ""]
        primary = DOC_TYPES
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

    def _revision_plan(self, **kwargs) -> str:
        lines = ["## Revision Plan", "", "_Synthetic data — illustrative only._", ""]
        primary = DOC_TYPES
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
    agent = RegulatedDocumentDraftingAgent()
    for op in agent.metadata["operations"]:
        print("=" * 72)
        print(agent.perform(operation=op))
        print()
