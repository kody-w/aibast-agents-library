"""Focused contracts for the staging librarian and library-source intake."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import unittest
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
LIBRARIAN = ROOT / "scripts" / "librarian_pipeline.py"
SUBMISSIONS = ROOT / "submissions" / "libraries"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ContributionGroupParser(HTMLParser):
    """Tracks form/div ancestry without treating void controls as containers."""

    def __init__(self):
        super().__init__()
        self.stack: list[str | None] = []
        self.parents: dict[str, str | None] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        if tag not in {"form", "div"}:
            return
        element_id = dict(attrs).get("id")
        if element_id in {"blog-contribution-fields", "library-source-fields"}:
            self.parents[element_id] = self.stack[-1] if self.stack else None
        self.stack.append(element_id)

    def handle_endtag(self, tag: str):
        if tag in {"form", "div"} and self.stack:
            self.stack.pop()


class LibrarianPipelineTests(unittest.TestCase):
    def execute_handoff(self, source: str, setup: str, function: str) -> str:
        self.assertTrue(shutil.which("node"), "node is required to exercise the handoff contract")
        program = f"""
const vm = require("vm");
const opened = [];
const sandbox = {{
  URL,
  window: {{ open: (url) => opened.push(url) }},
  {setup}
}};
vm.createContext(sandbox);
vm.runInContext({json.dumps(source)}, sandbox);
sandbox.{function}();
process.stdout.write(opened[0] || "");
"""
        result = subprocess.run(
            ["node", "-e", program],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue(result.stdout, "handoff did not open a URL")
        return result.stdout

    def evaluate_javascript(self, source: str, setup: str, expression: str):
        self.assertTrue(shutil.which("node"), "node is required to exercise the browser contract")
        program = f"""
