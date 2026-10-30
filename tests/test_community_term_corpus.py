"""One cumulative corpus for the Community agents word checks.

The checker in tools/demo_submission.py flags two kinds of words on the
public demo card:

    words  - internal or forbidden words ("Remove these words ...")
    vendor - other companies' AI product names (OTHER_AI_PRODUCTS_PROBLEM)

Every case below is a real repro or control from a review round, or from an
earlier test. Each case lists exactly which kinds must be reported for that
one field; an empty set means the field must pass both checks.

This corpus only grows. Never delete a case to make it pass. If two cases
truly conflict, stop and ask a maintainer.

The rules the cases pin down:
  * Words of a name may be joined by nothing, spaces, or punctuation with no
    space after it ("RAPP/Factory", "Vertex.AI", "Salesforce·Einstein").
  * A punctuation mark followed by whitespace is a sentence break, so names
    never join across it ("Amazon. Q4", "Amazon, Q3").
  * A possessive joins ("Google’s Bard").
  * A one-letter last word takes no digit ("Amazon Q4" is a sales quarter).
  * Everyday words pass unless the vendor word is next to them
    ("perplexity", "bard", "bedrock").
  * One-pager links: the host is read both ways round (bard.google.com is
    Google's Bard), readable path words are split at capitals
    (AzureFunctionsDemo.pdf), opaque ids are not (AbNDA9xQ, 1aGPT3kz), and the
    query and fragment are never read.
"""

from __future__ import annotations

import pytest

from tests.test_community_agents import filled_body
from tools import demo_submission as ds

W, V = "words", "vendor"
PASS: frozenset = frozenset()


def _set(*kinds):
    return frozenset(kinds)


