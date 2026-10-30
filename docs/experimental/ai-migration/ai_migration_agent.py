"""
AI Migration agent: bring your setup from another AI assistant or AI coding
tool into your own Brainstem.

Experimental and not an officially supported Microsoft product or service.
Provided as is under the repository's MIT license, with no support or
warranty. Use at your own risk.

What it does, in order:
  scan     find setups on this device (or under a folder you name) and report
           names and counts only, never file contents
  plan     say what each found item becomes in a Brainstem, and what does not
           carry over
  apply    write everything to a NEW staging folder for review; never touches
           soul.md or existing agents; installs generated agents only with
           confirm=true; writes a manifest
  undo     remove exactly what one apply added, using its manifest
  compare  a short plain-words comparison

Rules it keeps:
  - dry run by default: apply and undo change nothing unless dry_run=false
  - carry everything but the keys: files named like credentials, tokens,
    auth or .env are skipped, and key-looking values are redacted
  - names and counts only in chat; file contents stay in files on this device
  - nothing leaves the device: no network calls, standard library only

Install: drop this one file into your Brainstem's agents/ folder.
Remove: delete the file.
"""

import fnmatch
import glob
import hashlib
import json
import os
import re
import shutil
import zipfile
from datetime import datetime

try:
    from agents.basic_agent import BasicAgent
except ImportError:  # running outside a Brainstem (tests, plain Python)
    try:
        from basic_agent import BasicAgent
    except ImportError:
        class BasicAgent:
            def __init__(self, name=None, metadata=None):
                if name is not None:
                    self.name = name
                if metadata is not None:
                    self.metadata = metadata


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@aibast-agents-library/ai-migration",
    "version": "1.0.0",
    "display_name": "AI Migration",
    "description": (
        "Bring your instructions, skills, tools and memory from another AI "
        "assistant or AI coding tool into your own Brainstem, as plain files "
        "on your device."
    ),
    "author": "AIBAST",
    "tags": ["experimental", "migration", "local-first", "setup"],
    "category": "experimental",
    "quality_tier": "experimental",
    "requires_env": [],
    "example_call": "Scan this device for AI setups I can bring into my Brainstem.",
}


# ── Detection table ──────────────────────────────────────────────────────────
# Where each known setup keeps its files. Source ids are neutral on purpose.
# "~" is the home folder (or the folder you pass as home_path); "{project}" is
# the project folder you pass as project_path (skipped when none is given).
DETECTION = {
    "coding-tool-a": {
        "folder": "~/.claude",
        "label": "an AI coding tool",
        "instructions": [
            "~/.claude/CLAUDE.md",
            "{project}/CLAUDE.md",
            "{project}/.claude/CLAUDE.md",
            "{project}/CLAUDE.local.md",
        ],
        "skills": [
            "~/.claude/skills/*/SKILL.md",
            "{project}/.claude/skills/*/SKILL.md",
        ],
        "subagents": [
            "~/.claude/agents/**/*.md",
            "{project}/.claude/agents/**/*.md",
        ],
        "commands": [
            "~/.claude/commands/**/*.md",
            "{project}/.claude/commands/**/*.md",
        ],
        "mcp_json": [
            ("~/.claude.json", "mcpServers"),
            ("~/.claude.json", "projects.*.mcpServers"),
            ("~/.claude/settings.json", "mcpServers"),
            ("{project}/.mcp.json", "mcpServers"),
        ],
        "hooks_json": [
            "~/.claude/settings.json",
            "~/.claude/settings.local.json",
            "{project}/.claude/settings.json",
            "{project}/.claude/settings.local.json",
        ],
        "memory": ["~/.claude/projects/*/memory/*.md"],
    },
    "coding-tool-b": {
        "folder": "~/.gemini",
        "label": "an AI coding tool",
        "instructions": ["~/.gemini/GEMINI.md", "{project}/GEMINI.md"],
        "commands": [
            "~/.gemini/commands/**/*.toml",
            "{project}/.gemini/commands/**/*.toml",
        ],
        "mcp_json": [
            ("~/.gemini/settings.json", "mcpServers"),
            ("{project}/.gemini/settings.json", "mcpServers"),
        ],
        "extensions": ["~/.gemini/extensions/*/gemini-extension.json"],
    },
    "coding-tool-c": {
        "folder": "~/.codex and ~/.agents",
        "label": "an AI coding tool",
        "instructions": [
            "~/.codex/AGENTS.md",
            "~/.codex/AGENTS.override.md",
            "{project}/AGENTS.md",
        ],
        "commands": ["~/.codex/prompts/*.md"],
        "skills": [
            "~/.agents/skills/*/SKILL.md",
            "{project}/.agents/skills/*/SKILL.md",
        ],
        "mcp_toml": [
            ("~/.codex/config.toml", "mcp_servers"),
            ("{project}/.codex/config.toml", "mcp_servers"),
        ],
    },
    "assistant-export": {
        # A data-export zip or folder you downloaded from a hosted assistant.
        "folder": "(the export you name)",
        "label": "a hosted AI assistant export",
        "conversations": ["conversations.json"],
        "archive_also": ["chat.html"],
    },
}

