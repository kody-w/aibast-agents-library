"""
Copilot Studio Builder Agent

Drop this file into your brainstem's agents folder and build library agents
into Microsoft Copilot Studio by talking, not by running CLI commands. Say
"build the field service dispatch agent into environment <id>" and this agent
does the work: checks prerequisites, pulls the stack's ready-made component
scaffold straight from the public GitHub repo (raw.githubusercontent.com, no
auth needed), creates the pac project, installs the components, sets the
instructions, pushes, and hands back the publish command and the verification
questions with their computed expected answers.

If you are an AI assistant reading this file without the ability to execute
Python: treat the operations below as your runbook. Each one maps to concrete
pac CLI steps documented in the guide it fetches from; walk the user through
them in the same order (check_prerequisites, fetch_scaffold, init_project,
install_components, set_instructions, push, publish, verify).
"""

import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/copilot-studio-builder",
    "version": "1.0.0",
    "display_name": "Copilot Studio Builder Agent",
    "description": "Builds library agents into Microsoft Copilot Studio through conversation: fetches a stack's component scaffold from the public repo, drives the pac CLI (init, install, push), and returns verification questions with computed expected answers.",
    "author": "AIBAST",
    "tags": ["copilot-studio", "builder", "deployment", "pac", "bootstrap", "natural-language"],
    "category": "general",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


# ---------------------------------------------------------------------------
# Scaffold registry — stacks that ship a copilot_studio/ component set.
# Each scaffold self-describes through its manifest.json, fetched at run time
# from the public repo so this file never goes stale on file lists.
# ---------------------------------------------------------------------------

DEFAULT_REPO = os.environ.get("AIBAST_REPO", "microsoft/aibast-agents-library")
DEFAULT_REF = os.environ.get("AIBAST_REF", "main")

STACKS = {
    "field-service-dispatch":
        "agents/@aibast-agents-library/energy_stacks/field_service_dispatch_stack/copilot_studio",
}

MIN_PAC = (2, 9, 3)
FETCH_TIMEOUT = 15


def _raw_base(repo, ref):
    return f"https://raw.githubusercontent.com/{repo}/{ref}"


def _fetch(url):
    """GET a public raw URL; return text. Raises on failure."""
    req = urllib.request.Request(url, headers={"User-Agent": "aibast-copilot-studio-builder"})
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as r:
        return r.read().decode("utf-8")


def _run(cmd, cwd=None, timeout=180):
    """Run a CLI command; return (ok, output). Never raises."""
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
        return p.returncode == 0, out.strip()
    except FileNotFoundError:
        return False, f"`{cmd[0]}` is not installed or not on PATH."
    except subprocess.TimeoutExpired:
        return False, f"`{' '.join(cmd)}` timed out after {timeout}s."
    except Exception as e:  # noqa: BLE001 — report, never crash the chat loop
        return False, f"`{' '.join(cmd)}` failed: {e}"


def _pac_version():
    """Return (version_tuple or None, message)."""
    ok, out = _run(["pac", "help"], timeout=30)
    if not ok and "not installed" in out:
        return None, out
    m = re.search(r"Version:\s*([\d.]+)", out) or re.search(r"(\d+\.\d+\.\d+)", out)
    if not m:
        return None, "Could not read the pac CLI version from `pac help` output."
    ver = tuple(int(x) for x in m.group(1).split(".")[:3])
    return ver, m.group(1)


def _default_project_dir(stack):
    return os.path.join(os.path.expanduser("~"), "CopilotStudioAgents", stack)


