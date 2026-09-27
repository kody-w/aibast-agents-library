import copy
import csv
import io
import json
from pathlib import Path

import pytest

from tools import build_studio_data as data
from tools import build_studio_package as packages
from tools import studio_knowledge_tables as tables


def markdown(tmp_path, text):
    path = tmp_path / "records.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_pipe_table_values_are_exact_and_only_defined_numeric_forms_convert(tmp_path):
    path = markdown(tmp_path, r"""## Purchase requests

| ID | Name | Amount | Percentage | Mixed | Date | Count | Note |
|---|---|---:|---:|---|---|---|---|
| PR-001 | Fictional A | $125,000 | 92% | 92% | 2026-09-26 | 0012 | Left \| right |
| PR-002 | Fictional B | $-60,000 | 50% | not supplied | 2026-09-27 | 4 | Plain |
""")
    parsed = tables.parse_knowledge(path)
    assert len(parsed.records) == 1
    result = parsed.records[0]
    assert result.rows == [
        {"id": "PR-001", "name": "Fictional A", "amount": 125000, "percentage": 92, "mixed": "92%",
         "date": "2026-09-26", "count": "0012", "note": "Left | right"},
        {"id": "PR-002", "name": "Fictional B", "amount": -60000, "percentage": 50, "mixed": "not supplied",
         "date": "2026-09-27", "count": "4", "note": "Plain"},
    ]
    assert result.formats == {"amount": "currency", "percentage": "percent1"}
    assert tables.split_pipe(r"| key | path\\ | x\|y |") == ["key", r"path\\", "x|y"]


def test_rule_and_contract_tables_do_not_become_entities(tmp_path):
    path = markdown(tmp_path, """## Approval thresholds
| ID | Amount |
|---|---|
| RULE-001 | $100 |
## Locked-case evidence contract
| ID | Prompt |
|---|---|
| CASE-001 | Find records |
## Required response headings
| ID | Heading |
|---|---|
| CASE-001 | Evidence |
## Vendor records
| ID | Name |
|---|---|
| VND-001 | Fictional vendor |
""")
    parsed = tables.parse_knowledge(path)
    assert [item.section for item in parsed.records] == ["Vendor records"]
    assert len(parsed.retained) == 3


def test_unequal_heading_field_sets_remain_in_knowledge(tmp_path):
    path = markdown(tmp_path, """## Employee profiles
### emp-1001 — Jordan Chen (`jordan`)
- Department: Product
- Role: Manager
### emp-1002 — Fictional Colleague (`colleague`)
- Department: Sales
""")
    parsed = tables.parse_knowledge(path)
    assert not parsed.records
    assert "unequal field sets" in parsed.retained[0]["reason"]


def test_uniform_heading_records_include_only_authored_fields(tmp_path):
    path = markdown(tmp_path, """## Employee profiles
### emp-1001 — Jordan Chen (`jordan`)
- Department: Product
- Premium: $450
### emp-1002 — Fictional Colleague (`colleague`)
- Department: Sales
- Premium: $220
""")
    parsed = tables.parse_knowledge(path)
    record = parsed.records[0]
    assert record.form == "heading-records"
    assert record.fields == ["id", "name", "alias", "department", "premium"]
    assert record.rows[0] == {"id": "emp-1001", "name": "Jordan Chen", "alias": "jordan",
                              "department": "Product", "premium": 450}


def test_fenced_examples_and_nested_heading_fields_are_not_fabricated(tmp_path):
    path = markdown(tmp_path, """```markdown
## Not actual records
| ID | Name |
|---|---|
| FAKE-001 | Example |
```
## Knowledge articles
### KB-001 — Example
- Category: Help
- Steps:
  1. Read the source.
""")
    parsed = tables.parse_knowledge(path)
    assert not parsed.records


def test_malformed_entity_table_fails_instead_of_dropping_cells(tmp_path):
    path = markdown(tmp_path, "## Records\n| ID | Name |\n|---|---|\n| A-1 | Name | Extra |\n")
    with pytest.raises(tables.KnowledgeTableError, match="expected 2"):
        tables.parse_knowledge(path)


