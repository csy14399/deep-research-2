import json
from types import SimpleNamespace
from unittest import mock

import pytest
import requests

from deep_research.client import (
    RequestContext,
    build_brainstorm_payload,
    build_deep_research_payload,
    pretty_print_payload,
    run_deep_research,
    run_brainstorm,
    send_response_request,
)


def test_build_deep_research_payload_includes_high_reasoning_and_tools():
    context = RequestContext(conversation_id="conv1", vector_store_ids=["vs1", "vs2"])
    payload = build_deep_research_payload("test prompt", context=context)

    assert payload["model"] == "gpt-5.1"
    assert payload["reasoning"] == {"effort": "high"}
    assert payload["text"] == {"verbosity": "high"}
    assert payload["max_output_tokens"] == 100_000
    assert payload["conversation"] == "conv1"

    tool_types = [tool["type"] for tool in payload["tools"]]
    assert tool_types == ["web_search", "file_search", "code_interpreter", "image_generation"]

    file_search = payload["tools"][1]
    assert file_search["vector_store_ids"] == ["vs1", "vs2"]
    assert file_search["max_num_results"] == 30
    assert payload["tools"][2]["container"] == {"type": "auto"}


def test_build_deep_research_payload_skips_file_search_when_no_vector_store():
    payload = build_deep_research_payload("test prompt", context=RequestContext())

    tool_types = [tool["type"] for tool in payload["tools"]]
    assert tool_types == ["web_search", "code_interpreter", "image_generation"]


def test_small_output_budget_dials_down_reasoning_effort():
    payload = build_deep_research_payload("short", context=RequestContext(max_output_tokens=2000))

    assert payload["max_output_tokens"] == 2000
    assert payload["reasoning"] == {"effort": "medium"}


def test_build_brainstorm_payload_enables_sampling_defaults():
    payload = build_brainstorm_payload("prompt", context=RequestContext())

    assert payload["reasoning"] == {"effort": "none"}
    assert payload["temperature"] == 1.2
    assert payload["top_p"] == 1.0
    assert payload["max_output_tokens"] == 20_000

    assert payload["tools"][0]["external_web_access"] is True


def test_common_tools_allow_overrides_and_toggles():
    context = RequestContext(
        vector_store_ids=["vs1"],
        web_search_options={"user_location": {"country": "CN"}},
        file_search_options={"max_num_results": 5},
        include_code_interpreter=False,
        include_image_generation=False,
        extra_tools=[{"type": "custom_tool"}],
    )

    payload = build_deep_research_payload("prompt", context=context)

    tool_types = [tool["type"] for tool in payload["tools"]]
    assert tool_types == ["web_search", "file_search", "custom_tool"]

    assert payload["tools"][0]["user_location"] == {"country": "CN"}
    assert payload["tools"][1]["max_num_results"] == 5


def test_file_search_can_be_opted_in_via_options_without_context_vector_store():
    context = RequestContext(
        file_search_options={"vector_store_ids": ["vs_opt_in"], "max_num_results": 10}
    )

    payload = build_deep_research_payload("prompt", context=context)

    tool_types = [tool["type"] for tool in payload["tools"]]
    assert tool_types[0] == "web_search"
    assert "file_search" in tool_types
    file_search = next(tool for tool in payload["tools"] if tool["type"] == "file_search")
    assert file_search["vector_store_ids"] == ["vs_opt_in"]
    assert file_search["max_num_results"] == 10


def test_extra_options_deep_merge_nested_fields():
    payload = build_deep_research_payload(
        "prompt",
        context=RequestContext(),
        extra_options={"text": {"verbosity": "low", "format": "markdown"}, "metadata": {"team": "alpha"}},
    )

    assert payload["text"] == {"verbosity": "low", "format": "markdown"}
    assert payload["metadata"] == {"team": "alpha"}


def test_custom_tools_and_input_blocks_are_respected():
    custom_tools = [{"type": "web_search", "filters": {"allowed_domains": ["openai.com"]}}]
    input_blocks = [{"role": "user", "content": [{"type": "input_text", "text": "hi"}]}]

    payload = build_brainstorm_payload(
        "ignored",
        tools=custom_tools,
        input_blocks=input_blocks,
        reasoning_effort="low",
        context=RequestContext(max_output_tokens=123),
    )

    assert payload["tools"] == custom_tools
    assert payload["input"] == input_blocks
    assert payload["reasoning"] == {"effort": "low"}
    assert payload["max_output_tokens"] == 123


def test_pretty_print_payload_sorts_keys():
    payload = {"b": 1, "a": {"c": 2}}
    pretty = pretty_print_payload(payload)
    lines = pretty.splitlines()
    # First key should be sorted alphabetically.
    assert lines[1].strip().startswith('"a"')
    assert lines[-2].strip().startswith('"b"')


def test_send_response_request_uses_environment_api_key(monkeypatch):
    payload = {"model": "x", "input": []}
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    fake_response = SimpleNamespace(status_code=200, json=lambda: {"ok": True})
    fake_response.raise_for_status = lambda: None

    with mock.patch("requests.post", return_value=fake_response) as mock_post:
        result = send_response_request(payload, api_url="https://example.com")

    assert result == {"ok": True}
    mock_post.assert_called_once()
    headers = mock_post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer env-key"


