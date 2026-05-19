---
change_id: tree-nested-domain-20260520
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-agent:tree-nested-domain-20260520-stage2-reviewer-v1
reviewed_at: 2026-05-19T15:00:00Z
verdict: REVISION REQUIRED
---

# Spec Review v1

## 检查清单结论

| 条目 | 状态 | 备注 |
|---|---|---|
| 背景写明了为什么现在做 | PASS | 扁平模型痛点 + pdf-mineru 实测 83 行扁平明确 |
| 问题陈述与目标可被外部读者理解 | PASS | 问题陈述清晰，soft mode 语义明确 |
| 范围 / 非范围都有 | PASS | In scope / 非范围均明确 |
| 验收标准每条都可演示且可机械化 | PARTIAL（详见 MUST FIX-1、SHOULD FIX-1） | AC-5 grep 过宽；AC-6 措辞误导 |
| 风险有缓解措施或显式 accept | PASS | 9 条风险全有缓解或 accept |
| 没有把已有架构当新提案重复 | PASS | 明引 domain/tree.py 已支持，正确定位为"把路通起来" |
| AC kind 列存在 | PASS | 第 80 行有 `kind` 列定义 |
| 至少 1 行 kind=behavioral | PASS | AC-9/10/11/13 均为 behavioral，4 条 |
| spec frontmatter ac_kind_lint: exempt | N/A | 未声明 exempt；不需查 git diff |

---

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | spec.md AC-5 验证命令 | grep 表达式 `grep -qE "all_trees\|for[[:space:]]+\(?[a-z_]+,[[:space:]]+entries_at_level\|for[[:space:]]+sub_tree"` 存在严重假阳性风险：任何含字面量字符串 `"all_trees"` 的注释 / 变量声明 / 测试文件都能命中。在步骤 4 改造完成前，若 generator 在 service 文件里写了 `# old: all_trees` 注释，AC-5 即通过但实际循环未实现。AC-5 声明目的是"create_commit 步骤 4 含 all_trees / 多 TreeORM upsert"，但 grep 对代码位置没有任何限制（扫整个文件）。 | 加 `-n` 配合 context 过滤，或改为 `grep -qE "for .+, entries_at_level in all_trees"` 并加文件路径 `apps/api/dataplat_api/services/commit.py`（已有）；或把 AC-5 拆成两条：一条检查函数名存在，一条用 dry-import 跑 `_normalize_to_nested` 并断言返回值包含多个 tree（类 AC-4 写法），以 behavioral 替换 static grep |
| MUST FIX-2 | spec.md AC-3 + 风险表第 1 行 | 路径校验列出了 `""` / `/` 起头 / `//` / `.` / `..` / blob-dir 冲突，但**遗漏了以下边界**：(a) 末尾 `/`（`"a/"` — 以斜杠结尾）：spec AC-3 仅列"以 `/` 起头"，没有明确"以 `/` 结尾"；(b) 空 segment（`"a//b"` 虽列，但 `"/a"` 与 `"a/"` 语义不同，需明说）；(c) segment 含前导/末尾空格（`" a"` / `"a "`）。这些边界不进 spec 就不进 _validate_tree_paths，也不会进 AC 测试用例（test_path_validation_rejects 只列了 5 条）。 | 在 AC-3 的"拒 xxx"列表里**显式补充**：拒 name 以 `/` 结尾；拒 segment 为纯空白（strip 后为空）；风险表缓解条对应追加。不要求 unicode 归一化（可留 NICE TO HAVE），但 ASCII 空白 segment 必须拒 |
| MUST FIX-3 | spec.md AC-6 措辞 | AC-6 描述为"`_canonical_tree_bytes` / `_tree_hash` **算法不变**"，但用 grep 函数签名锚定做验证。"算法不变"的自然理解是**输出行为不变**，而本 change 之后算法的**输入空间扩大**（`entry_type` 可为 `"tree"`），输出哈希值空间自然也改变。措辞在语义层是**假陈述**（新 tree entry 传入会产生与旧逻辑不同的哈希），会误导后续 reviewer 认为"hash 空间兼容"。AC-6 本意是"代码实现（函数签名/内容）不改"，应明确这点。 | 将 AC-6 描述改为"`_canonical_tree_bytes` / `_tree_hash` 实现代码不改（函数签名与内部逻辑 unchanged）；但 `entry_type` 现可为 `'tree'`，故 hash 输入空间扩大，跨 commit 含相同 entry_type='tree' 的子 tree 才可 dedup"；验证方式 grep 签名锚定保持即可 |
| MUST FIX-4 | spec.md AC-5 + AC-3（_validate_tree_paths 语义） | spec 未定义 `entry_type="tree"` + `mode != 16384` 的处理语义。`_canonical_tree_bytes` 把 mode 进 JSON 参与 hash，因此 mode 错误的 tree entry（`entry_type="tree"`, `mode=33188`）会产生与合规 mode（`mode=16384`）不同的哈希，造成隐性数据不一致。调用方若手写 `mode=33188, entry_type="tree"`，服务端静默接受会写入脏数据。spec 应在 AC-3 或新的 AC 里**显式定义**：如 `entry_type=="tree"` 且 `mode != 16384` → ValueError（400）。 | 在 AC-3 的"拒 xxx"列表补充一条：`entry_type="tree"` 时 `mode` 必须为 16384（0o040000），否则 ValueError；同步在风险表"中间 tree 的 mode 字段约定不一致"的缓解措辞里明示 service 会拒不合规 mode |

