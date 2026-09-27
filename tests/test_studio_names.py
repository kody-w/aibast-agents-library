import html
from pathlib import Path

import pytest

from tools import build_studio_package as package

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(("title", "suffix", "limit", "expected"), [
    ("Asset Maintenance Forecast", " Manual", 30, "Asset Maintenance Manual"),
    ("Asset Maintenance Forecast", " Studio", 30, "Asset Maintenance Studio"),
    ("Customer Sentiment & Churn Prediction", " Manual", 30, "Customer Sentiment Manual"),
    ("Customer Sentiment and Churn Prediction", " Studio", 30, "Customer Sentiment Studio"),
    ("Supply Risk Monitoring", " Manual", 30, "Supply Risk Monitoring Manual"),
    ("Loan Origination Assistant", " Manual", 30, "Loan Origination Manual"),
    ("Retail Store Associate Copilot", " Manual", 30, "Retail Store Associate Manual"),
    ("Win/Loss Analysis", " Manual", 30, "Win/Loss Analysis Manual"),
    ("Asset Maintenance Forecast", " Workspace", 40, "Asset Maintenance Forecast Workspace"),
    ("Asset Maintenance Forecast", " Workspace Manual", 40, "Asset Maintenance Workspace Manual"),
    ("Supply Chain Disruption", " Manual", 30, "Supply Chain Disruption Manual"),
    ("Supply Chain Disruptions", " Manual", 30, "Supply Chain Manual"),
    ("Customer Account Method", " Workspace Manual", 40, "Customer Account Method Workspace Manual"),
    ("Customer Account Methods", " Workspace Manual", 40, "Customer Account Workspace Manual"),
])
def test_whole_word_names_are_readable_and_keep_the_required_suffix(title, suffix, limit, expected):
    assert package.whole_word_name(title, suffix, limit) == expected
    assert len(expected) <= limit


def assert_title_words(name, title, suffix):
    assert name.endswith(suffix)
    selected = name[:-len(suffix)].split()
    original = iter(title.split())
    assert selected
    for word in selected:
        assert any(candidate == word for candidate in original), (name, title)
    assert selected[-1].lower() not in package.TRAILING_NAME_JOINERS


def test_collisions_restore_a_distinguishing_word_for_both_workshops():
    titles = {
        "prediction": "Customer Sentiment Prediction",
        "monitoring": "Customer Sentiment Monitoring",
    }
    suffixes = {"easy": " Studio", "manual": " Manual"}
    result = package.whole_word_catalog_names(titles, suffixes, 30)
    assert result["prediction"] == {"easy": "Customer Prediction Studio", "manual": "Customer Prediction Manual"}
    assert result["monitoring"] == {"easy": "Customer Monitoring Studio", "manual": "Customer Monitoring Manual"}
    for slug, names in result.items():
        for mode, name in names.items():
            assert name != "Customer Sentiment" + suffixes[mode]
            assert_title_words(name, titles[slug], suffixes[mode])
            assert len(name) <= 30
    assert result == package.whole_word_catalog_names(dict(reversed(list(titles.items()))), suffixes, 30)


def test_collision_recovery_does_not_steal_another_workshops_name():
    titles = {
        "prediction": "Customer Sentiment Prediction",
        "monitoring": "Customer Sentiment Monitoring",
        "existing": "Customer Prediction",
    }
    result = package.whole_word_catalog_names(titles, {"manual": " Manual"}, 30)
    assert result["existing"]["manual"] == "Customer Prediction Manual"
    assert result["prediction"]["manual"] == "Sentiment Prediction Manual"
    assert len({names["manual"] for names in result.values()}) == 3


def test_app_collisions_follow_the_same_whole_word_rule_at_forty_characters():
    titles = {"prediction": "Customer Sentiment Prediction", "monitoring": "Customer Sentiment Monitoring"}
    result = package.whole_word_catalog_names(titles, {"manual": " Workspace Manual"}, 40)
    assert result["prediction"]["manual"] == "Customer Prediction Workspace Manual"
    assert result["monitoring"]["manual"] == "Customer Monitoring Workspace Manual"
    assert all(len(names["manual"]) <= 40 for names in result.values())


def test_fixed_live_names_are_never_changed_by_collision_recovery():
    titles = {"live": "Customer Sentiment", "new": "Customer Sentiment Prediction"}
    fixed = {"live": {"manual": "Customer Sentiment Manual"}}
    result = package.whole_word_catalog_names(titles, {"manual": " Manual"}, 30, fixed)
    assert result["live"] == fixed["live"]
    assert result["new"]["manual"] == "Customer Prediction Manual"


def test_an_overlong_single_word_is_not_cut_or_replaced_with_an_initial():
    with pytest.raises(package.StudioPackageError, match="cannot fit a whole word"):
        package.whole_word_name("ABCDEFGHIJKLMNOPQRSTUVWXYZ", " Manual", 30)


def test_all_51_planned_agent_and_app_names_are_unique_whole_words():
    titles = package.workshop_titles()
    assert len(titles) == 51
    for names, suffixes, limit in (
        (package.agent_names(), {"easy": " Studio", "manual": " Manual"}, 30),
        (package.app_names(), {"easy": " Workspace", "manual": " Workspace Manual"}, 40),
    ):
        flattened = [name for pair in names.values() for name in pair.values()]
        assert len(flattened) == 102
        assert len({name.casefold() for name in flattened}) == 102
        assert all(len(name) <= limit for name in flattened)
        for slug, pair in names.items():
            if slug == package.REFERENCE:
                continue
            for mode, name in pair.items():
                assert_title_words(name, titles[slug], suffixes[mode])
    assert package.agent_names()["asset-maintenance-forecast"]["manual"] == "Asset Maintenance Manual"
    assert package.agent_names()["emission-tracking"] == {
        "easy": "Emissions Tracking Studio", "manual": "Emissions Studio Manual",
    }


def test_committed_packages_use_the_planned_names_in_every_surface():
    agents, apps = package.agent_names(), package.app_names()
    for slug in package.data.studio_slugs():
        if slug == package.REFERENCE:
            continue
        base = ROOT / "solutions" / slug
        document = package.read_json(base / "studio/walkthrough.json")
        spec = package.read_json(base / "studio/managed-app/app.json")
        assert document["agent"]["names"] == agents[slug], slug
        assert document["app"]["names"] == apps[slug], slug
        assert spec["name"] == apps[slug]["easy"], slug
        page = (base / "studio-tutorial.html").read_text()
        assert html.escape(apps[slug]["manual"]) in page
        assert html.escape(agents[slug]["manual"]) in page
        assert any(f'--display-name "{apps[slug]["manual"]}"' in command
                   for step in document["modes"]["manual"]["steps"] for command in step.get("commands", []))
