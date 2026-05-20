# 开发流程规则：三阶段（v2，2026-05-20 简化版）

本文件是项目唯一的流程权威。Application Owner Agent 严格按此推进任何变更。

## 为什么从 v1 (10 阶段) 简化到 v2 (3 阶段)

23 个 change 实测后：

- v1 把"需求/编码/单测/CI/部署"各自切出独立 stage + 独立 reviewer + 独立 report，文档开销大、reviewer 调用频繁
- 70% 的 reviewer MUST FIX 集中在 spec 阶段；coding / unit_test 评审多数只抓到 NTH 或 SHOULD FIX
- Doc-only change 跑完 3 个 reviewer 性价比极低

简化决策（2026-05-20 用户授权直接落地，无 change-record-bureaucracy）：

- 把"需求 + 评审"合 → **Phase 1 Design**（opus 出方案 + opus reviewer 把关）
- 把"编码 + 单测 + 端到端验证 + push + PR"合 → **Phase 2 Implementation**（sonnet 端到端做完）
- 把"PR 复核 + 用户确认"合 → **Phase 3 Verify**（opus reviewer 对照 Phase 1 设计验 PR）

## 总览

```text
Phase 1 Design (opus)  ──→  Phase 2 Implementation (sonnet)  ──→  Phase 3 Verify (opus)
   ↓                            ↓                                     ↓
design.md                  implementation.md                     verify_review.md
design_review.md           (含 PR link)                          ↓
   ↓                            ↓                              merge + close
APPROVED / SMALL /         全部 AC PASS +
BIG REWRITE                端到端验证通过
```

3 个阶段，5 个产物文件，每阶段一次 model spawn。

## 模型分配硬约束

| 阶段 | 主模型 | 为什么 |
|---|---|---|
| Phase 1 Design | **opus** | 设计判断重，需要深度推理 + 架构视野 |
| Phase 1 Reviewer | **opus** | 同上，复审需要至少跟设计同级别的判断力 |
| Phase 2 Implementation | **sonnet** | 执行密度高，速度优先；端到端做完不打断 |
| Phase 3 Reviewer | **opus** | 最终把关，对照原始设计验收 PR 是否落地 |

违反此分配 → 流程失败。

## Phase 1：Design

### 由谁做

Application Owner（即当前会话的主 agent，默认 opus）。

### Entry Criteria

- 用户提出明确诉求（即使只有一两句话）
- 已通过 `bash scripts/harness_new_change.sh <change-id> [title]` 创建 `.harness/changes/<change-id>/`，切到 `change/<change-id>` 分支

### 产物：`design.md`（单个文件，spec + tasks 合并）

强制章节：

1. **一句话目标**（≤ 30 字，复述用户诉求）
2. **背景**（为什么现在做，1-2 段）
3. **范围 / 非范围**（bullet list，非范围列出"不做 X：理由"）
4. **验收标准**（AC 表，至少 1 条 `kind: behavioral`；纯 doc/治理变更可声明 `ac_kind_lint: exempt` + 理由）
5. **任务清单**（粗粒度任务，标 covers_ac）
6. **风险**（risk + 缓解，至少 1 条）
7. **决策日志**（如果是从用户对话沉淀出来的，列时间戳 + 决策点）

### Quality Gate：spawn Phase 1 Reviewer (opus)

Application Owner 完成 design.md 后 spawn **opus reviewer**，prompt 应含：

- 读 design.md
- 验证 AC 是否可机械化（建议 reviewer 真去跑 grep / awk 命令，特别是带 `awk '/start/,/end/'` 类的命令避坑）
- 验证范围与非范围互不冲突 / 不漏
- 验证至少 1 条 behavioral AC（或合规声明 exempt）
- 验证决策日志真实（如有）
- 不允许 reviewer 改 design.md，只能写 `design_review.md`

**Reviewer 三档 verdict**：

| Verdict | 含义 | 后续 |
|---|---|---|
| `APPROVED` | 设计可直接进 Phase 2 | 进入 Phase 2 |
| `SMALL REVISIONS` | 有 MUST FIX 但都是局部修订（typo / AC 命令错误 / 漏 1-2 条非范围）| Application Owner 一轮修订 design.md → **不再 spawn reviewer**，直接进 Phase 2 |
| `BIG REWRITE` | 设计在范围 / 抽象 / 风险上有根本问题 | Application Owner 重写 design.md，**再 spawn 一次 reviewer** |

