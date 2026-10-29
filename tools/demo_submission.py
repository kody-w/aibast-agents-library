#!/usr/bin/env python3
"""Check and approve demo submissions for the Community agents page.

Colleagues submit a finished demo through the GitHub issue form
`.github/ISSUE_TEMPLATE/demo-submission.yml`. The workflow
`.github/workflows/demo-submission.yml` passes the issue body to this script
as a file (never through the shell) and acts on the JSON result.

    check  --body-file F --result R --comment C [--offline]
    apply  --body-file F --issue N --manifest community_tools.json --result R [--offline]

Approved demos become `kind: "demo"` entries in community_tools.json, the
existing aibast-community-tools/1.0 manifest. Entries without a kind are
tools, exactly as before. Demo entries stay out of the agent library: the
registry build and the library export both skip them.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

FORM_MARKER = "Submit a demo to Community agents"

TITLE = "Demo title"
VIDEO = "Public video URL"
DESCRIPTION = "Short description"
INDUSTRY = "Industry"
PRODUCTS = "Microsoft products used"
TEAM = "Owning team or channel"
ONEPAGER = "One-pager URL (optional)"
CONFIRMATIONS = "Before you submit"

INDUSTRIES = (
    "B2B Sales",
    "B2C Sales",
    "Cross-Industry",
    "Energy",
    "Financial Services",
    "Healthcare",
    "Human Resources",
    "Manufacturing",
    "Professional Services",
    "Retail & CPG",
    "SLG Government",
    "Software & Digital Products",
    "Telecom, Media & Gaming",
)

PRODUCT_OPTIONS = (
    "Copilot Studio",
    "Microsoft 365 Copilot",
    "Dataverse",
    "Power Apps",
    "Power Automate",
    "Teams",
    "SharePoint",
    "Dynamics 365",
    "Other",
)

REQUIRED_CONFIRMATIONS = (
    "The demo uses synthetic data only.",
    "The demo contains no customer names or customer data.",
    "The video is public and ours to share.",
    "It is built only with Microsoft 365, Power Platform, Dynamics 365 or Copilot Studio (no Azure services).",
)

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
STREAM_HOST_SUFFIXES = ("microsoftstream.com",)

# Words that must never reach the public page. Matched case-insensitively on
# word boundaries across every free-text field.
FORBIDDEN_TERMS = (
    "rapp factory",
    "confidential",
    "internal only",
    "internal use only",
    "do not share",
    "do not distribute",
    "nda",
    "azure",
)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
HANDLE_RE = re.compile(r"(?<![\w.])@[A-Za-z0-9][\w-]*")
NO_RESPONSE = {"", "_no response_", "none"}

MANIFEST_SCHEMA = "aibast-community-tools/1.0"


class SubmissionError(Exception):
    pass


# --------------------------------------------------------------------- parse
def parse_issue_form(body: str) -> dict[str, str]:
    """Split a rendered issue form into {heading: raw value}."""
    sections: dict[str, str] = {}
    current = None
    lines: list[str] = []
    for line in (body or "").replace("\r\n", "\n").split("\n"):
        heading = re.match(r"^###\s+(.+?)\s*$", line)
        if heading:
            if current is not None:
                sections[current] = "\n".join(lines).strip()
            current = heading.group(1).strip()
            lines = []
        elif current is not None:
            lines.append(line)
    if current is not None:
        sections[current] = "\n".join(lines).strip()
    return sections


def _value(sections: dict[str, str], key: str) -> str:
    value = sections.get(key, "").strip()
    return "" if value.lower() in NO_RESPONSE else value


def _checked(raw: str) -> list[str]:
    return [
        m.group(2).strip()
        for m in re.finditer(r"^\s*[-*]\s+\[([xX])\]\s+(.+?)\s*$", raw or "", re.M)
    ]


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60].strip("-")


# ------------------------------------------------------------------ validate
def classify_video_url(url: str) -> str:
    """Return 'youtube' or 'stream', or raise SubmissionError."""
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError as exc:
        raise SubmissionError("The video link is not a valid URL.") from exc
    if parts.scheme != "https":
        raise SubmissionError("The video link must start with https://.")
    if parts.username or parts.password or parts.port:
        raise SubmissionError("The video link must be a plain public https link.")
    host = (parts.hostname or "").lower()
    if host in YOUTUBE_HOSTS:
        return "youtube"
    if any(host == s or host.endswith("." + s) for s in STREAM_HOST_SUFFIXES):
        return "stream"
    raise SubmissionError(
        "The video must be hosted on YouTube or Microsoft Stream "
        f"(got {host or 'no host'})."
    )


def forbidden_terms_in(text: str) -> list[str]:
    found = []
    lowered = (text or "").lower()
    for term in FORBIDDEN_TERMS:
        if re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", lowered):
            found.append(term)
    return found


def _sentences(text: str) -> int:
    return len([s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()])


def validate(sections: dict[str, str]) -> tuple[dict, list[str]]:
    """Validate a parsed form. Returns (entry fields, problems)."""
    problems: list[str] = []
    title = _value(sections, TITLE)
    video = _value(sections, VIDEO)
    description = " ".join(_value(sections, DESCRIPTION).split())
    industry = _value(sections, INDUSTRY)
    products = [p for p in _checked(sections.get(PRODUCTS, "")) if p in PRODUCT_OPTIONS]
    team = " ".join(_value(sections, TEAM).split())
    onepager = _value(sections, ONEPAGER)
    confirmed = set(_checked(sections.get(CONFIRMATIONS, "")))

    if not title:
        problems.append("Add a demo title.")
    elif len(title) > 80:
        problems.append("Keep the demo title to 80 characters or fewer.")

    video_kind = None
    if not video:
        problems.append("Add the public video link.")
    else:
        try:
            video_kind = classify_video_url(video)
        except SubmissionError as exc:
            problems.append(str(exc))

    if not description:
        problems.append("Add a short description.")
    else:
        count = _sentences(description)
        if count < 2 or count > 4:
            problems.append(f"Write the description in 2 to 4 sentences (found {count}).")
        if len(description) > 700:
            problems.append("Keep the description under 700 characters.")

    if industry not in INDUSTRIES:
        problems.append("Pick an industry from the list.")
    if not products:
        problems.append("Tick at least one Microsoft product.")
    if not team:
        problems.append("Add the owning team or channel for credit.")

    if onepager:
        try:
            parts = urllib.parse.urlsplit(onepager)
            if parts.scheme != "https" or not parts.hostname or parts.username:
                raise ValueError
        except ValueError:
            problems.append("The one-pager link must be a public https link.")

    for item in REQUIRED_CONFIRMATIONS:
        if item not in confirmed:
            problems.append(f"Confirm: {item}")

    free_text = "\n".join([title, description, team])
    terms = forbidden_terms_in(free_text)
    if terms:
        problems.append(
            "Remove these words, which cannot appear on the public page: "
            + ", ".join(sorted(terms)) + "."
        )
    if EMAIL_RE.search(free_text) or HANDLE_RE.search(free_text):
        problems.append(
            "Remove email addresses and @handles. Credit a team or channel, not a person."
        )

    entry = {
        "id": slugify(title) if title else "",
        "kind": "demo",
        "name": title,
        "url": video,
        "author": team,
        "description": description,
        "industry": industry,
        "products": products,
    }
    if onepager:
        entry["onepager"] = onepager
    entry["_video_kind"] = video_kind
    return entry, problems


# -------------------------------------------------------------------- network
def _fetch_json(url: str, timeout: float = 15):
    request = urllib.request.Request(url, headers={"User-Agent": "aibast-demo-check"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def resolve_video(url: str, kind: str, fetch=_fetch_json, opener=None) -> dict:
    """Confirm the video is publicly reachable. Returns oEmbed facts."""
    if kind == "youtube":
        oembed = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(url, safe="")
        try:
            data = fetch(oembed)
        except (urllib.error.URLError, ValueError, TimeoutError) as exc:
            raise SubmissionError(
                "The YouTube video could not be found or is not public."
            ) from exc
        thumb = data.get("thumbnail_url", "")
        result = {"title": data.get("title", "")}
        if isinstance(thumb, str) and thumb.startswith("https://"):
            result["thumbnail"] = thumb
        return result
    open_url = opener or (lambda u: urllib.request.urlopen(  # noqa: S310
        urllib.request.Request(u, headers={"User-Agent": "aibast-demo-check"}), timeout=15
    ))
    try:
        with open_url(url) as response:
            final = response.geturl()
    except (urllib.error.URLError, ValueError, TimeoutError) as exc:
        raise SubmissionError("The Stream video could not be opened.") from exc
    host = (urllib.parse.urlsplit(final).hostname or "").lower()
    if "login" in host:
        raise SubmissionError(
            "The Stream video asks viewers to sign in. Share a public link."
        )
    return {}


# ------------------------------------------------------------------- manifest
def apply_entry(manifest: dict, entry: dict, issue: int, today: str) -> dict:
    """Add or replace a demo entry in the community manifest."""
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise SubmissionError(f"Manifest schema must be {MANIFEST_SCHEMA}.")
    tools = manifest.get("tools")
    if not isinstance(tools, list):
        raise SubmissionError("Manifest tools must be a list.")
    clean = {k: v for k, v in entry.items() if not k.startswith("_")}
    clean["submission_issue"] = int(issue)
    if not clean.get("id"):
        raise SubmissionError("The demo needs a title to build its id.")
    for existing in tools:
        if (
            existing.get("id") == clean["id"]
            and existing.get("kind") != "demo"
        ):
            raise SubmissionError(
                f"The id {clean['id']} is already used by a related resource."
            )
        if (
            existing.get("kind") == "demo"
            and existing.get("submission_issue") == clean["submission_issue"]
            and existing.get("id") != clean["id"]
        ):
            # A retitled resubmission replaces its earlier entry.
            existing["_drop"] = True
    kept = [
        t for t in tools
        if not t.get("_drop") and not (t.get("kind") == "demo" and t.get("id") == clean["id"])
    ]
    for t in kept:
        t.pop("_drop", None)
    previous = next(
        (t for t in tools if t.get("kind") == "demo" and t.get("id") == clean["id"]), None
    )
    if previous and previous.get("graduated_to"):
        clean["graduated_to"] = previous["graduated_to"]
    kept.append(clean)
    manifest["tools"] = kept
    manifest["count"] = len(kept)
    manifest["snapshot_date"] = today
    return manifest


def comment_for(problems: list[str]) -> str:
    if not problems:
        return (
            "Thank you. This demo passed the automatic checks and is ready for "
            "review by a library maintainer.\n\n"
            "Checked: required confirmations, a public video link on an allowed "
            "host, and wording that is safe for the public page."
        )
    lines = [
        "Thank you. This demo needs a few changes before review. Edit the "
        "issue to fix them and the checks run again.",
        "",
    ]
    lines += [f"- {p}" for p in problems]
    return "\n".join(lines)


def run_check(body: str, offline: bool, fetch=_fetch_json) -> tuple[dict, list[str]]:
    entry, problems = validate(parse_issue_form(body))
    if not problems and not offline:
        try:
            facts = resolve_video(entry["url"], entry["_video_kind"], fetch=fetch)
            if facts.get("thumbnail"):
                entry["thumbnail"] = facts["thumbnail"]
        except SubmissionError as exc:
            problems.append(str(exc))
    return entry, problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("--body-file", required=True, type=Path)
    check.add_argument("--result", required=True, type=Path)
    check.add_argument("--comment", required=True, type=Path)
    check.add_argument("--offline", action="store_true")
    apply_cmd = sub.add_parser("apply")
    apply_cmd.add_argument("--body-file", required=True, type=Path)
    apply_cmd.add_argument("--issue", required=True, type=int)
    apply_cmd.add_argument("--manifest", required=True, type=Path)
    apply_cmd.add_argument("--result", required=True, type=Path)
    apply_cmd.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)

    body = args.body_file.read_text(encoding="utf-8")
    entry, problems = run_check(body, args.offline)
    result = {"ok": not problems, "problems": problems, "id": entry.get("id", ""),
              "name": entry.get("name", "")}

    if args.command == "check":
        args.comment.write_text(comment_for(problems) + "\n", encoding="utf-8")
    elif not problems:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        try:
            apply_entry(manifest, entry, args.issue, date.today().isoformat())
        except SubmissionError as exc:
            result.update(ok=False, problems=[str(exc)])
        else:
            args.manifest.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
    args.result.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
