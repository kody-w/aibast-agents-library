#!/usr/bin/env python3
"""
Registry Builder — Auto-generates registry.json from __manifest__ dicts in agent .py files.

Run manually:   python build_registry.py
Or via CI:      Triggered on every push by .github/workflows/build-registry.yml

Scans agents/@publisher/slug.py for __manifest__ dicts and builds:
- registry.json (full index for programmatic access)
- Validates all manifests against schema
- Reports errors for malformed agents
"""

import ast
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AGENTS_DIR = ROOT / "agents"
REGISTRY_FILE = ROOT / "registry.json"
REQUIRED_MANIFEST_FIELDS = [
    "schema", "name", "version", "display_name",
    "description", "author", "tags", "category",
]
MANIFEST_NAME_RE = re.compile(
    r"^@[a-z0-9][a-z0-9-]*/[a-z0-9]+(?:-[a-z0-9]+)*$"
)
SEMVER_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
QUALITY_TIERS = {"community", "verified", "official"}


def _is_manifest_assignment(node: ast.stmt) -> bool:
    """Return whether a module-level statement assigns __manifest__."""
    if isinstance(node, ast.Assign):
        return any(
            isinstance(target, ast.Name) and target.id == "__manifest__"
            for target in node.targets
        )
    return (
        isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "__manifest__"
    )


def extract_manifest_from_source(source: str) -> tuple[dict | None, list[str]]:
    """Extract one literal, module-level manifest without importing agent code."""
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return None, [f"Syntax error: {error}"]

    assignments = [node for node in tree.body if _is_manifest_assignment(node)]
    if not assignments:
        return None, []
    if len(assignments) != 1:
        return None, ["Multiple top-level __manifest__ declarations"]

    try:
        manifest = ast.literal_eval(assignments[0].value)
    except (ValueError, TypeError) as error:
        return None, [f"Cannot parse __manifest__: {error}"]
    if not isinstance(manifest, dict):
        return None, ["__manifest__ must be a dict"]
    return manifest, []


def _extract_manifest_with_source(py_path: Path) -> tuple[dict | None, list[str], str | None]:
    """Read and statically parse an agent file once for catalog generation."""
    try:
        source = py_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return None, [f"Cannot read file: {error}"], None

    manifest, errors = extract_manifest_from_source(source)
    return manifest, errors, source


def extract_manifest(py_path: Path) -> dict | None:
    """Extract __manifest__ from a Python file using static AST parsing."""
    manifest, errors, _ = _extract_manifest_with_source(py_path)
    for error in errors:
        print(f"  [WARN] {error} in {py_path}")
    return manifest


def validate_manifest(py_path: Path, manifest: dict) -> list:
    """Validate a manifest and return a list of schema errors."""
    if not isinstance(manifest, dict):
        return ["__manifest__ must be a dict"]

    errors = []
    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in manifest:
            errors.append(f"Missing required field: {field}")

    if manifest.get("schema") != "rapp-agent/1.0":
        errors.append("schema must be 'rapp-agent/1.0'")

    name = manifest.get("name")
    if not isinstance(name, str) or not MANIFEST_NAME_RE.fullmatch(name):
        errors.append(
            f"Invalid name format '{name}' — must be @publisher/kebab-case-slug"
        )

    version = manifest.get("version")
    if not isinstance(version, str) or not SEMVER_RE.fullmatch(version):
        errors.append(
            f"Invalid version '{version}' — must be semver (e.g., 1.0.0)"
        )

    for field in ("display_name", "description", "author", "category"):
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be a non-empty string")

    tags = manifest.get("tags")
    if (
        not isinstance(tags, list)
        or not all(isinstance(tag, str) and tag.strip() for tag in tags)
    ):
        errors.append("tags must be a list of non-empty strings")

    quality_tier = manifest.get("quality_tier")
    if quality_tier is not None and quality_tier not in QUALITY_TIERS:
        errors.append(
            f"Invalid quality_tier '{quality_tier}' — must be one of "
            f"{', '.join(sorted(QUALITY_TIERS))}"
        )

    for field in ("requires_env", "dependencies"):
        value = manifest.get(field)
        if value is not None and (
            not isinstance(value, list)
            or not all(isinstance(item, str) and item.strip() for item in value)
        ):
            errors.append(f"{field} must be a list of non-empty strings")

    return errors


