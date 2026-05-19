---
change_id: tree-nested-domain-20260520
version: 1
authored_at: 2026-05-19T14:00:00Z
status: draft
---

# Spec：Tree 嵌套支持（后端域 / Soft mode / 类 git 递归 GET）

## 背景

dataplat 当前 commit tree 模型是**单层扁平**：`TreeEntryCreate.entry_type = Literal["blob"]`；adapter / processor 把"路径里含 `/`"塞进 entry 的 `name` 字段（如 `name="images/abc.jpg"`），用前缀字符串模拟文件夹。

- 起源：`commit-api-mvp-20260517` § "MVP 仅支持单层 entry_type='blob'；嵌套 tree 留 follow-up tree-nested-*"
- 实测痛点（pdf-mineru-assets 跑出来）：一个 PDF → 1 markdown + 81 张 image + 1 content_list = **83 行扁平 entry**，全在根 tree。导致：
  1. **改一个 blob 全 tree 重 hash**（扁平没有子 hash 复用）
  2. 列子目录 = 前缀字符串扫描（语义层不存在"images/"作为一等公民）
  3. 跨 commit 重名子目录无法 dedup（image 81 张内容相同的子集，两次提交得两份完全独立的 TreeORM 行）
  4. 没有空文件夹概念

**Domain 层（`packages/core/.../tree.py`）早就声明** `entry_type: Literal["blob", "tree"]` —— 只是 schemas / service / API / runner 全锁死了 blob。本 change 把这条路通起来。

用户在本会话 stage 0 选定：
1. **Soft mode 迁移**：POST tree 时服务端自动把 `name="a/b/c"` 拆为嵌套 tree；调用方（adapter / processor）一行不动；旧 commit 只读不动。
2. **GET 默认只本级 + `?recursive=1` 全展开**：类 git 风格，子目录可点开。
3. **本 change 只做后端**：Web UI 另一个 change（`web-tree-nested-ui-*`）走完整 reviewer。

## 问题陈述

- `apps/api/dataplat_api/schemas/tree.py`：`TreeEntryCreate.entry_type` / `TreeEntryRead.entry_type` 锁 `Literal["blob"]`，无法承载子 tree entry。
- `apps/api/dataplat_api/services/commit.py`：
  - `_tree_hash(entries)` 只算一层 sha256；无递归 hash 子 tree 的能力。
  - `create_commit` 步骤 4 只插一行 TreeORM + N 行 TreeEntryORM；没有递归插入多个 TreeORM（每层一个）。
  - 缺路径拆分器：把扁平 entry list 转换成 nested 结构 + 中间 tree 列表。
  - 缺路径合法性校验：`""` / `"/"` / `"a//b"` / `"a/./b"` / `"a/../b"` 必须拒。
  - 缺冲突检测：entries 含 `name="a"`（blob）+ `name="a/b"`（隐含 a 是子目录）→ 矛盾，必须 400。
- `apps/api/dataplat_api/routers/commits.py`：
  - `GET /repos/{o}/{n}/tree/{commit_hash}`：当前返回单层 entry list；没有 `?recursive` 参数；type=tree 的 entry 无路径可下钻。
  - 缺独立 GET 子 tree 的端点（按 subtree hash 取内容）。
- 现 7+ closed change 的所有 commit 都用 `name="a/b/c"` 扁平模式；**必须读取兼容**（GET 返回时不变）。

## 范围

In scope（与下方 AC 对齐）：

- AC-1: `schemas/tree.py` `TreeEntryCreate.entry_type` 与 `TreeEntryRead.entry_type` 放宽到 `Literal["blob", "tree"]`；docstring 同步更新（移除"MVP 仅支持单层"）
- AC-2: `services/commit.py` 新增 `_normalize_to_nested(entries) -> tuple[str, list[tuple[str, list[TreeEntryCreate]]]]`：
  - 输入：扁平 entries（name 可含 `/`）
  - 输出：(root_tree_hash, 待持久化的所有 tree 列表[(hash, level_entries), ...]，含 root 在最后)
  - 算法：解析每个 entry 的 path segments → 构 in-memory trie → 自底向上递归算子 tree hash → 父 entry 引用子 tree hash
  - 子目录 entry：`name=<segment>` + `mode=0o040000` + `entry_type="tree"` + `target_hash=<subtree_hash>`
