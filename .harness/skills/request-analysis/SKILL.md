---
name: request-analysis
description: 把模糊的用户诉求转成可验收的 spec.md 与可执行的 tasks.md
applicable_stage: 阶段 1（需求分析）
inputs:
  - 用户的原始诉求文字 / 会话上下文
  - .harness/design.md（系统总体设计，按需查阅）
  - 关联的旧 change（如有，看 summary.md 与 spec.md）
outputs:
  - request_analysis/spec.md
  - request_analysis/tasks.md
---

# request-analysis Skill

## 进入条件

- 已经在 `.harness/changes/<id>/` 下复制好 `_template/`。
- 用户诉求至少能用一句话总结。
- 当前 `summary.md` 标记 stage=`request_analysis`、status=`in_progress`。

## 输入

1. **用户诉求**：原始描述（粘贴或链接到会话）。
2. **领域知识**：必要时查 `wiki/domain-glossary.md`、`.harness/design.md`。
3. **历史决策**：搜 `wiki/adr/` 与已 close 的 changes，看有无相关结论。

## 步骤

### 1. 复述与澄清

- 用自己的话复述需求到 spec.md 的"问题陈述"段。
- 列出**所有不确定点**到"待澄清问题"段；不要自我消解模糊。
- 如需用户回答，立即用 `AskUserQuestion` 等手段问，不要靠猜。

### 2. 边界识别

- 范围（in scope）：本次变更要做什么。
- 非范围（out of scope）：明确**不做**什么，避免后续 scope creep。
- 受影响模块：列出会改的目录/文件大类。
- 不受影响但常被混淆的模块：显式排除。

### 3. 验收标准

每条标准必须满足：

- **可演示**：能给用户跑一遍证明它达成（请求/响应、UI 操作、CLI 输出）。
- **可机械化**：能写成测试用例或检查脚本（最好直接附 pseudocode）。
- **可拒绝**：能写出"什么情况算没达成"。

不允许"用户感觉良好"、"性能更好"（除非附具体阈值）。

### 4. 风险识别

- 技术风险：依赖未就绪、性能边界、并发坑。
- 范围风险：可能与其他 change 冲突。
- 数据/合规风险：是否动到 PII、license、用户上传内容。
- 不可逆风险：迁移、删除、外部副作用。

每条风险必须配缓解方案或显式 accept。

### 5. 任务拆解

将 spec 落到 `tasks.md`：

- 每个任务粒度 1-3 小时可完成。
- 标明：`id` / `title` / `description` / `depends_on` / `estimated_stage`（落到哪个开发阶段产出）。
- 评审 / 单测 / CI / 部署作为任务模板里已有的占位，**不要漏写**。

## 产出

- `request_analysis/spec.md`：按模板填齐所有章节。
- `request_analysis/tasks.md`：按模板填齐任务表。
- `summary.md` 更新 stage=`request_analysis`、status=`waiting_review`、最近更新时间。

## 质量门禁

```text
spec.md 存在
spec.md 包含章节：背景 / 问题陈述 / 范围 / 非范围 / 验收标准 / 风险
验收标准条数 > 0
每条验收标准能被一条测试或一次演示验证
tasks.md 存在
tasks.md 任务条数 > 0
每个任务有 id / depends_on（可为空数组）/ estimated_stage
```

## 失败回退

- 用户诉求模糊到无法写出验收标准 → **不要硬写**，把澄清问题列在 spec.md，停在本阶段，向用户提问。
- 发现与现有架构冲突 → 暂停，先去 `wiki/adr/` 写一份 ADR proposed，跑评审流程。
- 范围明显超出单 change 承载（≥10 个任务且跨多模块）→ 拆 change，本 change 缩到第一个最小可交付。

## 反模式（评审会打回）

- "实现 / 完善 / 优化 X 功能" 类目标，没有验收标准。
- 验收标准纯定性："性能更好"、"代码更清晰"、"用户体验提升"。
- 任务直接写"实现整个系统"，没有粒度拆分。
- spec 偷偷加入 design.md 里已有的设计内容当背景，让评审分不清是已决策还是新提案。
