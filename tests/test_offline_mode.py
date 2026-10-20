"""Offline mode: an organ installed live on a running Brainstem, then removed.

No network and no Ollama: a fake registry and a fake OpenAI-compatible model
server run on 127.0.0.1 threads. A real kernel (a copy of rapp_brainstem/) runs
in its own process the whole time; the OfflineMode agent is driven the way the
kernel calls it (load_agents() -> perform).

The process tests need the Brainstem's dependencies (flask, requests). They use
this Python when it has them, else RAPP_KERNEL_PYTHON, else they skip.
"""

import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
from pathlib import Path
from urllib.request import Request, urlopen

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
KERNEL = REPO_ROOT / "rapp_brainstem"
SWITCH_AGENT = REPO_ROOT / "agents/@aibast-agents-library/templates/offline_mode_agent.py"
ORGAN = REPO_ROOT / "organs/offline/offline_brainstem.py"
PINS = Path(__file__).with_name("offline_kernel.sha256")
ORGAN_NAME = "@aibast-agents-library/offline-runner"

sys.path.insert(0, str(REPO_ROOT))
import build_registry  # noqa: E402


def _lf_sha(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _pinned_paths():
    inventory = json.loads((REPO_ROOT / "rapp/GRAIL-SPECIES.json").read_text(encoding="utf-8"))["inventory"]
    return [f"rapp_brainstem/{p}" for p in inventory] + ["install.sh", "install.ps1"]


# ── static checks (always run) ───────────────────────────────────────────────

def test_pinned_kernel_files_are_unchanged():
    pins = {}
    for line in PINS.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            digest, path = line.split(None, 1)
            pins[path] = digest
    assert sorted(pins) == sorted(_pinned_paths())
    changed = [p for p, d in pins.items() if _lf_sha(REPO_ROOT / p) != d]
    assert not changed, f"offline mode must not change kernel files: {changed}"


def test_organ_lives_outside_the_kernel():
    assert not (KERNEL / "offline").exists()
    assert not (KERNEL / "organs").exists()


def test_registry_lists_the_organ_and_switch_with_current_hashes():
    registry = json.loads((REPO_ROOT / "registry.json").read_text(encoding="utf-8"))
    errors = []
    built = build_registry.load_organs(errors, root=REPO_ROOT)
    assert not errors
    organ = next(o for o in registry["organs"] if o["name"] == ORGAN_NAME)
    assert organ["_files"] == next(o for o in built if o["name"] == ORGAN_NAME)["_files"]
    assert organ["_files"][0]["sha256"] == hashlib.sha256(ORGAN.read_bytes()).hexdigest()
    assert registry["stats"]["total_organs"] == len(registry["organs"])
    switch = next(a for a in registry["agents"] if a["name"] == "@aibast-agents-library/offline-mode")
    assert switch["_sha256"] == hashlib.sha256(
        SWITCH_AGENT.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    assert switch["organ"] == ORGAN_NAME


# ── live organ on a running kernel ───────────────────────────────────────────

def _kernel_python():
    probe = "import flask, flask_cors, requests, dotenv"
    for py in (sys.executable, os.environ.get("RAPP_KERNEL_PYTHON")):
        if py and subprocess.run([py, "-c", probe], capture_output=True,  # the tests' own sandboxed HOME
                                 env={**os.environ, "PYTHONNOUSERSITE": "1"}).returncode == 0:
            return py
    return None


KPY = _kernel_python()
needs_kernel = pytest.mark.skipif(KPY is None, reason="Brainstem deps (flask, requests) not installed")


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _get(url, timeout=3):
    with urlopen(Request(url), timeout=timeout) as r:
        return r.status, json.loads(r.read())


def _post(url, body, timeout=30):
    req = Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read())


def _alive(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    out = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True).stdout
    return bool(out.strip()) and not out.strip().startswith("Z")


class _FakeModel(BaseHTTPRequestHandler):
    """OpenAI-compatible: first turn asks for ProbeAgent, the next answers in prose."""
    calls = []

    def log_message(self, *a):
        pass

    def _send(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send({"object": "list", "data": [{"id": "fake-local", "object": "model"}]})

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).calls.append(req)
        tool_msgs = [m for m in req["messages"] if m.get("role") == "tool"]
        if tool_msgs:
            msg = {"role": "assistant", "content": "Offline answer: " + tool_msgs[-1]["content"]}
        else:
            msg = {"role": "assistant", "content": "", "tool_calls": [{
                "id": "call_1", "type": "function",
                "function": {"name": "ProbeAgent", "arguments": json.dumps({"note": "hello"})}}]}
        self._send({"choices": [{"index": 0, "message": msg, "finish_reason": "stop"}]})


PROBE_AGENT = '''
import os
from agents.basic_agent import BasicAgent

class ProbeAgent(BasicAgent):
    def __init__(self):
        self.name = "ProbeAgent"
        self.metadata = {"name": self.name, "description": "Test probe.",
                         "parameters": {"type": "object", "properties": {"note": {"type": "string"}}}}
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, note="", **kwargs):
        with open(os.path.join(os.path.expanduser("~"), "probe-ran.txt"), "w") as f:
            f.write(note)
        return "probe saw " + note
'''

DRIVE = (
    "import sys; sys.path.insert(0, sys.argv[1]); import brainstem; "
    "print(brainstem.load_agents()['OfflineMode'].perform(action=sys.argv[2]))"
)


def _serve(handler, directory=None):
    h = partial(handler, directory=directory) if directory else handler
    server = (ThreadingHTTPServer if directory else HTTPServer)(("127.0.0.1", 0), h)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.fixture(scope="module")
def rig(tmp_path_factory):
    if KPY is None:
        pytest.skip("Brainstem deps (flask, requests) not installed")
    home = tmp_path_factory.mktemp("home")
    src = home / ".brainstem/src/rapp_brainstem"
    shutil.copytree(KERNEL, src, ignore=shutil.ignore_patterns("tests", "__pycache__", ".brainstem_*", ".env"))
    shutil.copy(SWITCH_AGENT, src / "agents" / "offline_mode_agent.py")
    (src / "agents" / "probe_agent.py").write_text(PROBE_AGENT, encoding="utf-8")

    site = home / "site"
    (site / "organs/offline").mkdir(parents=True)
    shutil.copy(ORGAN, site / "organs/offline/offline_brainstem.py")
    errors = []
    organs = build_registry.load_organs(errors, root=REPO_ROOT)
    assert not errors
    (site / "registry.json").write_text(json.dumps({"organs": organs}), encoding="utf-8")
    bad = json.loads(json.dumps(organs))
    bad[0]["_files"][0]["sha256"] = "0" * 64
    (site / "tampered.json").write_text(json.dumps({"organs": bad}), encoding="utf-8")

    registry = _serve(SimpleHTTPRequestHandler, directory=str(site))
    model = _serve(_FakeModel)
    env = {k: v for k, v in os.environ.items() if k not in {"GITHUB_TOKEN", "GH_TOKEN", "PORT"}}
    env.update(HOME=str(home), USERPROFILE=str(home), BRAINSTEM_LAN_MODE="true")
    kernel_port = _free_port()
    kernel = subprocess.Popen([KPY, "brainstem.py"], cwd=src, env=dict(env, PORT=str(kernel_port)),
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:
            _get(f"http://127.0.0.1:{kernel_port}/health")
            break
        except Exception:
            time.sleep(0.2)
    reg_url = f"http://127.0.0.1:{registry.server_address[1]}/registry.json"
    rig = {
        "home": home, "src": src, "env": env, "kernel": kernel, "kernel_port": kernel_port,
        "organ_dir": home / ".brainstem/organs/offline", "reg_url": reg_url,
        "model_url": f"http://127.0.0.1:{model.server_address[1]}/v1", "offline_port": _free_port(),
    }
    yield rig
    state = rig["organ_dir"] / "runner.json"
    if state.exists():
        try:
            os.kill(json.loads(state.read_text())["pid"], 15)
        except OSError:
            pass
    kernel.terminate()
    kernel.wait(10)
    registry.shutdown()
    model.shutdown()


def _drive(rig, action, **extra):
    env = dict(rig["env"], OFFLINE_REGISTRY_URL=rig["reg_url"], OFFLINE_BASE_URL=rig["model_url"],
               OFFLINE_PORT=str(rig["offline_port"]))
    env.update(extra)
    out = subprocess.run([KPY, "-c", DRIVE, str(rig["src"]), action], env=env, cwd=rig["src"],
                         capture_output=True, text=True, timeout=90)
    return out.stdout.strip().splitlines()[-1]


def _kernel_ok(rig):
    assert rig["kernel"].poll() is None, "kernel process stopped"
    status, body = _get(f"http://127.0.0.1:{rig['kernel_port']}/health")
    assert status == 200 and body["status"] in {"ok", "unauthenticated"}


@needs_kernel
def test_tampered_hash_is_refused_and_nothing_is_written(rig):
    reply = _drive(rig, "on", OFFLINE_REGISTRY_URL=rig["reg_url"].replace("registry.json", "tampered.json"))
    assert reply.startswith("Refused:") and "Nothing was installed" in reply
    assert not rig["organ_dir"].exists()
    assert not rig["organ_dir"].with_name("offline.staging").exists()
    _kernel_ok(rig)


@needs_kernel
def test_no_local_model_server_fails_in_plain_words(rig):
    reply = _drive(rig, "on", OFFLINE_BASE_URL=f"http://127.0.0.1:{_free_port()}/v1")
    assert "did not start" in reply and "No local model server" in reply and "never falls back" in reply
    assert not rig["organ_dir"].exists()
    _kernel_ok(rig)


@needs_kernel
def test_on_chat_off_leaves_the_kernel_running(rig):
    port = rig["offline_port"]
    assert _drive(rig, "status") == "Offline mode is off."

    reply = _drive(rig, "on")
    assert reply.startswith(f"Offline mode is on. Chat at http://127.0.0.1:{port}"), reply
    registry = json.loads(urlopen(rig["reg_url"]).read())
    for f in registry["organs"][0]["_files"]:
        written = rig["organ_dir"] / Path(f["path"]).name
        assert hashlib.sha256(written.read_bytes()).hexdigest() == f["sha256"]
    pid = json.loads((rig["organ_dir"] / "runner.json").read_text())["pid"]
    assert _alive(pid)
    # Bound to loopback only, even with BRAINSTEM_LAN_MODE=true in its environment.
    log = (rig["organ_dir"] / "runner.log").read_text()
    assert f"listening on 127.0.0.1:{port}" in log

    _, health = _get(f"http://127.0.0.1:{port}/health")
    assert health["mode"] == "offline" and health["model"] == "fake-local"
    assert "OfflineMode" not in health["agents"] and "ProbeAgent" in health["agents"]

    status, body = _post(f"http://127.0.0.1:{port}/chat", {"user_input": "probe please"})
    assert status == 200
    assert body["response"] == "Offline answer: probe saw hello"
    assert "[ProbeAgent]" in body["agent_logs"] and body["mode"] == "offline"
    assert (rig["home"] / "probe-ran.txt").read_text() == "hello"
    assert "is on at" in _drive(rig, "status")
    _kernel_ok(rig)

    reply = _drive(rig, "off")
    assert reply.startswith("Offline mode is off.") and f"process {pid}" in reply
    for _ in range(50):
        if not _alive(pid):
            break
        time.sleep(0.1)
    assert not _alive(pid)
    assert not rig["organ_dir"].exists()
    _kernel_ok(rig)
    assert _drive(rig, "status") == "Offline mode is off."


if __name__ == "__main__" and sys.argv[1:] == ["--pin"]:
    header = [line for line in PINS.read_text(encoding="utf-8").splitlines() if line.startswith("#")]
    PINS.write_text("\n".join(header + [f"{_lf_sha(REPO_ROOT / p)}  {p}" for p in _pinned_paths()]) + "\n",
                    encoding="utf-8")
