"""Build the library's static public API: api/public/<id>.json for every source in api/public/sources.json.

The pattern: content we need from a public page is fetched from that page, one named value is read out of it exactly
(never paraphrased), and published here with its provenance (the page, the file, the file's SHA-256, when it was read
and the source's own disclaimer), so anything downstream reads one static URL instead of integrating with the source.

    python scripts/build_public_api.py            # fetch every source, write api/public/*.json + index.json
    python scripts/build_public_api.py --check    # fail if a source no longer yields its value (no writes)

Standard library only. A source that cannot be read leaves its last published file untouched and fails the run.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api" / "public"
SCHEMA = "aibast-public-api/1"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "aibast-agents-library/public-api"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def js_object(source: str, symbol: str) -> dict:
    """The literal object assigned to `const <symbol> = {...};`: comments dropped, keys quoted, then strict JSON."""
    match = re.search(r"(?:const|let|var)\s+" + re.escape(symbol) + r"\s*=\s*(\{.*?\n\})\s*;", source, re.S)
    if not match:
        raise ValueError("%s not found" % symbol)
    body = re.sub(r"//[^\n]*", "", match.group(1))
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    body = re.sub(r"([{,]\s*)([A-Za-z_$][\w$]*)\s*:", r'\1"\2":', body)
    body = re.sub(r",(\s*[}\]])", r"\1", body)
    value = json.loads(body)
    if not isinstance(value, dict) or not value:
        raise ValueError("%s is not a non-empty object" % symbol)
    return value


EXTRACT = {"js-object": lambda text, spec: js_object(text, spec["symbol"])}


def build(source: dict, now: str) -> dict:
    data = fetch(source["file"])
    value = EXTRACT[source["extract"]["kind"]](data.decode("utf-8"), source["extract"])
    return {"schema": SCHEMA, "id": source["id"], "title": source["title"], "data": value,
            "units": source.get("units"), "disclaimer": source["disclaimer"],
            "provenance": {"page": source["page"], "file": source["file"], "file_sha256": hashlib.sha256(data).hexdigest(),
                           "extract": source["extract"], "fetched_at": now}}


def main(argv: list[str]) -> int:
    check = "--check" in argv
    sources = json.loads((API / "sources.json").read_text())["sources"]
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    index, failed = [], []
    for source in sources:
        target = API / (source["id"] + ".json")
        try:
            doc = build(source, now)
        except Exception as exc:  # one broken source never rewrites the others
            failed.append("%s: %s" % (source["id"], exc))
            continue
        previous = json.loads(target.read_text()) if target.exists() else None
        unchanged = previous and previous.get("data") == doc["data"] and \
            previous["provenance"].get("file_sha256") == doc["provenance"]["file_sha256"]
        if unchanged:
            doc["provenance"]["fetched_at"] = previous["provenance"]["fetched_at"]   # no churn when nothing changed
        if not check:
            target.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
        index.append({"id": doc["id"], "title": doc["title"], "path": "api/public/%s.json" % doc["id"],
                      "page": source["page"], "fetched_at": doc["provenance"]["fetched_at"]})
        print("%s %s (%d values)" % ("ok" if unchanged else "updated", source["id"], len(doc["data"])))
    if not check and index:
        (API / "index.json").write_text(json.dumps({"schema": "aibast-public-api-index/1", "sources": index},
                                                    indent=2, sort_keys=True) + "\n")
    for line in failed:
        print("FAILED", line, file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