- AC-3: `services/commit.py` 新增 `_validate_tree_paths(entries)`：拒 `""` / `/` 起头 / `//` 出现 / segments 含 `.` 或 `..` / 同名 blob 与目录冲突；冲突 → ValueError（路由层 400）
- AC-4: `CommitService.create_commit` 步骤 2 改为先 `_validate_tree_paths` → `_normalize_to_nested` 得 (root_hash, all_trees) → tree_hash = root_hash
- AC-5: `CommitService.create_commit` 步骤 4 改为**遍历 all_trees 列表 upsert**（每个子 tree 也是 TreeORM 行；按 hash dedup）；保持事务性
- AC-6: `_canonical_tree_bytes` 不变（per-level entries → JSON bytes → sha256）；语义保证：同一层 entries 完全相同 → 同 hash → 跨 commit / 跨 repo 自然 dedup 子 tree
- AC-7: `routers/commits.py` `GET /tree/{commit_hash}` 加 `?recursive: bool = False` 查询参数
  - 默认 false：返当前根 tree 的直接 entries（含 type=tree 的子目录 entry，`target_hash` 为子 tree hash）
  - true：递归展开所有 type=tree entry，输出全为 type=blob 的 leaf 列表；entry 的 `name` 字段为"扁平全路径"（与旧扁平 commit 的 name 形式一致——**软兼容门面**）
- AC-8: 新端点 `GET /repos/{owner}/{name}/trees/{tree_hash}` （注意复数 `trees`，与 `/tree/{commit_hash}` 区分）：按任意 tree hash（root 或 subtree）取该层 entries；不存在或不属于该 repo → 404
- AC-9: 旧扁平 commit 读路径完全不变：GET `/tree/{commit_hash}` 不带 `?recursive` 也返当前 entries（与本变更之前形态完全一样，因为旧 entries 全是 blob）；带 `?recursive=1` 也能跑（无嵌套就是 no-op）
- AC-10: 新嵌套 commit 写路径：POST `/commits` body 的 tree.entries 仍可全是扁平 name（含 `/`）；adapter / processor 一行不动；服务端自动 nested 化
- AC-11: behavioral：≥ 8 个单测；含：(a) 扁平 input → nested 化 root hash 与展平后 GET ?recursive 一致；(b) GET 默认含 type=tree entry；(c) GET ?recursive=1 等价于旧扁平 GET；(d) 重复提交相同 nested commit → dedup；(e) 同 images/ 子目录两个 commit → 共享 TreeORM hash；(f) 路径校验拒 `""` / `..` / 冲突；(g) GET /trees/{subtree_hash} 拿任意子层；(h) 深嵌套 3+ 层 OK
- AC-12: ruff + mypy 全 PASS
- AC-13: 上游 commits / commit-api-mvp / processor-framework / pdf-mineru chain 等 closed change 的所有 self_check current 不回归（数据格式向后兼容；新写入用 nested，旧读取仍可）
- AC-14: AC-14 自递归 + self_check 含 `run_tree_nested_domain` block

## 非范围

- 不动 Web UI（开独立 follow-up `web-tree-nested-ui-*`）
- 不重写历史 commit（旧扁平 entries 数据库行不动，永远以扁平形式存）
- 不引入 `.gitkeep` 风格的"空文件夹标记"（domain 已支持空 entries，但 entries 必须可达；空根 tree 是合法的"全空仓"语义）
- 不实现 `git ls-tree --abbrev` 或对象 size 字段（leaf blob 的 size 仍由 BlobStore 单独提供）
- 不动 `_canonical_tree_bytes` / `_tree_hash` 算法本身（hash 输入仍为 per-level entries 列表，只是 entry_type 现可为 "tree"）
- 不动 Lineage / Commit 表 schema
- 不引入分页（GET /tree 当前未分页，本变更也不引入；大子目录归 follow-up `tree-nested-pagination-*`）
- 不动 adapter / processor 写代码（端到端验证由 AC-13 上游 self_check 完成）

## 验收标准（14 AC）

`kind` 列：static = grep / dry-import；behavioral = 真跑 pytest 行为。

