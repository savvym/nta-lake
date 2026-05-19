---
change_id: tree-nested-domain-20260520
target: spec.md
target_version: 2
review_version: 2
reviewer: claude-agent:tree-nested-domain-20260520-stage2-reviewer-v2
reviewed_at: 2026-05-19T16:00:00Z
verdict: REVISION REQUIRED
---

# Spec Review v2

## §1 v1 MUST FIX 复检表

| # | v1 MUST FIX 摘要 | v2 修法 | 状态 | 证据 |
|---|---|---|---|---|
| MUST FIX-1 | AC-5 grep 假阳性：任意含 `all_trees` 字符串的注释 / 变量声明即通过 | 改为 `inspect.getsource(CommitService.create_commit)` + `'_normalize_to_nested' in src` + `src.count('TreeORM(') >= 1`，不再依赖 grep | **RESOLVED（部分残留，降为 SHOULD FIX，见 §3）** | spec.md AC-5 验证命令（第 102 行）已替换为 dry-import + source 检查 |
| MUST FIX-2 | AC-3 遗漏末尾 `/`、空白 segment（`" a"` / `"a/ /b"` 等） | AC-3 §范围补全：加"以 `/` 结尾（含 `'a/'`）"与"任一 segment 经 `strip()` 后为空（覆盖 `' a'`、`'a/ /b'`、`'a/  '`）" | **RESOLVED** | spec.md 第 61–63 行显式列出两项；`_validate_tree_paths` 描述及测试用例均对应补全 |
| MUST FIX-3 | AC-6 描述"算法不变"语义误导（输入空间扩大后哈希值空间变化） | §范围 AC-6 文本改为"代码实现不改"并追加"但输入空间扩大……导致 root hash 与扁平模式完全不同" | **PARTIAL（表行描述未同步，降为 MUST FIX，见 §3 MUST FIX-1）** | §范围 AC-6（第 69 行）已修正；但 AC 验收表第 103 行"描述"列仍为"算法不变（grep 函数签名锚定）"——两处措辞不一致，表行是 self_check 脚本 / generator 最优先参考的机器可读来源 |
| MUST FIX-4 | AC-3 未定义 `entry_type="tree"` + `mode != 16384` 的行为（脏 mode 静默写入） | AC-3 §范围末尾追加：`entry_type=="tree"` 时 `mode != 0o040000 (16384)` → ValueError | **RESOLVED** | spec.md 第 66 行；风险表"中间 tree 的 mode 字段约定不一致"缓解已同步（第 129 行） |

---

## §2 v2 新增内容审查

### 检查清单结论

| 条目 | 状态 | 备注 |
|---|---|---|
| 背景写明了为什么现在做 | PASS | 未改动，同 v1 |
| 问题陈述与目标可被外部读者理解 | PASS | 未改动 |
| 范围 / 非范围都有 | PASS | 未改动 |
| 验收标准每条都可演示且可机械化 | PARTIAL | AC-5 残留弱点；AC-6 表行描述未同步（见 §3） |
| 风险有缓解措施或显式 accept | PASS | mode 风险缓解已更新 |
| 没有把已有架构当新提案重复 | PASS | 未改动 |
| AC kind 列存在 | PASS | 表头第 94 行有 `kind` 列 |
| 至少 1 行 kind=behavioral | PASS | AC-9 / AC-10 / AC-11 / AC-13 共 4 条 behavioral |
| spec frontmatter ac_kind_lint: exempt | N/A | 未声明 exempt |

### v2 新增改动审查

**AC-3 修补**（第 61–66 行）

v2 在 §范围 AC-3 中逐条补全了路径校验规则，包括：末尾 `/`、前导 `/`、空白 segment、`entry_type="tree"` + mode 校验。措辞清晰，覆盖合理。

但注意：AC-3 的**验收表行验证命令**仅为 `grep -q "_validate_tree_paths" apps/api/dataplat_api/services/commit.py`（第 100 行）——这只验证函数存在，不验证具体校验规则是否实现。对于一个包含 7 类边界校验的函数，仅 grep 函数名偏弱。此问题已在 v1 SHOULD FIX 中被提及（间接），此处作为 SHOULD FIX 登记（见 §3）。

**AC-5 修补**（第 102 行）

改为 dry-import + `inspect.getsource` 检查，避免了 v1 指出的 grep 跨文件误命中。但当前断言 `src.count('TreeORM(') >= 1` 只验证 `create_commit` 内至少一次 `TreeORM(` 实例化，无法区分"单 tree upsert（旧路径）"和"多 tree 循环 upsert（新路径）"。若 generator 保留旧单 tree 写入但未改为循环 upsert，AC-5 仍通过。此问题降为 SHOULD FIX（相比 v1 MUST FIX-1 已实质改善）。

**AC-6 §范围文本修补**（第 69 行）

§范围的 AC-6 描述已正确修改为"代码实现不改"并补充输入空间扩大的说明。**但验收表 AC-6 行的"描述"列（第 103 行）仍为"_canonical_tree_bytes / _tree_hash 算法不变（grep 函数签名锚定）"**，与 §范围描述不一致。Generator 和 self_check 在实现时首先参考 AC 表，旧措辞残留会重新引入 v1 指出的语义误导问题。这是 v2 引入的**表内 / 范围描述不一致回归**，登记为 MUST FIX。

**AC-14 描述**（第 111 行）

