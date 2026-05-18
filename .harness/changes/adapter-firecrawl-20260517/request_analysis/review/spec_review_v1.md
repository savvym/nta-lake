---
change_id: adapter-firecrawl-20260517
target: spec.md
target_version: 1
review_version: 1
reviewer: self-attest (会话级授权偏离 #1; 2026-05-17/18 用户授权 "你合理安排规划" 省 spawn 成本; 详见 harness-reviewer-agent-separation-20260518 §背景)
reviewed_at: 2026-05-18T08:20:00Z
verdict: APPROVED
---

# Spec Review v1

## 检查清单结论（expert-reviewer SKILL §1）

- [x] 背景写明了为什么现在做：design.md §2.3/§4.1/§11.6 + ctx.llm 已落地 + AdapterRunner 漏注入 follow-up + 用户 stage 0 选定
- [x] 问题陈述对外部读者可理解：5 项缺失（adapter / image extract / ctx 注入 / 6 测试 / self_check）
- [x] 范围 / 非范围都有：In scope 列 6 类；Out of scope 列 9 类 follow-up
- [x] 每条 AC 可机械化：13 条全有验证命令；5 条 python -c 已 compile 通过
- [x] 风险有缓解：8 条风险全部配缓解（含 SKILL #8/#9/#10 三条流程风险）
- [x] 没有把已有架构当新提案：引用了 llm-gateway-mvp 8f2a867/fee46ee 和 adapter-framework 7b6f7ce/d41ead7 的产物
- [x] 待澄清问题已清零（无 deferred；scope 选择已通过 AskUserQuestion）

## 跨链路一致性检查（SKILL 9 条）

- [x] 全部 9 条已在 spec §跨链路一致性自审 段自审通过
- [x] AC-3 用三重 grep（test -f + 正向双 grep + 反向双拦 None）—— reverse-grep checklist 第 6 条强化
- [x] AC-7 反向拦 asyncio.gather（防"以为串行实际并发"陷阱）
- [x] process_tasks 6 条：T-7~T-12 完整

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec §AC-5 | extract_image_urls 命令很长（4 行连串 assert），dry-parse 通过但可读性差 | coding 阶段把 assert 拆开；spec 不动 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec §范围 | image 失败"吞掉不阻塞"未在 AC 中机械化校验 | 端到端 test_e 可断言"图片 GET 失败时 content.md 仍然成功"，但增加复杂度；保留为隐式语义 |
| 2 | spec §FirecrawlURLSpec | request_timeout_seconds 默认 30s 是否太长 | 实测 8s html + ctx.llm 调用通常 < 10s；保留 30s 作为安全冗余 |

## Verdict

APPROVED。

## 后续指引

进入 stage 3 coding；按 T-1 → T-6 顺序推进。AC-3 反向 grep 包含两个 None pattern（llm 和 blob_store），需在 coding 阶段确保 adapter_runner.py 不出现这两个 pattern。
