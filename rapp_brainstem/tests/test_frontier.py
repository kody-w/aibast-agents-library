"""Regression tests for the Brainstem Frontier outbound intelligence boundary.

Every request is mocked: these tests prove what leaves the Brainstem-owned
Copilot path without using an account, a real endpoint, or a real token.
"""
import copy
import json
import threading
from unittest import mock

import pytest

import brainstem as bs


PUBLIC_ENDPOINT = "https://api.individual.githubcopilot.com"
ENTERPRISE_ENDPOINT = "https://copilot.enterprise.example/v1"
GITHUB_TOKEN = "ghp_" + "A" * 36
JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhbGljZSJ9.c2lnbmF0dXJl"
EMAIL = "alice.sensitive@example.com"
CARD = "4242 4242 4242 4242"
SSN = "123-45-6789"
PHONE = "+1 206-555-0123"


class _Response:
    status_code = 200
    text = ""
    encoding = None

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "choices": [{
                "message": {"role": "assistant", "content": "ok"},
                "finish_reason": "stop",
            }],
        }


class _ToolResponse(_Response):
    def json(self):
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call-secret",
                        "type": "function",
                        "function": {"name": "SecretTool", "arguments": "{}"},
                    }],
                },
                "finish_reason": "tool_calls",
            }],
        }


class _StreamResponse:
    status_code = 200
    text = ""
    encoding = None

    def __init__(self):
        self.closed = False

    def iter_lines(self, decode_unicode=False):
        yield 'data: {"choices":[{"delta":{"content":"ok"}}]}'
        yield "data: [DONE]"

    def close(self):
        self.closed = True


class _ExchangeResponse:
    status_code = 200
    text = ""

    def __init__(self, endpoint):
        self.endpoint = endpoint

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "token": "copilot-session",
            "endpoints": {"api": self.endpoint},
            "expires_at": 9_999_999_999,
        }


@pytest.fixture(autouse=True)
def _isolate_frontier_state():
    original_cache = dict(bs._copilot_token_cache)
    original_no_copilot = dict(bs._no_copilot_access)
    original_invalid_credential = dict(bs._invalid_github_credential)
    with bs._flight_log_lock:
        original_log = list(bs._flight_log)
    yield
    bs._copilot_token_cache = original_cache
    bs._no_copilot_access = original_no_copilot
    bs._invalid_github_credential = original_invalid_credential
    with bs._flight_log_lock:
        bs._flight_log[:] = original_log


def _captured_json(post_mock):
    return [call.kwargs["json"] for call in post_mock.call_args_list]


def _assert_absent(values, payloads):
    serialized = json.dumps(payloads, sort_keys=True)
    for value in values:
        assert value not in serialized


def _call_non_streaming(monkeypatch, post_mock, messages):
    monkeypatch.setattr(bs, "get_copilot_token", lambda: ("copilot-session", PUBLIC_ENDPOINT))
    post_mock.return_value = _Response()
    return bs.call_copilot(messages)


def test_non_streaming_redacts_system_memory_history_and_tool_payload(monkeypatch):
    messages = [
        {"role": "system", "content": f"soul\n<memory>token={GITHUB_TOKEN}</memory>"},
        {"role": "user", "content": f"Contact {EMAIL}"},
        {"role": "assistant", "content": f"Prior card {CARD}"},
        {"role": "tool", "tool_call_id": "old-call", "content": f"SSN {SSN}; phone {PHONE}"},
    ]
    with mock.patch.object(bs.requests, "post") as post:
        _call_non_streaming(monkeypatch, post, messages)

    payloads = _captured_json(post)
    _assert_absent([GITHUB_TOKEN, EMAIL, CARD, SSN, PHONE], payloads)
    assert "[REDACTED]" in json.dumps(payloads)


def test_streaming_redacts_before_the_network_request(monkeypatch):
    messages = [{"role": "user", "content": f"JWT: {JWT}; email: {EMAIL}"}]
    response = _StreamResponse()
    monkeypatch.setattr(bs, "get_copilot_token", lambda: ("copilot-session", PUBLIC_ENDPOINT))

    with mock.patch.object(bs.requests, "post", return_value=response) as post:
        events = list(bs.call_copilot_stream(messages))

    assert any(kind == "done" for kind, _ in events)
    _assert_absent([JWT, EMAIL], _captured_json(post))
    assert response.closed


