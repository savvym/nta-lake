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

8. **AC 验证命令必须真跑过 dry-parse**（rq-worker-skeleton stage 2 反哺；checklist 第 3 条的执行加强）：第 3 条"AC 验证命令一行式"只是 grep 形态匹配；但**形态合法不代表语法合法**——典型陷阱：
   - Python 复合语句嵌 `;`：`python -c "import x; for m in [...]: assert ..."` 会 SyntaxError，因为 `for` 不能跟在 `;` 后（compound statement 必须独立行 / 用 `exec()`）
   - 改用 generator：`assert all(hasattr(X, m) for m in [...])`
   - 或用 `\n` 真换行：`python -c "import x$(printf '\nfor m in [...]:\n    assert ...')"`（更丑）
   - 验证：每条新写的 AC 验证命令，generator 必须把命令复制到本地 shell 真跑一次（即便目标文件还不存在——`ModuleNotFoundError` 是预期的；SyntaxError 不是）；或至少用 `python -c "<cmd>"; echo $?` 看是否 syntax-valid。
   - 类似坑还有：未转义引号（spec 用 `"..."` 嵌 `"..."`）；未引用的 shell glob；未 quote 的 `$` 变量。
   - Generator 自查：把所有 `uv run python -c` / `bash -c` 命令收集 → 用 `bash -n -c "$cmd"` 或 `python -c "compile($cmd, '', 'exec')"` 做 dry-parse；命令报 SyntaxError → spec MUST FIX。

9. **summary.md frontmatter 必须在 stage 1 启动时就填好**（processor-framework stage 0 反哺）：典型陷阱——generator 把 spec.md / tasks.md 写好就直接进 stage 3 写代码，summary.md 一路停留在 `_template/summary.md` 模板（`change_id: <feature-slug>-<yyyymmdd>` / `stage: request_analysis` / `last_updated: <YYYY-MM-DDTHH:MM:SSZ>`），导致：
   - SSoT 漂移：summary.md 名义上是 Single Source of Truth，但实际状态在 spec/coding/test 各文件零散
   - stage 推进失序：reviewer 无法从 summary 表知道当前应该看哪个产物
   - close 时一次性补 9 个文件（tasks_review / coding_report / code_review / test_report / test_review / ci / deploy / summary），评审品质打折
   - 防复发：进入 change 目录的**第一动作**是改 summary.md frontmatter（change_id / title / owner / started_at / stage=request_analysis / status=in_progress / last_updated），然后才开始写 spec.md。每完成一个阶段，**同一次编辑**里更新 summary.md 阶段进度表 + last_updated。
   - Generator 自查：`grep -c "<feature-slug>\|<YYYY-MM-DDTHH:MM:SSZ>\|<复述\|<bullet list>" summary.md` → 必须为 0（即没有任何模板占位符残留）；spec_review reviewer 必须先 cat summary.md frontmatter 才能开始评审。

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
# 8. AC 验证命令 dry-parse（rq-worker-skeleton 反哺）
# 抽出所有 python -c 命令，逐一 compile dry-parse；语法非法 → MUST FIX
grep -oE 'python -c "[^"]+"' spec.md | while read cmd; do
  payload=$(echo "$cmd" | sed -E 's|^python -c "||; s|"$||')
  python -c "compile(r'''$payload''', '<ac>', 'exec')" || echo "SyntaxError: $cmd"
