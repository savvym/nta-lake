---
change_id: sdk-cli-mvp-20260518
version: 1
env: dev
deployed_at: 2026-05-18T12:00:00Z
image_tag: working-tree（dev 本地 uv run）
commit_sha: (will-be-filled-at-commit)
verifier: application-owner-agent
verdict: PASS
---

# Deploy Verification v1

> Dev 用 `uv run` 跑。本变更是 client 端（SDK + CLI），不需要部署到 backend；
> 验证通过：(1) SDK + CLI import 不报错；(2) `dataplat --help` 可用；(3) 全仓 self_check 无回归。

## 验证矩阵

| ID | 验收项 | 验证方式 | 期望 | 实际 | 备注 |
|---|---|---|---|---|---|
| AC-7 | CLI app 可 import | self_check AC-7 | typer.Typer 实例 | True | — |
| AC-10 | 12 测试全 PASS | pytest packages/sdk-py/tests | 12 passed | 12 passed in 0.38s | — |
| DEP-1 | SDK Client import 不报错 | `uv run python -c "from dataplat_sdk import Client; print(Client.__name__)"` | 退出 0 + 输出 Client | True | — |
| DEP-2 | CLI script entry 可发现 | `uv run python -c "from dataplat_sdk.cli import app; print(app.info.name)"` | 输出 dataplat | True | — |
| DEP-3 | `dataplat --help` 列子命令 | test_a_cli_help_lists_subcommands | help 含 7 个子命令 | True | — |
| DEP-4 | 全仓 self_check 无回归 | self_check 全跑 | 225/225 PASS | 225/225 PASS | — |
| DEP-5 | apps/api 测试无回归 | pytest 跨变更 26 PASS | 26 passed | 26 passed | — |
| DEP-6 | ruff/mypy 全仓 0 errors（含新加 mypy.overrides） | self_check AC-11 | 0 errors | 0 errors / 91 source files | — |

## 证据

### DEP-1 / DEP-2

```text
$ uv run python -c "from dataplat_sdk import Client; print(Client.__name__)"
Client
$ uv run python -c "from dataplat_sdk.cli import app; print(app.info.name)"
dataplat
```

### DEP-3

```text
$ uv run python -m dataplat_sdk.cli --help
 Usage: ... dataplat [OPTIONS] COMMAND [ARGS]...
 dataplat CLI
 Commands:
   blob     Blob 上传
   commit   Commit 操作
   ingest   ...
   jobs     Job 查询
   login    登录 dataplat
   process  ...
   repo     Repository 操作
```

### DEP-4

```text
PASS: 225
FAIL: 0
SKIP: 0
```

## 风险评估

- [ ] schema 不兼容？**否**。本变更纯 client 端；不动 backend
- [ ] 不可回滚操作？**否**
- [ ] 需要 follow-up？**是**。已列：async / retry / multiformat upload / error detail / global options / getpass / output format / auto-close / typer stub / config file / autocomplete / progress bar / PyPI publish / live test / lineage / pipeline / etc.

## Verdict

PASS。
