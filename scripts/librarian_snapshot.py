#!/usr/bin/env python3
"""Create librarian metric/snapshot sidecars without executing remote content.

This is intentionally metadata-only. A future trusted ingestion worker may
download a pinned artifact into an isolated CI workspace and call
validate_candidate(); browser clients never perform that acquisition.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "state" / "libraries.json"
DEFAULT_SNAPSHOT = ROOT / "state" / "libraries.snapshot.json"
DEFAULT_METRICS = ROOT / "state" / "libraries.metrics.json"
MAX_BYTES = 10 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 500
MAX_ARCHIVE_EXPANDED_BYTES = 50 * 1024 * 1024
EXECUTABLE_SUFFIXES = {".bat", ".cmd", ".com", ".exe", ".msi", ".ps1", ".sh"}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def validate_candidate(path: Path, expected_digest: str) -> list[str]:
    """Validate a CI-downloaded artifact without importing or executing it."""

    errors: list[str] = []
    if path.is_symlink() or not path.is_file():
        return [f"{path}: candidate must be a regular non-symlink file"]
    size = path.stat().st_size
    if size > MAX_BYTES:
        return [f"{path}: candidate exceeds {MAX_BYTES} byte limit"]
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != expected_digest:
        errors.append(f"{path}: SHA-256 does not match the canonical source digest")
    try:
        payload.decode("utf-8")
    except UnicodeDecodeError:
        # A ZIP may be binary, but plain manifests must be UTF-8.
        if path.suffix.lower() != ".zip":
            errors.append(f"{path}: text manifest must be UTF-8")
    if path.suffix.lower() == ".zip":
        try:
            with zipfile.ZipFile(path) as archive:
                infos = archive.infolist()
                if len(infos) > MAX_ARCHIVE_ENTRIES:
                    errors.append(f"{path}: archive has too many entries")
                expanded = sum(info.file_size for info in infos)
                if expanded > MAX_ARCHIVE_EXPANDED_BYTES:
                    errors.append(f"{path}: archive expands beyond allowed size")
                for info in infos:
                    item = Path(info.filename)
                    is_symlink = (info.external_attr >> 16) & 0o170000 == 0o120000
                    if item.is_absolute() or ".." in item.parts or is_symlink:
                        errors.append(f"{path}: archive contains unsafe path or symlink")
                        break
                    if item.suffix.lower() in EXECUTABLE_SUFFIXES:
                        errors.append(f"{path}: archive contains an executable installer")
                        break
        except zipfile.BadZipFile:
            errors.append(f"{path}: invalid ZIP archive")
    return errors


def source_metric(source: dict[str, Any], status: str | None = None) -> dict[str, Any]:
    return {
        "status": status or source.get("status"),
        "trust_tier": source.get("trust_tier"),
        "enabled": bool(source.get("enabled")),
        "immutable_ref": source.get("immutable_ref"),
        "source_digest": source.get("source_digest"),
        # Existing agent Discussion data is deliberately not borrowed: bare
        # item slugs collide across libraries. A source may opt into one
        # canonical Discussion; item discussions must use namespaced item ids.
        "discussion_url": source.get("discussion_url"),
        "downloads": None,
        "upvotes": None,
    }


def write_snapshot(catalog: dict[str, Any], snapshot_path: Path, metrics_path: Path, stale: bool) -> None:
    now = datetime.now(timezone.utc).isoformat()
    sources = catalog.get("sources", [])
    items = catalog.get("items", [])
    stale_sources = [source.get("slug") for source in sources] if stale else []
    snapshot = {
        "schema": "aibast-libraries-snapshot/1.0",
        "generated_at": now,
        "sync_mode": "metadata_only_no_remote_acquisition",
        "last_known_good_sources": sources,
        "last_known_good_items": items,
        "stale_sources": stale_sources,
    }
    metrics = {
        "schema": "aibast-library-metrics/1.0",
        "generated_at": now,
        "item_namespace": catalog.get("item_namespace", "library-slug:item-slug"),
        "sources": {
            source["slug"]: source_metric(source, "stale" if stale else None)
            for source in sources
        },
        "items": {
            item["id"]: {
                "library_slug": item["library_slug"],
                "digest": item.get("digest"),
                "discussion_url": None,
                "downloads": None,
                "upvotes": None,
            }
            for item in items
        },
        "notes": "No external source content was fetched, imported, or executed by this snapshot.",
    }
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")


def snapshot(catalog_path: Path, snapshot_path: Path, metrics_path: Path, force_stale: bool = False) -> int:
    try:
        catalog = read_json(catalog_path)
        if catalog.get("schema") != "aibast-libraries/2.0":
            raise ValueError("catalog schema is unsupported")
        write_snapshot(catalog, snapshot_path, metrics_path, stale=force_stale)
        if force_stale:
            print("Preserved catalog snapshot and marked sources stale.", file=sys.stderr)
            return 0
        print("Wrote metadata-only librarian snapshot and metric sidecar.")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        if not snapshot_path.exists():
            print(f"Snapshot failed without a last-known-good catalog: {error}", file=sys.stderr)
            return 1
        previous = read_json(snapshot_path)
        fallback = {
            "schema": "aibast-libraries/2.0",
            "sources": previous.get("last_known_good_sources", []),
            "items": previous.get("last_known_good_items", []),
            "item_namespace": "library-slug:item-slug",
        }
        write_snapshot(fallback, snapshot_path, metrics_path, stale=True)
        print(f"Snapshot source failed; preserved last-known-good catalog and marked it stale: {error}", file=sys.stderr)
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    snapshot_parser = commands.add_parser("snapshot")
    snapshot_parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    snapshot_parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    snapshot_parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    snapshot_parser.add_argument("--force-stale", action="store_true")
    candidate_parser = commands.add_parser("validate-candidate")
    candidate_parser.add_argument("--candidate", type=Path, required=True)
    candidate_parser.add_argument("--digest", required=True)
    args = parser.parse_args()
    if args.command == "validate-candidate":
        errors = validate_candidate(args.candidate, args.digest)
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        print(f"PASS: {args.candidate} passed non-executing CI artifact validation.")
        return 0
    return snapshot(args.catalog, args.snapshot, args.metrics, args.force_stale)


if __name__ == "__main__":
    raise SystemExit(main())
