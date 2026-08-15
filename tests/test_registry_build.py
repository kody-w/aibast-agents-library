"""Regression tests for deterministic, safe catalog generation."""

import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

import pytest

import build_rar
import build_registry
from tools import create_discussions, fetch_ratings
from tools import fetch_release_downloads

REPO_ROOT = Path(__file__).resolve().parent.parent


def _valid_manifest(name="@aibast-agents-library/test-agent"):
    return {
        "schema": "rapp-agent/1.0",
        "name": name,
        "version": "1.0.0",
        "display_name": "Test Agent",
        "description": "Provides a deterministic test capability.",
        "author": "AIBAST",
        "tags": ["test"],
        "category": "general",
    }


def _checked_in_registry():
    return json.loads((REPO_ROOT / "registry.json").read_text(encoding="utf-8"))


def _checked_in_rar_registry():
    return json.loads(
        (REPO_ROOT / "rar" / "registry.json").read_text(encoding="utf-8")
    )


def _checked_in_discussions():
    return json.loads(
        (REPO_ROOT / "rar" / "discussions.json").read_text(encoding="utf-8")
    )


def test_registry_build_exits_zero_from_a_non_root_directory(monkeypatch):
    """The script must find its catalog, not an arbitrary caller's agents/ tree."""
    monkeypatch.chdir(REPO_ROOT / "tests")

    assert build_registry.build_registry(write=False) == 0


def test_checked_in_registry_matches_current_sources():
    generated, errors = build_registry.collect_registry()
    checked_in = _checked_in_registry()

    assert not errors
    assert generated == checked_in


def test_manifest_parser_ignores_nested_manifest_assignments():
    source = """
def make_manifest():
    __manifest__ = {"name": "@aibast-agents-library/not-an-agent"}
"""

    manifest, errors = build_registry.extract_manifest_from_source(source)

    assert manifest is None
    assert errors == []


def test_manifest_parser_rejects_multiple_top_level_manifests():
    source = """
__manifest__ = {"name": "@aibast-agents-library/one"}
__manifest__ = {"name": "@aibast-agents-library/two"}
"""

    manifest, errors = build_registry.extract_manifest_from_source(source)

    assert manifest is None
    assert errors == ["Multiple top-level __manifest__ declarations"]


def test_manifest_validation_rejects_unsafe_names_and_invalid_metadata():
    manifest = _valid_manifest("@aibast-agents-library/../../outside")
    manifest["schema"] = "rapp-agent/9.9"
    manifest["tags"] = ["valid", ""]
    manifest["dependencies"] = "not-a-list"

    errors = build_registry.validate_manifest(REPO_ROOT / "agent.py", manifest)

    assert any("schema must be" in error for error in errors)
    assert any("Invalid name format" in error for error in errors)
    assert "tags must be a list of non-empty strings" in errors
    assert "dependencies must be a list of non-empty strings" in errors


def test_catalog_relative_path_rejects_files_outside_agents_directory():
    with pytest.raises(ValueError, match="agents directory"):
        build_registry.catalog_relative_path(REPO_ROOT / "build_registry.py")


def test_agent_discovery_does_not_follow_symbolic_link_directories(monkeypatch):
    calls = []

    def fake_walk(path, *, followlinks):
        calls.append((path, followlinks))
        yield str(REPO_ROOT / "agents"), [], ["z_agent.py", "a_agent.py"]

    monkeypatch.setattr(build_registry.os, "walk", fake_walk)

    paths = build_registry.iter_agent_files()

    assert calls == [(build_registry.AGENTS_DIR, False)]
    assert [path.name for path in paths] == ["a_agent.py", "z_agent.py"]


