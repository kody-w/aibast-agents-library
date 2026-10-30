#!/usr/bin/env python3
"""Check and approve demo submissions for the Community agents page.

Colleagues submit a finished demo through the GitHub issue form
`.github/ISSUE_TEMPLATE/demo-submission.yml`. The workflow
`.github/workflows/demo-submission.yml` passes the issue body to this script
as a file (never through the shell) and acts on the JSON result.

    check  --body-file F --result R --comment C [--issue N] [--manifest M] [--offline]
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
# Microsoft Stream videos live on SharePoint and need a sign-in, so they cannot
# play on a public page. Only public YouTube links are accepted.

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

# Other vendors' AI products. Demo cards describe what was built with
# Microsoft products, so these names are flagged too. The problem text never
# repeats them, because the check comment is public.
OTHER_AI_PRODUCT_TERMS = (
    "chatgpt",
    "openai",
    "gpt",
    "anthropic",
    "claude",
    "gemini",
    "bard",
    "llama",
    "mistral",
    "grok",
    "perplexity",
    "deepseek",
    "midjourney",
)
OTHER_AI_PRODUCTS_PROBLEM = (
    "Remove the names of AI products from other companies. "
    "Describe the demo with the Microsoft products it uses."
)

# A host a browser URL parser accepts: dot-separated letters, digits and hyphens.
_HOST_LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
HOST_RE = re.compile(rf"^{_HOST_LABEL}(?:\.{_HOST_LABEL})*\.?$")
PORT_RE = re.compile(r"^[0-9]{1,5}$")

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
HANDLE_RE = re.compile(r"(?<![\w.])@[A-Za-z0-9][\w-]*")
NO_RESPONSE = {"", "_no response_", "none"}

MANIFEST_SCHEMA = "aibast-community-tools/1.0"
DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / "community_tools.json"


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
def split_url(url: str) -> tuple[urllib.parse.SplitResult, int | None]:
    """Split a link the way a browser would accept it, or raise ValueError.

    Python's urlsplit accepts hosts and ports that a browser's URL parser
    rejects (spaces, an out-of-range or non-numeric port). Such a link would
    break the public page, so it is refused here.
    """
    if not url or any(ch.isspace() or ord(ch) < 0x20 or ch == "\\" for ch in url):
        raise ValueError("whitespace, control character or backslash")
    parts = urllib.parse.urlsplit(url)
    hostport = parts.netloc.rpartition("@")[2]
    host, colon, port = hostport.rpartition(":") if ":" in hostport else (hostport, "", "")
    if not HOST_RE.match(host):
        raise ValueError("invalid host")
    if colon and port:
        if not PORT_RE.match(port) or int(port) > 65535:
            raise ValueError("invalid port")
    return parts, (int(port) if colon and port else None)


def classify_video_url(url: str) -> str:
    """Return 'youtube', or raise SubmissionError."""
    try:
        parts, port = split_url(url)
    except ValueError as exc:
        if not url.lower().startswith("https://"):
            raise SubmissionError("The video link must start with https://.") from exc
        raise SubmissionError("The video link is not a valid URL.") from exc
    if parts.scheme != "https":
        raise SubmissionError("The video link must start with https://.")
    if parts.username or parts.password or port is not None:
        raise SubmissionError("The video link must be a plain public https link.")
    host = (parts.hostname or "").lower()
    if host in YOUTUBE_HOSTS:
        return "youtube"
    raise SubmissionError(
        f"The video must be a public YouTube link (got {host or 'no host'}). "
        "Microsoft Stream videos need a sign-in, so they cannot play on the public page."
    )


def forbidden_terms_in(text: str, terms: tuple[str, ...] = FORBIDDEN_TERMS) -> list[str]:
    found = []
    lowered = (text or "").lower()
    for term in terms:
        if re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", lowered):
            found.append(term)
    return found


def other_ai_products_in(text: str) -> bool:
    return bool(forbidden_terms_in(text, OTHER_AI_PRODUCT_TERMS))


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
    elif not slugify(title):
        problems.append(
            "Use at least one English letter or number in the demo title, "
            "so the demo can have its own web address."
        )

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
            parts, _port = split_url(onepager)
            if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
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
    if other_ai_products_in(free_text):
        problems.append(OTHER_AI_PRODUCTS_PROBLEM)
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


def widescreen_thumbnail(thumb: str) -> str:
    """Prefer YouTube's 16:9 thumbnail over the 4:3 one with black bars."""
    parts = urllib.parse.urlsplit(thumb)
    if (parts.hostname or "").lower() == "i.ytimg.com" and parts.path.endswith("/hqdefault.jpg"):
        path = parts.path[: -len("hqdefault.jpg")] + "mqdefault.jpg"
        return urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, "", ""))
    return thumb


def resolve_video(url: str, kind: str, fetch=_fetch_json) -> dict:
    """Confirm the video is publicly reachable. Returns oEmbed facts."""
    if kind != "youtube":
        raise SubmissionError("The video must be a public YouTube link.")
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
        result["thumbnail"] = widescreen_thumbnail(thumb)
    return result


# ------------------------------------------------------------------- manifest
def id_problems(manifest: dict, entry_id: str, issue: int | None) -> list[str]:
    """Problems with using entry_id for the demo from this issue.

    An id may be reused only by the issue that first claimed it, so a new
    submission can never replace another team's demo or take its credit.
    """
    if not entry_id:
        return []
    for existing in manifest.get("tools") or []:
        if not isinstance(existing, dict) or existing.get("id") != entry_id:
            continue
        if existing.get("kind") != "demo":
            return ["This title is already used by a related resource. Choose a different title."]
        if issue is None or existing.get("submission_issue") != int(issue):
            return ["This title is already used by another demo. Choose a different title."]
    return []


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
    clash = id_problems(manifest, clean["id"], clean["submission_issue"])
    if clash:
        raise SubmissionError(clash[0])
    for existing in tools:
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
        (
            t for t in tools
            if t.get("kind") == "demo"
            and t.get("id") == clean["id"]
            and t.get("submission_issue") == clean["submission_issue"]
        ),
        None,
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
            "Checked: required confirmations, a public YouTube video link, a "
            "title no other demo uses, and wording that is safe for the public page."
        )
    lines = [
        "Thank you. This demo needs a few changes before review. Edit the "
        "issue to fix them and the checks run again.",
        "",
    ]
    lines += [f"- {p}" for p in problems]
    return "\n".join(lines)


def run_check(body: str, offline: bool, fetch=_fetch_json,
              manifest: dict | None = None, issue: int | None = None) -> tuple[dict, list[str]]:
    entry, problems = validate(parse_issue_form(body))
    if manifest is not None:
        problems += id_problems(manifest, entry.get("id", ""), issue)
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
    check.add_argument("--issue", type=int)
    check.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    check.add_argument("--offline", action="store_true")
    apply_cmd = sub.add_parser("apply")
    apply_cmd.add_argument("--body-file", required=True, type=Path)
    apply_cmd.add_argument("--issue", required=True, type=int)
    apply_cmd.add_argument("--manifest", required=True, type=Path)
    apply_cmd.add_argument("--result", required=True, type=Path)
    apply_cmd.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)

    body = args.body_file.read_text(encoding="utf-8")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    entry, problems = run_check(body, args.offline, manifest=manifest, issue=args.issue)
    result = {"ok": not problems, "problems": problems, "id": entry.get("id", ""),
              "name": entry.get("name", "")}

    if args.command == "check":
        args.comment.write_text(comment_for(problems) + "\n", encoding="utf-8")
    elif not problems:
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
