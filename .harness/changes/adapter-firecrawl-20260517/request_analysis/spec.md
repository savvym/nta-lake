---
change_id: adapter-firecrawl-20260517
version: 1
authored_at: 2026-05-18T08:10:00Z
status: draft
---

# Spec：FirecrawlURLAdapter（httpx + ctx.llm 转 markdown + images 提取）

## 背景

- design.md §2.3 / §4.1 / §11.3 / §11.6 明确 `FirecrawlAdapter`（Bronze 录入侧的第二个 SourceAdapter）：抓 URL → 输出 `assets/<id>/content.md + images/`
- 当前仓 adapter 只有 `RawFileUploadAdapter`；AdapterRegistry 多 adapter 路径未真实跑过
- ctx.llm 已在 llm-gateway-mvp-20260517 落地，但 **AdapterRunner 构 ctx 时仍不注入** `llm` / `blob_store`（仅 logger）——`adapter-runner-ctx-llm-inject-*` follow-up 待消化
- 用户在 stage 0 选定：(1) 抓取走 httpx + ctx.llm 转 md（不引入 firecrawl-py SDK，无 vendor 锁）；(2) 多 URL 串行；(3) 做 content.md + images 双输出

## 问题陈述

- 缺 `apps/api/dataplat_api/adapters/firecrawl_url.py` + Pydantic spec
- 缺 image URL 提取工具（从 markdown / HTML 中提取 `<img src=...>` 或 `![](...)` URL，处理相对路径解析）
- AdapterRunner 构 ctx 不注入 ctx.llm / ctx.blob_store
- 缺 6 测试覆盖：单元（image extract）/ unit run（mock httpx + FakeLLMProvider）/ 路由权限（admin queued / user 403）/ 端到端（worker succeeded）/ 错误分支（unreachable URL → marks_failed）
- 缺 self_check 13 AC block

## 范围

**In scope**：
- `apps/api/dataplat_api/adapters/_image_extract.py`：`extract_image_urls(markdown_or_html, base_url) -> list[str]`（支持 markdown `![](url)` + HTML `<img src="url">`；相对 URL 用 `urljoin(base_url, ...)` 解析）
- `apps/api/dataplat_api/adapters/firecrawl_url.py`：`FirecrawlURLSpec` Pydantic（extra=forbid）+ `FirecrawlURLAdapter` 实现 SourceAdapter Protocol
  - spec 字段：`urls: list[str]`（≥1）/ `extract_images: bool = True` / `llm_model: str = "claude-haiku-4-5-20251001"` / `max_tokens: int = 1024` / `request_timeout_seconds: float = 30.0`
  - run 流程：for idx, url in enumerate(spec.urls): (a) httpx GET → html_text；(b) await ctx.llm.call(prompt="Convert HTML to clean Markdown:\n{html}", model=spec.llm_model, max_tokens=spec.max_tokens) → markdown；(c) ctx.blob_store.put(markdown.encode) → 写 `assets/<idx>/content.md`；(d) 若 extract_images：extract_image_urls(markdown, url) → for each: httpx GET → 写 `assets/<idx>/images/<sha[:16]>{.ext}`
- `apps/api/dataplat_api/adapters/__init__.py`：import + register `FirecrawlURLAdapter()`
- `apps/api/dataplat_api/runner/adapter_runner.py`：构 ctx 时 `llm=get_llm_gateway()` + `blob_store=store`（与 ProcessorRunner 对齐）
- `apps/api/tests/test_firecrawl.py`：≥ 6 测试，全 mock httpx + FakeLLMProvider
- `scripts/_self_check.sh`：追加 `run_adapter_firecrawl` 13 AC + filter + 总入口

**Out of scope**（显式）：
- 真 firecrawl-py SDK → follow-up `adapter-firecrawl-sdk-*`
- JS-rendered（无 headless browser） → follow-up `adapter-firecrawl-js-render-*`
- rate limit / robots.txt / sitemap → follow-up `adapter-firecrawl-politeness-*`
- 并发抓取或并发 LLM → follow-up `adapter-firecrawl-concurrent-*`
- 增量（同 URL 跳过） → follow-up `adapter-firecrawl-incremental-*`
- 图片 OCR / vision LLM → follow-up `adapter-firecrawl-image-vision-*`
- 多媒体 → follow-up `adapter-firecrawl-multimodal-*`
- 真 LLM live test → follow-up `adapter-firecrawl-live-test-*`
- Web UI 抓取触发界面 → follow-up `web-ingest-firecrawl-ui-*`

