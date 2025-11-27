# Deep Research Responses API 工具：Windows 超详细使用教程

> 本文面向在 Windows 10/11 上使用 Deep Research Responses API 辅助工具的初学者与进阶用户。内容极长且细节化，覆盖从环境准备、安装、命令行调用、参数调优、网络代理、常见报错到运维排查的全链路流程，并给出示例命令、截图建议与最佳实践清单。按章节逐步操作即可完成端到端体验。

## 1. 前置要求与整体流程概览

1. **系统版本**：建议 Windows 10 21H2 及以上、或 Windows 11 任意正式版，已安装最新累积更新补丁。
2. **用户权限**：建议使用具备本地管理员权限的帐户，便于安装 Python、写入环境变量与运行网络代理。
3. **必备软件**：
   - Python 3.10/3.11/3.12（官方 Windows x64 安装包）。
   - Git（可选，用于拉取仓库；若直接下载 ZIP，可跳过）。
   - PowerShell 7（推荐，以获得更好的终端体验）。
   - 可选：VS Code、Windows Terminal、Node.js（仅在需要额外工具时）。
4. **网络准备**：若需访问 OpenAI 官方端点，确保网络可达；如使用代理或私有网关，请提前确认 `OPENAI_BASE_URL` 配置。
5. **运行顺序**：下载代码 → 安装依赖 → 配置环境变量 → 选择模式（research/brainstorm）运行命令 → 查看 JSON 负载或真实响应 → 排查可能问题。

## 2. 获取代码与目录布局

- **克隆仓库（推荐）**：
  ```powershell
  git clone https://github.com/.../deep-research-2.git
  cd deep-research-2
  ```
- **下载 ZIP（无需 Git）**：在浏览器打开仓库页面，点击 "Code → Download ZIP"，解压后进入解压目录。
- **目录结构提示**：核心脚本位于 `src/deep_research/cli.py`；根目录包含 `README.md`、`requirements.txt`、`plan.md` 等文件；本教程位于 `docs/windows_tutorial_cn.md`。

## 3. 安装 Python 与环境配置

### 3.1 安装官方 Python

1. 访问 https://www.python.org/downloads/windows/ 下载 64 位 installer（例如 `python-3.12.2-amd64.exe`）。
2. 安装时勾选 **Add python.exe to PATH**，点击 "Customize installation"；保持默认选项即可。
3. 完成后在 PowerShell 执行：
   ```powershell
   python --version
   pip --version
   ```
   确认输出显示 3.10/3.11/3.12 版本及 pip 版本。

### 3.2 创建虚拟环境（强烈推荐）

```powershell
cd deep-research-2
python -m venv .venv
.\.venv\Scripts\activate
```
- 激活后提示符前应出现 `(.venv)`。
- 若遇执行策略限制，运行 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 再重试激活。

### 3.3 升级 pip 并安装依赖

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```
- 如果网络受限，可配置国内镜像：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`。

## 4. 配置 OpenAI 相关环境变量

在 PowerShell 中执行（示例）：
```powershell
setx OPENAI_API_KEY "sk-********"
setx OPENAI_BASE_URL "https://api.openai.com/v1"   # 若走官方；代理或私有网关请替换
setx OPENAI_ORG_ID "org_..."                        # 如需组织级别身份
setx OPENAI_PROJECT "proj_..."                      # 某些密钥必需
```
- `setx` 会写入当前用户的环境变量，需要重开终端或 `refreshenv` 生效。
- 临时会话可直接 `$env:OPENAI_API_KEY="sk-..."`，仅对当前窗口有效。

## 5. 运行 CLI：基础示例

### 5.1 深度研究模式（高推理、高工具覆盖）
```powershell
python -m deep_research.cli "Explain Q2 guidance risks for NVDA" \
  --mode research \
  --vector-store vs_invest_global \
  --conversation-id conv_nvda_2025 \
  --max-output-tokens 100000
```
- 适用于需要长篇、严谨、带搜索/文件检索/代码解释/图片生成的分析。
- `--vector-store` 提供向量库 ID 时才会启用文件检索；否则为了避免 API 校验报错会跳过。

### 5.2 头脑风暴模式（高多样性、低推理约束）
```powershell
python -m deep_research.cli "Brainstorm 20 non-consensus bearish theses for NVIDIA." \
  --mode brainstorm \
  --max-output-tokens 20000
```
- 适合多样化、发散式点子；推理关闭，采样参数更开放。

