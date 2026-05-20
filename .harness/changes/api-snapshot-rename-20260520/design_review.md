---
change_id: api-snapshot-rename-20260520
phase: design_review
reviewer: claude-agent:opus-phase1-reviewer
model_used: opus
authored_at: 2026-05-20T08:52:29Z
verdict: SMALL REVISIONS
---

# Design Review

> Phase 1 reviewer 产物。本次 reviewer 真去跑了 design.md 全部 12 条 AC 命令，验证语法可执行 + 当前未实现时如预期失败。也比对了 roadmap W1-1 / decisions.md D-1/D-2/D-10/D-11 / data-not-code-pivot 永不做清单。

---

## 1. 结构检查表

| 强制章节 | PASS / FAIL | 备注 |
|---|---|---|
| 一句话目标 | PASS | 22 字 ≤ 30，复述 W1-1 |
| 背景 | PASS | 2 段；交代 v1 22 个 change 闭环但词汇未对齐 + roadmap W1-1 定位 |
| 范围 | PASS | 14 条 bullet，覆盖 api / sdk / web / openapi / self_check |
| 非范围 | PASS | 7 条 bullet，每条都有"理由"句 |
| 验收标准 | PASS | 12 条 AC，其中 3 条 behavioral（AC-9 / AC-10 / AC-12），满足 ≥ 1 + 远超下限 |
| 任务清单 | PASS | 7 task，全部标 covers_ac；每条 AC 至少有 1 个 task 指向（覆盖矩阵核查见 § 2 末） |
| 风险 | PASS | 6 风险 + 缓解；含极低/低/中三档；含 308 redirect path-param 陷阱（实测中容易踩） |
| 决策日志 | PASS | 7 行，覆盖 prompt § 5 要求的全部 7 条（DB 不动 / 路径风格 A / 308 / parent 单数 / 类型重生 / web folder / refs.py 不清理） |

任务-AC 覆盖矩阵（reviewer 真校）：

| AC | 覆盖 task |
|---|---|
| AC-1 | T-2 |
| AC-2 | T-2 |
| AC-3 | T-1 |
| AC-4 | T-4 |
| AC-5 | T-4 |
| AC-6 | T-5 |
| AC-7 | T-6 |
| AC-8 | T-6 |
| AC-9 | T-7 |
| AC-10 | T-3 + T-7 |
| AC-11 | T-7 |
| AC-12 | T-7 |

12/12 AC 全部有 task 覆盖。无遗漏。

---

## 2. AC 命令真跑日志（每条都执行）

> 当前未实现状态下，static AC 应 FAIL（防 false-pass）；behavioral AC 应 symbol-not-found / file-not-found 即可。

