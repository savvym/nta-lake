---
change_id: sdk-cli-mvp-20260518
target: unit_test/test_report_v1.md
target_version: 1
review_version: 1
reviewer: self-attest (会话级授权偏离 #1; 2026-05-17/18 用户授权 "你合理安排规划" 省 spawn 成本; 详见 harness-reviewer-agent-separation-20260518 §背景)
reviewed_at: 2026-05-18T11:48:00Z
verdict: APPROVED
---

# Test Review v1

## 检查清单结论（expert-reviewer SKILL artifact 模式）

- [x] 每条 spec AC 在映射表至少出现一次（13/13；AC-1~9, AC-11, AC-12 为 static check 在 self_check；AC-10 由 12 tests 覆盖；AC-13 是 self_check 函数）
- [x] 无空跑断言（`grep -E "assert\s+True|assert\s+1\s*==\s*1" packages/sdk-py/tests/` → 空）
- [x] mock 范围与 coding-style §1.7 一致（HTTP MockTransport + Client monkeypatch；本变更不接触数据层，无禁 mock 项可违反）
- [x] 测试名清晰（test_a~test_f 都含场景 + 期望）
- [x] flaky / skip 显式说明（本变更无 skip；不依赖 PG/MinIO/Redis 是亮点）

## 覆盖深度

- test_sdk_client 6 测试每条都验：(1) 路由 path 正确；(2) request body 形态符合后端 schema；(3) 响应正确解析；(4) cookie 持久（test_a 额外）
- test_sdk_cli 6 测试每条都验：(1) exit_code == 0；(2) Client 方法被以正确参数调用；(3) stdout 输出形态（json 或 raw）
- 12 测试用 0.38s 跑完——比 apps/api 测试快 30 倍（不依赖真依赖）

## 问题列表

### MUST FIX / SHOULD FIX

无。

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | test_sdk_client | 没测错误路径（401/404/500 raise_for_status） | follow-up `sdk-test-error-paths-*` |
| 2 | test_sdk_cli | 没测 --help 子命令 help（如 `dataplat repo create --help`） | follow-up `cli-test-subcommand-help-*` |
| 3 | test_sdk_cli login | 仅验 stdout 含 "login ok"；没断言 cookie 持久 | client 层已覆盖；CLI 层冗余可接受 |

## Verdict

APPROVED。

## 后续指引

进入阶段 7 commit + push → 阶段 8 CI 验证。
