#!/usr/bin/env python3
"""Install a separate creature Brainstem using the installer behind aka.ms/rapp."""

import argparse
import hashlib
import importlib.util
import json
import os
import shlex
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


CORE_INSTALLER = "https://microsoft.github.io/aibast-agents-library/install.sh"
DEFAULT_SOURCE = "https://raw.githubusercontent.com/kody-w/aibast-agents-library/astra/brainstem-creature"
LISPY_COMMIT = "5e3a2e3275825ffecdbc4b12541aff48d7ff235e"
PAYLOAD = {
    "setup.py": "rapp_brainstem/experiments/creature/setup.py",
    "terrarium.py": "rapp_brainstem/experiments/creature/terrarium.py",
    "index.html": "rapp_brainstem/experiments/creature/index.html",
    "start.sh": "rapp_brainstem/experiments/creature/start.sh",
    "requirements.txt": "rapp_brainstem/experiments/creature/requirements.txt",
    "creature_twin_agent.py": "rapp_brainstem/agents/experimental/creature_twin_agent.py",
    "genome_creature_agent.py": "rapp_brainstem/agents/experimental/genome_creature_agent.py",
}
SOUL = """# RAPP Brainstem: creature twin

You are the caretaker of this isolated, local Brainstem terrarium.
Each creature is a separate standalone agent Python file. Its memory, genome,
lineage and eggs live in a separate data directory. Moving the file out of
AGENTS_PATH makes that creature dormant; it does not erase its history.

Use CreatureTwin for inventory, introduction, inspection, sleep and wake.
Use each creature's own tool for hatching, bounded evolution, fair held-out
races, tool-invention experiments, and egg export or resume.
When the user names an action and arguments, invoke that tool exactly once.
After introducing or waking a file, explain that the next request discovers it.
Never claim you invoked a newly introduced tool before it is in your tool list.
Report tool errors as errors. Never retry a state-changing action automatically.
Preserve expected_generation guards. Do not invent a score, mutation, tool,
memory, action trace, instruction cost or successful egg restoration.

The creature genome runs on the pinned LisPy runtime's safe core profile, with
additional bounded genome grammar and metered execution. Host Python agent
files are trusted capabilities, not genome code. Do not add host execution,
network, filesystem, Python-interoperability or unrestricted evaluation
capabilities to the genome interpreter. The original Brainstem core is unchanged.

This is a simulation. Evolution is a bounded computation, not evidence of
consciousness or biological life. Distinguish a recorded replay from current
computation. Keep training evidence separate from held-out evaluation, and do
not claim reusable tools beat a primitive-only baseline unless measurements do.
Keep answers short and point to the actual results.
"""


class InstallError(ValueError):
    pass


def download(url, maximum=2 * 1024 * 1024):
    if not url.startswith("https://"):
        raise InstallError("Installer payloads require HTTPS.")
    request = urllib.request.Request(url, headers={"User-Agent": "RAPP-Brainstem-Terrarium"})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read(maximum + 1)
    if len(raw) > maximum:
        raise InstallError(f"Download exceeded its size limit: {url}")
    return raw


def private_write(path, raw):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def checked_root(value):
    raw = Path(value).expanduser()
    if raw.is_symlink():
        raise InstallError("The installation root must not be a symlink.")
    root = raw.resolve()
    home = Path.home().resolve()
    forbidden = {Path("/"), home, home / ".brainstem", home / ".copilot"}
    if root in forbidden or root.is_relative_to(home / ".brainstem"):
        raise InstallError("Choose a separate directory, never the existing Brainstem, Copilot, or home directory.")
    return root


