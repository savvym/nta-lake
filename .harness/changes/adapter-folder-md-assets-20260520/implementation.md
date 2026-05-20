---
change_id: adapter-folder-md-assets-20260520
phase: implementation
status: done
authored_at: 2026-05-21T03:30:00Z
author: sonnet-phase2-implementer
model_used: sonnet
branch: change/adapter-folder-md-assets-20260520
base_commit: fe6254d
---

# Implementation：folder md+assets adapter (W3-2)

## 落地文件

- `packages/core/src/dataplat_core/adapters/folder_md_assets.py`（新，~100 行）
- `packages/core/src/dataplat_core/adapters/__init__.py`（改，+6 行）
- `packages/core/tests/test_adapter_folder_md_assets.py`（新，~60 行 / 4 用例）

## 实现要点

- 按 W3-1 `raw_upload.py` 模板：pydantic `_FolderMdFile` / `_FolderMdSpec` + try/except → "FolderMdAssets spec 非法"
- 校验顺序：(1) path safety per file → (2) 重复 path → (3) 至少 1 个 .md；严格按 design.md 顺序
- path safety 用 `PurePosixPath(path).parts` 检测 `..`；`path == ""` 和 `path.startswith("/")` 并列；错误消息含 "非法相对路径"
- `asset_count = len(files) - md_count`（非 .md 数，design 决策 3）
- `__init__.py` try/except ValueError idempotent 追加注册；`__all__` 加 `"FolderMdAssetsAdapter"`

## 验证

- AC-1 PASS: "folder-md-assets" in get_default().list_names()（auto-register 测试通过）
- AC-2 PASS: file_count==2, asset_count==1, paths/sha256 正确（happy path 测试通过）
- AC-3 PASS: "/abs.md" / "../escape.md" / "" 均 raise ValueError match "非法相对路径"
- AC-4 PASS: 纯 png spec raise ValueError match "至少一个 .md"
- 全套：`cd packages/core && uv run pytest tests/ -x -q` → **70 passed**（66 旧 + 4 新）

## 偏离 design.md

无偏离。
