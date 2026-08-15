"""Contracts for the shared CAT-style download acknowledgement gate."""

from __future__ import annotations

import re
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import unittest
import urllib.parse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APPLIER = ROOT / "scripts" / "apply_download_trust_gate.py"
ANCHOR = re.compile(r"<a\b(?P<attrs>[^>]*)>", re.IGNORECASE | re.DOTALL)


def artifact(attrs: str) -> bool:
    href = re.search(r"""href\s*=\s*["']([^"']+)["']""", attrs, re.IGNORECASE | re.DOTALL)
    download = re.search(r"""download\s*=\s*["']([^"']+)["']""", attrs, re.IGNORECASE | re.DOTALL)
    href_value = (href.group(1) if href else "").lower()
    download_value = (download.group(1) if download else "").lower()
    has_download = bool(re.search(r"\bdownload(?:\s*=|\s|$)", attrs, re.IGNORECASE))
    if "/blob/" in href_value:
        return False
    value = " ".join([href_value, download_value])
    acquired = has_download or "raw.githubusercontent.com" in href_value or "/releases/download/" in href_value
    return "skill.md" in value or (acquired and re.search(r"(?:^|[/?._-])[^/\s]*\.py(?:$|[?#\s])", value) is not None) or (
        acquired and ".zip" in value and any(token in value for token in ("copilot", "solution", "powerplatform", "msft", "agent"))
    )


def source_bundle_target(page: Path, attrs: str) -> Path | None:
    href = re.search(r"""href\s*=\s*["']([^"']+)["']""", attrs, re.IGNORECASE | re.DOTALL)
    if not href:
        return None
    parsed = urllib.parse.urlsplit(href.group(1))
    if parsed.scheme or parsed.netloc:
        return None
    target = (page.parent / urllib.parse.unquote(parsed.path)).resolve()
    try:
        relative = target.relative_to(ROOT)
    except ValueError:
        return None
    if (
        len(relative.parts) == 4
        and relative.parts[0] == "solutions"
        and relative.parts[2] == "exports"
        and relative.name.endswith("-source.zip")
    ):
        return target
    return None


