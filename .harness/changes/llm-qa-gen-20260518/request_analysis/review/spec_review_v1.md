---
change_id: llm-qa-gen-20260518
target: spec.md
target_version: 1
review_version: 1
reviewer: application-owner-agent
reviewed_at: 2026-05-18T09:50:00Z
verdict: APPROVED
---

# Spec Review v1

## 检查清单结论（expert-reviewer SKILL §1）

- [x] 背景：design.md §2.3 Repo E 核心 processor；processor-framework / llm-gateway-mvp / adapter-firecrawl 都已就位
- [x] 问题陈述：4 项缺失（processor 实现 / parse 工具 / jsonl 聚合 / 测试 + self_check）
- [x] 范围 / 非范围都有：In scope 列 5 类；Out of scope 列 8 类 follow-up
- [x] 每条 AC 可机械化：13 条全有验证命令；7 条 python -c 已 compile 通过
- [x] 风险有缓解：6 条风险全配缓解（含 SKILL #8/#9 流程风险 + adapter-firecrawl 已踩过的 FakeLLMProvider 模式）
- [x] 没有把已有架构当新提案：明确引用 llm-gateway-mvp fee46ee / processor-framework 8f2a867 / adapter-firecrawl 67a8e8b 的产物
- [x] 待澄清问题已清零（无 deferred；scope 选择已通过 AskUserQuestion）

## 跨链路一致性检查（SKILL 9 条）

- [x] 全部 9 条已在 spec §跨链路一致性自审 段自审通过
- [x] AC-12 用正向双 grep：`ctx.llm` 出现 + `llm is None` 出现（确保 processor 显式检查 + raise，而非 silent fallback）
- [x] AC-7 用 grep alternation 覆盖 3 个 suffix；AC-8 用单 grep "sft.jsonl"
- [x] process_tasks 6 条：T-7~T-12 完整

## 问题列表

### MUST FIX / SHOULD FIX

无。

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec §AC-12 | "llm is None" grep 命中实现里的检查 if 语句即可；但实现可能写成 `if llm is None` 也可能 `if not llm`，spec 强制了语法形态 | coding 阶段用 `if llm is None`；后续可改为更弹性的 pattern |
| 2 | spec §default prompt_template | 默认 prompt 没指定输出语言；中英文混排时可能不确定 | follow-up `llm-qa-gen-prompt-lang-*` |
| 3 | spec §_run_all | text_truncate=6000 字符对长文档会丢正文末段 | follow-up `llm-qa-gen-chunking-*`（与 adapter-firecrawl-chunking-* 同模式） |

## Verdict

APPROVED。

## 后续指引

进入 stage 3 coding。AC-12 实现用 `if llm is None: raise ValueError(...)` 形态以匹配 spec grep。
