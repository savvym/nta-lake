---
change_id: web-row-preview-20260520
phase: verify
status: approved
verdict: APPROVED
reviewer: claude-agent:opus-phase3-reviewer
model_used: opus
reviewed_at: 2026-05-21T11:30:00Z
ac_kind_lint: enforce
---

# Verify Review：通用 silver/gold row 预览 + 虚拟化 (W4-2) — APPROVED

**VERDICT：APPROVED**（0 MUST FIX / 0 SHOULD FIX / 1 NICE TO HAVE，非阻塞）。

4 个 AC 全 PASS（2 static + 2 behavioral）；apps/web 全套 18/18 files 52/52 tests PASS（W4-1 baseline 49 + W4-2 新增 3，零回归）；`pnpm tsc --noEmit` clean；diff scope 严格限定在 design 允许范围（apps/api / packages/core / W1..W3 / W4-1 repos 路由全部 0 改动）；2 个 DEV 偏离全部预批 ACCEPT；新增依赖 `@tanstack/react-virtual@3.13.24` + transitive `@tanstack/virtual-core@3.14.0` 锁文件抖动极小，TanStack 同生态零负担；D-1 永不做清单 grep clean。

## 输入

- Design：`.harness/changes/web-row-preview-20260520/design.md`
- Implementation：`.harness/changes/web-row-preview-20260520/implementation.md`
- Git diff：`git diff main...change/web-row-preview-20260520`
- HEAD：`41c09b9` (branch `change/web-row-preview-20260520`)

## 1. AC 对照表

| AC | kind | reviewer 跑的命令 | 结果 | PASS/FAIL |
|---|---|---|---|---|
| AC-1 | static | `test -f apps/web/src/routes/snapshots/$owner.$name.$hash/rows.tsx && grep 'createFileRoute("/snapshots/$owner/$name/$hash/rows")' ...` | 命中 line 21 | PASS |
| AC-2 | static | `grep '<Outlet' apps/web/src/routes/snapshots/$owner.$name.$hash.tsx` | 命中 line 154 | PASS |
| AC-3 | behavioral | `cd apps/web && pnpm vitest run 'src/routes/snapshots/$owner.$name.$hash/rows.test.tsx' -t "renders virtualized rows"` | 1 passed | PASS |
| AC-4 | behavioral | `cd apps/web && pnpm vitest run 'src/routes/snapshots/$owner.$name.$hash/rows.test.tsx' -t "empty snapshot"` | 1 passed | PASS |

实际跑（合并）：

```text
$ test -f 'apps/web/src/routes/snapshots/$owner.$name.$hash/rows.tsx' && echo "AC-1 file exists OK"
AC-1 file exists OK

$ grep -n 'createFileRoute("/snapshots/\$owner/\$name/\$hash/rows")' 'apps/web/src/routes/snapshots/$owner.$name.$hash/rows.tsx'
21:export const Route = createFileRoute("/snapshots/$owner/$name/$hash/rows")({

$ grep -n '<Outlet' 'apps/web/src/routes/snapshots/$owner.$name.$hash.tsx'
154:      <Outlet />

$ cd apps/web && pnpm vitest run 'src/routes/snapshots/$owner.$name.$hash/rows.test.tsx' -t "renders virtualized rows"
 ✓ src/routes/snapshots/$owner.$name.$hash/rows.test.tsx (3 tests | 2 skipped) 129ms
 Test Files  1 passed (1)
      Tests  1 passed | 2 skipped (3)

$ cd apps/web && pnpm vitest run 'src/routes/snapshots/$owner.$name.$hash/rows.test.tsx' -t "empty snapshot"
 ✓ src/routes/snapshots/$owner.$name.$hash/rows.test.tsx (3 tests | 2 skipped) 108ms
 Test Files  1 passed (1)
      Tests  1 passed | 2 skipped (3)
```

(stderr `Error: Not implemented: window.scrollTo` 是 TanStack Router scroll-restoration 在 jsdom 下的已知噪音，非 AC 失败信号；与 W4-1 同模式。)

## 2. Cross-regression

### apps/web 全套（18/18 files，52/52 tests）

```text
$ cd apps/web && pnpm vitest run
 Test Files  18 passed (18)
      Tests  52 passed (52)
   Duration  3.49s
```

49 → 52（+3 新增 W4-2 测试：renders virtualized rows / empty snapshot / 第三个用例），零回归。W4-1 17 files 49 tests 全部仍 PASS。

### TypeScript 检查

```text
$ cd apps/web && pnpm tsc --noEmit
（无输出 = clean）
```

### apps/api

未触及（git diff main...HEAD -- apps/api/ packages/ = empty）。无需重跑。

## 3. Diff scope 审计

```text
$ git diff main...HEAD --name-only
.harness/changes/web-row-preview-20260520/design.md
.harness/changes/web-row-preview-20260520/implementation.md
apps/web/package.json
apps/web/src/routeTree.gen.ts
apps/web/src/routes/snapshots/$owner.$name.$hash.tsx
apps/web/src/routes/snapshots/$owner.$name.$hash/rows.test.tsx
apps/web/src/routes/snapshots/$owner.$name.$hash/rows.tsx
pnpm-lock.yaml
```

