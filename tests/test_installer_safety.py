"""Regression tests for destructive and fail-open installer paths."""

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INSTALLER = ROOT / "install.sh"
WINDOWS_INSTALLER = ROOT / "install.ps1"
LANDING_PAGE = ROOT / "index.html"


def installer_functions():
    text = INSTALLER.read_text(encoding="utf-8")
    return text.rsplit('\nmain "$@"', 1)[0]


def run_harness(tmp_path, body):
    script = f"""
set -e
export HOME={str(tmp_path)!r}
{installer_functions()}
{body}
"""
    return subprocess.run(
        ["bash"],
        input=script,
        text=True,
        capture_output=True,
        check=False,
    )


def init_source_repo(path, branch, brainstem_source, extra_file=None):
    (path / "rapp_brainstem").mkdir(parents=True)
    (path / "rapp_brainstem/VERSION").write_text("0.6.16\n", encoding="utf-8")
    (path / "rapp_brainstem/brainstem.py").write_text(
        brainstem_source,
        encoding="utf-8",
    )
    (path / "rapp_brainstem/requirements.txt").write_text(
        "flask\n",
        encoding="utf-8",
    )
    if extra_file:
        target = path / extra_file
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("snapshot\n", encoding="utf-8")
    subprocess.run(["git", "init", "-b", branch], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=path,
        check=True,
    )
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "fixture"],
        cwd=path,
        check=True,
        capture_output=True,
    )


def test_incomplete_matching_version_falls_through_to_repair(tmp_path):
    source = tmp_path / ".brainstem/src"
    (source / ".git").mkdir(parents=True)
    trace = tmp_path / "trace"
    result = run_harness(
        tmp_path,
        f"""
check_for_upgrade() {{ return 1; }}
brainstem_source_ready() {{ return 1; }}
check_prereqs() {{ echo prereqs >> {str(trace)!r}; }}
install_brainstem() {{ echo repair >> {str(trace)!r}; }}
setup_venv() {{ :; }}
setup_deps() {{ :; }}
install_cli() {{ :; }}
create_env() {{ :; }}
main --no-launch
""",
    )
    assert result.returncode == 0, result.stderr
    assert trace.read_text().splitlines() == ["prereqs", "repair"]


def test_same_version_different_requested_brainstem_tree_forces_refresh(tmp_path):
    installed = tmp_path / ".brainstem/src"
    staging = tmp_path / "staging-source"
    init_source_repo(installed, "main", "print('production')\n")
    init_source_repo(
        staging,
        "easy-mode-copilot-chat-pilot",
        "print('staging health public')\n",
    )

    result = run_harness(
        tmp_path,
        f"""
REPO_URL={str(staging)!r}
REPO_REF=easy-mode-copilot-chat-pilot
REMOTE_VERSION_URL=https://example.invalid/VERSION
SOURCE_OVERRIDE_REQUESTED=true
curl() {{ printf '0.6.16\\n'; }}
if check_for_upgrade; then echo REFRESH; else echo CURRENT; fi
""",
    )

    assert result.returncode == 0, result.stderr
    assert "REFRESH" in result.stdout
    assert "CURRENT" not in result.stdout


def test_same_version_staging_override_replaces_production_runtime(tmp_path):
    installed = tmp_path / ".brainstem/src"
    staging = tmp_path / "staging-source"
    init_source_repo(installed, "main", "print('production')\n")
    init_source_repo(
        staging,
        "easy-mode-copilot-chat-pilot",
        "print('staging health public')\n",
    )

    result = run_harness(
        tmp_path,
        f"""
SOURCE_OVERRIDE_REQUESTED=true
REPO_URL={str(staging)!r}
REPO_REF=easy-mode-copilot-chat-pilot
REMOTE_VERSION_URL=https://example.invalid/VERSION
curl() {{ printf '0.6.16\\n'; }}
install_brainstem
""",
    )

    assert result.returncode == 0, result.stderr
    assert (installed / "rapp_brainstem/brainstem.py").read_text(
        encoding="utf-8"
    ) == "print('staging health public')\n"


