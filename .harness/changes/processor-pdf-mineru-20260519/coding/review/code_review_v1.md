---
change_id: processor-pdf-mineru-20260519
target: coding_report_v1.md + diff (commit 6e726e5)
target_version: 1
review_version: 1
reviewer: claude-agent:processor-pdf-mineru-20260519-stage4-reviewer-v1
reviewed_at: 2026-05-19T09:45:00Z
verdict: APPROVED
---

# Code Review v1

## 范围审查结论

coding_report_v1.md 声明 3 个文件（`_mineru_client.py` new / `pdf_mineru.py` new / `__init__.py` modify），与 `git diff main...HEAD` 实际改动文件完全一致，无 scope creep，无遗漏，无目录错位。T-4（单测）/ T-5（self_check）按 DAG 留到 stage 5/8，符合流程设计。

---

## §1 文件级评审

### `_mineru_client.py`（新建，124 行）

**优点：**
- JSON 解析集中在 `_parse_submit_response` / `_parse_poll_response` 两个模块级函数，符合 spec 中"改一处"的可维护性要求。
- `_TERMINAL_OK` / `_TERMINAL_FAIL` 用集合枚举，扩展友好，查找 O(1)。
- `fetch_markdown` 的超时判断用 `time.monotonic()`（单调时钟，不受系统时间回拨影响），正确。
- `_headers()` 是唯一操作 token 的地方，token 不出现在日志、URL 或错误消息里，安全。
- 每条错误都带上下文（status_code / task_id），利于调试。

**问题：**

1. `_parse_submit_response`（line 113）和 `_parse_poll_response`（line 122）在 raise ValueError 时将完整 `payload` 用 `!r` 格式化进错误字符串。`payload` 在 poll 正常响应中可能包含 `"markdown"` 字段，即完整 Markdown 文本（数万字符）。这会：(a) 使异常消息体积无限膨胀；(b) 可能将文档内容暴露进日志（若上层 catch 后 logger.exception）。低概率但真实的可观测性与安全风险，建议 SHOULD FIX（见 §3）。

2. `_logger.debug`（line 105）行长 97 字符，通过 ruff 默认限制（88）——已确认 ruff green，但视觉上偏长。NICE TO HAVE。

### `pdf_mineru.py`（新建，143 行）

**优点：**
- 五项 Processor Protocol 数据属性齐全（`name` / `version` / `config_schema` / `accepts` / `produces`），且 `config_schema` 用模块级常量 `_CONFIG_SCHEMA` 与类体分离，保持类体简洁。
- `_ENV_URL` / `_ENV_TOKEN` 常量化，env key 不散落在代码里，符合 §0.5 "密钥走 config"。
- env 读取后立即 `.strip()` 防止空白字符误判，细节正确。
- `api_token = os.environ.get(_ENV_TOKEN, "").strip() or None`：token 缺失时为 `None`，有值时传给 client，整条链路无多余 None 检查。
- `del workspace` 与 `llm_summarize.py:57` 模式一致。
- `_PDF_SUFFIXES` 大小写不敏感过滤（`p.lower().endswith()`），符合 AC-7 语义。
- `Path(src_path).with_suffix(".md")` 正确替换后缀，符合 AC-8。
- `ProcessResult` 构造字段齐全，`files` 列表逐文件追加。

**问题：**

3. `run()` 中的串行主循环（line 122-135）对每个 PDF 调用了**两次** `asyncio.run`（`_convert_one` + `_upload` 各一次），共建两个事件循环。对比 `llm_summarize.py:103` 把 LLM 调用与 blob.put 合并在一个 `_do()` 协程里（一次 `asyncio.run`），以及 `markdown_normalize.py:103` 的单次调用模式，这里的双次调用偏离了既有模式，且两个事件循环之间无实际的并发收益（反而增加了 event loop 创建销毁开销）。不影响正确性，但偏离项目惯例。SHOULD FIX（见 §3）。

4. `run()` line 82：`blob_store = getattr(ctx, "blob_store", None)` 使用 `getattr` 动态取属性，与 `markdown_normalize.py:70` / `llm_summarize.py:63` 模式一致——项目历史遗留模式，本 change 无需单独修。但 mypy --strict 下此处是 `Any` 类型。（不计入本次 MUST/SHOULD，与先例一致。）

