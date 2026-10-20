"""
Offline runner — the Brainstem's chat loop on a local model, beside the kernel.

An organ: the OfflineMode agent fetches this file from the AIBAST registry,
checks its SHA-256, writes it to ~/.brainstem/organs/offline/ and starts it as
its own process. The kernel (brainstem.py) is imported read-only for its agent
loader, soul loader, tool runner and request guards; it is never edited and
keeps running on its own port the whole time.

    BRAINSTEM_SRC=~/.brainstem/src/rapp_brainstem python offline_brainstem.py

POST /chat    { user_input, conversation_history?, session_id? }  -> { response, ... }
GET  /health  { status, mode: "offline", model, ... }

Env:
    OFFLINE_BASE_URL  OpenAI-compatible local server (default http://127.0.0.1:11434/v1, Ollama)
    OFFLINE_MODEL     model id (default: the first model the server lists)
    OFFLINE_PORT      port to serve on (default 7072); always bound to 127.0.0.1
"""

import os
import sys
import uuid
import ipaddress
from urllib.parse import urlsplit

__manifest__ = {
    "schema": "rapp-organ/1.0",
    "name": "@aibast-agents-library/offline-runner",
    "version": "1.0.0",
    "display_name": "Offline Runner",
    "description": (
        "Runs the Brainstem's agents and soul on a model on this computer "
        "(Ollama or Foundry Local) on 127.0.0.1:7072, beside the unchanged kernel."
    ),
    "author": "AIBAST",
    "tags": ["offline", "local-model", "ollama", "organ"],
    "category": "general",
    "entry": "offline_brainstem.py",
    "switch_agent": "@aibast-agents-library/offline-mode",
}

BIND_HOST = "127.0.0.1"
DEFAULT_BASE_URL = "http://127.0.0.1:11434/v1"
SWITCH_AGENT = "OfflineMode"  # never offered to the local model: it would switch itself off

