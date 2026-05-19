---
change_id: tree-nested-domain-20260520
target: tasks.md
target_version: 2
review_version: 2
reviewer: claude-agent:tree-nested-domain-20260520-stage2-reviewer-v2
reviewed_at: 2026-05-19T16:00:00Z
verdict: APPROVED
---

# Tasks Review v2

## §1 v1 MUST FIX 复检表

| # | v1 MUST FIX 摘要 | v2 修法 | 状态 | 证据 |
|---|---|---|---|---|
| MUST FIX-1 | T-2 合并 _validate_tree_paths + _normalize_to_nested 颗粒度违规（> 3h，逻辑独立） | 拆为 T-2a（`_validate_tree_paths`，covers AC-3，~1.5h）和 T-2b（`_normalize_to_nested`，covers AC-2/AC-4，~2h）；DAG 更新为 T-1→T-2a→T-2b→T-3；验收覆盖表同步 | **RESOLVED** | tasks.md T-2a（第 27–47 行）/ T-2b（第 49–69 行）；DAG（第 215 行）；验收覆盖表 AC-3→T-2a、AC-2→T-2b |
| MUST FIX-2 | T-3 未明确步骤 1 blob 存在性校验范围，含 entry_type=tree 时误用子 tree hash 调 BlobStore → 400 误拒 | T-3 description 开头增加"步骤 1（blob 存在性校验）：保持原位不动——在 _normalize_to_nested 之前对 payload.tree.entries（全扁平、全 type=blob、target_hash 全是 blob hash）调用 store.exists；不要把这个校验移到 normalize 之后" | **RESOLVED** | tasks.md T-3 description 第 75–79 行 |

---

## §2 v2 新增内容审查

### 检查清单结论

| 条目 | 状态 | 备注 |
|---|---|---|
| 每个任务粒度合理（1-3 小时） | PASS | T-2 已拆分；T-2a ~1.5h / T-2b ~2h；其余任务未变 |
| depends_on 形成 DAG，没有循环 | PASS | T-1→T-2a→T-2b→T-3→T-4→T-5→T-6→T-7 线性 DAG，无环 |
| 评审 / 单测 / CI 阶段对应任务都存在 | PASS | process_tasks 含 P-spec-review / P-code-review / P-test-review；T-5/T-6/T-7 对应单测和 CI |
| 没有"做完整个系统"类目标性任务 | PASS | 每个任务有具体产物和 AC 映射 |
| 验收覆盖表 14 AC 全覆盖 | PASS | AC-1 至 AC-14 均有对应任务；拆分后 AC-3→T-2a，AC-2/AC-4→T-2b，与范围描述一致 |
| spec ↔ tasks ↔ self_check 一致 | PASS | T-2a/T-2b 覆盖 spec AC-2/AC-3/AC-4；T-3 明确 step 1 不动 |

### v2 新增改动审查

**T-2a（第 27–47 行）**

描述详尽，列出 6 类校验逻辑（name==""、含 `//`、前导/末尾 `/`、segment `.`/`..`、空白 segment、entry_type=tree+mode 校验）及交叉校验（blob-dir 冲突、同层重名）；颗粒度 ~1.5h 合理。

注意：T-2a 对"同层重名"的处理描述为"normalize 后某中间 tree 的两个 entries 同 segment"，并注明"在 _normalize_to_nested 内做（在该函数里也有 detect）"——即同层重名放在 T-2b (_normalize) 内冗余 detect，T-2a 本身不做。这与 spec AC-3 §范围描述"同层重名（normalize 后某中间 tree 的两个 entries 同 segment）"列于 _validate_tree_paths 下存在轻微不一致：spec 把同层重名挂在 AC-3（_validate 函数），但 T-2a description 把主要实现放在 _normalize 内。此不一致为 SHOULD FIX（不阻塞，但影响 generator 实现位置选择）。

**T-2b（第 49–69 行）**

描述了 trie 构造、自底向上递归 hash、同层重名兜底 detect、all_trees 顺序保证及空 entries 边界。颗粒度 ~2h 合理。depends_on T-2a 正确。

**T-3 step 1 说明（第 75–79 行）**

"步骤 1（blob 存在性校验）：保持原位不动……payload.tree.entries（全扁平、全 type=blob）"——此说明正确，与 spec SHOULD FIX-3 对应修复一致。但需注意：若调用方直接 POST 包含 entry_type='tree' 的手工嵌套 entries（非 soft-mode 输入），步骤 1 的 `target_hash` 集合会包含子 tree hash，导致误拒。T-3 description 已隐含"正常路径 = soft mode 全是 blob"，此边界在 spec AC-3 mode 校验（_validate_tree_paths 先拒不合规情形）+ T-2a 描述中均有防护，整体可接受，不额外登记问题。

