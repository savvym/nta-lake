---
change_id: commit-api-mvp-20260517
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-stage2-reviewer
reviewed_at: 2026-05-17T09:35:00Z
verdict: REVISION REQUIRED
---

# Spec Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1 plan 模式 spec.md 列表。

- [x] 背景写明了为什么现在做（spec L11-13：adapter 写入侧被堵；§4.4 CAS 路由必须落最小子集）。
- [x] 问题陈述对外部读者可理解（spec L15-19）。
- [x] 范围 / 非范围都有（spec L22-43，明确列出 6 项推后 follow-up）。
- [ ] **每条验收标准可演示且可机械化（部分不达标，见 MUST FIX-1）**。
- [ ] **风险有缓解或显式 accept（部分缓解措施未映射到 AC-11 测试列表，见 SHOULD FIX-2/3）**。
- [x] 没有把已有架构当新提案（spec 一致引用 design.md §4.4、cas-storage、repo-api-mvp 已有产物）。
- [x] 待澄清问题段：spec 中无 `## 待澄清问题` 章节但所有决策都已在 L70-80 决策表中确定，可视为已清零。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md §验收标准 L44-57（AC-1 至 AC-13 整体）| 缺少与 repo-api-mvp spec 平行的"验证方式表"。AC-1~AC-5 / AC-12 / AC-13 这种纯结构/lint 类断言应可一行式 `uv run python -c "..."` 校验；spec 仅做了散文描述，没有把命令直接放出。这违反 [[project-followup-harness-lint]] 的核心教训：AC 验证命令必须能直接复制粘贴到 `scripts/_self_check.sh` 跑。参考 repo-api-mvp spec.md L60-70 的"AC \| 验证方式 \| 期望"表格。| 补一个 `## 验收标准（验证方式表）` 章节或在每条 AC 下追加"验证命令"小节，至少 AC-1 / AC-2 / AC-3 / AC-4 / AC-5 / AC-12 / AC-13 必须给出一行式命令；AC-6~AC-11 可写"由集成测试 (a)~(m) 覆盖"。 |
| 2 | spec.md AC-9 L53 + AC-10 L54 + AC-1 L45 三者矛盾 | AC-9 写 `created_at:iso` 且备注"client 可控"，AC-10 写"含 created_at——client 可控"，但 AC-1 的 `CommitCreate(tree, parents, author_id, message?, lineage?, ref?)` schema **不包含 `created_at` 字段**；tasks.md T-3 L44 写 `created_at = datetime.utcnow()` （服务端算）。直接后果：测试 (g)（spec L55 AC-11）"相同 payload 二次 POST → deduplicated=true" 永远不可能成立——服务端两次取 `utcnow()` 不同 → commit canonical bytes 不同 → commit_hash 不同 → 永远走新插入路径 → AC-10 幂等性破坏。| 二选一：(A) 把 `created_at: datetime` 加入 `CommitCreate` schema 让 client 控；服务端只验合理范围 / (B) 从 commit canonical bytes 公式里**去掉** `created_at`，幂等 key 只依赖 (tree_hash, parents 升序, author_id, message, lineage)；服务端记录 created_at 但不参与 hash。建议 (B)，与 Git 实际语义一致（Git commit hash 包含 author_date 因为它就是 client 给的，而我们这里若希望"完全确定性内容寻址"应去掉时间）。修完后 AC-9 / AC-10 / AC-11 (g) 一致。 |
| 3 | spec.md AC-9 L53 lineage canonical 序列化规则 | AC-9 文本 `<lineage canonical or null>` 没有钉死"lineage 嵌套字段是否递归 sort_keys"。tasks T-3 L40 `_lineage_to_canonical` 用 `model_dump(mode="json")` 取 dict，但 dict 本身是 unordered；只靠外层 `json.dumps(..., sort_keys=True)` 递归排序成立的前提是嵌套结构均为 plain dict/list/scalar，不含自定义 Pydantic 对象。若 `Lineage.produced_by` 在 model_dump 后已是 plain dict，则 `sort_keys=True` 递归生效；但 spec 必须明示这条不变量。| AC-9 末尾追加：`lineage canonical = model_dump(mode="json") 得到的 plain dict 经同样 sort_keys=True ensure_ascii=False separators=(",", ":") 序列化；不允许 lineage 内嵌任何 datetime / UUID 等非 JSON 原生类型（model_dump mode="json" 已保证）`。 |
| 4 | spec.md AC-8 L52 与 风险 #3 L63 内部矛盾 | AC-8 文本：「事务内做 blob 存在性校验，缺失 → 400」。风险 #3：「MVP 把 blob 存在性校验放在 `session.begin()` **之前**（事务外做 IO，事务内只做 DB 写）」。tasks T-3 步骤 1 跟随风险 #3。同一份 spec 里两处对存在性校验位置说法不一致；执行者会困惑实现哪个。| 改 AC-8 文本：「`POST commits` 用 `async with session.begin()` 单事务包裹 tree + tree_entries + commit + ref 的 DB 写；blob 存在性校验在事务**前**完成（异步 `store.exists()` 串行调用），缺失 → 400 含 `missing_hashes: [...]`；MVP 接受『校验后/事务内 race 期间 blob 被删』作为非目标（cas-storage 无 GC 路径）」。 |
| 5 | spec.md AC-11 L55 测试矩阵缺 AC-9 hash 确定性专门测试 | AC-11 13 个测试 (a)~(m) 没有任何一条**单元级断言** canonical hash 函数是确定性的。(g) 是端到端幂等测试，依赖 router + service + DB；若 (g) 失败无法定位是 hash 计算 bug 还是 DB 唯一约束 bug 还是 session 状态问题。AC-9 是本变更的**核心确定性承诺**，缺单元测试导致 Phase 2 切 Python 版本/平台时无法回归。| (a) 把 (g) 拆成两条：(g1) 单元测试 `_canonical_tree_bytes(entries_unordered) == _canonical_tree_bytes(entries_sorted)`（断言 entries 排序不变性）+ `_commit_hash(tree_hash, p1, p2)` 与 `_commit_hash(tree_hash, p2, p1)` 相等（parents 排序不变性）；(g2) 端到端幂等 POST。(b) AC-11 列表中数量从"≥ 12"改"≥ 14"。 |
| 6 | spec.md AC-11 L55 测试矩阵缺大文件流式 round-trip | 风险 #2 L62 写"MVP 测试 ≥ 2MB 流式 round-trip"作为缓解措施，但 AC-11 (a)~(m) 列表中**没有大文件测试**。"缓解措施"在 AC-11 没落地等于无缓解。这是 spec 与 risk 自相矛盾。| AC-11 追加 (n) "admin POST 2MB 随机字节 blob → 200 + sha256 与本地 hashlib.sha256 一致；GET 同 sha256 → 流式字节完全相等"；AC-11 数量从"≥ 12"改"≥ 14"（合并问题 5 后 "≥ 15"）。 |
| 7 | spec.md AC-11 L55 测试矩阵缺 lineage round-trip | 风险 #5 L65 写"commit.lineage 是 JSONB；POST Pydantic Lineage → JSON 存；GET 时反序列化回 Lineage。测试 round-trip"——但 AC-11 (a)~(m) 没有 lineage 测试。同问题 6，缓解措施在 AC-11 没落地。| AC-11 追加 (o) "POST commit 含 lineage（含 produced_by + inputs 至少 1 个）→ 200；GET 同 hash → lineage 字段反序列化为完整 Lineage 模型，produced_by.kind / inputs[0].repo / inputs[0].commit 字段全在"。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md AC-6 L50 "写路由：repo 不可见也 → 404（含 admin 看不到的非法状态不触发；admin 见全部）" | 这句话语义混乱：「含 admin 看不到的非法状态不触发」+「admin 见全部」自相矛盾，读者无法判断 admin POST commit 到 repo 行不存在时应该 404 还是 500。| 改为两条清晰条目：(1) admin 写路由：repo 不存在 → 404（与 read 一致）；(2) 非 admin 写路由：require_admin → 403 在 visibility 之前；不存在 case 不会到达 visibility 检查层。 |
| 2 | spec.md AC-6 L50 visibility 测试覆盖 | (l)/(m) 仅覆盖 anonymous × public/private 两格；缺 internal × user / private × user 等格子。repo-api-mvp AC-11 (h)/(i) 已涵盖 user × internal/private 视角。commit-api 应同样级别覆盖。| AC-11 追加 (p) user GET commit on internal repo → 200，(q) user GET commit on private repo → 404。 |
| 3 | spec.md AC-5 L49 OpenAPI 含 5 新 paths | 没有列在 AC-11 测试里、也没有写一行式 `python -c "from dataplat_api.main import app; ..."` 验证命令。仅靠 `make codegen` 跑过不等于 5 paths 真的出现在 spec 里。| AC-5 末尾追加验证命令模板（spec L49）：`cd apps/api && uv run python -c "from dataplat_api.main import app; s=app.openapi(); assert {'/repos/{owner}/{name}/blobs', '/repos/{owner}/{name}/blobs/{sha256}', '/repos/{owner}/{name}/commits', '/repos/{owner}/{name}/commits/{hash}', '/repos/{owner}/{name}/tree/{commit_hash}'} <= set(s['paths'].keys())"`。 |
| 4 | spec.md AC-10 L54 并发 race 路径无测试覆盖 | 风险 #4 + AC-10 都声明 IntegrityError catch → dedup，但 AC-11 (g) 是顺序 dedup（先 POST → 再 POST）；走 SELECT 命中分支，**永远不触发 IntegrityError 兜底**。Race 路径无回归保障。| (a) 把 (g) 顺序 dedup 保留并新增 (r) 并发 dedup：`asyncio.gather(POST commit, POST commit)` 两个同 payload → exactly one created，另一个 deduplicated=true，无 500（用 `pytest-asyncio` + 两个独立 AsyncClient 实例）。或 (b) 显式 deferred 并在 spec 注明"race 路径通过 catch 实现但 MVP 不测试覆盖，理由：pytest-asyncio + asyncpg session 跨协程开销大；follow-up 用 locust/k6 压测覆盖"。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md AC-1 L45 `TreeEntryCreate(... entry_type='blob' ...)` 默认值 | AC-1 写 `entry_type='blob'`（带默认值），tasks T-1 L14 写 `entry_type: Literal["blob"]`（无默认值）。Pydantic 允许 Literal 带默认值；不会破坏但 AC-1 与 tasks T-1 微小不一致。| 统一为带默认值（让 client 不必传），与 schema 文档一致。 |
| 2 | spec.md L78 决策表 "Ref upsert 语义" | 没有约束 ref 名格式（`main` vs `refs/heads/main` vs 任意字符串）。MVP admin only 不构成安全风险但 follow-up `ref-api-mvp-*` 需要兼容。| 追加："ref 名 MVP 接受任意非空字符串，长度 ≤ 255；具体语法规则推后到 ref-api-mvp-* 收紧。" |
| 3 | spec.md L82 流程偏离声明 | "无。本变更与 repo-api-mvp 同节奏"——MUST FIX-2 / MUST FIX-4 暴露 spec 内部不自洽，说明本次 generator 没有充分做"自审 cross-AC consistency"检查。| 在反哺 `.harness/skills/request-analysis/SKILL.md` 末尾增加 checklist：「跨 AC consistency 检查 — schema 字段 ↔ canonical hash 输入 ↔ idempotency key ↔ test fixture 四链路必须一致」。这条作为流程改进，不阻塞当前 spec。 |