**反 over-engineering 约束**：reviewer 一次给出**所有** MUST FIX，不允许"v1 修了再说 v2 还有问题"挤牙膏。Application Owner 修完一轮就进 Phase 2。

### Rollback Route

- 用户在 Phase 1 reviewer 之后反悔 → 直接改 design.md + 重写 design_review.md（记录"用户后撤一轮"）
- Phase 2 中途发现设计不对 → 回到 Phase 1 改 design.md + 写 design_review_v2.md 说明改了什么

---

## Phase 2：Implementation

### 由谁做

Application Owner spawn **sonnet** 实现 agent，sonnet **端到端**做完编码 + 测试 + 验证 + PR。

### Entry Criteria

- design.md APPROVED (或 SMALL REVISIONS + 一轮修订完成)
- design_review.md 存在且 verdict ≠ BIG REWRITE

### sonnet 必做事项（在一次 agent 调用内全部完成）

1. **编码**：按 design.md § 任务清单 落实改动
2. **单元测试**：写 pytest / vitest，按 AC 表覆盖 behavioral AC
3. **端到端验证**：
   - 跑 `bash scripts/_self_check.sh <change-id>` → 10/10 PASS（或本 change 实际 AC 数）
   - 跑相关业务测试：`pnpm --filter web test` / `uv run pytest tests/test_<related>.py`
   - 如涉及 UI：本地 curl smoke 验证 API 端点 / dev server 起来验证 import 不挂
4. **修当前 change 引入的 lint / typecheck**：`pnpm --filter web typecheck` + `uv run ruff check` 全过
5. **commit + push**：单一 commit（除非 design 明确分多个），推到 `change/<change-id>` 分支
6. **提 PR**（如 gh 可用）或返回 branch ref + 等同 PR 描述

### 产物：`implementation.md`（单个文件）

sonnet 必填字段：

1. **改动文件清单**（`git diff --name-only main...HEAD` 等同）
2. **任务完成情况**（design.md 每个 task 标 done / partial / deferred + 理由）
3. **测试通过证据**：self_check 输出 / pytest / vitest 末尾 PASS 行
4. **端到端验证证据**：curl 命令 + 200 响应 / vitest snapshot / dev server log 等
5. **偏离 design.md 的地方**（如有，每条带理由）
6. **PR 链接**或 branch HEAD SHA + PR 描述草稿

### Quality Gate（sonnet 自检 + Application Owner 收尾）

- self_check `<change-id>` 全 PASS（FAIL 必须是 pre-existing flake 且在 implementation.md 标注）
- 全 web vitest 不回归 / 全 pytest 当前 module 不回归
- 没有 typecheck / lint 错误
- branch 已 push

### Rollback Route

- 发现 design.md 漏了某个 AC 或漏了某个约束 → Application Owner 改 Phase 1 design.md + 写 design_review_v2 → sonnet 续做
- 测试始终过不了 → 回 Phase 1 重新评估方案

---

## Phase 3：Verify

### 由谁做

Application Owner spawn **opus reviewer**。

### Entry Criteria

- implementation.md 写完
- branch 已 push 且 PR 已开（或等同物：branch ref + PR 描述）
- self_check `<change-id>` PASS

### Phase 3 Reviewer 必做事项

1. **读 design.md**（原始要求）
2. **读 implementation.md**（声称的实现）
3. **读 git diff**：`git diff main...change/<change-id>` 对照实际改动
4. **运行 mechanical 检查**（reviewer 真去跑，不只是看声明）：
   - `bash scripts/_self_check.sh <change-id>`
   - 如涉及 API：用 curl 真打一次新端点
   - 如涉及 UI：检查 vite build 不挂
5. **判断 PR 是否兑现 design**：每条 AC 标 PASS / FAIL / NOT-VERIFIABLE
6. **判断有没有偏离 design.md 且未在 implementation.md § 偏离 处声明**（隐式偏离 = MUST FIX）

### 产物：`verify_review.md`

