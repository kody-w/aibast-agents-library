"""
SendToStudio — switch the Brainstem's "Send to Copilot Studio" organ on and off, live.

Drop this file into a running Brainstem's agents/ folder. Nothing changes until
someone asks for it:

    on      fetch the studio organ from the AIBAST registry, check every file's
            SHA-256 against the registry entry (refuse on any mismatch), write it to
            ~/.brainstem/organs/studio/
    plan    say, in plain words, how each of this Brainstem's agents would move to
            Copilot Studio: what runs as a skill, what becomes a workflow tool, why
    build   write that Copilot Studio workspace to ~/.brainstem/organs/studio/workspace/
    send    open a page on 127.0.0.1 that shows what would be created; the person presses
            Send there (drafts; publish only with publish=true). The chat never sends.
    off     delete ~/.brainstem/organs/studio/ (the workspace with it)
    status  on or off, and whether a workspace is built

Nothing runs in the background and the kernel is never touched. Every agent file is
read, never run, and travels byte for byte into the skills it becomes.

Env: STUDIO_REGISTRY_URL, STUDIO_RAW_BASE (where the registry's files are served;
defaults to this repository on GitHub), STUDIO_COPILOT_NAME.
"""

import hashlib
import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

from agents.basic_agent import BasicAgent

__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/send-to-studio",
    "version": "1.0.0",
    "display_name": "Send to Copilot Studio",
    "description": (
        "Turns this Brainstem's agents into a Copilot Studio agent: plans which parts run as skills "
        "and which become workflow tools, builds the workspace, and sends it as a draft on request."
    ),
    "author": "AIBAST",
    "tags": ["copilot-studio", "skills", "organ-switch"],
    "category": "general",
    "quality_tier": "community",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
    "organ": "@aibast-agents-library/studio-organ",
}

ORGAN_NAME = "@aibast-agents-library/studio-organ"
DEFAULT_REGISTRY_URL = "https://microsoft.github.io/aibast-agents-library/registry.json"
DEFAULT_RAW_BASE = "https://raw.githubusercontent.com/microsoft/aibast-agents-library/main/"
# Each published registry's files live on its own repository's branch: production on microsoft/main, the
# staging ring on kody-w/staging. Any other registry address serves its files beside itself.
RAW_BASES = {
    "https://microsoft.github.io/aibast-agents-library/": DEFAULT_RAW_BASE,
    "https://kody-w.github.io/aibast-agents-library/": "https://raw.githubusercontent.com/kody-w/aibast-agents-library/staging/",
}
STATE_FILE = "organ.json"
SEND_PAGE_FILE = "send-page.json"  # the open send page: port and pid


def _organ_dir():
    return Path.home() / ".brainstem" / "organs" / "studio"


def _kernel_dir():
    """The folder holding brainstem.py: the running kernel's, else the default install."""
    main = getattr(sys.modules.get("__main__"), "__file__", None)
    candidates = [
        Path(main).resolve().parent if main else None,
        Path(__file__).resolve().parent.parent,
        Path.home() / ".brainstem" / "src" / "rapp_brainstem",
    ]
    for c in candidates:
        if c and (c / "brainstem.py").is_file():
            return c
    return candidates[-1]


def _agents_dir():
    return Path(os.getenv("AGENTS_PATH") or (_kernel_dir() / "agents"))


def _http_get(url, timeout=20):
    import requests
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.content


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, TypeError, ValueError):
        return False