---

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | spec.md §范围 AC-6 + "跨 commit / 跨 repo 自然 dedup 子 tree" | spec AC-6 声称"跨 repo 自然 dedup 子 tree"。但 `models/tree.py` 的 `TreeORM` 主键是 `hash`（String 64），并不是 `(hash, repo_id)` 复合键——`repo_id` 只是一个带 index + FK 的普通列。因此 `TreeORM` 实际**跨 repo 共享同一行**（hash 全局唯一主键）。这与 spec AC-8 要求的 "不存在或**不属于该 repo → 404**"（即按 `(hash, repo_id)` 查）形成矛盾：若 hash 全局唯一，`trees` 表只有一行，但 repo_id 只是该行的一个属性，不能同时属于 repo A 和 repo B。跨 repo 的 dedup 语义与安全边界在 spec 层面**未澄清**。建议 spec 明确：跨 repo dedup 是否可行、GET /trees/{hash} 的 repo 鉴权逻辑具体用什么查询（按 hash + repo_id 过滤，还是按 hash 全局查后再校验？） | 在 §背景 / AC-6 / AC-8 加说明框："TreeORM 主键为 hash（全局唯一），repo_id 是所属 repo 标注。跨 repo 插入相同 hash 时，若 hash 已存在则 upsert 幂等（不更新 repo_id）。GET /trees/{hash} 安全边界：查 trees WHERE hash=? AND repo_id=? 如无结果则 404。若跨 repo 希望共享 read，需评估 phase 2。" 同时 tasks.md T-3 的 upsert 逻辑要对应更新说明 |
| SHOULD FIX-2 | spec.md §验收标准 AC-14 | AC-14 描述为"AC-14 自递归 + self_check 含 `run_tree_nested_domain` block"。"AC-14 自递归"没有任何语义，读者无法理解。这是一个措辞缺陷，不影响验证命令（grep 命令明确），但会让读者困惑 AC-14 到底要验什么。 | 改描述为"scripts/_self_check.sh 已注册 run_tree_nested_domain block（含本 change 14 条 AC 的 grep/pytest 命令）；self_check current 可独立运行" |
| SHOULD FIX-3 | spec.md §问题陈述 / blob 存在性校验 | 步骤 1 blob 存在性校验逻辑（`service/commit.py:130-139`）在 nested 化之后需要遍历 `all_trees` 的 **leaf blob**，而不是 `payload.tree.entries`（此时 entries 里含 `/`，直接 target_hash 是叶子 blob 的 hash；但 nested 化之后子 tree entry 的 `target_hash` 是子 tree hash，不是 blob hash）。spec 没有明确说明嵌套化后步骤 1 如何取到所有叶子 blob hash。若 generator 照搬旧逻辑 `{e.target_hash for e in payload.tree.entries}`，对含 type=tree 的 entries 会跑去校验子 tree hash 是否在 BlobStore 里，恒为 False，导致 400 误拒。 | 在 AC-4 或 AC-3 前加一段说明："步骤 1 blob 存在性校验须在 _normalize_to_nested 之后（或用原始 payload entries 中 entry_type=blob 的 target_hash，因为 soft mode 下所有输入 entries 均为 blob）"；或在 spec 步骤拆解里明确 steps 1→2→3→4 中 validate/normalize 的位置 |

