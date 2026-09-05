"""Manage standalone creatures on one RAPP Brainstem without changing its core.

CreatureTwin copies a trusted, installed single-file creature template, changing
only its literal CREATURE_PROFILE. Sleeping moves that Python file out of the
discovery directory; memory, genomes, eggs and history are never deleted.

Configuration: RAPP_CREATURE_HOME, RAPP_CREATURE_DATA_DIR,
RAPP_CREATURE_TEMPLATE and AGENTS_PATH. The standalone terrarium installer sets
these to an isolated installation. Python agent files are trusted host code;
their evolving LisPy programs have a separate, restricted execution boundary.
"""

import ast
import contextlib
import json
import os
import re
import tempfile
from pathlib import Path

from agents.basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@kody-w/creature-twin",
    "version": "0.1.0",
    "display_name": "Brainstem Creature Twin",
    "description": "Introduce, inspect, sleep and wake standalone creature agents.",
    "author": "kody-w",
    "tags": ["brainstem", "creature", "terrarium", "experimental"],
    "category": "devtools",
    "quality_tier": "community",
    "requires_env": ["RAPP_CREATURE_HOME", "RAPP_CREATURE_TEMPLATE"],
    "dependencies": ["@rapp/basic-agent"],
}

MAX_CREATURES = 12
MAX_AGENT_BYTES = 1024 * 1024
MAX_SNAPSHOT_BYTES = 8 * 1024 * 1024
IDENTIFIER = re.compile(r"[a-z][a-z0-9-]{0,31}\Z")
TOOL_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
DISPLAY_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9 _.-]{0,63}\Z")


class CreatureTwinError(ValueError):
    """A requested lifecycle operation cannot be performed safely."""


def checked_id(value):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise CreatureTwinError("Creature id must be 1-32 lowercase letters, digits or '-', starting with a letter.")
    if value in {"basic", "creature_twin", "genome_creature"}:
        raise CreatureTwinError("That creature id is reserved.")
    return value


def checked_profile(profile):
    if not isinstance(profile, dict) or set(profile) != {"id", "name", "agent_name", "capabilities"}:
        raise CreatureTwinError("CREATURE_PROFILE must contain exactly id, name, agent_name and capabilities.")
    checked_id(profile.get("id"))
    name = profile.get("name")
    if not isinstance(name, str) or not DISPLAY_NAME.fullmatch(name):
        raise CreatureTwinError("Creature name must use 1-64 letters, numbers, spaces, '.', '_' or '-', starting with a letter or number.")
    agent_name = profile.get("agent_name")
    if not isinstance(agent_name, str) or not TOOL_NAME.fullmatch(agent_name):
        raise CreatureTwinError("Creature profile has an invalid agent_name.")
    capabilities = profile.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities or len(capabilities) > 32:
        raise CreatureTwinError("Creature capabilities must be a nonempty, bounded list.")
    if any(not isinstance(item, str) or not item or len(item) > 64 for item in capabilities):
        raise CreatureTwinError("Creature capabilities must be short strings.")
    if len(set(capabilities)) != len(capabilities):
        raise CreatureTwinError("Creature capabilities must not contain duplicates.")
    return profile


def source_profile(source):
    if len(source.encode("utf-8")) > MAX_AGENT_BYTES:
        raise CreatureTwinError("Agent file exceeds the creature size limit.")
    try:
        tree = ast.parse(source)
    except (SyntaxError, RecursionError, ValueError) as exc:
        raise CreatureTwinError(f"Cannot parse creature file: {exc}") from exc
    assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "CREATURE_PROFILE" for target in node.targets)
    ]
    if not assignments:
        return None, None
    if len(assignments) != 1 or len(assignments[0].targets) != 1:
        raise CreatureTwinError("Creature file must have exactly one CREATURE_PROFILE assignment.")
    try:
        profile = ast.literal_eval(assignments[0].value)
    except (ValueError, TypeError, SyntaxError, RecursionError) as exc:
        raise CreatureTwinError("CREATURE_PROFILE must contain only literal data.") from exc
    return checked_profile(profile), assignments[0]


def read_source(path):
    if path.is_symlink() or not path.is_file():
        raise CreatureTwinError(f"Expected a regular agent file: {path.name}")
    if path.stat().st_size > MAX_AGENT_BYTES:
        raise CreatureTwinError(f"Agent file is too large: {path.name}")
    return path.read_text(encoding="utf-8")


def materialize(source, profile):
    """Replace one data literal, never interpolate user data as Python code."""
    checked_profile(profile)
    _, assignment = source_profile(source)
    if assignment is None:
        raise CreatureTwinError("The installed template has no CREATURE_PROFILE.")
    lines = source.splitlines(keepends=True)
    replacement = f"CREATURE_PROFILE = {profile!r}\n"
    result = "".join(lines[:assignment.lineno - 1]) + replacement + "".join(lines[assignment.end_lineno:])
    parsed, _ = source_profile(result)
    if parsed != profile:
        raise CreatureTwinError("The materialized creature profile did not round-trip.")
    return result