done
# 9. summary.md 模板占位符残留检查（processor-framework 反哺）
grep -cE "<feature-slug>|<YYYY-MM-DDTHH:MM:SSZ>|<复述|<bullet list>" summary.md  # 期望 = 0
```

跨 AC 矛盾是 spec generator 最高频的失败模式，**比"没写测试" 更隐蔽 + 更致命**——它通过了语法检查但在 stage 3 实现期才暴露，回退成本最高。第 5~7 条来自 adapter-framework v1 stage 2 review 实证；其中第 6 条是 [project-followup-harness-lint] 累积 5 次预警后的第 6 次同型 bug，必须重视。第 8 条来自 rq-worker-skeleton v1 stage 2 反哺（AC-4 Python 复合语句 SyntaxError）——形态合法 ≠ 语法合法，generator 必须真跑 dry-parse。

## AC 分层规约（harness-ac-behavioral-tier-20260518 反哺）

`pipeline-orchestrator-mvp-20260518` stage 9 第一次真跑端到端 demo 暴露 3 个真 bug：demo recipe 字段名误用（grep 命中 PASS、`load_recipe` 直接挂）、`test_cache_hit_*` fixture 撞 hash、`pipeline_cache` FK 缺 CASCADE。直接根因：**self_check 226/226 PASS 是 grep 假象**——大量 AC 用 `grep` / `test -f` / `uv run python -c "import X"` 类静态检查，能证明源码骨架存在，但无法证明业务路径真跑通。

本段把 AC 升级为分层（static / behavioral），让 self_check "全 PASS" 不再是 grep 假象——同 `harness-reviewer-agent-separation-20260518` 模式：先在 SKILL 加规约，再用 `scripts/_self_check.sh` 加 `run_ac_kind_lint` global function 机械化守门，与 `run_reviewer_lint` 协同。

### kind 字段二分定义

`spec.md` 验收标准表每条 AC 必须有 `kind` 列，值二选一：

- **`static`**：源码骨架检查。命令形态：`grep`、`test -f`、`ls`、`uv run python -c "import X"`、`tomllib.load`、`json.load` 等纯 parse / 文件存在性 / 字面命中检查。**不真跑业务路径**。
- **`behavioral`**：真跑代码并断言行为。

不引入 `mixed` 第三类——混合型 AC 必须拆为两条独立 AC（见下方"混合型拆分示例"）。

### behavioral 三层判定

`behavioral` AC 三层（任一即可，不强求"必须 L1"）：

| 层级 | 形态 | 例子 |
|---|---|---|
| L1 | 真起服务 curl smoke（含部署面） | `curl -X POST http://localhost:8080/repos ... → 201`；适用 stage 9 deploy_verify |
| L2 | ASGITransport in-process roundtrip（含路由） | `httpx.AsyncClient(transport=ASGITransport(app=app)).post(...)`；现有 apps/api/tests 大量用此模式，**是事实标准** |
| L3 | load_recipe / pydantic parse / bash fixture 真跑断言（含纯逻辑） | `from dataplat_api.schemas.pipeline import load_recipe; load_recipe(yaml_text)`；或 `bash scripts/lint/test_*.sh` 真跑脚本断言；适用纯 Python / 纯脚本路径 |

不算 behavioral 的（明确反例）：

- `uv run python -c "import dataplat_api.foo"` —— 仅验证 import 成功，不调用业务函数。
- `grep "@router.post" routers/foo.py` —— 仅验证路由定义存在，不打实际请求。
- `test -f tests/test_foo.py` —— 仅验证测试文件存在，不跑测试。

### 硬约束

**每个非豁免 change 至少 1 条 `kind: behavioral` AC**。stage 2 reviewer 必查（详见 `.harness/skills/expert-reviewer/SKILL.md` § "stage 2 AC kind 字段必查"），违反者 MUST FIX。

机械化守门：`scripts/_self_check.sh::run_ac_kind_lint` 扫所有未豁免 change 的 `spec.md`，**双条件断言**：

1. AC 表头含 `kind` 列：`grep -qE '^\|[^|]*\|[[:space:]]*kind[[:space:]]*\|' <段>`
2. 至少 1 行 AC 的 kind 单元格真值为 `behavioral`（**锚定 AC 行 regex，不接受裸字串 grep**，避免被 AC 描述里 "behavioral" 字串误命中）：`grep -qE '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|' <段>`

任一不满足 → 整个 lint FAIL。

### 豁免清单（grandfather 期）

`harness-ac-behavioral-tier-20260518` close 时硬编码 19 个历史 closed change，**分两类**：

**永久豁免（2 个，"纯 harness/纯文档" change，无 dataplat 实代码）**：

- `harness-bootstrap-20260516`
- `harness-reviewer-agent-separation-20260518`

