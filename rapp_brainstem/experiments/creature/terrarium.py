#!/usr/bin/env python3
"""Serve a local view of creature evidence beside an unchanged Brainstem.

This is a file reader and a same-origin proxy, not another agent runtime.
Every action goes through the original Brainstem POST /chat.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import shlex
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


MAX_BODY = 2 * 1024 * 1024
MAX_RESPONSE = 16 * 1024 * 1024


class TerrariumError(ValueError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def local_request(port, path, payload=None, timeout=180):
    body = None if payload is None else json.dumps(payload, allow_nan=False).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE + 1)
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_RESPONSE + 1)
        status = exc.code
    if len(raw) > MAX_RESPONSE:
        raise TerrariumError("Brainstem response exceeded the local view's size limit.")
    return status, raw


def read_config(root):
    root = Path(root).expanduser().resolve()
    path = root / "terrarium.json"
    if not path.is_file() or path.is_symlink():
        raise TerrariumError(f"No terrarium installation at {root}; run its installer first.")
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema") != "rapp-creature/install/1":
        raise TerrariumError("Unknown terrarium installation schema.")
    for key in ("brainstem_port", "ui_port"):
        value = config.get(key)
        if type(value) is not int or not 1024 <= value <= 65535:
            raise TerrariumError(f"Invalid {key}.")
    if config["brainstem_port"] == config["ui_port"]:
        raise TerrariumError("Brainstem and the evidence view need different ports.")
    return root, config


def load_manager(root, config):
    runtime = root / "bootstrap-home" / ".brainstem" / "src" / "rapp_brainstem"
    sys.path.insert(0, str(runtime))
    path = root / "payload" / "creature_twin_agent.py"
    spec = importlib.util.spec_from_file_location("terrarium_file_reader", path)
    if spec is None or spec.loader is None:
        raise TerrariumError("Cannot load the installed creature file reader.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bounded_file(path, root, maximum=MAX_RESPONSE):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(Path(root).resolve()):
        raise TerrariumError("The requested evidence file is unavailable.")
    if path.stat().st_size > maximum:
        raise TerrariumError("The requested evidence file exceeds the size limit.")
    return path.read_bytes()


def make_handler(root, config, manager):
    port = config["brainstem_port"]
    ui_port = config["ui_port"]
    allowed_hosts = {f"127.0.0.1:{ui_port}", f"localhost:{ui_port}"}
    allowed_origins = {f"http://{host}" for host in allowed_hosts}

    class Handler(BaseHTTPRequestHandler):
        server_version = "BrainstemTerrarium/0.1"

        def log_message(self, format_string, *args):
            return

        def _permitted(self):
            if self.headers.get("Host") not in allowed_hosts:
                self._json(403, {"error": "This evidence view accepts only its own localhost host."})
                return False
            origin = self.headers.get("Origin")
            if origin is not None and origin not in allowed_origins:
                self._json(403, {"error": "Cross-origin requests are not allowed."})
                return False
            return True

        def _send(self, status, body, content_type, filename=None):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            if filename:
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status, value):
            self._send(status, json.dumps(value, allow_nan=False).encode("utf-8"), "application/json; charset=utf-8")

        def do_GET(self):
            if not self._permitted():
                return
            path = urllib.parse.urlsplit(self.path).path
            try:
                if path == "/":
                    self._send(200, bounded_file(root / "payload" / "index.html", root), "text/html; charset=utf-8")
                elif path == "/brainstem":
                    self.send_response(303)
                    self.send_header("Location", f"http://127.0.0.1:{port}")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                elif path == "/health":
                    status, raw = local_request(port, "/health", timeout=8)
                    self._send(status, raw, "application/json; charset=utf-8")
                elif path == "/api/terrarium":
                    self._catalog()
                elif path.startswith("/api/egg/"):
                    creature_id = manager.checked_id(path.removeprefix("/api/egg/"))
                    egg = root / "data" / creature_id / "public" / "egg.json"
                    self._send(200, bounded_file(egg, root / "data"), "application/json", f"{creature_id}.egg.json")
                elif path.startswith("/api/source/"):
                    creature_id = manager.checked_id(path.removeprefix("/api/source/"))
                    source = root / "agents" / f"{creature_id}_agent.py"
                    if not source.exists():
                        source = root / "dormant" / source.name
                    profile, _ = manager.source_profile(manager.read_source(source))
                    if not profile or profile["id"] != creature_id:
                        raise TerrariumError("Agent file does not match the requested identity.")
                    self._send(200, bounded_file(source, root), "text/x-python; charset=utf-8", source.name)
                else:
                    self._json(404, {"error": "No such terrarium resource."})
            except (TerrariumError, manager.CreatureTwinError, OSError, UnicodeError, json.JSONDecodeError) as exc:
                self._json(400, {"error": str(exc)})

        def _catalog(self):
            try:
                status, raw = local_request(port, "/health", timeout=8)
                health = json.loads(raw)
                if status != 200 or not isinstance(health, dict):
                    health = {"status": "unavailable", "error": f"Brainstem health returned HTTP {status}."}
            except (OSError, ValueError) as exc:
                health = {"status": "unavailable", "error": str(exc)}
            catalog = manager.inventory(root / "agents", root / "dormant", root / "data", health.get("agents", []))
            profile, _ = manager.source_profile(manager.read_source(root / "payload" / "genome_creature_agent.py"))
            if profile is None:
                raise TerrariumError("The installed creature template has no profile.")
            response = {
                "status": "ok",
                "brainstem": health,
                **catalog,
                "agents_path": str(root / "agents"),
                "dormant_path": str(root / "dormant"),
                "capability_options": profile["capabilities"],
                "limits": {"max_creatures": manager.MAX_CREATURES},
                "resume_command": (
                    f"{shlex.quote(str(root / 'bootstrap-home' / '.brainstem' / 'venv' / 'bin' / 'python'))} "
                    f"{shlex.quote(str(root / 'payload' / 'setup.py'))} "
                    "--root ~/.brainstem-creature-resumed --port 7083 --ui-port 7084 "
                    "--egg /path/to/creature.egg.json"
                ),
            }
            self._json(200, response)

        def do_POST(self):
            if not self._permitted():
                return
            if urllib.parse.urlsplit(self.path).path != "/chat":
                self._json(404, {"error": "All creature actions use the native Brainstem /chat endpoint."})
                return
            if self.headers.get("Transfer-Encoding"):
                self._json(400, {"error": "Use a Content-Length JSON request."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._json(400, {"error": "Invalid Content-Length."})
                return
            if length <= 0 or length > MAX_BODY:
                self._json(413, {"error": "Chat request is empty or exceeds the local size limit."})
                return
            try:
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict) or not isinstance(body.get("user_input"), str) or not body["user_input"].strip():
                    raise TerrariumError("user_input must be a nonempty string.")
                allowed = {"user_input", "session_id", "conversation_history"}
                if set(body) - allowed:
                    raise TerrariumError("Only native chat input, session id and history are accepted.")
            except (ValueError, UnicodeError, RecursionError) as exc:
                self._json(400, {"error": str(exc)})
                return
            try:
                status, raw = local_request(port, "/chat", payload=body)
                self._send(status, raw, "application/json; charset=utf-8")
            except (TerrariumError, OSError) as exc:
                self._json(502, {"error": f"Brainstem chat failed: {exc}"})

    return Handler


def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError as exc:
            raise TerrariumError(f"Local port {port} is already in use; no existing process was stopped.") from exc


def apply_auth_reference(environment, reference, independent=False):
    if independent or environment.get("GITHUB_TOKEN") or not reference:
        return
    path = Path(reference)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 8192:
        raise TerrariumError("Existing Brainstem login reference is unavailable; use --independent-auth to sign in separately.")
    raw = path.read_text(encoding="utf-8").strip()
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
        except (ValueError, RecursionError):
            raise TerrariumError("Existing Brainstem login is not valid credential JSON.") from None
        token = data.get("access_token") if isinstance(data, dict) else None
    else:
        token = raw
    if not isinstance(token, str) or not token.strip() or len(token) > 4096:
        raise TerrariumError("Existing Brainstem login has no usable access token.")
    token = token.strip()
    if not token.isascii() or any(character.isspace() for character in token):
        raise TerrariumError("Existing Brainstem login has an invalid access-token format.")
    environment["GITHUB_TOKEN"] = token


def wait_for_brainstem(port, process, timeout=100):
    deadline = time.monotonic() + timeout
    last_error = "not listening yet"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise TerrariumError("The isolated Brainstem exited; inspect its local logs/brainstem.log.")
        try:
            status, raw = local_request(port, "/health", timeout=3)
            health = json.loads(raw)
            if status == 200 and health.get("status") in {"ok", "unauthenticated"}:
                return health
            last_error = f"HTTP {status}: {health.get('status', 'invalid health')}"
        except (OSError, ValueError) as exc:
            last_error = str(exc)
        time.sleep(0.4)
    raise TerrariumError(f"The isolated Brainstem did not become responsive: {last_error}")


def serve(root, config, independent_auth=False):
    runtime = root / "bootstrap-home" / ".brainstem" / "src" / "rapp_brainstem"
    python = root / "bootstrap-home" / ".brainstem" / "venv" / "bin" / "python"
    kernel = runtime / "brainstem.py"
    if hashlib.sha256(kernel.read_bytes()).hexdigest() != config["kernel_sha256"]:
        raise TerrariumError("Brainstem core differs from the installed official source; refusing to silently run a different core.")
    check_port(config["brainstem_port"])
    check_port(config["ui_port"])
    manager = load_manager(root, config)
    handler = make_handler(root, config, manager)
    server = ThreadingHTTPServer(("127.0.0.1", config["ui_port"]), handler)
    server.daemon_threads = True
    environment = os.environ.copy()
    environment.update({
        "HOME": str(root / "bootstrap-home"),
        "GH_CONFIG_DIR": config["gh_config_dir"],
        "RAPP_CREATURE_HOME": str(root),
        "RAPP_CREATURE_DATA_DIR": str(root / "data"),
        "RAPP_CREATURE_TEMPLATE": str(root / "payload" / "genome_creature_agent.py"),
        "AGENTS_PATH": str(root / "agents"),
        "SOUL_PATH": str(root / "creature-soul.md"),
        "PORT": str(config["brainstem_port"]),
        "BRAINSTEM_LAN_MODE": "false",
        "PYTHONUNBUFFERED": "1",
    })
    environment.pop("BRAINSTEM_ALLOWED_HOSTS", None)
    apply_auth_reference(environment, config.get("auth_reference"), independent_auth)
    logs = root / "logs"
    logs.mkdir(mode=0o700, exist_ok=True)
    process = None
    try:
        with (logs / "brainstem.log").open("ab") as log:
            os.chmod(log.name, 0o600)
            process = subprocess.Popen([str(python), str(kernel)], cwd=runtime, env=environment, stdout=log, stderr=subprocess.STDOUT)
            health = wait_for_brainstem(config["brainstem_port"], process)
            print(f"RAPP Brainstem terrarium: http://127.0.0.1:{config['ui_port']}", flush=True)
            print(f"Brainstem: http://127.0.0.1:{config['brainstem_port']} ({health['status']})", flush=True)
            print(f"Agent files: {root / 'agents'}", flush=True)
            print("Only recorded creature actions are animated. Ctrl-C stops this twin, not your original Brainstem.", flush=True)
            if health["status"] != "ok":
                print(f"Authentication required at http://127.0.0.1:{config['brainstem_port']}/login", flush=True)
            if config.get("resume_egg") and health["status"] == "ok":
                resume_pending(root, config)
            server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("\nStopping this isolated twin; all creature history is preserved.", flush=True)
    finally:
        server.server_close()
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def resume_pending(root, config):
    path = root / "pending.egg.json"
    if not path.exists():
        return
    agent_name = config["resume_agent_name"]
    prompt = (
        f"Call {agent_name} exactly once with action='resume' and egg_id='{config['resume_egg_id']}'. "
        "The installer has staged the complete egg in this creature's private inbox. "
        "Do not supply egg_json, hatch, evolve, alter or reconstruct the egg. Report the actual tool result."
    )
    status, response = local_request(config["brainstem_port"], "/chat", {"user_input": prompt})
    if status != 200:
        raise TerrariumError(f"Egg resume failed with HTTP {status}; the pending egg is preserved.")
    result = json.loads(response)
    print(result.get("response", json.dumps(result)), flush=True)
    snapshot = root / "data" / config["resume_id"] / "public" / "snapshot.json"
    if not snapshot.exists():
        raise TerrariumError("Brainstem returned without producing a resumed creature; pending egg is preserved.")
    state = json.loads(snapshot.read_text(encoding="utf-8"))
    if not state.get("resumed_from"):
        raise TerrariumError("The creature did not report verified egg provenance; pending egg is preserved.")
    if state.get("generation") != config["resume_generation"] or state.get("genome_sha256") != config["resume_genome_sha256"]:
        raise TerrariumError("Resumed genome or generation differs from the supplied egg; pending egg is preserved.")
    path.rename(root / "resumed.egg.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["start", "status", "chat"], nargs="?", default="start")
    parser.add_argument("--root", default=str(Path.home() / ".brainstem-creature"))
    parser.add_argument("--message", help="Plain English request sent through the native Brainstem /chat.")
    parser.add_argument("--independent-auth", action="store_true", help="Do not reuse the original Brainstem login; sign in on this twin.")
    args = parser.parse_args()
    try:
        root, config = read_config(args.root)
        if args.command == "start":
            def stop(signum, frame):
                raise KeyboardInterrupt
            signal.signal(signal.SIGTERM, stop)
            serve(root, config, args.independent_auth)
        elif args.command == "status":
            status, raw = local_request(config["brainstem_port"], "/health", timeout=5)
            print(raw.decode("utf-8"))
            if status != 200 or json.loads(raw).get("status") != "ok":
                return 1
        else:
            if not args.message:
                raise TerrariumError("chat requires --message.")
            status, raw = local_request(config["brainstem_port"], "/chat", {"user_input": args.message})
            print(raw.decode("utf-8"))
            if status != 200 or "error" in json.loads(raw):
                return 1
        return 0
    except (TerrariumError, OSError, ValueError) as exc:
        print(f"Terrarium: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
