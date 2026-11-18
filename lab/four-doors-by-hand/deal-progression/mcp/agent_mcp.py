#!/usr/bin/env python3
"""Offer one library agent.py as one MCP tool over stdio. Standard library only.

    python3 agent_mcp.py deal_progression_agent DealProgressionAgent

The tool's name, description and inputs are the agent's own `metadata`. A call runs
`perform(**arguments)` and returns its text unchanged. Nothing is restated here.
"""
import importlib, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
agent = getattr(importlib.import_module(sys.argv[1]), sys.argv[2])()
meta = agent.metadata


def reply(i, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": i}
    msg.update({"error": error} if error else {"result": result})
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    req = json.loads(line)
    i, method, params = req.get("id"), req.get("method"), req.get("params") or {}
    if i is None:
        continue  # a notification: nothing to answer
    if method == "initialize":
        reply(i, {"protocolVersion": params.get("protocolVersion", "2024-11-05"),
                  "capabilities": {"tools": {}},
                  "serverInfo": {"name": "aibast-" + meta["name"], "version": "1.0.0"}})
    elif method == "ping":
        reply(i, {})
    elif method == "tools/list":
        reply(i, {"tools": [{"name": meta["name"], "description": meta["description"],
                             "inputSchema": meta["parameters"]}]})
    elif method == "tools/call":
        if params.get("name") != meta["name"]:
            reply(i, error={"code": -32602, "message": "unknown tool"})
            continue
        try:
            text, bad = agent.perform(**(params.get("arguments") or {})), False
        except Exception as exc:  # the agent failed: say so, do not guess
            text, bad = "The agent could not run: %s" % exc, True
        reply(i, {"content": [{"type": "text", "text": text}], "isError": bad})
    else:
        reply(i, error={"code": -32601, "message": "method not found"})
