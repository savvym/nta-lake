---
change_id: harness-reviewer-model-sonnet-20260518
version: 1
authored_at: 2026-05-18T20:55:00Z
status: draft
ac_kind_lint: exempt
ac_kind_lint_exempt_reason: |
  纯 harness 文档改动（仅改 .harness/agents/* + .harness/skills/expert-reviewer/SKILL.md）；
  无 dataplat 实代码改动；
  reviewer 复核必跑 `git log --stat <baseline>..HEAD` 确认所有改动文件 path 在 .harness/* 范围内。
---

# Spec：reviewer 子 agent 默认 sonnet 模型

## 背景

`harness-reviewer-agent-separation-20260518`（已 close）建立了"stage 2/4/6 必须 spawn 独立 reviewer 子 agent"的硬约束，但当时未约束 spawn 时的 **模型选择**——sub agent 默认继承父 session 模型（当前 opus 4.7）。

**触发**：本会话中，repo-files-tab-v2-20260518 stage 2 准备阶段，用户反馈"spawn 产生的模型感觉速度好慢"，要求"使用 sonnet 模型"，并进一步说"修改一下 .harness 里生成 reviewer 的逻辑"。

**根因**：review 任务（核对 grep 表达式语法 / 跨文件 cross-ref / 模板字段 lint / DAG 健全性）的智力负载 ≈ 模式匹配 + 谨慎陈述，不需要 opus 级推理（也不太能从 opus 拿到比 sonnet 显著好的 review 质量）。Opus 4.7 比 sonnet 4.6 慢约 3-5x，长链 review 累积体感非常明显。

## 问题陈述

三处 `Agent(...)` spawn 模板缺 `model=` 字段：

1. `.harness/agents/application-owner.md §7.5`（主模板，Owner 直接 copy）
2. `.harness/agents/reviewer-agent.md §7 spawn 入口签名`（reviewer 自查时参考）
3. `.harness/skills/expert-reviewer/SKILL.md § Application Owner 怎么 spawn`（SKILL 内嵌示例）

任一处漏改 → Owner 复制粘贴时 spawn 出 opus reviewer → 用户继续被慢拖慢。固化到规约层而非每次会话临时约定。

## 范围

In scope（**4 条 AC**）：

- **AC-1**：`application-owner.md §7.5` 的 `Agent(...)` 代码块含 `model="sonnet"` 字面 + 紧邻一段"为什么 sonnet"说明（review 智力负载 + 速度 3-5x + opus 留给 generator）
- **AC-2**：`reviewer-agent.md §7` 的 `Agent(...)` 代码块含 `model="sonnet"` 字面
- **AC-3**：`expert-reviewer/SKILL.md § Application Owner 怎么 spawn` 的 `Agent(...)` 代码块含 `model="sonnet"` 字面
- **AC-4**：`reviewer-agent.md` 新增一节（标题如 `## 8. 模型选择`），定义"reviewer 默认 sonnet"为硬约束 + 何时可以偏离（如 reviewer 自报"本次评审涉及深度因果推理，需切换 opus" → 仍允许 Owner override，但必须在 review 文件附理由）

## 非范围

- 不改 `scripts/_self_check.sh` 加 grep 守门 `model="sonnet"`（→ follow-up `harness-reviewer-model-lint-*` P3）
- 不强制 generator / coding agent 也 sonnet（generator 跟 session 主模型 = 用户当前 opus session 的合理默认）
- 不引入 model 可配置参数（保持字面 sonnet 避免过早抽象）
- 不动 `scripts/_self_check.sh` 既有 reviewer-lint / ac-kind-lint 任何逻辑
- 不回填历史 review 文件标注 spawning model

## 验收标准

`kind` 二分：static / behavioral。本 change 声明 `ac_kind_lint: exempt`（纯 .harness/* 文档改动）。

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | application-owner.md §7.5 模板含 model="sonnet" 字面 + 邻近"为什么 sonnet"段 | `awk '/^## 7\\.5/{p=1;next} p && /^## /{exit} p' .harness/agents/application-owner.md \| grep -q 'model="sonnet"' && awk '/^## 7\\.5/{p=1;next} p && /^## /{exit} p' .harness/agents/application-owner.md \| grep -qE 'review.*不需.*opus\|速度.*3-5x\|sonnet'` | 2 grep 命中（model 字面 + 理由文案）|
| AC-2 | static | reviewer-agent.md §7 spawn 入口签名代码块含 model="sonnet" 字面 | `awk '/^## 7\\./{p=1;next} p && /^## /{exit} p' .harness/agents/reviewer-agent.md \| grep -q 'model="sonnet"'` | 1 grep 命中 |
| AC-3 | static | expert-reviewer SKILL § Application Owner 怎么 spawn 含 model="sonnet" | `awk '/Application Owner 怎么 spawn/{p=1;next} p && /^### |^## /{exit} p' .harness/skills/expert-reviewer/SKILL.md \| grep -q 'model="sonnet"'` | 1 grep 命中 |
| AC-4 | static | reviewer-agent.md 新增"模型选择"节（标题含"模型"），含"默认 sonnet"硬约束 + override 路径 | `grep -qE '^## [0-9]+\\..*模型' .harness/agents/reviewer-agent.md && grep -qE '默认.*sonnet\|sonnet.*默认' .harness/agents/reviewer-agent.md && grep -qE 'override\|偏离\|切换 opus' .harness/agents/reviewer-agent.md` | 3 grep 命中 |
| AC-5 | **behavioral** | self_check 跑 reviewer-lint + ac-kind-lint 未引入回归 | `DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 bash scripts/_self_check.sh reviewer-lint` 退码 0 + `bash scripts/_self_check.sh ac-kind-lint` 退码 0 | 2 lint block 全 PASS（**behavioral：真跑 lint，不只 grep**） |

**Behavioral AC：AC-5**（真跑 self_check lint 2 块）。配合 `ac_kind_lint: exempt` 自声明，未来 reviewer 复核必跑 git diff --stat 验证范围。

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| sonnet 4.6 在某些 review 场景（复杂跨文件 cross-ref / 反例构造）质量明显逊于 opus 4.7 | 中 | 中 | 在 reviewer-agent.md §模型选择节加 override 路径：Owner 判定本次评审需要 opus → 可以显式 spawn `model="opus"`，但必须在 review 文件附理由 |
| Sonnet reviewer 漏报 MUST FIX → 次轮 stage 4/6 才发现 → 流程回退多走一轮 | 中 | 中 | 长期靠 reviewer-lint + ac-kind-lint 等机械化守门兜底；reviewer 单体偶发漏报 ≠ 模型选择失败；持续观察跨 change 漏报率，必要时再回切 |
| Anthropic 模型 ID 字面 "sonnet" 在未来工具行为变更（如默认指向不同版本）| 低 | 低 | Agent tool 当前接受 enum {haiku,sonnet,opus}；若变更，统一规约一次 update |

## 受影响模块

- `.harness/agents/application-owner.md`：§7.5 spawn 模板 + 邻近一段说明
- `.harness/agents/reviewer-agent.md`：§7 spawn 入口签名 + 新增 §8 模型选择
- `.harness/skills/expert-reviewer/SKILL.md`：§ Application Owner 怎么 spawn 模板示例
- `.harness/changes/harness-reviewer-model-sonnet-20260518/`：本 change 自身（spec / tasks / summary）

## 不受影响

- `scripts/_self_check.sh`：不动
- `.harness/rules/development-process.md`：不动（spawn 模板细节由 application-owner.md 承载，rules 只引用）
- 既有 closed change 的 review 文件：不动
- 既有运行中 change（repo-files-tab-v2-20260518）的产物：不动；其 stage 2 reviewer 将在本 change merge 后用新规约 spawn

## 引用

- `.harness/agents/application-owner.md §7.5`
- `.harness/agents/reviewer-agent.md §7`
- `.harness/skills/expert-reviewer/SKILL.md § Application Owner 怎么 spawn`
- `.harness/changes/harness-reviewer-agent-separation-20260518/` 上游硬约束建立
- `.harness/skills/request-analysis/SKILL.md § 自声明豁免（ac_kind_lint: exempt）`
