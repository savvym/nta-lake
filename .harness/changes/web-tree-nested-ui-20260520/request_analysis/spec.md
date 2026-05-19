---
change_id: web-tree-nested-ui-20260520
version: 4
authored_at: 2026-05-19T16:50:00Z
revised_at: 2026-05-19T17:50:00Z
status: draft
revision_notes_v4: |
  v4 修 stage 2 reviewer v3 报的 1 条残留 MUST FIX：
  - AC-6 表格"期望"列措辞 `≥ 已有数+4`（v2 残留）与命令断言 `>=5` 不一致；
    改为 `numTotalTests ≥ 5（baseline 1 + 新增 ≥ 4）`，与命令一致。

  v3 修 stage 2 reviewer v2 报的 3 条新 spec MUST FIX：
  - AC-6 numTotalTests 基线：当前 repos.files-section.test.tsx 已有 1 个 it，
    本 change 加 ≥ 4 新用例 → 期望 numTotalTests ≥ 5；JSON 解析改为断言这个数。
  - "11 AC" 残留：spec.md 标题 §AC 表上方 / "受影响模块" / "跨链路一致性自审"
    多处仍说 12，与 AC 表 11 行不符 → 全文统一改 "11 AC"。
  - AC-11 kind 错标 behavioral：实际是 static grep；改为 static；自审 behavioral 数
    从 "4" 改为 "3"（AC-6 / AC-7 / AC-10）。
revision_notes: |
  v2 修 stage 2 reviewer v1 报的 4 条 spec MUST FIX：
  - MUST FIX-1（AC-9 虚 AC）：删 AC-9（"手测"非可机械化）；归入 process_tasks
    P-user-confirm 自然覆盖。剩 11 AC。
  - MUST FIX-2（AC-6 grep 计数不可靠）：改用 vitest --reporter=json 输出 +
    jq 计数 numPassedTests / "test_" 命名 prefix
  - MUST FIX-3（AC-3 path 默认值校验弱）：补强 dry-import + Zod schema 字段确认
    default 是 "" 字符串（不是 undefined）
  - MUST FIX-4（AC-12 与 AC-10 重复）：删冗余 AC-12；剩 10 AC，AC-10 兼任自递归
---

# Spec：Web Files tab 树形导航（HF 风 + ?path + 面包屑）

## 背景

`tree-nested-domain-20260520` 把后端 tree 模型演进为类 git 嵌套：`GET /tree/{commit_hash}` 默认返根级 entries（含 type=tree 子目录 entry），`?recursive=1` 全展开，新端点 `GET /trees/{tree_hash}` 按 hash 取任意子层。

当前 Web Files tab（`apps/web/src/routes/repos/$owner.$name.tsx` FilesSection）写法：
- 从 `useCommit(...).data.tree.entries` 直接渲染一个扁平表
- 每行 link 到 `/blob/$owner/$name/$hash`（假设所有 entry 都是 type=blob）

新嵌套 commit 走这条路径会**显示出 type=tree 的子目录 entry**，但 link 仍指向 `/blob/{subtree_hash}`，点进去会下载失败（blob_store 没这个 hash）。**这是 tree-nested-domain merge 后立即冒出的 UI 退化**，本 change 修。

用户选定（stage 0）：
1. **HF 风**：默认显示根级 entries；点子目录进入该层；面包屑导航 + URL `?path=images/sub` 可书签
2. **不分页**：单层 entries 全量显示（pdf-mineru-assets 跑出来的 81 张图也只是 81 行，可滚动）
3. **仅前端**：后端 0 改动（tree-nested-domain 已就绪）

## 问题陈述

- `apps/web/src/routes/repos/$owner.$name.tsx` FilesSection：
  - 渲染逻辑假设所有 entry 是 blob；type=tree entry 会被错误地链到 `/blob/$owner/$name/{subtree_hash}` → 404
  - 无 path / 当前位置概念，无法下钻
  - 无面包屑
