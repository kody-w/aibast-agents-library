"""
AIBASTRegistry — find and install AIBAST agents by chat, from the AIBAST registry.

Drop this file into a running Brainstem's agents/ folder. It reads the AIBAST
library's registry (not any personal one) and works in plain words:

    search  find agents by what they do (name, description, tags, solution terms)
    install fetch one agent's file from the registry's own repository, check its
            SHA-256 against the registry entry (refuse on any mismatch, nothing is
            written), then save it into this agents/ folder. The Brainstem loads its
            agents folder on every message, so the agent is ready on the next one,
            with no restart.
    list    what this agent installed
    remove  delete a file this agent installed (never anything else)
    submit  how to propose an agent to the AIBAST library (prepares, never sends)

Downloaded code is never run here: it is checked and written, nothing more. Only
.py files that land inside this agents/ folder are accepted. No telemetry.

Env: AIBAST_REGISTRY_URL (production by default; staging is
https://kody-w.github.io/aibast-agents-library/registry.json), AIBAST_RAW_BASE
(where that registry's files are served; defaults to the registry's own branch).
"""

import ast
import hashlib
import json
import os
import re
import time
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen

from agents.basic_agent import BasicAgent

__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/aibast-registry",
    "version": "1.0.0",
    "display_name": "AIBAST Registry",
    "description": (
        "Finds and installs AIBAST library agents by chat: search by what they do, install "
        "one (checked against the registry before it is saved), list or remove what it installed."
    ),
    "author": "AIBAST",
    "tags": ["registry", "install", "search", "agent-library"],
    "category": "general",
    "quality_tier": "community",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}

DEFAULT_REGISTRY_URL = "https://microsoft.github.io/aibast-agents-library/registry.json"
DEFAULT_RAW_BASE = "https://raw.githubusercontent.com/microsoft/aibast-agents-library/main/"
# Each published registry's files live on its own repository's branch: production on microsoft/main, the
# staging ring on kody-w/staging. Any other registry address serves its files beside itself.
RAW_BASES = {
    "https://microsoft.github.io/aibast-agents-library/": DEFAULT_RAW_BASE,
    "https://kody-w.github.io/aibast-agents-library/": "https://raw.githubusercontent.com/kody-w/aibast-agents-library/staging/",
}
LIBRARY_REPO = "https://github.com/microsoft/aibast-agents-library"
LEDGER_FILE = "aibast_registry_installed.json"
PROTECTED = {"basic_agent.py", "__init__.py"}
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def _agents_dir():
    """The folder this agent was loaded from: the Brainstem's agents/ folder."""
    return Path(__file__).resolve().parent


def _http_get(url, timeout=20):
    if urlparse(url).scheme not in ("https", "http"):
        raise ValueError(f"not a web address: {url}")
    with urlopen(url, timeout=timeout) as r:  # raises on 4xx/5xx
        return r.read()


def _one_line(text, limit=140):
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


