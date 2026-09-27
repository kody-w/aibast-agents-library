from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import os
import re
import shutil
from pathlib import Path

import pytest

from tests.test_studio_walkthrough import write_png
from tools import build_studio_data as data
from tools import build_studio_package as package
from tools import render_studio_walkthrough as renderer

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "solutions/emission-tracking"
SAMPLE = "asset-maintenance-forecast"
REFERENCE_SITE_SECTION = ROOT / "tests/fixtures/studio/emission-tracking-site-section.md"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(package.json_text(value), encoding="utf-8")


def reference_files():
    return sorted([
        REFERENCE / "studio/data/schema.json",
        *REFERENCE.glob("studio/data/*.csv"),
        REFERENCE / "studio/agent/GLOBAL-INSTRUCTIONS.md",
        *REFERENCE.glob("studio/agent/skills/*/SKILL.md"),
        REFERENCE / "studio/managed-app/app.json",
    ])


def reference_bytes(source):
    expected = source.read_bytes()
    if source == REFERENCE / "studio/agent/GLOBAL-INSTRUCTIONS.md" and b"\n## SharePoint site\n" not in expected:
        # The protected checkpoint predates the lead's contract; the reviewed suffix is a static oracle fixture.
        expected = expected.rstrip() + b"\n\n" + REFERENCE_SITE_SECTION.read_bytes()
    return expected


def assert_reference_matches(output):
    for source in reference_files():
        relative = source.relative_to(ROOT)
        assert (output / relative).read_bytes() == reference_bytes(source), str(relative)


@pytest.fixture
def reference_output(tmp_path):
    package.write_package(package.package_files("emission-tracking"), tmp_path)
    return tmp_path


def test_emission_reference_oracle_is_byte_identical(reference_output):
    assert len(reference_files()) == 10
    assert_reference_matches(reference_output)


def test_oracle_rejects_a_controlled_mutation(reference_output):
    path = reference_output / "solutions/emission-tracking/studio/data/schema.json"
    original = path.read_bytes()
    path.write_bytes(original.replace(b"Baseline year", b"Changed year", 1))
    with pytest.raises(AssertionError, match="studio/data/schema.json"):
        assert_reference_matches(reference_output)
    path.write_bytes(original)
    assert_reference_matches(reference_output)


def test_generation_keeps_the_reference_read_only():
    before = {p: hashlib.sha256(p.read_bytes()).digest() for p in reference_files()}
    package.package_files("emission-tracking")
    assert {p: hashlib.sha256(p.read_bytes()).digest() for p in before} == before


def test_emission_site_section_matches_the_reviewed_fixture(reference_output):
    instructions = (reference_output / "solutions/emission-tracking/studio/agent/GLOBAL-INSTRUCTIONS.md").read_text()
    assert instructions.count("YOUR_SITE_ADDRESS") == 1
    assert instructions.endswith("<!-- locked-preview-anchors:end -->\n\n" + REFERENCE_SITE_SECTION.read_text())


@pytest.mark.parametrize(("counts", "word", "titles", "small"), [
    ([50], "one", "*First Records*", True),
    ([50, 50], "two", "*First Records* or *Second Records*", True),
    ([50, 51], "two", "*First Records* or *Second Records*", False),
    ([51, 1], "two", "*First Records* or *Second Records*", False),
    ([1, 50, 2], "three", "*First Records*, *Second Records* or *Third Records*", True),
])
def test_site_section_uses_each_list_count_and_the_exact_fifty_item_boundary(counts, word, titles, small):
    inputs = copy.deepcopy(package.load_inputs(SAMPLE))
    inputs.records = {f"RECORDS_{i}": [{"name": f"Record {n}"} for n in range(count)]
                      for i, count in enumerate(counts)}
    names = ("First Records", "Second Records", "Third Records")
    schema = {"lists": [{"title": names[i], "record_set": f"RECORDS_{i}"} for i in range(len(counts))]}
    section = package.sharepoint_site_section(inputs, schema)
    assert section.count("YOUR_SITE_ADDRESS") == 1
    assert f"The {word} " in section
    assert f"List Name (`table`): {titles}." in section
    assert "Site Address (`dataset`)" in section
    assert "Never call Get datasets and never guess another site." in section
    assert ("Read all items with no filter; each list is small." in section) is small
    assert ("Use a filter on the list's internal names (above) to read only the records you need." in section) is not small


