#!/usr/bin/env python3
"""The Microsoft products a library entry involves — derived, never assumed.

Every page that draws a product (the reference architecture, the one-pager,
their filters) reads this one file, so a product cannot be named one way on one
surface and another way on the next.

Three rules hold the file honest:

  DECLARED beats IMPLIED beats NOTHING. A product is `declared` only when the
  entry names it — in a systems field (featured_tools / requires / built_with),
  in a configuration variable, or by its full product name in the entry's own
  description or source. It is `implied` only when a tag or category the entry
  itself carries points at it, and the tag that did the pointing is recorded as
  evidence. Everything else stays unknown: an entry with no product signal
  reports no products rather than being decorated with plausible ones.

  A MARK IS A MARK. The real product marks in media/jewels were cropped from
  the corpus. A product with no mark on file gets a labelled chip and is listed
  in `missing_marks` — no product mark is ever approximated, redrawn, or stood
  in for by a lookalike, because a wrong logo is a trademark problem long
  before it is a design problem.

  APP LEVEL WHERE DERIVABLE. "Dynamics 365 CcaaS" names the contact-centre app,
  so it resolves to Dynamics 365 Customer Service. "Dynamics 365 CRM" names a
  family and not an app, so it resolves to Dynamics 365 with `app: null` — the
  filter can still find it under the family, and nobody is told which app.

Output: data/products.json  (aibast-products/1.0)

Usage:
    python3 scripts/build_products.py
    python3 scripts/build_products.py --only care-gap-closure
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_FILE = REPO_ROOT / "data" / "products.json"
JEWELS = REPO_ROOT / "media" / "jewels" / "index.json"

SCHEMA = "aibast-products/1.0"
FORMAT_VERSION = "1.0.0"

# Which real marks exist, and which product each one is genuinely the mark FOR.
# `family` means the mark is the family's mark used beside an app's name — the
# Dynamics 365 mark next to "Dynamics 365 Field Service" is the real Dynamics
# mark, correctly labelled, not an invented Field Service icon.
def _load_marks() -> dict[str, tuple[str, str]]:
    """The marks on disk, as harvested from Microsoft's own icon sets.

    This used to be a hand-written table, and it was wrong in a way nobody
    caught: half its entries pointed at media/jewels PNGs that were crops from
    a VIDEO FRAME — SharePoint was 32x77 pixels. They passed every check
    because a check can see that a file exists, not that a logo is a smudge.

    Reading scripts/fetch_product_marks.py's index instead means the table
    cannot disagree with the files, and a mark added by a fetch is available
    immediately without a second edit here. Provenance for every entry (source
    URL, date read) lives in assets/products/index.json.
    """
    idx = REPO_ROOT / "assets" / "products" / "index.json"
    out: dict[str, tuple[str, str]] = {}
    try:
        doc = json.loads(idx.read_text(encoding="utf-8"))
        for pid, rec in (doc.get("marks") or {}).items():
            f = rec.get("file")
            if f and (REPO_ROOT / f).is_file():
                out[pid] = (f, "exact")
    except (OSError, ValueError):
        pass
    return out


# Family fall-backs: an app that has no mark of its own borrows its family's,
# correctly labelled. `family` never means an invented app icon — where the
# official set ships a real app mark (Dynamics 365 Sales, Field Service, and
# the rest do), _load_marks picks it up as `exact` and this never applies.
FAMILY_MARKS = {
    "dynamics-365-sales": "dynamics-365",
    "dynamics-365-customer-service": "dynamics-365",
    "dynamics-365-field-service": "dynamics-365",
    "dynamics-365-finance": "dynamics-365",
    "dynamics-365-supply-chain": "dynamics-365",
    "dynamics-365-commerce": "dynamics-365",
    "azure-sql": "azure-sql",
}

MARKS = _load_marks()
for _app, _fam in FAMILY_MARKS.items():
    if _app not in MARKS and _fam in MARKS:
        MARKS[_app] = (MARKS[_fam][0], "family")

# id, name, family, app, column, declares, prose names, implying tags,
# implying categories.
#
# `declares` are matched against systems fields and configuration variables —
# short forms are allowed there because the field's whole purpose is to name a
# system. `names` are matched against free prose (a description, source code),
# where only the full product name counts: "sales" in a sentence is not a
# declaration of Dynamics 365 Sales.
_P = [
    dict(id="dynamics-365", name="Dynamics 365", family="Dynamics 365", app=None,
         column="knowledge",
         declares=["dynamics 365", "dynamics365", "d365", "dynamics"],
         names=[r"dynamics\s?365", r"\bd365\b"],
         tags=["crm", "erp"], categories=[]),
    dict(id="dynamics-365-sales", name="Dynamics 365 Sales", family="Dynamics 365",
         app="Sales", column="knowledge",
         declares=["dynamics 365 sales", "d365 sales"],
         names=[r"dynamics\s?365 sales"],
         tags=["pipeline", "deal-progression", "opportunity", "lead-scoring",
               "account-intelligence", "quoting", "win-loss", "territory"],
         categories=["b2b_sales", "b2c_sales"]),
    dict(id="dynamics-365-customer-service", name="Dynamics 365 Customer Service",
         family="Dynamics 365", app="Customer Service", column="knowledge",
         declares=["dynamics 365 customer service", "d365 customer service",
                   "dynamics 365 ccaas", "ccaas", "contact center", "contact centre"],
         names=[r"dynamics\s?365 customer service", r"contact cent(er|re)"],
         tags=["customer-service", "case-management", "ticketing", "support",
               "routing", "escalation", "knowledge-base"],
         categories=[]),
    dict(id="dynamics-365-field-service", name="Dynamics 365 Field Service",
         family="Dynamics 365", app="Field Service", column="knowledge",
         declares=["dynamics 365 field service", "field service"],
         names=[r"field service"],
         tags=["field-service", "work-order", "dispatch", "technician",
               "maintenance", "asset-management"],
         categories=[]),
    dict(id="dynamics-365-finance", name="Dynamics 365 Finance",
         family="Dynamics 365", app="Finance", column="knowledge",
         declares=["dynamics 365 finance", "d365 finance", "finance and operations",
                   "finance & operations"],
         names=[r"dynamics\s?365 finance", r"finance (and|&) operations"],
         tags=["finance", "invoicing", "billing", "budget", "revenue",
               "accounts-payable", "accounts-receivable", "collections"],
         categories=[]),
    dict(id="dynamics-365-supply-chain", name="Dynamics 365 Supply Chain Management",
         family="Dynamics 365", app="Supply Chain Management", column="knowledge",
         declares=["dynamics 365 supply chain", "supply chain management",
                   "d365 supply chain"],
         names=[r"dynamics\s?365 supply chain", r"supply chain management"],
         tags=["supply-chain", "inventory", "procurement", "logistics",
               "warehouse", "demand-planning", "supplier", "sourcing"],
         categories=[]),
    dict(id="dynamics-365-commerce", name="Dynamics 365 Commerce",
         family="Dynamics 365", app="Commerce", column="knowledge",
         declares=["dynamics 365 commerce", "d365 commerce"],
         names=[r"dynamics\s?365 commerce"],
         tags=["commerce", "point-of-sale", "merchandising", "cart-abandonment",
               "storefront"],
         categories=[]),

    dict(id="microsoft-teams", name="Microsoft Teams", family="Microsoft 365",
         app=None, column="interface",
         declares=["microsoft teams", "ms teams", "teams"],
         names=[r"microsoft teams", r"\bms teams\b"],
         tags=["teams", "collaboration", "chat", "meetings"], categories=[]),
    dict(id="outlook", name="Outlook", family="Microsoft 365", app=None,
         column="interface",
         declares=["outlook", "exchange"],
         names=[r"\boutlook\b", r"microsoft exchange"],
         tags=["email", "outreach", "inbox"], categories=[]),
    dict(id="sharepoint", name="SharePoint", family="Microsoft 365", app=None,
         column="knowledge",
         declares=["sharepoint", "onedrive"],
         names=[r"sharepoint", r"onedrive"],
         tags=["documents", "document-management", "records", "policy",
               "knowledge-management", "content", "drafting"], categories=[]),
    dict(id="microsoft-365-copilot", name="Microsoft 365 Copilot",
         family="Microsoft 365", app=None, column="interface",
         declares=["microsoft 365 copilot", "m365 copilot", "microsoft 365"],
         names=[r"microsoft 365 copilot", r"m365 copilot"],
         tags=[], categories=[]),
    dict(id="word", name="Microsoft Word", family="Microsoft 365", app=None,
         column="interface", declares=["word"], names=[r"microsoft word"],
         tags=[], categories=[]),
    dict(id="excel", name="Microsoft Excel", family="Microsoft 365", app=None,
         column="interface", declares=["excel"], names=[r"microsoft excel"],
         tags=[], categories=[]),
    dict(id="powerpoint", name="Microsoft PowerPoint", family="Microsoft 365",
         app=None, column="interface", declares=["powerpoint"],
         names=[r"microsoft powerpoint"], tags=[], categories=[]),
    dict(id="microsoft-graph", name="Microsoft Graph", family="Microsoft 365",
         app=None, column="knowledge", declares=["microsoft graph", "graph api"],
         names=[r"microsoft graph"], tags=[], categories=[]),

    dict(id="power-bi", name="Power BI", family="Power Platform", app=None,
         column="reporting", declares=["power bi", "powerbi"],
         names=[r"power\s?bi"],
         tags=["reporting", "analytics", "dashboard", "dashboards", "kpi",
               "scorecard", "benchmarking", "forecasting"], categories=[]),
    dict(id="power-automate", name="Power Automate", family="Power Platform",
         app=None, column="automation", declares=["power automate", "flow"],
         names=[r"power automate"],
         tags=["automation", "workflow", "approval", "approvals", "alerts",
               "notifications", "orchestration", "campaign"], categories=[]),
    dict(id="power-apps", name="Power Apps", family="Power Platform", app=None,
         column="interface", declares=["power apps", "powerapps"],
         names=[r"power apps"], tags=[], categories=[]),
    dict(id="microsoft-copilot-studio", name="Microsoft Copilot Studio",
         family="Power Platform", app=None, column="interface",
         declares=["copilot studio"], names=[r"copilot studio"],
         tags=[], categories=[]),
    dict(id="dataverse", name="Dataverse", family="Power Platform", app=None,
         column="knowledge", declares=["dataverse", "common data service"],
         names=[r"dataverse"], tags=[], categories=[]),

    dict(id="azure-openai", name="Azure OpenAI", family="Azure", app=None,
         column="processing",
         declares=["azure openai", "azure_openai", "openai"],
         names=[r"azure openai"],
         tags=["azure-openai", "gpt-image"], categories=[]),
    dict(id="azure-functions", name="Azure Functions", family="Azure", app=None,
         column="automation", declares=["azure functions", "function app"],
         names=[r"azure functions?"], tags=[], categories=[]),
    dict(id="azure-ai-search", name="Azure AI Search", family="Azure", app=None,
         column="knowledge", declares=["azure ai search", "cognitive search"],
         names=[r"azure ai search"], tags=[], categories=[]),
    dict(id="azure-sql", name="Azure SQL", family="Azure", app=None,
         column="knowledge", declares=["azure sql", "sql database", "sql"],
         names=[r"azure sql"], tags=[], categories=[]),
    dict(id="azure-cosmos-db", name="Azure Cosmos DB", family="Azure", app=None,
         column="knowledge", declares=["cosmos"], names=[r"cosmos db"],
         tags=[], categories=[]),
    dict(id="azure-blob-storage", name="Azure Blob Storage", family="Azure",
         app=None, column="knowledge", declares=["blob storage", "blob"],
         names=[r"blob storage"], tags=[], categories=[]),
    dict(id="azure-iot-hub", name="Azure IoT Hub", family="Azure", app=None,
         column="knowledge", declares=["azure iot hub", "iot hub", "iot"],
         names=[r"azure iot hub"], tags=["telemetry", "sensors"], categories=[]),
    dict(id="azure-logic-apps", name="Azure Logic Apps", family="Azure", app=None,
         column="automation", declares=["logic apps"], names=[r"logic apps"],
         tags=[], categories=[]),
    dict(id="microsoft-fabric", name="Microsoft Fabric", family="Azure", app=None,
         column="knowledge", declares=["fabric"], names=[r"microsoft fabric"],
         tags=[], categories=[]),
    dict(id="microsoft-purview", name="Microsoft Purview", family="Azure",
         app=None, column="reporting", declares=["purview"], names=[r"purview"],
         tags=["compliance", "audit", "governance"], categories=[]),
]

BY_ID = {p["id"]: p for p in _P}

# Longest declaration first: "dynamics 365 customer service" must win over
# "dynamics 365", or every app collapses into the family.
_DECLARE_INDEX = sorted(
    ((term, p["id"]) for p in _P for term in p["declares"]),
    key=lambda t: -len(t[0]))

CONFIDENCE_ORDER = {"declared": 2, "implied": 1}


def catalog() -> list[dict]:
    """The product catalog, with each product's mark resolved."""
    out = []
    for p in _P:
        mark, scope = MARKS.get(p["id"], (None, None))
        out.append({
            "id": p["id"], "name": p["name"], "family": p["family"],
            "app": p["app"], "column": p["column"],
            "mark": mark,
            "mark_scope": scope,
            "mark_status": "mark" if mark else "labelled-chip",
        })
    return out


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def _match_declaration(value: str) -> str | None:
    low = " " + _norm(value) + " "
    for term, pid in _DECLARE_INDEX:
        if " " + _norm(term) + " " in low:
            return pid
    return None


