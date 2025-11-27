"""Utilities for building high-capability OpenAI Responses API requests.

This module encodes the guidance outlined in ``plan.md`` for running
rigorous investment research and brainstorming flows with the GPT-5.1
model. It builds request payloads with reasoning, verbosity, and tool
configurations tuned for long-form, tool-augmented tasks and provides
helpers to send those requests via HTTP.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Dict, List, Optional

import requests

DEFAULT_API_URL = "https://api.openai.com/v1/responses"

DEEP_RESEARCH_INSTRUCTION = (
    "You are a rigorous investment research analyst. Prioritize accuracy,\n"
    "multi-step reasoning, and transparent sourcing. Use web_search for any\n"
    "time-sensitive data, consult vector stores for prior research, and use\n"
    "code_interpreter for calculations and charting. Produce exhaustive,\n"
    "well-structured output in English even if the prompt is bilingual."
)

BRAINSTORM_INSTRUCTION = (
    "You are a creative but realistic investment thinker. Focus on non-"
    "consensus scenarios, tail risks, alternative mechanisms, and leading "
    "indicators. Avoid restating the base case; surface what the market may"
    " be missing."
)


def _deep_merge(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge dictionaries without mutating the inputs."""

    merged = {**base}
    for key, value in overrides.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


@dataclass
class RequestContext:
    """Holds contextual options shared by both modes."""

    conversation_id: Optional[str] = None
    vector_store_ids: Optional[List[str]] = None
    max_output_tokens: Optional[int] = None
    web_search_options: Optional[Dict[str, Any]] = None
    file_search_options: Optional[Dict[str, Any]] = None
    include_code_interpreter: bool = True
    include_image_generation: bool = True
    extra_tools: Optional[List[Dict[str, Any]]] = None


def _input_block(prompt: str) -> List[Dict[str, Any]]:
    return [
        {
            "role": "user",
            "content": [{"type": "input_text", "text": prompt}],
        }
    ]