@pytest.mark.parametrize(("count", "word"), [
    (1, "one"), (2, "two"), (3, "three"), (4, "four"), (5, "five"), (6, "six"), (7, "seven"), (8, "eight"),
])
def test_list_counts_are_spelled_out(count, word):
    assert package.list_count_word(count) == word


@pytest.fixture
def source_root(tmp_path):
    catalog = package.read_json(ROOT / "solutions/catalog.json")
    registry = package.read_json(ROOT / "registry.json")
    rows = [row for row in registry["agents"] if row.get("_solution", {}).get("package", {}).get("slug") == SAMPLE]
    write_json(tmp_path / "registry.json", {"agents": rows})
    write_json(tmp_path / "solutions/catalog.json", {"solutions": {row["name"]: catalog["solutions"][row["name"]]
                                                               for row in rows}})
    source = package.load_inputs(SAMPLE)
    for path in (source.source, *source.rules, source.records_path,
                 ROOT / "solutions" / SAMPLE / "deployment.json", ROOT / "tests/demo_cases" / f"{SAMPLE}.json"):
        target = tmp_path / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    manual = tmp_path / "solutions" / SAMPLE / "manual"
    shutil.copyfile(ROOT / "solutions" / SAMPLE / "manual/GLOBAL-INSTRUCTIONS.md", manual / "GLOBAL-INSTRUCTIONS.md")
    shutil.copytree(ROOT / "solutions" / SAMPLE / "manual/skills", manual / "skills")
    package.write_package(package.package_files(SAMPLE, root=tmp_path), tmp_path)
    return tmp_path


def test_generation_and_check_are_deterministic_and_non_writing(source_root, capsys):
    assert package.main([SAMPLE, "--check"], root=source_root) == 0
    path = source_root / "solutions" / SAMPLE / "studio/data/assets.csv"
    before = path.read_bytes()
    path.write_bytes(before + b"\n")
    changed = path.read_bytes()
    assert package.main([SAMPLE, "--check"], root=source_root) == 1
    assert "Stale studio package files" in capsys.readouterr().err
    assert path.read_bytes() == changed
    assert package.main([SAMPLE], root=source_root) == 0
    assert path.read_bytes() == before
    assert package.main(["--check"], root=source_root) == 0


def test_duplicate_site_token_in_manual_input_is_rejected_without_writing(source_root, capsys):
    manual = source_root / "solutions" / SAMPLE / "manual/GLOBAL-INSTRUCTIONS.md"
    manual.write_text(manual.read_text().replace("## Boundaries", "YOUR_SITE_ADDRESS\n\n## Boundaries", 1))
    base = source_root / "solutions" / SAMPLE / "studio"
    before = {p: p.read_bytes() for p in base.rglob("*") if p.is_file()}
    assert package.main([SAMPLE], root=source_root) == 1
    assert "YOUR_SITE_ADDRESS exactly once" in capsys.readouterr().err
    assert {p: p.read_bytes() for p in before} == before


def test_custom_manual_postscript_is_preserved_before_the_site_section(source_root):
    source = source_root / "solutions" / SAMPLE / "manual/GLOBAL-INSTRUCTIONS.md"
    postscript = "## Additional review boundary\n\nNever change external records."
    source.write_text(source.read_text().rstrip() + "\n\n" + postscript + "\n")
    files = package.package_files(SAMPLE, root=source_root)
    instructions = files[Path("solutions") / SAMPLE / "studio/agent/GLOBAL-INSTRUCTIONS.md"]
    assert postscript + "\n<!-- locked-preview-anchors:end -->\n\n## SharePoint site\n" in instructions
    assert instructions.count("YOUR_SITE_ADDRESS") == 1