frontmatter：
```yaml
---
change_id: <id>
reviewer: opus-phase3-reviewer
authored_at: <ISO timestamp>
verdict: APPROVED | MINOR FIX | MAJOR ISSUE
---
```

正文：
- **AC 对照表**：每条 AC PASS/FAIL + 证据命令
- **隐式偏离审计**：implementation.md 没声明的偏离（如有）
- **机械化检查日志**：reviewer 自己跑的命令 + 输出
- **Verdict**

**三档 verdict**：

| Verdict | 含义 | 后续 |
|---|---|---|
| `APPROVED` | PR 兑现 design + AC 全 PASS + 无隐式偏离 | merge to main + close change |
| `MINOR FIX` | 1-3 个小问题（test 漏一个 case / doc 错字 / 1 个文件漏改） | spawn sonnet 一轮修 → **不再 spawn 第二轮 verify**，直接 merge |
| `MAJOR ISSUE` | 多个 AC 没兑现 / 实现跟 design 严重偏离 / 引入回归 | 回 Phase 2 重做，spawn 新 sonnet（带具体修订要求）|

### Rollback Route

- 用户在 Phase 3 之后实测发现问题 → 不开新 change，直接在当前 change 加 `verify_review_v2.md` + sonnet 续做

---

## change 目录结构（新，v2）

```
.harness/changes/<id>-<date>/
├── summary.md          # 3 行阶段表 + meta（封面，永远是 SoT）
├── design.md           # Phase 1 产物（含 spec + tasks）
├── design_review.md    # Phase 1 reviewer 报告
├── implementation.md   # Phase 2 产物（含编码/测试/e2e/PR）
└── verify_review.md    # Phase 3 reviewer 报告
```

5 个文件。**废除** v1 的 `request_analysis/` / `coding/` / `unit_test/` / `ci_result/` / `deployment/` 目录结构。

旧 change（v1 时期的 23 个）保留原结构，**不回写**。

## 何时可以跳过 reviewer？

- **极小变更**（< 3 行代码 + 不动 API / schema / 接口）：可由 Application Owner 自审
- 自审仍要 design.md + implementation.md（即使简短，1 段就够）
- 跳过的 reviewer 文件用 `<file>.md` 含 frontmatter `verdict: self-attest` + 一段理由代替

不允许跳过的情况：
- 涉及 schema 变更 / API 接口变更 / 跨 change 影响
- 涉及违反 `.harness/rules/data-not-code-pivot.md` 任意一条（永不做清单）—— 这种 change 不允许做，reviewer 必查
- 涉及 architecture pivot

## 自检（保留 v1 逻辑）

每个 change 仍要在 `scripts/_self_check.sh` 添加自己的 AC block（如适用）。

- **阶段内快检**：`bash scripts/_self_check.sh quick [change-id]`
- **当前 change 检查**：`bash scripts/_self_check.sh current [change-id]`
- **最终门禁**：`bash scripts/_self_check.sh full`

sonnet 在 Phase 2 完成前必须验证 `bash scripts/_self_check.sh <change-id>` PASS。

## Git 边界（保留 v1 逻辑）

- 每个 change 一个 `change/<change-id>` 分支
- Phase 2 完成时一次 push；Phase 3 APPROVED 后 merge --no-ff 到 main
- 不在 main 直接 commit（除非是当前这种"用户授权绕过流程改 harness 框架本身"的极特殊情况）

## 跨 reviewer 反复迭代的硬约束

为了防止 reviewer cycle 无限拉长：

- Phase 1 reviewer 一次给完**所有** MUST FIX
- Application Owner 修一轮就进 Phase 2，**不允许 spawn Phase 1 reviewer v2**（除非用户明确要求或 verdict 是 BIG REWRITE）
- Phase 3 reviewer 给 MINOR FIX → sonnet 修一轮直接 merge，**不允许 spawn Phase 3 reviewer v2**
- 反复迭代是 v1 时代的失败模式，v2 显式禁止

---

## v1 兼容（仅供历史参考）

23 个 v1 时期 change 的目录结构（`request_analysis/spec.md` + `coding/coding_report_v1.md` + …）保留不动。新 change 一律按 v2 走。

v1 流程文档：`.harness/rules/development-process-v1-deprecated.md`。
