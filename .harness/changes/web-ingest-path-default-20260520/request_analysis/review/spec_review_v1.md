---
change_id: web-ingest-path-default-20260520
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-agent:web-ingest-path-default-20260520-stage2-reviewer-v1
reviewed_at: 2026-05-20T11:30:00Z
verdict: REVISION REQUIRED
---

# Spec Review v1

## 检查清单结论（plan 模式）

| 条目 | 状态 | 备注 |
|---|---|---|
| 背景写明了为什么现在做 | PASS | 明确描述 tree-nested-domain 合并后的副作用 |
| 问题陈述与目标可被外部读者理解 | PASS | 清晰 |
| 范围 / 非范围都有 | PASS | in scope / out of scope 俱全 |
| 验收标准每条都可演示且可机械化 | PARTIAL | AC-1、AC-5 机械化正确；AC-2 grep 语义与 prose 不符；AC-6 与 AC-5 完全重复；AC-3 行为覆盖缺口（见问题列表） |
| 风险有缓解措施或显式 accept | PARTIAL | blob-dir 冲突风险描述语义不准确（见 SHOULD FIX）|
| 没有把已有架构当新提案重复 | PASS | |
| AC 表存在 `kind` 列 | PASS | ✓ |
| 至少 1 行 AC kind=behavioral（锚定 regex） | PASS | AC-3 / AC-4 = behavioral；用 awk+grep 锚定确认 |

---

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST-1 | spec.md AC-3（验收标准表） | AC-3（behavioral）仅要求 "vitest 不回归"，但当前没有任何测试覆盖 `IngestSection.onFiles` 默认 path 行为。`repos.tabs.test.tsx` 中无 ingest path 相关断言；`repos.files-section.test.tsx` 中 `content/` 仅出现为 Files Section 显示 fixture，与 IngestSection 无关。一次 1 行 code change 的 behavioral AC 应当至少有 1 条测试 **直接断言改后的行为**，否则 AC-3 vacuously PASS，回归保护失效。 | 在 AC 表（或非范围说明）中明确：T-2/coding 阶段须新增一条 vitest 用例，模拟 `onFiles` 调用并断言 `path === f.name`（不含 `content/` 前缀）。若不加测试，需在 spec 显式写明 "IngestSection 暂无 unit test，behavioral 只靠手工 e2e"，并把 AC-3 的期望从 "PASS" 改为 "全 PASS（含已有用例；新行为无 vitest 覆盖，风险 deferred）"。 |
| MUST-2 | spec.md AC-2（验收标准 + 范围说明） | AC-2 验证命令 `! grep -rE "content/\""` 仅能匹配 `content/"` 这种路径**以引号立即结束**的形式。实测：`repos.files-section.test.tsx:118`（`name: "content/a.md"`）和 `commits.$owner.$name.$hash.test.tsx:33`（同形）**均不被命中**——该 grep 已经漏过所有 `"content/<filename>"` 形态。若将来有 ingest 相关测试断言为 `expect(path).toBe("content/a.pdf")`，AC-2 grep 同样无法抓住。此外，spec prose 说"content/ 应仅出现 0 次"，但已存在 6 处合理的显示 fixture（files-section + commits 测试中的 legacy flat commit fixture）——两者矛盾会误导 coder 不当删除这些 fixture。 | 修正 AC-2 验证命令，改为能同时命中 `"content/xxx"` 和 `"content/"` 的更宽 pattern，例如 `! grep -rE 'path:\s*["`]content/' apps/web/src/routes/*.test.tsx`（仅扫 path 赋值行，不影响 display fixture）；或 scope 缩窄为只扫 ingest-related 测试文件。同时修正 prose："ingest 路径断言不得含 content/ 前缀"（而非"test 文件整体 ≤ 0 次"）。 |
| MUST-3 | spec.md AC-5 与 AC-6（验收标准表） | AC-5 和 AC-6 的验证命令完全相同（均为 `grep -q "run_web_ingest_path_default" scripts/_self_check.sh`）。AC-6 描述为"self_check 含 run_web_ingest_path_default"，与 AC-5 无差异。若 AC-6 意图是"AC block 内部自引用"（即 self_check script 中的 run_web_ingest_path_default 函数本身包含对这两个 AC 的检测），则验证命令应检查的是 **self_check.sh 里的 AC block 内容**，而非仅仅函数名存在与否。重复 AC 浪费 self_check 执行资源，且 MUST FIX 数计数失真。 | 合并 AC-5 和 AC-6，或给 AC-6 赋予真正不同的验证：例如 `grep -qE "run_web_ingest_path_default\b.*AC-6" scripts/_self_check.sh`（验证 self_check 的 AC block 确实覆盖了 AC-6 这行），区分于 AC-5 的"函数名存在"检测。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD-1 | spec.md 风险表（第 3 行） | "upload after change：仓里同时有旧 content/xxx + 新 xxx → 路径冲突？" 描述语义不准确。实际分析：每次 raw-file-upload ingest 产生独立新 commit，仅包含本次上传的文件；不存在跨 commit 继承路径的机制。"新 content 与旧 content/xxx 冲突"只有在**同一次上传**中用户既上传名为 `content`（裸文件名）又上传 `content/xxx`（以 content/ 开头）时才会触发 blob-dir 冲突。这与改动本身关系不大——是通用上传校验，不是本 change 引入的风险。目前缓解描述"commit 4xx 即可"在这个语境下不准确（跨 commit 不会冲突，同 commit 裸 content + content/xxx 才会）。 | 重写风险描述：区分"跨 commit 无冲突（每次上传独立 snapshot）"和"同一批次上传名为 content 的文件时触发 blob-dir 冲突"。缓解可明确为"同批次路径冲突由 `_validate_tree_paths` 检测，返回 400，用户侧可见错误提示"。若认为风险概率极低可显式 accept。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | spec.md 范围（In scope 第 2 点） | "AC-2: 测试断言（如有）调整" 括号 "如有" 容易被误解为"如果存在需改的断言才做"。实际上即使无断言需调整，T-2 也应跑 grep 并确认（甚至新增测试）。 | 改为"梳理测试中涉及默认 path 的断言，确保无遗留 content/ 前缀断言；若无则在 tasks T-2 记录 'grep 结果 = 0'。" |
| NTH-2 | spec.md 跨链路自审第 6 条 | "AC-1 反向 grep 含 `! grep` 防回归（'content/${ 模式不存在'）" 已自审通过，但 AC-2 反向 grep 的问题未在自审中被识别，说明自审 checklist 对"grep 语义宽窄"覆盖不足。 | 在 request-analysis SKILL 的自审 checklist 中补充一条"grep 语义宽窄自检：确认 pattern 能命中所有目标形态"（反馈至 `.harness/skills/request-analysis/SKILL.md`，本 change 范围外）。 |