def test_check_detects_obsolete_csvs_without_deleting_them(source_root):
    extra = source_root / "solutions" / SAMPLE / "studio/data/obsolete.csv"
    extra.write_text("Title,Id\nOld,1\n", encoding="utf-8")
    files = package.package_files(SAMPLE, root=source_root)
    assert extra.relative_to(source_root) in package.write_package(files, source_root, check=True)
    with pytest.raises(package.StudioPackageError, match="obsolete generated files"):
        package.write_package(files, source_root)
    assert extra.is_file()


def test_all_excludes_reference_and_unadvertised_workshops(monkeypatch, tmp_path):
    called = []
    monkeypatch.setattr(package, "agent_names", lambda root: {})
    monkeypatch.setattr(package, "existing_catalog", lambda root, exclude: [])
    monkeypatch.setattr(package, "validate_catalog", lambda entries: None)
    monkeypatch.setattr(package, "tool_names", lambda schema, overrides: {})
    monkeypatch.setattr(package, "write_package", lambda files, root, check: [])
    def generated(slug, **kwargs):
        called.append(slug)
        base = Path("solutions") / slug / "studio"
        return {base / "data/schema.json": "{}", base / "walkthrough.json": "{}"}
    monkeypatch.setattr(package, "package_files", generated)
    assert package.main(["--all", "--out", str(tmp_path)]) == 0
    assert len(called) == 50
    assert "emission-tracking" not in called
    assert "grid-outage-response" not in called
    called.clear()
    assert package.main(["emission-tracking", "--out", str(tmp_path)]) == 0
    assert called == ["emission-tracking"]


def test_unadvertised_slug_is_rejected():
    with pytest.raises(package.StudioPackageError, match="not an advertised workshop"):
        package.load_inputs("grid-outage-response")


def test_blocked_inputs_are_not_fabricated_or_written(tmp_path, capsys):
    assert package.main(["account-intelligence", "--out", str(tmp_path)]) == 1
    assert "BLOCKED" in capsys.readouterr().err
    assert not list(tmp_path.iterdir())


def test_no_email_policy_blocks_lossless_order_records():
    with pytest.raises(package.BlockedWorkshop, match="email address"):
        package.load_inputs("order-status-communication")


def test_no_complete_literals_is_an_explicit_blocker():
    with pytest.raises(package.BlockedWorkshop, match="no named literal JSON record sets"):
        package.load_inputs("account-intelligence")


@pytest.mark.parametrize("as_array", [False, True])
def test_reviewed_and_pending_screenshots_survive_regeneration(source_root, as_array):
    base = source_root / "solutions" / SAMPLE
    path = base / "studio/walkthrough.json"
    document = package.read_json(path)
    shot = {
        "file": "screenshots/studio-easy/reviewed-test-fixture.png", "status": "reviewed",
        "alt": "Test-only image, not live workshop evidence", "anchors": ["Synthetic fixture"],
        "captured_at": "2026-09-27T01:00:00Z", "width": 32, "height": 16, "density": 1,
    }
    write_png(base / shot["file"], 32, 16)
    screenshot = [shot, document["modes"]["easy"]["steps"][0]["screenshot"]] if as_array else shot
    document["modes"]["easy"]["steps"][0]["screenshot"] = screenshot
    write_json(path, document)
    for _ in range(2):
        files = package.package_files(SAMPLE, root=source_root)
        package.write_package(files, source_root)
        result = package.read_json(path)
        assert result["modes"]["easy"]["steps"][0]["screenshot"] == screenshot
        assert "data-evidence-status=\"reviewed\"" in (base / "studio-tutorial.html").read_text()


def test_out_directory_screenshots_take_precedence(source_root, tmp_path):
    out = tmp_path / "out"
    package.write_package(package.package_files(SAMPLE, root=source_root), out)
    path = out / "solutions" / SAMPLE / "studio/walkthrough.json"
    document = package.read_json(path)
    shot = document["modes"]["easy"]["steps"][0]["screenshot"]
    shot["file"] = "screenshots/studio-easy/retake-planned.webp"
    shot["note"] = "Keep this pending capture request"
    write_json(path, document)
    files = package.package_files(SAMPLE, root=source_root, existing_root=out)
    package.write_package(files, out)
    assert package.read_json(path)["modes"]["easy"]["steps"][0]["screenshot"] == shot


