---
change_id: harness-ac-behavioral-tier-20260518
target: coding_report_v1.md + 6 改动文件
target_version: 1
review_version: 1
reviewer: claude-agent:harness-ac-behavioral-tier-20260518-stage4-reviewer-v1
reviewed_at: 2026-05-18T10:30:00Z
verdict: APPROVED
---

# Code Review v1

> 独立 reviewer 子 agent；不共享 generator 上下文；按 reviewer-agent.md §5 + expert-reviewer SKILL artifact 模式 + code-review SKILL 工作；所有断言**实跑命令验证**，不只看 coding_report 自述 PASS。

## 上游材料

- `coding/coding_report_v1.md`（generator 自述）
- `request_analysis/spec.md` v3 APPROVED
- `request_analysis/tasks.md` v3 APPROVED
- `request_analysis/review/spec_review_v3.md` APPROVED
- 6 个改动文件（详 coding_report "改动文件清单"）

## AC 逐条复检（实跑命令证据）

| AC | kind | 复检命令（reviewer 真跑） | 结果 | 状态 |
|---|---|---|---|---|
| AC-1 | static | `test -f .harness/skills/request-analysis/SKILL.md && grep -q "AC 分层规约" ... && grep -q "kind: behavioral" ... && grep -q "豁免判定" ...` | 4 grep 命中 | **PASS** |
| AC-2 | static | `grep -qE "至少.*1 ?条.*behavioral" SKILL.md && grep -q "ac_kind_lint: exempt" SKILL.md` | 命中 | **PASS** |
| AC-3 | static | `grep -q "至少 1 条 behavioral\\|至少 1 行 AC" expert-reviewer/SKILL.md && grep -qE "git diff.*--stat" ... && grep -q "ac_kind_lint" ...` | 3 grep 命中 | **PASS** |
| AC-4 | **behavioral** | `bash scripts/lint/test_ac_kind_lint_fixture.sh`（**reviewer 亲自跑**） | exit 0；fixture (1) PASS / (2) FAIL / (3) FAIL **三场景全断言成功** | **PASS（关键证据）** |
| AC-5 | static | awk 抽 stage 9 段 + 4 个 grep（verdict/self-attest/禁止 deferred/必填字段） | 全命中 | **PASS** |
| AC-6 | static | `grep -q run_ac_kind_lint scripts/_self_check.sh && SEG=$(awk ... spec.md) && [ $(echo "$SEG" \| grep -cE "AC 行 behavioral regex") -ge 2 ]` | **behavioral count=2**（AC-4 + AC-8）；_template 含 kind | **PASS** |
| AC-7 | static | for loop 19 ID grep + "永久豁免" + "暂豁免" 字面 | 19/19 命中 + 分类字面命中 | **PASS** |
| AC-8 | **behavioral** | `grep -q run_harness_ac_behavioral_tier scripts/_self_check.sh` | 命中 | **PASS** |

**8/8 AC 真覆盖**，包括 2 条 behavioral（AC-4 fixture 真跑 + AC-8 自递归确认）。

## artifact 模式 checklist

- [x] 每条 spec AC 都映射到至少一条改动 / 真跑命令（上表逐条列出）
- [x] 没有空跑断言（fixture 真创建 3 个 mktemp 目录 + 跑 lint + 断言退码；不是 `assert True`）
- [x] mock 范围合理（fixture 用 mktemp + AC_KIND_LINT_SCAN_DIR/AC_KIND_LINT_EXEMPT_OVERRIDE env 注入；不 mock _self_check 内部函数）
- [x] 测试名 / 函数名 反映场景（`fixture-ok` / `fixture-bad-no-kind` / `fixture-bad-static-mention`）

## 代码层深度审查

### 1. `run_ac_kind_lint` 函数（scripts/_self_check.sh L1214-1281）

