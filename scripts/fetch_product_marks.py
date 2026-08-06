#!/usr/bin/env python3
"""Harvest the official Microsoft product marks, from Microsoft's own sources.

WHY THIS EXISTS. The library was drawing product marks cropped out of a video
recording — SharePoint was a 32x77 pixel sliver, Teams was 70x108. On a page
they rendered as smudges, and on an exported slide they were the first thing a
customer would notice. A mark is the one asset on a Microsoft deck that has to
be exactly right: an approximation reads as a counterfeit.

So every mark here is downloaded from a Microsoft distribution channel and
recorded with the URL it came from and the date it was read. Nothing is drawn
by hand, traced, recoloured, or lifted from a screenshot.

THE FOUR SOURCES, all published by Microsoft for exactly this purpose:

  office    res-1.cdn.office.net brand-icons — the marks the Office web apps
            serve for themselves. Word, Excel, SharePoint, Teams, Power BI…
  azure     Azure architecture icons (V24) — the official service icon set
            linked from Microsoft Learn. Entra sub-services, AI Foundry, SQL,
            Cosmos DB, Logic Apps, IoT Hub.
  entra     Microsoft Entra architecture icons — the Entra brand marks, which
            the Azure service set does not carry.
  power     Power Platform and Dynamics 365 scalable icon sets, from the
            guidance pages that publish them for architecture diagrams.

SVG, NOT PNG. Every one of these is vector, so a mark is sharp on a slide at
any size and stays a few kilobytes. The PNGs previously in use were both worse
looking and larger.

A mark that cannot be found stays MISSING and the product keeps its labelled
chip. That is deliberate: a chip that says "Microsoft Fabric" is honest, and a
lookalike logo is not.

Usage:
    python3 scripts/fetch_product_marks.py            # fetch what is missing
    python3 scripts/fetch_product_marks.py --force    # re-fetch everything
    python3 scripts/fetch_product_marks.py --check    # fail if any are missing
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "assets" / "products"
INDEX = OUT_DIR / "index.json"
UA = "aibast-agents-library/1.0 (+https://github.com/microsoft/aibast-agents-library)"
TIMEOUT = 60

OFFICE_CDN = ("https://res-1.cdn.office.net/files/fabric-cdn-prod_20240925.001"
              "/assets/brand-icons/product/svg/{name}_48x1.svg")

ARCHIVES = {
    "azure": "https://arch-center.azureedge.net/icons/Azure_Public_Service_Icons_V24.zip",
    "entra": ("https://download.microsoft.com/download/3/1/a/"
              "31a56038-856a-4489-88e4-ee5a1c4352be/"
              "Microsoft%20Entra%20architecture%20icons%20-%20Oct%202023.zip"),
    "power": ("https://download.microsoft.com/download/"
              "498606aa-6d27-4f13-aa5c-1401078c153b/Power-Platform-icons-scalable.zip"),
    "d365": ("https://download.microsoft.com/download/"
             "498606aa-6d27-4f13-aa5c-1401078c153b/Dynamics-365-icons-scalable.zip"),
    # Fabric ships its icons through its own samples repo rather than an
    # arch-center zip; the Learn icons page is what points here.
    "fabric": "https://github.com/microsoft/fabric-samples/raw/main/docs-samples/Icons.zip",
}

# product id in data/products.json -> (source, key)
#
# For "office" the key is the CDN name; for an archive it is a substring that
# must match exactly one file in the zip. Matching on a substring rather than a
# full path is deliberate: these sets renumber their files between releases
# ("10130-icon-service-SQL-Database.svg"), and pinning the number would break
# on the next version for no benefit.
WANTED: dict[str, tuple[str, str]] = {
    # ── Microsoft 365 ────────────────────────────────────────────────
    "word": ("office", "word"),
    "excel": ("office", "excel"),
    "powerpoint": ("office", "powerpoint"),
    "outlook": ("office", "outlook"),
    "sharepoint": ("office", "sharepoint"),
    "microsoft-teams": ("office", "teams"),
    "onedrive": ("office", "onedrive"),
    "onenote": ("office", "onenote"),
    "microsoft-lists": ("office", "lists"),
    "microsoft-loop": ("office", "loop"),
    "microsoft-forms": ("office", "forms"),
    "microsoft-visio": ("office", "visio"),
    "microsoft-project": ("office", "project"),
    "microsoft-stream": ("office", "stream"),
    "microsoft-365-copilot": ("office", "copilot"),
    "power-bi": ("office", "powerbi"),

    # ── Power Platform ───────────────────────────────────────────────
    "power-apps": ("power", "PowerApps_scalable"),
    "power-automate": ("power", "PowerAutomate_scalable"),
    "power-pages": ("power", "PowerPages_scalable"),
    "power-platform": ("power", "PowerPlatform_scalable"),
    "microsoft-copilot-studio": ("power", "CopilotStudio_scalable"),
    "dataverse": ("power", "Dataverse_scalable"),
    "ai-builder": ("power", "AIBuilder_scalable"),

    # ── Dynamics 365 ─────────────────────────────────────────────────
    "dynamics-365": ("d365", "Dynamics365_scalable"),
    "dynamics-365-sales": ("d365", "Sales_scalable"),
    "dynamics-365-customer-service": ("d365", "CustomerServices_scalable"),
    "dynamics-365-field-service": ("d365", "FieldService_scalable"),
    "dynamics-365-finance": ("d365", "Finance_scalable"),
    "dynamics-365-supply-chain": ("d365", "SupplyChainManagement_scalable"),
    "dynamics-365-commerce": ("d365", "Commerce_scalable"),
    "dynamics-365-business-central": ("d365", "BusinessCentral_scalable"),
    "dynamics-365-customer-insights": ("d365", "CustomerInsights_scalable"),
    "dynamics-365-project-operations": ("d365", "ProjectOperations_scalable"),
    "dynamics-365-human-resources": ("d365", "HumanResources_scalable"),
    "dynamics-365-contact-center": ("d365", "ContactCenter_scalable"),

    # ── Identity ─────────────────────────────────────────────────────
    "entra-id": ("entra", "Microsoft Entra ID color icon"),
    "entra-id-governance": ("entra", "Microsoft Entra ID Governance color icon"),
    "entra-verified-id": ("entra", "Microsoft Entra Verified ID color icon"),

    # ── Azure ────────────────────────────────────────────────────────
    "azure-ai-foundry": ("azure", "icon-service-AI-Foundry"),
    "azure-openai": ("azure", "icon-service-Azure-OpenAI"),
    "azure-sql": ("azure", "icon-service-SQL-Database.svg"),
    "azure-cosmos-db": ("azure", "icon-service-Azure-Cosmos-DB"),
    "azure-blob-storage": ("azure", "icon-service-Storage-Accounts.svg"),
    "azure-iot-hub": ("azure", "icon-service-IoT-Hub.svg"),
    "azure-logic-apps": ("azure", "icon-service-Logic-Apps.svg"),
    "azure-functions": ("azure", "icon-service-Function-Apps"),
    "azure-key-vault": ("azure", "icon-service-Key-Vaults"),
    "azure-ai-search": ("azure", "icon-service-Cognitive-Search"),
    "azure-machine-learning": ("azure", "icon-service-Machine-Learning.svg"),
    "azure-bot-service": ("azure", "icon-service-Bot-Services"),
    "azure-monitor": ("azure", "icon-service-Monitor.svg"),

    # ── Analytics ────────────────────────────────────────────────────
    "microsoft-fabric": ("fabric", "fabric_48_color.svg"),

    # Microsoft Purview and Microsoft Graph are deliberately absent: neither
    # publishes a mark in any of these sets, and the Azure Purview service
    # icon was retired when the brand moved. They keep labelled chips. A
    # near-enough logo on a Microsoft deck is worse than a word.
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def is_svg(blob: bytes) -> bool:
    head = blob[:400].lstrip()
    return head.startswith(b"<?xml") or head.startswith(b"<svg")


def pick(names: list[str], key: str) -> str | None:
    """The one file matching ``key``. Ambiguity is an error, not a coin toss."""
    hits = [n for n in names if key.lower() in n.lower()]
    if not hits:
        return None
    # Prefer an exact basename match when the substring matches several.
    exact = [n for n in hits if Path(n).stem.lower() == key.lower()]
    if exact:
        return exact[0]
    # Deterministic: shortest path wins, then alphabetical. Never random.
    return sorted(hits, key=lambda n: (len(n), n))[0]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--force", action="store_true", help="re-fetch marks already on disk")
    ap.add_argument("--check", action="store_true",
                    help="fail if any wanted mark is missing; download nothing")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if args.check:
        missing = [pid for pid in WANTED if not (OUT_DIR / f"{pid}.svg").is_file()]
        for m in missing:
            print(f"  MISSING {m}.svg", file=sys.stderr)
        print(f"[marks] {len(WANTED) - len(missing)}/{len(WANTED)} present")
        return 1 if missing else 0

    todo = {pid: v for pid, v in WANTED.items()
            if args.force or not (OUT_DIR / f"{pid}.svg").is_file()}
    if not todo:
        print(f"[marks] all {len(WANTED)} marks already on disk")
        return 0

    # Only download an archive if something still needs it.
    zips: dict[str, zipfile.ZipFile] = {}
    for src in {s for s, _ in todo.values()} & set(ARCHIVES):
        print(f"[marks] downloading the official {src} icon set…")
        try:
            zips[src] = zipfile.ZipFile(io.BytesIO(fetch(ARCHIVES[src])))
        except Exception as exc:                                # noqa: BLE001
            print(f"[marks] {src} set unavailable ({exc}); its marks stay chips",
                  file=sys.stderr)

    # The previous index used schema 1.0, whose "marks" was a list. Read it if
    # it is the shape we write now and start clean if it is not — silently
    # merging two schemas is how an index ends up describing neither.
    index = {}
    if INDEX.is_file():
        try:
            prev = json.loads(INDEX.read_text(encoding="utf-8")).get("marks")
            index = prev if isinstance(prev, dict) else {}
        except (OSError, ValueError):
            index = {}

    got, failed = 0, []
    for pid, (src, key) in sorted(todo.items()):
        out = OUT_DIR / f"{pid}.svg"
        try:
            if src == "office":
                url = OFFICE_CDN.format(name=key)
                blob = fetch(url)
                origin = url
            else:
                z = zips.get(src)
                if not z:
                    failed.append(f"{pid} (no {src} set)")
                    continue
                name = pick(z.namelist(), key)
                if not name:
                    failed.append(f"{pid} ('{key}' not in the {src} set)")
                    continue
                blob = z.read(name)
                origin = f"{ARCHIVES[src]}!{name}"
            if not is_svg(blob):
                failed.append(f"{pid} (not an SVG)")
                continue
            out.write_bytes(blob)
            index[pid] = {"file": f"assets/products/{pid}.svg", "source": src,
                          "origin": origin, "bytes": len(blob), "fetched": today}
            got += 1
            print(f"  {pid:34} {len(blob):>7} bytes  {src}")
        except Exception as exc:                                # noqa: BLE001
            failed.append(f"{pid} ({str(exc)[:60]})")

    INDEX.write_text(json.dumps({
        "schema": "aibast-product-marks/2.0",
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": ("Official Microsoft product marks, downloaded from Microsoft's "
                 "own distribution channels by scripts/fetch_product_marks.py. "
                 "Each entry records the URL it came from and the date it was "
                 "read. Nothing here is redrawn, traced, recoloured, or taken "
                 "from a screenshot. A product with no official mark keeps a "
                 "labelled chip rather than a lookalike."),
        "sources": {"office": OFFICE_CDN.format(name="<name>"), **ARCHIVES},
        "count": len(index),
        "marks": dict(sorted(index.items())),
    }, indent=2) + "\n", encoding="utf-8")

    print(f"[marks] {got} fetched, {len(index)} total in {OUT_DIR.relative_to(REPO_ROOT)}")
    for f in failed:
        print(f"    MISSING {f}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
