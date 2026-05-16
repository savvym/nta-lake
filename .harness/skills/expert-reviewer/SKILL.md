---
name: expert-reviewer
description: 对计划（spec/tasks）或产物（test 报告等）做独立、严格的评审
applicable_stage: 阶段 2（需求评审）/ 阶段 6（单测评审）
modes:
  - plan：评审 spec.md + tasks.md
  - artifact：评审 unit_test/test_report 或其他非代码产物
inputs:
  - 被评审对象（spec/tasks 或 report）
  - 上游 spec.md（artifact 模式时用于核对覆盖率）
  - .harness/rules/development-process.md
  - .harness/rules/coding-style.md（仅 artifact 模式需要）
outputs:
  - <stage>/review/<target>_review_v{N}.md
---

# expert-reviewer Skill

> 评判者必须是独立子会话或独立 Agent，**不能与 Generator 共享上下文**。否则会偏袒。

## 进入条件

- 被评审产物已生成且对应阶段 status=`waiting_review`。
- 当前会话**未**参与该产物的撰写。

## 输入

- **plan 模式**：spec.md 与 tasks.md 的最新版本。
- **artifact 模式**：被评对象（test_report 等）+ 它声明覆盖的上游 spec。
- 必读规则：`development-process.md`。

## 步骤

### 1. 对照清单做静态检查

#### plan 模式 spec.md：

- [ ] 背景写明了为什么现在做。
- [ ] 问题陈述与目标可被一个外部读者理解。
- [ ] 范围 / 非范围都有。
- [ ] 验收标准每条都可演示且可机械化。
- [ ] 风险有缓解措施或显式 accept。
- [ ] 没有把已有架构（design.md）当新提案重复。

#### plan 模式 tasks.md：

- [ ] 每个任务粒度合理（1-3 小时）。
- [ ] depends_on 形成 DAG，没有循环。
- [ ] 评审 / 单测 / CI 阶段对应任务都存在。
- [ ] 没有 "做完整个系统" 类目标性任务。

#### artifact 模式（例如 test_report）：

- [ ] 每条 spec 验收标准都映射到至少一条具体测试用例。
- [ ] 没有空跑断言（`assert True`、断言任意 != None 等）。
- [ ] mock 范围与 `coding-style.md` §1.7 一致（数据访问层禁 mock）。
- [ ] 测试名能反映场景，不是 `test_1` `test_a`。

### 2. 标注分级

每条问题打标签：

- **MUST FIX**：阻塞通过；必须在下一版关闭。
- **SHOULD FIX**：强烈建议；如不修必须在 `summary.md` 写明 deferred 原因和跟进点。
- **NICE TO HAVE**：可选改进；不阻塞。

每条问题必须包含：

- 出现位置（文件路径 + 行号或章节）。
- 问题描述（一句话讲清楚）。
- 建议改法（一句话，可以是方向不必精确到代码）。

### 3. 给 verdict

- `APPROVED`：可以进入下一阶段。
- `REVISION REQUIRED`：必须修后再评审一轮。

verdict 唯一判据：是否还有未关闭的 MUST FIX。

### 4. 写 review 报告

按对应模板：

- `request_analysis/review/spec_review_v{N}.md`
- `request_analysis/review/tasks_review_v{N}.md`
- `unit_test/review/test_review_v{N}.md`

报告末尾必须有"复检指引"：列出 Generator 修完后**怎么自查**（运行什么命令、查什么字段）。

### 5. 更新 summary.md

- 在对应阶段 review 子项下追加：`v{N}`、verdict、MUST FIX 数量、报告路径。
- 不修改 Generator 的产出文件本身。

## 质量门禁

```text
review 报告存在
报告包含必填章节：检查清单结论 / 分级问题列表 / verdict / 复检指引
verdict ∈ {APPROVED, REVISION REQUIRED}
verdict == APPROVED 时：MUST FIX 数 == 0
```

## 失败回退（你自己做的评审被打回时）

- 上游 Generator 抱怨标准不一致 → 检查是否真的越界做了 NICE TO HAVE 的强制要求；如否，在 review 中给出依据（rule 文件章节 / 历史 review）。
- 同一 MUST FIX 被反复打回 3 次以上 → 提示组织召集面对面对齐；这种情况通常是底层共识缺失。

## 反模式

- **既改产物又评审**——本质失效。
- 评审只写"看起来不错"或"建议优化命名"，没有引用任何规则或验收标准。
- 把 NICE TO HAVE 当 MUST FIX 阻塞流程。
- 给 verdict 但不留 MUST FIX 关闭判据。
- review_v2 直接改 v1 文件，丢失历史。