def load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class DownloadTrustGateTests(unittest.TestCase):
    def test_applier_is_idempotent_and_current(self):
        result = subprocess.run(
            [sys.executable, str(APPLIER), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_every_static_code_bearing_anchor_is_gated(self):
        found = 0
        for page in ROOT.rglob("*.html"):
            if ".git" in page.parts or "tools" in page.parts or "assets" in page.parts:
                continue
            text = page.read_text(encoding="utf-8")
            for match in ANCHOR.finditer(text):
                attrs = match.group("attrs")
                if not artifact(attrs):
                    continue
                found += 1
                self.assertIn("data-download-gated", attrs, page)
                self.assertIn('aria-disabled="true"', attrs, page)
                for class_name in ("pointer-events-none", "opacity-50", "cursor-not-allowed"):
                    self.assertIn(class_name, attrs, page)
            if "data-download-gated" in text:
                self.assertIn("data-aibast-trust-assets", text, page)
                self.assertIn("assets/trust-gate.js", text, page)
        self.assertGreater(found, 100)

    def test_every_solution_source_bundle_anchor_is_gated(self):
        source_bundles = []
        for page in ROOT.rglob("*.html"):
            if any(part in {".git", "tools", "assets"} for part in page.parts):
                continue
            for match in ANCHOR.finditer(page.read_text(encoding="utf-8")):
                attrs = match.group("attrs")
                target = source_bundle_target(page, attrs)
                if target is None:
                    continue
                source_bundles.append((page, target, attrs))
                self.assertIn("data-download-gated", attrs, page)
                self.assertIn('data-download-kind="solution"', attrs, page)
                self.assertIn('aria-disabled="true"', attrs, page)
        self.assertEqual(204, len(source_bundles))

    def test_shared_gate_uses_reference_sync_behavior(self):
        script = (ROOT / "assets" / "trust-gate.js").read_text(encoding="utf-8")
        for token in (
            "data-download-gated",
            "aria-disabled",
            "pointer-events-none",
            "opacity-50",
            "cursor-not-allowed",
            "ack.focus()",
            "data-download-kind",
            "aibast-download-ack:v1",
            "ensureGate",
        ):
            self.assertIn(token, script)
        brainstem = (ROOT / "rapp_brainstem" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="trust-ack"', brainstem)
        library = (ROOT / "library.html").read_text(encoding="utf-8")
        self.assertIn('data-download-kind="agent"', library)
        self.assertIn('data-download-kind="solution"', library)
        self.assertIn("assets/trust-gate.js", library)

    def test_global_interception_covers_a_gated_link_outside_an_optional_container(self):
        script = (ROOT / "assets" / "trust-gate.js").read_text(encoding="utf-8")
        fixture = (ROOT / "tests" / "fixtures" / "trust-gate-global-delegation.html").read_text(encoding="utf-8")
        self.assertNotIn("trust-download-actions", script)
        self.assertIn('document.addEventListener("click"', script)
        self.assertIn('document.addEventListener("keydown"', script)
        self.assertIn('event.target.closest("[data-download-gated]")', script)
        self.assertIn('id="trust-download-actions"', fixture)
        self.assertIn('id="outside-gated-download"', fixture)
        self.assertGreater(
            fixture.index('id="outside-gated-download"'),
            fixture.index("</div>"),
        )
        self.assertIn("data-download-gated", fixture)

    def test_solution_generator_emits_the_shared_gate(self):
        generator = (ROOT / "tools" / "scaffold_solution_journey.py").read_text(encoding="utf-8")
        self.assertIn("def apply_trust_gate", generator)
        self.assertIn("data-download-gated", generator)
        self.assertIn("trust-gate.css", generator)
        self.assertIn("-source\\.zip", generator)

    def test_source_bundle_classification_does_not_depend_on_slug_keywords(self):
        attrs = ' href="exports/neutral-source.zip"'
        applier = load_script("download_gate_applier", APPLIER)
        generator = load_script("solution_scaffold", ROOT / "tools" / "scaffold_solution_journey.py")
        self.assertEqual("solution", applier.artifact_kind(attrs))
        self.assertEqual("solution", generator.trust_download_kind(attrs))

    def test_quest_troubleshooting_tables_stay_inside_narrow_cards(self):
        table_rule = (
            ".troubleshooting-table { width: 100%; max-width: 100%; "
            "box-sizing: border-box; table-layout: fixed; border-collapse: collapse; }"
        )
        cell_rule = (
            ".troubleshooting-table th, .troubleshooting-table td { padding: 12px; "
            "border: 1px solid var(--cp-border); text-align: left; vertical-align: top; "
            "overflow-wrap: anywhere; word-break: break-word; }"
        )
        quests = sorted(ROOT.glob("solutions/*/quest.html"))
        self.assertEqual(51, len(quests))
        for quest in quests:
            page = quest.read_text(encoding="utf-8")
            self.assertIn(table_rule, page, quest)
            self.assertIn(cell_rule, page, quest)
        generator = (ROOT / "tools" / "scaffold_solution_journey.py").read_text(encoding="utf-8")
        self.assertIn(table_rule.replace("{", "{{").replace("}", "}}"), generator)
        self.assertIn(cell_rule.replace("{", "{{").replace("}", "}}"), generator)

    def test_quest_pages_do_not_overflow_a_390px_chromium_viewport(self):
        playwright = ROOT / "browser-audit" / "node_modules" / "playwright"
        chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        if not shutil.which("node") or not playwright.exists() or not chrome.exists():
            self.skipTest("real Chromium/Playwright is unavailable")
        quests = sorted(path.relative_to(ROOT).as_posix() for path in ROOT.glob("solutions/*/quest.html"))
        program = """
const { chromium } = require(process.env.PLAYWRIGHT_MODULE);
const { pathToFileURL } = require("url");
const path = require("path");
(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.CHROME_PATH
  });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const results = [];
  for (const relative of JSON.parse(process.env.QUEST_FILES)) {
    await page.goto(pathToFileURL(path.join(process.env.REPO_ROOT, relative)).href, {
      waitUntil: "domcontentloaded"
    });
    results.push(await page.evaluate(() => ({
      path: location.pathname,
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth
    })));
  }
  await browser.close();
  process.stdout.write(JSON.stringify(results));
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
                "QUEST_FILES": json.dumps(quests),
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
        overflow = [
            metrics
            for metrics in json.loads(result.stdout)
            if metrics["scrollWidth"] > metrics["innerWidth"] + 1
        ]
        self.assertEqual([], overflow)

    def test_focused_gate_applier_never_mutates_source_archives(self):
        archives = sorted(ROOT.glob("solutions/*/exports/*-source.zip"))
        self.assertGreater(len(archives), 10)
        before = {
            archive: hashlib.sha256(archive.read_bytes()).hexdigest()
            for archive in archives
        }
        result = subprocess.run(
            [sys.executable, str(APPLIER)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        after = {
            archive: hashlib.sha256(archive.read_bytes()).hexdigest()
            for archive in archives
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
