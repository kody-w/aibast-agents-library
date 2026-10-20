"""
Studio organ — turn a Brainstem's agents into a Copilot Studio workspace, by one rule.

An organ: the StudioOrgan agent fetches this folder from the AIBAST registry,
checks every file's SHA-256 and writes it to ~/.brainstem/organs/studio/. Nothing
runs in the background; the kernel is never touched.

The rule (sandbox-profile.json is the only input that decides):
  1. read each agent.py without running it and list what it NEEDS (web calls,
     saved memory, subprocesses, libraries, files it writes, environment values);
  2. whatever the skill sandbox can do stays in a skinny skill: SKILL.md says when
     to use it, scripts/agent.py is the original byte for byte, scripts/run.py
     stands in for the Brainstem so perform() runs;
  3. each need the sandbox cannot meet becomes a workflow tool (an agent-called
     flow) that run.py routes to; a need with no workflow-tool route holds the
     agent back, in plain words.

    python studio_organ.py plan  <agents_dir> [--profile p.json] [--json]
    python studio_organ.py build <agents_dir> --out <workspace> [--soul soul.md] [--name "My Copilot"]
"""

import ast
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

__manifest__ = {
    "schema": "rapp-organ/1.0",
    "name": "@aibast-agents-library/studio-organ",
    "version": "1.0.0",
    "display_name": "Send to Copilot Studio",
    "description": (
        "Turns a Brainstem's agents into a Copilot Studio workspace: skinny skills that carry each "
        "agent.py unchanged, plus workflow tools for what the skill sandbox cannot do."
    ),
    "author": "AIBAST",
    "tags": ["copilot-studio", "skills", "workflow-tools", "organ"],
    "category": "general",
    "entry": "studio_organ.py",
    "switch_agent": "@aibast-agents-library/send-to-studio",
}

HERE = Path(__file__).resolve().parent
PROFILE = HERE / "sandbox-profile.json"
RUN_PY = HERE / "skill_run.py"

PROVIDED = {"agents", "basic_agent", "openrappter", "utils", "local_storage"}  # run.py stands in for these
NETWORK = {"requests", "urllib.request", "urllib3", "httpx", "aiohttp", "http.client", "socket",
           "pyodide.http", "websocket", "websockets", "ftplib", "smtplib"}
ROUTED_LIBS = {"urllib.request", "requests"}  # run.py answers these from workflow tools
BROWSER_ONLY = {"pyodide", "js"}
STORAGE_MAKERS = {"AzureFileStorageManager", "DynamicsStorageManager", "get_storage_manager"}
STORAGE_READS = {"read_json", "read_file", "file_exists"}
STORAGE_WRITES = {"write_json", "write_file", "update_json"}
STORAGE_UNROUTED = {"list_files", "delete_file"}
VERBS = {"get", "post", "put", "patch", "delete", "head"}
SECRET = re.compile(r"KEY|TOKEN|SECRET|PASSWORD|CONNECTION_STRING", re.I)
DATAVERSE = "shared_commondataserviceforapps"
FORMAT_NOTE = ("Spec, not a confirmed Copilot Studio file format: the MCP route reads it and authors the real "
               "workflow with manage_workflows after discover_resources action=describe_actions.")


def load_profile(path=None):
    return json.loads(Path(path or PROFILE).read_text(encoding="utf-8"))


def _sha(data):
    return hashlib.sha256(data).hexdigest()


# ── 1. what an agent needs (static: the file is parsed, never run) ───────────

