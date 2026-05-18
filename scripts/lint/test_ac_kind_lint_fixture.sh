#!/bin/bash
# AC-4 fixture：跑 run_ac_kind_lint 3 个场景验证机械化守门
# (1) 合规 spec.md → 期望 PASS
# (2) 缺 kind 列 → 期望 FAIL
# (3) 全 static kind + AC 描述含 behavioral 字串（**最隐蔽反例**） → 期望 FAIL
#
# 反例 (3) 是 stage 2 v2 reviewer 抓到的实证：原 v2 spec 用裸 grep -q behavioral 会
# 被 AC 描述里"behavioral 三层"等字串误命中，机械化保护失效。v3 改为 AC 行 regex 锚定。

set -e

# ---- 路径准备 ----
REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
SELF_CHECK="$REPO_ROOT/scripts/_self_check.sh"

if [ ! -f "$SELF_CHECK" ]; then
  echo "FAIL: $SELF_CHECK 不存在" >&2
  exit 1
fi

# ---- mktemp + cleanup trap ----
FIXTURE_OK=$(mktemp -d /tmp/ac-kind-fixture-ok.XXXXXX)
FIXTURE_BAD_NO_KIND=$(mktemp -d /tmp/ac-kind-fixture-bad-no-kind.XXXXXX)
FIXTURE_BAD_STATIC_MENTION=$(mktemp -d /tmp/ac-kind-fixture-bad-static-mention.XXXXXX)
cleanup() {
  rm -rf "$FIXTURE_OK" "$FIXTURE_BAD_NO_KIND" "$FIXTURE_BAD_STATIC_MENTION"
}
trap cleanup EXIT

# ---- 构造 fixture 1：合规 spec ----
mkdir -p "$FIXTURE_OK/test-change-fixture-ok/request_analysis"
cat > "$FIXTURE_OK/test-change-fixture-ok/request_analysis/spec.md" <<'OK_EOF'
---
change_id: test-change-fixture-ok
version: 1
status: draft
---

# Spec

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | 文件存在 | test -f foo | 0 |
| AC-2 | behavioral | POST /repos 返回 201 | pytest test_create_201 | 201 |
OK_EOF

# ---- 构造 fixture 2：缺 kind 列 ----
mkdir -p "$FIXTURE_BAD_NO_KIND/test-change-fixture-bad-no-kind/request_analysis"
cat > "$FIXTURE_BAD_NO_KIND/test-change-fixture-bad-no-kind/request_analysis/spec.md" <<'BAD1_EOF'
---
change_id: test-change-fixture-bad-no-kind
version: 1
status: draft
---

# Spec

## 验收标准

| ID | 描述 | 验证方式 | 期望 |
|---|---|---|---|
| AC-1 | 文件存在 | test -f foo | 0 |
BAD1_EOF

# ---- 构造 fixture 3：**关键打靶** 全 static + 描述含 behavioral 字串 ----
mkdir -p "$FIXTURE_BAD_STATIC_MENTION/test-change-fixture-bad-static-mention/request_analysis"
cat > "$FIXTURE_BAD_STATIC_MENTION/test-change-fixture-bad-static-mention/request_analysis/spec.md" <<'BAD2_EOF'
---
change_id: test-change-fixture-bad-static-mention
version: 1
status: draft
---

# Spec

本变更参考 behavioral 三层判定（L1/L2/L3），未来可加 behavioral AC。

## 验收标准

注：本表所有 AC 均为 static；后续会补 behavioral 测试。

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | 文件存在（参考 behavioral 三层指引） | test -f foo | 0 |
| AC-2 | static | 路由声明含 @router.post（未来加 behavioral 集成测试） | grep | hit |
| AC-3 | static | 模型 import 成功（不算 behavioral） | python -c import | 0 |
BAD2_EOF

# ---- 跑 3 个场景 ----

# subshell 跑 + 捕获退码（自定义 trap 兜底，避 fail-fast 污染主脚本）
run_lint_in_subshell() {
  local scan_dir="$1"
  (
    export AC_KIND_LINT_SCAN_DIR="$scan_dir"
    export AC_KIND_LINT_EXEMPT_OVERRIDE=""
    # 用 FILTER=ac-kind-lint 单跑 lint；exit code 反映 lint 结果
    bash "$SELF_CHECK" ac-kind-lint >/dev/null 2>&1
    echo $?
  )
}

echo "=== fixture (1) 合规 spec → 期望 PASS（exit 0） ==="
rc1=$(run_lint_in_subshell "$FIXTURE_OK")
echo "exit=$rc1"
if [ "$rc1" != "0" ]; then
  echo "FAIL: fixture-ok 应 PASS 但 exit=$rc1" >&2
  exit 1
fi

echo
echo "=== fixture (2) 缺 kind 列 → 期望 FAIL（exit != 0） ==="
rc2=$(run_lint_in_subshell "$FIXTURE_BAD_NO_KIND")
echo "exit=$rc2"
if [ "$rc2" = "0" ]; then
  echo "FAIL: fixture-bad-no-kind 应 FAIL 但 exit=0" >&2
  exit 1
fi

echo
echo "=== fixture (3) **关键打靶** 全 static + 描述含 behavioral 字串 → 期望 FAIL（exit != 0） ==="
rc3=$(run_lint_in_subshell "$FIXTURE_BAD_STATIC_MENTION")
echo "exit=$rc3"
if [ "$rc3" = "0" ]; then
  echo "FAIL: fixture-bad-static-mention 应 FAIL 但 exit=0" >&2
  echo "  这意味着 run_ac_kind_lint 的 (ii) 实现用了裸 grep behavioral 被字串误命中" >&2
  echo "  → 机械化保护实质失效，违反 spec_v3 MUST FIX #2 / harness-ac-behavioral-tier 核心命题" >&2
  exit 1
fi

echo
echo "=== ALL 3 FIXTURES PASS ==="
echo "  (1) 合规 PASS ✓"
echo "  (2) 缺 kind 列 FAIL ✓"
echo "  (3) 全 static + 描述含 behavioral 字串 FAIL ✓（机械化锚定 regex 真守门）"
exit 0