SOURCE_IDS = tuple(DETECTION)

# The model reading these replies must not turn folders into product names.
NAMING_RULE = "Describe each setup by its folder; don't name products."

# What each item type becomes in a Brainstem.
BECOMES = {
    "instructions": "a soul addition (soul.import.md, you merge it)",
    "skill": "a generated single-file agent",
    "subagent": "a generated single-file agent",
    "command": "a generated single-file agent",
    "extension": "its context file joins the soul addition; its tool servers need a bridge",
    "mcp": "needs a bridge (listed in mcp.bridge.json, keys stripped)",
    "hook": "not carried (see below)",
    "memory": "memory entries (memory.import.md)",
    "conversations": "optional read-only archive (include_conversations=true)",
}

NOT_CARRIED = [
    "Hooks are not carried. They run shell commands when the other tool fires "
    "an event. A Brainstem has no event hooks: it answers /chat and runs the "
    "agents you call. Rebuild a hook you still need as an agent you call on purpose.",
    "Tool servers (MCP) are not run by a Brainstem. They are listed with their "
    "keys stripped so you can put a bridge agent or a sidecar in front of them.",
    "Keys, tokens, sign-ins and .env files are never read or copied. Set them "
    "again on this device where each tool needs them.",
    "Custom assistants that have no file export: copy their instructions into "
    "soul.import.md by hand.",
]

COMPARE = """Plain-words comparison. Pricing changes often: check each provider's own pricing page.

| | Hosted AI assistant | Cloud AI coding tool | Your Brainstem |
|---|---|---|---|
| Architecture | A web or mobile app; the provider runs it | A local app or terminal tool that calls the provider's models | A small local server on your device that calls models through GitHub Copilot |
| Plugins / extensions | The provider's own add-ons and connectors | Config-file plugins, skills, commands and tool servers | Single-file Python agents in your agents/ folder |
| Where your data lives | Mostly in the provider's account | Config and history in a folder on your device; prompts go to the provider | soul.md, agents and memory as plain files on your device; prompts go to the model you choose |
| Cost model | Subscription tiers | Subscription tiers or per-token API billing | Your existing GitHub Copilot plan |

GitHub Copilot offers models from several providers, so you keep model choice. What you own is your setup."""


# ── Safety: carry everything but the keys ────────────────────────────────────
_SECRET_NAME = re.compile(
    r"(auth|credential|secret|token|oauth|password|passwd|cookie|session|"
    r"keychain|api[_-]?key|private[_-]?key|^\.env|\.env$|\.env\.|\.pem$|\.key$|\.p12$|\.pfx$|id_rsa|id_ed25519)",
    re.IGNORECASE,
)
_SECRET_VALUE_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),
    re.compile(r"xox[abprs]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-~+/]{12,}=*"),
]
_ASSIGNMENT = re.compile(
    r"(?i)\b([A-Z0-9_\-]*(?:key|token|secret|password|passwd|pwd|credential|auth)[A-Z0-9_\-]*)"
    r"(\s*[:=]\s*[\"']?)([^\s\"',}]{4,})"
)
_LONG_RANDOM = re.compile(r"\b(?=[A-Za-z0-9_\-+=]*\d)(?=[A-Za-z0-9_\-+=]*[A-Za-z])[A-Za-z0-9_\-+=]{32,}\b")
_SECRET_FLAG = re.compile(r"(?i)^--?[a-z0-9_\-]*(key|token|secret|password|auth|credential)[a-z0-9_\-]*$")
REDACTED = "[REDACTED]"


def redact_text(text):
    """Replace key-looking values. Used on everything that gets staged."""
    if not isinstance(text, str):
        return text
    for pattern in _SECRET_VALUE_PATTERNS:
        text = pattern.sub(REDACTED, text)
    text = _ASSIGNMENT.sub(lambda m: m.group(1) + m.group(2) + REDACTED, text)
    text = _LONG_RANDOM.sub(REDACTED, text)
    return text


