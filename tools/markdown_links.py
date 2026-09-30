#!/usr/bin/env python3
"""Check Markdown links offline, using Git's case-exact file names.

Usage: python tools/markdown_links.py PATH...

Directories select their Markdown descendants. ``--root`` selects a repository
explicitly; ``--repository`` maps that repository's GitHub main-branch URLs to
local files. ``check_links`` accepts an in-memory document overlay so generated
pages can be checked before writing them.
"""
from __future__ import annotations

import argparse
import html
import json
import posixpath
import re
import subprocess
import sys
import unicodedata
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import NamedTuple
from urllib.parse import unquote, urlsplit


REPOSITORY = "microsoft/aibast-agents-library"
PAGES = "https://microsoft.github.io/aibast-agents-library/"
RAW = "https://raw.githubusercontent.com/microsoft/aibast-agents-library/main/"
RUNBOOKS = "https://github.com/microsoft/ai-agent-runbooks/blob/main/"
RUNBOOKS_REFERENCES = frozenset(
    RUNBOOKS + "03-references/" + name
    for name in ("Agent-Delivery-Reference-Library.md", "Known-Limitations-and-Workarounds.md")
)
HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
REFERENCE = re.compile(r"^ {0,3}\[[^\]\n]+\]:[ \t]*(<[^>\n]*>|(?:\\.|[^\s])+)", re.M)
ATTRIBUTE = re.compile(
    r"\b([a-zA-Z_:][\w:.-]*)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s\"'=<>`]+))",
    re.I,
)
HTML_TAG = re.compile(
    r"""<[a-zA-Z][a-zA-Z0-9:-]*(?=\s|/?>)(?:"[^"]*"|'[^']*'|[^'">])*>""", re.S,
)
CODE_SPAN = re.compile(r"(?<![\\`])(`+)(?!`)(.*?)(?<!`)\1(?!`)", re.S)
LOCAL_PATH = re.compile(
    r"^(?:[a-z]:[/\\]|\\\\|~[/\\]|/"
    r"(?:Users|home|Volumes|private|var|tmp|etc|usr|opt|Applications|Library|mnt|media)(?:/|$))",
    re.I,
)


class LinkProblem(NamedTuple):
    source: str
    line: int
    target: str
    kind: str
    resolved: str
    detail: str

    def __str__(self) -> str:
        return f"{self.source}:{self.line}: {self.target!r}: {self.kind}: {self.detail}"


