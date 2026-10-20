"""
OfflineMode — switch the Brainstem's offline organ on and off, live.

Drop this file into a running Brainstem's agents/ folder. Nothing changes until
someone asks for it:

    on      fetch the offline runner from the AIBAST registry, check every file's
            SHA-256 against the registry entry (refuse on any mismatch), write it to
            ~/.brainstem/organs/offline/, start it on 127.0.0.1:7072, return its URL
    off     stop that recorded process and delete ~/.brainstem/organs/offline/
    status  running or not, model, port

The kernel keeps running untouched the whole time; off returns it to the plain
Brainstem. The runner talks only to a model server on this computer (Ollama by
default) and never falls back to the cloud.

Env: OFFLINE_REGISTRY_URL, OFFLINE_RAW_BASE (where the registry's files are
served; defaults to this repository on GitHub), OFFLINE_PORT, OFFLINE_MODEL,
OFFLINE_BASE_URL.
"""

import hashlib
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
    "name": "@aibast-agents-library/offline-mode",
    "version": "1.0.0",
    "display_name": "Offline Mode",
    "description": (
        "Turns offline mode on or off: runs this Brainstem's agents on a model on "
        "your own computer (Ollama) at 127.0.0.1:7072, beside the normal Brainstem."
    ),
    "author": "AIBAST",
    "tags": ["offline", "local-model", "ollama", "organ-switch"],
    "category": "general",
    "quality_tier": "community",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
    "organ": "@aibast-agents-library/offline-runner",
}

ORGAN_NAME = "@aibast-agents-library/offline-runner"
DEFAULT_REGISTRY_URL = "https://microsoft.github.io/aibast-agents-library/registry.json"
DEFAULT_RAW_BASE = "https://raw.githubusercontent.com/microsoft/aibast-agents-library/main/"
# Each published registry's files live on its own repository's branch: production on microsoft/main, the
# staging ring on kody-w/staging. Any other registry address serves its files beside itself.
RAW_BASES = {
    "https://microsoft.github.io/aibast-agents-library/": DEFAULT_RAW_BASE,
    "https://kody-w.github.io/aibast-agents-library/": "https://raw.githubusercontent.com/kody-w/aibast-agents-library/staging/",
}
STATE_FILE = "runner.json"


def _organ_dir():
    return Path.home() / ".brainstem" / "organs" / "offline"


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


def _http_get(url, timeout=20):
    import requests
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.content


def _alive(pid):
    try:
        os.kill(pid, 0)
    except (OSError, ValueError):
        return False
    try:  # a finished child of this process is a zombie until reaped
        done, _ = os.waitpid(pid, os.WNOHANG)
        return done == 0
    except (ChildProcessError, OSError, AttributeError):
        return True


