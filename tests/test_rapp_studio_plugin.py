import json
import hashlib
import importlib.util
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "rapp-studio"


def test_marketplace_resolves_the_packaged_plugin():
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    entry = next(row for row in marketplace["plugins"] if row["name"] == "rapp-studio")
    assert (ROOT / entry["source"]).resolve() == PLUGIN
    manifest = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())
    assert manifest["name"] == entry["name"]
    assert manifest["version"] == entry["version"]
    assert (PLUGIN / "plugin.json").read_bytes() == (
        PLUGIN / ".claude-plugin/plugin.json"
    ).read_bytes()
    assert {path.name for path in PLUGIN.rglob("*.py")} == {"start-baseline.py"}
    assert not list(PLUGIN.rglob("*.mcs.yml"))


def test_command_resolves_the_skill_and_preserves_caller_arguments():
    command = (PLUGIN / "commands/convert.md").read_text()
    assert "$ARGUMENTS" in command
    skill_path = PLUGIN / "skills/rapp-to-studio/SKILL.md"
    assert "skills/rapp-to-studio/SKILL.md" in command
    frontmatter = skill_path.read_text().split("---", 2)[1]
    metadata = yaml.safe_load(frontmatter)
    assert metadata["name"] == "rapp-to-studio"
    assert "any explicitly selected group" in metadata["description"]
    for path in (PLUGIN / "agents").glob("*.md"):
        agent_metadata = yaml.safe_load(path.read_text().split("---", 2)[1])
        assert agent_metadata["name"] == path.stem


def test_workflow_delegates_authoring_and_requires_complete_native_evidence():
    skill = " ".join((PLUGIN / "skills/rapp-to-studio/SKILL.md").read_text().split())
    for specialist in (
        "mcs-assistant:copilot-studio-init",
        "mcs-assistant:copilot-studio-architect",
        "mcs-assistant:copilot-studio-manage",
    ):
        assert specialist in skill
    for contract in (
        "No Azure Functions",
        "Use Dataverse",
        "Every selected agent and public operation must be accounted for",
        "An unmappable behavior is an explicit blocker",
        "Do not import untrusted modules",
        "every required ledger row is `parity-passed`",
        "a successful `pac copilot pack` exit alone",
        "Keep the target Draft-only unless",
    ):
        assert contract in skill


def test_parity_compares_real_conversations_not_verbatim_text():
    command = (PLUGIN / "commands/parity.md").read_text()
    reviewer = (PLUGIN / "agents/response-parity-reviewer.md").read_text()
    assert "rapp-studio:response-parity-reviewer" in command
    for requirement in (
        "functional response parity",
        "Do not use lexical overlap",
        "same answer meaning",
        "real receipts",
        "later native invocation",
        '"verdict": "pass | fail | blocked"',
    ):
        assert requirement in reviewer


def test_functional_mismatches_require_plugin_repair_and_retest():
    skill = " ".join((PLUGIN / "skills/rapp-to-studio/SKILL.md").read_text().split())
    command = " ".join((PLUGIN / "commands/parity.md").read_text().split())
    for invariant in (
        "Mandatory compare / repair / retest loop",
        "Repeat while functional mismatches remain",
        "zero failed and zero blocked required cases",
        "Do not modify the source, weaken the rubric, drop difficult cases",
        "run the full required case set before declaring convergence",
        "reported as stalled",
    ):
        assert invariant in skill
    assert "existing Microsoft Architect session" in command
    assert "Rerun the shared cases after each repair" in command


def test_default_test_is_real_ootb_deployment_and_complete_operation_coverage():
    command = (PLUGIN / "commands/test.md").read_text()
    skill = (PLUGIN / "skills/test-ootb/SKILL.md").read_text()
    scenario = json.loads((PLUGIN / "examples/ootb/scenario.json").read_text())
    assert "No arguments means the complete OOTB deployment/parity example" in command
    assert "not an optional demonstration" in skill
    assert {row["tool"] for row in scenario["source"]["agents"]} == {
        "ManageMemory", "ContextMemory", "HackerNews", "LearnNew",
    }
    assert scenario["target"]["environment"] == "user-selected"
    assert scenario["target"]["publish"] is False
    assert scenario["target"]["publish_test_target_when_explicitly_approved"] is True
    assert scenario["target"]["durable_storage"] == "Dataverse"
    assert scenario["comparison"]["require_actual_local_chat"] is True
    assert scenario["comparison"]["require_actual_native_chat"] is True
    assert scenario["comparison"]["repair_target_until_pass"] is True
    assert scenario["comparison"]["modify_source_to_pass"] is False
    assert scenario["comparison"]["browser_testing"] == "optional"
    assert scenario["comparison"]["transport_preference"][0] == "direct-to-engine"
    ids = {row["id"] for row in scenario["cases"]}
    assert len(ids) == len(scenario["cases"])
    assert {
        "memory-per-turn-context", "memory-new-conversation", "memory-isolation",
        "hackernews-live", "learn-preview", "learn-create", "learn-list",
        "learn-invoke", "learn-new-conversation", "learn-duplicate",
        "learn-submit", "learn-swarm", "learn-delete", "learn-absent-after-delete",
    } <= ids
    for case in scenario["cases"]:
        assert set(case.get("depends_on", [])) <= ids
        assert case["requires"]


def test_baseline_helper_pins_sources_and_copies_no_credentials(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "rapp_baseline_test", PLUGIN / "scripts/start-baseline.py",
    )
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    source = tmp_path / "source"
    (source / "agents").mkdir(parents=True)
    rows = []
    for tool in ("ManageMemory", "ContextMemory", "HackerNews", "LearnNew"):
        relative = f"agents/{tool.lower()}_agent.py"
        data = f"# fixture: {tool}\n".encode()
        (source / relative).write_bytes(data)
        rows.append({"tool": tool, "path": relative, "sha256": hashlib.sha256(data).hexdigest()})
    (source / "soul.md").write_text("Synthetic baseline only.")
    (source / ".env").write_text("MUST_NOT_COPY=private")
    (source / ".copilot_token").write_text("MUST_NOT_COPY")
    scenario = {"source": {"agents": rows, "supporting_files": []}}
    run_dir = tmp_path / "run"
    record = helper.prepare(source, run_dir, scenario)
    assert set(record["agents"]) == {row["tool"] for row in rows}
    assert not (run_dir / ".env").exists()
    assert not (run_dir / ".copilot_token").exists()
    assert list((run_dir / "data").iterdir()) == []
    with pytest.raises(FileExistsError):
        helper.prepare(source, run_dir, scenario)


def test_baseline_helper_refuses_source_drift_before_creating_output(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "rapp_baseline_drift_test", PLUGIN / "scripts/start-baseline.py",
    )
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    scenario = json.loads((PLUGIN / "examples/ootb/scenario.json").read_text())
    with pytest.raises(ValueError, match="source hash"):
        helper.prepare(tmp_path, tmp_path / "run", scenario)
    assert not (tmp_path / "run").exists()