| AC | 命令 | 实际 exit | 期望 | 结论 |
|---|---|---|---|---|
| AC-1 | `test -f apps/api/dataplat_api/routers/snapshots.py && grep -q 'tags=["snapshots"]' ... && grep -q '/snapshots"' ... && grep -q '/snapshots/{hash}"' ...` | **1**（test -f 直接挂） | 当前应 FAIL | PASS-as-expected |
| AC-2 | `test ! -e apps/api/dataplat_api/routers/commits.py` | **1**（commits.py 仍在） | 当前应 FAIL | PASS-as-expected |
| AC-3 | `test -f schemas/snapshot.py && grep ...` | **1**（snapshot.py 不存在） | 当前应 FAIL | PASS-as-expected |
| AC-4 | `grep -q "SnapshotCreate" generated.ts && grep -q "SnapshotRead" generated.ts && ! grep -E "CommitCreate\|CommitRead:" generated.ts` | **1**（SnapshotCreate 不存在） | 当前应 FAIL | **PASS-as-expected，但命令本身有 false-pass 隐患**：`grep -E "CommitCreate\|CommitRead:"` 中 `\|` 在 ERE 里是**字面字符**，等价于搜 `CommitCreate|CommitRead:`（带字面竖线）这串字符。该串在 generated.ts 中**不存在**，所以 `! grep -E ...` 永远返回 0（true）—— 即使将来 generated.ts 仍含 `CommitCreate` / `CommitRead` 该子句也不会 FAIL。**MUST FIX #1**。验证：`grep -E "CommitCreate\|CommitRead:" packages/api-types/src/generated.ts` 当前输出空，但 `grep -E "CommitCreate|CommitRead:" packages/api-types/src/generated.ts` 输出 5 行匹配。 |
| AC-5 | `grep -q '"/repos/{owner}/{name}/snapshots"' openapi.json && grep -q '"/repos/{owner}/{name}/snapshots/{hash}"' openapi.json` | **1**（openapi.json 仍是 commits） | 当前应 FAIL | PASS-as-expected |
| AC-6 | `grep -q 'def create_snapshot(' client.py && ... && grep -q 'snapshot_app.command("create")' cli.py && grep -q '"--parent"' cli.py` | **1**（create_snapshot 不存在） | 当前应 FAIL | PASS-as-expected |
| AC-7 | `test -f routes/snapshots/\$owner.\$name.\$hash.tsx && grep -q 'createFileRoute(...)' ... && test ! -e routes/commits.\$owner.\$name.\$hash.tsx && test ! -e routes/commits.\$owner.\$name.\$hash.test.tsx` | **1**（snapshots/ 目录不存在 + commits 旧文件还在） | 当前应 FAIL | PASS-as-expected |
| AC-8 | `grep -q "interface SnapshotRead" queries.ts && grep -q "parent: string \| null" queries.ts && grep -q "export function useSnapshot(" queries.ts && ! grep -q "interface CommitRead" queries.ts && ! grep -q "export function useCommit(" queries.ts` | **1**（SnapshotRead 不存在 + 反向条件命中：当前文件含 `interface CommitRead` 和 `useCommit`） | 当前应 FAIL | PASS-as-expected。反向 grep 子句**真实可触发**（与 AC-4 形成对比，证明负向检查这里没坏） |
| AC-9 | `cd apps/api && uv run pytest tests/test_snapshots_api.py -x -q` | n/a（文件不存在；symbol-not-found） | 当前应 FAIL | PASS-as-expected |
| AC-10 | `cd apps/api && uv run pytest tests/test_snapshots_api.py::test_old_commits_path_redirects_308 -x -q` | n/a（同上） | 当前应 FAIL | PASS-as-expected |
| AC-11 | `awk 'found && /^## [^#]/{exit} /^run_api_snapshot_rename\(\)/{found=1; print; next} found' scripts/_self_check.sh \| head -1 \| grep -q "run_api_snapshot_rename" && grep -q "api-snapshot-rename-20260520) run_api_snapshot_rename" scripts/_self_check.sh` | **1**（awk 输出空 → head -1 空 → grep 不匹配；case 派发也无） | 当前应 FAIL | PASS-as-expected。awk flag-based 句式语法对（用 `run_bootstrap_monorepo` 替换测过，能正确打印函数体直到下一个 `## ` 退出） |
| AC-12 | `bash scripts/_self_check.sh current api-snapshot-rename-20260520 2>&1 \| tail -20 \| grep -qE "FAIL=0\\b"` | **1**（self_check 在 reviewer-lint 阶段就 fail-fast 退出） | 当前应 FAIL | PASS-as-expected，**但有隐含问题**：reviewer-lint 走的白名单是 `claude-agent:` / `self-attest`，v2 模板的 `reviewer: opus-phase1-reviewer` / `opus-phase3-reviewer` 不在白名单内。AC-12 在 Phase 2 sonnet 写完所有代码之后**仍会因为这个原因 FAIL**。详见 **SHOULD FIX #1**。 |

**reviewer 真跑结论**：12/12 AC 在当前 main HEAD 状态下都 FAIL，无 false-pass（AC-4 例外，详见 MUST FIX #1）。awk + 反向 grep 语法都验证可执行。

---

## 3. 永不做清单核查（data-not-code-pivot.md 硬约束）

逐条对照 `.harness/rules/data-not-code-pivot.md` § 永不做清单：

