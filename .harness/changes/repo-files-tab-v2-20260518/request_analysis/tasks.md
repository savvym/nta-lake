---
change_id: repo-files-tab-v2-20260518
version: 2
authored_at: 2026-05-18T22:15:00Z
prior_version: 1
prior_review: request_analysis/review/tasks_review_v1.md
---

# Tasks

> 任务粒度 1-3 小时。每个任务都要标明 `depends_on` 与 `estimated_stage`。
>
> **v2 修订说明**：闭 tasks_review_v1 的 1 SHOULD FIX-T-1（T-10 加备注）+ 1 NICE-T-1（T-8b 删降级方案）。tasks_review_v1 已表态 spec_v2 关 MUST FIX 后 tasks 无需独立重评。

## 任务清单

```yaml
tasks:
  - id: T-1
    title: 后端 schemas/blob.py 加 BlobMetaResponse + __init__.py 导出
    description: |
      新建 apps/api/dataplat_api/schemas/blob.py（如不存在），加：
        class BlobMetaResponse(BaseModel):
            model_config = ConfigDict(extra="forbid")
            sha256: SHA256
            size: int
      在 apps/api/dataplat_api/schemas/__init__.py 加 import + __all__ 导出。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1]
    status: pending
    commits: []

  - id: T-2
    title: 后端 routers/commits.py 加 get_blob_meta 路由
    description: |
      在 commits.py 中既有 download_blob 函数下方加：
        @router.get(
            "/{owner}/{name}/blobs/{sha256}/meta",
            response_model=BlobMetaResponse,
        )
        async def get_blob_meta(
            owner: str,
            name: str,
            sha256: str = Path(pattern=_SHA256_PATTERN),
            current_user: AuthenticatedUser | None = Depends(get_optional_user),
            session: AsyncSession = Depends(get_session),
            store: BlobStore = Depends(get_blob_store),
        ) -> BlobMetaResponse:
            await _resolve_repo(session, owner, name, current_user)
            size = await store.get_size(sha256)
            if size is None:
                raise HTTPException(status_code=404, detail=f"Blob {sha256} 不存在")
            return BlobMetaResponse(sha256=sha256, size=size)
      复用既有 _SHA256_PATTERN / _resolve_repo / get_optional_user / get_blob_store；
      不动 upload_blob / download_blob 实现。
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-1]
    status: pending
    commits: []

  - id: T-3
    title: 后端 test_commits.py 加 3 个 test_blob_meta 测试
    description: |
      apps/api/tests/test_commits.py 末尾加：
        test_blob_meta_returns_size：上传 b"hello" → GET /blobs/{sha}/meta → 200 +
          {sha256, size: 5}
        test_blob_meta_not_found：GET /blobs/{'9'*64}/meta → 404
        test_blob_meta_public_anon：建 public repo → 匿名客户端 GET /blobs/{sha}/meta → 200
      复用既有 fixtures + ASGITransport 模式。
    depends_on: [T-2]
    estimated_stage: unit_test
    covers_ac: [AC-7]
    status: pending
    commits: []

  - id: T-4
    title: 前端 queries.ts 加 BlobMetaResponse interface + useBlobMeta hook
    description: |
      在 apps/web/src/lib/api/queries.ts 末尾加：
        export interface BlobMetaResponse {
          sha256: string;
          size: number;
        }
        export function useBlobMeta(owner: string, name: string, sha256: string) {
          return useQuery({
            queryKey: ["blob-meta", owner, name, sha256],
            queryFn: () =>
              fetchJson<BlobMetaResponse>(
                `/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}/blobs/${encodeURIComponent(sha256)}/meta`,
              ),
            enabled: /^[0-9a-f]{64}$/.test(sha256),
          });
        }
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-2]
    status: pending
    commits: []

  - id: T-5
    title: 前端 RepoDetailPage 重构为 Metadata + Tabs（保留三个 section 组件不变）
    description: |
      apps/web/src/routes/repos/$owner.$name.tsx：
        - 在 createFileRoute 加 validateSearch：
            (s) => ({ tab: ['files','ingest','pipelines'].includes(String(s.tab))
              ? (s.tab as 'files'|'ingest'|'pipelines') : 'files' })
        - RepoDetailPage 中：
            const search = Route.useSearch();
            const navigate = Route.useNavigate();
            const activeTab = search.tab;
            const onTabChange = (t) => navigate({ search: { tab: t }, replace: false });
        - JSX 改为：
            <h1>...</h1> + Metadata <Card>
            + <Tabs activeTab={activeTab} onChange={onTabChange} isAdmin={isAdmin}>
                <TabPanel hidden={activeTab !== 'files'}><FilesSection ... /></TabPanel>
                {isAdmin && (
                  <>
                    <TabPanel hidden={activeTab !== 'ingest'}><IngestSection ... /></TabPanel>
                    <TabPanel hidden={activeTab !== 'pipelines'}><PipelinesSection ... /></TabPanel>
                  </>
                )}
              </Tabs>
        - Tabs / TabPanel 同文件内本地小组件（不抽 components/ui/tabs.tsx，避免范围爆炸）
        - **重要：TabPanel 用 `hidden` className 而非条件 mount**，保留 PipelinesSection 内部
          state（activeRunId）跨 Tab 切换
        - 非 admin 只看到 Files Tab；Ingest/Pipelines Tab trigger 不渲染
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-3]
    status: pending
    commits: []

  - id: T-6
    title: 前端 FilesSection 表 path 列改为 Link → /blob 路由
    description: |
      apps/web/src/routes/repos/$owner.$name.tsx 内 FilesSection：
        <td>{e.name}</td>
      改为：
        <td>
          <Link
            to="/blob/$owner/$name/$hash"
            params={{ owner, name, hash: e.target_hash }}
            search={{ path: e.name }}
            className="text-blue-700 hover:underline break-all"
          >
            {e.name}
          </Link>
        </td>
      "下载"列不动。
    depends_on: [T-5]
    estimated_stage: coding
    covers_ac: [AC-5]
    status: pending
    commits: []

  - id: T-7
    title: 前端新建路由 blob.$owner.$name.$hash.tsx（4 渲染策略 + 5MB 守门）
    description: |
      apps/web/src/routes/blob.$owner.$name.$hash.tsx，含：
        - createFileRoute("/blob/$owner/$name/$hash") + validateSearch:
            (s) => ({ path: typeof s.path === 'string' ? s.path : '' })
        - BlobPage 函数：
            const { owner, name, hash } = Route.useParams();
            const { path } = Route.useSearch();
            const metaQuery = useBlobMeta(owner, name, hash);
        - 面包屑：Link("/repos/$owner/$name?tab=files") → "Files" → <path or '(unknown path)'>
        - 副信息卡：sha256 完整 + 复制按钮（navigator.clipboard）；size（KB/MB 格式化）；
          ref 固定 "—"
        - 5MB 守门：常量 MAX_PREVIEW_SIZE = 5 * 1024 * 1024；
          if metaQuery.data && metaQuery.data.size > MAX_PREVIEW_SIZE：渲染
            "文件过大（X.X MB > 5 MB）" + 下载按钮（指向 /api/.../blobs/{hash}）
        - 否则 detectKind(path) 分派：
            text 扩展名 → fetchText hook（自定义；fetch + resp.text() + setText）→
              <pre><code className="text-xs font-mono whitespace-pre-wrap break-all">
            .md → 同上 + "Source / Rendered" toggle 按钮；Rendered 调
              renderMinimalMarkdown(text)
            图片扩展名 → <img src=`/api/.../blobs/${hash}` className="max-w-full" />
            其他 → "二进制文件，无法预览。size: X · sha256: ABC…" + 下载按钮
        - renderMinimalMarkdown(src: string): ReactNode[] 实现 4 类语法（见 spec AC-4）：
            // 按行扫描；fenced code 用栈状态机；其他直接 map
        - detectKind(path: string): 'text' | 'markdown' | 'image' | 'binary'
        - formatSize(bytes: number): string  (e.g. "12.3 KB", "1.2 MB")
    depends_on: [T-4]
    estimated_stage: coding
    covers_ac: [AC-4]
    status: pending
    commits: []

  - id: T-8a
    title: vitest 新建 blob-meta.test.tsx（hook 测试）
    description: |
      apps/web/src/lib/api/blob-meta.test.tsx，1 测试：
        useBlobMeta 成功路径：vi.spyOn(global, 'fetch') 返 {sha256, size: 1234} →
          renderHook + QueryClientProvider wrapper → waitFor data → 断言 data.size === 1234
      参考既有 src/lib/api/pipeline.test.tsx 模式（spyOn 不用 msw）。
    depends_on: [T-4]
    estimated_stage: unit_test
    covers_ac: [AC-6]
    status: pending
    commits: []

  - id: T-8b
    title: vitest 新建 repos.tabs.test.tsx（Tab URL state）
    description: |
      apps/web/src/routes/repos.tabs.test.tsx，1 测试：
        Tab URL state 切换：mock useRepo/useMe/useRepoRef/useCommit 等（vi.mock 模式）+
          createMemoryHistory({ initialEntries: ['/repos/test/r?tab=files'] }) +
          createRouter({ routeTree, history }) → renderRouter → 点击 "Pipelines" Tab →
          等 URL 更新 → assert router.state.location.search 含 tab=pipelines
      **createMemoryHistory + createRouter 已在仓库建立（repos.test.tsx L47-53）**，
      直接复用模式，无需降级方案。
      参考既有 src/routes/repos.test.tsx / repos.pipelines-section.test.tsx 的 vi.mock 模式。
    depends_on: [T-5]
    estimated_stage: unit_test
    covers_ac: [AC-6]
    status: pending
    commits: []

  - id: T-8c
    title: vitest 新建 blob.test.tsx（3 测试：文本 / 二进制 / size 守门）
    description: |
      apps/web/src/routes/blob.test.tsx，3 测试：
        (c) 文本预览：
            mock useBlobMeta 返 {sha256:'a'*64, size: 11}
            spy fetch（GET /blobs/{sha}）返 text "hello world"
            params={ owner:'o', name:'n', hash:'a'*64 }, search={ path:'x.txt' }
            screen.findByText('hello world') 命中
        (d) 二进制 fallback：
            mock useBlobMeta 返 size: 1024
            search={ path:'data.bin' }
            screen.getByText(/二进制文件/) 命中 + 下载按钮在
        (e) 5MB 守门：
            mock useBlobMeta 返 size: 6 * 1024 * 1024
            search={ path:'big.txt' }
            screen.getByText(/文件过大/) 命中 + fetch text 不被调用
            (vi.spyOn(global, 'fetch') + 断言只有 useBlobMeta 那一次 mocked call)
      用 vi.mock("../lib/api/queries", ...) 模式。
    depends_on: [T-7]
    estimated_stage: unit_test
    covers_ac: [AC-6]
    status: pending
    commits: []

  - id: T-9
    title: 跑通 vitest 3 文件 + npm run build + pytest blob_meta
    description: |
      cd apps/web
      npx vitest run src/lib/api/blob-meta.test.tsx src/routes/repos.tabs.test.tsx \
        src/routes/blob.test.tsx
      期望: Test Files 3 passed; Tests ≥5 passed
      npm run build
      期望: 含 "built in"; 不含 "error TS" 或 "Found N errors"

      cd apps/api
      uv run pytest -q --tb=no tests/test_commits.py -k blob_meta
      期望: ≥3 passed
    depends_on: [T-3, T-8a, T-8b, T-8c]
    estimated_stage: unit_test
    covers_ac: [AC-6, AC-7, AC-8]
    status: pending
    commits: []

  - id: T-10
    title: scripts/_self_check.sh 加 run_repo_files_tab_v2 block
    description: |
      在 main 调用链插入 run_repo_files_tab_v2（pipeline-ui-tab 之后、stage9-followup-cleanup 之前）。
      **AC 命令以 spec_v2.md 的"验证方式"列为准**——本任务 description 中的 8 行摘要
      仅作签证范围参考，不要照搬本 description 写 self_check.sh；coding 时打开 spec_v2.md
      §验收标准表格，复制每条 AC 的 bash 命令（已修 v1 review 5 MUST FIX：拆 alternation
      为 shell `||` 链 / 路径去单引号 / 去掉 `$()` 内 awk count）。
      8 个 AC（spec_v2 验证方式概述）：
        AC-1 static：4 直接 grep（router 路径 / 函数名 / schema class / schema 文件存在）
        AC-2 static：4 grep（含 awk 状态机锚定 useBlobMeta 函数体内 /meta）
        AC-3 static：5 直接 grep + 1 个 alternation 组（Route.useSearch 或 useSearch）
        AC-4 static：3 直接 grep + 3 个 alternation 组（5MB 常量 / Markdown 锚 / 图片扩展名 各组任一命中）
        AC-5 static：2 awk+grep（FilesSection 函数体内含 /blob/ 路径 + search）
        AC-6 behavioral：cd apps/web && npx vitest run 3 测试文件 → 2 grep `Tests +[5-9] passed` 或 `Tests +[1-9][0-9]+ passed` 任一命中
        AC-7 behavioral：cd apps/api && uv run pytest -k blob_meta → 2 grep `[3-9] passed` 或 `[1-9][0-9]+ passed` 任一命中
        AC-8 behavioral：cd apps/web && npm run build → grep `built in` + 2 个独立 `! grep`（error TS / Found N errors）
      加 case 分支 repo-files-tab-v2 | repo-files-tab-v2-20260518。
      帮助文案 echo "已知 change" 加 repo-files-tab-v2。
    depends_on: [T-2, T-5, T-6, T-7]
    estimated_stage: coding
    covers_ac: [AC-8]
    status: pending
    commits: []
```

