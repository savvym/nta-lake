---
change_id: web-tree-nested-ui-20260520
target: spec.md
target_version: 2
review_version: 2
reviewer: claude-agent:web-tree-nested-ui-20260520-stage2-reviewer-v2
reviewed_at: 2026-05-19T18:00:00Z
verdict: REVISION REQUIRED
---

# Spec Review v2

## v1 MUST FIX 复检

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| MUST FIX-1 | AC-9 kind=behavioral 但验证为 n/a，不可机械化 | RESOLVED | v2 删除旧 AC-9（手测），新 AC-9 kind=static，验证命令为 `grep -q "run_web_tree_nested_ui" scripts/_self_check.sh`，完全可机械化 |
| MUST FIX-2 | AC-6 grep 计数在 vitest verbose 输出中假 FAIL | RESOLVED（但引入新回归，见 MUST FIX-1 below） | v2 改用 JSON reporter + python3 断言，修了原始 grep 问题；但 `numTotalTests>=4` 断言存在新缺陷 |
| MUST FIX-3 | AC-3 默认值验证弱，未确认 path default === "" | RESOLVED | 拆出 AC-11 专门验证：`grep -qE 'path\s*:\s*z\.string\(\)\.(default\(["\x27]{2}\)|catch\(["\x27]{2}\))'`，同时覆盖 `.default("")` 和 `.catch("")` 两种 Zod 写法 |
| MUST FIX-4 | AC-12 与 AC-10 完全重复，草稿遗留 | RESOLVED | v2 删除 AC-12，AC 总数降为 11 |

---

## 检查清单结论（plan 模式）

| 项 | 状态 | 说明 |
|---|---|---|
| 背景写明了为什么现在做 | PASS | tree-nested-domain merge 后 UI 退化，背景清晰 |
| 问题陈述与目标可被外部读者理解 | PASS | 问题陈述具体，含代码路径与预期失败场景 |
| 范围 / 非范围都有 | PASS | In scope / Out of scope 均明确 |
| 验收标准每条都可演示且可机械化 | PARTIAL - 见 MUST FIX-1 / MUST FIX-2 | AC-6 基线问题 + AC-11 mislabeled behavioral |
| 风险有缓解措施或显式 accept | PASS | 8 条风险，每条均有缓解或 accept 声明 |
| 没有把已有架构当新提案重复 | PASS | 未重复 design.md 内容 |
| AC 表存在 kind 列 | PASS | 表头含 kind 列 |
| 至少 1 行 AC 的 kind 为 behavioral（锚定 regex） | PASS | AC-6 / AC-7 / AC-10 均为 behavioral（已可执行验证） |

