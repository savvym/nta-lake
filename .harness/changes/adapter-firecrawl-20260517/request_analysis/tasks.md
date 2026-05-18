---
change_id: adapter-firecrawl-20260517
version: 1
authored_at: 2026-05-18T08:15:00Z
---

# Tasks

## T-1 _image_extract.py 工具

- `apps/api/dataplat_api/adapters/_image_extract.py`：`extract_image_urls(content: str, base_url: str) -> list[str]`
  - 用 regex 提取 HTML `<img src="X">` 与 markdown `![alt](X)`
  - `urljoin(base_url, X)` 解析相对路径
  - data: URI 跳过；javascript: 跳过；ftp:// 跳过；只保留 http(s)://
  - 去重保序
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-5

## T-2 FirecrawlURLSpec + FirecrawlURLAdapter

- `apps/api/dataplat_api/adapters/firecrawl_url.py`：
  - `FirecrawlURLSpec(BaseModel, extra=forbid)`：urls / extract_images / llm_model / max_tokens / request_timeout_seconds
  - field_validator urls：list 非空 + 每个 startswith http(s)://
  - `FirecrawlURLAdapter`（SourceAdapter Protocol；name="firecrawl-url" version="0.1" output_subtype="webpage-collection"）
  - `ingest(spec, workspace, ctx)`：parse spec → ctx.llm / ctx.blob_store 取出 → `asyncio.run(_run_all(...))`
  - `_run_all`：共享 httpx.AsyncClient（timeout + UA header）；for idx, url in enumerate(urls): GET → ctx.llm.call(prompt="Convert HTML to clean Markdown:") → blob put → assets/{idx}/content.md；可选 extract_image_urls → 各 image GET → blob put → assets/{idx}/images/{sha[:16]}{ext}（每个 image 失败吞掉不阻塞）
- depends_on: T-1 / estimated_stage: stage-3 / AC: AC-1, AC-2, AC-6, AC-7, AC-8, AC-9, AC-12

## T-3 adapters/__init__.py 注册 + AdapterRunner ctx 扩

- `adapters/__init__.py`：import FirecrawlURLAdapter + register
- `runner/adapter_runner.py`：构 ctx 时 `llm=get_llm_gateway()` + `blob_store=store`
- 反向 grep 自审通过
- depends_on: T-2 / estimated_stage: stage-3 / AC: AC-3, AC-4

## T-4 测试 tests/test_firecrawl.py ≥ 6

- test_a_extract_image_urls_unit
- test_b_adapter_ingest_unit_with_fakes（mock httpx + FakeLLMProvider；单 URL；验 content.md + ≥1 image entry）
- test_c_admin_ingest_returns_queued
- test_d_user_ingest_returns_403
- test_e_end_to_end_succeeded（admin POST → worker → succeeded；下游 commit 含 assets/0/content.md + images）
- test_f_unreachable_url_marks_failed（mock httpx 抛 ConnectError）
- depends_on: T-1, T-2, T-3 / estimated_stage: stage-3 / AC: AC-10

## T-5 lint + type

- `cd apps/api && uv sync --extra dev`（首次跑测试前必做）
- `uv run ruff check apps/api packages/core worker/src` 0 errors
- `uv run mypy apps/api/dataplat_api packages/core/src worker/src` 0 errors
- depends_on: T-1~T-4 / estimated_stage: stage-3 / AC: AC-11

## T-6 self_check adapter-firecrawl block

- `scripts/_self_check.sh` 追加 `run_adapter_firecrawl` 13 AC + filter + 总入口
- AC-10 走 `run_ac_skipif_no_pg_minio_redis`
- depends_on: T-1~T-5 / estimated_stage: stage-3 / AC: AC-13

## process_tasks

## T-7 stage-2 spec/tasks review

- depends_on: T-6 v1 完
- estimated_stage: stage-2

## T-8 stage-4 coding review

- depends_on: T-1~T-5
- estimated_stage: stage-4

## T-9 stage-5/6 test_report + review

- depends_on: T-4
- estimated_stage: stage-6

## T-10 stage-7 CI

- depends_on: T-6, T-9
- estimated_stage: stage-7

## T-11 stage-9 deploy verify

- depends_on: T-10
- estimated_stage: stage-9

## T-12 stage-10 close

- depends_on: T-10, T-11
- estimated_stage: stage-10

## 任务依赖图

```
T-1 (_image_extract) ─┐
                      ├→ T-2 (FirecrawlURLAdapter)
                      │      ↓
                      │   T-3 (register + AdapterRunner ctx 扩)
                      │      ↓
                      └→ T-4 (6 tests)
                            ↓
                         T-5 (lint+type)
                            ↓
                         T-6 (self_check)
                            ↓
                  T-7 → T-8 → T-9 → T-10 → T-11 → T-12
```

## AC 覆盖矩阵

| AC | task |
|---|---|
| AC-1 | T-2 |
| AC-2 | T-2 |
| AC-3 | T-3 |
| AC-4 | T-3 |
| AC-5 | T-1 |
| AC-6 | T-2 |
| AC-7 | T-2 |
| AC-8 | T-2 |
| AC-9 | T-2 |
| AC-10 | T-4 |
| AC-11 | T-5 |
| AC-12 | T-2 |
| AC-13 | T-6 |