# (source, field, text, expected kinds)
CORPUS = [
    # ---------------------------------------------- existing tests, forbidden words
    ("test", "description", "Built in the RAPP Factory. Second sentence.", _set(W)),
    ("test", "description", "This is confidential. Second sentence.", _set(W)),
    ("test", "description", "Runs on Azure Functions. Second sentence.", _set(W)),
    ("test", "description", "Uses AzureOpenAI under the hood. The agent drafts the summary.", _set(W, V)),
    ("test", "description", "Uses azureopenai under the hood. The agent drafts the summary.", _set(W, V)),
    ("test", "description", "Runs on AzureFunctions. The agent drafts the summary.", _set(W)),
    ("test", "description", "Runs on Ａｚｕｒｅ Functions. The agent drafts the summary.", _set(W)),
    ("test", "description", "Hosted in Azure2 regions. The agent drafts the summary.", _set(W)),
    # ---------------------------------------------- existing tests, vendor names
    ("test", "description", "We rebuilt our ChatGPT prototype in Copilot Studio. It drafts replies.", _set(V)),
    ("test", "description", "It replaces a Gemini workflow. It drafts replies.", _set(V)),
    ("test", "description", "Built on GPT-4 first. It drafts replies.", _set(V)),
    ("test", "team", "OpenAI Partner Team", _set(V)),
    ("test", "title", "Claude reply drafter", _set(V)),
    ("test", "description", "Built like a GPT4 helper. The agent drafts the summary.", _set(V)),
    ("test", "description", "It started as a Claude3 prototype. The agent drafts the summary.", _set(V)),
    ("test", "description", "Replaces Salesforce Agentforce. The agent drafts the summary.", _set(V)),
    ("test", "description", "Replaces Google Vertex AI. The agent drafts the summary.", _set(V)),
    ("test", "description", "Moved off Amazon Bedrock. The agent drafts the summary.", _set(V)),
    ("test", "description", "Moved off IBM watsonx. The agent drafts the summary.", _set(V)),
    ("test", "title", "ＣｈａｔＧＰＴ Helper", _set(V)),
    ("test", "title", "Chat​GPT Helper", _set(V)),
    ("test", "description", "It replaces Amazon Q in the store. The agent drafts replies.", _set(V)),
    ("test", "description", "It replaces Amazon-Q. The agent drafts replies.", _set(V)),
    ("test", "description", "It started on Perplexity AI. The agent drafts replies.", _set(V)),
    ("test", "description", "It started on GPT4. The agent drafts replies.", _set(V)),
    ("test", "title", "Mistral Wind Farm Ops", _set(V)),
    ("test", "team", "Gemini Squad", _set(V)),
    ("test", "title", "Gemini Reply Drafter", _set(V)),
    ("test", "team", "Mistral Squad", _set(V)),
    # ---------------------------------------------- existing tests, must pass
    ("test", "description", "Copilot Studio drafts the reply. Microsoft 365 Copilot summarises it in Teams.", PASS),
    ("test", "description", "Power Automate routes the request. Dynamics 365 and SharePoint keep the record.", PASS),
    ("test", "description", "PowerApps and Dataverse hold the plan. The bedrock of the process is one Teams channel.", PASS),
    ("test", "description", "The agenda covers standard tasks. It handles grading and abandoned carts.", PASS),
    ("test", "description", "The agent can now assist managers. Amazon queue times are not involved.", PASS),
    ("test", "description", "Sellers list on Amazon. Q4 returns spike and the agent triages them.", PASS),
    ("test", "description", "Stores order from Amazon, Q3 forecasts guide stock. The agent helps.", PASS),
    ("test", "description", "Stores order from Amazon; Q3 forecasts guide stock. The agent helps.", PASS),
    ("test", "description", "Sales on Amazon Q4 were strong. The agent forecasts the next quarter.", PASS),
    ("test", "description", "Planners face perplexity over shift rules. The agent explains them.", PASS),
    ("test", "description", "The town bard wrote the anthem. The agent books the hall.", PASS),
    ("test", "title", "Retail Returns Triage", PASS),
    ("test", "title", "Tiered Digital Huddle Board", PASS),
    ("test", "team", "Microsoft Healthcare AI Business Process Solutions", PASS),
    # ---------------------------------------------- existing tests, one-pager link
    ("test", "onepager", "https://chatgpt.com/share/abc", _set(V)),
    ("test", "onepager", "https://example.com/our-gpt4-onepager.pdf", _set(V)),
    ("test", "onepager", "https://example.com/gemini-onepager.pdf", _set(V)),
    ("test", "onepager", "https://example.com/files/confidential-onepager.pdf", _set(W)),
    ("test", "onepager", "https://example.com/files/internal%20only/onepager.pdf", _set(W)),
    ("test", "onepager", "https://azure-demo.example.com/onepager.pdf", _set(W)),
    ("test", "onepager", "https://example.com/azureopenai-onepager.pdf", _set(W, V)),
    ("test", "onepager", "https://contoso.github.io/doc?id=AbNDA9xQ", PASS),
    ("test", "onepager", "https://example.com/files/1aGPT3kz.pdf", PASS),
    ("test", "onepager", "https://example.com/d/AbNDA9xQ/view", PASS),
    ("test", "onepager", "https://example.com/view?file=confidential-gpt4.pdf", PASS),
    ("test", "onepager", "https://example.com/onepager.pdf#azure", PASS),
    ("test", "onepager", "https://example.com/onepager.pdf", PASS),
    # ---------------------------------------------- round 2 repros
    ("round 2", "description", "We rebuilt our ChatGPT and Gemini prototype in Copilot Studio. It drafts replies.", _set(V)),
    # ---------------------------------------------- round 3 repros
    ("round 3", "description", "Uses AzureOpenAI under the hood. The agent drafts.", _set(W, V)),
    ("round 3", "description", "Replaces Salesforce Agentforce and Google Vertex AI. The agent drafts.", _set(V)),
    ("round 3", "description", "Uses Amazon Bedrock and IBM watsonx. The agent drafts.", _set(V)),
    ("round 3", "title", "ＣｈａｔＧＰＴ Helper", _set(V)),
    ("round 3", "description", "Built with GPT-4o and Claude3 first. The agent drafts.", _set(V)),
    ("round 3", "onepager", "https://chatgpt.com/share/confidential-internal-only", _set(W, V)),
    # ---------------------------------------------- round 4 repros
    ("round 4", "onepager", "https://contoso.github.io/doc?id=AbNDA9xQ", PASS),
    ("round 4", "onepager", "https://example.com/files/1aGPT3kz.pdf", PASS),
    # ---------------------------------------------- round 5: joins with no space
    ("round 5", "description", "This is RAPP/Factory output. The agent drafts replies.", _set(W)),
    ("round 5", "description", "Built with RAPP.Factory tools. The agent drafts replies.", _set(W)),
    ("round 5", "description", "Marked internal/only. The agent drafts replies.", _set(W)),
    ("round 5", "description", "It started on Perplexity.ai. The agent drafts replies.", _set(V)),
    ("round 5", "title", "Vertex.AI Swap", _set(V)),
    ("round 5", "description", "It replaces Salesforce·Einstein. The agent drafts replies.", _set(V)),
    ("round 5", "description", "Built with Google’s Bard. The agent drafts replies.", _set(V)),
    ("round 5", "description", "Built with Google's Bard. The agent drafts replies.", _set(V)),
    ("round 5", "description", "Marked do/not/share. The agent drafts replies.", _set(W)),
    # ---------------------------------------------- round 5: one-pager link
    ("round 5", "onepager", "https://example.com/files/AzureFunctionsDemo.pdf", _set(W)),
    ("round 5", "onepager", "https://example.com/ConfidentialOnepager.pdf", _set(W)),
    ("round 5", "onepager", "https://example.com/files/GeminiOnePager.pdf", _set(V)),
    ("round 5", "onepager", "https://example.com/OurChatGPTDemo.pdf", _set(V)),
    ("round 5", "onepager", "https://www.perplexity.ai/page/onepager", _set(V)),
    ("round 5", "onepager", "https://bard.google.com/share/abc", _set(V)),
    ("round 5", "onepager", "https://example.com/internal+only/onepager.pdf", _set(W)),
    ("round 5", "onepager", "https://example.com/rapp/factory/onepager.pdf", _set(W)),
    # ---------------------------------------------- round 5 controls that must keep passing
    ("round 5", "description", "Sellers list on Amazon. Q4 returns spike and the agent triages them.", PASS),
    ("round 5", "description", "Stores order from Amazon, Q3 forecasts guide stock. The agent helps.", PASS),
    ("round 5", "description", "Planners face perplexity over shift rules. The agent explains them.", PASS),
    ("round 5", "description", "Sellers list on Amazon.com and the agent triages returns. It drafts replies.", PASS),
    ("round 5", "description", "Stores sell on Amazon.Q4 returns spike. The agent helps.", PASS),
    ("round 5", "onepager", "https://www.example.com/perplexity/onepager.pdf", PASS),
    ("round 5", "onepager", "https://example.com/TieredHuddleBoardOnePager.pdf", PASS),
    ("round 5", "onepager", "https://example.com/docs/Tiered-Huddle-Board.pdf", PASS),
    # ---------------------------------------------- redesign probes (round 5 fix)
    ("probe", "description", "Built with RAPP-Factory parts. It drafts replies.", _set(W)),
    ("probe", "description", "Built with rapp_factory parts. It drafts replies.", _set(W)),
    ("probe", "description", "The RAPP Factory's output. It drafts replies.", _set(W)),
    ("probe", "description", "Marked Internal-Only. It drafts replies.", _set(W)),
    ("probe", "description", "Marked do-not-share. It drafts replies.", _set(W)),
    ("probe", "description", "Reviewed under NDA. It drafts replies.", _set(W)),
    ("probe", "description", "It replaces Amazon Q. The agent drafts replies.", _set(V)),
    ("probe", "description", "It replaces AmazonQ today. The agent drafts replies.", _set(V)),
    ("probe", "description", "Planned with perplexity, AI helps after. The agent drafts replies.", PASS),
    ("probe", "description", "Sellers on Amazon - Q4 returns spike. The agent helps.", PASS),
    ("probe", "description", "The agent uses e.g. Dataverse rows. It drafts replies in the U.S. market.", PASS),
    ("probe", "title", "Agent for the U.S. Market", PASS),
    ("probe", "team", "Retail AI Ops (EMEA)", PASS),
    ("probe", "onepager", "https://example.com/docs/Vertex.AI.pdf", _set(V)),
    ("probe", "onepager", "https://example.com/docs/VertexAIDemo.pdf", _set(V)),
    ("probe", "onepager", "https://vertex.ai/docs", _set(V)),
    ("probe", "onepager", "https://nda.example.com/docs", _set(W)),
    ("probe", "onepager", "https://example.com/DoNotShare.pdf", _set(W)),
    ("probe", "onepager", "https://example.com/amazon/q/report.pdf", _set(V)),
    ("probe", "onepager", "https://example.com/docs/Amazon-Q4-Report.pdf", PASS),
    ("probe", "onepager", "https://example.com/docs/Amazon.Q4.pdf", PASS),
    ("probe", "onepager", "https://example.com/files/Huddle%20Board%20One%20Pager.pdf", PASS),
    ("probe", "onepager", "https://example.com/files/q/amazon/report.pdf", PASS),
]


def _kinds(field: str, text: str) -> frozenset:
    _, problems = ds.validate(ds.parse_issue_form(filled_body(**{field: text})))
    found = set()
    if any(p.startswith("Remove these words") for p in problems):
        found.add(W)
    if any(p.startswith(ds.OTHER_AI_PRODUCTS_PROBLEM) for p in problems):
        found.add(V)
    return frozenset(found)


@pytest.mark.parametrize(
    "source, field, text, expected", CORPUS,
    ids=[f"{s}|{f}|{t}" for s, f, t, _ in CORPUS],
)
def test_term_corpus(source, field, text, expected):
    assert _kinds(field, text) == expected


def test_the_corpus_has_no_conflicting_cases():
    seen: dict = {}
    for _source, field, text, expected in CORPUS:
        key = (field, text)
        assert seen.setdefault(key, expected) == expected, key
