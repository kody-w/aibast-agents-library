"""Hermetic portal tests: real workers, fake CLI, project-local pytest basetemp."""

import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time

import pytest

from agents import copilot_cli_agent as tasks


ACTOR = {"sender": "+15550100101", "chat": "synthetic-owner-chat"}
OTHER = {"sender": "+15550100102", "chat": "synthetic-other-chat"}
SAME_SENDER_OTHER_CHAT = {"sender": ACTOR["sender"], "chat": "synthetic-second-chat"}
SCRIPT = Path(tasks.__file__).resolve()

FAKE_CLI = r'''
import json, os, signal, sys, time
from pathlib import Path

args = sys.argv[1:]
prompt = args[args.index("-p") + 1]
mode = prompt.splitlines()[0]
with open("starts.txt", "a") as marker:
    marker.write("started\n")
observation = {
    "argv": args, "cwd": os.getcwd(),
    "env": {k: os.environ.get(k) for k in (
        "COPILOT_HOME", "COPILOT_ALLOW_ALL", "COPILOT_AUTO_UPDATE",
        "COPILOT_PROVIDER_BASE_URL", "COPILOT_CUSTOM_INSTRUCTIONS_DIRS", "TMPDIR",
        "BASH_ENV", "RAPP_COPILOT_WORKER_TOKEN"
    )},
    "auth_env_present": [key for key in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN") if key in os.environ]
}
auth_metadata = Path(os.environ["COPILOT_HOME"]) / "config.json"
observation["auth_metadata"] = json.loads(auth_metadata.read_text()) if auth_metadata.exists() else None
Path("observed.json").write_text(json.dumps(observation))
if mode == "fail":
    print("partial output is not success", flush=True)
    print("synthetic CLI refusal", file=sys.stderr, flush=True)
    sys.exit(7)
if mode == "empty":
    sys.exit(0)
if mode == "slow":
    print("phase one", flush=True)
    time.sleep(0.7)
    print("phase two", flush=True)
    time.sleep(0.3)
if mode in ("sleep", "stubborn"):
    if mode == "stubborn":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    print("waiting", flush=True)
    time.sleep(30)
if mode == "crash-worker":
    # This executable's direct parent is the test's dedicated worker, never a service.
    os.kill(os.getppid(), signal.SIGKILL)
    sys.exit(0)
if mode == "huge":
    print("x" * 32768, flush=True)
if mode == "artifact":
    Path("report.txt").write_text("deliberate synthetic artifact\n")
    Path("not-declared.txt").write_text("must not be published\n")
if mode == "symlink-artifact":
    Path("report.txt").symlink_to(Path.cwd().parent / "task.txt")
if mode == "hardlink-artifact":
    os.link(Path.cwd().parent / "task.txt", "report.txt")
if mode == "executable-artifact":
    Path("report.txt").write_bytes(b"MZsynthetic-not-executable")
if mode == "large-artifact":
    Path("report.txt").write_bytes(b"x" * 128)
if mode == "invented-path":
    print("/arbitrary/generated/path/never-open-this.txt", flush=True)
print("synthetic final result", flush=True)
'''


def save_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")
    path.chmod(0o600)


@pytest.fixture
def config(tmp_path, monkeypatch):
    for key in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN", "GH_HOST", "COPILOT_GH_HOST"):
        monkeypatch.delenv(key, raising=False)
    binary = tmp_path / "fake-copilot"
    binary.write_text(f"#!{sys.executable}\n" + FAKE_CLI, encoding="utf-8")
    binary.chmod(0o700)
    staging = tmp_path / "staging"
    staging.mkdir(mode=0o700)
    path = tmp_path / "portal.json"
    value = {
        "version": 1,
        "jobs_dir": str(tmp_path / "jobs"),
        "staging_root": str(staging),
        "copilot_path": str(binary),
        "authorized": [ACTOR, OTHER, SAME_SENDER_OTHER_CHAT],
        "profiles": {
            "read-only": {"available_tools": ["view", "glob", "rg"]},
            "workspace-write": {"available_tools": ["view", "apply_patch"], "allow_tools": ["write"]},
        },
        "approval_ttl_seconds": 60,
        "max_runtime_seconds": 5,
    }
    save_json(path, value)
    return path


def update_config(config, **fields):
    value = json.loads(config.read_text())
    value.update(fields)
    save_json(config, value)


def request(store, operation, actor=ACTOR, **fields):
    return store.handle({"op": operation, "actor": actor, **fields})


def submit(store, prompt="success", request_id=None, **fields):
    return request(store, "submit", prompt=prompt, request_id=request_id or f"event-{time.time_ns()}",
                   profile="read-only", **fields)


def approve(store, submission, **fields):
    return request(store, "approve", job_id=submission["job"]["job_id"],
                   approval_token=submission["approval"]["token"], **fields)


def wait_for(store, job_id, predicate=None, timeout=10):
    deadline = time.monotonic() + timeout
    predicate = predicate or (lambda value: value["job"]["status"] in tasks._TERMINAL)
    last = None
    while time.monotonic() < deadline:
        last = request(store, "result", job_id=job_id)
        assert last["ok"], last
        if predicate(last):
            return last
        time.sleep(0.04)
    pytest.fail(f"worker did not reach expected state: {last}")


