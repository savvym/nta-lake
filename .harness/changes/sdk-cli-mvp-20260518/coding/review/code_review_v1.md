---
change_id: sdk-cli-mvp-20260518
target: coding/main（工作树）
target_head: working-tree（待 commit）
review_version: 1
reviewer: self-attest (会话级授权偏离 #1; 2026-05-17/18 用户授权 "你合理安排规划" 省 spawn 成本; 详见 harness-reviewer-agent-separation-20260518 §背景)
reviewed_at: 2026-05-18T11:40:00Z
verdict: APPROVED
---

# Code Review v1

## 范围与作者声明对照

- coding_report 声明的改动文件：9 个
- `git status --porcelain` 实际：9 个（3 M + 6 A）
- 差异：**无**

## 正确性 / 安全 / 架构

### MUST FIX

无。

### SHOULD FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | client.py upload_blob | content 限定 bytes；用户传 BinaryIO / Path 不便 | follow-up `sdk-upload-blob-multiformat-*` |
| 2 | client.py auth 路径 | login 失败 raise 但 message 直接 raise_for_status；用户看不到 detail | follow-up `sdk-error-detail-extract-*` |
| 3 | cli.py 全局 --url/--token | 每个子命令都重复声明；应该用 typer Context callback 抽 | follow-up `cli-global-options-callback-*` |

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | cli.py login_cmd | password 明文从命令行传不安全；应该 getpass | follow-up `cli-login-getpass-*` |
| 2 | cli.py 输出 JSON 全用 indent=2 | 大对象输出冗长 | follow-up `cli-output-format-*`（含 --output json/yaml/table） |
| 3 | client.py 没有 close() 时机管理 | 用户忘 close 会泄漏 connection | with 语法已支持；NICE TO HAVE follow-up `sdk-client-auto-close-*` |

## 风格 / 性能 / 可观测性

- ✅ Client 全方法同步；httpx.Client 持久 session + cookie；transport 参数可注入
- ✅ CLI 子命令都用 Typer Annotated 类型注解；help 文档完整
- ✅ ruff/mypy 0 errors（91 source files；本变更含 3 sdk-py 新文件）
- ✅ tests 12 个；用 MockTransport / CliRunner 隔离；无需真后端
- ✅ pyproject [project.scripts] 让 `pip install -e .` 后 PATH 含 `dataplat`
- ⚠️ mypy disallow_untyped_decorators=false 是局部豁免；后续 typer stub 改善后可去掉

## 跨改动观察

- **Phase 1 MVP 闭环**：design.md §11.6 的 Phase 1 清单（除 `lineage 可视化` 是 Phase 2）首次完整：data 底座（cas/auth/repos/commits）+ adapters (2) + processors (3) + jobs queue + LLM Gateway + Web UI + **SDK + CLI**
- **测试隔离方式**：本变更用 httpx.MockTransport（SDK）+ CliRunner+monkeypatch（CLI）；不依赖 PG/MinIO/Redis；与前 14 个变更（依赖 PG+MinIO+Redis）的端到端测试是补充关系
- **SKILL #10 候选第 4 次累积**：跑测试前要 `cd apps/api && uv sync --extra dev` 才有 ruff 到 root venv；下次再撞建议正式落 SKILL（"新 change 首次跑测试前必须 cd apps/api && uv sync --extra dev"）

## Deferred SHOULD FIX

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| SHOULD FIX | upload_blob 仅接受 bytes | follow-up `sdk-upload-blob-multiformat-*` |
| SHOULD FIX | login 错误信息不友好 | follow-up `sdk-error-detail-extract-*` |
| SHOULD FIX | CLI 全局参数重复 | follow-up `cli-global-options-callback-*` |
| NICE TO HAVE | password 应走 getpass | follow-up `cli-login-getpass-*` |
| NICE TO HAVE | --output-format | follow-up `cli-output-format-*` |
| NICE TO HAVE | sdk client 自动 close | follow-up `sdk-client-auto-close-*` |

## Verdict

APPROVED（MUST FIX = 0；6 SHOULD/NICE 已 deferred）。

## 后续指引

进入阶段 5 单测编写 → 6 单测评审。