const vm = require("vm");
const sandbox = {{ URL }};
vm.createContext(sandbox);
vm.runInContext({json.dumps(setup)}, sandbox);
vm.runInContext({json.dumps(source)}, sandbox);
process.stdout.write(JSON.stringify(vm.runInContext({json.dumps(expression)}, sandbox)));
"""
        result = subprocess.run(
            ["node", "-e", program],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_library_sources_validate_and_generated_catalog_has_no_drift(self):
        pipeline = load_module("librarian_pipeline", LIBRARIAN)
        submissions, errors = pipeline.validate_all(SUBMISSIONS)
        self.assertEqual([], errors)
        self.assertGreaterEqual(len(submissions), 1)
        result = subprocess.run(
            [sys.executable, str(LIBRARIAN), "check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        catalog = json.loads((ROOT / "state" / "libraries.json").read_text(encoding="utf-8"))
        self.assertEqual("library-slug:item-slug", catalog["item_namespace"])
        self.assertIn("items", catalog)
        source = next(source for source in catalog["sources"] if source["slug"] == "aibast-agents-library")
        for field in (
            "canonical_url",
            "immutable_ref",
            "manifest_locator",
            "spdx_license",
            "owner",
            "trust_tier",
            "status",
            "enabled",
            "source_digest",
            "review_cadence",
        ):
            self.assertIn(field, source)
        self.assertIn(source["immutable_ref"], source["canonical_url"])

    def test_nonexecuting_candidate_validator_checks_hash_and_utf8(self):
        snapshot = load_module("librarian_snapshot", ROOT / "scripts" / "librarian_snapshot.py")
        candidate = ROOT / "state" / "libraries.json"
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        self.assertEqual([], snapshot.validate_candidate(candidate, digest))

    def test_oversized_candidate_is_rejected_before_reading_bytes(self):
        snapshot = load_module("librarian_snapshot", ROOT / "scripts" / "librarian_snapshot.py")

        class OversizedCandidate:
            suffix = ".zip"

            def __init__(self):
                self.read_attempted = False

            def __str__(self):
                return "oversized-candidate.zip"

            def is_symlink(self):
                return False

            def is_file(self):
                return True

            def stat(self):
                return SimpleNamespace(st_size=snapshot.MAX_BYTES + 1)

            def read_bytes(self):
                self.read_attempted = True
                raise AssertionError("oversized candidates must not be read")

        candidate = OversizedCandidate()
        self.assertEqual(
            [f"oversized-candidate.zip: candidate exceeds {snapshot.MAX_BYTES} byte limit"],
            snapshot.validate_candidate(candidate, "0" * 64),
        )
        self.assertFalse(candidate.read_attempted)

    def test_snapshot_sidecars_preserve_namespaced_metric_shape(self):
        metrics = json.loads((ROOT / "state" / "libraries.metrics.json").read_text(encoding="utf-8"))
        snapshot = json.loads((ROOT / "state" / "libraries.snapshot.json").read_text(encoding="utf-8"))
        self.assertEqual("library-slug:item-slug", metrics["item_namespace"])
        self.assertIn("last_known_good_sources", snapshot)
        self.assertEqual("metadata_only_no_remote_acquisition", snapshot["sync_mode"])
        discussions = json.loads((ROOT / "state" / "library_discussions.json").read_text(encoding="utf-8"))
        self.assertEqual("Ideas", discussions["source_suggestion_category"])
        self.assertEqual("Announcements", discussions["approved_item_category"])
        self.assertEqual("library-slug:item-slug", discussions["item_namespace"])

    def test_internal_workshop_source_is_public_safe_and_first(self):
        catalog = json.loads((ROOT / "state" / "libraries.json").read_text(encoding="utf-8"))
        source = catalog["sources"][0]
        self.assertEqual("internal-workshop-assets", source["slug"])
        self.assertEqual("owner_manual_private_channel", source["access_flow"])
        self.assertIsNone(source["canonical_url"])
        self.assertEqual("owner-managed-private", source["immutable_ref"])
        self.assertEqual("2026-08-15", source["acknowledgement_terms_version"])
        self.assertEqual({"workshop-demo-001", "workshop-onepager-001"}, {asset["id"] for asset in source["public_safe_assets"]})
        metadata = (SUBMISSIONS / "internal-workshop-assets" / "metadata.json").read_text(encoding="utf-8").lower()
        self.assertNotIn("sharepoint.com", metadata)
        self.assertNotIn("tenant_id", metadata)

    def test_internal_access_flow_uses_raw_issue_handoff_and_deferred_metric_shape(self):
        page = (ROOT / "libraries.html").read_text(encoding="utf-8")
        for marker in (
            "access-ack-limited",
            "access-ack-least",
            "access-ack-terms",
            "access-ack-data",
            "access-ack-metrics",
            "aibast-internal-workshop-access:v1",
            "never post private links",
            "access-intended-use",
            "terms version 2026-08-15",
        ):
            self.assertIn(marker, page)
        self.assertIn("Pages cannot create access or call GraphQL", page)
        public_issue = page[page.index('const body = ['):page.index('window.open(issue.toString()', page.index('const body = ['))]
        self.assertIn("terms_version", public_issue)
        self.assertIn("optional_aggregate_metrics_consent", public_issue)
        self.assertIn("optional_follow_up_consent", public_issue)
        self.assertNotIn("accessJustification", public_issue)
        self.assertIn('href="LICENSE"', page)
        self.assertIn('href="SECURITY.md"', page)
        self.assertIn("raw, marker-first GitHub issue", page)
        self.assertNotIn('searchParams.set("template"', page)
        self.assertFalse((ROOT / ".github" / "ISSUE_TEMPLATE" / "internal-workshop-access.yml").exists())
        self.assertFalse((ROOT / ".github" / "workflows" / "internal-workshop-access.yml").exists())
        metrics = json.loads((ROOT / "state" / "internal_workshop_access_metrics.json").read_text(encoding="utf-8"))
        self.assertTrue(metrics["aggregate_only"])
        self.assertFalse(metrics["identity_fields_published"])
        self.assertNotIn("identity_fields_collected", metrics)
        self.assertEqual("deferred_no_active_collector", metrics["analytics_collection_status"])
        self.assertTrue(metrics["analytics_requires_explicit_opt_in"])
        self.assertEqual(5, metrics["minimum_public_cohort"])
        self.assertIn("asset", metrics["counts"])
        self.assertIn("impact_band", metrics["counts"])
        self.assertIn("suppressed", metrics)

    def test_forms_configuration_is_placeholder_only(self):
        config = json.loads((ROOT / "state" / "internal_workshop_access_config.example.json").read_text(encoding="utf-8"))
        self.assertFalse(config["forms_enabled"])
        self.assertIsNone(config["microsoft_forms_url"])
        self.assertIn("expected_audience_reach", config["required_fields"])
        self.assertEqual("2026-08-15", config["terms_version"])
        page = (ROOT / "libraries.html").read_text(encoding="utf-8")
        self.assertIn("configuredFormsUrl", page)
        self.assertIn("Request through Microsoft Forms", page)

    def test_giscus_curation_is_configured_without_page_tokens(self):
        config = json.loads((ROOT / "state" / "librarian_giscus_config.example.json").read_text(encoding="utf-8"))
        self.assertFalse(config["enabled"])
        self.assertIsNone(config["repo"])
        self.assertEqual("Ideas", config["source_category"])
        self.assertEqual("Announcements", config["item_category"])
        page = (ROOT / "libraries.html").read_text(encoding="utf-8")
        self.assertIn("giscus.app/client.js", page)
        self.assertIn("library-slug:item-slug", page)
        self.assertIn("curation signals only", page)
        self.assertIn('config.repo !== `${DISTRIBUTION_OWNER}/${DISTRIBUTION_REPO}`', page)
        self.assertNotIn('config.repo !== "microsoft/aibast-agents-library"', page)
        self.assertNotIn("accessToken", page)
        config_script = (ROOT / "assets" / "librarian-giscus-config.example.js").read_text(encoding="utf-8")
        self.assertIn("repo: null", config_script)
        self.assertIn("kody-w/aibast-agents-library", config_script)

    def test_discussion_urls_allow_the_controlled_staging_distribution(self):
        pipeline = load_module("librarian_pipeline", LIBRARIAN)
        original = pipeline.read_submission(SUBMISSIONS / "aibast-agents-library")
        metadata = dict(original.metadata)
        metadata["discussion_url"] = "https://github.com/kody-w/aibast-agents-library/discussions/42"
        staging = pipeline.SourceSubmission(original.directory, metadata, original.source)
        self.assertEqual([], pipeline.validate_submission(staging))
        metadata["discussion_url"] = "https://github.com/untrusted/aibast-agents-library/discussions/42"
        untrusted = pipeline.SourceSubmission(original.directory, metadata, original.source)
        errors = pipeline.validate_submission(untrusted)
        self.assertTrue(any("discussion_url" in error for error in errors), errors)

    def test_librarian_page_uses_generated_local_metadata_only(self):
        page = (ROOT / "libraries.html").read_text(encoding="utf-8")
        self.assertIn('localJson("state/libraries.json")', page)
        self.assertIn('localJson("state/libraries.metrics.json")', page)
        self.assertIn('localJson("state/libraries.snapshot.json")', page)
        self.assertIn('localJson("state/library_discussions.json")', page)
        self.assertIn("never fetches, imports, renders, or executes", page)
        self.assertNotIn("api.github.com", page)
        self.assertNotIn('fetch("http', page)
        self.assertIn("community_suggested", page)
        self.assertIn("quarantined", page)

    def test_librarian_cards_do_not_overflow_a_390px_chromium_viewport(self):
        page = (ROOT / "libraries.html").read_text(encoding="utf-8")
        self.assertIn(".card { min-width: 0;", page)
        self.assertIn(".meta { min-width: 0;", page)
        self.assertIn(".meta > div { min-width: 0; overflow-wrap: anywhere; word-break: break-word; }", page)

        playwright = ROOT / "browser-audit" / "node_modules" / "playwright"
        chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        if not shutil.which("node") or not playwright.exists() or not chrome.exists():
            self.skipTest("real Chromium/Playwright is unavailable")
        program = """