---

## Verdict

**REVISION REQUIRED**

存在 3 条 MUST FIX：
1. **MUST-1**：AC-3 无行为级测试覆盖——behavioral AC 空转，回归保护形同虚设。
2. **MUST-2**：AC-2 grep 语义过窄（漏匹配 `"content/xxx"` 形态）+ prose 与现有合理 fixture 矛盾，会误导 coder。
3. **MUST-3**：AC-5 与 AC-6 验证命令完全相同，AC-6 形同重复，需赋予独立语义或合并。

1 条 SHOULD FIX（风险表第 3 行语义不准确，但不阻塞实现正确性）。

---

## 复检指引（Generator 修完后自查）

1. **MUST-1**：确认 spec AC-3 表格描述更新，并在 tasks.md T-2 中明确写出"新增 IngestSection onFiles 单测断言"或在 spec 显式记录 deferred。
2. **MUST-2**：用以下命令验证新 AC-2 grep 能正确命中 ingest path 断言（如有）而不误伤 display fixture：
   ```bash
   # 应返回空（无 ingest path 相关 content/ 断言）
   grep -rE 'path:\s*["`]content/' apps/web/src/routes/*.test.tsx
   # 应仍存在（合法 display fixture 不受影响）
   grep -rn '"content/' apps/web/src/routes/repos.files-section.test.tsx
   ```
3. **MUST-3**：确认 AC-5 与 AC-6 的 verification 命令不再相同，或已合并为 1 条。运行：
   ```bash
   grep -A5 "AC-5\|AC-6" .harness/changes/web-ingest-path-default-20260520/request_analysis/spec.md
   ```
   确认两行内容不同。
4. **SHOULD-1**：风险表第 3 行已重写，可用 diff 确认。
