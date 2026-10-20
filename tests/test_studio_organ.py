"""Send to Copilot Studio: the translation rule, its outputs, and the switch agent.

Offline: no Copilot Studio, no sign-in, no network. Web answers are recorded,
workflow tools are fakes, and the Brainstem is a copy of rapp_brainstem/ run with
the kernel's own Python (this one when it has flask and requests, else
RAPP_KERNEL_PYTHON, else those tests skip).
"""

import hashlib
import json
import re
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import zipfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
KERNEL = REPO_ROOT / "rapp_brainstem"
BUNDLED = KERNEL / "agents"
ORGAN_DIR = REPO_ROOT / "organs/studio"
SWITCH_AGENT = REPO_ROOT / "agents/@aibast-agents-library/templates/studio_organ_agent.py"
PINS = Path(__file__).with_name("offline_kernel.sha256")
ORGAN_NAME = "@aibast-agents-library/studio-organ"

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(ORGAN_DIR))
import build_registry  # noqa: E402
import send_to_studio  # noqa: E402
import studio_organ  # noqa: E402

FOUR = ["basic_agent.py", "context_memory_agent.py", "hacker_news_agent.py", "manage_memory_agent.py"]

PURE_AGENT = '''
import math
from agents.basic_agent import BasicAgent


class CircleAgent(BasicAgent):
    def __init__(self):
        self.name = "Circle"
        self.metadata = {"name": self.name, "description": "Area of a circle.",
                         "parameters": {"type": "object", "properties": {
                             "radius": {"type": "number", "description": "The radius."}}, "required": ["radius"]}}
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, radius=1, **kwargs):
        return f"area {math.pi * float(radius) ** 2:.4f}"
'''

TOP = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM = "https://hacker-news.firebaseio.com/v0/item/{}.json"
RECORDED = {TOP: [9001, 9002, 9003, 9004]}
RECORDED.update({ITEM.format(i): {"id": i, "title": f"Story {i}", "by": f"user{i}", "score": i - 8990,
                                  "descendants": i % 7, **({"url": f"https://example.org/{i}"} if i % 2 else {})}
                 for i in (9001, 9002, 9003, 9004)})
MEMORY_DOC = json.dumps({"m1": {"message": "Prefers tea", "theme": "preference", "date": "2026-10-01",
                                "time": "09:00:00"},
                         "m2": {"message": "Works in Denver", "theme": "fact", "date": "2026-10-02",
                                "time": "10:00:00"}}, indent=2)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


@pytest.fixture(scope="module")
def agents_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("agents")
    for name in FOUR:
        shutil.copy(BUNDLED / name, d / name)
    (d / "circle_agent.py").write_text(PURE_AGENT, encoding="utf-8")
    shutil.copy(SWITCH_AGENT, d / "studio_organ_agent.py")  # an organ switch: stays with the Brainstem
    return d


def _by_file(p):
    return {a["file"]: a for a in p["agents"]}


def _flipped(**changes):
    profile = studio_organ.load_profile()
    for section, value in changes.items():
        profile[section] = dict(profile[section], **value)
    return profile


# ── the rule ────────────────────────────────────────────────────────────────