const http = require("http");
const fs = require("fs");
const path = require("path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE);
const root = path.resolve(process.env.REPO_ROOT);
const server = http.createServer((request, response) => {
  const pathname = decodeURIComponent(new URL(request.url, "http://localhost").pathname);
  const file = path.resolve(root, "." + pathname);
  if (file !== root && !file.startsWith(root + path.sep)) {
    response.writeHead(403).end();
    return;
  }
  fs.readFile(file, (error, payload) => {
    if (error) {
      response.writeHead(404).end();
      return;
    }
    response.writeHead(200).end(payload);
  });
});
(async () => {
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const port = server.address().port;
  let browser;
  try {
    browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_PATH });
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    await page.goto(`http://127.0.0.1:${port}/libraries.html`, { waitUntil: "networkidle" });
    await page.waitForFunction(() => document.querySelectorAll(".card").length >= 2);
    const metrics = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      maxCardWidth: Math.max(...[...document.querySelectorAll(".card")].map(card => card.getBoundingClientRect().width))
    }));
    process.stdout.write(JSON.stringify(metrics));
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => {
  console.error(error.stack || error);
  process.exit(1);
});
"""
        env = os.environ.copy()
        env.update(
            {
                "PLAYWRIGHT_MODULE": str(playwright),
                "CHROME_PATH": str(chrome),
                "REPO_ROOT": str(ROOT),
            }
        )
        result = subprocess.run(
            ["node", "-e", program],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        metrics = json.loads(result.stdout)
        self.assertLessEqual(metrics["scrollWidth"], metrics["innerWidth"] + 1)

    def test_contribution_form_supports_library_source(self):
        library = (ROOT / "library.html").read_text(encoding="utf-8")
        for field in (
            "contribution-type",
            "library-source-name",
            "library-source-url",
            "library-source-ref",
            "library-source-manifest",
            "library-source-type",
            "library-source-format",
            "library-source-owner",
            "library-source-license",
            "library-source-digest",
            "library-source-trust",
            "library-source-cadence",
            "library-source-tier",
            "library-source-useful",
        ):
            self.assertIn(field, library)
        self.assertIn("ci_or_trusted_backend_only", library)
        self.assertIn("browser_execution", library)
        self.assertIn('schema: "aibast-library-source/2.0"', library)
        self.assertIn('category", "ideas"', library)
        self.assertIn("library-slug:item-slug", library)

    def test_contribution_type_groups_are_siblings_and_toggle(self):
        library = (ROOT / "library.html").read_text(encoding="utf-8")
        parser = ContributionGroupParser()
        parser.feed(library)
        self.assertEqual("contribution-form", parser.parents["blog-contribution-fields"])
        self.assertEqual("contribution-form", parser.parents["library-source-fields"])
        self.assertIn("[hidden] { display: none !important; }", library)

        start = library.index("function setContributionType()")
        end = library.index("function renderContributionChecks", start)
        toggles = self.evaluate_javascript(
            library[start:end],
            """
