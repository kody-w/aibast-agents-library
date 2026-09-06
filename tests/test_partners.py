"""Contract tests for the curated partner agent catalog and library view."""

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PARTNERS_FILE = REPO_ROOT / "partners.json"
REGISTRY_FILE = REPO_ROOT / "registry.json"
LIBRARY_PAGE = REPO_ROOT / "library.html"

REQUIRED_AGENT_FIELDS = {
    "id", "partner_id", "name", "category", "product",
    "description", "source_url",
}


@pytest.fixture(scope="module")
def catalog():
    return json.loads(PARTNERS_FILE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def partners(catalog):
    return catalog["partners"]


@pytest.fixture(scope="module")
def entries(catalog):
    return catalog["agents"]


@pytest.fixture(scope="module")
def registry():
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def test_schema_and_count(catalog, entries):
    assert catalog["schema"] == "aibast-partners/1.0"
    assert catalog["count"] == len(entries)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", catalog["snapshot_date"])


def test_partners_are_identified_and_linked(partners):
    ids = [p["id"] for p in partners]
    assert len(ids) == len(set(ids))
    for partner in partners:
        assert partner["url"].startswith("http")
        assert partner["name"]


def test_required_fields_and_identity(entries, partners):
    partner_ids = {p["id"] for p in partners}
    ids = []
    names = []
    for entry in entries:
        assert REQUIRED_AGENT_FIELDS.issubset(entry), (
            f"{entry.get('id')}: missing "
            f"{sorted(REQUIRED_AGENT_FIELDS - set(entry))}"
        )
        assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", entry["id"])
        assert entry["partner_id"] in partner_ids
        assert entry["source_url"].startswith("http")
        assert len(entry["description"].strip()) > 20
        ids.append(entry["id"])
        names.append(entry["name"])
    assert len(ids) == len(set(ids))
    assert len(names) == len(set(names))


def test_descriptions_are_not_copied_marketing_headlines(entries):
    # Guards against verbatim reuse of the partner site's own promotional
    # headline copy instead of a paraphrased, factual summary.
    banned_phrases = (
        "real-time answers, smarter sales on the go",
        "unleash revenue with ai agents",
    )
    for entry in entries:
        blob = entry["description"].lower()
        for phrase in banned_phrases:
            assert phrase not in blob, f"{entry['id']}: verbatim partner headline reused"


def test_registry_carries_partner_agents_separately(registry, entries, partners):
    assert len(registry["partner_agents"]) == len(entries)
    assert registry["partners"] == partners
    assert registry["stats"]["total_partner_agents"] == len(entries)
    assert registry["stats"]["partner_list"] == sorted({p["name"] for p in partners})
    assert all(
        agent.get("_catalog_kind") != "partner"
        for agent in registry["agents"]
    ), "partner agents must never be merged into the repo-owned agents array"
    assert registry["stats"]["total_agents"] == len(registry["agents"])


def test_registry_derived_fields(registry):
    for entry in registry["partner_agents"]:
        assert entry["_catalog_kind"] == "partner"


def test_library_exposes_the_partners_tab_and_contract():
    page = LIBRARY_PAGE.read_text(encoding="utf-8")
    for token in (
        'data-view="partners"',
        "registry.partner_agents",
        "registry.partners",
        "function filteredPartnerAgents",
        "function partnerAgentCard",
        "function openPartnerAgent",
        "Partner listing",
    ):
        assert token in page


def test_partner_agents_link_back_to_source(entries):
    for entry in entries:
        assert entry["source_url"].startswith("https://congruentx.com/") or entry["partner_id"] != "congruentx"
