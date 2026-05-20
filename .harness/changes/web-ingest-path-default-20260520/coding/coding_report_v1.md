---
change_id: web-ingest-path-default-20260520
version: 1
authored_at: 2026-05-20T11:25:00Z
branch: change/web-ingest-path-default-20260520
base_commit: 35eacd6
head_commit: TBD
status: waiting_review
---

# Coding Report v1

## 改动文件

| 路径 | 改动 | 任务 |
|---|---|---|
| `apps/web/src/routes/repos/$owner.$name.tsx` | line 583 `path: \`content/${f.name}\`` → `path: f.name` | T-1 |
| `apps/web/src/routes/repos.ingest-section.test.tsx` | 新建 2 用例（默认 path = filename / 用户编辑保留） | T-2a |
| `scripts/_self_check.sh` | 加 run_web_ingest_path_default 5 AC + filter + 全跑入口 | T-3 |

display fixture 6 处保留（T-2b 验证）。

## 与 tasks 映射

| Task | 状态 | 备注 |
|---|---|---|
| T-1 业务代码 | done | 1 行改 |
| T-2a 单测 | done | 2 用例 |
| T-2b display fixture 保留 | done | 6 处 (4 files-section + 2 commits page) |
| T-3 self_check AC | done | 5 AC + filter + 全跑入口 |
| T-4 本地校验 | done | current 14/14 PASS / vitest 33 passed / typecheck 0 errors |

## 偏离 spec

无；按 v2 精确执行。

## 本地校验

```
typecheck: 0 errors
vitest: 33 passed (15 files)（含新 ingest-section.test.tsx 2 用例）
self_check current web-ingest-path-default-20260520: 14/14 PASS
```

## 下一步

stage 4 + 6 combined sonnet reviewer。
