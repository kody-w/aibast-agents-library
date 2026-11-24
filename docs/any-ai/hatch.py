"""hatch.py: use a Brainstem as your own, with you as its model. No sign-in, no server, no open port.

The Brainstem's real /chat runs, unchanged. Each time it needs the model, it stops and hands you the
question. You answer, it carries on: it runs the agents you asked for and comes back with their output,
until you give the words for the person. Every turn is added to one chat file the person keeps.

    python hatch.py get                         fetch the Brainstem beside this file, every file fingerprint-checked,
                                                and install the few Python packages it needs
    python hatch.py bring <agent name>          add an agent from the AIBAST Agents Library catalog, fingerprint-checked
    python hatch.py tools                       the agents on offer right now (name and description)
    python hatch.py ask "<what the person said>"    start a turn; prints what the model must answer
    python hatch.py answer '<your answer>'      plain words to finish the turn, or JSON to run agents first:
                                                {"tool_calls": [{"function": {"name": "<Agent>", "arguments": {...}}}]}
    python hatch.py chat                        where the chat file is, and which agents have run in it

Set BRAINSTEM_HOME to the folder holding brainstem.py if it is not ./rapp_brainstem or beside this file.
State lives in ./.hatch/ (delete it to start fresh). Up to three rounds of agents a turn, as in any Brainstem.
"""
import contextlib, hashlib, io, json, os, subprocess, sys, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE = Path(os.environ.get("HATCH_STATE", ".hatch"))
WAIT = "\x00hatch-waiting-for-the-model\x00"


SOURCE = os.environ.get("HATCH_SOURCE", "https://raw.githubusercontent.com/microsoft/aibast-agents-library/main")
CATALOG = os.environ.get("HATCH_CATALOG", "https://raw.githubusercontent.com/microsoft/aibast-agents-library/main")
PACKAGES = ["flask", "flask-cors", "requests", "python-dotenv"]


def _fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "brainstem-hatch"}), timeout=60).read()


def get():
    """Fetch the Brainstem into ./rapp_brainstem. The list of files and their fingerprints sits beside this
    file (hatch-manifest.json) or is fetched from the same place; a file that does not match is refused."""
    mf = HERE / "hatch-manifest.json"
    manifest = json.loads(mf.read_text() if mf.exists() else _fetch(f"{SOURCE}/docs/any-ai/hatch-manifest.json"))
    dest, done = Path("rapp_brainstem"), []
    for rel, sha in sorted(manifest["files"].items()):
        target = dest / rel
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == sha:
            done.append(rel)
            continue
        body = _fetch(f"{SOURCE}/rapp_brainstem/{rel}")
        if hashlib.sha256(body).hexdigest() != sha:
            return 1, {"status": "error", "error": f"{rel} does not match its fingerprint; nothing more was fetched"}
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        done.append(rel)
    missing = [p for p in PACKAGES if not _has(p)]
    note = ""
    if missing:
        r = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", *missing], capture_output=True, text=True)
        note = "" if r.returncode == 0 else "could not install: " + ", ".join(missing) + ". " + r.stderr.strip()[-300:]
    return (1 if note else 0), {"status": "error" if note else "ok", "brainstem": str(dest.resolve()),
                                "kernel_version": manifest.get("kernel_version"), "files": len(done), "note": note}


def _has(package):
    import importlib.util
    return importlib.util.find_spec({"flask-cors": "flask_cors", "python-dotenv": "dotenv"}.get(package, package)) is not None


def bring(name):
    """Add one agent from the library catalog to the Brainstem's agents folder, checked against the catalog's fingerprint."""
    reg = json.loads(_fetch(f"{CATALOG}/registry.json"))
    norm = lambda s: " ".join(w for w in "".join(c if c.isalnum() else " " for c in str(s).lower()).split() if w != "agent")
    want = norm(name.split("/")[-1])
    hits = [a for a in reg["agents"] if want in (norm(a["name"].split("/")[-1]), norm(a.get("display_name", "")), norm(Path(a["_file"]).stem))]
    if not hits:
        word = (want.split() or [""])[0]
        return 1, {"status": "error", "error": f"no agent called {name!r} in the library catalog",
                   "close": sorted(a["name"].split("/")[-1] for a in reg["agents"] if word and word in a["name"].lower())[:10]}
    a = hits[0]
    body = _fetch(f"{CATALOG}/" + urllib.request.quote(a["_file"]))
    if hashlib.sha256(body).hexdigest() != a["_sha256"]:
        return 1, {"status": "error", "error": "the agent file does not match the catalog's fingerprint"}
    folder = Path(os.environ.get("AGENTS_PATH") or _home() / "agents")
    (folder / Path(a["_file"]).name).write_bytes(body)
    return 0, {"status": "ok", "agent": Path(a["_file"]).name, "sha256": a["_sha256"], "message": "It is on offer from the next turn."}


def _home():
    for c in (os.environ.get("BRAINSTEM_HOME"), "rapp_brainstem", HERE / "rapp_brainstem", HERE.parent.parent / "rapp_brainstem"):
        if c and (Path(c) / "brainstem.py").exists():
            return Path(c).resolve()
    sys.exit("No Brainstem found. Set BRAINSTEM_HOME to the folder that holds brainstem.py.")


def _kernel():
    home = _home()
    sys.path.insert(0, str(home))
    sys.path.insert(0, str(HERE))
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        import brainstem
    import plug
    return brainstem, plug