v2 未修改 AC-14 表行描述，仍为"AC-14 自递归 + self_check 含 `run_tree_nested_domain` block"。"AC-14 自递归"措辞无意义（v1 SHOULD FIX-2）。v2 修订说明未提及此项。登记为 SHOULD FIX（同 v1，尚未关闭）。

**风险表**（第 124–134 行）

v2 风险表内容与 v1 相同，仅第 129 行措辞新增"写入 service 强制"对应 MUST FIX-4。其余风险条目无回归。

**frontmatter revision_notes**

v2 frontmatter 的 `revision_notes` 准确列出 4 条 MUST FIX 对应修改。但 MUST FIX-3 注明"改为'算法实现代码不改，entry_type 可为 tree 故 hash 输入空间扩大'"——实际上只改了 §范围文本，AC 表行描述未同步，与 notes 声称不符。

---

## §3 v2 Verdict + 新发现 MUST FIX

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | spec.md 验收表 AC-6 描述列（第 103 行） | v2 只修了 §范围 AC-6 文本，**验收表 AC-6 行"描述"列仍为"_canonical_tree_bytes / _tree_hash 算法不变"**，与已修正的 §范围描述形成内部不一致。表行描述是 generator 编码和 self_check 脚本优先参考来源，旧措辞会重新误导后续读者认为 hash 输出空间未变。这是 v1 MUST FIX-3 的**不完整修复残留**。 | 将 AC-6 表行"描述"列改为："`_canonical_tree_bytes` / `_tree_hash` 代码实现不改（函数签名 unchanged）；entry_type 现可为 'tree'，hash 输入空间扩大"；与 §范围 AC-6 描述保持一致 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | spec.md 验收表 AC-5 验证命令（第 102 行） | `src.count('TreeORM(') >= 1` 断言只要求 `create_commit` 内至少存在一次 `TreeORM(` 调用，旧单 tree 写入路径也能满足。无法验证循环 upsert 的实现。若 generator 写出只处理 root tree 的代码（1 次 TreeORM 实例化），AC-5 仍通过而实质未完成。 | 改断言为 `src.count('TreeORM(') >= 2` 或添加对 `all_trees` / 循环语句的检查：`assert 'all_trees' in src`（`_normalize_to_nested` 返回值变量名）；或将 AC-5 改为 behavioral（AC-11 的 test_dedup_same_subtree_across_commits 可作为验证手段） |
| SHOULD FIX-2 | spec.md 验收表 AC-3 验证命令（第 100 行） | AC-3 §范围定义了 7 类路径校验规则，但验证命令仅 `grep -q "_validate_tree_paths"`，只确认函数存在，不验证任何一类规则被实现。若 generator 写出空函数或遗漏某类校验，AC-3 仍通过自检。（此问题在 v1 中未单独报出，v2 补全 7 类规则后差距更显著。） | 将 AC-3 验证命令改为 dry-import 运行时检查，类似 AC-4：`uv run python -c "from dataplat_api.services.commit import _validate_tree_paths; from dataplat_api.schemas.tree import TreeEntryCreate as T; ..."`；至少测试 `name=''` 和 `name='a/'` 两个边界 raise ValueError |
| SHOULD FIX-3 | spec.md 验收表 AC-14 描述列（第 111 行） | "AC-14 自递归"措辞无意义（v1 SHOULD FIX-2 未关闭）。 | 改为"scripts/_self_check.sh 已注册 run_tree_nested_domain block（含本 change 14 条 AC 的 grep/pytest 命令）；self_check current 可独立运行" |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | spec.md §验收标准 AC-11 (f) | 路径校验测试用例 (f) 列了"路径校验拒 `""` / `..` / 冲突"，但 v2 新增的"末尾 `/`"和"空白 segment"未出现在 (f) 描述。test_path_validation_rejects 用例说明也未同步更新（v1 NTH-2 提及）。 | AC-11 (f) 描述补"trailing `/`、空白 segment" case；tasks.md T-5 用例 6 同步 |
| NTH-2 | spec.md §风险 第 127 行 | "旧扁平 commit + 新嵌套 commit 混合读时 GET ?recursive=1 输出形式不一致"风险缓解里写"reviewer 复核"——reviewer 无法在 spec review 阶段复核运行时行为，这个"reviewer 复核"实际上无操作意义。 | 删除或改为"AC-9 behavioral test 覆盖" |

---

## Verdict

**REVISION REQUIRED**

未关闭 MUST FIX：1 条。

- **MUST FIX-1**：AC-6 验收表行描述列仍为"算法不变"，与 §范围已修正文本不一致；v1 MUST FIX-3 的修复不完整。

v1 的其余 3 条 MUST FIX（MUST FIX-1 / MUST FIX-2 / MUST FIX-4）均已关闭；tasks v1 的 2 条 MUST FIX 均已关闭（见 tasks_review_v2）。

---

## 后续指引（Generator 修 v3 后自查）

```bash
# 1. 确认 AC-6 表行"描述"列已改为"代码实现不改"
grep "AC-6" .harness/changes/tree-nested-domain-20260520/request_analysis/spec.md | \
  grep -v "算法不变"

# 2. 确认表行描述与 §范围 AC-6 文本语义一致
awk '/^## 验收标准/,/^## 非范围/' \
  .harness/changes/tree-nested-domain-20260520/request_analysis/spec.md | \
  grep "AC-6"
```

v3 review 将以上输出作为 MUST FIX-1 复检证据。
