#!/usr/bin/env python3
"""Generate source-backed SharePoint, agent, managed-app and tutorial packages.

    python3 tools/build_studio_package.py asset-maintenance-forecast
    python3 tools/build_studio_package.py --all
    python3 tools/build_studio_package.py --check

--all attempts every advertised workshop except the hand-authored emission-tracking
reference. Workshops without complete, matching literal JSON records are reported
as blocked, not fabricated. --check checks existing generated packages without
writing. Pass emission-tracking explicitly to generate it, preferably with --out
pointing at a temporary repository root. Existing screenshot objects/lists are
preserved by step id. No browser, network, agent execution or tenant API is used.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import build_studio_data as data  # noqa: E402
from tools import render_studio_walkthrough as renderer  # noqa: E402
from tools import scaffold_solution_journey as journey  # noqa: E402

REFERENCE = "emission-tracking"
SITE = "https://contoso.sharepoint.com/sites/aibast-synthetic-data"
DESCRIPTION = ("The workshop's synthetic records as SharePoint lists: the same records the portable agent "
               "and the knowledge file hold, one list per record set. Every value is fictional.")
OLD_OPENING = "Use only the uploaded synthetic knowledge and operation skills."
OLD_ROUTING = ("If the correct skill or its knowledge cannot be loaded after one retry in the same turn, "
               "say so honestly and stop. Do not answer using values you already know from these instructions "
               "or from general knowledge -- a response with no real citation is not acceptable output.")
ROUTING = ("If the correct skill, a list tool or the rules knowledge cannot be loaded after one retry in the "
           "same turn, say so honestly and stop. Do not answer using values you already know from these "
           "instructions or from general knowledge -- every record value must come from a list tool result "
           "or the rules knowledge in this turn.")
READ_RECORDS = "Read the records with the SharePoint list tools, and the rules and controls knowledge."
OVERRIDE_KEYS = {"prefix", "agent_names", "opening", "record_sources", "lists", "app"}
FORMATS = {"integer", "number", "percent1", "currency", "text"}
FORBIDDEN_IDENTITY = (
    "github.com/kody-w/", "raw.githubusercontent.com/kody-w/", "kody-w.github.io", "kodyw.com",
)
MISSING = object()


class StudioPackageError(ValueError):
    """An inconsistent input or generated package; never a successful partial build."""


class BlockedWorkshop(StudioPackageError):
    """The workshop lacks publishable, independently verifiable record inputs."""


@dataclass
class Inputs:
    slug: str
    title: str
    source: Path
    records_path: Path
    rules: list[Path]
    records: dict[str, Any]
    overrides: dict[str, Any]
    cases: list[dict[str, Any]]
    skills: list[Path]


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise StudioPackageError(f"{path.name} must contain a JSON object")
    return value


def json_text(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def advertised_slugs(root: Path = ROOT) -> list[str]:
    names = read_json(root / "solutions/catalog.json")["solutions"]
    registry = read_json(root / "registry.json")["agents"]
    by_name = {row["name"]: row for row in registry if row.get("_solution")}
    return sorted({by_name[name]["_solution"]["package"]["slug"] for name in names})


def merge(base: dict, changes: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in changes.items():
        result[key] = merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else value
    return result


def overrides_for(slug: str, root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for path in (root / "tools/studio_overrides" / f"{slug}.json",
                 root / "solutions" / slug / "studio/overrides.json"):
        if path.is_file():
            result = merge(result, read_json(path))
    unknown = set(result) - OVERRIDE_KEYS
    if unknown:
        raise StudioPackageError(f"{slug}: unknown override keys: {', '.join(sorted(unknown))}")
    return result


def load_inputs(slug: str, root: Path = ROOT) -> Inputs:
    if not renderer.SLUG_RE.fullmatch(slug) or slug not in advertised_slugs(root):
        raise StudioPackageError(f"{slug!r} is not an advertised workshop")
    package = root / "solutions" / slug
    deployment = read_json(package / "deployment.json")
    source = journey.source_agent_path(root, deployment, {})
    if source is None:
        raise BlockedWorkshop("deployment metadata does not identify a portable agent source")
    renderer.referenced_path(root, source.relative_to(root).as_posix(), "portable source")
    knowledge = journey.manual_knowledge_files(package)
    record_files = [p for p in knowledge if "synthetic" in p.name]
    if len(record_files) != 1:
        raise BlockedWorkshop("expected one synthetic-records Markdown file; found "
                              + ", ".join(p.relative_to(package).as_posix() for p in record_files))
    records_path = record_files[0]
    written = data.markdown_record_sets(records_path)
    if not written:
        raise BlockedWorkshop(f"{records_path.relative_to(root)} has no named literal JSON record sets "
                              "(narrative/table snapshots cannot prove complete source equality)")
    overrides = overrides_for(slug, root)
    literals = data.record_sets(source, overrides.get("record_sources"))
    records = {}
    for name, expected in written.items():
        if name not in literals:
            raise BlockedWorkshop(f"{name} has no matching literal assignment in {source.relative_to(root)}")
        actual = data.json_records(literals[name])
        if actual != expected:
            raise StudioPackageError(f"{name} in {records_path.relative_to(root)} differs from the agent's source")
        data.record_rows(actual)
        try:
            renderer.check_privacy(actual, name)
        except renderer.WalkthroughError as error:
            raise BlockedWorkshop(f"{error}; cannot publish a lossless CSV under the no-email/tenant-id policy") from error
        records[name] = actual
    rules = [p for p in knowledge if p != records_path]
    if not rules:
        raise BlockedWorkshop("no separate rules-and-controls knowledge file")
    skills = sorted((package / "manual/skills").rglob("SKILL.md"))
    if not skills:
        raise BlockedWorkshop("manual/skills contains no SKILL.md")
    cases = read_json(root / "tests/demo_cases" / f"{slug}.json")["cases"]
    title = re.sub(r"\s+Agent$", "", deployment["display_name"])
    return Inputs(slug, title, source, records_path, rules, records, overrides, cases, skills)


def words(value: str) -> list[str]:
    return re.findall(r"[A-Za-z]+[0-9]*|[0-9]+", value.strip("_"))


def human(value: str) -> str:
    acronyms = {"id", "hr", "ai", "ae", "icp", "sku", "skus", "nps", "sla", "rfp", "rfps",
                "co2", "ch4", "n2o", "mw", "mwh", "kwh", "usd", "fpl", "kyc", "ab"}
    return " ".join(w.upper() if w.lower() in acronyms else w.capitalize() for w in words(value))


def singular(value: str) -> str:
    lower = value.lower()
    if lower.endswith("ies"):
        return value[:-3] + "y"
    if lower.endswith(("statuses", "processes")):
        return value[:-2]
    if lower.endswith("s") and not lower.endswith(("ss", "status", "analysis", "news")):
        return value[:-1]
    return value


def short(value: str, limit: int) -> str:
    value = " ".join(words(value))
    if len(value) <= limit:
        return value
    replacements = {
        "Intelligence": "Intel", "Qualification": "Qual", "Opportunities": "Opps",
        "Personalized": "Personal", "Maintenance": "Maint", "Management": "Mgmt",
        "Regulatory": "Reg", "Optimization": "Opt", "Communication": "Comms",
        "Communications": "Comms", "Assistant": "Asst", "Customer": "Cust",
        "Origination": "Orig", "Disruption": "Disrupt", "Prediction": "Pred",
        "Abandonment": "Abandon", "Processing": "Process", "Rebalancing": "Rebal",
        "Generation": "Gen", "Financial": "Fin", "Forecast": "Fcst",
        "Utilization": "Util", "Synthesizer": "Synth", "Engagement": "Engage",
    }
    parts = [w for w in value.split() if w.lower() not in {"and", "the", "of"}]
    for index, word in enumerate(parts):
        parts[index] = replacements.get(word, word)
    if len(" ".join(parts)) <= limit:
        return " ".join(parts)
    for index in range(len(parts) - 1, 0, -1):
        parts[index] = parts[index][0]
        if len(" ".join(parts)) <= limit:
            return " ".join(parts)
    suffix = " " + " ".join(parts[1:]) if len(parts) > 1 else ""
    return parts[0][:limit - len(suffix)] + suffix


def agent_names(root: Path = ROOT) -> dict[str, dict[str, str]]:
    result = {}
    for slug in advertised_slugs(root):
        title = re.sub(r"\s+Agent$", "", read_json(root / "solutions" / slug / "deployment.json")["display_name"])
        override = overrides_for(slug, root).get("agent_names", {})
        result[slug] = {mode: override.get(mode, short(title, 30 - len(suffix)) + suffix)
                        for mode, suffix in (("easy", " Studio"), ("manual", " Studio Manual"))}
    owners: dict[str, list[tuple[str, str]]] = {}
    for slug, names in result.items():
        for mode, name in names.items():
            owners.setdefault(name.casefold(), []).append((slug, mode))
    for entries in owners.values():
        if len(entries) > 1:
            for slug, mode in entries:
                suffix = " Studio" if mode == "easy" else " Studio Manual"
                digest = hashlib.sha256(slug.encode()).hexdigest()[:4]
                result[slug][mode] = short(result[slug][mode][:-len(suffix)], 25 - len(suffix)) + " " + digest + suffix
    return result


def column_name(path: str, used: set[str]) -> str:
    name = human(path).replace(" ", "") or "Value"
    if name[0].isdigit():
        name = "Value" + name
    if len(name) > 32 or name.casefold() in used:
        name = name[:25] + hashlib.sha256(path.encode()).hexdigest()[:7]
    if name.casefold() in used:
        raise StudioPackageError(f"column-name collision for {path!r}")
    used.add(name.casefold())
    return name


def value_at(row: Any, path: str) -> Any:
    if path == "$value":
        return row
    value = row
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return MISSING
        value = value[part]
    return value


def kind_for(path: str, values: list[Any]) -> str:
    present = [v for v in values if v is not MISSING and v is not None]
    tokens = set(words(path.lower()))
    if tokens & {"id", "code", "zip", "postal", "phone", "ssn", "ein", "tin", "lei", "vintage"}:
        return "text"
    if "year" in tokens or path.lower().endswith(("_number", "_fy")):
        return "text"
    if present and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in present):
        return "number"
    return "text"


def columns_for(name: str, records: Any, override: dict[str, Any]) -> list[dict[str, Any]]:
    rows = data.record_rows(records)
    record_dicts = all(isinstance(row, dict) for _, row in rows)
    paths = list(dict.fromkeys(path for _, row in rows for path, _ in data._leaves(row))) if record_dicts else ["$value"]
    if "" in paths:
        paths = ["$value"]
    values = {path: [value_at(row, path) for _, row in rows] for path in paths}
    scalar = lambda path: all(v is MISSING or v is None or isinstance(v, (str, int, float, bool))
                              for v in values[path])
    title_candidates = ("name", "title", "label", "project", "customer", "client", "company", "product",
                        "shopper_label", "member_label", "subject", "description", "role")
    title = override.get("title_from")
    if not title:
        title = next((p for candidate in title_candidates for p in paths
                      if (p == candidate or p.endswith("_" + candidate)) and scalar(p)
                      and all(v is not MISSING and v is not None for v in values[p])), None)
    if not title:
        title = "$key" if isinstance(records, dict) else (
            "$value" if paths == ["$value"] and scalar("$value") else "$key")
    key_path = "$key"
    if isinstance(records, list) and record_dicts:
        key_path = next((p for p in paths if (p == "id" or p.endswith("_id"))
                         and scalar(p) and all(v is not MISSING and v is not None for v in values[p])
                         and len({str(v) for v in values[p]}) == len(rows)), "$key")
    key_name = override.get("key_name", human(singular(name)).replace(" ", "") + "Id")
    used = {"title"}
    if len(key_name) > 32:
        key_name = column_name(key_name, used)
    else:
        used.add(key_name.casefold())
    labels = override.get("labels", {})
    aliases = override.get("column_names", {})
    columns = [
        {"name": "Title", "label": labels.get(title, singular(human(name))), "from": title, "type": "text"},
        {"name": key_name, "label": labels.get("$key", singular(human(name)) + " ID"),
         "from": key_path, "type": "text"},
    ]
    for path in paths:
        if path in (title, key_path):
            continue
        colname = aliases.get(path)
        if colname:
            if colname.casefold() in used:
                raise StudioPackageError(f"{name}: duplicate column alias {colname}")
            used.add(colname.casefold())
        else:
            colname = column_name("Value" if path == "$value" else path, used)
        kind = kind_for(path, values[path])
        if path == "$value" and isinstance(records, dict) and any(
            kind_for(key, [value]) == "text" and isinstance(value, (int, float)) for key, value in rows
        ):
            kind = "text"
        column = {"name": colname, "label": labels.get(path, human("Value" if path == "$value" else path)),
                  "from": path, "type": kind}
        if any(v is MISSING for v in values[path]):
            column["optional"] = True
        if any(isinstance(v, dict) or (isinstance(v, list) and any(isinstance(x, (dict, list)) for x in v))
               for v in values[path]):
            column["encoding"] = "json"
        elif any(isinstance(v, list) for v in values[path]):
            column["encoding"] = "joined"
        columns.append(column)
    return columns


def make_schema(inputs: Inputs, root: Path) -> dict[str, Any]:
    prefix = inputs.overrides.get("prefix", inputs.title)
    lists = []
    for name, records in inputs.records.items():
        override = inputs.overrides.get("lists", {}).get(name, {})
        label = human(name)
        title = override.get("title", short(prefix, 59 - len(label)) + " " + label)
        lists.append({
            "id": override.get("id", "-".join(words(name.lower()))),
            "title": title,
            "description": override.get("description", f"Synthetic {label.lower()} "
                                        f"(AIBAST {inputs.title} workshop; fictional)."),
            "record_set": name,
            "columns": columns_for(name, records, override),
        })
    schema = {"schema": data.SCHEMA, "solution": inputs.slug, "description": DESCRIPTION,
              "source": inputs.source.relative_to(root).as_posix(),
              "records_markdown": inputs.records_path.relative_to(root).as_posix(), "lists": lists}
    if inputs.overrides.get("record_sources"):
        schema["record_sources"] = inputs.overrides["record_sources"]
    data.check_schema(schema)
    return schema


def schema_text(schema: dict[str, Any]) -> str:
    # Compact column rows match the hand-authored reference and keep large flattened schemas readable.
    return re.sub(r"(?m)^        \{\n(?:          [^\n]*\n)+        \}",
                  lambda m: "        " + json.dumps(json.loads(m[0]), ensure_ascii=False),
                  json_text(schema))


def tool_names(schema: dict[str, Any], overrides: dict[str, Any]) -> dict[str, str]:
    result = {}
    for item in schema["lists"]:
        override = overrides.get("lists", {}).get(item["record_set"], {})
        result[item["id"]] = override.get("tool", "Get " + singular(human(item["record_set"])).lower() + " records")
    if len({name.casefold() for name in result.values()}) != len(result):
        raise StudioPackageError("tool names must be unique within an agent; supply a list tool override")
    return result


def column_instructions(schema: dict[str, Any], tools: dict[str, str]) -> str:
    lines = ["## List columns", "", "The list tools return each record's columns under SharePoint's internal names. "
             "Read them as:", ""]
    for item in schema["lists"]:
        columns = item["columns"]
        mapping = ", ".join(f"`field_{i}` {column['name']}" for i, column in enumerate(columns[1:], 1))
        lines.append(f"- **{tools[item['id']]}** (*{item['title']}*): `Title` {columns[0]['label']}; {mapping}.")
    return "\n".join(lines)


def rewrite_source_references(text: str, inputs: Inputs) -> str:
    text = text.replace("Use only the two uploaded knowledge files in this package.",
                        "Use only the workshop's SharePoint list tools and the uploaded rules knowledge.")
    text = text.replace("Use both uploaded files together:", "Use the SharePoint list tools and the rules file together:")
    text = text.replace(f"`{inputs.records_path.name}`", "the SharePoint list tools")
    text = text.replace("synthetic-records knowledge file", "SharePoint list tools")
    text = re.sub(r"\bpackaged\s+knowledge(?: files)?", "SharePoint list tools and uploaded rules knowledge", text)
    text = text.replace("uploaded synthetic", "list-backed synthetic")
    text = text.replace("uploaded anonymous synthetic", "list-backed anonymous synthetic")
    text = text.replace("uploaded aggregate synthetic", "list-backed aggregate synthetic")
    text = text.replace("bundled synthetic", "list-backed synthetic")
    text = text.replace("anonymous packaged records", "anonymous list-backed records")
    text = text.replace("attached records, controls,", "SharePoint list records, uploaded controls,")
    text = text.replace("relevant attached evidence", "relevant list records and rules evidence")
    text = text.replace("relevant attached source", "relevant list tool result or rules source")
    text = text.replace("Retrieve the paired synthetic records and controls.", READ_RECORDS)
    text = text.replace("retrieve attached knowledge", "retrieve the list records and uploaded rules knowledge")
    return text


def instructions_for(inputs: Inputs, schema: dict[str, Any], tools: dict[str, str], root: Path) -> str:
    original = (root / "solutions" / inputs.slug / "manual/GLOBAL-INSTRUCTIONS.md").read_text(encoding="utf-8")
    first, rest = original.split("\n", 1)
    if "Manual" in first:
        first = first.replace("Manual", "Studio")
    elif "Global Instructions" in first:
        first = first.replace("Global Instructions", "Studio Global Instructions")
    else:
        first += " - Studio Global Instructions"
    opening = inputs.overrides.get("opening")
    if not opening:
        refs = "; ".join(f"**{tools[item['id']]}** (*{item['title']}*)" for item in schema["lists"])
        opening = ("Use only the synthetic records in the workshop's SharePoint lists, the uploaded rules-and-controls "
                   f"knowledge, and the operation skills. Read records with these list tools: {refs}.")
    mapping = column_instructions(schema, tools)
    if OLD_OPENING in rest:
        rest = rest.replace(OLD_OPENING, opening, 1)
        start, remaining = rest.lstrip("\n").split("\n\n", 1)
        text = first + "\n\n" + start + "\n\n" + mapping + "\n\n" + remaining
    else:
        text = first + "\n\n" + opening + "\n\n" + mapping + "\n\n" + rest.lstrip("\n")
    if OLD_ROUTING in text:
        text = text.replace(OLD_ROUTING, ROUTING)
    else:
        text = text.rstrip() + "\n\n" + ROUTING + "\n"
    return rewrite_source_references(text, inputs)


def skill_for(path: Path, inputs: Inputs) -> str:
    text = path.read_text(encoding="utf-8")
    if "1. Read the synthetic knowledge records and controls." in text:
        return text.replace("1. Read the synthetic knowledge records and controls.", "1. " + READ_RECORDS)
    text = rewrite_source_references(text, inputs)
    text = text.replace("Read the synthetic records and operating rules before analyzing.", READ_RECORDS)
    if READ_RECORDS not in text:
        match = re.search(r"(?m)^# [^\n]+\n", text)
        if not match:
            raise StudioPackageError(f"{path.name}: skill needs a title")
        text = text[:match.end()] + "\n" + READ_RECORDS + "\n" + text[match.end():]
    return text


def numeric_format(column: dict[str, Any], rows: list[dict[str, str]]) -> str:
    if column["type"] == "text":
        return "text"
    tokens = set(words(column["from"].lower()))
    if tokens & {"pct", "percent", "percentage"}:
        return "percent1"
    if tokens & {"cost", "spend", "revenue", "balance", "price", "amount", "budget", "premium", "value"}:
        return "currency"
    values = [float(row[column["name"]]) for row in rows if row[column["name"]]]
    return "integer" if all(value.is_integer() for value in values) else "number"


def summable(column: dict[str, Any]) -> bool:
    if column["from"] == "$value":
        return False
    tokens = set(words(column["from"].lower()))
    blocked = {"id", "year", "vintage", "per", "rate", "price", "pct", "percent", "percentage",
               "probability", "ratio", "factor", "threshold", "average", "avg", "limit", "target",
               "score", "benchmark", "discount", "premium"}
    return column["type"] == "number" and not tokens & blocked and bool(tokens & {
        "spend", "amount", "balance", "value", "revenue", "cost", "quantity", "units", "count",
        "credits", "co2", "tonnes", "capacity", "hours",
    })


def make_app(inputs: Inputs, schema: dict[str, Any], csvs: dict[str, str]) -> dict[str, Any]:
    tables = []
    for item in schema["lists"]:
        columns = item["columns"]
        rows = list(csv.DictReader(io.StringIO(csvs[item["id"]])))
        key = columns[1]["name"]
        displayed = [key, "Title"] + [c["name"] for c in columns[2:] if c.get("encoding") != "json"][:8]
        metrics = [{"label": human(item["record_set"]), "op": "count"}]
        metrics += [{"label": c["label"], "op": "sum", "column": c["name"]}
                    for c in columns if summable(c)][:2]
        table = {
            "id": item["id"], "list": item["title"], "title": human(item["record_set"]), "key": key,
            "fields": {c["name"]: f"field_{i}" for i, c in enumerate(columns[1:], 1)},
            "columns": displayed, "labels": {c["name"]: c["label"] for c in columns},
            "formats": {c["name"]: numeric_format(c, rows) for c in columns},
            "metrics": metrics,
        }
        group = next((c["name"] for c in columns[2:] if c["type"] == "text" and not c.get("encoding")
                      and 2 <= len({r[c["name"]] for r in rows if r[c["name"]]}) <= 6
                      and not any(re.match(r"\d{4}-\d\d-", r[c["name"]]) for r in rows)), None)
        if group:
            table["groupBy"] = group
        table["sortBy"] = key
        patch = inputs.overrides.get("app", {}).get("tables", {}).get(item["id"], {})
        if patch:
            table.update(copy.deepcopy(patch))
            table = {name: table[name] for name in ("id", "list", "title", "key", "fields", "columns", "labels",
                     "computed", "formats", "metrics", "groupBy", "sortBy") if name in table}
        tables.append(table)
    app = {
        "kind": "scenario-workspace", "name": inputs.title + " Workspace", "title": inputs.title,
        "description": f"The {inputs.title} workshop's synthetic records, read from its SharePoint lists.",
        "site": SITE,
        "notice": "Synthetic demonstration data: every record and figure is fictional. This read-only workspace "
                  "does not verify evidence, make an approval or determination, or perform an external action.",
        "tables": tables,
    }
    app.update({key: value for key, value in inputs.overrides.get("app", {}).items() if key != "tables"})
    return app


def example(item: dict[str, Any], csv_text: str) -> str:
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    row = rows[0]
    key = item["columns"][1]["name"]
    result = f"{len(rows)} fictional records, including {row['Title']} ({key} {row[key]})"
    detail = next((c for c in item["columns"][2:] if not c.get("encoding") and row[c["name"]]
                   and len(row[c["name"]]) <= 80), None)
    return result + (f", with {detail['name']} {row[detail['name']]}" if detail else "") + "."


def make_walkthrough(inputs: Inputs, schema: dict[str, Any], csvs: dict[str, str], tools: dict[str, str],
                     names: dict[str, str], root: Path, existing_root: Path | None = None) -> dict[str, Any]:
    package = root / "solutions" / inputs.slug
    lists = schema["lists"]
    count, skill_count = len(lists), len(inputs.skills)
    rules = [p.relative_to(package).as_posix() for p in inputs.rules]
    skills = ["studio/agent/skills/" + p.relative_to(package / "manual/skills").as_posix() for p in inputs.skills]
    app_names = {"easy": inputs.title + " Workspace", "manual": inputs.title + " Workspace Manual"}
    modes: dict[str, dict[str, Any]] = {}

    def lane(mode: str, title: str) -> Callable[..., None]:
        steps: list[dict[str, Any]] = []
        modes[mode] = {"title": title, "steps": steps}

        def step(title: str, action: str, expected: str, shot: str, **extra: Any) -> None:
            index = len(steps) + 1
            steps.append({"id": f"{mode}-{index:02d}", "title": title, "action": action, **extra,
                          "expected": expected, "screenshot": {
                              "file": f"screenshots/studio-{mode}/{index:02d}-{shot}.webp", "status": "pending"}})
        return step

    def test_steps(add: Callable[..., None]) -> None:
        for case in inputs.cases:
            add("Test: " + case["persona"], "In a fresh Preview conversation, send the locked prompt.",
                "The relevant list tool ran. Required evidence: " + "; ".join(case["must_include"])
                + ". Preserve the synthetic-data and authorized-review boundaries; no external action occurred.",
                case["id"].lower().replace("_", "-"), case=case["id"], prompt=case["prompt"])

    add = lane("easy", "Easy mode: brainfreeze studio builds it")
    add("Get the tools and sign in once",
        "Clone the library, get brainfreeze studio from your workshop host (it has no public download yet), "
        "install Microsoft's managed apps CLI, and sign in with the account that can make agents and apps in your environment.",
        "The library is cloned, `python3 -m brainfreeze_studio --help` lists its commands, `ms auth status` "
        "shows your account, and `az account show` shows your tenant.", "sign-in",
        commands=["git clone https://github.com/microsoft/aibast-agents-library.git",
                  "npm install -g @microsoft/managed-apps-cli", "ms auth login", "az login"])
    add("Build and deploy everything with one command",
        "Run brainfreeze studio's AIBAST command for this workshop, with your SharePoint site and your environment.",
        f"It prints the {count} lists it made and filled, the Draft agent it deployed, and the managed app's play link. "
        "The first run opens one browser sign-in for the app's repository.", "deploy",
        commands=[f"python3 -m brainfreeze_studio aibast {inputs.slug} --library ./aibast-agents-library "
                  "--site https://<your-tenant>.sharepoint.com/sites/<your-site> "
                  "--environment https://<your-org>.crm.dynamics.com --deploy"])
    add("See the synthetic records in SharePoint", f"Open the site and the {lists[0]['title']} list.",
        example(lists[0], csvs[lists[0]["id"]]), "lists")
    add("Open the Draft agent in Copilot Studio", f"Open {names['easy']} and review its inventory.",
        f"The studio instructions, {skill_count} skills, {len(rules)} rules knowledge file(s) and {count} SharePoint "
        "Get items tools; no web search; Draft, not published.", "agent")
    test_steps(add)
    add("Open the managed app",
        "Open the play link brainfreeze studio printed, and allow the app to use your SharePoint connection the first time.",
        f"{inputs.title}: {count} read-only tabs from the same lists. " + example(lists[0], csvs[lists[0]["id"]]), "app")

    add = lane("manual", "Manual mode: build it yourself")
    add("Open a SharePoint site for the workshop data",
        "Use a SharePoint site you can edit, or create one (SharePoint start page, Create site, Communication site) "
        "named AIBAST Synthetic Data Manual.",
        "The site's home page opens and you can create lists on it.", "site")
    for item in lists:
        text_columns = ", ".join(c["name"] for c in item["columns"][1:] if c["type"] == "text")
        numbers = ", ".join(c["name"] for c in item["columns"] if c["type"] == "number")
        action = (f"On the site: New, List, From CSV. Upload {item['id']}.csv. On Customize, keep Title mapped "
                  f"to the Title column. Set {text_columns} to Single line of text. Keep dates as ISO text, "
                  "not Date and time; years and numeric-looking identifiers stay text (2022, not 2,022). ")
        if numbers:
            action += f"Keep {numbers} as Number. "
        action += f"Name the list {item['title']}. Preserve the CSV column order."
        add(f"Create {item['title']} from its CSV", action, example(item, csvs[item["id"]]),
            "list-" + item["id"], downloads=[f"studio/data/{item['id']}.csv"])
    add("Create a blank agent", "In Copilot Studio, create a new agent and skip the description flow.",
        "A new, empty agent opens on its Build page.", "blank-agent")
    add("Name the agent", f"Rename it {names['manual']}. (Agent names can be at most 30 characters.)",
        "The name shows at the top of the Build page.", "name")
    add("Paste the studio instructions",
        "Copy the whole instructions file and paste it into Instructions, replacing anything there.",
        f"The studio instructions name the {count} list tools and map every Title and field_N column.",
        "instructions", downloads=["studio/agent/GLOBAL-INSTRUCTIONS.md"])
    add("Save, and check the instructions stayed", "Save, go back to the agents list, and reopen the agent.",
        "The same instructions are there after reopening.", "instructions-saved")
    add("Remove web search", "In Knowledge, remove Search all websites.", "No web search knowledge remains.", "no-web-search")
    add("Add the rules-and-controls knowledge", "Knowledge, Add, upload " + ", ".join(p.name for p in inputs.rules)
        + ", and wait until ready. Do not upload the synthetic-records file: those records come from the list tools.",
        f"{len(rules)} rules knowledge file(s) listed as ready.", "rules-knowledge", downloads=rules)
    for item in lists:
        add(f"Add the {human(item['record_set']).lower()} tool",
            f"Tools, Add a tool, SharePoint, Get items. Set Site Address to your site and List Name to {item['title']}; "
            f"name the tool {tools[item['id']]}.",
            f"{tools[item['id']]} is listed under Tools.", "tool-" + item["id"])
    add(f"Add the {skill_count} skills", "Skills, Add, and upload each studio SKILL.md from the downloads.",
        f"{skill_count} skills listed, with their frontmatter names.", "skills", downloads=skills)
    add("Review the agent", f"Check the model, {skill_count} skills, the rules knowledge and {count} tools.",
        f"Sonnet 4.6, {skill_count} skills, {len(rules)} knowledge file(s), {count} Get items tools, no web search, "
        "nothing else.", "inventory")
    test_steps(add)
    add("Confirm the agent is a Draft", "Check the agent's status; do not publish.",
        "Draft; Publish was never selected.", "draft")
    out = inputs.slug + "-app"
    add("Get the app's source and set your site",
        "Generate the workshop's app folder, and set site in its src/config.ts to your SharePoint site.",
        f"{out}/managed-app holds a React + Vite managed app whose config names your site and the {count} lists.",
        "app-source", commands=[f"python3 -m brainfreeze_studio managed-app "
        f"aibast-agents-library/solutions/{inputs.slug}/studio/managed-app/app.json --out {out}"])
    add("Register the app and connect the lists",
        "In that folder, register the app with Microsoft's CLI and bind each list with your SharePoint connection.",
        f"ms.config.json lists one SharePoint connection with the {count} tables, and generated/services has a "
        "service for each list.", "app-register", commands=[
            f"cd {out}/managed-app", f'ms app init --display-name "{app_names["manual"]}" --repo native',
            *(f'ms app add data-source --connector sharepointonline --as table --dataset <your-site> '
              f'--table "{item["title"]}" --use-sso' for item in lists)])
    add("Build, push and deploy", "Build it, commit it, push it to the app's repository and deploy it.",
        "ms app deploy prints the app's play link.", "app-deploy", commands=[
            "npm install", "npm run build", f'git add -A && git commit -m "{app_names["easy"]}"',
            "git push -u origin HEAD:main", "ms app deploy"])
    add("Open the app and compare it with the agent",
        f"Open the play link, allow the SharePoint connection the first time, and open the {lists[0]['title']} tab.",
        "The app and the agent read the same synthetic records. " + example(lists[0], csvs[lists[0]["id"]]), "app")
    document = {
        "schema": renderer.SCHEMA, "solution": inputs.slug, "title": inputs.title + ", built with brainfreeze studio",
        "summary": f"The {inputs.title} agent on real SharePoint lists that hold the workshop's synthetic records, "
                   "with its own managed app. Easy mode has brainfreeze studio build all of it; Manual mode builds "
                   "the same thing by hand.",
        "data": "studio/data/schema.json",
        "agent": {"instructions": "studio/agent/GLOBAL-INSTRUCTIONS.md", "skills": "studio/agent/skills",
                  "knowledge": rules, "model": "Sonnet 4.6", "names": names},
        "app": {"spec": "studio/managed-app/app.json", "names": app_names},
        "cases": f"tests/demo_cases/{inputs.slug}.json", "modes": modes,
    }
    existing = (existing_root or root) / "solutions" / inputs.slug / "studio/walkthrough.json"
    if existing.is_file():
        preserve_screenshots(document, read_json(existing))
    for mode, lane in document["modes"].items():
        for step in lane["steps"]:
            renderer.validate_screenshot(existing.parent.parent, step["screenshot"], f"{step['id']}.screenshot", mode)
    return document


def preserve_screenshots(document: dict, existing: dict) -> None:
    old = {step["id"]: step["screenshot"] for mode in existing["modes"].values() for step in mode["steps"]
           if "screenshot" in step}
    for mode in document["modes"].values():
        for step in mode["steps"]:
            if step["id"] in old:
                step["screenshot"] = copy.deepcopy(old[step["id"]])


def validate_package_contract(schema: dict, app: dict, document: dict, tools: dict[str, str]) -> None:
    data.check_schema(schema)
    lists = schema["lists"]
    if len(lists) > 8:
        raise StudioPackageError("scenario-workspace accepts at most 8 lists")
    if any(len(item["title"]) > 60 for item in lists):
        raise StudioPackageError("list titles must be at most 60 characters")
    names = document["agent"]["names"]
    if any(not name or len(name) > 30 for name in names.values()) or len(set(names.values())) != 2:
        raise StudioPackageError("Easy and Manual agent names must differ and be at most 30 characters")
    if len(tools) != len(lists) or len({name.casefold() for name in tools.values()}) != len(tools):
        raise StudioPackageError("tool names must be unique within an agent")
    if {t["id"] for t in app["tables"]} != {item["id"] for item in lists}:
        raise StudioPackageError("app must contain exactly one table per list")
    by_id = {item["id"]: item for item in lists}
    for table in app["tables"]:
        item = by_id[table["id"]]
        columns = item["columns"]
        mapping = {c["name"]: f"field_{i}" for i, c in enumerate(columns[1:], 1)}
        if table["fields"] != mapping or table["list"] != item["title"]:
            raise StudioPackageError(f"{table['id']}: app fields must follow CSV order: Title, field_1..N")
        if table["key"] != columns[1]["name"]:
            raise StudioPackageError(f"{table['id']}: app key must be the separate record-id column after Title")
        if any(c["name"] in table["columns"] for c in columns if c.get("encoding") == "json"):
            raise StudioPackageError(f"{table['id']}: complex JSON must not be an app displayed column")
        if not set(table.get("formats", {}).values()) <= FORMATS:
            raise StudioPackageError(f"{table['id']}: unsupported app format")
    for value in (schema, app, document):
        renderer.check_privacy(value)


def validate_catalog(packages: list[tuple[dict, dict, dict[str, str]]]) -> None:
    titles, names = {}, {}
    for schema, document, tools in packages:
        slug = schema["solution"]
        for item in schema["lists"]:
            key = item["title"].casefold()
            if key in titles:
                raise StudioPackageError(f"duplicate list title across workshops: {item['title']} ({titles[key]}, {slug})")
            titles[key] = slug
        for name in document["agent"]["names"].values():
            if len(name) > 30:
                raise StudioPackageError(f"{slug}: agent name exceeds 30 characters")
            key = name.casefold()
            if key in names:
                raise StudioPackageError(f"duplicate agent name across workshops: {name} ({names[key]}, {slug})")
            names[key] = slug
        if len({name.casefold() for name in tools.values()}) != len(tools):
            raise StudioPackageError(f"{slug}: duplicate tool name within an agent")


def existing_catalog(root: Path, exclude: list[str]) -> list[tuple[dict, dict, dict[str, str]]]:
    result = []
    for slug in data.studio_slugs(root):
        if slug not in exclude:
            walk = renderer.load_walkthrough(slug, root=root)
            result.append((read_json(walk.package / walk.document["data"]), walk.document, walk.tools))
    return result


def managed_app_validator(path: Path | None = None) -> Callable[[dict], dict]:
    if path is not None:
        if not (path / "brainfreeze_studio/managed_app.py").is_file():
            raise StudioPackageError("--brainfreeze-root must contain brainfreeze_studio/managed_app.py")
        sys.path.insert(0, str(path.resolve()))
    try:
        module = importlib.import_module("brainfreeze_studio.managed_app")
    except ModuleNotFoundError as error:
        if error.name not in {"brainfreeze_studio", "brainfreeze_studio.managed_app"}:
            raise
        raise StudioPackageError("Install brainfreeze studio or set --brainfreeze-root / AIBAST_BRAINFREEZE_ROOT "
                                 "to run the actual managed-app lifecycle validator") from error
    def check(spec: dict) -> dict:
        try:
            return module.check_spec(spec)
        except module.ManagedAppError as error:
            raise StudioPackageError(f"managed-app lifecycle validator: {error}") from error
    return check


def package_files(slug: str, *, root: Path = ROOT, names: dict[str, str] | None = None,
                  validator: Callable[[dict], dict] | None = None,
                  existing_root: Path | None = None) -> dict[Path, str]:
    inputs = load_inputs(slug, root)
    schema = make_schema(inputs, root)
    csvs = data.build_schema(schema, root=root)
    tools = tool_names(schema, inputs.overrides)
    app = make_app(inputs, schema, csvs)
    if existing_root is None or not (existing_root / "solutions" / slug / "studio/walkthrough.json").is_file():
        existing_root = root
    document = make_walkthrough(inputs, schema, csvs, tools, names or agent_names(root)[slug], root, existing_root)
    validate_package_contract(schema, app, document, tools)
    if validator is not None:
        validator(app)
    base = Path("solutions") / slug
    files = {
        base / "studio/data/schema.json": schema_text(schema),
        **{base / "studio/data" / f"{key}.csv": value for key, value in csvs.items()},
        base / "studio/agent/GLOBAL-INSTRUCTIONS.md": instructions_for(inputs, schema, tools, root),
        **{base / "studio/agent/skills" / p.relative_to(root / base / "manual/skills"): skill_for(p, inputs)
           for p in inputs.skills},
        base / "studio/managed-app/app.json": json_text(app),
        base / "studio/walkthrough.json": json_text(document),
    }
    for relative, text in files.items():
        renderer.check_privacy(text, relative.as_posix())
        if any(forbidden in text.lower() for forbidden in FORBIDDEN_IDENTITY):
            raise StudioPackageError(f"{relative}: personal-fork identity is not publishable")
    with tempfile.TemporaryDirectory(prefix=".studio-render-", dir=root) as folder:
        stage = Path(folder)
        dependencies = [(p, p.relative_to(root))
                        for p in (inputs.source, inputs.records_path, *inputs.rules, root / document["cases"])]
        for mode in document["modes"].values():
            for step in mode["steps"]:
                dependencies += [(existing_root / base / shot["file"], base / shot["file"])
                                 for shot in renderer.screenshot_list(step["screenshot"]) if shot["status"] == "reviewed"]
        for source, relative in dependencies:
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for relative, text in files.items():
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        files[base / "studio-tutorial.html"] = renderer.render_walkthrough(slug, root=stage)
    return files


def write_package(files: dict[Path, str], root: Path, *, check: bool = False) -> list[Path]:
    bases = {root / Path(*relative.parts[:2]) / "studio" for relative in files}
    extras = sorted({path.relative_to(root) for base in bases
                     for pattern in ("data/*.csv", "agent/skills/**/SKILL.md") for path in base.glob(pattern)}
                    - files.keys())
    if extras and not check:
        raise StudioPackageError("obsolete generated files require explicit removal before regeneration: "
                                 + ", ".join(str(p) for p in extras))
    stale = list(extras)
    for relative, text in files.items():
        target = root / relative
        if not target.is_file() or target.read_bytes() != text.encode("utf-8"):
            stale.append(relative)
            if not check:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8")
    return stale


def main(argv: list[str] | None = None, *, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("slugs", nargs="*")
    parser.add_argument("--all", action="store_true", help="attempt all advertised workshops except emission-tracking")
    parser.add_argument("--check", action="store_true", help="check generated packages without writing")
    parser.add_argument("--out", type=Path, help="write to a separate repository root (useful for the reference oracle)")
    parser.add_argument("--brainfreeze-root", type=Path, default=os.environ.get("AIBAST_BRAINFREEZE_ROOT"),
                        help="validate every app with brainfreeze_studio.managed_app.check_spec")
    args = parser.parse_args(argv)
    if args.slugs and args.all:
        parser.error("use workshop slugs or --all, not both")
    if not args.slugs and not args.all and not args.check:
        parser.error("supply one or more workshop slugs, --all, or --check")
    slugs = args.slugs or ([s for s in advertised_slugs(root) if s != REFERENCE] if args.all else
                          [s for s in data.studio_slugs(root) if s != REFERENCE])
    if not slugs:
        print("No generated studio packages to check.", file=sys.stderr)
        return 1
    failures, stale, completed = [], [], 0
    try:
        names = agent_names(root)
        validator = managed_app_validator(args.brainfreeze_root) if args.brainfreeze_root else None
        catalog = existing_catalog(root, slugs)
        for slug in slugs:
            try:
                files = package_files(slug, root=root, names=names.get(slug), validator=validator, existing_root=args.out)
                base = Path("solutions") / slug / "studio"
                schema = json.loads(files[base / "data/schema.json"])
                document = json.loads(files[base / "walkthrough.json"])
                entry = (schema, document, tool_names(schema, overrides_for(slug, root)))
                validate_catalog([*catalog, entry])
                changed = write_package(files, args.out or root, check=args.check)
            except (StudioPackageError, data.StudioDataError, renderer.WalkthroughError, OSError, ValueError) as error:
                failures.append(f"{slug}: {'BLOCKED: ' if isinstance(error, BlockedWorkshop) else ''}{error}")
                continue
            catalog.append(entry)
            stale.extend(changed if args.check else [])
            completed += 1
            print(f"{slug}: {len(files)} files {'checked' if args.check else 'generated'}")
    except (StudioPackageError, OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 2
    if stale:
        print("Stale studio package files (run tools/build_studio_package.py <slug>):\n  "
              + "\n  ".join(str(p) for p in stale), file=sys.stderr)
    if failures:
        print("\n".join(failures), file=sys.stderr)
    print(f"{completed} package(s) {'checked' if args.check else 'generated'}; {len(failures)} blocked/failed.")
    return 1 if stale or failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
