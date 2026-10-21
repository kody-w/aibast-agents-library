from pathlib import Path

from tests.test_library_agent_upvotes import run_library_node


ROOT = Path(__file__).resolve().parent.parent
LIBRARY = ROOT / "index.html"
BRAINSTEM_UI = ROOT / "rapp_brainstem/index.html"


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


def test_failed_search_offers_learn_new_and_prefills_without_sending():
    result = run_library_node(
        """
state.query = "build a customs tariff classifier";
const html = emptyState();
const url = learnNewBrainstemUrl(state.query);
console.log(JSON.stringify({html, url, prompt: learnNewPrompt(state.query)}));
"""
    )
    assert "No library match" in result["html"]
    assert "Download Learn New agent.py" in result["html"]
    assert "Open Brainstem with this request" in result["html"]
    assert "VS Code" in result["html"]
    assert "Brain Surgeon" in result["html"]
    assert result["url"].startswith("http://localhost:7071/?prompt=")
    assert "customs+tariff+classifier" in result["url"]
    assert "preview, create, self-test, and hot-load" in result["prompt"]

    brainstem = BRAINSTEM_UI.read_text(encoding="utf-8")
    assert "new URLSearchParams(window.location.search).get('prompt')" in brainstem
    assert "input.value = prefilledPrompt.slice(0, 4000)" in brainstem
    assert "history.replaceState" in brainstem
    assert "handleSendButton()" not in brainstem[
        brainstem.index("const prefilledPrompt"):
        brainstem.index("input.addEventListener('input'")
    ]


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
    assert "Request access" in result["withQuery"]
    assert 'class="button primary" href="https://forms.cloud.microsoft/' in result["withQuery"]
    assert result["url"] == REQUEST_FORM_URL + "&r2c6c3672a0d9465d8f24e5caf6f21619=%22My%20use%20case%20is%20not%20listed%22"
    # The search text never goes into the form, and Factory access is an internal follow-up.
    assert "photo%20inspection" not in result["url"]
    assert "Factory" not in result["withQuery"]
    assert "RAPP Factory" not in (ROOT / "request-info.html").read_text(encoding="utf-8")


REQUEST_FORM_URL = "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=v4j5cvGGr0GRqy180BHbR7RNABRLLw9Eq-9okV_7Z-hUOEY3QjQ3V1RJUk43OEs4WEkzTDZQUVdNMC4u"
