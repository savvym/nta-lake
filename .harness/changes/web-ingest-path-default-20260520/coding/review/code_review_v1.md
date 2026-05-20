---
change_id: web-ingest-path-default-20260520
target: coding_report_v1.md + apps/web/src/routes/repos/$owner.$name.tsx
target_version: 1
review_version: 1
reviewer: claude-agent:web-ingest-path-default-20260520-stage4and6-reviewer-v1
reviewed_at: 2026-05-20T12:00:00Z
verdict: APPROVED
---

# Code Review v1

## 检查清单结论

### 1. 范围审查

- coding_report 声明 3 个改动文件：`$owner.$name.tsx`（T-1）、`repos.ingest-section.test.tsx`（T-2a）、`scripts/_self_check.sh`（T-3）。
- 逐一核查：T-1 line 583 确为 `path: f.name`，无 scope creep；T-2a 为新测试文件，符合 spec §风险 "放新文件" 决策；T-3 加 `run_web_ingest_path_default` 5 AC block，与 AC-5 对齐。
- 无 scope creep，无跨目录越界，符合 `engineering-structure.md`。

### 2. 正确性审查

**T-1（核心改动）**

- `apps/web/src/routes/repos/$owner.$name.tsx` line 583：`path: f.name`。
- 核查：`onFiles` 函数（lines 579-588）中唯一的 path 赋值点，改动精确，无其他路径被动改写。
- `updatePath`（lines 590-594）未改，用户手工编辑路径的逻辑完整保留。
- `remove`（lines 596-598）未改。
- submit 逻辑中 `paths = files.map(f => f.path)`（line 610）——使用 `f.path`，与改动一致，无副作用。
- 反向验证：`grep -qE 'path:[[:space:]]+\`content/'` 在当前文件中无匹配，旧前缀已消除。
- 其余 onFiles / drag-drop 路径：查询 `onDrop` / `drag`——本组件无 drop handler，文件输入唯一入口为 `<Input id="ingest-files" onChange={(e) => onFiles(e.target.files)}`（line 689），与测试触发点一致。

**T-3（self_check AC block）**

- 5 个 AC 命令与 spec v2 AC 表对齐，详见下方逐条核对（"self_check AC 对齐"节）。

### 3. 架构审查

- 本次改动未引入新依赖、未跨越分层、未新建顶层目录，合规。

### 4. 风格审查

- `path: f.name` 是简单字段赋值，命名、类型与现有 `UploadedFile` 类型兼容。
- 无新增注释需求（改动语义自明）。

### 5. self_check AC 逐条对齐

| AC | spec v2 命令摘要 | self_check line 1295-1308 | 对齐 |
|---|---|---|---|
| AC-1 | `grep -qE "path:\s*f\.name" ... && ! grep -qE 'path:`content/'` | line 1296：`grep -qE "path:[[:space:]]+f\.name" ... && ! grep -qE "path:[[:space:]]+\`content/"` | ✅ 语义等价；`\s*` vs `[[:space:]]+` 细微差异（见 SHOULD FIX-1）|
| AC-3a | JSON reporter + `grep -E "^{" + python assert` | line 1299：完全对齐 | ✅ |
| AC-3b | `pnpm test -- --run` | line 1302 | ✅ |
| AC-4 | `pnpm --filter web typecheck` | line 1305 | ✅ |
| AC-5 | `grep -q "run_web_ingest_path_default" scripts/_self_check.sh` | line 1307-1308 | ✅ |

### 6. 副作用检查

- display fixture 保留（T-2b）：6 处 `content/` 字面量在 `repos.files-section.test.tsx` 与 `commits.$owner.$name.$hash.test.tsx` 中均为历史 commit 数据结构，与 IngestSection 的 `onFiles` 无关。这符合 spec v2 revision_notes 的明确说明。
- `repos.ingest-section.test.tsx` 中的 `queryByDisplayValue("content/a.pdf")` 反向断言（line 98）确认旧前缀不再出现在 Input value 中，有效。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD-1 | `scripts/_self_check.sh` line 1296，AC-1 grep pattern | spec v2 AC-1 用 `\s*`（匹配 0 个或多个空白），self_check 用 `[[:space:]]+`（至少 1 个空白）。若代码格式化后变成 `path:f.name`（无空格），`[[:space:]]+` 不匹配，AC-1 会误 FAIL。虽然当前代码有空格，两者等价，但语义不严格一致。 | 将 AC-1 grep 中 `[[:space:]]+` 改为 `[[:space:]]*`，与 spec v2 原始表述对齐，消除格式化导致误判的可能性。 |

### NICE TO HAVE

| # | 位置 | 建议 |
|---|---|---|
| NTH-1 | `repos.ingest-section.test.tsx` | 第 2 个用例 `findByLabelText` 用的是 `await`，第 1 个用例后也用了 `waitFor`。两个用例均未调用 `cleanup()`；由于 vitest 默认每 `it` 自动清理，不影响正确性，但如未来改 setup 方式，若同一 describe 内两个用例共享同一路由实例可能有状态残留风险。目前无问题，可在后续测试扩展时留意。 |

## Verdict

**APPROVED**

MUST FIX = 0。SHOULD FIX-1 为 AC-1 grep 正则的极端边界情况（当前代码格式固定，不影响 CI 通过），不阻塞。核心改动（line 583 `path: f.name`）精确、无副作用，self_check 5 AC 与 spec v2 对齐，display fixture 6 处合理保留。

## 复检指引

若 generator 修 SHOULD-1：
```bash
grep -n "path:\[:\[" scripts/_self_check.sh
# 确认 AC-1 正则变为 [[:space:]]* 而非 [[:space:]]+
bash scripts/_self_check.sh current web-ingest-path-default-20260520
# 期望: 5/5 PASS
```

后续指引：进入 stage 6 test review（合并评审，见 test_review_v1.md）。
