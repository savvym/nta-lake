---
change_id: sdk-cli-mvp-20260518
version: 1
authored_at: 2026-05-18T11:00:00Z
status: draft
---

# Spec：Python SDK Client (sync) + CLI (Typer) MVP

## 背景

- design.md §7.2 / §7.3 + §11.6 Phase 1 MVP 最后一项："Python SDK 基本命令 + CLI 基本命令"
- 之前 14 个 change 搭好 backend（FastAPI + auth + repos + commits + blobs + ingest + process + jobs）+ Web UI；但用户**只能通过 Web UI 或 curl** 操作 dataplat
- `packages/sdk-py/src/dataplat_sdk/__init__.py` 只有 `__version__ = "0.0.0"` 占位（bootstrap-monorepo 阶段建的）
- Phase 1 MVP 收尾需要这块；做完后用户能：(a) 在 Python 脚本里 `Client().create_repo(...).upload_blob(...).commit(...)`；(b) 在 shell 里 `dataplat repo create ...`

## 问题陈述

- 缺 `Client(base_url, token=None)` 同步类（httpx.Client 持有 cookie session）
- 缺 8 个 Client 方法：login / create_repo / get_repo / upload_blob / create_commit / enqueue_ingest / enqueue_process / get_job
- 缺 Typer-based `dataplat` CLI + entry_point
- 缺 6 测试（3 SDK unit 用 ASGITransport 直接打 FastAPI app + 3 CLI integration 用 CliRunner）
- 缺 self_check 13 AC

## 范围

**In scope**：
- `packages/sdk-py/pyproject.toml`：加 `typer>=0.12` 依赖 + `[project.scripts] dataplat = "dataplat_sdk.cli:app"`
- `packages/sdk-py/src/dataplat_sdk/__init__.py`：export Client + __version__
- `packages/sdk-py/src/dataplat_sdk/client.py`：`Client(base_url, token=None, timeout=30.0)` 同步类
  - 内部 `_http: httpx.Client(base_url=base_url, cookies=httpx.Cookies(), timeout=timeout)`
  - `login(username, password) -> None`：POST /auth/login；cookie 自动持久
  - `create_repo(owner, name, layer="bronze", subtype="pdf", visibility="public") -> dict`：POST /repos
  - `get_repo(owner, name) -> dict`：GET /repos/{owner}/{name}
  - `upload_blob(owner, name, content: bytes) -> str (sha256)`：POST /repos/{}/{}/blobs
  - `create_commit(owner, name, entries: list[dict], parents=None, author_id, message=None, ref=None) -> dict`：POST /repos/{}/{}/commits
  - `enqueue_ingest(owner, name, adapter_name, adapter_version, spec, author_id, ref=None) -> str (job_id)`：POST /jobs/ingest
  - `enqueue_process(source_owner, source_name, source_ref, target_owner, target_name, processor_name, processor_version, config, author_id, ref=None) -> str (job_id)`：POST /process
  - `get_job(job_id) -> dict`：GET /jobs/{job_id}
- `packages/sdk-py/src/dataplat_sdk/cli.py`：
  - `app = typer.Typer(name="dataplat", help="dataplat CLI")`
  - 子命令：`login` / `repo create|get` / `blob upload` / `commit create` / `ingest` / `process` / `jobs get`
  - 全局参数：`--url` (env DATAPLAT_URL) / `--username` (env DATAPLAT_USERNAME)
- `packages/sdk-py/tests/test_sdk_client.py`：3 SDK unit 测试用 `httpx.ASGITransport(app=fastapi_app)` 直打 backend（不开 HTTP server）
- `packages/sdk-py/tests/test_sdk_cli.py`：3 CLI integration 用 `typer.testing.CliRunner` + monkeypatch SDK Client
- `scripts/_self_check.sh`：追加 `run_sdk_cli_mvp` 13 AC + filter