def read_snapshot(data_root, creature_id):
    path = Path(data_root) / checked_id(creature_id) / "public" / "snapshot.json"
    if not path.exists():
        return None
    if path.is_symlink() or path.stat().st_size > MAX_SNAPSHOT_BYTES:
        raise CreatureTwinError(f"Invalid public snapshot for {creature_id}.")
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError, RecursionError) as exc:
        raise CreatureTwinError(f"Cannot read {creature_id}'s snapshot: {exc}") from exc
    if not isinstance(result, dict) or result.get("schema") != "rapp-creature/snapshot/1":
        raise CreatureTwinError(f"Unknown snapshot schema for {creature_id}.")
    return result


def inventory(agents_dir, dormant_dir, data_root, loaded_names=None):
    """Read actual files and public evidence without importing any creature."""
    creatures = {}
    issues = []
    other_agents = []
    locations = ((Path(dormant_dir), False), (Path(agents_dir), True))
    for directory, active in locations:
        if not directory.exists():
            continue
        if directory.is_symlink():
            raise CreatureTwinError(f"Creature directory may not be a symlink: {directory}")
        for path in sorted(directory.glob("*_agent.py")):
            if path.name in {"basic_agent.py", "creature_twin_agent.py"}:
                continue
            try:
                profile, _ = source_profile(read_source(path))
                if profile is None:
                    other_agents.append(path.name)
                    continue
                creature_id = profile["id"]
                if path.name != f"{creature_id}_agent.py":
                    raise CreatureTwinError(f"{path.name} must be named {creature_id}_agent.py.")
                if creature_id in creatures:
                    raise CreatureTwinError(f"Duplicate active/dormant identity: {creature_id}.")
                snapshot = read_snapshot(data_root, creature_id)
                status = "active" if active else "dormant"
                if active and loaded_names is not None and profile["agent_name"] not in loaded_names:
                    status = "unavailable"
                elif active and not (snapshot and snapshot.get("exists")):
                    status = "unhatched"
                creatures[creature_id] = {
                    **profile,
                    "status": status,
                    "filename": path.name,
                    "generation": snapshot.get("generation") if snapshot else None,
                    "genome_sha256": snapshot.get("genome_sha256") if snapshot else None,
                    "snapshot": snapshot,
                    "problem": "The file is present but Brainstem did not load its tool." if status == "unavailable" else None,
                }
            except (CreatureTwinError, OSError, UnicodeError) as exc:
                issues.append(f"{path.name}: {exc}")

    # A user can move a file somewhere other than our archive. Its saved evidence
    # still belongs in the terrarium, with the missing executable stated plainly.
    root = Path(data_root)
    if root.exists():
        for directory in sorted(root.iterdir()):
            if not directory.is_dir() or directory.is_symlink() or not IDENTIFIER.fullmatch(directory.name):
                continue
            if directory.name in creatures:
                continue
            try:
                snapshot = read_snapshot(root, directory.name)
                if snapshot and snapshot.get("exists"):
                    creatures[directory.name] = {
                        "id": directory.name,
                        "name": snapshot.get("name", directory.name),
                        "agent_name": None,
                        "capabilities": snapshot.get("capabilities", []),
                        "status": "dormant",
                        "filename": f"{directory.name}_agent.py",
                        "generation": snapshot.get("generation"),
                        "genome_sha256": snapshot.get("genome_sha256"),
                        "snapshot": snapshot,
                        "problem": "Agent file is outside the active and dormant folders; restore the original file to wake it.",
                    }
            except (CreatureTwinError, OSError, UnicodeError) as exc:
                issues.append(f"{directory.name}: {exc}")
    return {
        "creatures": sorted(creatures.values(), key=lambda item: item["id"]),
        "issues": issues,
        "other_agents": sorted(set(other_agents)),
    }


