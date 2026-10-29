"""Community agents: the demo submission form, its checker, the page, and the
rule that community demos stay out of the agent library until one graduates."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from tests.test_catalog_export import probe, run_community_tools_node
from tools import demo_submission as ds

ROOT = Path(__file__).resolve().parents[1]
FORM = ROOT / ".github" / "ISSUE_TEMPLATE" / "demo-submission.yml"
WORKFLOW = ROOT / ".github" / "workflows" / "demo-submission.yml"
MANIFEST = json.loads((ROOT / "community_tools.json").read_text(encoding="utf-8"))
DEMOS = [t for t in MANIFEST["tools"] if t.get("kind") == "demo"]

SAMPLE_DEMO = {
    "id": "sample-community-demo",
    "kind": "demo",
    "name": "Sample Community Demo",
    "url": "https://www.youtube.com/watch?v=abc123",
    "author": "Sample Team",
    "description": "One sentence. Two sentences.",
    "industry": "Healthcare",
    "products": ["Copilot Studio"],
    "submission_issue": 1,
    "thumbnail": "https://i.ytimg.com/vi/abc123/hqdefault.jpg",
}


def filled_body(**overrides):
    values = {
        "title": "Tiered Digital Huddle Board",
        "video": "https://www.youtube.com/watch?v=9A8k0z77NFo",
        "description": (
            "A hospital runs its daily tiered huddles on one live board. "
            "Copilot briefs the whole board before the huddle. "
            "One approval escalates an issue up a tier and notifies the right people in Teams."
        ),
        "industry": "Healthcare",
        "team": "Microsoft Healthcare AI Business Process Solutions",
        "onepager": "_No response_",
        "products": ["Copilot Studio", "Dataverse", "Teams", "Power Apps"],
        "confirm": list(ds.REQUIRED_CONFIRMATIONS),
    }
    values.update(overrides)
    products = "\n".join(
        f"- [{'X' if p in values['products'] else ' '}] {p}" for p in ds.PRODUCT_OPTIONS
    )
    confirmations = "\n".join(
        f"- [{'X' if c in values['confirm'] else ' '}] {c}" for c in ds.REQUIRED_CONFIRMATIONS
    )
    return (
        f"### Demo title\n\n{values['title']}\n\n"
        f"### Public video URL\n\n{values['video']}\n\n"
        f"### Short description\n\n{values['description']}\n\n"
        f"### Industry\n\n{values['industry']}\n\n"
        f"### Microsoft products used\n\n{products}\n\n"
        f"### Owning team or channel\n\n{values['team']}\n\n"
        f"### One-pager URL (optional)\n\n{values['onepager']}\n\n"
        f"### Before you submit\n\n{confirmations}\n"
    )


# ------------------------------------------------------------------ the form
def test_form_parses_and_matches_the_checker():
    yaml = pytest.importorskip("yaml")
    form = yaml.safe_load(FORM.read_text(encoding="utf-8"))
    assert form["name"] == "Submit a demo to Community agents"
    assert form["labels"] == ["demo: submitted"]
    fields = {item["id"]: item for item in form["body"] if "id" in item}
    labels = {f["attributes"]["label"] for f in fields.values()}
    assert {ds.TITLE, ds.VIDEO, ds.DESCRIPTION, ds.INDUSTRY, ds.PRODUCTS,
            ds.TEAM, ds.ONEPAGER, ds.CONFIRMATIONS} == labels
    for required in ("title", "video", "description", "industry", "team"):
        assert fields[required]["validations"]["required"] is True
    assert tuple(fields["industry"]["attributes"]["options"]) == ds.INDUSTRIES
    assert tuple(o["label"] for o in fields["products"]["attributes"]["options"]) == ds.PRODUCT_OPTIONS
    confirm = fields["confirmations"]["attributes"]["options"]
    assert tuple(o["label"] for o in confirm) == ds.REQUIRED_CONFIRMATIONS
    assert all(o.get("required") is True for o in confirm)


def test_form_industries_match_the_library_names():
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    block = re.search(r"const CATEGORY_NAMES = \{(.*?)\};", index, re.S).group(1)
    names = set(re.findall(r':\s*"([^"]+)"', block))
    assert set(ds.INDUSTRIES) == names


def test_public_copy_follows_the_tone_rules():
    for path in (FORM, ROOT / "community-agents.html", ROOT / "community-tools.html"):
        text = path.read_text(encoding="utf-8")
        assert "RAPP Factory" not in text, path
        assert not re.search(r"[\U0001F300-\U0001FAFF]", text), path


# ------------------------------------------------------------- the checker
def test_parser_reads_a_filled_form():
    sections = ds.parse_issue_form(filled_body())
    assert sections[ds.TITLE] == "Tiered Digital Huddle Board"
    entry, problems = ds.validate(sections)
    assert problems == []
    assert entry["id"] == "tiered-digital-huddle-board"
    assert entry["kind"] == "demo"
    assert entry["products"] == ["Copilot Studio", "Dataverse", "Power Apps", "Teams"]
    assert entry["author"] == "Microsoft Healthcare AI Business Process Solutions"
    assert "onepager" not in entry


def test_unticked_confirmation_is_rejected():
    body = filled_body(confirm=list(ds.REQUIRED_CONFIRMATIONS[:-1]))
    _, problems = ds.validate(ds.parse_issue_form(body))
    assert any("no Azure services" in p for p in problems)


@pytest.mark.parametrize("url, message", [
    ("http://www.youtube.com/watch?v=x", "https"),
    ("https://example.com/video", "YouTube or Microsoft Stream"),
    ("https://user:pw@youtube.com/watch?v=x", "plain public"),
    ("not a url", "https"),
])
def test_bad_video_links_are_rejected(url, message):
    _, problems = ds.validate(ds.parse_issue_form(filled_body(video=url)))
    assert any(message in p for p in problems), problems


def test_allowed_video_hosts():
    assert ds.classify_video_url("https://youtu.be/9A8k0z77NFo") == "youtube"
    assert ds.classify_video_url("https://web.microsoftstream.com/video/abc") == "stream"


@pytest.mark.parametrize("field, text", [
    ("description", "Built in the RAPP Factory. Second sentence."),
    ("description", "This is confidential. Second sentence."),
    ("description", "Runs on Azure Functions. Second sentence."),
    ("team", "Contact jane@example.com"),
    ("team", "@someone"),
])
def test_forbidden_words_and_personal_contacts_are_rejected(field, text):
    _, problems = ds.validate(ds.parse_issue_form(filled_body(**{field: text})))
    assert problems


def test_description_length_is_two_to_four_sentences():
    _, problems = ds.validate(ds.parse_issue_form(filled_body(description="Only one.")))
    assert any("2 to 4 sentences" in p for p in problems)


def test_youtube_resolution_uses_oembed_and_keeps_https_thumbnail():
    seen = []

    def fetch(url):
        seen.append(url)
        return {"title": "t", "thumbnail_url": "https://i.ytimg.com/vi/x/hqdefault.jpg"}

    facts = ds.resolve_video("https://www.youtube.com/watch?v=x", "youtube", fetch=fetch)
    assert seen[0].startswith("https://www.youtube.com/oembed?")
    assert facts["thumbnail"] == "https://i.ytimg.com/vi/x/hqdefault.jpg"

    def missing(url):
        raise ValueError("404")

    with pytest.raises(ds.SubmissionError):
        ds.resolve_video("https://www.youtube.com/watch?v=x", "youtube", fetch=missing)


def test_apply_adds_then_replaces_the_demo_and_keeps_tools():
    manifest = json.loads(json.dumps(MANIFEST))
    tool_count = len([t for t in manifest["tools"] if t.get("kind", "tool") == "tool"])
    entry, _ = ds.validate(ds.parse_issue_form(filled_body()))
    entry["id"] = "unit-test-demo"
    ds.apply_entry(manifest, entry, 7, "2026-10-28")
    ds.apply_entry(manifest, dict(entry), 7, "2026-10-29")
    demos = [t for t in manifest["tools"] if t.get("id") == "unit-test-demo"]
    assert len(demos) == 1 and demos[0]["submission_issue"] == 7
    assert "_video_kind" not in demos[0]
    assert manifest["count"] == len(manifest["tools"])
    assert manifest["snapshot_date"] == "2026-10-29"
    assert len([t for t in manifest["tools"] if t.get("kind", "tool") == "tool"]) == tool_count


def test_apply_never_overwrites_a_related_resource():
    manifest = json.loads(json.dumps(MANIFEST))
    entry, _ = ds.validate(ds.parse_issue_form(filled_body()))
    entry["id"] = manifest["tools"][0]["id"]
    with pytest.raises(ds.SubmissionError):
        ds.apply_entry(manifest, entry, 3, "2026-10-28")


def test_check_cli_writes_result_and_comment(tmp_path):
    body = tmp_path / "body.md"
    body.write_text(filled_body(confirm=[]), encoding="utf-8")
    result, comment = tmp_path / "r.json", tmp_path / "c.md"
    subprocess.run(
        [sys.executable, str(ROOT / "tools" / "demo_submission.py"), "check", "--offline",
         "--body-file", str(body), "--result", str(result), "--comment", str(comment)],
        check=True, capture_output=True,
    )
    assert json.loads(result.read_text())["ok"] is False
    assert "needs a few changes" in comment.read_text()


# ------------------------------------------------------------ the workflow
def test_workflow_is_least_privilege_pinned_and_injection_safe():
    text = WORKFLOW.read_text(encoding="utf-8")
    yaml = pytest.importorskip("yaml")
    flow = yaml.safe_load(text)
    assert flow["permissions"] == {}
    assert flow["jobs"]["check"]["permissions"] == {"contents": "read", "issues": "write"}
    assert set(flow["jobs"]["approve"]["permissions"]) == {"contents", "issues", "pull-requests"}
    for uses in re.findall(r"uses:\s*(\S+)", text):
        assert re.search(r"@[0-9a-f]{40}$", uses), uses
    for job in flow["jobs"].values():
        for step in job["steps"]:
            run = step.get("run", "")
            assert "github.event.issue.body" not in run
            assert "github.event.issue.title" not in run
            assert "${{" not in run, step.get("name")
    assert "collaborators/$SENDER/permission" in text
    assert "Closes #" in text


# ----------------------------------------------------------------- the page
def test_page_has_shelf_submit_button_and_related_resources():
    page = BeautifulSoup((ROOT / "community-agents.html").read_text(encoding="utf-8"), "html.parser")
    assert page.title.get_text().startswith("Community agents")
    assert page.select_one("#demo-grid")
    assert page.select_one("#community-grid")
    assert page.find("h2", string="Colleague demos")
    assert page.find("h2", string="Related resources")
    submit = page.select_one("#submit-demo")
    assert submit.get_text(strip=True) == "Submit your demo"
    assert submit["href"].endswith("/issues/new?template=demo-submission.yml")
    assert "kody-w" not in str(page)
    assert 'data-clarity-project' in str(page)
    assert "aibast-design:start" in str(page)


def test_old_page_redirects_and_keeps_hash_and_query():
    text = (ROOT / "community-tools.html").read_text(encoding="utf-8")
    assert 'location.replace("community-agents.html" + location.search + location.hash)' in text
    assert 'content="0; url=community-agents.html"' in text
    page = BeautifulSoup(text, "html.parser")
    assert "This page is now Community agents" in page.body.get_text(" ", strip=True)
    assert page.select_one('body a[href="community-agents.html"]')


def test_page_renders_demos_as_cards_and_submit_points_at_this_repo():
    result = run_community_tools_node(
        f"""
