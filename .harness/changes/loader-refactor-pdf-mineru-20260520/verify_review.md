---
change_id: loader-refactor-pdf-mineru-20260520
phase: verify
reviewer: claude-agent:opus-phase3-reviewer
model_used: opus
authored_at: 2026-05-20T10:30:47Z
verdict: APPROVED
---

# Verify Review

> Phase 3 reviewer 产物。对照 design.md（原始要求）+ implementation.md（声称的实现）+ `git diff main...change/loader-refactor-pdf-mineru-20260520` 验 PR。
> v3 mini-design 流程（D-13）：本 change 无 Phase 1 reviewer 阶段，design 由 application-owner 自写；Phase 3 直接验。

## 输入

- **Design**：`.harness/changes/loader-refactor-pdf-mineru-20260520/design.md`（v3 mini-design，application-owner 自写）
- **Implementation**：`.harness/changes/loader-refactor-pdf-mineru-20260520/implementation.md`（sonnet 自报）
- **Git diff**：`git diff main...change/loader-refactor-pdf-mineru-20260520`（10 files, +694 lines）
- **Branch**：`change/loader-refactor-pdf-mineru-20260520`（head: `e14f946`；3 commits ahead of merge base `0e4bf66`：`daf820a` 主实现 + `2ad6003` impl.md 回填 + `e14f946` nit fix）
- **PR**：n/a（gh PAT 缺 pr:write；直接 branch ref）

## AC 对照表

每条 AC 真去跑命令验证：

| AC | kind | reviewer 跑的命令 | 结果 | PASS/FAIL/NOT-VERIFIABLE |
|---|---|---|---|---|
| AC-1 | behavioral | `cd packages/core && uv run pytest tests/test_loader_registry.py -x -q` | `1 passed in 0.01s` | PASS |
| AC-2 | behavioral | `cd apps/api && uv run pytest tests/test_pdf_mineru_loader.py::test_load_returns_single_silver_row -x -q` | `1 passed in 0.59s` | PASS |
| AC-3 | behavioral | `cd apps/api && uv run pytest tests/test_pdf_mineru_loader.py::test_load_missing_env_raises -x -q` | `1 passed in 0.56s` | PASS |

## 机械化检查日志

```text
$ cd packages/core && uv run pytest tests/test_loader_registry.py -x -q
.                                                                        [100%]
1 passed in 0.01s

$ cd apps/api && uv run pytest tests/test_pdf_mineru_loader.py::test_load_returns_single_silver_row -x -q
.                                                                        [100%]
1 passed in 0.59s

$ cd apps/api && uv run pytest tests/test_pdf_mineru_loader.py::test_load_missing_env_raises -x -q
.                                                                        [100%]
1 passed in 0.56s

$ cd apps/api && uv run pytest tests/test_pdf_mineru.py -q
.........                                                                [100%]
9 passed in 0.65s

$ git diff --stat main...HEAD
 .../loader-refactor-pdf-mineru-20260520/design.md  |  98 +++++++++++++++
 .../implementation.md                              |  86 +++++++++++++
 .../loader-refactor-pdf-mineru-20260520/summary.md |  49 ++++++++
 .../verify_review.md                               |  81 ++++++++++++
 apps/api/dataplat_api/loaders/__init__.py          |  14 +++
 apps/api/dataplat_api/loaders/pdf_mineru.py        | 134 ++++++++++++++++++++
 apps/api/tests/test_pdf_mineru_loader.py           | 139 +++++++++++++++++++++
 .../core/src/dataplat_core/loaders/__init__.py     |  11 ++
 .../core/src/dataplat_core/loaders/registry.py     |  48 +++++++
 packages/core/tests/test_loader_registry.py        |  34 +++++
 10 files changed, 694 insertions(+)

$ git diff main...HEAD -- apps/api/dataplat_api/processors/pdf_mineru.py | wc -l
0

$ git diff main...HEAD -- apps/api/dataplat_api/processors/__init__.py | wc -l
0

$ git diff main...HEAD -- packages/core/src/dataplat_core/operators/ | wc -l
0

$ git diff main...HEAD -- packages/core/src/dataplat_core/schemas/ | wc -l
0

$ git diff main...HEAD -- packages/core/src/dataplat_core/protocols/loader.py | wc -l
0
```