---

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | spec.md §路径校验（AC-3）| 大小写敏感性、Windows 风格 `\`、unicode 归一化（NFD vs NFC）未提及。这些是边界情况，但在跨平台数据生产场景（Windows adapter）可能出现。 | 明确"不做 case folding / unicode 归一化（留 follow-up）；`\` 不视为分隔符（视为合法文件名字符）"；或显式补到非范围 |
| NTH-2 | spec.md AC-11 | test_path_validation_rejects 未列 `"a/"` / `" a"` 等边界（见 MUST FIX-2）。若 MUST FIX-2 采纳则 AC-11 用例列表也需同步增加。 | 随 MUST FIX-2 一起修 |
| NTH-3 | spec.md §问题陈述 | 空 segment 在 `"a//b"` 里已隐含，但 spec 在 AC-3 用 `"//` 出现" 表达；如果 validator 实现为按 `/` 切割后检查 segment，则 `"a//b"` 拆出空 segment `""` 自然被"拒 name==" "覆盖，无需独立规则。建议 spec 统一用 segment 语义描述（"每个 segment 不得为空、不得为 `.` 或 `..`、不得含前导或末尾空白"）减少歧义。 | 可选 |

---

## Verdict

**REVISION REQUIRED**

未关闭 MUST FIX 共 4 条：

1. **MUST FIX-1**：AC-5 grep 可靠性缺陷（假阳性）
2. **MUST FIX-2**：路径校验边界遗漏（末尾 `/`、空白 segment）
3. **MUST FIX-3**：AC-6 措辞语义误导（"算法不变"但输入空间扩大）
4. **MUST FIX-4**：`entry_type="tree"` + mode 不合规时未定义行为（可写入脏 hash）

这 4 条均直接影响编码阶段的实现正确性：MUST FIX-1 会使 AC-5 在不健全实现下仍通过自检；MUST FIX-2 会漏过非法路径写入数据库；MUST FIX-3 会导致后续 reviewer 错误理解 hash 兼容性；MUST FIX-4 会导致脏 mode 数据静默写入后无法检测。

---

## 后续指引（Generator 修 v2 后自查）

```bash
# 1. 确认 AC-5 验证命令改为不可假阳性的形式（推荐 dry-import 或带精确 regex 的 grep）
grep -A5 "AC-5" .harness/changes/tree-nested-domain-20260520/request_analysis/spec.md

# 2. 确认 AC-3 列表含"以 / 结尾"与"segment 含空白"
grep -A10 "AC-3" .harness/changes/tree-nested-domain-20260520/request_analysis/spec.md | grep -E "结尾|空白|trailing"

# 3. 确认 AC-6 描述去掉"算法不变"改为"实现代码不改"
grep "AC-6" .harness/changes/tree-nested-domain-20260520/request_analysis/spec.md | grep -v "算法不变"

# 4. 确认 AC-3 or 新 AC 含 entry_type=tree + mode != 16384 → ValueError
grep -E "16384|mode.*tree|tree.*mode" .harness/changes/tree-nested-domain-20260520/request_analysis/spec.md
```

v2 review 时将以上自查输出作为 MUST FIX 复检证据。
