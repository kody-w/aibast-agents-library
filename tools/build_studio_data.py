#!/usr/bin/env python3
"""Build a workshop's studio data: its synthetic records as CSV files, one per SharePoint list.

    python3 tools/build_studio_data.py emission-tracking          # write solutions/<slug>/studio/data/*.csv
    python3 tools/build_studio_data.py --check                    # every studio package: CSVs current, records intact

The records come from the portable agent itself: the module-level record sets named in
solutions/<slug>/studio/data/schema.json, read with ast.literal_eval (the agent is never imported or run). They must
equal the JSON blocks of the workshop's synthetic-records knowledge file, so the lists, the knowledge the manual
workshop uploads and the agent's own answers all rest on the same records. Every field of every record must land in
a column; a field the schema leaves out is an error, not a silent omission.
"""

import argparse
import ast
import csv
import io
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "aibast-studio-data/1.0"
TYPES = {"text", "number", "date"}
COLUMN = re.compile(r"[A-Za-z][A-Za-z0-9]{0,31}")


class StudioDataError(Exception):
    pass


def record_sets(source_path, aliases=None):
    """{NAME: literal} for every module-level UPPER_CASE assignment the agent source defines as a literal."""
    tree = ast.parse(Path(source_path).read_text(encoding="utf-8"))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name.isupper():
                try:
                    found[name] = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    continue
    for name, qualified in (aliases or {}).items():
        nodes = tree.body
        parts = qualified.split(".")
        for part in parts[:-1]:
            matches = [n for n in nodes if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                       and n.name == part]
            if len(matches) != 1:
                raise StudioDataError(f"no unambiguous literal scope {qualified!r}")
            nodes = matches[0].body
        matches = [n.value for n in nodes if isinstance(n, ast.Assign) and len(n.targets) == 1
                   and isinstance(n.targets[0], ast.Name) and n.targets[0].id == parts[-1]]
        if len(matches) != 1:
            raise StudioDataError(f"no unambiguous literal assignment {qualified!r}")
        try:
            value = ast.literal_eval(matches[0])
        except (ValueError, TypeError):
            raise StudioDataError(f"{qualified!r} is not a literal") from None
        if name in found:
            raise StudioDataError(f"literal alias would replace {name}")
        found[name] = value
    return found


def markdown_record_sets(markdown_path):
    """Named JSON records under plain/backticked headings or an explicit canonical-source declaration."""
    text = Path(markdown_path).read_text(encoding="utf-8")
    found, name, body = {}, None, None
    for line in text.splitlines():
        if body is not None:
            if line.strip() == "```":
                if name:
                    if name in found:
                        raise StudioDataError(f"duplicate Markdown record set {name}")
                    found[name] = json.loads("\n".join(body))
                body = None
            else:
                body.append(line)
            continue
        heading = re.fullmatch(r"#{1,6}\s+(.+)", line)
        declaration = re.fullmatch(r"Canonical source constant:\s*`([_A-Z][_A-Z0-9]*)`\.", line)
        if heading:
            title = heading[1]
            match = re.fullmatch(r"`?([_A-Z][_A-Z0-9]*)`?", title)
            if not match:
                match = re.fullmatch(r"Exact dataset `([_A-Z][_A-Z0-9]*)`", title)
            name = match[1] if match else None
        elif declaration:
            name = declaration[1]
        elif line.strip() == "```json":
            body = []
    if body is not None:
        raise StudioDataError("unterminated JSON block in synthetic records")
    return found


