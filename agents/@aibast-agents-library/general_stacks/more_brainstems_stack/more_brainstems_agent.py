"""
More Brainstems Agent

Starts more Brainstems beside the one you are chatting with, each on its own
port on this computer, each with its own agents folder. Then it talks to them
the only way a Brainstem is ever driven: a message to its /chat.

Use it to give a repository its own Brainstem, to split a big job into small
helpers that each report back, or to try an agent without touching your own
Brainstem. Every helper is stopped with one ask, and its folder can be kept or
removed.

Rules it keeps:
- Helpers listen on this computer only (127.0.0.1). LAN mode is switched off for them.
- It adds no route to the Brainstem and calls nothing but /health and /chat.
- It never installs packages; helpers run with the same Python as this Brainstem.
"""

import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    from agents.basic_agent import BasicAgent
except ImportError:
    from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/more-brainstems",
    "version": "1.0.0",
    "display_name": "More Brainstems",
    "description": "Start, message and stop helper Brainstems on this computer, each with its own agents, driven only through /chat.",
    "author": "AIBAST",
    "tags": ["brainstem", "helpers", "local"],
    "category": "general",
    "quality_tier": "community",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}

_NAME_RE = re.compile(r"[^a-z0-9-]+")


def _home() -> Path:
    return Path(os.environ.get("MORE_BRAINSTEMS_HOME") or Path.home() / ".brainstem" / "more")


def _slug(value: str) -> str:
    return _NAME_RE.sub("-", str(value or "").lower()).strip("-")[:40]


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _brainstem_file() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "brainstem.py"
        if candidate.is_file():
            return candidate
    env = os.environ.get("BRAINSTEM_HOME")
    if env and (Path(env) / "brainstem.py").is_file():
        return Path(env) / "brainstem.py"
    return None


def _get(url: str, timeout: float = 2.0):
    with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310 (loopback only)
        return json.loads(r.read().decode("utf-8") or "{}")


def _post(url: str, body: dict, timeout: float):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (loopback only)
        return json.loads(r.read().decode("utf-8") or "{}")


class MoreBrainstemsAgent(BasicAgent):
    def __init__(self):
        self.name = "MoreBrainstems"
        self.metadata = {
            "name": self.name,
            "description": (
                "Runs helper Brainstems on this computer. action=start makes a named helper "
                "(optionally copying agent files into it), action=list shows them, action=chat "
                "sends a helper a message and returns its answer, action=stop stops one "
                "(remove=true also deletes its folder)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["start", "list", "chat", "stop"]},
                    "name": {"type": "string", "description": "Helper name, e.g. the repository it serves."},
                    "message": {"type": "string", "description": "What to say to the helper (action=chat)."},
                    "agent_files": {
                        "type": "array", "items": {"type": "string"},
                        "description": "Paths of *_agent.py files to copy into the helper (action=start).",
                    },
                    "remove": {"type": "boolean", "description": "Delete the helper's folder on stop."},
                },
                "required": ["action"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    # registry -----------------------------------------------------------
    def _registry_path(self) -> Path:
        return _home() / "brainstems.json"

    def _load(self) -> dict:
        try:
            return json.loads(self._registry_path().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save(self, brainstems: dict) -> None:
        path = self._registry_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(brainstems, indent=2), encoding="utf-8")

    @staticmethod
    def _alive(entry: dict) -> bool:
        try:
            _get(f"http://127.0.0.1:{entry['port']}/health")
            return True
        except (OSError, urllib.error.URLError, ValueError, KeyError):
            return False

    # actions -------------------------------------------------------------
    def perform(self, **kwargs):
        action = str(kwargs.get("action") or "list").lower()
        try:
            if action == "start":
                return self._start(kwargs)
            if action == "chat":
                return self._chat(kwargs)
            if action == "stop":
                return self._stop(kwargs)
            return self._list()
        except Exception as exc:  # report, never crash the chat
            return json.dumps({"ok": False, "error": str(exc)})

    def _list(self):
        brainstems = self._load()
        rows = [
            {"name": n, "port": e["port"], "running": self._alive(e), "folder": e["folder"]}
            for n, e in sorted(brainstems.items())
        ]
        return json.dumps({"ok": True, "helpers": rows})

    def _start(self, kw):
        name = _slug(kw.get("name"))
        if not name:
            return json.dumps({"ok": False, "error": "Give the helper a name."})
        brainstems = self._load()
        if name in brainstems and self._alive(brainstems[name]):
            return json.dumps({"ok": True, "name": name, "port": brainstems[name]["port"], "note": "already running"})
        brainstem = _brainstem_file()
        if brainstem is None:
            return json.dumps({"ok": False, "error": "Could not find brainstem.py beside this agent."})
        folder = _home() / name
        agents = folder / "agents"
        agents.mkdir(parents=True, exist_ok=True)
        base = brainstem.parent / "agents" / "basic_agent.py"
        if base.is_file():
            shutil.copy2(base, agents / "basic_agent.py")
        copied = []
        for item in kw.get("agent_files") or []:
            src = Path(str(item)).expanduser()
            if src.is_file() and src.name.endswith("_agent.py"):
                shutil.copy2(src, agents / src.name)
                copied.append(src.name)
        port = _free_port()
        env = dict(os.environ)
        env.update({"PORT": str(port), "AGENTS_PATH": str(agents), "BRAINSTEM_LAN_MODE": "0"})
        log = open(folder / "brainstem.log", "ab")  # noqa: SIM115 (kept open by the child)
        proc = subprocess.Popen(
            [sys.executable, str(brainstem)], cwd=str(brainstem.parent), env=env,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
        )
        entry = {"port": port, "pid": proc.pid, "folder": str(folder)}
        deadline = time.time() + 30
        while time.time() < deadline:
            if proc.poll() is not None:
                return json.dumps({"ok": False, "error": f"Helper stopped at start; see {folder / 'brainstem.log'}"})
            try:
                _get(f"http://127.0.0.1:{port}/health")
                break
            except (OSError, urllib.error.URLError, ValueError):
                time.sleep(0.5)
        else:
            return json.dumps({"ok": False, "error": "Helper did not answer within 30 seconds."})
        brainstems[name] = entry
        self._save(brainstems)
        return json.dumps({"ok": True, "name": name, "port": port, "agents_copied": copied})

    def _chat(self, kw):
        name = _slug(kw.get("name"))
        entry = self._load().get(name)
        if not entry:
            return json.dumps({"ok": False, "error": f"No helper named {name!r}. Start it first."})
        message = str(kw.get("message") or "").strip()
        if not message:
            return json.dumps({"ok": False, "error": "Say what to send."})
        reply = _post(f"http://127.0.0.1:{entry['port']}/chat", {"user_input": message}, timeout=300)
        return json.dumps({"ok": True, "name": name, "response": reply.get("response", "")})

    def _stop(self, kw):
        name = _slug(kw.get("name"))
        brainstems = self._load()
        entry = brainstems.pop(name, None)
        if not entry:
            return json.dumps({"ok": False, "error": f"No helper named {name!r}."})
        try:
            os.killpg(entry["pid"], signal.SIGTERM) if hasattr(os, "killpg") else os.kill(entry["pid"], signal.SIGTERM)
        except (OSError, ProcessLookupError):
            pass
        if kw.get("remove"):
            shutil.rmtree(entry["folder"], ignore_errors=True)
        self._save(brainstems)
        return json.dumps({"ok": True, "name": name, "stopped": True, "removed": bool(kw.get("remove"))})
