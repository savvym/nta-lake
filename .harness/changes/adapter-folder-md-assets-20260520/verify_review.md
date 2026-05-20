---
change_id: adapter-folder-md-assets-20260520
phase: verify
status: approved
reviewer: opus
reviewed_at: 2026-05-21T03:55:00Z
verdict: APPROVED
---

# Verify Review：folder md+assets adapter (W3-2)

## 验证结果

| AC | kind | 结果 | 证据 |
|---|---|---|---|
| AC-1 auto_registered | behavioral | PASS | `pytest ::test_folder_md_assets_auto_registered -x -q` → 1 passed in 0.10s |
| AC-2 ingest_happy | behavioral | PASS | `pytest ::test_folder_md_assets_ingest_happy -x -q` → 1 passed in 0.10s |
| AC-3 rejects_unsafe_paths | behavioral | PASS | `pytest ::test_folder_md_assets_rejects_unsafe_paths -x -q` → 1 passed in 0.10s（"/abs.md" / "../escape.md" / "" 三种全覆盖 match "非法相对路径"） |
| AC-4 requires_md | behavioral | PASS | `pytest ::test_folder_md_assets_requires_md -x -q` → 1 passed in 0.10s（match "至少一个 .md"） |

## 全套测试

`cd packages/core && uv run pytest tests/ -x -q` → **70 passed in 0.28s**（66 旧 + 4 新，与 implementation.md 声明一致）

raw-upload 回归 `pytest tests/test_adapter_raw_upload.py -x -q` → **4 passed**（W3-1 未受影响）

## Diff 扫描

修改文件（`git diff main..HEAD --name-only`）：

- `packages/core/src/dataplat_core/adapters/folder_md_assets.py`（新，114 行）
- `packages/core/src/dataplat_core/adapters/__init__.py`（改，+8 行）
- `packages/core/tests/test_adapter_folder_md_assets.py`（新，66 行）
- `.harness/changes/adapter-folder-md-assets-20260520/{design,design_review,implementation,summary,verify_review}.md`

scope 内：**YES**。未动 raw_upload.py / registry.py / protocols/ / apps/api / apps/web / W1-* / W2-* / W3-1 产物。

永不做清单 grep：**clean**（命中均为 design.md / summary.md 里"决策 7：不做 manifest.yaml"的元声明，非代码引入；无 row-diff / cherry-pick / rollback / dataset-card.yaml 行为）

## 不变量校验

- ingest 顺序（pydantic → path safety → 重复 path → .md 数量）：**OK**（folder_md_assets.py:79-106 严格按 design.md 顺序；AC-3 测试 path 含 .md 后缀，path safety 先生效与 design 一致）
- path safety 拒绝条件（空 / 绝对 / `..` 三种 + 消息含 "非法相对路径"）：**OK**（line 87-94）
- asset_count 语义（= 非 .md 文件数）：**OK**（line 104 `md_count = sum(... .lower().endswith(".md"))`；line 109 `asset_count = len(files) - md_count`）
- list_names 测试用 `in` 而非 `== N`：**OK**（test line 14 `assert "folder-md-assets" in names`，W2-4 反脆弱教训已吸收）
- auto-register idempotent（try/except ValueError）：**OK**（__init__.py:12-20）
- pydantic ConfigDict(extra="forbid") + sha256 pattern 在 input_schema 一致：**OK**

## Verdict

**APPROVED**

- 4/4 AC PASS（机械化证据齐全）
- scope 干净（只动声明范围内文件）
- 永不做清单 clean
- 实现严格遵循 design 决策 1-7
- implementation.md "无偏离" 声明经 diff 比对真实
- 与 W3-1 raw-upload 模板高度一致，验证模板可复用性（design 立项目标）

## NICE TO HAVE / Deferred

- follow-up `adapter-folder-md-assets-route-*`：apps/api 加 POST /repos/.../folder-md-assets 路由 + worker（design 已声明）
- follow-up `adapter-folder-md-assets-mime-sniff-*`：content-type 推断（design 已声明）
- follow-up `adapter-folder-md-assets-zip-stream-*`：服务端 zip 流式解压（design 已声明）
- （观察）asset_count 在 raw-upload vs folder-md-assets 语义不同（前者 `1 if asset_id else 0`，后者非 .md 文件数）；caller 须按 adapter.name 分支处理；design § 风险表 1 已声明，不阻塞