class AIBASTRegistryAgent(BasicAgent):
    def __init__(self):
        self.name = "AIBASTRegistry"
        self.metadata = {
            "name": self.name,
            "description": (
                "Searches the AIBAST agent library and installs agents from it into this "
                "Brainstem. Use action 'search' with a query when the user wants an agent for "
                "a task, 'install' with the agent's name to add one, 'list' to show what was "
                "installed, 'remove' to take one out, 'submit' when the user wants to propose "
                "their own agent to the AIBAST library."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["search", "install", "list", "remove", "submit"],
                        "description": "search (default), install, list, remove, or submit.",
                    },
                    "query": {
                        "type": "string",
                        "description": "What to search for, e.g. 'outage' or 'deal risk'.",
                    },
                    "name": {
                        "type": "string",
                        "description": "The agent to install or remove: its name, display name, or file.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "How many search results to show (default 5).",
                    },
                },
                "required": [],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, action="search", query=None, name=None, limit=5, **kwargs):
        action = (action or "search").strip().lower()
        try:
            if action == "install":
                return self._install(name or query)
            if action == "remove":
                return self._remove(name or query)
            if action == "list":
                return self._list()
            if action == "submit":
                return self._submit(name or query)
            return self._search(query or name, limit)
        except Exception as e:  # plain words, never a traceback in chat
            return f"AIBAST Registry: something went wrong ({e})."

    # ── registry ─────────────────────────────────────────────────────────────

    def _registry(self):
        url = os.getenv("AIBAST_REGISTRY_URL") or DEFAULT_REGISTRY_URL
        site = urljoin(url, ".")
        raw_base = os.getenv("AIBAST_RAW_BASE") or RAW_BASES.get(site, site)
        return url, raw_base, json.loads(_http_get(url))

    @staticmethod
    def _find(agents, ref):
        ref = (ref or "").strip()
        low = ref.lower()
        for a in agents:
            keys = {a.get("name", ""), a.get("display_name", ""), a.get("_file", ""),
                    a.get("_install_filename", ""), a.get("name", "").split("/")[-1],
                    PurePosixPath(a.get("_file", "")).name}
            if low in {k.lower() for k in keys if k}:
                return a
        return None

    # ── ledger ───────────────────────────────────────────────────────────────

    def _ledger(self):
        try:
            data = json.loads((_agents_dir() / LEDGER_FILE).read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, ValueError):
            return []

    def _save_ledger(self, rows):
        path = _agents_dir() / LEDGER_FILE
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        os.replace(tmp, path)

    # ── search ───────────────────────────────────────────────────────────────

    def _search(self, query, limit):
        _, _, registry = self._registry()
        agents = registry.get("agents", [])
        words = [w for w in re.split(r"[^a-z0-9]+", (query or "").lower()) if w]
        if not words:
            return "Tell me what the agent should do, for example: search for 'outage' or 'deal risk'."
        installed = {r.get("name") for r in self._ledger()}
        here = {p.name for p in _agents_dir().glob("*.py")}
        scored = []
        for a in agents:
            sol = a.get("_solution") or {}
            fields = [
                (3, " ".join([a.get("name", ""), a.get("display_name", ""), sol.get("advertised_name") or ""])),
                (2, " ".join(a.get("tags", []) + list(sol.get("search_terms", [])))),
                (1, a.get("description", "")),
            ]
            score = 0
            for w in words:
                for weight, text in fields:
                    if w in text.lower():
                        score += weight
            if score and all(any(w in t.lower() for _, t in fields) for w in words):
                scored.append((score, a))
        if not scored:
            return f"No AIBAST agents match '{query}'. Try a broader word."
        scored.sort(key=lambda s: (-s[0], s[1].get("display_name", "")))
        try:
            limit = max(1, min(int(limit or 5), 20))
        except (TypeError, ValueError):
            limit = 5
        lines = [f"AIBAST agents for '{query}' ({len(scored)} found, showing {min(limit, len(scored))}):"]
        for i, (_, a) in enumerate(scored[:limit], 1):
            is_in = a.get("name") in installed or a.get("_install_filename") in here
            lines.append(f"{i}. {a.get('display_name') or a.get('name')} ({a.get('name')}): "
                         f"{_one_line(a.get('description'))}" + (" [installed]" if is_in else ""))
        lines.append("Say 'install' and the name to add one.")
        return "\n".join(lines)

    # ── install ──────────────────────────────────────────────────────────────

    @staticmethod
    def _safe_source(path):
        """The registry file path must stay inside the repository: relative, no '..', a .py file."""
        p = PurePosixPath(str(path or ""))
        if (not str(path) or p.is_absolute() or ".." in p.parts or "\\" in str(path)
                or urlparse(str(path)).scheme or p.suffix != ".py"):
            return None
        return str(p)

    @staticmethod
    def _safe_target(filename):
        """The file is written straight into the agents folder, never anywhere else."""
        name = str(filename or "")
        if (not name or "/" in name or "\\" in name or name in (".", "..") or name.startswith(".")
                or not name.endswith(".py") or name in PROTECTED):
            return None
        if not name.endswith("_agent.py"):  # the Brainstem only loads *_agent.py
            name = name[:-3] + "_agent.py"
        folder = _agents_dir()
        target = (folder / name).resolve()
        return target if target.parent == folder else None

    def _install(self, ref):
        if not ref:
            return "Which agent? Give its name, for example from a search."
        url, raw_base, registry = self._registry()
        entry = self._find(registry.get("agents", []), ref)
        if not entry:
            return f"There is no '{ref}' in the AIBAST registry. Try a search first."
        label = entry.get("display_name") or entry.get("name")
        source = self._safe_source(entry.get("_file"))
        if not source:
            return f"Refused: {label} is not a .py file inside the library. Nothing was installed."
        target = self._safe_target(entry.get("_install_filename") or PurePosixPath(source).name)
        if target is None:
            return f"Refused: {label} would be saved outside the agents folder. Nothing was installed."
        expected = str(entry.get("_sha256") or "").lower()
        if not SHA_RE.match(expected):
            return f"Refused: the registry has no checksum for {label}. Nothing was installed."

        ledger = self._ledger()
        mine = next((r for r in ledger if r.get("file") == target.name), None)
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest() == expected:
                return f"{label} is already installed and up to date ({target.name})."
            if not mine:
                return (f"Refused: {target.name} already exists in the agents folder and was not "
                        "installed by me. Nothing was changed.")

        body = _http_get(urljoin(raw_base, source))
        digest = hashlib.sha256(body).hexdigest()
        if digest != expected:
            return (f"Refused: {label} does not match the registry (expected sha256 {expected[:12]}..., "
                    f"got {digest[:12]}...). Nothing was installed.")

        tmp = target.with_name("." + target.name + ".part")  # not *_agent.py: never loaded half-written
        tmp.write_bytes(body)
        os.replace(tmp, target)
        for old in [r for r in ledger if r.get("name") == entry.get("name") and r.get("file") != target.name]:
            stale = self._safe_target(old.get("file"))  # an older version this agent installed
            if stale is not None and stale.name == old.get("file") and stale.exists():
                stale.unlink()
        ledger = [r for r in ledger if r.get("file") != target.name and r.get("name") != entry.get("name")]
        ledger.append({"name": entry.get("name"), "file": target.name, "sha256": digest,
                       "version": entry.get("version"), "registry": url,
                       "installed_at": time.strftime("%Y-%m-%dT%H:%M:%S")})
        self._save_ledger(ledger)
        needs = entry.get("requires_env") or []
        return (f"Installed {label} as {target.name} (checked against the AIBAST registry). "
                "It is ready from your next message; no restart needed."
                + (f" It needs these settings to work fully: {', '.join(needs)}." if needs else ""))

    # ── list / remove ────────────────────────────────────────────────────────

    def _list(self):
        rows = self._ledger()
        if not rows:
            return "I have not installed any AIBAST agents here yet."
        lines = ["AIBAST agents I installed:"]
        for r in rows:
            present = (_agents_dir() / str(r.get("file"))).exists()
            lines.append(f"- {r.get('name')} ({r.get('file')}, installed {r.get('installed_at')})"
                         + ("" if present else " [file is gone]"))
        return "\n".join(lines)

    def _remove(self, ref):
        if not ref:
            return "Which agent should I remove? Say 'list' to see what I installed."
        rows = self._ledger()
        low = ref.strip().lower()
        row = next((r for r in rows if low in {str(r.get("name", "")).lower(), str(r.get("file", "")).lower(),
                                                str(r.get("name", "")).split("/")[-1].lower()}), None)
        if not row:
            return (f"I did not install '{ref}', so I will not remove it. "
                    "I only remove agents I installed; say 'list' to see them.")
        target = self._safe_target(row.get("file"))
        if target is not None and target.name == row.get("file") and target.exists():
            target.unlink()
        self._save_ledger([r for r in rows if r is not row])
        return f"Removed {row.get('name')} ({row.get('file')}). It is gone from your next message."

    # ── submit ───────────────────────────────────────────────────────────────

    def _submit(self, ref):
        lines = [
            "To propose an agent to the AIBAST library (nothing is sent from here):",
            "1. Keep it to one .py file with a __manifest__ (name, version, display_name, description, "
            "author, tags, category, quality_tier 'community', requires_env, dependencies).",
            "2. It inherits BasicAgent and perform() returns plain text.",
            "3. No secrets, keys, customer names or customer data in the file; settings come from the "
            "environment and are listed in requires_env.",
            "4. It works without network in its constructor and says plainly when a setting is missing.",
            "5. Fork the library, add it under agents/@yourname/, run python build_registry.py (it must pass).",
            "6. Open a pull request to the library.",
            f"Library: {LIBRARY_REPO}",
            f"How to contribute: {LIBRARY_REPO}/blob/main/CONTRIBUTING.md",
            f"Start a pull request: {LIBRARY_REPO}/compare",
        ]
        if ref:
            lines.append(self._check_local(ref))
        return "\n".join(lines)

    def _check_local(self, ref):
        """Read (never run) a file in this agents folder and say which checklist items it meets."""
        path = (_agents_dir() / str(ref)).resolve()
        if path.parent != _agents_dir() or path.suffix != ".py" or not path.is_file():
            return f"I could not find {ref} in this agents folder to check it."
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, ValueError, OSError):
            return f"{path.name}: it does not read as Python, so it is not ready."
        manifest = None
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "__manifest__" for t in node.targets):
                try:
                    manifest = ast.literal_eval(node.value)
                except ValueError:
                    manifest = None
        needed = ["schema", "name", "version", "display_name", "description", "author", "tags",
                  "category", "quality_tier", "requires_env", "dependencies"]
        missing = [k for k in needed if not isinstance(manifest, dict) or k not in manifest]
        base = any(isinstance(n, ast.ClassDef) and any(getattr(b, "id", None) == "BasicAgent" for b in n.bases)
                   for n in ast.walk(tree))
        notes = []
        notes.append("has a complete __manifest__" if not missing else f"__manifest__ is missing: {', '.join(missing)}")
        notes.append("inherits BasicAgent" if base else "does not inherit BasicAgent")
        return f"Check of {path.name}: " + "; ".join(notes) + "."


if __name__ == "__main__":
    print(AIBASTRegistryAgent().perform(action="submit"))