def test_duplicate_manifest_names_fail_before_registry_write(monkeypatch, capsys):
    paths = sorted((REPO_ROOT / "agents").rglob("*_agent.py"))[:2]
    manifests = iter(
        [
            _valid_manifest("@aibast-agents-library/duplicate"),
            _valid_manifest("@aibast-agents-library/duplicate"),
        ]
    )
    written = []

    monkeypatch.setattr(build_registry, "iter_agent_files", lambda: paths)
    monkeypatch.setattr(
        build_registry,
        "_extract_manifest_with_source",
        lambda _path: (next(manifests), [], "agent source\n"),
    )
    monkeypatch.setattr(
        build_registry, "write_registry", lambda registry: written.append(registry)
    )

    assert build_registry.build_registry() == 1
    assert written == []
    assert "Duplicate manifest name" in capsys.readouterr().out


def test_rar_rejects_paths_outside_the_catalog():
    with pytest.raises(ValueError, match="canonical repository-relative path"):
        build_rar.resolve_catalog_agent_path("../build_rar.py")


def test_stack_discovery_does_not_follow_symbolic_link_directories(monkeypatch):
    calls = []

    def fake_walk(path, *, followlinks):
        calls.append((path, followlinks))
        yield str(build_rar.AGENTS_DIR), [], []

    monkeypatch.setattr(build_rar.os, "walk", fake_walk)

    assert build_rar.iter_copilot_studio_manifests() == []
    assert calls == [(build_rar.AGENTS_DIR, False)]


def test_rar_build_is_deterministic_and_resolves_install_collisions():
    catalog = _checked_in_registry()
    colliding_agents = [
        agent
        for agent in catalog["agents"]
        if Path(agent["_file"]).name
        in {
            "ask_hr_agent.py",
            "dynamics_365_agent.py",
            "email_drafting_agent.py",
        }
    ]
    source = {
        "schema": "rapp-registry/1.0",
        "version": "1.0.0",
        "generated_at": "2026-08-07T14:22:13.450913+00:00",
        "stats": {"total_agents": len(colliding_agents)},
        "agents": colliding_agents,
    }

    first = build_rar.build_rar_registry(source)
    second = build_rar.build_rar_registry(source)
    filenames = [agent["_install_filename"] for agent in first["agents"]]

    assert len(colliding_agents) == 6
    assert first == second
    assert first["generated_at"] == source["generated_at"]
    assert len(filenames) == len(set(filenames))
    assert all(
        filename.endswith("_agent.py")
        and "/" not in filename
        and "\\" not in filename
        for filename in filenames
    )


