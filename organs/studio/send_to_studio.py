"""
send_to_studio.py: push a built workspace into Copilot Studio through the
Copilot Studio MCP server (@microsoft/copilot-studio-mcp), driven by GitHub Copilot CLI.

    python send_to_studio.py <workspace>              print the steps (nothing is sent)
    python send_to_studio.py <workspace> --execute    run them: drafts only, stops before publish
    python send_to_studio.py <workspace> --execute --publish
    python send_to_studio.py <workspace> --confirm-page --port-file F
                                                      a page on 127.0.0.1 where the person presses Send;
                                                      the chat can open it but never press it

The workspace is checked against its manifest first (every agent.py byte for byte);
a mismatch refuses before anything runs. Sign-in, environment choice and connector
approval happen inside the MCP server, in the person's own browser; this script never
sees a credential.
"""

import html
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_organ  # noqa: E402

SERVER = "copilot-studio-mcp"
ADD_SERVER = ["copilot", "mcp", "add", SERVER, "--", "npx", "-y", "@microsoft/copilot-studio-mcp@latest"]


def steps(workspace, publish=False):
    ws = Path(workspace)
    m = json.loads((ws / "manifest.json").read_text(encoding="utf-8"))
    tools = [w for a in m["agents"] for w in a["workflow_tools"]]
    out = [("discover_resources", "action=describe_actions for manage_workflows and manage_agents; use the "
            "contracts it returns for every later call and never guess a field")]
    for t in m["tables"]:
        spec = json.loads((ws / t).read_text(encoding="utf-8"))
        out.append(("discover_resources", f"confirm the Dataverse table {spec['logical_name']} "
                    f"(columns {', '.join(spec['columns'].values())}) and an existing Dataverse connection; "
                    "if either is missing, stop and say so"))
    for w in tools:
        spec = json.loads((ws / w).read_text(encoding="utf-8"))
        out.append(("manage_workflows", f"create a draft agent-callable workflow {spec['name']} from {w}: "
                    f"trigger '{spec['trigger']}' with inputs {', '.join(spec['inputs']) or '(none)'}, the "
                    f"definition's actions, then '{spec['respond']}' with {', '.join(spec['outputs'])}"))
    skills = ", ".join(a["skill_zip"] for a in m["agents"])
    out.append(("manage_agents", f"create or update the draft agent '{m['copilot']['name']}': instructions from "
                f"{m['copilot']['instructions']}, inline skills from {skills} (each SKILL.md and scripts/ "
                "unchanged), and the workflows above as its tools"))
    if publish:
        out.append(("manage_agents", "publish the agent and report its published time"))
    else:
        out.append(("stop", "do not publish; report the draft's id and each step as worked or broke"))
    return out