### 5.3 仅打印请求 JSON（不发网络请求）
```powershell
python -m deep_research.cli "Explain NVIDIA competitive moats" --dry-run
```
- 输出完整的 Responses API 载荷，便于审阅或调试。

## 6. 参数调优全览

| 分类 | 关键参数 | 作用 | Windows 终端示例 |
| ---- | -------- | ---- | ---------------- |
| 模型选择 | `--model` | 切换 Responses API 模型，如 `gpt-5.1`、`gpt-5.1-mini` | `--model gpt-5.1-mini` |
| 采样控制 | `--temperature` / `--seed` | 提升随机性或固定输出 | `--temperature 1.2 --seed 42` |
| 推理/文本 | `--max-output-tokens` / `--top-p` | 控制输出长度与核采样 | `--max-output-tokens 50000` |
| 工具策略 | `--tool-choice` | `auto`/`required`/`none` | `--tool-choice auto` |
| 自定义工具 | `--tools-json` | 传入 JSON 数组覆盖工具列表 | `--tools-json '[{"type":"web_search"}]'` |
| 额外字段 | `--extra-options` | 任意 Responses API 字段合并 | `--extra-options '{"response_format":"json"}'` |
| 上下文 | `--conversation-id` | 持久化对话线程 | `--conversation-id demo_thread` |
| 调试 | `--dry-run` | 仅打印 payload | `--dry-run` |

> 提示：在 PowerShell 输入多行命令时，用反引号 `` ` `` 续行，或改用单行命令避免换行带来的转义问题。

## 7. 向量检索与文件搜索

- 当提供 `--vector-store` 或在 `RequestContext.vector_store_ids` 里填写 ID 时，CLI 会自动开启文件搜索工具。
- 常见向量库 ID 需与后端配置对应；若 ID 不存在会触发 Responses API 校验错误。
- 建议先用 `--dry-run` 查看最终 JSON 是否包含 `file_search` 与正确的 `vector_store_ids`。

## 8. 网络与代理设置（Windows 专项）

1. **系统代理**：如需走企业代理或自建代理，确保代理允许 HTTPS 并与 `OPENAI_BASE_URL` 兼容。
2. **终端级代理**：
   ```powershell
   setx HTTPS_PROXY "http://127.0.0.1:7890"
   setx HTTP_PROXY  "http://127.0.0.1:7890"
   ```
   重新打开终端后生效。临时会话可用 `$env:HTTPS_PROXY="http://127.0.0.1:7890"`。
3. **证书问题**：企业代理可能需要根证书；在 Windows 证书管理器导入后，Python `ssl` 才能正常握手。
4. **常见报错**：
   - `SSLError: CERTIFICATE_VERIFY_FAILED`：检查代理证书或将代理切换到信任链完整的端点。
   - `ProxyError: tunneling failed`：确认代理允许 CONNECT 443、未拦截目标域名。

## 9. 典型工作流范例

### 9.1 投资研究：长篇报告
```powershell
python -m deep_research.cli "Produce a 10-page earnings preview for NVIDIA." \
  --mode research \
  --vector-store vs_invest_global \
  --conversation-id conv_global_equity_research_2025Q4 \
  --max-output-tokens 100000 \
  --tool-choice auto
```
- 生成包含网搜、引用与代码计算的长篇报告，适合投研、咨询等场景。

### 9.2 中文合规热点梳理
```powershell
python -m deep_research.cli "列举本周全球 AI 监管的新动态并给出来源链接" \
  --mode research \
  --max-output-tokens 12000 \
  --conversation-id live_demo
```
- 若缺少 API Key，程序会清晰提示；补充 `--api-key` 或设置环境变量后重试。

### 9.3 JSON 输出供二次处理
```powershell
python -m deep_research.cli "Write a markdown brief" \
  --extra-options '{"response_format": "json", "text": {"verbosity": "medium"}}' \
  --dry-run
```
- 便于在 Windows 上将 JSON 复制到后续自动化脚本或 VS Code 中处理。

## 10. 故障排查与常见问题

1. **缺少 API Key**：
   - 现象：CLI 报错提示 401 或缺少密钥。
   - 解决：检查 `OPENAI_API_KEY` 是否已在当前会话生效；在 PowerShell 执行 `echo $env:OPENAI_API_KEY` 验证。
2. **模型不可用或 entitlement 问题**：
   - 现象：401/403 或提示模型未启用。
   - 解决：确认账号具备 Responses API 权限；尝试 `--project`、`--organization` 补全范围。
3. **网络不通**：
   - 现象：连接超时、代理隧道失败。
   - 解决：测试 `Invoke-WebRequest https://api.openai.com/v1`；调整代理或切换出口网络。