def test_checked_in_rar_registry_has_unique_install_filenames():
    rar_registry = _checked_in_rar_registry()
    agents = rar_registry["agents"]
    assert rar_registry["instance"] == build_rar.AIBAST_RAR_INSTANCE
    assert rar_registry["repository"] == build_rar.AIBAST_RAR_REPOSITORY
    assert rar_registry["catalog_path"] == build_rar.AIBAST_RAR_CATALOG_PATH
    assert rar_registry["scope"] == "business-curated"
    filenames = [agent["_install_filename"] for agent in agents]
    duplicates = sorted(
        name for name, count in Counter(filenames).items() if count > 1
    )

    assert not duplicates, f"RAR install filename collisions: {duplicates}"
    assert all(
        filename.endswith("_agent.py")
        and "/" not in filename
        and "\\" not in filename
        for filename in filenames
    )
    for agent in agents:
        source = build_rar.resolve_catalog_agent_path(agent["_file"])
        assert agent["_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()


def test_checked_in_rar_timestamp_matches_its_source_registry():
    assert _checked_in_rar_registry()["generated_at"] == _checked_in_registry()[
        "generated_at"
    ]


def test_checked_in_rar_registry_matches_current_aibast_catalog():
    assert build_rar.build_rar_registry(
        _checked_in_registry()
    ) == _checked_in_rar_registry()


def test_checked_in_frontier_channel_matches_kernel_version():
    checked_in = json.loads(
        (REPO_ROOT / "rapp_brainstem" / "frontier-channel.json").read_text(
            encoding="utf-8"
        )
    )

    assert checked_in == build_rar.build_frontier_channel()
    assert checked_in["repository"] == "microsoft/aibast-agents-library"
    assert checked_in["subscription"]["default"] == "follow"


def test_brainstem_pinned_rar_snapshot_has_compatible_aibast_identity():
    source = (
        REPO_ROOT / "rapp_brainstem" / "brainstem.py"
    ).read_text(encoding="utf-8")
    revision = re.search(
        r'^RAR_REVISION = "([0-9a-f]{40})"$',
        source,
        flags=re.MULTILINE,
    )
    assert revision
    pinned = json.loads(
        subprocess.check_output(
            [
                "git",
                "show",
                f"{revision.group(1)}:rar/registry.json",
            ],
            cwd=REPO_ROOT,
            text=True,
            encoding="utf-8",
        )
    )

    assert pinned["instance"] == build_rar.AIBAST_RAR_INSTANCE
    assert pinned.get(
        "repository", build_rar.AIBAST_RAR_REPOSITORY
    ) == build_rar.AIBAST_RAR_REPOSITORY
    assert pinned.get(
        "catalog_path", build_rar.AIBAST_RAR_CATALOG_PATH
    ) == build_rar.AIBAST_RAR_CATALOG_PATH


def test_ratings_use_canonical_aibast_discussion_titles():
    name = "@aibast-agents-library/account-intelligence"
    slug = "account-intelligence"

    assert create_discussions.canonical_title(name) == name
    assert fetch_ratings.catalog_discussion(name) == (name, True)
    assert fetch_ratings.catalog_discussion(slug) == (name, False)
    assert fetch_ratings.catalog_discussion(f"[Acquisition] {name}") == (
        None,
        False,
    )


def test_legacy_discussion_slug_is_ignored_when_publishers_collide(monkeypatch):
    name = "@aibast-agents-library/account-intelligence"
    partner = "@partner/account-intelligence"
    monkeypatch.setattr(fetch_ratings, "CATALOG_NAMES", {name, partner})
    monkeypatch.setattr(
        fetch_ratings,
        "SLUG_TO_NAMES",
        {"account-intelligence": [name, partner]},
    )

    assert fetch_ratings.catalog_discussion(name) == (name, True)
    assert fetch_ratings.catalog_discussion(partner) == (partner, True)
    assert fetch_ratings.catalog_discussion("account-intelligence") == (
        None,
        False,
    )


def test_checked_in_discussion_map_uses_publisher_qualified_names():
    catalog_names = {
        agent["name"] for agent in _checked_in_rar_registry()["agents"]
    }
    discussions = _checked_in_discussions()

    assert set(discussions).issubset(catalog_names)
    assert all(name.startswith("@") and "/" in name for name in discussions)
    assert all(
        url.startswith(
            "https://github.com/microsoft/aibast-agents-library/discussions/"
        )
        for url in discussions.values()
    )


def test_release_assets_map_to_catalog_names_without_collisions():
    agents = _checked_in_rar_registry()["agents"]
    mapping = fetch_release_downloads.build_asset_agent_map(agents)

    for agent in agents:
        assert mapping[agent["_install_filename"]] == agent["name"]


def test_static_metric_consumers_prefer_canonical_names_with_legacy_fallback():
    metrics = (REPO_ROOT / "docs" / "metrics.html").read_text(encoding="utf-8")
    workshop = (REPO_ROOT / "docs" / "workshop.html").read_text(encoding="utf-8")
    brainstem = (
        REPO_ROOT / "rapp_brainstem" / "index.html"
    ).read_text(encoding="utf-8")

    assert "hasOwnProperty.call(values,a.name)" in metrics
    assert "return values[slug(a)]" in metrics
    assert "encodeURIComponent(r.key)" in metrics
    assert "hasOwnProperty.call(values,a.name)" in workshop
    assert "return values&&a?values[slugOf(a)]" in workshop
    assert "BYNAME[a.name]=a" in workshop
    assert "function rarValueForAgent(values, agent)" in brainstem
    assert "hasOwnProperty.call(values, agent.name)" in brainstem
