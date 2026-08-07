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
# The library lives upstream at microsoft/…, staged downstream-first at
# kody-w/…. The twin works wherever the content currently is: each fetch
# tries the configured repo, then the mirrors, and locks onto whichever
# answered so one downloaded file works before and after the upstream merge.
MIRRORS = [
    ("kody-w/aibast-agents-library", "main"),
    (REPO, REF),
    ("kody-w/aibast-agents-library", "feature/field-service-dispatch-copilot-studio"),
]
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


_active = MIRRORS[:1]  # mutable: locks onto the first mirror that answers


def _fetch(path):
    if path.startswith("http"):
        url = urllib.parse.quote(path, safe=":/%?=&")
        req = urllib.request.Request(url, headers={"User-Agent": "aibast-sales-specialist-twin"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.read().decode("utf-8")
    order = _active + [m for m in MIRRORS if m not in _active]
    last = None
    for repo, ref in order:
        url = urllib.parse.quote(
            f"https://raw.githubusercontent.com/{repo}/{ref}/{path}", safe=":/%?=&")
        req = urllib.request.Request(url, headers={"User-Agent": "aibast-sales-specialist-twin"})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                _active[0] = (repo, ref)
                return r.read().decode("utf-8")
        except Exception as e:  # noqa: BLE001 — try the next mirror
            last = e
    raise last


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


# "copilot" is NOT a mission word on its own — stripping it collided
# "Proposal Copilot" with "Proposal Generation". The PHRASE is stripped below.
MISSION_PHRASES = ("copilot studio", "microsoft copilot studio")
MISSION_WORDS = {"deploy", "install", "build", "publish", "ship",
                 "locally", "local", "brainstem", "verify", "test", "the", "a", "an",
                 "agent", "to", "into", "my", "in", "for", "please", "and", "then"}


def _stack_context(request):
    """Resolve which library stack the request names, and build its context block."""
    reg = json.loads(_fetch("registry.json"))
    cleaned = request.lower()
    for phrase in MISSION_PHRASES:
        cleaned = cleaned.replace(phrase, " ")
    domain_words = " ".join(w for w in re.sub(r"[^a-z0-9 ]", " ", cleaned).split()
                            if w not in MISSION_WORDS)
    candidates = [a for a in reg.get("agents", [])
                  if a.get("name") != "@aibast-agents-library/sales-specialist-twin"]
    # The workshop shows sellers the ADVERTISED name, so that is what they say.
    # Fold the SharePoint crosswalk's names in as matchable aliases.
    aliases = {}
    try:
        cw = json.loads(_fetch("twin/sharepoint_crosswalk.json"))
        for e in cw.get("entries", []):
            if e.get("b_slug"):
                aliases.setdefault(e["b_slug"], []).append(e.get("sharepoint_name", ""))
    except Exception:  # noqa: BLE001 — aliases are a convenience, not a dependency
        pass
    # Slug tokens decide; description words only break ties. A big multi-agent
    # stack's rich description must never outscore an exact-name match (seen
    # live: "win loss analysis" landing on the deal-progression suite).
    words = set(domain_words.split())
    entry, score = None, 0
    for a in candidates:
        slug = a["name"].split("/")[1]
        slug_tokens = set(re.split(r"[^a-z0-9]+", slug.lower())) - {""}
        alias_names = aliases.get(slug, [])
        alias_tokens = set()
        for an in alias_names:
            alias_tokens |= set(re.split(r"[^a-z0-9]+", an.lower())) - {"", "agent"}
        hay = (a.get("display_name", "") + " " + " ".join(a.get("tags", [])) + " " +
               a.get("description", "") + " " + " ".join(alias_names)).lower()
        sc = (10 * len(words & slug_tokens) + 10 * len(words & alias_tokens)
              + sum(1 for w in words if w in hay))
        if sc > score:
            entry, score = a, sc
    if not entry or score == 0:
        return None, None
    stack_dir = os.path.dirname(entry["_file"]) + "/copilot_studio"
    try:
        man = json.loads(_fetch(f"{stack_dir}/manifest.json"))
    except Exception:  # noqa: BLE001 — stack has no Copilot Studio scaffold
        return entry, None
    base = f"https://raw.githubusercontent.com/{_active[0][0]}/{_active[0][1]}/{stack_dir}"
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
        # Tool name must be a bare identifier — the Copilot API rejects
        # function names containing @ or / and the tool silently never
        # registers. The library identity stays in __manifest__.
        self.name = "SalesSpecialistTwin"
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
            "- “How do I test the agent you deployed?”\n"
            "- “Give me the architecture review for the claims agent” — Well-Architected "
            "rigor with honest concessions, for technical audiences.\n\n"
            "**Your system, your adventure:** every use case defaults to Dynamics 365 but "
            "adapts to what you actually run — just say it: “deploy the deal progression "
            "agent for our Salesforce org” (also ServiceNow, SAP, Workday, or a custom REST "
            "API). Same logic, same Copilot Studio deployment, different hookup.\n\n"
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

        # First-party missions: context comes from the curated 1P catalog
        # (official docs links), not from library scaffolds.
        if mission.get("needs_first_party"):
            fp = json.loads(_fetch("twin/first_party.json"))
            agents = [dict(a, group=g["name"]) for g in fp.get("groups", [])
                      for a in g.get("agents", [])]
            hit, score = _match(request, agents, ["name", "summary", "id"])
            if not hit or score == 0:
                names = ", ".join(a["name"] for a in agents)
                return ("Which first-party agent? I know these: " + names + ".")
            ctx = (f"**First-party agent:** {hit['name']} ({hit['status']}) — {hit['group']}\n"
                   f"**What it does:** {hit['summary']}\n"
                   f"**Overview doc (authoritative):** {hit['overview']}\n"
                   f"**Configure doc (authoritative):** {hit['configure']}")
            playbook = playbook.replace("{{STACK_CONTEXT}}", ctx)

        # Inject live library context for stack-scoped missions.
        elif mission.get("needs_stack"):
            entry, ctx = _stack_context(request)
            if entry is None:
                return ("Which library agent do you mean? Say it by name — e.g. "
                        "“deploy the *field service dispatch* agent”. Ask `list_agents` "
                        "to see the catalog.")
            if ctx is None:
                # No authored scaffold: hand the engine the intent file itself and
                # tell it to derive the components by the same rules.
                base = (f"https://raw.githubusercontent.com/{_active[0][0]}/"
                        f"{_active[0][1]}/{entry['_file']}")
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

        arepo, aref = _active[0]
        araw = f"https://raw.githubusercontent.com/{arepo}/{aref}"
        playbook = playbook.replace("{{REPO}}", arepo).replace("{{REF}}", aref).replace("{{RAW}}", araw)

        # Choose-your-own-adventure: if the request names a system of record
        # (Salesforce, ServiceNow, SAP, Workday, a custom API), append the
        # authored mutation directive — same generic use case, Dynamics 365
        # default swapped for the system the customer actually runs.
        mutation = self._mutation_for(request)
        if mutation is not None:
            playbook += (f"\n\n---\n\n# MUTATION — adapt for {mutation['name']}\n\n"
                         f"{mutation['directive']}\n")
        return HARNESS_HEADER + "\n---\n\n" + playbook

    # ------------------------------------------------------------------
    def _mutation_for(self, request):
        words = set(re.sub(r"[^a-z0-9 ]", " ", (request or "").lower()).split())
        try:
            muts = json.loads(_fetch("twin/mutations.json")).get("mutations", [])
        except Exception:  # noqa: BLE001 — mutations are optional sugar
            return None
        for m in muts:
            if words & set(m.get("triggers", "").split()):
                return m
        return None


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = SalesSpecialistTwinAgent()
    print(agent.perform(operation="help"))
