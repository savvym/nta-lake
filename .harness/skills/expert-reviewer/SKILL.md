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

## reviewer 字段填写规约（**硬约束**）

> 本节由 harness-reviewer-agent-separation-20260518 引入，对应实证：本会话连续 7 个变更全部 `reviewer: application-owner-agent` 违反了本文开头 "评判者必须是独立子会话或独立 Agent" 硬约束。本节把规约**机械化**——`scripts/_self_check.sh` `run_reviewer_lint` 硬 FAIL 守门。

### 白名单（合法值）

| 形态 | 例 | 含义 |
|---|---|---|
| `claude-agent:<change-id>-stage{N}-reviewer-v{M}` | `claude-agent:harness-reviewer-agent-separation-stage2-reviewer-v1` | 真 spawn 的独立 reviewer 子 agent ID；推荐路径 |
| `self-attest (<理由>)` | `self-attest (会话级授权偏离 #1；2026-05-17/18 用户授权 "你合理安排规划" 省 spawn 成本)` | 显式偏离声明；括号文案必填，含具体理由 / change 路径 / 时间 |

### 黑名单（禁止值；self_check 硬 FAIL）

| 形态 | 为什么禁止 |
|---|---|
| `application-owner-agent` / `application-owner` | 等价 self-review，违反"评判者必须独立"硬约束 |
| `claude` / `agent` / 空 | 不可识别身份 |
| `<name 或 agent id>` 等模板占位符 | template 未填，等价未评 |
| `self-attest`（无括号文案） | 偏离未说明理由，无可追责性 |

### Application Owner 怎么 spawn

详见 `.harness/agents/application-owner.md` § 7.5 "如何 spawn reviewer 子 agent" + `.harness/agents/reviewer-agent.md` § 模型选择。模板示例（**默认 sonnet** 硬约束）：

```python
Agent(
    subagent_type="general-purpose",
    model="sonnet",
    description="<stage> reviewer for <change-id>",
    prompt="""你是 stage {N} 独立 reviewer 子 agent v{M}...
    reviewer 字段固定为：claude-agent:<change-id>-stage{N}-reviewer-v{M}
    ...""",
)
```

### self_check 守门

`bash scripts/_self_check.sh reviewer-lint`：

- 反向 grep：`! grep -rE "^reviewer:[[:space:]]+application-owner-agent" .harness/changes/`
- 反向 grep：`! grep -rE "^reviewer:[[:space:]]+<" .harness/changes/ --exclude-dir=_template`
- 白名单校验：所有 `reviewer:` 字段以 `claude-agent:` 或 `self-attest (` 起头

FAIL 立 exit 1，阻止其他 block 跑。

## stage 2 AC kind 字段必查（**硬约束**）

> 本节由 `harness-ac-behavioral-tier-20260518` 引入，对应实证：`pipeline-orchestrator-mvp-20260518` stage 9 第一次真跑端到端抓到 3 个真 bug（demo recipe 字段名 / fixture 撞 hash / FK 缺 CASCADE），证明 self_check 226/226 PASS 是 grep 假象。本节把 AC 分层规约的 reviewer 复核**机械化**——`scripts/_self_check.sh::run_ac_kind_lint` 与本节互锁。

### 必查 3 项

reviewer 评 stage 2 spec.md 时**必须**核对以下 3 项；任一不满足 → MUST FIX：

1. **AC 表存在 `kind` 列**：用 `awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' spec.md | grep -qE '^\|[^|]*\|[[:space:]]*kind[[:space:]]*\|'`。
2. **至少 1 行 AC 的 kind 单元格真值为 `behavioral`**：用 `awk ... | grep -qE '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|'`。**不接受裸字串 `grep -q behavioral`**——会被描述里 "behavioral 三层" 等字串误命中，机械化保护失效。
3. **若 spec frontmatter 声明 `ac_kind_lint: exempt`**：reviewer **必跑** `git diff --stat origin/main..HEAD` 并**把结果粘贴到 review 文件**，验证所有改动文件 path 仅在 `.harness/*` / `wiki/*` / `scripts/*` / `*.md` 范围内。任一文件不满足 → MUST FIX（"声明 exempt 但有非豁免范围改动"）。

详细规约见 `.harness/skills/request-analysis/SKILL.md` § "AC 分层规约"。

### MUST FIX 模板措辞

```markdown
| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-K | spec.md AC 表 | AC 表缺 `kind` 列（或所有 AC kind=static，违反"每个非豁免 change 至少 1 条 behavioral AC"硬约束） | 加 `kind` 列；至少 1 条 AC 设计为 `kind: behavioral`（ASGITransport / pytest 集成 / load_recipe / curl smoke 任一）。详 `.harness/skills/request-analysis/SKILL.md` § "AC 分层规约" |
| MUST FIX-K | spec.md frontmatter ac_kind_lint: exempt | 声明 exempt 但 git diff --stat 显示 `apps/api/dataplat_api/foo.py` 等非豁免范围改动 | 删除 frontmatter `ac_kind_lint: exempt` 字段；按正常规约补 ≥1 条 behavioral AC。或缩范围只在豁免目录改动 |
```

### self_check 守门

`bash scripts/_self_check.sh ac-kind-lint`：

- 对所有未豁免 change 跑双条件断言（kind 列存在 + AC 行 kind=behavioral 锚定 regex）
- 永久豁免 2 个 + grandfather 暂豁免 17 个（详 `.harness/skills/request-analysis/SKILL.md` § "豁免清单"）
- 自声明 `ac_kind_lint: exempt` 通过 frontmatter 解析跳过 lint，但 reviewer 必查 git diff（本 SKILL 上方第 3 项）
- FAIL 立 exit 1，阻止其他 block 跑