globalThis.elements = {
  "contribution-type": { value: "blog_post" },
  "blog-contribution-fields": { hidden: false },
  "library-source-fields": { hidden: true },
  "contribution-title": { textContent: "" },
  "open-github-handoff": { textContent: "" }
};
globalThis.$ = (id) => globalThis.elements[id];
""",
            """
(() => {
  setContributionType();
  const blog = [elements["blog-contribution-fields"].hidden, elements["library-source-fields"].hidden];
  elements["contribution-type"].value = "library_source";
  setContributionType();
  const source = [elements["blog-contribution-fields"].hidden, elements["library-source-fields"].hidden];
  return { blog, source };
})()
""",
        )
        self.assertEqual({"blog": [False, True], "source": [True, False]}, toggles)

    def test_contribution_manifest_traversal_is_rejected_in_browser_validation(self):
        library = (ROOT / "library.html").read_text(encoding="utf-8")
        start = library.index("function contributionChecks(data)")
        end = library.index("function contributionSlug", start)
        results = self.evaluate_javascript(
            library[start:end],
            'globalThis.SECRET_PATTERN = /never-match/;',
            """
(() => {
  const ref = "a".repeat(40);
  const base = {
    type: "library_source",
    name: "Example library",
    owner: "Example owner",
    sourceType: "agent library",
    sourceFormat: "JSON catalog",
    canonicalUrl: `https://github.com/example/repo/tree/${ref}`,
    immutableRef: ref,
    sourceDigest: "b".repeat(64),
    license: "MIT",
    updateCadence: "monthly",
    trustTier: "reviewed",
    trustNotes: "A reviewed source with enough detail to explain its provenance and trust boundary.",
    whyUseful: "A useful source with enough detail to explain its reproducible operational value.",
    sourceNote: Array(81).fill("review").join(" "),
    tags: ["agents", "catalog"]
  };
  const cases = ["..", "../x", "a/../b", ".." + String.fromCharCode(92) + "x", "catalog.json"];
  return cases.map((manifestLocator) => {
    base.manifestLocator = manifestLocator;
    return [manifestLocator, contributionChecks(base)[2][1]];
  });
})()
""",
        )
        self.assertEqual(
            [["..", False], ["../x", False], ["a/../b", False], ["..\\x", False], ["catalog.json", True]],
            results,
        )

    def test_library_source_handoff_uses_ideas_and_defers_automation(self):
        library = (ROOT / "library.html").read_text(encoding="utf-8")
        self.assertIn('url.searchParams.set("category", "ideas")', library)
        self.assertIn("aibast-library-source-suggestion:v1", library)
        self.assertFalse((ROOT / ".github" / "workflows" / "blog-submission.yml").exists())

    def test_metric_discussion_url_is_distribution_validated_before_linking(self):
        page = (ROOT / "libraries.html").read_text(encoding="utf-8")
        start = page.index("function distributionDiscussionUrl(value)")
        end = page.index("function mountGiscus", start)
        results = self.evaluate_javascript(
            page[start:end],
            'globalThis.DISTRIBUTION_OWNER = "kody-w"; globalThis.DISTRIBUTION_REPO = "aibast-agents-library";',
            """
