# Architecture Decision Records

> 每一个**架构级**决策（影响跨模块行为、跨 change 生效、难以回退）都写一份 ADR。

## 何时需要 ADR

至少满足以下任一条：

1. 引入或替换一个顶层依赖（数据库、消息队列、前端框架、构建工具）。
2. 改动跨多个 apps/packages 共享的接口契约（`packages/core` 的 Protocol、API gateway 路由模式、CAS 物理路径规则等）。
3. 选择多个合理方案中的一个并要锁定（如"用 Argon2 而非 bcrypt"——已写在 design.md §11.6，未来重审时需新 ADR）。
4. 推翻或修改一个既有 ADR。

**不需要 ADR 的情况**：单文件实现细节、命名风格、一次性补丁——这些归 PR 评论与 change 内 `summary.md` 的"关键决策"段。

## 文件命名

```
adr-NNNN-<kebab-case-title>.md
```

`NNNN` 是四位序号，从 `0001` 开始，**只增不复用**。被 supersede 的 ADR 不删，保留作历史。

示例：

- `adr-0001-monorepo-tooling-uv-pnpm-turbo.md`
- `adr-0002-cas-storage-path-layout.md`
- `adr-0003-llm-gateway-cache-key-strategy.md`

## 模板

新建 ADR 必须包含以下章节，结构固定：

```markdown
---
adr_id: NNNN
title: <一句话标题>
status: proposed       # proposed | accepted | superseded | rejected
date_proposed: YYYY-MM-DD
date_accepted: YYYY-MM-DD | n/a
deciders: [<name 或 agent id 列表>]
supersedes: []         # 旧 ADR id 列表
superseded_by: null
---

# ADR-NNNN: <标题>

## 上下文

<问题是什么、为什么现在做这个决策、约束有哪些。>

## 决策

<选择了什么。一句话总结，下面展开。>

## 理由

<为什么选这个方案。引用约束、数据、其他 ADR、design.md 章节。>

## 备选方案

| 方案 | 优势 | 劣势 | 拒绝原因 |
|---|---|---|---|
| A | | | |
| B | | | |

## 后果

- 正面：<带来什么>
- 负面：<引入什么风险 / 复杂度 / 学习成本>
- 不变量：<本 ADR 之后必须始终成立的约束，未来变更需新 ADR 推翻>

## 后续动作

- [ ] <跟进 task / change id>

## 引用

- design.md §x.y
- 相关 change / PR
```

## 工作流

1. 起草：`status=proposed`，提交到 PR。
2. 评审：走 `expert-reviewer` Skill（plan 模式）。Reviewer 标 MUST FIX / SHOULD FIX / NICE TO HAVE。
3. 通过：合并 PR，将 `status=accepted`、`date_accepted` 填上。
4. 推翻：新 ADR 的 `supersedes` 填旧 ADR id；旧 ADR 同步把 `superseded_by` 填新 ADR id、`status=superseded`。**不删旧文件**。

## 当前 ADR 列表

| ID | 标题 | 状态 | 日期 |
|---|---|---|---|
| — | _暂无_ | | |

> `bootstrap-monorepo` 变更落地时，建议起草至少以下 ADR：
>
> - ADR-0001：monorepo 工具栈（uv / pnpm / turbo）
> - ADR-0002：CAS 物理路径与 GC 策略
> - ADR-0003：JWT 双 token + httpOnly cookie 的具体 TTL 与轮换策略
>
> 这些当前已在 `design.md` §11 中阐述，但 design.md 是设计蓝图，决策固化必须有独立 ADR。
