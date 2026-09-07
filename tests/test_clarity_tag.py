"""Every published page carries one identical Microsoft Clarity tag."""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import apply_clarity_tag as clarity  # noqa: E402

BLOCK_RE = re.compile(
    re.escape(clarity.START_MARK) + r"(.*?)" + re.escape(clarity.END_MARK), re.DOTALL
)


def blocks(path):
    return BLOCK_RE.findall(path.read_text(encoding="utf-8"))


def test_config_names_a_valid_or_empty_project_id():
    config = json.loads((ROOT / "clarity.json").read_text(encoding="utf-8"))
    assert config["provider"] == "Microsoft Clarity"
    assert config["site"] == "https://microsoft.github.io/aibast-agents-library"
    project_id = config["project_id"]
    assert project_id == "" or clarity.PROJECT_ID_RE.match(project_id)


def test_every_public_page_carries_the_current_tag_once():
    pages = clarity.public_pages(ROOT)
    assert len(pages) > 200
    expected = clarity.render_tag(clarity.load_config()["project_id"])
    expected_body = BLOCK_RE.search(expected).group(1)
    for page in pages:
        found = blocks(page)
        assert found == [expected_body], page.relative_to(ROOT)
        html = page.read_text(encoding="utf-8")
        head_end = html.lower().index("</head>")
        assert html.index(clarity.START_MARK) < head_end, page.relative_to(ROOT)


def test_landing_catalog_metrics_and_solution_pages_are_covered():
    for relative in (
        "index.html",
        "library.html",
        "metrics.html",
        "docs/rapp-guide.html",
        "reports/impact-report.html",
        "solutions/ask-hr/quest.html",
    ):
        assert len(blocks(ROOT / relative)) == 1, relative


def test_installed_software_and_local_tools_are_never_tagged():
    for relative in (
        "rapp_brainstem/index.html",
        "rapp_ai/index.html",
        "beta/index.html",
        "beta/ui/index.html",
    ):
        path = ROOT / relative
        if path.exists():
            assert blocks(path) == [], relative
    for path in ROOT.glob("tools/*.html"):
        assert blocks(path) == [], path.relative_to(ROOT)


def test_check_mode_passes_on_the_committed_tree():
    assert clarity.main(["--check"]) == 0


def test_stamp_is_idempotent_and_replaces_stale_ids():
    old = clarity.render_tag("oldid12345")
    new = clarity.render_tag("newid12345")
    page = "<html><head><title>x</title>\n</head><body></body></html>"
    once = clarity.stamp(page, old)
    assert once.count(clarity.START_MARK) == 1
    assert clarity.stamp(once, old) == once
    swapped = clarity.stamp(once, new)
    assert swapped.count(clarity.START_MARK) == 1
    assert "oldid12345" not in swapped and 'data-clarity-project="newid12345"' in swapped
    with pytest.raises(ValueError):
        clarity.stamp("<html><body></body></html>", new)


def test_check_mode_flags_a_stale_page(tmp_path):
    (tmp_path / "clarity.json").write_text(json.dumps({"project_id": "abc1234567"}))
    (tmp_path / "index.html").write_text("<html><head></head><body></body></html>")
    assert clarity.main(["--check", "--root", str(tmp_path)]) == 1
    assert clarity.main(["--root", str(tmp_path)]) == 0
    assert clarity.main(["--check", "--root", str(tmp_path)]) == 0
    assert 'data-clarity-project="abc1234567"' in (tmp_path / "index.html").read_text()


def test_rejects_a_malformed_project_id(tmp_path):
    (tmp_path / "clarity.json").write_text(json.dumps({"project_id": "not a real id!"}))
    (tmp_path / "index.html").write_text("<html><head></head><body></body></html>")
    assert clarity.main(["--check", "--root", str(tmp_path)]) == 1


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js required")
def test_loader_only_runs_on_github_pages_and_honors_privacy_signals():
    body = BLOCK_RE.search(clarity.render_tag("abc1234567")).group(1)
    script = re.search(r"<script[^>]*>(.*?)</script>", body, re.DOTALL).group(1)
    harness = """
function run(hostname, nav, winDnt) {
  const inserted = [];
  const first = {};
  const document = {
    location: { hostname },
    createElement: () => ({}),
    getElementsByTagName: () => [Object.assign(first, {
      parentNode: { insertBefore: (el) => inserted.push(el.src) },
    })],
  };
  const window = { navigator: nav, doNotTrack: winDnt };
  (function (window, document) {
    %s
  })(window, document);
  return inserted;
}
const out = {
  pages: run("microsoft.github.io", {}, undefined),
  fork: run("kody-w.github.io", {}, undefined),
  local: run("localhost", {}, undefined),
  file: run("", {}, undefined),
  gpc: run("microsoft.github.io", { globalPrivacyControl: true }, undefined),
  dnt: run("microsoft.github.io", { doNotTrack: "1" }, undefined),
  winDnt: run("microsoft.github.io", {}, "1"),
};
console.log(JSON.stringify(out));
""" % script
    result = subprocess.run(["node"], input=harness, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    assert out["pages"] == ["https://www.clarity.ms/tag/abc1234567"]
    assert out["fork"] == ["https://www.clarity.ms/tag/abc1234567"]
    for key in ("local", "file", "gpc", "dnt", "winDnt"):
        assert out[key] == [], key
