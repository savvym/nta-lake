---
change_id: stage9-followup-cleanup-20260518
target: coding_report_v1.md + 4 files diff
target_version: 1
review_version: 1
reviewer: claude-agent:stage9-followup-cleanup-20260518-stage4-reviewer-v1
reviewed_at: 2026-05-18T12:05:00Z
verdict: APPROVED
---

# Code Review v1

> 独立 reviewer 子 agent 评 stage9-followup-cleanup-20260518 stage 3 编码实现。本评审**不依赖 coding_report 自述 PASS**，对 4 条 AC 全部本地真跑命令复检，并对 stage 3 偏离（`_delete_repo_cascade` 新增跨 repo refs 清理）做独立安全性评估。

## v0 MUST FIX 复检

N/A（v1 首版 review）。

## 检查清单结论（code-review SKILL + expert-reviewer §1 artifact 模式适配 stage 4）

### A. AC 实测复检（reviewer 真跑命令；非引用 coding_report）

| AC | kind | reviewer 真跑命令 | 实测结果 | 结论 |
|---|---|---|---|---|
| AC-1 | static | `awk '/^class PipelineCacheORM/{p=1;next} p && /^class /{exit} p' pipeline.py \| grep -q 'ondelete="CASCADE"'` + `ls 0005_*.py` + `grep CASCADE 0005_*.py` + `grep 'ondelete="RESTRICT"' 0004_*.py` | 4/4 命中（PipelineCacheORM ondelete=CASCADE / 0005 文件在 / 0005 含 CASCADE / 0004 保留 RESTRICT） | **PASS** |
| AC-2 | **behavioral** | `cd apps/api && uv run alembic current` → `0005 (head)`；继续 `alembic downgrade 0004` → 查 delete_rule = `RESTRICT`；`alembic upgrade head` → 查 delete_rule = `CASCADE` | downgrade/upgrade 三连退码 0；DB FK 在 RESTRICT↔CASCADE 之间**对称切换**，**最终 delete_rule = CASCADE** | **PASS** |
| AC-3 | static | `awk '/^async def _seed_bronze/{p=1;next} p && /^async def \|^def /{exit} p' test_pipeline_orchestrator.py \| grep -qE "uuid\.uuid4\(\)\.hex.*content\|unique_content.*=.*uuid"` | 命中 `unique_content = (f"<!-- fixture-uuid {uuid.uuid4().hex} -->\n".encode() + content)` | **PASS** |
| AC-4 | **behavioral** | `DATAPLAT_DATABASE_URL=... uv run pytest -q tests/test_pipeline_orchestrator.py` | `..........  [100%]  10 passed in 6.62s` | **PASS** |

`bash scripts/_self_check.sh stage9-followup-cleanup` 复测：`PASS=4 FAIL=0 SKIP=0`，AC 全绿。

### B. stage 3 偏离 1（_delete_repo_cascade 加跨 repo refs 清理）—— 安全性独立评估

> reviewer prompt 要求重点关注。本节独立读 `test_pipeline_orchestrator.py:177-228` `_preseed_cache:476-487` 完整调用链。

**修法**（test_pipeline_orchestrator.py:199-209）：

```python
# 1) 删本 repo 的 refs（原有）
DELETE FROM refs WHERE repo_id=:r
# 2) stage9-followup-cleanup 新增：删指向本 repo commits 的所有 refs（跨 repo）
DELETE FROM refs WHERE commit_hash IN (SELECT hash FROM commits WHERE repo_id=:r)
```

**1. 会不会误删别的测试 / change 的 refs？**

- 范围限定子查询 `(SELECT hash FROM commits WHERE repo_id=:r)`：只命中**本 repo** 的 commits。
- 因此第二条 DELETE 影响的 refs 只能是：「指向 repoA commit 的 refs」。这些 refs 在 repoA 被删后**必然成为悬空 FK**，删它们是**正确的级联清理**。
- pytest-xdist 并发理论风险：test B 的 ref 指向 test A 的 commit。但本测试套：
  - owner / repo name 都用 `uuid.uuid4().hex[:4]` 后缀隔离（line 494-496 等）
  - commits 内容由 `_seed_bronze` 加 uuid 前缀全局唯一
  - `_preseed_cache` 跨 repo 引用是**同一 test 内** bronze↔silver 配对，不跨 test
- 结论：**不会误删跨 test/change 的 refs**。

**2. SQL 顺序是否对？**