def fixture_schema(tmp_path, *, literal=True):
    source = tmp_path / "agent.py"
    source.write_text("raise RuntimeError('The agent must never execute')\n" + (
        "RECORDS = {'PR-001': {'name': 'Fictional A', 'amount': 125000, 'rating': 4}}\n" if literal else
        "NOTICE = 'PR-001 is a curated record, not a literal record object'\n"))
    path = markdown(tmp_path, "## Requests\n| ID | Name | Amount |\n|---|---|---|\n| PR-001 | Fictional A | $125,000 |\n")
    table = tables.parse_knowledge(path).records[0]
    tables.cross_check(table, source)
    schema = {
        "schema": data.SCHEMA, "solution": "sample", "source": "agent.py", "records_markdown": "records.md",
        "source_of_truth": "knowledge-table",
        "lists": [{
            "id": "requests", "title": "Sample Requests", "record_set": "REQUESTS",
            "source_of_truth": "knowledge-table",
            "knowledge_table": {"file": "records.md", "section": "Requests",
                                "selector": "Requests [table 1]", "form": "pipe-table"},
            "literal_cross_check": {"rows": table.literal_rows, "sources": table.literal_sources},
            "columns": [
                {"name": "Title", "label": "Name", "from": "name", "type": "text"},
                {"name": "RequestId", "label": "ID", "from": "id", "type": "text"},
                {"name": "Amount", "label": "Amount", "from": "amount", "type": "number"},
            ],
        }],
    }
    return path, source, schema


def test_existing_literal_values_are_checked_without_executing_agent(tmp_path):
    path, source, schema = fixture_schema(tmp_path)
    assert data.build_schema(schema, root=tmp_path)["requests"] == "Title,RequestId,Amount\nFictional A,PR-001,125000\n"
    path.write_text(path.read_text().replace("$125,000", "$4"))
    with pytest.raises(data.StudioDataError, match="Amount disagrees"):
        data.build_schema(schema, root=tmp_path)


def test_curated_table_without_literals_is_authoritative_and_freshly_parsed(tmp_path):
    path, _source, schema = fixture_schema(tmp_path, literal=False)
    first = data.build_schema(schema, root=tmp_path)["requests"]
    path.write_text(path.read_text().replace("$125,000", "$125,001"))
    second = data.build_schema(schema, root=tmp_path)["requests"]
    assert first != second
    assert "125001" in second
    assert schema["lists"][0]["literal_cross_check"]["rows"] == 0


def test_check_compares_csv_bytes_and_never_repairs_them(tmp_path, capsys):
    path, _source, schema = fixture_schema(tmp_path, literal=False)
    base = tmp_path / "solutions/sample/studio/data"
    base.mkdir(parents=True)
    (base / "schema.json").write_text(json.dumps(schema))
    csv_path = base / "requests.csv"
    csv_path.write_text(data.build_schema(schema, root=tmp_path)["requests"])
    assert data.main(["sample", "--check"], root=tmp_path) == 0
    original = csv_path.read_bytes()
    csv_path.write_bytes(original.replace(b"\n", b"\r\n"))
    changed = csv_path.read_bytes()
    assert data.main(["sample", "--check"], root=tmp_path) == 1
    assert csv_path.read_bytes() == changed
    csv_path.write_bytes(original)
    path.write_text(path.read_text().replace("$125,000", "$125,001"))
    assert data.main(["sample", "--check"], root=tmp_path) == 1
    assert csv_path.read_bytes() == original
    assert "out of date" in capsys.readouterr().err


def test_missing_or_reclassified_table_and_bad_provenance_fail(tmp_path):
    path, _source, schema = fixture_schema(tmp_path)
    path.write_text(path.read_text().replace("## Requests", "## Approval thresholds"))
    with pytest.raises(data.StudioDataError, match="missing or no longer clean"):
        data.build_schema(schema, root=tmp_path)
    schema["lists"][0]["knowledge_table"].pop("section")
    with pytest.raises(data.StudioDataError, match="provenance needs"):
        data.build_schema(schema, root=tmp_path)


