"""High-level helpers for issuing GPT-5.1 Responses API calls.

The package exposes convenience functions for the two primary workflows
outlined in ``plan.md``:

- ``run_deep_research``: strict, tool-heavy research mode with reasoning
  turned up and large output budgets.
- ``run_brainstorm``: divergent, sampling-driven exploration with
  verbosity preserved and reasoning disabled.
"""
from .client import (
    BRAINSTORM_INSTRUCTION,
    DEEP_RESEARCH_INSTRUCTION,
    RequestContext,
    build_brainstorm_payload,
    build_deep_research_payload,
    pretty_print_payload,
    run_brainstorm,
    run_deep_research,
    send_response_request,
)

__all__ = [
    "BRAINSTORM_INSTRUCTION",
    "DEEP_RESEARCH_INSTRUCTION",
    "RequestContext",
    "build_brainstorm_payload",
    "build_deep_research_payload",
    "pretty_print_payload",
    "run_brainstorm",
    "run_deep_research",
    "send_response_request",
]
