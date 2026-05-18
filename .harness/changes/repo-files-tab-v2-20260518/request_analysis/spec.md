---
change_id: repo-files-tab-v2-20260518
version: 2
authored_at: 2026-05-18T22:15:00Z
status: draft
prior_version: 1
prior_review: request_analysis/review/spec_review_v1.md
---

# Spec：Repo 详情页 Files 独立 Tab + 文件预览页

> **v2 修订说明**：闭 spec_review_v1 的 5 MUST FIX + 3 SHOULD FIX + 2 NICE TO HAVE。

## v1 review 闭环表

| # | v1 问题 | v2 状态 |
|---|---|---|
| MUST #1 | AC-4/AC-8 ERE 内 quoted alternation `\|` 是字面竖线（5MB 常量 / 图片扩展名 / error TS 三处假阴性 / 假阳性）| **CLOSED**：拆为独立 grep 用 shell `\|\|` 链（unquoted alternation）；AC-4 5MB 拆 3 grep / 扩展名拆 3 grep / Markdown 锚拆 3 grep；AC-8 error TS 拆 2 grep |
| MUST #2 | AC-6 `$()` 内 `\|` 非 shell pipe（subshell 内 grep 把 `\|` 当字面参数）| **CLOSED**：去掉 `$() ... awk count` 比较；改为 2 个独立 grep + shell `\|\|` 链：`grep -qE 'Tests +[5-9] passed' \|\| grep -qE 'Tests +[1-9][0-9]+ passed'` |
| MUST #3 | AC-3/AC-4/AC-5 单引号 `\$` 路径 bug（`'...\$owner.\$name.tsx'` test -f 永远 NOT_FOUND）| **CLOSED**：去掉路径单引号，改为无引号形式 `apps/web/src/routes/repos/\$owner.\$name.tsx`（参考 pipeline-ui-tab spec/self_check 模式，bash unquoted `\$` = 字面 `$`）|
| MUST #4 | AC-7 ERE 内 `\|` 字面竖线（pytest count grep 假 FAIL）| **CLOSED**：拆为 `grep -qE '[3-9] passed' \|\| grep -qE '[1-9][0-9]+ passed'`（unquoted shell `\|\|`） |
| MUST #5 | AC-6 `\$2` 联动（awk 在 bash -c 单引号上下文）| **CLOSED**：MUST #2 修法直接去掉 awk count 比较，无 `\$2` 残留 |
| SHOULD #1 | summary.md frontmatter `status: in_progress` 应为 `waiting_review` | **CLOSED**：本次 spec_v2 提交时同步更新 summary.md `status: waiting_review` + `last_updated` |
| SHOULD #2 | AC-4 §Markdown 渲染缺 fenced block 内 heading 识别压制说明 | **CLOSED**：AC-4 描述 (b) 项加"fenced block 状态机优先级最高——fenced 内的行不触发 (i) heading / (ii) list / (iv) paragraph 识别" |
| SHOULD #3 | 待澄清问题末尾 BlobStore deferred 未关闭 | **CLOSED**：本节末尾把该项标 `[x] reviewer 已查` + 结论 |
| NICE #1 | AC-6 (b) Tab URL state 测试 "或 Route.useSearch().tab" 备选措辞歧义 | **CLOSED**：AC-6 (b) 改为"用 createMemoryHistory + createRouter 渲染（参考 repos.test.tsx L47-53 模式），点 Pipelines Tab → URL contains tab=pipelines" |
| NICE #2 | §引用缺 pipeline.test.tsx | **CLOSED**：§引用加 `apps/web/src/lib/api/pipeline.test.tsx`（spyOn fetch 模式参考）|

> **联动**：tasks.md 同步小修（T-10 description 加"AC 命令以 spec_v2 为准" + T-8b 删 createMemoryHistory 降级方案）。tasks_v2 不另申请 review（tasks_review_v1 已表态 spec_v2 关 MUST FIX 后 tasks 无需重评）。

## 背景

`repo-files-tab-20260517` 阶段把 Files 作为一个 section 加到了 Repo 详情页（Metadata + Files + Ingest + Pipelines 四段堆叠），让用户能看到 main 分支的 commit + tree entries 表 + 下载链。