def prompt(workspace, publish=False):
    lines = ["Send the prepared Copilot Studio workspace in this folder, using only the copilot-studio-mcp tools.",
             "Do the steps in order. Stop at the first step that fails and report it; never retry an uncertain "
             "write. Unzip a skill to read it; never change its files."]
    lines += [f"{i}. {tool}: {what}." for i, (tool, what) in enumerate(steps(workspace, publish), 1)]
    return "\n".join(lines)


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Send to Copilot Studio</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:640px;margin:32px auto;padding:0 16px;
color:#1f2328;background:#fff}}@media (prefers-color-scheme:dark){{body{{color:#e6edf3;background:#0d1117}}}}
button{{font:inherit;padding:10px 20px;border:0;border-radius:6px;background:#1f6feb;color:#fff;cursor:pointer}}
li{{margin:6px 0}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}</style></head><body>{body}</body></html>"""


def _plain_steps(workspace, publish):
    m = json.loads((Path(workspace) / "manifest.json").read_text(encoding="utf-8"))
    tools = [w for a in m["agents"] for w in a["workflow_tools"]]
    items = [f"A draft agent named <b>{html.escape(m['copilot']['name'])}</b> with "
             f"{len(m['agents'])} skill(s)", f"{len(tools)} draft workflow(s) it calls for outside data"]
    if m["tables"]:
        items.append("Memory kept in your Dataverse table")
    items.append("Then it is published" if publish else "Nothing is published: it stays a draft")
    return "".join(f"<li>{i}</li>" for i in items)


def confirm_page(workspace, publish, port_file, ttl=900):
    """Serve one page on 127.0.0.1 until the person presses Send (or ttl seconds pass). The send runs only
    on a form post from that page: right Host, same-origin Origin header, and the page's one-time token."""
    import secrets
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import parse_qs

    token, done = secrets.token_urlsafe(24), threading.Event()

    class Page(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _origin_ok(self):
            here = f"127.0.0.1:{self.server.server_port}"
            return self.headers.get("Host") == here and self.headers.get("Origin") == f"http://{here}"

        def _reply(self, code, body):
            data = PAGE.format(body=body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Frame-Options", "DENY")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}" or self.path != "/":
                return self._reply(404, "<p>Not here.</p>")
            verb = "Send and publish" if publish else "Send as a draft"
            self._reply(200, f"<h1>Send to Copilot Studio</h1><p>This creates, signed in as you:</p>"
                             f"<ul>{_plain_steps(workspace, publish)}</ul>"
                             f"<form method=post action=/send><input type=hidden name=t value={token}>"
                             f"<button>{verb}</button></form><p>Close this page to cancel.</p>")

        def do_POST(self):
            size = min(int(self.headers.get("Content-Length") or 0), 4096)
            form = parse_qs(self.rfile.read(size).decode("utf-8", "replace"))
            if self.path != "/send" or not self._origin_ok() or form.get("t") != [token] or done.is_set():
                return self._reply(403, "<p>Refused: press Send on this page yourself.</p>")
            done.set()
            args = [sys.executable, __file__, str(workspace), "--execute"] + (["--publish"] if publish else [])
            out = subprocess.run(args, capture_output=True, text=True, timeout=3600)
            tail = html.escape("\n".join((out.stdout + out.stderr).strip().splitlines()[-20:]))
            word = "finished" if out.returncode == 0 else "stopped"
            self._reply(200, f"<h1>Send {word}</h1><pre>{tail}</pre><p>You can close this page.</p>")
            threading.Thread(target=self.server.shutdown, daemon=True).start()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Page)
    Path(port_file).write_text(json.dumps({"port": server.server_port, "pid": os.getpid()}), encoding="utf-8")
    threading.Timer(ttl, server.shutdown).start()
    try:
        server.serve_forever()
    finally:
        Path(port_file).unlink(missing_ok=True)
    return 0


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="send_to_studio.py")
    ap.add_argument("workspace")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--confirm-page", action="store_true")
    ap.add_argument("--port-file")
    a = ap.parse_args(argv)
    problems = studio_organ.verify_workspace(a.workspace)
    if problems:
        print("Refused: the workspace does not match its manifest. " + "; ".join(problems))
        return 2
    if a.confirm_page:
        return confirm_page(a.workspace, a.publish, a.port_file)
    command = ["copilot", "-p", prompt(a.workspace, a.publish), "--allow-tool", SERVER]
    if not a.execute:
        print("Dry run: nothing is sent.")
        print("Once: " + " ".join(ADD_SERVER))
        for i, (tool, what) in enumerate(steps(a.workspace, a.publish), 1):
            print(f"{i}. {tool}: {what}")
        print(f"Then: copilot -p <these steps> --allow-tool {SERVER}   (run in {a.workspace})")
        return 0
    if not shutil.which("copilot"):
        print("GitHub Copilot CLI (copilot) is not installed, so nothing was sent.")
        return 3
    listed = subprocess.run(["copilot", "mcp", "list"], capture_output=True, text=True)
    if SERVER not in listed.stdout:
        subprocess.run(ADD_SERVER, check=True)
    return subprocess.run(command, cwd=a.workspace).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