def import_manager(root):
    runtime = root / "bootstrap-home" / ".brainstem" / "src" / "rapp_brainstem"
    sys.path.insert(0, str(runtime))
    path = root / "payload" / "creature_twin_agent.py"
    spec = importlib.util.spec_from_file_location("creature_install_manager", path)
    if spec is None or spec.loader is None:
        raise InstallError("Cannot import the installed creature materializer.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def install(args):
    root = checked_root(args.root)
    marker = root / "terrarium.json"
    if marker.exists():
        config = json.loads(marker.read_text(encoding="utf-8"))
        if config.get("schema") != "rapp-creature/install/1":
            raise InstallError("Existing directory is not a recognized terrarium installation.")
        if args.egg:
            raise InstallError("Egg resume requires a fresh installation root; existing history was not changed.")
        print(f"Existing creature installation preserved: {root}", flush=True)
        return root, config
    if root.exists() and any(root.iterdir()):
        raise InstallError(f"Refusing to install over the nonempty directory {root}.")
    if os.name != "posix":
        raise InstallError("This experimental installer currently supports macOS and Linux.")
    for value in (args.port, args.ui_port):
        if not 1024 <= value <= 65535:
            raise InstallError("Ports must be between 1024 and 65535.")
    if args.port == args.ui_port or args.port == 7071 or args.ui_port == 7071:
        raise InstallError("Use two distinct ports, neither the original Brainstem's port 7071.")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    for name in ("payload", "agents", "dormant", "data", "logs", "bootstrap-home"):
        (root / name).mkdir(mode=0o700, exist_ok=True)

    print(f"Installing a separate RAPP Brainstem under {root}", flush=True)
    print("Your existing ~/.brainstem, shell configuration and Copilot plugins are not changed.", flush=True)
    source_root = Path(args.source_root).resolve() if args.source_root else None
    for name, relative in PAYLOAD.items():
        raw = (source_root / relative).read_bytes() if source_root else download(f"{args.source_url.rstrip('/')}/{relative}")
        private_write(root / "payload" / name, raw)
    private_write(root / "creature-soul.md", SOUL.encode("utf-8"))

    official_installer = root / "payload" / "official-install.sh"
    installer_raw = download(CORE_INSTALLER)
    if not installer_raw.startswith(b"#!/bin/bash"):
        raise InstallError("The aka.ms/rapp installer source did not return a Bash installer.")
    private_write(official_installer, installer_raw)
    environment = os.environ.copy()
    environment.update({
        "HOME": str(root / "bootstrap-home"),
        "BRAINSTEM_REPO_URL": "https://github.com/microsoft/aibast-agents-library.git",
        "BRAINSTEM_REPO_REF": "main",
        "BRAINSTEM_VERSION_URL": "https://raw.githubusercontent.com/microsoft/aibast-agents-library/main/rapp_brainstem/VERSION",
        "PYTHONUNBUFFERED": "1",
    })
    log_path = root / "logs" / "install.log"
    print(f"Running the official aka.ms/rapp installer with an isolated HOME; progress: {log_path}", flush=True)
    with log_path.open("wb") as log:
        os.chmod(log_path, 0o600)
        subprocess.run(
            ["/bin/bash", str(official_installer), "--no-launch"],
            env=environment,
            cwd=root / "bootstrap-home",
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    runtime = root / "bootstrap-home" / ".brainstem" / "src" / "rapp_brainstem"
    kernel = runtime / "brainstem.py"
    if not kernel.is_file():
        raise InstallError("The official installer finished without a Brainstem core.")
    python = root / "bootstrap-home" / ".brainstem" / "venv" / "bin" / "python"
    subprocess.run([str(python), "-c", "import flask, flask_cors, requests, dotenv"], check=True)
    print("Installing the pinned LisPy VM into this twin's private environment.", flush=True)
    with log_path.open("ab") as log:
        subprocess.run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(root / "payload" / "requirements.txt")],
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    runtime_probe = subprocess.run(
        [str(python), "-c",
         "import json; from importlib.metadata import distribution; "
         "from lisppy import VERSION, LANGUAGE_PROFILE; "
         "d=distribution('rappterbook-lispy-runtime'); "
         "origin=json.loads(d.read_text('direct_url.json') or '{}'); "
         "print(json.dumps({'version':VERSION,'profile':LANGUAGE_PROFILE,"
         "'commit':origin.get('vcs_info',{}).get('commit_id')}))"],
        capture_output=True,
        text=True,
        check=True,
    )
    lispy_identity = json.loads(runtime_probe.stdout)
    if lispy_identity.get("commit") != LISPY_COMMIT:
        raise InstallError("Installed LisPy does not match the pinned source commit.")

    manager = import_manager(root)
    source = (root / "payload" / "genome_creature_agent.py").read_text(encoding="utf-8")
    baseline, _ = manager.source_profile(source)
    if baseline is None:
        raise InstallError("The creature template has no literal profile.")
    profiles = []
    capabilities = baseline["capabilities"]
    if args.egg:
        egg_path = Path(args.egg).expanduser()
        if not egg_path.is_file() or egg_path.stat().st_size > 2_000_000:
            raise InstallError("Resume requires an egg JSON file of at most 2,000,000 bytes.")
        egg_raw = egg_path.read_bytes()
        envelope = json.loads(egg_raw)
        if not isinstance(envelope, dict) or envelope.get("schema") != "rapp-creature/egg/3":
            raise InstallError("Unsupported creature egg schema; it was not executed.")
        if not isinstance(envelope.get("profile"), dict) or not isinstance(envelope.get("state"), dict):
            raise InstallError("Egg does not contain a supported creature profile; it was not executed.")
        profile = manager.checked_profile(envelope["profile"])
        if not set(profile["capabilities"]).issubset(capabilities):
            raise InstallError("Egg requests capabilities outside the installed VM.")
        profiles.append(profile)
        egg_id = hashlib.sha256(egg_raw).hexdigest()
        private_write(root / "data" / profile["id"] / "inbox" / f"{egg_id}.egg.json", egg_raw)
        private_write(root / "pending.egg.json", egg_raw)
    else:
        variants = [
            ("astra", "Astra", capabilities),
            ("ember", "Ember", [sensor for sensor in capabilities if sensor != "hazard"]),
            ("moss", "Moss", [sensor for sensor in capabilities if sensor != "distance"]),
        ]
        for creature_id, name, selected in variants:
            profiles.append({**baseline, "id": creature_id, "name": name, "agent_name": f"{name}Creature", "capabilities": selected})
    for profile in profiles:
        manager.create_agent(root / "agents" / f"{profile['id']}_agent.py", manager.materialize(source, profile))
    for name, source_path in (
        ("basic_agent.py", runtime / "agents" / "basic_agent.py"),
        ("creature_twin_agent.py", root / "payload" / "creature_twin_agent.py"),
    ):
        private_write(root / "agents" / name, source_path.read_bytes())
    private_write(root / "start", (root / "payload" / "start.sh").read_bytes())
    os.chmod(root / "start", 0o700)

    revision = subprocess.run(["git", "-C", str(runtime), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    original_login = Path.home() / ".brainstem" / "src" / "rapp_brainstem" / ".copilot_token"
    config = {
        "schema": "rapp-creature/install/1",
        "brainstem_port": args.port,
        "ui_port": args.ui_port,
        "core_installer": CORE_INSTALLER,
        "core_installer_sha256": hashlib.sha256(installer_raw).hexdigest(),
        "core_commit": revision,
        "kernel_sha256": hashlib.sha256(kernel.read_bytes()).hexdigest(),
        "lispy": lispy_identity,
        "source_url": args.source_url,
        "gh_config_dir": os.environ.get("GH_CONFIG_DIR", str(Path.home() / ".config" / "gh")),
        "auth_reference": str(original_login) if not args.independent_auth and original_login.is_file() else None,
        "resume_egg": bool(args.egg),
        "resume_id": profiles[0]["id"] if args.egg else None,
        "resume_agent_name": profiles[0]["agent_name"] if args.egg else None,
        "resume_egg_id": egg_id if args.egg else None,
        "resume_generation": envelope["state"].get("generation") if args.egg else None,
        "resume_genome_sha256": envelope["state"].get("genome_sha256") if args.egg else None,
        "payload_hashes": {name: hashlib.sha256((root / "payload" / name).read_bytes()).hexdigest() for name in PAYLOAD},
    }
    private_write(marker, (json.dumps(config, indent=2) + "\n").encode("utf-8"))
    print(f"Installed one Brainstem with {len(profiles)} standalone creature agent files.", flush=True)
    return root, config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path.home() / ".brainstem-creature"))
    parser.add_argument("--port", type=int, default=7081)
    parser.add_argument("--ui-port", type=int, default=7082)
    parser.add_argument("--source-root", help="Local repository source for development installs.")
    parser.add_argument("--source-url", default=DEFAULT_SOURCE, help="Raw GitHub repository prefix containing this experimental payload.")
    parser.add_argument("--egg", help="Resume this egg in a fresh root, through Brainstem /chat.")
    parser.add_argument("--no-start", action="store_true", help="Install only; print the exact foreground start command.")
    parser.add_argument("--independent-auth", action="store_true", help="Use a separate login instead of a read-only reference to an existing Brainstem login.")
    args = parser.parse_args()
    try:
        if sys.version_info < (3, 11):
            raise InstallError("Python 3.11+ is required. The original aka.ms/rapp installer can install Python first.")
        root, config = install(args)
        command = [str(root / "start")]
        if args.independent_auth:
            command.append("--independent-auth")
        print("Start this twin: " + shlex.join(command), flush=True)
        print(f"Terrarium: http://127.0.0.1:{config['ui_port']}", flush=True)
        if not args.no_start:
            return subprocess.call(command)
        return 0
    except (InstallError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Creature installation failed: {exc}", file=sys.stderr)
        print("No existing Brainstem was replaced. Any partial isolated install and its logs were preserved.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