class _Scan(ast.NodeVisitor):
    def __init__(self, tree):
        self.alias, self.imports, self.optional = {}, set(), set()
        self.consts, self.calls, self.fetchers, self.sessions = {}, [], {}, set()
        self.storage_vars, self.storage_ops, self.shares = set(), set(), set()
        self.subprocess, self.writes, self.env = [], [], set()
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        self.consts[t.id] = node.value.value
        self._try = 0
        self.visit(tree)

    def visit_Try(self, node):
        self._try += 1
        for n in node.body + node.handlers:  # an import here has a fallback
            self.visit(n)
        self._try -= 1
        for n in node.orelse + node.finalbody:
            self.visit(n)

    def _imported(self, module):
        (self.optional if self._try else self.imports).add(module)

    def visit_Import(self, node):
        for a in node.names:
            self._imported(a.name)
            self.alias[a.asname or a.name.split(".")[0]] = a.asname and a.name or a.name.split(".")[0]

    def visit_ImportFrom(self, node):
        mod = node.module or ""
        self._imported(mod)
        for a in node.names:
            full = f"{mod}.{a.name}"
            if full in NETWORK:
                self._imported(full)
            self.alias[a.asname or a.name] = full

    def qual(self, node):
        if isinstance(node, ast.Name):
            return self.alias.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            base = self.qual(node.value)
            return f"{base}.{node.attr}" if base else None
        return None

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call):
            q = self.qual(node.value.func) or ""
            for t in node.targets:
                target = self.qual(t)
                if q.split(".")[-1] in STORAGE_MAKERS:
                    self.storage_vars.add(target)
                    share = next((k.value for k in node.value.keywords if k.arg == "share_name"),
                                 node.value.args[0] if node.value.args else None)
                    self.shares.add(share.value if isinstance(share, ast.Constant) else None)
                if q in ("requests.Session", "requests.session"):
                    self.sessions.add(target)
        self.generic_visit(node)

    def visit_Call(self, node):
        q = self.qual(node.func) or ""
        line = node.lineno
        if q in ("subprocess.run", "subprocess.Popen", "subprocess.call", "subprocess.check_output",
                 "subprocess.check_call", "os.system", "os.popen") or q.startswith(("os.exec", "os.spawn")):
            self.subprocess.append(f"{q} (line {line})")
        elif q in ("open", "io.open") and self._write_mode(node):
            self.writes.append(f"open(..., {self._write_mode(node)!r}) (line {line})")
        elif q.split(".")[-1] in ("write_text", "write_bytes", "makedirs", "mkdir", "rmtree", "unlink") \
                or q in ("os.remove", "os.rename", "os.replace", "shutil.copy", "shutil.copyfile", "shutil.move"):
            self.writes.append(f"{q.split('.')[-1]}() (line {line})")
        elif q in ("os.getenv", "os.environ.get") and node.args and isinstance(node.args[0], ast.Constant):
            self.env.add(node.args[0].value)
        base, _, attr = q.rpartition(".")
        if base in self.storage_vars:
            self.storage_ops.add(attr)
        web = self._web(q, base, attr, node)
        if web:
            self.calls.append(web)
        self.generic_visit(node)

    def visit_Subscript(self, node):
        if self.qual(node.value) == "os.environ" and isinstance(node.slice, ast.Constant):
            self.env.add(node.slice.value)
        self.generic_visit(node)

    @staticmethod
    def _write_mode(node):
        mode = node.args[1] if len(node.args) > 1 else next((k.value for k in node.keywords if k.arg == "mode"), None)
        if isinstance(mode, ast.Constant) and isinstance(mode.value, str) and set(mode.value) & set("wax+"):
            return mode.value
        return None

    def _web(self, q, base, attr, node):
        kw = {k.arg: k.value for k in node.keywords}
        if q == "urllib.request.urlopen":
            method = "POST" if (len(node.args) > 1 or "data" in kw) else "GET"
            return {"lib": "urllib.request", "method": method, "url": node.args[0] if node.args else kw.get("url"),
                    "params": None, "line": node.lineno}
        if q == "pyodide.http.open_url":
            return {"lib": "pyodide.http", "method": "GET", "url": node.args[0] if node.args else None,
                    "params": None, "line": node.lineno}
        if (base == "requests" or base in self.sessions) and attr in VERBS | {"request"}:
            args = list(node.args)
            method = attr.upper()
            if attr == "request":
                m = args.pop(0) if args else kw.get("method")
                method = m.value.upper() if isinstance(m, ast.Constant) else None
            return {"lib": "requests", "method": method, "url": args[0] if args else kw.get("url"),
                    "params": kw.get("params"), "line": node.lineno}
        top = q.split(".")[0]
        if top in ("httpx", "aiohttp", "socket", "urllib3", "websocket", "websockets", "ftplib", "smtplib") or \
                q.startswith("http.client."):
            return {"lib": top if top != "http" else "http.client", "method": None, "url": None,
                    "params": None, "line": node.lineno}
        return None


def _template(node, consts, bound=None):
    """A call's address as a template ("https://x/item/{sid}.json"), or None when it is worked out at run time."""
    bound = bound or {}
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return bound.get(node.id, consts.get(node.id))
    if isinstance(node, ast.JoinedStr):
        out = []
        for i, v in enumerate(node.values):
            if isinstance(v, ast.Constant):
                out.append(str(v.value))
            else:
                inner = v.value
                out.append("{" + (inner.id if isinstance(inner, ast.Name) else f"p{i}") + "}")
        return "".join(out)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _template(node.left, consts, bound), _template(node.right, consts, bound)
        return left + right if left is not None and right is not None else None
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "format":
        base = _template(node.func.value, consts, bound)
        if base is None:
            return None
        names = iter(a.id if isinstance(a, ast.Name) else f"p{i}" for i, a in enumerate(node.args))
        return re.sub(r"\{\}", lambda _m: "{" + next(names, "p") + "}", base)
    return None