BASE_URL = (os.getenv("OFFLINE_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
try:
    PORT = int((os.getenv("OFFLINE_PORT") or "7072").strip())
except ValueError:
    PORT = 7072
MODEL = (os.getenv("OFFLINE_MODEL") or "").strip()
TIMEOUT = 300


class OfflineError(RuntimeError):
    """A plain-words problem the person can fix (no model server, no model)."""


def _kernel_dir():
    src = os.getenv("BRAINSTEM_SRC") or os.path.join(
        os.path.expanduser("~"), ".brainstem", "src", "rapp_brainstem")
    return os.path.abspath(src)


def _import_kernel():
    src = _kernel_dir()
    if not os.path.isfile(os.path.join(src, "brainstem.py")):
        raise OfflineError(f"No Brainstem found at {src}. Install the Brainstem first.")
    if src not in sys.path:
        sys.path.insert(0, src)
    os.chdir(src)
    import brainstem  # read-only reuse: loaders, tool runner, guards
    return brainstem


def _is_loopback_url(url):
    host = (urlsplit(url).hostname or "").lower()
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _session():
    import requests
    s = requests.Session()
    s.trust_env = False  # no proxies: the model server is on this computer
    return s


def _unreachable():
    return OfflineError(
        f"No local model server is answering at {BASE_URL}. Start Ollama "
        "(open the Ollama app, or run: ollama serve), then try again. "
        "Offline mode never falls back to the cloud."
    )


def list_local_models():
    import requests
    try:
        r = _session().get(f"{BASE_URL}/models", timeout=5)
        r.raise_for_status()
        return [m.get("id") for m in r.json().get("data", []) if m.get("id")]
    except (requests.RequestException, ValueError):
        raise _unreachable()


def resolve_model():
    """Pick OFFLINE_MODEL, or the first model the local server lists."""
    if not _is_loopback_url(BASE_URL):
        raise OfflineError(
            f"OFFLINE_BASE_URL must point at this computer (localhost or 127.0.0.1); got {BASE_URL}.")
    models = list_local_models()
    if not models:
        raise OfflineError("The local model server has no models yet. Run: ollama pull qwen3:4b")
    if MODEL and MODEL not in models:
        raise OfflineError(f"The model '{MODEL}' is not on this computer. Run: ollama pull {MODEL}")
    return MODEL or models[0]


def call_local(model, messages, tools=None):
    import requests
    body = {"model": model, "messages": messages, "stream": False}
    if tools:
        body["tools"] = tools
    try:
        r = _session().post(f"{BASE_URL}/chat/completions", json=body, timeout=TIMEOUT)
    except requests.RequestException:
        raise _unreachable()
    if r.status_code >= 400:
        raise OfflineError(f"The local model answered {r.status_code}: {r.text[:200]}")
    return r.json()


def create_app(kernel, model):
    from flask import Flask, request, jsonify, send_from_directory

    app = Flask(__name__, static_folder=None)
    # The kernel's own Host and cross-origin guards, unchanged.
    app.before_request(kernel._reject_untrusted_host)
    app.before_request(kernel._reject_cross_origin_unsafe_request)
    state = {"model": model}

    def _agents():
        agents = kernel.load_agents()
        agents.pop(SWITCH_AGENT, None)
        return agents

    @app.route("/", methods=["GET"])
    def index():
        return send_from_directory(kernel._BASE_DIR, "index.html")

    @app.route("/health", methods=["GET"])
    @kernel._require_secret
    def health():
        try:
            agents = list(_agents().keys())
        except Exception:
            agents = []
        try:
            list_local_models()
            server = "reachable"
        except OfflineError:
            server = "unreachable"
        return jsonify({
            "status": "ok",
            "mode": "offline",
            "model": state["model"],
            "model_server": server,
            "base_url": BASE_URL,
            "version": kernel.VERSION,
            "soul": kernel.SOUL_PATH if os.path.exists(kernel.SOUL_PATH) else "missing",
            "agents": agents,
            "brainstem_dir": kernel._BASE_DIR,
        })

    @app.route("/version", methods=["GET"])
    def version():
        return jsonify({"version": kernel.VERSION, "mode": "offline"})

    @app.route("/models", methods=["GET"])
    @kernel._require_secret
    def models():
        try:
            ids = list_local_models()
        except OfflineError:
            ids = [state["model"]]
        return jsonify({"models": [{"id": m, "name": m} for m in ids], "current": state["model"]})

    @app.route("/models/set", methods=["POST"])
    @kernel._require_secret
    def models_set():
        data = request.get_json(force=True, silent=True) or {}
        wanted = data.get("model")
        try:
            ids = list_local_models()
        except OfflineError as e:
            return jsonify({"error": str(e)}), 503
        if wanted in ids:
            state["model"] = wanted
        return jsonify({"status": "ok", "model": state["model"]})

    app.add_url_rule("/agents", "agents", kernel.list_agents_files, methods=["GET"])

    @app.route("/chat", methods=["POST"])
    @kernel._require_secret
    def chat():
        data = request.get_json(force=True, silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "Request body must be a JSON object"}), 400
        user_input = data.get("user_input", "")
        if not isinstance(user_input, str) or not user_input.strip():
            return jsonify({"error": "user_input is required"}), 400
        history, history_error = kernel._validate_conversation_history(
            data.get("conversation_history", []))
        if history_error:
            return jsonify({"error": history_error}), 400
        session_id = data.get("session_id") or str(uuid.uuid4())
        model_id = state["model"]

        try:
            soul = kernel.load_soul()
            agents = _agents()
            tools = []
            for a in agents.values():
                try:
                    tools.append(a.to_tool())
                except Exception as e:
                    print(f"[offline] Skipping agent with bad metadata ({getattr(a, 'name', '?')}): {e}")
            extra = ""
            for a in agents.values():
                try:
                    ctx = a.system_context()
                    if ctx:
                        extra += "\n" + ctx
                except Exception as e:
                    print(f"[offline] system_context failed for {a.name}: {e}")

            messages = [{"role": "system", "content": soul + extra}]
            messages += [m for m in history if m.get("role") in ("user", "assistant", "tool")]
            messages.append({"role": "user", "content": user_input.strip()})

            all_logs = []
            msg = {}
            for _ in range(3):  # same tool-round budget as the kernel
                msg = call_local(model_id, messages, tools or None)["choices"][0]["message"]
                messages.append(msg)
                if not msg.get("tool_calls"):
                    break
                results, logs = kernel.run_tool_calls(msg["tool_calls"], agents, session_id=session_id)
                all_logs.extend(logs)
                messages.extend(results)

            reply = msg.get("content") or ""
            if msg.get("tool_calls"):
                final = call_local(model_id, messages, None)["choices"][0]["message"]
                reply = (final.get("content") or "").strip() or (
                    "I couldn't finish that within the available tool steps. "
                    "Try rephrasing, or breaking it into smaller steps.")
        except OfflineError as e:
            return jsonify({"error": str(e), "mode": "offline", "model": model_id}), 503

        return jsonify({
            "response": reply,
            "session_id": session_id,
            "agent_logs": "\n".join(all_logs),
            "voice_mode": False,
            "model": model_id,
            "requested_model": model_id,
            "mode": "offline",
        })

    return app


def main():
    try:
        kernel = _import_kernel()
        model = resolve_model()
    except OfflineError as e:
        print(f"[offline] {e}", flush=True)
        return 2
    from werkzeug.serving import make_server
    app = create_app(kernel, model)
    try:
        server = make_server(BIND_HOST, PORT, app, threaded=True)
    except OSError:
        print(f"[offline] Port {PORT} on {BIND_HOST} is already in use. "
              "Set OFFLINE_PORT to a free port, or stop what is using it.", flush=True)
        return 2
    host, port = server.server_address[:2]
    print(f"[offline] Offline Brainstem listening on {host}:{port} (model {model}, server {BASE_URL})",
          flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
