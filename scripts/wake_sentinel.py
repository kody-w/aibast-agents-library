#!/usr/bin/env python3
"""Wake a Sentinel run — inject a model into the neighborhood's bones.

The neighborhood is data. `sentinel.py run` measures with its deterministic
residents and stops, because measurement is not judgment: a run with no model
attached is dormant and produces no verdicts, by design.

This is the injector. It takes the packets a dormant run emitted, executes them
against an inference endpoint, and absorbs the answers back with the model
recorded as attribution. That is the whole mechanism by which aggregated work
gets better here rather than merely being listed: an outside skill is crawled,
shaped into the RAPP format, mirrored into both projections, and then actually
*reviewed* — by a model reasoning about it against published principles, in the
same automated pass.

Deliberately separate from `sentinel.py`. The runner holds no credential and
calls nothing; swapping which model reviews the library is a change to this
file and to nothing else, and the neighborhood itself stays portable data that
anyone can run under any runtime.

Any OpenAI-compatible chat-completions endpoint works, which is what keeps the
neighborhood portable: the same review runs in CI against Azure OpenAI and on a
laptop against a local model, with no change to the data.

  SENTINEL_ENDPOINT + SENTINEL_MODEL  (+ SENTINEL_API_KEY)  any compatible API,
                                          including a local Ollama or llama.cpp
  AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_DEPLOYMENT (+ AZURE_OPENAI_API_KEY)

Nothing configured means nothing is woken: the run stays dormant, the exit code
stays zero, and it says so. A review pipeline that silently degrades into
rubber-stamping is worse than one that admits it did not run.

(GitHub Models is deliberately not a fallback: it is being retired, and a
default that returns 410 would make a working pipeline look broken.)

Usage:
    python3 scripts/wake_sentinel.py                       # wake the latest run
    python3 scripts/wake_sentinel.py --run <id>
    python3 scripts/wake_sentinel.py --resident honesty --limit 20
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SENTINEL_DIR = REPO_ROOT / "sentinel"
_RUNS_OVERRIDE = os.environ.get("SENTINEL_RUNS_DIR")
RUNS_DIR = Path(_RUNS_OVERRIDE) if _RUNS_OVERRIDE else SENTINEL_DIR / "runs"
LATEST = (RUNS_DIR / "latest.json") if _RUNS_OVERRIDE else (SENTINEL_DIR / "latest.json")

DEFAULT_MODEL = os.environ.get("SENTINEL_MODEL", "gpt-4o-mini")
MAX_SOURCE_CHARS = 24000


def warn(msg: str) -> None:
    print(f"[wake] {msg}", file=sys.stderr)


def resolve_endpoint() -> tuple[str, dict, str, str] | None:
    """Return (url, headers, model_label, kind) for whatever is configured."""
    generic = os.environ.get("SENTINEL_ENDPOINT")
    if generic:
        headers = {}
        key = os.environ.get("SENTINEL_API_KEY")
        if key:
            headers["Authorization"] = f"Bearer {key}"
        return generic, headers, f"{DEFAULT_MODEL}", "openai"

    az_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    az_deploy = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
    if az_endpoint and az_deploy:
        version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21")
        url = (f"{az_endpoint.rstrip('/')}/openai/deployments/{az_deploy}"
               f"/chat/completions?api-version={version}")
        key = os.environ.get("AZURE_OPENAI_API_KEY")
        if not key:
            warn("AZURE_OPENAI_ENDPOINT set without AZURE_OPENAI_API_KEY")
            return None
        return url, {"api-key": key}, f"azure:{az_deploy}", "azure"

    return None


def call_model(url: str, headers: dict, model: str, kind: str,
               system: str, user: str) -> str | None:
    payload = {
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    if kind != "azure":
        payload["model"] = model
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            doc = json.loads(r.read().decode("utf-8"))
        return doc["choices"][0]["message"]["content"]
    except (urllib.error.URLError, OSError, KeyError, json.JSONDecodeError) as exc:
        warn(f"inference failed: {exc}")
        return None


def parse_json(text: str) -> dict | None:
    """Models sometimes fence their JSON. Recover it rather than losing the run."""
    if not text:
        return None
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    try:
        doc = json.loads(text)
        return doc if isinstance(doc, dict) else None
    except json.JSONDecodeError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", help="run id (default: the latest recorded run)")
    ap.add_argument("--resident", help="wake only this resident")
    ap.add_argument("--limit", type=int, default=0,
                    help="review at most N subjects per resident (0 = all)")
    args = ap.parse_args()

    if not LATEST.is_file():
        warn("no recorded run; run scripts/sentinel.py first")
        return 0
    run_id = args.run or json.loads(LATEST.read_text(encoding="utf-8"))["run_id"]
    run_file = RUNS_DIR / f"{run_id}.json"
    if not run_file.is_file():
        warn(f"no run {run_id}")
        return 0

    run = json.loads(run_file.read_text(encoding="utf-8"))
    if not run.get("packets"):
        print(f"[wake] run {run_id} has no pending residents — already awake")
        return 0

    resolved = resolve_endpoint()
    if not resolved:
        # The honest outcome. A dormant run that says it is dormant is a
        # working pipeline reporting no model was available; a run that
        # invents verdicts to look complete is a broken one hiding it.
        print("[wake] no inference endpoint configured — run stays DORMANT "
              "(set SENTINEL_ENDPOINT + SENTINEL_MODEL for any OpenAI-compatible "
              "API, or AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_DEPLOYMENT)")
        return 0
    url, headers, model_label, kind = resolved

    subjects = {s["slug"]: s for s in run["subjects"]}
    packets = run["packets"]
    if args.resident:
        packets = [p for p in packets if p["resident"] == args.resident]

    woke = 0
    for packet in packets:
        slugs = packet.get("subject_slugs") or list(subjects)
        if args.limit:
            slugs = slugs[:args.limit]

        answers: dict[str, dict] = {}
        for slug in slugs:
            subject = subjects.get(slug)
            if not subject:
                continue
            path = REPO_ROOT / subject["file"]
            if not path.is_file():
                continue
            source = path.read_text(encoding="utf-8", errors="replace")[:MAX_SOURCE_CHARS]
            user = (f"Subject: {subject['file']}\n"
                    f"Reference: {slug}\n\n"
                    f"--- BEGIN SOURCE ---\n{source}\n--- END SOURCE ---")
            raw = call_model(url, headers, DEFAULT_MODEL, kind, packet["prompt"], user)
            answer = parse_json(raw or "")
            if answer:
                answers[slug] = answer

        if not answers:
            warn(f"resident {packet['resident']} produced no usable answers; "
                 "leaving it asleep rather than recording an empty review")
            continue

        # Hand back through sentinel.py so absorption, attribution, and verdict
        # recomputation stay in one place.
        tmp = RUNS_DIR / f".{run_id}.{packet['resident']}.answers.json"
        tmp.write_text(json.dumps(answers, indent=2), encoding="utf-8")
        rc = os.system(
            f"python3 {REPO_ROOT / 'scripts' / 'sentinel.py'} absorb "
            f"--run {run_id} --resident {packet['resident']} "
            f"--answers {tmp} --model '{model_label}'")
        tmp.unlink(missing_ok=True)
        if rc == 0:
            woke += 1
            print(f"[wake] {packet['resident']}: {len(answers)} subject(s) reviewed "
                  f"by {model_label}")

    run = json.loads(run_file.read_text(encoding="utf-8"))
    print(f"[wake] run {run_id} is now {run['status'].upper()} "
          f"({woke} resident(s) woken, {len(run.get('packets') or [])} still asleep)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