def _endpoints(tree, scan):
    """Every web call with the address it makes: direct calls, and calls through a helper
    that passes one of its own parameters as the address (followed a few levels)."""
    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    calls_in = {f: [c for c in scan.calls if f.lineno <= c["line"] <= f.end_lineno] for f in funcs}
    fetchers = {}  # name -> (param index, libs, method)
    for _ in range(3):
        for f in funcs:
            params = [a.arg for a in f.args.args if a.arg != "self"]
            for c in calls_in[f]:
                if isinstance(c["url"], ast.Name) and c["url"].id in params:
                    i = params.index(c["url"].id)
                    prev = fetchers.get(f.name, (i, set(), c["method"]))
                    fetchers[f.name] = (i, prev[1] | {c["lib"]}, prev[2] or c["method"])
            for node in ast.walk(f):
                if isinstance(node, ast.Call):
                    callee = node.func.id if isinstance(node.func, ast.Name) else (
                        node.func.attr if isinstance(node.func, ast.Attribute) else None)
                    if callee in fetchers and callee != f.name:
                        i, libs, method = fetchers[callee]
                        if len(node.args) > i and isinstance(node.args[i], ast.Name) and node.args[i].id in params:
                            prev = fetchers.get(f.name, (params.index(node.args[i].id), set(), method))
                            fetchers[f.name] = (prev[0], prev[1] | libs, prev[2] or method)
    found = []
    for c in scan.calls:
        f = next((f for f in funcs if f.name in fetchers and f.lineno <= c["line"] <= f.end_lineno
                  and isinstance(c["url"], ast.Name) and c["url"].id in [a.arg for a in f.args.args]), None)
        if f is None:
            found.append({"libs": {c["lib"]}, "method": c["method"],
                          "uri": _template(c["url"], scan.consts) if c["url"] is not None else None,
                          "queries": _queries(c["params"]), "line": c["line"]})
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callee = node.func.id if isinstance(node.func, ast.Name) else (
                node.func.attr if isinstance(node.func, ast.Attribute) else None)
            if callee in fetchers and len(node.args) > fetchers[callee][0]:
                arg = node.args[fetchers[callee][0]]
                if isinstance(arg, ast.Name) and any(arg.id in [a.arg for a in f.args.args]
                                                     for f in funcs if f.name in fetchers and
                                                     f.lineno <= node.lineno <= f.end_lineno):
                    continue  # a helper handing its own parameter on: counted at its callers
                i, libs, method = fetchers[callee]
                found.append({"libs": libs, "method": method, "uri": _template(arg, scan.consts),
                              "queries": [], "line": node.lineno})
    unique = {}
    for e in found:
        unique.setdefault((e["method"], e["uri"], tuple(e["queries"])), e)
    return sorted(unique.values(), key=lambda e: e["line"])


def _queries(node):
    if isinstance(node, ast.Dict):
        return [k.value for k in node.keys if isinstance(k, ast.Constant)]
    return []