def _is_our_runner(pid):
    """Only ever stop the process this agent started (checked by its command line)."""
    if os.name == "nt":
        return True
    try:
        cmd = subprocess.run(["ps", "-o", "command=", "-p", str(pid)],
                             capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return False
    return "offline_brainstem.py" in cmd


class OfflineModeAgent(BasicAgent):
    def __init__(self):
        self.name = "OfflineMode"
        self.metadata = {
            "name": self.name,
            "description": (
                "Turns offline mode on or off, or reports its status. Offline mode runs "
                "this Brainstem on a model on the user's own computer (Ollama) at a "
                "second local address. Use action 'on' when the user asks to go offline "
                "or use a local model, 'off' to turn it off, 'status' to check."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["status", "on", "off"],
                        "description": "status (default), on, or off.",
                    },
                    "model": {
                        "type": "string",
                        "description": "Optional local model id, e.g. qwen3:4b.",
                    },
                },
                "required": [],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, action="status", model=None, **kwargs):
        action = (action or "status").strip().lower()
        try:
            if action == "on":
                return self._on(model)
            if action == "off":
                return self._off()
            return self._status()
        except Exception as e:  # plain words, never a traceback in chat
            return f"Offline mode: something went wrong ({e})."

    # ── state ────────────────────────────────────────────────────────────────

    def _state(self):
        try:
            return json.loads((_organ_dir() / STATE_FILE).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def _health(self, port):
        import requests
        s = requests.Session()
        s.trust_env = False
        r = s.get(f"http://127.0.0.1:{port}/health", timeout=3)
        r.raise_for_status()
        return r.json()

    def _status(self):
        st = self._state()
        if not st or not _alive(st.get("pid", -1)):
            return "Offline mode is off."
        try:
            h = self._health(st["port"])
            model = h.get("model")
        except Exception:
            model = st.get("model") or "starting"
        return (f"Offline mode is on at http://127.0.0.1:{st['port']} "
                f"(model {model}, process {st['pid']}).")

    # ── on ───────────────────────────────────────────────────────────────────

    def _fetch_organ(self):
        """Download the organ's files and check each against the registry. Nothing is
        written here; any mismatch raises before a byte reaches the disk."""
        registry_url = os.getenv("OFFLINE_REGISTRY_URL") or DEFAULT_REGISTRY_URL
        site = urljoin(registry_url, ".")
        raw_base = os.getenv("OFFLINE_RAW_BASE") or RAW_BASES.get(site, site)
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

    def _on(self, model):
        st = self._state()
        if st and _alive(st.get("pid", -1)):
            return self._status()
        try:
            organ, files = self._fetch_organ()
        except ValueError as e:
            return str(e)
        except Exception as e:
            return f"Offline mode could not get the offline runner from the registry: {e}"

        target = _organ_dir()
        staging = target.with_name("offline.staging")
        shutil.rmtree(staging, ignore_errors=True)
        staging.mkdir(parents=True)
        for name, body in files.items():
            (staging / name).write_bytes(body)
        shutil.rmtree(target, ignore_errors=True)
        os.replace(staging, target)

        port = int(os.getenv("OFFLINE_PORT") or "7072")
        env = dict(os.environ, BRAINSTEM_SRC=str(_kernel_dir()), OFFLINE_PORT=str(port))
        if model:
            env["OFFLINE_MODEL"] = model
        log = open(target / "runner.log", "ab")
        kw = {"start_new_session": True} if os.name != "nt" else {
            "creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        proc = subprocess.Popen(
            [sys.executable, str(target / organ.get("entry", "offline_brainstem.py"))],
            cwd=str(target), env=env, stdout=log, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, **kw)
        log.close()
        (target / STATE_FILE).write_text(json.dumps({
            "pid": proc.pid, "port": port, "model": model,
            "organ": organ.get("name"), "version": organ.get("version"),
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }), encoding="utf-8")

        deadline = time.time() + 30
        while time.time() < deadline:
            if proc.poll() is not None:
                lines = (target / "runner.log").read_text(encoding="utf-8", errors="replace")
                why = [l for l in lines.splitlines() if l.startswith("[offline]")]
                shutil.rmtree(target, ignore_errors=True)
                return ("Offline mode did not start. "
                        + (why[-1][len("[offline] "):] if why else "See the runner log."))
            try:
                h = self._health(port)
                return (f"Offline mode is on. Chat at http://127.0.0.1:{port} "
                        f"(model {h.get('model')}). Your normal Brainstem keeps running.")
            except Exception:
                time.sleep(0.3)
        return f"Offline mode is starting at http://127.0.0.1:{port}; ask for status in a moment."

    # ── off ──────────────────────────────────────────────────────────────────

    def _off(self):
        st = self._state()
        target = _organ_dir()
        if not st and not target.exists():
            return "Offline mode is already off."
        pid = (st or {}).get("pid")
        stopped = ""
        if pid and _alive(pid) and _is_our_runner(pid):
            os.kill(pid, signal.SIGTERM)
            for _ in range(50):
                if not _alive(pid):
                    break
                time.sleep(0.1)
            else:
                os.kill(pid, getattr(signal, "SIGKILL", signal.SIGTERM))
            stopped = f" The runner (process {pid}) stopped."
        shutil.rmtree(target, ignore_errors=True)
        return ("Offline mode is off." + stopped
                + " Its files were removed; your Brainstem is back to its normal setup.")


if __name__ == "__main__":
    print(OfflineModeAgent().perform(action="status"))
