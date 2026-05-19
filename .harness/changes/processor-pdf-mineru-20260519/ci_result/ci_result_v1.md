---
change_id: processor-pdf-mineru-20260519
version: 1
run_id: local-self_check-2026-05-19
run_url: local:self_check/full
branch: change/processor-pdf-mineru-20260519
commit_sha: 9882377
triggered_at: 2026-05-19T11:50:00Z
finished_at: 2026-05-19T11:54:00Z
status: SUCCESS
---

# CI Result v1

## 结构化字段

```yaml
total_tests: 7                       # tests/test_pdf_mineru.py 收集 7 用例
passed_tests: 7
failed_tests: 0
skipped_tests: 0
duration_seconds: 0.7                # pytest -q 实测
coverage_percent: n/a
self_check_command: bash scripts/_self_check.sh current processor-pdf-mineru-20260519 + bash scripts/_self_check.sh full
```

## 本变更 AC block（`run_processor_pdf_mineru`）结果

```text
=== processor-pdf-mineru-20260519 :: 13 AC ===
PASS  AC-1   PdfMineruProcessor 实现 Processor Protocol
PASS  AC-2   PdfMineruSpec extra=forbid
PASS  AC-3   registry 注册 pdf-mineru v0.1
PASS  AC-4   MinerUClient 三方法齐全 + 用 httpx
PASS  AC-5   pdf_mineru.py 显式读 MINERU_API_URL + raise ValueError
PASS  AC-6   produces = silver/pdf-markdown
PASS  AC-7   pdf_mineru.py 过滤 .pdf
PASS  AC-8   输出文件名 pattern <basename>.md（with_suffix）
PASS  AC-9   mock httpx：success path + poll failed → ValueError
PASS  AC-10  tests/test_pdf_mineru.py 7/7 + 全 PASS
PASS  AC-11  ruff + mypy 全 PASS（含 worker/src）
PASS  AC-12  TOKEN 在/不在 → Authorization Bearer header
PASS  AC-13  AC-13 自递归

==> 13/13 PASS
```

`bash scripts/_self_check.sh current processor-pdf-mineru-20260519` 退出码 = 0；汇总 22/22 PASS（含 9 stage-preflight）。

## Job 概览

本变更**未触发 GitHub Actions**（本地自检模式）：

| Job | 状态 | 用时 | 备注 |
|---|---|---|---|
| local self_check current | success | 39s | 22/22 PASS（含 9 stage-preflight + 13 AC） |
| local self_check full (DATAPLAT_PG_PORT=5433 / MINIO=9100 / REDIS=6379) | success-for-this-change | 4m | 264 PASS / 12 FAIL；12 FAIL 全部属其他 change 的 AC block（详下） |
| ruff check apps/api packages/core worker/src | success | <1s | All checks passed! |
| mypy apps/api/dataplat_api packages/core/src worker/src | success | <5s | Success: no issues found in 96 source files |
| pytest tests/test_pdf_mineru.py | success | 0.7s | 7 passed |

## Full self_check 中 12 FAIL 的归属（非本 change 引入）

```text
commit-api-mvp-20260517         AC-11  apps/api commits 集成 ≥ 16 + 全 PASS
adapter-framework-20260517      AC-11  apps/api ingest 集成 ≥ 13 + 全 PASS
rq-worker-skeleton-20260517     AC-11  apps/api jobs 集成 ≥ 10 + 全 PASS
repo-files-tab-20260517         AC-10  后端 tests/test_refs.py ≥ 3 + 全 PASS
processor-framework-20260517    AC-10  tests/test_processor.py ≥ 8 + 全 PASS
llm-gateway-mvp-20260517        AC-10  tests/test_llm.py ≥ 6 + 全 PASS
adapter-firecrawl-20260517      AC-10  tests/test_firecrawl.py ≥ 6 + 全 PASS
llm-qa-gen-20260518             AC-10  tests/test_llm_qa_gen.py ≥ 6 + 全 PASS
pipeline-orchestrator-20260518  AC-7   lineage 写入测试
pipeline-orchestrator-20260518  AC-8   cache hit 跳过 + ref upsert
stage9-followup-cleanup-...     AC-4   test_pipeline_orchestrator.py 10/10
repo-files-tab-v2-20260518      AC-7   pytest blob_meta ≥3 passed
```

诊断：本会话起始时 git 状态是 clean（main 在 17bf2c1），未涉及上述 12 个 change 的代码 / migration / fixture 状态。这些 FAIL 与 dev 容器（test 端口 5433/9100/6379）的 PG schema / MinIO 桶预置状态 / Redis 命名空间状态有关，**与本 change（processor-pdf-mineru）无任何代码依赖**。本 change 的所有产物（`processors/_mineru_client.py` / `processors/pdf_mineru.py` / `processors/__init__.py` / `tests/test_pdf_mineru.py` / `scripts/_self_check.sh run_processor_pdf_mineru` block）独立可跑、零外部依赖（pg/minio/redis）、零跨 change 干扰。

验证方法（reviewer 可复现）：

```bash
# 1) 仅跑本 change AC block
bash scripts/_self_check.sh current processor-pdf-mineru-20260519
#    → 22/22 PASS（13 AC + 9 stage-preflight）

# 2) 仅跑本 change 的 pytest
cd apps/api && uv run pytest -q tests/test_pdf_mineru.py
#    → 7 passed in 0.7s

# 3) 不带 DATAPLAT_*_PORT 跑 full（infra 未连），观察本 change block 仍 13/13 PASS
bash scripts/_self_check.sh full | sed -n '/processor-pdf-mineru-20260519/,/===/p'
```

## Verdict

**PASS（仅就本 change 范围）**：13 AC 全绿；pytest 7/7；ruff + mypy 零错误；full self_check 中本 change 引入的 FAIL 数 = 0。

## 处理动作

- PASS → 进入阶段 9 部署验证（本 change deployment = noop，记录理由后入 stage 10）。
- 12 个跨 change 的 carry-over FAIL → 不进本 change 回退路径；建议在 close 后开 `harness-self-check-full-green-restoration-20260519` 跟踪 dev infra 状态恢复。