5. `notes` 字段（line 141）将 `api_url` 嵌入 ProcessResult.notes（`"pdf-mineru: N PDF(s) → markdown via {api_url}"`）。`api_url` 是内部服务 URL（env var），不是 secret，对比 `llm_summarize.py` 的 `notes` 同样暴露 model_id，模式一致，不构成安全问题。保留。

6. `view.iter_paths()` 后 `# type: ignore[attr-defined]`（line 98），与 `markdown_normalize.py:77` / `llm_summarize.py:68` 一致，沿用项目既有 workaround，不额外处理。

### `__init__.py`（修改，3 行增量）

**优点：**
- import 行、register 行、`__all__` 三处同步更新，无遗漏。
- 排列与已有 processor 风格一致。

**问题：** 无。

---

## §2 AC 对照表

| AC ID | kind | 代码位置（文件:行） | 实现是否名实相符 |
|---|---|---|---|
| AC-1 | static | `pdf_mineru.py:63-70`（类定义五属性）+ `pdf_mineru.py:72-78`（`run()` 签名） | 是。`name`/`version`/`config_schema`/`accepts`/`produces` + `run(inputs, config, workspace, ctx)` 完整实现 Processor Protocol。`isinstance(PdfMineruProcessor(), Processor)` runtime_checkable 可命中。 |
| AC-2 | static | `pdf_mineru.py:42-49`（`PdfMineruSpec`） | 是。`ConfigDict(extra="forbid")`，三字段类型与 spec 对齐。 |
| AC-3 | static | `__init__.py:9`（import）/ `__init__.py:16`（register）/ `__init__.py:23`（`__all__`） | 是。`_registry.register(PdfMineruProcessor())` 已调用；AC-3 命令 dry-import 可命中。 |
| AC-4 | static | `_mineru_client.py:30-77`（`MinerUClient` 类，三方法）/ `_mineru_client.py:21`（`import httpx`） | 是。`submit`/`poll`/`fetch_markdown` 齐全，全部 `async def`，使用 `httpx.AsyncClient`。 |
| AC-5 | static | `pdf_mineru.py:38`（`_ENV_URL = "MINERU_API_URL"`）/ `pdf_mineru.py:88-92`（读 env + ValueError） | 是。`os.environ.get(_ENV_URL, "").strip()` 空值分支显式 `raise ValueError`，语义正确不只是 grep 命中。 |
| AC-6 | static | `pdf_mineru.py:70`（`produces: RepoSpec = RepoSpec(layer="silver", subtype="pdf-markdown")`） | 是。`layer="silver"`, `subtype="pdf-markdown"`，精确匹配 spec。 |
| AC-7 | static | `pdf_mineru.py:37`（`_PDF_SUFFIXES = (".pdf",)`）/ `pdf_mineru.py:99`（`p.lower().endswith(_PDF_SUFFIXES)`） | 是。大小写不敏感过滤，非 PDF 不进 `pdf_paths`，也不进 `files` 产出列表，符合 AC-7 "不进产出 tree" 语义。 |
| AC-8 | static | `pdf_mineru.py:130`（`str(Path(src_path).with_suffix(".md"))`） | 是。用 `pathlib.Path.with_suffix(".md")` 替换后缀，`with_suffix` grep 命中；语义是将 `.pdf` 替换为 `.md`，正确。 |
| AC-9 | behavioral | 未在本 stage 落地（stage 5 T-4） | pending，符合 tasks.md DAG。本 stage 仅审静态实现。 |
| AC-10 | behavioral | 未在本 stage 落地（stage 5 T-4） | pending，符合 DAG。 |
| AC-11 | static | coding_report_v1.md 本地校验：`ruff` All passed / `mypy` 96 files no issues | 已通过，本 reviewer 未重跑，以 coding_report 为凭证，stage 8 T-6 会机械化复核。 |
| AC-12 | behavioral | `_mineru_client.py:45-48`（`_headers()` 含 Bearer token 分支） / `pdf_mineru.py:93`（token 读取传给 client） | 静态结构正确：有 token 时 `_headers()` 返回 `{"Authorization": "Bearer <token>"}`，`submit`/`poll` 均通过 `headers=self._headers()` 注入。behavioral 验证留 stage 5。 |
| AC-13 | static | 未在本 stage 落地（stage 8 T-5） | pending，符合 DAG。 |