def test_full_commit_pin_checks_out_exact_runtime_bytes(tmp_path):
    remote = tmp_path / "remote"
    init_source_repo(remote, "main", "print('immutable release')\n")
    pinned_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=remote,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    (remote / "rapp_brainstem/brainstem.py").write_text(
        "print('moving branch')\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=remote, check=True)
    subprocess.run(
        ["git", "commit", "-m", "move branch"],
        cwd=remote,
        check=True,
        capture_output=True,
    )
    isolated = tmp_path / "custom-runtime"

    result = run_harness(
        tmp_path,
        f"""
BRAINSTEM_HOME={str(isolated)!r}
VENV_DIR="$BRAINSTEM_HOME/venv"
REPO_URL={str(remote)!r}
REPO_REF=main
PIN_VERSION={pinned_commit!r}
SOURCE_OVERRIDE_REQUESTED=true
install_brainstem
""",
    )

    assert result.returncode == 0, result.stderr
    assert subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=isolated / "src",
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip() == pinned_commit
    assert (isolated / "src/rapp_brainstem/brainstem.py").read_text(
        encoding="utf-8"
    ) == "print('immutable release')\n"


def test_requested_source_failure_keeps_runtime_and_fails_closed(tmp_path):
    installed = tmp_path / ".brainstem/src"
    init_source_repo(installed, "main", "print('production preserved')\n")

    result = run_harness(
        tmp_path,
        f"""
SOURCE_OVERRIDE_REQUESTED=true
REPO_URL={str(tmp_path / "missing-source")!r}
REPO_REF=easy-mode-copilot-chat-pilot
REMOTE_VERSION_URL=https://example.invalid/VERSION
curl() {{ printf '0.6.16\\n'; }}
install_brainstem
""",
    )

    assert result.returncode != 0
    assert "Could not refresh the requested repository/ref" in result.stdout
    assert (installed / "rapp_brainstem/brainstem.py").read_text(
        encoding="utf-8"
    ) == "print('production preserved')\n"


def test_same_version_without_explicit_override_stays_current(tmp_path):
    installed = tmp_path / ".brainstem/src"
    staging = tmp_path / "staging-source"
    init_source_repo(installed, "main", "print('same runtime')\n")
    subprocess.run(
        ["git", "clone", str(installed), str(staging)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "-b", "easy-mode-copilot-chat-pilot"],
        cwd=staging,
        check=True,
        capture_output=True,
    )
    (staging / "state").mkdir()
    (staging / "state/metrics.json").write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=staging, check=True)
    subprocess.run(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test",
         "commit", "-m", "metrics only"],
        cwd=staging,
        check=True,
        capture_output=True,
    )

    result = run_harness(
        tmp_path,
        f"""
REPO_URL={str(staging)!r}
REPO_REF=easy-mode-copilot-chat-pilot
REMOTE_VERSION_URL=https://example.invalid/VERSION
curl() {{ printf '0.6.16\\n'; }}
if check_for_upgrade; then echo REFRESH; else echo CURRENT; fi
""",
    )

    assert result.returncode == 0, result.stderr
    assert "CURRENT" in result.stdout
    assert "REFRESH" not in result.stdout


def test_failed_fresh_clone_leaves_broken_install_untouched(tmp_path):
    brainstem = tmp_path / ".brainstem/src/rapp_brainstem"
    agents = brainstem / "agents"
    agents.mkdir(parents=True)
    (brainstem / "soul.md").write_text("custom soul", encoding="utf-8")
    (brainstem / ".env").write_text("SECRET=keep", encoding="utf-8")
    (brainstem / ".copilot_token").write_text("keep-token", encoding="utf-8")
    (agents / "custom_agent.py").write_text("custom = True", encoding="utf-8")
    result = run_harness(
        tmp_path,
        """
git() { return 1; }
install_brainstem
""",
    )
    assert result.returncode != 0
    assert (brainstem / "soul.md").read_text() == "custom soul"
    assert (brainstem / ".env").read_text() == "SECRET=keep"
    assert (brainstem / ".copilot_token").read_text() == "keep-token"
    assert (agents / "custom_agent.py").read_text() == "custom = True"