def test_send_response_request_includes_org_and_project_headers(monkeypatch):
    payload = {"model": "x", "input": []}
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setenv("OPENAI_ORG_ID", "org_123")
    monkeypatch.setenv("OPENAI_PROJECT", "proj_abc")
    fake_response = SimpleNamespace(status_code=200, json=lambda: {"ok": True})
    fake_response.raise_for_status = lambda: None

    with mock.patch("requests.post", return_value=fake_response) as mock_post:
        send_response_request(payload, organization="org_cli", project="proj_cli")

    headers = mock_post.call_args.kwargs["headers"]
    # Explicit CLI values should win over env vars.
    assert headers["OpenAI-Organization"] == "org_cli"
    assert headers["OpenAI-Project"] == "proj_cli"


def test_send_response_request_appends_responses_path(monkeypatch):
    payload = {"model": "x", "input": []}
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.bltcy.ai/v1")
    fake_response = SimpleNamespace(status_code=200, json=lambda: {"ok": True})
    fake_response.raise_for_status = lambda: None

    with mock.patch("requests.post", return_value=fake_response) as mock_post:
        send_response_request(payload)

    mock_post.assert_called_once()
    assert mock_post.call_args.args[0] == "https://api.bltcy.ai/v1/responses"


def test_send_response_request_respects_full_custom_endpoint(monkeypatch):
    payload = {"model": "x", "input": []}
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    fake_response = SimpleNamespace(status_code=200, json=lambda: {"ok": True})
    fake_response.raise_for_status = lambda: None

    with mock.patch("requests.post", return_value=fake_response) as mock_post:
        send_response_request(payload, api_url="https://example.com/v1/responses")

    mock_post.assert_called_once()
    assert mock_post.call_args.args[0] == "https://example.com/v1/responses"


def test_send_response_request_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        send_response_request({"model": "x", "input": []}, api_url="https://example.com")


def test_send_response_request_surface_endpoint_and_headers_on_401(monkeypatch):
    payload = {"model": "x", "input": []}
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")

    class FakeResponse:
        status_code = 401
        text = "unauthorized"

        def json(self):
            return {"error": {"message": "bad key"}}

    with mock.patch("requests.post", return_value=FakeResponse()):
        with pytest.raises(requests.HTTPError) as excinfo:
            send_response_request(
                payload,
                api_url="https://proxy.example.com/v1",
                organization="org_cli",
                project="proj_cli",
            )

    message = str(excinfo.value)
    assert "https://proxy.example.com/v1/responses" in message
    assert "OpenAI-Organization=org_cli" in message
    assert "OpenAI-Project=proj_cli" in message
    assert "bad key" in message


def test_send_response_request_notes_missing_headers_on_401(monkeypatch):
    payload = {"model": "x", "input": []}
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")

    class FakeResponse:
        status_code = 401
        text = "unauthorized"

        def json(self):
            return {"error": {"message": "missing project"}}

    with mock.patch("requests.post", return_value=FakeResponse()):
        with pytest.raises(requests.HTTPError) as excinfo:
            send_response_request(payload, api_url="https://api.openai.com/v1")

    message = str(excinfo.value)
    assert "https://api.openai.com/v1/responses" in message
    assert "no org/project headers" in message
    assert "missing project" in message


def test_send_response_request_surfaces_provider_message_on_other_errors(monkeypatch):
    payload = {"model": "x", "input": []}
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")

    class FakeResponse:
        status_code = 400
        text = "bad request"

        def json(self):
            return {"error": {"message": "missing tools"}}

        def raise_for_status(self):
            raise requests.HTTPError("boom", response=self)

    with mock.patch("requests.post", return_value=FakeResponse()):
        with pytest.raises(requests.HTTPError) as excinfo:
            send_response_request(payload, api_url="https://api.openai.com/v1")

    message = str(excinfo.value)
    assert "https://api.openai.com/v1/responses" in message
    assert "400" in message
    assert "missing tools" in message


def test_run_deep_research_forwards_timeout_and_api_values(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")

    with mock.patch("deep_research.client.send_response_request", return_value={"ok": True}) as mock_send:
        run_deep_research(
            "prompt",
            api_key="explicit",
            api_url="https://example.com",
            timeout=5,
            organization="org_cli",
            project="proj_cli",
        )

    assert mock_send.call_args.kwargs["api_key"] == "explicit"
    assert mock_send.call_args.kwargs["api_url"] == "https://example.com"
    assert mock_send.call_args.kwargs["timeout"] == 5
    assert mock_send.call_args.kwargs["organization"] == "org_cli"
    assert mock_send.call_args.kwargs["project"] == "proj_cli"


def test_run_brainstorm_forwards_org_and_project(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")

    with mock.patch("deep_research.client.send_response_request", return_value={"ok": True}) as mock_send:
        run_brainstorm(
            "prompt",
            api_key="explicit",
            organization="org_cli",
            project="proj_cli",
        )

    assert mock_send.call_args.kwargs["organization"] == "org_cli"
    assert mock_send.call_args.kwargs["project"] == "proj_cli"