def invoke(config, body):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--portal-config", str(config)],
        input=json.dumps(body), capture_output=True, text=True, timeout=10,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    return result, json.loads(result.stdout)


def test_import_is_inert_and_does_not_import_brainstem(tmp_path):
    home = tmp_path / "empty-home"
    home.mkdir()
    code = (
        "import importlib.util, pathlib, sys; "
        f"sys.path.insert(0, {str(SCRIPT.parent)!r}); "
        f"s=importlib.util.spec_from_file_location('portal_source', {str(SCRIPT)!r}); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
        "assert 'brainstem' not in sys.modules; "
        "assert not (pathlib.Path.home()/'.brainstem').exists()"
    )
    result = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True,
                            env={**os.environ, "HOME": str(home)}, timeout=10)
    assert result.returncode == 0, result.stderr
    assert list(home.iterdir()) == []


def test_submit_is_inert_private_and_legacy_records_stay_unmodified(config):
    store = tasks.PortalTaskStore(config)
    legacy = store.root / "20260101-120000"
    legacy.mkdir()
    (legacy / "meta.json").write_text('{"pid": 123, "task": "legacy local task"}')
    before = (legacy / "meta.json").read_bytes()
    result = submit(store)
    assert result["ok"] and result["job"]["status"] == "pending_approval"
    job = store.root / result["job"]["job_id"]
    assert not (job / "workspace" / "starts.txt").exists()
    for path in [job, job / "inputs", job / "workspace", store.root]:
        assert stat.S_IMODE(path.stat().st_mode) == 0o700
    for path in [job / "meta.json", job / "task.txt", job / "out.log"]:
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert (legacy / "meta.json").read_bytes() == before
    listed = request(store, "list")
    assert len(listed["jobs"]) == 1
    assert listed["jobs"][0]["job_id"] == result["job"]["job_id"]
    assert "approval" not in listed["jobs"][0]