**正面发现**：
- env 入口 `AC_KIND_LINT_SCAN_DIR` / `AC_KIND_LINT_EXEMPT_OVERRIDE` 真生效（reviewer 实跑 `AC_KIND_LINT_SCAN_DIR=$TMP bash scripts/_self_check.sh ac-kind-lint` 验证：spec.md 在 $TMP 下被 lint 跑过，绕过默认豁免清单）
- 双条件 regex 正确锚定 AC 行 kind 单元格（fixture (3) 实证：全 static + 描述含 behavioral 字串场景 → exit 1）
- `${AC_KIND_LINT_EXEMPT_OVERRIDE+x}` 用 `+x` 测试**是否 set**（不是是否非空），允许 `OVERRIDE=""` 表示"空豁免清单"（fixture 用例）。语义正确
- frontmatter `ac_kind_lint: exempt` 跳过逻辑实跑验证：reviewer 构造一个 exempt frontmatter 的非法 AC 表 spec，lint PASS（说明跳过生效）

**SHOULD FIX**：
- **fail-fast 用全局 `$FAIL` 反映累计失败数，不只反映 ac-kind-lint 自身失败数**（L1275-1280）。reviewer 实跑全仓 self_check 复现：`pipeline-orchestrator-mvp-20260518 AC-8 FAIL`（已知 fixture-isolation bug）导致全局 `$FAIL=1`，跑到 ac-kind-lint 时本 lint 实际 PASS，但因 `$FAIL>0` 触发误导日志：
  ```
  PASS  ac-kind-lint  AC 分层规约守门（kind 列存在 + AC 行 kind=behavioral 锚定 regex）
  ac-kind-lint FAIL → exit 1（fail-fast；不跑后续 block）
  修复参考：.harness/skills/request-analysis/SKILL.md § AC 分层规约
  ```
  这里 "ac-kind-lint FAIL" 与上一行 "PASS ac-kind-lint" **自相矛盾**；"修复参考：AC 分层规约" 引导用户去查错误的方向（实际应该指向 pipeline AC-8 的 fixture-isolation）。**且强制 exit 1 截断了汇总段 `=== 汇总 === PASS:.../FAIL:.../SKIP:...` 不再打印**。
- **同型缺陷**继承自 `run_reviewer_lint`（L1382），但 reviewer-lint 放最前面位置时全局 `$FAIL=0`，所以没暴露。ac-kind-lint 放最后位置（L1430，在 18 个 block + 1 个本 block 之后），同模式不再适用。
- **修法建议**：用局部计数器记录本 lint 内的 fail，或读取 `run_ac` 返回退码：
  ```bash
  local lint_failed=$FAIL
  run_ac "ac-kind-lint" "..." bash -c '...'
  if [ "$FAIL" -gt "$lint_failed" ]; then
    echo "ac-kind-lint FAIL → exit 1..."
    exit 1
  fi
  ```

### 2. `_ac_kind_lint_exempt_changes` 死代码

- L1181 定义 `_ac_kind_lint_exempt_changes()`，L1221 注释提及；**全脚本无任何真实调用**（reviewer 用 `grep -n "_ac_kind_lint_exempt_changes\\b" scripts/_self_check.sh` 验证：仅定义 + 注释 2 处命中，无 invocation）
- L1284 `_ac_kind_lint_exempt_changes_inline()` 代码完全相同（同一份 19 ID + 同一个 OVERRIDE 逻辑）—— DRY 违反

### 3. `_ac_kind_lint_exempt_changes_inline` export 行为

reviewer 抽函数定义到临时文件 source 后实跑：
```bash
$ _ac_kind_lint_exempt_changes_inline | head -3        # 直接调用：3 行
$ bash -c '_ac_kind_lint_exempt_changes_inline | head -3'   # 子 shell（依赖 export -f）：3 行
$ AC_KIND_LINT_EXEMPT_OVERRIDE="a,b,c" bash -c '_ac_kind_lint_exempt_changes_inline'   # OVERRIDE 注入：a/b/c
```
**全部按预期工作**；`export -f` + `${VAR+x}` 检测 + tr 转换都正确。

### 4. shell 健壮性

- `bash -c '...'` 大字符串：`set -e` + `if ! cmd; then ... continue; fi` 模式在 reviewer 模拟实跑下控制流正确（grep miss 进 if 分支，不让 bash -c 退出）
- `head -20 "$spec" | grep -qE "^ac_kind_lint:[[:space:]]+exempt"` 跳过 frontmatter exempt：reviewer 实构造一个 exempt 字段 + 故意违反 AC 表的 spec，lint PASS 验证 ✓
- `grep -Fxq` 精确行匹配验证：`harness-bootstrap-20260516` 不被 `harness-bootstrap-2026` 子串误命中 ✓