| 永不做项 | design 是否触发 | PASS / FAIL |
|---|---|---|
| 不做 branch | **否**。design § 范围未引入任何 branch 概念；§ 非范围明确"不撤 `/branches`"是因为实际**没有** `/branches` 路由（grep 证实 `apps/api/.../routers/` 与 `main.py` 都无 `branches` 字面） | PASS |
| 不做 merge | 否。design 不引入 merge 操作 | PASS |
| 不做 cherry-pick | 否 | PASS |
| 不做 rollback / force-push | 否；308 redirect 不是 rollback | PASS |
| 不做 row-level diff | 否；本 change 不动 row 层 | PASS |
| 不做 blob → blob 派生图 | 否；不动 lineage 模块（design § 非范围明确） | PASS |
| 不做 Asset / manifest.yaml 强制 | 否 | PASS |
| 不做"silver 是文件树" | 否；本 change 不动 silver / gold（W1-3 范围） | PASS |
| 不做强 schema 在 bronze | 否；本 change 不动 bronze schema | PASS |

**额外正向核查**（旧→新术语对照表）：

- ✅ design 用 v2 词汇引用：Snapshot（贯穿 routes / schemas / SDK / web）；用 Commit 仅在描述老路径 / DB 列保留时出现（合理，因为本 change 主旨就是 rename，DB 不动是 D-1 决策）
- ✅ `commit.parents: list[str]` → `snapshot.parent: str | None` 单数化 **真在 schemas/snapshot.py + sdk client + web queries 三处都改**；这是数据结构层面"撤 DAG"的兑现，符合 data-not-code-pivot § 旧→新术语表
- ✅ design § 非范围声明了下游 follow-up：`api-snapshot-rename-cleanup-*`（删 redirect）+ `db-snapshot-rename-*`（可选 DB 改名）+ W2-5 `recipe-yaml-v2`（pipeline / lineage 字段统一），与 roadmap W2 衔接
- ✅ 不抢跑 W1-2（packages/core protocols）/ W1-3（silver schema）/ W1-4（loader 重构）

**永不做清单核查总体**：9/9 PASS。

---

## 4. 决策日志真实性核查

prompt 要求 7 条关键决策齐全：

| 关键决策 | design § 决策日志位置 | 含 alternatives 暗示？ | 含 why-picked？ | PASS / FAIL |
|---|---|---|---|---|
| ① DB 不动 | 行 2026-05-20 16:30 | 暗示（"5 个 alembic migration 涉及 commits 表，迁移代价 >> 改名收益" → 拒绝 DB 改名方案） | ✅ | PASS |
| ② 路径风格 A：`/snapshots/{sha}` | 行 16:31 | 暗示（参照 `/blobs/{sha}` / `/trees/{tree_hash}` 习惯 → 拒绝其他风格） | ✅ | PASS |
| ③ 308 redirect（非并行响应） | 行 16:32 | 显式（"并行响应会让 schema 维护翻倍 + 测试翻倍" 列出被拒方案） | ✅ | PASS |
| ④ `parents: list[str]` → `parent: str \| None`（API 层） | 行 16:33 | 暗示（与 § 风险表"历史 row parents > 1 → 退化为 parent[0]"配合，拒绝"双字段并存") | ✅ | PASS |
| ⑤ api-types 27 处不手改，跑生成器重生 | 行 16:34 | 显式（"手改生成产物 = 反模式" 拒绝手改） | ✅ | PASS |
| ⑥ web 路由 flat-dot 改 folder | 行 16:35 | 暗示（"为后续 W4-1/W4-2 加 list 页让路" → 拒绝保留 flat-dot） | ✅ | PASS |
| ⑦ `models/refs.py` 不清理 | 行 16:36 | 显式（"grep 证实 routes 无 `/branches/` 字面值；本 change scope 已足够，引入额外清理违反不超 500 行 design / 不超 7 task" 拒绝清理方案） | ✅ | PASS |

7/7 PASS。每条决策都有 why-picked，alternatives 多数以 "拒绝 X 因为 Y" 的反向表达隐含。reviewer 觉得这种"反推式 alternatives"在 v2 模板下可接受（v1 时期 spec_review_v* 普遍这么写）。

---

## 5. MUST FIX 列表

> reviewer 一次性列**所有** MUST FIX；不允许第二轮挤牙膏。

### MUST FIX #1：AC-4 的反向 grep 语法 bug（false-pass 风险）

**问题**：AC-4 命令含 `! grep -E "CommitCreate\|CommitRead:" packages/api-types/src/generated.ts`。`grep -E` 在 ERE 模式下 `|` 是 alternation 元字符；`\|` 是**字面竖线**字符（与 BRE 相反）。因此该子句实际在搜字符串 `CommitCreate|CommitRead:`（13 个连续字符，含字面竖线），这在 TypeScript 文件中**永远不会出现**。`! grep ...` 因此**恒为 true**，**无论 generated.ts 是否仍含 `CommitCreate` / `CommitRead:` schema 定义**。