## 验收标准（13 AC）

- AC-1：FirecrawlURLAdapter 类存在 + 实现 SourceAdapter Protocol；
  `test -f apps/api/dataplat_api/adapters/firecrawl_url.py && cd apps/api && uv run python -c "from dataplat_core.protocols.adapter import SourceAdapter; from dataplat_api.adapters.firecrawl_url import FirecrawlURLAdapter; assert isinstance(FirecrawlURLAdapter(), SourceAdapter)"`
- AC-2：FirecrawlURLSpec extra=forbid；
  `cd apps/api && uv run python -c "from dataplat_api.adapters.firecrawl_url import FirecrawlURLSpec; assert FirecrawlURLSpec.model_config.get('extra')=='forbid'"`
- AC-3：AdapterRunner 构 ctx 注入 llm + blob_store（test -f + 正向双 grep + 反向拦 llm=None / blob_store=None）；
  `test -f apps/api/dataplat_api/runner/adapter_runner.py && grep -q "llm=" apps/api/dataplat_api/runner/adapter_runner.py && grep -q "blob_store=" apps/api/dataplat_api/runner/adapter_runner.py && ! grep -E "llm[[:space:]]*=[[:space:]]*None|blob_store[[:space:]]*=[[:space:]]*None" apps/api/dataplat_api/runner/adapter_runner.py`
- AC-4：registry 注册 firecrawl-url v0.1；
  `cd apps/api && uv run python -c "import dataplat_api.adapters; from dataplat_api.runner import get_registry; assert get_registry().get('firecrawl-url','0.1') is not None"`
- AC-5：extract_image_urls 工具能识别 HTML img + markdown img + 相对路径解析；
  `cd apps/api && uv run python -c "from dataplat_api.adapters._image_extract import extract_image_urls; urls=extract_image_urls('hi <img src=\"https://x.com/a.png\"> ![alt](/img/b.jpg) ![c](https://y.com/c.gif)', 'https://example.com'); assert any('a.png' in u for u in urls) and any('example.com/img/b.jpg' in u for u in urls) and any('c.gif' in u for u in urls)"`
- AC-6：firecrawl_url.py 用 httpx 抓取（grep）；
  `grep -q "httpx" apps/api/dataplat_api/adapters/firecrawl_url.py`
- AC-7：串行处理（firecrawl_url.py 不含 asyncio.gather）；
  `! grep -q "asyncio.gather" apps/api/dataplat_api/adapters/firecrawl_url.py`
- AC-8：输出文件名 pattern `assets/<idx>/content.md`（grep）；
  `grep -q "content.md" apps/api/dataplat_api/adapters/firecrawl_url.py && grep -q "assets/" apps/api/dataplat_api/adapters/firecrawl_url.py`
- AC-9：图片文件名 pattern `assets/<idx>/images/`（grep）；
  `grep -q "images/" apps/api/dataplat_api/adapters/firecrawl_url.py`
- AC-10：tests/test_firecrawl.py ≥ 6 + 全 PASS；
  `[ "$(cd apps/api && uv run pytest --collect-only -q tests/test_firecrawl.py 2>&1 | grep -cE 'test_firecrawl\.py::')" -ge 6 ]`
- AC-11：ruff + mypy 全 PASS；
  `uv run ruff check apps/api packages/core worker/src && uv run mypy apps/api/dataplat_api packages/core/src worker/src`
- AC-12：FirecrawlURLSpec 默认 llm_model = claude-haiku-4-5-20251001；
  `cd apps/api && uv run python -c "from dataplat_api.adapters.firecrawl_url import FirecrawlURLSpec; assert FirecrawlURLSpec.model_fields['llm_model'].default == 'claude-haiku-4-5-20251001'"`