def _load(name, default):
    f = STATE / name
    return json.loads(f.read_text()) if f.exists() else default


def _save(name, value):
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / name).write_text(json.dumps(value, indent=1))


def _run(turn):
    """Replay this turn through the real /chat. Model answers already given are fed back in order; agent
    rounds already run are returned from the turn's record, so no agent ever runs twice. When /chat asks
    for an answer that has not been given yet, it is handed out and the turn waits."""
    kernel, plug = _kernel()
    need, seen = {}, {"model": 0, "tools": 0}

    def answer(messages, tools):
        i = seen["model"]
        seen["model"] += 1
        if i < len(turn["answers"]):
            return turn["answers"][i]
        if not need:
            need.update(messages=list(messages), tools=tools)
        return {"content": WAIT}

    real_tools = kernel.run_tool_calls

    def tool_round(tool_calls, agents, session_id=None):
        i = seen["tools"]
        seen["tools"] += 1
        if i < len(turn["rounds"]):
            return turn["rounds"][i]["results"], turn["rounds"][i]["logs"]
        results, logs = real_tools(tool_calls, agents, session_id=session_id)
        turn["rounds"].append({"results": results, "logs": logs,
                               "agents": [c.get("function", {}).get("name") for c in tool_calls]})
        return results, logs

    undo = plug.use(kernel, answer, turn.get("model") or "host-ai")
    kernel.run_tool_calls = tool_round
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            r = kernel.app.test_client().post("/chat", json={
                "user_input": turn["words"], "session_id": turn["session_id"],
                "conversation_history": turn["history"]})
        body = r.get_json()
    finally:
        kernel.run_tool_calls = real_tools
        undo()
    if need:
        shown = turn.get("shown", 0)
        fresh = need["messages"][shown:]
        turn["shown"] = len(need["messages"])
        return {"need": "your answer, as the model",
                "new_messages": fresh,
                "agents_you_may_call": [t["function"] for t in (need["tools"] or [])] if not shown else
                                       ("the same agents as before" if need["tools"] else "none on this step: answer in words"),
                "answer_with": "python hatch.py answer '<words for the person>'   or   "
                               "python hatch.py answer '{\"tool_calls\": [{\"function\": {\"name\": \"<Agent>\", \"arguments\": {}}}]}'"}
    return {"done": body, "status": r.status_code}


def _finish(turn, out):
    body = out["done"] if isinstance(out["done"], dict) else {}
    chat = _load("chat.json", {"session_id": turn["session_id"], "turns": []})
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ran = [a for rnd in turn["rounds"] for a in rnd["agents"] if a]
    chat["exported_at"], chat["model"] = now, body.get("model")
    chat["turns"].append({"role": "user", "content": turn["words"], "timestamp": now})
    chat["turns"].append({"role": "assistant", "content": body.get("response", ""), "timestamp": now,
                          "agents": ran, "agent_logs": body.get("agent_logs", "")})
    _save("chat.json", chat)
    history = turn["history"] + [{"role": "user", "content": turn["words"]},
                                 {"role": "assistant", "content": body.get("response", "")}]
    _save("history.json", history[-40:])
    (STATE / "turn.json").unlink()
    out["chat_file"] = str((STATE / "chat.json").resolve())
    out["agents_that_ran"] = ran
    return out


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd in ("get", "bring"):
        code, out = get() if cmd == "get" else bring(" ".join(argv[2:]))
        print(json.dumps(out, indent=1))
        return code
    if cmd == "tools":
        kernel, _ = _kernel()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            agents = kernel.load_agents()
        print(json.dumps([{"name": n, "description": a.metadata.get("description", "")} for n, a in sorted(agents.items())], indent=1))
        return 0
    if cmd == "ask" and len(argv) > 2:
        chat = _load("chat.json", None)
        turn = {"words": " ".join(argv[2:]), "answers": [], "rounds": [], "history": _load("history.json", []),
                "session_id": (chat or {}).get("session_id") or "hatch-" + time.strftime("%Y%m%d%H%M%S", time.gmtime()),
                "model": os.environ.get("HATCH_MODEL", "host-ai")}
    elif cmd == "answer" and len(argv) > 2:
        turn = _load("turn.json", None)
        if not turn:
            print(json.dumps({"error": "no turn is waiting; start one with: python hatch.py ask \"<what the person said>\""}))
            return 1
        raw = " ".join(argv[2:])
        try:
            given = json.loads(raw)
            given = given if isinstance(given, dict) else {"content": raw}
        except ValueError:
            given = {"content": raw}
        turn["answers"].append(given)
    elif cmd == "chat":
        chat = _load("chat.json", {"turns": []})
        ran = sorted({a for t in chat["turns"] for a in t.get("agents", [])})
        print(json.dumps({"chat_file": str((STATE / "chat.json").resolve()), "turns": len(chat["turns"]) // 2,
                          "agents_that_ran": ran}, indent=1))
        return 0
    else:
        print(__doc__)
        return 2
    out = _run(turn)
    _save("turn.json", turn)
    if "done" in out:
        out = _finish(turn, out)
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:  # say what went wrong in one line the AI can act on, never a wall of trace
        print(json.dumps({"status": "error", "error": f"{type(e).__name__}: {e}"}))
        sys.exit(1)
