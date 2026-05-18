---
change_id: sdk-cli-mvp-20260518
version: 1
authored_at: 2026-05-18T11:05:00Z
---

# Tasks

## T-1 packages/sdk-py/pyproject.toml + __init__.py 改造

- 加 deps：`httpx>=0.27`（已有）+ `typer>=0.12`
- 加 `[project.optional-dependencies] dev = ["pytest>=8.0", "pytest-asyncio>=0.23"]`
- 加 `[project.scripts] dataplat = "dataplat_sdk.cli:app"`
- `__init__.py` export Client + __version__
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-8

## T-2 src/dataplat_sdk/client.py 实现 8 个方法

- `Client(base_url, token=None, timeout=30.0)`：内部 `_http: httpx.Client(base_url=base_url, cookies=httpx.Cookies(), timeout=timeout)`
- `login(username, password) -> None`：POST /auth/login；cookie 自动持久
- `create_repo(owner, name, layer="bronze", subtype="pdf", visibility="public") -> dict`：POST /repos
- `get_repo(owner, name) -> dict`：GET /repos/{owner}/{name}
- `upload_blob(owner, name, content: bytes) -> str`：POST /repos/{}/{}/blobs；返 sha256
- `create_commit(owner, name, entries, parents=None, author_id, message=None, ref=None) -> dict`
- `enqueue_ingest(owner, name, adapter_name, adapter_version, spec, author_id, ref=None) -> str`
- `enqueue_process(source_owner, source_name, source_ref, target_owner, target_name, processor_name, processor_version, config, author_id, ref=None) -> str`
- `get_job(job_id) -> dict`
- `close()`：关闭 _http
- depends_on: T-1 / estimated_stage: stage-3 / AC: AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-12

## T-3 src/dataplat_sdk/cli.py 实现 Typer app

- `app = typer.Typer(name="dataplat", help="dataplat CLI")`
- 全局参数：`--url` (env DATAPLAT_URL) / `--token` (env DATAPLAT_TOKEN)
- 子 Typer：`repo_app` / `blob_app` / `commit_app` / `jobs_app` / `ingest`（直接 cmd） / `process`（直接 cmd） / `login`（直接 cmd）
- 每个子命令构造 Client + 调对应方法 + json.dumps 输出
- 子命令清单：`login` / `repo create|get` / `blob upload` / `commit create` / `ingest` / `process` / `jobs get`
- depends_on: T-2 / estimated_stage: stage-3 / AC: AC-7, AC-9

## T-4 tests/test_sdk_client.py（3 测试，用 ASGITransport）

- 用 `httpx.ASGITransport(app=fastapi_app)` 把 Client._http 替换为打 FastAPI 的 mock；不开真 HTTP
- test_a_client_login_persists_cookie：login 后 cookies 含 access_token
- test_b_client_create_and_get_repo：create_repo 201 + get_repo 200 返同 owner/name
- test_c_client_upload_blob_returns_sha：bytes content → sha 64 hex
- depends_on: T-2 / estimated_stage: stage-3 / AC: AC-10（部分）

## T-5 tests/test_sdk_cli.py（3 测试，用 CliRunner）

- 用 `typer.testing.CliRunner` 调 `app`；monkeypatch `dataplat_sdk.cli.Client` 类替换为 fake
- test_d_cli_help_lists_subcommands：`dataplat --help` 输出含 login/repo/blob/commit/ingest/process/jobs
- test_e_cli_login_calls_client_login：monkeypatch Client；assert client.login 被调
- test_f_cli_repo_create_outputs_json：monkeypatch Client；assert stdout json 含 owner/name
- depends_on: T-3 / estimated_stage: stage-3 / AC: AC-10（部分）

## T-6 lint + type

- `cd packages/sdk-py && uv sync --extra dev`（SKILL #10 候选第 4 次累积；预防 venv 漂移）
- `uv run ruff check packages/sdk-py` 0 errors
- `uv run mypy packages/sdk-py/src` 0 errors
- depends_on: T-1~T-5 / estimated_stage: stage-3 / AC: AC-11

## T-7 self_check sdk-cli-mvp block

- `scripts/_self_check.sh` 追加 `run_sdk_cli_mvp` 13 AC + filter + 总入口
- AC-10 不需 PG/MinIO/Redis（ASGITransport + CliRunner 都在内存）
- depends_on: T-1~T-6 / estimated_stage: stage-3 / AC: AC-13

## process_tasks

- T-8 stage-2 spec/tasks review
- T-9 stage-4 coding review
- T-10 stage-5/6 test_report + review
- T-11 stage-7 CI
- T-12 stage-9 deploy verify
- T-13 stage-10 close

## 任务依赖图

```
T-1 (pyproject + __init__) → T-2 (client.py)
                                ├→ T-3 (cli.py)
                                ├→ T-4 (test_sdk_client.py)
                                └→ T-5 (test_sdk_cli.py)
                                       ↓
                                    T-6 (lint+type)
                                       ↓
                                    T-7 (self_check)
                                       ↓
                          T-8 → T-9 → T-10 → T-11 → T-12 → T-13
```

## AC 覆盖矩阵

| AC | task |
|---|---|
| AC-1 | T-2 |
| AC-2 | T-2 |
| AC-3 | T-2 |
| AC-4 | T-2 |
| AC-5 | T-2 |
| AC-6 | T-2 |
| AC-7 | T-3 |
| AC-8 | T-1 |
| AC-9 | T-3 |
| AC-10 | T-4 + T-5 |
| AC-11 | T-6 |
| AC-12 | T-2 |
| AC-13 | T-7 |
