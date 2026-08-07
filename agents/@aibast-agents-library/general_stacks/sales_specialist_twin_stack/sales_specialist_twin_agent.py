"""
Sales Specialist Twin Agent

The one agent.py for the whole AIBAST library. Drop it into a brainstem and
GitHub Copilot becomes an AIBAST sales specialist: say what you want in plain
language — "deploy the field service dispatch agent to Copilot Studio", "set
up my machine", "install the contract review agent locally" — and this agent
fetches the authored mission playbook from the public library repo and hands
it to GitHub Copilot to EXECUTE, end to end, inside the loop.

This is the personless-harness pattern: the person steers, GitHub Copilot is
the engine that does all the work, and this agent is how the engine gets its
operating doctrine. The agent does not run commands itself — it retrieves the
instructions WE publish (raw.githubusercontent.com, globally available, no
auth) and returns them as the engine's marching orders, with live context
(which stack, which files, which verification answers) injected.
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates"))
from basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/sales-specialist-twin",
    "version": "1.0.0",
    "display_name": "Sales Specialist Twin Agent",
    "description": "The one agent for the whole AIBAST library: matches any plain-language request to an authored mission playbook fetched from the public repo, injects live library context, and hands GitHub Copilot everything it needs to execute the mission end to end — machine setup, local installs, Copilot Studio deployment, and verification.",
    "author": "AIBAST",
    "tags": ["twin", "sales-specialist", "deploy", "copilot-studio", "bootstrap", "personless-harness", "one-command"],
    "category": "general",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic-agent"],
}


REPO = os.environ.get("AIBAST_REPO", "microsoft/aibast-agents-library")
REF = os.environ.get("AIBAST_REF", "main")
RAW = f"https://raw.githubusercontent.com/{REPO}/{REF}"
TIMEOUT = 15

# The engine's standing orders, prepended to every mission. These four rules
# are the personless-harness contract — they are what makes an autonomous run
# trustworthy enough to hand to a seller.
HARNESS_HEADER = """\
# MISSION BRIEFING — you are the engine

You are GitHub Copilot operating inside a brainstem loop. The person has asked
for an outcome; YOU do the work. Execute the mission below yourself — run the
commands, edit the files, check the results. Do not hand steps back to the
person unless a step is marked **PERSON** (those are the only steps that need
a human: interactive sign-ins and go-live confirmations).

Standing orders, always:
1. **Real execution** — actually run each command and read its real output.
2. **Expect friction** — errors are listed with their fixes; apply the fix and
   continue rather than giving up or improvising.
3. **Verify, don't assume** — a step is done when its check passes, not when
   its command exits.
4. **Honest reporting** — report what actually happened, including failures.
   Never present an unverified step as complete.