@contextlib.contextmanager
def lifecycle_lock(home):
    if os.name != "posix":
        raise CreatureTwinError("This experimental lifecycle manager currently requires macOS or Linux.")
    import fcntl

    home.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock_path = home / ".creature-lifecycle.lock"
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "a") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def create_agent(path, source):
    if path.exists() or path.is_symlink():
        raise CreatureTwinError(f"Refusing to replace existing agent file: {path.name}")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=".creature-", delete=False) as stream:
            temporary = Path(stream.name)
            os.chmod(temporary, 0o600)
            stream.write(source)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    except FileExistsError as exc:
        raise CreatureTwinError(f"Another process introduced {path.name}; no file was replaced.") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class CreatureTwinAgent(BasicAgent):
    def __init__(self):
        self.name = "CreatureTwin"
        self.metadata = {
            "name": self.name,
            "description": (
                "Caretaker of the Brainstem terrarium. Inventory actual standalone creatures, "
                "introduce a trusted creature file, inspect its evidence, or sleep/wake it by "
                "moving its file. Never deletes memory or alters the Brainstem core. "
                "After introduce/wake, use a NEW chat request before calling that creature."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["inventory", "introduce", "inspect", "sleep", "wake"]},
                    "id": {"type": "string", "description": "Stable lowercase creature identity."},
                    "name": {"type": "string", "description": "Display name for a new creature."},
                    "capabilities": {"type": "array", "items": {"type": "string"}, "description": "Subset of the installed template's sensory capabilities."},
                },
                "required": ["action"],
                "additionalProperties": False,
            },
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        try:
            return json.dumps(self._perform(kwargs), allow_nan=False)
        except (CreatureTwinError, OSError, UnicodeError) as exc:
            return json.dumps({"status": "error", "error": str(exc)})

    def _perform(self, arguments):
        home = Path(os.environ.get("RAPP_CREATURE_HOME", str(Path.home() / ".brainstem-creature"))).expanduser()
        if home.is_symlink():
            raise CreatureTwinError("Creature home may not be a symlink.")
        agents = Path(os.environ.get("AGENTS_PATH", str(home / "agents")))
        dormant = home / "dormant"
        data = Path(os.environ.get("RAPP_CREATURE_DATA_DIR", str(home / "data")))
        template = Path(os.environ.get("RAPP_CREATURE_TEMPLATE", str(home / "payload" / "genome_creature_agent.py")))
        action = arguments.get("action")
        if action not in {"inventory", "introduce", "inspect", "sleep", "wake"}:
            raise CreatureTwinError("Unknown lifecycle action.")
        for directory in (agents, dormant, data):
            if directory.is_symlink():
                raise CreatureTwinError("Creature directories may not be symlinks.")
        with lifecycle_lock(home):
            catalog = inventory(agents, dormant, data)
            if action == "inventory":
                summaries = []
                for creature in catalog["creatures"]:
                    summary = {key: value for key, value in creature.items() if key != "snapshot"}
                    evidence = creature.get("snapshot")
                    if evidence:
                        summary["training"] = evidence.get("training")
                        summary["energy"] = evidence.get("energy")
                    summaries.append(summary)
                return {"status": "ok", **catalog, "creatures": summaries}
            creature_id = checked_id(arguments.get("id"))
            if action == "inspect":
                matches = [item for item in catalog["creatures"] if item["id"] == creature_id]
                if not matches:
                    raise CreatureTwinError(f"No creature named {creature_id}.")
                entry = dict(matches[0])
                snapshot = entry.pop("snapshot")
                if snapshot:
                    entry["evidence"] = {
                        key: snapshot.get(key)
                        for key in ("program", "training", "energy", "memory", "vm", "tools", "comparison", "egg")
                    }
                    if snapshot.get("lineage"):
                        entry["evidence"]["latest_change"] = snapshot["lineage"][-1]
                return {"status": "ok", "creature": entry}
            if action == "introduce":
                if len(catalog["creatures"]) >= MAX_CREATURES:
                    raise CreatureTwinError(f"This terrarium is limited to {MAX_CREATURES} creatures.")
                if any(item["id"] == creature_id for item in catalog["creatures"]):
                    raise CreatureTwinError("That identity already exists, possibly dormant; wake or restore its original file.")
                source = read_source(template)
                baseline, _ = source_profile(source)
                if baseline is None:
                    raise CreatureTwinError("Installed template has no creature profile.")
                capabilities = arguments.get("capabilities", baseline["capabilities"])
                if not isinstance(capabilities, list) or any(not isinstance(item, str) for item in capabilities):
                    raise CreatureTwinError("Requested capabilities must be a list of sensor names.")
                if not set(capabilities).issubset(baseline["capabilities"]):
                    raise CreatureTwinError("Requested capabilities are not available in the installed template.")
                profile = {
                    **baseline,
                    "id": creature_id,
                    "name": arguments.get("name", creature_id.title()),
                    "agent_name": "".join(part.capitalize() for part in re.split(r"[-_]", creature_id)) + "Creature",
                    "capabilities": capabilities,
                }
                checked_profile(profile)
                if any(item.get("agent_name") == profile["agent_name"] for item in catalog["creatures"]):
                    raise CreatureTwinError("A creature already uses that tool name.")
                create_agent(agents / f"{creature_id}_agent.py", materialize(source, profile))
                return {
                    "status": "ok",
                    "action": action,
                    "creature": profile,
                    "message": "Agent file introduced. Refresh Brainstem discovery, then hatch in a new chat request.",
                }
            source_dir, destination_dir = (agents, dormant) if action == "sleep" else (dormant, agents)
            source_path = source_dir / f"{creature_id}_agent.py"
            destination = destination_dir / source_path.name
            profile, _ = source_profile(read_source(source_path))
            if profile is None or profile["id"] != creature_id:
                raise CreatureTwinError("File does not contain the requested creature identity.")
            if destination.exists() or destination.is_symlink():
                raise CreatureTwinError("Destination already contains an agent; nothing was replaced.")
            destination_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            os.link(source_path, destination)
            source_path.unlink()
            return {
                "status": "ok",
                "action": action,
                "id": creature_id,
                "message": "Agent file moved; genome, memory, eggs and lineage are unchanged.",
            }