### 5. fixture 脚本 `scripts/lint/test_ac_kind_lint_fixture.sh`

- 用 `mktemp -d /tmp/ac-kind-fixture-*.XXXXXX` 创建 3 个独立目录
- `trap cleanup EXIT` 实证：reviewer 跑 fixture 前后 `ls /tmp/ac-kind-fixture-* 2>/dev/null | wc -l` = 0 → 0，cleanup 真生效
- 3 个 fixture 子 shell 隔离（`(export AC_KIND_LINT_SCAN_DIR=... ; bash $SELF_CHECK ac-kind-lint >/dev/null; echo $?)`）；主脚本退码不被污染

### 6. 文档健壮性

- `.harness/skills/request-analysis/SKILL.md` § "AC 分层规约" 接在原 § "跨 AC 一致性自审清单" 之后；衔接自然，无内容冲突；豁免清单 19 ID 分两类（永久 2 + 暂豁免 17）醒目分段
- `.harness/skills/expert-reviewer/SKILL.md` § "stage 2 AC kind 字段必查" 接在 § "reviewer 字段填写规约" 之后；同型模式（机械化 lint 守门），引用回 request-analysis SKILL 的 "AC 分层规约" 段，互锁清晰
- `.harness/rules/development-process.md` stage 9 段加 4 checkpoint + (iv) AC 真实性 + self-attest 模板：覆盖 spec AC-5 + 决策"verdict 必须 PASS via self-attest 显式偏离"；模板片段（YAML 块）字段齐全

### 7. 自递归 dogfood

reviewer 仅扫本 change 目录 + 空豁免清单实跑：
```bash
TMP=$(mktemp -d)
mkdir -p "$TMP/harness-ac-behavioral-tier-20260518/request_analysis"
cp .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/spec.md "$TMP/.../spec.md"
AC_KIND_LINT_SCAN_DIR="$TMP" AC_KIND_LINT_EXEMPT_OVERRIDE="" bash scripts/_self_check.sh ac-kind-lint
# → PASS（本 change spec 真过自己写的 lint，dogfood 成立）
```

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| S-1 | `scripts/_self_check.sh` L1275-1280 `run_ac_kind_lint` 末尾 fail-fast | 用全局 `$FAIL` 计数器判定"本 lint 是否 FAIL"，但 ac-kind-lint 在 main 末尾位置，全局 `$FAIL` 累计了前面所有 block 的 FAIL（如 pipeline AC-8 fixture-isolation）。导致 ac-kind-lint 自身 PASS 时仍触发"ac-kind-lint FAIL → exit 1（fail-fast）"误导日志 + 修复参考误归因 + 强制 exit 1 截断汇总段。reviewer 实跑复现 | 用局部计数器 `local lint_failed_before=$FAIL` 在 `run_ac` 之前快照，比较 `[ "$FAIL" -gt "$lint_failed_before" ]` 才触发 fail-fast；或直接捕获 `run_ac` 退码。同型缺陷 reviewer-lint L1382 也存在，但 reviewer-lint 在 main 最前位置 $FAIL=0 不暴露——可一并修但不阻塞本 change |
| S-2 | `scripts/_self_check.sh` L1181-1212 `_ac_kind_lint_exempt_changes` 死代码 | L1181 定义但全脚本无任何调用（reviewer grep 验证：仅定义 + 注释 2 处命中）；与 L1284 `_ac_kind_lint_exempt_changes_inline` 完全相同 → DRY 违反 + 未来 backfill 工作要改两份硬编码清单 | 删除 `_ac_kind_lint_exempt_changes`，注释只引用 `_inline` 版本；或反过来让 inline 复用前者（同型 export -f 即可）。**不阻塞当前合规性**，但保留会让 follow-up `harness-ac-kind-backfill-*` 编辑时漏改一份 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| N-1 | `scripts/_self_check.sh` L1262 "FAIL: ... 无 kind=behavioral 行（注意：必须 AC 行 kind 单元格真为 behavioral，AC 描述里出现 \"behavioral\" 字串不算）" | 提示信息已经很好；可以多加一句"参考：.harness/skills/request-analysis/SKILL.md § AC 分层规约 § kind 字段二分定义"指向修复方向 | 加 SKILL 路径，不阻塞 |
| N-2 | `scripts/lint/test_ac_kind_lint_fixture.sh` L99-103 `run_lint_in_subshell` | 用 `bash "$SELF_CHECK" ac-kind-lint >/dev/null 2>&1` 完全静默，调试时看不到 lint 输出；fixture 失败时排错麻烦 | 加 env DEBUG=1 时 `>&2` 不静默；fixture FAIL 时打印最后 5 行 stderr |
| N-3 | spec AC-4 / SKILL `_template` | 字面"ASGITransport L2" / "load_recipe L3" 引用尚未在 .harness/skills 内提供独立的 behavioral-test-pattern SKILL；未来跨 change 复用可能各写各的 | follow-up `behavioral-test-pattern-skill-*`（已隐含在 spec out-of-scope） |