## Verdict

REVISION REQUIRED（MUST FIX 数 = 7）

## 复检指引

作者写 `spec_v2.md` 时按下述命令自查（修完一条核一条）：

1. **MUST FIX-1（验证表）**：在 spec_v2.md 内执行
   ```bash
   grep -E "uv run python -c|test -f|bash scripts" .harness/changes/commit-api-mvp-20260517/request_analysis/spec_v2.md | wc -l
   ```
   期望 ≥ 7（AC-1/2/3/4/5/12/13 各至少一条）。

2. **MUST FIX-2（created_at 一致性）**：
   ```bash
   grep -nE "created_at" .harness/changes/commit-api-mvp-20260517/request_analysis/spec_v2.md
   ```
   人工核对：要么 (A) CommitCreate schema 显式有 `created_at`；要么 (B) commit canonical 公式中**不含** created_at。两路径与 tasks_v2.md T-3 步骤 2 描述一致。

3. **MUST FIX-3（lineage canonical 规则）**：
   ```bash
   grep -nE "model_dump\(mode=.json.\)|lineage canonical" .harness/changes/commit-api-mvp-20260517/request_analysis/spec_v2.md
   ```
   AC-9 末尾包含明确条款。

4. **MUST FIX-4（AC-8 与 风险 #3 一致）**：
   ```bash
   awk '/AC-8/,/AC-9/' spec_v2.md | grep -E "事务前|事务外|begin\(\) 之前|before"
   ```
   期望出现"事务前/事务外"措辞，且与 风险 #3 一致。

5. **MUST FIX-5/6/7（AC-11 测试增补）**：
   ```bash
   awk '/AC-11/,/AC-12/' spec_v2.md | grep -cE "^\s*-\s*\*\*AC-11\*\*|^\s*\(\w\)"
   ```
   期望 ≥ 15 个测试条目（原 13 + hash 单元 + 2MB blob + lineage round-trip + 可选 race 与 user×internal/private commit visibility）。

6. **SHOULD FIX**：上述自查命令同结构。

7. 重新跑：
   ```bash
   grep -E "矛盾|fix\?|TODO|XXX" spec_v2.md
   ```
   期望空。

提交 v2 后开 `spec_review_v2.md`。