---

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | spec.md §验收标准 标题 + AC-6 完整命令 | **AC-6 "≥ 已有数+4" 断言回归**：v2 AC-6 期望列写 `numTotalTests ≥ 已有数+4`，但实际验证命令 `assert d['numTotalTests']>=4` 只检查总数 ≥ 4，**没有捕获"已有数"基线**。若测试文件在改动前已有 5+ 测试（现有基线很可能如此），该断言在不添加任何新用例的情况下也会通过，AC-6 的"≥ 4 新用例"约束形同虚设。 | 修法二选一：(a) 命令里先读基线数再断言增量，如 `python3 -c "import json; d=json.load(...); baseline=d['numTotalTests']-4; assert d['numTotalTests']>=baseline+4"` ——但这在同一次跑中无法自举，需要先 git stash 存基线；(b) **更简洁**：改期望为 `numTotalTests >= N`（N 为 spec 写死的绝对值，如现有用例数 + 4 = 写死为 6），并在 spec 注明"基线为 2 条 legacy 用例，完成后总数 ≥ 6"。选 (b) 只需在 spec 明确 N 的具体值，coding agent 可以在写测试后自查。 |
| MUST FIX-2 | spec.md §验收标准 标题行 + §跨链路自审第 4 条 | **头部数字与表格不一致**：`## 验收标准（12 AC）` 标题仍写 12，但 AC 表只有 11 行（AC-1 到 AC-11）；`§受影响模块` 也写 `追加 run_web_tree_nested_ui 12 AC`。两处数字是 v1 遗留，v2 删 AC-12 后未同步更新。 | 将所有出现 "12 AC" 的地方（标题、受影响模块、自审第 5 行）统一改为 "11 AC"。 |
| MUST FIX-3 | spec.md §验收标准 AC-11 kind 字段 + §跨链路自审第 4 条 | **AC-11 mislabeled：表格 kind 列标 `behavioral`，实质是 static grep**。AC-11 验证命令是 `grep -qE '...'`，只检查源码字面量，不执行任何运行时行为，应为 `static` 而非 `behavioral`。同时，self_check 注释 `behavioral AC = 3（AC-6 / AC-7 / AC-10）` 与表格的"AC-11 = behavioral"矛盾。自审第 4 条写"4 behavioral"，但注释写 3 个，内部数字不一致（三处不同值：表格 4、注释 3、自审 4）。 | 将 AC-11 的 kind 改为 `static`；将自审第 4 条改为 `AC 分层：3 behavioral（AC-6/AC-7/AC-10）`；删除 self_check 注释的"behavioral AC = 3"补注或与表格保持一致。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | spec.md §AC-11 完整命令 | AC-11 regex 使用 `\x27` 表示单引号（`'`）。在 bash `grep -qE '...'` 单引号字符串中，`\x27` 不会被 shell 解析为十六进制字符（shell 单引号不做转义），但 GNU grep ERE 支持 `\x27` 作为 hex escape——这是 GNU grep 扩展，POSIX ERE 不保证。若 CI 环境用 macOS grep（BSD grep 不支持 `\x27`），该命令将匹配失败。 | 改用明确的字符类：`(default\(["']{2}\)|catch\(["']{2}\))` 或在 shell 中提前定义变量拼接，避免 `\x27` 的跨平台依赖。 |
| SHOULD FIX-2 | spec.md §AC-9 描述 | AC-9 描述写 `（AC-9 也兼自递归）`，自审第 7 条写 `spec ↔ tasks ↔ self_check 一致`，但"自递归"的含义模糊——不清楚是指 self_check 脚本自身递归运行还是 AC 本身验证自身的注册。这个括号注释在 spec 中没有后续说明，且与原 v1 MUST FIX-4 的删除理由（"AC-12 是 AC-10 副本，无独立意义"）不一致——v2 把"自递归"转移到 AC-9，使 AC-9 同时承担两个不相关的验证职责（self_check 存在 + 自递归）。 | 删除 `（AC-9 也兼自递归）` 括号注释，或写明"自递归"指的是具体什么机制；如无独立含义，直接删除。 |
| SHOULD FIX-3 | spec.md §AC-6 完整命令 | `--reporter json` 在 vitest 中会把 JSON 输出到 stdout，但同时也可能夹杂 stderr 警告，导致 `/tmp/web-tree-nested-vitest.json` 文件不是纯净 JSON，`json.load()` 会报 `JSONDecodeError`。 | 命令中加 `2>/dev/null` 过滤 stderr，或改为 `--reporter=json --outputFile=/tmp/web-tree-nested-vitest.json`（vitest 支持 `--outputFile` 将 JSON 写入文件而非 stdout）。 |
| SHOULD FIX-4 | spec.md §跨链路自审第 4 条 | 自审第 4 条写 `AC 分层：4 behavioral`，但与 MUST FIX-3 指出的三处数字不一致（表格标注 AC-11 为 behavioral，但验证为 static grep；同时注释写 3 个）。自审数字应在 AC-11 kind 修正后同步改为 3。 | 待 MUST FIX-3 修正后，自审第 4 条改为 `AC 分层：3 behavioral（AC-6/AC-7/AC-10）+ 8 static`。 |
| SHOULD FIX-5 | spec.md §风险 第 5 行 | 风险缓解写 `AC-11 显式覆盖`（指"现有 test.tsx 断言与新逻辑冲突 → AC-11 显式覆盖"），但 AC-11 实际验证的是 path 默认值（静态 grep），不是测试不冲突。风险实际由 AC-7 / AC-10 覆盖（vitest run 全 PASS）。 | 将风险第 5 行缓解栏改为 `AC-7 / AC-10 显式覆盖；改测试时保留原"扁平 commit 渲染"断言为 legacy 用例`。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | spec.md §AC-3 验证命令 | AC-3 验证命令只 grep path 字符串出现 + tsc --noEmit，但未单独验证 path 字段在 `validateSearch` 范围内（而不是文件其他地方的 `path` 变量）。AC-11 补了 default 的 grep，但两者组合后仍然存在如果 `path` 是 component local state 而非 search param 时的误命中。低概率但值得注意。 |
| NTH-2 | spec.md §AC-11 | AC-11 只 grep `.default("")` 或 `.catch("")`，不覆盖 TanStack Router `z.string().optional().default("")`（chain 顺序不同时 regex 会失效）。实际 Zod 链可能写成 `z.string().optional().default("")`——此时 `path\s*:\s*z\.string\(\)\.(default...)` 不匹配（`.string()` 后跟 `.optional()` 而不是直接 `.default()`）。 | 在 regex 加可选 `.optional()` 前缀：`z\.string\(\)(\.optional\(\))?\.(default\(...\)|catch\(...\))`，或在 spec 中明确"实现必须用 `.string().default("")`（不得插入 `.optional()`）"。 |
| NTH-3 | spec.md v1 SHOULD FIX-1 到 SHOULD FIX-6（未处理） | v1 的 6 条 SHOULD FIX 在 v2 未处理（除 SHOULD FIX-5 通过删 AC-9 间接解决）。尤其 SHOULD FIX-2（`path=""` vs `undefined`）和 SHOULD FIX-4（tab 切换 path 保留/重置）在 v2 T-2 description 里仍有"看交互期望"歧义。这是 SHOULD FIX 级，不阻塞，但 coding agent 遇到时会随机选择。 |

