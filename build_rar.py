#!/usr/bin/env python3
"""Build the AIBAST-owned artifacts consumed by the Brainstem.

The curated RAR catalog derives only from this repository's registry.json and
adds a SHA-256 digest and collision-safe install filename for each agent. It
never consumes or falls back to the public/global RAR. The same build emits the
workshop stack-name index and the mutable frontier-kernel update channel.

Run after build_registry.py; commit the result, then update RAR_REVISION in
rapp_brainstem to publish a new immutable catalog snapshot.
"""

import hashlib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AGENTS_DIR = ROOT / "agents"
RAR_FILE = ROOT / "rar" / "registry.json"
STACK_NAMES_FILE = ROOT / "twin" / "stack_names.json"
FRONTIER_CHANNEL_FILE = ROOT / "rapp_brainstem" / "frontier-channel.json"
AIBAST_RAR_REPOSITORY = "microsoft/aibast-agents-library"
AIBAST_RAR_INSTANCE = "AIBAST RAR"
AIBAST_RAR_CATALOG_PATH = "rar/registry.json"
FRONTIER_CHANNEL_URL = (
    "https://raw.githubusercontent.com/microsoft/aibast-agents-library/"
    "main/rapp_brainstem/frontier-channel.json"
)
MANIFEST_NAME_RE = re.compile(
    r"^@[a-z0-9][a-z0-9-]*/[a-z0-9]+(?:-[a-z0-9]+)*$"
)
VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)*$")


