---
change_id: sdk-cli-mvp-20260518
version: 1
authored_at: 2026-05-18T11:45:00Z
status: waiting_review
---

# Test Report v1

## 验收项 ↔ 测试映射

| AC ID | 测试文件 | 测试函数 |
|---|---|---|
| AC-1 | n/a | static check（self_check AC-1 isinstance httpx.Client） |
| AC-2 | n/a | static check（self_check AC-2 8 方法 hasattr） |
| AC-3 | n/a | static check（self_check AC-3 login 参数 inspect） |
| AC-4 | n/a | static check（self_check AC-4 content 注解 bytes） |
| AC-5 | n/a | static check（self_check AC-5 create_commit 参数 inspect） |
| AC-6 | n/a | static check（self_check AC-6 enqueue_process 参数 inspect） |
| AC-7 | n/a | static check（self_check AC-7 typer.Typer isinstance） |
| AC-8 | n/a | static check（self_check AC-8 pyproject grep） |
| AC-9 | n/a | static check（self_check AC-9 7 子命令 typer get_command） |
| AC-10 | packages/sdk-py/tests/test_sdk_client.py + tests/test_sdk_cli.py | 12 测试（6 client + 6 cli） |
| AC-11 | n/a | static check（self_check AC-11 ruff + mypy 含 packages/sdk-py） |
| AC-12 | n/a | static check（self_check AC-12 grep httpx.Client + 反向 AsyncClient） |
| AC-13 | scripts/_self_check.sh | run_sdk_cli_mvp |

## 测试文件清单

| 文件 | 类型 | 用例数 |
|---|---|---|
| packages/sdk-py/tests/test_sdk_client.py | 单元（httpx.MockTransport） | 6 |
| packages/sdk-py/tests/test_sdk_cli.py | 集成（CliRunner + monkeypatch Client） | 6 |

## Mock 范围声明

- 允许 mock：HTTP layer（httpx.MockTransport）；Client 类（monkeypatch cli.Client）
- 禁止 mock：无（本变更纯 client 端，无 DB / S3 / Redis 接触）

**本轮 mock**：
- `httpx.MockTransport(handler)`：测试 SDK Client 各方法时拦截 HTTP 请求；assert 路由 + body + 返预设响应
- `monkeypatch.setattr(cli_mod, "Client", factory)`：测试 CLI 时把 cli.Client 引用替换为 _FakeClient 工厂；fake 记录调用 + 返 stub
- `typer.testing.CliRunner().invoke(app, [...])`：测试 CLI argv 解析 + stdout

均与 coding-style §1.7 一致（数据访问层禁 mock；本变更不接触数据层）。

## 本地运行结果

```text
$ cd packages/sdk-py && uv run pytest -q tests/
............                                                             [100%]
12 passed in 0.38s

# 跨变更回归（apps/api 测试无破）：
$ cd apps/api && uv run pytest -q tests/test_llm_qa_gen.py tests/test_processor.py tests/test_firecrawl.py tests/test_llm.py
..........................                                               [100%]
26 passed in 12.24s
```

## 已知 flaky / 跳过

- 无 skip。本变更测试**不依赖 PG/MinIO/Redis**（前 14 个变更都依赖；本变更纯 client）

## 覆盖率

- Client 8 方法：6 个直接覆盖（login/create_repo/get_repo/upload_blob/create_commit/enqueue_ingest+process/get_job）；剩 2 个间接覆盖
- CLI 7 子命令：6 个直接覆盖（login/repo create/blob upload/ingest/jobs get）；commit/process/repo get 路径在 client 层间接覆盖

## 下一步

进入阶段 6 单测评审。
