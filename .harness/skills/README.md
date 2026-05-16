# Skills 索引

Skills 是可复用 SOP，把团队隐性知识显性化。**按阶段加载，不要全量加载**。

| Skill | 用途 | 主要使用阶段 |
|---|---|---|
| [request-analysis](request-analysis/SKILL.md) | 把模糊诉求转成 spec+tasks | 阶段 1：需求分析 |
| [coding-skill](coding-skill/SKILL.md) | 按 spec/tasks 实现代码 | 阶段 3：编码实现 |
| [expert-reviewer](expert-reviewer/SKILL.md) | 计划/产物的独立评审 | 阶段 2、6（plan 模式 / review 模式） |
| [unit-test-write](unit-test-write/SKILL.md) | 改动驱动的单测编写 | 阶段 5：单测编写 |
| [unit-test-ci](unit-test-ci/SKILL.md) | CI 结果收集与门禁判定 | 阶段 8：CI 验证 |
| [deploy-verify](deploy-verify/SKILL.md) | 部署后行为验证与证据归档 | 阶段 9：部署验证 |
| [code-review](code-review/SKILL.md) | 代码实现的独立评审 | 阶段 4：编码评审 |
| [project-analysis](project-analysis/SKILL.md) | 项目结构 / 链路 / 依赖梳理 | 不定期；新成员上手、重大重构前 |
| [ci-generate](ci-generate/SKILL.md) | 生成/维护 CI 配置 | CI 配置变更子变更 |

## Skill 之间的关系

```
request-analysis ──产出 spec/tasks──▶ expert-reviewer (plan 模式)
                                         │ APPROVED
                                         ▼
                              coding-skill ──产出代码──▶ code-review
                                                          │ APPROVED
                                                          ▼
                                     unit-test-write ──产出测试──▶ expert-reviewer (review 模式)
                                                                     │ APPROVED
                                                                     ▼
                                                              unit-test-ci ──产出 ci_result──▶ deploy-verify
```

`project-analysis` 与 `ci-generate` 是**支援型** Skill，可在主流程之外独立触发。

## 写新 Skill 的约定

新增 Skill 必须遵循模板（参见任一现有 SKILL.md）：

1. **YAML 前言**：name / description / applicable_stage / inputs / outputs。
2. **必备章节**：进入条件、输入、步骤、产出、质量门禁、失败回退。
3. **门禁可机械化**：列出至少一条可程序检验的标准。
4. **不可复用就不要做 Skill**——单次性流程直接在 change 里写说明即可。
