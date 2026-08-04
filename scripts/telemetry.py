#!/usr/bin/env python3
"""aibast.tooling.v1 — ToolInteractionEvent emitter.

The minimum event contract every AIBAST TA tool emits (schema:
schemas/tool-interaction-event.schema.json). Import `emit()` from any tool
in this repo, or call the CLI for shell tooling.

Design guardrails, enforced in code (not just documented):
  * PROHIBITED content can never ride along: unknown keys are rejected, and
    a denylist refuses prompt/response/customer/document/user-identity
    fields by name even if someone widens the call site.
  * Role, never person — actorRole/actorRegion are closed enums.
  * Events go to the endpoint in AIBAST_TELEMETRY_ENDPOINT (an internal
    collector). With no endpoint configured, emit() validates and returns
    the event without sending — tools stay functional offline and NOTHING
    is ever written into this repository. Business identifiers
    (msxOpportunityId, tpid) exist only in flight to the internal
    collector; they are never persisted here.

Usage (library):
    from telemetry import emit
    emit("rapp.prototype.generated", tool_id="RAPP", tool_version="1.0.0",
         correlation_id=cid, actor_role="TA", actor_region="AMER",
         program_id="AGENTS", outcome="success", duration_ms=5321)

Usage (CLI):
    python3 scripts/telemetry.py --event-name library.agent.deployed \
        --tool-id LIBRARY --tool-version 1.0.0 --actor-role SE \
        --actor-region EMEA --program-id AGENTS --outcome success \
        --duration-ms 1200 [--correlation-id GUID] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
import uuid
from datetime import datetime, timezone

TOOL_IDS = {"RAPP", "AIDEATE", "LIBRARY", "DMT", "SOWAGENT"}
ACTOR_ROLES = {"TA", "SE", "GBB", "PARTNER", "ISD"}
ACTOR_REGIONS = {"AMER", "EMEA", "APAC", "LATAM"}
PROGRAM_IDS = {"SFRC", "ERP", "CCAS", "AGENTS", "LOWCODE"}
OUTCOMES = {"success", "failure", "abandoned"}
EVENT_NAME_RE = re.compile(
    r"^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)+"
    r"\.(created|started|completed|failed|deployed|shared|generated)$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+([-+][0-9A-Za-z.-]+)?$")

# Names that must never appear in a payload, whatever the caller intended.
PROHIBITED_KEYS = {
    "prompt", "prompts", "response", "responses", "completion", "messages",
    "customerdata", "customer", "document", "documents", "content",
    "contents", "user", "username", "useremail", "email", "upn", "alias",
    "displayname", "actorname",
}

ENDPOINT_ENV = "AIBAST_TELEMETRY_ENDPOINT"


class TelemetryError(ValueError):
    pass


def build_event(event_name: str, *, tool_id: str, tool_version: str,
                correlation_id: str | None, actor_role: str,
                actor_region: str, program_id: str, outcome: str,
                duration_ms: int, msx_opportunity_id: str | None = None,
                tpid: str | None = None, **extra) -> dict:
    """Build and validate a ToolInteractionEvent. Raises TelemetryError on
    any contract violation — a bad event is dropped loudly, never sent."""
    if extra:
        lowered = {k.lower() for k in extra}
        if lowered & PROHIBITED_KEYS:
            raise TelemetryError(
                f"PROHIBITED field(s) in payload: {sorted(lowered & PROHIBITED_KEYS)} "
                "— prompts, responses, customer data, document contents and "
                "individual user identity never ride in telemetry.")
        raise TelemetryError(f"unknown field(s): {sorted(extra)} — the contract "
                             "is closed (additionalProperties: false).")
    if not EVENT_NAME_RE.match(event_name):
        raise TelemetryError(f"bad eventName {event_name!r}")
    if tool_id not in TOOL_IDS:
        raise TelemetryError(f"bad toolId {tool_id!r} (allowed: {sorted(TOOL_IDS)})")
    if not SEMVER_RE.match(tool_version):
        raise TelemetryError(f"toolVersion must be semver, got {tool_version!r}")
    if actor_role not in ACTOR_ROLES:
        raise TelemetryError(f"bad actorRole {actor_role!r} — role, never name")
    if actor_region not in ACTOR_REGIONS:
        raise TelemetryError(f"bad actorRegion {actor_region!r}")
    if program_id not in PROGRAM_IDS:
        raise TelemetryError(f"bad programId {program_id!r}")
    if outcome not in OUTCOMES:
        raise TelemetryError(f"bad outcome {outcome!r}")
    if not isinstance(duration_ms, int) or duration_ms < 0:
        raise TelemetryError(f"durationMs must be a non-negative int, got {duration_ms!r}")
    for label, v in (("msxOpportunityId", msx_opportunity_id), ("tpid", tpid)):
        if v is not None and not isinstance(v, str):
            raise TelemetryError(f"{label} must be a string or null")
    cid = correlation_id or str(uuid.uuid4())
    uuid.UUID(cid)  # raises on non-GUID
    return {
        "eventId": str(uuid.uuid4()),
        "eventName": event_name,
        "toolId": tool_id,
        "toolVersion": tool_version,
        "correlationId": cid,
        "msxOpportunityId": msx_opportunity_id,
        "tpid": tpid,
        "actorRole": actor_role,
        "actorRegion": actor_region,
        "programId": program_id,
        "outcome": outcome,
        "durationMs": duration_ms,
        "timestampUtc": datetime.now(timezone.utc).isoformat(),
    }


def emit(event_name: str, **kwargs) -> dict:
    """Validate and send one event. Returns the event dict. If no endpoint
    is configured, validation still runs and the event is returned unsent —
    never queued to disk, never committed anywhere."""
    event = build_event(event_name, **kwargs)
    endpoint = os.environ.get(ENDPOINT_ENV, "")
    if endpoint:
        req = urllib.request.Request(
            endpoint, data=json.dumps(event).encode(),
            headers={"Content-Type": "application/json",
                     "User-Agent": "aibast-tooling-v1"})
        try:
            with urllib.request.urlopen(req, timeout=10):
                pass
        except Exception as exc:
            # Telemetry never breaks the tool. Report, move on.
            print(f"[telemetry] send failed ({exc}); event dropped",
                  file=sys.stderr)
    return event


def main() -> int:
    ap = argparse.ArgumentParser(description="Emit a ToolInteractionEvent (aibast.tooling.v1)")
    ap.add_argument("--event-name", required=True)
    ap.add_argument("--tool-id", required=True)
    ap.add_argument("--tool-version", required=True)
    ap.add_argument("--correlation-id")
    ap.add_argument("--msx-opportunity-id")
    ap.add_argument("--tpid")
    ap.add_argument("--actor-role", required=True)
    ap.add_argument("--actor-region", required=True)
    ap.add_argument("--program-id", required=True)
    ap.add_argument("--outcome", required=True)
    ap.add_argument("--duration-ms", required=True, type=int)
    ap.add_argument("--dry-run", action="store_true",
                    help="validate + print, never send")
    a = ap.parse_args()
    try:
        if a.dry_run:
            os.environ.pop(ENDPOINT_ENV, None)
        event = emit(a.event_name, tool_id=a.tool_id, tool_version=a.tool_version,
                     correlation_id=a.correlation_id,
                     msx_opportunity_id=a.msx_opportunity_id, tpid=a.tpid,
                     actor_role=a.actor_role, actor_region=a.actor_region,
                     program_id=a.program_id, outcome=a.outcome,
                     duration_ms=a.duration_ms)
    except TelemetryError as exc:
        print(f"[telemetry] REJECTED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(event, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