老 PdfMineruProcessor 及其 `__init__.py` 注册 / `packages/core/operators/` / `packages/core/schemas/` / W1-2 落地的 `protocols/loader.py` 全部 0-byte diff，design § 决策 1 + § 交叉引用清单 "应当不动" 列表完整兑现。

## 隐式偏离审计

> reviewer 对照 design.md vs implementation.md vs git diff，列出 implementation.md § 偏离 没声明但实际发生的偏离。**隐式偏离 = MUST FIX**。

逐项核对 design § In scope：

- `packages/core/src/dataplat_core/loaders/__init__.py` + `registry.py`：均新建；`LoaderRegistry` 含 staticmethod `register/get/list_names`；重复 ValueError、缺失 KeyError；与 `operators/registry.py` 结构逐字对齐（仅类名 / 错误消息中 "Loader" 替换 "Operator"）。**对齐。**
- `loaders/__init__.py` export `LoaderRegistry`：`__all__ = ["LoaderRegistry"]`。**对齐。**
- `apps/api/dataplat_api/loaders/__init__.py` + `pdf_mineru.py`：均新建；`__init__.py` import `PdfMineruLoader` 并调 `LoaderRegistry.register("pdf-mineru", PdfMineruLoader)`，与 `processors/__init__.py` 自动注册模式一致。**对齐。**
- `PdfMineruLoader` 四属性：`name = "pdf-mineru"`、`version = "0.1"`、`input_subtype = "pdf"`、`output_schema_id = "silver-text-v1"`。**全齐。**
- `load()` 输入 `(bronze_blob_sha: SHA256, config: dict, ctx: RunContext) -> LoadResult`：签名匹配 Loader Protocol。**对齐。**
- ctx.blob_store 缺失 → ValueError：`getattr(ctx, "blob_store", None)` is None 时 raise，与 design § 风险 ctx 兜底模式一致。**对齐。**
- env 处理：`MINERU_API_URL` 必需（缺则 ValueError，消息含 "MINERU_API_URL"）；`MINERU_API_TOKEN` 可选。**对齐。**
- MinerU 调用流：`client.submit → _wait_terminal → client.fetch_full_result`；复用 `apps/api/dataplat_api/processors/_mineru_client.py` 与 `pdf_mineru.PdfMineruSpec` / `_wait_terminal`。**对齐。**
- SilverRow 5 字段：
  - `text` = `full["markdown"]`。**对齐。**
  - `images` = 先 `blob_store.put(BytesIO(bytes), declared_size=len)` 再以 `{"filename", "blob_sha"}` 入 row（CAS dedup 关键路径正确）。**对齐。**
  - `source_ref` = `{"blob_sha", "loader": "pdf-mineru", "loader_version": "0.1"}`。**对齐。**
  - `stats` = `{"text_chars": len(markdown), "image_count": len(images)}`。**对齐。**
  - `lineage_ops = []`（Loader 不属于 lineage_ops）。**对齐。**
- `LoadResult(rows=[row], total_count=1, notes=f"pdf-mineru via {api_url}")`：**对齐。**
- 一个 PDF blob → 一个 SilverRow（不按页拆分）：**对齐**（决策 4）。
- 测试用例：`test_loader_registry.py` 1 case 覆盖 register/get/list_names/重复 ValueError/缺失 KeyError；`test_pdf_mineru_loader.py` 2 cases 覆盖 AC-2 全字段断言 + AC-3 缺 env raise。**对齐。**

Out of scope 核查：

- 老 `PdfMineruProcessor` / `processors/__init__.py` 0-byte diff。**符合。**
- 不动 worker / API recipe 调度：本 change 仅新增文件，未触 runner / endpoints。**符合。**
- 不动 commit/snapshot 写入：未触 `commit_writer` / `silver_writer` / `repo`。**符合。**
- 不实施 row schema 校验：`load()` 不调 `silver_schemas.validate(...)`。**符合**（W2-5 才接）。
- 不支持批量：单 blob → 单 row。**符合。**
- 不生成 content_list.json 附产物：`full.get("images")` 写入，`content_list` 字段忽略（test mock 中 `content_list: None` 也确实未消费）。**符合。**