**Out of scope**（显式）：
- async Client → follow-up `sdk-async-client-*`
- retry / rate-limit / pagination → follow-up `sdk-retry-*`
- download_blob / iter_records / dataset() 高级 API → follow-up `sdk-dataset-iter-*` / `sdk-download-blob-*`
- lineage_show / pipeline run → follow-up `cli-lineage-*` / `sdk-pipeline-*`
- 配置文件（~/.dataplat/config.yaml）+ profile → follow-up `cli-config-file-*`
- shell autocomplete → follow-up `cli-autocomplete-*`
- 进度条 / 断点续传 → follow-up `cli-progress-bar-*` / `sdk-resumable-upload-*`
- SDK 发到 PyPI → follow-up `sdk-pypi-publish-*`
- 真后端 live test → follow-up `sdk-live-test-*`

## 验收标准（13 AC）

- AC-1：Client 类存在 + 持有 httpx.Client 实例；
  `test -f packages/sdk-py/src/dataplat_sdk/client.py && uv run python -c "from dataplat_sdk import Client; import httpx; c=Client(base_url='http://x'); assert isinstance(c._http, httpx.Client)"`
- AC-2：Client 8 个方法齐全；
  `uv run python -c "from dataplat_sdk.client import Client; assert all(hasattr(Client, m) for m in ['login','create_repo','get_repo','upload_blob','create_commit','enqueue_ingest','enqueue_process','get_job'])"`
- AC-3：Client.login 签名含 username + password；
  `uv run python -c "from dataplat_sdk.client import Client; import inspect; s=inspect.signature(Client.login); assert 'username' in s.parameters and 'password' in s.parameters"`
- AC-4：Client.upload_blob 接受 bytes content（typed）；
  `uv run python -c "from dataplat_sdk.client import Client; import inspect; sig=inspect.signature(Client.upload_blob); ann=sig.parameters['content'].annotation; assert ann in (bytes, 'bytes')"`
- AC-5：Client.create_commit 签名含 entries + parents + author_id；
  `uv run python -c "from dataplat_sdk.client import Client; import inspect; s=inspect.signature(Client.create_commit); assert set(['entries','parents','author_id']).issubset(set(s.parameters))"`
- AC-6：Client.enqueue_process 签名含 source_owner / target_owner / processor_name 等；
  `uv run python -c "from dataplat_sdk.client import Client; import inspect; s=inspect.signature(Client.enqueue_process); assert set(['source_owner','source_name','target_owner','target_name','processor_name','processor_version']).issubset(set(s.parameters))"`
- AC-7：CLI app 是 typer.Typer 实例；
  `test -f packages/sdk-py/src/dataplat_sdk/cli.py && uv run python -c "from dataplat_sdk.cli import app; import typer; assert isinstance(app, typer.Typer)"`
- AC-8：pyproject.toml 声明 dataplat CLI script entry；
  `grep -q '^dataplat = "dataplat_sdk.cli:app"' packages/sdk-py/pyproject.toml || grep -qE '^dataplat\s*=\s*"dataplat_sdk\.cli:app"' packages/sdk-py/pyproject.toml`
- AC-9：CLI 含 7 个子命令（login / repo / blob / commit / ingest / process / jobs）；
  `uv run python -c "from dataplat_sdk.cli import app; from typer.main import get_command; cmd=get_command(app); names={c for c in cmd.commands.keys()}; assert {'login','repo','blob','commit','ingest','process','jobs'}.issubset(names)"`
- AC-10：tests/ ≥ 6 + 全 PASS；
  `[ "$(cd packages/sdk-py && uv run pytest --collect-only -q tests/ 2>&1 | grep -cE 'tests/test_sdk_(client|cli)\.py::')" -ge 6 ]`
- AC-11：ruff + mypy 含 packages/sdk-py 全 PASS；
  `uv run ruff check packages/sdk-py && uv run mypy packages/sdk-py/src`
- AC-12：Client 用 sync httpx.Client（反向 grep 拦 AsyncClient）；
  `test -f packages/sdk-py/src/dataplat_sdk/client.py && grep -q "httpx.Client" packages/sdk-py/src/dataplat_sdk/client.py && ! grep -q "httpx.AsyncClient" packages/sdk-py/src/dataplat_sdk/client.py`
