import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gallery_to_workshop", ROOT / "tools/gallery_to_workshop.py")
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)

HAND_RUNS = ("contract-compliance-reviewer", "invoice-processing", "team-ideas-board")
NEW_RUNS = ("meeting-coordinator", "customer-support-triage", "project-status-narrator")


def records_path(root, slug):
    return root / f"solutions/{slug}/manual/knowledge/aibast_{slug}-synthetic-records.md"


@pytest.fixture
def workspace(tmp_path):
    for relative in (
        "tools/gallery_to_workshop.py", "tools/agent_to_package.py",
        "rapp_brainstem/agents/basic_agent.py",
        "agents/@aibast-agents-library/templates/basic_agent.py",
        "solutions/invoice-processing/README.md", "solutions/invoice-processing/deployment.json",
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    (tmp_path / pipeline.LIBRARY / "general_stacks").mkdir()
    for slug in NEW_RUNS:
        relative = f"federation/copilot-studio-gallery/{slug}"
        shutil.copytree(ROOT / relative, tmp_path / relative, ignore=shutil.ignore_patterns("__pycache__"))
    return tmp_path


@pytest.mark.parametrize("slug", HAND_RUNS)
def test_hand_runs_are_byte_identical(slug):
    planned, notices = pipeline.plan(ROOT, slug, records=records_path(ROOT, slug))
    assert pipeline.changes(ROOT, planned) == {}
    assert any("every evidence section is non-empty" in notice for notice in notices)
    assert "metadata.description" in "\n".join(notices)


@pytest.mark.parametrize("slug", NEW_RUNS)
def test_json_drafts_have_grounded_evidence_and_no_validation_claims(workspace, slug):
    records = workspace / "authored.md"
    records.write_text("# Fictional records\n\nAuthored fixture, not generated from the agent.\n")
    planned, notices = pipeline.plan(workspace, slug, "general", records)
    agent_path = next(path for path in planned if path.suffix == ".py")
    assert f"general_stacks/{agent_path.stem.removesuffix('_agent')}_stack" in str(agent_path)
    assert pipeline.FALLBACK in planned[agent_path].decode()
    agent_file = workspace / "load_agent.py"
    agent_file.write_bytes(planned[agent_path])
    module, agent = pipeline.load_agent(agent_file, workspace)
    assert module.__manifest__["category"] == "general"
    cases = json.loads(planned[Path(f"tests/demo_cases/{slug}.json")])
    assert 1 <= len(cases["cases"]) <= 2
    for case in cases["cases"]:
        guide = module.OPERATION_GUIDE[case["operation"]]
        assert case["persona"] == "TODO persona"
        assert case["prompt"] == guide["ask"]
        assert case["arguments"] == {"operation": case["operation"], **guide.get("args", {})}
        output = agent.perform(**case["arguments"])
        assert output.startswith("{")
        assert 1 <= len(case["must_include"]) <= 3
        assert all(item in output for item in case["must_include"])
    skills = {path: data.decode() for path, data in planned.items() if path.name == "SKILL.md"}
    assert len(skills) == len(module.OPERATION_GUIDE)
    for text in skills.values():
        section = text.split("## Deterministic pilot evidence\n")[1].split("\n## ")[0]
        assert "- `" in section
    assert planned[Path(f"solutions/{slug}/manual/knowledge/aibast_{slug}-synthetic-records.md")] == records.read_bytes()
    deployment = json.loads(planned[Path(f"solutions/{slug}/deployment.json")])
    assert "validated_" not in json.dumps(deployment)
    assert deployment["copilot_studio"]["required_connections"] == [pipeline.TODO]
    assert deployment["copilot_studio"]["manual_skill_count"] == len(module.OPERATION_GUIDE)
    assert deployment["smoke_test"]["arguments"] == cases["cases"][0]["arguments"]
    assert deployment["smoke_test"]["must_call"] == agent.name
    assert deployment["source_path"] == str(agent_path)
    readme = planned[Path(f"solutions/{slug}/README.md")].decode()
    assert str(agent_path) in readme
    assert f"## Scope\n\n{pipeline.TODO}\n" in readme
    assert f"## Approval boundary\n\n{pipeline.TODO}\n" in readme
    assert "validated" not in readme.lower()
    assert "71 resources ready" not in readme
    assert not (workspace / agent_path).exists()
    assert not list(workspace.rglob("*.pyc"))
    assert "Transcripts NOT recorded." in "\n".join(notices)


def test_records_gate_stops_before_packaging(workspace, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("packager must not run without authored records")

    monkeypatch.setattr(pipeline.subprocess, "run", forbidden)
    planned, notices = pipeline.plan(workspace, "meeting-coordinator", "general")
    draft = planned[Path("solutions/meeting-coordinator/RECORDS-DRAFT.md")].decode()
    assert "DRAFT" in draft and "authored, not derived" in draft
    assert not any(path.name in ("SKILL.md", "README.md", "deployment.json") for path in planned)
    assert "STOP before stage 5" in "\n".join(notices)


@pytest.mark.parametrize("vertical", (None, "invented", "../general"))
def test_refuses_unknown_verticals(workspace, vertical):
    with pytest.raises(ValueError, match="vertical|does not exist"):
        pipeline.plan(workspace, "meeting-coordinator", vertical)


@pytest.mark.parametrize("slug", ("../meeting-coordinator", "missing", "/tmp/anything"))
def test_refuses_invalid_or_missing_slug(workspace, slug):
    with pytest.raises(ValueError, match="slug|expected one gallery"):
        pipeline.plan(workspace, slug, "general")


def test_reuses_existing_library_folder_and_keeps_authored_files(workspace):
    slug = "meeting-coordinator"
    existing = pipeline.LIBRARY / "general_stacks/authored_folder_stack/meeting_coordinator_agent.py"
    source = next((workspace / f"federation/copilot-studio-gallery/{slug}").glob("*_agent.py"))
    (workspace / existing).parent.mkdir(parents=True)
    (workspace / existing).write_text(pipeline.normalized_source(source.read_text(), "general"))
    case_path = workspace / f"tests/demo_cases/{slug}.json"
    case_path.parent.mkdir(parents=True)
    authored = {"cases": [{"persona": "Coordinator", "prompt": "My authored ask",
                          "must_include": ["2026-11-02"], "arguments": {"operation": "score_votes"}}]}
    case_path.write_text(json.dumps(authored))
    solution = workspace / f"solutions/{slug}"
    solution.mkdir(parents=True)
    (solution / "README.md").write_text("authored README\n")
    (solution / "deployment.json").write_text('{"validated_manual": "keep existing"}\n')
    records = workspace / "records.md"
    records.write_text("authored records")
    before = {path: path.read_bytes() for path in (case_path, solution / "README.md", solution / "deployment.json")}
    planned, notices = pipeline.plan(workspace, slug, records=records)
    assert existing in planned
    assert all(path.relative_to(workspace) not in planned for path in before)
    assert all(path.read_bytes() == data for path, data in before.items())
    assert "draft differences: persona, prompt, must_include" in "\n".join(notices)
    with pytest.raises(ValueError, match="existing library agent"):
        (workspace / pipeline.LIBRARY / "other_stacks").mkdir()
        pipeline.plan(workspace, slug, "other")


def test_conflict_requires_an_exact_existing_resolution():
    source = "before\n<<<<<<< HEAD\nleft\n=======\nright\n>>>>>>> branch\nafter\n"
    notices = []
    assert pipeline.resolved_source(source, "before\nright\nafter\n", notices) == "before\nright\nafter\n"
    assert notices and "WARNING" in notices[0]
    for existing in (None, "unrelated\n", "before\nleft\nchanged\n"):
        with pytest.raises(ValueError, match="unresolved conflicts"):
            pipeline.resolved_source(source, existing, [])


def test_json_evidence_uses_nested_identity_strings_not_numbers():
    output = json.dumps({"amount": 1234.56, "count": 3, "approved": True,
                         "records": [{"id": "REQ-42", "title": "Repair loading bay"},
                                     {"id": "REQ-43", "title": "Night shift"}]})
    assert pipeline.agent_to_package.evidence(output) == ["REQ-42", "Repair loading bay", "REQ-43"]
    assert pipeline.case_evidence(output) == ["REQ-42", "Repair loading bay", "REQ-43"]
    assert pipeline.agent_to_package.evidence('{"amount": 1234, "count": 3}') == []


def test_case_evidence_ignores_amounts_and_count_words():
    output = ("| Record | Total |\n|---|---|\n| $1,234.50 | total |\n| 3 findings | all |\n"
              "| REQ-01 | yes |\n\n- **Authored title**\n"
              "On 2026-11-03 INV-42 was reviewed. 6 of 7 findings shown.")
    assert pipeline.case_evidence(output) == ["REQ-01", "Authored title", "2026-11-03"]


def test_empty_skill_evidence_aborts_before_writing(workspace, monkeypatch):
    records = workspace / "records.md"
    records.write_text("authored")
    real_run = pipeline.subprocess.run

    def empty_skill(command, **kwargs):
        result = real_run(command, **kwargs)
        package = Path(command[5])
        skill = next((package / "manual/skills").glob("*/SKILL.md"))
        text = skill.read_text()
        start, rest = text.split("## Deterministic pilot evidence\n")
        _, end = rest.split("## Safety gate", 1)
        skill.write_text(start + "## Deterministic pilot evidence\n\n## Safety gate" + end)
        return result

    monkeypatch.setattr(pipeline.subprocess, "run", empty_skill)
    with pytest.raises(ValueError, match="empty evidence"):
        pipeline.plan(workspace, "meeting-coordinator", "general", records)
    assert not (workspace / "solutions/meeting-coordinator").exists()


def snapshot(root):
    return {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def test_cli_dry_run_writes_nothing_and_write_is_idempotent(workspace):
    slug = "meeting-coordinator"
    records = workspace / "records.md"
    records.write_text("# Authored fictional records\n")
    command = [sys.executable, "-B", str(workspace / "tools/gallery_to_workshop.py"),
               slug, "--vertical", "general", "--records", str(records)]
    before = snapshot(workspace)
    dry = subprocess.run(command, capture_output=True, text=True)
    assert dry.returncode == 0, dry.stderr
    assert "--- /dev/null" in dry.stdout
    assert snapshot(workspace) == before
    written = subprocess.run(command + ["--write"], capture_output=True, text=True)
    assert written.returncode == 0, written.stderr
    assert "Wrote " in written.stdout
    after = snapshot(workspace)
    assert after != before
    repeat = subprocess.run(command, capture_output=True, text=True)
    assert repeat.returncode == 0, repeat.stderr
    assert "Diff: EMPTY" in repeat.stdout
    assert snapshot(workspace) == after
    inside = records_path(workspace, slug)
    command[command.index("--records") + 1] = str(inside)
    rerun = subprocess.run(command + ["--write"], capture_output=True, text=True)
    assert rerun.returncode == 0, rerun.stderr
    assert "Wrote 0 file(s)." in rerun.stdout
    assert inside.read_bytes() == records.read_bytes()