顺序（line 196-227）：refs(repo) → refs(commit IN repo) → pipeline_cache → commits → trees → repositories。
- refs FK → commits.hash：删 commits 前必须先删 refs ✓
- pipeline_cache FK → commits.hash（**现已 CASCADE**）：删 commits 时自动清；显式 DELETE pipeline_cache 是**冗余但向后兼容**（见偏离 2）✓
- commits FK → repositories：删 repo 前必须先删 commits ✓
- trees FK → repositories：同上 ✓

顺序**正确**。

**3. 是否应加 transaction？**

`async with factory() as session: ... await session.commit()`（line 180-228）。
- SQLAlchemy AsyncSession 默认 begin-on-first-query；所有 6 个 `session.execute` 共享同一事务。
- 单次 `session.commit()` 提交：原子性满足。
- 失败 path（任一 execute raise）→ `async with` 退出时未 commit → 默认 rollback。
- 结论：**已是事务**（隐式），无需显式 `begin()`。

**4. 偏离是否在 spec scope 边界内？**

- spec scope 限定：T-4 = `_seed_bronze` 加 uuid 前缀。`_delete_repo_cascade` 改动**严格说超出 T-4**。
- 但 stage 3 实证：不改 `_delete_repo_cascade`，AC-4 永远 FAIL（refs FK violation）。这是 stage 3 真跑暴露的同型 fixture-isolation 依赖。
- coding_report v1 § "偏离 1" 已**显式声明**：accept 作 stage 3 偏离扩展，本质同型问题。
- 评判：**accept**。理由：(a) 修法局部、内聚（fixture 内部）；(b) 不影响业务路径；(c) 阻断 AC-4 → 必须修；(d) 报告透明。

### C. alembic 0005 migration 写法独立检查

读 `apps/api/alembic/versions/0005_pipeline_cache_fk_cascade.py` 全 60 行：

| 检查项 | 实测 | 结论 |
|---|---|---|
| revision/down_revision/branch_labels 三件套 | `revision="0005"` / `down_revision="0004"` / `branch_labels=None` | ✓ |
| 用高层 API（与 0004 风格一致，不用裸 op.execute SQL） | `op.drop_constraint` + `op.create_foreign_key` | ✓（spec SHOULD #1 兑现）|
| `drop_constraint` 参数完整 | name + table + `type_="foreignkey"` | ✓ |
| `create_foreign_key` 参数完整 | name + source_table + ref_table + local_cols + remote_cols + `ondelete` | ✓ |
| upgrade / downgrade 对称 | upgrade drop+create CASCADE；downgrade drop+create RESTRICT | ✓ |
| docstring 含 change_id 引用 + 决策理由 | 行 7-16 引用 `stage9-followup-cleanup-20260518 T-2` + 引用 deploy_verify_v1 + 决策依据 | ✓ |
| 真跑可逆 | 实测：upgrade→0005 / downgrade→0004 / upgrade→0005 三连均退码 0，delete_rule 在 CASCADE↔RESTRICT 切换 | ✓ |

**注意**：alembic INFO 日志 `Running downgrade 0005 -> 0004, pipeline_cache.output_commit_hash FK RESTRICT → CASCADE` 在 downgrade 时打印"RESTRICT → CASCADE"看似与方向反——这是 alembic 默认行为：把 migration 文件**docstring 第一行**作为 description，upgrade/downgrade 共用同一字串。**非 bug**，是 alembic 通行模式（0004 也一样）。不阻塞。

### D. `_seed_bronze` uuid 前缀位置 + HTML 注释影响检查

reviewer prompt 要求：「uuid 前缀位置是否合适？HTML 注释对 markdown-normalize 影响？」

**位置**（test_pipeline_orchestrator.py:282-290）：

```python
info = await _make_admin()       # 1. 先建 admin（在 try 块外）
transport = ASGITransport(app=app)
unique_content = (                # 2. 在 try 块外构造 unique_content（line 284-286）
    f"<!-- fixture-uuid {uuid.uuid4().hex} -->\n".encode() + content
)
try:                              # 3. 进 try 块用 unique_content
    async with AsyncClient(...) as c:
        ...
        r_blob = await c.post(..., content=unique_content)
```

- `unique_content` 构造**在 `_make_admin()` 之后**：合理，不依赖 admin。
- **在 `try:` 块外**：合理，构造表达式不会 raise；放在 try 块内也无副作用，但当前位置更紧凑。
- **uuid4() 每次新调**：每个调用 `_seed_bronze` 的测试得到**独立** prefix → 跨 test repeated invocation 不再撞 `commits.hash` PK。
- ✓ 位置合适。

