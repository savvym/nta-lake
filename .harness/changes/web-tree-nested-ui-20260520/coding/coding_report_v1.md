---
change_id: web-tree-nested-ui-20260520
version: 1
authored_at: 2026-05-19T18:30:00Z
branch: change/web-tree-nested-ui-20260520
base_commit: d973fe8
head_commit: TBD（commit 后填）
status: waiting_review
---

# Coding Report v1

## 改动文件清单

| 路径 | 类型 | 一句话说明 | 任务 |
|---|---|---|---|
| `apps/web/src/lib/api/queries.ts` | modify | 新增 `useSubtree` + `useSubtreeByPath`（后者串行 fetch root → 每段 entries → /trees/{hash}）；含 fetchJson null-guard | T-1 |
| `apps/web/src/routes/repos/$owner.$name.tsx` | modify | zod searchSchema 加 `path: z.string().catch("").default("")`；FilesSection 改 HF 风：面包屑 + folder 行 + 返回上一级 + error UI；移除未用 TAB_KEYS 常量 | T-2 / T-3a / T-3b |
| `apps/web/src/routes/repos.files-section.test.tsx` | rewrite | 5 用例：legacy / nested 根 / click folder / 面包屑回退 / path 不存在 error | T-4 |
| `apps/web/src/routes/repos.tabs.test.tsx` | modify | mock 加 `useSubtreeByPath`（avoid undefined export） | T-4 |
| `apps/web/src/routes/repos/index.tsx` | modify | Link search 加 `path: ""`（schema 要求非可选） | T-2 副作用 |
| `apps/web/src/routes/repos.new.tsx` | modify | navigate search 加 `path: ""` | T-2 副作用 |
| `apps/web/src/routes/jobs.$job_id.tsx` | modify | Link search 加 `path: ""` | T-2 副作用 |
| `apps/web/src/routes/blob.$owner.$name.$hash.tsx` | modify | 2 处 Link search 加 `path: ""` | T-2 副作用 |
| `apps/web/src/routes/commits.$owner.$name.$hash.tsx` | modify | 2 处 Link search 加 `path: ""` | T-2 副作用 |

self_check AC block + smoke / lint / vitest 由 stage 8 跑。

## 与 tasks.md 映射

| Task | 状态 | 备注 |
|---|---|---|
| T-1 queries hooks | done | useSubtree + useSubtreeByPath 含 fetchJson null-guard |
| T-2 validateSearch | done | 用 zod schema；path .catch("").default("") |
| T-3a 数据层接入 | done | useSearch / useNavigate + setPath helper |
| T-3b 表现层 | done | 面包屑（button + 中间段可点）+ folder 行（role=button + Enter/Space）+ 返回上一级 + error UI + legacy 提示 |
| T-4 单测 | done | 5 用例（含 1 legacy + 4 新 nested 行为） |
| T-5 self_check AC block | pending | stage 8 |
| T-6 跑 self_check current | pending | stage 8 |

## 偏离 spec / trade-off

- **schema 改 zod 触发链式 path 必填**：原 searchSchema 是 manual `(s) => ({tab})`；改 zod 后 `path: string` 在 parsed 类型里**非可选**（`.default("")` 填充）。导致全仓所有 `to: "/repos/$owner/$name"` 的 Link / navigate 都需要补 `path: ""`。这是 zod 路径 trade-off：换来 AC-11 grep 直接命中、search reducer typing 严格；代价是 7 处机械修改。
- **setPath 不用 reducer fn**：原本 `(prev) => ({...prev, path})` reducer 形式被 typecheck 拒（prev 是 `Record<string, unknown>` 而 reducer 期望已 parsed 类型）。改为 `{ ...search, path: newPath }` 完整对象形式。
- **切 tab 时清空 path**：onTabChange 显式 `{ tab, path: "" }`。spec 说"看交互期望"未明确；选清空因不同 tab 共用 path 字段语义不一致。
- **Empty entries but path != ""**：渲染"空目录"提示，不显错。

## 本地校验结果

```text
pnpm --filter web typecheck → success（0 errors）
pnpm --filter web test -- --run → 26 passed (13 test files)
   含 src/routes/repos.files-section.test.tsx：5 用例全 PASS
   含 src/routes/repos.tabs.test.tsx：现有 4 用例不回归
pnpm --filter web lint → success (placeholder)
```

## 已知未解决

- AC-9 / AC-10 self_check AC block 留到 stage 8（T-5）
- 上游 tree-nested-domain self_check 回归 留到 stage 8（T-6）
- 用户实测（P-user-confirm）留到 stage 10

## 下一步

stage 4：spawn 独立 sonnet code reviewer。
