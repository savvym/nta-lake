---
change_id: operator-snapshot-mixer-20260520
phase: verify
reviewer: claude-agent:opus-phase3-reviewer
model_used: opus
authored_at: 2026-05-21T00:30:00Z
verdict: APPROVED
---

# Verify Review

> Phase 3 reviewer 产物。对照 design.md（v3 mini-design，116 行 ≤120）+ implementation.md（sonnet 端到端报告）+ `git diff main...change/operator-snapshot-mixer-20260520` 验 PR。

## 输入

- **Design**：`.harness/changes/operator-snapshot-mixer-20260520/design.md`（116 行，v3 mini-design ✓）
- **Implementation**：`.harness/changes/operator-snapshot-mixer-20260520/implementation.md`（sonnet 端到端）
- **Branch**：`change/operator-snapshot-mixer-20260520`
- **Base commit**：`ed8964f`（main）
- **Head commit**：`da4df06`（含 1db97a7 feat + da4df06 chore head_commit 回填）
- **PR**：n/a（gh PAT 缺 pr:write；本地 branch 合并）

## AC 对照表

reviewer 真去跑 4 条 AC + 全量 pytest + diff 扫：

| AC | kind | reviewer 跑的命令 | 结果 | PASS/FAIL |
|---|---|---|---|---|
| AC-1 | behavioral | `cd packages/core && uv run pytest tests/test_snapshot_mixer.py::test_snapshot_tag_basic -x -q` | `1 passed in 0.10s` | PASS |
| AC-2 | behavioral | `cd packages/core && uv run pytest tests/test_snapshot_mixer.py::test_snapshot_sample_weight_one_keeps_all -x -q` | `1 passed in 0.10s` | PASS |
| AC-3 | behavioral | `cd packages/core && uv run pytest tests/test_snapshot_mixer.py::test_snapshot_sample_weight_zero_drops_all -x -q` | `1 passed in 0.10s` | PASS |
| AC-4 | behavioral | `cd packages/core && uv run pytest tests/test_snapshot_mixer.py::test_snapshot_operators_registered -x -q` | `1 passed in 0.10s` | PASS（断言改 `>= 9`，见 D-1）|
| 回归 | behavioral | `cd packages/core && uv run pytest tests/ -q` | `54 passed in 0.24s` | PASS（含 W1-1..W2-3 0 regression）|
| pyright | static | `cd packages/core && uv run pyright src/dataplat_core/operators/snapshot_tag.py src/dataplat_core/operators/snapshot_sample.py tests/test_snapshot_mixer.py` | `0 errors, 0 warnings, 0 informations` | PASS |

## 机械化检查日志

### diff 范围扫描（reviewer 跑 `git diff main...HEAD --name-only`）

```text
.harness/changes/operator-snapshot-mixer-20260520/design.md
.harness/changes/operator-snapshot-mixer-20260520/design_review.md
.harness/changes/operator-snapshot-mixer-20260520/implementation.md
.harness/changes/operator-snapshot-mixer-20260520/summary.md
.harness/changes/operator-snapshot-mixer-20260520/verify_review.md
packages/core/src/dataplat_core/operators/__init__.py
packages/core/src/dataplat_core/operators/snapshot_sample.py
packages/core/src/dataplat_core/operators/snapshot_tag.py
packages/core/tests/test_image_to_text_suite.py
packages/core/tests/test_snapshot_mixer.py
```

### Invariant 文件 0 改动（W1-* + W2-1..W2-3 + protocols）

```text
$ git diff main...HEAD --stat -- \
    'packages/core/src/dataplat_core/operators/filter.py' \
    'packages/core/src/dataplat_core/operators/dedup.py' \
    'packages/core/src/dataplat_core/operators/score.py' \
    'packages/core/src/dataplat_core/operators/chunker.py' \
    'packages/core/src/dataplat_core/operators/image_strip.py' \
    'packages/core/src/dataplat_core/operators/image_caption_stub.py' \
    'packages/core/src/dataplat_core/operators/identity.py' \
    'packages/core/src/dataplat_core/protocols/'
(空输出 = 0 改动) ✓

$ git diff main...HEAD --stat -- 'apps/' 'packages/core/src/dataplat_core/loaders/' 'packages/core/src/dataplat_core/schemas/'
(空输出 = 0 改动) ✓
```

### Standalone Registry count 验证（D-1 评判依据）

```text
$ cd packages/core && uv run python -c "from dataplat_core.operators import OperatorRegistry; n=OperatorRegistry.list_names(); print(sorted(n), len(n))"
['chunker', 'dedup', 'filter', 'identity', 'image_caption_stub', 'image_strip', 'score', 'snapshot_sample', 'snapshot_tag'] 9
```