def test_ordinary_authorization_words_remain_byte_exact_in_actual_post_json(monkeypatch):
    ordinary = [
        "token counting",
        "bearer authentication",
        "basic authentication",
        "token expiration",
    ]
    messages = [{"role": "user", "content": text} for text in ordinary]

    with mock.patch.object(bs.requests, "post") as post:
        _call_non_streaming(monkeypatch, post, messages)

    outbound = _captured_json(post)[0]["messages"]
    assert [message["content"] for message in outbound] == ordinary
    assert "[REDACTED]" not in json.dumps(outbound)


def test_sensitive_tool_result_is_redacted_before_next_tool_loop_round(monkeypatch):
    class SecretTool:
        name = "SecretTool"

        def to_tool(self):
            return {
                "type": "function",
                "function": {
                    "name": self.name,
                    "description": "Returns a local result.",
                    "parameters": {"type": "object", "properties": {}},
                },
            }

        def system_context(self):
            return ""

        def perform(self, **kwargs):
            return f"authorization: Bearer {GITHUB_TOKEN}"

    monkeypatch.setattr(bs, "load_soul", lambda: "SOUL")
    monkeypatch.setattr(bs, "load_agents", lambda: {"SecretTool": SecretTool()})
    monkeypatch.setattr(bs, "get_copilot_token", lambda: ("copilot-session", PUBLIC_ENDPOINT))

    with mock.patch.object(
            bs.requests, "post", side_effect=[_ToolResponse(), _Response()]) as post:
        response = bs.app.test_client().post("/chat", json={"user_input": "run the tool"})

    assert response.status_code == 200
    assert len(post.call_args_list) == 2
    second_round = _captured_json(post)[1]
    _assert_absent([GITHUB_TOKEN], [second_round])
    tool_results = [message for message in second_round["messages"]
                    if message.get("role") == "tool"]
    assert tool_results[-1]["content"] == "authorization: Bearer [REDACTED]"


def test_ordinary_text_stays_byte_equivalent():
    payload = {
        "model": "gpt-4o",
        "messages": [{
            "role": "user",
            "content": "Ordinary punctuation, unicode café, and line one.\nLine two.",
        }],
    }

    original = copy.deepcopy(payload)
    endpoint, prepared, summary = bs._prepare_copilot_inference(PUBLIC_ENDPOINT, payload)

    assert endpoint == PUBLIC_ENDPOINT
    assert prepared == payload
    assert prepared is not payload
    assert prepared["messages"] is not payload["messages"]
    assert payload == original
    assert summary["counts_by_category"] == {}
    assert summary["images_withheld"] is False


def test_nested_message_and_tool_payloads_are_redacted_without_mutating_history():
    payload = {
        "model": "gpt-4o",
        "messages": [{
            "role": "assistant",
            "content": "tool work",
            "metadata": {"nested": [{"credential": f"token={GITHUB_TOKEN}"}]},
            "tool_calls": [{
                "function": {
                    "name": "Lookup",
                    "arguments": {"deep": {"contact": EMAIL}},
                },
            }],
        }],
        "tools": [{
            "type": "function",
            "function": {
                "name": "Lookup",
                "description": f"configuration contains {GITHUB_TOKEN}",
                "parameters": {
                    "type": "object",
                    "properties": {"deep": {"description": f"email {EMAIL}"}},
                },
            },
        }],
    }
    original = copy.deepcopy(payload)

    _, prepared, summary = bs._prepare_copilot_inference(PUBLIC_ENDPOINT, payload)

    _assert_absent([GITHUB_TOKEN, EMAIL], [prepared, summary])
    assert payload == original
    assert payload["messages"][0]["metadata"]["nested"][0]["credential"].endswith(
        GITHUB_TOKEN)


def test_masks_are_fixed_width_for_short_and_long_detected_values():
    short_value = "abcdefgh"
    long_value = "B" * 120
    payload = {
        "model": "gpt-4o",
        "messages": [{
            "role": "user",
            "content": f"token={short_value}; token={long_value}",
        }],
    }

    _, prepared, _ = bs._prepare_copilot_inference(PUBLIC_ENDPOINT, payload)

    assert prepared["messages"][0]["content"] == (
        "token=[REDACTED]; token=[REDACTED]")


