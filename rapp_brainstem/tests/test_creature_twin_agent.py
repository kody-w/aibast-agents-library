import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("test_creature_twin", ROOT / "agents/experimental/creature_twin_agent.py")
twin = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(twin)
PROFILE = {
    "id": "astra",
    "name": "Astra",
    "agent_name": "AstraCreature",
    "capabilities": ["food", "hazard", "distance", "visited"],
}
TEMPLATE = f'"""Standalone test fixture."""\nCREATURE_PROFILE = {PROFILE!r}\nUNCHANGED = 42\n'


@pytest.fixture
def habitat(tmp_path, monkeypatch):
    home = tmp_path / "twin"
    home.mkdir()
    payload = home / "payload"
    payload.mkdir()
    template = payload / "genome_creature_agent.py"
    template.write_text(TEMPLATE)
    monkeypatch.setenv("RAPP_CREATURE_HOME", str(home))
    monkeypatch.setenv("RAPP_CREATURE_TEMPLATE", str(template))
    monkeypatch.setenv("RAPP_CREATURE_DATA_DIR", str(home / "data"))
    monkeypatch.setenv("AGENTS_PATH", str(home / "agents"))
    return home, twin.CreatureTwinAgent()


def call(agent, **arguments):
    return json.loads(agent.perform(**arguments))


def snapshot(home, creature_id, generation=12):
    directory = home / "data" / creature_id / "public"
    directory.mkdir(parents=True)
    path = directory / "snapshot.json"
    path.write_text(json.dumps({
        "schema": "rapp-creature/snapshot/1",
        "exists": True,
        "name": creature_id.title(),
        "generation": generation,
        "program": "(+ food 1)",
        "memory": {"meals": 8},
        "genome_sha256": "a" * 64,
        "capabilities": ["food"],
    }))
    return path


def test_constructor_does_not_write(tmp_path, monkeypatch):
    home = tmp_path / "untouched"
    monkeypatch.setenv("RAPP_CREATURE_HOME", str(home))
    twin.CreatureTwinAgent()
    assert not home.exists()


def test_introduce_two_standalone_files_with_distinct_capabilities(habitat):
    home, agent = habitat
    assert call(agent, action="introduce", id="ember", name="Ember", capabilities=["food"])["status"] == "ok"
    assert call(agent, action="introduce", id="moss", name="Moss", capabilities=["food", "hazard"])["status"] == "ok"
    rows = call(agent, action="inventory")["creatures"]
    assert [row["agent_name"] for row in rows] == ["EmberCreature", "MossCreature"]
    assert [row["capabilities"] for row in rows] == [["food"], ["food", "hazard"]]
    assert all(row["status"] == "unhatched" for row in rows)
    assert "UNCHANGED = 42" in (home / "agents/ember_agent.py").read_text()


def test_sleep_and_wake_preserve_all_history(habitat):
    home, agent = habitat
    call(agent, action="introduce", id="astra", name="Astra")
    evidence = snapshot(home, "astra")
    original = evidence.read_bytes()
    source = (home / "agents/astra_agent.py").read_bytes()
    assert call(agent, action="sleep", id="astra")["status"] == "ok"
    assert not (home / "agents/astra_agent.py").exists()
    assert (home / "dormant/astra_agent.py").read_bytes() == source
    assert call(agent, action="inventory")["creatures"][0]["status"] == "dormant"
    assert call(agent, action="wake", id="astra")["status"] == "ok"
    assert (home / "agents/astra_agent.py").read_bytes() == source
    assert evidence.read_bytes() == original


def test_external_file_add_and_move_are_observed(habitat, tmp_path):
    home, agent = habitat
    agents = home / "agents"
    agents.mkdir()
    (agents / "astra_agent.py").write_text(TEMPLATE)
    evidence = snapshot(home, "astra")
    assert call(agent, action="inventory")["creatures"][0]["status"] == "active"
    (agents / "astra_agent.py").rename(tmp_path / "astra_agent.py")
    entry = call(agent, action="inventory")["creatures"][0]
    assert entry["status"] == "dormant"
    assert entry["generation"] == 12
    assert evidence.exists()
    assert "restore the original file" in entry["problem"]
    (tmp_path / "astra_agent.py").rename(agents / "astra_agent.py")
    assert call(agent, action="inventory")["creatures"][0]["status"] == "active"


def test_missing_loaded_tool_is_not_reported_alive(habitat):
    home, agent = habitat
    call(agent, action="introduce", id="astra")
    snapshot(home, "astra")
    entry = twin.inventory(home / "agents", home / "dormant", home / "data", [])["creatures"][0]
    assert entry["status"] == "unavailable"


