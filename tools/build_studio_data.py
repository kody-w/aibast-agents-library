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
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "aibast-studio-data/1.0"
TYPES = {"text", "number", "date"}
COLUMN = re.compile(r"[A-Za-z][A-Za-z0-9]{0,31}")


class StudioDataError(Exception):
    pass


def record_sets(source_path):
    """{NAME: literal} for every module-level UPPER_CASE assignment the agent source defines as a literal."""
    tree = ast.parse(Path(source_path).read_text(encoding="utf-8"))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name.isupper():
                try:
                    found[name] = ast.literal_eval(node.value)
                except ValueError:
                    continue
    return found


def markdown_record_sets(markdown_path):
    """{NAME: literal} for every `## NAME` section followed by a ```json block in a synthetic-records file."""
    text = Path(markdown_path).read_text(encoding="utf-8")
    return {name: json.loads(body) for name, body in
            re.findall(r"^## ([A-Z0-9_]+)\n+```json\n(.*?)\n```", text, re.S | re.M)}


def _leaves(value, prefix=""):
    if isinstance(value, dict):
        for key, inner in value.items():
            yield from _leaves(inner, f"{prefix}{key}.")
    else:
        yield prefix[:-1], value


def _get(record, path):
    value = record
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
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
        if lst["id"] in ids or lst["title"] in titles:
            raise StudioDataError(f"duplicate list {lst['id']} / {lst['title']}")
        ids.add(lst["id"])
        titles.add(lst["title"])
        names = [c.get("name") for c in lst["columns"]]
        if names[:1] != ["Title"]:
            raise StudioDataError(f"{lst['id']}: the first column must be Title (SharePoint's own)")
        if len(set(names)) != len(names) or any(not COLUMN.fullmatch(n or "") for n in names):
            raise StudioDataError(f"{lst['id']}: column names must be unique letters and digits (they become "
                                  "SharePoint internal names, and the From CSV import keeps them only then)")
        for c in lst["columns"]:
            if c.get("type") not in TYPES or not c.get("from"):
                raise StudioDataError(f"{lst['id']}.{c.get('name')}: needs from and a type in {sorted(TYPES)}")
    if not ids:
        raise StudioDataError("no lists")


def _cell(value, kind):
    if value is None:
        return ""
    if kind == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise StudioDataError(f"not a number: {value!r}")
        return repr(value) if isinstance(value, float) else str(value)
    if kind == "date":
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d\d-\d\d", value):
            raise StudioDataError(f"not a date (YYYY-MM-DD): {value!r}")
        return value
    return str(value)


def build(slug, root=ROOT):
    """{list id: CSV text} for a workshop, after checking the records against the source and the knowledge file."""
    base = Path(root) / "solutions" / slug / "studio" / "data"
    schema = json.loads((base / "schema.json").read_text(encoding="utf-8"))
    check_schema(schema)
    if schema.get("solution") != slug:
        raise StudioDataError(f"schema.json names {schema.get('solution')!r}, not {slug!r}")
    source = record_sets(Path(root) / schema["source"])
    written = markdown_record_sets(Path(root) / schema["records_markdown"])
    out = {}
    for lst in schema["lists"]:
        name = lst["record_set"]
        if name not in source:
            raise StudioDataError(f"the agent defines no literal record set {name}")
        records = source[name]
        if written.get(name) != records:
            raise StudioDataError(f"{name} in {schema['records_markdown']} differs from the agent's source")
        if not isinstance(records, dict) or not all(isinstance(r, dict) for r in records.values()):
            raise StudioDataError(f"{name} must map an id to a record")
        paths = {c["from"] for c in lst["columns"]}
        for rid, record in records.items():
            missing = sorted(p for p, _ in _leaves(record) if p not in paths)
            if missing:
                raise StudioDataError(f"{name}.{rid}: fields with no column: {', '.join(missing)}")
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow([c["name"] for c in lst["columns"]])
        for rid, record in records.items():
            try:
                writer.writerow([_cell(rid if c["from"] == "$key" else _get(record, c["from"]), c["type"])
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
