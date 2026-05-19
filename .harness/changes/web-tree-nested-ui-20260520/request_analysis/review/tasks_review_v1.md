---
change_id: web-tree-nested-ui-20260520
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-agent:web-tree-nested-ui-20260520-stage2-reviewer-v1
reviewed_at: 2026-05-19T17:30:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v1

## v0 MUST FIX 复检

无上一轮，跳过。

---

## 检查清单结论（plan 模式）

| 项 | 状态 | 说明 |
|---|---|---|
| 每个任务粒度合理（1-3 小时） | PARTIAL - 见 MUST FIX-1 | T-3 含 6 个子功能点，超出 1-3h 粒度 |
| depends_on 形成 DAG，没有循环 | PASS | T-1→T-2→T-3→T-4→T-5→T-6 线性链，无环 |
| 评审 / 单测 / CI 阶段对应任务都存在 | PASS | process_tasks 含 P-spec-review / P-code-review / P-test-review / P-push / P-ci / P-deploy / P-user-confirm |
| 没有 "做完整个系统" 类目标性任务 | PASS | 每个任务都指向具体文件和操作 |
| AC 覆盖完整（每条 AC 有对应任务） | PARTIAL - 见 MUST FIX-2 | AC-8 只被 T-6 覆盖，T-6 是 ci_result 阶段但 AC-8 是 lint/typecheck；AC-9 只映射到 "stage 10 用户实测" 但无 task ID |
| estimated_stage 与十阶段定义对齐 | PARTIAL - 见 SHOULD FIX-1 | T-5/T-6 标 ci_result 但 T-5 是 self_check 脚本属 coding 阶段产物 |

---

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | tasks.md T-3 | T-3 "FilesSection 改造为 HF 风" 包含：面包屑渲染、返回上一级按钮、type=tree 行 folder icon + click handler、type=blob 行保留现有 Link、loading/error/空 tree 三种状态、error from useSubtreeByPath 错误 UI + "返 root" 按钮，合计 6 个独立子功能点。按每任务 1-3h 标准，此任务预计需要 5-8h，超过 Quality Gate 上限。超大任务在 code review 时难以逐一核对覆盖，且一旦某子功能出错，整个 T-3 会被打回导致全部子功能返工。 | 将 T-3 拆分为至少 2 个任务：(a) T-3a 路由 search 接入 + useSubtreeByPath 调用 + loading/error/空 tree 状态（数据层改造）；(b) T-3b 面包屑组件 + folder/blob 行渲染 + click handler + 返 root 按钮（表现层改造）。两者均 depends_on T-2，T-3b depends_on T-3a。 |
| MUST FIX-2 | tasks.md 验收覆盖表 | AC-9 在覆盖表中标为 "stage 10 用户实测"，但 tasks.md 中无对应 task ID（既无 T-x covers_ac [AC-9]，也无 process_task）。流程要求每条 AC 在任务拆解中有归宿，否则 coding agent 不知道谁负责 AC-9 的实现。若 AC-9 是 stage 10 process task，需要在 process_tasks 里加一条 `id: P-user-confirm-ac9`，或在 P-user-confirm 的 description 里明写 "验证 AC-9"。 | 在 process_tasks 中 P-user-confirm 条目加 `covers_ac: [AC-9]`，并在 T-4 或 T-6 的 covers_ac 里确认 AC-9 的行为被手测覆盖路径；或若 AC-9 按 MUST FIX-1（spec_review）改为 process 类型，则从 AC 编号表中移除，更新覆盖表。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | tasks.md T-5 estimated_stage: ci_result | T-5 是向 `scripts/_self_check.sh` 添加 12 个 AC block 的 coding 工作，产物是脚本代码修改，按十阶段定义属于 **coding（阶段 3）** 的一部分，不是 ci_result（阶段 8）。标错 estimated_stage 会让 coding agent 误以为此任务在阶段 8 才做，导致阶段 3 产物不完整（_self_check.sh 未注册新 block 时 `bash scripts/_self_check.sh current` 只能 SKIP 而不能校验）。 | 将 T-5 的 estimated_stage 改为 `coding`；T-5 的 depends_on 保留 T-4（需先有测试才能确认 block 内容正确）。 |
| SHOULD FIX-2 | tasks.md T-2 description | T-2 写 "tab 切换时保留 path（或重置到 ""），看交互期望"，交互期望未定。spec_review SHOULD FIX-4 要求 spec 明确此行为，但 tasks.md 也需对应更新——目前 coding agent 在 T-2 时遇到此歧义会随机选择。 | 待 spec v2 明确 tab 切换 path 行为后，T-2 description 中同步更新，删除 "看交互期望" 歧义语。 |
| SHOULD FIX-3 | tasks.md T-4 description | T-4 的 5 个用例命名格式为 `test_default_root_shows_mixed_entries` 等下划线风格。查看现有测试基线 `repos.files-section.test.tsx`，使用的是 `it("renders main badge + file count...")` 的 describe/it 风格（camelCase 描述字符串）。任务描述中的测试命名格式与现有基线不一致，会让 coding agent 写出风格割裂的测试。 | 将 T-4 用例名改为 vitest it/describe 风格（如 `it('root shows mixed entries, including folder icon and blob rows', ...)`），与现有基线保持一致。 |
| SHOULD FIX-4 | tasks.md T-4 mock 策略 | T-4 description 写 "mock useSearch + useSubtreeByPath（或直接 fetch fixture）"，两种 mock 策略并存。现有基线 (`repos.files-section.test.tsx`) 采用 `vi.mock('../lib/api/queries', ...)` 整体 mock hook；T-4 如果改用 fetch fixture（MSW 或 `fetchMock`），需要引入额外测试基础设施。不明确选哪种策略会让 coding agent 做出与 codebase 不一致的选择。 | 明确 T-4 复用现有 `vi.mock('../lib/api/queries', ...)` 策略，mock `useSubtreeByPath` 返回受控 fixture；不引入 MSW 等新基础设施（除非 spec 另有说明）。 |
| SHOULD FIX-5 | tasks.md T-6 covers_ac | T-6 标 `covers_ac: [AC-7, AC-8, AC-11]`，但 AC-8 的执行命令在 T-6 description 中的第一行（`pnpm --filter web lint && pnpm --filter web typecheck`）。AC-8 同时也在 T-5 的 scripts/_self_check.sh 注册中被 block 覆盖；但 T-5 的 `covers_ac` 只列了 AC-10/AC-12，未列 AC-8。AC-8 由谁"主负责"不清晰。 | 确认 AC-8 的主负责任务：若 T-6 主负责，T-5 只是把命令注册到 self_check，则 T-6 覆盖 AC-8 是对的，无需改；但需删除 T-5 的隐含 AC-8 覆盖歧义（T-5 description 中提到 `AC-8 跑 pnpm lint + typecheck`）。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | tasks.md DAG | 当前 DAG 为完全串行链（T-1→T-2→T-3→T-4→T-5→T-6），无并行机会。T-5（_self_check.sh 改动）与 T-3（FilesSection 改造）实际上都依赖 T-4，但它们互相独立。若改为 T-5 depends_on T-4 而不是 T-3，T-3 和 T-5 可以并行（代码写作时）。不影响正确性，仅影响并行执行效率。 |
| NTH-2 | tasks.md process_tasks | process_tasks 中 P-deploy 的 description 为 "noop（仅前端，无 schema 改动；vite 重 build 即可）"，但 spec §风险 `TanStack Router validateSearch 改动可能破坏 URL 兼容` 提到 path 字段加 default 不带 ?path 的 URL 等价 root。如果 staging 环境有用户书签了某个 ?path=... URL，部署后的兼容性值得在 P-deploy 中留一句验证说明（"验证旧 URL ?path 不存在时路由行为"）。 |
| NTH-3 | tasks.md T-1 description | T-1 写 `enabled: !!commit_hash && /^[0-9a-f]{64}$/.test(commit_hash)`，与现有 `useCommit` 的 enabled 逻辑完全一致（见 queries.ts line 146）。建议提取为共享 helper `isSha256(hash: string)` 以避免在 useSubtreeByPath queryFn 内也重复写同一 regex；tasks.md 可在 T-1 中提示 coding agent 复用或提取。 |