**实测对照**：
- 当前 `grep -E "CommitCreate\|CommitRead:" generated.ts` → 输出空（match=0）→ `! grep` 返回 0
- 而 `grep -E "CommitCreate|CommitRead:" generated.ts` → 输出 5 行（含 `CommitCreate: {` / `CommitRead: {` / `commit: components["schemas"]["CommitRead"]` 等）

**后果**：AC-4 即使 Phase 2 sonnet 没真把 generated.ts 里的 `CommitCreate` / `CommitRead` schema 干掉（例如生成器忘了重跑、或 308 redirect 端点意外保留了 schema 引用），AC-4 静态检查**仍会 PASS**，造成假阳性。这是机械化 AC 的根本失格。

**修法**（Application Owner 在 design.md AC-4 行做局部替换）：
将 `! grep -E "CommitCreate\|CommitRead:"` 改为 `! grep -E "CommitCreate|CommitRead:"`（去掉反斜杠）。

或更稳妥地拆为两条 grep：`! grep -q "CommitCreate" generated.ts && ! grep -q "CommitRead:" generated.ts`，避开 BRE/ERE 转义陷阱（推荐，且与 AC-8 同款风格保持一致）。

---

## 6. SHOULD FIX 列表（非阻塞，留给 Phase 2 sonnet 看着办）

### SHOULD FIX #1：AC-12 与 reviewer-lint 白名单冲突（harness 模板 vs lint 不一致）

**问题**：当前 `scripts/_self_check.sh:1783` reviewer-lint 白名单只接受 `claude-agent:` / `self-attest` 起头的 reviewer 字段值。但 v2 模板 `.harness/changes/_template/design_review.md` / `verify_review.md` 直接写死 `reviewer: opus-phase1-reviewer` / `opus-phase3-reviewer`。任何 v2 change 一进 `_self_check.sh current ...` 就会在 reviewer-lint 阶段 fail-fast 退出，AC-12 必 FAIL。

**实测**：`bash scripts/_self_check.sh current api-snapshot-rename-20260520` 在 reviewer-lint 阶段就 `exit 1`：
```
FAIL: 命中非白名单 reviewer 值（必须以 claude-agent: 或 self-attest 起头）
.harness/changes/api-snapshot-rename-20260520/design_review.md:reviewer: opus-phase1-reviewer
.harness/changes/api-snapshot-rename-20260520/verify_review.md:reviewer: opus-phase3-reviewer
```

**影响范围**：这是 v2 模板与 v1 时期建立的 reviewer-lint 之间的遗留不一致，**所有 27 个 follow-up change 都会踩**。本 change 是 W1-1（第一个 v2 change），是发现该问题的最早时机。

**为何只是 SHOULD FIX 而非 MUST FIX**：本 change 主旨是 API rename，不应背 harness meta 修复负担。但 sonnet 在 Phase 2 真跑 `_self_check.sh current` 时一定会撞到这个坑，需要选一个路径：
- (a) Phase 2 sonnet 把本 change 自己的 `design_review.md` / `verify_review.md` 的 reviewer 字段改成 `claude-agent:api-snapshot-rename-phase1-reviewer` / `claude-agent:api-snapshot-rename-phase3-reviewer`（局部 patch，verify_review.md 由 Phase 3 reviewer 自己填）
- (b) 顺手在本 change 内扩白名单（`scripts/_self_check.sh:1783` regex 加 `|opus-phase[13]-reviewer`），但这跨 harness meta scope，按 D-3 应单独开 `harness-reviewer-whitelist-v2-*` change
- (c) 把 `_self_check.sh` 模板替换字符串 `reviewer: opus-phaseN-reviewer` 视为占位符（与现 `reviewer: <` 占位规则统一），跨 harness meta scope

**建议**：sonnet 走 (a)，把本 change 自己的两个 review 文件 reviewer 字段改成 `claude-agent:...` 形态，并把 (b)/(c) 列入 deferred（`harness-reviewer-whitelist-v2-*` follow-up change）。否则 W1-1 的 AC-12 PASS 不了。

