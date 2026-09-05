import copy
import hashlib
import importlib.util
import json
import os
import random
import stat
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip(
    "lisppy",
    reason="Install experiments/creature/requirements.txt to exercise the optional creature VM.",
)

from agents.experimental import genome_creature_agent as creature


def call(agent, **kwargs):
    return json.loads(agent.perform(**kwargs))


def make_agent(monkeypatch, base):
    monkeypatch.setenv("RAPP_CREATURE_DATA_DIR", str(base))
    return creature.GenomeCreatureAgent()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def raw_score_program(body, capabilities=None):
    enabled = capabilities or creature.CREATURE_PROFILE["capabilities"]
    return creature._value_repr(
        creature._definition_expression("score-move", enabled, body)
    )


def resign_egg(egg):
    payload = {
        "schema": creature.EGG_SCHEMA,
        "profile": egg["profile"],
        "state": egg["state"],
    }
    egg["checksum"] = hashlib.sha256(
        creature._canonical_json(payload)
    ).hexdigest()
    return creature._canonical_json(egg).decode("utf-8")


def materialize_profile_copy(tmp_path, module_name, profile):
    source = Path(creature.__file__).read_text(encoding="utf-8")
    start = source.index("CREATURE_PROFILE = {")
    end = source.index("\n\n\n__manifest__", start)
    materialized = source[:start] + f"CREATURE_PROFILE = {profile!r}" + source[end:]
    path = tmp_path / f"{module_name}_agent.py"
    path.write_text(materialized, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def assert_error(result, text=None):
    assert result["status"] == "error"
    assert set(result) == {"status", "error"}
    if text:
        assert text in result["error"]


def assert_trace_is_real(replay):
    food = {tuple(cell) for cell in replay["food"]}
    hazards = {tuple(cell) for cell in replay["hazards"]}
    trace = replay["trace"]
    assert trace[0] == {
        "step": 0,
        "x": creature.WORLD_WIDTH // 2,
        "y": creature.WORLD_HEIGHT // 2,
        "energy": creature.INITIAL_ENERGY,
        "collected": 0,
        "event": "start",
        "action": "start",
    }
    collected_positions = set()
    for index, frame in enumerate(trace[1:], 1):
        previous = trace[index - 1]
        assert frame["step"] == index
        assert abs(frame["x"] - previous["x"]) + abs(
            frame["y"] - previous["y"]
        ) == 1
        expected_energy = previous["energy"] - creature.MOVE_COST
        expected_collected = previous["collected"]
        position = (frame["x"], frame["y"])
        if frame["event"] == "food":
            assert position in food
            assert position not in collected_positions
            collected_positions.add(position)
            expected_energy += creature.FOOD_REWARD
            expected_collected += 1
        elif frame["event"] == "hazard":
            assert position in hazards
            expected_energy -= creature.HAZARD_COST
        else:
            assert frame["event"] == "move"
            assert position not in food - collected_positions
            assert position not in hazards
        assert frame["energy"] == max(0, expected_energy)
        assert frame["collected"] == expected_collected
    assert len(trace) <= creature.MAX_STEPS + 1
    assert replay["operations"] <= replay["operation_limit"]
    assert replay["attempted_operations"] >= replay["operations"]
    assert replay["attempted_operations"] <= replay["operations"] + 1


@pytest.fixture(scope="module")
def seed41_state():
    state = creature._new_state("Astra", 41, build_comparison=False)
    for _ in range(12):
        creature._advance_generation(state, build_comparison=False)
    state["comparison"] = creature._build_comparison(
        state, creature.COMPARISON_TRIALS
    )
    return state


def test_manifest_profile_attribution_constructor_and_rng(monkeypatch, tmp_path):
    root = tmp_path / "constructor"
    monkeypatch.setenv("RAPP_CREATURE_DATA_DIR", str(root))
    rng_state = random.getstate()

    agent = creature.GenomeCreatureAgent()

    assert not root.exists()
    assert agent.name == "AstraCreature"
    assert agent.profile == creature.CREATURE_PROFILE
    assert agent.store.root == root / "astra"
    assert creature.__manifest__["name"] == "@kody-w/genome-creature"
    assert creature.__manifest__["quality_tier"] == "community"
    assert creature.__manifest__["version"] == "3.0.0"
    assert creature.LISPPY_SOURCE_COMMIT in creature.__doc__
    assert creature.LISPPY_SOURCE_URL in creature.__doc__
    assert creature._vm_metadata()["name"] == "LispyVM core"
    assert creature._vm_metadata()["distribution"] == "rappterbook-lispy-runtime"
    assert random.getstate() == rng_state

    runtime = creature._load_runtime()
    assert runtime["facade"].DISTRIBUTION_NAME == "rappterbook-lispy-runtime"
    assert runtime["facade"].VERSION == "0.24.0"
    vm = runtime["LispyVM"](
        profile="core",
        trusted=False,
        load_stdlib=False,
        limits=creature._runtime_limits(),
        state_root=tmp_path / "vm-state",
    )
    result = vm.execute(
        "(begin (define (twice x) (+ x x)) (twice 7))"
    )
    assert result.ok is True
    assert result.value == 14
    assert result.usage == {"steps": 11, "peak_call_depth": 1}
    denied = vm.execute('(rb-run "x")')
    assert denied.ok is False
    assert "rb-run" in denied.error["message"]
    safe_env = runtime["lisp"].make_global_env(
        profile="core",
        trusted=False,
        load_stdlib=False,
        limits=creature._runtime_limits(),
        output=lambda _text: None,
        state_dir=tmp_path / "core-state",
    )
    assert {
        "curl",
        "py-import",
        "read-file",
        "write-file",
        "rb-state",
        "rb-run",
    }.isdisjoint(safe_env)

    assert call(agent, action="hatch", seed=41)["status"] == "ok"
    assert call(
        agent, action="evolve", generations=1, expected_generation=0
    )["status"] == "ok"
    assert random.getstate() == rng_state


def test_profile_validation_is_tight():
    valid = copy.deepcopy(creature.CREATURE_PROFILE)
    assert creature._validated_profile(valid) == valid
    invalid = copy.deepcopy(valid)
    invalid["id"] = "../escape"
    with pytest.raises(creature.CreatureError, match="profile.id"):
        creature._validated_profile(invalid)
    invalid = copy.deepcopy(valid)
    invalid["agent_name"] = "not a tool"
    with pytest.raises(creature.CreatureError, match="agent_name"):
        creature._validated_profile(invalid)
    invalid = copy.deepcopy(valid)
    invalid["capabilities"] = ["food", "curl"]
    with pytest.raises(creature.CreatureError, match="unknown sensor"):
        creature._validated_profile(invalid)
    invalid = copy.deepcopy(valid)
    invalid["capabilities"] = ["food", "food"]
    with pytest.raises(creature.CreatureError, match="duplicate sensor"):
        creature._validated_profile(invalid)


def test_metered_lispy_definitions_lambdas_and_lexical_scope_are_real():
    capabilities = creature.CREATURE_PROFILE["capabilities"]
    tool_body = [
        [creature.Symbol("lambda"), [creature.Symbol("v")],
         [creature.Symbol("+"), creature.Symbol("v"), 1]],
        [creature.Symbol("+"), creature.Symbol("hazard"), creature.Symbol("visited")],
    ]
    tool_source = creature._value_repr(
        creature._definition_expression("tool-g1-0", capabilities, tool_body)
    )
    score_body = [
        creature.Symbol("-"),
        [creature.Symbol("*"), creature.Symbol("food"), 6],
        [
            creature.Symbol("tool-g1-0"),
            *[creature.Symbol(name) for name in capabilities],
        ],
    ]
    source = creature._build_program([tool_source], score_body)
    program = creature.MeteredLispyProgram(source)
    runtime = program.start()
    sensors = {
        name: minimum for name, (minimum, _) in creature.SENSOR_RANGES.items()
    }
    sensors.update(food=1, hazard=1, visited=2)

    assert runtime.score_move(sensors) == 2
    assert runtime.definition_costs["tool-g1-0"] > 0
    assert runtime.definition_costs["score-move"] > 0
    assert runtime.meter.used > sum(runtime.definition_costs.values())
    assert program.tool_definitions[0]["name"] == "tool-g1-0"


@pytest.mark.parametrize(
    "body",
    [
        [creature.Symbol("curl"), 1],
        [creature.Symbol("py-import"), 1],
        [creature.Symbol("rb-state"), 1],
        [creature.Symbol("eval"), 1],
        [creature.Symbol("read-file"), 1],
        [creature.Symbol("write-file"), 1, 2],
        [creature.Symbol("dotimes"), [], 1],
        [creature.Symbol("set!"), creature.Symbol("food"), 1],
        [creature.Symbol("define-macro"), [], 1],
        [creature.Symbol("unknown"), 1],
    ],
)
def test_metered_lispy_rejects_host_meta_and_unbounded_forms(body):
    with pytest.raises(creature.LispSyntaxError):
        creature.MeteredLispyProgram(raw_score_program(body))


def test_metered_lispy_rejects_strings_floats_depth_size_and_forbidden_sensors():
    with pytest.raises(creature.LispSyntaxError, match="string"):
        creature.MeteredLispyProgram(
            raw_score_program("not executable")
        )
    source = raw_score_program(creature.Symbol("food")).replace(
        "food)", "1.25)", 1
    )
    with pytest.raises(creature.LispSyntaxError, match="floating"):
        creature.MeteredLispyProgram(source)
    with pytest.raises(creature.LispSyntaxError, match="integer literal"):
        creature.MeteredLispyProgram(raw_score_program(1001))
    with pytest.raises(creature.LispSyntaxError, match="character"):
        creature.MeteredLispyProgram(
            raw_score_program(1) + "\n;" + "x" * creature.MAX_PROGRAM_CHARS
        )

    deep = creature.Symbol("food")
    for _ in range(creature.MAX_FORM_DEPTH + 2):
        deep = [creature.Symbol("+"), deep, 1]
    with pytest.raises(creature.LispSyntaxError, match="depth"):
        creature.MeteredLispyProgram(raw_score_program(deep))

    limited = ["food", "distance"]
    forbidden = raw_score_program(creature.Symbol("hazard"), limited)
    with pytest.raises(creature.LispSyntaxError, match="unbound"):
        creature.MeteredLispyProgram(forbidden, limited)


def test_fuel_numeric_bounds_and_tool_overhead_are_metered():
    with pytest.raises(creature.FuelExhausted):
        creature.MeteredLispyProgram(creature.FOUNDER_PROGRAM).start(0)

    overflow = raw_score_program(
        [
            creature.Symbol("*"),
            [
                creature.Symbol("*"),
                creature.Symbol("energy"),
                creature.Symbol("energy"),
            ],
            [
                creature.Symbol("*"),
                creature.Symbol("energy"),
                creature.Symbol("energy"),
            ],
        ]
    )
    with pytest.raises(creature.LispSyntaxError, match="arithmetic can exceed"):
        creature.MeteredLispyProgram(overflow)

    capabilities = creature.CREATURE_PROFILE["capabilities"]
    body = [creature.Symbol("+"), creature.Symbol("hazard"), creature.Symbol("visited")]
    tool_source = creature._value_repr(
        creature._definition_expression("tool-g1-0", capabilities, body)
    )
    tool_program = creature._build_program(
        [tool_source],
        [
            creature.Symbol("tool-g1-0"),
            *[creature.Symbol(name) for name in capabilities],
        ],
    )
    inline_program = creature._build_program([], body)
    tool_runtime = creature.MeteredLispyProgram(tool_program).start()
    inline_runtime = creature.MeteredLispyProgram(inline_program).start()
    sensors = {
        name: minimum for name, (minimum, _) in creature.SENSOR_RANGES.items()
    }
    before_tool = tool_runtime.meter.used
    before_inline = inline_runtime.meter.used
    assert tool_runtime.score_move(sensors) == inline_runtime.score_move(sensors)
    assert (
        tool_runtime.meter.used - before_tool
        > inline_runtime.meter.used - before_inline
    )


def test_episode_energy_trace_and_operation_budget_are_actual():
    seed = creature._heldout_seeds(41, 1)[0]
    episode = creature._simulate_episode(
        creature.FOUNDER_PROGRAM, seed, include_trace=True
    )
    assert episode["steps"] == len(episode["trace"]) - 1
    assert episode["operations"] <= creature.OPERATION_LIMIT
    assert episode["termination"] in {
        "all_food",
        "energy_depleted",
        "step_limit",
        "fuel_exhausted",
    } or episode["termination"].startswith("vm_error:")
    assert_trace_is_real(
        {
            "food": episode["food_locations"],
            "hazards": episode["hazards"],
            "trace": episode["trace"],
            "operations": episode["operations"],
            "attempted_operations": episode["attempted_operations"],
            "operation_limit": episode["operation_limit"],
        }
    )


def test_status_hatch_and_generation_guards(monkeypatch, tmp_path):
    agent = make_agent(monkeypatch, tmp_path / "shared")
    missing = call(agent, action="status")
    assert missing["status"] == "ok"
    assert missing["snapshot"]["exists"] is False
    assert missing["snapshot"]["id"] == "astra"
    assert missing["snapshot"]["vm"]["name"] == "LispyVM core"
    assert missing["snapshot"]["public_file"] == "astra/public/snapshot.json"
    assert read_json(agent.store.snapshot_path)["comparison"] is None

    assert_error(call(agent, action="hatch", seed=True), "seed must be")
    assert_error(
        call(agent, action="hatch", name="Other", seed=41),
        "name must match",
    )
    assert call(agent, action="hatch", seed=41)["status"] == "ok"
    assert_error(call(agent, action="hatch"), "refuses to overwrite")
    assert_error(
        call(agent, action="evolve", generations=1, expected_generation=1),
        "expected_generation mismatch",
    )
    assert_error(
        call(agent, action="evolve", generations=13),
        "generations must be",
    )
    assert stat.S_IMODE(agent.store.state_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(agent.store.snapshot_path.stat().st_mode) == 0o644


def test_seed41_is_deterministic_monotonic_and_invents_a_real_tool(seed41_state):
    duplicate = creature._new_state("Astra", 41, build_comparison=False)
    for _ in range(12):
        creature._advance_generation(duplicate, build_comparison=False)
    duplicate["comparison"] = creature._build_comparison(
        duplicate, creature.COMPARISON_TRIALS
    )
    assert duplicate == seed41_state

    state = seed41_state
    full_scores = [entry["training"]["score"] for entry in state["lineage"]]
    primitive_scores = [
        entry["primitive_training"]["score"] for entry in state["lineage"]
    ]
    assert full_scores == sorted(full_scores)
    assert primitive_scores == sorted(primitive_scores)
    assert state["lineage"][0]["training"]["score"] == 9505
    assert state["training"]["score"] == 9513
    assert state["primitive_training"]["score"] == 9718
    assert state["memory"]["accepted_generations"] == 1
    assert state["memory"]["inventions_accepted"] == 1
    assert state["memory"]["tools_inherited"] == 1
    assert state["tools"][0]["id"] == "tool-g4-0"
    assert state["tools"][0]["source"] in state["program"]
    assert "(tool-g4-0 " in state["program"]
    assert state["genome_sha256"] == creature._genome_sha256(state["program"])


def test_lineage_diffs_invention_failures_and_dependency_tree_are_exact(
    seed41_state,
):
    state = seed41_state
    known_tools = set()
    for generation, entry in enumerate(state["lineage"][1:], 1):
        parent = state["lineage"][generation - 1]
        assert entry["parent_sha256"] == parent["genome_sha256"]
        assert entry["diff"] == creature._unified_diff(
            parent["program"], entry["program"], generation
        )
        assert entry["primitive_diff"] == creature._unified_diff(
            parent["primitive_program"],
            entry["primitive_program"],
            generation,
            primitive=True,
        )
        assert entry["mutations_tested"] == creature.MAX_CANDIDATES_PER_GENERATION
        assert (
            entry["primitive_mutations_tested"]
            == creature.MAX_CANDIDATES_PER_GENERATION
        )
        assert entry["selection_compute"]["candidates"] == (
            creature.MAX_CANDIDATES_PER_GENERATION
        )
        assert entry["primitive_selection_compute"]["budget"] == (
            entry["selection_compute"]["budget"]
        )
        assert entry["selection_compute"]["used"] <= entry["selection_compute"]["budget"]
        assert entry["selection_compute"]["diagnostic_budget"] == creature.DIAGNOSTIC_BUDGET
        assert entry["selection_compute"]["diagnostic_used"] == sum(
            item["diagnostic_compute"]["used"]
            for item in state["inventions"]
            if item["generation"] == entry["generation"]
        )
        assert entry["primitive_selection_compute"]["diagnostic_used"] == 0
        assert (
            entry["primitive_selection_compute"]["used"]
            <= entry["primitive_selection_compute"]["budget"]
        )
        if entry["accepted"]:
            assert entry["training"]["score"] > parent["training"]["score"]
            assert entry["diff"]
        else:
            assert entry["program"] == parent["program"]
            assert entry["diff"] == ""
        for tool in entry["tools"]:
            assert set(tool["depends_on"]) <= known_tools
            known_tools.add(tool["id"])

    assert len(state["inventions"]) == 12 * creature.TOOL_CANDIDATES_PER_GENERATION
    assert any(item["accepted"] for item in state["inventions"])
    assert any(item["reason"].startswith("failed:") for item in state["inventions"])
    assert any(item["depends_on"] for item in state["inventions"])
    assert all(item["source"].startswith("(define (tool-g") for item in state["inventions"])
    for invention in state["inventions"]:
        assert invention["reason"]
        assert isinstance(invention["depends_on"], list)
        if invention["accepted"]:
            assert invention["operation_cost"] > 0
            assert invention["definition_cost"] > 0
            assert invention["tool_id"] in {tool["id"] for tool in state["tools"]}
    assert state["memory"]["selection_compute_used"] > 0
    assert (
        state["memory"]["selection_compute_used"]
        <= state["memory"]["selection_compute_budget"]
    )


def test_equal_compute_comparison_is_fair_and_honest(seed41_state):
    comparison = seed41_state["comparison"]
    seeds = creature._heldout_seeds(41, creature.COMPARISON_TRIALS)
    assert comparison["seeds"] == seeds
    assert set(seeds).isdisjoint(creature._training_seeds(41))
    assert comparison["compute_budget"] == (
        creature.COMPARISON_TRIALS * creature.OPERATION_LIMIT
    )
    assert comparison["compute_used"]["primitive_only"] <= comparison["compute_budget"]
    assert comparison["compute_used"]["tool_enabled"] <= comparison["compute_budget"]
    primitive = creature._evaluate_program(
        seed41_state["primitive_program"], seeds
    )
    tools = creature._evaluate_program(seed41_state["program"], seeds)
    assert comparison["primitive_only"]["metrics"] == primitive["metrics"]
    assert comparison["tool_enabled"]["metrics"] == tools["metrics"]
    difference = tools["metrics"]["score"] - primitive["metrics"]["score"]
    assert comparison["improvement"] == difference == -7
    assert comparison["winner"] == "primitive_only"
    assert "(define (tool-" not in seed41_state["primitive_program"]


def test_race_uses_same_heldout_courses_and_real_replays(seed41_state):
    race = creature._build_race(seed41_state, 12)
    founder, descendant = race["replays"]
    heldout = creature._race_seeds(41, 12)
    assert set(heldout).isdisjoint(creature._heldout_seeds(41, creature.MAX_RACE_TRIALS))
    assert set(heldout).isdisjoint(creature._training_seeds(41))
    assert race["seeds"] == heldout
    assert founder["seed"] == descendant["seed"] == heldout[0]
    assert founder["food"] == descendant["food"]
    assert founder["hazards"] == descendant["hazards"]
    assert race["improvement"] == (
        race["descendant"]["score"] - race["ancestor"]["score"]
    )
    assert race["contestants"][0]["generation"] == 0
    assert race["contestants"][-1]["generation"] == 12
    assert_trace_is_real(founder)
    assert_trace_is_real(descendant)


def test_snapshot_contains_vm_tools_inventions_and_comparison(monkeypatch, tmp_path):
    agent = make_agent(monkeypatch, tmp_path / "snapshot")
    call(agent, action="hatch", seed=41)
    call(agent, action="evolve", generations=4, expected_generation=0)
    snapshot = read_json(agent.store.snapshot_path)
    required = {
        "schema",
        "exists",
        "profile",
        "id",
        "capabilities",
        "name",
        "seed",
        "generation",
        "program",
        "genome_sha256",
        "energy",
        "training",
        "limits",
        "memory",
        "lineage",
        "race",
        "egg",
        "resumed_from",
        "vm",
        "inventions",
        "tools",
        "comparison",
    }
    assert set(snapshot) == required
    assert snapshot["vm"] == creature._vm_metadata()
    assert snapshot["profile"] == creature.CREATURE_PROFILE
    assert snapshot["capabilities"] == creature.CREATURE_PROFILE["capabilities"]
    assert len(snapshot["inventions"]) == 16
    assert snapshot["tools"][0]["id"] == "tool-g4-0"
    assert snapshot["comparison"]["compute_budget"] > 0


def test_two_materialized_creatures_coexist_and_enforce_capabilities(
    monkeypatch, tmp_path
):
    sprout_profile = {
        "id": "sprout",
        "name": "Sprout",
        "agent_name": "SproutCreature",
        "capabilities": ["food", "distance"],
    }
    ember_profile = {
        "id": "ember",
        "name": "Ember",
        "agent_name": "EmberCreature",
        "capabilities": ["hazard", "visited", "edge", "dx", "dy"],
    }
    sprout = materialize_profile_copy(tmp_path, "sprout_creature", sprout_profile)
    ember = materialize_profile_copy(tmp_path, "ember_creature", ember_profile)
    shared = tmp_path / "shared"
    monkeypatch.setenv("RAPP_CREATURE_DATA_DIR", str(shared))
    sprout_agent = sprout.GenomeCreatureAgent()
    ember_agent = ember.GenomeCreatureAgent()
    assert sprout_agent.name == "SproutCreature"
    assert ember_agent.name == "EmberCreature"
    assert sprout_agent.store.root == shared / "sprout"
    assert ember_agent.store.root == shared / "ember"

    assert json.loads(sprout_agent.perform(action="hatch", seed=41))["status"] == "ok"
    assert json.loads(ember_agent.perform(action="hatch", seed=41))["status"] == "ok"
    assert json.loads(
        sprout_agent.perform(action="evolve", generations=1, expected_generation=0)
    )["status"] == "ok"
    assert json.loads(ember_agent.perform(action="status"))["generation"] == 0
    sprout_state = read_json(sprout_agent.store.state_path)
    ember_state = read_json(ember_agent.store.state_path)
    assert sprout_state["profile"] == sprout_profile
    assert ember_state["profile"] == ember_profile
    assert sprout_state["generation"] == 1
    assert ember_state["generation"] == 0

    with pytest.raises(sprout.LispSyntaxError, match="unbound"):
        sprout.MeteredLispyProgram(
            sprout._value_repr(
                sprout._definition_expression(
                    "score-move",
                    sprout_profile["capabilities"],
                    sprout.Symbol("hazard"),
                )
            ),
            sprout_profile["capabilities"],
        )
    with pytest.raises(ember.LispSyntaxError, match="unbound"):
        ember.MeteredLispyProgram(
            ember._value_repr(
                ember._definition_expression(
                    "score-move",
                    ember_profile["capabilities"],
                    ember.Symbol("food"),
                )
            ),
            ember_profile["capabilities"],
        )
    for entry in sprout_state["lineage"]:
        program = sprout.MeteredLispyProgram(entry["program"])
        assert set(program.capabilities) == {"food", "distance"}

    assert json.loads(sprout_agent.perform(action="export_egg"))["status"] == "ok"
    egg = sprout_agent.store.egg_path.read_text(encoding="utf-8")
    monkeypatch.setenv("RAPP_CREATURE_DATA_DIR", str(tmp_path / "different"))
    incompatible = ember.GenomeCreatureAgent()
    assert_error(
        json.loads(incompatible.perform(action="resume", egg_json=egg)),
        "egg profile 'sprout' is incompatible with 'ember'",
    )


def test_prepared_egg_resumes_by_content_id_without_model_roundtrip(monkeypatch, tmp_path, seed41_state):
    _, raw = creature._build_egg(seed41_state)
    egg_id = hashlib.sha256(raw).hexdigest()
    target = make_agent(monkeypatch, tmp_path / "prepared")
    inbox = target.store.root / "inbox"
    inbox.mkdir(parents=True)
    (inbox / f"{egg_id}.egg.json").write_bytes(raw)
    result = call(target, action="resume", egg_id=egg_id)
    assert result["status"] == "ok"
    restored = read_json(target.store.state_path)
    for key in creature.ALGORITHMIC_STATE_KEYS:
        assert restored[key] == seed41_state[key]
    assert restored["resumed_from"]["sha256"] == egg_id


def test_prepared_egg_rejects_paths_content_changes_and_symlinks(monkeypatch, tmp_path):
    target = make_agent(monkeypatch, tmp_path / "prepared")
    assert_error(call(target, action="resume", egg_id="../escape"), "SHA-256")
    inbox = target.store.root / "inbox"
    inbox.mkdir(exist_ok=True)
    egg_id = "a" * 64
    path = inbox / f"{egg_id}.egg.json"
    path.write_text("changed content")
    assert_error(call(target, action="resume", egg_id=egg_id), "content id")
    path.unlink()
    outside = tmp_path / "outside"
    outside.write_text("not an egg")
    path.symlink_to(outside)
    assert_error(call(target, action="resume", egg_id=egg_id), "unavailable")
    assert_error(call(target, action="resume", egg_id=egg_id, egg_json="{}"), "not both")
    assert not target.store.state_exists()
    assert outside.read_text() == "not an egg"


def test_failed_diagnostic_probe_still_charges_executed_steps(monkeypatch):
    monkeypatch.setattr(creature, "OPERATION_LIMIT", 7)
    definition, call_cost, used, attempted, error = creature._measure_tool_cost(
        creature.FOUNDER_PROGRAM, "score-move"
    )
    assert error
    assert used == 7
    assert attempted == 8
    assert definition > 0
    assert call_cost > 0


def test_export_resume_and_malicious_egg_validation(monkeypatch, tmp_path):
    source = make_agent(monkeypatch, tmp_path / "source")
    call(source, action="hatch", seed=41)
    call(source, action="evolve", generations=4, expected_generation=0)
    exported = call(source, action="export_egg")
    assert exported["status"] == "ok"
    egg_text = source.store.egg_path.read_text(encoding="utf-8")
    egg = json.loads(egg_text)
    assert egg["profile"] == creature.CREATURE_PROFILE
    assert egg["state"]["tools"][0]["source"] in egg["state"]["program"]

    resumed = make_agent(monkeypatch, tmp_path / "resumed")
    assert call(resumed, action="resume", egg_json=egg_text)["status"] == "ok"
    for key in creature.ALGORITHMIC_STATE_KEYS:
        assert read_json(resumed.store.state_path)[key] == egg["state"][key]
    assert_error(
        call(resumed, action="resume", egg_json=egg_text),
        "refuses to overwrite",
    )

    checksum_tamper = copy.deepcopy(egg)
    checksum_tamper["state"]["name"] = "Other"
    malicious = copy.deepcopy(egg)
    malicious_source = raw_score_program(
        [creature.Symbol("curl"), 1]
    )
    malicious["state"]["program"] = malicious_source
    malicious["state"]["genome_sha256"] = creature._genome_sha256(malicious_source)
    malicious["state"]["lineage"][-1]["program"] = malicious_source
    malicious["state"]["lineage"][-1][
        "genome_sha256"
    ] = creature._genome_sha256(malicious_source)
    false_history = copy.deepcopy(egg)
    false_history["state"]["inventions"][0]["accepted"] = not false_history[
        "state"
    ]["inventions"][0]["accepted"]

    cases = [
        ("malformed", "{", "valid bounded JSON"),
        (
            "duplicate",
            '{"schema":"one","schema":"two"}',
            "duplicate key",
        ),
        (
            "oversized",
            "x" * (creature.MAX_EGG_BYTES + 1),
            "byte limit",
        ),
        (
            "checksum",
            creature._canonical_json(checksum_tamper).decode(),
            "checksum mismatch",
        ),
        ("malicious", resign_egg(malicious), "unavailable function: curl"),
        (
            "history",
            resign_egg(false_history),
            "does not match deterministic history",
        ),
    ]
    for label, candidate, message in cases:
        target = make_agent(monkeypatch, tmp_path / f"reject-{label}")
        assert_error(call(target, action="resume", egg_json=candidate), message)
        assert not target.store.state_path.exists()


def test_fresh_process_resume_continuation_is_exact(monkeypatch, tmp_path):
    source = make_agent(monkeypatch, tmp_path / "uninterrupted")
    call(source, action="hatch", seed=41)
    call(source, action="evolve", generations=3, expected_generation=0)
    call(source, action="export_egg")
    egg_text = source.store.egg_path.read_text(encoding="utf-8")
    assert call(
        source, action="evolve", generations=2, expected_generation=3
    )["status"] == "ok"
    uninterrupted = read_json(source.store.state_path)

    resumed_base = tmp_path / "fresh"
    brainstem_root = Path(creature.__file__).resolve().parents[2]
    script = """
import json
import sys
from agents.experimental.genome_creature_agent import GenomeCreatureAgent

agent = GenomeCreatureAgent()
first = json.loads(agent.perform(action="resume", egg_json=sys.stdin.read()))
if first["status"] != "ok":
    raise SystemExit(json.dumps(first))
print(agent.perform(action="evolve", generations=2, expected_generation=3))
"""
    environment = os.environ.copy()
    environment["RAPP_CREATURE_DATA_DIR"] = str(resumed_base)
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(brainstem_root), environment.get("PYTHONPATH", "")]
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        input=egg_text,
        text=True,
        capture_output=True,
        env=environment,
        timeout=90,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert json.loads(completed.stdout.strip().splitlines()[-1])["status"] == "ok"
    continued = read_json(resumed_base / "astra" / "creature.json")
    for key in creature.ALGORITHMIC_STATE_KEYS | {"comparison"}:
        assert continued[key] == uninterrupted[key]


def test_concurrent_hatches_are_serialized(monkeypatch, tmp_path):
    base = tmp_path / "concurrent"
    brainstem_root = Path(creature.__file__).resolve().parents[2]
    script = """
from agents.experimental.genome_creature_agent import GenomeCreatureAgent
print(GenomeCreatureAgent().perform(action="hatch", seed=41))
"""
    environment = os.environ.copy()
    environment["RAPP_CREATURE_DATA_DIR"] = str(base)
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(brainstem_root), environment.get("PYTHONPATH", "")]
    )
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", script],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
        )
        for _ in range(2)
    ]
    results = []
    for process in processes:
        stdout, stderr = process.communicate(timeout=30)
        assert process.returncode == 0, stderr
        results.append(json.loads(stdout.strip()))
    assert sorted(item["status"] for item in results) == ["error", "ok"]
    assert any("refuses to overwrite" in item.get("error", "") for item in results)
    agent = make_agent(monkeypatch, base)
    assert call(agent, action="status")["generation"] == 0


def test_unexpected_errors_propagate(monkeypatch, tmp_path):
    agent = make_agent(monkeypatch, tmp_path / "unexpected")
    monkeypatch.setattr(agent.store, "state_exists", lambda: True)

    def explode():
        raise RuntimeError("unexpected storage failure")

    monkeypatch.setattr(agent.store, "read_state", explode)
    with pytest.raises(RuntimeError, match="unexpected storage failure"):
        agent.perform(action="status")
