"""Frontline workers can find their agents in one click, with a shareable link.

work_style lives in solutions.json (the advertised catalog), is carried into
registry.json by build_registry.py, and drives the "Frontline workers" filter
on index.html (?work=frontline preselects it).
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLISHER = "@aibast-agents-library/"
FRONTLINE = {
    PUBLISHER + slug for slug in [
        "field-service-dispatch",
        "store-associate-copilot",
        "grid-outage-response",
        "field-permit-to-work",
        "maintenance-scheduling",
        "engineering-standards-advisor",
        "inventory-visibility",
        "returns-complaints-resolution",
        "supplier-claim-engagement",
        "ask-hr",
        "benefits-enrollment-assistant",
    ]
}
FIELD_SERVICE = PUBLISHER + "field-service-dispatch"


def _solutions():
    return json.loads((ROOT / "solutions.json").read_text(encoding="utf-8"))["solutions"]


def _registry_agents():
    doc = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))
    return {agent["name"]: agent for agent in doc["agents"]}


def test_exactly_the_frontline_solutions_carry_the_marker():
    marked = {s["repo_agent"] for s in _solutions() if "frontline" in s.get("work_style", [])}
    assert marked == FRONTLINE


def test_work_style_is_always_a_list_of_strings():
    for s in _solutions():
        if "work_style" in s:
            assert isinstance(s["work_style"], list), s["repo_agent"]
            assert all(isinstance(w, str) and w for w in s["work_style"]), s["repo_agent"]


def test_registry_carries_work_style_to_the_library_page():
    agents = _registry_agents()
    marked = {
        name for name, agent in agents.items()
        if "frontline" in agent.get("_solution", {}).get("work_style", [])
    }
    assert marked == FRONTLINE


def test_build_registry_passes_work_style_through():
    source = (ROOT / "build_registry.py").read_text(encoding="utf-8")
    assert '"work_style": sol.get("work_style", [])' in source


def test_field_service_dispatch_has_industries_and_personas():
    row = next(s for s in _solutions() if s["repo_agent"] == FIELD_SERVICE)
    assert row["industries"], "Field Service Dispatch must show under an industry"
    assert "Energy and Utilities" in row["industries"]
    assert row["personas"]
    published = _registry_agents()[FIELD_SERVICE]["_solution"]
    assert published["industries"] == row["industries"]
    assert published["personas"] == row["personas"]


def test_index_has_frontline_filter_and_shareable_param():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert re.search(r'<select class="field" id="work"', html)
    assert 'frontline: "Frontline workers"' in html
    assert 'params.get("work")' in html, "?work=frontline must preselect the filter"
    assert 'params.set("work"' in html, "the filter must be written back to the URL"
    assert "solutionOf(row.agent).work_style" in html, "the filter must narrow the results"
