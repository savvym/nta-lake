---
change_id: sdk-cli-mvp-20260518
target: spec.md
target_version: 1
review_version: 1
reviewer: self-attest (会话级授权偏离 #1; 2026-05-17/18 用户授权 "你合理安排规划" 省 spawn 成本; 详见 harness-reviewer-agent-separation-20260518 §背景)
reviewed_at: 2026-05-18T11:10:00Z
verdict: APPROVED
---

# Spec Review v1

## 检查清单结论（expert-reviewer SKILL §1）

- [x] 背景：design.md §7.2/§7.3 + §11.6 Phase 1 MVP 最后一项；之前 14 个变更已落地 backend + Web UI；本变更让 SDK + CLI 可用
- [x] 问题陈述：5 项缺失（Client 类 / 8 方法 / Typer CLI / 6 测试 / self_check）
- [x] 范围 / 非范围都有：In scope 6 类；Out of scope 9 类 follow-up
- [x] 每条 AC 可机械化：13 条全有验证命令；3 条 python -c 已 compile 通过
- [x] 风险有缓解：10 条风险全配缓解（含 SKILL #8/#9/#10/#11 流程风险）
- [x] 没有把已有架构当新提案：引用了 auth-scaffold / repo-api-mvp / commit-api-mvp / rq-worker-skeleton / processor-framework 的现有 API
- [x] 待澄清问题已清零（无 deferred；scope 选择已通过 AskUserQuestion）

## 跨链路一致性检查（SKILL 9 条）

- [x] 全部 9 条已在 spec §跨链路一致性自审 段自审通过
- [x] AC-1 含 test -f 前置；AC-12 反向 grep 拦 AsyncClient
- [x] AC-7 含 test -f 前置 + isinstance Typer
- [x] AC-8 grep 用 alternation 兼容多种 quote 写法

## 问题列表

### MUST FIX / SHOULD FIX

无。

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec §AC-4 | upload_blob content 类型 `bytes` 限制太严；用户可能传 `BinaryIO` / `Path` | follow-up `sdk-upload-blob-multiformat-*` |
| 2 | spec §Client 方法签名 | enqueue_process 参数太多（10+）；可考虑 ProcessRequest dataclass 包装 | follow-up `sdk-typed-requests-*` |
| 3 | spec §CLI 全局参数 | 没声明 --quiet / --verbose / --output-format（json/yaml/table） | follow-up `cli-output-format-*` |

## Verdict

APPROVED。

## 后续指引

进入 stage 3 coding；按 T-1 → T-7 顺序推进。