def test_frontier_detects_private_keys_azure_assignments_and_common_api_tokens():
    azure_key = "A" * 42 + "=="
    google_key = "AIza" + "B" * 35
    private_key = (
        "-----BEGIN PRIVATE KEY-----\n"
        "MIIEvQIBADANBgkqhkiG9w0BAQEFAASC\n"
        "-----END PRIVATE KEY-----"
    )
    payload = {
        "model": "gpt-4o",
        "messages": [{
            "role": "user",
            "content": (
                f"AccountKey={azure_key}; google={google_key}\n{private_key}"),
        }],
    }

    _, prepared, summary = bs._prepare_copilot_inference(PUBLIC_ENDPOINT, payload)

    _assert_absent(
        [azure_key, google_key, private_key], [prepared, summary])
    assert summary["counts_by_category"]["credential-assignment"] == 1
    assert summary["counts_by_category"]["api-token"] == 1
    assert summary["counts_by_category"]["private-key"] == 1


def test_scanner_failure_fails_closed_without_a_network_call(monkeypatch):
    monkeypatch.setattr(bs, "get_copilot_token", lambda: ("copilot-session", PUBLIC_ENDPOINT))
    monkeypatch.setattr(bs, "_frontier_scan_text", lambda text: (_ for _ in ()).throw(RuntimeError()))

    with mock.patch.object(bs.requests, "post") as post:
        with pytest.raises(bs.FrontierBlockedError, match="safety scanning failed"):
            bs.call_copilot([{"role": "user", "content": "ordinary"}])

    post.assert_not_called()


@pytest.mark.parametrize("content", [
    [{"type": "image_url", "image_url": {"url": "data:image/png;base64,aGVsbG8="}}],
    "Please inspect data:image/jpeg;base64,aGVsbG8= before sending.",
])
def test_image_content_is_withheld_without_a_local_sanitizer(monkeypatch, content):
    monkeypatch.setattr(bs, "get_copilot_token", lambda: ("copilot-session", PUBLIC_ENDPOINT))

    with mock.patch.object(bs.requests, "post") as post:
        with pytest.raises(bs.FrontierBlockedError, match="image") as error:
            bs.call_copilot([{"role": "user", "content": content}])

    post.assert_not_called()
    assert error.value.summary["images_withheld"] is True


def test_data_image_in_tool_metadata_is_withheld_before_network(monkeypatch):
    monkeypatch.setattr(bs, "get_copilot_token", lambda: ("copilot-session", PUBLIC_ENDPOINT))
    tools = [{
        "type": "function",
        "function": {
            "name": "Photo",
            "description": "metadata data:image/png;base64,aGVsbG8=",
            "parameters": {"type": "object", "properties": {}},
        },
    }]

    with mock.patch.object(bs.requests, "post") as post:
        with pytest.raises(bs.FrontierBlockedError, match="image") as error:
            bs.call_copilot([{"role": "user", "content": "ordinary"}], tools=tools)

    post.assert_not_called()
    assert error.value.summary["images_withheld"] is True


@pytest.mark.parametrize("endpoint", [
    "http://api.individual.githubcopilot.com",
    "https://127.0.0.1",
    "https://127.1",
    "https://2130706433",
    "https://0x7f000001",
    "https://017700000001",
    "https://0x7f.0.0.1",
    "https://127.0.0.01",
    "https://10.0.0.1",
    "https://[::1]",
    "https://[fe80::1]",
    "https://[fc00::1]",
    "https://[::ffff:127.0.0.1]",
    "https://[::]",
    "https://169.254.169.254",
    "https://user:password@api.individual.githubcopilot.com",
    "https://api.individual.githubcopilot.com#fragment",
    "https://api.individual.githubcopilot.com.evil.example",
    "https://untrusted.example",
])
def test_unsafe_inference_endpoints_make_zero_network_calls(monkeypatch, endpoint):
    monkeypatch.setattr(bs, "get_copilot_token", lambda: ("copilot-session", endpoint))

    with mock.patch.object(bs.requests, "post") as post:
        with pytest.raises(bs.FrontierBlockedError, match="endpoint") as error:
            bs.call_copilot([{"role": "user", "content": "ordinary"}])

    post.assert_not_called()
    assert endpoint not in str(error.value)


