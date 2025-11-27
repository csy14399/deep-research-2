# Deep Research Responses API Helpers

This repository implements the guidance from `plan.md` by providing Python
helpers to build and submit OpenAI Responses API requests for two
workflows:

- **Deep research mode**: maximizes reasoning effort, verbosity, and tool
  coverage for long-form investment analysis.
- **Brainstorming mode**: disables reasoning to enable sampling
  parameters, while keeping verbose, tool-assisted outputs.

## Installation

```bash
pip install -e .

# Optional: install testing tools
pip install -e .[dev]
```

> Tip for Windows users: if you see `ModuleNotFoundError: No module named 'deep_research'`
> when running `python -m deep_research.cli`, make sure the project is installed in
> your virtual environment via `pip install -e .`. Installing only the dependencies
> from `requirements.txt` will not place the `deep_research` package on your
> `PYTHONPATH`.

## Usage

Run either mode from the command line. Prompts can be supplied directly
or loaded from a file with the `@path` shorthand. File search is included
only when you provide vector store IDs via `--vector-store` (or
`RequestContext.vector_store_ids`); otherwise it is omitted to avoid
`vector_store_ids` validation errors from the Responses API.

```bash
# High-rigor research with large output budget
python -m deep_research.cli "Explain Q2 guidance risks for NVDA" \
  --mode research \
  --vector-store vs_invest_global \
  --conversation-id conv_nvda_2025 \
  --max-output-tokens 100000

# Divergent brainstorming with higher temperature
python -m deep_research.cli "@prompts/nvda_tail_risks.txt" \
  --mode brainstorm \
  --vector-store vs_invest_global \
  --max-output-tokens 20000
```

Use `--dry-run` to print the JSON payload without sending a network
request:

```bash
python -m deep_research.cli "Explain NVIDIA competitive moats" --dry-run
```

### Run a live, internet-backed research request

Provide a valid OpenAI key (via `OPENAI_API_KEY` or `--api-key`) to let the
Responses API perform real-time web searches and calculations. For
example:

```bash
export OPENAI_API_KEY=sk-...
python -m deep_research.cli "列举本周全球 AI 监管的新动态并给出来源链接" \
  --mode research \
  --max-output-tokens 12000 \
  --conversation-id live_demo
```

The CLI will exit with a clear error if a key is missing when attempting a
live call. If you see a `401 Unauthorized` response, double-check that your
key is valid, enabled for the Responses API, and routed through the correct
`OPENAI_BASE_URL` when using a proxy. Some organization-scoped keys require
project scoping to authenticate correctly—pass `--project <project_id>` (or
set `OPENAI_PROJECT`) and `--organization <org_id>` (or `OPENAI_ORG_ID`) if
you receive 401s while the key works elsewhere. Keys that succeed for Chat
Completions may still be blocked from the Responses API; confirm your
account has the proper entitlement if authentication keeps failing.

### Adjust every parameter

All request fields can be overridden from the CLI. You can swap models,
edit reasoning/text settings, change tools, and merge arbitrary JSON into
the payload:

```bash
# Custom tool list and deterministic sampling
python -m deep_research.cli "Summarize the latest NVIDIA headlines" \
  --model gpt-5.1-mini \
  --tool-choice auto \
  --tools-json '[{"type": "web_search", "filters": {"allowed_domains": ["nvidia.com"]}}]' \
  --seed 42 \
  --dry-run

# Merge any Responses API field
python -m deep_research.cli "Write a markdown brief" \
  --extra-options '{"response_format": "json", "text": {"verbosity": "medium"}}' \
  --dry-run
```

Environment variables:

- `OPENAI_API_KEY`: required if `--api-key` is not provided.
- `OPENAI_BASE_URL`: optional override of the API endpoint. Set to
  `https://api.bltcy.ai/v1` to route through Plato AI's proxy; the
  `/responses` path is appended automatically when omitted.
- `OPENAI_ORG_ID`: optional organization ID header if your key is scoped to a
  specific org.
- `OPENAI_PROJECT`: optional project ID header; required for some keys.

## Library API

The `deep_research` package exposes convenient builders and runners if
you prefer to integrate the flows directly in Python:

```python
from deep_research import RequestContext, run_deep_research, run_brainstorm

context = RequestContext(
    conversation_id="conv_global_equity_research_2025Q4",
    vector_store_ids=["vs_invest_global"],
)

response = run_deep_research(
    "Produce a 10-page earnings preview for NVIDIA.",
    context=context,
    max_output_tokens=100000,
)
```

### Brainstorming

```python
response = run_brainstorm(
    "Brainstorm 20 non-consensus bearish theses for NVIDIA.",
    context=context,
    max_output_tokens=20000,
)
```

The payloads align with the parameter recommendations in `plan.md`,
including high verbosity, tool coverage (web search, file search, code
interpreter, image generation), and conversation persistence.

## 额外资源（中文）

面向非技术同事的超长中文教程，涵盖安装、环境配置、命令行示例、常见问题与排错指南：请见
[`docs/tutorial_cn.md`](docs/tutorial_cn.md)。
