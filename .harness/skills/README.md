# Skills 索引（v2，2026-05-20 三阶段流程下精简）

> v2 三阶段流程下 skill 大幅精简。绝大多数旧 skill 已 DEPRECATED（保留只为历史 change 引用），新 change 只需要加载下方"现役" skill。

## 现役 Skills

| Skill | 用途 | 主要使用阶段 | 谁加载 |
|---|---|---|---|
| [request-analysis](request-analysis/SKILL.md) | 把模糊诉求转成 design.md（spec+tasks 合并） | Phase 1 Design 产物 | application-owner (opus) |
| [expert-reviewer](expert-reviewer/SKILL.md) | 独立评审（两种模式：Design Review / Verify Review） | Phase 1 Reviewer / Phase 3 Reviewer | spawn opus reviewer |
| [coding-skill](coding-skill/SKILL.md) | 编码 + 测试 + 端到端验证（v2 下合并到 Phase 2） | Phase 2 Implementer | spawn sonnet implementer |

## Deprecated Skills（保留历史引用，不要新加载）

> 以下 skills 在 v1 时代独立存在，v2 后职责并入 Phase 2 sonnet implementer 端到端或 Phase 1/3 expert-reviewer 两种模式：

| Skill | 状态 | 替代 |
|---|---|---|
| `unit-test-write` | DEPRECATED | Phase 2 sonnet 端到端做 |
| `unit-test-ci` | DEPRECATED | Phase 2 sonnet 端到端做 |
| `deploy-verify` | DEPRECATED | Phase 2 sonnet 端到端做（含 curl smoke / vite build） |
| `code-review` | DEPRECATED | Phase 3 expert-reviewer (Verify Review 模式) |
| `ci-generate` | DEPRECATED | 一次性配置，不再作 skill；需要时直接改 .github/workflows |
| `project-analysis` | DEPRECATED | 用 Agent 工具 subagent_type=Explore / general-purpose 临时调研 |

## Skill 之间的关系（v2）

```
Phase 1 Design                Phase 2 Implementation        Phase 3 Verify
─────────────────             ──────────────────────        ───────────────
application-owner (opus)      spawn sonnet implementer      spawn opus reviewer
+ request-analysis SKILL      + coding-skill SKILL          + expert-reviewer SKILL
       │                              │                            │
       ▼                              ▼                            ▼
design.md                      implementation.md             verify_review.md
       │                              │                            │
   spawn opus reviewer            (含 PR)                       APPROVED
   + expert-reviewer SKILL                                          │
   ▼                                                                ▼
design_review.md                                              merge + close
```

## 写新 Skill 的约定

新增 Skill 必须遵循模板（参见任一现有 SKILL.md）：

1. **YAML 前言**：name / description / applicable_phase / inputs / outputs
2. **必备章节**：进入条件、输入、步骤、产出、质量门禁、失败回退
3. **门禁可机械化**：列出至少一条可程序检验的标准
4. **不可复用就不要做 Skill**——单次性流程直接在 change design.md 里写说明

## v1 引用

23 个 v1 时期 change 的 spec.md / coding_report.md 仍引用 deprecated skill 文件名（如 `code-review`）。**保留**这些 skill 文件不删，新 change 用现役清单。