`pipeline-ui-tab-20260518` 又在底部加了 PipelinesSection。

至此 Repo 详情页变成"垂直堆 4 段，越滚越长"的形态，与 GitHub / HuggingFace Files Tab 那种"页头 + 顶部 Tabs 切换"的范式有明显落差，且只能下载、不能预览。

本 change 把这两件事一起做：(1) **三个 section 改为 Tabs**；(2) **文件支持点击预览**。

## 问题陈述

当前 `apps/web/src/routes/repos/$owner.$name.tsx` 的 UX：

1. 三个 section 同时渲染，admin 用户首屏要滚动两屏才能看到 Pipelines；guest 看到 Metadata + Files 后下方空白（Ingest / Pipelines 被 admin gate 隐藏）。
2. Files section 的 entries 表"path"列只是纯文本，"操作"列只有"下载"，**没有预览**——用户必须下载到本地用编辑器打开才能看 jsonl/md/txt 内容，对于 LLM 训练数据集的"快速抽检"场景反摩擦。
3. Tab 切换状态全部缺失，刷新 / 分享链接无法定位到具体 section。

后端目前已有 `GET /repos/{o}/{n}/blobs/{sha}` 流式下载（`apps/api/dataplat_api/routers/commits.py` L119-148），但**不返回 Content-Length**，前端无法在不下载完整文件的前提下得知 size——这是 5 MB 守门的关键障碍。BlobStore.get_size 已实现（`minio_store.py` L168-178，返回 `int | None`，ClientError code ∈ {404, NoSuchKey, NotFound} 时 return None；其他 ClientError raise，FastAPI 默认 500）；reviewer 实读确认 spec 的 `None → 404` 假设成立，无需 router 补 try/except。

## 范围

In scope：

- AC-1：后端 `apps/api/dataplat_api/routers/commits.py` 新增 `GET /repos/{owner}/{name}/blobs/{sha256}/meta` 返 JSON `{sha256, size}`；同 download 权限：`get_optional_user` + `_resolve_repo`（private repo 匿名 → 404）；blob 不存在 → 404；schema 新增 `BlobMetaResponse`（Pydantic）。
- AC-2：`apps/web/src/lib/api/queries.ts` 新增 `BlobMetaResponse` TS interface + `useBlobMeta(owner, name, sha)` query（用 `fetchJson`；`enabled = sha matches /^[0-9a-f]{64}$/`）。
- AC-3：`apps/web/src/routes/repos/$owner.$name.tsx` 重构：保留顶部 Repo 标题 + Metadata 卡片不动，下方插入 **Tabs 区**：
  - Tab 列表：`Files`（始终）/ `Ingest`（admin only）/ `Pipelines`（admin only）。
  - 激活 Tab 由 URL search param `?tab=files|ingest|pipelines` 控制，默认 `files`；切换 Tab 调用 TanStack Router `navigate({ search: ... })` 更新 URL（不全页刷新）。
  - 各 Tab 内容沿用既有 `FilesSection` / `IngestSection` / `PipelinesSection` 组件，**不重写组件逻辑**——只是切换可见性 + URL 同步。
  - Tab UI：纯 Tailwind 实现（无新依赖），4 个 div 按钮 + 下划线指示激活；reuse 既有 Button 组件不强求。
