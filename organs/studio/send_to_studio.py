"""
send_to_studio.py: push a built workspace into Copilot Studio through the
Copilot Studio MCP server (@microsoft/copilot-studio-mcp), driven by GitHub Copilot CLI.

    python send_to_studio.py <workspace>              print the steps (nothing is sent)
    python send_to_studio.py <workspace> --execute    run them: drafts only, stops before publish
    python send_to_studio.py <workspace> --execute --publish

The workspace is checked against its manifest first (every agent.py byte for byte);
a mismatch refuses before anything runs. Sign-in, environment choice and connector
approval happen inside the MCP server, in the person's own browser; this script never
sees a credential.
"""

import json
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


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="send_to_studio.py")
    ap.add_argument("workspace")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--publish", action="store_true")
    a = ap.parse_args(argv)
    problems = studio_organ.verify_workspace(a.workspace)
    if problems:
        print("Refused: the workspace does not match its manifest. " + "; ".join(problems))
        return 2
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