**验收覆盖表（第 218–235 行）**

AC-1→T-1、AC-2→T-2b、AC-3→T-2a、AC-4→T-2b+T-3、AC-5→T-3……全 14 AC 覆盖正确；拆分后无遗漏。

**process_tasks（第 189–211 行）**

未变，P-spec-review / P-code-review / P-test-review 均为 pending + 走完整 reviewer spawn，符合本 change 约定。

---

## §3 v2 Verdict + 新发现问题

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | tasks.md T-2a description（第 41 行）vs spec.md AC-3 | T-2a description 把"同层重名"的主要实现放在 _normalize_to_nested 内，T-2a 仅在交叉校验说明里提"normalize 后同层重名：在 _normalize_to_nested 内做"。但 spec AC-3 §范围把"同层重名"列于 `_validate_tree_paths` 的职责下。generator 可能按 T-2a 理解把同层重名只放在 T-2b 里，而 spec AC-3 的 self_check grep 命令只检查函数存在，不验证行为。两者实现位置不一致不影响正确性，但影响代码可读性和测试定位。 | 明确一个实现位置：建议 T-2a description 改为"_validate_tree_paths 内只做无需 trie 即可判断的校验（前 5 类）；同层重名留 _normalize_to_nested 内 detect（需构造 trie 后才能判断），在 T-2b 中明确"；并同步在 spec AC-3 注释"同层重名在 _normalize 内 detect" |
| SHOULD FIX-2 | tasks.md T-5 description 用例 6（第 145 行） | test_path_validation_rejects 用例 6 列了 5 个 case，但 spec v2 AC-3 新增了"末尾 `/`"和"空白 segment"两类边界，T-5 用例 6 未同步（v1 NTH-1 仍未关闭）。 | 在用例 6 case 列表补：`"a/"` 和 `" a"` 两个 case，覆盖 spec v2 新增规则 |
| SHOULD FIX-3 | tasks.md T-6 covers_ac（第 161–166 行） | T-6 `covers_ac: [AC-14, AC-12, AC-13]`，T-7 also covers `[AC-11, AC-12, AC-13]`。T-6 含义是"注册命令"，T-7 是"实际执行"；AC-12/AC-13 重复覆盖语义不清（v1 SHOULD FIX-1 未关闭）。 | T-6 covers_ac 改为仅 `[AC-14]`；T-6 description 尾部加注"T-6 仅注册命令，执行验证在 T-7" |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | tasks.md T-7（第 169–183 行）| T-7 引用 `processor-pdf-mineru-20260519` 和 `processor-pdf-mineru-assets-20260520` 两个 change，summary.md related_changes 可能只列其一（v1 NTH-3 未关闭）。 | 核实上游 change id；若只有一个则删多余 |
| NTH-2 | tasks.md T-4 | T-4 description 未说明空 root tree（entries=[]）时 GET 默认模式的预期响应（v1 SHOULD FIX-3 降级为 NTH）。 | T-4 description 末尾加"边界：空 root tree → 返 TreeRead(hash=..., entries=[])" |

---

## Verdict

**APPROVED**

tasks.md v2 两条 MUST FIX 均已关闭：T-2 正确拆为 T-2a/T-2b；T-3 step 1 blob 校验范围已明确。新增 3 条 SHOULD FIX（均非阻塞）和 2 条 NICE TO HAVE。无新 MUST FIX。

tasks.md v2 可进入下一阶段（spec MUST FIX 关闭后协同推进）。

---

## 后续指引（Generator 修 v3 后自查）

```bash
# 1. 确认 T-2a / T-2b 拆分与覆盖表一致（已在 v2 中验证，v3 不改动时跳过）
grep -E "id: T-2[ab]|covers_ac" \
  .harness/changes/tree-nested-domain-20260520/request_analysis/tasks.md

# 2. 确认 T-6 covers_ac 已移除 AC-12 / AC-13（若采纳 SHOULD FIX-3）
grep -A3 "id: T-6" \
  .harness/changes/tree-nested-domain-20260520/request_analysis/tasks.md

# 3. 确认 T-5 用例 6 含末尾 / 和空白 segment（若采纳 SHOULD FIX-2）
grep -A20 "test_path_validation_rejects" \
  .harness/changes/tree-nested-domain-20260520/request_analysis/tasks.md
```
