---
change_id: processor-pdf-mineru-20260519
version: 1
authored_at: 2026-05-19T09:10:00Z
status: draft
---

# Spec：PdfMineruProcessor（PDF → MD via MinerU 异步 API）

## 背景

- `design.md` §2.3 / §4.2：Processor 把上游 Repository 转换为下游 Repository；Bronze（raw 文件）→ Silver（cleaned / 规范化文本）是其典型形态之一。
- 当前已有的 processor 都处理纯文本（`markdown-normalize` / `llm-summarize` / `llm-qa-gen`），缺少把 PDF 原始资产转为 Markdown 的能力。
- 业务诉求：用户录入的 PDF 文档需要进入 LLM 训练数据流水线，前置必须转成 Markdown 才能跑 `markdown-normalize` / `llm-summarize` / `llm-qa-gen` 等下游 processor。
- MinerU（OpenDataLab）已经在集群中部署为独立服务：用户在 stage 0 选定 (1) HTTP API 集成（worker 不直接 import mineru/magic-pdf，规避 GPU/torch 依赖膨胀）；(2) 异步 job 接口（POST 提交 → GET 轮询），适合大 PDF；(3) endpoint / token 走环境变量 `MINERU_API_URL` / `MINERU_API_TOKEN`（与 LLM Gateway 习惯对齐，避免 token 落入 ProcessRequest.config）；(4) 产出落在 Silver 层。

## 问题陈述

- 缺 `apps/api/dataplat_api/processors/pdf_mineru.py`（含 `PdfMineruSpec` Pydantic + `PdfMineruProcessor` 实现）。
- 缺 `apps/api/dataplat_api/processors/_mineru_client.py`（薄 HTTP 客户端：`submit` / `poll` / `fetch_markdown`；放独立模块便于 mock & 单测）。
- `processors/__init__.py` 未注册新 processor → registry 调用方 404。
- 没有 mock 异步 job 轮询的测试 fixture；test_processor.py / test_llm_qa_gen.py 均无 httpx mock 模式，需借鉴 `adapters/firecrawl_url.py` + `tests/test_firecrawl.py` 的 `_FakeAsyncClient` 模式。
- `scripts/_self_check.sh` 未含本 change AC block，stage 2 reviewer 无法机械化校验。

## 范围

In scope（与下方 AC 编号对齐）：

- AC-1: `PdfMineruProcessor` 实现 `Processor` Protocol
- AC-2: `PdfMineruSpec` Pydantic（extra=forbid）
- AC-3: `processors/__init__.py` 注册 `pdf-mineru` v0.1
- AC-4: `_mineru_client.py` 含 `MinerUClient` 类，方法 `submit` / `poll` / `fetch_markdown`，使用 `httpx.AsyncClient`
- AC-5: `pdf_mineru.py` 显式读 env `MINERU_API_URL`（空/缺失 → ValueError，端到端体现在 AC-9 失败分支）
- AC-6: `PdfMineruProcessor.produces` = `RepoSpec(layer="silver", subtype="pdf-markdown")`
- AC-7: `pdf_mineru.py` 显式过滤 `.pdf`（大小写不敏感）；非 PDF 文件被跳过（不落入产出 tree）
- AC-8: `pdf_mineru.py` 输出文件名 pattern `<basename>.md`（同名替换 .pdf → .md）
- AC-9: behavioral —— pytest 行为：mock httpx，跑完 `pdf-mineru` processor 对一个 1-PDF 仓产出含 `<basename>.md` 的 commit，且轮询失败分支 raise ValueError
- AC-10: `tests/test_pdf_mineru.py` ≥ 6 测试 + 全 PASS
- AC-11: ruff + mypy 全 PASS（含 worker/src）
- AC-12: `MINERU_API_TOKEN` 存在时 `MinerUClient` 在请求头注入 `Authorization: Bearer <token>`；不存在时不发头（pytest 行为验证）
- AC-13: AC-13 自递归（self_check 入口存在）

## 非范围

显式列出**不做**的事，避免后续 scope creep：

