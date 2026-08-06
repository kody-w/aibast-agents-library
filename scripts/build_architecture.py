#!/usr/bin/env python3
"""Generate a reference architecture for every entry in the library.

The AIBAST architecture slide is as much a format as the demo recording is:
four columns — Knowledge, Processing, User Interface, Reporting — over a Tools
band and a Supporting Features band, with a numbered request flow running
through them. Every solution gets one drawn by hand today.

It does not have to be drawn by hand. The four columns are exactly the four
things a manifest already declares: what it reads, what it does, where the
operator meets it, and what it leaves behind. So the architecture is derived,
the same way the one-pager and the walkthrough are.

WHY THIS WAS REWRITTEN. The first version derived a real architecture for the
48 catalog solutions and then, for the 112 registry agents, fed itself a
constant — every agent was handed `built_with: ["Microsoft Copilot Studio"]`
and nothing else. Measured: 112 agents, ONE distinct set of columns. The
diagrams were identical apart from the title, which is worse than having none,
because a picture that says nothing still looks like it decided something.

The fix is not more decoration. It is reading the four things each agent
actually declares and that genuinely differ between agents:

  * its TOOL SCHEMA — the operation enum and parameters in the agent's own
    `self.metadata`, parsed from source. 94 of 112 agents declare an operation
    enum and 95 distinct enums exist across them. This is the strongest signal
    in the repository and it was going unread.
  * its DESCRIPTION, split into the clauses it is already written as.
  * its TAGS, which are the subject areas it says it works on.
  * its PRODUCTS, resolved through scripts/build_products.py so that the
    architecture, the one-pager and the product filters cannot disagree.

Deterministic. No model, no network. Nothing is invented to fill a column:
where a surface is not declared the column says so, and a system whose name
matches no known platform lands in Knowledge under its own name and is listed
as unclassified — a confidently wrong box is worse than an honest one.

Output: data/architectures.json  (aibast-architecture/1.0)

Usage:
    python3 scripts/build_architecture.py
    python3 scripts/build_architecture.py --only contract-review-agent
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_products import MARKS  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_products import (  # noqa: E402
    BY_ID, detect, entries as product_entries, resolve, source_text_for)

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_FILE = REPO_ROOT / "data" / "architectures.json"

SCHEMA = "aibast-architecture/1.0"
FORMAT_VERSION = "1.0.0"

# The glyph class each product draws with when it has no real mark on file.
# It is a colour and a label, never a redrawn logo.
GLYPH = {
    "Dynamics 365": "d365", "Microsoft 365": "m365", "Power Platform": "power",
    "Azure": "azure",
}

# The request flow, in the order the reference slide numbers it. Steps 1 and 5
# name the entry's own surface and system of record when it declares them.
FLOW = [
    "Natural language input",
    "Preliminary checks including responsible AI checks and security measures",
    ("Formulates a plan comprised of multiple actions including context and "
     "tool selection, function matching and parameter determination, tool "
     "initiation, then result analysis and response formulation."),
    "NL response after guideline checks",
    "Action taken in the system of record",
    "Feedback",
]

# Internal shop language, never on a page someone outside reads. The narrow
# form matters: "pipeline snapshot" and "renewal pipeline" are sales terms an
# agent legitimately declares, and only the bare internal sense is dropped.
INTERNAL = re.compile(r"\brapp\b|\bbrainstem\b|^run pipeline$|^pipeline$", re.I)


# --------------------------------------------------------------------------
# The agent's own tool schema, read from source.
# --------------------------------------------------------------------------
def tool_schema(source: str) -> dict:
    """The operation enum and parameter names an agent declares to the model.

    Parsed rather than executed, and read off `self.metadata` because that is
    the dict the agent hands the model — the one place an agent says, in its
    own words, what it can be asked to do.
    """
    out = {"operations": [], "parameters": [], "operation_hint": ""}
    if not source:
        return out
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return out

    node = None
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Dict):
            if any(isinstance(t, ast.Attribute) and t.attr == "metadata"
                   for t in n.targets):
                node = n.value
                break
    if node is None:
        return out

    def properties(d: ast.Dict):
        for k, v in zip(d.keys, d.values):
            if isinstance(k, ast.Constant) and k.value == "properties" \
                    and isinstance(v, ast.Dict):
                return v
            if isinstance(v, ast.Dict):
                found = properties(v)
                if found is not None:
                    return found
        return None

    props = properties(node)
    if props is None:
        return out
    for k, v in zip(props.keys, props.values):
        if not isinstance(k, ast.Constant) or not isinstance(v, ast.Dict):
            continue
        out["parameters"].append(k.value)
        for ik, iv in zip(v.keys, v.values):
            if not isinstance(ik, ast.Constant):
                continue
            if ik.value == "enum" and isinstance(iv, (ast.List, ast.Tuple)):
                out["operations"] += [e.value for e in iv.elts
                                      if isinstance(e, ast.Constant)
                                      and isinstance(e.value, str)]
            if ik.value == "description" and isinstance(iv, ast.Constant) \
                    and not out["operation_hint"] and k.value in ("operation", "action"):
                out["operation_hint"] = iv.value
    return out


# Acronyms a reader expects to see shouted. Anything else that should be
# uppercase is learned from the entry's own prose rather than listed here —
# "HEDIS dashboard" reads right because the entry writes HEDIS that way.
ACRONYMS = {"B2B", "B2C", "CRM", "ERP", "ROI", "KPI", "SLA", "API", "HR", "IT",
            "AI", "PDF", "SKU", "POS", "QA", "RFP", "RFQ", "CSAT", "NPS", "ARR",
            "MRR", "EBITDA", "GDPR", "PII", "SOC", "ESG", "IoT", "ML"}


def acronyms_in(text: str) -> set[str]:
    """Words the entry itself writes in capitals — HEDIS, CMS, FAR, ITAR."""
    return {w for w in re.findall(r"\b[A-Z][A-Z0-9]{1,7}\b", text or "")}


# Words that are an acronym somewhere and an ordinary English word here. In
# prose they stay lowercase: "every clause it could not source" is not a
# sentence about information technology.
STOP = {"it", "is", "as", "at", "in", "on", "or", "no", "so", "an", "am", "be",
        "by", "do", "go", "he", "if", "me", "my", "of", "to", "up", "us", "we",
        "a", "i", "the", "and"}


def shout_text(text: str, shout: set[str] | None = None) -> str:
    """Restore capitals an upstream field lost: "Campaign roi" -> "Campaign ROI"."""
    upper = {s.upper(): s for s in (shout or set()) | ACRONYMS}

    def one(m):
        w = m.group(0)
        if w.lower() in STOP:
            return w
        return upper.get(w.upper(), w)

    return re.sub(r"\b[A-Za-z][A-Za-z0-9]{1,7}\b", one, text or "")


def humanise(key: str, shout: set[str] | None = None) -> str:
    words = [w for w in re.split(r"[_\-\s]+", key.strip()) if w]
    if not words:
        return ""
    shout = (shout or set()) | ACRONYMS
    upper = {s.upper(): s for s in shout}
    out = []
    for i, w in enumerate(words):
        if w.upper() in upper:
            out.append(upper[w.upper()])
        elif i == 0:
            out.append(w[0].upper() + w[1:])
        else:
            out.append(w)
    return " ".join(out)


# --------------------------------------------------------------------------
# What the entry says it does, in the clauses it already wrote.
# --------------------------------------------------------------------------
def clauses(text: str, limit: int = 4, shout: set[str] | None = None) -> list[str]:
    """Split a description into the actions it is already a list of.

    "Analyzes HEDIS quality measure gaps, prioritizes patient outreach, manages
    campaigns, and provides HEDIS compliance dashboards" is four actions
    written as one sentence. Splitting it is reading, not inventing.
    """
    t = (text or "").strip().rstrip(".")
    if not t:
        return []
    parts = re.split(r",\s*(?:and\s+)?|\s+and\s+then\s+", t)
    out = []
    for p in parts:
        p = p.strip().rstrip(".")
        if len(p) < 8:
            continue
        p = shout_text(p[0].upper() + p[1:], shout)
        if p not in out:
            out.append(p)
        if len(out) == limit:
            break
    return out



# ── Marks for the structural boxes ───────────────────────────────────────
#
# The four columns carry named Microsoft things that are not catalog products:
# the identity layer, the connector layer, the admin surface. They were built
# with mark=None and drew a dashed blank, which on an exported slide reads as
# broken rather than as careful — and in Entra ID's case the real mark was
# already on disk, unused.
#
# So every structural box resolves to the nearest REAL mark and records how
# near it is. Nothing is drawn that Microsoft does not publish; a `closest`
# scope means "this is a true mark from one level up", and every surface says
# so on hover.
def _load_authored() -> dict:
    f = REPO_ROOT / "data" / "solution_actions.json"
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("solutions", {})
    except (OSError, ValueError):
        return {}


AUTHORED_ACTIONS = _load_authored()

STRUCTURAL = {
    "entra id": ("entra-id", "exact"),
    "power platform connectors and actions": ("power-platform", "family"),
    "copilot control system": ("microsoft-365-copilot", "closest"),
    "microsoft 365": ("microsoft-365", "exact"),
}

# Keyword -> mark id, for a label nobody enumerated. Longest key wins, so
# "power bi" beats "power".
STRUCTURAL_HINTS = [
    ("copilot studio", "microsoft-copilot-studio"), ("power automate", "power-automate"),
    ("power platform", "power-platform"), ("power apps", "power-apps"),
    ("power pages", "power-pages"), ("power bi", "power-bi"),
    ("dataverse", "dataverse"), ("sharepoint", "sharepoint"), ("teams", "microsoft-teams"),
    ("outlook", "outlook"), ("dynamics", "dynamics-365"), ("entra", "entra-id"),
    ("azure", "azure"), ("copilot", "microsoft-365-copilot"),
    ("microsoft 365", "microsoft-365"), ("connector", "power-platform"),
    ("graph", "microsoft-365"), ("purview", "azure-compliance"),
]


def structural_mark(label: str) -> tuple[str | None, str | None]:
    """The nearest real mark for a structural box, and how near it is."""
    key = (label or "").strip().lower()
    if key in STRUCTURAL:
        pid, scope = STRUCTURAL[key]
        m = MARKS.get(pid)
        return (m[0], scope) if m else (None, None)
    for word, pid in sorted(STRUCTURAL_HINTS, key=lambda x: -len(x[0])):
        if word in key:
            m = MARKS.get(pid)
            if m:
                return m[0], "closest"
    return None, None


def structural_item(label: str, **extra) -> dict:
    mark, scope = structural_mark(label)
    item = {"label": label, "glyph": "generic", "mark": mark,
            "mark_scope": scope,
            "mark_status": "mark" if mark else "labelled-chip",
            "product": None, "family": None, "app": None}
    item.update(extra)
    return item


def subject_areas(entry: dict, limit: int = 6, shout: set[str] | None = None) -> list[str]:
    """The tags the entry carries, read as the subject areas it works on.

    A tag is a declaration. It is the only per-entry statement of subject
    matter that every entry in the registry makes.
    """
    out, seen = [], set()
    for t in entry.get("tags") or []:
        label = humanise(str(t), shout)
        low = label.lower()
        if not label or low in seen or INTERNAL.search(label):
            continue
        seen.add(low)
        out.append(label)
        if len(out) == limit:
            break
    return out


# --------------------------------------------------------------------------
def _product_item(p: dict) -> dict:
    return {
        "label": p["name"],
        "glyph": GLYPH.get(p["family"], "generic"),
        "mark": p["mark"],
        "mark_scope": p["mark_scope"],
        "mark_status": p["mark_status"],
        "product": p["id"],
        "family": p["family"],
        "app": p["app"],
        "confidence": p["confidence"],
        "from": p["evidence"],
    }


def build(entry: dict, source_text: str = "") -> dict:
    # Capitals the entry itself uses, so a derived label does not spell HEDIS
    # "Hedis" back at the person who wrote it.
    shout = acronyms_in(" ".join(filter(None, [
        entry.get("description"), entry.get("lede"), entry.get("summary"),
        entry.get("display_name"), " ".join(entry.get("business_value") or []),
        " ".join(entry.get("featured_tools") or [])])))

    products = [resolve(a) for a in detect(entry, source_text)]
    by_column: dict[str, list[dict]] = {}
    for p in products:
        by_column.setdefault(p["column"], []).append(_product_item(p))

    # Systems the entry named that match no known platform. They keep their own
    # name, in Knowledge, and are reported — never sorted into a guess.
    matched = {m for p in products for m in p.get("matched") or []}
    unclassified = []
    named_systems = list(dict.fromkeys(
        (entry.get("featured_tools") or []) + (entry.get("requires") or [])
        + (entry.get("built_with") or [])))
    for s in named_systems:
        if s in matched or s in unclassified:
            continue
        unclassified.append(s)

    knowledge = by_column.get("knowledge", []) + [
        structural_item(s, confidence="declared",
                        **{"from": "named by this entry"})
        for s in unclassified]

    areas = subject_areas(entry, shout=shout)
    if not knowledge:
        knowledge = [{
            "label": "No Microsoft product named", "glyph": "unknown",
            "mark": None, "mark_scope": None, "mark_status": "labelled-chip",
            "product": None, "family": None, "app": None,
            "confidence": "unknown", "unknown": True,
            "from": ("this entry declares no system, so none is drawn — it reads "
                     "whatever the operator already has open"),
        }]

    surfaces = by_column.get("interface", [])
    surface_declared = bool(surfaces)
    if not surfaces:
        surfaces = [{
            "label": "No surface declared", "glyph": "unknown", "mark": None,
            "mark_scope": None, "mark_status": "labelled-chip", "product": None,
            "family": None, "app": None, "confidence": "unknown", "unknown": True,
            "from": "this entry names no surface; it answers wherever it is installed",
        }]

    schema = tool_schema(source_text)
    operations = []
    dropped = []
    for op in schema["operations"]:
        label = humanise(op, shout)
        if INTERNAL.search(label):
            dropped.append(op)
            continue
        if label not in operations:
            operations.append(label)

    parameters = []
    for name in schema["parameters"]:
        if INTERNAL.search(name.replace("_", " ")):
            dropped.append(name)
            continue
        parameters.append(name)

    # WHAT THE ORCHESTRATOR ACTUALLY RUNS.
    #
    # This used to read business_value first, which is why an architecture
    # could show "Enable faster" and "Lower-risk" in the box where the work
    # belongs. Those are outcomes. Listing an outcome as an action tells a
    # reader nothing about what the agent does, and it is worse than an empty
    # box because it looks answered.
    #
    # Order of truth, best first:
    #   1. the agent's own tool schema — a declared operation enum is fact
    #   2. an authored breakdown in data/solution_actions.json, for the
    #      solutions whose only source is one sentence of marketing copy
    #   3. verb clauses from the description, when it describes real steps
    # business_value is never used here. It has its own place on the page.
    authored = AUTHORED_ACTIONS.get(entry.get("slug", "")) or {}
    agents = authored.get("agents") or []
    if operations:
        actions = operations[:6]
        action_source = "the agent's own tool schema"
    elif agents:
        actions = [a["name"] for a in agents]
        action_source = "authored for this solution"
    else:
        actions = clauses(entry.get("description") or entry.get("lede")
                          or entry.get("summary") or "", shout=shout)
        action_source = "read from this entry's description"
    if not actions:
        actions = ["Runs the task described in this entry"]
        action_source = "nothing declared"

    personas = [p for p in (entry.get("personas") or entry.get("audience") or []) if p]
    actors = [{"label": p, "declared": True} for p in personas[:2]]
    if not actors:
        actors = [{"label": "Operator", "declared": False,
                   "note": "no audience declared by this entry"}]

    automation = by_column.get("automation", [])
    connectors = [a["label"] for a in automation]
    connectors_declared = bool(connectors)
    if not connectors:
        connectors = ["Power Platform connectors and actions"]
    connector_items = [structural_item(c, confidence=(
        "declared" if connectors_declared else "platform")) for c in connectors]

    reporting = by_column.get("reporting", [])
    reporting_declared = bool(reporting)
    if not reporting:
        reporting = [structural_item(
            "Copilot Control System", glyph="m365", family="Microsoft 365",
            confidence="platform", **{"from": "platform default"})]

    # Steps 1 and 5 say the entry's own surface and system of record when it
    # declares them, and stay generic when it does not.
    flow = list(FLOW)
    if surface_declared:
        flow[0] = "Natural language input in " + surfaces[0]["label"]
    systems_of_record = [k["label"] for k in knowledge if not k.get("unknown")]
    if systems_of_record:
        flow[4] = "Action taken in " + systems_of_record[0]

    model = by_column.get("processing", [])

    core = {
        "knowledge": [k["label"] for k in knowledge],
        "areas": areas,
        "surfaces": [s["label"] for s in surfaces],
        "operations": operations,
        "parameters": parameters,
        "actions": actions,
        "actors": [a["label"] for a in actors],
        "reporting": [r["label"] for r in reporting],
    }
    signature = hashlib.sha1(
        json.dumps(core, sort_keys=True).encode("utf-8")).hexdigest()[:12]

    return {
        "slug": entry["slug"],
        "kind": entry.get("kind", "solution"),
        "ref": entry.get("ref"),
        "display_name": entry.get("display_name") or entry["slug"],
        "industries": [i for i in (entry.get("industries") or []) if i],
        "signature": signature,
        "products": products,
        "product_ids": [p["id"] for p in products],
        "families": list(dict.fromkeys(p["family"] for p in products)),
        "columns": {
            "knowledge": {
                "title": "Knowledge",
                "grounding": knowledge,
                "subject_areas": areas,
                "connectors": connectors,
                "connectors_declared": connectors_declared,
                "note": ("Grounding data the agent reads. It is not copied — the "
                         "agent reads it in place, under the caller's permissions."),
            },
            "processing": {
                "title": "Processing",
                "orchestration": (authored.get("orchestration")
                                  or "Multi-agent orchestration"),
                "agents": agents,
                "action_source": action_source,
                "plan": FLOW[2],
                "operations": operations,
                "operation_hint": schema["operation_hint"],
                "parameters": parameters,
                "model": model,
                "actions": actions,
            },
            "interface": {
                "title": "User Interface",
                "surfaces": surfaces,
                "surface_declared": surface_declared,
                "actors": actors,
                "checks": FLOW[1],
            },
            "reporting": {
                "title": "Reporting",
                "systems": reporting,
                "reporting_declared": reporting_declared,
                "governance": ("Reviews audit logs, sensitivity labels, data "
                               "policies, CMK, DLP"),
                "insights": "Logs and telemetry data for analysis and monitoring",
            },
        },
        "flow": [{"step": i + 1, "text": t} for i, t in enumerate(flow)],
        "tools_band": ("Automatic orchestration using prompts, agent flows, computer "
                       "use, custom connectors, Model Context Protocol and REST API"),
        "foundation_band": dict(
            structural_item("Entra ID"),
            identity="Entra ID",
            label="Supporting features and foundation models"),
        "configuration": entry.get("requires_env") or [],
        "derivation": {
            "systems_declared": named_systems,
            "unclassified": unclassified,
            "operations_read_from_source": bool(operations),
            "operations_withheld": dropped,
            "signals": {
                "tool_schema": len(schema["operations"]),
                "tags": len(entry.get("tags") or []),
                "products_declared": sum(1 for p in products
                                         if p["confidence"] == "declared"),
                "products_implied": sum(1 for p in products
                                        if p["confidence"] == "implied"),
            },
            "note": ("Every box is derived from what the entry declares — its "
                     "description, its tags, its configuration and the operation "
                     "enum in its own tool schema. Products are resolved through "
                     "data/products.json, where each one carries the evidence "
                     "that put it there. Systems whose name matched no known "
                     "platform are placed in Knowledge under their own name and "
                     "listed here rather than sorted into a category they may "
                     "not belong to."),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only")
    args = ap.parse_args()

    items = product_entries()
    if args.only:
        items = [e for e in items if args.only in e["slug"]]
    if not items:
        print(f"[architecture] nothing matched {args.only!r}", file=sys.stderr)
        return 1

    built = [build(e, source_text_for(e)) for e in items]
    doc = {
        "schema": SCHEMA,
        "format_version": FORMAT_VERSION,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": ("Reference architectures, derived from what each entry declares. "
                 "They describe the shape of a working deployment, not a deployment "
                 "anyone has made — nothing here is a statement about a customer "
                 "environment."),
        "count": len(built),
        "distinct_signatures": len({b["signature"] for b in built}),
        "architectures": built,
    }
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    unc = sum(1 for b in built if b["derivation"]["unclassified"])
    ops = sum(1 for b in built if b["derivation"]["operations_read_from_source"])
    print(f"[architecture] {len(built)} architectures · "
          f"{doc['distinct_signatures']} distinct "
          f"({100 * doc['distinct_signatures'] // max(len(built), 1)}%)")
    print(f"[architecture] {ops} read an operation enum from the agent's own tool "
          f"schema · {unc} with a system left unclassified rather than guessed")
    print(f"[architecture] wrote {OUT_FILE.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