def test_email_omission_is_explicit_and_does_not_rewrite_source(tmp_path):
    path = markdown(tmp_path, "## Contacts\n| ID | Name | Email |\n|---|---|---|\n"
                    "| C-1 | Fictional A | demo@unapproved.example.net |\n"
                    "| C-2 | Fictional B | demo@example.com |\n")
    original = path.read_bytes()
    table = tables.parse_knowledge(path).records[0]
    tables.omit_private_columns(table)
    assert table.omitted_columns == [{"name": "Email", "from": "email", "reason": "email privacy gate"}]
    assert all("email" not in row for row in table.rows)
    assert path.read_bytes() == original


def test_literal_arithmetic_proof_rejects_mutated_values(tmp_path):
    source = tmp_path / "agent.py"
    source.write_text("DATA={'M-1':{'name':'Measure','population':400,'closed':292}}\n")
    path = markdown(tmp_path, "## Measures\n| ID | Name | Gap | Closed rate |\n|---|---|---|---|\n"
                    "| M-1 | Measure | 108 | 73% |\n")
    table = tables.parse_knowledge(path).records[0]
    proofs = {"Gap": {"op": "subtract", "fields": ["population", "closed"]},
              "Closed rate": {"op": "percent", "fields": ["closed", "population"], "round": 1}}
    tables.cross_check(table, source, proofs)
    table.rows[0]["gap"] = "109"
    with pytest.raises(tables.LiteralDisagreement, match="Gap disagrees"):
        tables.cross_check(table, source, proofs)


def test_literal_email_omission_is_checked_and_cannot_hide_an_unrelated_field(tmp_path):
    source = tmp_path / "agent.py"
    records = {"C-1": {"name": "Fictional A", "contact_email": "demo@unapproved.example.net", "amount": 5}}
    source.write_text("RECORDS = " + repr(records) + "\n")
    path = markdown(tmp_path, "## RECORDS\n```json\n" + json.dumps(records) + "\n```\n")
    inputs = packages.Inputs("sample", "Sample", source, path, [], {"RECORDS": records}, {}, [], [])
    schema = packages.make_schema(inputs, tmp_path)
    item = schema["lists"][0]
    assert item["omitted_columns"] == [
        {"name": "ContactEmail", "from": "contact_email", "reason": "email privacy gate"}
    ]
    csv_text = data.build_schema(schema, root=tmp_path)["records"]
    assert "ContactEmail" not in csv_text and "unapproved.example.net" not in csv_text
    unsafe = copy.deepcopy(schema)
    unsafe["lists"][0]["omitted_columns"] = []
    unsafe["lists"][0]["columns"].append(
        {"name": "ContactEmail", "label": "Contact email", "from": "contact_email", "type": "text"})
    with pytest.raises(data.StudioDataError, match="unapproved email in a listed column"):
        data.build_schema(unsafe, root=tmp_path)
    item["omitted_columns"].append({"name": "Amount", "from": "amount", "reason": "email privacy gate"})
    with pytest.raises(data.StudioDataError, match="not justified"):
        data.build_schema(schema, root=tmp_path)


def test_listed_entities_and_retained_policy_knowledge_are_separate():
    files = packages.package_files("procurement-agent")
    base = Path("solutions/procurement-agent")
    retained = files[base / "studio/agent/knowledge/aibast_procurement-agent-synthetic-records.md"]
    assert "## Approval thresholds" in retained
    assert "| $500,000 | CFO | 48 hours |" in retained
    assert "## Spend categories" in retained
    assert "| PR-5001 |" not in retained
    assert "Procurement Purchase Requests" in retained
    instructions = files[base / "studio/agent/GLOBAL-INSTRUCTIONS.md"]
    assert "## Evidence locations" in instructions
    assert "Read unlisted records, rule tables" in instructions
    schema = json.loads(files[base / "studio/data/schema.json"])
    assert schema["source_of_truth"] == "knowledge-table"
    assert all(item["source_of_truth"] == "knowledge-table" for item in schema["lists"])
    assert [item["literal_cross_check"]["rows"] for item in schema["lists"]] == [4, 6]