def resolve_catalog_agent_path(relative_path: str) -> Path:
    """Resolve one canonical catalog path without allowing registry traversal."""
    if not isinstance(relative_path, str) or not relative_path:
        raise ValueError("Agent _file must be a non-empty string")

    supplied = relative_path.replace("\\", "/")
    path = Path(relative_path)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Agent _file must be a canonical repository-relative path")

    candidate = ROOT / path
    if candidate.is_symlink():
        raise ValueError("Agent _file must not reference a symbolic link")

    try:
        resolved = candidate.resolve(strict=True)
        canonical = resolved.relative_to(ROOT.resolve(strict=True)).as_posix()
        resolved.relative_to(AGENTS_DIR.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise ValueError(
            "Agent _file must resolve inside the repository agents directory"
        ) from error

    if supplied != canonical:
        raise ValueError("Agent _file must use its canonical repository-relative path")
    if not resolved.is_file() or resolved.suffix != ".py":
        raise ValueError("Agent _file must reference a Python file")
    return resolved


def legacy_install_filename(agent_path: Path) -> str:
    """Keep existing install names where they do not collide."""
    if agent_path.name.endswith("_agent.py"):
        return agent_path.name
    return f"{agent_path.stem}_agent.py"


def manifest_install_filename(name: str) -> str:
    """Build a safe filename from a validated publisher-qualified agent name."""
    if not isinstance(name, str) or not MANIFEST_NAME_RE.fullmatch(name):
        raise ValueError(
            f"Invalid manifest name '{name}' for RAR install filename generation"
        )
    publisher, slug = name[1:].split("/", maxsplit=1)
    return (
        f"{publisher.replace('-', '_')}__{slug.replace('-', '_')}_agent.py"
    )


def build_install_filenames(agents: list[dict]) -> tuple[list[Path], list[str]]:
    """Return resolved files and unique, browser-compatible install filenames."""
    source_paths = []
    names = []
    for agent in agents:
        if not isinstance(agent, dict):
            raise ValueError("Each registry agent entry must be an object")
        name = agent.get("name")
        if not isinstance(name, str) or not MANIFEST_NAME_RE.fullmatch(name):
            raise ValueError(f"Invalid registry agent name '{name}'")
        source_paths.append(resolve_catalog_agent_path(agent.get("_file")))
        names.append(name)

    duplicate_names = sorted(
        name for name, count in Counter(names).items() if count > 1
    )
    if duplicate_names:
        raise ValueError(
            "Duplicate registry agent names: " + ", ".join(duplicate_names)
        )

    legacy_names = [legacy_install_filename(path) for path in source_paths]
    legacy_counts = Counter(legacy_names)
    reserved_unique_names = {
        name for name, count in legacy_counts.items() if count == 1
    }
    filenames = []
    used_names = set()

    for name, legacy_name in zip(names, legacy_names):
        filename = legacy_name
        if legacy_counts[legacy_name] > 1:
            filename = manifest_install_filename(name)
            if filename in reserved_unique_names or filename in used_names:
                digest = hashlib.sha256(name.encode("utf-8")).hexdigest()[:12]
                stem = filename.removesuffix("_agent.py")
                filename = f"{stem}__{digest}_agent.py"

        if filename in used_names:
            raise ValueError(f"Unable to derive a unique install filename for '{name}'")
        filenames.append(filename)
        used_names.add(filename)

    return source_paths, filenames


def build_rar_registry(registry: dict) -> dict:
    """Create a deterministic RAR document from a validated registry document."""
    if not isinstance(registry, dict):
        raise ValueError("registry.json must contain an object")
    if registry.get("schema") != "rapp-registry/1.0":
        raise ValueError("registry.json has an unsupported schema")
    generated_at = registry.get("generated_at")
    if not isinstance(generated_at, str) or not generated_at:
        raise ValueError("registry.json must include generated_at")
    stats = registry.get("stats")
    if not isinstance(stats, dict):
        raise ValueError("registry.json must include stats")
    catalog_agents = registry.get("agents")
    if not isinstance(catalog_agents, list):
        raise ValueError("registry.json must include an agents list")

    source_paths, filenames = build_install_filenames(catalog_agents)
    agents = []
    for agent, source_path, filename in zip(
        catalog_agents, source_paths, filenames
    ):
        entry = dict(agent)
        entry["_sha256"] = hashlib.sha256(source_path.read_bytes()).hexdigest()
        entry["_install_filename"] = filename
        agents.append(entry)

    return {
        "schema": registry["schema"],
        "version": registry.get("version", "1.0.0"),
        "generated_at": generated_at,
        "instance": AIBAST_RAR_INSTANCE,
        "repository": AIBAST_RAR_REPOSITORY,
        "catalog_path": AIBAST_RAR_CATALOG_PATH,
        "scope": "business-curated",
        "stats": dict(stats),
        "duplicates": [],
        "swarms": [],
        "stacks": [],
        "agents": agents,
    }


def iter_copilot_studio_manifests() -> list[Path]:
    """Discover stack manifests without following untrusted symbolic links."""
    manifests = []
    for directory, child_dirs, filenames in os.walk(AGENTS_DIR, followlinks=False):
        directory_path = Path(directory)
        child_dirs[:] = sorted(
            child for child in child_dirs
            if not (directory_path / child).is_symlink()
        )
        if "manifest.json" not in filenames:
            continue

        manifest_path = directory_path / "manifest.json"
        relative_path = manifest_path.relative_to(AGENTS_DIR)
        if (
            len(relative_path.parts) == 5
            and relative_path.parts[0] == "@aibast-agents-library"
            and relative_path.parts[1].endswith("_stacks")
            and relative_path.parts[3] == "copilot_studio"
        ):
            if manifest_path.is_symlink():
                raise ValueError(
                    f"{manifest_path}: Copilot Studio manifest must not be a symbolic link"
                )
            manifests.append(manifest_path)
    return manifests


def build_stack_name_index() -> dict:
    """Build the workshop name index before writing either generated artifact."""
    names = {}
    for manifest_path in iter_copilot_studio_manifests():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        stack = data.get("stack")
        display_name = data.get("display_name")
        if not isinstance(stack, str) or not stack:
            raise ValueError(f"{manifest_path}: stack must be a non-empty string")
        if not isinstance(display_name, str) or not display_name:
            raise ValueError(
                f"{manifest_path}: display_name must be a non-empty string"
            )
        if stack in names:
            raise ValueError(f"Duplicate Copilot Studio stack name '{stack}'")

        sharepoint = data.get("sharepoint") or {}
        if not isinstance(sharepoint, dict):
            raise ValueError(f"{manifest_path}: sharepoint must be an object")
        advertised = sharepoint.get("also_advertised_as") or {}
        if not isinstance(advertised, dict):
            raise ValueError(
                f"{manifest_path}: also_advertised_as must be an object"
            )
        candidate_names = [
            display_name,
            sharepoint.get("approved_name"),
            advertised.get("name"),
        ]
        names[stack] = {
            "dir": manifest_path.parent.parent.name,
            "names": sorted(
                {
                    candidate
                    for candidate in candidate_names
                    if isinstance(candidate, str) and candidate
                }
            ),
        }

    return {
        "schema": "aibast-twin-stack-names/1.0",
        "note": (
            "Every name the workshop can show for a stack. The twin resolves any "
            "of them."
        ),
        "stacks": names,
    }


def build_frontier_channel() -> dict:
    """Describe the canonical kernel broadcast that downstream forks may follow."""
    version = (ROOT / "rapp_brainstem" / "VERSION").read_text(
        encoding="utf-8"
    ).strip()
    if not VERSION_RE.fullmatch(version):
        raise ValueError("rapp_brainstem/VERSION must contain a numeric version")

    return {
        "schema": "aibast-brainstem-channel/1.0",
        "channel": "frontier",
        "kernel": "rapp_brainstem",
        "repository": AIBAST_RAR_REPOSITORY,
        "version": version,
        "channel_url": FRONTIER_CHANNEL_URL,
        "update_url": "https://microsoft.github.io/aibast-agents-library/",
        "install": {
            "bash": (
                "curl -fsSL "
                "https://microsoft.github.io/aibast-agents-library/install.sh | bash"
            ),
            "powershell": (
                "irm https://raw.githubusercontent.com/microsoft/"
                "aibast-agents-library/main/install.ps1 | iex"
            ),
        },
        "subscription": {
            "default": "follow",
            "pin": "Use an immutable tag or commit URL for this manifest.",
            "off": "Set BRAINSTEM_UPDATE_CHANNEL_URL=off.",
            "boundary": (
                "The channel advertises the canonical Brainstem kernel. Forks that "
                "modify the kernel should pin or disable it; distro-owned catalogs "
                "and workshops should stay outside the kernel overlay."
            ),
        },
    }


def main() -> int:
    try:
        registry = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))
        rar_registry = build_rar_registry(registry)
        stack_names = build_stack_name_index()
        frontier_channel = build_frontier_channel()
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        print(f"[ERROR] AIBAST RAR build failed: {error}", file=sys.stderr)
        return 1

    RAR_FILE.parent.mkdir(exist_ok=True)
    RAR_FILE.write_text(json.dumps(rar_registry, indent=1), encoding="utf-8")
    STACK_NAMES_FILE.write_text(json.dumps(stack_names, indent=1), encoding="utf-8")
    FRONTIER_CHANNEL_FILE.write_text(
        json.dumps(frontier_channel, indent=1) + "\n", encoding="utf-8"
    )

    print(
        f"[OK] AIBAST RAR built: {len(rar_registry['agents'])} agents, "
        "digests verified installable"
    )
    print(f"[OK] stack-name index: {len(stack_names['stacks'])} stacks")
    print(
        f"[OK] frontier channel: v{frontier_channel['version']} "
        f"({frontier_channel['repository']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
