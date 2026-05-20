---
change_id: recipe-yaml-v2-20260520
phase: verify
status: approved
reviewer: opus-verify-agent
model_used: opus
authored_at: 2026-05-21T02:30:00Z
reviewed_at: 2026-05-21T02:30:00Z
head_commit: 860ffcd
verdict: APPROVED
---

# Verify Review

> Phase 3 reviewer 产物。对照 design.md（v3 mini-design，127 行）+ implementation.md（sonnet 端到端）+ `git diff main...change/recipe-yaml-v2-20260520` 验 PR。

## 输入

- **Design**：`.harness/changes/recipe-yaml-v2-20260520/design.md`（127 行，v3 mini-design）
- **Implementation**：`.harness/changes/recipe-yaml-v2-20260520/implementation.md`（sonnet 端到端，head_commit=860ffcd）
- **Branch**：`change/recipe-yaml-v2-20260520`
- **Commits**：`482ee20` (design) → `6dcaf86` (feat impl+test) → `860ffcd` (chore head_commit 回填)
- **PR**：n/a（gh PAT 缺 pr:write；本地 branch 合并）

## AC 对照表

reviewer 真跑 4 条 AC + 全量 pytest + diff 扫：

| AC | kind | reviewer 跑的命令 | 结果 | PASS/FAIL |
|---|---|---|---|---|
| AC-1 | behavioral | `cd packages/core && uv run pytest tests/test_recipe_v2.py::test_load_recipe_v2_valid -x -q` | `1 passed in 0.11s` | PASS |
| AC-2 | behavioral | `cd packages/core && uv run pytest tests/test_recipe_v2.py::test_load_recipe_v2_rejects_v1 -x -q` | `1 passed in 0.11s` | PASS |
| AC-3 | behavioral | `cd packages/core && uv run pytest tests/test_recipe_v2.py::test_run_recipe_v2_end_to_end -x -q` | `1 passed in 0.11s` | PASS |
| AC-4 | behavioral | `cd packages/core && uv run pytest tests/test_recipe_v2.py::test_run_recipe_v2_empty_operators -x -q` | `1 passed in 0.11s` | PASS |
| 全量回归 | behavioral | `cd packages/core && uv run pytest -x -q` | `58 passed in 0.27s` | PASS（W1-1..W2-4 共 54 + W2-5 新增 4，0 regression）|

## 机械化检查日志

### diff 范围扫描（reviewer 跑 `git diff main...HEAD --stat / --name-only`）

```text
$ git diff main...HEAD --name-only
.harness/changes/recipe-yaml-v2-20260520/design.md
.harness/changes/recipe-yaml-v2-20260520/design_review.md
.harness/changes/recipe-yaml-v2-20260520/implementation.md
.harness/changes/recipe-yaml-v2-20260520/summary.md
.harness/changes/recipe-yaml-v2-20260520/verify_review.md
packages/core/src/dataplat_core/recipe.py
packages/core/tests/test_recipe_v2.py

$ git diff main...HEAD --stat
 .harness/changes/recipe-yaml-v2-20260520/design.md            | 127 ++++++++
 .../recipe-yaml-v2-20260520/design_review.md                  |  58 ++++
 .../recipe-yaml-v2-20260520/implementation.md                 |  96 +++++++
 .harness/changes/recipe-yaml-v2-20260520/summary.md           |  55 +++
 .../recipe-yaml-v2-20260520/verify_review.md                  |  81 +++++
 packages/core/src/dataplat_core/recipe.py                     | 191 ++++++++++
 packages/core/tests/test_recipe_v2.py                         | 220 ++++++++++
 7 files changed, 828 insertions(+)
```

新增文件 2 个（recipe.py + test_recipe_v2.py） + harness 文档 5 个。范围严格符合 design.md In scope。

### Invariant 文件 0 改动核对（design.md "应当不动"清单）

```text
$ git diff main...HEAD -- \
    packages/core/src/dataplat_core/__init__.py \
    packages/core/src/dataplat_core/operators/__init__.py \
    packages/core/src/dataplat_core/loaders/registry.py \
    packages/core/src/dataplat_core/protocols/ \
    apps/api/
(空输出 = 0 改动) ✓
```