@pytest.mark.parametrize("screenshot", [None, [], {"file": "screenshots/studio-easy/test.webp", "status": "invalid"}])
def test_invalid_preserved_screenshots_fail_before_writing(source_root, capsys, screenshot):
    path = source_root / "solutions" / SAMPLE / "studio/walkthrough.json"
    document = package.read_json(path)
    document["modes"]["easy"]["steps"][0]["screenshot"] = screenshot
    write_json(path, document)
    before = {p: p.read_bytes() for p in path.parent.rglob("*") if p.is_file()}
    assert package.main([SAMPLE], root=source_root) == 1
    assert "screenshot" in capsys.readouterr().err
    assert {p: p.read_bytes() for p in before} == before


def dataset(tmp_path, records):
    source = tmp_path / "agent.py"
    source.write_text("raise RuntimeError('Never execute the agent')\nRECORDS = " + repr(records) + "\n")
    markdown = tmp_path / "synthetic-records.md"
    markdown.write_text("### `RECORDS`\n\n```json\n" + package.json_text(data.json_records(records)).rstrip() + "\n```\n")
    inputs = package.Inputs("sample-workshop", "Sample Workshop", source, markdown, [], {"RECORDS": records}, {}, [], [])
    schema = package.make_schema(inputs, tmp_path)
    csvs = data.build_schema(schema, root=tmp_path)
    return inputs, schema, csvs


def test_flattening_keeps_all_values_and_import_sensitive_types(tmp_path):
    records = {
        "007": {"name": "Fictional North", "year": 2022, "vintage": 2025, "postal_code": "00123",
                "phone": "5550100", "opened": "2026-08-07", "active": True, "amount": 24.5,
                "nested": {"units": 3, "empty": None, "object": {}}, "tags": ["A", "B"],
                "events": [{"day": "2026-08-07", "amount": 5}], "long_nested_column_name": {"with_more_words": 7}},
        "008": {"name": "Fictional South", "year": 2023, "vintage": 2024, "postal_code": "00456",
                "phone": "5550101", "opened": "2026-08-08", "active": False, "amount": 12,
                "nested": {"units": 4, "empty": None, "object": {}}, "tags": [], "events": []},
    }
    inputs, schema, csvs = dataset(tmp_path, records)
    columns = schema["lists"][0]["columns"]
    by_path = {c["from"]: c for c in columns}
    assert columns[:2] == [
        {"name": "Title", "label": "Record", "from": "name", "type": "text"},
        {"name": "RecordId", "label": "Record ID", "from": "$key", "type": "text"},
    ]
    for path in ("year", "vintage", "postal_code", "phone", "opened", "active"):
        assert by_path[path]["type"] == "text", path
    for path in ("amount", "nested.units"):
        assert by_path[path]["type"] == "number", path
    assert all(re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,31}", c["name"]) for c in columns)
    rows = list(csv.DictReader(io.StringIO(csvs["records"])))
    assert rows[0]["RecordId"] == "007"
    assert rows[0]["Active"] == "Yes" and rows[1]["Active"] == "No"
    assert rows[0]["Tags"] == "A; B" and rows[1]["Tags"] == ""
    assert rows[0]["NestedEmpty"] == ""
    assert rows[0]["NestedObject"] == "{}"
    assert json.loads(rows[0]["Events"]) == records["007"]["events"]
    optional = by_path["long_nested_column_name.with_more_words"]
    assert optional["optional"] is True and rows[1][optional["name"]] == ""
    app = package.make_app(inputs, schema, csvs)
    assert "Events" not in app["tables"][0]["columns"]
    assert "NestedObject" not in app["tables"][0]["columns"]