- AC-4：新路由 `apps/web/src/routes/blob.$owner.$name.$hash.tsx`：
  - 路径：`/blob/$owner/$name/$hash`；查询参数 `?path=<encoded path>`（可选；缺省时 path 显示为 `(unknown path)`）。
  - 流程：(1) `useBlobMeta` 拿 size → (2) 判断 `size > 5 * 1024 * 1024`：显示 "文件过大（X MB > 5 MB），请下载查看" + 下载按钮，停止后续 fetch；(3) 否则按 path 扩展名分派：
    - (a) **文本**（扩展名属于 `.md/.txt/.json/.jsonl/.yaml/.yml/.csv/.tsv/.py/.ts/.tsx/.js/.jsx/.sh/.toml/.ini/.conf/.rst/.html/.css/.scss/.xml/.sql` 之一，大小写不敏感）→ `fetch('/api/.../blobs/{sha}')` → `await resp.text()` → `<pre><code className="text-xs font-mono whitespace-pre-wrap break-all">`。
    - (b) **Markdown**（`.md` 专属，复用文本拿到的字符串）→ 额外提供 "Source / Rendered" 切换按钮（默认 Source）；Rendered 用 **内置极简渲染器**（一个本地函数 `renderMinimalMarkdown(src: string) -> ReactNode[]`），支持 4 类语法：(i) `^#{1-6} ` 行 → `<h1>...<h6>`；(ii) `^- ` / `^* ` 行连续段 → `<ul><li>`；(iii) ` ``` ... ``` ` fenced code → `<pre><code>`；(iv) 其余非空行段 → `<p>`。**优先级硬规约**：fenced block 状态机**优先级最高**——fenced block 内的行**不触发** (i) heading / (ii) list / (iv) paragraph 识别，统一作为 fenced 内 raw text 处理；未闭合 fenced 按 "剩余全是 code" 处理。**不支持 inline emphasis / link / image / table / blockquote**（→ follow-up）。
    - (c) **图片**（`.png/.jpg/.jpeg/.gif/.svg/.webp/.ico`，大小写不敏感）→ `<img src="/api/.../blobs/{sha}" className="max-w-full" />`；不再 fetch text。
    - (d) **二进制 fallback**（其余）→ "二进制文件，无法预览。size: X MB · sha256: <abbrev>" + 下载按钮。
  - 头部面包屑：`<owner>/<name>` → `Files` → `<path or (unknown path)>`；面包屑前两段 Link 回 Files Tab。
  - 副信息卡：sha256（完整 + 一键复制按钮）/ size / 当前 ref（暂只支持 `?path=` 不携带 ref；副信息卡 ref 字段固定显示 `—`，等 follow-up `web-ref-switcher-*`）。
- AC-5：`apps/web/src/routes/repos/$owner.$name.tsx` 的 `FilesSection` entries 表 path 列改为 `<Link to="/blob/$owner/$name/$hash" params=... search={{ path: e.name }}>`；保留"下载"列不变；下载链接仍指向 `/api/repos/{o}/{n}/blobs/{sha}`。
- AC-6：vitest 单测（**behavioral**）≥ 5 PASS，覆盖：
  - (a) `useBlobMeta` 成功路径：spy fetch → 返 `{sha256, size: 1234}` → 断言 `data.size === 1234`
  - (b) Tab URL state 切换：用 `createMemoryHistory` + `createRouter` 渲染 RepoDetailPage（参考 `repos.test.tsx` L47-53 既有模式），点 `Pipelines` Tab → 等 URL 更新 → 断言 URL 包含 `tab=pipelines`
  - (c) BlobPage 文本预览渲染：mock useBlobMeta 返 size=10 + spy fetch 返 text "hello world"；path=`content/x.txt` → DOM 含 "hello world"
  - (d) BlobPage 二进制 fallback：mock useBlobMeta 返 size=1024；path=`content/blob.bin` → DOM 含 "二进制" + 下载按钮
  - (e) BlobPage size 守门：mock useBlobMeta 返 size=`6 * 1024 * 1024`；path 任意 → DOM 含 "文件过大" + 不发起 fetch text
- AC-7：后端 pytest（**behavioral**）`apps/api/tests/test_commits.py` 新增 `test_blob_meta_*` 至少 3 测试：
  - (a) 上传 blob → GET `/blobs/{sha}/meta` 返 200 + `{sha256, size}`（size 与上传的 bytes 长度一致）
  - (b) GET `/blobs/{'9' * 64}/meta` 返 404
  - (c) public repo 匿名 GET `/blobs/{sha}/meta` 返 200（沿用既有 download 的 anon 客户端模式）
- AC-8：`scripts/_self_check.sh` 加 `run_repo_files_tab_v2` block（8 AC，含 3 behavioral：AC-6 vitest / AC-7 pytest / AC-8 npm run build）；本 block 全 PASS；`cd apps/web && npm run build` 含 `built in` + 不含 `error TS` 也不含 `Found N errors`。