- `apps/api/*`（v1 Recipe + pipeline router + orchestrator）真实 0 改动 ✓
- W1-* / W2-1..W2-4 Operator 实现（filter / dedup / score / chunker / image_strip / image_caption_stub / snapshot_tag / snapshot_sample / identity）0 改动 ✓
- `packages/core/src/dataplat_core/protocols/*` 0 改动（SilverRow / LoadResult / Loader / Operator Protocol 仅引用未修改）✓
- `loaders/registry.py` + `operators/__init__.py` + `dataplat_core/__init__.py` 0 改动 ✓（design.md § 范围"如有 __all__ 则导出"决策——目前无 root export，按 design 保持现状）

### Schema / 关键不变量检查

```text
$ grep -n 'extra="forbid"\|Literal\[2\]\|min_length=1\|v1 deprecated\|RecipeRunResult\|class Recipe' \
    packages/core/src/dataplat_core/recipe.py
34:class RecipeLoaderSpec(BaseModel):
42:    model_config = ConfigDict(extra="forbid")
49:class RecipeOperatorSpec(BaseModel):
56:    model_config = ConfigDict(extra="forbid")
62:class RecipeV2(BaseModel):
71:    model_config = ConfigDict(extra="forbid")
73:    name: str = Field(min_length=1)
74:    version: Literal[2]
84:class RecipeRunResult(BaseModel):
93:    model_config = ConfigDict(extra="forbid")
128:    raise ValueError("recipe v1 deprecated; please use v2 (version: 2)")
```

| 不变量 | 期望（design.md） | 实际（recipe.py） | 结论 |
|---|---|---|---|
| `RecipeLoaderSpec` extra="forbid" | 必须 | line 42 ✓ | PASS |
| `RecipeOperatorSpec` extra="forbid" | 必须 | line 56 ✓ | PASS |
| `RecipeV2` extra="forbid" | 必须 | line 71 ✓ | PASS |
| `RecipeV2.version` Literal[2] | 必须 | line 74 ✓ | PASS |
| `RecipeV2.name` min_length=1 | 必须 | line 73 ✓ | PASS |
| `RecipeRunResult` extra="forbid" | 推荐 | line 93 ✓ | PASS |
| `RecipeRunResult` 字段 rows/total_input/total_output/loader_notes | 必须 | line 95-98 ✓ | PASS |
| `load_recipe_v2` 缺/异常 version → ValueError("v1 deprecated") | 必须 | line 126-128 ✓ | PASS |
| `run_recipe_v2` 步骤 1-7 顺序 | 必须 | line 161-191（loader_cls → loader() → blob_sha → load → list rows → linear ops → RecipeRunResult）✓ | PASS |
| stub TestLoader 在 test 文件 inline 定义 + try/except ValueError 注册 | 必须 | tests/test_recipe_v2.py line 25-46 ✓ | PASS |

### Permanent-not-do 扫描（`.harness/rules/data-not-code-pivot.md` 永不做清单）

```text
$ grep -rn 'branch\|merge\|cherry-pick\|row-diff\|rollback' \
    packages/core/src/dataplat_core/recipe.py \
    packages/core/tests/test_recipe_v2.py
(空输出 = 0 命中) ✓
```

本 change 不触碰 branch / merge / cherry-pick / rollback / row-diff / blob 派生图 / Asset / manifest.yaml / silver 文件树 / bronze 强 schema 任何一项 ✓。`run_recipe_v2` 返回 in-memory `RecipeRunResult`，不写 CAS / 不生 snapshot，符合 design.md § Out of scope 与"永不做清单"双约束。

### executor 步骤精读（design.md §run_recipe_v2 vs recipe.py line 160-191）

| design 步骤 | recipe.py 行 | 结论 |
|---|---|---|
| 1) `loader_cls = LoaderRegistry.get(recipe.loader.name)` | line 161 | ✓ |
| 2) `loader = loader_cls()` | line 164 | ✓ |
| 3) `blob_sha = recipe.loader.input["blob_sha"]`（缺 → KeyError） | line 167（直接 `[...]` 取值 → 缺 key 自动 KeyError） | ✓ |
| 4) `load_result = loader.load(blob_sha, recipe.loader.config, ctx)` | line 170 | ✓ |
| 5) `rows = list(load_result.rows); total_input = len(rows)` | line 173-174 | ✓ |
| 6) 逐个 operator：registry.get → 实例化 → row 级 extend 收集 → rows 替换 | line 177-183 | ✓ |
| 7) 返 `RecipeRunResult(rows, total_input, total_output=len(rows), loader_notes=load_result.notes)` | line 186-191 | ✓ |

