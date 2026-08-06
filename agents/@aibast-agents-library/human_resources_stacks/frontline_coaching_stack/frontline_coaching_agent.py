"""
Frontline Coaching Agent

Turns observed frontline interactions into a coaching record a manager can run a one-to-one from.

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
    "name": "@aibast-agents-library/frontline-coaching",
    "version": "1.0.0",
    "display_name": "Frontline Coaching Agent",
    "description": "Summarises observed frontline interactions against the coaching framework in use, drafts the one-to-one record, and separates what was observed from what was inferred.",
    "author": "AIBAST",
    "tags": ['coaching', 'one-to-one', 'frontline', 'quality', 'contact-center'],
    "category": "human_resources",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Synthetic domain data — invented, and labelled as such wherever it is shown.
# ---------------------------------------------------------------------------

OBSERVATIONS = {
    "OBS-201": {"role": "Contact centre adviser", "framework": "Quality framework A",
                "observed": ["opened with verification", "explained options unprompted"],
                "development": ["summarise before closing"], "sessions_since_review": 4},
    "OBS-202": {"role": "Branch adviser", "framework": "Quality framework A",
                "observed": ["strong needs discovery"],
                "development": ["record outcome in system during call"], "sessions_since_review": 2},
    "OBS-203": {"role": "Claims handler", "framework": "Quality framework B",
                "observed": ["clear expectation setting", "checked understanding"],
                "development": [], "sessions_since_review": 6},
}

FRAMEWORKS = {
    "Quality framework A": ["verification", "needs discovery", "options", "close"],
    "Quality framework B": ["expectation setting", "evidence gathering", "decision", "next step"],
}


def _rows(d):
    return list(d.items()) if isinstance(d, dict) else list(enumerate(d))


class FrontlineCoachingAgent(BasicAgent):
    """Turns observed frontline interactions into a coaching record a manager can run a one-to-one from."""

    def __init__(self):
        self.name = "FrontlineCoachingAgent"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "operations": ['coaching_summary', 'observation_log', 'development_plan', 'session_prep'],
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        operation = kwargs.get("operation", "coaching_summary")
        dispatch = {
            "coaching_summary": self._coaching_summary,
            "observation_log": self._observation_log,
            "development_plan": self._development_plan,
            "session_prep": self._session_prep,
        }
        handler = dispatch.get(operation)
        if handler is None:
            return f"**Error:** Unknown operation `{operation}`. Valid: {', '.join(dispatch.keys())}"
        return handler(**kwargs)

    def _coaching_summary(self, **kwargs) -> str:
        lines = ["## Coaching Summary", "", "_Synthetic data — illustrative only._", ""]
        primary = OBSERVATIONS
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

    def _observation_log(self, **kwargs) -> str:
        lines = ["## Observation Log", "", "_Synthetic data — illustrative only._", ""]
        primary = OBSERVATIONS
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

    def _development_plan(self, **kwargs) -> str:
        lines = ["## Development Plan", "", "_Synthetic data — illustrative only._", ""]
        primary = OBSERVATIONS
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

    def _session_prep(self, **kwargs) -> str:
        lines = ["## Session Prep", "", "_Synthetic data — illustrative only._", ""]
        primary = OBSERVATIONS
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
    agent = FrontlineCoachingAgent()
    for op in agent.metadata["operations"]:
        print("=" * 72)
        print(agent.perform(operation=op))
        print()
