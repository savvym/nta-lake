#!/usr/bin/env bash
# scripts/lint/check_design_north_star.sh
#
# 验证 .harness/design.md 的北极星结构完整：
# - 6 个顶层节都存在且非空：北极星 / 三层算子模型 / stats-first 设计 / 行级血缘 / 永不做清单 / 迁移路径
# - 每节正文 ≥ 100 字节
# - 三层算子节含 Adapter / Loader / Operator 三个三级子节，每个含 Protocol 草图（class/Protocol 字样）
#
# 来源 change：platform-north-star-pivot-20260520
# 调用方：self_check run_platform_north_star_pivot AC-9
#
# 退出码：0 = 全部 PASS（stdout "OK: design.md north-star structure complete"）
#         1 = 任一 FAIL（stderr 含明确指引）

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DESIGN="$REPO_ROOT/.harness/design.md"

if [ ! -f "$DESIGN" ]; then
  echo "FAIL: $DESIGN 不存在" >&2
  exit 1
fi

FAIL=0

# extract_section <section-title> → stdout 输出该 ## 顶层节的正文（不含标题行）
# 使用 flag-based awk 避开 `awk '/start/,/end/'` 闭区间陷阱
extract_section() {
  local title="$1"
  awk -v t="$title" '
    $0 == "## " t { found=1; next }
    found && /^## / { exit }
    found { print }
  ' "$DESIGN"
}

# 6 个必须存在的顶层节
SECTIONS=("北极星" "三层算子模型" "stats-first 设计" "行级血缘" "永不做清单" "迁移路径")

for s in "${SECTIONS[@]}"; do
  body=$(extract_section "$s")
  if [ -z "$body" ]; then
    echo "FAIL: design.md 缺少 § '$s' 顶层节，或节内无正文" >&2
    echo "  → 修复指引：在 design.md 加 '## $s' 标题 + 正文" >&2
    FAIL=1
    continue
  fi
  bytes=$(printf '%s' "$body" | wc -c | tr -d ' ')
  if [ "$bytes" -lt 100 ]; then
    echo "FAIL: design.md § '$s' 正文太短（$bytes < 100 字节，疑似 stub）" >&2
    echo "  → 修复指引：扩充该节内容，至少 100 字节" >&2
    FAIL=1
  fi
done

# 三层算子节必须含三个子节 + 每节有 Protocol/class 草图
SUBS=("Adapter" "Loader" "Operator")
for subname in "${SUBS[@]}"; do
  found=$(awk -v sname="$subname" '
    $0 == "### " sname { f=1; next }
    f && /^### / { exit }
    f && /^## [^#]/ { exit }
    f { print }
  ' "$DESIGN")
  if [ -z "$found" ]; then
    echo "FAIL: design.md § 三层算子模型 缺少 '### $subname' 子节" >&2
    FAIL=1
    continue
  fi
  if ! printf '%s' "$found" | grep -qE 'Protocol|class '; then
    echo "FAIL: design.md § 三层算子模型 § $subname 缺少 Protocol 或 class 草图" >&2
    echo "  → 修复指引：在该子节加 Python class/Protocol 签名代码块" >&2
    FAIL=1
  fi
done

if [ "$FAIL" -ne 0 ]; then
  echo >&2
  echo "design.md north-star structure 检查未通过 ($FAIL 项 FAIL)" >&2
  echo "权威结构定义见 platform-north-star-pivot-20260520 spec AC-1~AC-6" >&2
  exit 1
fi

echo "OK: design.md north-star structure complete"
exit 0