无任何步骤丢失 / 顺序错乱 / 额外步骤插入。

### load_recipe_v2 精读（design.md §parser vs recipe.py line 106-130）

- str → `yaml.safe_load`：line 120 ✓
- 顶层 mapping 校验：line 121-122 抛 `ValueError("recipe yaml 顶层必须是 mapping (dict)")` ✓
- version 字段路由：line 126-128 `data.get("version") != 2` 则抛 `ValueError("recipe v1 deprecated; please use v2 (version: 2)")` ✓
- v2 合规 → `RecipeV2.model_validate(data)`：line 130 ✓
- 处理顺序：先查 version 再 pydantic 校验 → v1 错误信息友好（design.md § 风险 5 缓解）✓

### test_recipe_v2.py 精读

- stub `_StubRecipeV2Loader`（line 25-40）：定义 4 属性 + load() 返 1 SilverRow text=150 chars + notes="stub" ✓
- `try: LoaderRegistry.register(...) except ValueError: pass`（line 43-46）：W2-1..W2-4 一致 auto-register 容错 ✓
- `_make_ctx()`（line 56-58）：SimpleNamespace duck-typing RunContext ✓
- AC-1（line 66-102）：合规 yaml str 含 1 loader + 3 operators；断言 name/version/loader.name/operators 全字段 ✓
- AC-2（line 110-131）：双 case 覆盖（缺 version + 显式 version:1），全部断言 `ValueError` + `match="v1 deprecated"` ✓
- AC-3（line 139-188）：filter(min_chars=50) → chunker(max_chars=100) → snapshot_tag；total_input=1 / total_output=2 / 每行 lineage_ops 含 3 个 op + loader_notes="stub" 透传 ✓
- AC-4（line 196-220）：空 operators → 1→1 row 原样 + lineage_ops 空 list ✓

### 4 个 AC 命令完整输出

```text
$ cd packages/core && uv run pytest tests/test_recipe_v2.py::test_load_recipe_v2_valid -x -q
.                                                                        [100%]
1 passed in 0.11s

$ cd packages/core && uv run pytest tests/test_recipe_v2.py::test_load_recipe_v2_rejects_v1 -x -q
.                                                                        [100%]
1 passed in 0.11s

$ cd packages/core && uv run pytest tests/test_recipe_v2.py::test_run_recipe_v2_end_to_end -x -q
.                                                                        [100%]
1 passed in 0.11s

$ cd packages/core && uv run pytest tests/test_recipe_v2.py::test_run_recipe_v2_empty_operators -x -q
.                                                                        [100%]
1 passed in 0.11s
```

### 全量 pytest 尾段

```text
$ cd packages/core && uv run pytest -x -q
..........................................................               [100%]
58 passed in 0.27s
```

基线 54（W1-1..W2-4 累计）+ 本 change 新增 4 = 58 ✓。无任何 regression。

## 隐式偏离审计

> reviewer 对照 design.md vs implementation.md vs git diff，列出 implementation.md § 偏离 没声明但实际发生的偏离。**隐式偏离 = MUST FIX**。

- **无隐式偏离**。implementation.md § 偏离 明确写"无偏离。严格按 design.md In scope 落地"，reviewer 全量 diff + 不变量精读后**确认**：
  - In scope 2 个文件（recipe.py 新 + test_recipe_v2.py 新）全部落地，无超范围
  - design.md "应当不动"清单（apps/api / W1-* / W2-1..W2-4 Operator / protocols / loaders/registry / operators/__init__）真实 0 改动（diff stat 验证）
  - schema / 不变量 10 项全部 PASS
  - executor 7 步严格按 design 顺序，0 偏差
  - parser 4 项要点（safe_load / mapping check / version route / model_validate）全部到位