class SendToStudioAgent(BasicAgent):
    def __init__(self):
        self.name = "SendToStudio"
        self.metadata = {
            "name": self.name,
            "description": (
                "Moves this Brainstem's agents to Copilot Studio. Use 'plan' when the user asks how "
                "their agents would work in Copilot Studio, 'build' to prepare the Copilot Studio "
                "workspace, 'send' to open a page on this computer where the user reviews it and presses Send "
                "themselves (nothing is sent from the chat), 'on' or 'off' to add or remove this feature, "
                "'status' to check."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["status", "on", "off", "plan", "build", "send"],
                        "description": "status (default), on, off, plan, build or send.",
                    },
                    "publish": {
                        "type": "boolean",
                        "description": "With send: also publish. Only when the user asks to publish.",
                    },
                },
                "required": [],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, action="status", publish=False, **kwargs):
        action = (action or "status").strip().lower()
        try:
            if action == "on":
                return self._on()
            if action == "off":
                return self._off()
            if action in ("plan", "build", "send"):
                if action in ("plan", "build") and not self._state():
                    turned_on = self._on()  # local and checksum-checked; asking for a plan is the yes
                    if not self._state():
                        return turned_on
                organ = self._load()
                if isinstance(organ, str):
                    return organ
                if action == "plan":
                    return organ.plain_words(organ.plan(_agents_dir()))
                if action == "build":
                    return self._build(organ)
                return self._send(publish is True)
            return self._status()
        except Exception as e:  # plain words, never a traceback in chat
            return f"Send to Copilot Studio: something went wrong ({e})."

    # ── state ────────────────────────────────────────────────────────────────

    def _state(self):
        try:
            return json.loads((_organ_dir() / STATE_FILE).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def _status(self):
        st = self._state()
        if not st:
            return "Send to Copilot Studio is off."
        built = (_organ_dir() / "workspace" / "manifest.json").is_file()
        return (f"Send to Copilot Studio is on (organ {st.get('version')}). "
                + ("A workspace is built." if built else "No workspace built yet."))

    def _load(self):
        """The installed organ, after checking its files still match what was installed."""
        st, target = self._state(), _organ_dir()
        if not st:
            return "Send to Copilot Studio is off. Ask to turn it on first."
        for name, digest in st["files"].items():
            path = target / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                return f"Refused: {name} changed since it was installed. Turn it off and on again."
        spec = importlib.util.spec_from_file_location("studio_organ_installed", target / st["entry"])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    # ── on / off ─────────────────────────────────────────────────────────────

    def _fetch_organ(self):
        """Download the organ's files and check each against the registry. Nothing is
        written here; any mismatch raises before a byte reaches the disk."""
        registry_url = os.getenv("STUDIO_REGISTRY_URL") or os.getenv("AIBAST_REGISTRY_URL") or DEFAULT_REGISTRY_URL
        site = urljoin(registry_url, ".")
        raw_base = os.getenv("STUDIO_RAW_BASE") or RAW_BASES.get(site, site)
        registry = json.loads(_http_get(registry_url))
        organ = next((o for o in registry.get("organs", []) if o.get("name") == ORGAN_NAME), None)
        if not organ or not organ.get("_files"):
            raise LookupError(f"the registry at {registry_url} has no {ORGAN_NAME}")
        files = {}
        for f in organ["_files"]:
            name = os.path.basename(f["path"])
            body = _http_get(urljoin(raw_base, f["path"]))
            digest = hashlib.sha256(body).hexdigest()
            if digest != f.get("sha256"):
                raise ValueError(
                    f"Refused: {name} does not match the registry (expected sha256 "
                    f"{str(f.get('sha256'))[:12]}..., got {digest[:12]}...). Nothing was installed.")
            files[name] = body
        return organ, files

    def _on(self):
        if self._state():
            return self._status()
        try:
            organ, files = self._fetch_organ()
        except ValueError as e:
            return str(e)
        except Exception as e:
            return f"Send to Copilot Studio could not get its organ from the registry: {e}"
        target = _organ_dir()
        staging = target.with_name("studio.staging")
        shutil.rmtree(staging, ignore_errors=True)
        staging.mkdir(parents=True)
        for name, body in files.items():
            (staging / name).write_bytes(body)
        (staging / STATE_FILE).write_text(json.dumps({
            "organ": organ.get("name"), "version": organ.get("version"),
            "entry": organ.get("entry", "studio_organ.py"),
            "files": {n: hashlib.sha256(b).hexdigest() for n, b in files.items()},
        }), encoding="utf-8")
        shutil.rmtree(target, ignore_errors=True)
        os.replace(staging, target)
        return ("Send to Copilot Studio is on. Ask for the plan to see how your agents would move; "
                "nothing is sent until you say so.")

    def _off(self):
        target = _organ_dir()
        if not target.exists():
            return "Send to Copilot Studio is already off."
        page = _read_json(target / SEND_PAGE_FILE)
        if page and _alive(page.get("pid")):
            os.kill(page["pid"], signal.SIGTERM)  # the send page this switch opened
        shutil.rmtree(target, ignore_errors=True)
        return ("Send to Copilot Studio is off. Its files and any built workspace were removed; "
                "your Brainstem is back to its normal setup.")

    # ── build / send ─────────────────────────────────────────────────────────

    def _build(self, organ):
        soul = os.getenv("SOUL_PATH") or str(_kernel_dir() / "soul.md")
        name = os.getenv("STUDIO_COPILOT_NAME") or "Brainstem Copilot"
        m = organ.build(_agents_dir(), _organ_dir() / "workspace", soul=soul, name=name)
        tools = sum(len(a["workflow_tools"]) for a in m["agents"])
        held = "".join(f" {h['agent'] or h['file']} is held back: {'; '.join(h['why'])}." for h in m["held_back"])
        return (f"The Copilot Studio workspace is ready at {_organ_dir() / 'workspace'}: "
                f"{len(m['agents'])} skill(s) and {tools} workflow tool(s).{held} "
                "Say 'send it' when you want it in Copilot Studio as a draft.")

    def _send(self, publish):
        """Never sends. Opens a page on 127.0.0.1 where the person presses Send; the model cannot press it."""
        ws = _organ_dir() / "workspace"
        if not (ws / "manifest.json").is_file():
            return "Nothing is built yet. Ask to build the workspace first."
        port_file = _organ_dir() / SEND_PAGE_FILE
        page = _read_json(port_file)
        if not (page and _alive(page.get("pid"))):
            port_file.unlink(missing_ok=True)
            cmd = [sys.executable, str(_organ_dir() / "send_to_studio.py"), str(ws), "--confirm-page",
                   "--port-file", str(port_file)] + (["--publish"] if publish else [])
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            for _ in range(300):  # a busy laptop can take a while to start Python
                page = _read_json(port_file)
                if page:
                    break
                time.sleep(0.1)
        if not page:
            return "Send to Copilot Studio could not open its send page, so nothing was sent."
        return (f"Nothing was sent. Open http://127.0.0.1:{page['port']}/ to see what it creates and press Send "
                "yourself; close that page to cancel (it closes on its own in 15 minutes).")


if __name__ == "__main__":
    print(SendToStudioAgent().perform(action="status"))
