---
change_id: processor-framework-20260517
version: 1
authored_at: 2026-05-17T18:00:00Z
status: draft
---

# Spec：Processor 框架 + markdown-normalize + POST /process

## 范围

In scope：
- `runner/repo_view.py` DbRepoView（实现 RepoView Protocol）
- `runner/processor_registry.py` ProcessorRegistry + get_processor_registry 单例
- `runner/processor_runner.py` ProcessorRunner.run async
- `processors/__init__.py` + `markdown_normalize.py`（normalize CRLF + trailing ws）
- StandardRunContext 加 blob_store 字段
- `schemas/process.py` ProcessRequest + Response
- `routers/process.py` POST /process（admin）
- `jobs/tasks.py` 加 run_process_job + JobsService.enqueue 按 job_type 派发
- ≥ 8 集成测试
- self_check 13 AC

Out of scope：Schema Registry / iter_records / parallel map / subprocess / web UI / 真 PDF/HTML processor

## 验收标准（13 AC）

- AC-1：DbRepoView 存在；验证 `grep -q "class DbRepoView" apps/api/dataplat_api/runner/repo_view.py`
- AC-2：ProcessorRegistry 单例 + markdown-normalize 注册；`cd apps/api && uv run python -c "import dataplat_api.processors; from dataplat_api.runner.processor_registry import get_processor_registry; assert get_processor_registry().get('markdown-normalize','0.1') is not None"`
- AC-3：ProcessorRunner.run 是 coroutine；`cd apps/api && uv run python -c "from dataplat_api.runner.processor_runner import ProcessorRunner; import inspect; assert inspect.iscoroutinefunction(ProcessorRunner.run)"`
- AC-4：MarkdownNormalizeProcessor 实现 Processor Protocol；`cd apps/api && uv run python -c "from dataplat_core.protocols.processor import Processor; from dataplat_api.processors.markdown_normalize import MarkdownNormalizeProcessor; assert isinstance(MarkdownNormalizeProcessor(), Processor)"`
- AC-5：ProcessRequest extra=forbid；`cd apps/api && uv run python -c "from dataplat_api.schemas.process import ProcessRequest; assert ProcessRequest.model_config.get('extra')=='forbid'"`
- AC-6：POST /process 路由 + main include + OpenAPI；`cd apps/api && uv run python -c "from dataplat_api.main import app; s=app.openapi(); assert '/process' in s['paths']"`
- AC-7：run_process_job 签名含 job_id；`cd apps/api && uv run python -c "from dataplat_api.jobs.tasks import run_process_job; import inspect; assert 'job_id' in inspect.signature(run_process_job).parameters"`
- AC-8：JobsService.enqueue 接 job_type 按值 dispatch；`grep -qE "run_process_job|run_ingest_job" apps/api/dataplat_api/jobs/service.py`
- AC-9：StandardRunContext 含 blob_store 字段；`cd apps/api && uv run python -c "from dataplat_api.runner.runcontext import StandardRunContext; import dataclasses; assert 'blob_store' in {f.name for f in dataclasses.fields(StandardRunContext)}"`
- AC-10：tests/test_processor.py ≥ 8；`[ "$(cd apps/api && uv run pytest --collect-only -q tests/test_processor.py 2>&1 | grep -cE 'test_processor\.py::')" -ge 8 ]`
- AC-11：ruff + mypy；`uv run ruff check apps/api packages/core worker/src && uv run mypy apps/api/dataplat_api packages/core/src worker/src`
- AC-12：openapi.json 含 /process；`grep -q "/process" packages/api-types/openapi.json`
- AC-13：self_check 自递归

## 风险与缓解

1. worker 进程要 import processors 触发 register（沿 adapter 模式修复）
2. CAS dedup 自然保证幂等
3. cycle detection 留 follow-up（MVP 接受 source==target）
4. SKILL 8 条 checklist 第六次回归