@pytest.mark.parametrize("endpoint", [
    "https://127.0.0.1",
    "https://127.1",
    "https://2130706433",
    "https://0x7f000001",
    "https://017700000001",
    "https://0x7f.0.0.1",
    "https://127.0.0.01",
    "https://10.0.0.1",
    "https://169.254.169.254",
    "https://[::1]",
    "https://[fe80::1]",
    "https://[fc00::1]",
    "https://[::ffff:127.0.0.1]",
    "https://[::]",
])
def test_token_exchange_cannot_accept_nonpublic_literal_endpoints(endpoint):
    with pytest.raises(ValueError):
        bs._normalize_inference_endpoint(endpoint)


def test_known_public_and_exchange_trusted_enterprise_endpoints_work(monkeypatch):
    real_get_copilot_token = bs.get_copilot_token
    monkeypatch.setattr(bs, "get_copilot_token", lambda: ("copilot-session", PUBLIC_ENDPOINT))
    with mock.patch.object(bs.requests, "post", return_value=_Response()) as public_post:
        bs.call_copilot([{"role": "user", "content": "ordinary"}])
    assert public_post.called
    assert public_post.call_args.kwargs["allow_redirects"] is False

    bs._copilot_token_cache = {"token": None, "endpoint": None, "expires_at": 0}
    monkeypatch.setattr(bs, "get_copilot_token", real_get_copilot_token)
    monkeypatch.setattr(bs, "get_github_token", lambda: "ghu_exchange_account")
    monkeypatch.setattr(bs, "_load_copilot_cache", lambda github_token=None: None)
    monkeypatch.setattr(
        bs, "_exchange_github_for_copilot",
        lambda github_token: _ExchangeResponse(ENTERPRISE_ENDPOINT))
    monkeypatch.setattr(bs, "_save_copilot_cache", lambda *args: None)
    token, endpoint = bs.get_copilot_token()
    assert token == "copilot-session"
    assert endpoint == ENTERPRISE_ENDPOINT

    with mock.patch.object(bs.requests, "post", return_value=_Response()) as enterprise_post:
        bs.call_copilot([{"role": "user", "content": "ordinary"}])
    assert enterprise_post.called
    assert enterprise_post.call_args.args[0] == ENTERPRISE_ENDPOINT + "/chat/completions"


@pytest.mark.parametrize("cached_endpoint", [
    "https://attacker.example",
    "http://api.individual.githubcopilot.com",
    "https://127.0.0.1",
    "not a valid endpoint",
])
def test_disk_cache_never_restores_custom_or_malformed_endpoint_provenance(
        monkeypatch, tmp_path, cached_endpoint):
    github_token = "ghu_matching_account"
    cache_path = tmp_path / ".copilot_session"
    cache_path.write_text(json.dumps({
        "token": "copilot-cache-token",
        "endpoint": cached_endpoint,
        # This field is attacker-controlled on disk and must never bless a host.
        "endpoint_source": "token_exchange",
        "live_exchange_endpoint": True,
        "expires_at": 9_999_999_999,
        "github_token_fingerprint": bs._github_token_fingerprint(github_token),
    }), encoding="utf-8")
    exchange_calls = []

    def fresh_exchange(token):
        exchange_calls.append(token)
        return _ExchangeResponse(PUBLIC_ENDPOINT)

    monkeypatch.setattr(bs, "_copilot_cache_file", str(cache_path))
    monkeypatch.setattr(bs, "get_github_token", lambda: github_token)
    monkeypatch.setattr(bs, "_exchange_github_for_copilot", fresh_exchange)
    monkeypatch.setattr(bs, "_save_copilot_cache", lambda *args: None)
    bs._copilot_token_cache = {"token": None, "endpoint": None, "expires_at": 0}

    token, endpoint = bs.get_copilot_token()

    assert token == "copilot-session"
    assert endpoint == PUBLIC_ENDPOINT
    assert exchange_calls == [github_token]
    with mock.patch.object(bs.requests, "post", return_value=_Response()) as post:
        bs.call_copilot([{"role": "user", "content": "ordinary"}])
    assert post.call_args.args[0] == PUBLIC_ENDPOINT + "/chat/completions"


