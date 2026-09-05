import importlib.util
import json
import shutil
import subprocess
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from test_creature_twin_agent import PROFILE, TEMPLATE, twin


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("test_terrarium_view", ROOT / "experiments/creature/terrarium.py")
view = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(view)
SETUP_SPEC = importlib.util.spec_from_file_location("test_terrarium_setup", ROOT / "experiments/creature/setup.py")
setup = importlib.util.module_from_spec(SETUP_SPEC)
SETUP_SPEC.loader.exec_module(setup)


@pytest.fixture
def http_view(tmp_path, monkeypatch):
    root = tmp_path / "terrarium"
    for name in ("payload", "agents", "dormant", "data"):
        (root / name).mkdir(parents=True)
    (root / "payload/genome_creature_agent.py").write_text(TEMPLATE)
    (root / "payload/index.html").write_text("<!doctype html><title>Real evidence</title>")
    (root / "agents/astra_agent.py").write_text(TEMPLATE)
    calls = []

    def native(port, path, payload=None, timeout=180):
        calls.append((path, payload))
        body = {"status": "ok", "agents": ["AstraCreature", "CreatureTwin"]}
        if path == "/chat":
            body = {"response": "Actual tool result", "agent_logs": [{"tool": "AstraCreature"}], "session_id": "fixture"}
        return 200, json.dumps(body).encode()

    monkeypatch.setattr(view, "local_request", native)
    server = ThreadingHTTPServer(("127.0.0.1", 0), view.BaseHTTPRequestHandler)
    port = server.server_address[1]
    config = {"brainstem_port": 7081, "ui_port": port}
    server.RequestHandlerClass = view.make_handler(root, config, twin)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}", calls, root
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def request(url, payload=None, headers=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def test_read_only_catalog_reflects_actual_files(http_view):
    url, calls, root = http_view
    status, raw = request(url + "/api/terrarium")
    data = json.loads(raw)
    assert status == 200
    assert data["creatures"][0]["id"] == "astra"
    assert data["creatures"][0]["status"] == "unhatched"
    assert calls == [("/health", None)]
    (root / "agents/astra_agent.py").rename(root / "dormant/astra_agent.py")
    _, raw = request(url + "/api/terrarium")
    assert json.loads(raw)["creatures"][0]["status"] == "dormant"


def test_actions_forward_only_to_native_chat(http_view):
    url, calls, _ = http_view
    payload = {"user_input": "Call AstraCreature with action=status."}
    status, raw = request(url + "/chat", payload)
    assert status == 200
    assert json.loads(raw)["response"] == "Actual tool result"
    assert calls == [("/chat", payload)]
    assert request(url + "/api/evolve", {"generations": 12})[0] == 404
    assert calls == [("/chat", payload)]


def test_external_origin_and_host_are_rejected(http_view):
    url, calls, _ = http_view
    assert request(url + "/chat", {"user_input": "hello"}, {"Origin": "https://example.com"})[0] == 403
    assert request(url + "/api/terrarium", headers={"Host": "example.com"})[0] == 403
    assert calls == []


@pytest.mark.parametrize("payload", [{}, {"user_input": 7}, {"user_input": " "}, {"user_input": "go", "endpoint": "https://example.com"}, []])
def test_invalid_chat_payload_is_not_forwarded(http_view, payload):
    url, calls, _ = http_view
    assert request(url + "/chat", payload)[0] == 400
    assert not calls


def test_source_download_preserves_standalone_file(http_view):
    url, _, _ = http_view
    status, raw = request(url + "/api/source/astra")
    assert status == 200
    assert raw.decode() == TEMPLATE
    assert request(url + "/api/source/../payload")[0] == 400


def test_egg_download_is_fixed_to_public_evidence(http_view, tmp_path):
    url, _, root = http_view
    public = root / "data/astra/public"
    public.mkdir(parents=True)
    egg = public / "egg.json"
    egg.write_text('{"fixture":"egg"}')
    assert request(url + "/api/egg/astra") == (200, b'{"fixture":"egg"}')
    egg.unlink()
    external = tmp_path / "private.json"
    external.write_text('{"private":"not served"}')
    egg.symlink_to(external)
    assert request(url + "/api/egg/astra")[0] == 400


def test_setup_forbids_live_brainstem_and_home(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    for location in (tmp_path, tmp_path / ".brainstem", tmp_path / ".brainstem/anything", tmp_path / ".copilot", Path("/")):
        with pytest.raises(setup.InstallError):
            setup.checked_root(location)
    assert setup.checked_root(tmp_path / ".brainstem-creature") == tmp_path / ".brainstem-creature"


def test_setup_does_not_follow_install_root_symlink(tmp_path):
    target = tmp_path / "existing"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises(setup.InstallError):
        setup.checked_root(link)


def test_all_actions_have_one_native_transport():
    source = (ROOT / "experiments/creature/terrarium.py").read_text()
    assert ".perform(" not in source
    assert '"/chat"' in source


@pytest.mark.parametrize("restore_egg", [False, True])
def test_installer_isolates_official_install_and_preserves_original(tmp_path, monkeypatch, restore_egg):
    real_home = tmp_path / "real-home"
    original = real_home / ".brainstem"
    original.mkdir(parents=True)
    sentinel = original / "do-not-change"
    sentinel.write_text("existing creature memory")
    shell = real_home / ".zshrc"
    shell.write_text("original shell")
    monkeypatch.setenv("HOME", str(real_home))
    source = tmp_path / "source"
    for name, relative in setup.PAYLOAD.items():
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if name == "genome_creature_agent.py":
            path.write_text(TEMPLATE)
        elif name == "creature_twin_agent.py":
            path.write_bytes((ROOT / "agents/experimental/creature_twin_agent.py").read_bytes())
        else:
            path.write_text("test fixture, not executed")
    monkeypatch.setattr(setup, "download", lambda url: b"#!/bin/bash\n# test fixture\n")
    invocations = []
    target = real_home / ".brainstem-creature"

    def official(command, **kwargs):
        invocations.append((command, kwargs))
        if command[0] == "/bin/bash":
            assert kwargs["env"]["HOME"] == str(target / "bootstrap-home")
            assert command[-1] == "--no-launch"
            runtime = target / "bootstrap-home/.brainstem/src/rapp_brainstem"
            (runtime / "agents").mkdir(parents=True)
            (runtime / "brainstem.py").write_text("# immutable kernel fixture\n")
            (runtime / "agents/basic_agent.py").write_text("# shared base fixture\n")
        if command[-2] == "-c" and "direct_url.json" in command[-1]:
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps({
                "version": "fixture",
                "profile": "lispy-core@1",
                "commit": setup.LISPY_COMMIT,
            }))
        return subprocess.CompletedProcess(command, 0, stdout="a" * 40 + "\n")

    monkeypatch.setattr(setup.subprocess, "run", official)
    egg_file = None
    if restore_egg:
        pytest.importorskip("lisppy", reason="This case exercises the optional creature VM.")
        from agents.experimental import genome_creature_agent

        egg, raw = genome_creature_agent._build_egg(
            genome_creature_agent._new_state("Astra", 41)
        )
        egg_file = tmp_path / "source.egg.json"
        egg_file.write_bytes(raw)
        source_agent = source / setup.PAYLOAD["genome_creature_agent.py"]
        source_agent.write_bytes(Path(genome_creature_agent.__file__).read_bytes())
    args = type("Args", (), {
        "root": target,
        "port": 7081,
        "ui_port": 7082,
        "source_root": source,
        "source_url": setup.DEFAULT_SOURCE,
        "egg": egg_file,
        "independent_auth": False,
    })()
    root, config = setup.install(args)
    assert root == target
    assert config["core_installer"] == setup.CORE_INSTALLER
    assert config["core_commit"] == "a" * 40
    assert sentinel.read_text() == "existing creature memory"
    assert shell.read_text() == "original shell"
    assert not (real_home / ".copilot").exists()
    for creature in (("astra",) if restore_egg else ("astra", "ember", "moss")):
        assert (root / "agents" / f"{creature}_agent.py").exists()
    if restore_egg:
        assert config["resume_generation"] == 0
        assert config["resume_genome_sha256"] == egg["state"]["genome_sha256"]
        assert (root / "data/astra/inbox" / f"{config['resume_egg_id']}.egg.json").read_bytes() == raw
        args.egg = None
    installed_source = (root / "agents/astra_agent.py").read_bytes()
    call_count = len(invocations)
    setup.install(args)
    assert len(invocations) == call_count
    assert (root / "agents/astra_agent.py").read_bytes() == installed_source


def test_installer_refuses_unrecognized_existing_directory(tmp_path):
    root = tmp_path / "existing"
    root.mkdir()
    sentinel = root / "private-data"
    sentinel.write_text("preserve")
    args = type("Args", (), {"root": root})()
    with pytest.raises(setup.InstallError, match="nonempty"):
        setup.install(args)
    assert sentinel.read_text() == "preserve"


def test_fresh_resume_sends_only_content_id_to_brainstem(tmp_path, monkeypatch):
    root = tmp_path / "resume"
    root.mkdir()
    (root / "pending.egg.json").write_text("large private egg body is not sent to the model")
    snapshot = root / "data/astra/public/snapshot.json"
    snapshot.parent.mkdir(parents=True)
    config = {
        "brainstem_port": 7083,
        "resume_agent_name": "AstraCreature",
        "resume_id": "astra",
        "resume_egg_id": "a" * 64,
        "resume_generation": 12,
        "resume_genome_sha256": "b" * 64,
    }

    def native(port, endpoint, payload):
        assert port == 7083
        assert endpoint == "/chat"
        assert "egg_id='" + "a" * 64 + "'" in payload["user_input"]
        assert "large private egg body" not in payload["user_input"]
        snapshot.write_text(json.dumps({
            "generation": 12,
            "genome_sha256": "b" * 64,
            "resumed_from": {"sha256": "a" * 64, "generation": 12},
        }))
        return 200, b'{"response":"resumed fixture"}'

    monkeypatch.setattr(view, "local_request", native)
    view.resume_pending(root, config)
    assert (root / "resumed.egg.json").exists()
    assert not (root / "pending.egg.json").exists()


def test_existing_login_is_read_only_and_never_copied_to_configuration(tmp_path):
    reference = tmp_path / "original-login"
    original = '{"access_token":"fixture-not-a-real-credential","refresh_token":"unused-fixture"}'
    reference.write_text(original)
    environment = {}
    view.apply_auth_reference(environment, str(reference))
    assert environment == {"GITHUB_TOKEN": "fixture-not-a-real-credential"}
    assert reference.read_text() == original
    assert list(tmp_path.iterdir()) == [reference]
    explicit = {"GITHUB_TOKEN": "explicit-fixture"}
    view.apply_auth_reference(explicit, str(reference))
    assert explicit["GITHUB_TOKEN"] == "explicit-fixture"
    independent = {}
    view.apply_auth_reference(independent, str(tmp_path / "does-not-exist"), independent=True)
    assert independent == {}


def test_invalid_login_does_not_leak_credential_contents(tmp_path):
    reference = tmp_path / "bad-login"
    reference.write_text('{"access_token": {"sensitive-fixture": "do-not-echo"}}')
    with pytest.raises(view.TerrariumError) as failure:
        view.apply_auth_reference({}, str(reference))
    assert "sensitive-fixture" not in str(failure.value)
    assert "do-not-echo" not in str(failure.value)


def test_refresh_control_recovers_after_action_finishes():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is only needed for the optional browser-control unit.")
    html = (ROOT / "experiments/creature/index.html").read_text()
    start = html.index("function renderReadState()")
    end = html.index("function renderHeader()", start)
    program = (
        "const assert = require('node:assert/strict');"
        "const state = {busy: true, staleError: null};"
        "const elements = {refresh: {disabled: false}, readError: {textContent: ''}};"
        "function setHidden() {};"
        + html[start:end]
        + "renderReadState(); assert.equal(elements.refresh.disabled, true);"
        "state.busy = false; renderReadState(); assert.equal(elements.refresh.disabled, false);"
    )
    subprocess.run([node, "-e", program], check=True, capture_output=True, text=True)
