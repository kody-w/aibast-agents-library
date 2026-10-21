from pathlib import Path

from tests.test_library_agent_upvotes import run_library_node


ROOT = Path(__file__).resolve().parent.parent
LIBRARY = ROOT / "index.html"


def test_search_supports_synonyms_stems_and_typo_tolerance():
    result = run_library_node(
        """
const agent = {
  name: "@aibast-agents-library/example",
  display_name: "Greenwashing Analysis",
  description: "Analyze sustainability claims and governance risk",
  category: "general",
  tags: ["compliance"],
  _solution: {personas: ["Analyst"], capabilities: ["Analyze claims"]}
};
console.log(JSON.stringify({
  exact: scoreAgent(agent, "greenwashing analysis"),
  typo: scoreAgent(agent, "greenwashing analyser"),
  synonym: scoreAgent(agent, "audit sustainability claims")
}));
"""
    )
    assert result["exact"] > 0
    assert result["typo"] > 0
    assert result["synonym"] > 0


def test_failed_search_offers_learn_new_as_a_request_to_paste():
    result = run_library_node(
        """
state.query = "build a customs tariff classifier";
console.log(JSON.stringify({html: emptyState(), prompt: learnNewPrompt(state.query)}));
state.query = "";
"""
    )
    assert "No library match" in result["html"]
    assert "Download Learn New agent.py" in result["html"]
    assert "VS Code" in result["html"]
    assert "Brain Surgeon" in result["html"]
    assert "preview, create, self-test, and hot-load" in result["prompt"]
    assert "customs tariff classifier" in result["html"]
    # Installed Brainstems before the replaceState fix break on ?prompt=, so the library links no prefill.
    assert "localhost:7071/?prompt=" not in result["html"]
    assert "learnNewBrainstemUrl" not in LIBRARY.read_text(encoding="utf-8")


def test_library_displays_and_sorts_observed_agent_downloads():
    text = LIBRARY.read_text(encoding="utf-8")
    assert '<option value="downloads">Top downloaded</option>' in text
    assert 'const downloads = row.downloads;' in text
    assert 'function agentDownloadCount(agent)' in text
    assert "observed agent.py download" in text
    assert "${agentDownloadCount(agent)}" in text


def test_failed_search_offers_a_request_access_link_for_a_missing_use_case():
    result = run_library_node(
        """
state.query = "field technician photo inspection";
console.log(JSON.stringify({withQuery: emptyState(), url: requestMissingUrl()}));
state.query = "";
"""
    )
    assert "Tell us what you need" in result["withQuery"]
    assert "Request access" not in result["withQuery"]
    assert 'class="button primary" href="https://forms.cloud.microsoft/' in result["withQuery"]
    assert result["url"] == REQUEST_FORM_URL + "&r2c6c3672a0d9465d8f24e5caf6f21619=%22My%20use%20case%20is%20not%20listed%22"
    # The search text never goes into the form, and Factory access is an internal follow-up.
    assert "photo%20inspection" not in result["url"]
    assert "Factory" not in result["withQuery"]
    assert "RAPP Factory" not in (ROOT / "request-info.html").read_text(encoding="utf-8")


REQUEST_FORM_URL = "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=v4j5cvGGr0GRqy180BHbR7RNABRLLw9Eq-9okV_7Z-hUOEY3QjQ3V1RJUk43OEs4WEkzTDZQUVdNMC4u"



def test_install_link_does_not_carry_the_search():
    # Carrying the search into the installer waits on security review; the link stays plain.
    result = run_library_node(
        """
state.query = "field technician photo inspection";
console.log(JSON.stringify({html: emptyState()}));
state.query = "";
"""
    )
    assert 'href="docs/installer.html">Install it first</a>' in result["html"]
    assert "?request=" not in result["html"]
    assert "pending-request" not in (ROOT / "docs" / "installer.html").read_text(encoding="utf-8")


def test_tell_us_is_offered_after_every_search_not_only_empty_ones():
    library = LIBRARY.read_text(encoding="utf-8")
    suggestions = library[library.index("function renderSuggestions()"):library.index("function learnNewPrompt")]
    assert 'join("") + tellUs;' in suggestions
    assert "if (!rows.length)" not in suggestions
    assert "Request access" not in library