def _literal(node, names):
    """A metadata literal, reading self.name and module constants."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Dict):
        return {_literal(k, names): _literal(v, names) for k, v in zip(node.keys, node.values)}
    if isinstance(node, (ast.List, ast.Tuple)):
        return [_literal(v, names) for v in node.elts]
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
        return names.get(f"self.{node.attr}")
    if isinstance(node, ast.Name):
        return names.get(node.id)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _literal(node.left, names) + _literal(node.right, names)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_literal(node.operand, names)
    raise ValueError("not a literal")


def _agent_class(tree, consts):
    classes = [c for c in tree.body if isinstance(c, ast.ClassDef)
               and any(isinstance(f, ast.FunctionDef) and f.name == "perform" for f in c.body)]
    if not classes:
        return None
    cls = next((c for c in classes if c.name != "BasicAgent"), classes[0])
    names, meta = dict(consts), None
    for node in ast.walk(cls):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                try:
                    value = _literal(node.value, names)
                except (ValueError, TypeError):
                    continue
                if t.attr == "name" and isinstance(value, str) and "self.name" not in names:
                    names["self.name"] = value
                elif t.attr == "metadata" and isinstance(value, dict) and meta is None:
                    meta = value
    name = names.get("self.name") or cls.name
    meta = meta or {"name": name, "description": "", "parameters": {"type": "object", "properties": {}}}
    return {"class": cls.name, "name": name, "description": meta.get("description", ""),
            "parameters": meta.get("parameters") or {"type": "object", "properties": {}}}


def analyze(path):
    """What one agent.py needs, read from its source."""
    source = Path(path).read_bytes()
    tree = ast.parse(source)
    scan = _Scan(tree)
    agent = _agent_class(tree, scan.consts)
    tops = {m.split(".")[0] for m in scan.imports if m}
    libs = sorted(t for t in tops if t not in sys.stdlib_module_names and t not in PROVIDED)
    optional = sorted({m.split(".")[0] for m in scan.optional if m} - tops - set(sys.stdlib_module_names) - PROVIDED)
    storage = None
    if scan.storage_vars or {m for m in scan.imports if m.startswith(("utils.", "local_storage"))}:
        storage = {"ops": sorted(scan.storage_ops), "shares": sorted({s or "" for s in scan.shares}) or [""]}
    network_mods = sorted(m for m in scan.imports | scan.optional if m in NETWORK or m.split(".")[0] in ("httpx", "aiohttp", "requests"))
    return {"file": Path(path).name, "sha256": _sha(source), "agent": agent,
            "network": {"modules": network_mods, "calls": _endpoints(tree, scan)} if network_mods or scan.calls else None,
            "storage": storage, "subprocess": scan.subprocess, "file_writes": scan.writes,
            "env": sorted(scan.env), "libraries": libs, "optional_libraries": optional}


# ── 2. classify each need against the profile ───────────────────────────────

def skill_name(agent_name):
    words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "-", agent_name)
    return re.sub(r"[^a-z0-9]+", "-", words.lower()).strip("-")[:64] or "agent"


def _tool_name(agent, uri, used):
    segs = [s for s in re.split(r"[/?]", (uri or "").split("://", 1)[-1])[1:] if s and "{" not in s]
    stem = re.sub(r"\.[a-z]+$", "", segs[-1]) if segs else "call"
    base = f"{agent}_{re.sub(r'[^A-Za-z0-9]+', '_', stem).strip('_') or 'call'}"
    name, n = base, 2
    while name in used:
        name, n = f"{base}_{n}", n + 1
    used.add(name)
    return name


def _table(share):
    slug = re.sub(r"[^a-z0-9]+", "", (share or "").lower())
    logical = f"rapp_{slug}share" if slug else "rapp_brainstemmemory"
    return {"logical_name": logical, "entity_set": logical + "s",
            "display_name": f"{share} share" if share else "Brainstem memory",
            "columns": {"key": "rapp_key", "document": "rapp_document", "id": logical + "id"}}


def _cite(profile, section):
    s = profile.get(section) or {}
    return f"{s.get('note', section)} (profile {profile['version']}" + (f", {s['source']})" if s.get("source") else ")")


def plan_agent(path, profile):
    need = analyze(path)
    agent = need["agent"]
    out = {"file": need["file"], "sha256": need["sha256"], "parts": [], "workflow_tools": [],
           "tables": [], "routes": {}}
    if agent is None:
        out.update(agent=None, ready=False)
        out["parts"].append({"need": "an agent class", "goes_to": "held back",
                             "why": "no class with perform() in the file"})
        return out
    name = agent["name"]
    out.update(agent=name, skill=skill_name(name), routes={"class": agent["class"]},
               description=agent["description"], parameters=agent["parameters"])
    parts = out["parts"]
    parts.append({"need": "the agent's Python logic", "goes_to": "skill",
                  "why": f"the sandbox runs Python {profile['python']['version']} (profile {profile['version']})"})
    known = set(profile["libraries"]["known"])
    for lib in need["libraries"]:
        if lib in known:
            parts.append({"need": f"library {lib}", "goes_to": "skill", "why": _cite(profile, "libraries")})
        else:
            parts.append({"need": f"library {lib}", "goes_to": "skill, unconfirmed",
                          "why": f"{lib} is not on the profile's known list; " + _cite(profile, "libraries")})
    for lib in need["optional_libraries"]:
        parts.append({"need": f"optional library {lib}", "goes_to": "skill",
                      "why": "imported inside a try; the agent carries on without it"})

    net = need["network"]
    if net:
        if profile["network"]["outbound"]:
            parts.append({"need": "web calls", "goes_to": "skill", "why": _cite(profile, "network")})
        else:
            used, routes = set(), []
            for call in net["calls"]:
                libs = call["libs"] - {"pyodide.http"}
                what = f"{call['method'] or 'a web call'} {call['uri'] or '(address worked out at run time)'}"
                reason = (f"run.py routes urllib and requests, not {', '.join(sorted(libs)) or 'the browser'}"
                          if not libs & ROUTED_LIBS else
                          "only GET calls become workflow tools (no headers, body or sign-in)"
                          if call["method"] != "GET" else
                          "its address is worked out at run time" if call["uri"] is None else None)
                if reason:
                    parts.append({"need": what, "goes_to": "held back",
                                  "why": f"the sandbox cannot make it ({_cite(profile, 'network')}) and {reason}"})
                    continue
                tool = _tool_name(name, call["uri"], used)
                spec = _http_tool(tool, name, call)
                out["workflow_tools"].append(spec)
                routes.append({"tool": tool, "method": "GET", "uri": call["uri"], "queries": call["queries"]})
                parts.append({"need": what, "goes_to": "workflow tool", "tool": tool,
                              "why": _cite(profile, "network")})
            if not net["calls"]:
                parts.append({"need": f"web access ({', '.join(net['modules'])})", "goes_to": "held back",
                              "why": f"no call this file makes could be read; {_cite(profile, 'network')}"})
            out["routes"]["http"] = routes

    store = need["storage"]
    if store:
        ops = set(store["ops"])
        if profile["persistence"]["across_conversations"]:
            parts.append({"need": "saved memory", "goes_to": "skill", "why": _cite(profile, "persistence")})
        elif ops & STORAGE_UNROUTED:
            parts.append({"need": "saved memory (" + ", ".join(sorted(ops & STORAGE_UNROUTED)) + ")",
                          "goes_to": "held back",
                          "why": f"{_cite(profile, 'persistence')}; listing and deleting have no workflow tool yet"})
        else:
            table = _table(store["shares"][0])
            out["tables"].append(table)
            read = f"{name}_read"
            out["workflow_tools"].append(_dataverse_read(read, name, table))
            parts.append({"need": f"read saved memory ({table['display_name']})", "goes_to": "workflow tool",
                          "tool": read, "why": _cite(profile, "persistence")})
            route = {"read": read, "save": None, "table": table["logical_name"]}
            if ops & STORAGE_WRITES or not ops:
                save = f"{name}_save"
                out["workflow_tools"].append(_dataverse_save(save, name, table))
                route["save"] = save
                parts.append({"need": f"save memory ({table['display_name']})", "goes_to": "workflow tool",
                              "tool": save, "why": _cite(profile, "persistence")})
            out["routes"]["storage"] = route

    for what in need["subprocess"]:
        parts.append({"need": f"run a program: {what}",
                      "goes_to": "skill" if profile["subprocess"]["allowed"] else "held back",
                      "why": _cite(profile, "subprocess")})
    for what in need["file_writes"]:
        ok = profile["created_files"]["allowed"]
        parts.append({"need": f"write a file: {what}", "goes_to": "skill" if ok else "held back",
                      "why": _cite(profile, "created_files")})
    for var in need["env"]:
        secret = bool(SECRET.search(var))
        parts.append({"need": f"setting {var}", "goes_to": "held back" if secret else "skill",
                      "why": _cite(profile, "environment") + (
                          "; a secret is never put in a skill" if secret else "; the skill runs with it unset")})
    out["ready"] = not any(p["goes_to"] == "held back" for p in parts)
    return out


def _trigger(inputs):
    return {"manual": {"type": "Request", "kind": "Skills", "inputs": {"schema": {
        "type": "object", "required": list(inputs),
        "properties": {k: {"title": k, "type": "string", "description": d, "x-ms-dynamically-added": True}
                       for k, d in inputs.items()}}}}}


def _flow(inputs, actions, outputs, last, connections=None):
    actions = dict(actions)
    actions["Respond_to_the_agent"] = {
        "type": "Response", "kind": "Skills", "runAfter": {last: ["Succeeded", "Failed"]},
        "inputs": {"statusCode": 200, "body": outputs,
                   "schema": {"type": "object", "properties": {k: {"type": "string"} for k in outputs}}}}
    return {"properties": {"connectionReferences": connections or {}, "definition": {
        "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {"$connections": {"defaultValue": {}, "type": "Object"},
                       "$authentication": {"defaultValue": {}, "type": "SecureObject"}},
        "triggers": _trigger(inputs), "actions": actions, "outputs": {}}, "templateName": ""},
        "schemaVersion": "1.0.0.0"}


def _tool(name, agent, kind, description, inputs, outputs, definition, **extra):
    return {"schema": "rapp-studio-workflow-tool/1.0", "name": name, "for_agent": agent, "kind": kind,
            "description": description, "trigger": "When an agent calls the flow",
            "respond": "Respond to the agent", "inputs": inputs, "outputs": outputs,
            "definition": definition, "format_confirmed": False, "format_note": FORMAT_NOTE, **extra}


def _http_tool(name, agent, call):
    placeholders = re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", call["uri"])
    inputs = {p: f"The {p} in the address" for p in placeholders}
    inputs.update({q: f"The {q} query value" for q in call["queries"]})
    uri = re.sub(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", r"@{triggerBody()?['\1']}", call["uri"])
    http = {"type": "Http", "runAfter": {}, "inputs": {
        "method": "GET", "uri": uri, "queries": {q: f"@{{triggerBody()?['{q}']}}" for q in call["queries"]}}}
    outputs = {"statusCode": "@{outputs('Call_the_API')?['statusCode']}", "body": "@{body('Call_the_API')}"}
    return _tool(name, agent, "http", f"{agent} reads {call['uri']} (GET) and returns its status and body.",
                 inputs, ["statusCode", "body"], _flow(inputs, {"Call_the_API": http}, outputs, "Call_the_API"),
                 request={"method": "GET", "uri": call["uri"], "queries": call["queries"]})


def _dv(operation, params, after=None):
    return {"type": "OpenApiConnection", "runAfter": {after: ["Succeeded"]} if after else {}, "inputs": {
        "host": {"connectionName": DATAVERSE, "operationId": operation,
                 "apiId": f"/providers/Microsoft.PowerApps/apis/{DATAVERSE}"}, "parameters": params}}


def _connections():
    return {DATAVERSE: {"api": {"name": DATAVERSE}, "runtimeSource": "embedded",
                        "connection": {"connectionReferenceLogicalName": None}}}


def _list_rows(table):
    c = table["columns"]
    return _dv("ListRecords", {"entityName": table["entity_set"], "$select": f"{c['id']},{c['document']}",
                               "$filter": f"{c['key']} eq '@{{replace(triggerBody()?['key'], '''', '''''')}}'",
                               "$top": 1})


def _dataverse_read(name, agent, table):
    rows = "outputs('Find_the_row')?['body/value']"
    outputs = {"found": f"@{{if(empty({rows}), 'false', 'true')}}",
               "document": f"@{{if(empty({rows}), '', first({rows})?['{table['columns']['document']}'])}}"}
    return _tool(name, agent, "dataverse_read",
                 f"{agent} reads one saved document (by key) from the {table['display_name']} table.",
                 {"key": "Which saved document, as run.py names it"}, ["found", "document"],
                 _flow({"key": "Which saved document"}, {"Find_the_row": _list_rows(table)}, outputs,
                       "Find_the_row", _connections()), table=table["logical_name"])


def _dataverse_save(name, agent, table):
    c, rows = table["columns"], "outputs('Find_the_row')?['body/value']"
    item = {f"item/{c['key']}": "@triggerBody()?['key']", f"item/{c['document']}": "@triggerBody()?['document']"}
    actions = {"Find_the_row": _list_rows(table), "Add_or_update": {
        "type": "If", "runAfter": {"Find_the_row": ["Succeeded"]},
        "expression": {"and": [{"equals": [f"@empty({rows})", True]}]},
        "actions": {"Add_a_new_row": _dv("CreateRecord", {"entityName": table["entity_set"], **item})},
        "else": {"actions": {"Update_a_row": _dv("UpdateRecord", {
            "entityName": table["entity_set"], "recordId": f"@first({rows})?['{c['id']}']",
            f"item/{c['document']}": "@triggerBody()?['document']"})}}}}
    return _tool(name, agent, "dataverse_save",
                 f"{agent} saves one document (by key) to the {table['display_name']} table: adds the row, or "
                 "updates it when the key is already there.",
                 {"key": "Which saved document", "document": "The whole document, as text"}, ["saved"],
                 _flow({"key": "Which saved document", "document": "The whole document, as text"}, actions,
                       {"saved": "true"}, "Add_or_update", _connections()), table=table["logical_name"])


def _is_organ_switch(path):
    """An organ's switch agent (its __manifest__ names an organ) stays with the Brainstem."""
    try:
        tree = ast.parse(Path(path).read_bytes())
    except SyntaxError:
        return False
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__manifest__" for t in node.targets):
            try:
                return "organ" in _literal(node.value, {})
            except (ValueError, TypeError):
                return False
    return False