@pytest.mark.parametrize("identifier", ["../other", "bad/id", "Astra", "", 7, True, "basic", "creature_twin", "red_fox", "4astra"])
def test_invalid_identity_cannot_create_host_files(habitat, identifier):
    home, agent = habitat
    result = call(agent, action="introduce", id=identifier)
    assert result["status"] == "error"
    assert not (home / "agents").exists()


@pytest.mark.parametrize("capabilities", [["network"], [], ["food", "food"], [dict(command="run")], "food"])
def test_capability_requests_are_bounded(habitat, capabilities):
    _, agent = habitat
    assert call(agent, action="introduce", id="astra", capabilities=capabilities)["status"] == "error"


def test_profile_interpolation_cannot_escape_into_python(habitat):
    home, agent = habitat
    name = "Astra'; raise RuntimeError('not executed') #"
    assert call(agent, action="introduce", id="astra", name=name)["status"] == "error"
    assert not (home / "agents/astra_agent.py").exists()


def test_existing_and_dormant_agents_are_not_replaced(habitat):
    home, agent = habitat
    call(agent, action="introduce", id="astra")
    original = (home / "agents/astra_agent.py").read_bytes()
    assert call(agent, action="introduce", id="astra")["status"] == "error"
    call(agent, action="sleep", id="astra")
    assert call(agent, action="introduce", id="astra")["status"] == "error"
    assert (home / "dormant/astra_agent.py").read_bytes() == original


def test_tool_name_collision_is_rejected(habitat):
    _, agent = habitat
    assert call(agent, action="introduce", id="red-fox")["status"] == "ok"
    result = call(agent, action="introduce", id="red--fox")
    assert result["status"] == "error"
    assert "tool name" in result["error"]


def test_malformed_file_and_wrong_filename_are_visible(habitat):
    home, agent = habitat
    agents = home / "agents"
    agents.mkdir()
    (agents / "broken_agent.py").write_text("CREATURE_PROFILE = {")
    (agents / "other_agent.py").write_text(TEMPLATE)
    result = call(agent, action="inventory")
    assert result["status"] == "ok"
    assert len(result["issues"]) == 2
    assert result["creatures"] == []


def test_corrupt_snapshot_is_not_success_shaped(habitat):
    home, agent = habitat
    call(agent, action="introduce", id="astra")
    evidence = snapshot(home, "astra")
    evidence.write_text("{broken")
    catalog = call(agent, action="inventory")
    assert catalog["issues"]
    assert not catalog["creatures"]


def test_template_does_not_execute_during_introduction(habitat):
    home, agent = habitat
    sentinel = home / "must-not-exist"
    template = home / "payload/genome_creature_agent.py"
    template.write_text(TEMPLATE + f"__import__('pathlib').Path({str(sentinel)!r}).touch()\n")
    assert call(agent, action="introduce", id="astra")["status"] == "ok"
    assert not sentinel.exists()


def test_symlink_agents_are_not_followed(habitat, tmp_path):
    home, agent = habitat
    original = tmp_path / "original.py"
    original.write_text(TEMPLATE)
    (home / "agents").mkdir()
    (home / "agents/astra_agent.py").symlink_to(original)
    result = call(agent, action="sleep", id="astra")
    assert result["status"] == "error"
    assert original.read_text() == TEMPLATE


def test_profile_must_be_data_not_an_expression():
    with pytest.raises(twin.CreatureTwinError, match="literal"):
        twin.source_profile("CREATURE_PROFILE = dict(id='astra')")


def test_inventory_never_runs_arbitrary_agent_source(habitat):
    home, agent = habitat
    (home / "agents").mkdir()
    sentinel = home / "no-execution"
    (home / "agents/astra_agent.py").write_text(TEMPLATE + f"open({str(sentinel)!r}, 'w').close()\n")
    assert len(call(agent, action="inventory")["creatures"]) == 1
    assert not sentinel.exists()


def test_profile_contract_agrees_with_actual_creature():
    from agents.experimental import genome_creature_agent

    profile = genome_creature_agent.CREATURE_PROFILE
    for creature_id, name, tool in (
        ("astra", "Astra", "AstraCreature"),
        ("red-fox", "Red Fox_2", "Red-Fox_Creature"),
    ):
        candidate = {**profile, "id": creature_id, "name": name, "agent_name": tool}
        assert twin.checked_profile(candidate) == genome_creature_agent._validated_profile(candidate)
    for update in ({"id": "with_underscore"}, {"id": "42"}, {"name": "bad\nname"}, {"extra": "not part of profile"}):
        with pytest.raises(twin.CreatureTwinError):
            twin.checked_profile({**profile, **update})
        with pytest.raises(genome_creature_agent.CreatureError):
            genome_creature_agent._validated_profile({**profile, **update})
