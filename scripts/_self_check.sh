#!/usr/bin/env bash
# scripts/_self_check.sh
#
# 仓库级自检脚本——把每个变更 spec §验收标准表的 shell 命令归档为
# 可重复运行的断言。当前实现 bootstrap-monorepo-20260516 的 17 条 AC。
#
# 设计意图：
# - 每个变更在 stage 5 单测编写阶段把自己的 AC 落到这里（追加块）；
# - stage 8 CI 调用本脚本作为统一 smoke gate；
# - 后续 follow-up `harness-script-productize-<yyyymmdd>` 会把 harness-bootstrap-20260516
#   的 12 条 AC（当前在 .harness/changes/harness-bootstrap-20260516/unit_test/
#   check_harness.sh）也搬进来，形成单一入口。
#
# 用法：
#   bash scripts/_self_check.sh                    # 跑全部
#   bash scripts/_self_check.sh bootstrap-monorepo # 只跑指定 change 的块
#
# 退出码：0 全过 / 1 至少一条 FAIL。
#
# 运行环境要求：bash ≥ 3.2 + python3（用于 tomllib / yaml / json / ast 解析）。

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

FILTER="${1:-}"

PASS=0
FAIL=0
FAILED_ACS=()

run_ac() {
  local id="$1"
  local desc="$2"
  shift 2
  if "$@" >/dev/null 2>&1; then
    printf "PASS  %-10s  %s\n" "$id" "$desc"
    PASS=$((PASS + 1))
  else
    printf "FAIL  %-10s  %s\n" "$id" "$desc"
    FAIL=$((FAIL + 1))
    FAILED_ACS+=("$id")
  fi
}

# =============================================================================
# Block: bootstrap-monorepo-20260516
# 17 条 AC（详见 .harness/changes/bootstrap-monorepo-20260516/request_analysis/spec.md）
# =============================================================================

run_bootstrap_monorepo() {
  echo "=== bootstrap-monorepo-20260516 :: 17 AC ==="

  run_ac AC-1 "pyproject uv workspace" \
    python3 -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); assert 'apps/api' in d['tool']['uv']['workspace']['members']"

  run_ac AC-2a "pnpm-workspace 含 apps/web" \
    python3 -c "import yaml; d=yaml.safe_load(open('pnpm-workspace.yaml')); assert 'apps/web' in d['packages']"

  run_ac AC-2b "package.json 合法" \
    python3 -c "import json; json.load(open('package.json'))"

  run_ac AC-3 "turbo.json 4 task" \
    python3 -c "import json; d=json.load(open('turbo.json')); [d['tasks'][k] for k in ['lint','typecheck','test','build']]"

  run_ac AC-4 "Makefile 必备 11 target make -n 干跑" \
    bash -c 'for t in up down api web worker migrate seed codegen test lint typecheck; do make -n "$t" >/dev/null 2>&1 || exit 1; done'

  run_ac AC-5 "README ≥ 30 行 + quickstart" \
    bash -c '[ "$(wc -l < README.md)" -ge 30 ] && grep -qE "快速开始|Quickstart" README.md'

  run_ac AC-6 ".gitignore 必备排除 + .claude/settings.local.json ignored" \
    bash -c 'test -f .gitignore && for p in .venv node_modules dist __pycache__ .pytest_cache .ruff_cache .mypy_cache .turbo ".claude/settings.local.json"; do grep -q "$p" .gitignore || exit 1; done && git check-ignore -q .claude/settings.local.json'

  run_ac AC-7 "apps/api 文件齐全 + /healthz" \
    bash -c 'for f in pyproject.toml dataplat_api/__init__.py dataplat_api/main.py tests/__init__.py tests/test_health.py; do test -f "apps/api/$f" || exit 1; done && grep -q "healthz" apps/api/dataplat_api/main.py'

  run_ac AC-8 "apps/web 文件齐全" \
    bash -c 'for f in package.json vite.config.ts tsconfig.json tsconfig.node.json index.html src/main.tsx src/App.tsx; do test -f "apps/web/$f" || exit 1; done'

  run_ac AC-9 "packages/core / sdk-py + worker src layout" \
    bash -c 'test -f packages/core/pyproject.toml && test -f packages/core/src/dataplat_core/__init__.py && test -f packages/sdk-py/pyproject.toml && test -f packages/sdk-py/src/dataplat_sdk/__init__.py && test -f worker/pyproject.toml && test -f worker/src/dataplat_worker/__init__.py'

  run_ac AC-10 "packages/api-types 占位" \
    bash -c 'test -f packages/api-types/package.json && test -f packages/api-types/src/generated.ts'

  run_ac AC-11 "plugins/recipes/docs README ≥ 10 行" \
    bash -c 'for f in plugins/README.md recipes/README.md docs/README.md; do test -f "$f" && [ "$(wc -l < "$f")" -ge 10 ] || exit 1; done'

  run_ac AC-12 "docker-compose.dev.yml 合法 + 3 service" \
    python3 -c "import yaml; d=yaml.safe_load(open('docker/docker-compose.dev.yml')); s=d.get('services',{}); [s[k] for k in ['postgres','minio','redis']]"

  run_ac AC-13 "3 个 Dockerfile" \
    bash -c 'for f in api.Dockerfile worker.Dockerfile web.Dockerfile; do test -f "docker/images/$f" || exit 1; done'

  run_ac AC-14 "scripts/export_openapi.py + AST 合法" \
    bash -c 'test -f scripts/export_openapi.py && python3 -c "import ast; ast.parse(open(\"scripts/export_openapi.py\").read())"'

  run_ac AC-15 "ci.yml 合法 + 5 job + concurrency" \
    python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/ci.yml')); j=d['jobs']; [j[k] for k in ['python-lint-type','python-test','web-lint-type','web-test','codegen-check']]; assert d['concurrency']['cancel-in-progress'] is True"

  run_ac AC-16 "apps/api pytest test_health.py exit 0" \
    bash -c 'cd apps/api && uv run pytest -q tests/test_health.py >/dev/null 2>&1'

  run_ac AC-17 "apps/web vite build → dist/index.html" \
    bash -c 'pnpm --filter web build >/dev/null 2>&1 && test -f apps/web/dist/index.html'
}

# =============================================================================
# 主控
# =============================================================================

case "$FILTER" in
  ""|bootstrap-monorepo|bootstrap-monorepo-20260516)
    run_bootstrap_monorepo
    ;;
  *)
    echo "未知 change: $FILTER" >&2
    echo "已知 change: bootstrap-monorepo（更多变更将随后续 stage 5 追加）" >&2
    exit 2
    ;;
esac

echo
echo "=== 汇总 ==="
echo "PASS: $PASS"
echo "FAIL: $FAIL"

if [ "$FAIL" -gt 0 ]; then
  echo "失败: ${FAILED_ACS[*]}"
  exit 1
fi

echo "全部通过。"
exit 0