@pytest.mark.parametrize("records", [
    [{"id": "001", "name": "First", "amount": 3}, {"id": "002", "name": "Second", "amount": 4}],
    {"group": [{"name": "First", "amount": 3}, {"name": "Second", "amount": 4}]},
    {"group": ["one", "two"], "other": ["three"]},
    {"year": 2022, "rate": 0.5, "allowed": True, "labels": ["a", "b"]},
    ["Discovery", "Proposal"], {"Discovery", "Proposal"},
])
def test_literal_container_shapes_keep_every_source_record(tmp_path, records):
    _inputs, schema, csvs = dataset(tmp_path, records)
    rows = list(csv.DictReader(io.StringIO(csvs["records"])))
    assert len(rows) == len(records)
    assert len({r[schema["lists"][0]["columns"][1]["name"]] for r in rows}) == len(records)
    assert len(schema["lists"]) == 1


def test_scalar_controls_are_not_summed(tmp_path):
    inputs, schema, csvs = dataset(tmp_path, {"baseline_year": 2022, "interest_rate": 4})
    assert schema["lists"][0]["columns"][2]["type"] == "text"
    app = package.make_app(inputs, schema, csvs)
    assert app["tables"][0]["metrics"] == [{"label": "RECORDS".capitalize(), "op": "count"}]


def test_boolean_to_number_knowledge_drift_is_rejected(tmp_path):
    inputs, schema, _csvs = dataset(tmp_path, {"x": {"name": "Example", "enabled": True}})
    inputs.records_path.write_text(inputs.records_path.read_text().replace('"enabled": true', '"enabled": 1'))
    with pytest.raises(data.StudioDataError, match="differs from the agent's source"):
        data.build_schema(schema, root=tmp_path)
    assert not data.matching_records({"flags": [False]}, {"flags": [0]})
    assert data.matching_records({"amount": 1}, {"amount": 1.0})


def test_column_name_collisions_are_deterministic():
    records = {"x": {"name": "Example", "same_name": 1, "same-name": 2}}
    first = package.columns_for("RECORDS", records, {})
    assert first == package.columns_for("RECORDS", records, {})
    assert len({c["name"].casefold() for c in first}) == len(first)


def test_unsafe_list_id_is_rejected_before_csv_writes(tmp_path):
    _inputs, schema, _csvs = dataset(tmp_path, {"x": {"name": "Example"}})
    schema["lists"][0]["id"] = "../../outside"
    with pytest.raises(data.StudioDataError, match="safe kebab-case CSV filenames"):
        data.build_schema(schema, root=tmp_path)


def test_named_markdown_forms_and_canonical_source_declarations(tmp_path):
    path = tmp_path / "records.md"
    path.write_text('## ALPHA\n\n```json\n{"x": 1}\n```\n'
                    '### `BETA`\n\n```json\n{"x": 2}\n```\n'
                    '## Exact dataset `_GAMMA`\n\nA literal.\n\n```json\n{"x": 3}\n```\n'
                    '## Human heading\n\nCanonical source constant: `DELTA`.\n\n```json\n{"x": 4}\n```\n')
    assert data.markdown_record_sets(path) == {"ALPHA": {"x": 1}, "BETA": {"x": 2}, "_GAMMA": {"x": 3}, "DELTA": {"x": 4}}


def test_local_literal_alias_and_json_key_normalization_do_not_execute_source(tmp_path):
    path = tmp_path / "agent.py"
    path.write_text("raise RuntimeError('Do not execute')\nclass Agent:\n"
                    "    def operation(self):\n        table = {1: 100, 2: 200}\n")
    result = data.record_sets(path, {"TABLE": "Agent.operation.table"})
    assert data.json_records(result["TABLE"]) == {"1": 100, "2": 200}
    with pytest.raises(data.StudioDataError, match="no unambiguous literal"):
        data.record_sets(path, {"TABLE": "Agent.missing.table"})


def catalog_packages():
    result = []
    for slug in data.studio_slugs():
        base = ROOT / "solutions" / slug
        schema = package.read_json(base / "studio/data/schema.json")
        walk = renderer.load_walkthrough(slug)
        result.append((schema, walk.document, walk.tools))
    return result


def test_all_package_names_and_tools_are_unique():
    packages = catalog_packages()
    assert packages
    package.validate_catalog(packages)
    planned = [name for names in package.agent_names().values() for name in names.values()]
    assert len(planned) == 102
    assert all(len(name) <= 30 for name in planned)
    assert len({name.casefold() for name in planned}) == 102