def test_plan_routes_each_need_by_the_profile(agents_dir):
    p = _by_file(studio_organ.plan(agents_dir))
    assert "studio_organ_agent.py" not in p

    hn = p["hacker_news_agent.py"]
    http = [t for t in hn["workflow_tools"] if t["kind"] == "http"]
    assert [t["request"]["uri"] for t in http] == [TOP, ITEM.replace("{}", "{sid}")]
    for t in http:
        action = t["definition"]["properties"]["definition"]["actions"]["Call_the_API"]
        assert action["type"] == "Http" and action["inputs"]["method"] == "GET"
        assert set(action["inputs"]) == {"method", "uri", "queries"}
    assert hn["parts"][0] == {"need": "the agent's Python logic", "goes_to": "skill",
                              "why": "the sandbox runs Python 3.12 (profile 2026.10.20)"}
    assert all("No outbound network" in x["why"] for x in hn["parts"] if x["goes_to"] == "workflow tool")
    assert hn["ready"] and hn["skill"] == "hacker-news"

    cm, mm = p["context_memory_agent.py"], p["manage_memory_agent.py"]
    assert [t["kind"] for t in cm["workflow_tools"]] == ["dataverse_read"]
    assert [t["kind"] for t in mm["workflow_tools"]] == ["dataverse_read", "dataverse_save"]
    assert {t["table"] for t in cm["workflow_tools"] + mm["workflow_tools"]} == {"rapp_brainstemmemory"}
    save = mm["workflow_tools"][1]["definition"]["properties"]["definition"]["actions"]
    ops = json.dumps(save)
    assert all(op in ops for op in ("ListRecords", "CreateRecord", "UpdateRecord"))
    assert "Nothing persists" in mm["parts"][-1]["why"]

    for pure in ("basic_agent.py", "circle_agent.py"):
        assert p[pure]["workflow_tools"] == [] and p[pure]["ready"]
        assert {x["goes_to"] for x in p[pure]["parts"]} == {"skill"}


def test_changing_the_profile_changes_the_plan_with_no_code_change(agents_dir):
    net = _by_file(studio_organ.plan(agents_dir, _flipped(network={"outbound": True})))
    assert net["hacker_news_agent.py"]["workflow_tools"] == []
    assert "http" not in net["hacker_news_agent.py"]["routes"]
    assert len(net["manage_memory_agent.py"]["workflow_tools"]) == 2  # persistence is still no
    kept = _by_file(studio_organ.plan(agents_dir, _flipped(persistence={"across_conversations": True})))
    assert kept["manage_memory_agent.py"]["workflow_tools"] == []
    assert len(kept["hacker_news_agent.py"]["workflow_tools"]) == 2


def test_needs_the_sandbox_cannot_meet_without_a_tool_hold_the_agent_back(tmp_path):
    (tmp_path / "poster_agent.py").write_text(PURE_AGENT.replace("import math", "import math, os, requests")
                                              .replace("return f\"area", "requests.post('https://x.example/a')\n"
                                                       "        os.getenv('API_KEY')\n        return f\"area"),
                                              encoding="utf-8")
    a = studio_organ.plan(tmp_path)["agents"][0]
    held = [x["need"] for x in a["parts"] if x["goes_to"] == "held back"]
    assert not a["ready"] and held == ["POST https://x.example/a", "setting API_KEY"]
    assert a["workflow_tools"] == []


# ── the workspace ───────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def workspace(agents_dir, tmp_path_factory):
    out = tmp_path_factory.mktemp("ws") / "workspace"
    m = studio_organ.build(agents_dir, out, soul=KERNEL / "soul.md", name="Test Copilot")
    unpacked = out.parent / "unpacked"
    for a in m["agents"]:
        with zipfile.ZipFile(out / a["skill_zip"]) as z:
            z.extractall(unpacked)
    return {"out": out, "manifest": m, "skills": unpacked}


def _code_lines(agent_source, text):
    """Lines of the agent's code that appear in a SKILL.md."""
    code = [ln.strip() for ln in agent_source.splitlines()
            if len(ln.strip()) > 12 and not ln.strip().startswith(("#", '"', "'"))]
    found = [ln for ln in code if ln in text]
    return found + [w for w in ("def ", "class ", "import ") if f"\n{w}" in text or f"    {w}" in text]


