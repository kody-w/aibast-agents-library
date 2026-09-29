"""GitHub Copilot is the default workshop engine; the RAPP Brainstem is opt-in.

Every AIBAST workshop must be completable with GitHub Copilot and Copilot
Studio alone. The Brainstem stays available as an optional lane that learners
select in Workshop settings, so no page may fall back to it or present
installing it as a required step.
"""

import json
import re
import subprocess
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

from tests.test_achievement_points import extract_function
from tests.test_scaffold_solution_journey_parity import advertised_slugs
from tools import scaffold_solution_journey as scaffold


ROOT = Path(__file__).resolve().parent.parent
SETTINGS = ROOT / "solutions" / "_shared" / "workshop-settings.html"
HOMEPAGE = ROOT / "index.html"
ACADEMY = ROOT / "academy.html"
README = ROOT / "README.md"
REPRESENTATIVE_QUEST = ROOT / "solutions" / "time-entry-billing" / "quest.html"

# Inline engine readers per generated page: the storage seed, the visual
# engine, and the quest's achievement lane.
ENGINE_READERS = {
    "quest.html": 3,
    "field-guide.html": 2,
    "manual-tutorial.html": 1,
}
WORKSHOP_COPY = (
    "quest.html",
    "field-guide.html",
    "manual-tutorial.html",
    "FIELD-GUIDE.md",
    "EASY-MODE-PERSONLESS.md",
    "EASY-MODE-COPILOT-CHAT.md",
    "README.md",
    "export-manifest.json",
)
COPILOT_DEFAULT = re.compile(
    r"""===\s*(["'])brainstem\1\s*\?\s*(["'])brainstem\2\s*:\s*(["'])copilot\3"""
)
BRAINSTEM_FALLBACK = re.compile(
    r"""\?\s*(["'])copilot\1\s*:\s*(["'])brainstem\2"""
    r"""|(?:\|\||\?\?)\s*(["'])brainstem\3"""
)
BRAINSTEM_PREREQUISITE = (
    re.compile(
        r"\binstall(?:s|ing)?\s+(?:the\s+)?(?:stable\s+)?(?:local\s+)?"
        r"(?:RAPP\s+)?Brainstem\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?<!no )(?<!no RAPP )\bBrainstem(?:\s+install(?:ation)?)?"
        r"\s+(?:is|are)\s+required\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\brequires?\s+(?:the\s+)?(?:local\s+)?(?:RAPP\s+)?Brainstem\b",
        re.IGNORECASE,
    ),
    re.compile(r"(?<!optional )\bpre-work:", re.IGNORECASE),
    re.compile(
        r"\bdefaults?\b[^.<\n]{0,40}\bto\s+(?:the\s+)?Brainstem\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bstep\s*(?:1|one)\b[^.<\n]{0,80}\bBrainstem\b",
        re.IGNORECASE,
    ),
)
CAPABILITY_CARD = re.compile(
    r'<article class="capability-card">\s*<code>(.*?)</code>\s*'
    r"<strong>(.*?)</strong>\s*<p>(.*?)</p>\s*</article>",
    re.DOTALL,
)
GENERATED_PAGES = (
    "quest.html",
    "field-guide.html",
    "manual-tutorial.html",
    "evidence-report.html",
)
LANES = {"copilot", "brainstem"}


class LaneBlockParser(HTMLParser):
    """Record where each lane block starts; CSS and script text is ignored."""

    def __init__(self):
        super().__init__()
        self.starts = {}

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()
        if "data-easy-lane" in attributes:
            marker, lane = "data-easy-lane", attributes["data-easy-lane"]
        elif "engine-panel" in classes:
            marker = "engine-panel"
            lane = next((token for token in classes if token in LANES), None)
        else:
            return
        if lane in LANES:
            self.starts.setdefault(marker, {}).setdefault(lane, self.getpos())


def lane_block_offsets(text):
    parser = LaneBlockParser()
    parser.feed(text)
    parser.close()
    line_starts = [0]
    line_starts.extend(index + 1 for index, char in enumerate(text) if char == "\n")
    return {
        marker: {
            lane: line_starts[line - 1] + column
            for lane, (line, column) in lanes.items()
        }
        for marker, lanes in parser.starts.items()
    }


