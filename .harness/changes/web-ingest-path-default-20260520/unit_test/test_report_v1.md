---
change_id: web-ingest-path-default-20260520
version: 1
authored_at: 2026-05-20T11:25:00Z
status: waiting_review
---

# Test Report v1

## AC 映射

| AC | 测试 |
|---|---|
| AC-1 | grep + reverse grep (static) |
| AC-3a | repos.ingest-section.test.tsx 2 用例：默认 path / 用户编辑保留 |
| AC-3b | 全 web vitest 33 passed (15 files) |
| AC-4 | pnpm typecheck 0 errors |
| AC-5 | self_check grep |

## 测试文件

| 文件 | 用例 | 类型 |
|---|---|---|
| repos.ingest-section.test.tsx | 2（新建） | 集成（路由 + UI） |
| 其他 14 文件 | 31（不变） | — |

## Mock

mock 全 queries module；含 useEnqueueIngest / useUploadBlob（vi.fn）；
fireEvent.change(fileInput, defineProperty files) 模拟拖入文件。

## 本地

```
pnpm test -- --run                   33 passed (15 files)
pnpm --filter web typecheck          0 errors
self_check current                   14/14 PASS
```

## 下一步

stage 6 sonnet reviewer 复检。