def test_every_agent_travels_byte_for_byte_in_a_skinny_skill(workspace, agents_dir):
    m, skills = workspace["manifest"], workspace["skills"]
    assert sorted(a["file"] for a in m["agents"]) == sorted(FOUR + ["circle_agent.py"])
    assert (workspace["out"] / "instructions.md").read_bytes() == (KERNEL / "soul.md").read_bytes()
    run_py = (ORGAN_DIR / "skill_run.py").read_bytes()
    for a in m["agents"]:
        original = (agents_dir / a["file"]).read_bytes()
        shipped = (skills / a["skill"] / "scripts/agent.py").read_bytes()
        assert _sha(shipped) == _sha(original) == a["sha256"]
        assert (skills / a["skill"] / "scripts/run.py").read_bytes() == run_py
        text = (skills / a["skill"] / "SKILL.md").read_text(encoding="utf-8")
        assert text.startswith(f"---\nname: {a['skill']}\n")
        assert _code_lines(original.decode("utf-8"), text) == []
    assert studio_organ.verify_workspace(workspace["out"]) == []
    names = sorted(p.name for p in (workspace["out"] / "workflows").iterdir())
    assert names == ["ContextMemory_read.json", "HackerNews_item.json", "HackerNews_topstories.json",
                     "ManageMemory_read.json", "ManageMemory_save.json"]


def test_negative_controls_for_the_workspace_checks(workspace, tmp_path):
    a = next(x for x in workspace["manifest"]["agents"] if x["skill"] == "hacker-news")
    source = (BUNDLED / a["file"]).read_text(encoding="utf-8")
    doctored = (workspace["skills"] / "hacker-news/SKILL.md").read_text(encoding="utf-8") + \
        "\n    top_ids = _fetch_json(_HN_TOP)\n"
    assert _code_lines(source, doctored) != []

    copy = tmp_path / "ws"
    shutil.copytree(workspace["out"], copy)
    zpath = copy / a["skill_zip"]
    with zipfile.ZipFile(zpath) as z:
        members = {n: z.read(n) for n in z.namelist()}
    members["hacker-news/scripts/agent.py"] += b"\n# edited\n"
    with zipfile.ZipFile(zpath, "w") as z:
        for n, data in members.items():
            z.writestr(n, data)
    m = json.loads((copy / "manifest.json").read_text())
    next(x for x in m["agents"] if x["skill"] == "hacker-news")["skill_zip_sha256"] = _sha(zpath.read_bytes())
    (copy / "manifest.json").write_text(json.dumps(m))
    assert studio_organ.verify_workspace(copy) == [f"{a['skill_zip']}: agent.py is not the original {a['file']}"]
    assert send_to_studio.main([str(copy)]) == 2  # the driver refuses before it prints a step


def test_driver_dry_run_reads_contracts_first_and_stops_before_publish(workspace, capsys):
    assert send_to_studio.main([str(workspace["out"])]) == 0
    out = capsys.readouterr().out
    steps = [ln for ln in out.splitlines() if ln[:1].isdigit()]
    assert out.startswith("Dry run: nothing is sent.")
    assert "copilot mcp add copilot-studio-mcp -- npx -y @microsoft/copilot-studio-mcp@latest" in out
    assert steps[0].startswith("1. discover_resources: action=describe_actions")
    tools = [s.split(": ", 1)[0].split(". ", 1)[1] for s in steps]
    assert tools.index("manage_agents") > max(i for i, t in enumerate(tools) if t == "manage_workflows")
    assert tools[-1] == "stop" and "publish" not in " ".join(steps[:-1]).lower()
    published = [t for t, _ in send_to_studio.steps(workspace["out"], publish=True)]
    assert published[-1] == "manage_agents" and "stop" not in published


# ── run.py runs the original logic with workflow answers ───────────────────

def _kernel_python():
    probe = "import flask, flask_cors, requests, dotenv"
    for py in (sys.executable, os.environ.get("RAPP_KERNEL_PYTHON")):
        if py and subprocess.run([py, "-c", probe], capture_output=True,  # the tests' own sandboxed HOME
                                 env={**os.environ, "PYTHONNOUSERSITE": "1"}).returncode == 0:
            return py
    return None


KPY = _kernel_python()
needs_kernel = pytest.mark.skipif(KPY is None, reason="Brainstem deps (flask, requests) not installed")