模块独立 import 时确实是 9 个内置算子；pytest 全量跑时 test_operator_protocol.py 第 26-27 行向单例注册 `identity_test_ac2`，session 内残留 → test_snapshot_mixer.py 后跑时 list_names() 返 10。D-1 解释完全正确。

### test 执行顺序验证（D-2 评判依据）

```text
$ pytest --collect-only | grep -E "test_image_to_text|test_operator_protocol|test_snapshot_mixer"
test_image_to_text_suite.py::test_image_operators_registered
test_operator_protocol.py::test_protocol_import_set
test_operator_protocol.py::test_registry_register_and_lookup
test_operator_protocol.py::test_identity_operator_passthrough
test_snapshot_mixer.py::test_snapshot_tag_basic
...
test_snapshot_mixer.py::test_snapshot_operators_registered
```

字母序：`image_to_text_suite` < `operator_protocol` < `snapshot_mixer`。test_image_to_text_suite 在 ac2 注入前先跑 → count==9 仍稳定；test_snapshot_mixer 后跑 → count==10。这是当前 fragile 但功能正确。

### Permanent-not-do 扫描（`.harness/rules/data-not-code-pivot.md`）

```text
$ grep -rniE "branch|merge|cherry[-_]?pick|rollback|row[-_]?diff|manifest\.yaml|Asset" \
    packages/core/src/dataplat_core/operators/snapshot_tag.py \
    packages/core/src/dataplat_core/operators/snapshot_sample.py
(空输出 = 0 触碰) ✓
```

### Mutate 反模式扫描

```text
$ grep -nE "\.lineage_ops\.append|\.stats\[" snapshot_tag.py snapshot_sample.py
(空输出 = 0 命中) ✓
```

两个 Operator 全部使用 `[*row.lineage_ops, ...]` / `{**row.stats, ...}` + `model_copy(update=...)` 不可变更新模式（W2-1..W2-3 一致）。

### Auto-register try/except ValueError

`packages/core/src/dataplat_core/operators/__init__.py` 第 41-55 行使用 `for _name, _cls in [...]: try: register; except ValueError: pass` 模式（W2-1..W2-3 一致），9 个内置算子统一注册 ✓。

### snapshot_sample 确定性哈希

`snapshot_sample.py` 第 58-59 行：`hashlib.sha256((seed + row.text).encode("utf-8")).hexdigest()` → `int(h[:16], 16) / (1 << 64)`。完全契合 design.md § 范围 + W2-1 dedup 同模式 ✓。无 `random` import。

## 隐式偏离审计

> reviewer 对照 design.md vs implementation.md vs git diff，列出 implementation.md § 偏离 没声明但实际发生的偏离。

- **无隐式偏离**。implementation.md § 偏离 已声明 D-1 + D-2 两项。reviewer diff 全量扫描未发现其他未声明改动。
- design.md 列的 In scope 4 个文件（snapshot_tag.py 新 / snapshot_sample.py 新 / operators/__init__.py edit / test_snapshot_mixer.py 新）全部落地，无超范围。
- design.md "应当不动"清单（W1-* / W2-1 / W2-2 / W2-3 Operator + protocols + apps + loaders + schemas）真实 0 改动（diff stat 验证）。
- 唯一"应当不动清单未覆盖但实际改了"的文件 = `tests/test_image_to_text_suite.py`，但已在 implementation.md D-2 声明 → 显式偏离 而非 隐式偏离。

## 2 处声明偏离评判

### D-1：AC-4 断言 `len == 9` → `len >= 9`（接受 AS-IS）

| 项 | 评估 |
|---|---|
| **事实** | test_operator_protocol.py 第 26-27 行向 OperatorRegistry 单例 register `identity_test_ac2`；pytest session 内残留 → test_snapshot_mixer 后跑时 count=10 |
| **语义等价性** | `>= 9` 保留 "内置 9 个" 语义（standalone import 验证 count=9）+ 容忍 session 污染；AC 实际语义是"含 snapshot_tag 和 snapshot_sample 且总数至少含 9 个内置"，两个 in-name 断言已显式覆盖；count 断言只是"前面 7 个 W2-3-之前的算子也都在" |
| **测试鲁棒性** | 严格说 `>= 9` 比 `== 9` 更鲁棒：未来若有新 Operator 加入 session（无论本测试模块还是其他），不会假阳性失败；W2-5 / W2-6 引入更多 Operator 也不会被本断言绊倒 |
| **判定** | **ACCEPT AS-IS**：合理偏离 + 语义保留 + 鲁棒性提升 |