- `apps/api/**`：**0 行**（grep clean）
- `packages/**`：**0 行**（grep clean）
- W1-* / W2-* / W3-* / W4-1 merged 产物：**0 行**（apps/web/src/routes/repos/ 未触及；apps/web/src/lib/api/queries.ts 未触及；apps/api/dataplat_api/routers/snapshots.py 未触及）
- `apps/web/src/routes/snapshots/$owner.$name.$hash.tsx`：仅 +16/-1：`Outlet` import + 1 `<Outlet />` JSX + `.jsonl`/`.jsonl.gz` 文件行的 "Preview rows" Link（design § 范围 In-scope bullet 2 明确允许）
- 新依赖：`@tanstack/react-virtual@3.13.24` + transitive `@tanstack/virtual-core@3.14.0`，与 design 决策 4 (`^3` 范围) 一致；TanStack 同生态零额外 transitive 爆炸
- 不在 design Out-of-scope（apps/api / 行筛选 / lineage 跳转 / 列配置 / image preview / 导出 / playwright / 老 metadata 页其余内容 / manifest.yaml）的任何文件被触及

## 4. DEV 偏离评估

| # | sonnet 报的偏离 | reviewer 判断 | 理由 |
|---|---|---|---|
| DEV-1 | rows.test.tsx 中 vi.mock useSnapshot 返回有效 snapshot 数据 | **ACCEPT** | 父路由 `$owner.$name.$hash.tsx` 在 useSnapshot 返回 null 时 early-return，会阻断 `<Outlet />` 渲染。测试要验证子路由 component，必须让父走"已加载"分支。design § 风险表第 7 行预判了 vitest jsdom + react-virtual 测试模式问题，授权 vi.mock；与 W4-1 vi.mock 模式一致；不破坏 AC 也不破坏 design 意图 |
| DEV-2 | routeTree.gen.ts 手动更新（非 vite plugin 自动生成） | **ACCEPT** | 本地无 dev server 环境；diff 验：新增 import + 新增 RowsRouteRoute / RowsRouteRouteImport / FileRoutesByPath interface 条目，格式与 plugin 生成完全一致；W4-1 同模式 DEV-2 已预批；不破坏 AC（vitest + tsc 全过即证明 routeTree 合法） |

2/2 DEV 全部 ACCEPT。无隐式偏离（reviewer 对照 design § 范围 vs git diff 文件清单，零未声明改动）。

## 5. 永不做清单 / 北极星合规

- 无 manifest.yaml / dataset-card.yaml 引入（`grep manifest.yaml apps/web/src/routes/snapshots/` clean）
- 无 branch / merge / cherry-pick / rollback / row-diff 概念
- 无 blob 派生图 / Asset 引入
- 无 silver 文件树（仍 JSONL → row list 显示）
- 无 bronze 强 schema
- 行展开看到的 source_ref / lineage_ops 都是显示用 JSON.stringify(row)，未篡改/未派生
- 仍走 W4-1 endpoint，未引入新 API 概念
- stats-first / 行级血缘语义不变

## 6. 实现质量抽查

- zod searchSchema：`offset` ge 0 / `limit` ge 1 le 500 / `blobSha` regex `/^[0-9a-f]{64}$/` ✓（design 决策 4 + 风险 4）
- `useVirtualizer` count = `data?.rows.length ?? 0` / estimateSize 48 / overscan 10 ✓（决策 6）
- 容器固定 600px (`h-[600px]`) + `overflow-auto` ✓（决策 5）
- 展开 = useState<Set<number>> local ✓（决策 7）
- `data-testid="row-{i}"` + `data-testid="row-detail-{i}"` ✓（AC-3 验证锚点）
- 空 snapshot 短路在虚拟化容器之前（`!data || data.rows.length === 0` → 占位）✓（决策 10）
- 分页用 `navigate({ search: prev => ... })` 改 URL search param ✓（决策 8）
- "上一页" `offset === 0` 禁用 / "下一页" `offset + limit >= data.total` 禁用 ✓（design § 范围 bullet "越界禁用"）
- 错误流：isError → 显示 `加载失败：{error}` + 重试按钮 ✓（决策 11）
- 父路由 Preview rows Link 仅 `.jsonl` / `.jsonl.gz` 显示 ✓（design § 范围 bullet 2）

## 7. 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

- **NICE-1**：rows.test.tsx 跑 `-t` 单测时 console 仍打印 `Error: Not implemented: window.scrollTo`（TanStack Router scroll-restoration on jsdom 噪音）。不影响 AC PASS，但日志干扰可读性。建议 follow-up `web-test-suppress-jsdom-scroll-noise-*` 在 `vitest.setup.ts` 加 `window.scrollTo = vi.fn()` stub 全局抑制。本 change 不阻塞。

## Verdict

**APPROVED** — 0 MUST FIX / 0 SHOULD FIX / 1 NICE TO HAVE（非阻塞）。4 个 AC 全 PASS（2 static + 2 behavioral），apps/web 18/18 files 52/52 tests，typecheck clean，apps/api / packages / W4-1 路由 0 行触及，2 个 DEV 偏离全部预批 ACCEPT，diff scope 严格符合 design § 范围，永不做清单 grep clean。16 连 0-MUST-FIX APPROVED 延续。

## 后续指引

1. application-owner merge `change/web-row-preview-20260520` → main（建议 `--no-ff`）
2. close W4-2 task；orchestration W4 计数 1/10 → 2/10
3. 启动 W4-3：`web-operator-chain-builder-*`（pipeline run UI / chain 配置编辑器）
4. 可选：在 `.harness/follow-ups/` 立 `web-test-suppress-jsdom-scroll-noise-*`（NICE-1）