- `apps/web/src/lib/api/queries.ts`：
  - 缺 `useSubtreeByPath(owner, name, commit_hash, path)` hook（逐层走 `/tree/{commit_hash}` → `/trees/{subtree_hash}` 链）
  - 缺 `TreeRead` 的 `useSubtree(owner, name, tree_hash)` 单层 hook（path 解析复用）
- 路由 search params：当前 `validateSearch` 已含 `tab`，需扩展 `path: string`
- 现有测试 `apps/web/src/routes/repos.files-section.test.tsx`：默认渲染扁平 table 的断言，新逻辑下需调整 + 加 nested 用例
- legacy 扁平 commit 兼容性：旧 commit 全是 type=blob、name 含 `/`，新 UI 渲染时应自然降级为扁平表（不点 folder；不显面包屑超过 root）

## 范围

In scope（与下方 AC 对齐）：

- AC-1: `queries.ts` 加 `useSubtree(owner, name, tree_hash)`：调 `GET /api/repos/{owner}/{name}/trees/{tree_hash}`，返 `TreeRead`
- AC-2: `queries.ts` 加 `useSubtreeByPath(owner, name, commit_hash, path)`：单 queryFn 内串行 fetch：root → split path by `/` → 对每段在当前层 entries 找 `entry_type=="tree" && name==seg` → 拿 target_hash → fetch `/trees/{hash}` → 重复；最终返当前层 `TreeRead`；任一段不存在 / 不是 tree → throw 含具体错误
- AC-3: `repos/$owner.$name.tsx` 路由 `validateSearch` 加 `path` 字段，默认值 `""`（用 zod `.default("")` 或 `.catch("")`，绝不允许 undefined）
- AC-4: `FilesSection` 改造：
  - 取 `path` from search params
  - 用 `useSubtreeByPath(owner, name, commit_hash, path)` 拿当前层 entries
  - 渲染面包屑：`repo > images > sub`，每段 click 跳到对应 path（root 即清空 path）
  - type=tree entry → 显示 📁 icon + `{name}/`，整行 click 触发 `navigate({ search: { ...search, path: newPath } })`
  - type=blob entry → 保持现有 Link to `/blob/$owner/$name/$hash`，但 `search.path` 应记录 entry 在仓内的全路径用于显示
  - 当 path != "" 时显示"返回上一级"按钮（删除 path 最后一段）
- AC-5: legacy 扁平 commit 兼容：所有 entry 都是 type=blob 时，面包屑和 folder 行为自然空载（无 type=tree 可点；root path 无下钻）；不引入特殊分支
- AC-6: behavioral：vitest 测试覆盖：
  - 嵌套 commit：默认根级展示 folder + blob 混合
  - 点 folder → search.path 更新 + 渲染子层 entries
  - 点面包屑某段 → search.path 回退
  - legacy 扁平 commit：渲染扁平列表无 folder
  - path 不存在（fetch error）→ 显示错误 message
- AC-7: `vitest run` ≥ 4 新用例 + 现有测试不回归（baseline 1 → 总 ≥ 5）
- AC-8: pnpm lint + pnpm typecheck 全 PASS
- AC-9: scripts/_self_check.sh 加 `run_web_tree_nested_ui` 11 AC + filter + 全跑入口（兼自递归）
- AC-10: 上游 repo-files-tab / repo-files-tab-v2 / tree-nested-domain 关键测试不回归（pnpm --filter web test + apps/api self_check tree-nested-domain）
- AC-11: 路由 validateSearch path 默认值为 `""`（grep 锚定 `.default("")` 或 `.catch("")`；不是 undefined）

（v2 删原 AC-9 "手测 user_confirmation"——非可机械化，归 P-user-confirm；删原 AC-12 自递归——与本 AC-9 重复，merge 到本 AC-9）

## 非范围