| ID | kind | 描述 | 验证 | 期望 |
|---|---|---|---|---|
| AC-1 | static | TreeEntryCreate / TreeEntryRead 接受 entry_type="tree" | `cd apps/api && uv run python -c "from dataplat_api.schemas.tree import TreeEntryCreate, TreeEntryRead; e=TreeEntryCreate(name='x', mode=16384, entry_type='tree', target_hash='a'*64); assert e.entry_type=='tree'; r=TreeEntryRead(name='x', mode=16384, entry_type='tree', target_hash='a'*64); assert r.entry_type=='tree'"` | 命令退出 0 |
| AC-2 | static | services/commit.py 含 _normalize_to_nested | `grep -q "_normalize_to_nested" apps/api/dataplat_api/services/commit.py` | 命令退出 0 |
| AC-3 | static | services/commit.py 含 _validate_tree_paths | `grep -q "_validate_tree_paths" apps/api/dataplat_api/services/commit.py` | 命令退出 0 |
| AC-4 | static | _normalize_to_nested 输出 root_hash 与多 tree 列表（dry-import + 微 fixture） | `cd apps/api && uv run python -c "from dataplat_api.services.commit import _normalize_to_nested; from dataplat_api.schemas.tree import TreeEntryCreate as T; root, trees = _normalize_to_nested([T(name='images/a.jpg', mode=33188, entry_type='blob', target_hash='a'*64), T(name='paper.md', mode=33188, entry_type='blob', target_hash='b'*64)]); assert isinstance(root, str) and len(trees) >= 2"` | 命令退出 0 |
| AC-5 | static | create_commit 步骤 4 含 all_trees / 多 TreeORM upsert（grep 锚定） | `grep -qE "all_trees\|for[[:space:]]+\(?[a-z_]+,[[:space:]]+entries_at_level\|for[[:space:]]+sub_tree" apps/api/dataplat_api/services/commit.py` | 命令退出 0 |
| AC-6 | static | _canonical_tree_bytes / _tree_hash 算法不变（grep 函数签名锚定） | `grep -q "def _canonical_tree_bytes" apps/api/dataplat_api/services/commit.py && grep -q "def _tree_hash" apps/api/dataplat_api/services/commit.py` | 命令退出 0 |
| AC-7 | static | GET /tree/{commit_hash} 路由含 recursive 参数 | `grep -q "recursive" apps/api/dataplat_api/routers/commits.py` | 命令退出 0 |
| AC-8 | static | 新路由 GET /repos/{owner}/{name}/trees/{tree_hash} 存在 | `grep -q "/{owner}/{name}/trees/{tree_hash}" apps/api/dataplat_api/routers/commits.py` | 命令退出 0 |
| AC-9 | behavioral | 旧扁平 commit 行为不回归（test_get_tree_legacy_flat_unchanged） | `cd apps/api && uv run pytest -q --tb=no tests/test_tree_nested.py::test_get_tree_legacy_flat_unchanged` | PASS |
| AC-10 | behavioral | 扁平 input → 服务端 nested 化 → GET ?recursive=1 等价扁平（test_post_flat_input_round_trip） | `cd apps/api && uv run pytest -q --tb=no tests/test_tree_nested.py::test_post_flat_input_round_trip` | PASS |
| AC-11 | behavioral | tests/test_tree_nested.py ≥ 8 + 全 PASS | 见 § "AC-11 完整命令" fenced block | ≥ 8 + 全 PASS |
| AC-12 | static | ruff + mypy 全 PASS | `uv run ruff check apps/api packages/core worker/src && uv run mypy apps/api/dataplat_api packages/core/src worker/src` | 命令退出 0 |
| AC-13 | behavioral | 上游 commit-api-mvp / processor-framework / pdf-mineru 关键 unit 不回归 | `cd apps/api && uv run pytest -q --tb=no tests/test_commits.py tests/test_processor.py tests/test_pdf_mineru.py` | 全 PASS |
| AC-14 | static | self_check 含 run_tree_nested_domain | `grep -q "run_tree_nested_domain" scripts/_self_check.sh` | 命令退出 0 |

### AC-11 完整命令

```bash
[ "$(cd apps/api && uv run pytest --collect-only -q tests/test_tree_nested.py 2>&1 | grep -cE 'test_tree_nested\.py::')" -ge 8 ] && \
(cd apps/api && uv run pytest -q --tb=no tests/test_tree_nested.py)
```

