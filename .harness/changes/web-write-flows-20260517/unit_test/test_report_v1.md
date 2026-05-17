---
change_id: web-write-flows-20260517
version: 1
authored_at: 2026-05-17T16:00:00Z
status: waiting_review
---

# Test Report v1

## AC ↔ 测试

| AC | 测试 |
|---|---|
| AC-1 | self_check AC-1 + `repos.new.test.tsx`（render + 必填校验） |
| AC-2 | self_check AC-2 + `jobs.$job_id.test.tsx`（queued / succeeded 状态） |
| AC-3 | self_check AC-3 + `commits.$owner.$name.$hash.test.tsx`（tree entries + 下载链） |
| AC-4~10 | self_check AC-4~10（grep 实现端关键 token） |
| AC-11 | self_check AC-11（pnpm test 7 file 12 test PASS） |
| AC-12 | self_check AC-12（typecheck + build + dist/index.html） |
| AC-13 | self_check AC-13 |

## 测试清单

| 文件 | 用例数 |
|---|---|
| App.test.tsx（既有） | 2 |
| routes/login.test.tsx（既有） | 2 |
| lib/api/client.test.tsx（既有） | 2 |
| routes/repos.test.tsx（既有） | 1 |
| `routes/repos.new.test.tsx` | 2 |
| `routes/jobs.$job_id.test.tsx` | 2 |
| `routes/commits.$owner.$name.$hash.test.tsx` | 1 |
| self_check web-write-flows | 13 |

**总：12 + 13 = 25 断言**

## Mock 范围

- 唯一 mock：`vi.mock("../lib/api/queries", ...)` 在路由测试中替换 hook 返 fixture
- 不连后端
- 与 web-mvp-pages 一致策略

## 运行结果

```
pnpm test: 7 files / 12 tests PASS in ~1.7s
self_check web-write-flows: PASS=13 FAIL=0
self_check 全仓: PASS=147 FAIL=0
```

## 已知 flaky

- 无。
