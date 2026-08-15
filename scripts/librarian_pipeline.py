#!/usr/bin/env python3
"""Validate canonical library-source submissions and generate the local catalog.

The browser reads only state/libraries.json. It never fetches, imports, or
executes material from a submitted canonical URL; that work belongs to approved
CI or a trusted backend after maintainer review.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUBMISSIONS = ROOT / "submissions" / "libraries"
DEFAULT_OUTPUT = ROOT / "state" / "libraries.json"
SCHEMA = "aibast-library-source/2.0"
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_COMMIT = re.compile(r"^[0-9a-f]{40}$")
# A production catalog uses microsoft; live staging Pages uses kody-w. The
# browser selects the matching owner from its Pages hostname before mounting
# Giscus, while canonical metadata accepts only these controlled distributions.
DISCUSSION = re.compile(
    r"^https://github\.com/(?:microsoft|kody-w)/aibast-agents-library/discussions/[1-9]\d*$"
)
STATUSES = {"first_party", "subscribed", "quarantined", "community_suggested", "stale"}
TRUST_TIERS = {"first_party", "reviewed", "unverified", "quarantined"}
REQUIRED_SECTIONS = {"Why useful", "Trust and review notes", "Update expectations"}
SECRET = re.compile(
    r"\b(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,})\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SourceSubmission:
    directory: Path
    metadata: dict[str, Any]
    source: str

    @property
    def slug(self) -> str:
        return str(self.metadata.get("slug", ""))


def text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def https(value: Any) -> bool:
    parsed = urlparse(value) if isinstance(value, str) else None
    return bool(parsed and parsed.scheme == "https" and parsed.netloc)


def pinned_github_source(value: Any, immutable_ref: Any) -> bool:
    if not https(value) or not isinstance(immutable_ref, str) or not GIT_COMMIT.fullmatch(immutable_ref):
        return False
    parsed = urlparse(value)
    if parsed.hostname != "github.com":
        return False
    return f"/tree/{immutable_ref}" in parsed.path or f"/blob/{immutable_ref}/" in parsed.path


def headings(source: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in re.finditer(r"^##\s+(.+?)\s*$", source, flags=re.MULTILINE)
    }


def read_submission(directory: Path) -> SourceSubmission:
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise ValueError("metadata.json must contain an object")
    return SourceSubmission(directory, metadata, (directory / "source.md").read_text(encoding="utf-8"))


def validate_submission(submission: SourceSubmission) -> list[str]:
    metadata = submission.metadata
    prefix = submission.directory.as_posix()
    errors: list[str] = []
    private_access = metadata.get("access_flow") == "owner_manual_private_channel"

    if metadata.get("schema") != SCHEMA:
        errors.append(f"{prefix}: metadata.schema must equal {SCHEMA}")
    if metadata.get("contribution_type") != "library_source":
        errors.append(f"{prefix}: metadata.contribution_type must be library_source")
    if not SLUG.fullmatch(submission.slug):
        errors.append(f"{prefix}: metadata.slug must be lowercase kebab-case")
    elif submission.directory.name != submission.slug:
        errors.append(f"{prefix}: directory name must match metadata.slug")

    for key, minimum in {
        "name": 3,
        "source_type": 3,
        "source_format": 3,
        "owner": 3,
        "spdx_license": 2,
        "trust_review_notes": 30,
        "review_cadence": 3,
        "why_useful": 30,
        "manifest_locator": 1,
    }.items():
        if len(text(metadata.get(key))) < minimum:
            errors.append(f"{prefix}: metadata.{key} must contain at least {minimum} characters")
    if private_access:
        if text(metadata.get("canonical_url")):
            errors.append(f"{prefix}: private access sources must not expose canonical_url")
        if metadata.get("immutable_ref") != "owner-managed-private":
            errors.append(f"{prefix}: private access sources must use immutable_ref owner-managed-private")
        if metadata.get("acknowledgement_terms_version") != "2026-08-15":
            errors.append(f"{prefix}: private access sources must declare acknowledgement_terms_version 2026-08-15")
        assets = metadata.get("public_safe_assets")
        if not isinstance(assets, list) or not assets:
            errors.append(f"{prefix}: private access sources require public_safe_assets")
        else:
            for asset in assets:
                if not isinstance(asset, dict) or not all(text(asset.get(key)) for key in ("id", "title", "description", "kind")):
                    errors.append(f"{prefix}: each public_safe_assets entry requires id, title, description, and kind")
                    break
    elif not pinned_github_source(metadata.get("canonical_url"), metadata.get("immutable_ref")):
        errors.append(f"{prefix}: metadata.canonical_url must be a GitHub repo/blob URL pinned to immutable_ref")
    if not SHA256.fullmatch(text(metadata.get("source_digest"))):
        errors.append(f"{prefix}: metadata.source_digest must be a SHA-256 digest")
    if not isinstance(metadata.get("enabled"), bool):
        errors.append(f"{prefix}: metadata.enabled must be boolean")
    if metadata.get("trust_tier") not in TRUST_TIERS:
        errors.append(f"{prefix}: metadata.trust_tier must be one of {', '.join(sorted(TRUST_TIERS))}")
    if metadata.get("status") not in STATUSES:
        errors.append(f"{prefix}: metadata.status must be one of {', '.join(sorted(STATUSES))}")
    expected_fetch_policy = "owner_private_channel_only" if private_access else "ci_or_trusted_backend_only"
    if metadata.get("fetch_policy") != expected_fetch_policy:
        errors.append(f"{prefix}: metadata.fetch_policy must be {expected_fetch_policy}")
    if metadata.get("browser_execution") != "never":
        errors.append(f"{prefix}: metadata.browser_execution must be never")
    discussion = text(metadata.get("discussion_url"))
    if discussion and not DISCUSSION.fullmatch(discussion):
        errors.append(f"{prefix}: metadata.discussion_url must be a canonical AIBAST GitHub Discussion URL when present")
    locator = text(metadata.get("manifest_locator"))
    if locator.startswith(("/", "\\")) or ".." in Path(locator).parts:
        errors.append(f"{prefix}: metadata.manifest_locator must be a relative safe path")
    if any(token in text(metadata.get("source_type")).lower() + text(metadata.get("source_format")).lower() for token in ("installer", "executable", "opaque web page")):
        errors.append(f"{prefix}: executable installers and opaque web pages are not accepted library sources")
    if len(re.findall(r"\S+", submission.source)) < 80:
        errors.append(f"{prefix}: source.md must contain at least 80 words")
    missing = REQUIRED_SECTIONS - headings(submission.source)
    if missing:
        errors.append(f"{prefix}: source.md is missing sections: {', '.join(sorted(missing))}")
    if SECRET.search(submission.source) or SECRET.search(json.dumps(metadata)):
        errors.append(f"{prefix}: source appears to contain a credential")
    return errors


def load_submissions(root: Path) -> list[SourceSubmission]:
    if not root.exists():
        return []
    return [
        read_submission(directory)
        for directory in sorted(path for path in root.iterdir() if path.is_dir() and not path.name.startswith("."))
    ]


def validate_all(root: Path) -> tuple[list[SourceSubmission], list[str]]:
    submissions = load_submissions(root)
    errors: list[str] = []
    slugs: set[str] = set()
    urls: set[str] = set()
    items: set[str] = set()
    for submission in submissions:
        errors.extend(validate_submission(submission))
        if submission.slug in slugs:
            errors.append(f"{submission.directory}: duplicate slug {submission.slug}")
        slugs.add(submission.slug)
        canonical_url = text(submission.metadata.get("canonical_url"))
        if canonical_url in urls:
            errors.append(f"{submission.directory}: duplicate canonical_url {canonical_url}")
        urls.add(canonical_url)
        for item in submission.metadata.get("items", []):
            if not isinstance(item, dict) or not SLUG.fullmatch(text(item.get("slug"))):
                errors.append(f"{submission.directory}: each item requires a lowercase slug")
                continue
            item_id = f"{submission.slug}:{item['slug']}"
            if item_id in items:
                errors.append(f"{submission.directory}: duplicate namespaced item {item_id}")
            items.add(item_id)
    if not submissions:
        errors.append(f"{root}: no library-source submissions found")
    return submissions, errors


def catalog(submissions: list[SourceSubmission]) -> dict[str, Any]:
    fields = (
        "slug",
        "name",
        "canonical_url",
        "source_type",
        "source_format",
        "owner",
        "spdx_license",
        "trust_review_notes",
        "review_cadence",
        "why_useful",
        "status",
        "trust_tier",
        "enabled",
        "immutable_ref",
        "manifest_locator",
        "source_digest",
        "fetch_policy",
        "browser_execution",
        "discussion_url",
        "access_flow",
        "acknowledgement_terms_version",
        "public_catalog_id",
        "public_safe_assets",
        "sort_order",
    )
    sources = [
        {field: submission.metadata.get(field) for field in fields}
        for submission in sorted(submissions, key=lambda item: (item.metadata.get("sort_order", 100), item.metadata["status"], item.metadata["name"].lower()))
    ]
    items = []
    for submission in submissions:
        for item in submission.metadata.get("items", []):
            item_slug = item["slug"]
            items.append(
                {
                    "id": f"{submission.slug}:{item_slug}",
                    "library_slug": submission.slug,
                    "slug": item_slug,
                    "manifest_locator": item.get("manifest_locator", submission.metadata["manifest_locator"]),
                    "digest": item.get("digest", submission.metadata["source_digest"]),
                }
            )
    return {
        "schema": "aibast-libraries/2.0",
        "sources": sources,
        "items": sorted(items, key=lambda item: item["id"]),
        "item_namespace": "library-slug:item-slug",
        "browser_policy": "metadata_only_no_remote_content_execution",
    }


def render(root: Path, output: Path, check: bool) -> int:
    submissions, errors = validate_all(root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    expected = json.dumps(catalog(submissions), indent=2) + "\n"
    actual = output.read_text(encoding="utf-8") if output.exists() else ""
    if check:
        if actual != expected:
            print(f"{output}: generated librarian catalog has drifted; run scripts/librarian_pipeline.py render", file=sys.stderr)
            return 1
        print(f"PASS: {output} matches {len(submissions)} canonical library-source submissions.")
        return 0
    if actual != expected:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(expected, encoding="utf-8")
        print(f"Wrote generated librarian catalog for {len(submissions)} sources.")
    else:
        print(f"No librarian catalog changes; {output} is current.")
    return 0


def import_submission(metadata_path: Path, source_path: Path, root: Path) -> int:
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be a JSON object")
        slug = text(metadata.get("slug"))
        directory = root / slug
        candidate = SourceSubmission(directory, metadata, source_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Import failed: {error}", file=sys.stderr)
        return 1
    errors = validate_submission(candidate)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    if directory.exists():
        print(f"Import failed: {directory} already exists", file=sys.stderr)
        return 1
    directory.mkdir(parents=True)
    (directory / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    (directory / "source.md").write_text(candidate.source.rstrip() + "\n", encoding="utf-8")
    print(f"Imported canonical library source {slug}.")
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
    import_parser.add_argument("--source", type=Path, required=True)
    import_parser.add_argument("--submissions", type=Path, default=DEFAULT_SUBMISSIONS)
    args = parser.parse_args()

    if args.command == "import":
        return import_submission(args.metadata, args.source, args.submissions)
    submissions, errors = validate_all(args.submissions)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    if args.command == "validate":
        print(f"PASS: validated {len(submissions)} canonical library-source submissions.")
        return 0
    return render(args.submissions, args.output, check=args.command == "check")


if __name__ == "__main__":
    raise SystemExit(main())