def json_records(value):
    """JSON's representation of a Python literal, without changing values or unordered set membership."""
    if isinstance(value, dict):
        if any(not isinstance(k, (str, int)) or isinstance(k, bool) for k in value):
            raise StudioDataError("record dictionary keys must be strings or integers")
        result = {str(k): json_records(v) for k, v in value.items()}
        if len(result) != len(value):
            raise StudioDataError("record dictionary keys collide after JSON conversion")
        return result
    if isinstance(value, (list, tuple)):
        return [json_records(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted((json_records(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True))
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise StudioDataError(f"not a JSON-compatible record value: {type(value).__name__}")


def record_rows(records):
    """Preserve mapping keys or use stable, one-based row numbers for a literal sequence."""
    records = json_records(records)
    if isinstance(records, dict) and records:
        return list(records.items())
    if isinstance(records, list) and records:
        return [(str(index), record) for index, record in enumerate(records, 1)]
    raise StudioDataError("a record set must be a non-empty mapping or sequence")


def matching_records(source, written):
    """Compare JSON values without Python's True == 1 / False == 0 coercion."""
    if isinstance(source, bool) or isinstance(written, bool):
        return type(source) is type(written) and source == written
    if isinstance(source, dict):
        return (isinstance(written, dict) and source.keys() == written.keys()
                and all(matching_records(value, written[key]) for key, value in source.items()))
    if isinstance(source, list):
        return (isinstance(written, list) and len(source) == len(written)
                and all(matching_records(a, b) for a, b in zip(source, written)))
    return source == written


def _leaves(value, prefix=""):
    if isinstance(value, dict) and value:
        for key, inner in value.items():
            yield from _leaves(inner, f"{prefix}{key}.")
    else:
        yield prefix[:-1], value


def _get(record, path, *, optional=False):
    if path == "$value":
        return record
    value = record
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            if optional:
                return None
            raise StudioDataError(f"no field {path!r}")
        value = value[part]
    return value


def check_schema(schema):
    if schema.get("schema") != SCHEMA:
        raise StudioDataError(f"schema must be {SCHEMA}")
    ids, titles = set(), set()
    for lst in schema.get("lists") or []:
        for key in ("id", "title", "record_set", "columns"):
            if not lst.get(key):
                raise StudioDataError(f"a list needs {key}")
        if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", lst["id"]):
            raise StudioDataError("list ids must be safe kebab-case CSV filenames")
        if lst["id"] in ids or lst["title"] in titles:
            raise StudioDataError(f"duplicate list {lst['id']} / {lst['title']}")
        ids.add(lst["id"])
        titles.add(lst["title"])
        names = [c.get("name") for c in lst["columns"]]
        if names[:1] != ["Title"]:
            raise StudioDataError(f"{lst['id']}: the first column must be Title (SharePoint's own)")
        if len(set(names)) != len(names) or any(not COLUMN.fullmatch(n or "") for n in names):
            raise StudioDataError(f"{lst['id']}: column names must be unique letters and digits (they become "
                                  "CSV headers and SharePoint display names; internal names are Title and field_N)")
        for c in lst["columns"]:
            if c.get("type") not in TYPES or not c.get("from"):
                raise StudioDataError(f"{lst['id']}.{c.get('name')}: needs from and a type in {sorted(TYPES)}")
            if "optional" in c and not isinstance(c["optional"], bool):
                raise StudioDataError(f"{lst['id']}.{c['name']}: optional must be a boolean")
            if c.get("encoding") not in (None, "joined", "json"):
                raise StudioDataError(f"{lst['id']}.{c['name']}: encoding must be joined or json")
    if not ids:
        raise StudioDataError("no lists")


def _cell(value, kind):
    if value is None:
        return ""
    if kind == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise StudioDataError(f"not a number: {value!r}")
        return repr(value) if isinstance(value, float) else str(value)
    if kind == "date":
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d\d-\d\d", value):
            raise StudioDataError(f"not a date (YYYY-MM-DD): {value!r}")
        return value
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (dict, list)):
        if isinstance(value, list) and all(not isinstance(v, (dict, list)) for v in value):
            return "; ".join(_cell(v, "text") for v in value)
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return str(value)


def build(slug, root=ROOT):
    """{list id: CSV text} for a workshop, after checking the records against the source and the knowledge file."""
    base = Path(root) / "solutions" / slug / "studio" / "data"
    schema = json.loads((base / "schema.json").read_text(encoding="utf-8"))
    if schema.get("solution") != slug:
        raise StudioDataError(f"schema.json names {schema.get('solution')!r}, not {slug!r}")
    return build_schema(schema, root=root)


def build_schema(schema, root=ROOT):
    """Build from an in-memory schema so package generation can validate before writing anything."""
    check_schema(schema)
    source = record_sets(Path(root) / schema["source"], schema.get("record_sources"))
    written = markdown_record_sets(Path(root) / schema["records_markdown"])
    out = {}
    for lst in schema["lists"]:
        name = lst["record_set"]
        if name not in source:
            raise StudioDataError(f"the agent defines no literal record set {name}")
        records = json_records(source[name])
        if not matching_records(records, written.get(name)):
            raise StudioDataError(f"{name} in {schema['records_markdown']} differs from the agent's source")
        rows = record_rows(records)
        paths = {c["from"] for c in lst["columns"]}
        for rid, record in rows:
            missing = sorted(p or "$value" for p, _ in _leaves(record)
                             if p not in paths and "$value" not in paths)
            if missing:
                raise StudioDataError(f"{name}.{rid}: fields with no column: {', '.join(missing)}")
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow([c["name"] for c in lst["columns"]])
        for rid, record in rows:
            try:
                writer.writerow([_cell(rid if c["from"] == "$key"
                                       else _get(record, c["from"], optional=c.get("optional", False)), c["type"])
                                 for c in lst["columns"]])
            except StudioDataError as e:
                raise StudioDataError(f"{name}.{rid}: {e}") from None
        out[lst["id"]] = buf.getvalue()
    return out


def studio_slugs(root=ROOT):
    return sorted(p.parent.parent.parent.name for p in (Path(root) / "solutions").glob("*/studio/data/schema.json"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("slugs", nargs="*", help="workshops to build (default: every one with studio/data)")
    parser.add_argument("--check", action="store_true", help="fail if a CSV is missing or out of date")
    args = parser.parse_args(argv)
    stale = []
    for slug in args.slugs or studio_slugs():
        base = ROOT / "solutions" / slug / "studio" / "data"
        try:
            files = build(slug)
        except (StudioDataError, OSError, ValueError) as e:
            print(f"{slug}: {e}", file=sys.stderr)
            return 1
        for list_id, text in files.items():
            target = base / f"{list_id}.csv"
            if args.check:
                if not target.exists() or target.read_text(encoding="utf-8") != text:
                    stale.append(str(target.relative_to(ROOT)))
            else:
                target.write_text(text, encoding="utf-8")
        print(f"{slug}: {len(files)} list(s) {'checked' if args.check else 'written'}")
    if stale:
        print("out of date (run tools/build_studio_data.py):\n  " + "\n  ".join(stale), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