def test_saved_copilot_cache_never_persists_endpoint_provenance(monkeypatch, tmp_path):
    cache_path = tmp_path / ".copilot_session"
    monkeypatch.setattr(bs, "_copilot_cache_file", str(cache_path))

    bs._save_copilot_cache(
        "copilot-token",
        PUBLIC_ENDPOINT,
        9_999_999_999,
        "ghu_cache_account",
    )

    saved = json.loads(cache_path.read_text(encoding="utf-8"))
    assert "endpoint_source" not in saved
    assert "live_exchange_endpoint" not in saved


def test_frontier_summary_events_and_health_status_never_contain_raw_matches(monkeypatch):
    messages = [{"role": "user", "content": f"secret={GITHUB_TOKEN}; {EMAIL}"}]
    with mock.patch.object(bs.requests, "post") as post:
        _call_non_streaming(monkeypatch, post, messages)

    with bs._flight_log_lock:
        evidence = json.dumps({
            "health": bs._frontier_health_status(),
            "events": bs._flight_log,
        }, sort_keys=True)
    _assert_absent([GITHUB_TOKEN, EMAIL], [evidence])
    assert "github-token" in evidence
    assert "email" in evidence
    assert '"report_scope": "request_local"' in evidence


def test_frontier_reports_are_request_local_and_concurrency_safe():
    reports = []
    errors = []
    barrier = threading.Barrier(3)
    payloads = [
        {"role": "user", "content": f"token={GITHUB_TOKEN}"},
        {"role": "user", "content": f"email={EMAIL}"},
        {"role": "user", "content": f"card={CARD}"},
    ]

    def prepare(message):
        try:
            barrier.wait(timeout=5)
            _, _, summary = bs._prepare_copilot_inference(
                PUBLIC_ENDPOINT, {"model": "gpt-4o", "messages": [message]})
            reports.append(summary)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=prepare, args=(message,)) for message in payloads]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert errors == []
    assert len(reports) == 3
    assert len({id(summary) for summary in reports}) == 3
    assert {next(iter(summary["counts_by_category"])) for summary in reports} == {
        "github-token", "email", "credit-card"}
    assert not hasattr(bs, "_frontier_last_summary")
    assert bs._frontier_health_status()["report_scope"] == "request_local"


def test_health_exposes_capability_not_a_previous_request_report(monkeypatch):
    _, _, prior_summary = bs._prepare_copilot_inference(PUBLIC_ENDPOINT, {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": f"token={GITHUB_TOKEN}"}],
    })
    assert prior_summary["counts_by_category"]["github-token"] == 1
    monkeypatch.setattr(bs, "load_agents", lambda: {})
    monkeypatch.setattr(bs, "get_github_token", lambda: None)

    response = bs.app.test_client().get("/health")
    frontier = response.get_json()["frontier"]

    assert frontier == {
        "enabled": True,
        "report_scope": "request_local",
        "image_policy": "withhold_without_local_sanitizer",
    }
    assert "github-token" not in json.dumps(frontier)


def test_redaction_assertion_detects_a_boundary_bypass_mutation(monkeypatch):
    """The behavioral assertion fails when the centralized wrapper is bypassed."""
    monkeypatch.setattr(bs, "get_copilot_token", lambda: ("copilot-session", PUBLIC_ENDPOINT))

    def unsafe_post(endpoint, headers, body, *, timeout, stream=False):
        kwargs = {"headers": headers, "json": body, "timeout": timeout}
        if stream:
            kwargs["stream"] = True
        return bs.requests.post(endpoint + "/chat/completions", **kwargs)

    monkeypatch.setattr(bs, "_post_copilot_inference", unsafe_post)
    with mock.patch.object(bs.requests, "post", return_value=_Response()) as post:
        bs.call_copilot([{"role": "user", "content": f"token={GITHUB_TOKEN}"}])
        with pytest.raises(AssertionError):
            _assert_absent([GITHUB_TOKEN], _captured_json(post))
