---
change_id: web-ingest-path-default-20260520
version: 2
authored_at: 2026-05-20T10:40:00Z
revised_at: 2026-05-20T11:10:00Z
status: draft
revision_notes: |
  v2 修 stage 2 reviewer v1 报的 3 条 spec MUST FIX：
  - MUST-1（AC-3 空转）：现有测试无 IngestSection.onFiles 默认 path 行为覆盖；6
    处 "content/" 全是 FilesSection/Commits 显示 fixture（legacy commit 形态），
    与 ingest 行为无关。新增 AC-3a：必须加一个新 IngestSection 单测断言默认 path
    不含 content/ 前缀；原 AC-3 改 ID 为 AC-3b（全 vitest 不回归）。
  - MUST-2（AC-2 grep 过窄 + prose 矛盾）：删 AC-2（IngestSection 单测断言比
    grep 字面更精确）；保留 6 处 display fixture 合理性显式说明。
  - MUST-3（AC-5 == AC-6）：删 AC-6（自递归并入 AC-5）。

  AC 数从 6 → 5（AC-1 / AC-3a / AC-3b / AC-4 / AC-5）。
  
  另修 SHOULD：风险表 "blob-dir 冲突" 描述精化（同 commit 同批 upload 才可能；
  跨 commit 由 tree-nested-domain 已隔离）。
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
- AC-3a: 新增 IngestSection 单测，断言 onFiles 默认 path = filename（不含 content/ 前缀）；现有 6 处 "content/" 字面在 *.test.tsx 中作为 **legacy commit 显示 fixture** 保留不动（FilesSection / Commits page 测试），它们模拟历史扁平 commit 形态
- AC-3b: vitest 全测试不回归
- AC-4: pnpm typecheck 全 PASS
- AC-5: scripts/_self_check.sh 加 `run_web_ingest_path_default` AC block（兼自递归）

## 非范围

- 不动 adapter / 后端代码（raw-file-upload 不感知 path 前缀）
- 不引入 "upload into folder" UI 控件（用户可以编辑 path 字段；高级 UX 留 follow-up `web-ingest-folder-picker-*`）
- 不重写历史 commit
- 不动其他 default path（如未来其他 adapter 的输入）

## 验收标准（5 AC，**2 behavioral**：AC-3b / AC-4；AC-3a 也 behavioral 一并算 3 条）

| ID | kind | 描述 | 验证 | 期望 |
|---|---|---|---|---|
| AC-1 | static | onFiles 默认 path 是 f.name（无 content/ 前缀） | `grep -qE "path:\s*f\.name" apps/web/src/routes/repos/\$owner.\$name.tsx && ! grep -qE 'path:[[:space:]]*\`content/' apps/web/src/routes/repos/\$owner.\$name.tsx` | 命令退出 0 |
| AC-3a | behavioral | 新单测断言 onFiles 默认 path = filename（一个用例必须含 "without content/" 含义；JSON reporter 计数 ≥ 1 ingest 测试 PASS） | `cd apps/web && pnpm test -- --run --reporter json src/routes/repos.ingest-section.test.tsx > /tmp/ingest.raw 2>&1 && grep -E '^{' /tmp/ingest.raw > /tmp/ingest.json && python3 -c "import json; d=json.load(open('/tmp/ingest.json')); assert d['numFailedTests']==0 and d['numTotalTests']>=1, d"` | numTotalTests ≥ 1，0 fail |
| AC-3b | behavioral | vitest run 全 PASS 不回归 | `cd apps/web && pnpm test -- --run` | 全 PASS |
| AC-4 | behavioral | pnpm typecheck 全 PASS | `pnpm --filter web typecheck` | 0 errors |
| AC-5 | static | self_check 含 run_web_ingest_path_default（兼自递归） | `grep -q "run_web_ingest_path_default" scripts/_self_check.sh` | 命令退出 0 |

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| 现有测试 fixture 用 `content/xxx` 形式断言 → vitest 红 | 中 | AC-3 fail | coding 时 grep "content/" 找到所有断言点，逐个改为不含前缀（或换 fixture 路径名） |
| 历史用户工作流"上传 → 自动归 content/"假设破坏 | 低 | 用户困惑 | spec 显式 deferred 文档变动到 follow-up；UI 不显示 "content/" 后用户行为更接近"自由路径" |
| upload after change：仓里同时有旧 content/xxx + 新 xxx → 路径冲突？ | 低 | 同名 entry 重复 | 仅当**同一次提交**的 entries 包含 `content`（blob）与 `content/xxx`（隐含子目录）才会被 `_validate_tree_paths` 拒 400。跨 commit 不冲突——每个 commit 是独立 tree。本 change 改默认前缀不影响该校验语义 |
| 新单测放新文件 vs 写进 repos.tabs.test.tsx | 低 | 测试组织混乱 | spec 选放新文件 `repos.ingest-section.test.tsx`（与 files-section / tabs 并列；命名一致） |

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
