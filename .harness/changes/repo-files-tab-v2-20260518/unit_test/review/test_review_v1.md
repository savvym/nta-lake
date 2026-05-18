---
change_id: repo-files-tab-v2-20260518
target: test_report_v1.md
target_version: 1
review_version: 1
reviewer: claude-agent:repo-files-tab-v2-20260518-stage6-reviewer-v1
reviewed_at: 2026-05-18T23:05:00Z
verdict: APPROVED
must_fix_count: 0
should_fix_count: 2
nice_to_have_count: 2
---

# Test Review v1

> 本次用 sonnet（默认规约；见 reviewer-agent.md §8）。

---

## 检查清单结论（artifact 模式）

| 项 | 结论 |
|---|---|
| 每条 spec 验收标准映射到至少 1 个测试 | PASS — AC-6 (a)-(e) 各有专属测试；AC-7 (a)-(c) 各有专属 pytest |
| 没有空跑断言（assert True / assert 1==1） | PASS — 所有断言均有实质性验证 |
| mock 范围与 coding-style §1.7 一致（数据访问层禁 mock） | PASS（带注：详见 SHOULD FIX-1） |
| 测试名能反映场景 | PASS — 测试名清晰描述场景和期望 |
| 真跑确认 | PASS — vitest 5 passed (3 files) + pytest 3 passed，机器实跑证实 |

---

## 行为级 AC 覆盖度逐条核对

### AC-6 (a) useBlobMeta data.size === 1234

**文件**：`apps/web/src/lib/api/blob-meta.test.tsx` L36-41。

实际断言：
- `expect(result.current.data?.size).toBe(1234)` — 精确数值 ✓
- `expect(result.current.data?.sha256).toBe(sha)` — sha256 字段 ✓
- `expect(capturedUrl).toBe('/api/repos/owner1/repo1/blobs/${sha}/meta')` — URL 精确匹配 ✓

结论：覆盖完整，断言强度充分。

### AC-6 (b) Tab URL state 切换

**文件**：`apps/web/src/routes/repos.tabs.test.tsx`。

实现路径：
- 用 `createMemoryHistory + createRouter + RouterProvider`（符合 spec 要求的真渲染模式，非降级方案）✓
- 查 `router.state.location.search as { tab?: string }` ✓
- `expect(search.tab).toBe("pipelines")` ✓
- 实现侧 `role="tab"` 与 `getByRole("tab", { name: "Pipelines" })` 匹配（已实读 `repos/$owner.$name.tsx` L206）✓

结论：AC-6 (b) 完整覆盖。

### AC-6 (c) 文本预览 "hello world"

**文件**：`apps/web/src/routes/blob.test.tsx` L48-64。

实际断言：
- `expect(screen.getByText("hello world")).toBeInTheDocument()` ✓
- fetch spy 返回 "hello world" 文本 ✓
- path=`content%2Fx.txt`（`.txt` 扩展名 → text 分支）✓

结论：覆盖完整。

### AC-6 (d) 二进制 fallback

**文件**：`apps/web/src/routes/blob.test.tsx` L66-82。

实际断言：
- `expect(screen.getByText(/二进制文件/)).toBeInTheDocument()` ✓
- `expect(fetchSpy).not.toHaveBeenCalled()` — 防止 false positive，断言强度充分 ✓

注意：`vi.restoreAllMocks()` 在 `beforeEach` 中于 `mockBlobMeta.mockReset()` 之后调用。`vi.restoreAllMocks()` 仅影响 `spyOn` spy，不影响 `vi.fn()`；`mockBlobMeta` 是 module-level `vi.fn()`，在 `vi.restoreAllMocks()` 后仍可用。顺序无问题。

### AC-6 (e) 5MB 守门

**文件**：`apps/web/src/routes/blob.test.tsx` L84-99。

实际断言：
- `expect(screen.getByText(/文件过大/)).toBeInTheDocument()` ✓
- `expect(fetchSpy).not.toHaveBeenCalled()` ✓
- `size: 6 * 1024 * 1024` 超过 `MAX_PREVIEW_SIZE = 5 * 1024 * 1024`（已实读实现）✓

结论：守门断言双重保险，覆盖完整。

### AC-7 (a) upload → GET /meta → 200 + size 正确

**文件**：`test_commits.py` L740-758。

- 唯一 `repo_name`：`f"repo-bm-{uuid.uuid4().hex[:6]}"` ✓
- `try/finally` + `_delete_repo_cascade` ✓
- ASGITransport（真 PG + MinIO，无 mock）✓
- `assert body["sha256"] == sha` + `assert body["size"] == len(data)`（`data = b"hello"` → size=5）✓

### AC-7 (b) 404

- 唯一 repo_name + try/finally ✓
- `'9' * 64` 不存在 sha → 断言 `r.status_code == 404` ✓

### AC-7 (c) public repo 匿名可读

- 上传用 admin 客户端，匿名用独立 `AsyncClient`（无 login）✓
- 断言 `r_meta.status_code == 200` + sha256 + size 正确 ✓

---

## 问题列表

### MUST FIX

无。

