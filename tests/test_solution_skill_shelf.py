"""Every industry solution with an agent file is on the skills shelf as one SKILL.md holding that agent unchanged."""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build_solution_shelf", ROOT / "tools" / "build_solution_shelf.py")
shelf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shelf)


def test_every_solution_agent_is_on_the_shelf_unchanged():
    problems, count = shelf.check()
    assert not problems, "\n".join(problems)
    assert count == len(shelf.solutions()) > 0


def test_the_agent_taken_out_of_each_shelf_file_answers_like_the_original():
    problems, count = shelf.smoke()
    assert not problems, "\n".join(problems)
    assert count == len(shelf.solutions())


def test_a_changed_agent_is_noticed(tmp_path, monkeypatch):
    slug, agent, _ = shelf.solutions()[0]
    md = shelf.shelf_files()[agent.name]
    copy = tmp_path / "skills" / md.parent.name / "SKILL.md"
    copy.parent.mkdir(parents=True)
    copy.write_text(md.read_text(encoding="utf-8").replace("def perform", "def  perform", 1), encoding="utf-8")
    for other in shelf.SHELF.glob("*/SKILL.md"):
        if other.parent.name != md.parent.name:
            (tmp_path / "skills" / other.parent.name).mkdir()
            (tmp_path / "skills" / other.parent.name / "SKILL.md").write_bytes(other.read_bytes())
    monkeypatch.setattr(shelf, "SHELF", tmp_path / "skills")
    problems, _ = shelf.check()
    assert any(p.startswith(slug + ":") and "no longer matches" in p for p in problems), problems