- 不做 Pipeline / Recipe 自动触发 PDF → MD：开 follow-up `recipe-pdf-mineru-*`。
- 不做 Web UI 「上传 PDF 一键转 MD」入口：开 follow-up `web-pdf-mineru-ui-*`。
- 不做真 MinerU 服务的 live CI 测试：单测仅用 `_FakeAsyncClient` mock；开 follow-up `processor-pdf-mineru-live-*`。
- 不抽取图片 / 表格 / 公式 资源（即便 MinerU 返回也只取 markdown 字段）：开 follow-up `processor-pdf-mineru-assets-*`。
- 不做多 PDF 并发处理 / 并发轮询：本 change 严格串行；开 follow-up `processor-pdf-mineru-concurrent-*`。
- 不做增量跳过（同 PDF 已有 MD 跳过）：本 change 总是重算；开 follow-up `processor-pdf-mineru-incremental-*`。
- 不动 `ProcessorRunner` / `StandardRunContext` / `routers/process.py` / `jobs/tasks.py`：现有 framework 足够。
- 不动 `markdown-normalize` / `llm-summarize` / `llm-qa-gen` / `firecrawl-url`：本 change 与它们正交。

## 验收标准（13 AC）

每条 AC 都附 1-行命令可在 `scripts/_self_check.sh` 直接跑。`kind` 列：static = grep / test -f / dry-import；behavioral = 真跑代码（pytest 等）。

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | PdfMineruProcessor 类存在 + 实现 Processor Protocol | `test -f apps/api/dataplat_api/processors/pdf_mineru.py && cd apps/api && uv run python -c "from dataplat_core.protocols.processor import Processor; from dataplat_api.processors.pdf_mineru import PdfMineruProcessor; assert isinstance(PdfMineruProcessor(), Processor)"` | 命令退出 0 |
| AC-2 | static | PdfMineruSpec extra=forbid | `cd apps/api && uv run python -c "from dataplat_api.processors.pdf_mineru import PdfMineruSpec; assert PdfMineruSpec.model_config.get('extra')=='forbid'"` | 命令退出 0 |
| AC-3 | static | registry 注册 pdf-mineru v0.1 | `cd apps/api && uv run python -c "import dataplat_api.processors; from dataplat_api.runner.processor_registry import get_processor_registry; assert get_processor_registry().get('pdf-mineru','0.1') is not None"` | 命令退出 0 |
| AC-4 | static | MinerUClient 三方法齐全 + 用 httpx（test -f + 正向 grep + dry-import） | `test -f apps/api/dataplat_api/processors/_mineru_client.py && grep -q "httpx" apps/api/dataplat_api/processors/_mineru_client.py && cd apps/api && uv run python -c "from dataplat_api.processors._mineru_client import MinerUClient; assert all(hasattr(MinerUClient, m) for m in ['submit','poll','fetch_markdown'])"` | 命令退出 0 |
| AC-5 | static | pdf_mineru.py 显式读 MINERU_API_URL + 缺失时 raise ValueError（正向双 grep） | `grep -q "MINERU_API_URL" apps/api/dataplat_api/processors/pdf_mineru.py && grep -qE "raise[[:space:]]+ValueError" apps/api/dataplat_api/processors/pdf_mineru.py` | 命令退出 0 |
| AC-6 | static | produces = silver/pdf-markdown | `cd apps/api && uv run python -c "from dataplat_api.processors.pdf_mineru import PdfMineruProcessor; p=PdfMineruProcessor(); assert p.produces.layer=='silver' and p.produces.subtype=='pdf-markdown'"` | 命令退出 0 |
| AC-7 | static | pdf_mineru.py 过滤 .pdf（_PDF_SUFFIXES 常量含 .pdf） | `grep -q "_PDF_SUFFIXES" apps/api/dataplat_api/processors/pdf_mineru.py && grep -F -q ".pdf" apps/api/dataplat_api/processors/pdf_mineru.py` | 命令退出 0 |
| AC-8 | static | 输出文件名 pattern `<basename>.md`（grep `.md` + 路径变换 hint：`with_suffix` 或 `[:-4]`） | `grep -F -q ".md" apps/api/dataplat_api/processors/pdf_mineru.py && grep -qE "with_suffix\|\[:-4\]" apps/api/dataplat_api/processors/pdf_mineru.py` | 命令退出 0 |
| AC-9 | behavioral | mock httpx，跑 pdf-mineru 成功路径产出 `<basename>.md` blob，且轮询返 status=failed 时 processor raise ValueError | `cd apps/api && uv run pytest -q --tb=no tests/test_pdf_mineru.py::test_run_success tests/test_pdf_mineru.py::test_run_poll_failed_raises` | pytest 2 case PASS |
| AC-10 | behavioral | tests/test_pdf_mineru.py ≥ 6 + 全 PASS | `[ "$(cd apps/api && uv run pytest --collect-only -q tests/test_pdf_mineru.py 2>&1 \| grep -cE 'test_pdf_mineru\.py::')" -ge 6 ] && (cd apps/api && uv run pytest -q --tb=no tests/test_pdf_mineru.py)` | ≥ 6 + 全 PASS |
| AC-11 | static | ruff + mypy 全 PASS（含 worker/src） | `uv run ruff check apps/api packages/core worker/src && uv run mypy apps/api/dataplat_api packages/core/src worker/src` | 命令退出 0 |
| AC-12 | behavioral | MINERU_API_TOKEN 存在时请求头含 Authorization Bearer；不存在时无 | `cd apps/api && uv run pytest -q --tb=no tests/test_pdf_mineru.py::test_client_token_header_present tests/test_pdf_mineru.py::test_client_token_header_absent` | pytest 2 case PASS |
| AC-13 | static | AC-13 自递归（self_check 含 run_processor_pdf_mineru） | `grep -q "run_processor_pdf_mineru" scripts/_self_check.sh` | 命令退出 0 |