---

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD-1 | `blob.test.tsx` L14 `vi.mock("../lib/api/queries", ...)` | mock 整个 `queries` 模块是 "bulk mock"，包含与当前测试无关的所有 hooks（useRepo, useMe 等）。虽然 unit-test-write SKILL 允许前端 hook mock，但 bulk mock 会导致 (1) 新增 export 时测试报错 "not a function"，增维护成本；(2) 只有 `useBlobMeta` 是真正的被测依赖，其余是 noise。 | 考虑仅 mock 必要的 hooks，或改用 `vi.mock` + `importActual` 对齐 queries 模块真实 shape，避免 bulk mock 脆性。 |
| SHOULD-2 | `repos.tabs.test.tsx` L12 `vi.mock("../lib/api/queries", ...)` | 与 SHOULD-1 同理：bulk mock 整个 queries 模块，无 `beforeEach` 重置（不同于 blob.test.tsx 有 `mockBlobMeta.mockReset()`）。若测试文件后续增加测试用例，mock 状态不会在测试间重置，存在泄漏风险。 | 在 `repos.tabs.test.tsx` 加 `beforeEach(() => { vi.clearAllMocks(); })` 或改用 `vi.mocked` 的 `mockReturnValue` 后在 beforeEach 中调用 `vi.restoreAllMocks()`；或保持现状并添加注释说明"这些 mock 是幂等的，无需 reset"。 |

---

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-1 | `blob.$owner.$name.$hash.tsx` L385 `renderMinimalMarkdown` | `renderMinimalMarkdown` 被 export，4 类语法 + fenced 优先级 + 未闭合 fenced 有多条 edge case，但测试报告自报"未直接 unit test"（→ follow-up `web-markdown-renderer-direct-test-*`）。目前 blob.test.tsx 仅通过 BlobPage 集成路径覆盖。该函数不复杂，直接测试成本低。 | 跟进 follow-up change 补 renderMinimalMarkdown 直接单测，覆盖：3 级 heading、嵌套 list、fenced 优先、未闭合 fenced 降级、空行段落分隔。 |
| NICE-2 | `test-setup.ts` L1 | `window.scrollTo` jsdom 缺实现产生 stderr noise（测试报告已自报）；虽不影响通过计数，但会污染 CI log，在 tty=false 环境中与真正 ERROR 难以区分。 | 跟进 `web-test-jsdom-scrollTo-shim-*`，在 `test-setup.ts` 加 `Object.defineProperty(window, 'scrollTo', { value: () => {}, writable: true })`。 |

---

## Flaky 风险评估

- `window.scrollTo` stderr noise：jsdom 25 的已知行为，不导致测试 FAIL，目前稳定。若 TanStack Router 升级调用频率增加或 jsdom 将其改为 throw，可能在未来引发 flaky。风险：低，可接受。
- `createMemoryHistory + RouterProvider` 在 jsdom：repos.tabs.test.tsx 真跑 188ms PASS，无间歇性问题；TanStack Router scroll-restoration 调用 `window.scrollTo` 只是 console stderr，不影响 DOM 状态。风险：低。
- `beforeEach` 中 `vi.restoreAllMocks()` 顺序（blob.test.tsx L43-44）：`mockBlobMeta.mockReset()` 先于 `vi.restoreAllMocks()`，`vi.fn()` 不受 `restoreAllMocks` 影响，`spyOn` spy 在上轮测试结束后被 restore。测试间无状态泄漏，稳定。

---

## 真跑确认（机器实跑，本次评审执行）

```text
$ cd /data/home/zhhdzhang/nta/nta-lake/apps/web && \
    NO_COLOR=1 npx vitest run src/lib/api/blob-meta.test.tsx \
    src/routes/repos.tabs.test.tsx src/routes/blob.test.tsx 2>&1 | tail -6

 Test Files  3 passed (3)
      Tests  5 passed (5)
   Start at  23:00:03
   Duration  1.78s

$ DATAPLAT_PG_PORT=5433 ... uv run pytest -q --tb=short tests/test_commits.py -k blob_meta 2>&1 | tail -3

...
3 passed, 18 deselected in 2.19s
```

结论：vitest 5/5 PASS，pytest 3/3 PASS，与 test_report_v1.md 声明一致。

---

## Verdict

**APPROVED**

0 MUST FIX。所有 8 个测试（5 vitest + 3 pytest）机器实跑全部通过；AC-6 (a)-(e) + AC-7 (a)-(c) 逐条验证覆盖充分；断言强度满足（二进制 + 5MB 守门双断言 DOM + fetchSpy not called）；后端三测均用 ASGITransport 真 PG/MinIO，无 mock 数据访问层；测试隔离正确（uuid repo_name + try/finally 清理）。

2 SHOULD FIX 均为软工程质量问题（bulk mock 脆性），不阻塞本 change 合入，建议在后续 change 内处理或 deferred 至 `web-test-mock-strategy-*`。

2 NICE TO HAVE 均有已有 follow-up change 跟踪计划。

---

## 后续指引

- generator 可直接进入阶段 7（代码推送）。
- SHOULD-1/2 建议在 summary.md Deferred 表记录，跟进 change 名：`web-test-mock-strategy-YYYYMMDD`。
- NICE-1 跟进 change：`web-markdown-renderer-direct-test-*`（已自报）。
- NICE-2 跟进 change：`web-test-jsdom-scrollTo-shim-*`（已自报）。

### 复检指引（如 generator 修改后重提 v2）

```bash
# vitest 5 tests PASS
cd apps/web && npx vitest run \
  src/lib/api/blob-meta.test.tsx \
  src/routes/repos.tabs.test.tsx \
  src/routes/blob.test.tsx 2>&1 | grep -E "Tests|passed|failed"

# pytest 3 tests PASS
DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat \
DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx \
DATAPLAT_MINIO_ENDPOINT=http://localhost:9100 \
DATAPLAT_REDIS_URL=redis://localhost:6379/0 \
bash -c '(cd apps/api && uv run pytest -q --tb=no tests/test_commits.py -k blob_meta 2>&1)' | tail -3

# 核查 SHOULD-2 修复：repos.tabs.test.tsx 含 beforeEach reset
grep -n "beforeEach\|clearAllMocks\|restoreAllMocks" apps/web/src/routes/repos.tabs.test.tsx
```