- AC-13：self_check 自递归

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| typer 依赖增加 SDK 体积 | 低 | 用户 pip install 多 3MB | typer + click 是事实标准；用户可接受 |
| CLI tests 用 CliRunner mock 复杂 | 中 | test_cli 慢 | 用 monkeypatch.setattr 替换 Client 实例；CliRunner.invoke 直接调 typer app |
| SDK Client 与 FastAPI ASGITransport 集成可能 cookie 不持久 | 中 | test_a/b 失败 | httpx.Cookies() 显式持有；ASGITransport 与真 HTTP 行为一致；adapter-firecrawl 已验过同 pattern |
| mypy 对 typer 装饰器签名宽容度低 | 中 | mypy 报 callable type 错 | typer 0.12+ 类型提示完善；ruff/mypy 0.x 已稳；fallback 用 `# type: ignore[misc]` |
| AC-8 pyproject grep 跨行 multiline 难匹配 | 中 | AC FAIL | 用 alternation grep；OR 备选 `grep -A2 "\\[project.scripts\\]" packages/sdk-py/pyproject.toml \| grep dataplat` |
| ASGITransport 需要 FastAPI app 实例 → SDK 测试要导 backend | 中 | 跨包依赖 | 测试时 import dataplat_api.main.app；workspace 模式下可行（test_processor / test_llm 已验） |
| AC 验证命令 dry-parse 全过（SKILL #8） | 低 | spec 卡 stage 2 | AC-1/2/7 已 compile 通过 |
| summary.md SSoT 漂移（SKILL #9） | 低 | 流程缺陷 | 已在 stage 1 启动时填好；占位符 grep = 0 |
| uv venv 没装 dev extras（SKILL #10 候选第 4 次） | 中 | 测试 import 失败 | 先 `cd packages/sdk-py && uv sync --extra dev` 或 root sync |
| 事件循环嵌套（SKILL #11 候选第 2 次） | 低 | 本变更 sync only 不撞 | 本变更 SDK Client 是 sync httpx.Client；不嵌套 |

## 跨链路一致性自审（request-analysis SKILL 9 条）

1. ✅ 四链路一致：Client 8 方法 ↔ backend 8 路由 ↔ test fixture（用 ASGITransport）↔ AC-2/3/4/5/6
2. ✅ 事务边界：本变更纯 client；无 DB 事务
3. ✅ AC 验证命令一行式：13 条全单行；3 条 python -c 已 compile 通过
4. ✅ 风险缓解 ↔ AC 测试：ASGITransport ↔ test_sdk_client；CliRunner monkeypatch ↔ test_sdk_cli
5. ✅ commit 链：llm-qa-gen-20260518 (fd33a82) → 本变更 base
6. ✅ 反向 grep：AC-12 反向拦 AsyncClient（确保 sync only）
7. ✅ process_tasks 6 条：T-7~T-12 占位
8. ✅ AC 验证命令真跑 dry-parse：AC-1/2/7 已 compile 通过
9. ✅ summary.md frontmatter：stage 0 即填好；占位符 grep = 0；**SKILL #9 第 5 次连胜**

## 受影响模块

- 新建：`packages/sdk-py/src/dataplat_sdk/client.py`
- 新建：`packages/sdk-py/src/dataplat_sdk/cli.py`
- 新建：`packages/sdk-py/tests/__init__.py` + `packages/sdk-py/tests/test_sdk_client.py` + `packages/sdk-py/tests/test_sdk_cli.py`
- 改动：`packages/sdk-py/pyproject.toml`（加 typer + script entry + dev extras）
- 改动：`packages/sdk-py/src/dataplat_sdk/__init__.py`（export Client）
- 改动：`scripts/_self_check.sh`（追加 13 AC）

## 不受影响但易混淆的模块

- `apps/api/dataplat_api/`：不动；本变更只**消费** backend API，不改 backend
- `apps/web/`：不动；CLI / SDK 是 backend 的独立 client
- `worker/`：不动

## 引用

- design.md §7.2 / §7.3（SDK / CLI 示例）
- design.md §11.6（Phase 1 MVP 包含 SDK + CLI）
- design.md §11.3（packages/sdk-py/ 目录占位）
- auth-scaffold-20260517 summary.md（cookie session 路径）
- repo-api-mvp + commit-api-mvp + rq-worker-skeleton + processor-framework summary.md（backend API 形态）
- SKILL.md request-analysis 9 条 checklist
