"""Exact Markdown entity records, with optional literal-source corroboration."""

from __future__ import annotations

import ast
import json
import re
import string
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from tools.studio_privacy import has_unapproved_email


class KnowledgeTableError(ValueError):
    pass


class UnverifiableTable(KnowledgeTableError):
    """A curated presentation cannot be proved against an available literal."""


class LiteralDisagreement(KnowledgeTableError):
    pass


IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:[-_][A-Za-z0-9]+)+")
ENTITY_HEADERS = {
    "id", "key", "code", "sku", "name", "client", "customer", "vendor", "supplier", "employee",
    "consultant", "competitor", "facility", "provider", "trader", "trade", "algorithm", "contract",
    "permit", "inspection", "inspector", "invoice", "entry", "inquiry", "project", "station", "line",
    "shift", "holiday", "sourcekey",
}
RULE_HEADING = re.compile(
    r"\b(?:polic(?:y|ies)|rules?|thresholds?|statutory|routing|rates?|configured\s+.+rates|"
    r"fee\s+schedule|(?:review|utilization)\s+targets?|reference\s+standards)\b|"
    r"locked[- ](?:case|preview)|required\s+response|"
    r"\b(?:exact|output|evidence|preview|calculation).*\bcontract\b|"
    r"\bbottleneck\b.*\btakt\b",
    re.I,
)
CURRENCY = re.compile(r"([+-]?)\$([+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)")
PERCENT = re.compile(r"([+-]?(?:\d+(?:\.\d+)?|\.\d+))%")
NUMBER = re.compile(r"[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
BULLET = re.compile(r"^-\s+(?:\*\*)?(.+?)(?::\*\*|:\s*|\*\*:)\s*(.*)$")


@dataclass
class KnowledgeRecords:
    selector: str
    section: str
    section_path: tuple[str, ...]
    form: str
    headers: list[str]
    fields: list[str]
    rows: list[dict[str, Any]]
    spans: list[tuple[int, int]]
    formats: dict[str, str] = field(default_factory=dict)
    literal_rows: int = 0
    literal_sources: list[str] = field(default_factory=list)
    omitted_columns: list[dict[str, str]] = field(default_factory=list)


@dataclass
class KnowledgeParse:
    records: list[KnowledgeRecords]
    retained: list[dict[str, str]]


def plain(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        value = value[1:-1]
    if len(value) >= 4 and value.startswith("**") and value.endswith("**"):
        value = value[2:-2]
    return value.strip()


def field_name(label: str) -> str:
    label = re.sub(r",?\s+in\s+(?:source\s+)?order\b", "", plain(label), flags=re.I)
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def split_pipe(line: str) -> list[str]:
    cells, current = [], []
    for character in line.strip():
        if character == "|":
            backslashes = len(current) - len("".join(current).rstrip("\\"))
            if backslashes % 2:
                current.pop()
                current.append("|")
            else:
                cells.append("".join(current).strip())
                current = []
        else:
            current.append(character)
    cells.append("".join(current).strip())
    if cells and cells[0] == "":
        cells.pop(0)
    if cells and cells[-1] == "" and line.rstrip().endswith("|"):
        cells.pop()
    return [plain(value) for value in cells]


def separator(line: str) -> bool:
    return "|" in line and all(re.fullmatch(r":?-+:?", value) for value in split_pipe(line))


def numeric(value: str) -> int | float:
    number = Decimal(value.replace(",", ""))
    return int(number) if number == number.to_integral() else float(number)


def entity_key(header: str, values: list[str]) -> bool:
    key = re.sub(r"[^a-z0-9]", "", plain(header).lower())
    if not values or any(not value for value in values):
        return False
    return (key in ENTITY_HEADERS or key.endswith(("id", "code", "key"))
            or (all(IDENTIFIER.fullmatch(value) for value in values)
                and key not in {"case", "operation", "rule", "requirement", "metric", "factor"}))


def convert_rows(headers: list[str], raw: list[list[str]]) -> tuple[list[str], list[dict], dict[str, str]]:
    fields = [field_name(header) for header in headers]
    if not all(fields) or len(set(fields)) != len(fields):
        raise KnowledgeTableError("table headers must identify unique fields")
    formats = {}
    percent_fields = {field for i, field in enumerate(fields) if i > 0
                      and all(PERCENT.fullmatch(row[i]) for row in raw)}
    rows = []
    for values in raw:
        row = {}
        for index, (name, value) in enumerate(zip(fields, values)):
            money = CURRENCY.fullmatch(value)
            if name in percent_fields:
                row[name] = numeric(PERCENT.fullmatch(value)[1])
                formats[name] = "percent1"
            elif money and index > 0:
                row[name] = numeric(money[1] + money[2])
                formats[name] = "currency"
            else:
                row[name] = value
        rows.append(row)
    return fields, rows, formats


def record_heading(title: str) -> tuple[str, str, str] | None:
    match = re.match(r"^(?:Synthetic (?:encounter|patient record|request):\s*)?"
                     r"([A-Za-z][A-Za-z0-9]*(?:[-_][A-Za-z0-9]+)+)(?:\s*(?:—|--|/)\s*(.*))?$", title)
    if not match:
        return None
    ident, name = match[1], (match[2] or "").strip()
    alias_match = re.search(r"\s*\(`([^`]+)`\)$", name)
    alias = alias_match[1] if alias_match else ""
    if alias_match:
        name = name[:alias_match.start()].strip()
    return ident, name, alias


def parse_knowledge(path: Path) -> KnowledgeParse:
    lines = path.read_text(encoding="utf-8").splitlines()
    stack: list[tuple[int, str]] = []
    current: tuple[str, ...] = ()
    records, retained = [], []
    table_counts: dict[tuple[str, ...], int] = {}
    heading_records: dict[tuple[str, ...], list[tuple[list[str], list[str], tuple[int, int]]]] = {}
    bad_heading_groups: set[tuple[str, ...]] = set()
    fence = False
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
            index += 1
            continue
        if fence:
            index += 1
            continue
        heading = HEADING.fullmatch(line)
        if heading:
            level, title = len(heading[1]), heading[2]
            while stack and stack[-1][0] >= level:
                stack.pop()
            parent = tuple(name for depth, name in stack if depth > 1)
            stack.append((level, title))
            current = tuple(name for depth, name in stack if depth > 1)
            identity = record_heading(title) if level >= 2 and not RULE_HEADING.search(title) else None
            if identity:
                group = parent or (re.sub(r":.*", "", title) if title.startswith("Synthetic ") else "Entity records",)
                ident, name, alias = identity
                headers, values = ["ID"], [ident]
                if name:
                    headers.append("Name")
                    values.append(name)
                if alias:
                    headers.append("Alias")
                    values.append(alias)
                end, last_field = index + 1, index + 1
                while end < len(lines) and not HEADING.fullmatch(lines[end]):
                    bullet = BULLET.fullmatch(lines[end])
                    if bullet:
                        headers.append(plain(bullet[1]))
                        values.append(plain(bullet[2]))
                        last_field = end + 1
                    elif lines[end].startswith(("  ", "\t")) and lines[end].strip():
                        bad_heading_groups.add(group)
                    end += 1
                if len(headers) > (3 if alias else 2 if name else 1):
                    heading_records.setdefault(group, []).append((headers, values, (index, last_field)))
                else:
                    bad_heading_groups.add(group)
            index += 1
            continue
        if "|" in line and index + 1 < len(lines) and separator(lines[index + 1]):
            headers = split_pipe(line)
            if len(headers) != len(split_pipe(lines[index + 1])):
                raise KnowledgeTableError(f"{path.name}:{index + 1}: table header/separator widths differ")
            raw, end = [], index + 2
            while end < len(lines) and "|" in lines[end] and lines[end].strip():
                values = split_pipe(lines[end])
                if len(values) != len(headers):
                    raise KnowledgeTableError(f"{path.name}:{end + 1}: table row has {len(values)} cells; "
                                              f"expected {len(headers)}")
                raw.append(values)
                end += 1
            table_counts[current] = table_counts.get(current, 0) + 1
            section = current[-1] if current else "Untitled table"
            selector = " / ".join(current) + f" [table {table_counts[current]}]"
            if RULE_HEADING.search(" / ".join(current)):
                retained.append({"section": section, "reason": "rule/policy/contract table"})
            elif raw and entity_key(headers[0], [row[0] for row in raw]):
                fields, rows, formats = convert_rows(headers, raw)
                records.append(KnowledgeRecords(selector, section, current, "pipe-table", headers, fields,
                                                 rows, [(index, end)], formats))
            else:
                retained.append({"section": section, "reason": "not an entity-keyed table"})
            index = end
            continue
        index += 1
    for group, entries in heading_records.items():
        section = group[-1]
        keys = [{field_name(name) for name in headers} for headers, _, _ in entries]
        if (group in bad_heading_groups or RULE_HEADING.search(" / ".join(group))
                or any(key != keys[0] for key in keys) or len(keys[0]) != len(entries[0][0])):
            retained.append({"section": section, "reason": "heading records are nested or have unequal field sets"})
            continue
        headers = entries[0][0]
        fields = [field_name(name) for name in headers]
        raw = []
        for names, values, _ in entries:
            by_name = {field_name(name): value for name, value in zip(names, values)}
            raw.append([by_name[name] for name in fields])
        fields, rows, formats = convert_rows(headers, raw)
        records.append(KnowledgeRecords(" / ".join(group) + " [headings]", section, group, "heading-records",
                                        headers, fields, rows, [span for _, _, span in entries], formats))
    return KnowledgeParse(sorted(records, key=lambda item: item.spans[0][0]), retained)


def _literal_containers(source: Path) -> list[tuple[str, Any]]:
    tree = ast.parse(source.read_text(encoding="utf-8"))
    containers = []
    seen = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            label = targets[0].id if targets and isinstance(targets[0], ast.Name) else f"literal-{node.lineno}"
        elif isinstance(node, ast.Dict):
            value, label = node, f"literal-{node.lineno}"
        else:
            continue
        try:
            literal = ast.literal_eval(value)
        except (ValueError, TypeError, SyntaxError):
            continue
        if not isinstance(literal, (dict, list, tuple)):
            continue
        signature = repr(literal)
        if signature not in seen:
            seen.add(signature)
            containers.append((label, literal))
    return containers


def _entities(value: Any, wanted: set[str], label: str, parent_key: str = ""):
    if isinstance(value, dict):
        identities = {str(v) for key, v in value.items() if isinstance(v, (str, int))
                      and (field_name(str(key)) in {"id", "name", "client", "customer", "title"}
                           or field_name(str(key)).endswith("_id"))}
        if parent_key in wanted or identities & wanted:
            if not ({"operation", "data_source"} & set(value)) and len(value) >= 2:
                yield label, value, parent_key
        for key, child in value.items():
            if str(key) in wanted and not isinstance(child, dict):
                yield label + "." + str(key), {field_name(label.split(".")[-1]): child}, str(key)
            yield from _entities(child, wanted, label + "." + str(key), str(key))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _entities(child, wanted, f"{label}[{index}]")


def _fields(value: Any, path: str = ""):
    if path:
        yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _fields(child, f"{path}.{key}" if path else str(key))


def _tokens(label: str) -> set[str]:
    value = field_name(label).replace("out_of_pocket", "oop")
    tokens = value.split("_")
    ignored = {"exact", "synthetic", "fictional", "source", "recorded", "complete", "in", "order", "of",
               "shown", "profile", "coded"}
    aliases = {"maximum": "max", "minimum": "min", "description": "desc", "percentage": "pct", "state": "status"}
    words = {aliases.get(token, token) for token in tokens if token and token not in ignored}
    return {word[:-1] if word.endswith("s") and word not in {"nps", "status", "analysis", "business"}
            and not word.endswith("ss") else word for word in words}


def _score(header: str, path: str) -> int:
    h, full, leaf = _tokens(header), _tokens(path.replace(".", "_")), _tokens(path.split(".")[-1])
    if h == full or h == leaf:
        return 100
    if h == {"id"} and path == "$key":
        return 100
    if h and h < leaf and leaf - h <= {"id", "pct", "score", "name", "date", "trend", "year", "month", "week", "day", "hour"}:
        return 85
    if h and leaf and leaf <= h:
        return 70
    aliases = {
        "vendor": {"name"}, "supplier": {"name"}, "consultant": {"name"}, "client": {"name"},
        "competitor": {"name"}, "inspector": {"name"}, "holiday": {"name"}, "station": {"name"},
        "contact_role": {"contact"}, "patient_label": {"patient"}, "display_label": {"name", "label"},
        "display_heading": {"label", "heading", "name"}, "fixed_date_text": {"date"},
    }
    if leaf & aliases.get(field_name(header), set()):
        return 60
    return 0


def _proof_value(spec: dict, fields: dict[str, Any]) -> tuple[Any, str] | None:
    paths = spec.get("fields") or [spec.get("field")]
    if any(path not in fields for path in paths):
        return None
    values = [fields[path] for path in paths]
    if "template" in spec:
        for _, name, _, conversion in string.Formatter().parse(spec["template"]):
            if name is not None and (not name.isdigit() or int(name) >= len(values) or conversion):
                raise KnowledgeTableError("literal proof templates may reference numbered source fields only")
        return spec["template"].format(*values), "$template"
    if "op" in spec:
        if len(values) != 2 or any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in values):
            raise KnowledgeTableError("literal arithmetic proofs require exactly two numeric source fields")
        a, b = values
        if spec["op"] == "subtract":
            result = a - b
        elif spec["op"] == "positive_difference":
            result = max(a - b, 0)
        elif spec["op"] == "percent" and b != 0:
            result = a / b * 100
        else:
            raise KnowledgeTableError("unsupported or undefined literal arithmetic proof")
        return round(result, spec["round"]) if "round" in spec else result, "$arithmetic"
    value = values[0]
    if "index" in spec:
        if not isinstance(value, (list, tuple)) or not 0 <= spec["index"] < len(value):
            raise KnowledgeTableError("literal proof index is outside its source sequence")
        value = value[spec["index"]]
    if "empty" in spec and (value is None or value == ""):
        value = spec["empty"]
    if "zero" in spec and value == 0 and not isinstance(value, bool):
        value = spec["zero"]
    if spec.get("transform") == "humanize":
        value = str(value).replace("_", " ").title()
    return value, str(paths[0])


def _equal_cell(actual: Any, literal: Any, path: str, format_name: str | None) -> bool:
    if isinstance(literal, bool):
        return str(actual).lower() in ({"yes", "true"} if literal else {"no", "false"})
    if literal is None:
        return str(actual).lower() in {"", "none", "not applicable", "n/a"}
    if isinstance(literal, (int, float)):
        if isinstance(actual, (int, float)) and not isinstance(actual, bool):
            return Decimal(str(actual)) == Decimal(str(literal))
        text = str(actual)
        if NUMBER.fullmatch(text):
            return Decimal(text.replace(",", "")) == Decimal(str(literal))
        match = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)\s*(days?|weeks?|years?|hours?|months?|x)", text)
        if match:
            unit = match[2].rstrip("s")
            path_words = _tokens(path)
            if unit in {word.rstrip("s") for word in path_words} or (unit == "x" and path_words & {"premium", "factor", "multiplier"}):
                return Decimal(match[1]) == Decimal(str(literal))
        return False
    if isinstance(literal, (list, tuple)) and all(isinstance(v, (str, int, float)) for v in literal):
        if not literal:
            return str(actual).lower() in {"", "none", "not applicable"}
        return str(actual) in {"; ".join(map(str, literal)), ", ".join(map(str, literal)),
                               json.dumps(literal, separators=(",", ":")), json.dumps(literal)}
    if isinstance(literal, dict):
        return str(actual) in {json.dumps(literal, separators=(",", ":")), json.dumps(literal)}
    expected, observed = str(literal).strip(), str(actual).strip()
    return observed == expected or observed.casefold() == expected.replace("_", " ").casefold()