def _drive_skill(skill_dir, args, web, table, py=None):
    """Play the Copilot: run run.py, answer each workflow-tool call from fakes, run again."""
    payload, calls = {"args": args, "responses": {}, "storage": {}}, []
    for _ in range(50):
        done = subprocess.run([py or KPY, "scripts/run.py", json.dumps(payload)], cwd=skill_dir,
                              capture_output=True, text=True, timeout=60)
        out = json.loads(done.stdout)
        if out["status"] != "needs":
            for s in out.get("save", []):
                table[s["inputs"]["key"]] = s["inputs"]["document"]
            return out, calls
        for call in out["call"]:
            calls.append(call["tool"])
            if call["into"] == "responses":
                url = call["key"].split(" ", 1)[1]
                payload["responses"][call["key"]] = {"status": 200, "body": json.dumps(web[url])}
            else:
                payload["storage"][call["key"]] = table.get(call["inputs"]["key"])
    raise AssertionError("run.py never finished")


ORIGINAL = r'''
import io, json, sys, urllib.request
sys.path.insert(0, sys.argv[1])
import brainstem
web = json.loads(open(sys.argv[2]).read())
class _R(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False
urllib.request.urlopen = lambda url, timeout=None: _R(json.dumps(web[url]).encode())
agent = brainstem.load_agents()[sys.argv[3]]
print(json.dumps(agent.perform(**json.loads(sys.argv[4]))))
'''


@pytest.fixture(scope="module")
def kernel_copy(tmp_path_factory, workspace):
    if KPY is None:
        pytest.skip("Brainstem deps (flask, requests) not installed")
    home = tmp_path_factory.mktemp("khome")
    src = home / ".brainstem/src/rapp_brainstem"
    shutil.copytree(KERNEL, src, ignore=shutil.ignore_patterns("tests", "__pycache__", ".brainstem_*", ".env"))
    for f in (src / "agents").glob("*_agent.py"):
        if f.name != "basic_agent.py":
            f.unlink()
    for a in workspace["manifest"]["agents"]:  # hot-load the copies that left in the skills, not the originals
        if a["file"] != "basic_agent.py":
            shutil.copy(workspace["skills"] / a["skill"] / "scripts/agent.py", src / "agents" / a["file"])
    env = {k: v for k, v in os.environ.items() if k not in {"GITHUB_TOKEN", "GH_TOKEN", "PORT"}}
    env.update(HOME=str(home), USERPROFILE=str(home))
    (home / "web.json").write_text(json.dumps(RECORDED), encoding="utf-8")
    return {"home": home, "src": src, "env": env}


def _original(kc, agent, args):
    out = subprocess.run([KPY, "-c", ORIGINAL, str(kc["src"]), str(kc["home"] / "web.json"), agent, json.dumps(args)],
                         cwd=kc["src"], env=kc["env"], capture_output=True, text=True, timeout=90)
    assert out.returncode == 0, out.stderr[-800:]
    return json.loads(out.stdout.strip().splitlines()[-1])


@needs_kernel
def test_shipped_agent_files_hot_load_in_the_kernel(kernel_copy):
    probe = "import sys; sys.path.insert(0, sys.argv[1]); import brainstem; print(sorted(brainstem.load_agents()))"
    out = subprocess.run([KPY, "-c", probe, str(kernel_copy["src"])], cwd=kernel_copy["src"],
                         env=kernel_copy["env"], capture_output=True, text=True, timeout=90)
    loaded = eval(out.stdout.strip().splitlines()[-1])
    assert {"Circle", "ContextMemory", "HackerNews", "ManageMemory"} <= set(loaded)
    broken = kernel_copy["src"] / "agents/broken_agent.py"  # negative control: a damaged copy does not load
    broken.write_bytes((BUNDLED / "hacker_news_agent.py").read_bytes().replace(b"class HackerNewsAgent", b"class (", 1)
                       .replace(b'self.name = "HackerNews"', b'self.name = "Broken"'))
    try:
        out = subprocess.run([KPY, "-c", probe, str(kernel_copy["src"])], cwd=kernel_copy["src"],
                             env=kernel_copy["env"], capture_output=True, text=True, timeout=90)
        assert "Broken" not in eval(out.stdout.strip().splitlines()[-1])
    finally:
        broken.unlink()