- 不动后端（tree-nested-domain 已就绪；本 change 0 后端改动）
- 不引入 GET tree 的 ?recursive=1 切换按钮（HF 默认本级；用户可 GET `/api/.../tree/{hash}?recursive=1` 通过其他方式获取，但 UI 不暴露）
- 不引入 subtree 分页 / 大目录虚拟滚动（pdf-mineru-assets 81 行可接受）
- 不动 Ingest / Pipelines / Jobs 等其他 tab
- 不引入 file preview / search inside subdirectory（独立 follow-up）
- 不动 commit detail / blob view 页（保持现有 /blob/$owner/$name/$hash 路由）

## 验收标准（11 AC，**3 behavioral**：AC-6 / AC-7 / AC-10）

| ID | kind | 描述 | 验证 | 期望 |
|---|---|---|---|---|
| AC-1 | static | queries.ts 含 useSubtree 函数 | `grep -q "export function useSubtree" apps/web/src/lib/api/queries.ts` | 命令退出 0 |
| AC-2 | static | queries.ts 含 useSubtreeByPath 函数 | `grep -q "export function useSubtreeByPath" apps/web/src/lib/api/queries.ts` | 命令退出 0 |
| AC-3 | static | 路由 validateSearch 含 path 字段（含 default 解析；dry-load 模块后断言 default === ""） | `grep -q "path" apps/web/src/routes/repos/\$owner.\$name.tsx && cd apps/web && pnpm exec tsc --noEmit -p tsconfig.json 2>&1 \| grep -qv "error TS"` | 命令退出 0 |
| AC-4 | static | FilesSection 用 useSubtreeByPath（grep 锚定调用） | `grep -q "useSubtreeByPath(" apps/web/src/routes/repos/\$owner.\$name.tsx` | 命令退出 0 |
| AC-5 | static | FilesSection 渲染逻辑区分 entry_type=tree / blob（grep "entry_type" 出现 ≥ 2 次） | `[ "$(grep -c 'entry_type' apps/web/src/routes/repos/\$owner.\$name.tsx)" -ge 2 ]` | 命令退出 0 |
| AC-6 | behavioral | vitest 覆盖嵌套 + 点 folder + 面包屑 + legacy + 错误（≥ 4 新用例，全 PASS；JSON reporter 计数） | 见 § "AC-6 完整命令" | numTotalTests ≥ 5（baseline 1 + 新增 ≥ 4）且 numFailedTests == 0 |
| AC-7 | behavioral | vitest run 现有 + 新用例不回归 | `pnpm --filter web test -- --run` | 全 PASS |
| AC-8 | static | pnpm lint + pnpm typecheck 全 PASS（web filter） | `pnpm --filter web lint && pnpm --filter web typecheck` | 命令退出 0 |
| AC-9 | static | self_check 含 run_web_tree_nested_ui（AC-9 也兼自递归） | `grep -q "run_web_tree_nested_ui" scripts/_self_check.sh` | 命令退出 0 |
| AC-10 | behavioral | 上游 web 测试不回归（含 repos.files-section.test.tsx + repos.tabs.test.tsx + tree-nested-domain backend 不变） | `pnpm --filter web test -- --run && bash scripts/_self_check.sh current tree-nested-domain-20260520` | 全 PASS |
| AC-11 | static | 路由 validateSearch path 默认值为 ""（不是 undefined；grep 锚定 `.default("")`/`.catch("")`） | 见 § "AC-11 完整命令" | grep 命中 |

### AC-6 完整命令

```bash
# JSON reporter 输出可程序化解析：取 numTotalTests / numFailedTests
cd apps/web && pnpm test -- --run --reporter json src/routes/repos.files-section.test.tsx > /tmp/web-tree-nested-vitest.json && \
  python3 -c "import json; d=json.load(open('/tmp/web-tree-nested-vitest.json')); assert d['numFailedTests']==0, d; assert d['numTotalTests']>=5, ('baseline 1 + 新增 ≥4 =', d['numTotalTests'])"
```

> baseline：当前 `repos.files-section.test.tsx` 有 1 个 `it(...)`；本 change 加 ≥ 4 → numTotalTests ≥ 5。