## 阶段任务（必备占位，不要漏）

```yaml
process_tasks:
  - id: P-spec-review
    estimated_stage: stage-2
    status: pending

  - id: P-code-review
    estimated_stage: stage-4
    status: pending

  - id: P-test-review
    estimated_stage: stage-6
    status: pending

  - id: P-push
    estimated_stage: stage-7
    status: pending

  - id: P-ci
    estimated_stage: stage-8
    status: self-attest
    notes: "项目无 remote 长期未决"

  - id: P-deploy
    estimated_stage: stage-9
    status: pending
    notes: "有部署面（前后端都有改动），必须真跑 deploy_verify（本机起 API 8080 + Web 5174 + npm run build）"

  - id: P-user-confirm
    estimated_stage: stage-10
    status: pending
```

## DAG 健全性

```text
T-1 ──→ T-2 ──→ T-3 ─┐
                     │
T-4 ──┬─→ T-7 ──→ T-8c ─┐
      ├─→ T-8a ─────────┤
T-5 ──┬─→ T-6           │
      └─→ T-8b ─────────┤
                        ├──→ T-9
T-2, T-5, T-6, T-7 ─────→ T-10
```

无环。终点 T-9（真跑 vitest + pytest + build）+ T-10（self_check block）。

## 验收覆盖矩阵

| AC | kind | 关联任务 |
|---|---|---|
| AC-1 | static | T-1, T-2, T-10 |
| AC-2 | static | T-4, T-10 |
| AC-3 | static | T-5, T-10 |
| AC-4 | static | T-7, T-10 |
| AC-5 | static | T-6, T-10 |
| AC-6 | **behavioral** | T-8a, T-8b, T-8c, T-9, T-10 |
| AC-7 | **behavioral** | T-3, T-9, T-10 |
| AC-8 | **behavioral** | T-9, T-10 |

每条 AC 至少 2 个非 process_tasks 任务覆盖（含 T-10 self_check）。

**behavioral AC：AC-6 + AC-7 + AC-8**，满足 ≥1。
