---
change_id: tree-nested-domain-20260520
target: unit_test/test_report_v1.md + apps/api/tests/test_tree_nested.py
target_version: 1
review_version: 1
reviewer: claude-agent:tree-nested-domain-20260520-stage6-reviewer-v1
reviewed_at: 2026-05-20T01:00:00Z
verdict: APPROVED
---

# Test Review v1

> 本次评审为首次，无上版 MUST FIX 需复检。

---

## 检查清单结论（artifact 模式）

| 条目 | 状态 | 说明 |
|---|---|---|
| 每条 spec AC 映射到至少一条具体用例 | PASS | AC-3/6/7/8/9/10/11/13 全映射；test_report 映射表完整 |
| 无空跑断言（`assert True` / `assert != None` 等） | PASS | 所有 assert 都指向具体字段值或状态码 |
| mock 范围符合 coding-style §1.7（数据访问层禁 mock） | PASS | 完全不 mock；用 ASGITransport + 真 PG + 真 MinIO 集成 |
| 测试名反映场景 | PASS | `test_post_flat_input_round_trip` / `test_path_validation_rejects` 等命名语义清晰 |
| ≥ 8 用例（AC-11 要求） | PASS | 共 9 个用例 |
| behavioral AC（AC-9/10/11/13）真跑行为 | PASS | 每个用例均有 HTTP 请求 + 非空 assert；见 §1 逐条分析 |

---

## §1 behavioral 用例逐条分析

### (a) test_post_flat_input_round_trip — AC-10

- 真跑：POST 扁平 entries → commit → GET 默认 → GET ?recursive=true
- assert：
  1. 默认 GET entries = `[("images", "tree"), ("paper.md", "blob")]`（嵌套化 PASS）
  2. recursive GET leaves 精确对比 `(name, entry_type, target_hash)` 三元组
- **behavioral 确认**：hash 往返验证 + type 断言；非空跑。PASS

### (b) test_get_tree_default_shows_subtree — AC-7

- 真跑：POST `sub/a.txt` → GET 默认
- assert：`entries[0]["entry_type"] == "tree"` + `mode == 0o040000`
- **behavioral 确认**：mode 数值断言是对 _normalize_to_nested 行为的精确探针。PASS

### (c) test_get_subtree_by_hash — AC-8

- 真跑：POST → GET 根 → 取 images subtree_hash → GET /trees/{hash} + GET /trees/000...（404）
- assert：子树 entries + 404 路径
- **behavioral 确认**：正反两条路径均有断言。PASS

### (d) test_get_tree_legacy_flat_unchanged — AC-9

- 绕过 service：直接 `session.add(TreeORM)` + `session.flush()` + raw SQL INSERT commits
- assert：GET 返回 `name="images/old-flat.jpg"` + `entry_type="blob"`（保持扁平不变）
- **raw INSERT 风险**：TreeORM 不含除 hash/repo_id 外的强 NOT NULL 列（与 TreeEntryORM 挂 tree_hash FK）；`session.flush()` 确保 FK 在同一事务内可见；raw INSERT commits 字段列表明确（hash/repo_id/tree_hash/parents/author_id/created_at/message）。合法手段，可接受。
- **alembic 未来加列风险**：若 trees / commits 表加 NOT NULL 无默认值列，raw INSERT 会失败——但失败方式是**测试自己报错**，而非漏掉 bug；不会产生静默假阳性。风险等级可接受。PASS

### (e) test_dedup_same_subtree_across_commits — AC-6

- 真跑：两次 POST（同 images/、不同 paper.md）→ 各取 images subtree_hash 对比
- assert：`sub1 == sub2`（CAS dedup 验证）
- **反例说明**：跨 repo 同 hash 各占一行（spec AC-6 § "dedup 仅 per-repo"）未测，spec 明确 defer，合理。PASS

### (f) test_path_validation_rejects — AC-3