def _defines_an_agent(path):
    """The kernel's rule: a file is an agent only if it defines a class other than BasicAgent itself
    (basic_agent.py loads as no agent, so it never becomes a Copilot Studio skill)."""
    try:
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return True  # let plan_agent report it in plain words
    return any(isinstance(n, ast.ClassDef) and n.name != "BasicAgent" for n in tree.body)


def agent_files(agents_dir, skip=()):
    return [p for p in sorted(Path(agents_dir).glob("*_agent.py"))
            if p.name not in skip and not _is_organ_switch(p) and _defines_an_agent(p)]


def plan(agents_dir, profile=None, skip=()):
    profile = profile or load_profile()
    return {"schema": "rapp-studio-plan/1.0", "profile": {"version": profile["version"], "as_of": profile["as_of"]},
            "agents": [plan_agent(p, profile) for p in agent_files(agents_dir, skip)]}


def plain_words(p):
    lines = [f"Translation plan (sandbox profile {p['profile']['version']}):"]
    for a in p["agents"]:
        if a.get("agent") is None:
            lines.append(f"- {a['file']}: held back, no agent class in it.")
            continue
        tools = [t["name"] for t in a["workflow_tools"]]
        head = f"- {a['agent']} ({a['file']}): skill {a['skill']}" + (
            f" + workflow tools {', '.join(tools)}" if tools else ", skill only") + (
            "" if a["ready"] else ". Held back")
        lines.append(head + ".")
        for part in a["parts"][1:]:
            lines.append(f"    {part['need']} -> {part['goes_to']}"
                         + (f" {part['tool']}" if part.get("tool") else "") + f": {part['why']}")
    return "\n".join(lines)