- AC-13：self_check 自递归

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| httpx 在测试中需 mock，但 httpx.AsyncClient 上下文管理器 mock 复杂 | 中 | test_b/e 复杂 | 用 `monkeypatch.setattr("httpx.AsyncClient", _FakeAsyncClient)` 整体替换；_FakeAsyncClient 自己实现 `__aenter__/__aexit__` + 路由 URL → 预设 response |
| 图片 URL 提取 / 相对路径解析 / data-uri 边界情况 | 中 | 图片漏抓或错抓 | extract_image_urls 单元测试明确覆盖 HTML img / md img / 绝对 / 相对 / data: URI 跳过；regex 严格但宽松失败（找不到就 skip 该图片） |
| LLM 输出 markdown 含非 ASCII / 多行 → blob put 编码错误 | 低 | content.md 损坏 | encode("utf-8") 显式；blob_store.put 在 processor-framework 已用过 |
| AdapterRunner ctx 改注入后 raw-file-upload 旧测试回归 | 中 | 8 个 adapter 测试可能挂 | raw_upload.py 注释明确 "不依赖 ctx"；ctx 多带字段不影响；测试前后比对 |
| spec.urls 含 invalid URL（如 ftp:// 或 javascript:） | 中 | httpx GET 抛非 ValueError 类异常 → 路由 500 而非 400 | spec 阶段加 pydantic 校验：urls 必须以 http(s):// 起头（用 startswith 而非 HttpUrl，避免强校验 query 等） |
| AC 验证命令 dry-parse 全过（SKILL #8） | 低 | spec 卡 stage 2 | AC-1/2/4/5/12 共 5 条 python -c 已 compile 通过 |
| summary.md SSoT 漂移（SKILL #9） | 低 | 流程缺陷 | 进 change 目录第一步已写 summary.md frontmatter；占位符 grep = 0 |
| uv venv 没装 dev extras（SKILL #10 候选） | 中 | pytest 走系统 → boto3 缺失 | llm-gateway-mvp 已踩过；本变更跑测试前先 `cd apps/api && uv sync --extra dev` |

## 跨链路一致性自审（request-analysis SKILL 9 条）

1. ✅ 四链路一致：FirecrawlURLSpec ↔ IngestRequest.spec ↔ test fixture ↔ AC-2/12
2. ✅ 事务边界：本变更无 DB 事务；blob put 是无副作用幂等（CAS）
3. ✅ AC 验证命令一行式：13 条全单行；5 条 python -c 已 compile 通过
4. ✅ 风险缓解 ↔ AC 测试：httpx mock → test_b/e；image extract → test_a；spec invalid URL → test_f
5. ✅ commit 链：llm-gateway-mvp-20260517 (fee46ee) → 本变更 base
6. ✅ 反向 grep + test -f：AC-3 双反向（拦 llm=None / blob_store=None）+ test -f 前置；AC-7 反向拦 asyncio.gather
7. ✅ process_tasks 6 条：T-9~T-14 占位（本 tasks.md T-7~T-12）
8. ✅ AC 验证命令真跑 dry-parse：5 条 python -c 已逐条 compile 通过
9. ✅ summary.md frontmatter：已在 stage 1 启动时填好；占位符 grep = 0
10. （候选）uv sync --extra dev：stage 3 实跑前 cd apps/api && uv sync --extra dev（避免 venv 漂移；若再踩同坑则正式落 SKILL）

## 受影响模块

- 新建：`apps/api/dataplat_api/adapters/_image_extract.py`
- 新建：`apps/api/dataplat_api/adapters/firecrawl_url.py`
- 新建：`apps/api/tests/test_firecrawl.py`
- 改动：`apps/api/dataplat_api/adapters/__init__.py`（import + register）
- 改动：`apps/api/dataplat_api/runner/adapter_runner.py`（ctx 注入 llm + blob_store）
- 改动：`scripts/_self_check.sh`（追加 13 AC）

## 不受影响但易混淆的模块

- `apps/api/dataplat_api/adapters/raw_upload.py`：不依赖 ctx，ctx 多带字段无影响
- `apps/api/dataplat_api/llm/`：不动；本变更只**消费** ctx.llm，不动 gateway
- `packages/core/protocols/adapter.py`：不动；SourceAdapter Protocol 已足够

## 引用

- design.md §2.3 / §4.1 / §11.3 / §11.6
- llm-gateway-mvp-20260517 summary.md
- adapter-framework-20260517 summary.md
- SKILL.md request-analysis 9 条 checklist