**暂豁免 grandfather（17 个，实代码 change，仅因历史原因暂豁免，必须 backfill）**：

- `bootstrap-monorepo-20260516`
- `core-domain-model-20260516`
- `cas-storage-20260517`
- `auth-scaffold-20260517`
- `repo-api-mvp-20260517`
- `commit-api-mvp-20260517`
- `rq-worker-skeleton-20260517`
- `processor-framework-20260517`
- `adapter-framework-20260517`
- `llm-gateway-mvp-20260517`
- `adapter-firecrawl-20260517`
- `llm-qa-gen-20260518`
- `web-mvp-pages-20260517`
- `web-write-flows-20260517`
- `repo-files-tab-20260517`
- `sdk-cli-mvp-20260518`
- `pipeline-orchestrator-mvp-20260518`

**注意**：`harness-ac-behavioral-tier-20260518` 自身**不**在豁免清单（meta-change 制定者也走 dogfood，自带 ≥2 条 behavioral AC = AC-4 + AC-8）；未来新 change 默认也不豁免。

后续 follow-up `harness-ac-kind-backfill-*` 标 **P1**（下个非紧急 sprint），不允许无限 deferred。

### 自声明豁免（`ac_kind_lint: exempt`）

新 change 如果**确实**是纯文档 / 纯 harness / 纯 wiki / 纯 scripts 改动，可在 `spec.md` frontmatter 加：

```yaml
---
change_id: <id>
version: 1
authored_at: <ISO8601>
status: draft
ac_kind_lint: exempt           # 自声明豁免（必须附理由 + 通过 reviewer git diff 复核）
ac_kind_lint_exempt_reason: |
  纯 harness 变更（仅改 .harness/* + scripts/*）；
  通过 reviewer 跑 git diff --stat origin/main..HEAD 验证。
---
```

### 豁免判定标准（reviewer 复核）

stage 2 reviewer 复核 `ac_kind_lint: exempt` 自声明时必跑：

```bash
git diff --stat origin/main..HEAD | awk '{print $1}'
```

声明合法当且仅当：**所有改动文件 path 满足以下任一前缀**：

- `.harness/*`
- `wiki/*`
- `scripts/*`（含 `scripts/lint/*`）
- `*.md`（README / CLAUDE / 文档）

任一文件不满足 → reviewer MUST FIX（"声明 exempt 但有非豁免范围改动"）。reviewer 必须把 `git diff --stat` 输出**粘贴到 review 文件**。

无 remote 项目（本仓库当前情况）：用 `git log --stat <baseline-commit>..HEAD` 等价。

### 混合型 AC 拆分示例（伪代码）

混合型 AC 必须拆为两条独立 AC，避免一条 AC 同时承载"骨架检查 + 行为断言"两种意图。示例：

**原（错误）**：

```markdown
| AC-N | mixed/不写 | POST /repos 返回 201 + 路由文件含 @router.post(/repos) | curl + grep | 201 + grep 命中 |
```

**改（正确，拆为两条）**：

```markdown
| AC-Na | static | 路由文件含 @router.post(/repos) | `test -f routers/repos.py && grep -q "@router.post.*\"/repos\"" routers/repos.py` | grep 命中 |
| AC-Nb | behavioral | POST /repos 用 bronze layer 返回 201 + repo_id | `uv run pytest -q apps/api/tests/test_repos.py::test_create_201`（ASGITransport L2） | pytest passed |
```

拆分判定：如果 AC 描述含"且 / 同时 / + ... + "等连接词，且两侧分别是 static / behavioral 形态，则必须拆。

### 与其他 lint 的关系

`run_ac_kind_lint` 与 `run_reviewer_lint` 同型协同（都是 global function、fail-fast、对外 1 个 run_ac 计数）：

- `run_reviewer_lint`：守门评审者独立性（防止 self-review）
- `run_ac_kind_lint`：守门验收标准真实性（防止 grep 假象）

合在一起：spec generator 写不出"骗 AC"的 spec、reviewer 不能"骗 review"——两道机械门。
