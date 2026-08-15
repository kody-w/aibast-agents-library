#!/usr/bin/env python3
"""Apply or verify focused static safeguards without rebuilding source archives."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_MARKER = "data-aibast-trust-assets"
GATE_MARKER = "<!-- aibast-trust-gate -->"
LOCKED = "pointer-events-none opacity-50 cursor-not-allowed"
ANCHOR = re.compile(r"<a\b(?P<attrs>[^>]*)>", re.IGNORECASE | re.DOTALL)
ATTRIBUTE = re.compile(r"""(?P<name>[\w:-]+)\s*=\s*(?P<quote>["'])(?P<value>.*?)\2""", re.DOTALL)
QUEST_TABLE_RULE = re.compile(
    r"(?m)^([ \t]*)\.troubleshooting-table\s*\{\s*"
    r"width:\s*100%;\s*"
    r"(?:max-width:\s*100%;\s*)?"
    r"(?:box-sizing:\s*border-box;\s*)?"
    r"(?:table-layout:\s*fixed;\s*)?"
    r"border-collapse:\s*collapse;\s*\}"
)
QUEST_TABLE_REPLACEMENT = (
    r"\1.troubleshooting-table { width: 100%; max-width: 100%; "
    r"box-sizing: border-box; table-layout: fixed; border-collapse: collapse; }"
)
QUEST_TABLE_CELLS_RULE = re.compile(
    r"(?m)^([ \t]*)\.troubleshooting-table th, \.troubleshooting-table td\s*\{\s*"
    r"padding:\s*12px;\s*border:\s*1px solid var\(--cp-border\);\s*"
    r"text-align:\s*left;\s*vertical-align:\s*top;\s*"
    r"(?:overflow-wrap:\s*anywhere;\s*)?"
    r"(?:word-break:\s*break-word;\s*)?\}"
)
QUEST_TABLE_CELLS_REPLACEMENT = (
    r"\1.troubleshooting-table th, .troubleshooting-table td { padding: 12px; "
    r"border: 1px solid var(--cp-border); text-align: left; vertical-align: top; "
    r"overflow-wrap: anywhere; word-break: break-word; }"
)


def artifact_kind(attrs: str) -> str | None:
    values = {match.group("name").lower(): match.group("value") for match in ATTRIBUTE.finditer(attrs)}
    href = values.get("href", "").lower()
    download = values.get("download", "").lower()
    has_download = bool(re.search(r"\bdownload(?:\s*=|\s|$)", attrs, re.IGNORECASE))
    if "/blob/" in href:
        return None
    candidate = " ".join([href, download]).lower().strip()
    export_zip = re.search(r"(?:^|/)exports/[^/?#]+\.zip(?:[?#]|$)", href)
    source_zip = re.search(r"(?:^|[/?._-])[^/?#]*-source\.zip(?:[?#]|$)", candidate)
    if export_zip or source_zip:
        return "solution"
    if "skill.md" in candidate or values.get("download", "").lower().endswith("skill.md"):
        return "skill"
    if (has_download or "raw.githubusercontent.com" in href or "/releases/download/" in href) and re.search(r"(?:^|[/?._-])[^/\s]*\.py(?:$|[?#\s])", candidate):
        return "agent"
    if (has_download or "raw.githubusercontent.com" in href or "/releases/download/" in href) and ".zip" in candidate and re.search(r"(copilot|solution|powerplatform|msft|agent)", candidate):
        return "solution"
    return None


def add_gate_attributes(match: re.Match[str]) -> str:
    attrs = match.group("attrs")
    if "data-download-gated" in attrs:
        return match.group(0)
    kind = artifact_kind(attrs)
    if not kind:
        return match.group(0)
    class_match = re.search(r"""class\s*=\s*(["'])(.*?)\1""", attrs, re.DOTALL)
    if class_match:
        classes = class_match.group(2).split()
        for name in LOCKED.split():
            if name not in classes:
                classes.append(name)
        attrs = attrs[:class_match.start(2)] + " ".join(classes) + attrs[class_match.end(2):]
    else:
        attrs += f' class="{LOCKED}"'
    attrs = re.sub(r"""\saria-disabled\s*=\s*(["']).*?\1""", "", attrs, flags=re.DOTALL)
    attrs += f' data-download-gated data-download-kind="{kind}" aria-disabled="true"'
    return f"<a{attrs}>"


def gate_markup() -> str:
    return f"""
{GATE_MARKER}
<section id="trust-gate" aria-labelledby="trust-gate-title">
  <h2 id="trust-gate-title">Add only what you trust</h2>
  <p id="trust-artifact" role="status" aria-live="polite">Choose a gated download to see its artifact-specific trust boundary.</p>
  <label for="trust-ack">
    <input type="checkbox" id="trust-ack">
    <span><strong>Review required.</strong> I understand that a gated artifact may be community-provided and code-bearing, can run with my permissions or affect my environment, and should be downloaded only from a trusted source.</span>
  </label>
</section>
"""


def asset_markup(page: Path) -> str:
    relative = Path("assets").relative_to("assets") if page.parent == ROOT else Path(
        __import__("os").path.relpath(ROOT / "assets", page.parent)
    )
    base = relative.as_posix()
    if base == ".":
        base = "assets"
    return (
        f'\n<link rel="stylesheet" href="{base}/trust-gate.css" {ASSET_MARKER}>\n'
        f'<script defer src="{base}/trust-gate.js" {ASSET_MARKER}></script>\n'
    )


def transform(page: Path, content: str) -> str:
    updated = re.sub(
        re.escape(GATE_MARKER) + r"\s*<section id=\"trust-gate\".*?</section>\s*",
        "",
        content,
        flags=re.DOTALL,
    )
    updated = ANCHOR.sub(add_gate_attributes, updated)
    if page.name == "quest.html" and page.parent.parent.name == "solutions":
        updated = QUEST_TABLE_RULE.sub(QUEST_TABLE_REPLACEMENT, updated)
        updated = QUEST_TABLE_CELLS_RULE.sub(QUEST_TABLE_CELLS_REPLACEMENT, updated)
    if "data-download-gated" not in updated:
        return updated
    if ASSET_MARKER not in updated:
        updated = updated.replace("</head>", asset_markup(page) + "</head>", 1)
    return updated


def pages() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*.html")
        if ".git" not in path.parts and "tools" not in path.parts and "assets" not in path.parts
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if a page needs trust-gate changes.")
    args = parser.parse_args()
    changed: list[Path] = []
    for page in pages():
        original = page.read_text(encoding="utf-8")
        updated = transform(page, original)
        if updated != original:
            changed.append(page)
            if not args.check:
                page.write_text(updated, encoding="utf-8")
    if args.check and changed:
        for page in changed:
            print(f"{page.relative_to(ROOT)}: trust gate is missing or stale", file=sys.stderr)
        return 1
    print(f"PASS: central trust gate covers {len([p for p in pages() if 'data-download-gated' in p.read_text(encoding='utf-8')])} static pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