def _add(found: dict, pid: str, confidence: str, evidence: str,
         value: str | None = None) -> None:
    """Record a product, keeping the strongest evidence and ALL of the values.

    Keeping every matched value matters downstream: an entry that names both
    "Dynamics 365 ERP" and "Dynamics 365 for CRM" resolves to one product, and
    if only the winning evidence were kept the other string would look like a
    system nobody could classify.
    """
    prev = found.get(pid)
    if prev is None:
        found[pid] = {"id": pid, "confidence": confidence, "evidence": evidence,
                      "matched": [value] if value else []}
        return
    if value and value not in prev["matched"]:
        prev["matched"].append(value)
    if CONFIDENCE_ORDER[confidence] > CONFIDENCE_ORDER[prev["confidence"]]:
        prev["confidence"], prev["evidence"] = confidence, evidence


SYSTEM_FIELDS = ("featured_tools", "requires", "built_with")


def detect(entry: dict, source_text: str = "") -> list[dict]:
    """Products this entry involves, each with the evidence that put it there.

    Returns assignments sorted declared-first. An entry that declares nothing
    and implies nothing returns [] — the surfaces render that as "no Microsoft
    product named", which is the truth and is also, usefully, visible.
    """
    found: dict[str, dict] = {}

    # 1. Systems fields. These exist to name systems, so a short form counts.
    for field in SYSTEM_FIELDS:
        for value in entry.get(field) or []:
            pid = _match_declaration(value)
            if pid:
                _add(found, pid, "declared", f'{field}: "{value}"', value)

    # 2. Configuration variables. AZURE_OPENAI_ENDPOINT is a declaration that
    #    the agent talks to Azure OpenAI; nothing else is inferred from it.
    for var in entry.get("requires_env") or []:
        pid = _match_declaration(var.replace("_", " "))
        if pid:
            _add(found, pid, "declared", f"requires_env: {var}", var)

    # 3. Full product names in the entry's own prose or source. Only the full
    #    name counts here — prose is where a short form goes wrong.
    prose = " ".join(filter(None, [
        entry.get("description"), entry.get("lede"), entry.get("summary"),
        source_text]))
    if prose:
        low = prose.lower()
        for p in _P:
            for pattern in p["names"]:
                if re.search(pattern, low):
                    where = "source" if source_text and re.search(
                        pattern, source_text.lower()) else "description"
                    _add(found, p["id"], "declared", f"{where} names {p['name']}")
                    break

    # 4. Implication, from a tag or category the entry itself carries. The tag
    #    is named in the evidence so a reader can disagree with the inference.
    tags = {_norm(t).replace(" ", "-") for t in entry.get("tags") or []}
    category = _norm(entry.get("category") or "").replace(" ", "_")
    for p in _P:
        hit = tags & set(p["tags"])
        if hit:
            _add(found, p["id"], "implied", f"tag: {sorted(hit)[0]}")
        elif category and category in p["categories"]:
            _add(found, p["id"], "implied", f"category: {category}")

    # An app makes its family redundant: "Dynamics 365 Sales" already says
    # Dynamics 365, and listing both twice draws the same logo twice.
    apps = {BY_ID[i]["family"] for i in found if BY_ID[i]["app"]}
    for pid in list(found):
        p = BY_ID[pid]
        if p["app"] is None and p["family"] in apps and p["family"] == p["name"]:
            if found[pid]["confidence"] == "implied":
                found.pop(pid)

    return sorted(found.values(),
                  key=lambda a: (-CONFIDENCE_ORDER[a["confidence"]],
                                 BY_ID[a["id"]]["name"]))


