---
change_id: processor-pdf-mineru-20260519
version: 1
authored_at: 2026-05-19T11:10:00Z
status: waiting_review
---

# Test Report v1

## 验收项 ↔ 测试映射

| AC ID | 测试文件 | 测试函数 |
|---|---|---|
| AC-9 (success + poll-failed) | apps/api/tests/test_pdf_mineru.py | test_run_success / test_run_poll_failed_raises |
| AC-10 (≥6 用例 + 全 PASS) | apps/api/tests/test_pdf_mineru.py | 7 个用例全部（test_run_success / test_run_poll_failed_raises / test_run_env_missing_url / test_client_token_header_present / test_client_token_header_absent / test_run_skips_non_pdf / test_run_poll_timeout） |
| AC-12 (token header 在/不在) | apps/api/tests/test_pdf_mineru.py | test_client_token_header_present / test_client_token_header_absent |
| AC-5 (env URL 缺失 → ValueError) | apps/api/tests/test_pdf_mineru.py | test_run_env_missing_url |
| AC-7 (跳过非 PDF) | apps/api/tests/test_pdf_mineru.py | test_run_skips_non_pdf |
| AC-8 (输出 .md 文件名) | apps/api/tests/test_pdf_mineru.py | test_run_success（断言 files[0].path == "sample.md"）+ test_run_skips_non_pdf（断言 "doc.md"） |

## 测试文件清单

| 文件 | 类型 | 用例数 |
|---|---|---|
| apps/api/tests/test_pdf_mineru.py | unit | 7 |

## Mock 范围声明

> 允许 mock：外部 HTTP（mineru API）、时间（poll 间隔通过 spec config 缩到 0.01s）。
> 禁止 mock：Processor / MinerUClient（被测对象本身）。

本轮 mock 了：
- `httpx.AsyncClient` → `_FakeAsyncClient`（按 method+url 路由到预设响应；记录 headers 用于 AC-12 断言）
- BlobStore → `_FakeBlobStore`（直接 hashlib.sha256 算 hash，回填 `BlobPutResult`；不走 MinIO）
- RepoView → `_FakeRepoView`（in-memory dict[path → bytes]，实现 iter_paths / open）
- 时间：test_run_poll_timeout 通过 `poll_interval_seconds=0.01 / poll_timeout_seconds=0.05` 让超时立即触发，不用 sleep mock

**没有 mock**：PdfMineruProcessor 本体、MinerUClient（直接调用其 submit/poll/fetch_markdown，httpx 那层才是 fake）、StandardRunContext、PdfMineruSpec、BlobPutResult。

## 本地运行结果

```text
$ cd apps/api && uv run pytest -q tests/test_pdf_mineru.py
.......                                                                  [100%]
7 passed in 0.70s

$ uv run ruff check apps/api packages/core worker/src
All checks passed!

$ uv run mypy apps/api/dataplat_api packages/core/src worker/src
Success: no issues found in 96 source files
```

## 已知 flaky / 跳过

- 无 skip / xfail / flaky；7/7 必过；testtimeout 是 wallclock-bound（poll_timeout=0.05s），在极端 CI 抖动下理论上可能慢，但 0.05s × 多次 = 仍 < 1s，监控 stage 8 CI 第一次跑结果即可。

## 覆盖率（按需）

未跑 coverage（spec 未要求；processor + client 总计 < 200 行，7 用例覆盖关键路径足够）。

## 偏离 spec / trade-off

- **测试不经 ProcessorRunner / FastAPI / DB / MinIO / Redis**：与 tasks.md T-4 v2 描述一致；behavioral AC 真跑代码，但跑的是 processor.run 直接调用而非端到端 HTTP 流程。这避免了 `run_ac_skipif_no_pg_minio_redis` 把 behavioral AC 静默 SKIP（v1 reviewer MUST FIX-4）。
- **`_patch_httpx` 用 firecrawl 风格替换 httpx 模块引用**（不是 setattr AsyncClient 子属性）：避免污染全局 httpx 模块；与 `tests/test_firecrawl.py` 一致。
- **顺带修了 stage 4 reviewer SHOULD FIX S-1**：pdf_mineru.py 把两次 `asyncio.run` 合并到一个 `_process_one` 协程（与 llm_summarize 模式一致）；不引入新 behavior，仅去除多余 event loop 创建。

## 下一步

进入阶段 6 单测评审：spawn 独立 sonnet reviewer 子 agent，加载 `.harness/skills/expert-reviewer/SKILL.md`，写 `unit_test/review/test_review_v1.md`。