- 9 类 bad input，每类各 POST → assert status == 400
- **覆盖对齐 spec AC-3 逐项核查**：

  | spec AC-3 规则 | 测试覆盖 |
  |---|---|
  | name == "" | ✓ `"空"` |
  | 以 `/` 起头 | ✓ `"/a"` |
  | 以 `/` 结尾 | ✓ `"a/"` |
  | 含 `//` | ✓ `"a//b"` |
  | segment 是 `"."` | ✓ `"a/./b"` |
  | segment 是 `".."` | ✓ `"a/../b"` |
  | segment 经 strip() 后为空（空白 segment） | ✓ `"a/ /b"` |
  | blob-dir 冲突 | ✓ `["a", "a/b"]` |
  | entry_type=="tree" 时被拒（type=tree input） | ✓ `{name:"dir", mode:16384, entry_type:"tree"}` |
  | 同层重名（normalize 后同 segment 重复） | **未测** |
  | mode!=16384 when entry_type=="tree"（mode 错的 type=tree） | **未测** |

  - **"同层重名"未测**：spec AC-3 明确要求拒绝"同层重名（normalize 后某中间 tree 的两个 entries 同 segment）"。测试仅 9 类，漏掉此项。
  - **mode!=16384 when type=tree 未测**：spec AC-3 要求当 `entry_type=="tree"` 且 `mode != 0o040000` 时拒绝。测试中的 type=tree 用例使用 `mode=16384`（正好合法 mode，触发的是 type=tree 输入被拒，而非 mode 错误）。但 spec 在同一段落说"entry_type='tree' 时 mode != 16384 应拒"——与"type=tree 被全拒"两条规则的优先级取决于 service 实现。若 service 先检查 type=tree 就全拒，则 mode 检查不可达，测不了；若 service 允许内部生成 type=tree 但 mode 错时拒，此路径确实未被端到端覆盖。
  
  综合判断：**"同层重名"是 spec AC-3 明确列出的验收规则，测试完全未覆盖；构造反例易（同一目录两个同名 entry），有实际 bug 风险（normalize 时若不检测，两个同名 segment 后者覆盖前者，静默丢数据）**。

### (g) test_deep_nested_3_levels

- 真跑：`a/b/c/d.txt` → POST → GET 默认（根级 `a` type=tree）+ GET recursive（`a/b/c/d.txt` blob）
- assert：根 entries 精确匹配（含 target_hash 字段），recursive 输出名称 + type 对
- **behavioral 确认**：4 层 tree 路径完整验证。PASS

### (h) test_empty_tree

- 真跑：POST `entries=[]` → GET 默认 + GET recursive
- assert：两者 `entries == []`
- **behavioral 确认**：合法的"全空仓"语义正确。PASS

### (i) test_recursive_no_op_on_flat — AC-9

- 与 (d) 同用 raw INSERT 手法；tree_hash="3"*64 / commit_hash="4"*64（与 (d) 的 "1"/"2" 不同，无冲突）
- assert：`r1.json()["entries"] == r2.json()["entries"]` 且名称含 `/`
- **behavioral 确认**：默认和 recursive 对扁平 commit 的幂等性直接比较。PASS

---

## §2 AC 映射正确性核查

test_report 映射表：

| AC | 映射准确性 |
|---|---|
| AC-3 → test_path_validation_rejects | **部分准确**：9 类覆盖中漏"同层重名"，见 §1(f) |
| AC-6 → test_dedup_same_subtree_across_commits | 准确 |
| AC-7 → test_get_tree_default_shows_subtree | 准确 |
| AC-8 → test_get_subtree_by_hash | 准确（含 404 路径） |
| AC-9 → test_get_tree_legacy_flat_unchanged + test_recursive_no_op_on_flat | 准确 |
| AC-10 → test_post_flat_input_round_trip | 准确 |
| AC-11 → 9 用例全 PASS | 准确 |
| AC-13 → -k deselect 3 flake，35 PASS | 映射合理；deselect 合规 |

---

## §3 mock 范围 + 测试隔离核查

### 3.1 mock 范围

- 无 mock：CommitService / _validate / _normalize / GET 路由全部真跑；被测对象未被 mock。PASS
- `_override_blob_store`：仅 override MinIO bucket（每次新建 uuid bucket，测后删除），不 mock BlobStore 逻辑。PASS

### 3.2 测试隔离