> behavioral AC 数 = 3（AC-9 / AC-10 / AC-12），满足 stage 1/2 SKILL § "AC 分层规约" 至少 1 条 behavioral 的硬规则。

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| MinerU 真实 API JSON schema 与 spec 假设有差异（字段名 / 状态枚举） | 中 | mock 跑通但 live 失败 | `_mineru_client.py` 把 JSON 解析集中到一处（解析 `task_id` / `status` / `markdown` 三个键）；spec 显式列出假设字段名；live 测试归 follow-up |
| httpx.AsyncClient 在 to_thread 内用 asyncio.run 调用 | 中 | event loop 冲突 | 已有 `llm-summarize` 同模式（`asyncio.run(_do())`）；processor.run 跑在 worker thread，主线程 loop 不在场，asyncio.run 合法 |
| 轮询无超时导致 worker 卡死 | 中 | 长 PDF 阻塞 job | `PdfMineruSpec.poll_timeout_seconds` 默认 600.0；超时显式 raise ValueError → ProcessorRunner 转 400 |
| env MINERU_API_URL 未设置 → 测试或部署时静默失败 | 中 | 难定位 | processor.run 启动时如读到空值显式 `raise ValueError("MINERU_API_URL 未设置")`；AC-5 grep 命中；测试用 monkeypatch.setenv |
| _FakeAsyncClient mock 复杂（异步上下文 + 多端点路由） | 中 | 测试维护成本 | 沿用 firecrawl test 的 `monkeypatch.setattr("httpx.AsyncClient", _FakeAsyncClient)` 模式；FakeClient `__aenter__/__aexit__` + `post/get` 按 URL 路由到预设 response |
| AC 命令 dry-parse 失败 | 低 | 卡 stage 2 | AC-1/2/3/6 共 4 条 python -c 已 compile 通过；AC-4 的 python -c 也已 compile |
| summary.md 占位符残留（SKILL #1） | 低 | _self_check 硬 FAIL | summary.md frontmatter 已填实值；范围摘要、关键决策、阶段表已填；占位符 grep = 0 |
| 测试不真跑 mineru → behavioral AC 名实不符（SKILL ac-kind-lint） | 低 | reviewer MUST FIX | behavioral AC 全部都跑 `uv run pytest` 真断言 HTTP 流程；FakeClient 验证 submit→poll→fetch 三跳 |
| worker 进程未 import dataplat_api.processors（沿 adapter 历史坑） | 低 | registry 拿不到 pdf-mineru | 已有 `processors/__init__.py` import 路径；本 change 在 init 加 `from .pdf_mineru import PdfMineruProcessor` + `register(...)`；AC-3 即覆盖 |

## 跨链路一致性自审（request-analysis SKILL 8 条硬规则摘要）

