"""Command-line interface for running GPT-5.1 research flows.

Two modes are supported:
- ``research``: high-rigor, tool-heavy configuration with reasoning enabled.
- ``brainstorm``: divergent exploration with sampling parameters enabled.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, List, Optional

from .client import (
    BRAINSTORM_INSTRUCTION,
    DEEP_RESEARCH_INSTRUCTION,
    RequestContext,
    build_brainstorm_payload,
    build_deep_research_payload,
    pretty_print_payload,
    send_response_request,
)


def _parse_arguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run GPT-5.1 deep research or brainstorming flows.")
    parser.add_argument("prompt", help="Prompt text to send to the model. Use @path to load from a file.")
    parser.add_argument("--mode", choices=["research", "brainstorm"], default="research")
    parser.add_argument("--model", default="gpt-5.1", help="Model name to target.")
    parser.add_argument("--instructions", help="Override system instructions (text or @path to file).")
    parser.add_argument("--reasoning-effort", dest="reasoning_effort", choices=["none", "low", "medium", "high"], help="Set reasoning.effort.")
    parser.add_argument("--text-verbosity", dest="text_verbosity", choices=["low", "medium", "high"], help="Set text.verbosity.")
    parser.add_argument("--temperature", type=float, help="Sampling temperature (research only when reasoning allows).")
    parser.add_argument("--top-p", dest="top_p", type=float, help="Sampling top_p (research only when reasoning allows).")
    parser.add_argument("--seed", type=int, help="Deterministic sampling seed.")
    parser.add_argument("--vector-store", action="append", dest="vector_store_ids", help="Vector store IDs to search.")
    parser.add_argument("--conversation-id", dest="conversation_id", help="Conversation identifier for persistence.")
    parser.add_argument("--max-output-tokens", type=int, help="Override max_output_tokens in the payload.")
    parser.add_argument("--max-num-results", type=int, help="file_search.max_num_results override.")
    parser.add_argument("--web-search-options", help="JSON string or @path to merge into the web_search tool.")
    parser.add_argument("--file-search-options", help="JSON string or @path to merge into the file_search tool.")
    parser.add_argument("--tools-json", help="Full tools array as JSON or @path (replaces defaults).")
    parser.add_argument("--input-json", help="Custom input blocks as JSON array or @path.")
    parser.add_argument("--metadata", help="Arbitrary metadata JSON object to attach.")
    parser.add_argument("--extra-options", help="JSON object merged into the final payload for full control.")
    parser.add_argument(
        "--tool-choice",
        dest="tool_choice",
        default="auto",
        help="Tool choice policy (auto, required, none, or tool name).",
    )
    parser.add_argument("--store", dest="store", action="store_true", help="Persist responses on the server (default).")
    parser.add_argument("--no-store", dest="store", action="store_false", help="Do not persist responses on the server.")
    parser.set_defaults(store=None)
    parser.add_argument("--no-code-interpreter", dest="include_code_interpreter", action="store_false", default=True)
    parser.add_argument("--no-image-generation", dest="include_image_generation", action="store_false", default=True)
    parser.add_argument("--api-key", dest="api_key", help="OpenAI API key (defaults to OPENAI_API_KEY env variable).")
    parser.add_argument("--api-url", dest="api_url", help="Override the API endpoint (defaults to OPENAI_BASE_URL or official URL).")
    parser.add_argument("--organization", dest="organization", help="OpenAI organization ID (defaults to OPENAI_ORG_ID env variable).")
    parser.add_argument("--project", dest="project", help="OpenAI project ID (defaults to OPENAI_PROJECT env variable).")
    parser.add_argument("--dry-run", action="store_true", help="Print the payload without sending the request.")
    return parser.parse_args(argv)


def _load_prompt(prompt: str) -> str:
    if prompt.startswith("@"):
        path = prompt[1:]
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    return prompt


def _load_json_arg(value: Optional[str]) -> Optional[Any]:
    if value is None:
        return None

    data = value
    if value.startswith("@"):
        with open(value[1:], "r", encoding="utf-8") as file:
            data = file.read()

    return json.loads(data)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_arguments(argv)
    prompt_text = _load_prompt(args.prompt)
    context = RequestContext(
        conversation_id=args.conversation_id,
        vector_store_ids=args.vector_store_ids,
        max_output_tokens=args.max_output_tokens,
        web_search_options=_load_json_arg(args.web_search_options),
        file_search_options=_load_json_arg(args.file_search_options),
        include_code_interpreter=args.include_code_interpreter,
        include_image_generation=args.include_image_generation,
    )

    if args.max_num_results and not args.file_search_options:
        context.file_search_options = {"max_num_results": args.max_num_results}
    elif args.max_num_results and args.file_search_options:
        context.file_search_options = _load_json_arg(args.file_search_options)
        context.file_search_options["max_num_results"] = args.max_num_results

    instructions = _load_prompt(args.instructions) if args.instructions else None
    tools_override = _load_json_arg(args.tools_json)
    input_blocks = _load_json_arg(args.input_json)
    metadata = _load_json_arg(args.metadata)
    extra_options = _load_json_arg(args.extra_options)

    if args.mode == "research":
        payload = build_deep_research_payload(
            prompt_text,
            context=context,
            instructions=instructions or DEEP_RESEARCH_INSTRUCTION,
            model=args.model,
            reasoning_effort=args.reasoning_effort or "high",
            text_verbosity=args.text_verbosity or "high",
            temperature=args.temperature if args.temperature is not None else None,
            top_p=args.top_p if args.top_p is not None else None,
            seed=args.seed,
            tool_choice=args.tool_choice,
            store=args.store,
            max_output_tokens=args.max_output_tokens,
            tools=tools_override,
            input_blocks=input_blocks,
            metadata=metadata,
            extra_options=extra_options,
        )
    else:
        payload = build_brainstorm_payload(
            prompt_text,
            context=context,
            instructions=instructions or BRAINSTORM_INSTRUCTION,
            model=args.model,
            reasoning_effort=args.reasoning_effort or "none",
            text_verbosity=args.text_verbosity or "high",
            temperature=args.temperature if args.temperature is not None else 1.2,
            top_p=args.top_p if args.top_p is not None else 1.0,
            seed=args.seed,
            tool_choice=args.tool_choice,
            store=args.store,
            max_output_tokens=args.max_output_tokens,
            tools=tools_override,
            input_blocks=input_blocks,
            metadata=metadata,
            extra_options=extra_options,
        )

    if args.dry_run:
        print(pretty_print_payload(payload))
        return 0

    if not (args.api_key or os.getenv("OPENAI_API_KEY")):
        sys.stderr.write("Error: provide an OpenAI API key via --api-key or OPENAI_API_KEY to run a live request.\n")
        return 2

    response = send_response_request(
        payload,
        api_key=args.api_key,
        api_url=args.api_url,
        organization=args.organization,
        project=args.project,
    )
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
