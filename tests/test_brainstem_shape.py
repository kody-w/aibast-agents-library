"""The shape test's verdict: what counts as the same Brainstem, and what does not."""
import copy, importlib.util, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("brainstem_shape", ROOT / "scripts" / "brainstem_shape.py")
shape = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shape)


def rec(python="3.11.18", platform="darwin"):
    tool = lambda n: {n: {"type": "function", "function": {"name": n, "description": "d", "parameters": {}}}}
    return {"python": python, "platform": platform, "kernel_import": "ok",
            "health": {"status": 200, "keys": ["agents", "status"]},
            "agents": {"a_agent.py": {"loaded": ["A"], "tools": tool("A"), "perform": {"A": {"type": "str", "text": "one"}}},
                       "b_agent.py": {"loaded": ["B"], "tools": tool("B"), "perform": {"B": {"type": "str", "text": "two"}}},
                       "c_agent.py": {"loaded": ["C"], "tools": tool("C")}}}


def verdict(ref, body, again=None, known=None):
    ok, lines = shape.compare(ref, body, again, known)
    return ok, "\n".join(lines)


def test_identical_records_are_the_same_shape():
    ok, text = verdict(rec(), rec("3.11.3", "emscripten"), rec())
    assert ok and "SAME SHAPE" in text and "2 of 2 repeatable" in text and "3 of 3" in text


def test_a_different_answer_fails():
    body = rec()
    body["agents"]["a_agent.py"]["perform"]["A"]["text"] = "ONE"
    ok, text = verdict(rec(), body, rec())
    assert not ok and "a_agent.py" in text


def test_an_answer_the_reference_does_not_repeat_is_set_aside_not_failed():
    again, body = rec(), rec()
    again["agents"]["b_agent.py"]["perform"]["B"]["text"] = "12:01"
    body["agents"]["b_agent.py"]["perform"]["B"]["text"] = "12:02"
    ok, text = verdict(rec(), body, again)
    assert ok and "1 of 1 repeatable" in text and "does not repeat itself: 1" in text


def test_an_agent_the_body_cannot_load_fails_unless_it_is_on_the_known_list():
    body = rec()
    body["agents"]["c_agent.py"] = {"loaded": [], "tools": {}}
    assert not verdict(rec(), body, rec())[0]
    ok, text = verdict(rec(), body, rec(), {"c_agent.py": "needs a package"})
    assert ok and "known, cannot run in this body: c_agent.py" in text


def test_a_known_entry_that_now_matches_must_be_removed():
    ok, text = verdict(rec(), rec(), rec(), {"c_agent.py": "needs a package"})
    assert not ok and "take it off the list" in text


def test_missing_agent_health_change_and_dead_kernel_all_fail():
    body = rec(); del body["agents"]["a_agent.py"]
    assert not verdict(rec(), body)[0]
    body = rec(); body["health"]["keys"] = ["status"]
    assert not verdict(rec(), body)[0]
    body = rec(); body["kernel_import"] = "ModuleNotFoundError: flask"
    assert not verdict(rec(), body)[0]


def test_the_known_list_names_real_agent_files():
    known = json.loads((ROOT / "tests" / "shape" / "in-page-known.json").read_text())
    names = {p.name for p in ROOT.rglob("*_agent.py")}
    assert known and all(k in names and v.strip() for k, v in known.items())


def test_command_line_exit_codes(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(rec())); bad = rec(); bad["agents"]["a_agent.py"]["perform"]["A"]["text"] = "x"
    b.write_text(json.dumps(bad))
    run = lambda *x: subprocess.run([sys.executable, str(ROOT / "scripts" / "brainstem_shape.py"), "compare", *map(str, x)], capture_output=True, text=True)
    assert run(a, a).returncode == 0 and run(a, b).returncode == 1