def _is_secret_name(name):
    return bool(_SECRET_NAME.search(name))


def _strip_url(url):
    """Keep scheme, host and path; drop user info, query and fragment."""
    if not isinstance(url, str):
        return None
    match = re.match(r"^([a-zA-Z][a-zA-Z0-9+.\-]*://)(?:[^@/]*@)?([^/?#]*)([^?#]*)", url)
    if not match:
        return REDACTED
    return redact_text(match.group(1) + match.group(2) + match.group(3))


def redact_server(name, config):
    """A tool-server entry with every secret stripped: env and header values
    are dropped, args and URLs are scrubbed, unknown keys are not kept."""
    config = config if isinstance(config, dict) else {}
    out = {"name": redact_text(str(name)), "status": "needs a bridge"}
    kind = config.get("type") or config.get("transport")
    if isinstance(kind, str):
        out["type"] = kind
    command = config.get("command")
    if isinstance(command, str) and command:
        out["command"] = redact_text(os.path.basename(command))
    args = config.get("args")
    if isinstance(args, list):
        cleaned, hide_next = [], False
        for arg in args:
            arg = str(arg)
            if hide_next:
                cleaned.append(REDACTED)
                hide_next = False
                continue
            if "=" in arg and _SECRET_FLAG.match(arg.split("=", 1)[0]):
                cleaned.append(arg.split("=", 1)[0] + "=" + REDACTED)
                continue
            if _SECRET_FLAG.match(arg):
                hide_next = True
            if arg.startswith(("/", "~")) or re.match(r"^[A-Za-z]:\\", arg):
                arg = os.path.basename(arg)
            cleaned.append(redact_text(arg))
        out["args"] = cleaned
    for url_key in ("url", "httpUrl", "serverUrl"):
        if url_key in config:
            out["url"] = _strip_url(config.get(url_key))
    for secret_block in ("env", "headers", "http_headers", "env_http_headers"):
        block = config.get(secret_block)
        if isinstance(block, dict) and block:
            out[secret_block + "_names"] = sorted(str(k) for k in block)
    if config.get("bearer_token_env_var"):
        out["bearer_token_env_var"] = "set on your device"
    out["note"] = "Values for env and headers were not copied. Set them again on this device."
    return out


# ── Small readers ────────────────────────────────────────────────────────────
_MAX_TEXT = 2_000_000


def _read_text(path):
    try:
        if os.path.getsize(path) > _MAX_TEXT:
            return None
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return None


