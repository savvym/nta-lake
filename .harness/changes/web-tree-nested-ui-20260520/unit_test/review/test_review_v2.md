---
change_id: web-tree-nested-ui-20260520
target: queries.tree-nested.test.tsx + test_report_v1.md
target_version: 2
review_version: 2
reviewer: claude-agent:web-tree-nested-ui-20260520-stage6-reviewer-v2
reviewed_at: 2026-05-19T21:00:00Z
verdict: APPROVED
---

# Test Review v2

## v1 MUST FIX 复检

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| MUST FIX-2 | `vi.mock("../lib/api/queries")` 直接 mock 了整个 queries 模块，useSubtreeByPath queryFn 未被任何测试验证 | **RESOLVED** | 新增 `apps/web/src/lib/api/queries.tree-nested.test.tsx`（166 行），使用 `vi.spyOn(client, "fetchJson")` spy 在 client.ts 层，renderHook + 真 QueryClient 让 queryFn 真跑；5 用例覆盖 happy-path / null-guard / segment 不存在 / blob-not-tree / 空段过滤 |
| MUST FIX-3 | test_report_v1.md 是未填充模板（change_id 占位符、AC 映射指向 Python 后端测试） | **RESOLVED** | test_report_v1.md frontmatter `change_id: web-tree-nested-ui-20260520`、`authored_at: 2026-05-19T18:50:00Z`；AC 映射表对应 repos.files-section.test.tsx（5 用例）+ queries.tree-nested.test.tsx（5 用例）；本地运行结果填写 31 passed；无占位符残留 |

---

## 检查清单结论（artifact 模式）

| # | 检查项 | 结论 |
|---|---|---|
| T-1 | 每条 spec AC 都映射到 ≥1 个测试用例 | PASS：AC-2/AC-4/AC-5/AC-6/AC-7 均有映射；queries.tree-nested 5 用例覆盖 AC-2 的串行 fetch 算法与 null-guard |
| T-2 | 无空跑断言 | PASS：5 个新用例均有实质断言（isSuccess/isError + data.hash/error message regex） |
| T-3 | mock 范围合理 | PASS：spy 目标为 `client.fetchJson`（I/O 层），不 mock fetch 本身也不 mock 整个 hook；queryFn 算法真跑 |
| T-4 | 测试名能反映场景 | PASS：中文描述场景，清晰（happy path、null-guard、segment 不存在、segment 是 blob、空段过滤） |
| T-5 | test_report_v1.md 正确填写 | PASS：change_id、AC 映射、运行结果均填写；31 passed / 0 skip |
| T-6 | queryFn 5 用例覆盖核心分支 | PASS：null-guard throw / segment not found throw / blob-not-tree throw / 空段 filter / happy path 均覆盖 |
| T-7 | 错误 message 断言精确 | PASS：null-guard 断言 `/tree not found/`（与源码 `tree not found` 对齐）；segment 不存在断言 `/nope/` + `/paper\.md/`（与源码错误字符串对齐，经交叉验证） |
| T-8 | spy 不会被其他 test 污染 | 基本 PASS：`afterEach + beforeEach` 各调一次 `mockReset()`（冗余，见 SHOULD FIX-1） |

---

## 问题列表

### MUST FIX

无。

---

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | `queries.tree-nested.test.tsx` 第 25–31 行 | `afterEach` 与 `beforeEach` 各调一次 `fetchJsonSpy.mockReset()`，冗余且顺序暗示"每次 after 也清"——实际上 `afterEach` 执行的 reset 完全被后续 `beforeEach` 的 reset 覆盖。保留其中一个（推荐 `afterEach`）即可，避免误读。 | 删除 `beforeEach(() => { fetchJsonSpy.mockReset(); })` 块，只保留 `afterEach` 的 reset |
| SHOULD FIX-2 | `queries.tree-nested.test.tsx` 第 23 行（module-level spy） | `vi.spyOn(client, "fetchJson")` 在模块顶层调用（非 `beforeEach` 内），spy 对象在整个 test file 生命周期共享。虽有 mockReset 清理 implementation，但若 vitest 在 `--reporter=verbose` 模式下重新 require 模块，spy 状态可能跨用例。参考 codebase 其余测试（`blob-meta.test.tsx`、`pipeline.test.tsx`）均在 `it` 内部或 `beforeEach` 内调用 spy——与项目惯例不一致。 | 将 `vi.spyOn(client, "fetchJson")` 移至 `beforeEach` 内（`let fetchJsonSpy: ReturnType<typeof vi.spyOn>` 在外层声明），在 `afterEach` 中 `vi.restoreAllMocks()`，与项目现有测试风格对齐 |
| SHOULD FIX-3 | `queries.tree-nested.test.tsx` happy-path（第 55 行） | URL 匹配 `url.includes(\`/trees/${IMAGES_TREE_HASH}\`)` 与源码路径 `${baseUrl}/trees/${encodeURIComponent(sub.target_hash)}` 一致（trees 复数），但 root fetch 路径 `url.includes(\`/tree/${COMMIT_HASH}\`)` 对应源码 `${baseUrl}/tree/${encodeURIComponent(commitHash)}`（tree 单数）——两者单复数不同属设计，测试已正确区分；但注释未说明这一区别，日后维护易混淆。 | 在 mockImplementation 中加一行注释说明 `/tree/{commitHash}` 是取 root tree 入口（单数），`/trees/{treeHash}` 是取任意 subtree（复数），两个端点路径不同。 |

---

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | `queries.tree-nested.test.tsx` | `null-guard` 用例（第 78–90 行）path 传 `""`，触发 segments=[] 路径，只走 root fetch 为 null → throw；这是"空 path + null root"场景。但"非空 path + 子层 fetch 返 null（中间节点 404）"没有覆盖（源码 217–221 行的 next===null throw）。该路径是 happy-path 的防御分支，不是主场景，但加一个用例可完整覆盖。 | 新增第 6 个用例：mockImplementation 让 root fetch 返正常 tree（含 images/tree entry），第二段 `/trees/{hash}` fetch 返 null，断言 `isError` + error message 含 `not found` |
| NTH-2 | `test_report_v1.md` 第 43 行 | `26 - 5 + 5 = 26 上轮基线全通` 算式写法容易误读（减法含义不明）；改写为 `现有 26 个基线用例全部保持通过；新增 10 个用例；合计 31/31 PASS` 更清晰。 | 小幅改写该行文案 |

---

## Verdict

**APPROVED**

理由：
1. v1 MUST FIX-2 真修：新建 `queries.tree-nested.test.tsx` 用 spy 在 client.ts 层让 queryFn 真跑，5 用例覆盖 null-guard / segment 校验 / blob-not-tree / 空段过滤 / happy path，error message 断言经交叉核验与源码错误字符串一致，无误报风险。
2. v1 MUST FIX-3 真修：test_report_v1.md frontmatter 占位符全部替换，AC 映射指向正确测试文件与函数，本地运行结果填写 31 passed。
3. SHOULD FIX（spy 位置惯例、冗余 reset）和 NTH 不阻塞，stage 6 质量门禁满足。

## 后续指引

APPROVED → 进入 stage 7（push + CI）。

自查命令：
```bash
# 验证 queryFn 测试存在且非空
wc -l apps/web/src/lib/api/queries.tree-nested.test.tsx

# 验证 test_report change_id 非占位符
grep "^change_id:" .harness/changes/web-tree-nested-ui-20260520/unit_test/test_report_v1.md

# 全跑
pnpm --filter web test -- --run
```