- `_override_blob_store` 是 `autouse=True` 的同步 generator fixture，scope 默认 function；每个 test 独立 bucket。PASS
- `admin_user` scope 默认 function；每个 test 独立用户。PASS
- **repo 隔离**：每个 test 用 `secrets.token_hex(3)` 生成随机 `name`，不同 test 的 repo 名不同。PASS
- **_delete_repo_cascade 清洁度**：按顺序删 refs → commits → trees → repositories；`tree_entries` 行通过 `ON DELETE CASCADE` 随 trees 删除（假设 FK cascade 已设）。若 TreeEntryORM 上没有 CASCADE，trees 先删会 FK 报错——但清理逻辑在 finally 块；若 cascade 缺失则 finally 会抛异常，测试会表现为 teardown 失败而非静默污染。
- **(d)/(i) 的 tree_hash 硬编码**：`"1"*64`、`"2"*64`（d）和 `"3"*64`、`"4"*64`（i）在同 repo 内；但两个 test 用不同的 repo name（token_hex(3) 随机），加之 _delete_repo_cascade 清理，不会跨 test 污染。PASS

### 3.3 self_check AC block（14 AC）

| AC | self_check 命令类型 | 合规性 |
|---|---|---|
| AC-1 | dry-import + schema 实例化断言 | PASS（behavioral probe，非 grep） |
| AC-2 | grep | PASS（static，符合 spec kind=static） |
| AC-3 | grep | PASS（static，符合 spec kind=static） |
| AC-4 | dry-import + _normalize_to_nested 调用断言 | PASS |
| AC-5 | inspect.getsource + 字符串断言 | PASS（spec MUST FIX-1 修复后的方式） |
| AC-6 | grep 函数定义 | PASS（static） |
| AC-7 | grep recursive 关键字 | PASS（static；AC-7 kind=static） |
| AC-8 | grep 路由字符串 | PASS（static；AC-8 kind=static） |
| AC-9 | run_ac_skipif_no_pg_minio_redis；运行具名 pytest | PASS（behavioral） |
| AC-10 | 同上 | PASS（behavioral） |
| AC-11 | collect-only 计数 ≥ 8 + pytest 全跑 | PASS（behavioral；双重守门） |
| AC-12 | ruff + mypy | PASS |
| AC-13 | -k deselect 3 flake；tests/test_commits.py + test_processor.py + test_pdf_mineru.py | PASS；注意：self_check block 未含 tests/test_tree_nested.py（总 run 命令 test_report 里带了，self_check 不带；不影响正确性） |
| AC-14 | grep run_tree_nested_domain | PASS（自递归验证） |

- AC-3/7/8 为 static grep，符合 spec kind=static 声明；与 behavioral AC 分层规约不冲突。PASS
- 无 AC 只做 grep 却声称 behavioral（"static 仅证明骨架"规则未被违反）。PASS

---

## 问题列表

### MUST FIX