def _read_json(path):
    text = _read_text(path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return None


def _read_toml(path):
    text = _read_text(path)
    if text is None:
        return None
    try:
        import tomllib  # Python 3.11+
        return tomllib.loads(text)
    except ImportError:
        return _mini_toml(text)
    except Exception:
        return None


def _mini_toml(text):
    """Enough TOML for [a.b] tables with key = "string" lines (Python < 3.11)."""
    data = {}
    current = data
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        table = re.match(r"^\[([^\]]+)\]$", line)
        if table:
            current = data
            for part in table.group(1).split("."):
                current = current.setdefault(part.strip().strip('"'), {})
            continue
        pair = re.match(r'^([A-Za-z0-9_\-]+)\s*=\s*(.+)$', line)
        if pair:
            value = pair.group(2).strip()
            if value.startswith(('"', "'")):
                value = value[1:-1] if len(value) > 1 else ""
            elif value.startswith("["):
                value = re.findall(r'"([^"]*)"', value)
            current[pair.group(1)] = value
    return data


def _frontmatter(text):
    """name/description from a leading --- block, if present."""
    meta = {}
    if not text or not text.startswith("---"):
        return meta, text or ""
    end = text.find("\n---", 3)
    if end == -1:
        return meta, text
    for line in text[3:end].splitlines():
        match = re.match(r"^([A-Za-z_\-]+)\s*:\s*(.*)$", line.strip())
        if match:
            meta[match.group(1).lower()] = match.group(2).strip().strip('"').strip("'")
    return meta, text[end + 4:].lstrip("\n")


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _slug(text):
    slug = re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")
    return slug[:40] or "item"


# ── Scan ─────────────────────────────────────────────────────────────────────
class _Scan:
    def __init__(self, home, project, export):
        self.home = os.path.abspath(os.path.expanduser(home))
        self.project = os.path.abspath(os.path.expanduser(project)) if project else None
        self.export = os.path.abspath(os.path.expanduser(export)) if export else None
        self.items = []
        self.skipped = 0

    def display(self, path):
        path = os.path.abspath(path)
        if self.project and (path == self.project or path.startswith(self.project + os.sep)):
            return "<project>" + path[len(self.project):]
        if path == self.home or path.startswith(self.home + os.sep):
            return "~" + path[len(self.home):]
        return path

    def expand(self, pattern):
        if pattern.startswith("{project}"):
            if not self.project:
                return None
            return self.project + pattern[len("{project}"):]
        if pattern.startswith("~"):
            return self.home + pattern[1:]
        return pattern

    def files(self, pattern):
        expanded = self.expand(pattern)
        if not expanded:
            return []
        found = []
        for path in sorted(glob.glob(expanded, recursive=True)):
            if not os.path.isfile(path) or os.path.islink(path):
                continue
            base = self.project if (self.project and path.startswith(self.project + os.sep)) else self.home
            relative = os.path.relpath(path, base)
            if any(_is_secret_name(part) for part in relative.split(os.sep)):
                self.skipped += 1
                continue
            found.append(path)
        return found

    def add(self, source, kind, name, path, **extra):
        item = {"source": source, "kind": kind, "name": name, "path": path}
        item.update(extra)
        self.items.append(item)

    def run(self, sources):
        for source in sources:
            spec = DETECTION[source]
            if source == "assistant-export":
                self._scan_export(source, spec)
                continue
            for pattern in spec.get("instructions", []):
                for path in self.files(pattern):
                    self.add(source, "instructions", self.display(path), path)
            for pattern in spec.get("skills", []):
                for path in self.files(pattern):
                    self.add(source, "skill", os.path.basename(os.path.dirname(path)), path)
            for pattern in spec.get("subagents", []):
                for path in self.files(pattern):
                    self.add(source, "subagent", os.path.splitext(os.path.basename(path))[0], path)
            for pattern in spec.get("commands", []):
                root = self.expand(pattern.split("*")[0].rstrip("/"))
                for path in self.files(pattern):
                    rel = os.path.relpath(path, root) if root else os.path.basename(path)
                    name = os.path.splitext(rel)[0].replace(os.sep, ":")
                    self.add(source, "command", name, path)
            for pattern, key in spec.get("mcp_json", []):
                for path in self.files(pattern):
                    self._servers_from(source, path, _read_json(path), key)
            for pattern, key in spec.get("mcp_toml", []):
                for path in self.files(pattern):
                    self._servers_from(source, path, _read_toml(path), key)
            for pattern in spec.get("hooks_json", []):
                for path in self.files(pattern):
                    data = _read_json(path)
                    hooks = data.get("hooks") if isinstance(data, dict) else None
                    if isinstance(hooks, dict):
                        for event, handlers in hooks.items():
                            count = len(handlers) if isinstance(handlers, list) else 1
                            self.add(source, "hook", str(event), path, count=count)
            for pattern in spec.get("memory", []):
                for path in self.files(pattern):
                    project_folder = os.path.basename(os.path.dirname(os.path.dirname(path)))
                    name = project_folder[-24:] + "/" + os.path.basename(path)
                    self.add(source, "memory", name, path)
            for pattern in spec.get("extensions", []):
                for path in self.files(pattern):
                    data = _read_json(path) or {}
                    folder = os.path.dirname(path)
                    ext_name = str(data.get("name") or os.path.basename(folder))
                    self.add(source, "extension", ext_name, path)
                    context_name = data.get("contextFileName") or "GEMINI.md"
                    names = context_name if isinstance(context_name, list) else [context_name]
                    for context in names:
                        context_path = os.path.join(folder, os.path.basename(str(context)))
                        if os.path.isfile(context_path) and not _is_secret_name(os.path.basename(context_path)):
                            self.add(source, "instructions", ext_name + "/" + os.path.basename(context_path), context_path)
                    servers = data.get("mcpServers")
                    if isinstance(servers, dict):
                        for server, config in servers.items():
                            self.add(source, "mcp", ext_name + "/" + str(server), path, config=config)
        return self

    def _servers_from(self, source, path, data, key):
        if not isinstance(data, dict):
            return
        if key.startswith("projects.*."):
            projects = data.get("projects")
            if isinstance(projects, dict):
                for project_data in projects.values():
                    if isinstance(project_data, dict):
                        self._servers_from(source, path, project_data, key[len("projects.*."):])
            return
        servers = data.get(key)
        if isinstance(servers, dict):
            for server, config in servers.items():
                self.add(source, "mcp", str(server), path, config=config)

    def _scan_export(self, source, spec):
        if not self.export:
            return
        wanted = spec["conversations"] + spec["archive_also"]
        if zipfile.is_zipfile(self.export):
            with zipfile.ZipFile(self.export) as archive:
                for member in archive.namelist():
                    base = os.path.basename(member)
                    if _is_secret_name(base):
                        self.skipped += 1
                        continue
                    if base in spec["conversations"]:
                        count = _conversation_count(archive.read(member))
                        self.add(source, "conversations", base, self.export, member=member, count=count)
                    elif base in wanted:
                        self.add(source, "archive-file", base, self.export, member=member)
        elif os.path.isdir(self.export):
            for path in sorted(glob.glob(os.path.join(self.export, "**", "*"), recursive=True)):
                base = os.path.basename(path)
                if not os.path.isfile(path) or os.path.islink(path):
                    continue
                if _is_secret_name(base):
                    self.skipped += 1
                    continue
                if base in spec["conversations"]:
                    with open(path, "rb") as handle:
                        count = _conversation_count(handle.read())
                    self.add(source, "conversations", base, path, count=count)
                elif base in wanted:
                    self.add(source, "archive-file", base, path)


def _conversation_count(raw):
    try:
        data = json.loads(raw.decode("utf-8", errors="replace"))
    except ValueError:
        return 0
    return len(data) if isinstance(data, list) else 0


# ── Generated agents ─────────────────────────────────────────────────────────
_AGENT_TEMPLATE = '''"""
Generated by AI Migration on {date} from a {kind} found at {where}.
Review it before you rely on it. Delete this file to remove it.
"""

try:
    from agents.basic_agent import BasicAgent
except ImportError:
    class BasicAgent:
        def __init__(self, name=None, metadata=None):
            self.name, self.metadata = name, metadata

_INSTRUCTIONS = {instructions}


class {class_name}(BasicAgent):
    def __init__(self):
        self.name = {tool_name}
        self.metadata = {{
            "name": self.name,
            "description": {description},
            "parameters": {{
                "type": "object",
                "properties": {{
                    "task": {{
                        "type": "string",
                        "description": "What the user wants done with these instructions.",
                    }}
                }},
                "required": [],
            }},
        }}
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, task="", **kwargs):
        return (
            "Follow these imported instructions for the task"
            + (": " + str(task) if task else ".")
            + "\\n\\n"
            + _INSTRUCTIONS
        )
'''


def _generated_agent(item, scan, used_names, date):
    text = _read_text(item["path"]) or ""
    if item["path"].endswith(".toml"):
        data = _read_toml(item["path"]) or {}
        body = str(data.get("prompt") or "")
        description = str(data.get("description") or "")
    else:
        meta, body = _frontmatter(text)
        description = meta.get("description", "")
    body = redact_text(body.strip())
    if not description:
        first = next((line.strip("# ").strip() for line in body.splitlines() if line.strip()), "")
        description = first[:160]
    description = redact_text(
        "Imported " + item["kind"] + " '" + item["name"] + "'. " + (description or "Use when the user asks for it.")
    )[:900]
    slug = _slug(item["name"])
    tool_name = "Imported_" + slug
    counter = 2
    while tool_name in used_names:
        tool_name = "Imported_" + slug + "_" + str(counter)
        counter += 1
    used_names.add(tool_name)
    file_slug = tool_name[len("Imported_"):]
    class_name = "Imported" + "".join(part.capitalize() for part in file_slug.split("_") if part) + "Agent"
    source = _AGENT_TEMPLATE.format(
        date=date,
        kind=item["kind"],
        where=scan.display(item["path"]).replace('"', "'"),
        instructions=json.dumps(body),
        class_name=class_name,
        tool_name=json.dumps(tool_name),
        description=json.dumps(description),
    )
    return "imported_" + file_slug + "_agent.py", source


# ── The agent ────────────────────────────────────────────────────────────────
class AIMigrationAgent(BasicAgent):
    def __init__(self):
        self.name = "AIMigration"
        self.metadata = {
            "name": self.name,
            "description": (
                "Brings a person's setup from another AI assistant or AI coding tool "
                "(instructions, skills, commands, tool servers, memory, exported "
                "conversations) into this Brainstem as plain local files. Actions: "
                "scan (find setups, names and counts only), plan (what each item "
                "becomes and what does not carry over), apply (write a staging folder "
                "for review; dry run unless dry_run is false; installs generated agents "
                "only with confirm true), undo (remove exactly what an apply added), "
                "compare (plain-words comparison). Never reads keys or credentials, "
                "never returns file contents, and nothing leaves the device. "
                "Describe each setup by its folder; don't name products."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["scan", "plan", "apply", "undo", "compare"],
                        "description": "What to do. Start with scan, then plan, then apply.",
                    },
                    "source": {
                        "type": "string",
                        "enum": ["all"] + list(SOURCE_IDS),
                        "description": "Which setup to look at. Default all.",
                    },
                    "home_path": {
                        "type": "string",
                        "description": "Look under this folder instead of the home folder.",
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Optional project folder to include project-level files.",
                    },
                    "export_path": {
                        "type": "string",
                        "description": "Optional path to a downloaded data-export zip or folder.",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "Default true. Set false to really write (apply) or remove (undo).",
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "Apply only: also copy generated agents into the agents folder. Default false.",
                    },
                    "include_conversations": {
                        "type": "boolean",
                        "description": "Apply only: also stage exported conversations as a read-only archive.",
                    },
                    "import_id": {
                        "type": "string",
                        "description": "Undo only: which import to remove. Default the most recent.",
                    },
                },
                "required": ["action"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    # Paths the agent writes to. Overridable for tests and throwaway runs.
    def _imports_root(self):
        return os.path.abspath(os.path.expanduser(
            os.environ.get("AI_MIGRATION_IMPORTS_DIR") or "~/.brainstem/imports"
        ))

    def _agents_dir(self):
        configured = os.environ.get("AGENTS_PATH")
        if configured and os.path.isabs(configured):
            return configured
        return os.path.dirname(os.path.abspath(__file__))

    def perform(self, **kwargs):
        action = str(kwargs.get("action") or "scan").lower()
        try:
            if action == "compare":
                return COMPARE
            if action == "undo":
                return self._undo(kwargs)
            source = str(kwargs.get("source") or "all")
            if source != "all" and source not in DETECTION:
                return "Unknown source. Use one of: all, " + ", ".join(SOURCE_IDS) + "."
            sources = list(SOURCE_IDS) if source == "all" else [source]
            scan = _Scan(
                kwargs.get("home_path") or "~",
                kwargs.get("project_path"),
                kwargs.get("export_path"),
            ).run(sources)
            if action == "scan":
                return self._report_scan(scan)
            if action == "plan":
                return self._report_plan(scan)
            if action == "apply":
                return self._apply(scan, kwargs, source)
            return "Unknown action. Use scan, plan, apply, undo or compare."
        except Exception as exc:  # never leak a traceback with file contents
            return "AI Migration stopped: " + type(exc).__name__ + ". Nothing was changed after this point."

    # ── reports ──
    @staticmethod
    def _names(items, limit=12):
        names = [str(item["name"]) for item in items]
        shown = ", ".join(names[:limit])
        return shown + (" (+%d more)" % (len(names) - limit) if len(names) > limit else "")

    def _grouped(self, scan):
        groups = {}
        for item in scan.items:
            groups.setdefault(item["source"], {}).setdefault(item["kind"], []).append(item)
        return groups

    def _report_scan(self, scan):
        lines = ["Scan (read only). Names and counts only; no file contents were read into this reply."]
        groups = self._grouped(scan)
        if not groups:
            lines.append("No AI setups found under " + scan.display(scan.home) + ".")
        for source in SOURCE_IDS:
            if source not in groups:
                continue
            folder = DETECTION[source]["folder"]
            if source == "assistant-export" and scan.export:
                folder = os.path.basename(scan.export)
            lines.append("")
            lines.append("Setup in " + folder + " (" + DETECTION[source]["label"] + "):")
            for kind, items in groups[source].items():
                if kind == "conversations":
                    lines.append("- conversations: %d" % sum(i.get("count", 0) for i in items))
                elif kind == "hook":
                    lines.append("- hooks: %d (%s)" % (sum(i.get("count", 1) for i in items), self._names(items)))
                else:
                    label = {"archive-file": "other export files", "mcp": "tool servers (MCP)"}.get(kind, kind)
                    lines.append("- %s: %d (%s)" % (label, len(items), self._names(items)))
        if scan.skipped:
            lines.append("")
            lines.append("Skipped %d file(s) whose names look like keys, tokens or sign-ins. They were not opened." % scan.skipped)
        lines.append("")
        lines.append("Next: say \"plan\" to see what each item becomes in your Brainstem.")
        lines.append(NAMING_RULE)
        return "\n".join(lines)

    def _report_plan(self, scan):
        lines = ["Plan (nothing written yet)."]
        groups = self._grouped(scan)
        if not groups:
            return "Plan: nothing to bring over. Run scan with a home_path or export_path."
        counts = {}
        for item in scan.items:
            kind = "archive-file" if item["kind"] == "archive-file" else item["kind"]
            counts[kind] = counts.get(kind, 0) + (item.get("count", 1) if kind in ("conversations", "hook") else 1)
        for kind, label in BECOMES.items():
            if counts.get(kind):
                lines.append("- %d %s -> %s" % (counts[kind], kind if kind != "mcp" else "tool server(s)", label))
        lines.append("")
        lines.append("Does not carry over:")
        for note in NOT_CARRIED:
            lines.append("- " + note)
        lines.append("")
        lines.append("apply writes a new staging folder under " + self._display_root() +
                     " and never changes soul.md or your existing agents. "
                     "It is a dry run until you say dry_run false.")
        lines.append(NAMING_RULE)
        return "\n".join(lines)

    def _display_root(self):
        root = self._imports_root()
        home = os.path.expanduser("~")
        return "~" + root[len(home):] if root.startswith(home + os.sep) else root

    # ── apply ──
    def _build(self, scan, include_conversations):
        """Return {relative path: text or ('copy-member', ...)} for the staging folder."""
        date = datetime.now().strftime("%Y-%m-%d")
        files = {}
        soul, memory, servers, hooks = [], [], [], []
        used = set()
        for item in scan.items:
            kind = item["kind"]
            where = scan.display(item["path"])
            if kind == "instructions":
                text = _read_text(item["path"])
                if text is not None:
                    soul.append("## From " + where + "\n\n" + redact_text(text.strip()) + "\n")
            elif kind in ("skill", "subagent", "command"):
                name, source = _generated_agent(item, scan, used, date)
                files["agents/" + name] = source
            elif kind == "memory":
                text = _read_text(item["path"])
                if text is not None:
                    memory.append("## " + item["name"] + "\n\n" + redact_text(text.strip()) + "\n")
            elif kind == "mcp":
                servers.append(redact_server(item["name"], item.get("config")))
            elif kind == "hook":
                hooks.append(item["name"])
            elif kind in ("conversations", "archive-file") and include_conversations:
                if "member" in item:
                    with zipfile.ZipFile(item["path"]) as archive:
                        raw = archive.read(item["member"])
                else:
                    with open(item["path"], "rb") as handle:
                        raw = handle.read()
                files["archive/" + item["name"]] = redact_text(raw.decode("utf-8", errors="replace"))
        if soul:
            files["soul.import.md"] = (
                "# Soul additions to review\n\n"
                "Nothing here is loaded automatically. Copy the parts you want into your soul.md yourself.\n"
                "If you used custom assistants that have no file export, paste their instructions here too.\n\n"
                + "\n".join(soul)
            )
        if memory:
            files["memory.import.md"] = (
                "# Memory entries to review\n\n"
                "Ask your Brainstem to remember the ones you want to keep.\n\n" + "\n".join(memory)
            )
        if servers:
            files["mcp.bridge.json"] = json.dumps({"servers": servers}, indent=2) + "\n"
        review = ["# Review this import", "", "Created " + date + ". Nothing in this folder is active until you act on it.", ""]
        review += ["- " + path for path in sorted(files)]
        if hooks:
            review += ["", "Hooks not carried: " + ", ".join(sorted(set(hooks)))]
        review += ["", "Not carried over:"] + ["- " + note for note in NOT_CARRIED]
        files["REVIEW.md"] = redact_text("\n".join(review) + "\n")
        return files

    def _apply(self, scan, kwargs, source):
        if not scan.items:
            return "Apply: nothing to bring over, so nothing was written."
        dry_run = kwargs.get("dry_run", True) not in (False, "false", "False", 0, "0", "no")
        confirm = kwargs.get("confirm") in (True, "true", "True", 1, "1", "yes")
        include = kwargs.get("include_conversations") in (True, "true", "True", 1, "1", "yes")
        files = self._build(scan, include)
        agent_files = sorted(path for path in files if path.startswith("agents/"))
        stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        import_id = stamp + "-" + source
        root = self._imports_root()
        staging = os.path.join(root, import_id)
        suffix = 2
        while os.path.exists(staging):
            import_id = stamp + "-" + source + "-" + str(suffix)
            staging = os.path.join(root, import_id)
            suffix += 1
        if dry_run:
            lines = [
                "Apply (dry run, nothing written). It would create a new folder " +
                os.path.join(self._display_root(), import_id) + " with %d file(s):" % len(files),
            ]
            lines += ["- " + path for path in sorted(files) if not path.startswith("agents/")]
            if agent_files:
                lines.append("- agents/: %d generated agent(s)" % len(agent_files))
            lines.append("soul.md and your existing agents are not touched.")
            lines.append("Say \"apply with dry_run false\" to write it. Add confirm true to also install the generated agents.")
            lines.append(NAMING_RULE)
            return "\n".join(lines)

        os.makedirs(staging, exist_ok=False)
        manifest = {
            "schema": "ai-migration-import/1.0",
            "import_id": import_id,
            "created": datetime.now().isoformat(timespec="seconds"),
            "staging_dir": staging,
            "files": [],
            "installed": [],
            "skipped_existing": [],
        }
        for relative, text in sorted(files.items()):
            target = os.path.join(staging, *relative.split("/"))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "x", encoding="utf-8") as handle:
                handle.write(text)
            manifest["files"].append({"path": target, "sha256": _sha256(target)})
        if confirm and agent_files:
            agents_dir = self._agents_dir()
            for relative in agent_files:
                target = os.path.join(agents_dir, os.path.basename(relative))
                if os.path.exists(target):
                    manifest["skipped_existing"].append(os.path.basename(relative))
                    continue
                shutil.copyfile(os.path.join(staging, *relative.split("/")), target)
                manifest["installed"].append({"path": target, "sha256": _sha256(target)})
        with open(os.path.join(staging, "manifest.json"), "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2)
        lines = [
            "Apply done. Wrote %d file(s) to %s." % (len(manifest["files"]), os.path.join(self._display_root(), import_id)),
            "Generated agents: %d. Installed into your agents folder: %d." % (len(agent_files), len(manifest["installed"])),
        ]
        if manifest["skipped_existing"]:
            lines.append("Not installed because a file with that name already exists: %d." % len(manifest["skipped_existing"]))
        if agent_files and not confirm:
            lines.append("To install the generated agents, run apply again with confirm true, or copy them yourself.")
        lines.append("Review soul.import.md and merge what you want into soul.md yourself.")
        lines.append("To remove all of it: undo with import_id " + import_id + " and dry_run false.")
        lines.append(NAMING_RULE)
        return "\n".join(lines)

    # ── undo ──
    def _undo(self, kwargs):
        root = self._imports_root()
        import_id = kwargs.get("import_id")
        if import_id:
            if os.sep in str(import_id) or str(import_id).startswith("."):
                return "Undo: that import id is not valid."
            manifest_path = os.path.join(root, str(import_id), "manifest.json")
        else:
            candidates = sorted(glob.glob(os.path.join(root, "*", "manifest.json")))
            if not candidates:
                return "Undo: no imports found."
            manifest_path = candidates[-1]
        manifest = _read_json(manifest_path)
        if not isinstance(manifest, dict) or manifest.get("schema") != "ai-migration-import/1.0":
            return "Undo: no manifest found for that import."
        staging = os.path.dirname(manifest_path)
        entries = list(manifest.get("installed", [])) + list(manifest.get("files", []))
        agents_dir = self._agents_dir()
        allowed = []
        for entry in entries:
            path = os.path.abspath(str(entry.get("path", "")))
            inside = path.startswith(staging + os.sep) or (
                os.path.dirname(path) == os.path.abspath(agents_dir)
                and fnmatch.fnmatch(os.path.basename(path), "imported_*_agent.py")
            )
            if inside:
                allowed.append((path, entry.get("sha256")))
        dry_run = kwargs.get("dry_run", True) not in (False, "false", "False", 0, "0", "no")
        if dry_run:
            return ("Undo (dry run, nothing removed). It would remove %d file(s) from import %s, "
                    "including %d installed agent(s). Say \"undo with dry_run false\" to do it."
                    % (len(allowed), os.path.basename(staging), len(manifest.get("installed", []))))
        removed, kept = 0, 0
        for path, digest in allowed:
            if not os.path.isfile(path):
                continue
            if digest and _sha256(path) != digest:
                kept += 1  # changed since apply; leave the person's edits alone
                continue
            os.remove(path)
            removed += 1
        if kept == 0:
            os.remove(manifest_path)
        for folder, _dirs, _files in sorted(os.walk(staging), key=lambda entry: -len(entry[0])):
            try:
                os.rmdir(folder)
            except OSError:
                pass
        message = "Undo done. Removed %d file(s) from import %s." % (removed, os.path.basename(staging))
        if kept:
            message += " Kept %d file(s) you changed since the import, and the manifest." % kept
        return message
