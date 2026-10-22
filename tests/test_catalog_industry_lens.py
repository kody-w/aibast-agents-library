"""The catalog treats industry as a lens: every template adapts, nothing is hidden for good."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


def test_catalog_remembers_the_same_industry_as_the_workshops():
    assert 'id="your-industry"' in INDEX
    assert 'const YOUR_INDUSTRY_KEY = "aibast.workshop.industry";' in INDEX
    quest = (ROOT / "solutions" / "time-entry-billing" / "quest.html").read_text(encoding="utf-8")
    assert 'const industryKey = "aibast.workshop.industry";' in quest


def test_remembered_industry_is_read_and_written_safely():
    read = re.search(r"function readYourIndustry\(\) \{(.+?)\n\}", INDEX, flags=re.S).group(1)
    write = re.search(r"function writeYourIndustry\(value\) \{(.+?)\n\}", INDEX, flags=re.S).group(1)
    assert "try {" in read and "catch" in read
    assert "try {" in write and "catch" in write
    # Typed text is escaped before it reaches the page.
    assert "${esc(state.yourIndustry)}" in INDEX
    assert "${state.yourIndustry}" not in INDEX


def test_library_industry_filter_still_works_and_offers_the_rest():
    # Old ?industry= links keep filtering; the other templates stay one click away.
    assert 'row.agent.category === state.industry' in INDEX
    assert "function moreThatAdapt(shownRows)" in INDEX
    assert "more template${others.length === 1 ? \"\" : \"s\"} adapt to" in INDEX
    assert "moreThatAdapt(rows)" in INDEX


def test_microsoft_first_party_agents_show_first_for_a_search():
    assert "Microsoft agents that already do this" in INDEX
    assert "firstPartyStrip() + (rows.length" in INDEX


def test_address_parameters_are_unchanged():
    for param in ('params.get("view")', 'params.get("q")', 'params.get("industry")'):
        assert param in INDEX, param


def test_one_industry_control_lives_in_the_industry_panel():
    panel = INDEX[INDEX.index('<div class="industry-selector">'):INDEX.index('<div class="industry-blueprint"')]
    assert 'id="your-industry"' in panel
    assert 'placeholder="Not listed? Type your industry"' in panel
    assert INDEX.count('id="your-industry"') == 1
    # Choosing a tile makes it your industry for the workshops, except the cross-industry tile.
    assert 'if (state.industry && industry !== "general") {' in INDEX
    assert "writeYourIndustry(industryName);" in INDEX