def cross_check(table: KnowledgeRecords, source: Path, field_overrides: dict[str, Any] | None = None) -> None:
    containers = _literal_containers(source)
    checked, sources = 0, set()
    for row in table.rows:
        identity = str(row[table.fields[0]])
        wanted = {identity} | {str(value) for key, value in row.items() if key == "id" or key.endswith("_id")}
        entities = []
        signatures = set()
        for label, value in containers:
            for record in _entities(value, wanted, label):
                signature = repr(record[1:])
                if signature not in signatures:
                    signatures.add(signature)
                    entities.append(record)
        if not entities:
            continue
        for field, header in zip(table.fields, table.headers):
            observed = row[field]
            override = (field_overrides or {}).get(header, (field_overrides or {}).get(field))
            options = []
            for label, entity, parent_key in entities:
                fields = list(_fields(entity))
                if parent_key:
                    fields.append(("$key", parent_key))
                if isinstance(override, dict):
                    proof = _proof_value(override, dict(fields))
                    if proof is not None:
                        options.append((200, label, proof[0], proof[1]))
                else:
                    for path, value in fields:
                        score = 200 if override == path else (0 if override else _score(header, path))
                        if field == table.fields[0] and (str(value) == identity) and (
                            path in {"id", "name", "$key"} or path.endswith("_id")
                        ):
                            score = max(score, 150)
                        if score:
                            options.append((score, label, value, path))
            if not options:
                raise UnverifiableTable(f"{table.section}: {identity}.{header} has no unambiguous literal field")
            score = max(option[0] for option in options)
            best = [option for option in options if option[0] == score]
            matching = [option for option in best if _equal_cell(observed, option[2], option[3], table.formats.get(field))]
            if not matching:
                if any(isinstance(option[2], (list, tuple, dict)) for option in best):
                    raise UnverifiableTable(f"{table.section}: {identity}.{header} is a curated composite, not a literal field")
                raise LiteralDisagreement(f"{table.section}: {identity}.{header} disagrees with the agent literal")
            named = [option[1].split(".")[0].split("[")[0] for option in matching
                     if not option[1].startswith("literal-")]
            sources.update(named or [option[1] for option in matching])
        checked += 1
    table.literal_rows = checked
    table.literal_sources = sorted(sources)


def omit_private_columns(table: KnowledgeRecords) -> None:
    for field, header in zip(table.fields, table.headers):
        if any(has_unapproved_email(str(row[field])) for row in table.rows):
            if field == table.fields[0]:
                raise UnverifiableTable(f"{table.section}: entity keys contain non-reserved email addresses")
            table.omitted_columns.append({"name": header, "from": field, "reason": "email privacy gate"})
            for row in table.rows:
                row.pop(field)
    omitted = {item["from"] for item in table.omitted_columns}
    table.fields = [name for name in table.fields if name not in omitted]
    table.headers = [header for header in table.headers if field_name(header) not in omitted]
    table.formats = {name: value for name, value in table.formats.items() if name not in omitted}
