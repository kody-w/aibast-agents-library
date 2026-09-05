"""
GenomeCreatureAgent runs bounded evolution on the maintained Lisppy runtime.

Each creature is a deterministic grid-foraging simulation, not a sentient
being. Its executable genome is a small Scheme-like program containing a
``score-move`` function and any reusable tool definitions that evolution has
accepted. Food adds energy; movement, hazards, evaluator steps, and function
calls consume bounded resources.

``CREATURE_PROFILE`` is the only literal a manager replaces when materializing
another standalone ``*_agent.py`` file. ``id`` selects isolated storage below
the shared ``RAPP_CREATURE_DATA_DIR`` base, ``name`` is the display name,
``agent_name`` is the unique Brainstem tool name, and ``capabilities`` is the
exact sensor allowlist available to that genome.

The evaluator is the host-installed ``rappterbook-lispy-runtime`` distribution:

  Repository: https://github.com/kody-w/lisppy
  Commit: 5e3a2e3275825ffecdbc4b12541aff48d7ff235e
  API: ``from lisppy import LispyVM, ExecutionLimits``

For throughput, this agent uses the runtime's supported lower-level
``make_global_env`` / ``parse`` / ``evaluate`` API with one fresh, isolated
``profile='core'``, ``trusted=False``, ``load_stdlib=False`` environment per
episode. It never copies or replaces the maintained evaluator. Runtime context
steps accumulate across definitions and every score/tool call in an episode,
so definitions, bodies, argument evaluation, and call dispatch are not free.

An additional host-side grammar validator restricts genomes to integer
arithmetic, comparisons, ``if``, ``let``, ``begin``, ``and``, ``or``, direct
bounded lambdas, function definitions, permitted sensors, primitives, and
earlier accepted tools. It rejects eval, macros, exponentiation, imports,
collections, strings, randomness, filesystem/network/Rappterbook operations,
caller-defined primitives, recursion, forward calls, and unbounded iteration.
Static interval analysis bounds every possible arithmetic intermediate.

Evolution integrates real tool invention. Each generation synthesizes source
over primitives, sensors, and inherited accepted tools, executes every valid
proposal on the training course, and records source, dependencies, actual
runtime step cost, failures, and measured acceptance reasons. A primitive-only
lineage evolves in parallel with the same candidate count, seeds, and per-
episode evaluator-step limit. Comparisons use identical held-out seeds and
equal total step allowances, and honestly report a primitive win or tie.

Actions are ``status``, ``hatch``, ``evolve``, ``race``, ``export_egg``, and
``resume``. Invention is integrated into ``evolve``. State and public artifacts
live under ``<base>/<profile.id>/`` and are written atomically under a process
lock. Eggs retain profile, programs, accepted tools, failed inventions, memory,
lineage, comparisons, and checksums for exact fresh-process continuation.
"""

import copy
import difflib
import fcntl
import hashlib
import json
import math
import os
import random
import re
from contextlib import contextmanager
from pathlib import Path

from agents.basic_agent import BasicAgent


CREATURE_PROFILE = {
    "id": "astra",
    "name": "Astra",
    "agent_name": "AstraCreature",
    "capabilities": [
        "food",
        "hazard",
        "visited",
        "distance",
        "energy",
        "step",
        "x",
        "y",
        "dx",
        "dy",
        "edge",
        "repeat",
    ],
}


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@kody-w/genome-creature",
    "version": "3.0.0",
    "display_name": "Genome Creature",
    "description": "Evolves a bounded grid creature whose pinned Lisppy genome can invent, inherit, race, compare, and export real reusable tools.",
    "author": "Kody Wildfeuer",
    "tags": ["simulation", "evolution", "lisppy", "genome", "invention", "deterministic"],
    "category": "productivity",
    "quality_tier": "community",
    "requires_env": [],
    "dependencies": ["@rapp/basic_agent"],
    "runtime_dependencies": [
        "rappterbook-lispy-runtime@5e3a2e3275825ffecdbc4b12541aff48d7ff235e"
    ],
    "example_call": {"args": {"action": "evolve", "generations": 12, "expected_generation": 0}},
}


STATE_SCHEMA = "rapp-creature/state/3"
SNAPSHOT_SCHEMA = "rapp-creature/snapshot/1"
EGG_SCHEMA = "rapp-creature/egg/3"

LISPPY_DISTRIBUTION = "rappterbook-lispy-runtime"
LISPPY_SOURCE_URL = "https://github.com/kody-w/lisppy"
LISPPY_SOURCE_COMMIT = "5e3a2e3275825ffecdbc4b12541aff48d7ff235e"
LISPPY_VERSION = "0.24.0"

WORLD_WIDTH = 7
WORLD_HEIGHT = 7
FOOD_COUNT = 7
HAZARD_COUNT = 8
INITIAL_ENERGY = 28
FOOD_REWARD = 9
HAZARD_COST = 7
MOVE_COST = 1
MAX_STEPS = 48
MAX_EPISODE_ENERGY = INITIAL_ENERGY + FOOD_COUNT * FOOD_REWARD

TRAINING_TRIALS = 12
COMPARISON_TRIALS = 6
MAX_GENERATIONS_PER_ACTION = 12
MAX_TOTAL_GENERATIONS = 48
MAX_CANDIDATES_PER_GENERATION = 8
TOOL_CANDIDATES_PER_GENERATION = 4
MAX_TOOLS = 12
MAX_RACE_TRIALS = 32
MAX_RACE_CONTESTANTS = 16

MAX_PROGRAM_CHARS = 5000
MAX_DEFINITION_CHARS = 700
MAX_FORM_NODES = 900
MAX_FORM_DEPTH = 24
MAX_BINDINGS = 4
MAX_INTEGER_LITERAL = 1000
MAX_ARITHMETIC_RESULT = 1_000_000
MAX_CALL_DEPTH = 16
OPERATION_LIMIT = 9000
TOOL_PROBE_TRIALS = 3
DIAGNOSTIC_BUDGET = TOOL_CANDIDATES_PER_GENERATION * TOOL_PROBE_TRIALS * OPERATION_LIMIT
MAX_COLLECTION_ITEMS = 64
MAX_OUTPUT_BYTES = 0

MAX_NAME_CHARS = 64
MAX_STATE_BYTES = 2_000_000
MAX_EGG_BYTES = 2_000_000
MAX_DIFF_CHARS = 12_000
MAX_METRIC_ABS = 1_000_000_000

NAME_PATTERN = r"[A-Za-z0-9][A-Za-z0-9 _.-]{0,63}\Z"
PROFILE_ID_PATTERN = r"[a-z][a-z0-9-]{0,31}\Z"
AGENT_NAME_PATTERN = r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z"
TOOL_ID_PATTERN = r"tool-g[1-9][0-9]*-[0-9]+\Z"
LOCAL_NAME_PATTERN = r"[a-z][a-z0-9-]{0,31}\Z"
SHA256_PATTERN = r"[0-9a-f]{64}\Z"

ACTIONS = (
    ("up", 0, -1),
    ("right", 1, 0),
    ("down", 0, 1),
    ("left", -1, 0),
)