## v1 MUST FIX 复检（M>1 时填）

不适用（本次为 v1 评审）。

## 与 coding_report 自述的一致性核查

| coding_report 声明 | reviewer 实跑验证 | 状态 |
|---|---|---|
| Fixture 3 场景 PASS（含 (3) 关键打靶）| `bash scripts/lint/test_ac_kind_lint_fixture.sh` → exit 0 + 3 场景日志全 ✓ | **一致** |
| 本 block 8/8 PASS | 全仓 self_check 输出 "=== harness-ac-behavioral-tier-20260518 :: 8 AC ===" 段 8 行全 PASS | **一致** |
| 2 个 global lint PASS（reviewer-lint + ac-kind-lint）| 全仓输出 PASS reviewer-lint + PASS ac-kind-lint | **一致**（但 ac-kind-lint 后被 fail-fast 误中断日志—— S-1） |
| self_check 总 exit 1 因为 pipeline AC-8 不属本 change | 实跑 EXIT=1；FAIL 列表仅 pipeline-orchestrator AC-8 | **一致** |

## Verdict

**APPROVED**

理由：
1. spec v3 全部 8 条 AC 实跑命令验证全 PASS，包括 2 条 behavioral（AC-4 fixture + AC-8 自递归）
2. AC-4 关键打靶（fixture 3：全 static + 描述含 behavioral 字串）实证机械化锚定 regex 真守门 —— 这是本 meta-change 的核心命题
3. 自递归 dogfood 成立：本 change spec.md 自身过自己写的 lint
4. 文档衔接自然，无自相矛盾；env 入口、export -f、frontmatter exempt 跳过、cleanup trap 全部实跑生效
5. 唯二 SHOULD FIX（fail-fast 误归因、`_ac_kind_lint_exempt_changes` 死代码）**不阻塞**本 change 验收：S-1 是日志误导不是判定错误（lint 输出"PASS"在前，FAIL 在后；准确解读后真实 PASS）；S-2 是 DRY 违反不影响功能；都可作为 follow-up 或在 stage 5/6 一并修

## 复检指引（给 Generator）

如需修 SHOULD FIX 后再过：

```bash
# S-1 修后验证：故意触发一个前置 block FAIL，看 ac-kind-lint 是否仍误中断
# 简易测：人为加一个 `run_ac AC-X "fake" false` 到 bootstrap-monorepo block 末尾，然后跑全仓
bash scripts/_self_check.sh 2>&1 | tail -10
# 预期：ac-kind-lint 段只显示 "PASS ac-kind-lint"，**不再有** "ac-kind-lint FAIL → exit 1"，
# 主脚本继续跑到 "=== 汇总 ===" 段

# S-2 修后验证：
grep -c "_ac_kind_lint_exempt_changes\\b" scripts/_self_check.sh
# 预期：仅 1 个（_inline 定义） + 1 个 export -f；调用点 2-3 处
```

## 后续指引

- APPROVED → 进入 stage 5（单测编写）
- summary.md 阶段进度表更新 stage 4 = done / verdict = APPROVED / 报告路径 = coding/review/code_review_v1.md
- 强烈建议 stage 5/6 一并把 S-1 / S-2 修掉（修法 < 10 行 diff，零额外成本），把 deferred 项控制在最少