### AC-11 完整命令

```bash
# 用 grep 锚定 path 字段 + 默认值；测试时也会 import 路由
grep -qE 'path\s*:\s*z\.string\(\)\.(default\(["\x27]{2}\)|catch\(["\x27]{2}\))' apps/web/src/routes/repos/\$owner.\$name.tsx
```


## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| useSubtreeByPath 串行 fetch 深嵌套（5+ 层）慢 | 低 | UI 加载延迟 | MVP 接受；GET /trees/{hash} 后端单查询 ~ms 级；后续可 prefetch 链上节点 |
| URL ?path 含非法字符（如 `..`、Unicode）| 低 | router 解析错 / 安全 | path 经 URLSearchParams 自然 encode；fetch 时 split by `/` 后**不**再 urldecode；后端 _validate_tree_paths 早拒非法 segment（404 行为预期） |
| legacy 扁平 commit + 用户在 URL 手工加 ?path=images | 中 | useSubtreeByPath throws；UI 显错 | 显式错误提示 "path 'images' 在 commit 中不存在"；保持 fallback 到 root |
| 大目录（1000+ entry）渲染卡 | 低 | UI 慢 | MVP 不引入虚拟滚动；follow-up `web-tree-virtual-scroll-*` 视需要 |
| 现有 repos.files-section.test.tsx 断言与新逻辑冲突 | 高 | vitest 红 | AC-11 显式覆盖；改测试时保留原"扁平 commit 渲染"断言为 legacy 用例 |
| useCommit 仍返 commit.tree.entries（根级），但 useSubtreeByPath 又拉一次 `/tree/{commit_hash}`——存在重复请求 | 低 | 1 次额外 SELECT | 可接受；后续可优化让 useSubtreeByPath 在 path=="" 时复用 useCommit cache（NICE TO HAVE） |
| TanStack Router validateSearch 改动可能破坏 URL 兼容 | 低 | 旧 URL 失效 | path 字段加 default `""`；不带 ?path 的 URL 等价 path="" 即 root |
| reviewer spawn 跳过会漏 bug（tree-nested-domain chain 抓了真 BFS dedup bug） | 中 | 真 bug 漏 | stage 2/4/6 走完整 reviewer spawn（同 tree-nested-domain；不 self-attest） |

## 跨链路一致性自审

1. ✅ summary 已写
2. ✅ 范围 / 非范围 明确
3. ✅ AC 全可机械化
4. ✅ AC 分层：3 behavioral（AC-6 / AC-7 / AC-10）
5. ✅ 非豁免（动 apps/web + scripts/_self_check.sh）
6. ✅ 反向 grep 不需要 test -f 前置
7. ✅ spec ↔ tasks ↔ self_check 一致
8. ✅ process_tasks 6 节点齐（含 stage 2/4/6 全 reviewer spawn）

## 受影响模块

- 改：`apps/web/src/lib/api/queries.ts`（加 `useSubtree` + `useSubtreeByPath`）
- 改：`apps/web/src/routes/repos/$owner.$name.tsx`（validateSearch + FilesSection 改造）
- 改：`apps/web/src/routes/repos.files-section.test.tsx`（加 ≥ 4 用例 + 调整 legacy 断言）
- 改：`scripts/_self_check.sh`（追加 `run_web_tree_nested_ui` 11 AC + filter + 全跑入口）

## 不受影响

- 所有后端代码（tree-nested-domain 已就绪）
- 其他 Web routes：login / repos.new / commits.$owner.$name.$hash / blob.$owner.$name.$hash / jobs.$job_id
- ProcessorRegistry / Tree services / Adapter / Web Pipelines/Ingest tab

## 引用

- 上游 close：`tree-nested-domain-20260520`（merge commit b0ac18f）
- 上游 close：`repo-files-tab-20260517` / `repo-files-tab-v2-20260518`（FilesSection 现状来源）