# ── 3. the workspace the MCP route pushes ────────────────────────────────────

ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def _arg_lines(parameters):
    props, required = parameters.get("properties") or {}, set(parameters.get("required") or [])
    if not props:
        return ["- (none)"]
    out = []
    for k, v in props.items():
        kind = v.get("type", "any") + (f", one of {', '.join(map(str, v['enum']))}" if v.get("enum") else "")
        out.append(f"- `{k}` ({kind}, {'required' if k in required else 'optional'}): {v.get('description', '')}")
    return out


def skill_md(a):
    """SKILL.md (agentskills.io): when to use it and how to run it. Never the agent's code."""
    tools = a["workflow_tools"]
    body = [
        "---",
        f"name: {a['skill']}",
        f"description: {json.dumps((a['description'] or a['agent'])[:1024])}",
        "metadata:",
        f"  source-agent: {a['file']}",
        f"  source-sha256: {a['sha256']}",
        "---",
        "",
        f"# {a['agent']}",
        "",
        f"Use this skill when: {a['description'] or 'the request matches ' + a['agent'] + '.'}",
        "",
        "Run the agent with its inputs as JSON:",
        "",
        "    python scripts/run.py '{\"args\": {...}}'",
        "",
        "Inputs (`args`):",
        *_arg_lines(a["parameters"]),
        "",
    ]
    if tools:
        body += [
            "Some of what this agent does goes through workflow tools ("
            + ", ".join(f"`{t['name']}`" for t in tools) + "), because the sandbox cannot do it. run.py says when:",
            "",
            "- `{\"status\": \"needs\", \"call\": [...]}`: for each call, call the workflow tool named in `tool` "
            "with its `inputs`, then put the answer in the input under `into`, at `key` "
            "(`responses`: `{\"status\": statusCode, \"body\": body}`; `storage`: the `document`, or `null` "
            "when `found` is false), and run run.py again with the same `args`. Repeat until it is done.",
            "- `{\"status\": \"done\", \"result\": ..., \"save\": [...]}`: call each tool in `save` with its "
            "`inputs`, then answer from `result`.",
            "",
        ]
    else:
        body += ["run.py prints `{\"status\": \"done\", \"result\": ...}`: answer from `result`.", ""]
    body += ["`scripts/agent.py` is the original Brainstem agent, unchanged; do not edit it.", ""]
    return "\n".join(body)


