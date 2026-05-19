---
change_id: processor-pdf-mineru-20260519
version: 2
authored_at: 2026-05-19T09:10:00Z
revised_at: 2026-05-19T09:55:00Z
revision_notes: |
  v2 修复 stage 2 reviewer v1 报出的 MUST FIX 2/4：
  - MUST FIX-2：T-2 描述补 `config_schema: dict[str, Any]` 必备字段（Processor
    Protocol runtime_checkable 检查依赖；缺则 AC-1 isinstance 失败）
  - MUST FIX-4：T-5 描述删除 `run_ac_skipif_no_pg_minio_redis`；测试是 pure
    unit（FakeRepoView + FakeBlobStore + monkeypatch httpx），不需要 pg/minio/redis；
    强制 SKIP 会让 behavioral AC 形同虚设。改为无条件 `run_ac`。同步把 T-4 测试
    设计改为直接构 view + ctx，不经 ProcessorRunner / DB / MinIO。
---

# Tasks

> 任务粒度 1-3 小时。每个任务都要标明 `depends_on` 与 `estimated_stage`。

## 任务清单

```yaml
tasks:
  - id: T-1
    title: 实现 _mineru_client.MinerUClient（submit / poll / fetch_markdown，httpx.AsyncClient）
    description: |
      apps/api/dataplat_api/processors/_mineru_client.py。
      构造接受 base_url + 可选 token + timeout；私有 _headers() 在有 token 时注入 Bearer。
      submit(pdf_bytes, filename, parse_method) → task_id（POST <base>/tasks，multipart）。
      poll(task_id) → dict{status, markdown?}（GET <base>/tasks/{id}），解析 status / markdown 字段集中处理。
      fetch_markdown(task_id, poll_interval, poll_timeout) → str：循环 poll 直到 succeeded/failed/超时；失败/超时 raise ValueError；成功返 markdown 文本。
      非 200 响应 raise ValueError 并带 status+url。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-4, AC-12]
    status: pending
    commits: []

  - id: T-2
    title: 实现 PdfMineruSpec + PdfMineruProcessor 主体
    description: |
      apps/api/dataplat_api/processors/pdf_mineru.py。
      PdfMineruSpec：BaseModel + ConfigDict(extra="forbid")，字段：parse_method:str="auto" / poll_interval_seconds:float=5.0 / poll_timeout_seconds:float=600.0。
      _PDF_SUFFIXES = (".pdf",)。
      PdfMineruProcessor 五项 Processor Protocol 必备数据属性 + run（缺一则 AC-1
      runtime_checkable isinstance 失败）：
        - name: str = "pdf-mineru"
        - version: str = "0.1"
        - config_schema: dict[str, Any] = {"type":"object","additionalProperties":False,
            "properties":{"parse_method":{"type":"string"},
                          "poll_interval_seconds":{"type":"number"},
                          "poll_timeout_seconds":{"type":"number"}}}
        - accepts: list[RepoSelector] = [RepoSelector()]
        - produces: RepoSpec = RepoSpec(layer="silver", subtype="pdf-markdown")
      run(inputs, config, workspace, ctx)：
        - 校验 inputs / ctx.blob_store 非空；
        - 读 env MINERU_API_URL（空 → ValueError），可选 MINERU_API_TOKEN；
        - PdfMineruSpec.model_validate(config) 解析配置；
        - iter_paths 过滤 .pdf（大小写不敏感）；空集合 → ValueError；
        - 串行：每个 PDF 调 client.fetch_markdown → blob_store.put → IngestFileRef(path=basename.md, sha256, ...)；
        - 输出 path 用 `Path(path).with_suffix(".md")`（满足 AC-8 `with_suffix` grep）；
        - 返 ProcessResult(file_count=len(md_files), bytes_written=sum, notes="...", files=[...])。
      使用 asyncio.run(_do()) 与 llm-summarize/markdown-normalize 对齐。
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-1, AC-2, AC-5, AC-6, AC-7, AC-8]
    status: pending
    commits: []

  - id: T-3
    title: 注册到 processors/__init__.py
    description: |
      apps/api/dataplat_api/processors/__init__.py 加：
        from dataplat_api.processors.pdf_mineru import PdfMineruProcessor
        _registry.register(PdfMineruProcessor())
      __all__ 加 "PdfMineruProcessor"。
    depends_on: [T-2]
    estimated_stage: coding
    covers_ac: [AC-3]
    status: pending
    commits: []

  - id: T-4
    title: 写 tests/test_pdf_mineru.py（≥ 6 个测试，纯 unit，无 pg/minio/redis）
    description: |
      apps/api/tests/test_pdf_mineru.py。**测试是纯 unit**：直接 new 一个
      `PdfMineruProcessor()` 并调 `.run([fake_view], config, workspace, fake_ctx)`，
      不经过 ProcessorRunner / FastAPI / 数据库 / MinIO / Redis。Fixture 构造：
        - FakeRepoView：实现 `iter_paths()` + `open(path)`（返 io.BytesIO），覆盖 RepoView Protocol 所需面；
        - FakeBlobStore：实现 `async def put(stream, declared_size) -> obj.sha256/.size`（用 hashlib.sha256 算真实 hash + 计数 size）；
        - fake_ctx：`StandardRunContext(logger=..., blob_store=FakeBlobStore(), llm=None)`；
        - monkeypatch.setattr("httpx.AsyncClient", _FakeAsyncClient)，FakeClient 实现 __aenter__/__aexit__/post/get；
          FakeResponse 实现 .status_code / .json() / .text / .raise_for_status()。
      测试至少 6 个：
        1) test_run_success：env 设好 + FakeRepoView 含 1 PDF → processor.run 返 ProcessResult，files 中含 `<basename>.md`，FakeBlobStore 收到对应 MD bytes；
        2) test_run_poll_failed_raises：FakeClient poll 返 {status:"failed"} → run 抛 ValueError；
        3) test_run_env_missing_url：monkeypatch.delenv("MINERU_API_URL", raising=False) → run 抛 ValueError；
        4) test_client_token_header_present：set MINERU_API_TOKEN → FakeClient.submit 收到的请求头含 Authorization: Bearer <token>；
        5) test_client_token_header_absent：unset MINERU_API_TOKEN → FakeClient.submit 收到的请求头无 Authorization；
        6) test_run_skips_non_pdf：FakeRepoView 含 .txt + .pdf → 产出 ProcessResult.files 仅含 1 个 .md，非 PDF 不进 tree。
      （可选 7）test_poll_timeout：FakeClient 永远返 running + 极小 poll_timeout_seconds → run 抛 ValueError。
    depends_on: [T-2, T-3]
    estimated_stage: unit_test
    covers_ac: [AC-9, AC-10, AC-12]
    status: pending
    commits: []

  - id: T-5
    title: 追加 scripts/_self_check.sh AC block
    description: |
      在 run_llm_qa_gen 后插入 run_processor_pdf_mineru 函数（13 AC，按 spec.md 表中命令逐条 run_ac）。
      **AC-10 一律用 run_ac（不是 run_ac_skipif_no_pg_minio_redis）**——测试是纯
      unit，不依赖 pg/minio/redis，若 SKIP 会让 behavioral AC 形同虚设（reviewer
      v1 MUST FIX-4）。AC-10 命令按 spec.md § "AC-10 完整验证命令" fenced block
      原样落地，管道符 `|` 不要加反斜杠转义。
      在「按 filter 执行」main case 列表与「跑全部」入口列表都加上 run_processor_pdf_mineru。
    depends_on: [T-4]
    estimated_stage: ci_result
    covers_ac: [AC-11, AC-13]
    status: pending
    commits: []

  - id: T-6
    title: 本地 lint + 单测 + self_check current 全绿
    description: |
      cd apps/api && uv run ruff check . && uv run mypy dataplat_api（必要时拓到 packages/core 与 worker/src）；
      cd apps/api && uv run pytest -q tests/test_pdf_mineru.py；
      bash scripts/_self_check.sh current processor-pdf-mineru-20260519。
      失败按 development-process.md Rollback Route 回退。
    depends_on: [T-5]
    estimated_stage: ci_result
    covers_ac: [AC-9, AC-10, AC-11, AC-12, AC-13]
    status: pending
    commits: []
```