1. ✅ summary 先行：summary.md frontmatter 已填；占位符 grep = 0
2. ✅ 边界清楚：范围 / 非范围 / 受影响模块 / 易混淆排除清晰，覆盖 coding 阶段所有可能动到的文件
3. ✅ AC 可执行：13 条 AC 每条都附 1-行命令；4 条 python -c 已 compile 通过；2 条 pytest 命令也 dry-parse 过
4. ✅ AC 分层规约：表含 kind 列；behavioral 数 = 3（AC-9 / AC-10 / AC-12），非豁免 change 满足 ≥ 1 条要求
5. ✅ 豁免判定：本 change 改 apps/api/ + scripts/_self_check.sh，**非豁免**；reviewer 用 git diff 复核应得出同样结论
6. ✅ 反向 grep：本 spec 未使用 `! grep` 模式；如 coding 阶段补反向断言（如 `! grep "asyncio.gather"`），按 SKILL 要求加 test -f 前置
7. ✅ 跨文档一致：spec 字段（`parse_method` / `poll_interval_seconds` / `poll_timeout_seconds`）↔ tasks 描述 ↔ 测试列表 互相对齐
8. ✅ process_tasks 必填：tasks.md 含 P-spec-review / P-code-review / P-test-review / P-ci / P-deploy / P-user-confirm

## 受影响模块

- 新建：`apps/api/dataplat_api/processors/_mineru_client.py`
- 新建：`apps/api/dataplat_api/processors/pdf_mineru.py`
- 新建：`apps/api/tests/test_pdf_mineru.py`
- 改动：`apps/api/dataplat_api/processors/__init__.py`（import + register `PdfMineruProcessor()`）
- 改动：`scripts/_self_check.sh`（追加 `run_processor_pdf_mineru` 13 AC + filter + 总入口）

## 不受影响但易混淆的模块

- `apps/api/dataplat_api/runner/processor_runner.py`：不动；现有 ctx 注入（llm + blob_store）已够；processor 通过 `ctx.blob_store.put` 写 MD。
- `apps/api/dataplat_api/runner/runcontext.py`：不动；不需要新字段，env 读直接在 processor 内做。
- `apps/api/dataplat_api/schemas/process.py`：不动；`ProcessRequest.config` 已是 `dict[str, Any]`，可承载新 spec 字段。
- `apps/api/dataplat_api/routers/process.py`：不动；现有路由对任何已注册 processor 都通。
- `apps/api/dataplat_api/jobs/tasks.py`：不动；`run_process_job` 已按 job_type 派发。
- `packages/core/src/dataplat_core/protocols/processor.py`：不动；Processor Protocol 已足够。
- `apps/api/dataplat_api/adapters/firecrawl_url.py`：不动；只是借鉴其 `_FakeAsyncClient` mock 模式到测试。
- `apps/api/dataplat_api/llm/`：不动；本 change 不消费 ctx.llm。

## 待澄清问题

> stage 2 评审前必须清零，或显式标记 deferred。

- [x] MinerU 集成方式 → HTTP API（用户 stage 0 已选定）
- [x] API 形态 → 异步 job + 轮询（用户 stage 0 已选定）
- [x] endpoint/token 注入方式 → env vars（用户 stage 0 已选定）
- [x] 输出层 → Silver（用户 stage 0 已选定）
- [x] 范围 → Processor 实现 + 单测（用户 stage 0 已选定）
- [ ] **deferred to coding 阶段**：MinerU 实际响应 JSON 字段名（`task_id` / `status` / `markdown`）的确切拼写——本 change 在 `_mineru_client.py` 集中处理，coding 阶段联系真服务确认；若有出入仅改 client 的解析函数，不影响 spec 的 13 AC 结构。

## 引用

- `.harness/design.md` §2.3（Bronze/Silver/Gold 三层）/ §4.2（Processor Protocol）
- `.harness/changes/processor-framework-20260517/`（先例：Processor + Runner + Registry）
- `.harness/changes/llm-qa-gen-20260518/`（先例：processor 调外部异步服务 + ctx.blob_store.put）
- `.harness/changes/adapter-firecrawl-20260517/`（先例：httpx + `_FakeAsyncClient` mock 模式）
- `.harness/skills/request-analysis/SKILL.md` § "硬规则摘要"
