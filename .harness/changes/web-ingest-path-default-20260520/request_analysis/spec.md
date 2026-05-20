---
change_id: web-ingest-path-default-20260520
version: 1
authored_at: 2026-05-20T10:40:00Z
status: draft
---

# Spec：Ingest 上传默认 path 去 `content/` 前缀（直接放仓根）

## 背景

`apps/web/src/routes/repos/$owner.$name.tsx::IngestSection` 在用户拖拽 / 选文件时硬编码 `path: \`content/${f.name}\``（line 583）。

合并 `tree-nested-domain-20260520` 后，这种"name 含 `/`"的 entry 被 service 自动 split 为嵌套子目录。结果：用户上传 `a.pdf` → silver commit tree 多出一个 `content` 子目录，里面装 `a.pdf`。

用户反馈：与"上传一个 PDF"的直觉不符，多出来的 `content/` 文件夹莫名其妙。HF 风的 Ingest UX 不应强制目录前缀；按"直接用文件名"的默认更直观。批量上传 + 想分目录的用户可以**手工改 path 字段**（UI 已支持 `updatePath`）。

## 问题陈述

- `$owner.$name.tsx` line 583：默认 path 写死 `content/<filename>`，用户无法绕过（除非每个文件单独改 path）
- 现有测试 `repos.tabs.test.tsx` 等若有断言依赖默认 `content/` 前缀，需同步调整
- 历史 commit 数据不动（旧 commit 里已是 `content/xxx` 的扁平 entry，向后兼容由 tree-nested-domain 已保证）

## 范围

In scope（与下方 AC 对齐）：

- AC-1: `$owner.$name.tsx` IngestSection 的 `onFiles` 默认 `path = f.name`（不加任何前缀）；用户可后续 `updatePath` 手工改
- AC-2: 测试断言（如有）调整：search "content/" 在 web 测试文件中应仅出现 0 次（除非作为用户手工输入的 fixture）
- AC-3: vitest 全测试不回归
- AC-4: pnpm typecheck 全 PASS
- AC-5: scripts/_self_check.sh 加 `run_web_ingest_path_default` AC block（含上述）
- AC-6: AC-6 自递归（self_check 含 run_web_ingest_path_default）

## 非范围

- 不动 adapter / 后端代码（raw-file-upload 不感知 path 前缀）
- 不引入 "upload into folder" UI 控件（用户可以编辑 path 字段；高级 UX 留 follow-up `web-ingest-folder-picker-*`）
- 不重写历史 commit
- 不动其他 default path（如未来其他 adapter 的输入）

## 验收标准（6 AC，**2 behavioral**：AC-3 / AC-4）

| ID | kind | 描述 | 验证 | 期望 |
|---|---|---|---|---|
| AC-1 | static | onFiles 默认 path 是 f.name（无 content/ 前缀） | `grep -qE "path:\s*f\.name" apps/web/src/routes/repos/\$owner.\$name.tsx && ! grep -qE "path:\s*\`content/\\\$" apps/web/src/routes/repos/\$owner.\$name.tsx` | 命令退出 0 |
| AC-2 | static | web 测试源里 "content/" 字符串 ≤ 0（仅当用户手工 fixture 才允许；本 change 范围内应 = 0） | `! grep -rE "content/\"" apps/web/src/routes/*.test.tsx 2>/dev/null` | 命令退出 0（或仅断言无） |
| AC-3 | behavioral | vitest run 全 PASS 不回归 | `cd apps/web && pnpm test -- --run` | 全 PASS |
| AC-4 | behavioral | pnpm typecheck 全 PASS | `pnpm --filter web typecheck` | 0 errors |
| AC-5 | static | self_check 含 run_web_ingest_path_default | `grep -q "run_web_ingest_path_default" scripts/_self_check.sh` | 命令退出 0 |
| AC-6 | static | AC-6 自递归（同 AC-5） | 同上 | 命令退出 0 |

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| 现有测试 fixture 用 `content/xxx` 形式断言 → vitest 红 | 中 | AC-3 fail | coding 时 grep "content/" 找到所有断言点，逐个改为不含前缀（或换 fixture 路径名） |
| 历史用户工作流"上传 → 自动归 content/"假设破坏 | 低 | 用户困惑 | spec 显式 deferred 文档变动到 follow-up；UI 不显示 "content/" 后用户行为更接近"自由路径" |
| upload after change：仓里同时有旧 content/xxx + 新 xxx → 路径冲突？ | 低 | 同名 entry 重复 | tree-nested-domain `_validate_tree_paths` 在新提交时会检测 blob-dir 冲突（如新 `content` 与旧 `content/xxx` 冲突）；commit 4xx 即可 |

## 跨链路一致性自审

1. ✅ summary 已写
2. ✅ 范围明确（单文件单行 change）
3. ✅ AC 可机械化
4. ✅ AC 分层：2 behavioral
5. ✅ 非豁免（动 apps/web + scripts/_self_check.sh）
6. ✅ AC-1 反向 grep 含 `! grep` 防回归（"content/${ 模式不存在"）
7. ✅ spec ↔ tasks ↔ self_check 一致
8. ✅ process_tasks 6 节点齐

## 受影响模块

- 改：`apps/web/src/routes/repos/$owner.$name.tsx`（line 583 默认 path）
- 改（如需）：`apps/web/src/routes/*.test.tsx` 中含 "content/" 字面的测试断言
- 改：`scripts/_self_check.sh`（加 run_web_ingest_path_default AC block）

## 不受影响

- 后端代码（adapter / service / router）
- 其他 web 路由 / 组件
- 历史 commit 数据

## 引用

- 现状：`apps/web/src/routes/repos/$owner.$name.tsx:583`（硬编码 `content/`）
- 上游 close：`tree-nested-domain-20260520`（merge commit b0ac18f）—— soft mode nested 化让此前缀的副作用更明显
- 上游 close：`web-tree-nested-ui-20260520`（merge commit 8b7a9ce）—— Files tab 现支持下钻，content/ 子目录会被显式渲染为 folder
