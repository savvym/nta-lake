---
change_id: llm-gateway-mvp-20260517
target: spec.md
target_version: 1
review_version: 1
reviewer: application-owner-agent
reviewed_at: 2026-05-17T20:00:00Z
verdict: APPROVED
---

# Spec Review v1

## 检查清单结论（expert-reviewer SKILL §1）

- [x] 背景写明了为什么现在做：design.md §4.5/§5.1/§11.2/§11.7 #2 显式要求 + processor-framework 已落地 RunContext.llm 占位
- [x] 问题陈述对外部读者可理解：列了 6 层（协议/provider/cache/gateway/factory/集成）+ 1 个 processor 端到端
- [x] 范围 / 非范围都有：In scope 列 11 项；Out of scope 列 10 项（cost / 多 provider / rate limit / audit / agent / budget / 多模态 / live test / UI 全显式排除）
- [x] 每条 AC 可机械化：13 条全有验证命令；9 条 python -c 均 compile 通过（dry-parse）
- [x] 风险有缓解：7 条风险全部配缓解（anthropic 惰性构造 / cache key sort_keys / fake 简单模板 / retry sleep monkeypatch / StandardRunContext 默认值不动 / dry-parse 全过 / summary frontmatter 已填）
- [x] 没有把已有架构当新提案：明确引用 processor-framework 8f2a867 / cas-storage / rq-worker-skeleton 的产物
- [x] 待澄清问题已清零（无 deferred 项；scope 选择已通过 stage 0 AskUserQuestion 与用户确认）

## 跨链路一致性检查（SKILL 9 条 checklist）

- [x] 全部 9 条已在 spec §跨链路一致性自审 段自审通过
- [x] AC-1 LLMRequest.extra=forbid ↔ AC-4 cache key 用 LLMRequest 字段（model_id+messages+sampling）↔ test_b cache roundtrip 用 LLMRequest fixture：四链路一致
- [x] 反向 grep + test -f：AC-8 含 `test -f` + 正向 grep + 反向 `! grep -E "llm\s*=\s*None"`（拦截"代码里显式注入 None 的退化")
- [x] process_tasks 6 条：T-11~T-16 完整

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec §AC-2 | AnthropicProvider 类存在 + hasattr call 不能证明它"实现了 LLMClient"。但 LLMClient Protocol 是 runtime_checkable，可直接 isinstance | 改为 `isinstance(AnthropicProvider(api_key='dummy'), LLMClient)`（构造惰性允许 dummy key） |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec §AC-3 | test_a 已覆盖 fake deterministic，AC-3 命令本质重复测试 | 保留 AC-3 作为 stage 0 静态门禁；test_a 作为运行期验证。可不改 |
| 2 | spec §LLMSummarizeProcessor | 没说 Processor.accepts/produces 的 RepoSelector/Spec 怎么填 | coding 阶段决定（按 markdown-normalize pattern：accepts layer=bronze/silver；produces layer=silver/gold） |

## Verdict

APPROVED（MUST FIX = 0；SHOULD FIX #1 在 coding 阶段顺手改 AC-2 命令为 isinstance 形态，spec 不动）。

## 后续指引

进入 stage 3 coding。SHOULD FIX #1 在 self_check 注册时把 AC-2 命令升级为 isinstance 校验（spec v1 保持原文本，coding_report 声明 trade-off）。