> behavioral AC = 4（AC-9 / AC-10 / AC-11 / AC-13），满足分层规约 ≥ 1 条；本 change 是基础设施改造，behavioral 比 static 多是合理的。

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| 路径冲突边界没考虑全：blob 名等于另一个 entry 的目录前缀 | 中 | tree 构造时数据丢失 / 异常 | AC-3 显式拒；test_path_conflict_blob_vs_dir 用例覆盖；service 层 ValueError → 路由 400 |
| 旧扁平 commit + 新嵌套 commit 混合读时 GET ?recursive=1 输出形式不一致 | 中 | UI 显示混乱 | 设计上：扁平 commit 的 ?recursive=1 = no-op；嵌套 commit 的 ?recursive=1 = 全展开为带 / 的 name；两者 leaf 形态完全相同（type=blob + name 含 /）；reviewer 复核 |
| 跨层 tree_hash 碰撞影响 dedup 语义 | 极低 | 误 dedup | sha256 + canonical bytes 设计已防；与 git tree 同模式；不额外做 |
| 中间 tree 的 mode 字段约定不一致 | 低 | reader 误解 | 统一约定：type=tree entry 的 mode = 0o040000 (16384)；写入 service 强制；reader 不依赖 mode 区分（依赖 entry_type） |
| 递归算 hash 时性能：1000 文件 deep tree → 算 hash 慢 | 低 | API 慢 | sha256 单次 ~ μs 级；1000 entries ~ ms 级；无优化需要；负载测试归 follow-up |
| 旧测试断言 GET tree 的 entries 形态会被打破 | 中 | self_check 回归 | AC-13 显式回归；预跑确认 tests/test_commits.py / tests/test_processor.py 旧用例不依赖嵌套 |
| processor 写嵌套后 ProcessResult.file_count 语义变（"扁平叶子数" vs "顶层 entry 数"） | 中 | 上游消费方误解 | processor 调 `len(IngestFileRef list)` 仍是叶子数，不通过 GET tree 测；语义实际保持 |
| schemas/tree.py mypy 严格模式：Literal["blob","tree"] 与现有 type: ignore[arg-type] 兼容 | 低 | mypy 红 | router get_tree 已用 type: ignore[arg-type]；放宽到 ["blob","tree"] 后该 ignore 仍有效；AC-12 验证 |
| 测试 fixture：原 test_commits.py 用扁平 entries 提交；本变更后这些仍应工作（"扁平"现在也是合法输入，只是 service 内部 nested 化） | 低 | 测试断言失败 | AC-13 显式跑；如失败说明设计破了向后兼容，必须修而非接受 |

## 跨链路一致性自审

1. ✅ summary 已写
2. ✅ 范围 / 非范围明确
3. ✅ AC 全可机械化
4. ✅ AC 分层：4 behavioral
5. ✅ 非豁免（动 apps/api + scripts/_self_check.sh）
6. ✅ 反向 grep 无需 test -f 前置
7. ✅ spec ↔ tasks ↔ self_check 一致
8. ✅ process_tasks 6 节点齐（stage 2/4/6 走完整 reviewer spawn，不 self-attest）

## 受影响模块

- 改：`apps/api/dataplat_api/schemas/tree.py`（Literal 放宽 + docstring）
- 改：`apps/api/dataplat_api/services/commit.py`（新增 `_validate_tree_paths` / `_normalize_to_nested`；改 `create_commit` 步骤 2 + 4）
- 改：`apps/api/dataplat_api/routers/commits.py`（`get_tree` 加 `?recursive`；新 `get_subtree_by_hash` 端点）
- 新建：`apps/api/tests/test_tree_nested.py`（≥ 8 用例）
- 改：`scripts/_self_check.sh`（追加 `run_tree_nested_domain` 14 AC + filter + 全跑入口）

## 不受影响

- `packages/core/src/dataplat_core/domain/tree.py`：domain 早就支持 entry_type=tree；不动
- `apps/api/dataplat_api/models/tree.py`：TreeORM / TreeEntryORM 早就用 String(8)；不动
- Alembic migrations：无 schema 变化
- `apps/api/dataplat_api/runner/processor_runner.py` / `adapter_runner.py`：仍传扁平 entries，service 自动 nested
- 所有 processor / adapter 实现：一行不动
- Web UI（独立 follow-up）

## 引用

- 上游 close：`commit-api-mvp-20260517` § "MVP 仅支持单层 entry_type='blob'；嵌套 tree 留 follow-up tree-nested-*"
- 上游 close：`processor-framework-20260517` 反哺 follow-up 清单含 `tree-nested-*`
- `packages/core/src/dataplat_core/domain/tree.py`：domain 已声明 Literal["blob", "tree"]
- `apps/api/dataplat_api/services/commit.py:53-70`：`_canonical_tree_bytes` / `_tree_hash` 现状
- `apps/api/dataplat_api/routers/commits.py:211-238`：`get_tree` 现状
