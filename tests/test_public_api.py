"""The static public API: the extractor reads the named object exactly, and the published files keep their shape."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_public_api", ROOT / "scripts" / "build_public_api.py")
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


def test_js_object_reads_the_literal_exactly():
    source = """// header
const OTHER = {a: 1};
const CREDIT_RATES = {
    // Knowledge rates
    tenantGraphGrounding: 12,  // TGG
    otherKnowledge: 2,
    /* block */ agentFlowPerAction: 0.13,
};
function f() {}"""
    assert api.js_object(source, "CREDIT_RATES") == {"tenantGraphGrounding": 12, "otherKnowledge": 2, "agentFlowPerAction": 0.13}


def test_js_object_refuses_a_missing_symbol():
    try:
        api.js_object("const X = {\n a: 1\n};", "CREDIT_RATES")
    except ValueError:
        return
    raise AssertionError("a missing symbol must fail")


def test_published_files_carry_provenance():
    sources = json.loads((ROOT / "api/public/sources.json").read_text())["sources"]
    index = {item["id"]: item for item in json.loads((ROOT / "api/public/index.json").read_text())["sources"]}
    for source in sources:
        doc = json.loads((ROOT / "api/public" / (source["id"] + ".json")).read_text())
        assert doc["schema"] == "aibast-public-api/1" and doc["id"] == source["id"] and doc["data"]
        assert doc["provenance"]["page"] == source["page"] and len(doc["provenance"]["file_sha256"]) == 64
        assert doc["disclaimer"] and source["id"] in index


def test_pages_publishes_the_api():
    pages = importlib.util.spec_from_file_location("build_pages_site", ROOT / "scripts" / "build_pages_site.py")
    site = importlib.util.module_from_spec(pages)
    import sys
    sys.modules["build_pages_site"] = site   # its dataclasses resolve their module by name
    pages.loader.exec_module(site)
    from pathlib import PurePosixPath
    assert site.classify_source_path(PurePosixPath("api/public/copilot-credit-rates.json")) == site.INCLUDE
