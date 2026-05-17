---
change_id: commit-api-mvp-20260517
target_head: working-tree (base 8f8d40d)
review_version: 1
reviewer: claude-stage4-reviewer
reviewed_at: 2026-05-17T10:35:00Z
verdict: APPROVED
---

# Code Review v1：commit-api-mvp-20260517

## 1. 范围审查

### 1.1 改动文件清单 vs coding_report 声明

| 报告声明 | git status | 一致？ |
|---|---|---|
| `apps/api/dataplat_api/schemas/blob.py`（new） | untracked | OK |
| `apps/api/dataplat_api/schemas/tree.py`（new） | untracked | OK |
| `apps/api/dataplat_api/schemas/commit.py`（new） | untracked | OK |
| `apps/api/dataplat_api/schemas/__init__.py`（edit） | M | OK |
| `apps/api/dataplat_api/services/blob.py`（new） | untracked | OK |
| `apps/api/dataplat_api/services/commit.py`（new） | untracked | OK |
| `apps/api/dataplat_api/services/__init__.py`（edit） | M | OK |
| `apps/api/dataplat_api/routers/commits.py`（new） | untracked | OK |
| `apps/api/dataplat_api/main.py`（edit） | M | OK |
| `apps/api/dataplat_api/models/tree.py`（edit） | M | OK |
| `apps/api/dataplat_api/models/commit.py`（edit） | M | OK |
| `packages/api-types/openapi.json`（edit） | M | OK |
| `apps/api/tests/test_commits.py`（new） | untracked | OK |
| `scripts/_self_check.sh`（edit） | M | OK |
| `.harness/skills/request-analysis/SKILL.md`（edit） | M | OK |

声明清单与 working-tree 完全一致；无未声明改动。

### 1.2 Scope 审查

- `models/{tree,commit}.py` 的 `relationship()` 增补**纯 Python 关系导航，无 schema 变更/无 alembic 迁移**。本质上是补 core-domain-model 落地的 ORM 查询侧缺口，spec AC-3 / AC-9 的 `selectinload(CommitORM.tree).selectinload(TreeORM.entries)` 是必要前置；不视为 scope creep。已在 coding_report v1 偏离说明里记录。**通过**。
- `.harness/skills/request-analysis/SKILL.md` 反哺属于 T-8 process task，已在 spec/tasks 中显式声明（spec v2 流程偏离声明 + tasks T-8）。**通过**。

### 1.3 目录与分层

- routers/services/schemas 层级与 `engineering-structure.md` 一致。
- 路由不直接写 SQL，全部走 CommitService / RepoService；BlobService 不查 session / role（AC-2）。
- 无新顶层目录、无未经 ADR 同意的新依赖。**通过**。

## 2. 正确性审查（含 reviewer 列出的 6 个重点）

### 2.1 事务实现偏离（reviewer 重点 #1）— 语义验证

**Spec AC-8 措辞**：`async with session.begin()` 包裹 tree + tree_entries + commit + ref 的 DB 写。
**实际实现**：try/except IntegrityError 包裹同样集合 + 末尾 `await session.commit()` + rollback 兜底。

分析：

- `CommitService.create_commit` 步骤 3 (`_fetch_with_tree` SELECT) 已触发 SQLAlchemy AsyncSession 的 **auto-begin**——这是 SQLAlchemy 2.0 文档明示行为（"transactions are begun lazily"），并非偏离。
- 在 auto-begin 状态下再调 `async with session.begin()` 会 raise `InvalidRequestError("A transaction is already begun on this Session")`。coding_report 描述与 SQLAlchemy 行为一致。
- 实际事务边界：步骤 3 SELECT → auto-begin → 步骤 4 多次 `session.add` + 末尾 `session.commit()`。所有 ORM 写在同一个底层 transaction 内，commit 时一次性 flush；IntegrityError 触发 rollback。**语义与 spec 声明的"单事务"等价**。
- Race 路径 rollback 后 `await CommitService._fetch_with_tree(session, ...)` 是 fresh SELECT（rollback 已释放事务状态；新查询走新 auto-begin）。返回 (existing, True) 路径在 g2 测试覆盖，且 AC-11 18/18 PASS。

**结论**：偏离是 SQLAlchemy 行为约束驱动，**非实现疏忽**；语义等价；已在 coding_report 显式声明；spec 应理解为"逻辑事务"。**不阻塞**。

> 建议（NICE TO HAVE）：未来 spec 写"事务边界"时直接说"单事务 + commit/rollback 兜底"，不锁定 `session.begin()` 字面句式——这是 SKILL.md 反哺已捕获的跨 AC 一致性问题的延伸。

### 2.2 Canonical hash 跨语言确定性（reviewer 重点 #2）— 验证

