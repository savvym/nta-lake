---
change_id: repo-files-tab-20260517
version: 1
authored_at: 2026-05-17T16:30:00Z
status: draft
---

# Spec：Repo 详情页 Files 视图（HF 风格）+ Ref API

## 背景

11 个变更后 ingest 端到端可用，但用户实测发现：上传文件后**详情页看不到文件**。根因 UI 无法把 `main` ref 解析到 commit_hash——后端尚无 `GET /repos/{o}/{n}/refs/{name}`。用户提供 HuggingFace `Files and versions` tab 截图（docs/image.png）作目标 UX。

## 问题陈述

- `RefORM` 表已存在；`POST /commits` 时也已 upsert ref；**无路由查询**
- 前端 `useCommit(hash)` 要求 client 知 commit_hash；admin ingest 后跳 `/jobs/$id` 才能看到 commit_hash，但回到 repo 详情页时**不知道 `main` 在哪**
- 详情页只有 metadata 卡片，没有文件列表

## 范围

In scope：

- **后端**：`GET /repos/{owner}/{name}/refs/{ref_name}` → `{name, commit_hash}`（visibility-aware；404 不区分不存在 / 不可见）
- **前端**：queries.ts 加 `useRef(owner, name, refName)`；repo 详情页加 Files section（main ref → commit → tree entries 表格 + 每行下载链）
- 后端集成测试 ≥ 3；前端测试 ≥ 1
- self_check ≥ 13 AC

Out of scope（follow-up）：

- LIST refs：`ref-list-api-*`
- Ref 写操作 CRUD：`ref-write-api-*`
- 嵌套目录 / path 分级浏览：`tree-path-browse-*`
- 文件 size 列：`tree-entry-size-*`
- 每文件 last commit：`commit-history-per-file-*`
- 分支切换器：`web-multi-ref-selector-*`
- Search by path / 文件预览：各自

## 验收标准（13 AC + 验证方式）

- **AC-1** `schemas/ref.py` 含 `RefRead(name, commit_hash)`；extra=forbid。
  - 验证：`cd apps/api && uv run python -c "from dataplat_api.schemas.ref import RefRead; assert RefRead.model_config.get('extra')=='forbid'"`

- **AC-2** `services/ref.py`：`RefService.get_by_name`。
  - 验证：`cd apps/api && uv run python -c "from dataplat_api.services.ref import RefService; assert hasattr(RefService, 'get_by_name')"`

- **AC-3** `routers/repos.py` 加 `GET /repos/{owner}/{name}/refs/{ref_name}` 路由；visibility-aware；404 一致。
  - 验证：`cd apps/api && uv run python -c "from dataplat_api.routers.repos import router; paths={r.path for r in router.routes}; assert '/repos/{owner}/{name}/refs/{ref_name}' in paths"`

- **AC-4** `main.py` include（无改动）+ openapi.json 含路径。
  - 验证：`cd apps/api && uv run python -c "from dataplat_api.main import app; s=app.openapi(); assert '/repos/{owner}/{name}/refs/{ref_name}' in s['paths']"`

- **AC-5** Repo visibility 复用 RepoService；不重复 `_visibility_visible`。
  - 验证：`test -f apps/api/dataplat_api/services/ref.py && test -f apps/api/dataplat_api/routers/repos.py && ! grep -E "_visibility_visible" apps/api/dataplat_api/services/ref.py`

- **AC-6** queries.ts 加 `useRef` + `RefRead` 类型。
  - 验证：`grep -q "useRef" apps/web/src/lib/api/queries.ts && grep -qE "RefRead|/refs/" apps/web/src/lib/api/queries.ts`

- **AC-7** 详情页加 Files section。
  - 验证：`grep -qE "FilesSection|useRef" "apps/web/src/routes/repos/\$owner.\$name.tsx"`

- **AC-8** Files section 含 main/files/下载/链。
  - 验证：`grep -qE "main|files|下载" "apps/web/src/routes/repos/\$owner.\$name.tsx" && grep -q "/api/repos/" "apps/web/src/routes/repos/\$owner.\$name.tsx"`

- **AC-9** 前端 ≥ 8 测试全 PASS。
  - 验证：`[ "$(find apps/web/src -name '*.test.tsx' -o -name '*.test.ts' | wc -l)" -ge 8 ] && cd apps/web && pnpm test 2>&1 | tail -5 | grep -qE "passed"`

- **AC-10** 后端 `tests/test_refs.py` ≥ 3 测试。
  - 验证：`[ "$(cd apps/api && uv run pytest --collect-only -q tests/test_refs.py 2>&1 | grep -cE 'test_refs\.py::')" -ge 3 ]`

- **AC-11** ruff + mypy 全 PASS。
  - 验证：`uv run ruff check apps/api packages/core worker/src && uv run mypy apps/api/dataplat_api packages/core/src worker/src`

- **AC-12** `cd apps/web && pnpm typecheck && pnpm build && test -f dist/index.html`。

- **AC-13** `bash scripts/_self_check.sh repo-files-tab` PASS=13。

## 风险

1. 既有 admin ingest 数据需重启 API 才能见——刚刚 cookie 修复也要重启
2. ref 名 URL-encode 即可
3. 3-segment param 与既有 commits/tree 同形态
4. useRef 404→null 由 fetchJson 处理；UI 走 empty state
5. 跨 AC 一致性 SKILL 8 条 checklist 第五次回归；AC-5 反向 grep 配 test -f 前置

## 关键决策

| 决策 | 选择 |
|---|---|
| 只 GET single ref | 采用；LIST 留 follow-up |
| Path 命名 | `/repos/{o}/{n}/refs/{ref_name}` |
| 前端 Files 位置 | 详情页底部新 Card；不引 tabs |
| size 列暂不显 | 接受；follow-up |

## 跨 AC 自审 grep

```bash
grep -nE "事务前|事务内|事务外" spec.md   # 不适用
grep -nE "parents=\[\]" spec.md          # 不适用
grep -nE "! *grep" spec.md               # AC-5 1 次，guard 模板
grep -nE "2>/dev/null" spec.md           # 0
grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" tasks.md  # 期望 ≥ 6
grep -cE "test -f|cd apps|grep -q|pnpm|uv run" spec.md  # 期望 ≥ 12
```

## 流程偏离

无。SKILL 8 条 checklist 第五次回归。
