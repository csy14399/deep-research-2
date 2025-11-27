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
pip install -r requirements.txt
```

## Usage

Run either mode from the command line. Prompts can be supplied directly
or loaded from a file with the `@path` shorthand.

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
