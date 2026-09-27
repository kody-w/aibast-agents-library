from __future__ import annotations

import html
import json
import re
import shutil
import struct
import subprocess
import sys
import zlib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

from tools import render_studio_walkthrough as studio
from tools import scaffold_solution_journey as scaffold
from tools.design_tokens import render_tokens


ROOT = Path(__file__).resolve().parents[1]
SLUG = "emission-tracking"
PACKAGE = ROOT / "solutions" / SLUG
DELETE = object()


class PageParser(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, content: str):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.elements = []
        self.ids = {}
        self.text = {}
        self.scripts = []
        self.feed(content)
        self.close()
        assert not self.stack, f"Unclosed elements: {self.stack}"

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        assert len(attributes) == len(attrs), f"Duplicate attribute on {tag}"
        self.elements.append((tag, attributes))
        if "id" in attributes:
            identity = attributes["id"]
            assert identity not in self.ids, f"Duplicate id: {identity}"
            self.ids[identity] = (tag, attributes)
            self.text[identity] = ""
        if tag == "script":
            self.scripts.append("")
        if tag not in self.VOID:
            self.stack.append((tag, attributes))

    def handle_endtag(self, tag):
        assert self.stack, f"Unexpected closing tag: {tag}"
        opened, _attributes = self.stack.pop()
        assert tag == opened, f"Closing {tag} while {opened} is open"

    def handle_data(self, text):
        for _tag, attributes in self.stack:
            if "id" in attributes:
                self.text[attributes["id"]] += text
        if self.stack and self.stack[-1][0] == "script":
            self.scripts[-1] += text

    def find(self, tag):
        return [attributes for element, attributes in self.elements if element == tag]


def write_json(path: Path, document) -> None:
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def seed_package(root: Path) -> Path:
    package = root / "solutions" / SLUG
    shutil.copytree(PACKAGE / "studio", package / "studio")
    document = json.loads((package / "studio/walkthrough.json").read_text(encoding="utf-8"))
    schema = json.loads((package / document["data"]).read_text(encoding="utf-8"))
    sources = [
        Path(document["cases"]),
        Path(schema["source"]),
        Path(schema["records_markdown"]),
        *(Path("solutions") / SLUG / path for path in document["agent"]["knowledge"]),
    ]
    sources += [
        Path("solutions") / SLUG / shot["file"]
        for mode in document["modes"].values() for step in mode["steps"]
        for shot in studio.screenshot_list(step["screenshot"]) if shot["status"] == "reviewed"
    ]
    for relative in sources:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    (package / "quest.html").write_text("<!doctype html><html lang=\"en\"><body>Workshop</body></html>", encoding="utf-8")
    (root / "academy.html").write_text("<!doctype html><html lang=\"en\"><body>Academy</body></html>", encoding="utf-8")
    return package


@pytest.fixture
def source(tmp_path):
    package = seed_package(tmp_path)
    path = package / "studio/walkthrough.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    # The tests below edit easy-03 as a single pending capture; pin that state so they do not depend on how
    # far the live reference package's captures have progressed.
    document["modes"]["easy"]["steps"][2]["screenshot"] = {"file": "screenshots/studio-easy/03-lists.webp",
                                                           "status": "pending"}
    path.write_text(json.dumps(document, indent=1) + "\n", encoding="utf-8")
    return tmp_path, package, path, document


def mutate(document, keys, value):
    target = document
    for key in keys[:-1]:
        target = target[key]
    if value is DELETE:
        del target[keys[-1]]
    else:
        target[keys[-1]] = value


def write_png(path: Path, width: int, height: int) -> None:
    """A real, decodable RGB PNG (white) built with the stdlib."""
    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    rows = b"".join(b"\x00" + b"\xff" * (3 * width) for _ in range(height))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def webp_header(width: int, height: int) -> bytes:
    bits = (width - 1) | (height - 1) << 14
    body = b"\x2f" + bits.to_bytes(4, "little") + b"\x00" * 8
    return b"RIFF" + struct.pack("<I", 4 + 8 + len(body)) + b"WEBP" + b"VP8L" + struct.pack("<I", len(body)) + body