## 阶段任务（必备占位，不要漏）

```yaml
process_tasks:
  - id: P-spec-review
    estimated_stage: request_analysis_review
    status: pending

  - id: P-code-review
    estimated_stage: coding_review
    status: pending

  - id: P-test-review
    estimated_stage: unit_test_review
    status: pending

  - id: P-push
    estimated_stage: stage-7
    status: pending

  - id: P-ci
    estimated_stage: ci_result
    status: pending

  - id: P-deploy
    estimated_stage: deployment       # 本 change 仅落 processor + 单测，不动部署面；stage 9 走 noop 并在 deployment/ 记录
    status: pending

  - id: P-user-confirm
    estimated_stage: user_confirmation
    status: pending
```

## DAG 健全性

依赖链：T-1 → T-2 → T-3 → T-4 → T-5 → T-6。无环。

## 验收覆盖矩阵

| AC | 关联任务 |
|---|---|
| AC-1 | T-2 |
| AC-2 | T-2 |
| AC-3 | T-3 |
| AC-4 | T-1 |
| AC-5 | T-2 |
| AC-6 | T-2 |
| AC-7 | T-2 |
| AC-8 | T-2 |
| AC-9 | T-4 |
| AC-10 | T-4 |
| AC-11 | T-5, T-6 |
| AC-12 | T-1, T-4 |
| AC-13 | T-5 |

每条 AC 至少有一个非 process_tasks 任务覆盖（已核对）。