- design.md § 范围"如有 __all__ 则导出 `RecipeV2 / load_recipe_v2 / run_recipe_v2`"——`packages/core/src/dataplat_core/__init__.py` 当前**无** `__all__` 也无 root export，sonnet 按 design 该条件分支跳过这步，保持当前模块边界。**不算偏离**（design 显式给出"否则跳过"分支）。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

> 完全可选；记入 follow-up change，不阻塞 merge。

- **Root export 缺位**：`packages/core/src/dataplat_core/__init__.py` 仍无 `__all__`，下游若 `from dataplat_core import RecipeV2` 会失败。design.md 已在 § 范围明确"如有 __all__ 则导出；否则跳过"为合规选项，但**长期看**应在某个 follow-up（如 `dataplat-core-root-exports-*`）统一为核心 schema/loader/operator/recipe API 建一份 `__all__`，方便 API 层 import 与 wiki 文档化。当前 W2-5 不阻塞。
- **`run_recipe_v2` 缺 ctx.cancel_event 协作取消检查**：design.md 未要求，但未来运行长链 Recipe 时 worker 取消信号应该被尊重。可在 `recipe-runner-cooperative-cancel-*` follow-up 内补 `if ctx.cancel_event and ctx.cancel_event.is_set(): raise CancelledError()` 在 operator 循环顶部。本 change 范围内不涉及。
- **`load_recipe_v2` 接受 dict 输入未做"顶层必须是 mapping"防御**：当前 `isinstance(data, str)` 分支才检查 mapping；如 caller 直接传非 mapping 对象（极不常见），会在 `data.get("version")` 抛 `AttributeError` 而非 `ValueError`。design.md 未明确该路径要求，且签名是 `str | dict[str, Any]`（类型守约），caller 越界应该被静态检查拦下。**非阻塞**，可在未来同 follow-up 统一加 `isinstance(data, dict)` 防御。

## Verdict

**APPROVED**

- 4 条 AC reviewer 真跑全 PASS（1 passed each）
- 全量回归 58/58 PASS（W1-1..W2-4 共 54 条 + W2-5 新 4 条；0 regression）
- diff 范围严格符合 design.md In scope：仅动 `recipe.py` + `test_recipe_v2.py` + 5 个 harness 文档；Invariant 文件（apps/api / W1-* / W2-1..W2-4 Operator + protocols + loaders/registry + operators/__init__ + dataplat_core/__init__）真实 0 改动
- Schema / 不变量 10 项全部 PASS（extra="forbid" × 4 / Literal[2] / min_length=1 / RecipeRunResult 字段 / ValueError "v1 deprecated" 文案 / executor 7 步顺序 / stub auto-register 模式）
- 永不做清单 0 触碰；executor 不写 CAS / 不生 snapshot，与 W2-6 dataset-export-engine 职责分界清晰
- 隐式偏离 0；声明偏离 0；NICE TO HAVE 3 项全部非阻塞 follow-up

## 后续指引

1. **Application Owner 合并**：
   - `git checkout main && git merge --no-ff change/recipe-yaml-v2-20260520`
   - 把 verdict APPROVED 回填到 `summary.md`，归档 close
   - close TaskList #32 W2-5 Phase 3
2. **进 W2-6 dataset-export-engine**：`RecipeRunResult.rows` 已就位，可被 W2-6 拿去做 silver snapshot 持久化（写 CAS / 生 snapshot manifest）。
3. **NICE TO HAVE 转 follow-up（可延后到 W3）**：
   - `dataplat-core-root-exports-*`：统一 `dataplat_core.__init__.py` 的 `__all__`
   - `recipe-runner-cooperative-cancel-*`：`run_recipe_v2` 在 operator 循环加 cancel_event 检查
   - `recipe-yaml-v2-input-defensive-*`：对非 mapping dict 输入给友好 ValueError
4. **预告 W3 / follow-up（design.md § 关联 follow-up 已列）**：
   - `recipe-api-v2-routes-*`：apps/api POST /recipes/v2/runs 接入新 engine
   - `recipe-yaml-v2-repo-ref-input-*`：input.snapshot 支持 `bronze/owner/name@ref` 解析
   - `recipe-yaml-v2-cache-*`：基于 (recipe_hash, blob_sha) 结果缓存