---

## Verdict

**REVISION REQUIRED**

存在 2 条 MUST FIX：
- MUST FIX-1：T-3 超大任务（6 个子功能），超 1-3h 粒度上限，需拆分
- MUST FIX-2：AC-9 在任务拆解中无归宿，覆盖表中只有文字说明无 task ID

SHOULD FIX 5 条，核心是 T-5 estimated_stage 标错（ci_result 应为 coding）、T-2/T-4 存在歧义需与 spec v2 同步修正。

---

## 后续指引

Generator 修完 v2 tasks 后，自查以下内容：

```bash
# 1. 确认所有 task estimated_stage 与十阶段一致
grep -A2 "estimated_stage:" .harness/changes/web-tree-nested-ui-20260520/request_analysis/tasks.md

# 2. 确认每条 AC 在覆盖表有 task 或 process_task 归宿
# 手动检查覆盖表：AC-9 是否有 P- 或 T- 对应

# 3. 确认 DAG 中无遗漏依赖（T-3 拆分后，T-3b depends_on T-3a）
grep "depends_on:" .harness/changes/web-tree-nested-ui-20260520/request_analysis/tasks.md

# 4. 确认每个 task 预计完成时间 ≤ 3h（无超 6 个子功能点的超大任务）
# 手动阅读 description 检查子功能数量

# 5. T-4 mock 策略已明确（选择 vi.mock hook 策略）
grep -A10 "id: T-4" .harness/changes/web-tree-nested-ui-20260520/request_analysis/tasks.md | grep -i "mock"
```

v2 修完后重新 spawn reviewer v2 复检，同时需确认 spec v2 中 MUST FIX-1/2 已关闭（AC-9 定性 + AC-12 去重），tasks v2 中 MUST FIX-1/2 对应修改落实。