## 非范围

显式列出**不做**的事，避免后续 scope creep：

- **嵌套目录展开**：`TreeEntry.entry_type` 当前 Literal["blob"]，commit-api-mvp 阶段决定 MVP 不递归 tree，本 change 维持单层平铺。
- **完整 Markdown 渲染**：本 change 仅 4 类语法。inline emphasis（**bold** / *italic*）、链接、图片、table、blockquote、setext heading（`===`）→ follow-up `web-markdown-renderer-full-*`。
- **不引入第三方依赖**：不引 `marked` / `react-markdown` / `highlight.js` / `prismjs` / `shadcn Tabs` / `radix-ui/tabs`；Tabs / Markdown 都用 Tailwind 手写 + ~50 行 JSX 实现。
- **不动 commit 详情页**：`commits.$owner.$name.$hash.tsx` 维持现状（历史 commit 快照视图，与 Files Tab 的"工作目录"职责不同；其表格的预览能力是 follow-up `commit-page-preview-*`）。
- **不做编辑 / 删除文件**：blob 是 CAS 内容寻址，编辑等价新建 commit；UI 流程在 `web-blob-edit-*` 单独 change。
- **不做分支切换器**：main hardcoded；ref 列表 / 切换 UI 是 `web-ref-switcher-*`。
- **不做语法高亮**：所有文本统一 `<pre><code>` 等宽展示；按扩展名高亮 → follow-up `web-blob-syntax-highlight-*`。
- **下载链接 UX 不动**：表格"下载"列、副信息卡的下载按钮，都指向既有 `/api/.../blobs/{sha}`（StreamingResponse），不改后端下载接口。
- **不修改 PipelinesSection / IngestSection 组件实现**：本 change 只是把它们移进 Tab；组件签名、props 不动；如确需在 Tab 切换时重置状态另开 change。
- **不做 lineage / commit 切换器**：副信息卡的 ref 字段固定 `—`（main hardcoded）。

## 验收标准

`kind` 二分：static / behavioral。

