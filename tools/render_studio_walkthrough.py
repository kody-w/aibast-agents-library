#!/usr/bin/env python3
"""Render studio editions from each solution's studio/walkthrough.json.

    python3 tools/render_studio_walkthrough.py [slug ...]
    python3 tools/render_studio_walkthrough.py --check

Paths are package-relative except the locked tests/demo_cases/<slug>.json.
Data CSVs sit beside their schema and are named <list-id>.csv. Step ids run
<mode>-01, <mode>-02, ... in each lane. Only reviewed captures may be displayed;
pending capture paths do not have to exist. No live service is consulted.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import struct
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote, unquote


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.design_tokens import render_tokens, stamp  # noqa: E402
from tools.scaffold_solution_journey import (  # noqa: E402
    COMMON_CSS,
    THEME_PREFERENCE_SCRIPT,
    WORKSHOP_STORAGE_SCRIPT,
    clarity_head_tag,
)


SCHEMA = "aibast-studio-walkthrough/1.0"
MODES = ("easy", "manual")
AGENT_NAME_MAX = 30  # the Build page name field has maxlength="30"
SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
GUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(
    r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@(?:[a-z0-9-]+\.)+[a-z]{2,}",
    re.IGNORECASE,
)
TENANT_HOST_RE = re.compile(
    r"(?<![\w.-])(?P<prefix>(?:<[^<>\s.]+>|[a-z0-9_-]+)"
    r"(?:\.(?:<[^<>\s.]+>|[a-z0-9_-]+))*)"
    r"\.(?P<service>sharepoint|dynamics|powerapps)\.com\b",
    re.IGNORECASE,
)


class WalkthroughError(ValueError):
    """A source contract is unsafe, incomplete, or inconsistent."""


@dataclass(frozen=True)
class Walkthrough:
    slug: str
    package: Path
    document: dict[str, Any]
    lists: list[dict[str, Any]]
    skills: list[tuple[str, str]]
    tools: dict[str, str]
    app: dict[str, Any]


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WalkthroughError(f"{label} must be an object")
    return value


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WalkthroughError(f"{label} must be a non-empty string")
    return value


def require_list(value: Any, label: str, *, nonempty: bool = True) -> list:
    if not isinstance(value, list) or (nonempty and not value):
        raise WalkthroughError(f"{label} must be {'a non-empty' if nonempty else 'an'} array")
    return value


def check_privacy(value: Any, label: str = "walkthrough") -> None:
    """Check unknown metadata too, and decode HTML/URL escapes before scanning."""
    if isinstance(value, dict):
        for key, child in value.items():
            check_privacy(key, f"{label} key")
            check_privacy(child, f"{label}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            check_privacy(child, f"{label}[{index}]")
    elif isinstance(value, str):
        text = unquote(html.unescape(value))
        for pattern, kind in ((EMAIL_RE, "email address"), (GUID_RE, "GUID-shaped id")):
            if pattern.search(text):
                raise WalkthroughError(f"Privacy check failed in {label}: {kind}")
        for match in TENANT_HOST_RE.finditer(text):
            prefix = match["prefix"]
            allowed = r"(?:contoso|<[^<>\s.]+>)"
            if match["service"].lower() == "dynamics":
                allowed += r"(?:\.crm[0-9]*)?"
            if not re.fullmatch(allowed, prefix, re.IGNORECASE):
                raise WalkthroughError(
                    f"Privacy check failed in {label}: tenant host; "
                    "use contoso or an <...> placeholder"
                )


def referenced_path(
    base: Path, value: Any, label: str, *, directory: bool = False, pending: bool = False
) -> Path:
    text = require_text(value, label)
    relative = PurePosixPath(text)
    if (
        relative.is_absolute()
        or not relative.parts
        or ".." in relative.parts
        or re.search(r"[\x00-\x20\\:?#<>]", text)
        or relative.as_posix() != text
    ):
        raise WalkthroughError(f"{label} must be a safe relative repository path")
    path = base / relative
    if not path.resolve().is_relative_to(base.resolve()):
        raise WalkthroughError(f"{label} escapes its source directory")
    cursor = base
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise WalkthroughError(f"{label} must not reference a symlink")
    if not pending and not (path.is_dir() if directory else path.is_file()):
        kind = "directory" if directory else "file"
        raise WalkthroughError(f"{label}: missing {kind} {text}")
    return path


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WalkthroughError(f"Could not read {label}: {exc}") from exc
    return require_object(document, label)


def load_lists(root: Path, package: Path, source: Path, slug: str) -> list[dict[str, Any]]:
    schema = read_json(source, "data schema")
    if schema.get("schema") != "aibast-studio-data/1.0" or schema.get("solution") != slug:
        raise WalkthroughError("data schema must be aibast-studio-data/1.0 for this solution")
    for field in ("source", "records_markdown"):
        if field in schema:
            referenced_path(root, schema[field], f"data.{field}")
    result = []
    seen = set()
    for index, value in enumerate(require_list(schema.get("lists"), "data.lists")):
        label = f"data.lists[{index}]"
        item = require_object(value, label)
        list_id = require_text(item.get("id"), f"{label}.id")
        if not SLUG_RE.fullmatch(list_id) or list_id in seen:
            raise WalkthroughError(f"{label}.id must be a unique kebab-case id")
        seen.add(list_id)
        title = require_text(item.get("title"), f"{label}.title")
        columns = require_list(item.get("columns"), f"{label}.columns")
        names = [
            require_text(require_object(column, label).get("name"), f"{label}.column.name")
            for column in columns
        ]
        relative = (source.parent / f"{list_id}.csv").relative_to(package).as_posix()
        csv_path = referenced_path(package, relative, f"{label}.csv")
        try:
            with csv_path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.reader(stream, strict=True))
        except (OSError, UnicodeError, csv.Error) as exc:
            raise WalkthroughError(f"Could not read {label}.csv: {exc}") from exc
        if not rows or rows[0] != names or any(len(row) != len(names) for row in rows[1:]):
            raise WalkthroughError(f"{label}.csv must match the schema columns")
        result.append({"id": list_id, "title": title, "csv": relative, "count": len(rows) - 1})
    return result


def load_skills(package: Path, source: Path) -> list[tuple[str, str]]:
    files = sorted(source.rglob("SKILL.md"))
    if not files:
        raise WalkthroughError("agent.skills must contain at least one SKILL.md")
    skills = []
    seen = set()
    for path in files:
        relative = path.relative_to(package).as_posix()
        referenced_path(package, relative, "agent.skills file")
        text = path.read_text(encoding="utf-8")
        frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.DOTALL)
        name = re.search(r"^name:\s*([^\r\n]+)", frontmatter[1], re.MULTILINE) if frontmatter else None
        skill_name = name[1].strip().strip("\"'") if name else ""
        if not SLUG_RE.fullmatch(skill_name) or skill_name in seen:
            raise WalkthroughError(f"agent.skills {relative} needs a unique frontmatter name")
        seen.add(skill_name)
        skills.append((skill_name, relative))
    return skills


def image_size(path: Path) -> tuple[int, int]:
    """Pixel size from a PNG, WebP or JPEG header (stdlib only)."""
    data = path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        chunk = data[12:16]
        if chunk == b"VP8X":
            return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
        if chunk == b"VP8L" and data[20] == 0x2F:
            bits = int.from_bytes(data[21:25], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        if chunk == b"VP8 " and data[23:26] == b"\x9d\x01\x2a":
            return (int.from_bytes(data[26:28], "little") & 0x3FFF,
                    int.from_bytes(data[28:30], "little") & 0x3FFF)
    if data[:2] == b"\xff\xd8":
        at = 2
        while at + 9 < len(data) and data[at] == 0xFF:
            marker, length = data[at + 1], struct.unpack(">H", data[at + 2:at + 4])[0]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                height, width = struct.unpack(">HH", data[at + 5:at + 9])
                return width, height
            at += 2 + length
    raise WalkthroughError(f"{path.name} is not a readable PNG, WebP or JPEG image")


def screenshot_list(screenshot: Any) -> list[Any]:
    return screenshot if isinstance(screenshot, list) else [screenshot]


def validate_screenshot(package: Path, screenshot: Any, label: str, mode: str) -> None:
    shots = screenshot_list(screenshot)
    if not shots:
        raise WalkthroughError(f"{label} must list at least one capture")
    for index, shot in enumerate(shots):
        validate_one_screenshot(package, shot, f"{label}[{index}]" if isinstance(screenshot, list) else label, mode)


def validate_one_screenshot(package: Path, screenshot: Any, label: str, mode: str) -> None:
    shot = require_object(screenshot, label)
    status = shot.get("status")
    if status not in ("pending", "reviewed"):
        raise WalkthroughError(f"{label}.status must be pending or reviewed")
    source = referenced_path(package, shot.get("file"), f"{label}.file", pending=status == "pending")
    relative = source.relative_to(package)
    if (
        relative.parts[:2] != ("screenshots", f"studio-{mode}")
        or source.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}
    ):
        raise WalkthroughError(f"{label}.file must be an image under screenshots/studio-{mode}/")
    if status == "reviewed":
        require_text(shot.get("alt"), f"{label}.alt")
        for anchor in require_list(shot.get("anchors"), f"{label}.anchors"):
            require_text(anchor, f"{label}.anchors entry")
        captured_at = require_text(shot.get("captured_at"), f"{label}.captured_at")
        try:
            datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise WalkthroughError(f"{label}.captured_at must be an ISO timestamp") from exc
        density = shot.get("density")
        if density not in (1, 2):
            raise WalkthroughError(f"{label}.density must be 1 or 2 device pixels per CSS pixel")
        declared = (shot.get("width"), shot.get("height"))
        if not all(isinstance(v, int) and v > 0 and v % density == 0 for v in declared):
            raise WalkthroughError(f"{label}.width and .height must be device pixels divisible by density")
        if image_size(source) != declared:
            raise WalkthroughError(f"{label} declares {declared[0]}x{declared[1]} but the image is "
                                   f"{image_size(source)[0]}x{image_size(source)[1]}")


def load_walkthrough(slug: str, *, root: Path = ROOT) -> Walkthrough:
    if not SLUG_RE.fullmatch(slug):
        raise WalkthroughError("solution slug must be kebab-case")
    package = referenced_path(root, f"solutions/{slug}", "solution package", directory=True)
    source = referenced_path(package, "studio/walkthrough.json", "walkthrough")
    document = read_json(source, "walkthrough")
    check_privacy(document)
    if document.get("schema") != SCHEMA:
        raise WalkthroughError(f"walkthrough.schema must be {SCHEMA}")
    if document.get("solution") != slug:
        raise WalkthroughError("walkthrough.solution must match its package slug")
    for field in ("title", "summary"):
        require_text(document.get(field), f"walkthrough.{field}")
    data_path = referenced_path(package, document.get("data"), "walkthrough.data")
    lists = load_lists(root, package, data_path, slug)
    agent = require_object(document.get("agent"), "agent")
    instructions = referenced_path(package, agent.get("instructions"), "agent.instructions")
    skills_path = referenced_path(package, agent.get("skills"), "agent.skills", directory=True)
    skills = load_skills(package, skills_path)
    for item in require_list(agent.get("knowledge"), "agent.knowledge", nonempty=False):
        referenced_path(package, item, "agent.knowledge file")
    require_text(agent.get("model"), "agent.model")
    app_config = require_object(document.get("app"), "app")
    for label, config in (("agent", agent), ("app", app_config)):
        names = require_object(config.get("names"), f"{label}.names")
        for mode in MODES:
            require_text(names.get(mode), f"{label}.names.{mode}")
        if label == "agent":
            for mode in MODES:
                if len(names[mode]) > AGENT_NAME_MAX:
                    raise WalkthroughError(f"agent.names.{mode} is {len(names[mode])} characters; Copilot Studio "
                                           f"accepts at most {AGENT_NAME_MAX} in an agent name")
            if names["easy"] == names["manual"]:
                raise WalkthroughError("agent.names must differ so a Manual build never repairs the Easy agent")
    app_path = referenced_path(package, app_config.get("spec"), "app.spec")
    app = read_json(app_path, "app spec")
    require_text(app.get("name"), "app spec.name")
    table_ids = set()
    for value in require_list(app.get("tables"), "app spec.tables"):
        table = require_object(value, "app table")
        for field in ("id", "title", "list"):
            require_text(table.get(field), f"app table.{field}")
        if table["id"] in table_ids:
            raise WalkthroughError("app table ids must be unique")
        table_ids.add(table["id"])
        if table["list"] not in {item["title"] for item in lists}:
            raise WalkthroughError("app table.list must reference a data schema list")

    case_path = f"tests/demo_cases/{slug}.json"
    if document.get("cases") != case_path:
        raise WalkthroughError(f"walkthrough.cases must reference the locked {case_path}")
    cases_source = referenced_path(root, document["cases"], "walkthrough.cases")
    cases = {}
    for item in require_list(read_json(cases_source, "locked cases").get("cases"), "locked cases"):
        case = require_object(item, "locked case")
        case_id = require_text(case.get("id"), "locked case.id")
        if case_id in cases:
            raise WalkthroughError("locked case ids must be unique")
        cases[case_id] = require_text(case.get("prompt"), "locked case.prompt")

    modes = require_object(document.get("modes"), "modes")
    if set(modes) != set(MODES):
        raise WalkthroughError("modes must contain exactly easy and manual")
    seen_steps = set()
    for mode in MODES:
        lane = require_object(modes[mode], f"modes.{mode}")
        require_text(lane.get("title"), f"modes.{mode}.title")
        for index, value in enumerate(require_list(lane.get("steps"), f"modes.{mode}.steps"), 1):
            label = f"modes.{mode}.steps[{index}]"
            step = require_object(value, label)
            for field in ("id", "title", "action", "expected"):
                require_text(step.get(field), f"{label}.{field}")
            if step["id"] in seen_steps:
                raise WalkthroughError(f"{label}.id must be unique")
            seen_steps.add(step["id"])
            if step["id"] != f"{mode}-{index:02d}":
                raise WalkthroughError(f"{label}.id must be ordered; expected {mode}-{index:02d}")
            if step.get("screenshot") is None:
                raise WalkthroughError(f"{label}.screenshot is required: every step shows a capture")
            validate_screenshot(package, step["screenshot"], f"{label}.screenshot", mode)
            for command in require_list(step.get("commands", []), f"{label}.commands", nonempty=False):
                require_text(command, f"{label}.commands entry")
            for download in require_list(step.get("downloads", []), f"{label}.downloads", nonempty=False):
                referenced_path(package, download, f"{label}.downloads entry")
            if "prompt" in step:
                require_text(step["prompt"], f"{label}.prompt")
            if "case" in step:
                case_id = require_text(step["case"], f"{label}.case")
                if case_id not in cases:
                    raise WalkthroughError(f"{label}.case does not exist in locked cases")
                if step.get("prompt") != cases[case_id]:
                    raise WalkthroughError(f"{label}.prompt must match locked case {case_id} exactly")

    # Tool aliases live in the instructions; the list inventory is schema-owned.
    tools = {
        match[2]: match[1]
        for match in re.finditer(
            r"\*\*([^*\r\n]+)\*\*\s*(?:tool\s*)?\((?:list\s*)?\*([^*\r\n]+)\*\)",
            instructions.read_text(encoding="utf-8"),
        )
    }
    return Walkthrough(slug, package, document, lists, skills, tools, app)


def escape(value: str) -> str:
    return html.escape(value, quote=True).replace("\r", "&#13;")


def download_link(path: str, label: str) -> str:
    return (
        f'<a class="button" href="{escape(quote(path, safe="/-._~"))}" '
        f'download="{escape(PurePosixPath(path).name)}">{escape(label)}</a>'
    )


def copy_block(value: str, target: str, label: str) -> str:
    return (
        '<div class="copy-block">'
        f'<div class="instruction-heading"><strong>{escape(label)}</strong>'
        f'<button class="button copy-button" type="button" data-copy-target="{target}" '
        f'aria-label="Copy {escape(label.lower())}">Copy</button></div>'
        f'<pre><code id="{target}">{escape(value)}</code></pre></div>'
    )


def render_inventory(walkthrough: Walkthrough) -> str:
    document = walkthrough.document
    agent = document["agent"]
    app = document["app"]
    lists = "\n".join(
        f'<li><strong>{escape(item["title"])}</strong> — '
        f'{item["count"]} synthetic records '
        f'{download_link(item["csv"], "Download " + PurePosixPath(item["csv"]).name)}</li>'
        for item in walkthrough.lists
    )
    skills = "\n".join(
        f"<li>{download_link(path, name)}</li>" for name, path in walkthrough.skills
    )
    knowledge = "\n".join(
        f"<li>{download_link(path, PurePosixPath(path).name)}</li>" for path in agent["knowledge"]
    ) or "<li>No knowledge files configured.</li>"
    tools = "\n".join(
        f'<li>{escape(walkthrough.tools[item["title"]])} — '
        f'SharePoint Get items: {escape(item["title"])}</li>'
        if item["title"] in walkthrough.tools
        else f'<li>SharePoint Get items: {escape(item["title"])}</li>'
        for item in walkthrough.lists
    )
    tables = "\n".join(
        f'<li><strong>{escape(table["title"])}</strong> — {escape(table["list"])}</li>'
        for table in walkthrough.app["tables"]
    )
    return f"""<section class="card inventory" id="what-youll-build" aria-labelledby="inventory-title">
        <h2 id="inventory-title">What you'll build</h2>
        <h3>SharePoint lists</h3>
        <ul class="inventory-list">{lists}</ul>
        <p>{download_link(document["data"], "Download data schema")}</p>
        <h3>Copilot Studio agent</h3>
        <p><strong>Easy:</strong> {escape(agent["names"]["easy"])}<br>
        <strong>Manual:</strong> {escape(agent["names"]["manual"])}<br>
        <strong>Model:</strong> {escape(agent["model"])}</p>
        <p>{download_link(agent["instructions"], "Download agent instructions")}</p>
        <details><summary>Skills ({len(walkthrough.skills)})</summary><ul>{skills}</ul></details>
        <details><summary>Knowledge ({len(agent["knowledge"])})</summary><ul>{knowledge}</ul></details>
        <details open><summary>Tools ({len(walkthrough.lists)})</summary><ul>{tools}</ul></details>
        <h3>Managed app: {escape(walkthrough.app["name"])}</h3>
        <p><strong>Easy:</strong> {escape(app["names"]["easy"])}<br>
        <strong>Manual:</strong> {escape(app["names"]["manual"])}</p>
        <ul>{tables}</ul>
        <p>{download_link(app["spec"], "Download managed app spec")}</p>
      </section>"""


def render_step(walkthrough: Walkthrough, mode: str, step: dict[str, Any], number: int, total: int) -> str:
    step_id = step["id"]
    location = f"Studio edition — {mode.title()} mode — step {number}: {step['title']}"
    screenshot = step["screenshot"]
    evidence = f"solutions/{walkthrough.slug}/studio/walkthrough.json"
    figures = []
    for shot in screenshot_list(screenshot):
        if shot["status"] == "pending":
            figures.append(
                '<div class="missing verification-checkpoint" data-evidence-status="pending">'
                "<strong>Screenshot pending</strong><p>A real capture will be added after "
                "this step is run live and reviewed. No screenshot is shown; this is not "
                "evidence that the step has passed.</p></div>"
            )
            continue
        if evidence.endswith("walkthrough.json"):
            evidence = f"solutions/{walkthrough.slug}/{shot['file']}"
        href = escape(quote(shot["file"], safe="/-._~"))
        anchors = "; ".join(shot["anchors"])
        density = shot["density"]
        figures.append(
            '<figure class="reference-shot-wrap">'
            f'<a class="shot-link" href="{href}" download="{escape(PurePosixPath(shot["file"]).name)}">'
            f'<img class="shot" data-evidence-status="reviewed" src="{href}" srcset="{href} {density}x" '
            f'width="{shot["width"] // density}" height="{shot["height"] // density}" '
            f'alt="{escape(shot["alt"])}" loading="lazy"></a>'
            f'<figcaption class="capture-meta">Reviewed visual checkpoint: {escape(anchors)}. '
            f'Captured <time datetime="{escape(shot["captured_at"])}">'
            f'{escape(shot["captured_at"])}</time>. '
            f'<a href="{href}" download>Download original</a> ({shot["width"]}×{shot["height"]}). '
            "This image does not certify other steps.</figcaption></figure>"
        )
    screenshot_html = "\n".join(figures)
    commands = "\n".join(
        copy_block(command, f"{step_id}-command-{index}", f"Command {index}")
        for index, command in enumerate(step.get("commands", []), 1)
    )
    prompt = copy_block(step["prompt"], f"{step_id}-prompt", "Preview prompt") if "prompt" in step else ""
    case = (
        f'<p class="case-label">Locked case: <code>{escape(step["case"])}</code>. '
        "Use a fresh Preview conversation.</p>" if "case" in step else ""
    )
    downloads = "\n".join(
        download_link(path, f"Download source: {PurePosixPath(path).name}")
        for path in step.get("downloads", [])
    )
    progress_key = f"aibast:{walkthrough.slug}:studio:{mode}:{step_id}"
    return f"""<article class="step" id="{step_id}" aria-labelledby="{step_id}-title">
        <header><span aria-hidden="true">{number}</span><div><h3 id="{step_id}-title">{escape(step["title"])}</h3>
          <p>Step {number} of {total}</p></div>
          <button class="button report-button" type="button"
            data-report-location="{escape(location)}"
            data-report-expected="{escape(step["expected"])}"
            data-report-evidence="{escape(evidence)}">Report an issue</button></header>
        <div class="step-body">
          <div class="instruction-grid">
            <div class="instruction"><strong>Action</strong><p>{escape(step["action"])}</p></div>
            <div class="instruction expected"><strong>Expected result</strong><p>{escape(step["expected"])}</p></div>
          </div>
          {commands}
          {case}
          {prompt}
          {screenshot_html}
          <footer><div class="downloads">{downloads}</div>
            <label for="{step_id}-complete"><input class="complete" type="checkbox"
              id="{step_id}-complete" data-step="{step_id}" data-mode="{mode}"
              data-progress-key="{progress_key}"> Mark complete</label></footer>
        </div>
      </article>"""


STUDIO_CSS = """
    [hidden] { display: none !important; }
    .layout { display: grid; grid-template-columns: 270px minmax(0, 840px); gap: 32px; max-width: 1180px; margin: 0 auto; padding: 32px 24px 80px; }
    .layout > *, .step, .step-body, .instruction-grid > * { min-width: 0; }
    .sidebar { position: sticky; top: 82px; align-self: start; max-height: calc(100vh - 104px); overflow: auto; }
    .toc { display: grid; gap: 4px; margin-top: 14px; }
    .toc a { padding: 7px 9px; border-left: 3px solid var(--cp-border); color: var(--cp-text-muted); text-decoration: none; font-size: 13px; }
    .toc a:hover { border-left-color: var(--cp-accent); color: var(--cp-text); }
    .mode-switch { display: flex; gap: 6px; margin: 18px 0; padding: 5px; border: 1px solid var(--cp-border); border-radius: var(--cp-radius-pill); background: var(--cp-surface-soft); }
    .mode { flex: 1; padding: 9px 14px; border-radius: var(--cp-radius-pill); color: var(--cp-text); text-align: center; text-decoration: none; font-weight: 750; }
    .mode[aria-current="location"] { background: var(--cp-accent); color: var(--cp-accent-fg); }
    .inventory { margin-top: 24px; }
    .inventory h2 { margin-top: 0; }
    .inventory li { margin: 10px 0; }
    .inventory-list .button { margin: 6px 0; }
    details { padding: 10px 0; }
    summary { cursor: pointer; font-weight: 700; }
    .step { scroll-margin-top: 90px; margin: 0 0 28px; overflow: hidden; border: 1px solid var(--cp-border); border-radius: 16px; background: var(--cp-surface); }
    .step header { display: grid; grid-template-columns: 36px minmax(0, 1fr) auto; gap: 14px; align-items: center; padding: 20px 22px; border-bottom: 1px solid var(--cp-border); }
    .step header > span { display: grid; width: 36px; height: 36px; place-items: center; border-radius: 10px; background: var(--cp-accent-soft); color: var(--cp-accent); font-weight: 800; }
    .step h3, .step header p { margin: 0; }
    .step header p, .capture-meta, .case-label { color: var(--cp-text-muted); font-size: 13px; }
    .step-body { padding: 22px; }
    .instruction-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-bottom: 18px; }
    .instruction { padding: 14px; border-radius: 10px; background: var(--cp-surface-soft); }
    .instruction strong { display: block; margin-bottom: 6px; }
    .instruction p { margin: 0; }
    .instruction.expected { border-left: 4px solid var(--cp-success); }
    .instruction-heading { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
    .copy-block { margin: 16px 0; }
    .copy-button { min-height: 34px; padding: 6px 10px; font-size: 13px; }
    pre { max-width: 100%; overflow-x: auto; white-space: pre-wrap; padding: 16px; border: 1px solid var(--cp-border); border-radius: 10px; background: var(--cp-surface-soft); }
    pre code { font-family: var(--cp-font-mono); font-size: 13px; }
    .shot-link { display: block; text-align: center; }
    .shot { display: block; max-width: 100%; height: auto; margin: 0 auto; border: 1px solid var(--cp-border); border-radius: 10px; }
    .reference-shot-wrap { margin: 16px 0; }
    .capture-meta { margin-top: 8px; text-align: center; }
    .missing { padding: 24px; border: 2px dashed var(--cp-warning); border-radius: 10px; color: var(--cp-text-muted); }
    .missing strong { color: var(--cp-text); }
    .report-button { border-color: var(--cp-accent); color: var(--cp-accent); }
    .feedback-notice { margin-top: 14px; padding: 14px; border-left: 4px solid var(--cp-accent); background: var(--cp-surface-soft); }
    .step footer, .downloads { display: flex; align-items: start; flex-wrap: wrap; gap: 12px; }
    .step footer { justify-content: space-between; margin-top: 16px; }
    .complete { width: 18px; height: 18px; accent-color: var(--cp-accent); vertical-align: middle; }
    .mode-progress { margin: 14px 0 24px; }
    .mode-progress p { margin-bottom: 8px; }
    @media (max-width: 900px) { .layout { grid-template-columns: 1fr; } .sidebar { position: static; max-height: none; } }
    @media (max-width: 620px) {
      .layout { padding: 24px 12px 60px; }
      .instruction-grid { grid-template-columns: 1fr; }
      .step header { grid-template-columns: 36px minmax(0, 1fr); padding: 16px; }
      .step header .report-button { grid-column: 1 / -1; }
      .step-body { padding: 16px; }
    }
"""


STUDIO_SCRIPT = r"""
    (() => {
      const storage = globalThis.aibastWorkshopStorage;
      const panels = Array.from(document.querySelectorAll("[data-mode-panel]"));
      const links = Array.from(document.querySelectorAll("[data-mode-link]"));
      storage.onUnavailable(() => {
        document.querySelector("[data-storage-notice]").hidden = false;
      });
      function activateMode(mode) {
        panels.forEach((panel) => { panel.hidden = panel.dataset.modePanel !== mode; });
        document.querySelectorAll("[data-mode-toc]").forEach((toc) => {
          toc.hidden = toc.dataset.modeToc !== mode;
        });
        links.forEach((link) => {
          if (link.dataset.modeLink === mode) link.setAttribute("aria-current", "location");
          else link.removeAttribute("aria-current");
        });
      }
      function followAnchor() {
        let id = "";
        try { id = decodeURIComponent(window.location.hash.slice(1)); } catch (_error) {}
        const target = document.getElementById(id);
        const panel = target?.closest("[data-mode-panel]");
        if (panel) {
          activateMode(panel.dataset.modePanel);
          target.scrollIntoView({ block: "start" });
        }
      }
      activateMode("easy");
      followAnchor();
      window.addEventListener("hashchange", followAnchor);
      links.forEach((link) => {
        link.addEventListener("click", () => activateMode(link.dataset.modeLink));
      });
      panels.forEach((panel) => {
        const mode = panel.dataset.modePanel;
        const boxes = Array.from(panel.querySelectorAll(".complete"));
        function update() {
          const count = boxes.filter((box) => box.checked).length;
          document.getElementById(`${mode}-progress-label`).textContent =
            `${count} of ${boxes.length} complete`;
          const bar = document.getElementById(`${mode}-progress-bar`);
          bar.setAttribute("aria-valuenow", String(count));
          bar.firstElementChild.style.width = `${count / boxes.length * 100}%`;
        }
        boxes.forEach((box) => {
          box.checked = storage.getItem(box.dataset.progressKey) === "true";
          box.addEventListener("change", () => {
            storage.setItem(box.dataset.progressKey, String(box.checked));
            update();
          });
        });
        update();
      });
      const copyStatus = document.getElementById("copy-status");
      document.querySelectorAll("[data-copy-target]").forEach((button) => {
        button.addEventListener("click", async () => {
          const target = document.getElementById(button.dataset.copyTarget);
          try {
            await navigator.clipboard.writeText(target.textContent);
            button.textContent = "Copied";
            copyStatus.textContent = "Copied to clipboard.";
            window.setTimeout(() => { button.textContent = "Copy"; }, 1400);
          } catch (_error) {
            button.textContent = "Select and copy";
            copyStatus.textContent = "Clipboard unavailable. Select and copy the visible code.";
            const range = document.createRange();
            range.selectNodeContents(target);
            const selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(range);
          }
        });
      });
      document.querySelectorAll("[data-report-location]").forEach((button) => {
        button.addEventListener("click", () => {
          const slug = document.body.dataset.studioSlug;
          const mode = button.closest("[data-mode-panel]").dataset.modePanel;
          const locationLabel = button.dataset.reportLocation;
          const owner = window.location.hostname.match(/^([a-z0-9-]+)\.github\.io$/i)?.[1] || "microsoft";
          const url = new URL(`https://github.com/${owner}/aibast-agents-library/issues/new`);
          url.searchParams.set("title", `[Workshop feedback] ${document.getElementById("course-title").textContent}: ${locationLabel}`);
          url.searchParams.set("body", `<!-- aibast-workshop-feedback:v1 -->
## Workshop signal

- Schema: \`aibast-workshop-feedback/1.0\`
- Solution: \`@aibast-agents-library/${slug}\`
- Page: solutions/${slug}/studio-tutorial.html
- Mode: \`${mode}\` (studio edition)
- Location: ${locationLabel}
- Evidence: \`${button.dataset.reportEvidence}\`

## Expected

${button.dataset.reportExpected}

## What happened instead

Describe what was inaccurate or missing.

## Reproduction

1. Open the studio edition tutorial.
2. Follow the step shown above.
3. Record the visible state, not an assumed result.

> Do not include credentials, tokens, email addresses, tenant identifiers, customer data, or other sensitive information.`);
          window.open(url.toString(), "_blank", "noopener");
        });
      });
    })();
"""


def render_walkthrough(slug: str, *, root: Path = ROOT) -> str:
    walkthrough = load_walkthrough(slug, root=root)
    document = walkthrough.document
    toc = []
    sections = []
    for mode in MODES:
        lane = document["modes"][mode]
        steps = lane["steps"]
        toc_links = "\n".join(
            f'<a href="#{step["id"]}">{index}. {escape(step["title"])}</a>'
            for index, step in enumerate(steps, 1)
        )
        toc.append(
            f'<nav class="toc" data-mode-toc="{mode}" aria-label="{mode.title()} tutorial actions">'
            f'<strong>{mode.title()} mode</strong>{toc_links}</nav>'
        )
        cards = "\n".join(
            render_step(walkthrough, mode, step, index, len(steps))
            for index, step in enumerate(steps, 1)
        )
        sections.append(f"""<section id="{mode}" data-mode-panel="{mode}" aria-labelledby="{mode}-title" tabindex="-1">
        <h2 id="{mode}-title">{escape(lane["title"])}</h2>
        <div class="mode-progress">
          <p id="{mode}-progress-label" role="status" aria-live="polite" aria-atomic="true">0 of {len(steps)} complete</p>
          <div class="progress" id="{mode}-progress-bar" role="progressbar"
            aria-labelledby="{mode}-progress-label" aria-valuemin="0" aria-valuemax="{len(steps)}" aria-valuenow="0"><span></span></div>
        </div>
        {cards}
      </section>""")
    page = f"""<!doctype html>
<!-- Generated by tools/render_studio_walkthrough.py from solutions/{slug}/studio/walkthrough.json.
     Do not edit this page; update the source and regenerate. -->
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{escape(document["summary"])}">
  <title>{escape(document["title"])} — studio edition</title>
  <script>
    {THEME_PREFERENCE_SCRIPT}
    {WORKSHOP_STORAGE_SCRIPT}
  </script>
  <style>
{COMMON_CSS}
{STUDIO_CSS}
  </style>
{clarity_head_tag()}
</head>
<body data-studio-slug="{slug}">
  <a class="skip-link" href="#course-content">Skip to course content</a>
  <header class="topbar">
    <div class="topbar-identity">
      <div class="brand"><span class="brand-mark" aria-hidden="true">A</span><span>AIBAST studio workshop</span></div>
      <a class="academy-breadcrumb" href="../../academy.html">Academy / Studio edition</a>
    </div>
    <div class="topbar-actions"><button class="button" type="button" data-theme-toggle aria-pressed="false">Use dark mode</button>
      <a class="button" href="quest.html">Back to workshop</a>
      {download_link("studio/walkthrough.json", "Download walkthrough source")}</div>
  </header>
  <div class="layout">
    <aside class="sidebar" aria-label="Studio tutorial navigation">
      <nav class="mode-switch" aria-label="Tutorial mode">
        <a class="mode" href="#easy" data-mode-link="easy">Easy</a>
        <a class="mode" href="#manual" data-mode-link="manual">Manual</a>
      </nav>
      <p class="muted">Progress is saved on this device, separately for each mode. It is self-reported, not live validation.</p>
      <a href="#what-youll-build">What you'll build</a>
      {"".join(toc)}
    </aside>
    <main id="course-content" tabindex="-1">
      <section class="hero" aria-labelledby="course-title">
        <p class="eyebrow">Studio edition · Easy and Manual</p>
        <h1 id="course-title">{escape(document["title"])}</h1>
        <p class="lede">{escape(document["summary"])}</p>
        <div class="notice"><strong>Synthetic data only:</strong> every record and figure is fictional workshop data, not customer results, verified emissions evidence, a compliance determination, or a credit purchase.</div>
        <p>Use the same lists, agent and managed app in either mode. Keep the agent in Draft.
        Expected results below are checks to run, not claims that a live run has passed.</p>
        <div class="notice" data-storage-notice role="status" aria-live="polite" aria-atomic="true" hidden>Progress remains available on this page but will not persist after you leave.</div>
        <div class="feedback-notice"><strong>Found something inaccurate?</strong> Use <em>Report an issue</em> on that step. It opens a prefilled GitHub issue for your review and never submits automatically.</div>
        <p id="copy-status" role="status" aria-live="polite" aria-atomic="true"></p>
      </section>
      {render_inventory(walkthrough)}
      {"".join(sections)}
    </main>
  </div>
  <script>{STUDIO_SCRIPT}
  </script>
</body>
</html>
"""
    page = stamp(page, render_tokens())
    check_privacy(page, "rendered page")
    return page


def discover_slugs(root: Path = ROOT) -> list[str]:
    return sorted(path.parent.parent.name for path in (root / "solutions").glob("*/studio/walkthrough.json"))


def main(argv: list[str] | None = None, *, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slugs", nargs="*", help="Solution slugs; defaults to every studio package")
    parser.add_argument("--check", action="store_true", help="Fail if a generated page is missing or differs")
    args = parser.parse_args(argv)
    slugs = list(dict.fromkeys(args.slugs)) if args.slugs else discover_slugs(root)
    try:
        # Validate every selected package before writing any output.
        pages = {
            root / "solutions" / slug / "studio-tutorial.html": render_walkthrough(slug, root=root).encode("utf-8")
            for slug in slugs
        }
        stale = []
        for path, content in pages.items():
            if path.is_symlink():
                raise WalkthroughError(f"Refusing symlink output: {path}")
            if not path.is_file() or path.read_bytes() != content:
                if args.check:
                    stale.append(path.relative_to(root).as_posix())
                else:
                    path.write_bytes(content)
        if stale:
            print("Stale studio tutorial(s); run tools/render_studio_walkthrough.py:\n" + "\n".join(stale), file=sys.stderr)
            return 1
    except (WalkthroughError, OSError, UnicodeError) as exc:
        print(f"Studio walkthrough error: {exc}", file=sys.stderr)
        return 2
    print(f"{'Checked' if args.check else 'Rendered'} {len(pages)} studio tutorial(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