def _build_common_tools(
    vector_store_ids: Optional[List[str]],
    *,
    web_search_options: Optional[Dict[str, Any]] = None,
    file_search_options: Optional[Dict[str, Any]] = None,
    include_code_interpreter: bool = True,
    include_image_generation: bool = True,
    extra_tools: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    tools: List[Dict[str, Any]] = []

    web_search = {"type": "web_search", "external_web_access": True}
    if web_search_options:
        web_search = _deep_merge(web_search, web_search_options)
    tools.append(web_search)

    resolved_vector_ids = vector_store_ids
    if file_search_options:
        resolved_vector_ids = file_search_options.get("vector_store_ids", vector_store_ids)

    if resolved_vector_ids:
        file_search: Dict[str, Any] = {"type": "file_search", "max_num_results": 30}
        file_search["vector_store_ids"] = resolved_vector_ids
        if file_search_options:
            file_search = _deep_merge(file_search, file_search_options)
        tools.append(file_search)

    if include_code_interpreter:
        tools.append({"type": "code_interpreter", "container": {"type": "auto"}})
    if include_image_generation:
        tools.append({"type": "image_generation"})

    if extra_tools:
        tools.extend(extra_tools)

    return tools


def build_deep_research_payload(
    prompt: str,
    *,
    context: Optional[RequestContext] = None,
    instructions: str = DEEP_RESEARCH_INSTRUCTION,
    model: str = "gpt-5.1",
    reasoning_effort: str = "high",
    text_verbosity: str = "high",
    max_output_tokens: Optional[int] = None,
    reasoning: Optional[Dict[str, Any]] = None,
    text: Optional[Dict[str, Any]] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    seed: Optional[int] = None,
    tool_choice: str = "auto",
    store: Optional[bool] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    input_blocks: Optional[List[Dict[str, Any]]] = None,
    extra_options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Builds a Responses API payload for high-rigor research.

    The payload uses GPT-5.1 with high reasoning effort, high verbosity,
    large max_output_tokens, and the full suite of tools recommended in
    ``plan.md``.
    """

    context = context or RequestContext()
    resolved_max_output_tokens = max_output_tokens or context.max_output_tokens or 100_000
    if reasoning is None:
        reasoning_config: Dict[str, Any] = {
            "effort": "medium" if resolved_max_output_tokens <= 4_000 else reasoning_effort
        }
    else:
        reasoning_config = reasoning

    payload: Dict[str, Any] = {
        "model": model,
        "instructions": instructions,
        "reasoning": reasoning_config,
        "text": text or {"verbosity": text_verbosity},
        "max_output_tokens": resolved_max_output_tokens,
        "tools": tools
        or _build_common_tools(
            context.vector_store_ids,
            web_search_options=context.web_search_options,
            file_search_options=context.file_search_options,
            include_code_interpreter=context.include_code_interpreter,
            include_image_generation=context.include_image_generation,
            extra_tools=context.extra_tools,
        ),
        "tool_choice": tool_choice,
        "store": True if store is None else store,
        "input": input_blocks or _input_block(prompt),
    }

    if temperature is not None:
        payload["temperature"] = temperature
    if top_p is not None:
        payload["top_p"] = top_p
    if seed is not None:
        payload["seed"] = seed
    if metadata is not None:
        payload["metadata"] = metadata
    if context.conversation_id:
        payload["conversation"] = context.conversation_id
    if extra_options:
        payload = _deep_merge(payload, extra_options)

    return payload


def build_brainstorm_payload(
    prompt: str,
    *,
    context: Optional[RequestContext] = None,
    instructions: str = BRAINSTORM_INSTRUCTION,
    model: str = "gpt-5.1",
    text_verbosity: str = "high",
    temperature: float = 1.2,
    top_p: float = 1.0,
    max_output_tokens: Optional[int] = None,
    reasoning_effort: str = "none",
    reasoning: Optional[Dict[str, Any]] = None,
    text: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None,
    tool_choice: str = "auto",
    store: Optional[bool] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    input_blocks: Optional[List[Dict[str, Any]]] = None,
    extra_options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Builds a Responses API payload for divergent brainstorming.

    This configuration disables reasoning tokens so that sampling
    parameters can be used while keeping verbose, tool-aware responses.
    """

    context = context or RequestContext()
    resolved_max_output_tokens = max_output_tokens or context.max_output_tokens or 20_000
    payload: Dict[str, Any] = {
        "model": model,
        "instructions": instructions,
        "reasoning": reasoning or {"effort": reasoning_effort},
        "text": text or {"verbosity": text_verbosity},
        "temperature": temperature,
        "top_p": top_p,
        "max_output_tokens": resolved_max_output_tokens,
        "tools": tools
        or _build_common_tools(
            context.vector_store_ids,
            web_search_options=context.web_search_options,
            file_search_options=context.file_search_options,
            include_code_interpreter=context.include_code_interpreter,
            include_image_generation=context.include_image_generation,
            extra_tools=context.extra_tools,
        ),
        "tool_choice": tool_choice,
        "store": True if store is None else store,
        "input": input_blocks or _input_block(prompt),
    }

    if seed is not None:
        payload["seed"] = seed
    if metadata is not None:
        payload["metadata"] = metadata
    if context.conversation_id:
        payload["conversation"] = context.conversation_id
    if extra_options:
        payload = _deep_merge(payload, extra_options)

    return payload


def _resolve_api_key(api_key: Optional[str]) -> str:
    resolved = api_key or os.getenv("OPENAI_API_KEY")
    if not resolved:
        raise ValueError("An OpenAI API key is required via argument or OPENAI_API_KEY env var.")
    return resolved


def _resolve_header_env(name: str, fallback: Optional[str]) -> Optional[str]:
    """Return a header value from explicit input or environment."""

    return fallback or os.getenv(name)


def _resolve_api_url(api_url: Optional[str]) -> str:
    """Return a full Responses endpoint, defaulting to OPENAI_BASE_URL when set."""

    base = api_url or os.getenv("OPENAI_BASE_URL") or DEFAULT_API_URL
    trimmed = base.rstrip("/")
    if trimmed.endswith("/responses"):
        return trimmed
    return f"{trimmed}/responses"


def send_response_request(
    payload: Dict[str, Any],
    *,
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    organization: Optional[str] = None,
    project: Optional[str] = None,
    timeout: int = 120,
) -> Dict[str, Any]:
    """Sends a request to the OpenAI Responses API and returns JSON.

    The function keeps side effects minimal to simplify unit testing.
    """

    resolved_key = _resolve_api_key(api_key)
    url = _resolve_api_url(api_url)
    headers = {
        "Authorization": f"Bearer {resolved_key}",
        "Content-Type": "application/json",
    }
    resolved_org = _resolve_header_env("OPENAI_ORG_ID", organization)
    if resolved_org:
        headers["OpenAI-Organization"] = resolved_org

    resolved_project = _resolve_header_env("OPENAI_PROJECT", project)
    if resolved_project:
        headers["OpenAI-Project"] = resolved_project

    response = requests.post(url, headers=headers, json=payload, timeout=timeout)

    detail: str = ""
    try:
        detail = response.json().get("error", {}).get("message", "")
    except Exception:
        detail = response.text

    if response.status_code == 401:
        header_summary_parts = []
        if resolved_org:
            header_summary_parts.append(f"OpenAI-Organization={resolved_org}")
        if resolved_project:
            header_summary_parts.append(f"OpenAI-Project={resolved_project}")
        header_summary = ", ".join(header_summary_parts) if header_summary_parts else "no org/project headers"

        message = (
            f"OpenAI returned 401 Unauthorized from {url}. Confirm OPENAI_API_KEY is valid and "
            "has access to the Responses API (keys that work for other endpoints may be scoped differently), "
            "set OPENAI_BASE_URL if using a proxy, and provide OpenAI-Organization / OpenAI-Project headers when "
            f"your key is scoped to a specific project (currently {header_summary})."
        )
        if detail:
            message = f"{message} Provider message: {detail}"
        raise requests.HTTPError(message, response=response)

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        message = f"OpenAI returned {response.status_code} from {url}."
        if detail:
            message = f"{message} Provider message: {detail}"
        raise requests.HTTPError(message, response=response) from exc

    return response.json()


def run_deep_research(prompt: str, *, context: Optional[RequestContext] = None, **kwargs: Any) -> Dict[str, Any]:
    """Convenience wrapper to build and send a deep research request."""

    api_key = kwargs.pop("api_key", None)
    api_url = kwargs.pop("api_url", None)
    timeout = kwargs.pop("timeout", 120)
    organization = kwargs.pop("organization", None)
    project = kwargs.pop("project", None)
    payload = build_deep_research_payload(prompt, context=context, **kwargs)
    return send_response_request(
        payload,
        api_key=api_key,
        api_url=api_url,
        organization=organization,
        project=project,
        timeout=timeout,
    )


def run_brainstorm(prompt: str, *, context: Optional[RequestContext] = None, **kwargs: Any) -> Dict[str, Any]:
    """Convenience wrapper to build and send a brainstorming request."""

    api_key = kwargs.pop("api_key", None)
    api_url = kwargs.pop("api_url", None)
    timeout = kwargs.pop("timeout", 120)
    organization = kwargs.pop("organization", None)
    project = kwargs.pop("project", None)
    payload = build_brainstorm_payload(prompt, context=context, **kwargs)
    return send_response_request(
        payload,
        api_key=api_key,
        api_url=api_url,
        organization=organization,
        project=project,
        timeout=timeout,
    )


def pretty_print_payload(payload: Dict[str, Any]) -> str:
    """Returns a stable JSON representation for CLI dry runs."""

    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