**v2 修订策略**（应对 v1 review 5 MUST FIX）：所有 ERE / shell quoted alternation `\|` 拆为独立 grep + shell `||` 链（unquoted——`\|\|` 在 markdown 表格里渲染为 `||`，bash 解释为 OR）；所有路径去单引号改无引号 `\$` 形态（bash unquoted `\$` 渲染为字面 `$`，与文件名 `$owner.$name.tsx` 匹配）。参考 pipeline-ui-tab spec/self_check.sh 既有模式。

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | 后端 commits.py 含 `@router.get("/{owner}/{name}/blobs/{sha256}/meta")` + 函数 `get_blob_meta` + schemas 含 `BlobMetaResponse` | `test -f apps/api/dataplat_api/routers/commits.py && grep -q '/{owner}/{name}/blobs/{sha256}/meta' apps/api/dataplat_api/routers/commits.py && grep -q 'def get_blob_meta' apps/api/dataplat_api/routers/commits.py && grep -q 'class BlobMetaResponse' apps/api/dataplat_api/schemas/blob.py` | 4 grep 全命中 |
| AC-2 | static | queries.ts 含 `interface BlobMetaResponse` + `export function useBlobMeta` + 路径含 `/meta` | `test -f apps/web/src/lib/api/queries.ts && grep -q 'interface BlobMetaResponse' apps/web/src/lib/api/queries.ts && grep -q 'export function useBlobMeta' apps/web/src/lib/api/queries.ts && awk '/^export function useBlobMeta/{p=1;next} p && /^export /{exit} p' apps/web/src/lib/api/queries.ts \| grep -q '/meta'` | 4 grep 全命中（awk 状态机锚定函数体；表格内 `\|` 是 markdown 转义 = shell pipe，unquoted OK）|
| AC-3 | static | 详情页 tsx 含 Tabs 实现：`tab` search param + 3 个 Tab key + 切换时 navigate search | `test -f apps/web/src/routes/repos/\$owner.\$name.tsx && grep -q 'tab=' apps/web/src/routes/repos/\$owner.\$name.tsx && grep -q '"files"' apps/web/src/routes/repos/\$owner.\$name.tsx && grep -q '"ingest"' apps/web/src/routes/repos/\$owner.\$name.tsx && grep -q '"pipelines"' apps/web/src/routes/repos/\$owner.\$name.tsx && { grep -q 'Route.useSearch' apps/web/src/routes/repos/\$owner.\$name.tsx \|\| grep -q 'useSearch(' apps/web/src/routes/repos/\$owner.\$name.tsx ; }` | 5 直接 grep 全命中 + Route.useSearch 或 useSearch( 任一命中（拆 alternation 用 shell `\|\|`）|
| AC-4 | static | 新路由 blob.$owner.$name.$hash.tsx 存在 + 含 `createFileRoute("/blob/$owner/$name/$hash")` + useBlobMeta + 5MB 守门常量 + Markdown renderer 锚 + 图片扩展名锚 | `test -f apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx && grep -q 'createFileRoute("/blob/\$owner/\$name/\$hash")' apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx && grep -q 'useBlobMeta' apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx && { grep -qE '5 ?\* ?1024 ?\* ?1024' apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx \|\| grep -q '5242880' apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx \|\| grep -q 'MAX_PREVIEW_SIZE' apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx ; } && { grep -q 'renderMinimalMarkdown' apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx \|\| grep -q 'MarkdownView' apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx \|\| grep -q 'MarkdownRendered' apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx ; } && { grep -q '\.png' apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx \|\| grep -q '\.jpg' apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx \|\| grep -q '\.jpeg' apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx ; }` | 3 直接 grep + 3 个 alternation 组（每组任一命中）均 PASS |
| AC-5 | static | 详情页 FilesSection 含 `<Link` 指向 `/blob/$owner/$name/$hash` + search `path` | `awk '/function FilesSection/{p=1;next} p && /^function /{exit} p' apps/web/src/routes/repos/\$owner.\$name.tsx \| grep -q '/blob/\$owner/\$name/\$hash' && awk '/function FilesSection/{p=1;next} p && /^function /{exit} p' apps/web/src/routes/repos/\$owner.\$name.tsx \| grep -q 'search'` | 2 awk+grep 全命中（awk 状态机锚定函数体）|
| AC-6 | **behavioral** | vitest 跑 ≥ 5 测试 PASS（blob-meta hook / Tab URL 切换 / 文本预览 / 二进制 fallback / 5MB 守门）| `cd apps/web && npx vitest run src/lib/api/blob-meta.test.tsx src/routes/repos.tabs.test.tsx src/routes/blob.test.tsx 2>&1 \| tee /tmp/dataplat-vitest-blob.log >/dev/null; { grep -qE 'Tests +[5-9] passed' /tmp/dataplat-vitest-blob.log \|\| grep -qE 'Tests +[1-9][0-9]+ passed' /tmp/dataplat-vitest-blob.log ; }` | Test Files 3 passed + Tests 命中 5-9 或 10+ passed（拆 alternation 为 2 grep + shell `\|\|`）|
| AC-7 | **behavioral** | pytest 跑 test_commits.py 内 test_blob_meta_* ≥ 3 PASS | `DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx DATAPLAT_MINIO_ENDPOINT=http://localhost:${DATAPLAT_MINIO_PORT:-9000} DATAPLAT_MINIO_ACCESS_KEY=${DATAPLAT_MINIO_ACCESS_KEY:-minioadmin} DATAPLAT_MINIO_SECRET_KEY=${DATAPLAT_MINIO_SECRET_KEY:-minioadmin} cd apps/api && uv run pytest -q --tb=no tests/test_commits.py -k blob_meta 2>&1 \| tee /tmp/dataplat-pytest-blob.log >/dev/null; { grep -qE '[3-9] passed' /tmp/dataplat-pytest-blob.log \|\| grep -qE '[1-9][0-9]+ passed' /tmp/dataplat-pytest-blob.log ; }` | log 命中 3-9 或 10+ passed（拆 alternation）|
| AC-8 | **behavioral** | self_check 本 block 全 PASS + apps/web npm run build 干净 | `DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 bash scripts/_self_check.sh repo-files-tab-v2` 退码 0；`(cd apps/web && npm run build 2>&1 \| tee /tmp/dataplat-web-build.log >/dev/null) && grep -q 'built in' /tmp/dataplat-web-build.log && ! grep -q 'error TS' /tmp/dataplat-web-build.log && ! grep -qE 'Found [0-9]+ errors' /tmp/dataplat-web-build.log` | 本 block 8/8 PASS + build 0 error（错误检查拆为 2 个独立 `! grep`，避 ERE alternation）|

**Behavioral AC：AC-6 + AC-7 + AC-8**，满足 ≥1 自约束。

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| TanStack Router search params 类型化（`validateSearch`）若与项目既有用法不一致 → tsc 编译失败 | 中 | 中 | reviewer v1 实读确认仓库**无 validateSearch 先例**；本 change 用 `validateSearch: (s) => ({ tab: ['files','ingest','pipelines'].includes(s.tab as string) ? s.tab : 'files' })` 极简校验；T-9 npm run build 含 tsc --noEmit，自动检测 |
| 后端 BlobStore.get_size 异常处理（key 不存在 vs S3 transient error）行为不一致 → 404 误返 500 | 低 | 低 | **v1 reviewer 已查关闭**：`minio_store.py` L168-178 `get_size` 返回 `int \| None`，ClientError ∈ `_NOT_FOUND_CODES` → None，其他 raise → FastAPI 500；spec router 的 `None → 404, else 200` 假设成立，无需 try/except |
| `path` query string 含 `/` / 中文 / 特殊字符（URL encoding）→ DOM 显示破损或 navigate 不正确 | 中 | 低 | 全部 path 走 `encodeURIComponent` / `decodeURIComponent`；entries 表里 e.name 直接传 search，TanStack Router 自动 encode；BlobPage 用 `decodeURIComponent` 显示面包屑 |
| Markdown 极简渲染漏处理 edge case（如未闭合 fenced / 多级嵌套 list）造成异常 | 中 | 低 | 写 5 行 markdown 测试 fixture 覆盖：3 级 heading / 段落 / 列表 / fenced code；未闭合 fenced 按"剩余全是 code"处理；fenced block 内行不触发 heading/list/paragraph 识别（AC-4 描述 (b) 已明示）；不抛异常 |
| Vitest 测试需 jsdom + TanStack Router memory history wrapper | 低 | 低 | **v1 reviewer 已查**：`repos.test.tsx` L47-53 已有 `createMemoryHistory + createRouter` 先例，可直接复用；AC-6 (b) 明示走此模式 |
| 5 MB 文本一次性 fetch → toString → React 渲染 → 浏览器卡顿（尤其 jsonl 单行超长）| 低 | 中 | 用 `whitespace-pre-wrap break-all` + 隐式 React 文本节点；接受首版风险；follow-up 改虚拟滚动 |
| Tab 切换时 PipelinesSection 内部 `activeRunId` 局部 state 丢失（unmount remount）| 低 | 低 | **v1 reviewer 已查**：PipelinesSection useState + usePipelineRun(enabled=!!runId) + useCreatePipelineRun（mutation 不自动 fire），无 unconditional 副作用 → 用 `hidden` className 而非条件 mount 安全 |

## 受影响模块

- `apps/api/dataplat_api/routers/commits.py`：加 `get_blob_meta` 路由（~25 行）
- `apps/api/dataplat_api/schemas/blob.py`：加 `BlobMetaResponse`（新文件，或加在既有 `schemas/__init__.py` 邻近 BlobUploadResponse 处）
- `apps/api/dataplat_api/schemas/__init__.py`：export `BlobMetaResponse`
- `apps/api/tests/test_commits.py`：加 3 测试
- `apps/web/src/lib/api/queries.ts`：加 `BlobMetaResponse` interface + `useBlobMeta` hook
- `apps/web/src/routes/repos/$owner.$name.tsx`：重构 RepoDetailPage 加 Tabs；FilesSection 改 Link
- `apps/web/src/routes/blob.$owner.$name.$hash.tsx`：**新建**
- `apps/web/src/lib/api/blob-meta.test.tsx`：**新建**
- `apps/web/src/routes/repos.tabs.test.tsx`：**新建**
- `apps/web/src/routes/blob.test.tsx`：**新建**
- `scripts/_self_check.sh`：加 `run_repo_files_tab_v2` block + 入口 dispatch
- `apps/web/src/routeTree.gen.ts`：自动重生成（vite 编译时由 `@tanstack/router-vite-plugin` 处理；不手改）

## 不受影响但易混淆的模块

- `apps/web/src/routes/commits.$owner.$name.$hash.tsx`：commit 详情页**不动**；其历史快照视图与 Files Tab 工作目录视图职责不同。
- `apps/web/src/routes/repos/$owner.$name.tsx` 内的 `IngestSection` / `PipelinesSection` 实现：**不动函数体**，仅作为 children 移入 Tab 容器；含 props 签名、useState、handler。
- `apps/api/dataplat_api/routers/commits.py` 的 `upload_blob` / `download_blob` / `create_commit` / `get_commit`：不动。
- `repo-files-tab-20260517` change 的 self_check block `run_repo_files_tab`：保留不动；新 block 与之并存（覆盖不同 AC）。

## 待澄清问题

> 在阶段 1 评审前必须清零，或显式标记 deferred。

- [x] Tab 状态：URL search param（决策：✓ `?tab=`，理由见 summary）
- [x] 文件预览路由：独立 `/blob/$owner/$name/$hash`（决策：✓ 用户明示要可分享）
- [x] sha vs path 谁做 URL path：sha 做 path / path 做 query（决策：✓ sha 是 CAS 一等公民；commit 内同 path 可能不同 sha，sha 不能重名）
- [x] Markdown 范围：内置 4 类语法 + 不引依赖 + fenced 优先级最高（决策：✓ 80% 价值 + 零依赖；AC-4 描述 (b) 已明示压制规则）
- [x] size 探测：后端新 `/meta` 端点（决策：✓ 避免浪费带宽）
- [x] Tab 切换时是否保留 PipelinesSection 内部 state：用 CSS hidden（决策：✓）
- [x] **stage 2 reviewer v1 查 BlobStore.get_size 异常路径**：已关闭——`get_size` 返回 `int | None`，blob 不存在时 ClientError code ∈ `_NOT_FOUND_CODES` → return None；spec 的 `None → 404` 假设完全成立，无需补强 AC，无需 router 加 try/except（详 `spec_review_v1.md §必查 3`）

## 引用

- `.harness/changes/repo-files-tab-20260517/` 既有 Files section 实现 + 设计取舍
- `.harness/changes/pipeline-ui-tab-20260518/request_analysis/spec.md` AC 分层规约 + ERE alternation 修复模式
- `.harness/changes/pipeline-ui-tab-20260518/request_analysis/review/spec_review_v1.md` ERE `\|` 字面竖线 MUST FIX 实证（同型 bug 警示）
- `apps/api/dataplat_api/routers/commits.py` L93-148（upload / download blob 现状）
- `apps/api/dataplat_api/storage/minio_store.py` L168-178（get_size 实现 + `_NOT_FOUND_CODES`）
- `apps/api/dataplat_api/schemas/tree.py`（TreeEntry MVP 仅 blob，无嵌套）
- `apps/web/src/routes/repos/$owner.$name.tsx`（既有 FilesSection / IngestSection / PipelinesSection）
- `apps/web/src/routes/commits.$owner.$name.$hash.tsx`（路由命名约定参考）
- `apps/web/src/routes/repos.test.tsx` L47-53（createMemoryHistory + createRouter 测试模式参考）
- `apps/web/src/lib/api/pipeline.test.tsx` L68（vi.spyOn(globalThis, "fetch") 模式参考）
- `.harness/skills/request-analysis/SKILL.md` § AC 分层规约
- `.harness/rules/development-process.md`