@pytest.mark.parametrize(("mutation", "message"), [
    ("list", "duplicate list title across workshops"),
    ("agent", "duplicate agent name across workshops"),
    ("length", "agent name exceeds 30 characters"),
    ("tool", "duplicate tool name within an agent"),
])
def test_catalog_checks_reject_controlled_mutations(mutation, message):
    packages = copy.deepcopy(catalog_packages())
    first = packages[0]
    if len(packages) < 2:
        packages.append(copy.deepcopy(first))
        packages[1][0]["solution"] = "second-fixture"
        for item in packages[1][0]["lists"]:
            item["title"] += " Second"
        packages[1][1]["agent"]["names"] = {"easy": "Second Studio", "manual": "Second Studio Manual"}
    second = packages[1]
    if mutation == "list":
        second[0]["lists"][0]["title"] = first[0]["lists"][0]["title"]
    elif mutation == "agent":
        second[1]["agent"]["names"]["easy"] = first[1]["agent"]["names"]["manual"]
    elif mutation == "length":
        first[1]["agent"]["names"]["easy"] = "X" * 31
    else:
        keys = list(first[2])
        first[2][keys[1]] = first[2][keys[0]]
    with pytest.raises(package.StudioPackageError, match=message):
        package.validate_catalog(packages)


def test_every_generated_package_is_current():
    for slug in data.studio_slugs():
        if slug != package.REFERENCE:
            assert package.write_package(package.package_files(slug), ROOT, check=True) == [], slug


def test_every_advertised_workshop_is_generated_or_explicitly_blocked():
    ready, blocked = set(), set()
    for slug in package.advertised_slugs():
        try:
            package.load_inputs(slug)
        except package.BlockedWorkshop as error:
            assert str(error)
            blocked.add(slug)
        else:
            ready.add(slug)
    assert ready and blocked
    assert ready == set(data.studio_slugs()), "Generate every source-verifiable edition; never invent blocked records"
    assert len(ready | blocked) == 51
    assert "grid-outage-response" not in ready | blocked
    for slug in blocked:
        assert not (ROOT / "solutions" / slug / "studio").exists(), slug


def test_generated_agent_inputs_use_lists_instead_of_the_removed_knowledge():
    for slug in data.studio_slugs():
        inputs = package.load_inputs(slug)
        base = ROOT / "solutions" / slug
        instructions = (base / "studio/agent/GLOBAL-INSTRUCTIONS.md").read_text()
        for path in [base / "studio/agent/GLOBAL-INSTRUCTIONS.md", *base.glob("studio/agent/skills/*/SKILL.md")]:
            text = path.read_text()
            assert inputs.records_path.name not in text, path
            assert "two uploaded knowledge files" not in text, path
            assert "both uploaded files" not in text, path
            assert "query external systems" not in text, path
            assert "do not imply live access" not in text, path
            if path.name == "SKILL.md":
                assert "SharePoint list tools" in text, path
        assert package.ROUTING in instructions, slug


def assert_site_contract(instructions, schema, counts):
    assert instructions.count("YOUR_SITE_ADDRESS") == 1, schema["solution"]
    assert instructions.count("\n## SharePoint site\n") == 1, schema["solution"]
    before, section = instructions.rsplit("\n\n## SharePoint site\n\n", 1)
    assert before.endswith("<!-- locked-preview-anchors:end -->"), schema["solution"]
    for item in schema["lists"]:
        assert f"*{item['title']}*" in section, (schema["solution"], item["title"])
    assert "Site Address (`dataset`)" in section
    assert "List Name (`table`)" in section
    assert section.rstrip().endswith("Never call Get datasets and never guess another site.")
    small = all(count <= 50 for count in counts)
    assert ("Read all items with no filter; each list is small." in section) is small
    assert ("Use a filter on the list's internal names (above) to read only the records you need." in section) is not small


