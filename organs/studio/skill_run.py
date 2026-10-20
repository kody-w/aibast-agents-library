"""
run.py: run this skill's agent.py, unchanged, inside the Copilot Studio skill sandbox.

agent.py is a Brainstem agent copied byte for byte. This file stands in for what
the Brainstem gives it: BasicAgent, and the storage helper behind
utils.azure_file_storage. Whatever routes.json sends to a workflow tool (web calls,
saved memory) is answered from the input instead of the network or the disk:

    python scripts/run.py '{"args": {...}, "responses": {...}, "storage": {...}}'
    python scripts/run.py --input input.json

It prints one JSON object:
    {"status": "needs", "call": [{"tool", "inputs", "into", "key"}]}
        call the tool with those inputs, put its answer under input[into][key],
        and run again with the same args
    {"status": "done", "result": ..., "save": [{"tool", "inputs"}]}
        answer from result; call each save tool with its inputs
    {"status": "blocked", "message": ...}
"""

import hashlib
import importlib.util
import json
import os
import re
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))


class BasicAgent:
    """The Brainstem's BasicAgent, as agents see it."""

    def __init__(self, name=None, metadata=None):
        if name is not None:
            self.name = name
        elif not hasattr(self, "name"):
            self.name = "BasicAgent"
        if metadata is not None:
            self.metadata = metadata
        elif not hasattr(self, "metadata"):
            self.metadata = {"name": self.name, "description": "",
                             "parameters": {"type": "object", "properties": {}, "required": []}}

    def perform(self, **kwargs):
        return "Not implemented."

    def system_context(self):
        return None


class Need(BaseException):
    """A value only a workflow tool can give. BaseException, so an agent's own
    `except Exception` cannot swallow it and carry on with a wrong answer."""

    def __init__(self, call):
        super().__init__(call["tool"])
        self.call = call


class Blocked(BaseException):
    pass


# ── web calls -> HTTP workflow tools ─────────────────────────────────────────

def _route_pattern(uri):
    parts = re.split(r"(\{[A-Za-z_][A-Za-z0-9_]*\})", uri)
    names = [p[1:-1] for p in parts[1::2]]
    rx = "".join(re.escape(p) if i % 2 == 0 else "([^/?#]+)" for i, p in enumerate(parts))
    return re.compile(rx + r"(?:\?(.*))?$"), names


class Web:
    def __init__(self, routes, responses):
        self.routes = [(r, *_route_pattern(r["uri"])) for r in routes]
        self.responses = responses

    def answer(self, method, url):
        """(status, body bytes) for this call, or Need for the tool that makes it."""
        key = f"{method} {url}"
        if key in self.responses:
            got = self.responses[key]
            if isinstance(got, dict):
                status, body = int(got.get("status") or got.get("statusCode") or 200), got.get("body", "")
            else:
                status, body = 200, got
            if not isinstance(body, str):
                body = json.dumps(body)
            return status, body.encode("utf-8")
        for route, rx, names in self.routes:
            m = rx.match(url)
            if route["method"] == method and m:
                inputs = dict(zip(names, m.groups()[:len(names)]))
                from urllib.parse import parse_qsl
                inputs.update({k: v for k, v in parse_qsl(m.group(len(names) + 1) or "")
                               if k in route.get("queries", [])})
                raise Need({"tool": route["tool"], "inputs": inputs, "into": "responses", "key": key})
        raise Blocked(f"this agent called {method} {url}, and no workflow tool makes that call")


def _patch_web(web):
    import urllib.error
    import urllib.request

    class _Answer:
        def __init__(self, url, status, body):
            self.url, self.status, self._body = url, status, body

        def read(self, *a):
            return self._body

        def getcode(self):
            return self.status

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def urlopen(url, data=None, timeout=None, **kw):
        full = url.full_url if hasattr(url, "full_url") else url
        method = url.get_method() if hasattr(url, "get_method") else ("POST" if data else "GET")
        status, body = web.answer(method, full)
        if status >= 400:
            raise urllib.error.HTTPError(full, status, f"HTTP {status}", {}, None)
        return _Answer(full, status, body)

    urllib.request.urlopen = urlopen
    try:
        import requests
    except ImportError:
        return

    def request(self, method, url, params=None, **kw):
        prepared = requests.models.PreparedRequest()
        prepared.prepare_url(url, params)
        status, body = web.answer(method.upper(), prepared.url)
        r = requests.Response()
        r.status_code, r._content, r.url, r.encoding = status, body, prepared.url, "utf-8"
        return r

    requests.Session.request = request


# ── saved memory -> Dataverse workflow tools ─────────────────────────────────

