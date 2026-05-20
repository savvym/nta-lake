---
change_id: web-blob-md-image-resolver-20260520
version: 1
authored_at: 2026-05-20T11:50:00Z
status: draft
---

# Spec：MD 预览支持 `![](images/x.jpg)` → 仓内 blob 解析

## 背景

`apps/web/src/routes/blob.$owner.$name.$hash.tsx::TextOrMarkdownBody` 当前用自实现的 `renderMinimalMarkdown`（line 385）渲染 markdown，**显式注释 "不支持 inline emphasis / link / image / table / blockquote"**。

实际场景（MinerU pdf-mineru 出的 silver/<repo>/<commit>/paper.md）markdown 内含大量 `![](images/<sha>.jpg)` 相对路径引用同 commit 内的 image blob（subtree `images/`）。当前 web 完全不渲染图片，用户看 paper.md 只剩纯文本。

用户选定（stage 0）：
1. **react-markdown** 作为 renderer（业界标准，bundle ~50KB gzipped，支持完整 markdown + GFM 表格 + 安全 HTML sanitize）
2. **blob 页组件里同步重写 `<img src>`**：渲染前扫 markdown，对每个 `![](相对路径)`，用 commit 内的 tree 解析到 blob sha，重写 src → `/api/repos/{o}/{n}/blobs/{sha}`

## 问题陈述

- `renderMinimalMarkdown` 不支持 inline image 语法 `![](url)`；扩这个 minimal 还有 inline emphasis / table / blockquote 等都得逐条补，工作量大且不完备
- `<img src="images/x.jpg">` 是浏览器相对路径解析，会落到 `/blob/{owner}/{name}/images/x.jpg` → 404；blob API 只按 sha 取
- BlobPage 现有 search param `path` 已知当前 blob 在仓内的"全路径"（如 `paper.md`），但缺：
  - **从 path 推算 "当前目录"**（用于解析相对路径）→ `paper.md` 在根，相对路径 `images/x.jpg` 等价仓根的 `images/x.jpg`
  - **commit_hash**（用于查 tree 拿 image blob sha）—— BlobPage 当前**完全不知道**这个 blob 属于哪个 commit；URL 只有 sha
- 需要一个机制：给 path（仓内相对路径） + commit_hash → 拿 blob sha
- 但 BlobPage 只有 sha 没 commit_hash。**怎么传 commit_hash**？两条路：
  - A: URL 加 `?commit=<hash>`（Link 来源已知 commit）；FilesSection 跳 BlobPage 时显式传
  - B: 不传 commit，BlobPage 用 main ref 当前 commit 解析（简化但失效场景：用户用 detail page 跳过来时；或主 ref 已往前推过）
- spec 选 A：commit_hash 显式传，最准；BlobPage 现有 search 加字段

## 范围

In scope（与下方 AC 对齐）：

- AC-1: 加 `react-markdown` + `remark-gfm` 为 `apps/web` 依赖（pnpm install）
- AC-2: BlobPage `validateSearch` 加 `commit?: string`（可选 sha；默认 undefined 时降级"无图片解析"）
- AC-3: FilesSection 中所有跳 BlobPage 的 `<Link to="/blob/$owner/$name/$hash" search={{ path }} />` 改为带上 `commit: commit_hash`
- AC-4: `TextOrMarkdownBody` 替换 `renderMinimalMarkdown` 为 `<ReactMarkdown remarkPlugins={[remarkGfm]} components={{img: <CustomImage>}}>`
- AC-5: 新 `<CustomImage>` 组件：接 props `src` + 上下文（owner / name / commit / 当前 md path），用 useSubtreeByPath（path = dirname(当前 md path) + relative path 的 dirname）拿 tree → entries 里找 basename → entries[k].target_hash → 改 src 为 `/api/repos/{o}/{n}/blobs/{sha}`；若 commit 缺 / 找不到 / 是绝对 URL 直接 fallback 原 src
- AC-6: 测试 ≥ 3 用例：(a) MD 含 `![](images/a.jpg)` 渲染出 `<img src=/api/repos/.../blobs/<sha>>` (b) MD 含 `<img src="https://...">` 绝对 URL 不重写 (c) commit 缺时降级 fallback
- AC-7: pnpm typecheck 0 errors
- AC-8: 全 web vitest 不回归
- AC-9: scripts/_self_check.sh 加 `run_web_blob_md_image_resolver` AC block（兼自递归）

## 非范围

- 不动后端（GET /trees/{hash} 已支持）
- 不支持 markdown 内任意远程图片 fetch 代理（绝对 URL 浏览器自取）
- 不支持 video / audio / iframe 标签
- 不实现 markdown editor / 写入
- 不实现 PDF / DOCX preview（独立 follow-up）
- 不引入 syntax highlight（不在本 change；follow-up `web-md-syntax-highlight-*`）
- 不动 IngestSection / FilesSection 行为（仅 BlobPage + FilesSection 跳 BlobPage 时多带 commit param）

## 验收标准（9 AC，**2 behavioral**：AC-6 / AC-8）

