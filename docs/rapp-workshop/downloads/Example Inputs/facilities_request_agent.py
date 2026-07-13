"""Synthetic facilities request agent for the FY27 RAPP workshop."""

from __future__ import annotations

import hashlib
import re

try:
    from agents.basic_agent import BasicAgent
except ImportError:
    from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/facilities-request-workshop",
    "version": "1.0.0",
    "display_name": "FacilitiesRequestAgent",
    "description": "Triage a synthetic facilities issue and return a simulated receipt.",
    "author": "Microsoft AIBAST",
    "tags": ["workshop", "facilities", "synthetic", "local"],
    "category": "general",
    "quality_tier": "official",
    "requires_env": [],
    "dependencies": ["@rapp/basic_agent"],
}


class FacilitiesRequestAgent(BasicAgent):
    CRITICAL = (
        "smoke", "fire", "exposed wire", "sparks", "flooding",
        "blocked emergency exit", "security event",
    )
    CATEGORIES = {
        "lighting": ("light", "lighting", "bulb"),
        "hvac": ("hot", "cold", "temperature", "thermostat", "heating", "cooling"),
        "plumbing": ("leak", "sink", "water", "drain", "plumbing"),
        "access": ("door", "badge", "reader", "access", "exit"),
        "cleaning": ("spill", "clean", "trash"),
        "furniture": ("chair", "desk", "furniture"),
    }

    def __init__(self):
        self.name = "FacilitiesRequestAgent"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "parameters": {
                "type": "object",
                "properties": {
                    "user_query": {
                        "type": "string",
                        "description": "The employee's facilities request in plain language.",
                    },
                    "building": {
                        "type": "string",
                        "description": "Building name or code exactly as the employee supplied it.",
                    },
                    "location": {
                        "type": "string",
                        "description": "Floor, room, area, or landmark.",
                    },
                },
                "required": ["user_query"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    @classmethod
    def _category(cls, text):
        for category, terms in cls.CATEGORIES.items():
            if any(term in text for term in terms):
                return category
        if any(term in text for term in cls.CRITICAL):
            return "safety"
        return "other"

    @staticmethod
    def _location_from_query(query):
        match = re.search(
            r"\b(?:floor|level|room|building)\s+[A-Za-z0-9-]+"
            r"(?:\s+(?:near|at)\s+[A-Za-z0-9 -]+)?",
            query,
            re.IGNORECASE,
        )
        return match.group(0) if match else ""

    def perform(self, user_query="", building="", location="", **kwargs):
        query = str(user_query or "").strip()
        if not query:
            return "Tell me what facilities issue you want to report."

        lowered = query.lower()
        critical = any(term in lowered for term in self.CRITICAL)
        category = self._category(lowered)
        supplied_location = str(location or "").strip() or self._location_from_query(query)
        supplied_building = str(building or "").strip()

        if critical:
            return (
                "Critical safety issue detected. Move away from the area and follow "
                "building emergency procedures. Contact the approved emergency channel "
                "now. I will not continue normal troubleshooting or declare the area safe."
            )

        missing = []
        if not supplied_building:
            missing.append("building")
        if not supplied_location:
            missing.append("exact location")
        if missing:
            return "Before I create the simulated request, provide: " + ", ".join(missing) + "."

        urgency = "high" if any(
            term in lowered for term in ("blocking", "outage", "customer meeting", "cannot work")
        ) else "normal"
        digest = hashlib.sha256(
            f"{supplied_building}|{supplied_location}|{query}".encode("utf-8")
        ).hexdigest()[:6].upper()
        receipt = f"SIM-FAC-{digest}"
        summary = re.sub(r"\s+", " ", query).strip()[:180]
        return (
            f"Simulated receipt {receipt}\n"
            f"Category: {category}\n"
            f"Urgency: {urgency}\n"
            f"Location: {supplied_building}, {supplied_location}\n"
            f"Summary: {summary}\n"
            "Next step: facilities coordinator review.\n"
            "Simulation only - no external system was updated."
        )