def reviewed_fixture(package, document, *, width=128, height=64, density=2):
    shot = document["modes"]["easy"]["steps"][2]["screenshot"]
    shot["file"] = shot["file"].rsplit(".", 1)[0] + ".png"
    write_png(package / shot["file"], width, height)
    shot.update(
        status="reviewed",
        alt='Reviewed fixture: Draft agent & "Build" tab',
        anchors=["Draft", "Build tab", "Synthetic records"],
        captured_at="2026-09-26T18:00:00Z",
        width=width,
        height=height,
        density=density,
    )
    return shot


def assert_links_resolve(page, package, root):
    parser = PageParser(page)
    for tag, attributes in parser.elements:
        for attribute in ("href", "src"):
            if attribute not in attributes:
                continue
            value = urlsplit(attributes[attribute])
            if value.scheme or value.netloc:
                continue
            target = (package / unquote(value.path)).resolve() if value.path else None
            if target is not None:
                assert target.is_relative_to(root.resolve()), attributes[attribute]
                assert target.is_file(), attributes[attribute]
            if value.fragment:
                target_parser = PageParser(target.read_text(encoding="utf-8")) if target else parser
                assert unquote(value.fragment) in target_parser.ids, attributes[attribute]
            if tag == "a" and "download" in attributes:
                assert target is not None and target.is_file()
    return parser


def test_render_is_deterministic_and_matches_committed_pages():
    slugs = studio.discover_slugs(ROOT)
    assert SLUG in slugs
    for slug in slugs:
        first = studio.render_walkthrough(slug)
        second = studio.render_walkthrough(slug)
        assert first == second
        assert (ROOT / "solutions" / slug / "studio-tutorial.html").read_bytes() == first.encode("utf-8")
        assert "Generated by tools/render_studio_walkthrough.py" in first
        assert "Do not edit this page" in first
        assert render_tokens() in first


