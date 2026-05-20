---
change_id: adapter-folder-md-assets-20260520
phase: design
status: approved
authored_at: 2026-05-21T03:05:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：folder md+assets adapter (W3-2，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

新增 `FolderMdAssetsAdapter` 到 `packages/core/src/dataplat_core/adapters/folder_md_assets.py`，把"已上传 zip / 文件夹内 `*.md + ./assets/*`"的 file refs 转成 IngestResult，保留相对路径并做 path-safety 校验，asset_count 等于非 .md 文件数。

## 背景

W3-1 已落 `RawFileUploadAdapter`（通用 binary → Bronze）+ `AdapterRegistry`（实例存储）；W3-2 按同模板落第二个 adapter，验证模板可复用性。

业务诉求（roadmap W3-2）：用户上传含 `doc.md + assets/img1.png` 的 zip / 拖拽含同结构的文件夹，平台保留**相对路径**（不扁平化），可区分 markdown 主体与图片素材。

与 raw-file-upload 的差异：

- raw-file-upload 是**类型不可知**：任何 (path, sha256) 都接受，asset_count = `1 if asset_id else 0`
- folder-md-assets 是**结构有意义**：
  - 至少 1 个 `.md` 文件（否则报错——不是 folder-md-assets，应走 raw-file-upload）
  - 路径必须相对（拒绝 `..` / 绝对路径 / 空）
  - `asset_count` = 非 `.md` 文件数（直观语义）

实际 zip 解压 / multipart 接收已由 raw-file-upload 上传链路完成（前端上传得到 blob sha256 列表）；本 adapter 只做"refs → IngestResult"。

## 范围

In scope：

- `packages/core/src/dataplat_core/adapters/folder_md_assets.py`（新）：
  - class `FolderMdAssetsAdapter`：name="folder-md-assets" / version="0.1" / output_subtype="folder-md-assets"
  - `input_schema`：与 raw-upload 同结构（files: [{path, sha256}], 可选 asset_id），path minLength=1
  - `ingest(spec, workspace, ctx) -> IngestResult`：
    - pydantic 校验 spec（同 raw-upload 风格 try/except）
    - **path safety**：每个 file.path 必须满足 `not path.startswith("/")` AND `".." not in PurePosixPath(path).parts` AND `path != ""`；任一违反 → raise ValueError 含 "非法相对路径" 子串
    - **至少 1 个 `.md`**：files 中 path.lower().endswith(".md") 的数量 ≥1；否则 raise ValueError 含 "至少一个 .md" 子串
    - 不允许重复 path（同 raw-upload）
    - `IngestResult.asset_count` = 非 `.md` 文件数（path.lower().endswith(".md") 判定）；`file_count` = len(files)；`files` = 全部 refs
- `packages/core/src/dataplat_core/adapters/__init__.py`（改）：
  - import + auto-register `FolderMdAssetsAdapter`（try/except ValueError，与 raw-upload 同模式）
  - `__all__` 加 `"FolderMdAssetsAdapter"`
- `packages/core/tests/test_adapter_folder_md_assets.py`（新）：4 个 behavioral 用例

Out of scope：

- **不**实际解压 zip / 不处理 multipart：上传链路是 raw-upload + apps/api blob endpoint（W3-1 已稳）
- **不**改 apps/api routes / runner：apps/api 接 packages/core registry 留 follow-up（与 W3-1 同节奏）
- **不**做 content-type sniff（如检测 png/jpg）：path 后缀够用；MIME 检测留 follow-up
- **不**做 dataset-card.yaml / manifest.yaml（D-1 永不做清单）
- **不**做 apps/web 拖拽 UI：W4 范围
- **不**改 SourceAdapter Protocol / RawFileUploadAdapter / AdapterRegistry

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | behavioral | import dataplat_core.adapters 后 get_default().list_names() 含 "folder-md-assets" | `cd packages/core && uv run pytest tests/test_adapter_folder_md_assets.py::test_folder_md_assets_auto_registered -x -q` | 1 passed |
| AC-2 | behavioral | happy path：spec={"files":[{"path":"doc.md","sha256":"a"*64},{"path":"assets/img.png","sha256":"b"*64}]} → IngestResult.file_count==2, asset_count==1, files[0].path=="doc.md", files[1].path=="assets/img.png" | `cd packages/core && uv run pytest tests/test_adapter_folder_md_assets.py::test_folder_md_assets_ingest_happy -x -q` | 1 passed |
| AC-3 | behavioral | path safety：绝对路径（"/etc/passwd"）、`..` 穿越（"../escape.md"）、空 path 三种都 → raise ValueError 含 "非法相对路径" 子串 | `cd packages/core && uv run pytest tests/test_adapter_folder_md_assets.py::test_folder_md_assets_rejects_unsafe_paths -x -q` | 1 passed |
| AC-4 | behavioral | 无 .md：spec={"files":[{"path":"assets/img.png","sha256":"a"*64}]} → raise ValueError 含 "至少一个 .md" 子串 | `cd packages/core && uv run pytest tests/test_adapter_folder_md_assets.py::test_folder_md_assets_requires_md -x -q` | 1 passed |

## 决策

1. **按 W3-1 raw-upload 模板复制**：refs-only adapter（不解压 zip）；上传链路复用 W3-1。Wave 3 adapter 系列的标准切口——adapter 做"refs → IngestResult"，blob 上传由 apps/api 路由 + raw-upload 链负责。
2. **path safety 用 PurePosixPath.parts 检查 `..`**：跨平台一致；不依赖 OS posix vs windows；`"a/../b".parts == ("a", "..", "b")` 可靠检测。
3. **asset_count 语义改为"非 md 文件数"**：与 raw-upload 的"asset_id 在则 1"不同；folder-md-assets 的语义更直观（图片即素材）；caller 看 IngestResult 立刻知道有几个素材。
4. **至少 1 个 .md 必需**：若 0 个 .md 则结构不符合 "md+assets"——应走 raw-file-upload；强制此约束让 adapter 选择有信息量。
5. **input_schema 不强 path pattern**：jsonschema 表达 `..` 检查太复杂；路径校验放代码里（与 W3-1 同模式：spec 内置校验，不引入 fastjsonschema）。
6. **不引入 ContentType 推断**：path 后缀（.md / .png / .jpg / ...）已足；细粒度 MIME sniff 留 follow-up `adapter-folder-md-assets-mime-sniff-*`。
7. **不做 dataset-card.yaml / manifest.yaml**：D-1 永不做清单（与 W3-1 决策 7 同 drift correction 节奏；本 change design 阶段已 grep 检查 roadmap.md W3-2 段，确认未提到 manifest）。

## 风险

| 风险 | 缓解 |
|---|---|
| asset_count 语义与 raw-upload 不一致让 caller 混乱 | 决策 3 显式记录；adapter 各有自己的 IngestResult 语义，caller 按 adapter.name 分支处理；不是 bug |
| Windows 路径反斜杠绕过 `..` 检查 | PurePosixPath 强制 posix 分隔；上传链路前端规范化为 posix 路径；若 future Windows zip 引入反斜杠路径，加 `"\\" not in path` 即可 |
| auto-register 顺序敏感 | try/except ValueError idempotent；与 W3-1 raw-upload 同模式；pytest 反复加载不破裂 |
| AdapterRegistry 测试 count regression | 已用 `name in names` 而非 `== N`（W2-4 教训） |
| roadmap drift（如 W3-2 spec 又含 manifest.yaml） | 已 grep roadmap.md W3-2 段；无 manifest 类违规 AC；决策 7 显式声明 |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/protocols/adapter.py`（SourceAdapter Protocol / IngestFileRef / IngestResult）
  - `packages/core/src/dataplat_core/protocols/runcontext.py`（RunContext）
  - `packages/core/src/dataplat_core/adapters/raw_upload.py`（**模板参考**，本 change 复用其 schema 形状）
  - `packages/core/src/dataplat_core/adapters/registry.py`（W3-1 已稳）
- 应当不动：
  - `apps/api/*`（全部不动）
  - `packages/core/src/dataplat_core/adapters/raw_upload.py`
  - `packages/core/src/dataplat_core/adapters/registry.py`
  - W1-* / W2-* / W3-1 所有产物
- 引用的其他 change：W1-2（Adapter Protocol）、W3-1（AdapterRegistry + raw-upload 模板）

## 关联 follow-up

- `adapter-folder-md-assets-route-*`：apps/api 加 `POST /repos/.../folder-md-assets` 路由 + worker
- `adapter-folder-md-assets-mime-sniff-*`：content-type 推断（png/jpg/webp）
- `adapter-folder-md-assets-zip-stream-*`：服务端 zip 流式解压 + 自动算 sha256
- `harness-data-not-code-grep-lint-*`：新 change 模板加"永不做清单" 自动 grep（W3-1 已埋）