| ID | kind | 描述 | 验证 | 期望 |
|---|---|---|---|---|
| AC-1 | static | react-markdown + remark-gfm 在 web deps | `grep -qE '"react-markdown"' apps/web/package.json && grep -qE '"remark-gfm"' apps/web/package.json` | 退出 0 |
| AC-2 | static | BlobPage validateSearch 含 commit 字段 | `grep -qE "commit" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx` | 退出 0 |
| AC-3 | static | FilesSection Link search 含 commit | `grep -q "commit:" apps/web/src/routes/repos/\$owner.\$name.tsx` | 退出 0 |
| AC-4 | static | BlobPage 用 ReactMarkdown 替换 renderMinimalMarkdown | `grep -q "ReactMarkdown" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx` | 退出 0 |
| AC-5 | static | 含自定义 img 组件解析逻辑（grep 锚定 "useSubtreeByPath\|target_hash\|/blobs/"） | `grep -qE "useSubtreeByPath|target_hash" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx` | 退出 0 |
| AC-6 | behavioral | ≥ 3 单测覆盖 image rewrite / 绝对 URL / commit 缺 | 见 § "AC-6 完整命令" | numTotalTests ≥ 3 + 0 fail |
| AC-7 | static | pnpm typecheck 0 errors | `pnpm --filter web typecheck` | 退出 0 |
| AC-8 | behavioral | 全 web vitest 不回归 | `cd apps/web && pnpm test -- --run` | 全 PASS |
| AC-9 | static | self_check 含 run_web_blob_md_image_resolver | `grep -q "run_web_blob_md_image_resolver" scripts/_self_check.sh` | 退出 0 |

### AC-6 完整命令

```bash
cd apps/web && pnpm test -- --run --reporter json src/routes/blob.test.tsx > /tmp/blob.raw 2>&1 && \
  grep -E '^{' /tmp/blob.raw > /tmp/blob.json && \
  python3 -c "import json; d=json.load(open('/tmp/blob.json')); assert d['numFailedTests']==0 and d['numTotalTests']>=3, d"
```

> baseline：当前 blob.test.tsx 用例数；改造时既要保留原有又要 ≥ 3。reviewer 复核数量。

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| react-markdown bundle ~50KB → web bundle 增大 | 低 | 加载稍慢 | 接受；用户 web 不是低带宽场景 |
| react-markdown 默认行为 sanitize HTML 是否够安全？ | 中 | XSS | react-markdown 默认不渲染 raw HTML（除非 rehypeRaw）；本 change 不引入 rehypeRaw |
| MD 含 `![](images/<sha>.jpg)`，但 当前 md path 是 nested 目录如 `papers/2026/a.md`：相对路径应解析到 `papers/2026/images/<sha>.jpg` | 高 | 路径错 → 找不到图 | CustomImage 必须按当前 md 的 dirname + 相对路径拼算"目标 path"；用 useSubtreeByPath 拿对应 subtree |
| useSubtreeByPath 异步：CustomImage 渲染时 tree 未到 → 显占位 / 空白 | 中 | 闪烁 | CustomImage 用 loading 占位 / 加载完后渲染 `<img>` |
| MinerU 出的 markdown 引用相对路径，但仓内实际 image blob 在 `images/<sha>` 而非 `images/<sha>.jpg`（mineru-3.1 实际 layout 是含扩展名的，但 sha 命名 vs blob_store path 命名是否一致？） | 中 | 找不到 | 在 pdf-mineru-assets-20260520 实测 MinerU 输出的 image filename 是 `<sha>.jpg` 含扩展名；处理器写 IngestFileRef path=`images/<sha>.jpg`；MD 引用也是 `images/<sha>.jpg`。一致。 |
| commit search param 形如 `?commit=<64-hex>` URL 偏长 | 低 | UX | 接受；blob 链接非高频复制 |
| 测试 mock react-markdown 复杂（默认 ReactMarkdown 是 ESM） | 中 | 测试设置坑 | 不 mock react-markdown，让它真渲染；mock useSubtreeByPath 控制 tree 返回 |
| 跳过 reviewer 漏 bug（tree-nested-domain / web-tree-nested-ui 都有真 bug 被抓） | 中 | 真 bug 漏 | stage 2/4/6 全 reviewer spawn 不 self-attest |

## 跨链路一致性自审

1. ✅ summary 待写
2. ✅ 范围 / 非范围 明确
3. ✅ AC 全可机械化
4. ✅ AC 分层：2 behavioral
5. ✅ 非豁免
6. ✅ 反向 grep 不需要 test -f 前置
7. ✅ spec ↔ tasks ↔ self_check 一致
8. ✅ process_tasks 7 节点全列

## 受影响模块

- 改：`apps/web/package.json`（依赖：react-markdown + remark-gfm）
- 改：`apps/web/src/routes/blob.$owner.$name.$hash.tsx`（validateSearch / TextOrMarkdownBody / 新 CustomImage）
- 改：`apps/web/src/routes/repos/$owner.$name.tsx`（FilesSection blob link search 加 commit）
- 改：`apps/web/src/routes/blob.test.tsx`（≥ 3 用例覆盖）
- 改：`scripts/_self_check.sh`（追加 AC block）

## 不受影响

- 后端（tree / blob API 已支持）
- 其他路由 / 组件

## 引用

- 上游 close：`web-tree-nested-ui-20260520`（merge 8b7a9ce）—— useSubtreeByPath 提供 path → tree 解析
- 上游 close：`processor-pdf-mineru-assets-20260520`—— MinerU 输出 markdown 含 `![](images/<sha>.jpg)`
- `blob.$owner.$name.$hash.tsx:385` renderMinimalMarkdown（要被替换）