community.tools.push({json.dumps({**SAMPLE_DEMO, "graduated_to": "tiered-huddle-board"})});
community.tools.push({json.dumps({**SAMPLE_DEMO, "id": "x2", "name": "<b>x</b>", "thumbnail": "javascript:1"})});
community.count = community.tools.length;
globalThis.fetch = async () => ({{ok: true, json: async () => community}});
const submit = {{href: ""}};
nodes.set("submit-demo", submit);
""",
        """
await renderCommunityTools();
console.log(JSON.stringify({
  demos: $("demo-grid").innerHTML, tools: $("community-grid").innerHTML,
  submit: $("submit-demo").href, errors
}));
""",
    )
    assert result["errors"] == []
    assert result["demos"].count('class="demo-card"') == len(DEMOS) + 2
    assert "Sample Team" in result["demos"]
    assert "Healthcare" in result["demos"]
    assert 'target="_blank"' in result["demos"]
    assert "<iframe" not in result["demos"]
    assert "&lt;b&gt;" in result["demos"]
    assert "javascript:" not in result["demos"]
    assert 'href="solution.html?id=tiered-huddle-board">Now in the library' in result["demos"]
    assert SAMPLE_DEMO["url"] not in result["tools"]
    # The harness serves the page from kody-w.github.io, so the form link follows it.
    assert result["submit"] == (
        "https://github.com/kody-w/aibast-agents-library/issues/new?template=demo-submission.yml"
    )


# ---------------------------------------------- isolation from the library
def test_manifest_stays_valid_for_both_kinds():
    assert MANIFEST["schema"] == "aibast-community-tools/1.0"
    assert MANIFEST["count"] == len(MANIFEST["tools"])
    assert "Community agents" in MANIFEST["note"]
    ids = [t["id"] for t in MANIFEST["tools"]]
    assert len(ids) == len(set(ids))
    for entry in MANIFEST["tools"]:
        assert entry.get("kind", "tool") in {"tool", "demo"}
        for key in ("id", "name", "url", "author", "description"):
            assert isinstance(entry[key], str) and entry[key].strip()
        assert entry["url"].startswith("https://")
    for demo in DEMOS:
        assert demo["industry"] in ds.INDUSTRIES
        assert demo["products"] and set(demo["products"]) <= set(ds.PRODUCT_OPTIONS)
        assert isinstance(demo["submission_issue"], int)
        assert ds.forbidden_terms_in(" ".join([demo["name"], demo["description"], demo["author"]])) == []


def test_registry_build_skips_demo_entries(tmp_path, monkeypatch):
    import build_registry

    manifest = json.loads(json.dumps(MANIFEST))
    manifest["tools"].append(SAMPLE_DEMO)
    manifest["count"] = len(manifest["tools"])
    path = tmp_path / "community_tools.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(build_registry, "COMMUNITY_TOOLS_FILE", path)
    errors = []
    rows = build_registry.load_community_tools(errors)
    assert errors == []
    assert all(r.get("kind", "tool") == "tool" for r in rows)
    assert SAMPLE_DEMO["id"] not in {r["id"] for r in rows}


def _library_surfaces():
    paths = [ROOT / "registry.json", ROOT / "solutions.json", ROOT / "academy.json",
             ROOT / "solutions" / "catalog.json"]
    paths += sorted((ROOT / "state").glob("*.json"))
    return [p for p in paths if p.exists()]


@pytest.mark.parametrize("demo", DEMOS or [SAMPLE_DEMO], ids=lambda d: d["id"])
def test_no_demo_appears_in_library_catalogs_academy_or_metrics(demo):
    registry = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))
    assert demo["id"] not in {t.get("id") for t in registry.get("community_tools", [])}
    assert all(t.get("kind", "tool") == "tool" for t in registry.get("community_tools", []))
    if demo.get("graduated_to"):
        return  # graduated demos live in the library under their template slug
    for path in _library_surfaces():
        text = path.read_text(encoding="utf-8")
        assert f'"{demo["id"]}"' not in text, path.relative_to(ROOT)


def test_library_page_only_links_community_agents_from_the_footer():
    page = BeautifulSoup((ROOT / "index.html").read_text(encoding="utf-8"), "html.parser")
    links = page.select('a[href^="community-agents.html"]')
    assert len(links) == 1
    assert links[0].find_parent("footer") is not None
    for demo in DEMOS:
        assert demo["name"] not in str(page)


def test_library_export_bundle_skips_demo_entries():
    result = probe(
        f"""
community.tools.push({json.dumps(SAMPLE_DEMO)});
community.count = community.tools.length;
globalThis.fetch = async path => ({{
  ok: true, json: async () => path === "registry.json" ? registry : community
}});
""",
        """
await exportRappWorkspace();
await new Promise(resolve => setTimeout(resolve, 1));
console.log(JSON.stringify({bundle: JSON.parse(await blobs[0].text()), errors}));
""",
    )
    tools = result["bundle"]["community_tools"]["tools"]
    assert result["errors"] == []
    assert all(t.get("kind", "tool") == "tool" for t in tools)
    assert result["bundle"]["community_tools"]["count"] == len(tools)