- `_lineage_to_canonical` 用 `Lineage.model_dump(mode="json")` 转 plain JSON-native dict（datetime / UUID → ISO string；嵌套全 dict/list/scalar）。
- 外层 `json.dumps(..., sort_keys=True, ensure_ascii=False, separators=(",",":"))` ——Python 文档明示 `sort_keys` **递归生效**（深度排序嵌套 dict）。
- **实证**：env 输入 `{'z':'1','a':'2','middle':'3'}` 序列化后 keys 顺序为 `a, middle, z`（已验证 → outer dumps 输出 `"env":{"a":"2","middle":"3","z":"1"}`）。
- entries 升序 by name + parents `sorted()` 升序 + `Literal["blob"]` 锁死 entry_type → 输入字符串完全可重放。
- 不变量：`Lineage` Pydantic ConfigDict `extra="forbid"` 限定结构；`env: dict[str, Any]` 经 `model_dump(mode="json")` 保证 value 序列化为 JSON-native（含 datetime / UUID 自动转 ISO string）。

**结论**：跨版本 / 跨语言确定性成立。**通过**。

### 2.3 SpooledTemporaryFile 真流式（reviewer 重点 #3）— 验证

- `routers/commits.py:107-114`：`tempfile.SpooledTemporaryFile(max_size=1<<20)` + `async for chunk in request.stream(): tmp.write(chunk)`。
- grep `request.body|request.form` on commits.py → **零命中**（已验证）。
- ASGI `request.stream()` 返回 async generator，逐块吐 bytes；写入 SpooledTemporaryFile 在 1MB 阈值上 spill 到磁盘——内存峰值受限。
- HashingStream 后续 `boto3.upload_fileobj` 通过 64KB chunk read 流式上传到 MinIO；不存在全量 read。
- AC-11 (n) 2MB+17 字节随机内容 round-trip 通过；sha256 与本地 hashlib 一致。

**结论**：流式语义成立。**通过**。

### 2.4 404 不泄露存在性（reviewer 重点 #4）— 验证

- `_resolve_repo` 在 3 个 GET 路由全部前置：repo 不存在或 visibility 不允许 → 404。
- AC-11 (l) `test_l_anonymous_private_repo_returns_404` 显式断言三路由（blobs/commits/tree）匿名访问私有 repo 均返 404；实测通过。
- POST 路由（admin）先 `Depends(require_admin)` → 403；admin 通过后 `_resolve_repo` → repo 不存在 404。**正确路径**。

> 边角观察（NICE TO HAVE）：`Path(pattern=_SHA256_PATTERN)` 触发 Pydantic Path 校验，非法 hash → 422。在私有 repo 上探测会先吃 422（结构层）再走 visibility 层 404，理论上是"格式错"vs"repo 不可见"的状态码分歧。但 422 是结构验证不区分目标资源——攻击者无法借此推断 repo 存在性。可以忽略。

**结论**：通过。

### 2.5 dependency_overrides 清理（reviewer 重点 #5）— 验证

- `tests/test_commits.py:135-139`：fixture `_override_blob_store` 在 yield 后 `finally` 块里 `app.dependency_overrides.pop(get_blob_store, None)`。
- bucket 清理在 pop 之后；异常吞掉（`except Exception: pass`）以保证 fixture teardown 不阻塞。这违反 coding-style §1.5 "禁止 except Exception: pass"——但**已带 `# noqa: BLE001`** 且行为合理（teardown best-effort）：bucket 清理失败不应影响测试退出。可接受。
- pop 是无条件 idempotent（dict.pop with default），fixture 间不会互污。**通过**。

### 2.6 ORM relationship 增补（reviewer 重点 #6）— scope 判定

- `models/tree.py`：加 `TreeORM.entries`（cascade + order_by）和 `TreeEntryORM.tree`（back_populates）。
- `models/commit.py`：加 `CommitORM.tree`。
- 这些是 SQLAlchemy ORM 关系导航，**不产生 alembic 迁移**（无新列、无 FK、无索引；FK 早在 core-domain-model 阶段已落库）。
- `selectinload(CommitORM.tree).selectinload(TreeORM.entries)` 依赖这些 relationship；本变更必要前置。
- 不算 schema 变更；不算 scope creep；coding_report 已声明。**通过**。

> 反哺建议（NICE TO HAVE）：core-domain-model 阶段定 ORM 时漏 `relationship()` 是常见缺口；可在 wiki/orm-conventions 加一条"声明 FK 时同步声明 relationship 双向"。

### 2.7 其他正确性观察