def test_unrelated_port_listener_is_not_killed(tmp_path):
    marker = tmp_path / "killed"
    result = run_harness(
        tmp_path,
        f"""
mkdir -p "$VENV_DIR/bin" "$BRAINSTEM_HOME/src/rapp_brainstem"
printf '#!/bin/sh\\nexit 0\\n' > "$VENV_DIR/bin/python"
chmod +x "$VENV_DIR/bin/python"
curl() {{ return 1; }}
lsof() {{ echo 4242; }}
ps() {{ echo "python -m http.server 7071"; }}
kill() {{ echo yes > {str(marker)!r}; }}
launch_brainstem
""",
    )
    assert result.returncode != 0
    assert not marker.exists()
    assert "Port 7071 is already used by another process" in result.stdout


def test_installer_preserves_sensitive_state_and_permissions_contract():
    text = INSTALLER.read_text(encoding="utf-8")
    assert "umask 077" in text
    assert 'chmod 600 "$token_file"' in text
    assert 'chmod 600 "$env_file"' in text
    for state_file in (
        ".copilot_token",
        ".copilot_session",
        ".copilot_pending",
        ".brainstem_model",
        ".brainstem_book.json",
        ".brainstem_secret",
        "voice.zip",
    ):
        assert text.count(state_file) >= 2


def test_runtime_only_mode_skips_user_cli_and_launch(tmp_path):
    trace = tmp_path / "trace"
    result = run_harness(
        tmp_path,
        f"""
check_prereqs() {{ echo prereqs >> {str(trace)!r}; }}
install_brainstem() {{ echo source >> {str(trace)!r}; }}
setup_venv() {{ echo venv >> {str(trace)!r}; }}
setup_deps() {{ echo deps >> {str(trace)!r}; }}
install_cli() {{ echo cli >> {str(trace)!r}; }}
create_env() {{ echo env >> {str(trace)!r}; }}
launch_brainstem() {{ echo launch >> {str(trace)!r}; }}
main --runtime-only
""",
    )
    assert result.returncode == 0, result.stderr
    assert trace.read_text().splitlines() == [
        "prereqs",
        "source",
        "venv",
        "deps",
        "env",
    ]


