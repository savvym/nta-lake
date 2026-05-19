---
change_id: processor-pdf-mineru-live-fix-20260519
version: 1
authored_at: 2026-05-19T12:30:00Z
---

# Tasks

```yaml
tasks:
  - id: T-1
    title: _mineru_client.py 适配真实 MinerU API
    description: |
      改动点（按 AC 编号）：
      - AC-1 _headers() 返回 {"X-API-Key": self._token}；删 Authorization Bearer
      - AC-2 submit 用 list 形式 multipart：`files=[("files", (filename, pdf_bytes, "application/pdf"))]`
      - AC-3 submit 接受 `if resp.status_code not in (200, 202): raise ...`
      - AC-4 拆 fetch_markdown：
          poll 内循环到 status ∈ TERMINAL_OK/FAIL；
          succeeded → 调 fetch_result(task_id) 拿 markdown；
          failed/超时 → ValueError；
        新增 fetch_result(task_id) -> str：
          GET <base>/tasks/{id}/result；非 200 → ValueError；
          响应 JSON 多 layout fallback：顶层 "markdown" / "md_content" / "results"[0]["markdown"]；
          全失败 → ValueError 列出 keys
      - AC-5 submit 签名增 `backend: str = "hybrid-auto-engine"` 参数；data 字典里加 backend
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1, AC-2, AC-3, AC-4, AC-5]
    status: pending

  - id: T-2
    title: pdf_mineru.py PdfMineruSpec 加 backend 字段 + run 透传
    description: |
      PdfMineruSpec 新增 `backend: str = "hybrid-auto-engine"`（forbid 不变；显式 default）。
      _CONFIG_SCHEMA properties 加 backend。
      run() 调 client.submit 时传 spec.backend。
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-5]
    status: pending

  - id: T-3
    title: tests/test_pdf_mineru.py 同步新协议
    description: |
      _FakeAsyncClient：
        post 路由：URL = base/tasks → 返 status_code=202 + payload {"task_id":"task-xyz"}；
        get 路由：base/tasks/{id} → 状态 payload；base/tasks/{id}/result → markdown payload；
        get/post 都记录 headers，断言 X-API-Key 而非 Authorization。
      用例改造：
        - test_run_success：检查 X-API-Key + 202 + /result fetch 路径
        - test_run_poll_failed_raises：status=failed 时 ValueError（fetch_result 不被调）
        - test_run_env_missing_url：保持
        - test_client_x_api_key_present：替换原 test_client_token_header_present，断言 X-API-Key
        - test_client_token_absent：保持但断言无 X-API-Key
        - test_run_skips_non_pdf：保持
        - test_run_poll_timeout：保持
      ≥ 7 用例。
    depends_on: [T-2]
    estimated_stage: unit_test
    covers_ac: [AC-6]
    status: pending

  - id: T-4
    title: scripts/_self_check.sh 追加 run_processor_pdf_mineru_live_fix
    description: |
      在 run_processor_pdf_mineru 后插入 run_processor_pdf_mineru_live_fix（9 AC）。
      AC-8 复用 `bash scripts/_self_check.sh current processor-pdf-mineru-20260519` 拼 grep
      （回归校验：不能让本 change 改坏上游 AC block；命令以 exit code 为准）。
      在 filter case + 跑全部入口列表都加上。
    depends_on: [T-3]
    estimated_stage: ci_result
    covers_ac: [AC-9, AC-7, AC-8]
    status: pending

  - id: T-5
    title: 本地 ruff/mypy/pytest + self_check current 双 change 全绿
    description: |
      uv run ruff check apps/api packages/core worker/src
      uv run mypy apps/api/dataplat_api packages/core/src worker/src
      cd apps/api && uv run pytest -q tests/test_pdf_mineru.py
      bash scripts/_self_check.sh current processor-pdf-mineru-live-fix-20260519
      bash scripts/_self_check.sh current processor-pdf-mineru-20260519
    depends_on: [T-4]
    estimated_stage: ci_result
    covers_ac: [AC-6, AC-7, AC-8]
    status: pending
```

## 阶段任务

```yaml
process_tasks:
  - id: P-spec-review
    estimated_stage: request_analysis_review
    status: deferred       # 会话级授权偏离 #1（用户授权 "一气呵成"）；self-attest
  - id: P-code-review
    estimated_stage: coding_review
    status: deferred       # 同上
  - id: P-test-review
    estimated_stage: unit_test_review
    status: deferred       # 同上
  - id: P-push
    estimated_stage: stage-7
    status: pending
  - id: P-ci
    estimated_stage: ci_result
    status: pending
  - id: P-deploy
    estimated_stage: deployment
    status: pending        # noop（理由同上游 change）
  - id: P-user-confirm
    estimated_stage: user_confirmation
    status: pending
```

## DAG

T-1 → T-2 → T-3 → T-4 → T-5（无环）

## 验收覆盖

| AC | 任务 |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-1 |
| AC-3 | T-1 |
| AC-4 | T-1 |
| AC-5 | T-1, T-2 |
| AC-6 | T-3, T-5 |
| AC-7 | T-5 |
| AC-8 | T-4, T-5 |
| AC-9 | T-4 |
