#!/usr/bin/env bash
# check_harness.sh
#
# 把 harness-bootstrap-20260516 spec.md §验收标准表的 12 条 AC 产品化为
# 可重复运行的断言脚本。本脚本是本变更 Stage 5 的"单测"路径：纯文档变更
# 没有 Python/TS 代码可测，所以把骨架的结构性约束转成 shell 级断言。
#
# 运行环境要求：bash ≥ 3.2（用到 BASH_SOURCE / local / 数组）。
# alpine busybox /bin/sh 与 dash 不兼容；显式用 bash 执行即可。
#
# 使用：
#     cd /path/to/nta-lake
#     bash .harness/changes/harness-bootstrap-20260516/unit_test/check_harness.sh
#
# 退出码：
#     0  全部 AC PASS
#     非0  至少一条 FAIL（脚本会在第一条失败处继续跑完所有 AC 再退出，
#         便于一次性看到全貌）
#
# follow-up：把本脚本提升到 `scripts/check_harness.sh` 由独立变更
# `harness-script-productize-<yyyymmdd>` 完成；本 change 内只追加结构性
# 复用，不动顶层目录（详见 spec §范围 与 summary §Deferred）。

set -u

# 切到仓库根（脚本可能从任何 cwd 启动）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
cd "$REPO_ROOT"

PASS=0
FAIL=0
FAILED_ACS=()

run_ac() {
  local id="$1"
  local desc="$2"
  shift 2
  if "$@" >/dev/null 2>&1; then
    printf "PASS  %-6s  %s\n" "$id" "$desc"
    PASS=$((PASS + 1))
  else
    printf "FAIL  %-6s  %s\n" "$id" "$desc"
    FAIL=$((FAIL + 1))
    FAILED_ACS+=("$id")
  fi
}

# ---- AC-1 ----
ac1() { test -f CLAUDE.md && grep -q "application-owner.md" CLAUDE.md; }

# ---- AC-2 ----
ac2() {
  test -f .harness/agents/application-owner.md && \
    grep -qE "配置索引|十阶段|硬性约束" .harness/agents/application-owner.md
}

# ---- AC-3 ----
ac3() {
  for f in development-process engineering-structure coding-style; do
    test -f ".harness/rules/$f.md" || return 1
  done
}

# ---- AC-4 ----
ac4() {
  local n
  n=$(grep -cE "^## 阶段 [0-9]+ " .harness/rules/development-process.md)
  [ "$n" -ge 10 ]
}

# ---- AC-5 ----
ac5() {
  local n
  n=$(find .harness/skills -name SKILL.md | wc -l)
  [ "$n" -eq 9 ] && test -f .harness/skills/README.md
}

# ---- AC-6 ----
ac6() {
  local n
  n=$(find .harness/changes/_template -type f | wc -l)
  [ "$n" -ge 10 ]
}

# ---- AC-7 ----
ac7() { grep -qE "feature-slug.*yyyymmdd" .harness/changes/README.md; }

# ---- AC-8 ----
ac8() {
  test -f .harness/mcp/README.md && \
    grep -qE "Phase 0|占位" .harness/mcp/README.md
}

# ---- AC-9 ----
ac9() {
  for f in README architecture domain-glossary adr/README; do
    test -f "wiki/$f.md" || return 1
  done
  for term in Repository Asset "Source Adapter" Processor Lineage Commit Blob; do
    grep -q "$term" wiki/domain-glossary.md || return 1
  done
}

# ---- AC-10 ----
ac10() {
  local f
  for f in .harness/skills/*/SKILL.md; do
    grep -qE "进入条件|质量门禁|失败回退" "$f" || return 1
  done
}

# ---- AC-11 ----
ac11() {
  find .harness wiki CLAUDE.md -name "*.md" -type f -exec wc -l {} + \
    | awk 'NF==2 && $1 < 20 {bad=1} END {exit bad}'
}

# ---- AC-12 ----
ac12() {
  local memdir
  memdir="$HOME/.claude/projects/$(pwd | sed 's|/|-|g')/memory"
  test -f "$memdir/MEMORY.md" || return 1
  local f
  for f in project_overview harness_constraints feedback_doc_language; do
    test -f "$memdir/$f.md" || return 1
  done
}

# ----- 主控 -----
echo "=== harness-bootstrap-20260516 :: 12 条 AC 断言 ==="
echo "仓库根: $REPO_ROOT"
echo
run_ac AC-1  "CLAUDE.md 存在且引用 Owner Agent"             ac1
run_ac AC-2  "Owner Agent 存在且声明配置索引/十阶段/硬约束"   ac2
run_ac AC-3  ".harness/rules/ 三份规则齐全"                  ac3
run_ac AC-4  "development-process.md 含 ≥10 个阶段定义"      ac4
run_ac AC-5  "9 个 SKILL.md + 索引 README.md 齐全"           ac5
run_ac AC-6  "changes/_template/ 含 ≥10 个文件"              ac6
run_ac AC-7  "changes/README.md 含命名约定（feature-slug + yyyymmdd）" ac7
run_ac AC-8  "mcp/README.md 含 Phase 0 / 占位语义"           ac8
run_ac AC-9  "wiki 四份文件 + 7 个核心术语齐全"               ac9
run_ac AC-10 "每个 SKILL.md 含进入条件/质量门禁/失败回退"     ac10
run_ac AC-11 "所有骨架 .md ≥ 20 行"                           ac11
run_ac AC-12 "项目记忆目录 MEMORY.md + 3 份记忆文件齐全"     ac12

echo
echo "=== 汇总 ==="
echo "PASS: $PASS / 12"
echo "FAIL: $FAIL / 12"

if [ "$FAIL" -gt 0 ]; then
  echo "失败 AC: ${FAILED_ACS[*]}"
  exit 1
fi

echo "全部通过。"
exit 0