- **commit/tree hash 全局 PK**（coding_report 已知问题）：`CommitORM.hash` / `TreeORM.hash` 是全局 PK；但 `_fetch_with_tree` SELECT 条件含 `(repo_id, hash)` 二维过滤，跨 repo dedup 不会"返回别 repo 的 commit"，实际表现是同 hash 跨 repo INSERT 时触发 IntegrityError race → rollback → 二次 SELECT 在本 repo 无命中 → re-raise（注意 `_fetch_with_tree(session, repo_id, ...)` 返 None 时代码会 `raise`，即跨 repo race 不会错把别 repo commit 当作 dedup 命中）。**当前实现正确**。follow-up `commits-hash-scoped-by-repo-*` 已开。
- **`hash` 路径参数遮蔽 builtin**（commits.py:175）：函数体没用 `hash()`，仅在签名层 shadow，本地作用域；mypy/ruff 通过；NICE TO HAVE 改名 `commit_hash_param`。
- **`_lineage_to_canonical` 类型签名用 `object`**（services/commit.py:72）：放宽到 object + `# type: ignore[attr-defined]` 三处；可直接 `Lineage | None` 类型并显式 import（services/commit.py 现已 import `dataplat_api.schemas.commit.CommitCreate`，进一步 import `Lineage` 不引入循环）。NICE TO HAVE。
- **bulk insert via add loop**：tree_entries 逐条 `session.add`，多 entries 时是 N 次 INSERT（不是真 batch）。MVP 单层 entries=blob、entries 数预期不大；性能可接受。SHOULD note 为 follow-up `commit-bulk-insert-perf-*`，不阻塞。
- **race rollback 后状态**：IntegrityError catch → `session.rollback()` → 二次 `_fetch_with_tree`。SQLAlchemy 2.0 async：rollback 后 session 仍可用，下次 query 走新事务（auto-begin）。代码正确。**通过**。

## 3. 架构审查

- Service / Router / Schema 分层清晰；Router 不写 SQL；Service 不持 state；Schema 全 `extra="forbid"`。
- 复用 `RepoService.get_by_owner_name` / `_visibility_visible`——AC-6 grep 验证 commit 层无重复实现（PASS）。
- BlobStore Protocol 由 `dataplat_core.protocols.storage` 抽象，BlobService 只依赖 Protocol，无 SDK 直接 import。
- Lineage 用现成 Pydantic 模型（`dataplat_core.domain.lineage`），无重复定义。
- 无 LLM Gateway / processor 相关代码，不涉及 §5 规则。

**结论**：架构干净，无破坏不变量。**通过**。

## 4. 风格审查（对照 coding-style.md）

- 类型注解：所有公共方法签名带类型；少数 `# type: ignore[arg-type]` 标注有理由（Pydantic Literal narrowing / FastAPI 路径参数推断局限）。**通过**。
- async 一致性：所有 IO 走 async；boto3 sync 调用通过 `asyncio.to_thread`。**通过**。
- 命名：snake_case / PascalCase / SHA256 alias 都正确。**通过**。
- 错误处理：用 `HTTPException` 在 router/service 边界；IntegrityError catch 显式 narrow（不裸 except）。test_commits.py 的 `except Exception: pass` 带 `# noqa: BLE001` + 注释解释，可接受（teardown best-effort）。**通过**。
- 日志：本变更未引入新 logging 调用——可以接受（不是评审范围）。
- 注释：docstring 仅说 contract / WHY；未见啰嗦"做什么"注释。**通过**。
- 测试：18 测试均有具体 assert；fixture 用真 PG + MinIO（不 mock 核心 BlobStore）；唯一 mock 是 `app.dependency_overrides[get_blob_store]` 注入 per-test bucket 隔离的真实 MinioBlobStore——符合"mock 让测试通过但生产挂掉" 反模式的反向（仍是真存储）。**通过**。

## 5. 性能与可观测性

- `selectinload(CommitORM.tree).selectinload(TreeORM.entries)` 杜绝 N+1。✓
- Blob 上传/下载流式（chunk size 64KB）。✓
- Commit `parents` array column 在 PG 是 inline ARRAY；无 join。✓
- 缺：metric / span（design.md telemetry 尚未接入；本变更不要求）。可接受。

## 6. 验证证据

所有 AC 验证命令复跑：

```
=== commit-api-mvp-20260517 :: 13 AC ===
PASS  AC-1   schemas/blob+tree+commit 7 类型 + extra=forbid + CommitCreate 不含 created_at
PASS  AC-2   BlobService 仅 stream 转发（不 import AsyncSession / 不查 role）
PASS  AC-3   CommitService 含 3 公共方法 + 5 私有 hash 函数
PASS  AC-4   commits router 5 路由 + prefix=/repos + tags=commits
PASS  AC-5   main 集成 commits_router + OpenAPI 含 5 paths
PASS  AC-6   router 不重复实现 _visibility_visible（复用 RepoService）
PASS  AC-7   BlobUploadResponse 字段与 BlobPutResult 字段对应
PASS  AC-8   create_commit 事务边界：blob 存在性校验在事务前（grep）
PASS  AC-9   canonical hash 确定性：entries / parents 顺序不变
PASS  AC-10  commits.hash PK 唯一约束存在（DDL 反射）
PASS  AC-11  apps/api commits 集成 ≥ 16 + 全 PASS（实际 18/18）
PASS  AC-12  ruff + mypy 全 PASS
PASS  AC-13  AC-13 自递归
=== PASS=13 FAIL=0 SKIP=0 ===
```