---

## §3 问题列表

### MUST FIX（0 条）

无。

### SHOULD FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| S-1 | `pdf_mineru.py:128-129` | 串行循环内对每个 PDF 调用两次 `asyncio.run`（`_convert_one` 与 `_upload` 各创建一个事件循环），偏离 `llm_summarize.py` / `markdown_normalize.py` 的单次 `asyncio.run` 惯例，存在无必要的事件循环创建开销（每次 `asyncio.run` 初始化 + 销毁 event loop）。 | 将 `_convert_one` 与 `_upload` 合并为一个 `_process_one` 协程，只调一次 `asyncio.run`：`sha, size, out_path = asyncio.run(_process_one(raw, filename, src_path))`。不影响 AC 通过。 |
| S-2 | `_mineru_client.py:113,122` | `_parse_submit_response` 和 `_parse_poll_response` 异常消息用 `{payload!r}` 打印完整响应。poll 响应中可能含完整 Markdown 文本（数万字符），会导致超大异常消息、并在上层 `logger.exception` 时将文档内容写入日志。 | 截断 payload repr：`repr(payload)[:200]` 或只提取 `{list(payload.keys())}` 打印键名；markdown 字段内容不入错误消息。 |

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| N-1 | `_mineru_client.py:105` | `_logger.debug(...)` 行长 97 字符，超过 88 字符视觉标准，ruff 通过但可读性略受影响。 | 可拆成两行，但因 ruff 通过，不影响合并。 |
| N-2 | `pdf_mineru.py:124` | `raw = stream.read() if hasattr(stream, "read") else b"".join(stream)` 读取模式与 `markdown_normalize.py:93` / `llm_summarize.py:77` 完全重复（3 处），属于跨 processor 的共有逻辑。 | 可抽取到 `dataplat_core` 或 `processor_utils.py` 的工具函数（但 coding-style §0.1 "三处相似不一定要抽"，留 follow-up 判断是否值得抽象）。 |
| N-3 | `pdf_mineru.py:98` | `# type: ignore[attr-defined]` 沿用先例，但 `RepoView` Protocol 未声明 `iter_paths`——系统性问题（所有 processor 都受影响）。 | 可在 `RepoView` Protocol 中添加 `iter_paths()` 声明；开 follow-up change `protocol-repoview-iter-paths-*` 系统修复（不属本 change 范围）。 |

---

## §4 Verdict 与建议下一步

### Verdict：APPROVED

**理由：**
- MUST FIX = 0。
- SHOULD FIX 2 条均不影响正确性、安全性或 AC 通过；S-1（双 asyncio.run）在功能上完全正确，只是偏离惯例；S-2（payload 截断）是防御性改进，当前 MinerU 解析失败的罕见路径不带高风险。
- 代码架构清晰：client / processor / registry 三层分离，JSON 解析集中，token 未泄漏，与先例模式（llm_summarize / markdown_normalize / firecrawl_url）高度一致。
- ruff + mypy 本地校验通过，coding_report 如实反映改动。

### 建议下一步

1. **进入 stage 5（T-4 单测）**。SHOULD FIX S-1 建议在 stage 5 coding 时顺带合并（修改 `pdf_mineru.py` 后 tests 更简洁）；S-2 可视需要在单测阶段补截断逻辑。
2. **deferred SHOULD FIX 跟进：**
   - S-1：在 stage 5 coding 时合并两个 `asyncio.run`，无需额外 change。
   - S-2：若不在本 change 修，在 `processor-pdf-mineru-live-*` follow-up 时补截断（live 联调更能暴露 payload 大小问题）。
3. **NICE TO HAVE N-3**：开 follow-up `protocol-repoview-iter-paths-*` 系统修复 `RepoView` Protocol，消除所有 processor 的 `type: ignore`。

### 复检指引（作者修 S-1/S-2 后应运行）

```bash
cd apps/api && uv run ruff check dataplat_api packages/core worker/src
cd apps/api && uv run mypy dataplat_api packages/core/src worker/src
# 确认 AC-1/2/3/4/5/6 dry-import 仍全部退出 0（见 spec.md 各 AC 命令）
```
