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


# ── the model plug: the AI that hatched the Brainstem is its model ────────────
pspec = importlib.util.spec_from_file_location("brainstem_plug", ROOT / "docs" / "any-ai" / "plug.py")
plug = importlib.util.module_from_spec(pspec)
pspec.loader.exec_module(plug)


class FakeKernel:
    def call_copilot(self, messages, tools=None):
        return "original", "original"

    def call_copilot_stream(self, messages, tools=None, model=None):
        yield ("done", {})


TOOLS = [{"type": "function", "function": {"name": "Pipe", "description": "", "parameters": {}}},
         {"type": "function", "function": {"name": "PipeLong", "description": "", "parameters": {}}}]


def test_plug_swaps_both_model_calls_and_undo_puts_them_back():
    k = FakeKernel()
    before = (k.call_copilot, k.call_copilot_stream)
    undo = plug.use(k, lambda m, t: "hi", "me")
    resp, model = k.call_copilot([{"role": "user", "content": "x"}])
    assert model == "me" and resp["choices"][0]["message"] == {"role": "assistant", "content": "hi"}
    assert resp["choices"][0]["finish_reason"] == "stop"
    assert list(k.call_copilot_stream([])) == [("delta", "hi"), ("done", {"message": {"role": "assistant", "content": "hi"}, "model": "me", "finish_reason": "stop"})]
    undo()
    assert (k.call_copilot, k.call_copilot_stream) == before


def test_plug_shapes_a_tool_call_the_way_the_kernel_reads_it():
    k = FakeKernel()
    plug.use(k, lambda m, t: {"tool_calls": [{"function": {"name": "Pipe", "arguments": {"a": 1}}}]})
    resp, _ = k.call_copilot([], TOOLS)
    choice = resp["choices"][0]
    call = choice["message"]["tool_calls"][0]
    assert choice["finish_reason"] == "tool_calls" and choice["message"]["content"] is None
    assert call == {"id": "call_1", "type": "function", "function": {"name": "Pipe", "arguments": '{"a": 1}'}}


def test_stand_in_model_is_fixed_and_picks_the_longest_matching_agent():
    ask = lambda words: plug.scripted([{"role": "user", "content": words}], TOOLS)
    assert ask("use PipeLong")["tool_calls"][0]["function"]["name"] == "PipeLong"
    assert ask("use pipe")["tool_calls"][0]["function"]["name"] == "Pipe"
    assert ask("hello") == ask("hello") == {"content": "Stand-in model. You said: hello"}
    said = plug.scripted([{"role": "user", "content": "use Pipe"}, {"role": "tool", "content": "42"}], TOOLS)
    assert said == {"content": "The agent answered:\n42"}


def test_a_chat_that_differs_fails_and_one_the_reference_does_not_repeat_is_set_aside():
    chat = lambda words: {"chat": {"status": 200, "body": {"response": words}}, "stream": {"status": 200, "body": words}}
    ref, body, again = rec(), rec(), rec()
    for r in (ref, body, again):
        r["chats"] = {"no agent": chat("a"), "A": chat("b")}
    assert verdict(ref, body, again)[0] and "2 of 2 repeatable" in verdict(ref, body, again)[1]
    body["chats"]["A"] = chat("B")
    ok, text = verdict(ref, body, again)
    assert not ok and "chat 'A'" in text
    again["chats"]["A"] = chat("clock")
    ok, text = verdict(ref, body, again)
    assert ok and "1 of 1 repeatable" in text


# ── hatch: a chat AI drives the real /chat from outside, as its model ─────────
def test_hatch_manifest_is_current():
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "build_hatch_manifest.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_hatch_turn_runs_the_agent_once_and_records_it(tmp_path):
    import pytest
    pytest.importorskip("flask"); pytest.importorskip("flask_cors"); pytest.importorskip("dotenv"); pytest.importorskip("requests")
    import os, shutil
    kernel = tmp_path / "rapp_brainstem"
    shutil.copytree(ROOT / "rapp_brainstem", kernel, ignore=shutil.ignore_patterns("tests", "__pycache__", ".env"))
    agents = tmp_path / "agents"; agents.mkdir()
    shutil.copy(ROOT / "rapp_brainstem" / "agents" / "basic_agent.py", agents)
    (agents / "count_agent.py").write_text(
        "from agents.basic_agent import BasicAgent\nimport pathlib\n"
        "class CountAgent(BasicAgent):\n"
        "    def __init__(self):\n        self.name='Count'; self.metadata={'name':'Count','description':'counts','parameters':{'type':'object','properties':{}}}\n"
        "    def perform(self, **kw):\n        p=pathlib.Path(__file__).with_name('runs.txt'); p.write_text(p.read_text()+'x' if p.exists() else 'x'); return 'ran '+p.read_text()\n")
    env = dict(os.environ, BRAINSTEM_HOME=str(kernel), AGENTS_PATH=str(agents), HOME=str(tmp_path), USERPROFILE=str(tmp_path))
    hatch = lambda *a: json.loads(subprocess.run([sys.executable, str(ROOT / "docs" / "any-ai" / "hatch.py"), *a],
                                                 capture_output=True, text=True, cwd=tmp_path, env=env).stdout)
    first = hatch("ask", "count please")
    assert first["new_messages"][-1] == {"role": "user", "content": "count please"}
    assert [a["name"] for a in first["agents_you_may_call"]] == ["Count"]
    second = hatch("answer", json.dumps({"tool_calls": [{"function": {"name": "Count", "arguments": {}}}]}))
    assert second["new_messages"][-1]["role"] == "tool" and second["new_messages"][-1]["content"] == "ran x"
    assert "waiting" not in json.dumps(second)
    last = hatch("answer", "It ran once.")
    assert last["done"]["response"] == "It ran once." and last["done"]["agent_logs"] == "[Count] ran x"
    assert last["agents_that_ran"] == ["Count"] and (agents / "runs.txt").read_text() == "x"   # never run twice
    assert hatch("chat")["agents_that_ran"] == ["Count"]
