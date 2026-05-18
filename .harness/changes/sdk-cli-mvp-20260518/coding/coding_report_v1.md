---
change_id: sdk-cli-mvp-20260518
version: 1
authored_at: 2026-05-18T11:30:00Z
branch: main
base_commit: fd33a82 (llm-qa-gen close)
head_commit: working-tree
status: waiting_review
---

# Coding Report v1

## 改动文件清单

| 路径 | 类型 | 说明 | 关联 task |
|---|---|---|---|
| `packages/sdk-py/pyproject.toml` | edit | 加 typer>=0.12 + [project.scripts] dataplat=cli:app + [project.optional-dependencies] dev | T-1 |
| `packages/sdk-py/src/dataplat_sdk/__init__.py` | edit | export Client + __version__=0.1.0 | T-1 |
| `packages/sdk-py/src/dataplat_sdk/client.py` | new | Client sync 类（httpx.Client）+ 8 方法（login/create_repo/get_repo/upload_blob/create_commit/enqueue_ingest/enqueue_process/get_job）+ context manager + transport 参数（测试用 MockTransport 注入） | T-2 |
| `packages/sdk-py/src/dataplat_sdk/cli.py` | new | Typer app + 4 sub-Typer (repo/blob/commit/jobs) + 3 顶级命令 (login/ingest/process)；全局参数 --url/--token；命令内构造 Client + json 输出 | T-3 |
| `packages/sdk-py/tests/__init__.py` | new | 空 init | T-4 |
| `packages/sdk-py/tests/test_sdk_client.py` | new | 6 测试用 httpx.MockTransport（不依赖真后端）：(a) login 持久 cookie / (b) create+get_repo 路由 / (c) upload_blob 返 sha / (d) create_commit payload 形态 / (e) enqueue_ingest+process 返 job_id / (f) get_job | T-4 |
| `packages/sdk-py/tests/test_sdk_cli.py` | new | 6 测试用 CliRunner + monkeypatch Client：(a) --help 列子命令 / (b) login 调 Client.login / (c) repo create 输出 json / (d) blob upload 读文件 / (e) ingest 输出 job_id / (f) jobs get 输出 json | T-5 |
| `pyproject.toml` | edit | 加 mypy.overrides：dataplat_sdk.cli disallow_untyped_decorators=false（typer 装饰器）+ typer/click ignore_missing_imports | T-6 |
| `scripts/_self_check.sh` | edit | 追加 run_sdk_cli_mvp 13 AC + filter + 总入口 | T-7 |

## 与 tasks.md 的映射

| Task | 状态 | 备注 |
|---|---|---|
| T-1 pyproject + __init__ | done | typer + script entry 双重生效 |
| T-2 client.py 8 方法 | done | transport= 参数让测试注入 MockTransport 不需开 server |
| T-3 cli.py Typer app | done | 7 子命令；help 友好；env vars 通过 typer.Option(envvar=) |
| T-4 SDK 6 测试（spec 写 3，实际 6） | done（全 PASS 0.38s） | MockTransport 隔离；不依赖后端 |
| T-5 CLI 6 测试（spec 写 3，实际 6） | done | monkeypatch Client + CliRunner |
| T-6 lint+type | done | ruff 自动 fix 2 处 I001；mypy 在 root pyproject 加 2 个 overrides |
| T-7 self_check | done | 13/13；全仓 212→225 |

## 偏离 spec / trade-off

- **tests 数量超 spec 预期**：spec 写 "3 SDK + 3 CLI = 6 测试"；实际写了 6 SDK + 6 CLI = 12 测试。每条 Client 方法 + 每条 CLI 子命令都有独立测试，AC-10 ≥ 6 仍然满足且超额。
- **mypy override 加在 root pyproject**：spec 没显式列；strict 模式下 typer 装饰器抱怨 "untyped decorator"；typer 0.12+ 行为稳定，trust 装饰器；同时加 typer/click ignore_missing_imports 防 stub 解析问题。
- **uv venv root sync 没自动装 sdk-py dev extras**：跑 `uv run ruff` 报 Failed to spawn；要在 `cd apps/api && uv sync --extra dev` 后才装 ruff 到 root .venv。**这是 SKILL #10 候选第 4 次累积**（前 3 次都是 apps/api；本次再次撞，建议下次落 SKILL）。临时绕开方式：`cd apps/api && uv sync --extra dev`（apps/api dev 已含 ruff/mypy）。
- **AC-8 grep pattern**：`grep -qE "^dataplat = \"dataplat_sdk\\.cli:app\""` 用 escape 在 toml multiline `[project.scripts]` 表中精确匹配。
- **SDK transport 字段**：Client.__init__ 加可选 `transport: httpx.BaseTransport | None = None`；生产用户不传走真 HTTP；测试传 MockTransport 拦截。比 monkeypatch.setattr 更显式 + 单向。

## 本地校验

```text
ruff check packages/sdk-py: All checks passed!（自动 fix 2 处）
mypy packages/sdk-py/src: Success: no issues found in 3 source files
ruff + mypy 全仓: All checks passed! / 91 source files 0 errors
pytest packages/sdk-py/tests: 12 passed in 0.38s
pytest apps/api/tests/test_llm_qa_gen + test_processor + test_firecrawl + test_llm: 26 passed in 12.24s（无回归）
self_check sdk-cli-mvp: PASS=13 / FAIL=0
self_check 全仓: PASS=225 / FAIL=0（16 个 block）
```

## 已知未解决问题

- spec §Out of scope 9 类（async / retry / download_blob / lineage / config file / autocomplete / progress bar / PyPI publish / live test）均为 follow-up
- mypy `disallow_untyped_decorators=false` 是 cli.py 局部豁免；可能掩盖真正的装饰器类型错误 → follow-up `sdk-cli-typer-stub-improve-*`
- CLI 没有 --quiet / --output-format（spec NICE TO HAVE）→ follow-up `cli-output-format-*`

## 下一步

进入阶段 4 编码评审。