Report progress to the person as you go, in plain language, one line per step.
"""


def _fetch(path):
    url = path if path.startswith("http") else f"{RAW}/{path}"
    url = urllib.parse.quote(url, safe=":/%?=&")
    req = urllib.request.Request(url, headers={"User-Agent": "aibast-sales-specialist-twin"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8")


def _missions():
    return json.loads(_fetch("twin/missions.json"))


def _match(text, candidates, keys):
    """Score candidates by trigger-word overlap with the request."""
    q = re.sub(r"[^a-z0-9 ]", " ", (text or "").lower()).split()
    best, best_score = None, 0
    for c in candidates:
        hay = " ".join(str(c.get(k, "")) for k in keys).lower()
        score = sum(1 for w in q if w and w in hay)
        if score > best_score:
            best, best_score = c, score
    return best, best_score


MISSION_WORDS = {"deploy", "install", "build", "publish", "ship", "copilot", "studio",
                 "locally", "local", "brainstem", "verify", "test", "the", "a", "an",
                 "agent", "to", "into", "my", "in", "for", "please", "and", "then"}


def _stack_context(request):
    """Resolve which library stack the request names, and build its context block."""
    reg = json.loads(_fetch("registry.json"))
    domain_words = " ".join(w for w in re.sub(r"[^a-z0-9 ]", " ", request.lower()).split()
                            if w not in MISSION_WORDS)
    candidates = [a for a in reg.get("agents", [])
                  if a.get("name") != "@aibast-agents-library/sales-specialist-twin"]
    entry, score = _match(domain_words, candidates,
                          ["name", "display_name", "tags", "description"])
    if not entry or score == 0:
        return None, None
    stack_dir = os.path.dirname(entry["_file"]) + "/copilot_studio"
    try:
        man = json.loads(_fetch(f"{stack_dir}/manifest.json"))
    except Exception:  # noqa: BLE001 — stack has no Copilot Studio scaffold
        return entry, None
    base = f"{RAW}/{stack_dir}"
    files = man.get("behaviors", []) + man.get("knowledge_files", [])
    ctx = [f"**Agent:** {man.get('display_name', entry['name'])}",
           f"**Scaffold base URL:** {base}",
           f"**Instructions file:** {base}/{man.get('instructions', 'instructions.md')}",
           "**Component files to download** (note: encode `@` as `%40` in raw URLs):"]
    ctx += [f"- {base}/{f}  →  place at `<project>/{f}`" for f in files]
    ctx.append("\n**Verification — ask the deployed agent these; every expected "
               "answer is computed from the data, so wrong is visible:**")
    for i, v in enumerate(man.get("verification", []), 1):
        ctx.append(f"{i}. Ask: “{v['ask']}” → Expect: {v['expect']}")
    return entry, "\n".join(ctx)


class SalesSpecialistTwinAgent(BasicAgent):
    """One request in, one executed mission out — GitHub Copilot does the work."""

    def __init__(self):
        self.name = "@aibast-agents-library/sales-specialist-twin"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["mission", "list_missions", "list_agents", "help"],
                        "description": "mission: fetch the playbook for the user's request and execute it. list_missions: what the twin can run. list_agents: what the library contains. help: what this is.",
                    },
                    "request": {
                        "type": "string",
                        "description": "The user's ask, in their own words (e.g. 'deploy the field service dispatch agent to copilot studio').",
                    },
                },
                "required": ["operation"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        op = kwargs.get("operation", "help")
        try:
            if op == "mission":
                return self._mission(kwargs.get("request", ""))
            if op == "list_missions":
                return self._list_missions()
            if op == "list_agents":
                return self._list_agents()
            return self._help()
        except Exception as e:  # noqa: BLE001 — a chat tool answers, never crashes
            return (f"**Could not load that mission:** {e}\n\n"
                    "Check connectivity to raw.githubusercontent.com and try again, "
                    "or ask for `list_missions`.")

    # ------------------------------------------------------------------
    def _help(self) -> str:
        return (
            "# Sales Specialist Twin\n\n"
            "I am the one agent for the whole AIBAST library. Tell me the outcome you want, "
            "in your own words:\n\n"
            "- “Deploy the field service dispatch agent to Copilot Studio”\n"
            "- “Set up my machine” (installs everything a build needs)\n"
            "- “Install the contract risk review agent locally”\n"
            "- “How do I test the agent you deployed?”\n\n"
            "For each request I fetch the authored playbook from the public AIBAST library and "
            "GitHub Copilot executes it end to end — you watch the progress and answer only "
            "the questions a person must answer (sign-ins, go-live). You never need to know "
            "pac, YAML, or Copilot Studio internals.\n\n"
            "Ask **list_missions** to see every mission, or **list_agents** for the library "
            "catalog."
        )

    # ------------------------------------------------------------------
    def _list_missions(self) -> str:
        ms = _missions().get("missions", [])
        out = ["# Missions the twin can run\n"]
        out += [f"- **{m['title']}** — {m['summary']}" for m in ms]
        out.append("\nSay the outcome you want and I fetch the playbook; GitHub Copilot "
                   "executes it while you watch.")
        return "\n".join(out)

    # ------------------------------------------------------------------
    def _list_agents(self) -> str:
        reg = json.loads(_fetch("registry.json"))
        agents = reg.get("agents", [])
        by_cat = {}
        for a in agents:
            by_cat.setdefault(a.get("category", "other"), []).append(a)
        out = [f"# AIBAST Agent Library — {len(agents)} agents\n"]
        for cat in sorted(by_cat):
            names = ", ".join(x.get("display_name", x["name"]) for x in by_cat[cat][:6])
            more = len(by_cat[cat]) - 6
            out.append(f"- **{cat}** ({len(by_cat[cat])}): {names}" +
                       (f", +{more} more" if more > 0 else ""))
        out.append("\nAny of these installs locally in one step ('install <name> locally'). "
                   "Stacks with a Copilot Studio scaffold also deploy end to end "
                   "('deploy <name> to copilot studio').")
        return "\n".join(out)

    # ------------------------------------------------------------------
    def _mission(self, request) -> str:
        if not request.strip():
            return self._help()
        idx = _missions()
        mission, score = _match(request, idx.get("missions", []),
                                ["title", "summary", "triggers"])
        if not mission or score == 0:
            return ("I don't have a playbook matching that yet.\n\n" + self._list_missions())

        playbook = _fetch(f"twin/playbooks/{mission['playbook']}")

        # Inject live library context for stack-scoped missions.
        if mission.get("needs_stack"):
            entry, ctx = _stack_context(request)
            if entry is None:
                return ("Which library agent do you mean? Say it by name — e.g. "
                        "“deploy the *field service dispatch* agent”. Ask `list_agents` "
                        "to see the catalog.")
            if ctx is None:
                # No authored scaffold: hand the engine the intent file itself and
                # tell it to derive the components by the same rules.
                base = f"{RAW}/{entry['_file']}"
                ctx = (f"**Agent:** {entry.get('display_name', entry['name'])}\n"
                       f"**agent.py (the intent) raw URL** (encode `@` as `%40`): {base}\n\n"
                       "**No authored scaffold exists for this stack yet.** Derive the "
                       "components from the intent file before executing the mission: read "
                       "the agent.py; its description and docstring become the instructions "
                       "(add the standing rules: recommend-don't-act, cite record IDs, "
                       "missing data is stated not guessed); each operation in its metadata "
                       "becomes one InlineAgentSkill whose procedure states the exact rules "
                       "and formulas found in the code; its module-level synthetic data "
                       "becomes one knowledge markdown file (banner it SYNTHETIC). Then "
                       "write your own 4-5 verification questions whose expected answers "
                       "you compute from that data before you deploy.")
            playbook = playbook.replace("{{STACK_CONTEXT}}", ctx)

        playbook = playbook.replace("{{REPO}}", REPO).replace("{{REF}}", REF).replace("{{RAW}}", RAW)
        return HARNESS_HEADER + "\n---\n\n" + playbook


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = SalesSpecialistTwinAgent()
    print(agent.perform(operation="help"))