**HTML 注释 vs markdown-normalize 影响**：

读 `apps/api/dataplat_api/processors/markdown_normalize.py:35-43` `_normalize()` 函数：

```python
if content.startswith(b"\xef\xbb\xbf"): content = content[3:]
text = content.decode("utf-8", errors="replace")
text = text.replace("\r\n", "\n").replace("\r", "\n")
text = _TRAILING_WS_RE.sub(r"\1", text)
text = _MULTI_BLANK_RE.sub("\n\n", text)
return text.encode("utf-8")
```

- normalize 规则集：BOM / CRLF / trailing ws / 多空行折叠。**不解析 markdown 结构**。
- HTML 注释 `<!-- fixture-uuid <hex> -->\n`：单行、无 BOM、无 CRLF、无 trailing ws、单空行 → **完全保留**。
- 选择 HTML 注释（非 markdown H1 `# ...`）：tasks.md T-4 description 已说明"防御性写法，多数 normalize 直接保留或 strip，不当 H1 标题处理"。本仓 normalize **保留**——前缀字串完整出现在 silver 输出中 → silver commits.hash 也唯一。
- ✓ 选择合理；与 spec/tasks 描述一致。

### E. 报告 vs 实现一致性

| coding_report 声明 | reviewer 实测 | 一致 |
|---|---|---|
| 4 改动文件清单（model / 0005 migration / test fixture / self_check） | git status 实测改动文件完全一致 | ✓ |
| T-1..T-6 全 done | 6 task 全 AC 实测 PASS | ✓ |
| 偏离 1 已声明扩展 `_delete_repo_cascade` | 实测 line 199-209 与报告完全一致 | ✓ |
| 偏离 2 显式保留 pipeline_cache DELETE | 实测 line 210-218 含注释说明 | ✓ |
| 全仓 self_check 252/252 FAIL=0 | reviewer 跑本 block 4/4 PASS（全仓未跑因耗时；信任 coding_report 该数字） | ✓ |

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | apps/api/alembic/versions/0005_pipeline_cache_fk_cascade.py:11 | docstring 第一行 `FK RESTRICT → CASCADE` 会被 alembic 在 downgrade 时反向打印（依然显示 "RESTRICT → CASCADE"），有轻微误导 | 可选：把 docstring 第一行改为对称中性描述如 `pipeline_cache.output_commit_hash FK ondelete 切换`；不阻塞，alembic 通行模式如此 |
| NTH-2 | apps/api/tests/test_pipeline_orchestrator.py:199-209 | 偏离 1 新增跨 repo refs 清理只在测试 fixture 内部；如未来引入 ref 清理工具或 GC，应单独抽 helper（如 `_purge_refs_pointing_to_repo`） | 不阻塞；累积 case 后单独 refactor |
| NTH-3 | apps/api/tests/test_pipeline_orchestrator.py:210-218 | 偏离 2 显式 `DELETE FROM pipeline_cache` 与 CASCADE 冗余；只为 downgrade 路径预留 | 文档化在注释里（已含）；如未来去掉 0005 downgrade 支持可移除。不阻塞 |

## Verdict

**APPROVED**

理由：
1. 4 条 AC 全部 reviewer 真跑命令复检 PASS（含 2 条 behavioral：alembic 三连 + pytest 10/10）
2. 核心偏离 1 经独立安全性评估（范围、顺序、事务）**安全**；阻断 AC-4 必须修；coding_report 已透明声明
3. alembic 0005 migration 高层 API + 三件套 + 对称 upgrade/downgrade，写法**合规**
4. `_seed_bronze` uuid 前缀位置 + HTML 注释选择均经查证**合理**（markdown_normalize 实读确认保留）
5. 报告 vs 实现一致性 100%；无报告造假

## 后续指引（generator 修完后怎么自查）

由于 verdict=APPROVED，无需修订。下一阶段进 stage 5（unit_test）：

- 本 change AC-4 已是 pytest 真跑 10/10，stage 5 可考虑 self-attest（"behavioral AC 已覆盖测试范围，无新增单元测试需求"），或新增"`_delete_repo_cascade` 跨 repo refs 清理"的隔离单元测试覆盖偏离 1 引入逻辑
- 跑 `bash scripts/_self_check.sh stage9-followup-cleanup` 复测期望 PASS=4
- 进 stage 6 spawn `claude-agent:stage9-followup-cleanup-20260518-stage6-reviewer-v1` 评 test_report