def test_concurrent_process_submissions_have_unique_ids(config):
    def one(index):
        process, result = invoke(config, {"op": "submit", "actor": ACTOR,
                                         "request_id": f"concurrent-{index}", "prompt": "success",
                                         "profile": "read-only"})
        assert process.returncode == 0, (process.stderr, result)
        return result["job"]["job_id"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        ids = list(pool.map(one, range(20)))
    assert len(ids) == len(set(ids)) == 20


def test_same_event_is_idempotent_and_changed_payload_is_rejected(config):
    store = tasks.PortalTaskStore(config)
    first = submit(store, request_id="same-event")
    second = submit(store, request_id="same-event")
    assert first["job"]["job_id"] == second["job"]["job_id"]
    assert first["approval"] == second["approval"]
    assert second["duplicate"]
    assert second["job"]["request_id"] == "same-event"
    changed = submit(store, prompt="different", request_id="same-event")
    assert changed["error"]["code"] == "idempotency_conflict"
    assert len(request(store, "list")["jobs"]) == 1


def test_concurrent_duplicate_submissions_share_one_approval(config):
    body = {"op": "submit", "actor": ACTOR, "request_id": "concurrent-same-event",
            "prompt": "success", "profile": "read-only"}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        replies = list(pool.map(lambda _: invoke(config, body)[1], range(6)))
    assert all(reply["ok"] for reply in replies)
    assert len({reply["job"]["job_id"] for reply in replies}) == 1
    assert len({reply["approval"]["token"] for reply in replies}) == 1


def test_concurrent_approvals_start_exactly_one_worker(config):
    store = tasks.PortalTaskStore(config)
    submission = submit(store, prompt="slow")
    body = {"op": "approve", "actor": ACTOR, "job_id": submission["job"]["job_id"],
            "approval_token": submission["approval"]["token"]}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        replies = list(pool.map(lambda _: invoke(config, body)[1], range(6)))
    assert sum(reply["ok"] for reply in replies) == 1
    assert all(reply["ok"] or reply["error"]["code"] == "approval_used" for reply in replies)
    wait_for(store, submission["job"]["job_id"])
    marker = store.root / submission["job"]["job_id"] / "workspace" / "starts.txt"
    assert marker.read_text() == "started\n"


def test_history_pagination_is_scoped_and_stable(config):
    store = tasks.PortalTaskStore(config)
    ids = {submit(store)["job"]["job_id"] for _ in range(7)}
    page = request(store, "list", limit=3)
    collected = {job["job_id"] for job in page["jobs"]}
    while page["next_before"]:
        page = request(store, "list", limit=3, before=page["next_before"])
        collected.update(job["job_id"] for job in page["jobs"])
    assert collected == ids
    assert request(store, "list", actor=OTHER, limit=3)["jobs"] == []


@pytest.mark.parametrize("actor", [OTHER, SAME_SENDER_OTHER_CHAT])
def test_wrong_sender_or_thread_cannot_approve_read_or_cancel(config, actor):
    store = tasks.PortalTaskStore(config)
    submission = submit(store)
    job_id = submission["job"]["job_id"]
    for operation in ("status", "result", "cancel", "recover"):
        assert request(store, operation, actor=actor, job_id=job_id)["error"]["code"] == "not_found"
    assert approve(store, submission, actor=actor)["error"]["code"] == "not_found"
    assert request(store, "list", actor=actor)["jobs"] == []
    assert request(store, "status", job_id=job_id)["job"]["status"] == "pending_approval"


def test_normalized_sender_matches_but_unconfigured_actor_is_denied(config):
    store = tasks.PortalTaskStore(config)
    normalized = {"sender": "+1 (555) 010-0101", "chat": ACTOR["chat"]}
    good = request(store, "submit", actor=normalized, request_id="normalized",
                   prompt="success", profile="read-only")
    assert good["ok"]
    denied = request(store, "list", actor={"sender": OTHER["sender"], "chat": ACTOR["chat"]})
    assert denied["error"]["code"] == "forbidden"


def test_boolean_or_wrong_token_cannot_authorize_work(config):
    store = tasks.PortalTaskStore(config)
    submission = submit(store)
    job_id = submission["job"]["job_id"]
    bad = request(store, "approve", job_id=job_id, approved=True)
    assert bad["error"]["code"] == "invalid_request"
    bad = request(store, "approve", job_id=job_id, approval_token="untrusted")
    assert bad["error"]["code"] == "approval_required"
    bad = submit(store, profile_override="--allow-all")
    assert bad["error"]["code"] == "invalid_request"
    assert not (store.root / job_id / "workspace" / "starts.txt").exists()


def test_expired_approval_never_starts_cli(config, monkeypatch):
    store = tasks.PortalTaskStore(config)
    submission = submit(store)
    expires = submission["approval"]["expires_at"]
    monkeypatch.setattr(tasks.time, "time", lambda: expires + 1)
    assert approve(store, submission)["error"]["code"] == "approval_expired"
    status = request(store, "result", job_id=submission["job"]["job_id"])
    assert status["job"]["status"] == "expired"
    assert status["result"]["exit_code"] is None


@pytest.mark.parametrize("mutation", ["prompt", "lifetime", "policy", "attachment"])
def test_approval_binds_exact_inputs_lifetime_and_policy(config, mutation):
    store = tasks.PortalTaskStore(config)
    staged = store.staging / "note.txt"
    staged.write_text("synthetic attachment")
    submission = submit(store, attachments=[{"path": str(staged), "name": "note.txt", "mime": "text/plain"}])
    directory = store.root / submission["job"]["job_id"]
    meta = tasks._read_json(directory / "meta.json")
    if mutation == "prompt":
        (directory / "task.txt").write_text("changed prompt")
    elif mutation == "lifetime":
        meta["approval"]["expires_at"] += 600
        save_json(directory / "meta.json", meta)
    elif mutation == "attachment":
        (directory / meta["spec"]["attachments"][0]["path"]).write_text("changed attachment")
    else:
        update_config(config, max_runtime_seconds=10)
        store = tasks.PortalTaskStore(config)
    assert approve(store, submission)["error"]["code"] == "approval_changed"
    assert not (directory / "workspace" / "starts.txt").exists()


def test_worker_completes_after_approver_exits_and_replay_cannot_start_twice(config):
    store = tasks.PortalTaskStore(config)
    submission = submit(store, prompt="slow")
    job_id = submission["job"]["job_id"]
    process, response = invoke(config, {"op": "approve", "actor": ACTOR, "job_id": job_id,
                                       "approval_token": submission["approval"]["token"]})
    assert process.returncode == 0 and response["ok"]
    # A newly constructed adapter has no Popen handles or process-local task state.
    restarted = tasks.PortalTaskStore(config)
    assert request(restarted, "recover", job_id=job_id)["ok"]
    terminal = wait_for(restarted, job_id)
    assert terminal["job"]["status"] == "succeeded"
    assert terminal["result"]["exit_code"] == 0
    assert "synthetic final result" in terminal["result"]["response"]
    assert approve(store, submission)["error"]["code"] == "approval_used"
    assert (store.root / job_id / "workspace" / "starts.txt").read_text() == "started\n"
    assert terminal["events"][-1]["type"] == "completed"


def test_real_worker_reports_incremental_output_and_stable_completion_event(config):
    store = tasks.PortalTaskStore(config)
    submission = submit(store, prompt="slow")
    job_id = submission["job"]["job_id"]
    assert approve(store, submission)["ok"]
    first = wait_for(store, job_id, lambda r: "phase one" in r["stdout"]["text"] and r["worker_active"])
    offset = first["stdout"]["next_offset"]
    terminal = wait_for(store, job_id)
    remainder = request(store, "status", job_id=job_id, stdout_offset=offset,
                        event_offset=first["next_event_offset"])
    assert "phase one" not in remainder["stdout"]["text"]
    assert "phase two" in remainder["stdout"]["text"]
    assert terminal["events"][-1]["id"] == remainder["events"][-1]["id"]
    assert request(store, "status", job_id=job_id, event_offset=terminal["next_event_offset"])["events"] == []


@pytest.mark.parametrize("prompt,code,error", [
    ("fail", 7, "cli_failed"), ("empty", 0, "empty_result"), ("huge", 0, "output_limit"),
])
def test_cli_error_empty_and_oversized_outputs_are_truthful(config, prompt, code, error):
    update_config(config, max_output_bytes=4096)
    store = tasks.PortalTaskStore(config)
    submission = submit(store, prompt=prompt)
    assert approve(store, submission)["ok"]
    result = wait_for(store, submission["job"]["job_id"])
    assert result["job"]["status"] == "failed"
    assert result["result"]["exit_code"] == code
    assert result["result"]["error"]["code"] == error
    if prompt == "fail":
        assert "partial output" in result["result"]["response"]
        assert "synthetic CLI refusal" in result["stderr"]["text"]


def test_missing_cli_after_approval_is_failed_not_success(config):
    store = tasks.PortalTaskStore(config)
    submission = submit(store)
    directory = store.root / submission["job"]["job_id"]
    Path(store.binary).write_text("#!/a/nonexistent/synthetic/interpreter\n", encoding="utf-8")
    assert approve(store, submission)["ok"]
    result = wait_for(store, directory.name)
    assert result["job"]["status"] == "failed"
    assert result["result"]["exit_code"] is None
    assert result["result"]["error"]["code"] == "worker_failed"
    assert "FileNotFoundError" in (directory / "worker.log").read_text()


def test_results_and_failure_recovery_work_when_cli_or_staging_is_unavailable(config):
    store = tasks.PortalTaskStore(config)
    completed = submit(store)
    assert approve(store, completed)["ok"]
    wait_for(store, completed["job"]["job_id"])
    pending = submit(store)
    Path(store.binary).unlink()
    store.staging.rmdir()
    restarted = tasks.PortalTaskStore(config)
    assert request(restarted, "result", job_id=completed["job"]["job_id"])["job"]["status"] == "succeeded"
    assert approve(restarted, pending)["ok"]
    failed = wait_for(restarted, pending["job"]["job_id"])
    assert failed["job"]["status"] == "failed"
    assert failed["result"]["error"]["code"] == "worker_unavailable"
    assert failed["result"]["exit_code"] is None
    assert approve(restarted, pending)["error"]["code"] == "approval_used"


def test_worker_error_commits_terminal_state_before_releasing_lease(config, monkeypatch):
    store = tasks.PortalTaskStore(config)
    submission = submit(store)
    directory = store.root / submission["job"]["job_id"]
    meta = tasks._read_json(directory / "meta.json")
    token = "synthetic-worker-token"
    meta["status"] = "queued"
    meta["worker_token_hash"] = hashlib.sha256(token.encode()).hexdigest()
    meta["approval"].update(token=None, consumed_at=time.time())
    save_json(directory / "meta.json", meta)
    original = store._finish
    def checked_finish(*args, **kwargs):
        assert store._worker_active(directory), "terminal commit must still hold the worker lease"
        return original(*args, **kwargs)
    def broken_popen(*args, **kwargs):
        raise OSError("synthetic launch failure")
    monkeypatch.setattr(store, "_finish", checked_finish)
    monkeypatch.setattr(tasks.subprocess, "Popen", broken_popen)
    assert store.run_worker(directory.name, token) == 1
    assert not store._worker_active(directory)
    assert request(store, "result", job_id=directory.name)["job"]["status"] == "failed"


@pytest.mark.parametrize("prompt", ["sleep", "stubborn"])
def test_cancellation_is_supervised_and_never_signals_persisted_pids(config, prompt):
    store = tasks.PortalTaskStore(config)
    submission = submit(store, prompt=prompt)
    job_id = submission["job"]["job_id"]
    assert approve(store, submission)["ok"]
    wait_for(store, job_id, lambda r: "waiting" in r["stdout"]["text"])
    assert request(store, "cancel", job_id=job_id)["ok"]
    terminal = wait_for(store, job_id)
    assert terminal["job"]["status"] == "cancelled"
    assert terminal["result"]["exit_code"] in {-signal.SIGTERM, -signal.SIGKILL}
    assert request(store, "cancel", job_id=job_id)["already_terminal"]


def test_pending_cancellation_and_unapproved_worker_stay_inert(config):
    store = tasks.PortalTaskStore(config)
    submission = submit(store)
    job_id = submission["job"]["job_id"]
    assert store.run_worker(job_id, "model-supplied-token") == 0
    assert request(store, "cancel", job_id=job_id)["job"]["status"] == "cancelled"
    assert approve(store, submission)["error"]["code"] == "approval_used"
    assert not (store.root / job_id / "workspace" / "starts.txt").exists()


def test_worker_timeout_is_terminal(config):
    update_config(config, max_runtime_seconds=0.25)
    store = tasks.PortalTaskStore(config)
    submission = submit(store, prompt="sleep")
    assert approve(store, submission)["ok"]
    result = wait_for(store, submission["job"]["job_id"])
    assert result["job"]["status"] == "failed"
    assert result["result"]["error"]["code"] == "timeout"
    assert result["result"]["exit_code"] == -signal.SIGTERM


def test_actual_worker_loss_recovers_as_interrupted_without_rerunning(config):
    store = tasks.PortalTaskStore(config)
    submission = submit(store, prompt="crash-worker")
    job_id = submission["job"]["job_id"]
    assert approve(store, submission)["ok"]
    result = wait_for(tasks.PortalTaskStore(config), job_id)
    assert result["job"]["status"] == "interrupted"
    assert result["result"]["exit_code"] is None
    assert result["job"]["execution_may_continue"] is True
    assert (store.root / job_id / "workspace" / "starts.txt").read_text() == "started\n"


def test_reused_or_stale_pid_is_not_liveness_and_is_never_killed(config, monkeypatch):
    store = tasks.PortalTaskStore(config)
    submission = submit(store)
    directory = store.root / submission["job"]["job_id"]
    meta = tasks._read_json(directory / "meta.json")
    meta.update(status="running", pid=os.getpid(), worker_pid=os.getpid(), child_pid=os.getpid(), started_at=time.time())
    meta["approval"].update(token=None, consumed_at=time.time() - 30)
    save_json(directory / "meta.json", meta)
    monkeypatch.setattr(tasks.os, "kill", lambda *a: pytest.fail("must never signal a persisted PID"))
    monkeypatch.setattr(tasks.os, "killpg", lambda *a: pytest.fail("must never signal a persisted process group"))
    recovered = request(store, "recover", job_id=directory.name)
    assert recovered["job"]["status"] == "interrupted"
    assert request(store, "cancel", job_id=directory.name)["already_terminal"]


def test_recovery_reconciles_result_committed_before_metadata(config):
    store = tasks.PortalTaskStore(config)
    submission = submit(store)
    directory = store.root / submission["job"]["job_id"]
    meta = tasks._read_json(directory / "meta.json")
    meta.update(status="running", started_at=time.time())
    meta["approval"].update(token=None, consumed_at=time.time() - 30)
    save_json(directory / "meta.json", meta)
    save_json(directory / "result.json", {
        "schema": tasks.PORTAL_SCHEMA, "job_id": directory.name, "spec_hash": meta["spec_hash"],
        "status": "succeeded", "exit_code": 0, "error": None, "response": "committed result",
        "artifacts": [],
    })
    result = request(store, "result", job_id=directory.name)
    assert result["job"]["status"] == "succeeded"
    assert result["result"]["response"] == "committed result"


def test_recovery_does_not_accept_a_result_from_another_job(config):
    store = tasks.PortalTaskStore(config)
    submission = submit(store)
    directory = store.root / submission["job"]["job_id"]
    meta = tasks._read_json(directory / "meta.json")
    meta.update(status="running", started_at=time.time())
    meta["approval"].update(token=None, consumed_at=time.time() - 30)
    save_json(directory / "meta.json", meta)
    save_json(directory / "result.json", {
        "schema": tasks.PORTAL_SCHEMA, "job_id": "another-job", "spec_hash": meta["spec_hash"],
        "status": "succeeded", "exit_code": 0, "response": "must not be accepted",
    })
    result = request(store, "result", job_id=directory.name)
    assert result["error"]["code"] == "state_corrupt"


def test_pending_launch_is_not_replayed_after_startup_allowance(config):
    store = tasks.PortalTaskStore(config)
    submission = submit(store)
    directory = store.root / submission["job"]["job_id"]
    meta = tasks._read_json(directory / "meta.json")
    meta["status"] = "queued"
    meta["approval"].update(token=None, consumed_at=time.time() - 30)
    save_json(directory / "meta.json", meta)
    result = request(store, "recover", job_id=directory.name)
    assert result["job"]["status"] == "interrupted"
    assert result["job"]["execution_may_continue"] is False
    assert not (directory / "workspace" / "starts.txt").exists()


def test_attachment_snapshot_is_bounded_and_detached_from_staging(config):
    store = tasks.PortalTaskStore(config)
    source = store.staging / "note.txt"
    data = b"synthetic data, not instructions"
    source.write_bytes(data)
    submission = submit(store, attachments=[{
        "path": str(source), "name": "note.txt", "mime": "text/plain",
        "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
    }])
    assert submission["ok"]
    source.unlink()
    assert approve(store, submission)["ok"]
    result = wait_for(store, submission["job"]["job_id"])
    assert result["job"]["status"] == "succeeded"
    meta = tasks._read_json(store.root / submission["job"]["job_id"] / "meta.json")
    snapshot = store.root / submission["job"]["job_id"] / meta["spec"]["attachments"][0]["path"]
    assert snapshot.read_bytes() == data
    assert stat.S_IMODE(snapshot.stat().st_mode) == 0o600


@pytest.mark.parametrize("kind", ["outside", "symlink", "parent-symlink", "hardlink", "executable", "magic", "oversize", "inline"])
def test_unsafe_attachment_references_are_inert(config, tmp_path, kind):
    update_config(config, max_attachment_bytes=32)
    store = tasks.PortalTaskStore(config)
    outside = tmp_path / "outside.txt"
    outside.write_text("synthetic outside")
    source = store.staging / "input.txt"
    source.write_text("safe")
    if kind == "outside":
        source = outside
    elif kind == "symlink":
        source.unlink()
        source.symlink_to(outside)
    elif kind == "parent-symlink":
        link = store.staging / "linked"
        link.symlink_to(tmp_path, target_is_directory=True)
        source = link / "outside.txt"
    elif kind == "hardlink":
        source.unlink()
        os.link(outside, source)
    elif kind == "executable":
        source.chmod(0o700)
    elif kind == "magic":
        source.write_bytes(b"MZnot-a-real-executable")
    elif kind == "oversize":
        source.write_bytes(b"x" * 33)
    reference = {"path": str(source), "name": "input.txt", "mime": "text/plain"}
    if kind == "inline":
        reference["base64"] = "not accepted"
    response = submit(store, attachments=[reference])
    assert not response["ok"], response
    assert request(store, "list")["jobs"] == []


def test_only_predeclared_regular_artifacts_are_published(config):
    store = tasks.PortalTaskStore(config)
    submission = submit(store, prompt="artifact", artifact_paths=["report.txt"])
    assert approve(store, submission)["ok"]
    result = wait_for(store, submission["job"]["job_id"])
    assert result["job"]["status"] == "succeeded"
    artifacts = result["result"]["artifacts"]
    assert len(artifacts) == 1 and artifacts[0]["name"] == "report.txt"
    assert artifacts[0]["mime"] == "text/plain"
    artifact = Path(artifacts[0]["path"])
    assert artifact.parent == store.root / submission["job"]["job_id"] / "artifacts"
    assert artifact.name.startswith(submission["job"]["job_id"])
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == artifacts[0]["sha256"]
    assert stat.S_IMODE(artifact.stat().st_mode) == 0o600
    assert any(event["type"] == "artifact" for event in result["events"])
    assert "not-declared.txt" not in json.dumps(artifacts)


@pytest.mark.parametrize("prompt", ["symlink-artifact", "hardlink-artifact", "executable-artifact", "large-artifact", "success"])
def test_bad_or_missing_declared_artifact_is_an_explicit_failure(config, prompt):
    update_config(config, max_artifact_bytes=64)
    store = tasks.PortalTaskStore(config)
    submission = submit(store, prompt=prompt, artifact_paths=["report.txt"])
    assert approve(store, submission)["ok"]
    result = wait_for(store, submission["job"]["job_id"])
    assert result["job"]["status"] == "failed"
    expected = "artifact_missing" if prompt == "success" else "artifact_rejected"
    assert result["result"]["error"]["code"] == expected
    assert result["result"]["artifacts"] == []
    assert not any(event["type"] == "artifact" for event in result["events"])


def test_generated_paths_are_never_followed_and_unsafe_declarations_rejected(config):
    store = tasks.PortalTaskStore(config)
    assert not submit(store, artifact_paths=["../out.log"])["ok"]
    assert not submit(store, artifact_paths=["/outside.txt"])["ok"]
    submission = submit(store, prompt="invented-path")
    assert approve(store, submission)["ok"]
    result = wait_for(store, submission["job"]["job_id"])
    assert result["job"]["status"] == "succeeded"
    assert result["result"]["artifacts"] == []


def test_partial_artifact_batch_is_not_published(config):
    store = tasks.PortalTaskStore(config)
    submission = submit(store, prompt="artifact", artifact_paths=["report.txt", "missing.txt"])
    assert approve(store, submission)["ok"]
    result = wait_for(store, submission["job"]["job_id"])
    assert result["job"]["status"] == "failed"
    assert result["result"]["error"]["code"] == "artifact_missing"
    assert not result["result"]["artifacts"]
    assert not any(event["type"] == "artifact" for event in result["events"])
    assert list((store.root / submission["job"]["job_id"] / "artifacts").iterdir()) == []


def test_explicit_cli_permissions_and_configuration_are_isolated(config, monkeypatch):
    monkeypatch.setenv("COPILOT_ALLOW_ALL", "true")
    monkeypatch.setenv("COPILOT_PROVIDER_BASE_URL", "https://untrusted.invalid")
    monkeypatch.setenv("COPILOT_CUSTOM_INSTRUCTIONS_DIRS", "/untrusted/instructions")
    monkeypatch.setenv("BASH_ENV", "/untrusted/startup")
    store = tasks.PortalTaskStore(config)
    submission = submit(store)
    assert approve(store, submission)["ok"]
    wait_for(store, submission["job"]["job_id"])
    directory = store.root / submission["job"]["job_id"]
    observed = json.loads((directory / "workspace" / "observed.json").read_text())
    argv = observed["argv"]
    assert argv[argv.index("--model") + 1] == "gpt-6-astra"
    assert "--available-tools=view,glob,rg" in argv
    assert {"--deny-tool=shell", "--deny-tool=write", "--deny-tool=url", "--disallow-temp-dir"} <= set(argv)
    assert not {"--allow-all", "--allow-all-tools", "--allow-all-paths", "--allow-all-urls", "--yolo"} & set(argv)
    assert observed["env"]["COPILOT_ALLOW_ALL"] == "false"
    assert observed["env"]["COPILOT_PROVIDER_BASE_URL"] is None
    assert observed["env"]["BASH_ENV"] is None
    assert observed["env"]["RAPP_COPILOT_WORKER_TOKEN"] is None
    assert observed["env"]["COPILOT_HOME"] == str(directory / "copilot-state")
    assert Path(observed["env"]["TMPDIR"]).is_relative_to(directory)


def test_policy_cannot_expose_state_or_use_blanket_tool_permissions(config):
    value = json.loads(config.read_text())
    value["profiles"]["unsafe"] = {"available_tools": ["bash"], "allow_tools": ["shell(*)"]}
    value["profiles"]["state"] = {"available_tools": ["view"], "add_dirs": [str(config.parent)]}
    save_json(config, value)
    store = tasks.PortalTaskStore(config)
    for name in ("unsafe", "state"):
        result = request(store, "submit", request_id=name, prompt="success", profile=name)
        assert result["error"]["code"] == "invalid_config"
    child = store.root / "private-child"
    child.mkdir()
    value["profiles"]["child"] = {"available_tools": ["view"], "add_dirs": [str(child)]}
    save_json(config, value)
    result = request(tasks.PortalTaskStore(config), "submit", request_id="child",
                     prompt="success", profile="child")
    assert result["error"]["code"] == "invalid_config"


@pytest.mark.parametrize("ttl", [0, True, float("inf"), 3601])
def test_approval_lifetime_must_be_explicitly_finite_and_bounded(config, ttl):
    update_config(config, approval_ttl_seconds=ttl)
    with pytest.raises(tasks.PortalError):
        tasks.PortalTaskStore(config)


def test_invalid_config_and_corrupt_state_fail_closed(config):
    config.chmod(0o644)
    with pytest.raises(tasks.PortalError, match="0600"):
        tasks.PortalTaskStore(config)
    config.chmod(0o600)
    store = tasks.PortalTaskStore(config)
    submission = submit(store)
    path = store.root / submission["job"]["job_id"] / "meta.json"
    path.write_text("{broken")
    result = request(store, "status", job_id=submission["job"]["job_id"])
    assert not result["ok"]
    assert path.read_text() == "{broken"


def test_metadata_symlink_is_not_read_or_overwritten(config, tmp_path):
    store = tasks.PortalTaskStore(config)
    submission = submit(store)
    outside = tmp_path / "untouched.txt"
    outside.write_text("synthetic unrelated file")
    target = store.root / submission["job"]["job_id"] / "meta.json"
    target.unlink()
    target.symlink_to(outside)
    assert not approve(store, submission)["ok"]
    assert outside.read_text() == "synthetic unrelated file"


def test_utf8_progress_cursor_does_not_split_a_character(config):
    store = tasks.PortalTaskStore(config)
    submission = submit(store)
    path = store.root / submission["job"]["job_id"] / "out.log"
    path.write_text("abc🦕def", encoding="utf-8")
    first = request(store, "status", job_id=submission["job"]["job_id"], limit=4)
    assert first["stdout"]["text"] == "abc"
    assert first["stdout"]["next_offset"] == 3
    second = request(store, "status", job_id=submission["job"]["job_id"], stdout_offset=3, limit=4)
    assert second["stdout"]["text"] == "🦕"
    assert second["stdout"]["next_offset"] == 7


def test_legacy_agent_remains_importable_and_local_ids_are_collision_safe(config, monkeypatch):
    store = tasks.PortalTaskStore(config)
    monkeypatch.setattr(tasks, "JOBS", str(store.root))
    monkeypatch.setattr(tasks, "_copilot_bin", lambda: store.binary)
    calls = []
    class FakeProcess:
        pid = 0
    def fake_popen(argv, **kwargs):
        calls.append(argv)
        return FakeProcess()
    monkeypatch.setattr(tasks.subprocess, "Popen", fake_popen)
    agent = tasks.CopilotCLIAgent()
    a = json.loads(agent.perform(action="dispatch", task="synthetic local task"))
    b = json.loads(agent.perform(action="dispatch", task="synthetic local task"))
    assert a["ok"] and b["ok"] and a["job_id"] != b["job_id"]
    assert "--allow-all" in calls[0]  # legacy local API only; portal tests explicitly forbid this.
    assert json.loads(agent.perform(action="result", job_id=a["job_id"]))["status"] == "done"
    assert request(store, "list")["jobs"] == []


def test_cli_json_protocol_rejects_extra_fields_and_never_accepts_non_json(config):
    process, result = invoke(config, {"op": "list", "actor": ACTOR, "approved": True})
    assert process.returncode == 1 and result["error"]["code"] == "invalid_request"
    bad = subprocess.run([sys.executable, str(SCRIPT), "--portal-config", str(config)],
                         input="not json", capture_output=True, text=True, timeout=10)
    assert bad.returncode == 1
    assert json.loads(bad.stdout)["error"]["code"] == "invalid_request"
    assert bad.stderr == ""


def configure_oauth(config):
    user = {"host": "https://github.com", "login": "synthetic-account"}
    update_config(config, auth_account=user)
    return user


def test_pinned_oauth_never_reads_parent_config_or_inherits_secrets_or_permissions(config, monkeypatch):
    user = configure_oauth(config)
    parent_home = config.parent / "unrelated-parent-home"
    source = parent_home / ".copilot" / "config.json"
    source.parent.mkdir(parents=True)
    source.write_text("// BROKEN parent config with SYNTHETIC_SECRET_DO_NOT_COPY and permissive hooks; never read it.")
    original = source.read_bytes()
    monkeypatch.setenv("HOME", str(parent_home))
    read_json = tasks._read_json
    def guarded_read(path):
        assert Path(path) != source, "must not read the parent Copilot configuration"
        return read_json(path)
    monkeypatch.setattr(tasks, "_read_json", guarded_read)
    for key in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        monkeypatch.setenv(key, "ghp_SYNTHETIC_CLASSIC_MUST_NOT_PROPAGATE")
    store = tasks.PortalTaskStore(config)
    submission = submit(store)
    directory = store.root / submission["job"]["job_id"]
    assert not (directory / "copilot-state" / "config.json").exists()
    assert approve(store, submission)["ok"]
    terminal = wait_for(store, directory.name)
    assert terminal["job"]["status"] == "succeeded"
    copied = tasks._read_json(directory / "copilot-state" / "config.json")
    assert copied == {"lastLoggedInUser": user, "loggedInUsers": [user]}
    assert source.read_bytes() == original
    assert stat.S_IMODE((directory / "copilot-state" / "config.json").stat().st_mode) == 0o600
    observed = json.loads((directory / "workspace" / "observed.json").read_text())
    assert observed["auth_metadata"] == copied
    assert observed["auth_env_present"] == []
    assert observed["env"]["COPILOT_ALLOW_ALL"] == "false"
    assert "--user" not in observed["argv"]
    assert "--available-tools=view,glob,rg" in observed["argv"]
    for path in directory.rglob("*"):
        if path.is_file():
            assert b"SYNTHETIC_SECRET_DO_NOT_COPY" not in path.read_bytes()
            assert b"ghp_SYNTHETIC_CLASSIC_MUST_NOT_PROPAGATE" not in path.read_bytes()


def test_oauth_account_switch_invalidates_the_pending_approval(config):
    configure_oauth(config)
    store = tasks.PortalTaskStore(config)
    submission = submit(store)
    changed = {"host": "https://github.com", "login": "new-synthetic-account"}
    update_config(config, auth_account=changed)
    assert approve(tasks.PortalTaskStore(config), submission)["error"]["code"] == "approval_changed"
    directory = store.root / submission["job"]["job_id"]
    assert not (directory / "workspace" / "starts.txt").exists()
    assert not (directory / "copilot-state" / "config.json").exists()


@pytest.mark.parametrize("mutation", ["missing", "unknown", "host", "login", "secret", "null"])
def test_invalid_pinned_oauth_metadata_fails_closed(config, mutation):
    user = configure_oauth(config)
    if mutation == "missing":
        bad = {"host": user["host"]}
    elif mutation == "unknown":
        bad = {**user, "permissions": ["*"]}
    elif mutation in {"host", "login"}:
        bad = {**user, mutation: "https://untrusted.invalid" if mutation == "host" else "not an account\n"}
    elif mutation == "secret":
        bad = {**user, "token": "SYNTHETIC_SECRET_DO_NOT_COPY"}
    else:
        bad = None
    update_config(config, auth_account=bad)
    with pytest.raises(tasks.PortalError) as caught:
        tasks.PortalTaskStore(config)
    assert caught.value.code == "auth_selector_invalid"
    assert "SYNTHETIC_SECRET" not in str(caught.value)


def test_general_copilot_config_source_option_is_rejected_without_reading_it(config):
    update_config(config, auth={"mode": "copilot_oauth", "source_config": "/must/not/read/config.json"})
    with pytest.raises(tasks.PortalError) as caught:
        tasks.PortalTaskStore(config)
    assert caught.value.code == "invalid_config"


def test_classic_pat_in_environment_is_rejected_without_exposing_it(config, monkeypatch):
    marker = "ghp_SYNTHETIC_CLASSIC_SECRET"
    monkeypatch.setenv("COPILOT_GITHUB_TOKEN", marker)
    store = tasks.PortalTaskStore(config)
    submission = submit(store)
    assert approve(store, submission)["ok"]
    directory = store.root / submission["job"]["job_id"]
    result = wait_for(store, directory.name)
    assert result["job"]["status"] == "failed"
    assert result["result"]["error"]["code"] == "auth_unsupported"
    assert result["result"]["exit_code"] is None
    assert not (directory / "workspace" / "starts.txt").exists()
    for path in directory.rglob("*"):
        if path.is_file():
            assert marker.encode() not in path.read_bytes()


def test_completed_history_needs_no_external_oauth_metadata(config):
    configure_oauth(config)
    store = tasks.PortalTaskStore(config)
    submission = submit(store)
    assert approve(store, submission)["ok"]
    wait_for(store, submission["job"]["job_id"])
    restarted = tasks.PortalTaskStore(config)
    assert request(restarted, "result", job_id=submission["job"]["job_id"])["job"]["status"] == "succeeded"


def test_permission_profiles_cannot_expose_parent_copilot_configuration(config, monkeypatch):
    configure_oauth(config)
    home = config.parent / "parent-home"
    auth_directory = home / ".copilot"
    auth_directory.mkdir(parents=True, mode=0o700)
    monkeypatch.setenv("HOME", str(home))
    values = json.loads(config.read_text())
    values["profiles"]["oauth-files"] = {"available_tools": ["view"], "add_dirs": [str(auth_directory)]}
    save_json(config, values)
    response = request(tasks.PortalTaskStore(config), "submit", prompt="success",
                       request_id="do-not-expose-auth", profile="oauth-files")
    assert response["error"]["code"] == "invalid_config"