def _zip(path, files):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files:
            info = zipfile.ZipInfo(name, ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, data)


def build(agents_dir, out, soul=None, name="Brainstem Copilot", profile=None, skip=()):
    profile = profile or load_profile()
    p = plan(agents_dir, profile, skip)
    out = Path(out)
    shutil.rmtree(out, ignore_errors=True)
    for sub in ("skills", "workflows", "tables"):
        (out / sub).mkdir(parents=True)
    soul_bytes = Path(soul).read_bytes() if soul and Path(soul).is_file() else b"You are a helpful Copilot.\n"
    (out / "instructions.md").write_bytes(soul_bytes)
    run_py = RUN_PY.read_bytes()
    entries, held, tables = [], [], {}
    for a in p["agents"]:
        if not a["ready"]:
            held.append({"file": a["file"], "sha256": a["sha256"], "agent": a.get("agent"),
                         "why": [f"{x['need']}: {x['why']}" for x in a["parts"] if x["goes_to"] == "held back"]})
            continue
        source = (Path(agents_dir) / a["file"]).read_bytes()
        files = [(f"{a['skill']}/SKILL.md", skill_md(a).encode("utf-8")),
                 (f"{a['skill']}/scripts/agent.py", source),
                 (f"{a['skill']}/scripts/run.py", run_py),
                 (f"{a['skill']}/scripts/routes.json", json.dumps(a["routes"], indent=2).encode("utf-8"))]
        zpath = out / "skills" / f"{a['skill']}.zip"
        _zip(zpath, files)
        for t in a["workflow_tools"]:
            (out / "workflows" / f"{t['name']}.json").write_text(json.dumps(t, indent=2), encoding="utf-8")
        for t in a["tables"]:
            tables[t["logical_name"]] = t
        entries.append({"file": a["file"], "sha256": a["sha256"], "agent": a["agent"], "skill": a["skill"],
                        "skill_zip": f"skills/{a['skill']}.zip", "skill_zip_sha256": _sha(zpath.read_bytes()),
                        "workflow_tools": [f"workflows/{t['name']}.json" for t in a["workflow_tools"]]})
    for t in tables.values():
        spec = dict(t, schema="rapp-studio-table/1.0", format_confirmed=False,
                    note="Must exist in the environment before the save/read workflow tools run.")
        (out / "tables" / f"{t['logical_name']}.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    manifest = {"schema": "rapp-studio-workspace/1.0", "profile": p["profile"],
                "copilot": {"name": name, "instructions": "instructions.md",
                            "instructions_sha256": _sha(soul_bytes)},
                "run_py_sha256": _sha(run_py), "agents": entries, "held_back": held,
                "tables": [f"tables/{t}.json" for t in sorted(tables)], "format_note": FORMAT_NOTE}
    (out / "plan.json").write_text(json.dumps(p, indent=2), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def verify_workspace(out):
    """Problems with a workspace, in words; empty means every file matches the manifest."""
    out, problems = Path(out), []
    m = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    if _sha((out / m["copilot"]["instructions"]).read_bytes()) != m["copilot"]["instructions_sha256"]:
        problems.append("instructions.md changed after it was built")
    for a in m["agents"]:
        z = out / a["skill_zip"]
        if not z.is_file() or _sha(z.read_bytes()) != a["skill_zip_sha256"]:
            problems.append(f"{a['skill_zip']} does not match the manifest")
            continue
        with zipfile.ZipFile(z) as zf:
            if _sha(zf.read(f"{a['skill']}/scripts/agent.py")) != a["sha256"]:
                problems.append(f"{a['skill_zip']}: agent.py is not the original {a['file']}")
            if _sha(zf.read(f"{a['skill']}/scripts/run.py")) != m["run_py_sha256"]:
                problems.append(f"{a['skill_zip']}: run.py is not the organ's")
        for w in a["workflow_tools"]:
            if not (out / w).is_file():
                problems.append(f"{w} is missing")
    return problems


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="studio_organ.py")
    ap.add_argument("command", choices=["plan", "build"])
    ap.add_argument("agents_dir")
    ap.add_argument("--profile")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--soul")
    ap.add_argument("--name", default="Brainstem Copilot")
    args = ap.parse_args(argv)
    profile = load_profile(args.profile)
    if args.command == "plan":
        p = plan(args.agents_dir, profile)
        print(json.dumps(p, indent=2) if args.json else plain_words(p))
        return 0
    if not args.out:
        ap.error("build needs --out")
    m = build(args.agents_dir, args.out, args.soul, args.name, profile)
    print(f"Workspace written to {args.out}: {len(m['agents'])} skill(s), "
          f"{sum(len(a['workflow_tools']) for a in m['agents'])} workflow tool(s), {len(m['held_back'])} held back.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