SENSOR_RANGES = {
    "food": (0, 1),
    "hazard": (0, 1),
    "visited": (0, MAX_STEPS + 1),
    "distance": (0, WORLD_WIDTH + WORLD_HEIGHT - 2),
    "energy": (0, MAX_EPISODE_ENERGY),
    "step": (0, MAX_STEPS - 1),
    "x": (0, WORLD_WIDTH - 1),
    "y": (0, WORLD_HEIGHT - 1),
    "dx": (-1, 1),
    "dy": (-1, 1),
    "edge": (0, min(WORLD_WIDTH, WORLD_HEIGHT) // 2),
    "repeat": (0, 1),
}

PRIMITIVE_ARITIES = {
    "+": (1, 4),
    "-": (1, 4),
    "*": (1, 4),
    "//": (2, 2),
    "%": (2, 2),
    "abs": (1, 1),
    "min": (1, 4),
    "max": (1, 4),
    "<": (2, 2),
    ">": (2, 2),
    "<=": (2, 2),
    ">=": (2, 2),
    "=": (2, 2),
    "not": (1, 1),
}

_RUNTIME = None


class CreatureError(ValueError):
    """Expected input, dependency, genome, or state error returned as JSON."""


class LisppyDependencyError(CreatureError):
    """The specifically pinned maintained runtime is not installed."""


class LispSyntaxError(CreatureError):
    """The host validator rejected a genome before execution."""


class LisppyRuntimeError(CreatureError):
    """The maintained runtime returned a structured execution error."""

    def __init__(self, message, resource=None):
        self.resource = resource
        super().__init__(message)


class FuelExhausted(LisppyRuntimeError):
    """The maintained runtime exhausted max_steps."""


class Symbol(str):
    """Host-side source-construction symbol; never evaluates code itself."""


def _load_runtime():
    global _RUNTIME
    if _RUNTIME is None:
        try:
            import lisppy
            from lisppy import ExecutionLimits, LispyVM
            import lisp
        except ModuleNotFoundError as error:
            if error.name in {"lisppy", "lisp"}:
                raise LisppyDependencyError(
                    "rappterbook-lispy-runtime dependency missing; install the pinned "
                    f"{LISPPY_SOURCE_COMMIT} build in the isolated Brainstem environment"
                ) from None
            raise
        if (
            getattr(lisppy, "DISTRIBUTION_NAME", None) != LISPPY_DISTRIBUTION
            or getattr(lisp, "DISTRIBUTION_NAME", None) != LISPPY_DISTRIBUTION
            or getattr(lisppy, "VERSION", None) != LISPPY_VERSION
            or LispyVM is not lisp.LispyVM
        ):
            raise LisppyDependencyError(
                "the installed 'lisppy' module is not the required "
                f"{LISPPY_DISTRIBUTION} distribution"
            )
        _RUNTIME = {
            "facade": lisppy,
            "LispyVM": LispyVM,
            "ExecutionLimits": ExecutionLimits,
            "lisp": lisp,
        }
    return _RUNTIME


def _runtime_limits(max_steps=OPERATION_LIMIT):
    runtime = _load_runtime()
    return runtime["ExecutionLimits"](
        max_steps=max_steps,
        max_call_depth=MAX_CALL_DEPTH,
        max_reader_depth=MAX_FORM_DEPTH,
        max_source_bytes=MAX_PROGRAM_CHARS,
        max_collection_items=MAX_COLLECTION_ITEMS,
        max_output_bytes=MAX_OUTPUT_BYTES,
    )


def _require_int(value, label, minimum, maximum):
    if type(value) is not int:
        raise CreatureError(f"{label} must be an integer, not a boolean or another type")
    if value < minimum or value > maximum:
        raise CreatureError(f"{label} must be between {minimum} and {maximum}")
    return value


def _require_sha256(value, label):
    if not isinstance(value, str) or not re.fullmatch(SHA256_PATTERN, value):
        raise CreatureError(f"{label} must be a lowercase SHA-256 hex digest")
    return value


def _normalize_name(value):
    if not isinstance(value, str) or not re.fullmatch(NAME_PATTERN, value):
        raise CreatureError(
            f"name must be 1-{MAX_NAME_CHARS} characters using letters, numbers, spaces, '.', '_' or '-'"
        )
    return value


def _validated_capabilities(value, label="profile.capabilities"):
    if not isinstance(value, list) or not value:
        raise CreatureError(f"{label} must be a non-empty list of sensor names")
    if len(value) > len(SENSOR_RANGES):
        raise CreatureError(f"{label} contains too many sensors")
    capabilities = []
    for sensor in value:
        if not isinstance(sensor, str) or sensor not in SENSOR_RANGES:
            raise CreatureError(f"{label} contains unknown sensor {sensor!r}")
        if sensor in capabilities:
            raise CreatureError(f"{label} contains duplicate sensor {sensor!r}")
        capabilities.append(sensor)
    return capabilities


def _validated_profile(value=None):
    profile = CREATURE_PROFILE if value is None else value
    expected = {"id", "name", "agent_name", "capabilities"}
    if not isinstance(profile, dict) or set(profile) != expected:
        raise CreatureError(
            "CREATURE_PROFILE must contain exactly id, name, agent_name and capabilities"
        )
    profile_id = profile["id"]
    if not isinstance(profile_id, str) or not re.fullmatch(
        PROFILE_ID_PATTERN, profile_id
    ):
        raise CreatureError("profile.id must match [a-z][a-z0-9-]{0,31}")
    name = _normalize_name(profile["name"])
    agent_name = profile["agent_name"]
    if not isinstance(agent_name, str) or not re.fullmatch(
        AGENT_NAME_PATTERN, agent_name
    ):
        raise CreatureError(
            "profile.agent_name must begin with a letter and use only letters, numbers, '_' or '-'"
        )
    return {
        "id": profile_id,
        "name": name,
        "agent_name": agent_name,
        "capabilities": _validated_capabilities(profile["capabilities"]),
    }


def _data_base():
    configured = os.environ.get("RAPP_CREATURE_DATA_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".brainstem-creature" / "data"


def _profile_root():
    return _data_base() / _validated_profile()["id"]


def _vm_metadata():
    return {
        "name": "LispyVM core",
        "distribution": LISPPY_DISTRIBUTION,
        "version": LISPPY_VERSION,
        "source_url": LISPPY_SOURCE_URL,
        "source_commit": LISPPY_SOURCE_COMMIT,
        "operation_limit": OPERATION_LIMIT,
        "selection_diagnostic_budget": DIAGNOSTIC_BUDGET,
        "cost_model": {
            "unit": "admitted maintained-runtime evaluator step",
            "evaluated_expression": 1,
            "function_dispatch": 1,
            "definitions": "included in episode usage",
            "function_bodies": "included in episode usage",
            "collection_work": "additional runtime-counted steps",
            "usage_field": "ExecutionContext.steps",
            "limit_rejection": "Lisppy counts the denied step before raising; attempted_used preserves that counter separately from admitted used.",
        },
    }


def _limits():
    return {
        "world_width": WORLD_WIDTH,
        "world_height": WORLD_HEIGHT,
        "food_count": FOOD_COUNT,
        "hazard_count": HAZARD_COUNT,
        "initial_energy": INITIAL_ENERGY,
        "food_reward": FOOD_REWARD,
        "hazard_cost": HAZARD_COST,
        "move_cost": MOVE_COST,
        "max_steps": MAX_STEPS,
        "training_trials": TRAINING_TRIALS,
        "comparison_trials": COMPARISON_TRIALS,
        "max_generations_per_action": MAX_GENERATIONS_PER_ACTION,
        "max_total_generations": MAX_TOTAL_GENERATIONS,
        "candidates_per_generation": MAX_CANDIDATES_PER_GENERATION,
        "tool_candidates_per_generation": TOOL_CANDIDATES_PER_GENERATION,
        "max_tools": MAX_TOOLS,
        "max_race_trials": MAX_RACE_TRIALS,
        "max_program_chars": MAX_PROGRAM_CHARS,
        "max_definition_chars": MAX_DEFINITION_CHARS,
        "max_form_nodes": MAX_FORM_NODES,
        "max_form_depth": MAX_FORM_DEPTH,
        "max_integer_literal": MAX_INTEGER_LITERAL,
        "max_arithmetic_result": MAX_ARITHMETIC_RESULT,
        "max_call_depth": MAX_CALL_DEPTH,
        "operation_limit": OPERATION_LIMIT,
        "max_collection_items": MAX_COLLECTION_ITEMS,
        "max_output_bytes": MAX_OUTPUT_BYTES,
        "max_egg_bytes": MAX_EGG_BYTES,
    }


# ---------------------------------------------------------------------------
# Source representation and strict host-side grammar validation.
# ---------------------------------------------------------------------------


def _value_repr(value):
    if value is True:
        return "#t"
    if value is False:
        return "#f"
    if isinstance(value, Symbol):
        return str(value)
    if isinstance(value, str):
        escaped = (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
        )
        return f'"{escaped}"'
    if isinstance(value, list):
        return "(" + " ".join(_value_repr(item) for item in value) + ")"
    return str(value)


def _normalize_program(source):
    if not isinstance(source, str):
        raise LispSyntaxError("genome source must be a string")
    source = source.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not source:
        raise LispSyntaxError("genome source must not be empty")
    if len(source) > MAX_PROGRAM_CHARS:
        raise LispSyntaxError(
            f"genome source exceeds the {MAX_PROGRAM_CHARS}-character limit"
        )
    if not source.isascii():
        raise LispSyntaxError("genome source must use ASCII Lisppy syntax")
    if any(ord(character) < 32 and character not in "\n\t" for character in source):
        raise LispSyntaxError("genome source contains a control character")
    if any(character in source for character in "[]'`\",;"):
        raise LispSyntaxError(
            "quotes, strings, comments, brackets and reader macros are outside the genome subset"
        )
    return source


def _to_gene(value, lisp_module):
    if isinstance(value, lisp_module.Symbol):
        return Symbol(str(value))
    if isinstance(value, list):
        return [_to_gene(item, lisp_module) for item in value]
    if type(value) in (int, bool):
        return value
    if value is lisp_module.NIL:
        return Symbol("nil")
    if isinstance(value, float):
        raise LispSyntaxError("floating-point literals are outside the genome subset")
    if isinstance(value, str):
        return value
    raise LispSyntaxError(f"unsupported parsed value: {type(value).__name__}")


def parse(source):
    normalized = _normalize_program(source)
    runtime = _load_runtime()
    try:
        expressions = runtime["lisp"].parse(
            normalized,
            max_depth=MAX_FORM_DEPTH,
            source_name="<creature-genome>",
        )
    except runtime["lisp"].LispError as error:
        raise LispSyntaxError(str(error)) from None
    return [_to_gene(expression, runtime["lisp"]) for expression in expressions]


def _form_node_count(value):
    if not isinstance(value, list):
        return 1
    return 1 + sum(_form_node_count(item) for item in value)


def _form_depth(value):
    if not isinstance(value, list) or not value:
        return 1
    return 1 + max(_form_depth(item) for item in value)


def _bounded_interval(low, high):
    if low < -MAX_ARITHMETIC_RESULT or high > MAX_ARITHMETIC_RESULT:
        raise LispSyntaxError(
            f"arithmetic can exceed +/-{MAX_ARITHMETIC_RESULT}"
        )
    return ("number", low, high)


def _require_number_interval(interval, label):
    if interval[0] != "number":
        raise LispSyntaxError(f"{label} requires numeric arguments")
    return interval[1], interval[2]


def _union_intervals(first, second):
    if first[0] != second[0]:
        raise LispSyntaxError("if branches must return the same value kind")
    if first[0] == "boolean":
        return ("boolean",)
    return _bounded_interval(min(first[1], second[1]), max(first[2], second[2]))


def _validate_arity(name, count):
    minimum, maximum = PRIMITIVE_ARITIES[name]
    if count < minimum or count > maximum:
        raise LispSyntaxError(
            f"{name} expects {minimum}-{maximum} arguments, got {count}"
        )


def _validate_body(
    expression,
    scope,
    available_tools,
    tool_intervals,
    capabilities,
    dependencies,
):
    if type(expression) is int:
        if abs(expression) > MAX_INTEGER_LITERAL:
            raise LispSyntaxError(
                f"integer literal exceeds +/-{MAX_INTEGER_LITERAL}"
            )
        return ("number", expression, expression)
    if type(expression) is bool:
        return ("boolean",)
    if isinstance(expression, str) and not isinstance(expression, Symbol):
        raise LispSyntaxError("string literals are outside the genome subset")
    if isinstance(expression, Symbol):
        if expression == "nil":
            raise LispSyntaxError("nil is outside numeric genome bodies")
        if expression not in scope:
            raise LispSyntaxError(f"unbound value symbol: {expression}")
        return scope[str(expression)]
    if not isinstance(expression, list) or not expression:
        raise LispSyntaxError("empty and non-list forms are not executable")

    head = expression[0]
    if isinstance(head, Symbol) and head == "if":
        if len(expression) != 4:
            raise LispSyntaxError("if requires exactly test, then and else")
        _validate_body(
            expression[1], scope, available_tools, tool_intervals, capabilities, dependencies
        )
        then_interval = _validate_body(
            expression[2], scope, available_tools, tool_intervals, capabilities, dependencies
        )
        else_interval = _validate_body(
            expression[3], scope, available_tools, tool_intervals, capabilities, dependencies
        )
        return _union_intervals(then_interval, else_interval)
    if isinstance(head, Symbol) and head == "let":
        if len(expression) != 3 or not isinstance(expression[1], list):
            raise LispSyntaxError("let requires bindings and one body expression")
        bindings = expression[1]
        if len(bindings) > MAX_BINDINGS:
            raise LispSyntaxError(f"let exceeds {MAX_BINDINGS} bindings")
        local_scope = dict(scope)
        names = []
        for binding in bindings:
            if (
                not isinstance(binding, list)
                or len(binding) != 2
                or not isinstance(binding[0], Symbol)
                or not re.fullmatch(LOCAL_NAME_PATTERN, binding[0])
            ):
                raise LispSyntaxError("invalid let binding")
            name = str(binding[0])
            if name in names or name in capabilities:
                raise LispSyntaxError(f"invalid or duplicate let name: {name}")
            local_scope[name] = _validate_body(
                binding[1],
                scope,
                available_tools,
                tool_intervals,
                capabilities,
                dependencies,
            )
            names.append(name)
        return _validate_body(
            expression[2],
            local_scope,
            available_tools,
            tool_intervals,
            capabilities,
            dependencies,
        )
    if isinstance(head, Symbol) and head == "begin":
        if len(expression) < 2 or len(expression) > 4:
            raise LispSyntaxError("begin requires 1-3 expressions")
        result = ("number", 0, 0)
        for item in expression[1:]:
            result = _validate_body(
                item, scope, available_tools, tool_intervals, capabilities, dependencies
            )
        return result
    if isinstance(head, Symbol) and head in ("and", "or"):
        if len(expression) < 2 or len(expression) > 5:
            raise LispSyntaxError(f"{head} requires 1-4 expressions")
        for item in expression[1:]:
            result = _validate_body(
                item, scope, available_tools, tool_intervals, capabilities, dependencies
            )
            if result[0] != "boolean":
                raise LispSyntaxError(f"{head} is restricted to boolean expressions")
        return ("boolean",)

    if isinstance(head, list):
        if (
            len(head) != 3
            or not isinstance(head[0], Symbol)
            or head[0] != "lambda"
            or not isinstance(head[1], list)
        ):
            raise LispSyntaxError("only direct bounded lambda calls are allowed")
        params = []
        for param in head[1]:
            if (
                not isinstance(param, Symbol)
                or not re.fullmatch(LOCAL_NAME_PATTERN, param)
                or str(param) in params
            ):
                raise LispSyntaxError("invalid lambda parameter")
            params.append(str(param))
        if len(params) != len(expression) - 1 or len(params) > len(capabilities):
            raise LispSyntaxError("lambda arity is invalid")
        argument_intervals = [
            _validate_body(
                item, scope, available_tools, tool_intervals, capabilities, dependencies
            )
            for item in expression[1:]
        ]
        lambda_scope = dict(scope)
        lambda_scope.update(zip(params, argument_intervals))
        return _validate_body(
            head[2],
            lambda_scope,
            available_tools,
            tool_intervals,
            capabilities,
            dependencies,
        )

    if not isinstance(head, Symbol):
        raise LispSyntaxError("call head must be a permitted symbol")
    name = str(head)
    argument_intervals = [
        _validate_body(
            item, scope, available_tools, tool_intervals, capabilities, dependencies
        )
        for item in expression[1:]
    ]
    if name in available_tools:
        if len(argument_intervals) != len(capabilities):
            raise LispSyntaxError(
                f"{name} requires all {len(capabilities)} capability arguments"
            )
        dependencies.add(name)
        return tool_intervals[name]
    if name not in PRIMITIVE_ARITIES:
        raise LispSyntaxError(f"call to unavailable function: {name}")
    _validate_arity(name, len(argument_intervals))

    if name in ("<", ">", "<=", ">="):
        for interval in argument_intervals:
            _require_number_interval(interval, name)
        return ("boolean",)
    if name == "=":
        if argument_intervals[0][0] != argument_intervals[1][0]:
            raise LispSyntaxError("= arguments must have the same value kind")
        return ("boolean",)
    if name == "not":
        if argument_intervals[0][0] != "boolean":
            raise LispSyntaxError("not requires a boolean")
        return ("boolean",)

    numeric = [
        _require_number_interval(interval, name)
        for interval in argument_intervals
    ]
    if name == "+":
        return _bounded_interval(
            sum(low for low, _ in numeric),
            sum(high for _, high in numeric),
        )
    if name == "-":
        if len(numeric) == 1:
            low, high = numeric[0]
            return _bounded_interval(-high, -low)
        low = numeric[0][0] - sum(high for _, high in numeric[1:])
        high = numeric[0][1] - sum(low for low, _ in numeric[1:])
        return _bounded_interval(low, high)
    if name == "*":
        low, high = 1, 1
        for right_low, right_high in numeric:
            products = (
                low * right_low,
                low * right_high,
                high * right_low,
                high * right_high,
            )
            low, high = min(products), max(products)
            _bounded_interval(low, high)
        return _bounded_interval(low, high)
    if name in ("//", "%"):
        divisor = expression[2]
        if type(divisor) is not int or divisor <= 0:
            raise LispSyntaxError(
                f"{name} requires a positive integer literal divisor"
            )
        left_low, left_high = numeric[0]
        if name == "//":
            return _bounded_interval(left_low // divisor, left_high // divisor)
        return _bounded_interval(0, divisor - 1)
    if name == "abs":
        low, high = numeric[0]
        return _bounded_interval(0, max(abs(low), abs(high)))
    if name == "min":
        return _bounded_interval(
            min(low for low, _ in numeric),
            min(high for _, high in numeric),
        )
    if name == "max":
        return _bounded_interval(
            max(low for low, _ in numeric),
            max(high for _, high in numeric),
        )
    raise LispSyntaxError(f"unsupported primitive: {name}")


class MeteredLispyProgram:
    """Validated source plus maintained-runtime parsed expressions."""

    def __init__(self, source, capabilities=None):
        self.source = _normalize_program(source)
        self.capabilities = tuple(
            _validated_profile()["capabilities"]
            if capabilities is None
            else _validated_capabilities(list(capabilities), "capabilities")
        )
        runtime = _load_runtime()
        try:
            runtime_expressions = runtime["lisp"].parse(
                self.source,
                max_depth=MAX_FORM_DEPTH,
                source_name="<creature-genome>",
            )
        except runtime["lisp"].LispError as error:
            raise LispSyntaxError(str(error)) from None
        expressions = [
            _to_gene(expression, runtime["lisp"])
            for expression in runtime_expressions
        ]
        if not expressions:
            raise LispSyntaxError("program contains no definitions")
        if len(expressions) > MAX_TOOLS + 1:
            raise LispSyntaxError("program contains too many definitions")
        if sum(_form_node_count(item) for item in expressions) > MAX_FORM_NODES:
            raise LispSyntaxError(
                f"program exceeds the {MAX_FORM_NODES}-node form limit"
            )
        if max(_form_depth(item) for item in expressions) > MAX_FORM_DEPTH:
            raise LispSyntaxError(
                f"program exceeds the form depth limit of {MAX_FORM_DEPTH}"
            )

        scope = {
            sensor: ("number", *SENSOR_RANGES[sensor])
            for sensor in self.capabilities
        }
        available_tools = set()
        tool_intervals = {}
        definitions = []
        score_definition = None
        for index, expression in enumerate(expressions):
            if (
                not isinstance(expression, list)
                or len(expression) != 3
                or not isinstance(expression[0], Symbol)
                or expression[0] != "define"
                or not isinstance(expression[1], list)
                or not expression[1]
            ):
                raise LispSyntaxError(
                    "top-level forms must be single-body function definitions"
                )
            target = expression[1]
            if not all(isinstance(item, Symbol) for item in target):
                raise LispSyntaxError("definition names and parameters must be symbols")
            name = str(target[0])
            params = [str(item) for item in target[1:]]
            if params != list(self.capabilities):
                raise LispSyntaxError(
                    f"{name} parameters must exactly match profile capabilities"
                )
            if name == "score-move":
                if index != len(expressions) - 1 or score_definition is not None:
                    raise LispSyntaxError("score-move must be the single final definition")
            elif not re.fullmatch(TOOL_ID_PATTERN, name):
                raise LispSyntaxError(f"invalid tool definition name: {name}")
            if name in available_tools:
                raise LispSyntaxError(f"duplicate tool definition: {name}")

            dependencies = set()
            interval = _validate_body(
                expression[2],
                scope,
                set(available_tools),
                tool_intervals,
                self.capabilities,
                dependencies,
            )
            if interval[0] != "number":
                raise LispSyntaxError(f"{name} must return a bounded integer")
            definition = {
                "name": name,
                "source": _value_repr(expression),
                "body": expression[2],
                "depends_on": sorted(dependencies),
                "interval": interval,
            }
            if name == "score-move":
                score_definition = definition
            else:
                definitions.append(definition)
                available_tools.add(name)
                tool_intervals[name] = interval
        if score_definition is None:
            raise LispSyntaxError("program must define score-move")

        self.expressions = expressions
        self.runtime_expressions = runtime_expressions
        self.tool_definitions = definitions
        self.score_definition = score_definition
        self.score_expression = score_definition["body"]
        self.score_expression_source = _value_repr(self.score_expression)

    def start(self, operation_limit=OPERATION_LIMIT):
        return LispyRuntime(self, operation_limit)


class _RuntimeMeter:
    def __init__(self, runtime):
        self.runtime = runtime

    @property
    def used(self):
        # Scalar genomes cannot execute the step that Lisppy rejects at its limit.
        # Preserve the upstream attempted counter separately rather than hiding it.
        return min(self.attempted, self.runtime.env.context.limits.max_steps)

    @property
    def attempted(self):
        return self.runtime.env.context.steps


class LispyRuntime:
    """One fresh core environment whose real context steps span an episode."""

    def __init__(self, program, operation_limit):
        self.program = program
        self.api = _load_runtime()
        lisp = self.api["lisp"]
        self.env = lisp.make_global_env(
            profile="core",
            trusted=False,
            load_stdlib=False,
            limits=_runtime_limits(operation_limit),
            output=lambda _text: None,
            state_dir=_profile_root(),
        )
        self.meter = _RuntimeMeter(self)
        self.definition_costs = {}
        for expression in program.runtime_expressions:
            name = str(expression[1][0])
            before = self.meter.used
            try:
                lisp.evaluate(expression, self.env)
            except lisp.LispError as error:
                raise _translated_runtime_error(error, lisp) from None
            self.definition_costs[name] = self.meter.used - before

    def call(self, name, values):
        lisp = self.api["lisp"]
        expression = [lisp.Symbol(name), *values]
        try:
            result = lisp.evaluate(expression, self.env)
        except lisp.LispError as error:
            raise _translated_runtime_error(error, lisp) from None
        if type(result) is not int:
            raise LisppyRuntimeError(f"{name} must return an integer score")
        if result < -MAX_ARITHMETIC_RESULT or result > MAX_ARITHMETIC_RESULT:
            raise LisppyRuntimeError(
                f"{name} result exceeds +/-{MAX_ARITHMETIC_RESULT}"
            )
        return result

    def score_move(self, sensors):
        values = []
        for sensor in self.program.capabilities:
            value = sensors[sensor]
            if type(value) is not int:
                raise LisppyRuntimeError(f"sensor {sensor} must be an integer")
            minimum, maximum = SENSOR_RANGES[sensor]
            if value < minimum or value > maximum:
                raise LisppyRuntimeError(
                    f"sensor {sensor} is outside its bounded range"
                )
            values.append(value)
        return self.call("score-move", values)


def _translated_runtime_error(error, lisp_module):
    resource = getattr(error, "resource", None)
    if isinstance(error, lisp_module.ExecutionLimitExceeded) and resource == "steps":
        return FuelExhausted(str(error), resource=resource)
    return LisppyRuntimeError(str(error), resource=resource)


def _genome_sha256(source):
    return hashlib.sha256(_normalize_program(source).encode("utf-8")).hexdigest()


def _definition_expression(name, capabilities, body):
    return [
        Symbol("define"),
        [Symbol(name), *[Symbol(sensor) for sensor in capabilities]],
        body,
    ]


def _build_program(tool_sources, score_expression, capabilities=None):
    enabled = (
        _validated_profile()["capabilities"]
        if capabilities is None
        else _validated_capabilities(list(capabilities), "capabilities")
    )
    sources = list(tool_sources)
    sources.append(
        _value_repr(_definition_expression("score-move", enabled, score_expression))
    )
    return "\n".join(sources)


def _founder_expression(capabilities=None):
    enabled = (
        _validated_profile()["capabilities"]
        if capabilities is None
        else _validated_capabilities(list(capabilities), "capabilities")
    )
    if "food" in enabled and "distance" in enabled:
        return [
            Symbol("-"),
            [Symbol("*"), Symbol("food"), 6],
            Symbol("distance"),
        ]
    if "food" in enabled:
        return [Symbol("*"), Symbol("food"), 6]
    preferred = (
        ("distance", [Symbol("-"), Symbol("distance")]),
        ("hazard", [Symbol("-"), [Symbol("*"), Symbol("hazard"), 3]]),
        ("visited", [Symbol("-"), Symbol("visited")]),
        ("repeat", [Symbol("-"), Symbol("repeat")]),
        ("edge", Symbol("edge")),
        ("dx", Symbol("dx")),
        ("dy", Symbol("dy")),
        ("x", Symbol("x")),
        ("y", Symbol("y")),
        ("energy", Symbol("energy")),
        ("step", [Symbol("-"), Symbol("step")]),
    )
    for sensor, expression in preferred:
        if sensor in enabled:
            return expression
    raise CreatureError("profile.capabilities cannot construct a founder genome")


FOUNDER_EXPRESSION = _founder_expression()
FOUNDER_PROGRAM = _build_program([], FOUNDER_EXPRESSION)


# ---------------------------------------------------------------------------
# Deterministic grid environment and maintained-runtime execution.
# ---------------------------------------------------------------------------


def _derive_seed(base_seed, domain, index):
    material = f"rapp-creature/3|{base_seed}|{domain}|{index}".encode("ascii")
    value = int.from_bytes(hashlib.sha256(material).digest()[:8], "big")
    if domain == "training":
        return value & ((1 << 30) - 1)
    if domain == "heldout":
        return (value & ((1 << 30) - 1)) | (1 << 30)
    if domain == "race":
        return (value & ((1 << 30) - 1)) | (1 << 31)
    return value


def _seed_sequence(base_seed, domain, count):
    seeds = []
    used = set()
    index = 0
    while len(seeds) < count:
        seed = _derive_seed(base_seed, domain, index)
        index += 1
        if seed not in used:
            used.add(seed)
            seeds.append(seed)
    return seeds


def _training_seeds(base_seed):
    return _seed_sequence(base_seed, "training", TRAINING_TRIALS)


def _heldout_seeds(base_seed, count):
    return _seed_sequence(base_seed, "heldout", count)


def _race_seeds(base_seed, count):
    return _seed_sequence(base_seed, "race", count)


def _seed_set_id(domain, seeds):
    encoded = ",".join(str(seed) for seed in seeds).encode("ascii")
    return f"{domain}-sha256:{hashlib.sha256(encoded).hexdigest()[:20]}"


def _world_for_seed(seed):
    rng = random.Random(seed)
    start = (WORLD_WIDTH // 2, WORLD_HEIGHT // 2)
    cells = [
        (x, y)
        for y in range(WORLD_HEIGHT)
        for x in range(WORLD_WIDTH)
        if (x, y) != start
    ]
    rng.shuffle(cells)
    food = frozenset(cells[:FOOD_COUNT])
    hazards = frozenset(cells[FOOD_COUNT:FOOD_COUNT + HAZARD_COUNT])
    actions = list(ACTIONS)
    rng.shuffle(actions)
    return {
        "start": start,
        "food": food,
        "hazards": hazards,
        "actions": tuple(actions),
    }


def _candidate_sensors(
    target,
    delta,
    remaining_food,
    hazards,
    visits,
    energy,
    step,
    previous,
    capabilities,
):
    x, y = target
    distance = (
        min(
            abs(x - food_x) + abs(y - food_y)
            for food_x, food_y in remaining_food
        )
        if remaining_food
        else 0
    )
    sensors = {
        "food": int(target in remaining_food),
        "hazard": int(target in hazards),
        "visited": visits.get(target, 0),
        "distance": distance,
        "energy": energy,
        "step": step,
        "x": x,
        "y": y,
        "dx": delta[0],
        "dy": delta[1],
        "edge": min(x, y, WORLD_WIDTH - 1 - x, WORLD_HEIGHT - 1 - y),
        "repeat": int(previous is not None and target == previous),
    }
    return {sensor: sensors[sensor] for sensor in capabilities}


def _simulate_episode(source, seed, include_trace=False):
    program = (
        source if isinstance(source, MeteredLispyProgram)
        else MeteredLispyProgram(source)
    )
    world = _world_for_seed(seed)
    runtime = program.start(OPERATION_LIMIT)
    position = world["start"]
    previous = None
    remaining_food = set(world["food"])
    visits = {position: 1}
    energy = INITIAL_ENERGY
    collected = 0
    steps = 0
    termination = None
    trace = []
    if include_trace:
        trace.append(
            {
                "step": 0,
                "x": position[0],
                "y": position[1],
                "energy": energy,
                "collected": 0,
                "event": "start",
                "action": "start",
            }
        )

    while energy > 0 and steps < MAX_STEPS and remaining_food:
        choices = []
        try:
            for action, dx, dy in world["actions"]:
                target = (position[0] + dx, position[1] + dy)
                if not (
                    0 <= target[0] < WORLD_WIDTH
                    and 0 <= target[1] < WORLD_HEIGHT
                ):
                    continue
                sensors = _candidate_sensors(
                    target,
                    (dx, dy),
                    remaining_food,
                    world["hazards"],
                    visits,
                    energy,
                    steps,
                    previous,
                    program.capabilities,
                )
                choices.append((runtime.score_move(sensors), action, target))
        except FuelExhausted:
            termination = "fuel_exhausted"
            break
        except LisppyRuntimeError as error:
            termination = f"vm_error:{str(error)[:120]}"
            break

        _, action, target = max(choices, key=lambda choice: choice[0])
        previous, position = position, target
        steps += 1
        energy -= MOVE_COST
        event = "move"
        if position in remaining_food:
            remaining_food.remove(position)
            collected += 1
            energy += FOOD_REWARD
            event = "food"
        elif position in world["hazards"]:
            energy -= HAZARD_COST
            event = "hazard"
        energy = max(0, energy)
        visits[position] = visits.get(position, 0) + 1
        if include_trace:
            trace.append(
                {
                    "step": steps,
                    "x": position[0],
                    "y": position[1],
                    "energy": energy,
                    "collected": collected,
                    "event": event,
                    "action": action,
                }
            )

    if termination is None:
        if not remaining_food:
            termination = "all_food"
        elif energy <= 0:
            termination = "energy_depleted"
        else:
            termination = "step_limit"
    score = collected * 100 + energy * 2 - steps
    if termination == "fuel_exhausted" or termination.startswith("vm_error:"):
        score -= 200
    return {
        "score": score,
        "food": collected,
        "steps": steps,
        "energy": energy,
        "operations": runtime.meter.used,
        "attempted_operations": runtime.meter.attempted,
        "operation_limit": OPERATION_LIMIT,
        "peak_call_depth": runtime.env.context.peak_call_depth,
        "termination": termination,
        "seed": seed,
        "width": WORLD_WIDTH,
        "height": WORLD_HEIGHT,
        "food_locations": [list(cell) for cell in sorted(world["food"])],
        "hazards": [list(cell) for cell in sorted(world["hazards"])],
        "trace": trace,
    }


def _evaluate_program(source, seeds):
    program = MeteredLispyProgram(source)
    metrics = {"score": 0, "food": 0, "steps": 0, "energy": 0}
    used = 0
    attempted_used = 0
    failures = 0
    peak_call_depth = 0
    for seed in seeds:
        episode = _simulate_episode(program, seed, include_trace=False)
        for key in metrics:
            metrics[key] += episode[key]
        used += episode["operations"]
        attempted_used += episode["attempted_operations"]
        peak_call_depth = max(peak_call_depth, episode["peak_call_depth"])
        if episode["termination"] == "fuel_exhausted" or episode[
            "termination"
        ].startswith("vm_error:"):
            failures += 1
    return {
        "metrics": metrics,
        "compute": {
            "budget": len(seeds) * OPERATION_LIMIT,
            "used": used,
            "attempted_used": attempted_used,
            "failures": failures,
            "peak_call_depth": peak_call_depth,
        },
    }


def _training_evaluation(source, base_seed):
    return _evaluate_program(source, _training_seeds(base_seed))


def _unified_diff(parent, child, generation, challenger=False, primitive=False):
    if parent == child:
        return ""
    suffix = "-challenger" if challenger else ""
    prefix = "primitive-" if primitive else ""
    parent_lines = [line + "\n" for line in parent.splitlines()]
    child_lines = [line + "\n" for line in child.splitlines()]
    return "".join(
        difflib.unified_diff(
            parent_lines,
            child_lines,
            fromfile=f"{prefix}generation-{generation - 1}.genome",
            tofile=f"{prefix}generation-{generation}{suffix}.genome",
            lineterm="\n",
        )
    )


# ---------------------------------------------------------------------------
# Bounded source mutation and reusable tool synthesis.
# ---------------------------------------------------------------------------


def _walk_paths(value, path=()):
    yield path, value
    if isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_paths(item, path + (index,))


def _replace_path(value, path, replacement):
    result = copy.deepcopy(value)
    target = result
    for index in path[:-1]:
        target = target[index]
    if path:
        target[path[-1]] = replacement
    else:
        result = replacement
    return result


def _mutate_expression(expression, rng, capabilities, mutation_type):
    paths = list(_walk_paths(expression))
    if mutation_type == "constant":
        candidates = [(path, value) for path, value in paths if type(value) is int]
        if not candidates:
            return None
        path, value = candidates[rng.randrange(len(candidates))]
        replacement = max(
            0,
            min(
                MAX_INTEGER_LITERAL,
                value + rng.choice((-3, -2, -1, 1, 2, 3)),
            ),
        )
        if replacement == value:
            replacement = 1 if value == 0 else value - 1
        return _replace_path(expression, path, replacement)
    if mutation_type == "sensor":
        candidates = [
            (path, value)
            for path, value in paths
            if isinstance(value, Symbol) and value in capabilities
        ]
        if not candidates or len(capabilities) < 2:
            return None
        path, value = candidates[rng.randrange(len(candidates))]
        replacements = [sensor for sensor in capabilities if sensor != value]
        return _replace_path(
            expression,
            path,
            Symbol(replacements[rng.randrange(len(replacements))]),
        )
    candidates = [
        (path, value)
        for path, value in paths
        if isinstance(value, Symbol) and value in ("+", "-", "*")
    ]
    if not candidates:
        return None
    path, value = candidates[rng.randrange(len(candidates))]
    replacements = [operator for operator in ("+", "-", "*") if operator != value]
    return _replace_path(
        expression,
        path,
        Symbol(replacements[rng.randrange(len(replacements))]),
    )


def _weighted_sensor(sensor, coefficient):
    if coefficient == 1:
        return Symbol(sensor)
    return [Symbol("*"), Symbol(sensor), coefficient]


def _tool_call(tool_id, capabilities):
    return [Symbol(tool_id), *[Symbol(sensor) for sensor in capabilities]]


def _policy_candidates(
    parent_expression,
    tools,
    capabilities,
    base_seed,
    generation,
    count,
    include_pairwise,
    domain,
):
    rng = random.Random(_derive_seed(base_seed, domain, generation))
    expressions = []
    seen = {_value_repr(parent_expression)}

    def add(expression):
        if expression is None:
            return
        source = _value_repr(expression)
        if source in seen:
            return
        candidate_program = _build_program(
            [tool["source"] for tool in tools],
            expression,
            capabilities,
        )
        try:
            MeteredLispyProgram(candidate_program, capabilities)
        except CreatureError:
            return
        seen.add(source)
        expressions.append(expression)

    hazard_weight = rng.choice((2, 3, 4, 6, 8))
    visit_weight = rng.choice((1, 2, 3, 4))
    if include_pairwise and "hazard" in capabilities and "visited" in capabilities:
        add(
            [
                Symbol("-"),
                parent_expression,
                [
                    Symbol("+"),
                    _weighted_sensor("hazard", hazard_weight),
                    _weighted_sensor("visited", visit_weight),
                ],
            ]
        )
    structural = (
        ("hazard", "-", hazard_weight),
        ("visited", "-", visit_weight),
        ("repeat", "-", rng.choice((1, 2, 3))),
        ("food", "+", rng.choice((1, 2, 3, 4))),
        ("distance", "-", rng.choice((1, 2, 3))),
        ("edge", "+", rng.choice((1, 2))),
    )
    for sensor, operator, coefficient in structural:
        if sensor in capabilities:
            add(
                [
                    Symbol(operator),
                    parent_expression,
                    _weighted_sensor(sensor, coefficient),
                ]
            )
            if len(expressions) >= count:
                return expressions[:count]
    mutation_types = ("constant", "sensor", "operator")
    attempts = 0
    while len(expressions) < count and attempts < 80:
        add(
            _mutate_expression(
                parent_expression,
                rng,
                capabilities,
                mutation_types[attempts % len(mutation_types)],
            )
        )
        attempts += 1
    while len(expressions) < count and attempts < 180:
        sensor = capabilities[rng.randrange(len(capabilities))]
        add(
            [
                Symbol(rng.choice(("+", "-"))),
                parent_expression,
                _weighted_sensor(sensor, rng.choice((1, 2, 3, 4, 6, 8))),
            ]
        )
        attempts += 1
    if len(expressions) != count:
        raise RuntimeError("could not construct the bounded policy tournament")
    return expressions


def _invention_candidates(
    parent_expression,
    tools,
    capabilities,
    base_seed,
    generation,
):
    if len(tools) >= MAX_TOOLS:
        return []
    rng = random.Random(_derive_seed(base_seed, "invention", generation))
    proposals = []
    for index in range(TOOL_CANDIDATES_PER_GENERATION):
        tool_id = f"tool-g{generation}-{index}"
        depends_on = []
        if index == 0 and "hazard" in capabilities and "visited" in capabilities:
            body = [
                Symbol("+"),
                _weighted_sensor("hazard", rng.choice((2, 3, 4, 6, 8))),
                _weighted_sensor("visited", rng.choice((1, 2, 3))),
            ]
            integration_operator = "-"
        elif tools and index == 1:
            dependency = tools[rng.randrange(len(tools))]["id"]
            depends_on = [dependency]
            sensor = capabilities[rng.randrange(len(capabilities))]
            body = [
                Symbol(rng.choice(("+", "-"))),
                _tool_call(dependency, capabilities),
                _weighted_sensor(sensor, rng.choice((1, 2, 3, 4))),
            ]
            integration_operator = rng.choice(("+", "-"))
        else:
            first = capabilities[rng.randrange(len(capabilities))]
            alternatives = [sensor for sensor in capabilities if sensor != first]
            second = (
                alternatives[rng.randrange(len(alternatives))]
                if alternatives
                else first
            )
            body = [
                Symbol(rng.choice(("+", "-"))),
                _weighted_sensor(first, rng.choice((1, 2, 3, 4))),
                _weighted_sensor(second, rng.choice((1, 2, 3, 4))),
            ]
            integration_operator = rng.choice(("+", "-"))
        definition_source = _value_repr(
            _definition_expression(tool_id, capabilities, body)
        )
        score_expression = [
            Symbol(integration_operator),
            parent_expression,
            _tool_call(tool_id, capabilities),
        ]
        candidate_tools = copy.deepcopy(tools)
        candidate_tools.append(
            {
                "id": tool_id,
                "generation": generation,
                "source": definition_source,
                "depends_on": depends_on,
                "definition_cost": None,
                "operation_cost": None,
            }
        )
        proposals.append(
            {
                "kind": "invention",
                "tool_id": tool_id,
                "definition_source": definition_source,
                "depends_on": depends_on,
                "score_expression": score_expression,
                "tools": candidate_tools,
            }
        )
    return proposals


def _probe_sensor_sets(capabilities):
    probes = []
    for mode in ("minimum", "middle", "maximum"):
        values = {}
        for sensor in capabilities:
            minimum, maximum = SENSOR_RANGES[sensor]
            if mode == "minimum":
                values[sensor] = minimum
            elif mode == "maximum":
                values[sensor] = maximum
            else:
                values[sensor] = (minimum + maximum) // 2
        probes.append(values)
    return probes


def _measure_tool_cost(program_source, tool_id):
    program = MeteredLispyProgram(program_source)
    definition_cost = None
    call_costs = []
    used = 0
    attempted_used = 0
    error = None
    for sensors in _probe_sensor_sets(program.capabilities):
        runtime = program.start(OPERATION_LIMIT)
        definition_cost = runtime.definition_costs[tool_id]
        before = runtime.meter.used
        try:
            runtime.call(
                tool_id,
                [sensors[sensor] for sensor in program.capabilities],
            )
        except CreatureError as caught:
            error = str(caught)
        used += runtime.meter.used
        attempted_used += runtime.meter.attempted
        call_costs.append(runtime.meter.used - before)
        if error is not None:
            break
    return definition_cost, max(call_costs), used, attempted_used, error


def _candidate_sort_key(candidate):
    evaluation = candidate["evaluation"]
    metrics = evaluation["metrics"]
    compute = evaluation["compute"]
    return (
        metrics["score"],
        metrics["food"],
        metrics["energy"],
        -metrics["steps"],
        -compute["used"],
        -len(candidate["program"]),
        candidate["program"],
    )


def _full_tournament(state, generation):
    capabilities = state["profile"]["capabilities"]
    parent = MeteredLispyProgram(state["program"], capabilities)
    tools = state["tools"]
    policy_count = MAX_CANDIDATES_PER_GENERATION - TOOL_CANDIDATES_PER_GENERATION
    candidates = [
        {
            "kind": "policy",
            "tool_id": None,
            "definition_source": None,
            "depends_on": [],
            "score_expression": expression,
            "tools": copy.deepcopy(tools),
        }
        for expression in _policy_candidates(
            parent.score_expression,
            tools,
            capabilities,
            state["seed"],
            generation,
            policy_count,
            include_pairwise=False,
            domain="tool-policy",
        )
    ]
    candidates.extend(
        _invention_candidates(
            parent.score_expression,
            tools,
            capabilities,
            state["seed"],
            generation,
        )
    )
    while len(candidates) < MAX_CANDIDATES_PER_GENERATION:
        existing = {_value_repr(item["score_expression"]) for item in candidates}
        for expression in _policy_candidates(
            parent.score_expression,
            tools,
            capabilities,
            state["seed"],
            generation,
            MAX_CANDIDATES_PER_GENERATION,
            include_pairwise=True,
            domain="tool-policy-fill",
        ):
            if _value_repr(expression) not in existing:
                candidates.append(
                    {
                        "kind": "policy",
                        "tool_id": None,
                        "definition_source": None,
                        "depends_on": [],
                        "score_expression": expression,
                        "tools": copy.deepcopy(tools),
                    }
                )
                existing.add(_value_repr(expression))
            if len(candidates) == MAX_CANDIDATES_PER_GENERATION:
                break
    candidates = candidates[:MAX_CANDIDATES_PER_GENERATION]

    invention_records = []
    valid = []
    for index, candidate in enumerate(candidates):
        error = None
        evaluation = None
        definition_cost = None
        operation_cost = None
        diagnostic_used = 0
        diagnostic_attempted = 0
        try:
            candidate["program"] = _build_program(
                [tool["source"] for tool in candidate["tools"]],
                candidate["score_expression"],
                capabilities,
            )
            evaluation = _training_evaluation(candidate["program"], state["seed"])
            if evaluation["compute"]["failures"]:
                error = (
                    f"runtime failure on {evaluation['compute']['failures']} "
                    "training episodes"
                )
            if candidate["kind"] == "invention" and error is None:
                definition_cost, operation_cost, diagnostic_used, diagnostic_attempted, error = _measure_tool_cost(
                    candidate["program"], candidate["tool_id"]
                )
                candidate["tools"][-1]["definition_cost"] = definition_cost
                candidate["tools"][-1]["operation_cost"] = operation_cost
        except CreatureError as caught:
            error = str(caught)
        candidate["evaluation"] = evaluation
        candidate["error"] = error
        candidate["definition_cost"] = definition_cost
        candidate["operation_cost"] = operation_cost
        candidate["diagnostic_used"] = diagnostic_used
        candidate["diagnostic_attempted"] = diagnostic_attempted
        if error is None:
            valid.append(candidate)
        if candidate["kind"] == "invention":
            invention_records.append(
                {
                    "id": f"inv-g{generation}-{index}",
                    "tool_id": candidate["tool_id"],
                    "generation": generation,
                    "source": candidate["definition_source"],
                    "depends_on": copy.deepcopy(candidate["depends_on"]),
                    "accepted": False,
                    "reason": "",
                    "definition_cost": definition_cost,
                    "operation_cost": operation_cost,
                    "diagnostic_compute": {
                        "used": diagnostic_used,
                        "attempted_used": diagnostic_attempted,
                        "budget": TOOL_PROBE_TRIALS * OPERATION_LIMIT,
                    },
                    "program_sha256": (
                        _genome_sha256(candidate["program"])
                        if "program" in candidate
                        else None
                    ),
                    "training": (
                        copy.deepcopy(evaluation["metrics"])
                        if evaluation is not None
                        else None
                    ),
                    "compute": (
                        copy.deepcopy(evaluation["compute"])
                        if evaluation is not None
                        else None
                    ),
                }
            )

    selection_compute = {
        "candidates": len(candidates),
        "budget": len(candidates) * TRAINING_TRIALS * OPERATION_LIMIT + DIAGNOSTIC_BUDGET,
        "used": sum(
            candidate["evaluation"]["compute"]["used"]
            for candidate in candidates
            if candidate["evaluation"] is not None
        ) + sum(candidate["diagnostic_used"] for candidate in candidates),
        "diagnostic_budget": DIAGNOSTIC_BUDGET,
        "diagnostic_used": sum(candidate["diagnostic_used"] for candidate in candidates),
        "attempted_used": sum(
            candidate["evaluation"]["compute"]["attempted_used"]
            for candidate in candidates
            if candidate["evaluation"] is not None
        ) + sum(candidate["diagnostic_attempted"] for candidate in candidates),
        "failed_episodes": sum(
            candidate["evaluation"]["compute"]["failures"]
            for candidate in candidates
            if candidate["evaluation"] is not None
        ),
    }
    reportable = [
        candidate for candidate in candidates if candidate["evaluation"] is not None
    ]
    if not reportable:
        raise RuntimeError("all bounded full-genome candidates failed before evaluation")
    best = max(valid if valid else reportable, key=_candidate_sort_key)
    accepted = (
        bool(valid)
        and best["evaluation"]["metrics"]["score"] > state["training"]["score"]
    )
    if accepted:
        current_program = best["program"]
        current_evaluation = best["evaluation"]
        current_tools = best["tools"]
        current_expression = _value_repr(best["score_expression"])
    else:
        current_program = state["program"]
        current_evaluation = {
            "metrics": state["training"],
            "compute": state["training_compute"],
        }
        current_tools = state["tools"]
        current_expression = parent.score_expression_source

    for record in invention_records:
        candidate = next(
            item for item in candidates if item.get("tool_id") == record["tool_id"]
        )
        if candidate["error"] is not None:
            record["reason"] = f"failed: {candidate['error']}"
        elif accepted and candidate is best:
            record["accepted"] = True
            record["reason"] = (
                f"accepted: training score {candidate['evaluation']['metrics']['score']} "
                f"exceeded parent {state['training']['score']}"
            )
        elif candidate is best:
            record["reason"] = (
                f"rejected: training score {candidate['evaluation']['metrics']['score']} "
                f"did not exceed parent {state['training']['score']}"
            )
        else:
            record["reason"] = (
                f"rejected: training score {candidate['evaluation']['metrics']['score']}; "
                f"selected candidate scored {best['evaluation']['metrics']['score']}"
            )

    return {
        "accepted": accepted,
        "program": current_program,
        "score_expression": current_expression,
        "evaluation": current_evaluation,
        "tools": copy.deepcopy(current_tools),
        "best_challenger": {
            "kind": best["kind"],
            "tool_id": best["tool_id"],
            "program": best["program"],
            "genome_sha256": _genome_sha256(best["program"]),
            "diff": _unified_diff(
                state["program"],
                best["program"],
                generation,
                challenger=not accepted,
            ),
            "training": copy.deepcopy(best["evaluation"]["metrics"]),
            "compute": copy.deepcopy(best["evaluation"]["compute"]),
            "fitness": best["evaluation"]["metrics"]["score"],
        },
        "inventions": invention_records,
        "mutations_tested": len(candidates),
        "selection_compute": selection_compute,
    }


def _primitive_tournament(state, generation):
    capabilities = state["profile"]["capabilities"]
    parent = MeteredLispyProgram(state["primitive_program"], capabilities)
    expressions = _policy_candidates(
        parent.score_expression,
        [],
        capabilities,
        state["seed"],
        generation,
        MAX_CANDIDATES_PER_GENERATION,
        include_pairwise=True,
        domain="primitive-policy",
    )
    candidates = []
    valid = []
    for expression in expressions:
        program = _build_program([], expression, capabilities)
        evaluation = _training_evaluation(program, state["seed"])
        candidate = {
            "program": program,
            "score_expression": _value_repr(expression),
            "evaluation": evaluation,
        }
        candidates.append(candidate)
        if evaluation["compute"]["failures"] == 0:
            valid.append(candidate)
    if not candidates:
        raise RuntimeError("all bounded primitive-only candidates failed")
    selection_compute = {
        "candidates": len(candidates),
        "budget": len(candidates) * TRAINING_TRIALS * OPERATION_LIMIT + DIAGNOSTIC_BUDGET,
        "used": sum(
            candidate["evaluation"]["compute"]["used"]
            for candidate in candidates
        ),
        "diagnostic_budget": DIAGNOSTIC_BUDGET,
        "diagnostic_used": 0,
        "attempted_used": sum(
            candidate["evaluation"]["compute"]["attempted_used"]
            for candidate in candidates
        ),
        "failed_episodes": sum(
            candidate["evaluation"]["compute"]["failures"]
            for candidate in candidates
        ),
    }
    best = max(valid if valid else candidates, key=_candidate_sort_key)
    accepted = (
        bool(valid)
        and best["evaluation"]["metrics"]["score"]
        > state["primitive_training"]["score"]
    )
    if accepted:
        return {
            "accepted": True,
            "program": best["program"],
            "score_expression": best["score_expression"],
            "evaluation": best["evaluation"],
            "best": best,
            "mutations_tested": len(expressions),
            "selection_compute": selection_compute,
        }
    return {
        "accepted": False,
        "program": state["primitive_program"],
        "score_expression": parent.score_expression_source,
        "evaluation": {
            "metrics": state["primitive_training"],
            "compute": state["primitive_training_compute"],
        },
        "best": best,
        "mutations_tested": len(expressions),
        "selection_compute": selection_compute,
    }


def _memory_for_state(state):
    lineage = state["lineage"]
    inventions = state["inventions"]
    return {
        "accepted_generations": sum(1 for entry in lineage[1:] if entry["accepted"]),
        "rejected_generations": sum(1 for entry in lineage[1:] if not entry["accepted"]),
        "primitive_accepted_generations": sum(
            1 for entry in lineage[1:] if entry["primitive_accepted"]
        ),
        "primitive_rejected_generations": sum(
            1 for entry in lineage[1:] if not entry["primitive_accepted"]
        ),
        "mutations_tested": sum(
            entry["mutations_tested"] + entry["primitive_mutations_tested"]
            for entry in lineage
        ),
        "inventions_tested": len(inventions),
        "inventions_accepted": sum(1 for item in inventions if item["accepted"]),
        "inventions_rejected": sum(
            1
            for item in inventions
            if not item["accepted"] and not item["reason"].startswith("failed:")
        ),
        "inventions_failed": sum(
            1 for item in inventions if item["reason"].startswith("failed:")
        ),
        "tools_inherited": len(state["tools"]),
        "selection_compute_budget": sum(
            entry["selection_compute"]["budget"]
            + entry["primitive_selection_compute"]["budget"]
            for entry in lineage
        ),
        "selection_compute_used": sum(
            entry["selection_compute"]["used"]
            + entry["primitive_selection_compute"]["used"]
            for entry in lineage
        ),
        "training_trials": TRAINING_TRIALS,
        "training_seed_set": _seed_set_id(
            "training", _training_seeds(state["seed"])
        ),
    }


def _founder_lineage_entry(evaluation):
    return {
        "generation": 0,
        "program": FOUNDER_PROGRAM,
        "genome_sha256": _genome_sha256(FOUNDER_PROGRAM),
        "parent_sha256": None,
        "diff": "",
        "accepted": True,
        "training": copy.deepcopy(evaluation["metrics"]),
        "training_compute": copy.deepcopy(evaluation["compute"]),
        "mutations_tested": 0,
        "parent_fitness": None,
        "current_fitness": evaluation["metrics"]["score"],
        "best_challenger": None,
        "tools": [],
        "invention_ids": [],
        "primitive_program": FOUNDER_PROGRAM,
        "primitive_genome_sha256": _genome_sha256(FOUNDER_PROGRAM),
        "primitive_diff": "",
        "primitive_accepted": True,
        "primitive_training": copy.deepcopy(evaluation["metrics"]),
        "primitive_training_compute": copy.deepcopy(evaluation["compute"]),
        "primitive_mutations_tested": 0,
        "selection_compute": {
            "candidates": 0,
            "budget": 0,
            "used": 0,
            "failed_episodes": 0,
        },
        "primitive_selection_compute": {
            "candidates": 0,
            "budget": 0,
            "used": 0,
            "failed_episodes": 0,
        },
    }


def _new_state(name, seed, build_comparison=True):
    profile = _validated_profile()
    if name != profile["name"]:
        raise CreatureError(
            f"name must match this creature profile: {profile['name']!r}"
        )
    evaluation = _training_evaluation(FOUNDER_PROGRAM, seed)
    state = {
        "schema": STATE_SCHEMA,
        "profile": profile,
        "name": name,
        "seed": seed,
        "generation": 0,
        "program": FOUNDER_PROGRAM,
        "genome_sha256": _genome_sha256(FOUNDER_PROGRAM),
        "score_expression": _value_repr(FOUNDER_EXPRESSION),
        "training": copy.deepcopy(evaluation["metrics"]),
        "training_compute": copy.deepcopy(evaluation["compute"]),
        "primitive_program": FOUNDER_PROGRAM,
        "primitive_genome_sha256": _genome_sha256(FOUNDER_PROGRAM),
        "primitive_score_expression": _value_repr(FOUNDER_EXPRESSION),
        "primitive_training": copy.deepcopy(evaluation["metrics"]),
        "primitive_training_compute": copy.deepcopy(evaluation["compute"]),
        "energy": round(evaluation["metrics"]["energy"] / TRAINING_TRIALS, 2),
        "limits": _limits(),
        "vm": _vm_metadata(),
        "memory": {},
        "lineage": [_founder_lineage_entry(evaluation)],
        "inventions": [],
        "tools": [],
        "comparison": None,
        "race": None,
        "egg": None,
        "resumed_from": None,
    }
    state["memory"] = _memory_for_state(state)
    if build_comparison:
        state["comparison"] = _build_comparison(state, COMPARISON_TRIALS)
    return state


def _advance_generation(state, build_comparison=True):
    generation = state["generation"] + 1
    full = _full_tournament(state, generation)
    primitive = _primitive_tournament(state, generation)
    parent_program = state["program"]
    parent_primitive = state["primitive_program"]
    entry = {
        "generation": generation,
        "program": full["program"],
        "genome_sha256": _genome_sha256(full["program"]),
        "parent_sha256": state["genome_sha256"],
        "diff": _unified_diff(parent_program, full["program"], generation),
        "accepted": full["accepted"],
        "training": copy.deepcopy(full["evaluation"]["metrics"]),
        "training_compute": copy.deepcopy(full["evaluation"]["compute"]),
        "mutations_tested": full["mutations_tested"],
        "parent_fitness": state["training"]["score"],
        "current_fitness": full["evaluation"]["metrics"]["score"],
        "best_challenger": full["best_challenger"],
        "tools": copy.deepcopy(full["tools"]),
        "invention_ids": [item["id"] for item in full["inventions"]],
        "primitive_program": primitive["program"],
        "primitive_genome_sha256": _genome_sha256(primitive["program"]),
        "primitive_diff": _unified_diff(
            parent_primitive,
            primitive["program"],
            generation,
            primitive=True,
        ),
        "primitive_accepted": primitive["accepted"],
        "primitive_training": copy.deepcopy(primitive["evaluation"]["metrics"]),
        "primitive_training_compute": copy.deepcopy(
            primitive["evaluation"]["compute"]
        ),
        "primitive_mutations_tested": primitive["mutations_tested"],
        "selection_compute": copy.deepcopy(full["selection_compute"]),
        "primitive_selection_compute": copy.deepcopy(
            primitive["selection_compute"]
        ),
    }
    state["generation"] = generation
    state["program"] = full["program"]
    state["genome_sha256"] = _genome_sha256(full["program"])
    state["score_expression"] = full["score_expression"]
    state["training"] = copy.deepcopy(full["evaluation"]["metrics"])
    state["training_compute"] = copy.deepcopy(full["evaluation"]["compute"])
    state["tools"] = copy.deepcopy(full["tools"])
    state["inventions"].extend(copy.deepcopy(full["inventions"]))
    state["primitive_program"] = primitive["program"]
    state["primitive_genome_sha256"] = _genome_sha256(primitive["program"])
    state["primitive_score_expression"] = primitive["score_expression"]
    state["primitive_training"] = copy.deepcopy(primitive["evaluation"]["metrics"])
    state["primitive_training_compute"] = copy.deepcopy(
        primitive["evaluation"]["compute"]
    )
    state["energy"] = round(state["training"]["energy"] / TRAINING_TRIALS, 2)
    state["lineage"].append(entry)
    state["memory"] = _memory_for_state(state)
    state["race"] = None
    if build_comparison:
        state["comparison"] = _build_comparison(state, COMPARISON_TRIALS)
    return state


# ---------------------------------------------------------------------------
# Equal-fuel comparisons, racing, and replay.
# ---------------------------------------------------------------------------


def _build_comparison(state, trials):
    seeds = _heldout_seeds(state["seed"], trials)
    primitive = _evaluate_program(state["primitive_program"], seeds)
    tools = _evaluate_program(state["program"], seeds)
    difference = tools["metrics"]["score"] - primitive["metrics"]["score"]
    winner = "tool_enabled" if difference > 0 else "primitive_only" if difference < 0 else "tie"
    return {
        "trials": trials,
        "seed_set": _seed_set_id("heldout", seeds),
        "seeds": seeds,
        "primitive_only": {
            "program": state["primitive_program"],
            "genome_sha256": state["primitive_genome_sha256"],
            "metrics": primitive["metrics"],
        },
        "tool_enabled": {
            "program": state["program"],
            "genome_sha256": state["genome_sha256"],
            "metrics": tools["metrics"],
            "tools": len(state["tools"]),
        },
        "compute_budget": trials * OPERATION_LIMIT,
        "compute_used": {
            "primitive_only": primitive["compute"]["used"],
            "tool_enabled": tools["compute"]["used"],
        },
        "compute_attempted": {
            "primitive_only": primitive["compute"]["attempted_used"],
            "tool_enabled": tools["compute"]["attempted_used"],
        },
        "peak_call_depth": {
            "primitive_only": primitive["compute"]["peak_call_depth"],
            "tool_enabled": tools["compute"]["peak_call_depth"],
        },
        "failures": {
            "primitive_only": primitive["compute"]["failures"],
            "tool_enabled": tools["compute"]["failures"],
        },
        "improvement": difference,
        "winner": winner,
    }


def _contestant_entries(state):
    entries = [state["lineage"][0]]
    entries.extend(entry for entry in state["lineage"][1:] if entry["accepted"])
    if entries[-1]["generation"] != state["generation"]:
        entries.append(state["lineage"][-1])
    if len(entries) <= MAX_RACE_CONTESTANTS:
        return entries
    indexes = {
        round(index * (len(entries) - 1) / (MAX_RACE_CONTESTANTS - 1))
        for index in range(MAX_RACE_CONTESTANTS)
    }
    return [entry for index, entry in enumerate(entries) if index in indexes]


def _replay(source, generation, seed):
    episode = _simulate_episode(source, seed, include_trace=True)
    return {
        "generation": generation,
        "seed": seed,
        "width": episode["width"],
        "height": episode["height"],
        "food": episode["food_locations"],
        "hazards": episode["hazards"],
        "trace": episode["trace"],
        "operations": episode["operations"],
        "attempted_operations": episode["attempted_operations"],
        "operation_limit": episode["operation_limit"],
        "peak_call_depth": episode["peak_call_depth"],
        "termination": episode["termination"],
    }


def _build_race(state, trials):
    seeds = _race_seeds(state["seed"], trials)
    founder = state["lineage"][0]
    ancestor = _evaluate_program(founder["program"], seeds)["metrics"]
    descendant = _evaluate_program(state["program"], seeds)["metrics"]
    contestants = [
        {
            "generation": entry["generation"],
            "genome_sha256": entry["genome_sha256"],
            "metrics": _evaluate_program(entry["program"], seeds)["metrics"],
        }
        for entry in _contestant_entries(state)
    ]
    return {
        "trials": trials,
        "seed_set": _seed_set_id("race", seeds),
        "seeds": seeds,
        "ancestor": ancestor,
        "descendant": descendant,
        "improvement": descendant["score"] - ancestor["score"],
        "contestants": contestants,
        "replays": [
            _replay(founder["program"], 0, seeds[0]),
            _replay(state["program"], state["generation"], seeds[0]),
        ],
    }


# ---------------------------------------------------------------------------
# Exact state and egg validation.
# ---------------------------------------------------------------------------


STATE_KEYS = {
    "schema",
    "profile",
    "name",
    "seed",
    "generation",
    "program",
    "genome_sha256",
    "score_expression",
    "training",
    "training_compute",
    "primitive_program",
    "primitive_genome_sha256",
    "primitive_score_expression",
    "primitive_training",
    "primitive_training_compute",
    "energy",
    "limits",
    "vm",
    "memory",
    "lineage",
    "inventions",
    "tools",
    "comparison",
    "race",
    "egg",
    "resumed_from",
}
ALGORITHMIC_STATE_KEYS = STATE_KEYS - {"race", "egg", "resumed_from", "comparison"}
METRIC_KEYS = {"score", "food", "steps", "energy"}
COMPUTE_KEYS = {"budget", "used", "attempted_used", "failures", "peak_call_depth"}
EGG_METADATA_KEYS = {"available", "file", "sha256", "generation"}
RESUMED_FROM_KEYS = {"sha256", "generation"}


def _validate_metrics(metrics, label, trials):
    if not isinstance(metrics, dict) or set(metrics) != METRIC_KEYS:
        raise CreatureError(f"{label} must contain score, food, steps and energy")
    _require_int(metrics["score"], f"{label}.score", -MAX_METRIC_ABS, MAX_METRIC_ABS)
    _require_int(metrics["food"], f"{label}.food", 0, trials * FOOD_COUNT)
    _require_int(metrics["steps"], f"{label}.steps", 0, trials * MAX_STEPS)
    _require_int(
        metrics["energy"],
        f"{label}.energy",
        0,
        trials * MAX_EPISODE_ENERGY,
    )


def _validate_compute(compute, label, trials):
    if not isinstance(compute, dict) or set(compute) != COMPUTE_KEYS:
        raise CreatureError(
            f"{label} must contain budget, used, attempted_used, failures and peak_call_depth"
        )
    expected_budget = trials * OPERATION_LIMIT
    if compute["budget"] != expected_budget:
        raise CreatureError(f"{label}.budget must equal {expected_budget}")
    _require_int(compute["used"], f"{label}.used", 0, expected_budget)
    _require_int(compute["failures"], f"{label}.failures", 0, trials)
    _require_int(
        compute["attempted_used"],
        f"{label}.attempted_used",
        compute["used"],
        compute["used"] + compute["failures"],
    )
    _require_int(
        compute["peak_call_depth"],
        f"{label}.peak_call_depth",
        0,
        MAX_CALL_DEPTH,
    )


def _prevalidate_state_sources(state, generation):
    capabilities = state["profile"]["capabilities"]
    programs = [
        ("program", state["program"], state["genome_sha256"]),
        (
            "primitive_program",
            state["primitive_program"],
            state["primitive_genome_sha256"],
        ),
    ]
    lineage = state["lineage"]
    if not isinstance(lineage, list) or len(lineage) != generation + 1:
        raise CreatureError("lineage must retain founder and every generation")
    for index, entry in enumerate(lineage):
        if not isinstance(entry, dict) or entry.get("generation") != index:
            raise CreatureError(f"lineage[{index}] has an invalid generation")
        programs.extend(
            [
                (
                    f"lineage[{index}].program",
                    entry.get("program"),
                    entry.get("genome_sha256"),
                ),
                (
                    f"lineage[{index}].primitive_program",
                    entry.get("primitive_program"),
                    entry.get("primitive_genome_sha256"),
                ),
            ]
        )
        if (
            not isinstance(entry.get("diff"), str)
            or not isinstance(entry.get("primitive_diff"), str)
            or len(entry["diff"]) > MAX_DIFF_CHARS
            or len(entry["primitive_diff"]) > MAX_DIFF_CHARS
        ):
            raise CreatureError(f"lineage[{index}] contains an invalid diff")
    for label, source, digest in programs:
        MeteredLispyProgram(source, capabilities)
        if _genome_sha256(source) != digest:
            raise CreatureError(f"{label} hash does not match its source")

    if not isinstance(state["tools"], list) or len(state["tools"]) > MAX_TOOLS:
        raise CreatureError("tools must be a bounded list")
    for tool in state["tools"]:
        if (
            not isinstance(tool, dict)
            or not isinstance(tool.get("source"), str)
            or len(tool["source"]) > MAX_DEFINITION_CHARS
        ):
            raise CreatureError("tool metadata or source is invalid")
    maximum_inventions = generation * TOOL_CANDIDATES_PER_GENERATION
    if (
        not isinstance(state["inventions"], list)
        or len(state["inventions"]) > maximum_inventions
    ):
        raise CreatureError("inventions exceed bounded generation history")
    for invention in state["inventions"]:
        if (
            not isinstance(invention, dict)
            or not isinstance(invention.get("source"), str)
            or len(invention["source"]) > MAX_DEFINITION_CHARS
            or not isinstance(invention.get("reason"), str)
            or len(invention["reason"]) > 300
        ):
            raise CreatureError("invention source or reason is invalid")


def _validate_artifacts(state):
    egg = state["egg"]
    if egg is not None:
        if not isinstance(egg, dict) or set(egg) != EGG_METADATA_KEYS:
            raise CreatureError("egg metadata has an invalid schema")
        if egg["available"] is not True or egg["file"] != "egg.json":
            raise CreatureError("stored egg metadata is invalid")
        _require_sha256(egg["sha256"], "egg.sha256")
        _require_int(egg["generation"], "egg.generation", 0, state["generation"])
    resumed = state["resumed_from"]
    if resumed is not None:
        if not isinstance(resumed, dict) or set(resumed) != RESUMED_FROM_KEYS:
            raise CreatureError("resumed_from has an invalid schema")
        _require_sha256(resumed["sha256"], "resumed_from.sha256")
        _require_int(
            resumed["generation"],
            "resumed_from.generation",
            0,
            state["generation"],
        )


def _validate_state(state):
    if not isinstance(state, dict) or set(state) != STATE_KEYS:
        raise CreatureError("creature state has an invalid schema")
    if state["schema"] != STATE_SCHEMA:
        raise CreatureError(f"unsupported creature state schema: {state['schema']!r}")
    profile = _validated_profile(state["profile"])
    if profile != state["profile"] or profile != _validated_profile():
        raise CreatureError("creature state profile is incompatible with this agent")
    name = _normalize_name(state["name"])
    if name != profile["name"]:
        raise CreatureError("creature state name does not match its profile")
    seed = _require_int(state["seed"], "seed", 0, (1 << 31) - 1)
    generation = _require_int(
        state["generation"], "generation", 0, MAX_TOTAL_GENERATIONS
    )
    if state["limits"] != _limits() or state["vm"] != _vm_metadata():
        raise CreatureError("creature limits or VM provenance do not match")
    _validate_metrics(state["training"], "training", TRAINING_TRIALS)
    _validate_compute(state["training_compute"], "training_compute", TRAINING_TRIALS)
    _validate_metrics(
        state["primitive_training"], "primitive_training", TRAINING_TRIALS
    )
    _validate_compute(
        state["primitive_training_compute"],
        "primitive_training_compute",
        TRAINING_TRIALS,
    )
    if (
        type(state["energy"]) not in (int, float)
        or not math.isfinite(state["energy"])
        or state["energy"] < 0
        or state["energy"] > MAX_EPISODE_ENERGY
    ):
        raise CreatureError("energy must be a finite bounded number")
    _prevalidate_state_sources(state, generation)

    expected = _new_state(name, seed, build_comparison=False)
    for _ in range(generation):
        _advance_generation(expected, build_comparison=False)
    for key in ALGORITHMIC_STATE_KEYS:
        if state[key] != expected[key]:
            raise CreatureError(
                f"creature state field {key} does not match deterministic history"
            )

    comparison = state["comparison"]
    if not isinstance(comparison, dict):
        raise CreatureError("comparison must be an object")
    trials = _require_int(
        comparison.get("trials"), "comparison.trials", 1, MAX_RACE_TRIALS
    )
    if comparison != _build_comparison(state, trials):
        raise CreatureError("comparison does not match equal-fuel held-out evaluation")
    if state["race"] is not None:
        race = state["race"]
        if not isinstance(race, dict):
            raise CreatureError("race must be an object or null")
        race_trials = _require_int(
            race.get("trials"), "race.trials", 1, MAX_RACE_TRIALS
        )
        if race != _build_race(state, race_trials):
            raise CreatureError("race or replay does not match held-out evaluation")
    _validate_artifacts(state)
    return state


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CreatureError(f"JSON contains duplicate key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value):
    raise CreatureError(f"JSON non-finite constant {value!r} is not allowed")


def _strict_json_loads(text, label):
    try:
        return json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except CreatureError:
        raise
    except (json.JSONDecodeError, UnicodeError, RecursionError, ValueError) as error:
        raise CreatureError(f"{label} is not valid bounded JSON: {error}") from None


def _canonical_json(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _pretty_json(value):
    return (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _build_egg(state):
    portable = copy.deepcopy(state)
    portable["egg"] = None
    payload = {
        "schema": EGG_SCHEMA,
        "profile": copy.deepcopy(portable["profile"]),
        "state": portable,
    }
    egg = {
        **payload,
        "checksum": hashlib.sha256(_canonical_json(payload)).hexdigest(),
        "integrity": "SHA-256 integrity checksum only; not a signature or authenticity proof.",
    }
    encoded = _canonical_json(egg)
    if len(encoded) > MAX_EGG_BYTES:
        raise CreatureError(f"egg exceeds the {MAX_EGG_BYTES}-byte limit")
    return egg, encoded


def _parse_egg(egg_json):
    if not isinstance(egg_json, str):
        raise CreatureError("egg_json must be a JSON string")
    try:
        encoded = egg_json.encode("utf-8")
    except UnicodeEncodeError as error:
        raise CreatureError(f"egg_json is not valid UTF-8 text: {error}") from None
    if len(encoded) > MAX_EGG_BYTES:
        raise CreatureError(f"egg_json exceeds the {MAX_EGG_BYTES}-byte limit")
    egg = _strict_json_loads(egg_json, "egg_json")
    expected_keys = {"schema", "profile", "state", "checksum", "integrity"}
    if not isinstance(egg, dict) or set(egg) != expected_keys:
        raise CreatureError("egg has an invalid schema")
    if egg["schema"] != EGG_SCHEMA:
        raise CreatureError(f"unsupported egg schema: {egg['schema']!r}")
    profile = _validated_profile(egg["profile"])
    current = _validated_profile()
    if profile != egg["profile"] or profile != current:
        raise CreatureError(
            f"egg profile {profile['id']!r} is incompatible with {current['id']!r}"
        )
    if not isinstance(egg["state"], dict) or egg["state"].get("profile") != profile:
        raise CreatureError("egg profile does not match its embedded state")
    if egg["integrity"] != (
        "SHA-256 integrity checksum only; not a signature or authenticity proof."
    ):
        raise CreatureError("egg integrity notice is invalid")
    _require_sha256(egg["checksum"], "egg.checksum")
    payload = {"schema": EGG_SCHEMA, "profile": profile, "state": egg["state"]}
    expected_checksum = hashlib.sha256(_canonical_json(payload)).hexdigest()
    if egg["checksum"] != expected_checksum:
        raise CreatureError("egg checksum mismatch")
    _validate_state(egg["state"])
    return egg["state"], hashlib.sha256(_canonical_json(egg)).hexdigest()


# ---------------------------------------------------------------------------
# Fixed-path atomic persistence and public snapshots.
# ---------------------------------------------------------------------------


class CreatureStore:
    def __init__(self, root):
        self.root = root
        self.state_path = root / "creature.json"
        self.lock_path = root / ".creature.lock"
        self.public_dir = root / "public"
        self.snapshot_path = self.public_dir / "snapshot.json"
        self.egg_path = self.public_dir / "egg.json"

    @contextmanager
    def locked(self):
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            os.chmod(self.root, 0o700)
        except PermissionError:
            pass
        descriptor = os.open(self.lock_path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            with os.fdopen(descriptor, "a+b", closefd=False) as lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        finally:
            os.close(descriptor)

    def _atomic_write(self, path, content, mode):
        path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.writing")
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            mode,
        )
        try:
            with os.fdopen(descriptor, "wb", closefd=False) as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
            os.chmod(temporary, mode)
            os.replace(temporary, path)
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            os.close(descriptor)
            if temporary.exists():
                temporary.unlink()

    def state_exists(self):
        return self.state_path.exists()

    def read_state(self):
        if self.state_path.stat().st_size > MAX_STATE_BYTES:
            raise CreatureError(f"creature state exceeds the {MAX_STATE_BYTES}-byte limit")
        try:
            text = self.state_path.read_bytes().decode("utf-8")
        except UnicodeDecodeError as error:
            raise CreatureError(f"creature state is not UTF-8: {error}") from None
        return _validate_state(_strict_json_loads(text, "creature state"))

    def write_state(self, state):
        encoded = _pretty_json(state)
        if len(encoded) > MAX_STATE_BYTES:
            raise CreatureError(f"creature state exceeds the {MAX_STATE_BYTES}-byte limit")
        self._atomic_write(self.state_path, encoded, 0o600)

    def write_snapshot(self, snapshot):
        self._atomic_write(self.snapshot_path, _pretty_json(snapshot), 0o644)

    def write_egg(self, encoded):
        self._atomic_write(self.egg_path, encoded, 0o644)

    def read_prepared_egg(self, egg_id):
        _require_sha256(egg_id, "egg_id")
        inbox = self.root / "inbox"
        path = inbox / f"{egg_id}.egg.json"
        if self.root.is_symlink() or inbox.is_symlink() or path.is_symlink() or not path.is_file():
            raise CreatureError("prepared egg is unavailable; stage it with the terrarium installer")
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(descriptor, "rb") as stream:
                raw = stream.read(MAX_EGG_BYTES + 1)
        except OSError as error:
            raise CreatureError(f"cannot read prepared egg: {error}") from None
        if len(raw) > MAX_EGG_BYTES:
            raise CreatureError(f"prepared egg exceeds the {MAX_EGG_BYTES}-byte limit")
        if hashlib.sha256(raw).hexdigest() != egg_id:
            raise CreatureError("prepared egg does not match its content id")
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise CreatureError(f"prepared egg is not UTF-8: {error}") from None


def _snapshot(state, store):
    profile = _validated_profile()
    if state is None:
        return {
            "schema": SNAPSHOT_SCHEMA,
            "exists": False,
            "profile": profile,
            "id": profile["id"],
            "capabilities": copy.deepcopy(profile["capabilities"]),
            "vm": _vm_metadata(),
            "inventions": [],
            "tools": [],
            "comparison": None,
        }
    egg = None
    if state["egg"] is not None:
        egg = copy.deepcopy(state["egg"])
        egg["available"] = store.egg_path.is_file()
        if egg["available"]:
            actual = hashlib.sha256(store.egg_path.read_bytes()).hexdigest()
            egg["available"] = actual == egg["sha256"]
    return {
        "schema": SNAPSHOT_SCHEMA,
        "exists": True,
        "profile": copy.deepcopy(state["profile"]),
        "id": state["profile"]["id"],
        "capabilities": copy.deepcopy(state["profile"]["capabilities"]),
        "name": state["name"],
        "seed": state["seed"],
        "generation": state["generation"],
        "program": state["program"],
        "genome_sha256": state["genome_sha256"],
        "energy": state["energy"],
        "training": copy.deepcopy(state["training"]),
        "limits": copy.deepcopy(state["limits"]),
        "memory": copy.deepcopy(state["memory"]),
        "lineage": copy.deepcopy(state["lineage"]),
        "race": copy.deepcopy(state["race"]),
        "egg": egg,
        "resumed_from": copy.deepcopy(state["resumed_from"]),
        "vm": copy.deepcopy(state["vm"]),
        "inventions": copy.deepcopy(state["inventions"]),
        "tools": copy.deepcopy(state["tools"]),
        "comparison": copy.deepcopy(state["comparison"]),
    }


def _snapshot_summary(snapshot):
    if not snapshot["exists"]:
        return {
            **snapshot,
            "public_file": f"{snapshot['id']}/public/snapshot.json",
        }
    race = snapshot["race"]
    race_summary = None
    if race is not None:
        race_summary = {
            "trials": race["trials"],
            "seed_set": race["seed_set"],
            "ancestor": race["ancestor"],
            "descendant": race["descendant"],
            "improvement": race["improvement"],
            "contestants": len(race["contestants"]),
            "replays": len(race["replays"]),
        }
    comparison = snapshot["comparison"]
    comparison_summary = {
        "trials": comparison["trials"],
        "seed_set": comparison["seed_set"],
        "primitive_only": comparison["primitive_only"]["metrics"],
        "tool_enabled": comparison["tool_enabled"]["metrics"],
        "compute_budget": comparison["compute_budget"],
        "compute_used": comparison["compute_used"],
        "peak_call_depth": comparison["peak_call_depth"],
        "failures": comparison["failures"],
        "improvement": comparison["improvement"],
        "winner": comparison["winner"],
    }
    tools = [
        {
            "id": tool["id"],
            "generation": tool["generation"],
            "depends_on": tool["depends_on"],
            "definition_cost": tool["definition_cost"],
            "operation_cost": tool["operation_cost"],
        }
        for tool in snapshot["tools"]
    ]
    return {
        "schema": SNAPSHOT_SCHEMA,
        "exists": True,
        "profile": snapshot["profile"],
        "id": snapshot["id"],
        "capabilities": snapshot["capabilities"],
        "name": snapshot["name"],
        "seed": snapshot["seed"],
        "generation": snapshot["generation"],
        "program": snapshot["program"],
        "genome_sha256": snapshot["genome_sha256"],
        "energy": snapshot["energy"],
        "training": snapshot["training"],
        "limits": snapshot["limits"],
        "memory": snapshot["memory"],
        "lineage": {
            "entries": len(snapshot["lineage"]),
            "accepted": snapshot["memory"]["accepted_generations"],
            "rejected": snapshot["memory"]["rejected_generations"],
        },
        "race": race_summary,
        "egg": snapshot["egg"],
        "resumed_from": snapshot["resumed_from"],
        "vm": snapshot["vm"],
        "inventions": {
            "tested": len(snapshot["inventions"]),
            "accepted": snapshot["memory"]["inventions_accepted"],
            "failed": snapshot["memory"]["inventions_failed"],
        },
        "tools": tools,
        "comparison": comparison_summary,
        "public_file": f"{snapshot['id']}/public/snapshot.json",
    }


class GenomeCreatureAgent(BasicAgent):
    def __init__(self):
        self.profile = _validated_profile()
        self.name = self.profile["agent_name"]
        self.metadata = {
            "name": self.name,
            "description": (
                f"Evolves {self.profile['name']}, a bounded grid simulation whose "
                "pinned Lisppy genome invents and inherits real reusable tools. "
                f"Available sensors: {', '.join(self.profile['capabilities'])}. "
                "Use hatch, evolve, race, export_egg, resume, or status. Evolution "
                "includes invention and an equal-fuel primitive-only comparison. "
                "This is a deterministic simulation and makes no sentience claim."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "status",
                            "hatch",
                            "evolve",
                            "race",
                            "export_egg",
                            "resume",
                        ],
                        "description": "Operation to perform. Defaults to status.",
                    },
                    "name": {
                        "type": "string",
                        "description": (
                            "Display name for hatch; must match profile name "
                            f"{self.profile['name']!r}."
                        ),
                    },
                    "seed": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": (1 << 31) - 1,
                        "description": "Deterministic founder seed. Defaults to 41.",
                    },
                    "generations": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": MAX_GENERATIONS_PER_ACTION,
                        "description": "Evolution and invention generations. Defaults to 12.",
                    },
                    "expected_generation": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": MAX_TOTAL_GENERATIONS,
                        "description": "Optional optimistic concurrency guard.",
                    },
                    "trials": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": MAX_RACE_TRIALS,
                        "description": "Held-out race courses. Defaults to 12.",
                    },
                    "egg_json": {
                        "type": "string",
                        "description": "Complete small exported egg JSON for resume; use egg_id for a staged full-history egg.",
                    },
                    "egg_id": {
                        "type": "string",
                        "description": "SHA-256 id of an egg staged in this creature's inbox by the installer. Exclusive with egg_json; no path or source code.",
                    },
                },
                "required": [],
                "additionalProperties": False,
            },
        }
        self.store = CreatureStore(_data_base() / self.profile["id"])
        super().__init__(name=self.name, metadata=self.metadata)

    def _ok(self, action, state):
        snapshot = _snapshot(state, self.store)
        self.store.write_snapshot(snapshot)
        result = {
            "status": "ok",
            "action": action,
            "snapshot": _snapshot_summary(snapshot),
        }
        if state is not None:
            result["generation"] = state["generation"]
        return json.dumps(result, sort_keys=True, separators=(",", ":"))

    def _status(self):
        with self.store.locked():
            if not self.store.state_exists():
                return self._ok("status", None)
            return self._ok("status", self.store.read_state())

    def _hatch(self, name, seed):
        name = _normalize_name(name)
        seed = _require_int(seed, "seed", 0, (1 << 31) - 1)
        with self.store.locked():
            if self.store.state_exists():
                raise CreatureError("creature already exists; hatch refuses to overwrite it")
            state = _new_state(name, seed)
            self.store.write_state(state)
            return self._ok("hatch", state)

    def _evolve(self, generations, expected_generation):
        generations = _require_int(
            generations,
            "generations",
            1,
            MAX_GENERATIONS_PER_ACTION,
        )
        if expected_generation is not None:
            expected_generation = _require_int(
                expected_generation,
                "expected_generation",
                0,
                MAX_TOTAL_GENERATIONS,
            )
        with self.store.locked():
            if not self.store.state_exists():
                raise CreatureError("no creature exists; hatch or resume one first")
            state = self.store.read_state()
            if (
                expected_generation is not None
                and expected_generation != state["generation"]
            ):
                raise CreatureError(
                    f"expected_generation mismatch: expected {expected_generation}, current {state['generation']}"
                )
            if state["generation"] + generations > MAX_TOTAL_GENERATIONS:
                raise CreatureError(
                    f"evolution would exceed the {MAX_TOTAL_GENERATIONS}-generation history cap"
                )
            for _ in range(generations):
                _advance_generation(state, build_comparison=False)
            state["comparison"] = _build_comparison(state, COMPARISON_TRIALS)
            self.store.write_state(state)
            return self._ok("evolve", state)

    def _race(self, trials):
        trials = _require_int(trials, "trials", 1, MAX_RACE_TRIALS)
        with self.store.locked():
            if not self.store.state_exists():
                raise CreatureError("no creature exists; hatch or resume one first")
            state = self.store.read_state()
            state["race"] = _build_race(state, trials)
            state["comparison"] = _build_comparison(state, trials)
            self.store.write_state(state)
            return self._ok("race", state)

    def _export_egg(self):
        with self.store.locked():
            if not self.store.state_exists():
                raise CreatureError("no creature exists; hatch or resume one first")
            state = self.store.read_state()
            _, encoded = _build_egg(state)
            egg_sha256 = hashlib.sha256(encoded).hexdigest()
            self.store.write_egg(encoded)
            state["egg"] = {
                "available": True,
                "file": "egg.json",
                "sha256": egg_sha256,
                "generation": state["generation"],
            }
            self.store.write_state(state)
            return self._ok("export_egg", state)

    def _resume(self, egg_json, egg_id=None):
        with self.store.locked():
            if self.store.state_exists():
                raise CreatureError("creature already exists; resume refuses to overwrite it")
            if egg_id is not None:
                if egg_json is not None:
                    raise CreatureError("resume accepts egg_id or egg_json, not both")
                egg_json = self.store.read_prepared_egg(egg_id)
            portable, egg_sha256 = _parse_egg(egg_json)
            state = copy.deepcopy(portable)
            state["egg"] = None
            state["resumed_from"] = {
                "sha256": egg_sha256,
                "generation": state["generation"],
            }
            self.store.write_state(state)
            return self._ok("resume", state)

    def perform(self, **kwargs):
        action = kwargs.get("action", "status")
        valid_actions = {
            "status",
            "hatch",
            "evolve",
            "race",
            "export_egg",
            "resume",
        }
        if not isinstance(action, str) or action not in valid_actions:
            return json.dumps(
                {
                    "status": "error",
                    "error": "action must be one of status, hatch, evolve, race, export_egg or resume",
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        try:
            _load_runtime()
            if action == "status":
                return self._status()
            if action == "hatch":
                return self._hatch(
                    kwargs.get("name", self.profile["name"]),
                    kwargs.get("seed", 41),
                )
            if action == "evolve":
                return self._evolve(
                    kwargs.get("generations", 12),
                    kwargs.get("expected_generation"),
                )
            if action == "race":
                return self._race(kwargs.get("trials", 12))
            if action == "export_egg":
                return self._export_egg()
            return self._resume(kwargs.get("egg_json"), kwargs.get("egg_id"))
        except CreatureError as error:
            return json.dumps(
                {"status": "error", "error": str(error)},
                sort_keys=True,
                separators=(",", ":"),
            )