def test_every_studio_site_contract_has_one_token_and_all_list_titles():
    for slug in data.studio_slugs():
        base = ROOT / "solutions" / slug
        source = base / "studio/agent/GLOBAL-INSTRUCTIONS.md"
        instructions = reference_bytes(source).decode("utf-8") if slug == package.REFERENCE else source.read_text()
        schema = package.read_json(base / "studio/data/schema.json")
        counts = []
        for item in schema["lists"]:
            with (base / "studio/data" / f"{item['id']}.csv").open(newline="") as stream:
                counts.append(sum(1 for _ in csv.DictReader(stream)))
        assert_site_contract(instructions, schema, counts)


@pytest.mark.parametrize("mutation", ["missing-token", "duplicate-token", "missing-title"])
def test_site_contract_gate_rejects_controlled_mutations(mutation):
    schema = package.read_json(REFERENCE / "studio/data/schema.json")
    instructions = reference_bytes(REFERENCE / "studio/agent/GLOBAL-INSTRUCTIONS.md").decode("utf-8")
    if mutation == "missing-token":
        instructions = instructions.replace("YOUR_SITE_ADDRESS", "MISSING_SITE")
    elif mutation == "duplicate-token":
        instructions = instructions.replace("YOUR_SITE_ADDRESS", "YOUR_SITE_ADDRESS YOUR_SITE_ADDRESS")
    else:
        before, section = instructions.rsplit("\n\n## SharePoint site\n\n", 1)
        instructions = before + "\n\n## SharePoint site\n\n" + section.replace("*Emissions Facilities*, ", "")
    with pytest.raises(AssertionError):
        assert_site_contract(instructions, schema, [4, 4, 3])


def test_manual_paste_step_explains_site_replacement_for_every_generated_edition():
    for slug in data.studio_slugs():
        if slug == package.REFERENCE:
            continue
        base = ROOT / "solutions" / slug
        document = package.read_json(base / "studio/walkthrough.json")
        step = next(s for s in document["modes"]["manual"]["steps"] if s["title"] == "Paste the studio instructions")
        assert "in the last section (SharePoint site), replace YOUR_SITE_ADDRESS with your site's address" in step["action"]
        assert "https://contoso.sharepoint.com/sites/AIBASTSyntheticDataManual" in step["action"]
        assert "Copilot Studio still asks the model for the site and list on every call." in step["action"]
        heading = (base / "studio/agent/GLOBAL-INSTRUCTIONS.md").read_text().splitlines()[0].removeprefix("# ")
        assert step["expected"].startswith(f"The instructions start with {heading}, name the ")
        assert step["expected"].endswith("and end with your site's address.")


def test_list_access_exception_preserves_other_system_boundaries():
    original = "Do not browse the web, query external systems, or invent facts. Never update CRM or send a message."
    rewritten = package.rewrite_source_references(original, package.load_inputs(SAMPLE))
    assert "query systems other than the workshop's synthetic SharePoint lists" in rewritten
    assert "Do not browse the web" in rewritten
    assert "Never update CRM or send a message." in rewritten


def test_every_walkthrough_has_all_locked_cases_and_valid_assets():
    for slug in data.studio_slugs():
        walk = renderer.load_walkthrough(slug)
        ids = [case["id"] for case in package.read_json(ROOT / walk.document["cases"])["cases"]]
        for mode in walk.document["modes"].values():
            assert [step["case"] for step in mode["steps"] if "case" in step] == ids, slug
        schema = package.read_json(walk.package / walk.document["data"])
        package.validate_package_contract(schema, walk.app, walk.document, walk.tools)
        assert all("synthetic" not in Path(p).name for p in walk.document["agent"]["knowledge"])
        assert len(walk.tools) == len(schema["lists"])


def test_import_guidance_names_every_numeric_looking_text_column():
    for slug in data.studio_slugs():
        walk = renderer.load_walkthrough(slug)
        schema = package.read_json(walk.package / walk.document["data"])
        steps = walk.document["modes"]["manual"]["steps"]
        for item in schema["lists"]:
            download = f"studio/data/{item['id']}.csv"
            step = next(step for step in steps if download in step.get("downloads", []))
            with (walk.package / download).open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            for column in item["columns"]:
                if column["type"] == "text" and any(re.match(r"^[+-]?\d", row[column["name"]]) for row in rows):
                    assert column["name"] in step["action"], (slug, column["name"])
                    assert "Single line of text" in step["action"], slug


