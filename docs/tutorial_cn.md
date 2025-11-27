# 深度研究与头脑风暴助手中文超详解教程（面向非技术人员）

本教程旨在帮助没有技术背景的同事，循序渐进地掌握本仓库提供的“深度研究（research）”与“头脑风暴（brainstorm）”两种模式。文章内容覆盖环境准备、安装、配置、常用命令、典型场景、排错、最佳实践与常见问答，力求一步步可操作。阅读完毕后，您无需编程经验即可独立使用工具，完成高质量的信息收集和创意发散。

---
## 1. 这是什么工具？
- **核心作用**：通过 OpenAI Responses API（支持官方与柏拉图 AI 中转）调用 GPT-5.1，自动完成深度研究或创意头脑风暴。
- **两种模式**：
  - **research（深度研究）**：强调推理链路、引用外部资料（网页、文件、代码执行、图片等工具），适合严谨、长篇的分析报告。
  - **brainstorm（头脑风暴）**：降低推理成本，提升想象力与发散性，适合快速收集非共识观点或创意。
- **交互方式**：既可以在命令行直接运行，也可在 Python 代码中调用封装好的函数。

---
## 2. 前置条件与准备清单
即便您不懂技术，也请按照清单逐项完成：
1. **安装 Python 3.10+**：建议从 [Python 官网](https://www.python.org/downloads/) 下载，安装时勾选“Add Python to PATH”。
2. **获取 API Key**：
   - 方式 A：OpenAI 账户的 `OPENAI_API_KEY`。
   - 方式 B：如果公司提供柏拉图 AI 中转，请准备对应的 Key，并将 `OPENAI_BASE_URL` 设为 `https://api.bltcy.ai/v1`。
3. **准备终端/命令行工具**：
   - Windows 可使用“命令提示符”或“PowerShell”。
   - macOS/Linux 可使用“终端（Terminal）”。
4. **克隆或下载代码**：
   - 若熟悉 Git：`git clone <仓库地址>`，或下载 Zip 后解压。
5. **网络要求**：确保能访问 `api.openai.com` 或柏拉图中转地址；公司网络若有代理，请按 IT 指引配置。

---
## 3. 安装步骤（零基础可跟做）
1. 打开终端，进入仓库文件夹。例如：
   ```bash
   cd /path/to/deep-research-2
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
   - 如果公司要求使用镜像源，可在命令后添加 `-i https://pypi.tuna.tsinghua.edu.cn/simple`。
   - 出现“权限不足”时，可在命令前加上 `python -m` 或在虚拟环境中执行。

---
## 4. 配置环境变量（最重要）
在运行命令前，需要告诉程序去哪个地址、用哪个 Key：
- **方式 1：一次性在命令前声明**（推荐临时使用）：
  ```bash
  OPENAI_API_KEY="你的密钥" OPENAI_BASE_URL="https://api.bltcy.ai/v1" \
  python -m deep_research.cli "输入你的问题" --mode research
  ```
- **方式 2：长期保存到系统**（便于多次使用）：
  - Windows：在“环境变量”界面添加 `OPENAI_API_KEY`，值为你的密钥；如需中转，再添加 `OPENAI_BASE_URL=https://api.bltcy.ai/v1`。
  - macOS/Linux：在 `~/.bashrc` 或 `~/.zshrc` 末尾加入：
    ```bash
    export OPENAI_API_KEY="你的密钥"
    export OPENAI_BASE_URL="https://api.bltcy.ai/v1"
    ```
    保存后执行 `source ~/.bashrc`（或相应文件）使其生效。

> 提示：若不使用柏拉图 AI 中转，可省略 `OPENAI_BASE_URL`，默认直连官方接口。

---
## 5. 最快捷的入门示例
1. **深度研究模式**：
   ```bash
   python -m deep_research.cli "解释 2024 年 NVIDIA 财报的主要风险" --mode research \
     --vector-store vs_invest_global --conversation-id demo_nvda --max-output-tokens 80000
   ```
   - 作用：生成长篇、严谨的风险分析，自动调用网页检索、文件检索、代码执行等工具。
2. **头脑风暴模式**：
   ```bash
   python -m deep_research.cli "给出 20 条针对 NVIDIA 的逆向投资观点" --mode brainstorm \
     --vector-store vs_invest_global --max-output-tokens 20000
   ```
   - 作用：快速产出发散性、非共识的想法，便于筛选创意。
3. **查看请求而不真正发送（dry-run）**：
   ```bash
   python -m deep_research.cli "解释 NVIDIA 竞争壁垒" --dry-run
   ```
   - 作用：打印将要发送的 JSON 请求体，便于审阅参数。

---
## 6. 命令行参数详细说明（逐条解读）
- `--mode`：选择 `research` 或 `brainstorm`。前者强调推理深度，后者强调创意发散。
- `--vector-store`：向模型声明可用的向量数据库 ID，便于调用内部知识库检索。可填多个，用空格分开。
- `--conversation-id`：会话标识，提供历史上下文，便于连续追问或分阶段完成报告。
- `--max-output-tokens`：控制生成长度。深度研究建议 50,000–100,000；头脑风暴可 10,000–30,000。
- `--api-key`：在命令行直接提供密钥；若已设置环境变量，可省略。
- `--api-url`：覆盖默认的 `OPENAI_BASE_URL`。留空则使用环境变量或官方地址。
- `--dry-run`：只打印请求，不发送网络请求；适用于审批或审计场景。

> 简化记忆：**模式、知识库、会话号、长度**是最常用的四个参数，其他保持默认即可。

### 6.1 全参数自由配置：想调什么就调什么

如果您希望完全掌控 Responses API 的所有字段，可以使用以下参数：

- **模型与指令**：`--model`、`--instructions`
- **推理/采样**：`--reasoning-effort`、`--temperature`、`--top-p`、`--seed`
- **文字风格**：`--text-verbosity`
- **工具策略**：`--tool-choice`、`--no-code-interpreter`、`--no-image-generation`
- **工具细节**：
  - `--web-search-options`：传入 JSON（或 `@文件路径`），可指定 `allowed_domains`、`user_location` 等。
  - `--file-search-options`：传入 JSON，或直接用 `--max-num-results` 覆盖检索召回数量。
  - `--tools-json`：完全替换默认工具列表。
- **输入与元数据**：`--input-json` 传入自定义 `input` 块，`--metadata` 附加任意业务字段。
- **任意合并**：`--extra-options '{"response_format": "json"}'` 可将任何合法字段合并到最终请求体。

示例：

```bash
# 使用自定义工具列表 + 设定随机种子 + 指定响应格式
python -m deep_research.cli "汇总英伟达近期负面新闻" \
  --mode research \
  --tools-json '[{"type": "web_search", "filters": {"allowed_domains": ["nvidia.com", "sec.gov"]}}]' \
  --seed 2025 \
  --extra-options '{"response_format": "json"}' \
  --dry-run
```

这样，几乎所有官方 Responses API 支持的字段都可以通过命令行直接控制。

---
## 7. 典型场景操作指南
### 7.1 投资研究报告
1. 准备好提问：如“请从需求、供应链、竞争对手三个维度评估英伟达 2024-2026 年增长确定性”。
2. 运行命令：
   ```bash
   python -m deep_research.cli "请从需求、供应链、竞争对手三个维度评估英伟达 2024-2026 年增长确定性" \
     --mode research --vector-store vs_invest_global --conversation-id nvda_growth_2024 --max-output-tokens 90000
   ```
3. 程序会输出详细的章节式分析、引用路径和推理步骤，可直接用于报告初稿。

### 7.2 市场创意头脑风暴
1. 准备主题：如“针对新能源汽车行业，列出 15 条反共识的风险点和投资机会”。
2. 运行命令：
   ```bash
   python -m deep_research.cli "新能源汽车行业的 15 条反共识风险与机会" --mode brainstorm \
     --vector-store vs_invest_global --max-output-tokens 25000
   ```
3. 结果会包含多角度、跳脱常规的想法，便于团队快速讨论。

### 7.3 分阶段对话
- 第一次运行指定 `--conversation-id`，获得初稿。
- 后续针对同一会话号追加问题（如“补充竞争对手对比表格”），模型会参考上下文继续扩展。

### 7.4 与知识库联动
- 如果已有内部文档被索引到向量数据库，只需在命令中提供对应的 `--vector-store` ID，模型会优先引用内部材料。

---
## 8. 图形化思维：请求流程一张图（文字说明版）
1. 读取命令行参数（模式、会话号、知识库、密钥等）。
2. 构造符合 Responses API 的 JSON 请求体：
   - 设定模型 `gpt-5.1`，高 `max_output_tokens` 与 `temperature` 取值（在 research/brainstorm 间有所区分）。
   - 自动声明工具：网页搜索、文件检索、代码解释器、图片生成、浏览器等。
   - 按需附带向量数据库 ID，启用 `conversation` 以持续对话。
3. 根据 `OPENAI_BASE_URL` 决定最终请求地址：
   - 若形如 `https://api.bltcy.ai/v1`，会自动补全 `/responses`。
   - 若已完整指定（含 `/responses`），则原样使用。
4. 携带 `Authorization: Bearer <API_KEY>` 发送请求。
5. 输出模型返回的内容；若 `--dry-run` 则只打印 JSON，不发送网络请求。

---
## 9. 常见问题（FAQ）
1. **提示未找到 API Key**：请检查是否在命令行或环境变量中正确设置 `OPENAI_API_KEY` 或 `--api-key`。
2. **提示连接失败**：
   - 公司网络可能限制外网访问，请联系 IT 开通或使用柏拉图中转 `OPENAI_BASE_URL=https://api.bltcy.ai/v1`。
   - 检查是否有代理软件冲突，可尝试临时关闭或在终端设置 `HTTP_PROXY`/`HTTPS_PROXY`。
3. **生成内容过短**：适当提高 `--max-output-tokens`，或在提示语中明确“生成 8 页报告”之类的长度要求。
4. **想让回答更有创意**：在头脑风暴模式下提高温度（目前默认已较高），并在提示中要求“非共识、逆向、跳脱常规”。
5. **想要更多引用或数据来源**：在提示语中注明“请列出引用链接或数据出处”，并保持 research 模式以便工具调用。
6. **如何保存结果**：在命令行中使用重定向，如 `... > output.txt`，即可把结果保存成文件。
7. **多轮追问会丢失上下文吗？** 只要保持相同的 `--conversation-id`，上下文会被模型保留用于后续回答。

---
## 10. 最佳实践清单
- **写清任务边界**：说明时间范围、行业、维度（市场/技术/财务等）。
- **明确输出格式**：例如“输出包含摘要、要点、数据表、结论、后续行动”。
- **控制长度**：给出期望页数或字数，并调整 `--max-output-tokens`。
- **善用知识库**：提供 `--vector-store` 以调用内部资料，减少公开信息的不确定性。
- **先 dry-run 再发送**：在正式调用前使用 `--dry-run` 复核请求体，确保参数正确。
- **保护密钥安全**：不要把 API Key 写入文档或截图；使用环境变量或安全凭证管理工具。

---
## 11. 进阶：在 Python 中使用（可选）
如果您愿意在少量代码中集成，也有简洁接口：
```python
from deep_research import RequestContext, run_deep_research, run_brainstorm

context = RequestContext(
    conversation_id="conv_demo", 
    vector_store_ids=["vs_invest_global"]
)

# 深度研究
resp = run_deep_research(
    "生成 10 页的 AI 芯片行业竞争格局报告", 
    context=context, 
    max_output_tokens=100000
)
print(resp)

# 头脑风暴
resp = run_brainstorm(
    "列出 15 个 AI 芯片行业的黑天鹅场景", 
    context=context, 
    max_output_tokens=25000
)
print(resp)
```
上述代码无需理解底层实现，只需照抄即可运行；与命令行效果一致。

---
## 12. 常见报错快速定位表
| 报错提示 | 可能原因 | 解决办法 |
| --- | --- | --- |
| `Missing API key` | 未设置密钥或拼写错误 | 核对 `OPENAI_API_KEY` 或 `--api-key` |
| `Connection error` | 网络受限或代理冲突 | 尝试柏拉图中转，或关闭冲突代理 |
| `Unauthorized` | 密钥无效或权限不足 | 更换有效 Key，确认账户余额或权限 |
| `Rate limit` | 请求过于频繁 | 等待几秒重试，或降低并发 |
| `Validation error` | 参数格式不符 | 使用 `--dry-run` 检查请求体，遵循示例 |

---
## 13. 结语
- 对于非技术同事，只需：**安装 → 设置密钥 → 复制示例命令**，即可生成高质量研究或创意内容。
- 若遇到任何困难，优先使用 `--dry-run` 查看请求体，再对照本教程的排错章节逐步解决。
- 熟练后，可根据业务需求调整提示、长度和模式，结合内部知识库实现更贴合团队的智能协作。

祝使用顺利！