class CopilotStudioBuilderAgent(BasicAgent):
    """Conversational end-to-end builder for Copilot Studio library agents."""

    def __init__(self):
        self.name = "@aibast-agents-library/copilot-studio-builder"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "guide",
                            "check_prerequisites",
                            "fetch_scaffold",
                            "init_project",
                            "install_components",
                            "set_instructions",
                            "push",
                            "publish",
                            "verify",
                            "bootstrap",
                        ],
                        "description": "The build step to perform. Use 'bootstrap' to run the whole chain end to end, or 'guide' to see what is possible.",
                    },
                    "stack": {
                        "type": "string",
                        "description": "Which library stack to build (default 'field-service-dispatch').",
                    },
                    "environment_id": {
                        "type": "string",
                        "description": "Power Platform environment ID to build into. Required for init_project, publish, and bootstrap.",
                    },
                    "project_dir": {
                        "type": "string",
                        "description": "Local folder for the pac project. Defaults to ~/CopilotStudioAgents/<stack>.",
                    },
                    "repo": {
                        "type": "string",
                        "description": "GitHub repo to fetch the scaffold from (default microsoft/aibast-agents-library).",
                    },
                    "ref": {
                        "type": "string",
                        "description": "Git branch or tag to fetch from (default main).",
                    },
                    "confirm_publish": {
                        "type": "boolean",
                        "description": "Publishing makes the agent live for everyone it is shared with. Must be true to actually publish.",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    # ------------------------------------------------------------------
    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation", "guide")
        dispatch = {
            "guide": self._guide,
            "check_prerequisites": self._check_prerequisites,
            "fetch_scaffold": self._fetch_scaffold,
            "init_project": self._init_project,
            "install_components": self._install_components,
            "set_instructions": self._set_instructions,
            "push": self._push,
            "publish": self._publish,
            "verify": self._verify,
            "bootstrap": self._bootstrap,
        }
        handler = dispatch.get(op)
        if handler is None:
            return f"**Error:** Unknown operation `{op}`. Valid: {', '.join(dispatch)}"
        try:
            return handler(**kwargs)
        except Exception as e:  # noqa: BLE001 — a chat tool must answer, not crash
            return f"**{op} failed:** {e}\n\nRun `check_prerequisites` and try again."

    # ------------------------------------------------------------------
    def _ctx(self, kwargs):
        stack = kwargs.get("stack", "field-service-dispatch")
        repo = kwargs.get("repo", DEFAULT_REPO)
        ref = kwargs.get("ref", DEFAULT_REF)
        project = kwargs.get("project_dir") or _default_project_dir(stack)
        return stack, repo, ref, os.path.expanduser(project)

    def _manifest(self, stack, repo, ref):
        if stack not in STACKS:
            known = ", ".join(sorted(STACKS))
            raise ValueError(f"Unknown stack '{stack}'. Stacks with a Copilot Studio scaffold: {known}")
        base = f"{_raw_base(repo, ref)}/{STACKS[stack]}"
        return json.loads(_fetch(f"{base}/manifest.json")), base

    # ------------------------------------------------------------------
    def _guide(self, **kwargs) -> str:
        stacks = "\n".join(f"- `{s}`" for s in sorted(STACKS))
        return (
            "# Copilot Studio Builder\n\n"
            "I build library agents into Microsoft Copilot Studio for you. Tell me things like:\n\n"
            "- \"Build the field service dispatch agent into environment `<env-id>`\" → I run `bootstrap`.\n"
            "- \"Check whether my machine is ready\" → `check_prerequisites`.\n"
            "- \"Show me what the scaffold contains\" → `fetch_scaffold`.\n"
            "- \"Publish it\" → `publish` (I will ask you to confirm — publishing makes the agent live).\n"
            "- \"How do I test it?\" → `verify` returns the questions with computed expected answers.\n\n"
            f"**Stacks I can build today:**\n{stacks}\n\n"
            "Everything I install comes from the public library repo over "
            "`raw.githubusercontent.com`, so there is nothing to download first. The one thing I "
            "cannot do for you is the interactive browser sign-in: if no pac auth profile exists "
            "yet, run `pac auth create` once in a terminal and come back."
        )

    # ------------------------------------------------------------------
    def _check_prerequisites(self, **kwargs) -> str:
        lines = ["# Prerequisite check\n"]
        ver, msg = _pac_version()
        if ver is None:
            lines.append(f"- ❌ **pac CLI**: {msg}")
            lines.append("  Install: `dotnet tool install --global Microsoft.PowerApps.CLI.Tool` "
                         "(or the VS Code extension), then re-run this check.")
        elif ver < MIN_PAC:
            lines.append(f"- ❌ **pac CLI {msg}** found, but {'.'.join(map(str, MIN_PAC))}+ is required "
                         "for CLI-authored agents. Update: `pac install latest`.")
        else:
            lines.append(f"- ✅ **pac CLI {msg}** — new enough for CLI-authored agents.")

        ok, out = _run(["pac", "auth", "list"], timeout=30)
        if ok and re.search(r"\S+@\S+|\bUNIVERSAL\b|\*", out):
            lines.append("- ✅ **pac auth profile** exists.")
        else:
            lines.append("- ❌ **No pac auth profile.** Run `pac auth create` in a terminal and "
                         "complete the browser sign-in (this is the one step I cannot do for you).")

        try:
            _fetch(f"{_raw_base(DEFAULT_REPO, DEFAULT_REF)}/registry.json")
            lines.append(f"- ✅ **Library reachable** at `{DEFAULT_REPO}@{DEFAULT_REF}`.")
        except Exception as e:  # noqa: BLE001
            lines.append(f"- ❌ **Library unreachable**: {e}")

        lines.append("\nWhen every line is ✅, say \"build <stack> into environment <env-id>\" "
                     "and I will take it from there.")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def _fetch_scaffold(self, **kwargs) -> str:
        stack, repo, ref, _ = self._ctx(kwargs)
        try:
            man, base = self._manifest(stack, repo, ref)
        except Exception as e:  # noqa: BLE001
            return f"**Could not fetch the scaffold for `{stack}`:** {e}"
        lines = [f"# Scaffold: {man.get('display_name', stack)}\n",
                 f"Source: `{base}`\n",
                 "**Skills (behaviors):**"]
        lines += [f"- `{b}`" for b in man.get("behaviors", [])]
        lines.append("\n**Knowledge files:**")
        lines += [f"- `{k}`" for k in man.get("knowledge_files", [])]
        lines.append(f"\n**Instructions:** `{man.get('instructions')}`")
        lines.append(f"\n**Verification questions:** {len(man.get('verification', []))} "
                     "(ask me to `verify` after the build).")
        lines.append("\nSay \"build it into environment <env-id>\" to run the whole chain.")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def _init_project(self, **kwargs) -> str:
        stack, repo, ref, project = self._ctx(kwargs)
        env = kwargs.get("environment_id")
        if not env:
            return ("**I need your Power Platform environment ID** to create the project "
                    "(Copilot Studio → Settings, or the maker portal URL). "
                    "Then say: build into environment `<env-id>`.")
        try:
            man, _ = self._manifest(stack, repo, ref)
        except Exception as e:  # noqa: BLE001
            return f"**Could not fetch the scaffold for `{stack}`:** {e}"
        base_dir = project
        n = 2
        while os.path.exists(project):
            project = f"{base_dir}-{n}"
            n += 1
        os.makedirs(os.path.dirname(project) or ".", exist_ok=True)
        name = man.get("display_name", stack)
        ok, out = _run([
            "pac", "copilot", "init",
            "--name", name,
            "--publisher-prefix", "aibast",
            "--authoring-mode", "cli-copilot",
            "--project-dir", project,
            "--environment", env,
        ], timeout=300)
        if not ok or not os.path.exists(os.path.join(project, "settings.mcs.yml")):
            return (f"**`pac copilot init` did not produce a project.**\n\n```\n{out}\n```\n\n"
                    "Usual causes: no auth profile (`pac auth create`), or no maker permission "
                    "in that environment.")
        return (f"✅ Project created at `{project}` for **{name}** in environment `{env}`.\n\n"
                f"Next: `install_components` (I will fetch and place every file), or just tell me "
                "to keep going.")

    # ------------------------------------------------------------------
    def _install_components(self, **kwargs) -> str:
        stack, repo, ref, project = self._ctx(kwargs)
        if not os.path.exists(os.path.join(project, "settings.mcs.yml")):
            return (f"**No pac project found at `{project}`.** Run `init_project` first "
                    "(I need the environment ID), or pass `project_dir` if it lives elsewhere.")
        try:
            man, base = self._manifest(stack, repo, ref)
        except Exception as e:  # noqa: BLE001
            return f"**Could not fetch the scaffold for `{stack}`:** {e}"
        placed, failed = [], []
        for rel in man.get("behaviors", []) + man.get("knowledge_files", []):
            dest = os.path.join(project, *rel.split("/"))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            try:
                content = _fetch(f"{base}/{rel}")
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(content)
                placed.append(rel)
            except Exception as e:  # noqa: BLE001
                failed.append(f"{rel} ({e})")
        report = [f"✅ Placed {len(placed)} component files into `{project}`:"]
        report += [f"- `{p}`" for p in placed]
        if failed:
            report.append(f"\n❌ Failed: {'; '.join(failed)}")
        report.append("\nNext: `set_instructions`, then `push`.")
        return "\n".join(report)

    # ------------------------------------------------------------------
    def _set_instructions(self, **kwargs) -> str:
        stack, repo, ref, project = self._ctx(kwargs)
        settings = os.path.join(project, "settings.mcs.yml")
        if not os.path.exists(settings):
            return f"**No pac project found at `{project}`.** Run `init_project` first."
        try:
            man, base = self._manifest(stack, repo, ref)
            instructions = _fetch(f"{base}/{man.get('instructions', 'instructions.md')}")
        except Exception as e:  # noqa: BLE001
            return f"**Could not fetch the instructions for `{stack}`:** {e}"

        indented = "\n".join(("            " + ln).rstrip() for ln in instructions.splitlines())
        block = ("configuration:\n"
                 "  agentSettings:\n"
                 "    instructions:\n"
                 "      segments:\n"
                 "        - kind: StaticSegment\n"
                 "          value: |\n"
                 f"{indented}\n")

        with open(settings, "r", encoding="utf-8") as f:
            text = f.read()

        if "agentSettings" not in text and "configuration:" not in text:
            with open(settings, "a", encoding="utf-8") as f:
                f.write(("\n" if not text.endswith("\n") else "") + block)
            return (f"✅ Instructions written into `{settings}` "
                    "(new configuration block appended). Next: `push`.")

        try:
            import yaml  # lazy — only needed when merging into an existing block
            data = yaml.safe_load(text) or {}
            cfg = data.setdefault("configuration", {}) or {}
            ags = cfg.setdefault("agentSettings", {}) or {}
            ins = ags.setdefault("instructions", {}) or {}
            ins["segments"] = [{"kind": "StaticSegment", "value": instructions}]
            cfg["agentSettings"] = ags
            data["configuration"] = cfg
            with open(settings, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True,
                               default_flow_style=False)
            return f"✅ Instructions merged into `{settings}`. Next: `push`."
        except ImportError:
            return ("**Almost:** the settings file already has a configuration block and I need "
                    "PyYAML to merge safely (`pip install pyyaml`), or open "
                    f"`{settings}` and paste the instructions into "
                    "`configuration.agentSettings.instructions.segments[0].value` yourself — "
                    "the full text is in the scaffold's `instructions.md`.")

    # ------------------------------------------------------------------
    def _push(self, **kwargs) -> str:
        _, _, _, project = self._ctx(kwargs)
        if not os.path.exists(os.path.join(project, "settings.mcs.yml")):
            return f"**No pac project found at `{project}`.** Run `init_project` first."
        ok1, out1 = _run(["pac", "copilot", "pull", "--project-dir", project], timeout=600)
        ok2, out2 = _run(["pac", "copilot", "push", "--project-dir", project], timeout=600)
        if not ok2:
            return f"**Push failed.**\n\nPull said:\n```\n{out1}\n```\nPush said:\n```\n{out2}\n```"
        return (f"✅ Pushed `{project}` to Copilot Studio.\n\n```\n{out2}\n```\n\n"
                "Next: `publish` (I will ask you to confirm — publishing makes the agent live), "
                "then `verify`.")

    # ------------------------------------------------------------------
    def _publish(self, **kwargs) -> str:
        _, _, _, project = self._ctx(kwargs)
        env = kwargs.get("environment_id")
        if not kwargs.get("confirm_publish"):
            return ("**Publishing makes the agent live for everyone it is shared with.** "
                    "If you are sure, say \"yes, publish it\" and I will run it with "
                    "`confirm_publish: true`.")
        settings = os.path.join(project, "settings.mcs.yml")
        schema_name = None
        if os.path.exists(settings):
            with open(settings, "r", encoding="utf-8") as f:
                m = re.search(r"schemaName:\s*([^\s#]+)", f.read())
                if m:
                    schema_name = m.group(1).strip("'\"")
        if not schema_name:
            return (f"**Could not read a schemaName from `{settings}`.** "
                    "Pass the bot schema name or check the project directory.")
        if not env:
            return "**I need the environment ID to publish** (same one used for init)."
        ok, out = _run(["pac", "copilot", "publish", "--bot", schema_name,
                        "--environment", env], timeout=900)
        if not ok:
            return f"**Publish failed.**\n\n```\n{out}\n```"
        return (f"✅ Published `{schema_name}` in environment `{env}` — the agent is live.\n\n"
                "Now run `verify`: ask it the five questions and check the computed answers.")

    # ------------------------------------------------------------------
    def _verify(self, **kwargs) -> str:
        stack, repo, ref, _ = self._ctx(kwargs)
        try:
            man, _ = self._manifest(stack, repo, ref)
        except Exception as e:  # noqa: BLE001
            return f"**Could not fetch the verification set for `{stack}`:** {e}"
        lines = [f"# Verify: {man.get('display_name', stack)}\n",
                 "Open the agent's **Test pane** in Copilot Studio and ask, in order. Every "
                 "expected answer is computed from the scaffold's data — a wrong answer is "
                 "visible, not arguable:\n"]
        for i, v in enumerate(man.get("verification", []), 1):
            lines.append(f"{i}. **Ask:** “{v['ask']}”")
            lines.append(f"   **Expect:** {v['expect']}\n")
        lines.append("If 2, 3, or 4 fail, the build is not done — the usual culprit is a "
                     "component that never pushed. Tell me and I will re-run `push`.")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def _bootstrap(self, **kwargs) -> str:
        """The whole chain, narrated. Stops at the first blocker with what to do."""
        stack, _, _, _ = self._ctx(kwargs)
        env = kwargs.get("environment_id")
        log = [f"# Building `{stack}` end to end\n"]

        prereq = self._check_prerequisites(**kwargs)
        log.append(prereq)
        if "❌" in prereq:
            log.append("\n**Stopped before touching anything** — clear the ❌ items above, "
                       "then tell me to build again.")
            return "\n".join(log)
        if not env:
            log.append("\n**One thing missing: your environment ID** (Copilot Studio → Settings). "
                       "Say: build into environment `<env-id>`.")
            return "\n".join(log)

        for step_name, step in (("init_project", self._init_project),
                                ("install_components", self._install_components),
                                ("set_instructions", self._set_instructions),
                                ("push", self._push)):
            result = step(**kwargs)
            log.append(f"\n---\n\n{result}")
            if result.startswith("**") or "❌" in result.split("\n")[0]:
                log.append(f"\n**Stopped at `{step_name}`** — fix the issue above and tell me to "
                           "continue; completed steps are safe to re-run.")
                return "\n".join(log)
            if step_name == "init_project":
                # init may have suffixed the directory; keep subsequent steps aligned
                m = re.search(r"Project created at `([^`]+)`", result)
                if m:
                    kwargs["project_dir"] = m.group(1)

        log.append("\n---\n\n" + self._publish(**kwargs))
        log.append("\n---\n\n" + self._verify(**kwargs))
        return "\n".join(log)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = CopilotStudioBuilderAgent()
    print(agent.perform(operation="guide"))
    print("=" * 72)
    print(agent.perform(operation="verify"))
