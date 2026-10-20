"""AIBAST Registry: search and install AIBAST agents by chat, never touching the kernel.

Offline: a fake registry on a 127.0.0.1 thread serves registry.json and the agent
files beside it (any registry address that is not production or staging serves its
files beside itself). The logic tests load the agent in this process from a copy in a
temporary agents/ folder; the kernel tests run a copy of rapp_brainstem/ with the
kernel's own Python (this one when it has flask and requests, else RAPP_KERNEL_PYTHON,
else they skip). Each safety check has a negative control: the same test against a
copy of the agent with that one check taken out goes red.
"""

import hashlib
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import types
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
KERNEL = REPO_ROOT / "rapp_brainstem"
AGENT = REPO_ROOT / "agents/@aibast-agents-library/templates/aibast_registry_agent.py"
PINS = Path(__file__).with_name("offline_kernel.sha256")
NAME = "@aibast-agents-library/aibast-registry"
# The bundled Learn New agent points at a personal registry; it is a kernel file and stays byte for byte.
LEARN_NEW = ("rapp_brainstem/agents/rar_rapp_learn_new_agent.py",
             "bd956087974334b7992e633d5a049fd441770b549e1e9781e229899e71572ea6")
REAL = "@aibast-agents-library/grid-outage-response"

PROBE = '''
from agents.basic_agent import BasicAgent


class RegistryProbeAgent(BasicAgent):
    def __init__(self):
        self.name = "RegistryProbe"
        self.metadata = {"name": self.name, "description": "Says it was installed from the registry.",
                         "parameters": {"type": "object", "properties": {}, "required": []}}
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        return "installed from the AIBAST registry"
'''


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _lf_sha(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _pin_mismatches(root):
    pins = dict(reversed(line.split(None, 1)) for line in PINS.read_text(encoding="utf-8").splitlines()
                if line and not line.startswith("#"))
    pins[LEARN_NEW[0]] = LEARN_NEW[1]
    return sorted(p for p, d in pins.items() if _lf_sha(root / p) != d)


def _entry(name, file, body, **extra):
    stem = name.split("/")[-1].replace("-", "_")
    e = {"name": name, "display_name": name.split("/")[-1].replace("-", " ").title(),
         "description": f"{name} for tests.", "tags": [], "requires_env": [], "_file": file,
         "_sha256": _sha(body), "_install_filename": f"{stem}__{_sha(body)[:12]}_agent.py"}
    e.update(extra)
    return e


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    """A fake registry: the real entry for one library agent plus test entries, files beside it."""
    top = tmp_path_factory.mktemp("site")
    root = top / "ring"  # the registry and its files; one level down so '..' has somewhere to go
    registry = json.loads((REPO_ROOT / "registry.json").read_text(encoding="utf-8"))
    real = next(a for a in registry["agents"] if a["name"] == REAL)
    (root / real["_file"]).parent.mkdir(parents=True)
    shutil.copy(REPO_ROOT / real["_file"], root / real["_file"])
    probe = PROBE.encode()
    (root / "agents/@test").mkdir(parents=True)
    (root / "agents/@test/registry_probe_agent.py").write_bytes(probe)
    (root / "agents/@test/notes.txt").write_bytes(probe)
    agents = [
        real,
        _entry("@test/registry-probe", "agents/@test/registry_probe_agent.py", probe,
               tags=["probe"], _solution={"search_terms": ["lighthouse"]}),
        _entry("@test/tampered", "agents/@test/registry_probe_agent.py", probe, _sha256="0" * 64),
        _entry("@test/escape-target", "agents/@test/registry_probe_agent.py", probe,
               _install_filename="../escaped_agent.py"),
        _entry("@test/escape-source", "../outside_agent.py", probe),
        _entry("@test/not-python", "agents/@test/notes.txt", probe, _install_filename="notes_agent.txt"),
        _entry("@test/takes-basic", "agents/@test/registry_probe_agent.py", probe,
               _install_filename="basic_agent.py"),
        _entry("@test/clobber", "agents/@test/registry_probe_agent.py", probe,
               _install_filename="hacker_news_agent.py"),
    ]
    (root / "registry.json").write_text(json.dumps({"agents": agents}), encoding="utf-8")
    (top / "outside_agent.py").write_bytes(probe)  # what the escaping source would reach
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(top)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield {"root": root, "url": f"http://127.0.0.1:{server.server_address[1]}/ring/registry.json",
           "real": real, "probe": probe}
    server.shutdown()


def _load(folder, source):
    """Load an agent source from <folder>/aibast_registry_agent.py the way the kernel does."""
    path = folder / "aibast_registry_agent.py"
    path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(f"aibast_registry_{id(path)}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.AIBASTRegistryAgent()


def _without(*swaps):
    """The agent's source with one check taken out; each swap must apply exactly once."""
    src = AGENT.read_text(encoding="utf-8")
    for old, new in swaps:
        assert src.count(old) == 1, old
        src = src.replace(old, new)
    return src


@pytest.fixture
def folder(tmp_path, site, monkeypatch):
    """A Brainstem-like agents/ folder with the kernel's bundled agents; agents.basic_agent importable."""
    agents = tmp_path / "brainstem/agents"
    agents.mkdir(parents=True)
    for f in ("basic_agent.py", "hacker_news_agent.py"):
        shutil.copy(KERNEL / "agents" / f, agents / f)
    pkg = types.ModuleType("agents")
    pkg.__path__ = [str(agents)]
    spec = importlib.util.spec_from_file_location("agents.basic_agent", agents / "basic_agent.py")
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    monkeypatch.setitem(sys.modules, "agents", pkg)
    monkeypatch.setitem(sys.modules, "agents.basic_agent", base)
    monkeypatch.setenv("AIBAST_REGISTRY_URL", site["url"])
    monkeypatch.delenv("AIBAST_RAW_BASE", raising=False)
    return agents


def _snapshot(folder):
    return {p.relative_to(folder.parent.parent).as_posix(): p.read_bytes()
            for p in folder.parent.parent.rglob("*") if p.is_file() and "__pycache__" not in p.parts}


# ── static checks ────────────────────────────────────────────────────────────

def test_kernel_files_are_unchanged(tmp_path):
    assert _pin_mismatches(REPO_ROOT) == []
    copy = tmp_path / "root"  # negative control: one changed byte in a copy of index.html is caught
    pins = [line.split(None, 1)[1] for line in PINS.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")] + [LEARN_NEW[0]]
    for rel in pins:
        (copy / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO_ROOT / rel, copy / rel)
    with open(copy / "rapp_brainstem/index.html", "ab") as f:
        f.write(b"\n")
    assert _pin_mismatches(copy) == ["rapp_brainstem/index.html"]


def test_registry_lists_the_agent_with_its_current_hash():
    registry = json.loads((REPO_ROOT / "registry.json").read_text(encoding="utf-8"))
    entry = next(a for a in registry["agents"] if a["name"] == NAME)
    body = AGENT.read_text(encoding="utf-8").encode("utf-8")
    assert entry["_sha256"] == _sha(body)
    assert entry["_install_filename"] == f"aibast_registry__{_sha(body)[:12]}_agent.py"
    assert entry["_file"] == AGENT.relative_to(REPO_ROOT).as_posix()
    assert registry["stats"]["total_agents"] == len(registry["agents"])


def test_points_at_the_aibast_registry_never_a_personal_one():
    src = AGENT.read_text(encoding="utf-8")
    assert "https://microsoft.github.io/aibast-agents-library/registry.json" in src
    assert "kody-w/RAR" not in src and "github.com/kody-w" not in src
    for word in ("subprocess", "exec(", " eval(", "importlib", "requests.post", "analytics"):
        assert word not in src, word  # nothing downloaded is run, nothing is reported anywhere


# ── search ───────────────────────────────────────────────────────────────────

def test_search_finds_by_name_tags_and_solution_terms(folder, site):
    agent = _load(folder, AGENT.read_text(encoding="utf-8"))
    out = agent.perform(action="search", query="outage")
    assert REAL in out and site["real"]["display_name"] in out and "[installed]" not in out
    assert "@test/registry-probe" in agent.perform(action="search", query="lighthouse")  # solution term
    assert "@test/registry-probe" in agent.perform(action="search", query="probe")       # tag
    assert agent.perform(action="search", query="zzzz-nothing").startswith("No AIBAST agents match")
    agent.perform(action="install", name="@test/registry-probe")
    assert "[installed]" in agent.perform(action="search", query="lighthouse")


# ── install / list / remove ──────────────────────────────────────────────────

def test_install_writes_the_file_with_the_registry_hash_and_ledger(folder, site):
    agent = _load(folder, AGENT.read_text(encoding="utf-8"))
    real = site["real"]
    out = agent.perform(action="install", name=real["display_name"])
    assert out.startswith("Installed") and "no restart" in out, out
    written = folder / real["_install_filename"]
    assert _sha(written.read_bytes()) == real["_sha256"]
    assert written.read_bytes() == (REPO_ROOT / real["_file"]).read_bytes()
    ledger = json.loads((folder / "aibast_registry_installed.json").read_text())
    assert [(r["name"], r["file"], r["sha256"]) for r in ledger] == [(REAL, written.name, real["_sha256"])]
    assert ledger[0]["installed_at"]
    assert REAL in agent.perform(action="list")
    assert "already installed" in agent.perform(action="install", name=REAL)
    assert not list(folder.glob(".*.part"))


def test_tampered_hash_is_refused_and_nothing_is_written(folder):
    agent = _load(folder, AGENT.read_text(encoding="utf-8"))
    before = _snapshot(folder)
    out = agent.perform(action="install", name="@test/tampered")
    assert out.startswith("Refused:") and "Nothing was installed" in out
    assert _snapshot(folder) == before


def test_negative_control_tamper_check_removed_writes_the_file(folder):
    agent = _load(folder, _without(("        if digest != expected:\n", "        if False:\n")))
    before = _snapshot(folder)
    agent.perform(action="install", name="@test/tampered")
    assert _snapshot(folder) != before


@pytest.mark.parametrize("ref", ["@test/escape-target", "@test/escape-source", "@test/not-python",
                                 "@test/takes-basic", "@test/clobber"])
def test_unsafe_entries_are_refused_and_nothing_is_written(folder, ref):
    agent = _load(folder, AGENT.read_text(encoding="utf-8"))
    before = _snapshot(folder)
    out = agent.perform(action="install", name=ref)
    assert out.startswith("Refused:"), out
    assert _snapshot(folder) == before
    assert not (folder.parent / "escaped_agent.py").exists()


def test_negative_control_target_check_removed_escapes_the_folder(folder):
    agent = _load(folder, _without(('if (not name or "/" in name or ', 'if (not name or '),
                                   (' or name.startswith(".")', ''),
                                   ("        return target if target.parent == folder else None\n",
                                    "        return folder / name\n")))
    agent.perform(action="install", name="@test/escape-target")
    assert (folder.parent / "escaped_agent.py").exists()


def test_negative_control_source_check_removed_reaches_outside_the_library(folder):
    agent = _load(folder, _without(('                or urlparse(str(path)).scheme or p.suffix != ".py"):\n'
                                    '            return None\n',
                                    '                or urlparse(str(path)).scheme or p.suffix != ".py"):\n'
                                    '            return str(path)\n'),
                                   ('or ".." in p.parts ', '')))
    agent.perform(action="install", name="@test/escape-source")
    assert list(folder.glob("escape_source__*_agent.py"))  # fetched from outside the registry's files


def test_negative_control_overwrite_check_removed_clobbers_a_bundled_agent(folder):
    agent = _load(folder, _without(("            if not mine:\n", "            if False:\n")))
    original = (folder / "hacker_news_agent.py").read_bytes()
    agent.perform(action="install", name="@test/clobber")
    assert (folder / "hacker_news_agent.py").read_bytes() != original


def test_remove_deletes_only_what_it_installed(folder):
    agent = _load(folder, AGENT.read_text(encoding="utf-8"))
    agent.perform(action="install", name="@test/registry-probe")
    installed = json.loads((folder / "aibast_registry_installed.json").read_text())[0]["file"]
    for ref in ("hacker_news_agent.py", "HackerNews", "basic_agent.py", "aibast_registry_agent.py"):
        assert agent.perform(action="remove", name=ref).startswith("I did not install")
    assert (folder / "hacker_news_agent.py").exists() and (folder / "basic_agent.py").exists()
    out = agent.perform(action="remove", name="@test/registry-probe")
    assert out.startswith("Removed") and not (folder / installed).exists()
    assert agent.perform(action="list").startswith("I have not installed")


def test_remove_answers_every_spelling_and_a_repeat_says_already_removed(folder):
    # 10/20 browser pass: the model removed by class name ("RegistryProbeAgent"), was refused, retried,
    # then a repeat ("Registry Probe") said "I did not install" and the model told the user the
    # removal had been false. Every spelling must hit, and a repeat must say "already removed".
    agent = _load(folder, AGENT.read_text(encoding="utf-8"))
    for ref in ("RegistryProbeAgent", "Registry Probe", "registry-probe", "RegistryProbe"):
        agent.perform(action="install", name="@test/registry-probe")
        file = json.loads((folder / "aibast_registry_installed.json").read_text())[-1]["file"]
        out = agent.perform(action="remove", name=ref)
        assert out.startswith("Removed Registry Probe"), (ref, out)
        assert not (folder / file).exists()
        again = agent.perform(action="remove", name=ref)
        assert again.startswith("Registry Probe is already removed"), (ref, again)
    assert agent.perform(action="list").startswith("I have not installed")
    assert agent.perform(action="remove", name="HackerNews").startswith("I did not install")


def test_negative_control_ledger_check_removed_deletes_a_bundled_agent(folder):
    agent = _load(folder, _without(("        row = next((r for r in hits if not r.get(\"removed_at\")), None)\n",
                                    "        row = next((r for r in hits if not r.get(\"removed_at\")), None)"
                                    " or {\"name\": ref, \"file\": ref}\n")))
    agent.perform(action="remove", name="hacker_news_agent.py")
    assert not (folder / "hacker_news_agent.py").exists()


def test_submit_prepares_the_library_path_and_sends_nothing(folder):
    agent = _load(folder, AGENT.read_text(encoding="utf-8"))
    out = agent.perform(action="submit", name="hacker_news_agent.py")
    assert "https://github.com/microsoft/aibast-agents-library/blob/main/CONTRIBUTING.md" in out
    assert "kody-w" not in out and "nothing is sent" in out
    assert "Check of hacker_news_agent.py" in out and "__manifest__ is missing" in out


# ── on a running kernel ──────────────────────────────────────────────────────

def _kernel_python():
    probe = "import flask, flask_cors, requests, dotenv"
    for py in (sys.executable, os.environ.get("RAPP_KERNEL_PYTHON")):
        if py and subprocess.run([py, "-c", probe], capture_output=True,  # the tests' own sandboxed HOME
                                 env={**os.environ, "PYTHONNOUSERSITE": "1"}).returncode == 0:
            return py
    return None


KPY = _kernel_python()
needs_kernel = pytest.mark.skipif(KPY is None, reason="Brainstem deps (flask, requests) not installed")

DRIVE = ("import sys, json; sys.path.insert(0, sys.argv[1]); import brainstem; "
         "a = brainstem.load_agents(); print(json.dumps(a[sys.argv[2]].perform(**json.loads(sys.argv[3]))))")


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def kernel(tmp_path_factory, site):
    if KPY is None:
        pytest.skip("Brainstem deps (flask, requests) not installed")
    home = tmp_path_factory.mktemp("home")
    src = home / ".brainstem/src/rapp_brainstem"
    shutil.copytree(KERNEL, src, ignore=shutil.ignore_patterns("tests", "__pycache__", ".brainstem_*", ".env"))
    shutil.copy(AGENT, src / "agents" / "aibast_registry_agent.py")
    env = {k: v for k, v in os.environ.items() if k not in {"GITHUB_TOKEN", "GH_TOKEN", "PORT"}}
    env.update(HOME=str(home), USERPROFILE=str(home), AIBAST_REGISTRY_URL=site["url"])
    port = _free_port()
    proc = subprocess.Popen([KPY, "brainstem.py"], cwd=src, env=dict(env, PORT=str(port)),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(150):
        try:
            urlopen(f"http://127.0.0.1:{port}/health", timeout=2)
            break
        except Exception:
            time.sleep(0.2)
    yield {"src": src, "env": env, "proc": proc, "port": port, "home": home}
    proc.terminate()
    proc.wait(10)


def _drive(k, agent, **kw):
    out = subprocess.run([KPY, "-c", DRIVE, str(k["src"]), agent, json.dumps(kw)], env=k["env"], cwd=k["src"],
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-800:]
    return json.loads(out.stdout.strip().splitlines()[-1])


def _health_agents(k):
    assert k["proc"].poll() is None, "kernel process stopped"
    with urlopen(f"http://127.0.0.1:{k['port']}/health", timeout=10) as r:
        assert r.status == 200
        return json.loads(r.read())["agents"]


@needs_kernel
def test_kernel_picks_up_an_install_and_a_removal_without_a_restart(kernel, site):
    pid = kernel["proc"].pid
    assert "AIBASTRegistry" in _health_agents(kernel) and "RegistryProbe" not in _health_agents(kernel)
    out = _drive(kernel, "AIBASTRegistry", action="install", name="@test/registry-probe")
    assert out.startswith("Installed"), out
    assert "RegistryProbe" in _health_agents(kernel)                      # the running kernel lists it
    assert _drive(kernel, "RegistryProbe") == "installed from the AIBAST registry"  # and answers with it
    assert "@test/registry-probe" in _drive(kernel, "AIBASTRegistry", action="list")
    assert _drive(kernel, "AIBASTRegistry", action="remove", name="@test/registry-probe").startswith("Removed")
    assert "RegistryProbe" not in _health_agents(kernel)
    assert kernel["proc"].pid == pid and kernel["proc"].poll() is None
    for rel in [line.split(None, 1)[1] for line in PINS.read_text(encoding="utf-8").splitlines()
                if line and not line.startswith("#") and line.split(None, 1)[1].startswith("rapp_brainstem/")]:
        copy = kernel["src"] / rel[len("rapp_brainstem/"):]
        assert copy.read_bytes() == (REPO_ROOT / rel).read_bytes(), rel
