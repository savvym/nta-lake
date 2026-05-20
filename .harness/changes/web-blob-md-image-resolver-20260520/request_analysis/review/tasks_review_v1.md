---
change_id: web-blob-md-image-resolver-20260520
target: request_analysis/tasks.md
target_version: 1
review_version: 1
reviewer: claude-agent:web-blob-md-image-resolver-20260520-stage2-reviewer-v1
reviewed_at: 2026-05-20T14:00:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v1

## 检查清单结论

| 项 | 结论 | 备注 |
|---|---|---|
| 每个任务粒度合理（1-3 小时） | PARTIAL FAIL | T-4 过大（见 MUST FIX-1） |
| depends_on 形成 DAG，没有循环 | PASS | T-1→T-2→T-3→T-4→T-5→T-6→T-7 线性无环 |
| 评审 / 单测 / CI 阶段对应任务都存在 | PASS | P-* 节点完整，7 个 process_task 全覆盖 |
| 没有"做完整个系统"类目标性任务 | PARTIAL FAIL | T-4 三合一偏目标性 |
| 验收覆盖矩阵完整 | PASS | AC-1~9 全有对应任务 |

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | tasks.md T-4 | T-4 同时包含三件互相独立的事：(a) ReactMarkdown 替换 renderMinimalMarkdown；(b) CustomImage 组件（含 useSubtreeByPath hook 调用逻辑）；(c) resolveRelative 辅助函数。这三件事有各自的正确性风险点（ReactMarkdown 渲染替换 / hooks rules 合规 / 路径算法正确性），混在一个 task 里会导致 coding_report 无法逐条追踪哪个子功能通过、哪个失败；且 resolveRelative 算法的"拒 leading /"语义在 spec MUST FIX-4 里标记为待澄清——如果 T-4 是一个整体，算法争议会阻塞整个 task。粒度估计：ReactMarkdown 替换约 30 min，CustomImage 约 90-120 min，resolveRelative 约 30-60 min，总计可能超 3 小时 | 拆为 T-4a（ReactMarkdown 替换 + TextOrMarkdownBody 改造）、T-4b（resolveRelative 辅助函数 + 单元测试基础）、T-4c（CustomImage 组件含 useSubtreeByPath 集成）；T-4c depends_on T-4a, T-4b |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | tasks.md T-2 depends_on | T-2 的 `depends_on: [T-1]`（依赖 pnpm install 依赖）实际上不合理：validateSearch 字段修改与依赖安装完全独立，开发者可以先写 TS 再 install。这会人为序列化导致等待。更重要的问题：T-2 的描述说"用 zod schema 风"但未指定具体 zod 写法（`z.string().optional()` 还是裸 `commit?: string`），导致 coding agent 可能选 TanStack Router 的 `validateSearch` 手写对象解析方式而不一致 | 将 T-2 `depends_on` 改为 `[]`（或改为`[T-1]`但保留合理性注释）；在 T-2 description 里补充"与 web-tree-nested-ui 保持一致：用 z.string().optional() 而非 catch"；同步确认是沿用 zod schema 模式还是手写 validateSearch |
| SHOULD FIX-2 | tasks.md T-5 description | T-5 第 a 用例描述"mock useSubtreeByPath 返 images/a.jpg entry"——但 useSubtreeByPath 返回的是 `TreeRead`（含 `entries: TreeEntryRead[]`），不是直接的 entry。mock 应返回 `{ hash: "...", entries: [{ name: "a.jpg", mode: 33188, entry_type: "blob", target_hash: "<64hex>" }] }` 格式。description 过于简略可能导致 generator 写出错误 mock 结构，导致测试通过但实际逻辑未测到（因为组件内用 `.entries.find(e => e.name === basename)` 找 entry） | 在 T-5 description 补充 mock 返回值结构示例：`{ hash: "aaaa...a", entries: [{ name: "a.jpg", mode: 33188, entry_type: "blob", target_hash: "<64hex>" }] }` |
| SHOULD FIX-3 | tasks.md T-3 description | T-3 只说"commit（来自 commitQuery.data.hash）；两者都缺则不传"，但 `commitQuery.data.hash` 与 `commitHash`（来自 `refQuery.data.commit_hash`）有区别：commitQuery.data 是完整 CommitRead 含 hash 字段，而 commitHash（用于 query enabled）是 refQuery 返回的 commit_hash。两者理论应该相同，但 FilesSection 已有 `commitQuery` 和 `commitHash` 两个变量——description 应指明"commit 值用 `commitQuery.data.hash`（CommitRead.hash）还是 `commitHash`（refQuery.data.commit_hash）"，避免 coding agent 用错 | 在 T-3 description 明确："commit 字段值用 FilesSection 中的 `commitHash` 变量（即 `refQuery.data?.commit_hash ?? ""`），与现有 useSubtreeByPath 入参保持一致" |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-1 | tasks.md T-5 | T-5 第 d 用例 `md_nested_md_relative_path` 标注为可选，但 spec 风险表"nested 目录场景"是高概率风险（MinerU 输出 papers/2026/a.md 引用 papers/2026/images/*.jpg）。建议将此用例从"可选"改为"推荐必做" | 将 d 用例提升为 required，调整 AC-6 期望为 `numTotalTests ≥ 7`（含 baseline 3 + 新 4） |
| NICE-2 | tasks.md T-6 | T-6 仅说"在 run_web_ingest_path_default 后插入"，未指定 AC block 的具体结构（9 个 AC 的 grep 命令）。建议 T-6 description 里列出所有 9 条 AC 的 grep 命令，与 spec.md 的验证列保持引用一致，防止 coding agent 写出与 spec 不一致的 self_check 命令 | T-6 description 补充"AC 块验证命令与 spec.md 验收标准表完全一致；逐条复制" |

## Verdict

**REVISION REQUIRED**

1 条 MUST FIX 阻塞：T-4 粒度过大（三合一），且与 spec MUST FIX-4（leading / 行为待澄清）耦合，在 spec 未修前 T-4 边界不清晰。

建议 Generator 等 spec v2 MUST FIX 全关闭后，同步修 tasks v2：拆 T-4 → T-4a/T-4b/T-4c，修 T-5 mock 描述，修 T-2 depends_on 合理性注释。

## 复检指引

Generator 修完 tasks v2 后，自查以下：

1. **T-4 拆分**：任务列表中存在至少两个子任务覆盖 AC-4 + AC-5（ReactMarkdown 替换 / CustomImage 独立）
2. **DAG 无环**：`python3 -c "tasks=[...]; deps={t['id']:t['depends_on'] for t in tasks}; ..."`（手动验证拆分后无循环依赖）
3. **T-5 mock 结构**：description 中有 `TreeRead` 格式示例（`entries: [{ name, mode, entry_type, target_hash }]`）
4. **验收覆盖矩阵**：拆分后 T-4a/T-4b/T-4c 分别覆盖的 AC 在矩阵里正确更新（AC-4 → T-4a, AC-5 → T-4c）
5. **process_tasks 完整性**：7 个 P-* 节点仍然完整（本次 PASS，复检确认未删除）