### SHOULD FIX #2：`/tree/{commit_hash}` path param 改名无 AC 兜底

**问题**：design § 范围明确"`GET /tree/{commit_hash}` 路径里的 path param 名改 `snapshot_hash`"，T-2 任务也提到此改名，但 12 条 AC 中没有任何一条断言 openapi.json / routers/snapshots.py 包含 `snapshot_hash` path param。Phase 2 sonnet 漏改 / Phase 3 reviewer 漏验都不会被机械化捕获。

**建议**：sonnet 在 Phase 2 写 self_check 的 `run_api_snapshot_rename` block 时顺手加一条 grep：`grep -q '"/repos/{owner}/{name}/tree/{snapshot_hash}"' packages/api-types/openapi.json` 或对 routers/snapshots.py 内 `snapshot_hash: str = Path(` 做断言。或 design.md 加 AC-13 显式列出。

### SHOULD FIX #3：openapi.json 老路径 redirect 残留无 AC 兜底

**问题**：design 引入 308 redirect 端点会让 openapi.json 仍含 `/repos/{owner}/{name}/commits` 与 `/repos/{owner}/{name}/commits/{hash}` 两个 path 键（FastAPI 把 redirect 端点也注册到 openapi）。AC-5 只检查新路径存在，没断言"老路径仅作为 redirect 操作存在 / 不含 CommitRead schema 引用"。如果未来 cleanup change 漏删 redirect，没有机械检查会报警。

**影响**：低。仅在 `api-snapshot-rename-cleanup-*` 阶段才会暴露。

**建议**：cleanup change 时再加；本 change 不必处理。

---

## 7. NICE TO HAVE（完全可选）

- **NTH #1**：design § 决策日志可以显式拆出 "alternatives considered" 子列（v1 时期 spec_review_v* 偏好的样式），让"反推式 alternatives"更醒目。但 v2 模板没要求，当前隐含写法可接受。
- **NTH #2**：风险表第 4 行"历史 row `commit.parents` 长度 > 1"建议加一条 self_check 兜底（grep DB dump 看是否真存在 list > 1 的行），不过这需要跑 docker-compose 起 pg，性价比低；让 `_snapshot_to_read` 的 log.warning 自然兜底也够。

---

## 8. Verdict

**SMALL REVISIONS** — 1 个 MUST FIX（AC-4 反向 grep 语法 false-pass）+ 3 个 SHOULD FIX；其余结构 / scope / 永不做清单 / 决策日志真实性 / 与 roadmap 一致性均 PASS。Application Owner 修 AC-4 一行（去掉 `\|` 的反斜杠）后直接进 Phase 2，**不再 spawn Phase 1 reviewer v2**。

## 9. 后续指引（给 Application Owner）

1. 在 `design.md` AC-4 行把 `! grep -E "CommitCreate\|CommitRead:"` 改为 `! grep -E "CommitCreate|CommitRead:"`（或拆两条独立 `! grep -q`，推荐后者）。无需重新 spawn reviewer。
2. spawn Phase 2 sonnet 时，prompt 里**强调**：
   - 处理 SHOULD FIX #1（reviewer-lint 白名单 vs v2 模板冲突）：在本 change 内把 `design_review.md` + `verify_review.md` 的 `reviewer:` 字段写成 `claude-agent:api-snapshot-rename-phase1-reviewer` / `claude-agent:api-snapshot-rename-phase3-reviewer`（这是本 change 内最小路径），并把"扩白名单 / 把 opus-phase* 视为占位符"列为 deferred follow-up（开 `harness-reviewer-whitelist-v2-*` 或合入下一个 harness meta change）。
   - 处理 SHOULD FIX #2：self_check 的 `run_api_snapshot_rename` block 内顺手加 1 条断言 `/tree/{snapshot_hash}` path param 改名生效，闭环 T-2 任务声明。
3. 不需要修动 design § 决策日志（7 行齐全 + why-picked 完整；alternatives 隐含可接受）。
4. 不需要修动范围 / 非范围（永不做清单 9/9 PASS；非范围声明的 follow-up 衔接 roadmap）。

**Phase 2 入口**：design.md 修 AC-4 一行 → 直接 spawn sonnet 端到端。
