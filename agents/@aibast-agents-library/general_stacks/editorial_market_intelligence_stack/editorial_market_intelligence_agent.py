"""
Editorial & Market Intelligence Agent

Finds the story worth pursuing across a watched set of sources, and says what is corroborated and what is single-sourced.

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
    "name": "@aibast-agents-library/editorial-market-intelligence",
    "version": "1.0.0",
    "display_name": "Editorial & Market Intelligence Agent",
    "description": "Scans a watched source set for emerging stories and market signals, clusters them by theme, and separates corroborated findings from single-sourced ones before briefing.",
    "author": "AIBAST",
    "tags": ['editorial', 'research', 'market-intelligence', 'media', 'briefing'],
    "category": "general",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Synthetic domain data — invented, and labelled as such wherever it is shown.
# ---------------------------------------------------------------------------

SIGNALS = {
    "SIG-301": {"theme": "Supply concentration", "sources_seen": 4, "corroborated": True,
                "movement": "rising", "first_seen": "this period"},
    "SIG-302": {"theme": "Regulatory consultation", "sources_seen": 1, "corroborated": False,
                "movement": "flat", "first_seen": "this period"},
    "SIG-303": {"theme": "Competitor product withdrawal", "sources_seen": 3, "corroborated": True,
                "movement": "rising", "first_seen": "prior period"},
    "SIG-304": {"theme": "Workforce action", "sources_seen": 2, "corroborated": False,
                "movement": "unclear", "first_seen": "this period"},
}

SOURCE_SET = ["trade press", "regulatory notices", "public filings", "sector newsletters"]


def _rows(d):
    return list(d.items()) if isinstance(d, dict) else list(enumerate(d))


class EditorialMarketIntelligenceAgent(BasicAgent):
    """Finds the story worth pursuing across a watched set of sources, and says what is corroborated and what is single-sourced."""

    def __init__(self):
        self.name = "EditorialMarketIntelligenceAgent"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "operations": ['story_radar', 'theme_clusters', 'corroboration_check', 'briefing_pack'],
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        operation = kwargs.get("operation", "story_radar")
        dispatch = {
            "story_radar": self._story_radar,
            "theme_clusters": self._theme_clusters,
            "corroboration_check": self._corroboration_check,
            "briefing_pack": self._briefing_pack,
        }
        handler = dispatch.get(operation)
        if handler is None:
            return f"**Error:** Unknown operation `{operation}`. Valid: {', '.join(dispatch.keys())}"
        return handler(**kwargs)

    def _story_radar(self, **kwargs) -> str:
        lines = ["## Story Radar", "", "_Synthetic data — illustrative only._", ""]
        primary = SIGNALS
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

    def _theme_clusters(self, **kwargs) -> str:
        lines = ["## Theme Clusters", "", "_Synthetic data — illustrative only._", ""]
        primary = SIGNALS
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

    def _corroboration_check(self, **kwargs) -> str:
        lines = ["## Corroboration Check", "", "_Synthetic data — illustrative only._", ""]
        primary = SIGNALS
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

    def _briefing_pack(self, **kwargs) -> str:
        lines = ["## Briefing Pack", "", "_Synthetic data — illustrative only._", ""]
        primary = SIGNALS
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
    agent = EditorialMarketIntelligenceAgent()
    for op in agent.metadata["operations"]:
        print("=" * 72)
        print(agent.perform(operation=op))
        print()