def git_file_universe(root: Path, documents: Mapping[str, str] | None = None) -> set[str]:
    """Include exact existing Git paths, rejecting stale index casing on macOS."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=root, capture_output=True, text=True, check=True,
    )
    directory_names = {}

    def exists_exactly(relative):
        if not (root / relative).is_file():
            return False
        parent = root
        for component in relative.split("/"):
            if parent not in directory_names:
                try:
                    directory_names[parent] = {entry.name for entry in parent.iterdir()}
                except (FileNotFoundError, NotADirectoryError):
                    directory_names[parent] = set()
            if component not in directory_names[parent]:
                return False
            parent /= component
        return True

    files = {p for p in result.stdout.split("\0") if p and exists_exactly(p)}
    return files | set(documents or {})


def _blank(text: str) -> str:
    return "".join("\n" if char == "\n" else " " for char in text)


def _unquote_line(line: str, limit: int | None = None) -> tuple[str, int]:
    depth = 0
    while limit is None or depth < limit:
        prefix = re.match(r"^ {0,3}>[ \t]?", line)
        if prefix is None:
            break
        depth += 1
        line = line[prefix.end():]
    return line, depth


def strip_code(text: str, *, inline: bool = True, fence_fill: str = "") -> str:
    """Mask code, optionally retaining fences as non-heading section content."""
    lines = []
    fence = None

    def masked_fence(line):
        return fence_fill + ("\n" if line.endswith("\n") else "") if fence_fill else _blank(line)

    for line in text.splitlines(keepends=True):
        if fence is not None:
            char, length, quote_depth = fence
            content, depth = _unquote_line(line, quote_depth)
            if depth == quote_depth or not line.strip():
                if re.fullmatch(r"\s*" + re.escape(char) + "{" + str(length) + r",}\s*", content):
                    fence = None
                lines.append(masked_fence(line))
                continue
            fence = None
        content, quote_depth = _unquote_line(line)
        opener = re.match(r"^[ \t]*(`{3,}|~{3,})(.*)", content)
        if opener and not (opener[1][0] == "`" and "`" in opener[2]):
            fence = (opener[1][0], len(opener[1]), quote_depth)
            lines.append(masked_fence(line))
        else:
            lines.append(line)
    visible = "".join(lines)
    visible = re.sub(r"<!--.*?-->", lambda match: _blank(match[0]), visible, flags=re.S)
    if inline:
        visible = CODE_SPAN.sub(lambda match: _blank(match[0]), visible)
    return visible


def _inline_destinations(text: str):
    """Yield destination spans, including balanced/escaped parentheses."""
    for match in re.finditer(r"(?<!\\)\]\([ \t\n]*", text):
        start = end = match.end()
        if start == len(text):
            continue
        if text[start] == "<":
            close = text.find(">", start + 1)
            if close == -1 or "\n" in text[start:close]:
                continue
            start += 1
            end = close
            after = close + 1
        else:
            depth = 0
            while end < len(text):
                char = text[end]
                if char == "\\" and end + 1 < len(text):
                    end += 2
                    continue
                if char == "(":
                    depth += 1
                elif char == ")":
                    if not depth:
                        break
                    depth -= 1
                elif char.isspace():
                    break
                end += 1
            if depth:
                continue
            after = end
        closing = re.match(r"\s*(?:(?:\"[^\"]*\"|'[^']*'|\([^)]*\))\s*)?\)", text[after:])
        if closing:
            yield match.start(), start, end


def _html_attributes(text: str, names: set[str]):
    for tag in HTML_TAG.finditer(text):
        for attribute in ATTRIBUTE.finditer(tag[0]):
            if attribute[1].lower() in names:
                value = next(value for value in attribute.groups()[1:] if value is not None)
                yield tag.start() + attribute.start(), value


def extract_links(text: str) -> list[tuple[int, str]]:
    """Extract inline/image destinations, reference definitions and href/src."""
    visible = strip_code(text)
    hits = [(offset, visible[start:end]) for offset, start, end in _inline_destinations(visible)]
    hits.extend((match.start(), match[1].strip("<>")) for match in REFERENCE.finditer(visible))
    hits.extend(_html_attributes(visible, {"href", "src"}))
    return [
        (visible.count("\n", 0, offset) + 1, html.unescape(re.sub(r"\\([\\()[\]<>])", r"\1", target)))
        for offset, target in sorted(hits)
    ]


def github_slug(text: str) -> str:
    """GitHub heading slug: preserve combining marks and inline-code content."""
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]*)\](?:\[[^\]]*\])", r"\1", text)
    text = html.unescape(re.sub(r"<[^>]+>", "", text.replace("`", "")))
    return "".join(
        char for char in text.strip().lower()
        if unicodedata.category(char)[0] in "LN"
        or unicodedata.category(char) == "Mn" or char in " -_"
    ).replace(" ", "-")


def anchors_of(text: str) -> set[str]:
    """Collect GitHub heading ids and explicit HTML id/name anchors."""
    visible = strip_code(text, inline=False)
    anchors, used = set(), set()
    lines = visible.splitlines()
    for index, line in enumerate(lines):
        heading = HEADING.match(line)
        title = heading[2] if heading else None
        if (
            title is None and line.strip() and index + 1 < len(lines)
            and re.fullmatch(r" {0,3}(?:=+|-+)[ \t]*", lines[index + 1])
            and not re.match(r"^\s*(?:[-*+] |\|)", line)
        ):
            title = line.strip()
        if title is not None:
            base = github_slug(title)
            slug, suffix = base, 0
            while slug in used:
                suffix += 1
                slug = f"{base}-{suffix}"
            used.add(slug)
            anchors.add(slug)
    anchors.update(html.unescape(value).lower() for _, value in _html_attributes(strip_code(text), {"id", "name"}))
    return anchors


def runbooks_allowlist(root: Path, files: Iterable[str]) -> set[str]:
    allowed = set(RUNBOOKS_REFERENCES)
    if "02-patterns/patterns.json" in files:
        data = json.loads((root / "02-patterns/patterns.json").read_text(encoding="utf-8"))
        allowed.update(
            entry[field] for entry in data["runbooks_patterns"]
            for field in ("url", "runbook_url")
        )
    return allowed


def check_links(
    root: Path,
    documents: Mapping[str, str],
    *,
    files: Iterable[str] | None = None,
    allowed_runbooks_urls: Iterable[str] | None = None,
    repository: str = REPOSITORY,
) -> list[LinkProblem]:
    """Validate targets only against the Git universe plus in-memory documents.

    External URLs are not fetched. AIBAST audits reject foreign GitHub owners
    and Pages hosts and fail closed on unmapped Pages/raw-content URLs.
    Auditing another repository uses its own namespace instead. Runbooks URLs
    require an explicit allowlist (the pattern index and documented references).
    """
    root = Path(root)
    known = set(files) if files is not None else git_file_universe(root)
    known.update(documents)
    directories = {"."}
    for path in known:
        directories.update("/".join(path.split("/")[:i]) for i in range(1, path.count("/") + 1))
    available = known | directories
    near = {}
    for path in sorted(available):
        near.setdefault(path.casefold(), []).append(path)
    allowed = set(allowed_runbooks_urls) if allowed_runbooks_urls is not None else runbooks_allowlist(root, known)
    problems = []
    anchor_cache = {}
    local_repositories = {REPOSITORY, repository}
    aibast_policy = repository.casefold() == REPOSITORY

    for source, text in sorted(documents.items()):
        for line, raw in extract_links(text):
            target = raw.strip()
            try:
                url = urlsplit(target)
            except ValueError as error:
                problems.append(LinkProblem(source, line, raw, "invalid URL", "", str(error)))
                continue
            host = (url.hostname or "").lower()
            github = host in ("github.com", "www.github.com")
            owner = unquote(url.path).strip("/").split("/", 1)[0].casefold()
            if (
                url.scheme.lower() == "file" or LOCAL_PATH.match(unquote(target))
                or (aibast_policy and github and owner != "microsoft")
                or (aibast_policy and host.endswith(".github.io") and host != "microsoft.github.io")
            ):
                problems.append(LinkProblem(source, line, raw, "forbidden link", "", "unapproved GitHub owner/Pages host or local path"))
                continue

            path, fragment = unquote(url.path), unquote(url.fragment).lower()
            absolute = False
            pages = (
                host == "microsoft.github.io" and url.scheme.lower() == "https"
                and url.netloc.lower() == "microsoft.github.io"
                and url.path.startswith("/aibast-agents-library/")
            )
            raw_content = (
                host == "raw.githubusercontent.com" and url.scheme.lower() == "https"
                and url.netloc.lower() == "raw.githubusercontent.com"
                and url.path.startswith("/microsoft/aibast-agents-library/main/")
            )
            if aibast_policy and (
                (host == "microsoft.github.io" and not pages)
                or (host == "raw.githubusercontent.com" and not raw_content)
            ):
                problems.append(LinkProblem(source, line, raw, "unmapped URL", "", "outside the canonical Pages/raw-content prefix"))
                continue
            if pages:
                path = unquote(url.path[len("/aibast-agents-library/"):])
                if not path or path.endswith("/"):
                    path += "index.html"
                absolute = True
            elif raw_content:
                path = unquote(url.path[len("/microsoft/aibast-agents-library/main/"):])
                absolute = True
            elif github:
                match = re.fullmatch(r"/([^/]+/[^/]+)/(?:blob|tree)/main(?:/(.*))?", url.path)
                if match and match[1].casefold() in local_repositories:
                    path, absolute = unquote(match[2] or ""), True
                elif match and match[1] == "microsoft/ai-agent-runbooks":
                    if target not in allowed:
                        problems.append(LinkProblem(
                            source, line, raw, "unlisted runbooks URL", "",
                            "not in patterns.json or the documented references",
                        ))
                    continue
                else:
                    continue
            elif url.scheme or url.netloc:
                continue

            if absolute or path.startswith("/"):
                resolved = posixpath.normpath(path.lstrip("/"))
            elif not path:
                resolved = source
            else:
                resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source), path))
            if resolved == ".." or resolved.startswith("../"):
                problems.append(LinkProblem(source, line, raw, "escapes repository", resolved, resolved))
                continue
            if resolved not in available:
                alternatives = near.get(resolved.casefold(), [])
                kind = "case mismatch" if alternatives else "missing target"
                detail = f"{resolved}; expected {', '.join(alternatives)}" if alternatives else resolved
                problems.append(LinkProblem(source, line, raw, kind, resolved, detail))
                continue
            if not fragment:
                continue
            anchor_path = resolved
            if resolved in directories:
                prefix = "" if resolved == "." else resolved + "/"
                readmes = [prefix + name for name in ("README.md", "readme.md", "Readme.md")]
                anchor_path = next((p for p in readmes if p in known), "")
                if not anchor_path:
                    problems.append(LinkProblem(
                        source, line, raw, "missing anchor", resolved,
                        f"#{fragment}: directory has no Markdown README",
                    ))
                    continue
            if not anchor_path.lower().endswith((".md", ".markdown", ".html", ".htm")):
                continue
            if anchor_path not in anchor_cache:
                body = documents.get(anchor_path)
                if body is None:
                    body = (root / anchor_path).read_text(encoding="utf-8")
                anchor_cache[anchor_path] = anchors_of(body)
            if fragment not in anchor_cache[anchor_path]:
                problems.append(LinkProblem(
                    source, line, raw, "missing anchor", anchor_path,
                    f"#{fragment} in {anchor_path}",
                ))
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Markdown files or directories to check")
    parser.add_argument("--root", type=Path, help="repository root (otherwise inferred from the first path)")
    parser.add_argument("--repository", default=REPOSITORY, help="GitHub OWNER/REPO for local main-branch links")
    args = parser.parse_args(argv)
    try:
        first = Path(args.paths[0]).absolute()
        root = args.root
        if root is None:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=first if first.is_dir() else first.parent,
                capture_output=True, text=True, check=True,
            )
            root = Path(result.stdout.strip())
        root = root.absolute()
        files = git_file_universe(root)
        selected = set()
        for value in args.paths:
            path = Path(value).absolute()
            relative = path.relative_to(root).as_posix()
            if relative in files:
                selected.add(relative)
            else:
                prefix = "" if relative == "." else relative.rstrip("/") + "/"
                matches = {p for p in files if p.startswith(prefix) and p.lower().endswith(".md")}
                if not matches:
                    raise ValueError(f"{value}: no case-exact Markdown paths in Git's file universe")
                selected.update(matches)
        documents = {p: (root / p).read_text(encoding="utf-8") for p in sorted(selected)}
        problems = check_links(root, documents, files=files, repository=args.repository)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f"Cannot check links: {error}", file=sys.stderr)
        return 1
    for problem in problems:
        print(problem)
    print(f"Checked {len(documents)} documents; {len(problems)} problems.")
    return int(bool(problems))


if __name__ == "__main__":
    raise SystemExit(main())