def catalog_relative_path(py_path: Path) -> str:
    """Return a canonical repository-relative path for a real catalog file."""
    if py_path.is_symlink():
        raise ValueError("Agent files must not be symbolic links")

    try:
        resolved = py_path.resolve(strict=True)
        resolved.relative_to(AGENTS_DIR.resolve(strict=True))
        return resolved.relative_to(ROOT).as_posix()
    except (OSError, ValueError) as error:
        raise ValueError(
            "Agent file must resolve inside the repository agents directory"
        ) from error


def iter_agent_files() -> list[Path]:
    """List agent candidates in a stable order without traversing symlinked dirs."""
    files = []
    for directory, child_dirs, filenames in os.walk(AGENTS_DIR, followlinks=False):
        directory_path = Path(directory)
        child_dirs[:] = sorted(
            child for child in child_dirs
            if not (directory_path / child).is_symlink()
        )
        files.extend(
            directory_path / filename
            for filename in sorted(filenames)
            if filename.endswith(".py")
        )
    return files


def generated_at_for_registry(registry: dict) -> str:
    """Keep a prior timestamp when a rebuild produces identical catalog data."""
    try:
        existing = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        existing = None

    if isinstance(existing, dict):
        timestamp = existing.get("generated_at")
        existing_payload = dict(existing)
        candidate_payload = dict(registry)
        existing_payload.pop("generated_at", None)
        candidate_payload.pop("generated_at", None)
        if isinstance(timestamp, str) and timestamp and existing_payload == candidate_payload:
            return timestamp

    return datetime.now(timezone.utc).isoformat()


def collect_registry() -> tuple[dict, list[str]]:
    """Build registry data in memory so invalid inputs never overwrite a catalog."""
    agents = []
    publishers = set()
    categories = set()
    errors = []
    seen_names = {}

    for py_path in iter_agent_files():
        try:
            relative_path = catalog_relative_path(py_path)
        except ValueError as error:
            errors.append(f"{py_path}: {error}")
            continue

        manifest, extraction_errors, source = _extract_manifest_with_source(py_path)
        if extraction_errors:
            errors.extend(f"{py_path}: {error}" for error in extraction_errors)
            continue
        if manifest is None:
            continue

        validation_errors = validate_manifest(py_path, manifest)
        if validation_errors:
            errors.extend(f"{py_path}: {error}" for error in validation_errors)
            continue

        name = manifest["name"]
        previous_path = seen_names.get(name)
        if previous_path is not None:
            errors.append(
                f"{py_path}: Duplicate manifest name '{name}' "
                f"(already declared in {previous_path})"
            )
            continue
        seen_names[name] = py_path

        entry = dict(manifest)
        entry["_file"] = relative_path
        entry["_size_kb"] = round(len(source.encode("utf-8")) / 1024, 1)
        entry["_lines"] = len(source.split("\n"))

        publishers.add(name.split("/")[0])
        categories.add(entry["category"])
        agents.append(entry)

    registry = {
        "schema": "rapp-registry/1.0",
        "version": "1.0.0",
        "generated_at": None,
        "stats": {
            "total_agents": len(agents),
            "publishers": len(publishers),
            "categories": len(categories),
            "publisher_list": sorted(publishers),
            "category_list": sorted(categories),
        },
        "agents": agents,
    }
    registry["generated_at"] = generated_at_for_registry(registry)
    return registry, errors


def write_registry(registry: dict) -> None:
    """Write a fully validated registry to its repository-owned destination."""
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def build_registry(*, write: bool = True) -> int:
    """Scan all agent .py files and build registry.json."""
    registry, errors = collect_registry()

    if errors:
        print(f"\n[ERROR] {len(errors)} validation errors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    if write:
        write_registry(registry)

    stats = registry["stats"]
    print(
        f"[OK] Registry built: {stats['total_agents']} agents from "
        f"{stats['publishers']} publishers"
    )
    print(f"  Categories: {', '.join(stats['category_list'])}")
    print(f"  Publishers: {', '.join(stats['publisher_list'])}")
    return 0


if __name__ == "__main__":
    sys.exit(build_registry())
