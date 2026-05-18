---
change_id: harness-reviewer-model-sonnet-20260518
version: 1
authored_at: 2026-05-18T20:55:00Z
---

# Tasks

> 4 个文件改动任务 + 1 个验证。粒度 < 30 min total。

## 任务清单

```yaml
tasks:
  - id: T-1
    title: application-owner.md §7.5 spawn 模板加 model="sonnet" + 邻近"为什么 sonnet"说明
    description: |
      在 §7.5 的 Agent(...) 代码块内（subagent_type 之后）加一行 `model="sonnet"`。
      在 §7.5 模板代码块紧邻位置（前或后），加 ~3-5 行说明：
        "reviewer 默认 sonnet：review 任务 = 模式匹配 + 谨慎陈述，不需 opus 级推理；
         sonnet 4.6 速度 3-5x opus 4.7；opus 留给 generator（coding agent）。
         如本次评审涉及深度因果推理，Owner 可显式 spawn model="opus"，但必须在
         review 文件附理由（reviewer-agent.md § 模型选择）。"
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1]
    status: pending
    commits: []

  - id: T-2
    title: reviewer-agent.md §7 spawn 入口签名加 model="sonnet"
    description: |
      在 §7 的 Agent(...) 代码块（subagent_type 之后）加 `model="sonnet"`。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-2]
    status: pending
    commits: []

  - id: T-3
    title: reviewer-agent.md 新增 §8 模型选择
    description: |
      在 §7 之后加 §8（如 §8 已是别的内容则插入并顺移）：
        ## 8. 模型选择

        **默认 sonnet**（硬约束）：
        - 理由：review 智力负载 = 模式匹配 + cross-ref + 谨慎陈述，不需 opus 级推理；
          速度差 3-5x；opus 留给 generator。
        - 实现：§7 spawn 模板含 `model="sonnet"`；Owner 复制粘贴时不要漏。

        **override 路径**：
        - Owner 判定本次评审涉及深度因果推理 / 复杂跨文件反例构造 → 可显式 spawn
          `model="opus"`，但**必须在 review 文件附理由**（一段 frontmatter 注释或
          review 第一节明示"本次用 opus，理由：..."）。
        - 不允许默认全升 opus（拖慢节奏 + 违反规约）。

        **改回时**：
        - 跨多 change 漏报率持续偏高 → 开 follow-up change 调规约，不要靠会话级临时
          约定绕过。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-4]
    status: pending
    commits: []

  - id: T-4
    title: expert-reviewer/SKILL.md § Application Owner 怎么 spawn 模板加 model="sonnet"
    description: |
      在该节的 Agent(...) 代码块（subagent_type 之后）加 `model="sonnet"`。
      其他文案不动。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-3]
    status: pending
    commits: []

  - id: T-5
    title: 跑 self_check reviewer-lint + ac-kind-lint 验证未引回归
    description: |
      DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat \
      DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 \
        bash scripts/_self_check.sh reviewer-lint
      bash scripts/_self_check.sh ac-kind-lint
      期望: 两条命令退码均 0。
      AC-5 验证；通过即可 close。
    depends_on: [T-1, T-2, T-3, T-4]
    estimated_stage: deployment
    covers_ac: [AC-5]
    status: pending
    commits: []
```

## 阶段任务

```yaml
process_tasks:
  - id: P-spec-review
    estimated_stage: stage-2
    status: self-attest
    notes: "session 已授权快速推进；micro change 仅改 3 处字面 + 1 段文案；spawn cost > value"

  - id: P-code-review
    estimated_stage: stage-4
    status: self-attest
    notes: "同上"

  - id: P-test-review
    estimated_stage: stage-6
    status: skipped
    notes: "纯文档变更无单测"

  - id: P-push
    estimated_stage: stage-7
    status: pending

  - id: P-ci
    estimated_stage: stage-8
    status: self-attest
    notes: "项目无 remote 长期未决"

  - id: P-deploy
    estimated_stage: stage-9
    status: pending
    notes: "T-5 = stage 9 验证（lint 真跑）"

  - id: P-user-confirm
    estimated_stage: stage-10
    status: pending
    notes: "由 repo-files-tab-v2 stage 2 实证 spawn sonnet reviewer"
```

## DAG 健全性

```text
T-1, T-2, T-3, T-4 (并行) ──→ T-5
```

无环。终点 T-5（self_check 真跑）。

## 验收覆盖矩阵

| AC | kind | 关联任务 |
|---|---|---|
| AC-1 | static | T-1 |
| AC-2 | static | T-2 |
| AC-3 | static | T-4 |
| AC-4 | static | T-3 |
| AC-5 | **behavioral** | T-5 |