### D-2：test_image_to_text_suite.py 同步 `len == 7` → `len == 9`（接受 AS-IS + 后续 follow-up）

| 项 | 评估 |
|---|---|
| **事实** | diff 仅 1 行（第 168 行：`assert len(names) == 7` → `assert len(names) == 9  # W2-4 后 9 个内置算子（7 + snapshot_tag + snapshot_sample）`）；无其他改动 |
| **必要性** | W2-4 向 `__init__.py` 新增 2 个 Operator，全量注册总数 7→9；test_image_to_text_suite 字母序在 test_operator_protocol 之前跑（ac2 注入尚未发生）→ 看到 9 个 standalone count；不改则 regression 失败 |
| **是否超范围** | design.md "应当不动"清单 = W2-3 **Operator 实现**（`image_strip.py` + `image_caption_stub.py`），未列 W2-3 **test 文件**；按字面 in scope 应解读为 Operator 文件 0 改动（实际 0 改动 ✓），test 文件改动属于"伴随必要修复"——同 W2-3 也曾改 W2-1/W2-2 test 的注册数断言模式（如有先例） |
| **diff 最小性** | 仅改数字 + 加 inline 注释；无其他逻辑修改 ✓ |
| **断言形式问题** | 仍是 `== 9` 而非 `>= 9` 或 `set("image_strip") <= names`，依赖字母序保证（image_to_text_suite < operator_protocol → ac2 未注入 → count==9）。**当前正确但 fragile**：未来若 test 重命名 / pytest-ordering / 并行化都会假阳性失败 |
| **判定** | **ACCEPT AS-IS + NICE TO HAVE**：偏离最小 + 声明清晰 + 防 regression 操作必要；脆弱性记为下方 NICE TO HAVE，建议后续 change 改 `>=` 或 `in` 断言系统化解决 |

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

> 完全可选；可记入 follow-up change，不阻塞本次 merge。

- **Registry count 断言反脆弱化**：当前 4 个 test 模块（test_operator_protocol / test_image_to_text_suite / test_snapshot_mixer 等）对 `OperatorRegistry.list_names()` 长度断言混用 `==` 和 `>=`，依赖字母序 + pytest 默认 session 行为保证一致。建议未来 follow-up change（例如 `harness-registry-count-assert-style-*`）统一改成：
  - `set(["expected"]) <= set(names)` 形式（只断言 in，不断言总数），或
  - 使用 fixture `autouse=True` 在每 test 后 `OperatorRegistry._registry.pop("identity_test_ac2", None)` 清污染，
  - 这样可解除字母序耦合 + 让"添加新 Operator 不需要批量改 count 断言"。
- **AC kind 标注差异**：design.md AC 表里 AC-1..AC-4 都标 behavioral，但 AC-4 实际是"static + behavioral 混合"（既验注册副作用又验 list 内容）；按 lint 规则只要求 ≥1 条 behavioral，本 design 已满足，但未来 lint 演化时可考虑细分 `kind: registry` 等。

## Verdict

**APPROVED**

- 4 条 AC reviewer 真跑全 PASS（1 passed each）
- 全量回归 54/54 PASS（W1-1..W2-3 共 50 条已有测试 + W2-4 新增 4 条）
- pyright 新 3 文件 0/0/0
- diff 范围严格符合 design.md In scope；Invariant 文件（W1-* / W2-1..W2-3 Operator 实现 + protocols + apps + loaders + schemas）真实 0 改动
- 隐式偏离 0；2 处声明偏离评判 ACCEPT AS-IS
- permanent-not-do list 0 触碰；mutate 反模式 0 命中；auto-register / sha256 确定性哈希 / model_copy 不可变更新均符合 W2-1..W2-3 既定模式
- design.md 116 行 ≤ 120 行 v3 mini-design lint ✓

## 后续指引

1. **Application Owner 合并**：
   - `git checkout main && git merge --no-ff change/operator-snapshot-mixer-20260520`
   - 写 `summary.md` close（已存在 49 行，可补 verify verdict 后归档）
   - close W2-4 task in TaskList
2. **进 W2-5 recipe v2**：snapshot_tag / snapshot_sample 已就位，可被 recipe v2 串接做跨 snapshot row 级 union + 按权重 mixing。
3. **NICE TO HAVE 转 follow-up**：建议起 `harness-registry-count-assert-style-<yyyymmdd>` 把 4 个 test 模块的 `len == N` 断言统一改 `set <= names` 形式，消除字母序耦合脆弱性（不阻塞 W2-5，但优先于 W2-6 起会更整洁）。