def prerequisite_phrases(text):
    return [
        match.group(0)
        for pattern in BRAINSTEM_PREREQUISITE
        for match in pattern.finditer(text)
    ]


def run_node(source, path):
    path.write_text(source, encoding="utf-8")
    result = subprocess.run(
        ["node", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def learn_and_build_block():
    text = HOMEPAGE.read_text(encoding="utf-8")
    start = text.index("<h3>Learn and build</h3>")
    end = text.index('<div class="detail-actions">', start)
    return text[start:end]


def test_every_workshop_engine_reader_defaults_to_copilot():
    offenders = []
    for slug in advertised_slugs():
        for name, readers in ENGINE_READERS.items():
            text = (ROOT / "solutions" / slug / name).read_text(encoding="utf-8")
            if BRAINSTEM_FALLBACK.search(text):
                offenders.append(f"{slug}/{name}: falls back to the Brainstem")
            if len(COPILOT_DEFAULT.findall(text)) != readers:
                offenders.append(f"{slug}/{name}: lacks {readers} Copilot defaults")

    tracked = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.html", "*.js", "*.mjs", "*.py"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8").split("\0")
    shared_readers = [
        ROOT / name
        for name in tracked
        if name
        and not name.startswith("tests/")
        and not re.match(r"solutions/(?!_shared/)", name)
        and "node_modules/" not in name
        and "aibast:workshop-engine"
        in (ROOT / name).read_text(encoding="utf-8", errors="ignore")
    ]
    assert SETTINGS in shared_readers and HOMEPAGE in shared_readers
    for path in shared_readers:
        if BRAINSTEM_FALLBACK.search(path.read_text(encoding="utf-8")):
            offenders.append(f"{path.relative_to(ROOT)}: falls back to the Brainstem")

    for name in ("WORKSHOP_STORAGE_SCRIPT", "WORKSHOP_ENGINE_SCRIPT"):
        script = getattr(scaffold, name)
        if BRAINSTEM_FALLBACK.search(script) or not COPILOT_DEFAULT.search(script):
            offenders.append(f"scaffold {name}: does not default to Copilot")

    settings = SETTINGS.read_text(encoding="utf-8")
    brainstem_option = settings.split('value="brainstem"', 1)[1].split("</label>", 1)[0]
    if re.search(r"\b(?:Default|Recommended)\b", brainstem_option):
        offenders.append("workshop-settings.html: Brainstem option is labeled default")
    assert offenders == []


def test_engine_readers_resolve_copilot_unless_the_learner_opts_into_brainstem(
    tmp_path,
):
    quest = REPRESENTATIVE_QUEST.read_text(encoding="utf-8")
    assert scaffold.WORKSHOP_STORAGE_SCRIPT in quest
    assert scaffold.WORKSHOP_ENGINE_SCRIPT in quest
    quest_script = re.findall(r"<script>(.*?)</script>", quest, re.DOTALL)[-1]
    current_easy_path = extract_function(quest_script, "currentEasyPath")
    configured_engine = re.search(
        r"const configuredEngine = .*?;",
        HOMEPAGE.read_text(encoding="utf-8"),
        re.DOTALL,
    ).group(0)
    probe = f"""
const storageSource = {json.dumps(scaffold.WORKSHOP_STORAGE_SCRIPT)};
const engineSource = {json.dumps(scaffold.WORKSHOP_ENGINE_SCRIPT)};
function install(stored, denied) {{
  const attributes = {{}};
  globalThis.document = {{
    documentElement: {{
      setAttribute(name, value) {{ attributes[name] = value; }},
    }},
  }};
  const guard = () => {{ if (denied) throw new Error("storage denied"); }};
  globalThis.localStorage = {{
    getItem(key) {{ guard(); return key === "aibast:workshop-engine" ? stored : null; }},
    setItem() {{ guard(); }},
    removeItem() {{ guard(); }},
  }};
  return attributes;
}}
function visual(stored, denied = false) {{
  const attributes = install(stored, denied);
  Function(storageSource)();
  Function(engineSource)();
  return attributes["data-workshop-engine"];
}}
function achievement(stored) {{
  const localStorage = {{ getItem: () => stored }};
  const globalEngineKey = "aibast:workshop-engine";
  return Function(
    "localStorage",
    "globalEngineKey",
    {json.dumps(current_easy_path)} + "\\nreturn currentEasyPath();",
  )(localStorage, globalEngineKey);
}}
function homepage(stored) {{
  const localStorage = {{ getItem: () => stored }};
  return Function(
    "localStorage",
    {json.dumps(configured_engine)} + "\\nreturn configuredEngine;",
  )(localStorage);
}}
const values = [null, "", "invalid", "BRAINSTEM", "copilot", "brainstem"];
console.log(JSON.stringify({{
  visual: values.map((value) => visual(value)),
  visualDenied: visual("brainstem", true),
  achievement: values.map((value) => achievement(value)),
  homepage: values.map((value) => homepage(value)),
}}));
"""
    result = run_node(probe, tmp_path / "engine-defaults.js")

    expected = ["copilot"] * 5 + ["brainstem"]
    assert result["visual"] == expected
    assert result["visualDenied"] == "copilot"
    assert result["achievement"] == expected
    assert result["homepage"] == ["GitHub Copilot"] * 5 + [
        "GitHub Copilot + Brainstem (optional)"
    ]


def test_homepage_learn_and_build_never_requires_the_brainstem():
    block = learn_and_build_block()
    intro = re.search(r"<p>(.*?)</p>", block, re.DOTALL).group(1)
    cards = CAPABILITY_CARD.findall(block)

    assert prerequisite_phrases(block) == []
    assert "no RAPP Brainstem install is required" in intro
    assert cards and cards[0][0] == "Step 1"
    for code, title, body in cards:
        if code.startswith("Step"):
            assert "brainstem" not in title.lower(), title
    brainstem_cards = [
        (code, title, body)
        for code, title, body in cards
        if "Brainstem" in title and "configuredEngine" not in title
    ]
    assert brainstem_cards, "the optional Brainstem track must stay discoverable"
    for code, title, body in brainstem_cards:
        assert code == "Optional", code
        assert "(optional)" in title, title
        assert 'href="docs/installer.html"' in body, body
        assert "Not needed for any workshop" in body, body


def test_workshop_copy_never_presents_the_brainstem_as_a_prerequisite():
    offenders = []
    for slug in advertised_slugs():
        for name in WORKSHOP_COPY:
            text = (ROOT / "solutions" / slug / name).read_text(encoding="utf-8")
            for phrase in prerequisite_phrases(text):
                offenders.append(f"{slug}/{name}: {phrase!r}")
    for path in (SETTINGS, ACADEMY):
        for phrase in prerequisite_phrases(path.read_text(encoding="utf-8")):
            offenders.append(f"{path.relative_to(ROOT)}: {phrase!r}")

    for clause in re.findall(
        r"[^.<>\"\n]*\bBrainstem\b[^.<>\"\n]*",
        ACADEMY.read_text(encoding="utf-8"),
    ):
        if "optional" not in clause.lower():
            offenders.append(f"academy.html: Brainstem is not optional in {clause!r}")

    academy_paragraph = next(
        line
        for line in README.read_text(encoding="utf-8").splitlines()
        if line.startswith("The [**Microsoft AI Academy**]")
    )
    if not re.search(
        r"Brainstem[^.]*\boptional|\boptional[^.]*Brainstem", academy_paragraph
    ):
        offenders.append("README.md: the Academy workshop path requires the Brainstem")
    assert offenders == []


def test_optional_brainstem_track_stays_available_and_labeled_optional():
    settings = SETTINGS.read_text(encoding="utf-8")
    assert 'value="brainstem"' in settings
    assert "GitHub Copilot + Brainstem (optional)" in settings

    for slug in advertised_slugs():
        package = ROOT / "solutions" / slug
        quest = (package / "quest.html").read_text(encoding="utf-8")
        assert 'data-easy-lane="brainstem"' in quest, slug
        assert "GitHub Copilot + Brainstem (optional)" in quest, slug
        assert "Optional Brainstem lane:" in quest, slug
        assert "Default lane — GitHub Copilot only:" in quest, slug
        assert "Download Brainstem SKILL.md" in quest, slug

        guide = (package / "FIELD-GUIDE.md").read_text(encoding="utf-8")
        page = (package / "field-guide.html").read_text(encoding="utf-8")
        assert "## Facilitator crash course — optional Brainstem track" in guide
        assert "> **Optional.** Skip this section unless participants choose" in guide
        assert "### Optional pre-work: only Brainstem-track participants" in guide
        assert "Facilitator crash course: optional Brainstem track" in page
        assert "skip this crash course unless participants choose" in page
        assert "Optional pre-work: only Brainstem-track participants" in page
        for text in (guide, page):
            assert "microsoft.github.io/aibast-agents-library/install.sh" in text

        personless = (package / "EASY-MODE-PERSONLESS.md").read_text(encoding="utf-8")
        copilot = (package / "EASY-MODE-COPILOT-CHAT.md").read_text(encoding="utf-8")
        assert "(optional Brainstem lane)" in personless.splitlines()[0], slug
        assert "> **Optional lane.**" in personless, slug
        assert copilot.splitlines()[0].endswith("GitHub Copilot Easy mode (default)"), slug


def test_academy_browser_audit_expects_the_copilot_default():
    source = (ROOT / "browser-audit" / "academy-course-audit.mjs").read_text(
        encoding="utf-8"
    )
    matrix = re.search(
        r"for \(const \[storedValue, expected\] of \[(.*?)\]\) \{",
        source,
        re.DOTALL,
    ).group(1)
    assert dict(re.findall(r'\[(null|"[^"]*"), "([^"]+)"\]', matrix)) == {
        "null": "copilot",
        '"invalid"': "copilot",
        '"copilot"': "copilot",
        '"brainstem"': "brainstem",
    }
    assert 'const DEFAULT_EASY_LANE = "copilot";' in source
    assert "storage denial defaults visual engine to copilot" in source
    assert 'localStorage.setItem("aibast:workshop-engine", "brainstem")' not in source
    assert 'await auditAchievementRuntime(browser, baseUrl, slug, "brainstem");' in source


def test_copilot_lane_comes_first_wherever_both_lanes_render():
    offenders = []
    checked = Counter()
    for slug in advertised_slugs():
        package = ROOT / "solutions" / slug
        for name in GENERATED_PAGES:
            blocks = lane_block_offsets((package / name).read_text(encoding="utf-8"))
            for marker, offsets in blocks.items():
                if offsets.keys() != LANES:
                    continue
                checked[(name, marker)] += 1
                if offsets["copilot"] > offsets["brainstem"]:
                    offenders.append(
                        f"{slug}/{name}: {marker} copilot block at offset "
                        f"{offsets['copilot']} follows brainstem at {offsets['brainstem']}"
                    )
        guide = (package / "FIELD-GUIDE.md").read_text(encoding="utf-8")
        copilot = guide.find("\n## Easy mode — GitHub Copilot (default)\n")
        brainstem = guide.find("\n## Easy mode — GitHub Copilot + Brainstem (optional)\n")
        checked[("FIELD-GUIDE.md", "Easy mode sections")] += 1
        if not 0 < copilot < brainstem:
            offenders.append(f"{slug}/FIELD-GUIDE.md: Copilot Easy-mode section is not first")

    settings = SETTINGS.read_text(encoding="utf-8")
    if not settings.index('value="copilot"') < settings.index('value="brainstem"'):
        offenders.append("workshop-settings.html: the Brainstem option is listed first")
    cards = [code for code, _title, _body in CAPABILITY_CARD.findall(learn_and_build_block())]
    if cards.index("Optional") < max(cards.index("Step 1"), cards.index("Guided Easy mode")):
        offenders.append("index.html: the optional Brainstem card precedes a Copilot card")

    assert offenders == []
    total = len(advertised_slugs())
    assert checked[("quest.html", "data-easy-lane")] == total
    assert checked[("field-guide.html", "engine-panel")] == total
    assert checked[("FIELD-GUIDE.md", "Easy mode sections")] == total
