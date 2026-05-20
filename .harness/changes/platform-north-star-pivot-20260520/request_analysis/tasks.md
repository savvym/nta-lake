---
change_id: platform-north-star-pivot-20260520
version: 1
authored_at: 2026-05-20T15:00:00Z
---

# Tasks

> 纯文档 / 治理 change，任务粒度 30-90 分钟。

## 任务清单

```yaml
tasks:
  - id: T-1
    title: 在 design.md 顶部新增 § 北极星（一句话定位 + 4 条硬约束 bullet）
    description: |
      位置：design.md 第 8 行 ## 1. 目标与设计原则 之前插入 ## 北极星 节。
      内容：一句话定位（"开箱即用的 LLM 训练数据工厂..."）+ 4 条硬约束
      （Bronze=文件树 / Silver+Gold=表 / Lineage=commit+row 双层 / 不做 git 语义）。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1]
    status: pending
    commits: []

  - id: T-2
    title: 新增 § 三层算子模型（Adapter / Loader / Operator 草图）
    description: |
      位置：design.md ## 4 关键抽象的接口设计 之内或之后新增。
      内容：三层定义表 + 每层 Protocol 草图（Python class 签名）+ 例子表
      （pdf-mineru → Loader、lang-id-filter → Operator）。
      开头加显眼"本节为契约草图，实现见 follow-up `operator-protocol-*` 等"标记。
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-2]
    status: pending
    commits: []

  - id: T-3
    title: 新增 § stats-first 设计 + § 行级血缘
    description: |
      stats-first：每行含 stats dict；Operator 显式声明 reads_stats / writes_stats。
      行级血缘：每行含 source_ref{repo,snapshot,path,blob_sha} + lineage_ops[]。
      给查询接口草图（"列出所有引用了 bronze/x/y@sha=abc 的 silver row"）。
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-4, AC-5]
    status: pending
    commits: []

  - id: T-4
    title: 新增 § 永不做清单（≥ 7 条粗体 bullet + 用户想要 X 时怎么指）
    description: |
      列表：branch / merge / cherry-pick / rollback / row-level diff /
      blob→blob lineage / Asset / manifest.yaml 至少 7 个。
      每条格式：**- 不做 X**：理由（一句）。用户想要 X 时该往哪指。
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-3]
    status: pending
    commits: []

  - id: T-5
    title: 新增 § 迁移路径（5 个 processor 重分类表）
    description: |
      表格列：name / current 形态 / 新形态 / 何时重写 follow-up 引用。
      行：pdf-mineru / llm-qa-gen / llm-summarize / markdown-normalize / firecrawl-adapter。
    depends_on: [T-2]
    estimated_stage: coding
    covers_ac: [AC-6]
    status: pending
    commits: []

  - id: T-6
    title: 新增 § 与业界的关系（data-juicer / The Stack / Dolma / lakeFS 借鉴 vs 划清）
    description: |
      4 行对照表 + 一段总结"为什么不直接用 data-juicer 而是自己实现"。
    depends_on: [T-2]
    estimated_stage: coding
    covers_ac: []  # 总结性章节，无独立 AC，整体性由 T-1~T-5 ACs 覆盖
    status: pending
    commits: []

  - id: T-7
    title: 把 design.md 老章节标 § "deprecated 设计（v1）"
    description: |
      老 §1.2 设计原则 / §2.2 概念定义 / §3.1 Bronze manifest 描述 / §4.2 Processor 接口 /
      §4.3 Recipe 部分内容标 deprecated 子节，附"v2 见 § <新章节>"指针。
      不删除原文（保留锚点避免 21 个老 change 引用 404）。
    depends_on: [T-1, T-2, T-3, T-4]
    estimated_stage: coding
    covers_ac: []
    status: pending
    commits: []

  - id: T-8
    title: 新增 .harness/rules/data-not-code-pivot.md
    description: |
      把永不做清单做成 rule 文件 + 一段"所有 change stage 2 评审必须确认不违反"。
      引用 design.md § 北极星 + § 永不做清单。
    depends_on: [T-4]
    estimated_stage: coding
    covers_ac: [AC-7]
    status: pending
    commits: []

  - id: T-9
    title: 更新 CLAUDE.md（指针 + 硬约束）
    description: |
      "关键文件导航"表加一行：理解北极星 → .harness/design.md § 北极星。
      "硬性约束"加第 6 条：所有改动不得违反 .harness/rules/data-not-code-pivot.md。
    depends_on: [T-1, T-8]
    estimated_stage: coding
    covers_ac: [AC-8]
    status: pending
    commits: []

  - id: T-10
    title: 写 scripts/lint/check_design_north_star.sh
    description: |
      bash 脚本，验证 design.md 含 § 北极星 / § 三层算子模型 / § 永不做清单 /
      § stats-first / § 行级血缘 / § 迁移路径 六个章节标题，
      每节字数 ≥ 100，并验证三层算子节含 Adapter / Loader / Operator 三个子节。
      OK 输出："OK: design.md north-star structure complete"；FAIL exit 1 含明确指引。
    depends_on: [T-1, T-2, T-3, T-4, T-5]
    estimated_stage: coding
    covers_ac: [AC-9]
    status: pending
    commits: []

  - id: T-11
    title: 在 scripts/_self_check.sh 新增 run_platform_north_star_pivot 块
    description: |
      10 条 AC 全部转 bash run_ac 调用。dispatcher case 加 platform-north-star-pivot 别名。
      full 调用链在 run_harness_ac_behavioral_tier 之前加 run_platform_north_star_pivot。
    depends_on: [T-10]
    estimated_stage: coding
    covers_ac: [AC-10]
    status: pending
    commits: []

  - id: T-12
    title: 本地跑 bash scripts/_self_check.sh platform-north-star-pivot → 10 PASS
    description: |
      作为 stage 5 单测验证。10 个 AC 全 PASS。
      verify pnpm/pytest 无回归（本 change 不动业务代码所以应当无回归）。
    depends_on: [T-11]
    estimated_stage: unit_test
    covers_ac: [AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10]
    status: pending
    commits: []
```

## DAG 摘要

```
T-1 ──┬── T-2 ──┬── T-5 ──┐
      │         └── T-6 ──┤
      ├── T-3 ────────────┤
      ├── T-4 ──┬── T-8 ──┼── T-9 ──┐
      │         └────────────────────┤
      └── T-7 (after T-1~T-4) ──────┤
                                     T-10 ── T-11 ── T-12
```

T-12 是 stage 5 单测，余下都是 stage 3 coding。

## Stage 估时

- Stage 1（spec/tasks）：已完成（本文件 + spec.md）
- Stage 2（review）：~30 分钟（sonnet reviewer）
- Stage 3（coding T-1 ~ T-11）：~3-4 小时
- Stage 4（code review）：~20 分钟
- Stage 5（T-12 自检）：~10 分钟
- Stage 6（test review）：~15 分钟
- Stage 7（push / merge）：~5 分钟
- Stage 8（CI = self_check full）：~5 分钟
- Stage 9（deploy verify）：n/a（doc-only，跳到 OK）
- Stage 10（用户确认）：~5 分钟
