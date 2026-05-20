---
change_id: web-row-preview-20260520
phase: design
status: approved
authored_at: 2026-05-21T11:00:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：通用 silver/gold row 预览 + 虚拟化 (W4-2，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

新增 `/snapshots/$owner/$name/$hash/rows` 通用预览路由：消费 W4-1 `useSnapshotRows` hook，引入 `@tanstack/react-virtual` 行虚拟化，单页支持 5k+ 行 silver 数据流畅滚动 + 行级展开看 source_ref / stats / lineage_ops。

## 背景

W4-1 落了 silver row endpoint（GET `/repos/{owner}/{name}/snapshots/{hash}/rows`）+ 单一 PDF→silver 路由 (`/repos/$owner/$name/pdf-mineru`)，但 row 预览能力被 hard-bind 在 PDF 场景下 (limit=50 + 简单 HTML table)。silver / gold snapshot 的通用预览能力是 Wave 4 UI 链路（W4-3 chain builder / W4-4 export UI）的前置：

- W4-3 需要 user 在 recipe 跑完后能立刻看 silver snapshot 行内容，验证 operator 效果
- W4-4 export 前需要预览将被导出的 gold dataset 行

通用路由应当满足：
- 任意 silver / gold snapshot 都可访问，URL pattern 与现有 `/snapshots/$owner/$name/$hash`（metadata + tree）平级
- 大 snapshot（几千行）不卡浏览器 → 虚拟化必需
- 行级展开看完整 JSON（不止 text 列）

参考实现：W4-1 `pdf-mineru.tsx` 提供 row table + 详情展开 + 分页基础逻辑；W4-2 把它泛化 + 虚拟化 + URL 可达。

新依赖：`@tanstack/react-virtual@^3` — TanStack 官方虚拟化库，与现有 react-query / react-router 同生态，~14KB gzipped，无 transitive 负担。

## 范围

In scope：

- `apps/web/package.json`：加 `@tanstack/react-virtual@^3`
- `apps/web/src/routes/snapshots/$owner.$name.$hash.tsx`（改）：加 `<Outlet />` + 在 "Tree entries" 表的 `.jsonl` 文件行旁加 "Preview rows" Link（指向新路由 + `blobSha` search param）。沿用 W4-1 DEV-2 模式（folder form 子路由必须父加 Outlet）。
- `apps/web/src/routes/snapshots/$owner.$name.$hash/rows.tsx`（新；folder form）：
  - zod search schema：`offset` (default 0, ge 0)、`limit` (default 100, ge 1, le 500)、`blobSha?` (64 hex 可选)
  - 路由 component：
    - 头部展示 owner / name / hash (short) + 返回 metadata 页 Link
    - 调 `useSnapshotRows(owner, name, hash, { offset, limit, blobSha })`
    - 加载中 → "加载中…" / 错误 → 错误信息 + 重试按钮 / 空 → "snapshot 无 silver/gold 行可预览"
    - 命中数据：顶部一行 metadata（total / offset+limit / resolved blob_sha 前 12 字符）+ 虚拟化滚动列表（高度 600px，行高 estimated 48px）
    - 每行渲染：行号（offset+i+1）+ text 截断（前 200 字符） + 展开按钮
    - 展开行：`<pre data-testid="row-detail-{i}">` 显示完整 JSON（含 source_ref / stats / lineage_ops / images）
    - 底部分页：上一页 / 下一页（offset ± limit；越界禁用），改 URL search param 而非 local state（与 W4-1 一致 + 可分享链接）
- `apps/web/src/routes/snapshots/$owner.$name.$hash/rows.test.tsx`（新）：3 个 vitest+RTL 用例（vi.mock useSnapshotRows pattern，与 W4-1 一致）

Out of scope：

- **不**改 apps/api（W4-1 endpoint 已满足；422 / 0-row / 多 .jsonl 错误流复用）
- **不**做 row-level filter / search / sort：留 follow-up `web-rows-filter-*`
- **不**做行级 lineage 跳转（点 source_ref 跳到 bronze blob 预览）：留 follow-up `web-rows-lineage-jump-*`
- **不**做列选择 / 列宽调整：留 follow-up `web-rows-column-config-*`
- **不**做 image 列预览（thumbnails）：留 follow-up `web-rows-image-preview-*`
- **不**做导出（CSV / JSONL 下载）：W4-4 范围
- **不**做 playwright e2e：W4-6 引入 + user final acceptance（与 W4-1 边界一致）
- **不**改现有 `/snapshots/$owner/$name/$hash` 页面除"加 Outlet + 加 Preview rows Link"以外内容
- **不**做 manifest.yaml / dataset-card.yaml（D-1）

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | 新路由文件存在且 createFileRoute 路径正确 | `test -f apps/web/src/routes/snapshots/\$owner.\$name.\$hash/rows.tsx && grep -q 'createFileRoute("/snapshots/\$owner/\$name/\$hash/rows")' apps/web/src/routes/snapshots/\$owner.\$name.\$hash/rows.tsx` | 0 退出码 |
| AC-2 | static | 父路由加了 `<Outlet />` (folder form 强制) | `grep -q '<Outlet' apps/web/src/routes/snapshots/\$owner.\$name.\$hash.tsx` | 命中 |
| AC-3 | behavioral | 命中 3 行 silver rows → 渲染 3 个 `row-{i}` 行项；点 [详情] → 展开 `row-detail-0` 含完整 JSON | `cd apps/web && pnpm vitest run src/routes/snapshots/\$owner.\$name.\$hash/rows.test.tsx -t "renders virtualized rows"` | 1 passed |
| AC-4 | behavioral | 空 snapshot（rows=[], total=0）→ 渲染 "无 silver/gold 行可预览" 占位（不展示虚拟化容器） | `cd apps/web && pnpm vitest run src/routes/snapshots/\$owner.\$name.\$hash/rows.test.tsx -t "empty snapshot"` | 1 passed |

## 决策

1. **路由位置 `/snapshots/$owner/$name/$hash/rows`**：与现有 `/snapshots/$owner/$name/$hash` 平级子路由；语义自然（"snapshot 的 rows view"）；不挂 `/repos/...` 下避免与 W4-1 PDF 专用路由混；通用预览归 `/snapshots` 命名空间。
2. **folder form 子路由（不走 flat-dot）**：W4-1 实测 flat-dot `repos.$owner.$name.pdf-mineru.tsx` 会被 TanStack 自动嵌套到 parent，需要 parent `<Outlet />`。本 change 直接采用 folder form `routes/snapshots/$owner.$name.$hash/rows.tsx` + parent Outlet，省去 flat-dot fallback 来回。
3. **复用 W4-1 `useSnapshotRows` hook**：endpoint + hook 已就位；不重复造；blobSha 透传 search param 让用户可以指定特定 .jsonl 而非自动解析（W4-1 endpoint 已支持 query param `blob_sha`）。
4. **`@tanstack/react-virtual` v3**：TanStack 官方虚拟化；与 react-query / react-router 同生态；API 稳定；社区主流；避免引入 react-window / react-virtuoso 等额外生态。下限 ^3 因为 v3 是当前 stable major；不锁更细版本。
5. **virtualization 容器固定高度 600px**：MVP；不做响应式高度（窗口 resize 跟随）—留 follow-up `web-rows-responsive-height-*`；600px 在标准 1080p 显示器上能看到 ~12 行同时，足够人眼校验。
6. **行高 estimateSize=48**：text 截断到 ~200 字符 + 行号 + 展开按钮，单行 24-32px 显示足够；48px 给展开后留 buffer；TanStack react-virtual 支持动态 measure，估计偏差不影响功能。
7. **行展开 = local state（useState Set<idx>），不入 URL**：避免 URL 爆炸；展开是 transient 操作；用户刷新页面无需保留展开状态；与 W4-1 一致。
8. **URL search param 驱动 offset/limit/blobSha**：使用 TanStack Router zod `validateSearch`；与 W4-1 一致；URL 可分享；offset/limit 默认 0/100。
9. **limit 默认 100（vs W4-1 的 50）**：W4-2 是通用预览页，虚拟化解决渲染压力，可一次拉更多；100 行平衡服务端单次序列化成本与翻页频率。limit 上限 500（防极端 caller 一次拉 GB 级 silver）。
10. **空 snapshot 不渲染虚拟化容器**：rows=[] 时直接显示占位文本；避免 react-virtual 在 0-row 输入下 console.warn。
11. **错误流复用 W4-1 endpoint 行为**：snapshot 不存在 → 404 → 显示"加载失败"+重试；多 .jsonl entry 且未传 blobSha → 422 → 显示错误 + 提示用户从 metadata 页选 entry；0 .jsonl entry → 422 → 显示"该 snapshot 无 silver/gold 行"。错误 detail 显示在 UI 上。
12. **不接 row click → bronze blob 跳转**：跨 snapshot 血缘跳转是 W4-3 chain builder 的事；本 change 仅展示。

## 风险

| 风险 | 缓解 |
|---|---|
| react-virtual API 在 v3 内变化 | pin `^3`；MVP 仅用 `useVirtualizer` + getVirtualItems + measureElement，跨 minor 稳定 |
| 大 row JSON 展开后撑爆容器高度（virtual item 高度突变） | virtual 容器固定 600px；展开 row 用 `<pre>` 内置 `max-h-64 overflow-auto`；超出滚 pre 自己 |
| folder form 与现有 flat-dot 文件冲突 | W4-1 实测同模式可行（parent 加 Outlet 即可）；TanStack route generator 自动识别两种形式共存 |
| search param `blobSha` 被用户改成非法 64-hex | zod schema 限定 `.regex(/^[0-9a-f]{64}$/).optional()`；非法直接 fallback 不传（hook 会自动解析） |
| total/pagination 与 virtual scroll 体验冲突（用户期望"无限滚动"而非"翻页"） | MVP 用翻页（与 W4-1 一致 + URL 可分享）；无限滚动留 follow-up `web-rows-infinite-scroll-*` |
| @tanstack/react-virtual 引入 pnpm lock 抖动 | sonnet 跑 `pnpm install` 让 lock 更新；CI 通过 |
| vitest jsdom 环境下 react-virtual 行为（不真渲染 layout） | useVirtualizer 在 jsdom 下默认 measure 返回 0，可能导致 0 rows 渲染；test 中 mock `getBoundingClientRect`（设置容器 height）或直接断言 mapped rows 而非虚拟容器；与 W4-1 vi.mock 模式一致 |
| pnpm 命令在 CI / 本地 fallback 到 npm | 与 W4-1 一致：本 change 测试命令以 pnpm vitest 表达；CI 已用 pnpm |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `apps/web/src/lib/api/queries.ts`（W4-1 useSnapshotRows / SilverRowRead / SnapshotRowsResponse）
  - `apps/api/dataplat_api/routers/snapshots.py`（W4-1 endpoint，不动）
  - `apps/api/dataplat_api/schemas/snapshot_rows.py`（W4-1 schema，不动）
  - `apps/web/src/routes/repos/$owner.$name/pdf-mineru.tsx`（W4-1 行展开模式参考）
- 应当不动：
  - `apps/api/*`（全部不动；只消费现有 endpoint）
  - W1-* / W2-* / W3-* 已 merge 产物
  - `apps/web/src/routes/snapshots/$owner.$name.$hash.tsx` 除了加 `<Outlet />` + Preview rows Link
- 引用的其他 change：W4-1（useSnapshotRows hook + folder form Outlet 模式 + endpoint）、W2-6（silver JSONL 写入方）、W1-1（snapshots router prefix）

## 关联 follow-up

- `web-rows-filter-*`：行筛选 / 文本搜索 / 列条件过滤
- `web-rows-lineage-jump-*`：点 source_ref → 跳到 bronze blob 预览
- `web-rows-column-config-*`：列选择 / 列宽 / 列顺序
- `web-rows-image-preview-*`：images 列 thumbnail 展示
- `web-rows-infinite-scroll-*`：无限滚动模式（vs 翻页）
- `web-rows-responsive-height-*`：虚拟容器响应式高度