def test_cli_check_parity_for_every_studio_package():
    result = subprocess.run(
        [sys.executable, "tools/render_studio_walkthrough.py", "--check"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert f"Checked {len(studio.discover_slugs(ROOT))} studio tutorial(s)." in result.stdout


def test_check_fails_on_missing_and_stale_pages_without_writing(source, capsys):
    root, package, _path, _document = source
    page = package / "studio-tutorial.html"
    assert studio.main(["--check"], root=root) == 1
    assert not page.exists()
    assert "Stale studio tutorial" in capsys.readouterr().err
    assert studio.main([], root=root) == 0
    original = page.read_bytes()
    assert studio.main([SLUG, "--check"], root=root) == 0
    page.write_bytes(original + b"\n<!-- controlled stale page -->\n")
    changed = page.read_bytes()
    assert studio.main(["--check"], root=root) == 1
    assert page.read_bytes() == changed
    page.write_bytes(original)
    assert studio.main(["--check"], root=root) == 0
    assert page.read_bytes() == original


def test_cli_validates_all_inputs_before_writing(source, capsys):
    root, package, _path, _document = source
    assert studio.main([SLUG, "missing-package"], root=root) == 2
    assert not (package / "studio-tutorial.html").exists()
    assert "missing directory solutions/missing-package" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("keys", "value", "message"),
    [
        (("schema",), "studio/unsupported", "schema"),
        (("solution",), "another-solution", "solution"),
        (("title",), DELETE, "title"),
        (("summary",), "", "summary"),
        (("data",), DELETE, "data"),
        (("agent",), [], "agent must be an object"),
        (("agent", "instructions"), DELETE, "instructions"),
        (("agent", "skills"), DELETE, "skills"),
        (("agent", "knowledge"), DELETE, "knowledge"),
        (("agent", "model"), " ", "model"),
        (("agent", "names", "easy"), DELETE, "names.easy"),
        (("app",), None, "app must be an object"),
        (("app", "spec"), DELETE, "spec"),
        (("app", "names", "manual"), DELETE, "names.manual"),
        (("cases",), DELETE, "locked tests/demo_cases"),
        (("modes", "manual"), DELETE, "exactly easy and manual"),
        (("modes", "easy", "title"), "", "title"),
        (("modes", "easy", "steps"), [], "non-empty array"),
        (("modes", "easy", "steps", 0), None, "must be an object"),
        (("modes", "easy", "steps", 0, "id"), DELETE, "id"),
        (("modes", "easy", "steps", 0, "title"), DELETE, "title"),
        (("modes", "easy", "steps", 0, "action"), "", "action"),
        (("modes", "easy", "steps", 0, "expected"), DELETE, "expected"),
        (("modes", "easy", "steps", 0, "screenshot"), DELETE, "screenshot is required"),
        (("modes", "easy", "steps", 0, "commands"), "echo wrong type", "array"),
        (("modes", "easy", "steps", 0, "commands"), [""], "non-empty string"),
        (("modes", "easy", "steps", 0, "downloads"), {}, "array"),
        (("modes", "easy", "steps", 0, "prompt"), "", "prompt"),
        (("modes", "easy", "steps", 1, "id"), "easy-01", "unique"),
        (("modes", "easy", "steps", 1, "id"), "easy-03", "ordered"),
        (("modes", "manual", "steps", 0, "id"), "easy-01", "unique"),
        (("modes", "easy", "steps", 2, "screenshot", "status"), "captured", "pending or reviewed"),
        (("modes", "easy", "steps", 2, "screenshot", "file"), DELETE, "file"),
    ],
)
def test_invalid_contract_fails_closed(source, keys, value, message):
    root, _package, path, document = source
    mutate(document, keys, value)
    write_json(path, document)
    with pytest.raises(studio.WalkthroughError, match=message):
        studio.render_walkthrough(SLUG, root=root)


@pytest.mark.parametrize(
    "relative",
    [
        "solutions/emission-tracking/studio/data/schema.json",
        "solutions/emission-tracking/studio/data/facilities.csv",
        "solutions/emission-tracking/studio/agent/GLOBAL-INSTRUCTIONS.md",
        "solutions/emission-tracking/studio/agent/skills",
        "solutions/emission-tracking/studio/agent/skills/aibast_compliance-status/SKILL.md",
        "solutions/emission-tracking/manual/knowledge/emission-tracking-rules-and-controls.md",
        "solutions/emission-tracking/studio/managed-app/app.json",
        "tests/demo_cases/emission-tracking.json",
    ],
)
def test_every_referenced_file_must_exist(source, relative):
    root, _package, _path, _document = source
    missing = root / relative
    if missing.is_dir():
        shutil.rmtree(missing)
    else:
        missing.unlink()
    with pytest.raises(studio.WalkthroughError, match="missing"):
        studio.render_walkthrough(SLUG, root=root)


@pytest.mark.parametrize("field", ["source", "records_markdown"])
def test_data_provenance_files_must_exist(source, field):
    root, package, _path, document = source
    schema = json.loads((package / document["data"]).read_text(encoding="utf-8"))
    (root / schema[field]).unlink()
    with pytest.raises(studio.WalkthroughError, match="missing"):
        studio.render_walkthrough(SLUG, root=root)


def test_additional_downloads_must_exist(source):
    root, _package, path, document = source
    document["modes"]["easy"]["steps"][0]["downloads"] = ["studio/missing.md"]
    write_json(path, document)
    with pytest.raises(studio.WalkthroughError, match="downloads entry: missing"):
        studio.render_walkthrough(SLUG, root=root)


@pytest.mark.parametrize("path_value", ["../README.md", "/outside.md", "https://example.invalid/input.md", "studio/data/facilities.csv?raw=1", "studio\\data\\facilities.csv"])
def test_referenced_paths_cannot_escape_or_be_urls(source, path_value):
    root, _package, path, document = source
    document["agent"]["instructions"] = path_value
    write_json(path, document)
    with pytest.raises(studio.WalkthroughError, match="safe relative repository path"):
        studio.render_walkthrough(SLUG, root=root)


def test_referenced_symlinks_fail_closed(source):
    root, package, path, document = source
    alias = package / "studio/instructions-link.md"
    alias.symlink_to(package / document["agent"]["instructions"])
    document["agent"]["instructions"] = alias.relative_to(package).as_posix()
    write_json(path, document)
    with pytest.raises(studio.WalkthroughError, match="symlink"):
        studio.render_walkthrough(SLUG, root=root)


def test_empty_skills_directory_fails_closed(source):
    root, package, _path, document = source
    for skill in (package / document["agent"]["skills"]).rglob("SKILL.md"):
        skill.unlink()
    with pytest.raises(studio.WalkthroughError, match="at least one SKILL.md"):
        studio.render_walkthrough(SLUG, root=root)


@pytest.mark.parametrize("mutation", ["drift", "trailing-space", "missing-prompt", "missing-case", "redirect-cases"])
def test_locked_case_ids_and_exact_prompts_fail_closed(source, mutation):
    root, _package, path, document = source
    step = document["modes"]["easy"]["steps"][4]
    if mutation == "drift":
        step["prompt"] = "Invent a different answer."
    elif mutation == "trailing-space":
        step["prompt"] += " "
    elif mutation == "missing-prompt":
        del step["prompt"]
    elif mutation == "missing-case":
        step["case"] = "EMISSION_TRACKING-UNKNOWN"
    else:
        alternative = root / "tests/demo_cases/alternative.json"
        shutil.copyfile(root / document["cases"], alternative)
        document["cases"] = "tests/demo_cases/alternative.json"
    write_json(path, document)
    with pytest.raises(studio.WalkthroughError, match="locked"):
        studio.render_walkthrough(SLUG, root=root)


@pytest.mark.parametrize(
    ("field", "value"),
    [("alt", DELETE), ("alt", " "), ("anchors", DELETE), ("anchors", []), ("anchors", [""]), ("captured_at", DELETE), ("captured_at", "not a date")],
)
def test_reviewed_captures_require_review_metadata(source, field, value):
    root, package, path, document = source
    shot = reviewed_fixture(package, document)
    mutate(shot, (field,), value)
    write_json(path, document)
    with pytest.raises(studio.WalkthroughError, match=field):
        studio.render_walkthrough(SLUG, root=root)


def test_reviewed_capture_file_must_exist(source):
    root, package, path, document = source
    shot = reviewed_fixture(package, document)
    (package / shot["file"]).unlink()
    write_json(path, document)
    with pytest.raises(studio.WalkthroughError, match="screenshot.file: missing file"):
        studio.render_walkthrough(SLUG, root=root)


PRIVATE_VALUES = [
    ("email address", "reviewer@example.com"),
    ("email address", "reviewer&#64;example.com"),
    ("email address", "reviewer%40example.com"),
    ("tenant host", "https://real-customer.sharepoint.com/sites/team"),
    ("tenant host", "REAL-CUSTOMER.crm4.dynamics.com"),
    ("tenant host", "https://real-customer.powerapps.com"),
    ("tenant host", "https://notcontoso.sharepoint.com"),
    ("tenant host", "https://contoso.real-customer.sharepoint.com"),
    ("tenant host", "https://real-customer%2Esharepoint.com"),
    ("GUID-shaped id", "12345678-1234-1234-1234-123456789abc"),
]


@pytest.mark.parametrize(("kind", "value"), PRIVATE_VALUES)
@pytest.mark.parametrize("field", ["summary", "unrendered_metadata"])
def test_private_walkthrough_strings_fail_closed(source, kind, value, field):
    root, _package, path, document = source
    document[field] = value if field == "summary" else {"nested": [value]}
    write_json(path, document)
    with pytest.raises(studio.WalkthroughError, match=kind):
        studio.render_walkthrough(SLUG, root=root)


@pytest.mark.parametrize(("kind", "value"), [PRIVATE_VALUES[0], PRIVATE_VALUES[3], PRIVATE_VALUES[-1]])
def test_privacy_is_rechecked_on_the_rendered_page(source, kind, value):
    root, package, _path, document = source
    app_path = package / document["app"]["spec"]
    app = json.loads(app_path.read_text(encoding="utf-8"))
    app["name"] = value
    write_json(app_path, app)
    with pytest.raises(studio.WalkthroughError, match=f"rendered page: {kind}"):
        studio.render_walkthrough(SLUG, root=root)


@pytest.mark.parametrize(
    "host",
    ["contoso.sharepoint.com", "contoso.crm.dynamics.com", "contoso.crm4.dynamics.com", "contoso.powerapps.com", "<your-tenant>.sharepoint.com", "<your-org>.crm.dynamics.com", "<your-env>.powerapps.com"],
)
def test_contoso_and_angle_bracket_host_placeholders_are_allowed(source, host):
    root, _package, path, document = source
    document["summary"] += f" Use https://{host}."
    write_json(path, document)
    assert html.escape(host) in studio.render_walkthrough(SLUG, root=root)


def test_page_structure_copy_payloads_progress_and_local_links(source):
    root, package, _path, document = source
    page = studio.render_walkthrough(SLUG, root=root)
    parser = assert_links_resolve(page, package, root)
    assert parser.find("html")[0]["lang"] == "en"
    assert parser.ids["course-content"][1]["tabindex"] == "-1"
    assert {"#easy", "#manual"} <= {link.get("href") for link in parser.find("a")}
    assert parser.ids["easy"][1]["data-mode-panel"] == "easy"
    assert parser.ids["manual"][1]["data-mode-panel"] == "manual"
    assert "hidden" not in parser.ids["easy"][1]
    assert "hidden" not in parser.ids["manual"][1]
    assert len(parser.find("article")) == sum(len(mode["steps"]) for mode in document["modes"].values())
    for mode, lane in document["modes"].items():
        for index, step in enumerate(lane["steps"], 1):
            assert parser.text[f'{step["id"]}-title'] == step["title"]
            checkbox = parser.ids[f'{step["id"]}-complete'][1]
            assert checkbox["data-progress-key"] == f'aibast:{SLUG}:studio:{mode}:{step["id"]}'
            assert checkbox["data-mode"] == mode
            assert checkbox["data-step"] == step["id"]
            for command_index, command in enumerate(step.get("commands", []), 1):
                assert parser.text[f'{step["id"]}-command-{command_index}'] == command
            if "prompt" in step:
                assert parser.text[f'{step["id"]}-prompt'] == step["prompt"]
            report = next(
                button for button in parser.find("button")
                if button.get("data-report-location") == f'Studio edition — {mode.title()} mode — step {index}: {step["title"]}'
            )
            assert report["data-report-expected"] == step["expected"]
            assert report["data-report-evidence"]
    assert "4 synthetic records" in page and "3 synthetic records" in page
    for name in ("Get facility records", "Get carbon offset records", "Get regulation records", "Sonnet 4.6"):
        assert name in page
    assert "Emissions Tracking Workspace Manual" in page
    assert "Synthetic data only" in page and "not claims that a live run has passed" in page
    assert all("src" not in script for script in parser.find("script"))
    assert "aibast-workshop-feedback:v1" in page
    assert "window.open(url.toString()" in page
    assert "storage.setItem(box.dataset.progressKey" in page


def test_pending_never_renders_fake_images(source):
    root, package, _path, document = source
    pending = document["modes"]["easy"]["steps"][2]["screenshot"]
    existing = package / pending["file"]
    existing.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(PACKAGE / "screenshots/manual/01-create-blank-agent.jpg", existing)
    page = studio.render_walkthrough(SLUG, root=root)
    shots = [shot for mode in document["modes"].values() for step in mode["steps"]
             for shot in studio.screenshot_list(step["screenshot"])]
    reviewed = [shot["file"] for shot in shots if shot["status"] == "reviewed"]
    assert [image["src"] for image in PageParser(page).find("img")] == reviewed
    assert page.count("Screenshot pending") == sum(shot["status"] == "pending" for shot in shots)
    assert "A real capture will be added after this step is run live and reviewed." in page
    assert f'href="{pending["file"]}"' not in page


@pytest.mark.parametrize("value", [None, []])
def test_every_step_must_show_a_capture(source, value):
    root, _package, path, document = source
    document["modes"]["easy"]["steps"][0]["screenshot"] = value
    write_json(path, document)
    with pytest.raises(studio.WalkthroughError, match="screenshot"):
        studio.load_walkthrough(SLUG, root=root)


def test_reviewed_capture_has_alt_lazy_original_and_visible_anchors(source):
    root, package, path, document = source
    shot = reviewed_fixture(package, document)
    write_json(path, document)
    page = studio.render_walkthrough(SLUG, root=root)
    card = re.search(r'<article class="step" id="easy-03".*?</article>', page, re.DOTALL)[0]
    assert_links_resolve(page, package, root)
    parser = PageParser(card)
    assert parser.find("img") == [{
        "class": "shot", "data-evidence-status": "reviewed", "src": shot["file"],
        "srcset": f'{shot["file"]} 2x', "width": "64", "height": "32",
        "alt": shot["alt"], "loading": "lazy",
    }]
    assert ".shot { display: block; max-width: 100%; height: auto;" in page
    assert all(anchor in page for anchor in shot["anchors"])
    assert f'href="{shot["file"]}" download>Download original</a> (128×64)' in page


def test_one_x_capture_displays_at_its_own_size(source):
    root, package, path, document = source
    shot = reviewed_fixture(package, document, width=90, height=40, density=1)
    write_json(path, document)
    img = PageParser(studio.render_walkthrough(SLUG, root=root)).find("img")[0]
    assert (img["srcset"], img["width"], img["height"]) == (f'{shot["file"]} 1x', "90", "40")


@pytest.mark.parametrize(("change", "message"), [
    ({"width": 130}, "declares 130x64 but the image is 128x64"),
    ({"density": 3}, "density must be 1 or 2"),
    ({"density": None}, "density must be 1 or 2"),
    ({"width": 127}, "divisible by density"),
    ({"height": "64"}, "divisible by density"),
])
def test_reviewed_capture_must_declare_its_true_size(source, change, message):
    root, package, path, document = source
    reviewed_fixture(package, document)["file"]
    document["modes"]["easy"]["steps"][2]["screenshot"].update(change)
    write_json(path, document)
    with pytest.raises(studio.WalkthroughError, match=re.escape(message)):
        studio.load_walkthrough(SLUG, root=root)


def test_a_step_may_show_several_captures_in_order(source):
    root, package, path, document = source
    first = reviewed_fixture(package, document)
    second = dict(first, file=first["file"].replace(".png", "-b.png"), alt="Second reviewed fixture",
                  width=64, height=32, anchors=["Second view"])
    write_png(package / second["file"], 64, 32)
    third = {"file": first["file"].replace(".png", "-c.webp"), "status": "pending"}
    document["modes"]["easy"]["steps"][2]["screenshot"] = [first, second, third]
    write_json(path, document)
    page = studio.render_walkthrough(SLUG, root=root)
    card = re.search(r'<article class="step" id="easy-03".*?</article>', page, re.DOTALL)[0]
    images = PageParser(card).find("img")
    assert [image["src"] for image in images] == [first["file"], second["file"]]
    assert [image["width"] for image in images] == ["64", "32"]
    assert card.count("Screenshot pending") == 1 and "Second view" in card


def test_image_size_reads_png_webp_and_jpeg_headers(tmp_path):
    png = tmp_path / "a.png"
    write_png(png, 30, 12)
    webp = tmp_path / "b.webp"
    webp.write_bytes(webp_header(2864, 1764))
    assert studio.image_size(png) == (30, 12)
    assert studio.image_size(webp) == (2864, 1764)
    assert studio.image_size(PACKAGE / "screenshots/manual/01-create-blank-agent.jpg") == (1424, 863)
    junk = tmp_path / "c.webp"
    junk.write_bytes(b"not an image at all, only text")
    with pytest.raises(studio.WalkthroughError, match="not a readable"):
        studio.image_size(junk)


def test_markup_is_escaped_without_changing_copy_text(source):
    root, _package, path, document = source
    step = document["modes"]["easy"]["steps"][0]
    step["title"] = '<script>alert("not markup")</script> & title'
    step["commands"] = ['printf "<tag> & quotes"\r\n  keep spaces  ']
    write_json(path, document)
    page = studio.render_walkthrough(SLUG, root=root)
    parser = PageParser(page)
    assert parser.text["easy-01-title"] == step["title"]
    assert parser.text["easy-01-command-1"] == step["commands"][0]
    assert len(parser.find("script")) == 3


def test_inline_javascript_parses():
    node = shutil.which("node")
    assert node, "node is required for the workshop JavaScript gate"
    parser = PageParser(studio.render_walkthrough(SLUG))
    result = subprocess.run(
        [node, "--check"], input="\n".join(parser.scripts),
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr


def test_conditional_scaffold_links_are_the_only_generated_changes(monkeypatch):
    context = scaffold.load_context(ROOT, SLUG, allow_pending=True, raw_base=scaffold.DEFAULT_RAW_BASE)
    resources = scaffold.collect_resources(context)
    with_link = scaffold.render_quest(context, resources)
    readme_with_link = scaffold.readme_block(context, resources)
    contract = PACKAGE / "studio/walkthrough.json"
    actual_is_file = Path.is_file
    monkeypatch.setattr(Path, "is_file", lambda path: False if path == contract else actual_is_file(path))
    without_link = scaffold.render_quest(context, resources)
    readme_without_link = scaffold.readme_block(context, resources)
    link = '<a class="button" href="studio-tutorial.html">Studio edition</a>'
    row = f"| Studio edition tutorial | [`solutions/{SLUG}/studio-tutorial.html`](studio-tutorial.html) |\n"
    assert with_link.count(link) == 1
    assert readme_with_link.count(row) == 1
    assert with_link.replace(link, "") == without_link
    assert readme_with_link.replace(row, "") == readme_without_link


@pytest.mark.parametrize(("names", "message"), [
    ({"easy": "Emissions Tracking Studio", "manual": "Emissions Tracking Studio Manual"}, "32 characters"),
    ({"easy": "E" * 31, "manual": "Emissions Studio Manual"}, "31 characters"),
    ({"easy": "Same Name", "manual": "Same Name"}, "must differ"),
])
def test_agent_names_fit_copilot_studio(source, names, message):
    root, _package, path, document = source
    document["agent"]["names"] = names
    write_json(path, document)
    with pytest.raises(studio.WalkthroughError, match=message):
        studio.load_walkthrough(SLUG, root=root)


def test_thirty_character_agent_name_is_accepted(source):
    root, _package, path, document = source
    document["agent"]["names"]["easy"] = "E" * 30
    write_json(path, document)
    studio.load_walkthrough(SLUG, root=root)