@needs_kernel
def test_run_py_gives_the_original_answer_byte_for_byte(kernel_copy, workspace):
    expected = _original(kernel_copy, "HackerNews", {"count": 3})
    got, calls = _drive_skill(workspace["skills"] / "hacker-news", {"count": 3}, RECORDED, {})
    assert got["status"] == "done" and got["save"] == []
    assert got["result"].encode("utf-8") == expected.encode("utf-8")
    assert calls == ["HackerNews_topstories"] + ["HackerNews_item"] * 3
    # negative control: one recorded answer changed for the skill only, and the answers differ
    altered = json.loads(json.dumps(RECORDED))
    altered[ITEM.format(9002)]["title"] = "Story 9002 (edited)"
    other, _ = _drive_skill(workspace["skills"] / "hacker-news", {"count": 3}, altered, {})
    assert other["result"] != expected


@needs_kernel
def test_memory_goes_through_dataverse_tools_and_comes_back(kernel_copy, workspace):
    data = kernel_copy["src"] / ".brainstem_data/shared_memories"
    data.mkdir(parents=True, exist_ok=True)
    (data / "memory.json").write_text(MEMORY_DOC, encoding="utf-8")
    expected = _original(kernel_copy, "ContextMemory", {})
    table = {"shared_memories/memory.json": MEMORY_DOC}
    got, calls = _drive_skill(workspace["skills"] / "context-memory", {}, {}, table)
    assert got["result"] == expected and calls == ["ContextMemory_read"]

    fresh = {}
    stored, calls = _drive_skill(workspace["skills"] / "manage-memory",
                                 {"memory_type": "fact", "content": "Likes jazz"}, {}, fresh)
    assert stored["result"] == _original(kernel_copy, "ManageMemory", {"memory_type": "fact", "content": "Likes jazz"})
    assert calls == ["ManageMemory_read"] and [s["tool"] for s in stored["save"]] == ["ManageMemory_save"]
    saved = json.loads(fresh["shared_memories/memory.json"])
    assert [m["message"] for m in saved.values()] == ["Likes jazz"]
    recalled, _ = _drive_skill(workspace["skills"] / "context-memory", {}, {}, fresh)
    assert '"Likes jazz"' in recalled["result"]


# ── registry, kernel, and the switch agent on a running Brainstem ───────────