D-1 / D-11 / D-13 / 永不做清单：

- **D-1**（DB schema 不动）：本 change 不涉及 DB，0 diff。
- **D-11**（理论单 commit）：主实现 1 个（`daf820a`）+ impl.md 回填 1 个（`2ad6003`）+ nit fix 1 个（`e14f946`，去掉未用 logging/os/MagicMock import）；与 W1-2 nit fix 模式一致，可接受。
- **D-13**（v3 mini-design）：design 由 application-owner 自写，无 Phase 1 reviewer cycle；frontmatter `process_variant: v3-mini-design` 标识正确。
- **永不做清单**（`.harness/rules/data-not-code-pivot.md`）：本 change 未引入 branch/merge/cherry-pick/rollback/row-diff/blob 派生图/Asset/manifest.yaml/silver 文件树/bronze 强 schema 任一禁项。

**结论**：implementation.md § 偏离 节声称"无偏离"——审计后**确认无任何显式或隐式偏离**。

## 问题列表

### MUST FIX

- 无。

### SHOULD FIX

- 无。

### NICE TO HAVE

- `PdfMineruLoader.load` 内部用 `asyncio.run(_run())`，意味着当未来 caller（W2-5 recipe v2）在 async 上下文调用时需走 `asyncio.run_in_executor` 或重构为 async 接口。当前 Loader Protocol 是 sync 签名，本 change 没有偏离 Protocol；W2-5 接 worker 时若 caller 是 async，可考虑给 Loader Protocol 加 `aload(...)` 异步入口，或让 Loader 直接 async。本 change 不需改。
- `test_load_returns_single_silver_row` 用 `_put_counter` 生成有序 fake sha，未验"同一图片字节复用同一 sha"（真 CAS dedup 语义）；当前断言只查 `len(blob_sha) == 64`。若 W2-2 chunker 接入后强化 dedup 不变量，建议补一个用例：put 同样 bytes 两次返同一 sha（需 fake blob_store 用 sha256 计算而非计数器）。follow-up，不阻塞 merge。
- `pdf_mineru.py:78-82` 对 `blob_store.get` 返 stream（`AsyncGenerator`）的兜底分支当前测试未覆盖（fake 返 bytes 直接走 isinstance 通过）。设计意图清晰，留作 follow-up。

## Verdict

**APPROVED**

- 3/3 AC PASS（实测命令日志见上）
- 老 `PdfMineruProcessor` + 注册 + operators/ + schemas/ + protocols/loader.py 全 0-byte diff（design § 决策 1 + 交叉引用清单完整兑现）
- 老 Processor 9 个回归测试全 pass
- LoaderRegistry 与 OperatorRegistry 结构逐字对齐
- SilverRow 5 字段语义、CAS dedup 路径（先 put 再写 sha）、env 约束消息文案、auto-register 模式全部精确兑现 design
- implementation.md 声称"无偏离"——审计确认
- D-1 / D-11（可接受 nit fix）/ D-13（v3 mini-design 流程合规）/ 永不做清单全部不违反
- 无 MUST FIX、无 SHOULD FIX；仅 3 条 NICE TO HAVE 建议（async 重构 / dedup 强化用例 / stream 兜底分支测试），均 follow-up 不阻塞

## 后续指引

1. Application Owner 直接 squash-merge `change/loader-refactor-pdf-mineru-20260520` → main（无须再 spawn Phase 3 / sonnet）。
2. 回填 `summary.md` § 阶段进度（Phase 2 / Phase 3 commit + verdict）+ § 交付（Merge commit + 关闭时间）。
3. Close W1-4 change；推进 Wave 1 末尾 checkpoint（"end-to-end PDF demo 跑通新模型"）—— W1-4 已交付 Loader 侧，Operator 链与 recipe v2 调度待 W2-2 / W2-5。
4. 3 条 NICE TO HAVE 记入 follow-up（可在 W2-5 recipe v2 change 里一并考虑 async Loader 接口 + dedup 不变量测试）。
