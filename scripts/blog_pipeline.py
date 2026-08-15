#!/usr/bin/env python3
"""Validate canonical blog submissions and render the generated blog region.

The public page is generated only from submissions/blog/<slug>/metadata.json and
post.md. Issue intake uses the same validator before a maintainer manually
reviews a staging-only submission.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUBMISSIONS = ROOT / "submissions" / "blog"
DEFAULT_OUTPUT = ROOT / "blog.html"
BEGIN = "<!-- blog-posts:begin -->"
END = "<!-- blog-posts:end -->"
SCHEMA = "aibast-blog/1.0"
REQUIRED_SECTIONS = {
    "Concrete problem",
    "Technical approach",
    "Reproduce",
    "Evidence",
    "Limitations",
    "Action",
}
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
TAG = re.compile(r"^[a-z0-9][a-z0-9-]{1,31}$")
SECRET = re.compile(
    r"\b(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,})\b",
    re.IGNORECASE,
)
MAX_ATTACHMENT_BYTES = 1_000_000
AUTHOR_PLACEHOLDERS = frozenset(
    {
        "aibast",
        "aibast engineering",
        "anonymous",
        "n/a",
        "rapp",
        "rapp team",
        "team",
        "unknown",
    }
)
AUTHOR_HANDLE = re.compile(r"^.+\s+\(@[A-Za-z0-9-]{1,39}\)$")
LEGACY_HTML_SLUGS = frozenset(
    {
        "device-code-login-race",
        "local-agent-boundaries",
        "version-file-release-signal",
    }
)
MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


@dataclass(frozen=True)
class Submission:
    directory: Path
    metadata: dict[str, Any]
    post: str

    @property
    def slug(self) -> str:
        return str(self.metadata.get("slug", ""))


def https_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urllib.parse.urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def scalar(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def read_submission(directory: Path) -> Submission:
    metadata_path = directory / "metadata.json"
    post_path = directory / "post.md"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    post = post_path.read_text(encoding="utf-8")
    if not isinstance(metadata, dict):
        raise ValueError("metadata.json must contain a JSON object")
    return Submission(directory, metadata, post)


def section_names(post: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in re.finditer(r"^##\s+(.+?)\s*$", post, flags=re.MULTILINE)
    }


def validate_submission(submission: Submission) -> list[str]:
    metadata = submission.metadata
    errors: list[str] = []
    prefix = submission.directory.as_posix()

    def require_text(key: str, minimum: int = 1) -> None:
        if len(scalar(metadata.get(key))) < minimum:
            errors.append(f"{prefix}: metadata.{key} must contain at least {minimum} characters")

    if metadata.get("schema") != SCHEMA:
        errors.append(f"{prefix}: metadata.schema must equal {SCHEMA}")
    if metadata.get("contribution_type") != "blog_post":
        errors.append(f"{prefix}: metadata.contribution_type must be blog_post")
    if not SLUG.fullmatch(submission.slug):
        errors.append(f"{prefix}: metadata.slug must be lowercase kebab-case")
    elif submission.directory.name != submission.slug:
        errors.append(f"{prefix}: directory name must match metadata.slug")
    require_text("title", 8)
    require_text("author", 3)
    require_text("summary", 30)
    require_text("audience", 12)
    require_text("prerequisites", 15)
    require_text("applicability", 20)
    require_text("support_boundary", 20)
    require_text("limitations", 30)
    if metadata.get("status") not in {"published", "staging"}:
        errors.append(f"{prefix}: metadata.status must be published or staging")
    if metadata.get("publication") != "generated-from-canonical-submission":
        errors.append(f"{prefix}: metadata.publication must declare generated output")

    try:
        published = date.fromisoformat(scalar(metadata.get("date")))
        if published > date.today():
            errors.append(f"{prefix}: metadata.date must not be in the future")
    except ValueError:
        errors.append(f"{prefix}: metadata.date must be ISO-8601 YYYY-MM-DD")
    author = scalar(metadata.get("author"))
    author_name = re.sub(r"\s+\(@[A-Za-z0-9-]{1,39}\)$", "", author).strip().casefold()
    if author_name in AUTHOR_PLACEHOLDERS:
        errors.append(f"{prefix}: metadata.author must identify a named individual, not a team or anonymous placeholder")
    elif not AUTHOR_HANDLE.fullmatch(author):
        errors.append(f"{prefix}: metadata.author must use a named individual plus GitHub handle, for example Name (@handle)")

    tags = metadata.get("tags")
    if (
        not isinstance(tags, list)
        or len(tags) < 2
        or any(not isinstance(tag, str) or not TAG.fullmatch(tag) for tag in tags)
    ):
        errors.append(f"{prefix}: metadata.tags must contain two lowercase kebab-case tags")

    for key in ("evidence", "links"):
        records = metadata.get(key)
        if not isinstance(records, list) or not records:
            errors.append(f"{prefix}: metadata.{key} must be a non-empty list")
            continue
        for index, record in enumerate(records, start=1):
            if not isinstance(record, dict) or not scalar(record.get("label")) or not https_url(record.get("url")):
                errors.append(f"{prefix}: metadata.{key}[{index}] requires label and HTTPS url")

    word_count = len(re.findall(r"\S+", submission.post))
    if word_count < 250:
        errors.append(f"{prefix}: post.md must contain at least 250 words (found {word_count})")
    legacy_html = metadata.get("legacy_html") is True
    if legacy_html:
        if metadata.get("status") != "published":
            errors.append(f"{prefix}: legacy_html is allowed only for published history")
        if submission.slug not in LEGACY_HTML_SLUGS:
            errors.append(f"{prefix}: legacy_html is restricted to migrated historical submissions")
        if re.search(r"<(?:script|iframe)\b|on\w+\s*=", submission.post, flags=re.IGNORECASE):
            errors.append(f"{prefix}: legacy_html must not contain active content")
    else:
        missing = REQUIRED_SECTIONS - section_names(submission.post)
        if missing:
            errors.append(f"{prefix}: post.md is missing sections: {', '.join(sorted(missing))}")
    if SECRET.search(submission.post) or SECRET.search(json.dumps(metadata)):
        errors.append(f"{prefix}: submission appears to contain a credential")
    if not legacy_html and re.search(r"^#\s+", submission.post, flags=re.MULTILINE):
        errors.append(f"{prefix}: post.md must not include H1; metadata.title is the canonical page title")
    action_match = re.search(r"^##\s+Action\s*$\s*(.*?)(?=^##\s+|\Z)", submission.post, flags=re.MULTILINE | re.DOTALL)
    if action_match and not action_match.group(1).strip():
        errors.append(f"{prefix}: Action section must not be empty")
    return errors


def load_submissions(root: Path) -> list[Submission]:
    if not root.exists():
        return []
    submissions: list[Submission] = []
    for directory in sorted(path for path in root.iterdir() if path.is_dir() and not path.name.startswith(".")):
        submissions.append(read_submission(directory))
    return submissions


def inline_markdown(value: str) -> str:
    output: list[str] = []
    cursor = 0
    for match in MARKDOWN_LINK.finditer(value):
        output.append(html.escape(value[cursor:match.start()], quote=False))
        label = html.escape(match.group(1), quote=False)
        url = match.group(2)
        if not https_url(url):
            output.append(f"{label} ({html.escape(url, quote=False)})")
        else:
            output.append(f'<a href="{html.escape(url, quote=True)}">{label}</a>')
        cursor = match.end()
    output.append(html.escape(value[cursor:], quote=False))
    return "".join(output)


def render_markdown(post: str) -> str:
    lines = post.strip().splitlines()
    output: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.startswith("# "):
            # The page already renders the canonical metadata title.
            index += 1
            continue
        if line.startswith("```"):
            language = line[3:].strip()
            index += 1
            code: list[str] = []
            while index < len(lines) and not lines[index].startswith("```"):
                code.append(lines[index])
                index += 1
            index += 1
            class_name = f' class="language-{html.escape(language, quote=True)}"' if language else ""
            output.append(f"<pre><code{class_name}>{html.escape(chr(10).join(code))}</code></pre>")
            continue
        heading = re.match(r"^(#{2,3})\s+(.+?)\s*$", line)
        if heading:
            level = len(heading.group(1))
            name = heading.group(2).strip()
            if level == 2 and name == "Action":
                index += 1
                while index < len(lines) and not lines[index].strip():
                    index += 1
                action_lines: list[str] = []
                while (
                    index < len(lines)
                    and lines[index].strip()
                    and not re.match(r"^#{2,3}\s+", lines[index])
                ):
                    action_lines.append(lines[index].strip())
                    index += 1
                output.append(
                    '<p class="post-action"><strong>Try this:</strong> '
                    f"{inline_markdown(' '.join(action_lines))}</p>"
                )
                continue
            tag = "h3" if level == 2 else "h4"
            output.append(f"<{tag}>{inline_markdown(name)}</{tag}>")
            index += 1
            continue
        if line.startswith("- "):
            items: list[str] = []
            while index < len(lines) and lines[index].startswith("- "):
                items.append(f"<li>{inline_markdown(lines[index][2:].strip())}</li>")
                index += 1
            output.append("<ul>" + "".join(items) + "</ul>")
            continue
        paragraph: list[str] = []
        while (
            index < len(lines)
            and lines[index].strip()
            and not re.match(r"^#{2,3}\s+", lines[index])
            and not lines[index].startswith("```")
            and not lines[index].startswith("- ")
        ):
            paragraph.append(lines[index].strip())
            index += 1
        output.append(f"<p>{inline_markdown(' '.join(paragraph))}</p>")
    return "\n".join(output)


def link_list(records: list[dict[str, Any]]) -> str:
    items = [
        f'<li><a href="{html.escape(record["url"], quote=True)}">{html.escape(record["label"])}</a></li>'
        for record in records
    ]
    return "<ul>" + "".join(items) + "</ul>"


def render_submission(submission: Submission) -> str:
    metadata = submission.metadata
    tags = "".join(f'<span class="tag">{html.escape(tag)}</span>' for tag in metadata["tags"])
    status_note = (
        f'<p class="post-status"><strong>Status note:</strong> {inline_markdown(metadata["status_note"])}</p>'
        if scalar(metadata.get("status_note"))
        else ""
    )
    rendered_body = (
        submission.post.strip()
        if metadata.get("legacy_html") and submission.slug in LEGACY_HTML_SLUGS
        else render_markdown(submission.post)
    )
    return f"""  <article class="post" id="{html.escape(submission.slug, quote=True)}">
    <div class="post-header">
      <h2>{html.escape(metadata["title"])}</h2>
      <div class="post-meta">
        <time datetime="{html.escape(metadata["date"], quote=True)}">{html.escape(metadata["date"])}</time>
        <span>By {html.escape(metadata["author"])}</span>
        {tags}
        <a href="#{html.escape(submission.slug, quote=True)}" aria-label="Permalink to {html.escape(metadata["title"], quote=True)}">Permalink</a>
      </div>
    </div>
    <div class="post-body">
      <p>{inline_markdown(metadata["summary"])}</p>
      <section class="post-rubric" aria-label="Article context and evidence">
        <div><strong>Audience</strong><p>{inline_markdown(metadata["audience"])}</p></div>
        <div><strong>Prerequisites</strong><p>{inline_markdown(metadata["prerequisites"])}</p></div>
        <div><strong>Evidence</strong>{link_list(metadata["evidence"])}</div>
        <div><strong>Limitations</strong><p>{inline_markdown(metadata["limitations"])}</p></div>
        <div><strong>Applicability</strong><p>{inline_markdown(metadata["applicability"])}</p></div>
        <div><strong>Support boundary</strong><p>{inline_markdown(metadata["support_boundary"])}</p></div>
      </section>
{status_note}
{rendered_body}
      <section class="post-links" aria-label="Current links">
        <h3>Current links</h3>
        {link_list(metadata["links"])}
      </section>
    </div>
  </article>"""


def render_region(submissions: list[Submission]) -> str:
    ordered = sorted(submissions, key=lambda submission: submission.metadata["date"], reverse=True)
    posts = "\n\n".join(render_submission(submission) for submission in ordered)
    return f"{BEGIN}\n  <!-- Generated by scripts/blog_pipeline.py; do not hand-edit. -->\n{posts}\n{END}"


def replace_region(page: str, region: str) -> str:
    start = page.find(BEGIN)
    end = page.find(END)
    if start < 0 or end < 0 or end < start:
        raise ValueError(f"{DEFAULT_OUTPUT}: generated blog markers are missing")
    end += len(END)
    return page[:start] + region + page[end:]


def validate_all(root: Path) -> tuple[list[Submission], list[str]]:
    submissions = load_submissions(root)
    errors: list[str] = []
    slugs: set[str] = set()
    for submission in submissions:
        errors.extend(validate_submission(submission))
        if submission.slug in slugs:
            errors.append(f"{submission.directory}: duplicate slug {submission.slug}")
        slugs.add(submission.slug)
    if not submissions:
        errors.append(f"{root}: no blog submissions found")
    return submissions, errors


def render(root: Path, output: Path, check: bool) -> int:
    submissions, errors = validate_all(root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    expected = replace_region(output.read_text(encoding="utf-8"), render_region(submissions))
    actual = output.read_text(encoding="utf-8")
    if check:
        if actual != expected:
            print(f"{output}: generated blog output has drifted; run scripts/blog_pipeline.py render", file=sys.stderr)
            return 1
        print(f"PASS: {output} matches {len(submissions)} canonical blog submissions.")
        return 0
    if actual != expected:
        output.write_text(expected, encoding="utf-8")
        print(f"Wrote generated blog region for {len(submissions)} submissions.")
    else:
        print(f"No blog changes; {output} is current.")
    return 0


def import_submission(metadata_path: Path, post_path: Path, root: Path) -> int:
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be a JSON object")
        slug = scalar(metadata.get("slug"))
        directory = root / slug
        candidate = Submission(directory, metadata, post_path.read_text(encoding="utf-8"))
        errors = validate_submission(candidate)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Import failed: {error}", file=sys.stderr)
        return 1
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    if directory.exists():
        print(f"Import failed: {directory} already exists", file=sys.stderr)
        return 1
    directory.mkdir(parents=True)
    (directory / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    (directory / "post.md").write_text(candidate.post.rstrip() + "\n", encoding="utf-8")
    print(f"Imported canonical submission {slug}.")
    return 0


def download_issue_attachments(issue_body: Path, output: Path) -> int:
    """Download only named GitHub user-attachment artifacts after approval.

    Issue text is untrusted: URLs are parsed, host/path constrained, filenames
    are never used as local paths, and bytes are bounded before validation.
    """

    text = issue_body.read_text(encoding="utf-8")
    links = re.findall(r"\[([^\]]+)\]\((https://github\.com/user-attachments/files/[^)\s]+)\)", text)
    metadata_links = [(label, url) for label, url in links if label.endswith(".metadata.json")]
    post_links = [(label, url) for label, url in links if label.endswith(".submission.md")]
    if len(metadata_links) != 1 or len(post_links) != 1:
        print("Issue must attach exactly one .metadata.json and one .submission.md file.", file=sys.stderr)
        return 1
    metadata_stem = metadata_links[0][0][: -len(".metadata.json")]
    post_stem = post_links[0][0][: -len(".submission.md")]
    if metadata_stem != post_stem or not SLUG.fullmatch(metadata_stem):
        print("Issue attachment names must share a safe canonical slug.", file=sys.stderr)
        return 1
    output.mkdir(parents=True, exist_ok=True)
    for _label, url, filename in (
        (*metadata_links[0], "metadata.json"),
        (*post_links[0], "post.md"),
    ):
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "github.com" or not parsed.path.startswith("/user-attachments/files/"):
            print("Issue attachment URL is not an approved GitHub user attachment.", file=sys.stderr)
            return 1
        request = urllib.request.Request(url, headers={"User-Agent": "aibast-blog-intake"})
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = response.read(MAX_ATTACHMENT_BYTES + 1)
        if len(payload) > MAX_ATTACHMENT_BYTES:
            print("Issue attachment exceeds the allowed size.", file=sys.stderr)
            return 1
        (output / filename).write_bytes(payload)
    print(f"Downloaded approved issue attachments for {metadata_stem}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "render", "check"):
        sub = subcommands.add_parser(command)
        sub.add_argument("--submissions", type=Path, default=DEFAULT_SUBMISSIONS)
        sub.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    import_parser = subcommands.add_parser("import")
    import_parser.add_argument("--metadata", type=Path, required=True)
    import_parser.add_argument("--post", type=Path, required=True)
    import_parser.add_argument("--submissions", type=Path, default=DEFAULT_SUBMISSIONS)
    attachments = subcommands.add_parser("download-issue-attachments")
    attachments.add_argument("--issue-body", type=Path, required=True)
    attachments.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "import":
        return import_submission(args.metadata, args.post, args.submissions)
    if args.command == "download-issue-attachments":
        return download_issue_attachments(args.issue_body, args.output)
    submissions, errors = validate_all(args.submissions)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    if args.command == "validate":
        print(f"PASS: validated {len(submissions)} canonical blog submissions.")
        return 0
    return render(args.submissions, args.output, check=args.command == "check")


if __name__ == "__main__":
    raise SystemExit(main())
