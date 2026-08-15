"""
Contract tests — parametrized over ALL agents.
Validates manifest, class structure, perform() return type, and standalone execution.
"""

import inspect
import subprocess
import sys
from pathlib import Path

import build_registry

REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_MANIFEST_FIELDS = [
    "schema", "name", "version", "display_name",
    "description", "author", "tags", "category",
]


def test_has_manifest(agent_info):
    mod, cls, path = agent_info
    assert hasattr(mod, "__manifest__"), f"{path.name}: missing __manifest__"
    assert isinstance(mod.__manifest__, dict), f"{path.name}: __manifest__ is not a dict"


def test_manifest_required_fields(agent_info):
    mod, cls, path = agent_info
    manifest = getattr(mod, "__manifest__", {})
    for field in REQUIRED_MANIFEST_FIELDS:
        assert field in manifest, f"{path.name}: __manifest__ missing '{field}'"


def test_manifest_name_format(agent_info):
    mod, cls, path = agent_info
    manifest = getattr(mod, "__manifest__", {})
    name = manifest.get("name", "")
    assert build_registry.MANIFEST_NAME_RE.fullmatch(name), (
        f"{path.name}: name must be @publisher/kebab-case-slug, got '{name}'"
    )


def test_manifest_matches_registry_schema(agent_info):
    mod, cls, path = agent_info
    errors = build_registry.validate_manifest(path, getattr(mod, "__manifest__", {}))

    assert not errors, f"{path.name}: invalid registry manifest: {'; '.join(errors)}"


def test_class_inherits_basic_agent(agent_info):
    mod, cls, path = agent_info
    assert cls is not None, f"{path.name}: no BasicAgent subclass found"
    from basic_agent import BasicAgent
    assert issubclass(cls, BasicAgent), f"{path.name}: {cls.__name__} does not inherit BasicAgent"


def test_instantiation(agent_info):
    mod, cls, path = agent_info
    assert cls is not None, f"{path.name}: no agent class found"
    instance = cls()
    assert instance is not None


def test_perform_accepts_unexpected_keyword_arguments(agent_info):
    mod, cls, path = agent_info
    assert cls is not None, f"{path.name}: no agent class found"

    accepts_kwargs = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in inspect.signature(cls.perform).parameters.values()
    )
    assert accepts_kwargs, f"{path.name}: perform() must accept **kwargs"


def test_perform_returns_str(agent_info):
    mod, cls, path = agent_info
    assert cls is not None, f"{path.name}: no agent class found"
    instance = cls()
    ops = []
    meta = getattr(instance, "metadata", {})
    params = meta.get("parameters", {})
    props = params.get("properties", {})
    op_prop = props.get("operation", {})
    ops = op_prop.get("enum", [])

    if ops:
        result = instance.perform(operation=ops[0])
    else:
        result = instance.perform()

    assert isinstance(result, str), (
        f"{path.name}: perform() returned {type(result).__name__}, expected str"
    )


def test_all_operations_return_nonempty(agent_info):
    mod, cls, path = agent_info
    assert cls is not None, f"{path.name}: no agent class found"
    instance = cls()

    meta = getattr(instance, "metadata", {})
    params = meta.get("parameters", {})
    props = params.get("properties", {})
    op_prop = props.get("operation", {})
    ops = op_prop.get("enum", [])

    if not ops:
        result = instance.perform()
        assert isinstance(result, str) and len(result) > 0, (
            f"{path.name}: perform() returned empty or non-str"
        )
        return

    for op in ops:
        result = instance.perform(operation=op)
        assert isinstance(result, str), (
            f"{path.name}: perform(operation='{op}') returned {type(result).__name__}"
        )
        assert len(result) > 0, (
            f"{path.name}: perform(operation='{op}') returned empty string"
        )


def test_standalone_execution(agent_info):
    mod, cls, path = agent_info
    result = subprocess.run(
        [sys.executable, str(path)],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, (
        f"{path.name}: standalone execution failed (exit {result.returncode})\n"
        f"stderr: {result.stderr[:500]}"
    )