class Store:
    """The documents an agent reads and writes, keyed by the path the Brainstem's
    local storage would use. Routed: reads ask the read tool, writes become saves.
    Not routed: they live in files under ./brainstem_data (this conversation only)."""

    def __init__(self, route, documents):
        self.route, self.documents, self.saves = route, documents, {}

    def read(self, key):
        if key in self.saves:
            return self.saves[key]
        if self.route is None:
            path = os.path.join("brainstem_data", key)
            return open(path, encoding="utf-8").read() if os.path.exists(path) else None
        if key not in self.documents:
            raise Need({"tool": self.route["read"], "inputs": {"key": key}, "into": "storage", "key": key})
        return self.documents[key]

    def write(self, key, text):
        self.saves[key] = text
        if self.route is None:
            path = os.path.join("brainstem_data", key)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)

    def save_calls(self):
        if self.route is None:
            return []
        return [{"tool": self.route["save"], "inputs": {"key": k, "document": v}} for k, v in self.saves.items()]


def _storage_class(store):
    class AzureFileStorageManager:
        DEFAULT_MARKER_GUID = "c0p110t0-aaaa-bbbb-cccc-123456789abc"

        def __init__(self, share_name=None, **kwargs):
            share = str(share_name or "").strip().lower()
            self.share_name = share or None
            self.storage_root = f"shares/{hashlib.sha256(share.encode('utf-8')).hexdigest()}/" if share else ""
            self.shared_memory_path = self.storage_root + "shared_memories"
            self.current_memory_path = self.shared_memory_path
            self.default_file_name = "memory.json"
            self.current_guid = None

        def set_memory_context(self, user_guid=None):
            if user_guid in (None, "", self.DEFAULT_MARKER_GUID):
                self.current_guid = None
                self.current_memory_path = self.shared_memory_path
                return True
            if not isinstance(user_guid, str) or user_guid in (".", "..") or re.search(r'[<>:"/\\|?*\x00-\x1f]', user_guid):
                raise ValueError("user_guid must be a single path component")
            self.current_guid = user_guid
            self.current_memory_path = f"{self.storage_root}memory/{user_guid}"
            return True

        def _key(self, file_path=None):
            if file_path:
                return self.storage_root + str(file_path).lstrip("/")
            if self.current_guid:
                return f"{self.storage_root}memory/{self.current_guid}/user_memory.json"
            return f"{self.shared_memory_path}/{self.default_file_name}"

        def read_json(self, file_path=None):
            text = store.read(self._key(file_path))
            try:
                return json.loads(text) if text else {}
            except ValueError:
                return {}

        def write_json(self, data, file_path=None):
            store.write(self._key(file_path), json.dumps(data, indent=2, default=str))
            return True

        def update_json(self, update_fn, file_path=None):
            key = self._key(file_path)
            text = store.read(key)
            updated = update_fn(json.loads(text) if text else {})
            store.write(key, json.dumps(updated, indent=2, default=str))
            return updated

        def read_file(self, file_path):
            return store.read(self._key(file_path))

        def write_file(self, file_path, content):
            store.write(self._key(file_path), content)
            return True

        def file_exists(self, file_path):
            return store.read(self._key(file_path)) is not None

        def list_files(self, directory=""):
            raise Blocked("listing saved files is not translated to a workflow tool")

        def delete_file(self, file_path):
            raise Blocked("deleting saved files is not translated to a workflow tool")

    return AzureFileStorageManager


def _install_shims(store):
    def module(name, **attrs):
        m = types.ModuleType(name)
        m.__path__ = []
        m.__dict__.update(attrs)
        sys.modules[name] = m
        return m

    ba = module("agents.basic_agent", BasicAgent=BasicAgent)
    module("agents", basic_agent=ba)
    module("basic_agent", BasicAgent=BasicAgent)
    module("openrappter.agents.basic_agent", BasicAgent=BasicAgent)
    manager = _storage_class(store)
    afs = module("utils.azure_file_storage", AzureFileStorageManager=manager)
    ds = module("utils.dynamics_storage", DynamicsStorageManager=manager)
    sf = module("utils.storage_factory", get_storage_manager=lambda: manager())
    module("utils", azure_file_storage=afs, dynamics_storage=ds, storage_factory=sf)


def _read_input(argv):
    if len(argv) >= 2 and argv[0] == "--input":
        with open(argv[1], encoding="utf-8") as f:
            return json.load(f)
    if argv:
        return json.loads(argv[0])
    text = sys.stdin.read()
    return json.loads(text) if text.strip() else {}


def run(payload, routes):
    store = Store(routes.get("storage"), dict(payload.get("storage") or {}))
    _install_shims(store)
    if "http" in routes:
        _patch_web(Web(routes["http"], dict(payload.get("responses") or {})))
    spec = importlib.util.spec_from_file_location("agent", os.path.join(HERE, "agent.py"))
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        result = getattr(mod, routes["class"])().perform(**(payload.get("args") or {}))
    except Need as n:
        return {"status": "needs", "call": [n.call]}
    except Blocked as b:
        return {"status": "blocked", "message": str(b)}
    return {"status": "done", "result": result, "save": store.save_calls()}


def main(argv):
    with open(os.path.join(HERE, "routes.json"), encoding="utf-8") as f:
        routes = json.load(f)
    print(json.dumps(run(_read_input(argv), routes), ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