---

## Verdict

**REVISION REQUIRED**

存在 3 条 MUST FIX：

- **MUST FIX-1**：AC-6 `numTotalTests>=4` 断言无法验证"新增 ≥ 4 用例"，缺少基线，判断永远偏宽松
- **MUST FIX-2**：标题 + 受影响模块 + 自审仍写 "12 AC"，与 AC 表 11 行不符，内部不一致
- **MUST FIX-3**：AC-11 表格 kind 标 `behavioral` 但验证是 static grep；自审第 4 条 "4 behavioral" 与注释 "3 个" 矛盾

v1 的 4 条 MUST FIX 均已修复，但 v2 引入了 3 条新 MUST FIX（数字不一致、AC-6 基线缺失、AC-11 kind 错标）。

---

## 后续指引

Generator 修完 v3 spec 后，自查：

```bash
# 1. 标题数字与 AC 表行数一致
ROWS=$(awk '/^\| ID \|/{p=1;next} p && /^\| AC-/{c++} END{print c}' \
  .harness/changes/web-tree-nested-ui-20260520/request_analysis/spec.md)
TITLE=$(grep "^## 验收标准" .harness/changes/web-tree-nested-ui-20260520/request_analysis/spec.md \
  | grep -oE '[0-9]+')
echo "rows=$ROWS title_num=$TITLE"
[ "$ROWS" = "$TITLE" ] && echo OK || echo MISMATCH

# 2. AC-11 kind 列为 static（不是 behavioral）
awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' \
  .harness/changes/web-tree-nested-ui-20260520/request_analysis/spec.md \
  | grep "AC-11" | grep -qv "behavioral" && echo "AC-11 kind PASS" || echo "AC-11 kind FAIL"

# 3. AC-6 期望有写死 N 值（不是 "已有数+4" 模糊表述）
grep "AC-6" .harness/changes/web-tree-nested-ui-20260520/request_analysis/spec.md \
  | grep -qE "numTotalTests\s*>=\s*[0-9]+" && echo "AC-6 baseline PASS" || echo "AC-6 baseline FAIL"

# 4. 自审 behavioral 数字与表格一致
grep "behavioral" .harness/changes/web-tree-nested-ui-20260520/request_analysis/spec.md \
  | grep -E "AC 分层|behavioral AC ="
# 目视检查：两处数字相同
```

v3 修完后重新 spawn reviewer v3 复检 MUST FIX 闭合状态。