[
  distributionDiscussionUrl("https://github.com/kody-w/aibast-agents-library/discussions/42"),
  distributionDiscussionUrl("https://github.com/microsoft/aibast-agents-library/discussions/42"),
  distributionDiscussionUrl("https://evil.example/discussions/42"),
  distributionDiscussionUrl("javascript:alert(1)"),
  distributionDiscussionUrl("https://github.com/kody-w/aibast-agents-library/discussions/42?unsafe=1")
]
""",
        )
        self.assertEqual(
            [
                "https://github.com/kody-w/aibast-agents-library/discussions/42",
                "",
                "",
                "",
                "",
            ],
            results,
        )
        self.assertIn(
            "const metricDiscussion = metric && distributionDiscussionUrl(metric.discussion_url);",
            page,
        )
        self.assertIn("discussion.href = metricDiscussion;", page)
        self.assertNotIn("discussion.href = metric.discussion_url;", page)

    def test_handoffs_use_real_newlines_and_kody_w_distribution_owner(self):
        library = (ROOT / "library.html").read_text(encoding="utf-8")
        libraries = (ROOT / "libraries.html").read_text(encoding="utf-8")
        literal_backslash_join = re.compile(r"""\.join\(\s*["']\\\\n["']\s*\)""")
        self.assertIsNone(literal_backslash_join.search(library))
        self.assertIsNone(literal_backslash_join.search(libraries))
        self.assertIn("const DISTRIBUTION_OWNER = location.hostname.endsWith", library)
        self.assertIn("const DISTRIBUTION_OWNER = location.hostname.endsWith", libraries)
        self.assertNotIn("https://github.com/microsoft/aibast-agents-library/issues/new", libraries)
        self.assertNotIn('searchParams.set("template"', libraries)

        contribution_start = library.index("function openContributionGitHubHandoff()")
        contribution_end = library.index("function initContributionForm", contribution_start)
        contribution_url = self.execute_handoff(
            library[contribution_start:contribution_end],
            """
contributionArtifacts: {
  type: "blog_post",
  title: "Example contribution",
  slug: "example-contribution",
  primaryFilename: "example-contribution.submission.md"
},
DISTRIBUTION_OWNER: "kody-w",
REPO: "aibast-agents-library"
""",
            "openContributionGitHubHandoff",
        )
        contribution = urllib.parse.urlparse(contribution_url)
        self.assertEqual("/kody-w/aibast-agents-library/issues/new", contribution.path)
        contribution_body = urllib.parse.parse_qs(contribution.query)["body"][0]
        self.assertTrue(contribution_body.startswith("<!-- aibast-blog-submission:v1 -->\n"))
        self.assertIn("\n## Generated contribution handoff\n", contribution_body)
        self.assertNotIn("\\n## Generated contribution handoff", contribution_body)

        source_url = self.execute_handoff(
            library[contribution_start:contribution_end],
            """
contributionArtifacts: {
  type: "library_source",
  title: "Example source",
  slug: "example-source",
  primaryFilename: "example-source.submission.md"
},
DISTRIBUTION_OWNER: "kody-w",
REPO: "aibast-agents-library"
""",
            "openContributionGitHubHandoff",
        )
        source = urllib.parse.urlparse(source_url)
        self.assertEqual("/kody-w/aibast-agents-library/discussions/new", source.path)
        self.assertEqual(["ideas"], urllib.parse.parse_qs(source.query)["category"])
        source_body = urllib.parse.parse_qs(source.query)["body"][0]
        self.assertTrue(source_body.startswith("<!-- aibast-library-source-suggestion:v1 -->\n"))

        access_start = libraries.index("function openInternalAccessGitHubHandoff()")
        access_end = libraries.index("accessPrepare.addEventListener", access_start)
        access_url = self.execute_handoff(
            libraries[access_start:access_end],
            """
accessPrepare: { disabled: false },
accessSource: {},
selectedAssets: () => ["workshop-demo-001"],
accessIntendedUse: { value: "learning" },
accessImpact: { value: "demo" },
document: { getElementById: (id) => ({ checked: id === "access-ack-metrics" }) },
ACCESS_TERMS_VERSION: "2026-08-15",
DISTRIBUTION_OWNER: "kody-w",
DISTRIBUTION_REPO: "aibast-agents-library",
accessDialog: { close: () => {} }
""",
            "openInternalAccessGitHubHandoff",
        )
        access = urllib.parse.urlparse(access_url)
        self.assertEqual("/kody-w/aibast-agents-library/issues/new", access.path)
        access_body = urllib.parse.parse_qs(access.query)["body"][0]
        self.assertTrue(access_body.startswith("<!-- aibast-internal-workshop-access:v1 -->\n"))
        self.assertIn("\n## Requested asset IDs\n", access_body)
        self.assertNotIn("\\n## Requested asset IDs", access_body)

    def test_staging_workflows_are_explicitly_deferred(self):
        contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        self.assertFalse((ROOT / ".github" / "workflows" / "librarian-snapshot.yml").exists())
        self.assertIn("Deferred staging automation design", contributing)
        self.assertIn("There is intentionally no active", contributing)
        self.assertIn("loaded from the repository default branch", contributing)
        self.assertIn("optional_aggregate_metrics_consent: true", contributing)
        self.assertIn("false or missing from analytics", contributing)


if __name__ == "__main__":
    unittest.main()