def test_generated_unix_launcher_honors_custom_home_and_bin(tmp_path):
    real_home = tmp_path / "real-home"
    brainstem_home = tmp_path / "custom-brainstem"
    brainstem_bin = tmp_path / "custom-bin"
    runtime = brainstem_home / "src/rapp_brainstem"
    python = brainstem_home / "venv/bin/python"
    marker = tmp_path / "launched"
    runtime.mkdir(parents=True)
    python.parent.mkdir(parents=True)
    real_home.mkdir()
    (runtime / "brainstem.py").write_text("\n", encoding="utf-8")
    python.write_text(
        "#!/bin/bash\n"
        "if [ \"$1\" = \"-c\" ]; then exit 0; fi\n"
        f"printf '%s\\n' \"$PWD|$BRAINSTEM_HOME|$*\" > {str(marker)!r}\n",
        encoding="utf-8",
    )
    python.chmod(0o700)

    result = run_harness(
        real_home,
        f"""
BRAINSTEM_HOME={str(brainstem_home)!r}
BRAINSTEM_BIN={str(brainstem_bin)!r}
VENV_DIR="$BRAINSTEM_HOME/venv"
install_cli
""",
    )
    assert result.returncode == 0, result.stderr
    launcher = brainstem_bin / "brainstem"
    assert launcher.exists()

    environment = os.environ.copy()
    environment["HOME"] = str(real_home)
    environment.pop("BRAINSTEM_HOME", None)
    launched = subprocess.run(
        [str(launcher), "hello"],
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert launched.returncode == 0, launched.stderr
    assert marker.read_text(encoding="utf-8").strip() == (
        f"{runtime}|{brainstem_home}|brainstem.py hello"
    )


def test_brainstem_home_environment_is_respected_at_initialization(tmp_path):
    custom_home = tmp_path / "not-the-default"
    script = f"""
set -e
export HOME={str(tmp_path)!r}
export BRAINSTEM_HOME={str(custom_home)!r}
{installer_functions()}
printf '%s\\n%s\\n' "$BRAINSTEM_HOME" "$VENV_DIR"
"""
    result = subprocess.run(
        ["bash"],
        input=script,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[-2:] == [
        str(custom_home),
        str(custom_home / "venv"),
    ]


def test_agent_name_collisions_are_kept_in_recovery():
    text = INSTALLER.read_text(encoding="utf-8")
    assert "preserve_agent_collision" in text
    assert "recovery/agent-collisions-" in text
    assert text.count('preserve_agent_collision "$') >= 2


def test_macos_git_bootstrap_never_continues_before_git_exists():
    text = INSTALLER.read_text(encoding="utf-8")
    assert "Complete the macOS Command Line Tools installation" in text
    assert "Git installation did not complete" in text
    assert 'git_version=$(git --version 2>/dev/null) || true' in text


def test_staging_can_override_repository_and_ref_without_changing_defaults():
    text = INSTALLER.read_text(encoding="utf-8")
    assert "BRAINSTEM_REPO_URL:-https://github.com/microsoft/aibast-agents-library.git" in text
    assert 'REPO_REF="${BRAINSTEM_REPO_REF:-main}"' in text
    assert '--branch "$REPO_REF"' in text
    assert 'origin "$REPO_REF"' in text


def test_static_landing_page_uses_minimal_public_readiness_probe():
    text = LANDING_PAGE.read_text(encoding="utf-8")
    check = text[text.index("async function checkBrainstem"):text.index(
        "checkBrainstem();"
    )]

    assert "http://localhost:7071/health/public" in check
    assert "http://localhost:7071/health'" not in check
    assert "d.agents" not in check
    assert "d.model" not in check


def test_windows_repair_and_port_paths_match_safety_contract():
    text = WINDOWS_INSTALLER.read_text(encoding="utf-8")
    assert "$SourceStage = \"$BRAINSTEM_HOME\\src-fresh-$PID\"" in text
    assert "Existing files were left untouched." in text
    for state_file in (
        ".copilot_token",
        ".copilot_session",
        ".copilot_pending",
        ".brainstem_model",
        ".brainstem_book.json",
        ".brainstem_secret",
        "voice.zip",
    ):
        assert text.count(state_file) >= 2
    assert "agent-collisions-" in text
    assert "Get-CimInstance Win32_Process" in text
    assert "Port 7071 is already used by another process" in text
    assert "$SOURCE_OVERRIDE_REQUESTED" in text
    assert "Refreshing the explicitly requested repository/ref" in text
    assert "Could not refresh the requested repository/ref" in text
    assert "if ($env:BRAINSTEM_HOME)" in text
    assert '$VENV_DIR = "$BRAINSTEM_HOME\\venv"' in text
    assert "--runtime-only" in text
    assert "Checked out immutable commit" in text
    assert "winget install --id $PackageId --scope user" in text


def test_documented_installer_mirrors_are_byte_identical():
    assert INSTALLER.read_bytes() == (ROOT / "docs/install.sh").read_bytes()
    assert WINDOWS_INSTALLER.read_bytes() == (
        ROOT / "docs/install.ps1"
    ).read_bytes()


def test_windows_launch_does_not_repeat_source_update():
    text = WINDOWS_INSTALLER.read_text(encoding="utf-8")
    launch = text[text.index("function Launch-Brainstem"):text.index("function Main")]

    assert "git pull" not in launch
    assert "git fetch" not in launch