def resolve(assignment: dict) -> dict:
    """An assignment plus everything a page needs to draw it."""
    p = BY_ID[assignment["id"]]
    mark, scope = MARKS.get(p["id"], (None, None))
    return {
        "id": p["id"], "name": p["name"], "family": p["family"], "app": p["app"],
        "column": p["column"], "mark": mark, "mark_scope": scope,
        "mark_status": "mark" if mark else "labelled-chip",
        "confidence": assignment["confidence"], "evidence": assignment["evidence"],
        "matched": assignment.get("matched") or [],
    }


# --------------------------------------------------------------------------
# Entry loading — the same joins the rest of the library uses.
# --------------------------------------------------------------------------
def _key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


def source_text_for(entry: dict) -> str:
    path = entry.get("file")
    if not path:
        return ""
    f = REPO_ROOT / path
    if not f.is_file():
        return ""
    try:
        return f.read_text(encoding="utf-8")
    except Exception:
        return ""


def entries() -> list[dict]:
    """Every library entry, with its one-pager joined in where there is one."""
    onepagers, out = {}, []
    op = REPO_ROOT / "data" / "onepagers.json"
    if op.is_file():
        for s in json.loads(op.read_text(encoding="utf-8"))["onepagers"]:
            onepagers[_key(s.get("display_name"))] = s
            out.append({
                **s, "kind": "solution", "ref": s["slug"],
                "industries": s.get("industries") or [s.get("industry")],
                "category": re.sub(r"[^a-z0-9]+", "_",
                                   (s.get("industry") or "general").lower()),
            })

    reg = REPO_ROOT / "api" / "v1" / "agents.json"
    if reg.is_file():
        for a in json.loads(reg.read_text(encoding="utf-8")).get("agents", []):
            sol = onepagers.get(_key(a.get("display_name")), {})
            out.append({
                "slug": a["name"].split("/")[-1], "kind": "agent", "ref": a["name"],
                "display_name": a.get("display_name"),
                "description": a.get("description"),
                "lede": sol.get("lede"),
                "tags": a.get("tags") or [],
                "category": a.get("category") or "general",
                "requires_env": a.get("requires_env") or [],
                "file": a.get("file"),
                "featured_tools": sol.get("featured_tools") or [],
                "requires": sol.get("requires") or [],
                "built_with": sol.get("built_with") or [],
                "personas": sol.get("personas") or sol.get("audience") or [],
                "business_value": sol.get("business_value") or [],
                "industries": [(a.get("category") or "general")
                               .replace("_", " ").title()],
                "joined_onepager": sol.get("slug"),
            })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only")
    args = ap.parse_args()

    items = entries()
    if args.only:
        items = [e for e in items if args.only in e["slug"]]
    if not items:
        print(f"[products] nothing matched {args.only!r}", file=sys.stderr)
        return 1

    assignments, counts, declared_counts = [], {}, {}
    for e in items:
        found = detect(e, source_text_for(e))
        for a in found:
            counts[a["id"]] = counts.get(a["id"], 0) + 1
            if a["confidence"] == "declared":
                declared_counts[a["id"]] = declared_counts.get(a["id"], 0) + 1
        assignments.append({
            "ref": e["ref"], "slug": e["slug"], "kind": e["kind"],
            "display_name": e.get("display_name") or e["slug"],
            "industries": [i for i in (e.get("industries") or []) if i],
            "products": found,
        })

    cat = catalog()
    for p in cat:
        p["entry_count"] = counts.get(p["id"], 0)
        p["declared_count"] = declared_counts.get(p["id"], 0)

    families = []
    for p in cat:
        if p["family"] not in families:
            families.append(p["family"])

    missing = sorted(p["id"] for p in cat if p["mark_status"] == "labelled-chip")
    jewel_note = ""
    if JEWELS.is_file():
        jewel_note = json.loads(JEWELS.read_text(encoding="utf-8")).get("note", "")

    doc = {
        "schema": SCHEMA,
        "format_version": FORMAT_VERSION,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": ("The Microsoft products each library entry involves. `declared` "
                 "means the entry names the product; `implied` means a tag or "
                 "category the entry carries points at it, and the tag is in the "
                 "evidence. An entry with neither lists no products — an unknown "
                 "is reported as unknown rather than filled in."),
        "marks": {
            "source": "media/jewels/index.json",
            "note": ("Real marks only. A product with no mark on file is drawn "
                     "as a labelled chip and listed in missing_marks; no mark is "
                     "ever approximated or substituted with a lookalike."),
            "provenance": jewel_note,
        },
        "families": families,
        "products": cat,
        "missing_marks": missing,
        "count": len(assignments),
        "entries": assignments,
    }
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    # Published alongside the rest of the static API, so a page served from
    # /api/v1/ finds it there and no reader has to know about data/.
    api = REPO_ROOT / "api" / "v1" / "products.json"
    if api.parent.is_dir():
        api.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    named = sum(1 for a in assignments if a["products"])
    decl = sum(1 for a in assignments
               if any(p["confidence"] == "declared" for p in a["products"]))
    print(f"[products] {len(cat)} products · {len(assignments)} entries · "
          f"{named} involve at least one ({decl} declared outright)")
    print(f"[products] real marks: {len(cat) - len(missing)} · "
          f"labelled chips (no mark on file): {len(missing)}")
    print(f"[products] wrote {OUT_FILE.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
