"""Studio data: each workshop's synthetic records as CSV files for SharePoint lists (tools/build_studio_data.py)."""
import csv
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import build_studio_data as bsd

ROOT = Path(__file__).resolve().parent.parent


class StudioDataTests(unittest.TestCase):
    def test_every_studio_package_is_current(self):
        slugs = bsd.studio_slugs()
        self.assertIn("emission-tracking", slugs)
        for slug in slugs:
            with self.subTest(slug=slug):
                for list_id, text in bsd.build(slug).items():
                    path = ROOT / "solutions" / slug / "studio" / "data" / f"{list_id}.csv"
                    self.assertEqual(path.read_text(encoding="utf-8"), text, f"run tools/build_studio_data.py {slug}")

    def test_the_lists_hold_the_records_the_locked_cases_rest_on(self):
        rows = list(csv.DictReader(io.StringIO(bsd.build("emission-tracking")["facilities"])))
        values = next(r for r in rows if r["Title"] == "Ridgeline Coal Station")
        self.assertEqual(values["Location"], "Moffat County, CO", "a quoted comma stays in its column")
        total = int(values["Scope1CO2"]) + int(values["Scope2CO2"]) + int(values["Scope3CO2"])
        self.assertEqual(total, 1533200, "EMISSION_TRACKING-01 anchors 1,533,200")
        self.assertEqual(round(int(values["Scope1CO2"]) / int(values["ThresholdCO2"]) * 100, 1), 94.7)
        self.assertEqual(values["FacilityId"], "FAC-E03")

    def copy_package(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        schema = json.loads((ROOT / "solutions/emission-tracking/studio/data/schema.json").read_text())
        for rel in (schema["source"], schema["records_markdown"], "solutions/emission-tracking/studio/data/schema.json"):
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, tmp / rel)
        return tmp, schema

    def test_a_knowledge_file_that_drifts_from_the_agent_is_refused(self):
        tmp, schema = self.copy_package()
        md = tmp / schema["records_markdown"]
        md.write_text(md.read_text().replace('"co2_tonnes": 1420000', '"co2_tonnes": 1420001'))
        with self.assertRaisesRegex(bsd.StudioDataError, "differs from the agent's source"):
            bsd.build("emission-tracking", root=tmp)

    def test_a_field_without_a_column_is_an_error_not_an_omission(self):
        tmp, schema = self.copy_package()
        path = tmp / "solutions/emission-tracking/studio/data/schema.json"
        data = json.loads(path.read_text())
        data["lists"][0]["columns"] = [c for c in data["lists"][0]["columns"] if c["name"] != "Scope3N2O"]
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(bsd.StudioDataError, "fields with no column: emissions.scope_3.n2o_tonnes"):
            bsd.build("emission-tracking", root=tmp)

    def test_column_names_must_survive_sharepoint_import(self):
        base = json.loads((ROOT / "solutions/emission-tracking/studio/data/schema.json").read_text())
        for bad, why in [("Scope 1 CO2", "letters and digits"), ("Scope_1", "letters and digits")]:
            data = json.loads(json.dumps(base))
            data["lists"][0]["columns"][5]["name"] = bad
            with self.subTest(bad=bad), self.assertRaisesRegex(bsd.StudioDataError, why):
                bsd.check_schema(data)
        data = json.loads(json.dumps(base))
        data["lists"][0]["columns"].insert(0, data["lists"][0]["columns"].pop(1))
        with self.assertRaisesRegex(bsd.StudioDataError, "first column must be Title"):
            bsd.check_schema(data)


    def test_the_app_reads_the_columns_under_the_names_sharepoint_gives_them(self):
        """SharePoint's From CSV import keeps a header only as the display name and names the columns field_1,
        field_2, ... in CSV order (Title stays Title); Easy mode creates its lists the same way, so one mapping in
        the app spec serves lists made either way."""
        for slug in bsd.studio_slugs():
            app_path = ROOT / "solutions" / slug / "studio" / "managed-app" / "app.json"
            if not app_path.exists():
                continue
            schema = json.loads((ROOT / "solutions" / slug / "studio" / "data" / "schema.json").read_text())
            by_title = {lst["title"]: lst for lst in schema["lists"]}
            for table in json.loads(app_path.read_text())["tables"]:
                with self.subTest(slug=slug, table=table["id"]):
                    names = [c["name"] for c in by_title[table["list"]]["columns"] if c["name"] != "Title"]
                    self.assertEqual(table["fields"], {n: f"field_{i}" for i, n in enumerate(names, start=1)})


    def test_the_agent_instructions_map_every_list_column(self):
        """The list tools return field_N keys; the studio instructions must name each one exactly as the lists do."""
        for slug in bsd.studio_slugs():
            text = (ROOT / "solutions" / slug / "studio" / "agent" / "GLOBAL-INSTRUCTIONS.md").read_text()
            controls = ROOT / "solutions" / slug / "studio/agent/knowledge" / f"{slug}-instruction-controls.md"
            if controls.name in text:
                document = json.loads((ROOT / "solutions" / slug / "studio/walkthrough.json").read_text())
                self.assertIn(controls.relative_to(ROOT / "solutions" / slug).as_posix(),
                              document["agent"]["knowledge"])
                text += "\n" + controls.read_text()
            schema = json.loads((ROOT / "solutions" / slug / "studio" / "data" / "schema.json").read_text())
            for lst in schema["lists"]:
                names = [c["name"] for c in lst["columns"] if c["name"] != "Title"]
                with self.subTest(slug=slug, list=lst["id"]):
                    self.assertIn(f"(*{lst['title']}*)", text)
                    self.assertIn(", ".join(f"`field_{i}` {n}" for i, n in enumerate(names, start=1)) + ".", text)


if __name__ == "__main__":
    unittest.main()