4. **Windows 路径与转义**：
   - 现象：命令行字符串含中文或特殊字符导致解析异常。
   - 解决：用双引号包裹完整提示；多行续行时避免末尾多余空格。
5. **虚拟环境未激活**：
   - 现象：`ModuleNotFoundError: deep_research`。
   - 解决：先执行 `.\.venv\Scripts\activate` 或用完整模块路径 `python -m deep_research.cli`。
6. **缺少构建工具**（少见）：
   - 现象：安装依赖时提示需要 Microsoft Build Tools。
   - 解决：安装 "Build Tools for Visual Studio"，勾选 C++ 构建工具；或在 `requirements.txt` 中锁定无需编译的依赖版本。

## 11. 性能与资源建议

- **输出配额**：`--max-output-tokens` 过高会增加费用与延迟；在 Windows 终端观察响应进度，必要时降低。
- **并发调用**：可在多个 PowerShell 标签页并行运行，但请注意 API 速率限制和账号配额。
- **日志记录**：利用 PowerShell 的重定向保存输出：`python -m deep_research.cli "..." *> logs\run1.txt`。
- **安全**：不要将密钥写入脚本仓库；使用 `.env` 文件并添加到 `.gitignore`。

## 12. 在 VS Code 中的集成

1. 打开项目根目录；安装 Python 扩展。
2. 选择 `.venv` 解释器；在 `Run and Debug` 中创建任务执行示例命令。
3. 在终端面板执行本教程的命令，便于查看彩色输出与 JSON。

## 13. 进阶：直接调用库 API

在 Python 交互式环境（`python` 或 VS Code Notebook）中运行：
```python
from deep_research import RequestContext, run_deep_research, run_brainstorm

context = RequestContext(
    conversation_id="conv_global_equity_research_2025Q4",
    vector_store_ids=["vs_invest_global"],
)

resp = run_deep_research(
    "Produce a 10-page earnings preview for NVIDIA.",
    context=context,
    max_output_tokens=100000,
)
print(resp)
```
- 在 Windows 下同样依赖前述环境变量；若需代理，可在代码中设置 `os.environ['HTTPS_PROXY']`。

## 14. 最佳实践速查表

- **先 dry-run**：每次改参数先 `--dry-run` 审核载荷。
- **保持对话 ID**：长会话复用 `--conversation-id`，便于上下文连贯。
- **显式工具策略**：当希望强制使用工具时设 `--tool-choice required`；禁用则 `none`。
- **控制费用**：调小 `--max-output-tokens`，必要时调高 `temperature` 取样多样化而非长篇幅。
- **记录版本**：使用 `git status` 记录变更；为关键提示保存终端输出。

## 15. 附录：常用 PowerShell 一行式

```powershell
# 查看当前环境变量
Get-ChildItem Env: | Where-Object { $_.Name -like "OPENAI*" }

# 临时设置环境变量（仅当前会话）
$env:OPENAI_API_KEY="sk-..."

# 激活虚拟环境并运行 dry-run
after=`PowerShell` # 仅提示：在新标签执行
.\.venv\Scripts\activate; python -m deep_research.cli "Test prompt" --dry-run

# 使用代理测试 API 可达性
$env:HTTPS_PROXY="http://127.0.0.1:7890"; Invoke-WebRequest https://api.openai.com/v1/models

# 将输出保存到文件
python -m deep_research.cli "Explain NVIDIA moat" --dry-run *> logs\dry_run.txt
```

## 16. 快速自检清单（执行顺序）

1. `python --version` / `pip --version` 正常输出。
2. `.\.venv\Scripts\activate` 成功且提示符出现 `(.venv)`。
3. `pip install -r requirements.txt` 无报错。
4. `echo $env:OPENAI_API_KEY` 显示有效密钥（或确认使用 `--api-key`）。
5. `python -m deep_research.cli "Ping" --dry-run` 正常打印 JSON。
6. 根据需要切换 `--mode research` 或 `--mode brainstorm` 并添加向量库 ID。
7. 若调用真实 API，确保网络/代理可达并观察终端输出。

阅读完本教程后，你可以在 Windows 机器上从零搭建环境、运行示例、调优参数，并定位常见故障。祝你在深度研究与头脑风暴场景中高效产出！