def test_import_guidance_protects_every_long_text_value():
    checked = 0
    for slug in data.studio_slugs():
        walk = renderer.load_walkthrough(slug)
        schema = package.read_json(walk.package / walk.document["data"])
        for item in schema["lists"]:
            download = f"studio/data/{item['id']}.csv"
            step = next(s for s in walk.document["modes"]["manual"]["steps"] if download in s.get("downloads", []))
            with (walk.package / download).open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            for column in item["columns"]:
                maximum = max(len(row[column["name"]]) for row in rows)
                if column["type"] == "text" and maximum > 255:
                    checked += 1
                    assert f"{column['name']} (up to {maximum} characters)" in step["action"], slug
                    assert "Multiple lines of text" in step["action"], slug
                    assert "stop and report the import limitation" in step["action"], slug
    assert checked > 0


@pytest.fixture
def lifecycle_validator():
    root = os.environ.get("AIBAST_BRAINFREEZE_ROOT")
    try:
        return package.managed_app_validator(Path(root) if root else None)
    except package.StudioPackageError:
        if root:
            raise
        pytest.skip("Set AIBAST_BRAINFREEZE_ROOT to run the real brainfreeze managed-app lifecycle validator")


def test_all_apps_pass_the_real_managed_app_validator(lifecycle_validator):
    slugs = data.studio_slugs()
    assert slugs
    for slug in slugs:
        spec = package.read_json(ROOT / "solutions" / slug / "studio/managed-app/app.json")
        assert lifecycle_validator(spec)["kind"] == "scenario-workspace", slug


def test_real_managed_app_validator_rejects_a_controlled_mutation(lifecycle_validator):
    spec = package.read_json(REFERENCE / "studio/managed-app/app.json")
    spec["tables"][0]["formats"]["Scope1CO2"] = "unsupported"
    with pytest.raises(package.StudioPackageError, match="formats"):
        lifecycle_validator(spec)


@pytest.mark.parametrize(("mutation", "message"), [
    ("mapping", "app fields must follow CSV order"),
    ("key", "app key must be"),
    ("format", "unsupported app format"),
    ("json", "complex JSON must not"),
])
def test_app_contract_checks_reject_controlled_mutations(tmp_path, mutation, message):
    inputs, schema, csvs = dataset(tmp_path, {"x": {"name": "Example", "events": [{"value": 1}]}})
    app = package.make_app(inputs, schema, csvs)
    document = {"agent": {"names": {"easy": "Sample Studio", "manual": "Sample Studio Manual"}}}
    tools = package.tool_names(schema, {})
    if mutation == "mapping":
        app["tables"][0]["fields"]["RecordId"] = "field_99"
    elif mutation == "key":
        app["tables"][0]["key"] = "Title"
    elif mutation == "format":
        app["tables"][0]["formats"]["RecordId"] = "unsupported"
    else:
        app["tables"][0]["columns"].append("Events")
    with pytest.raises(package.StudioPackageError, match=message):
        package.validate_package_contract(schema, app, document, tools)


@pytest.mark.parametrize(("mutation", "message"), [
    ("prompt", "must match locked case"),
    ("screenshot", "screenshot is required"),
    ("privacy", "Privacy check failed"),
])
def test_walkthrough_checks_reject_controlled_mutations(source_root, mutation, message):
    path = source_root / "solutions" / SAMPLE / "studio/walkthrough.json"
    document = package.read_json(path)
    if mutation == "prompt":
        next(step for step in document["modes"]["easy"]["steps"] if "case" in step)["prompt"] += " Changed"
    elif mutation == "screenshot":
        document["modes"]["easy"]["steps"][0].pop("screenshot")
    else:
        document["summary"] = "An invalid contact: fixture@example.invalid"
    write_json(path, document)
    with pytest.raises(renderer.WalkthroughError, match=message):
        renderer.load_walkthrough(SAMPLE, root=source_root)