def _lf_sha(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _pin_mismatches(root):
    pins = dict(reversed(line.split(None, 1)) for line in PINS.read_text(encoding="utf-8").splitlines()
                if line and not line.startswith("#"))
    return [p for p, d in pins.items() if _lf_sha(root / p) != d]


def test_kernel_files_are_unchanged(tmp_path):
    assert _pin_mismatches(REPO_ROOT) == []
    assert not (KERNEL / "organs").exists()
    copy = tmp_path / "root"  # negative control: one changed byte in a copy of brainstem.py is caught
    (copy / "rapp_brainstem").mkdir(parents=True)
    for p in PINS.read_text(encoding="utf-8").splitlines():
        if p and not p.startswith("#"):
            rel = p.split(None, 1)[1]
            (copy / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(REPO_ROOT / rel, copy / rel)
    with open(copy / "rapp_brainstem/brainstem.py", "ab") as f:
        f.write(b"\n")
    assert _pin_mismatches(copy) == ["rapp_brainstem/brainstem.py"]


def test_registry_lists_the_organ_and_switch_with_current_hashes():
    registry = json.loads((REPO_ROOT / "registry.json").read_text(encoding="utf-8"))
    errors = []
    built = build_registry.load_organs(errors, root=REPO_ROOT)
    assert not errors
    organ = next(o for o in registry["organs"] if o["name"] == ORGAN_NAME)
    assert organ["_files"] == next(o for o in built if o["name"] == ORGAN_NAME)["_files"]
    assert registry["stats"]["total_organs"] == len(registry["organs"])
    switch = next(a for a in registry["agents"] if a["name"] == "@aibast-agents-library/send-to-studio")
    assert switch["_sha256"] == _sha(SWITCH_AGENT.read_text(encoding="utf-8").encode("utf-8"))
    assert switch["organ"] == ORGAN_NAME


DRIVE = ("import sys, json; sys.path.insert(0, sys.argv[1]); import brainstem; "
         "print(json.dumps(brainstem.load_agents()['SendToStudio'].perform(**json.loads(sys.argv[2]))))")


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def rig(tmp_path_factory):
    if KPY is None:
        pytest.skip("Brainstem deps (flask, requests) not installed")
    home = tmp_path_factory.mktemp("home")
    src = home / ".brainstem/src/rapp_brainstem"
    shutil.copytree(KERNEL, src, ignore=shutil.ignore_patterns("tests", "__pycache__", ".brainstem_*", ".env"))
    shutil.copy(SWITCH_AGENT, src / "agents" / "studio_organ_agent.py")
    site = home / "site"
    shutil.copytree(ORGAN_DIR, site / "organs/studio", ignore=shutil.ignore_patterns("__pycache__"))
    errors = []
    organs = [o for o in build_registry.load_organs(errors, root=REPO_ROOT) if o["name"] == ORGAN_NAME]
    (site / "registry.json").write_text(json.dumps({"organs": organs}), encoding="utf-8")
    bad = json.loads(json.dumps(organs))
    bad[0]["_files"][-1]["sha256"] = "0" * 64
    (site / "tampered.json").write_text(json.dumps({"organs": bad}), encoding="utf-8")
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(site)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    env = {k: v for k, v in os.environ.items() if k not in {"GITHUB_TOKEN", "GH_TOKEN", "PORT"}}
    env.update(HOME=str(home), USERPROFILE=str(home),
               STUDIO_REGISTRY_URL=f"http://127.0.0.1:{server.server_address[1]}/registry.json")
    port = _free_port()
    kernel = subprocess.Popen([KPY, "brainstem.py"], cwd=src, env=dict(env, PORT=str(port)),
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:
            urlopen(f"http://127.0.0.1:{port}/health", timeout=2)
            break
        except Exception:
            time.sleep(0.2)
    yield {"home": home, "src": src, "env": env, "kernel": kernel, "port": port,
           "organ": home / ".brainstem/organs/studio"}
    kernel.terminate()
    kernel.wait(10)
    server.shutdown()


def _switch(rig, **kw):
    env = dict(rig["env"], **kw.pop("env", {}))
    out = subprocess.run([KPY, "-c", DRIVE, str(rig["src"]), json.dumps(kw)], env=env, cwd=rig["src"],
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-800:]
    return json.loads(out.stdout.strip().splitlines()[-1])


def _kernel_ok(rig):
    assert rig["kernel"].poll() is None, "kernel process stopped"
    with urlopen(f"http://127.0.0.1:{rig['port']}/health", timeout=3) as r:
        assert r.status == 200


@needs_kernel
def test_switch_on_plan_build_send_off_leaves_the_kernel_running(rig):
    assert _switch(rig, action="status") == "Send to Copilot Studio is off."
    assert _switch(rig, action="send") == "Send to Copilot Studio is off. Ask to turn it on first."

    tampered = rig["env"]["STUDIO_REGISTRY_URL"].replace("registry.json", "tampered.json")
    reply = _switch(rig, action="plan", env={"STUDIO_REGISTRY_URL": tampered})  # plan turns it on: same checks
    assert reply.startswith("Refused:") and "Nothing was installed" in reply
    assert not rig["organ"].exists()
    reply = _switch(rig, action="on", env={"STUDIO_REGISTRY_URL": tampered})
    assert reply.startswith("Refused:") and "Nothing was installed" in reply
    assert not rig["organ"].exists() and not rig["organ"].with_name("studio.staging").exists()

    assert _switch(rig, action="on").startswith("Send to Copilot Studio is on.")
    for f in json.loads((rig["src"].parent.parent / "organs/studio/organ.json").read_text())["files"]:
        assert (rig["organ"] / f).read_bytes() == (ORGAN_DIR / f).read_bytes()

    plan = _switch(rig, action="plan")
    assert "HackerNews (hacker_news_agent.py): skill hacker-news + workflow tools HackerNews_topstories, " \
           "HackerNews_item." in plan
    assert "SendToStudio" not in plan

    built = _switch(rig, action="build")
    assert built.startswith(f"The Copilot Studio workspace is ready at {rig['organ'] / 'workspace'}")
    assert studio_organ.verify_workspace(rig["organ"] / "workspace") == []
    # 10/20 gate: on "send it" the model set confirm itself. The chat now only opens a page the person presses.
    reply = _switch(rig, action="send", confirm=True, env={"PATH": "/usr/bin:/bin"})
    assert reply.startswith("Nothing was sent. Open http://127.0.0.1:"), reply
    url = re.search(r"http://127\.0\.0\.1:\d+/", reply).group(0)
    here = url[len("http://"):-1]
    page = urlopen(url, timeout=5).read().decode("utf-8")
    assert "Send as a draft" in page and "Nothing is published" in page
    token = re.search(r"name=t value=([\w-]+)", page).group(1)

    def post(headers, t=token):
        req = Request(url + "send", data=f"t={t}".encode(), headers=headers, method="POST")
        try:
            with urlopen(req, timeout=60) as r:
                return r.status, r.read().decode("utf-8")
        except HTTPError as e:
            return e.code, e.read().decode("utf-8")

    origin = {"Origin": f"http://{here}", "Content-Type": "application/x-www-form-urlencoded"}
    assert post({})[0] == 403                                    # a script with no Origin
    assert post(origin, t="guess")[0] == 403                     # the right origin, a guessed token
    assert post({**origin, "Origin": "http://evil.example"})[0] == 403
    assert _switch(rig, action="send").endswith("(it closes on its own in 15 minutes).")  # same page, not a second
    status, body = post(origin)                                  # the person's own press goes through
    assert status == 200 and "Send stopped" in body and "nothing was sent" in body  # no copilot on this PATH
    for _ in range(300):  # one press only: the page closes itself after it
        with socket.socket() as so:
            if so.connect_ex(("127.0.0.1", int(here.split(":")[1]))) != 0:
                break
        time.sleep(0.1)
    else:
        raise AssertionError("send page still open after the press")
    page_pid = None
    for _ in range(300):  # and its process ends too (10/20: a non-daemon timer kept it alive 15 minutes)
        out = subprocess.run(["pgrep", "-f", str(rig["organ"] / "send_to_studio.py")], capture_output=True, text=True)
        page_pid = out.stdout.split()
        if not page_pid:
            break
        time.sleep(0.1)
    assert not page_pid, f"send page process still running: {page_pid}"
    _kernel_ok(rig)

    (rig["organ"] / "studio_organ.py").write_text("# edited\n", encoding="utf-8")
    assert _switch(rig, action="plan").startswith("Refused: studio_organ.py changed since it was installed.")

    assert _switch(rig, action="off").startswith("Send to Copilot Studio is off.")
    assert not rig["organ"].exists()
    assert _switch(rig, action="status") == "Send to Copilot Studio is off."
    _kernel_ok(rig)

    # 10/20 browser pass: asking for the plan is the yes; it must not bounce the user to "turn it on"
    one_setting = {"STUDIO_REGISTRY_URL": "", "AIBAST_REGISTRY_URL": rig["env"]["STUDIO_REGISTRY_URL"]}
    plan = _switch(rig, action="plan", env=one_setting)  # the one AIBAST setting points every organ
    assert "HackerNews (hacker_news_agent.py): skill hacker-news" in plan and rig["organ"].exists()
    assert _switch(rig, action="off").startswith("Send to Copilot Studio is off.")
    _kernel_ok(rig)