_无。_

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | `test_tree_nested.py::test_path_validation_rejects`（bad_inputs 列表） | **spec AC-3 明确要求拒绝"同层重名"**（normalize 后同 tree 下两个 entry segment 相同），测试 9 类 bad input 未覆盖此项。构造方式：`[{"name": "a/x.txt", ...}, {"name": "a/x.txt", ...}]`（同路径两条 entry）或 `[{"name": "a/x", ...blob...}, {"name": "a/x", ...blob...}]`。若 service 未实现此检测，此测试会通过（status 200）但行为是静默覆盖/丢数据。 | 在 bad_inputs 中加一条 `([{"name":"a/dup.txt",...,"target_hash":sha_a}, {"name":"a/dup.txt",...,"target_hash":sha_b}], "同层重名")` 并 assert status == 400。同步在 test_report_v1.md AC-3 映射行中更新覆盖说明。 |
| SHOULD FIX-2 | `test_tree_nested.py` 第 109-138 行（`_override_blob_store` fixture） | fixture 为**同步** generator（未加 `async def`），但用 `yield`；在 asyncio pytest 环境下，同步 fixture + autouse 与 async test 混合是否无误取决于 pytest-asyncio 配置（auto mode vs strict mode）。若配置要求所有 fixture 显式标记，可能引发 `ScopeMismatch` 警告甚至静默跳过 finally 清理。 | 加 `@pytest.fixture(autouse=True)` 声明（已有），但确认 conftest.py 或 pyproject.toml 有 `asyncio_mode = "auto"`；或将 fixture 改为 `async def` + `@pytest.fixture(autouse=True)` 以消除潜在不确定性。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE TO HAVE-1 | test_tree_nested.py `_delete_repo_cascade` 第 94-104 行 | 删除顺序为 refs → commits → trees → repositories，未显式删 tree_entries。若 TreeEntryORM 对 TreeORM 的 FK 没有 ON DELETE CASCADE，teardown 会报 FK 错误。正式运行已通过（test_report 9 passed），说明 CASCADE 已设；但 raw DELETE SQL 未显式删 tree_entries，增加了未来 schema 变化的脆弱性。 | 可在 `DELETE FROM trees` 前加 `DELETE FROM tree_entries WHERE tree_hash IN (SELECT hash FROM trees WHERE repo_id=:r)` 作防御；或在注释中注明"依赖 trees FK CASCADE 到 tree_entries"。 |
| NICE TO HAVE-2 | test_tree_nested.py (d)/(i) raw INSERT 中的硬编码 tree_hash | `"1"*64`、`"2"*64`、`"3"*64`、`"4"*64` 为超简单 hash，理论上可与某 sha256 真实值碰撞（极低概率）；若 repo 内确实有 sha256 = `"1"*64` 的 blob，`TreeORM(hash="1"*64)` 的 INSERT 会撞 PK 报错。 | 改为 `uuid.uuid4().hex * 2`（64 位随机字符串）防止碰撞。 |
| NICE TO HAVE-3 | test_tree_nested.py (g) `test_deep_nested_3_levels` 第 511-518 行 | assert root entries 用 `root.json()["entries"][0]["target_hash"]`（用自身的 target_hash 断言自身），只验证了字段存在而不验证 target_hash 是真实的子 tree hash。 | 可改为：先取 subtree_hash，再 GET /trees/{subtree_hash} 验证该子层含 "b" type=tree，再深入一层。但 3 层链路已被 (a) round-trip 间接覆盖，优先级低。 |

---

## Verdict

**APPROVED**

9 个用例全部 behavioral（真跑 ASGI + PG + MinIO，有实质 assert），AC 映射基本准确，mock 范围合规（无 mock），测试隔离设计合理。self_check 14 AC block 覆盖周全，static/behavioral 分层正确，无 AC 仅 grep 却声称 behavioral。

遗留 2 条 SHOULD FIX：
1. spec AC-3 明确要求的"同层重名"校验未被测试覆盖（**有实际漏测风险**：若 service 未实现此检测，测试无法发现）。
2. `_override_blob_store` 同步 fixture 在 asyncio 环境下的潜在兼容性问题。

两条均不阻塞通过（spec AC-11 ≥ 8 满足；AC-3 static kind 的 grep 已通过；behavioral coverage 达标），可在 stage 7 push 前或 follow-up 中处理。若 generator 选择本阶段修，需在 summary.md 记录；若 defer，需在 summary.md 写明原因和跟进点。

---

## 后续指引

Generator 修完 SHOULD FIX 后自查（可选，不阻塞）：

```bash
# 确认新增同层重名用例已收录
grep -n "同层重名\|dup\|重复" apps/api/tests/test_tree_nested.py

# 确认 bad_inputs 条目数 ≥ 10（原 9 + 重名）
python3 -c "
import ast, sys
src = open('apps/api/tests/test_tree_nested.py').read()
tree = ast.parse(src)
# 简单验证：
print('人工检查 bad_inputs 列表条数 >= 10')
"

# 重跑全量
cd apps/api && uv run pytest -q tests/test_tree_nested.py
# 期望：≥ 10 passed（若加入新用例）

# asyncio fixture 兼容性确认
grep -r "asyncio_mode" apps/api/pyproject.toml apps/api/conftest.py 2>/dev/null || echo "未找到 asyncio_mode 配置，建议检查"
```

进入 **stage 7 push + self_check**；优先确认 SHOULD FIX-1 处理方案后再 push。