`uv run ruff check apps/api packages/core` → All checks passed!
`uv run mypy apps/api/dataplat_api packages/core/src` → Success: no issues found in 49 source files
`cd apps/api && uv run pytest tests/test_commits.py` → 18 passed in 9.24s
独立验证 `json.dumps(..., sort_keys=True)` 嵌套递归生效（env keys `{z,a,middle}` → `{a,middle,z}`）。

## 7. 分级问题列表

### MUST FIX

**无**。

### SHOULD FIX

- **S-1**（`services/commit.py:163-177`）tree_entries 多 entry 时是 N 次 `session.add` + 一次 commit；当前 MVP 单层 entries 可接受，但 entries 多时会逐条 INSERT。建议未来开 follow-up `commit-bulk-insert-perf-*` 用 `session.execute(insert(TreeEntryORM), [...])` 批量。**Deferred to follow-up；不阻塞**。

### NICE TO HAVE

- **N-1**（`routers/commits.py:175`）`hash: str = Path(...)` shadow builtin `hash`；改名 `commit_hash_param` 更干净（不影响 OpenAPI path）。
- **N-2**（`services/commit.py:72-77`）`_lineage_to_canonical(lineage_obj: object)` 用 object + `# type: ignore[attr-defined]`；可直接 `Lineage | None` 并显式 import。
- **N-3**（`apps/api/dataplat_api/models/{tree,commit}.py`）关系导航是 core-domain-model 漏项的修补；建议反哺 wiki/orm-conventions "FK 双向同步声明 relationship"。
- **N-4**（spec AC-8 措辞 vs 实际 SQLAlchemy 行为）spec 锁 `async with session.begin()` 字面句；SKILL.md 已加跨 AC 一致性 checklist 反哺，建议下次 spec 写"事务边界"用"单事务（含 commit/rollback 兜底）"避免锁定具体语法 token。
- **N-5**（`tests/test_commits.py:154`）`except Exception: pass` 带 `# noqa: BLE001`；可考虑收紧到 `except (ClientError, BotoCoreError)`，但 teardown best-effort 现状可接受。

## 8. 跨改动观察

- Coding-style §1.5 "禁止 except Exception" 在 test fixture teardown 处通过 `# noqa: BLE001` 旁路。可接受，但建议规则文档加一行"测试 fixture teardown 的 best-effort 清理允许带 noqa"——反哺。
- 本变更整体写得很干净：spec v2 7 + 4 fix 全部落地；coding_report 偏离声明诚实（事务实现 + MinIO 凭据 + ORM relationship）；AC 验证命令一行式都可跑；测试覆盖矩阵完整（admin × user × 匿名 × public × internal × private + 大文件 + lineage + 幂等 + missing blob 400 + ref upsert + 私有 404 一致）。

## 9. Verdict

**APPROVED**。MUST FIX = 0。

SHOULD FIX 1 条（S-1 性能 follow-up，不阻塞 MVP）；NICE TO HAVE 5 条。

## 10. Deferred SHOULD FIX

- **S-1** → follow-up change `commit-bulk-insert-perf-*`（未来开 change 时立题；当前阶段 10 close 时在 summary.md "Deferred" 表中列入）。

## 11. 复检指引

作者修任何 SHOULD/NICE 后跑：

```bash
cd /data/home/zhhdzhang/nta/nta-lake
uv run ruff check apps/api packages/core
uv run mypy apps/api/dataplat_api packages/core/src
DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
  DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
  bash scripts/_self_check.sh commit-api-mvp
# 期望：PASS=13 FAIL=0
```

下一步进 stage 5 单元测试 review / stage 6 CI / stage 7 部署 / stage 8 验收 / stage 10 close（SKILL.md 反哺已在 stage 3 完成，close 时在 summary.md 确认）。

## 12. Follow-up 清单

- `commit-bulk-insert-perf-*`（S-1）
- `commits-hash-scoped-by-repo-*`（coding_report 已知问题）
- `commit-race-load-test-*`（spec out-of-scope 已记）
- core-domain-model ORM relationship 规则反哺（N-3）
- coding-style.md 加"测试 teardown best-effort 允许 noqa"细则（cross-cutting 反哺）
