#!/usr/bin/env python3
"""Microsoft Clarity tag: the one rendering shared by the stamper and the scaffold.

The Clarity project ID lives in one place, ``clarity.json`` at the repository
root. ``render_tag`` turns it into the block every published page carries;
``scripts/apply_clarity_tag.py`` stamps or checks that block on the committed
pages and ``tools/scaffold_solution_journey.py`` emits it in fresh workshop
pages, so both paths produce byte-identical heads.

The rendered tag is the standard Clarity loader with two guards added:

* it only loads on ``*.github.io`` hosts, so local previews and file:// opens
  never report sessions;
* it stays silent when the browser sends Global Privacy Control or Do Not Track.

While ``project_id`` is empty the tag is still stamped (so every page carries
the same block) but the loader returns before contacting Clarity.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "clarity.json"

START_MARK = "<!-- clarity:start -->"
END_MARK = "<!-- clarity:end -->"
BLOCK_RE = re.compile(
    re.escape(START_MARK) + r".*?" + re.escape(END_MARK) + r"\n?", re.DOTALL
)
HEAD_CLOSE_RE = re.compile(r"</head>", re.IGNORECASE)
PROJECT_ID_RE = re.compile(r"^[a-z0-9]{6,20}$")

# Published site pages: root HTML plus these directories (see
# scripts/build_pages_site.py for what GitHub Pages actually serves).
PUBLIC_DIRECTORIES = ("docs", "reports", "solutions")
# Never tagged: the Brainstem UI that installs on users' machines, the
# Hippocampus docs bundled with the Azure function, local-first tools, and the
# beta Electron renderer.
EXCLUDED_PREFIXES = ("rapp_brainstem/", "rapp_ai/", "tools/", "beta/", "node_modules/")

TAG_TEMPLATE = """{start}
<script data-clarity-project="{project_id}">
(function (c, l, a, r, i, t, y) {{
  if (!i || !/\\.github\\.io$/i.test(l.location.hostname)) return;
  var n = c.navigator || {{}};
  if (n.globalPrivacyControl || n.doNotTrack === "1" || c.doNotTrack === "1") return;
  c[a] = c[a] || function () {{ (c[a].q = c[a].q || []).push(arguments); }};
  t = l.createElement(r); t.async = 1; t.src = "https://www.clarity.ms/tag/" + i;
  y = l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(t, y);
}})(window, document, "clarity", "script", "{project_id}");
</script>
{end}
"""


def load_config(path: Path = CONFIG_PATH) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    project_id = data.get("project_id", "")
    if not isinstance(project_id, str):
        raise ValueError("clarity.json project_id must be a string")
    if project_id and not PROJECT_ID_RE.match(project_id):
        raise ValueError(
            f"clarity.json project_id {project_id!r} is not a Clarity project ID"
        )
    return data


def render_tag(project_id: str) -> str:
    return TAG_TEMPLATE.format(start=START_MARK, end=END_MARK, project_id=project_id)


def is_public_page(relative: str) -> bool:
    if not relative.endswith(".html"):
        return False
    if relative.startswith(EXCLUDED_PREFIXES):
        return False
    if "/" not in relative:
        return True
    return relative.split("/", 1)[0] in PUBLIC_DIRECTORIES


def public_pages(root: Path = ROOT) -> list[Path]:
    pages = []
    for path in root.rglob("*.html"):
        relative = path.relative_to(root).as_posix()
        if "/node_modules/" in f"/{relative}" or relative.startswith(".git/"):
            continue
        if is_public_page(relative):
            pages.append(path)
    return sorted(pages)


def stamp(html: str, tag: str) -> str:
    """Return ``html`` carrying exactly one copy of ``tag`` before ``</head>``."""
    stripped = BLOCK_RE.sub("", html)
    match = HEAD_CLOSE_RE.search(stripped)
    if match is None:
        raise ValueError("page has no </head>")
    before = stripped[: match.start()]
    if before and not before.endswith("\n"):
        before += "\n"
    return before + tag + stripped[match.start() :]


def current_tag(root: Path = ROOT) -> str:
    """The tag every published page must carry right now (from clarity.json)."""
    return render_tag(load_config(root / "clarity.json")["project_id"])
