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

## 跨 AC 一致性自审清单（commit-api-mvp 反哺 + adapter-framework 扩充）

generator 提交 spec v1 前必须自查的一致性链路。原 commit-api-mvp v1 出现 `created_at` 进 hash 但 schema 不含、AC-8 vs 风险 #3 事务边界措辞相反 → checklist 第 1~4 条。adapter-framework v1 又暴露 orphan commit + 反向 grep 沉默通过两个新模式 → 扩充第 5~6 条 + 第 7 条 process_tasks 完整性。

1. **schema 字段 ↔ canonical hash 输入 ↔ idempotency key ↔ test fixture 四链路必须一致**：
   - 若某字段进入 hash 公式，要么它在 Create schema 里 client 可控，要么 hash 公式不含它。
   - 端到端幂等测试 payload 字段集合必须 = hash 公式输入集合。
   - 测试 fixture 不能引入参与 hash 计算的不确定字段（如服务端 `utcnow()`）。

2. **事务边界声明在 AC + 风险 + tasks 三处必须一字不差**：若 AC 写"事务内校验"而 风险 / tasks 写"事务前校验"，coding 阶段实现者会困惑——generator 必须 grep 自查。

3. **AC 验证命令一行式可执行**：每条 AC 必须能放进 `scripts/_self_check.sh` 跑（`uv run python -c "..."` / `bash -c "..."` / `test -f ...`）。一行无法表达的复杂 assertion，应归并到集成测试 AC by 引用——不在 AC 本体堆段落。

4. **风险缓解 ↔ AC 测试列表**：每条风险若声称有"测试覆盖"作为缓解，必须在 AC 测试列表里列出对应测试编号；否则缓解措施未落地。

5. **commit 历史链连续性**（adapter-framework v1 反哺）：任何"自动产 commit"路径若涉及更新 ref，必须明示 `parents` 怎么算（client 显式 / ref-current-commit 自动接 / orphan 显式 accept）。**写死 `parents=[]` + 更新 ref = orphan commit + 历史链断裂**，违反 design.md §4.4 类 Git 语义；spec 必须有"二次写形成父子链"测试。Generator 自查 `grep -nE "parents=\[\]" spec.md` 命中处必须每处都有 accept 或 follow-up 说明。

6. **反向 grep 必须配 `test -f` 前置 + 正向断言 + 不吞 stderr**（[project-followup-harness-lint] 第 6 次证据 / adapter-framework v1 反哺）：AC 验证里出现 `! grep ...` 形式时，若目标文件 / 目录在 T-* 实现前不存在，grep 退码 2 被 `!` 反转 → AC 在零代码状态下"通过"。**修复模板**：
   ```bash
   test -f <target_file> \
     && grep -q "<positive assertion>" <target_file> \
     && ! grep -rE "<negative pattern>" <target_dir>
   ```
   要求：(a) `test -f` 前置确保目标文件存在；(b) 正向 grep 证明真复用/真实现了预期；(c) 不写 `2>/dev/null` 吞 stderr——让路径错误暴露。

7. **process_tasks 6 条必填**（adapter-framework stage 2 反哺，系统性遗漏；既有 7/8 change 仅 commit-api-mvp 有 1 个）：tasks.md 不仅列实现任务 T-*，还必须列 6 个 process 节点对应 stage-2/4/6/7/9/10：
   - stage-2 spec/tasks review
   - stage-4 coding review
   - stage-6 test_report + unit-test review
   - stage-7 CI 验证
   - stage-9 deploy verify（即便 noop 也要显式 task）
   - stage-10 close + 反哺 SKILL（如有）
   - Generator 自查：`grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" tasks.md` 期望 ≥ 6。

generator 提交前 grep 自查（按需扩充）：

```bash
# 1. 跨 AC 矛盾词
grep -nE "事务内|事务前|事务外" spec.md
# 2. hash 输入字段 vs schema 字段
grep -nE "created_at|canonical|hash" spec.md
# 3. 每条 AC 是否有一行式验证命令
grep -cE "uv run python -c|test -f|bash scripts" spec.md  # 期望 ≥ AC 总数 × 0.5
# 4. 风险缓解 ↔ AC 测试
grep -A1 "缓解" spec.md | grep -E "AC-|测试 \([a-z]\)"
# 5. commit parents 写死检查
grep -nE "parents=\[\]" spec.md     # 命中处必须每处有 accept/follow-up 说明
# 6. 反向 grep 沉默通过检查
grep -nE "! *grep" spec.md          # 命中处必须配 `test -f` 前置 + 不吞 stderr
grep -nE "2>/dev/null" spec.md      # AC 验证命令不许吞 stderr
# 7. process_tasks 6 条必填
grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" tasks.md  # 期望 ≥ 6
```

跨 AC 矛盾是 spec generator 最高频的失败模式，**比"没写测试" 更隐蔽 + 更致命**——它通过了语法检查但在 stage 3 实现期才暴露，回退成本最高。第 5~7 条来自 adapter-framework v1 stage 2 review 实证；其中第 6 条是 [project-followup-harness-lint] 累积 5 次预警后的第 6 次同型 bug，必须重视。
