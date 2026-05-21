#!/usr/bin/env bash
# scripts/integration_test.sh
#
# 用法（Usage）：
#   bash scripts/integration_test.sh [subcommand]
#
#   子命令：
#     all       （默认）起容器 → alembic upgrade → 跑测试 → 关容器
#     up        起 docker-compose（PG/MinIO/Redis）+ alembic upgrade head
#     up-keep   起容器 + alembic upgrade，不自动关（dev 复用）
#     run       设 env → uv run pytest（apps/api + packages/core）
#     down      docker compose down -v（清 volume）
#     --help    打印此帮助
#
# 退码语义（sysexits.h）：
#   0   成功
#   1   run 阶段 pytest 失败
#   2   up 阶段失败（容器未就绪 / alembic 失败）
#   3   down 阶段失败
#  64   用法错误（EX_USAGE）
#
# 输出约定：
#   每行前缀 [integration]；最终结果打印 INTEGRATION_OK 或 INTEGRATION_FAIL <code>
#
# 注：minio-init 是一次性 init 容器，等其 exit (0) 即可；不在 healthcheck 服务列表内。
# 注：如 docker-compose.dev.yml 服务名变更，需同步更新本脚本第 SERVICES_HEALTH 行。

set -euo pipefail

# ---------------------------------------------------------------------------
# 路径
# ---------------------------------------------------------------------------
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${REPO_ROOT}/docker/docker-compose.dev.yml"

# source 共享函数（log_info / log_error / wait_for_healthy / wait_for_exit）
# shellcheck source=scripts/lib/integration_helpers.sh
source "${REPO_ROOT}/scripts/lib/integration_helpers.sh"

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
SERVICES_HEALTH=("postgres" "minio" "redis")
HEALTHCHECK_TIMEOUT=60

DATAPLAT_DATABASE_URL_DEFAULT="postgresql+asyncpg://dataplat:dataplat@localhost:5432/dataplat"
DATAPLAT_MINIO_ENDPOINT_DEFAULT="http://localhost:9000"
DATAPLAT_MINIO_ACCESS_KEY_DEFAULT="dataplat"
DATAPLAT_MINIO_SECRET_KEY_DEFAULT="dataplat-dev-secret"
DATAPLAT_REDIS_URL_DEFAULT="redis://localhost:6379/0"

# ---------------------------------------------------------------------------
# usage
# ---------------------------------------------------------------------------
usage() {
    cat <<'EOF'
用法：bash scripts/integration_test.sh [subcommand]

子命令（all up down run up-keep）：
  all       （默认）起容器 → alembic upgrade → 跑测试 → 关容器
  up        起 docker-compose（PG/MinIO/Redis）+ alembic upgrade head
  up-keep   起容器 + alembic upgrade，不自动关（dev 复用）
  run       设 env → uv run pytest（apps/api + packages/core）
  down      docker compose down -v（清 volume）
  --help    打印此帮助

退码语义（sysexits.h）：
  0   成功
  1   run 阶段 pytest 失败（EX_RUN）
  2   up 阶段失败（容器未就绪 / alembic 失败）（EX_UP）
  3   down 阶段失败（EX_DOWN）
 64   用法错误（EX_USAGE）

输出约定：
  每行前缀 [integration]；最终结果打印 INTEGRATION_OK 或 INTEGRATION_FAIL <code>

示例：
  bash scripts/integration_test.sh all        # 完整集成测试
  bash scripts/integration_test.sh up-keep    # 起容器不关（dev 调试）
  bash scripts/integration_test.sh run        # 已有容器时单独跑测试
  bash scripts/integration_test.sh down       # 清理容器和 volume
EOF
    exit 64
}

# ---------------------------------------------------------------------------
# cmd_up：起容器 + alembic upgrade
# ---------------------------------------------------------------------------
cmd_up() {
    log_info "=== UP：启动 docker-compose 服务 ==="

    # 清理孤儿容器（端口冲突预防）
    docker compose -f "${COMPOSE_FILE}" down --remove-orphans 2>/dev/null || true

    # 起 postgres / minio / minio-init / redis（不起 mailpit）
    docker compose -f "${COMPOSE_FILE}" up -d postgres minio minio-init redis

    # 等待有 healthcheck 的服务
    for svc in "${SERVICES_HEALTH[@]}"; do
        wait_for_healthy "${svc}" "${HEALTHCHECK_TIMEOUT}" || exit 2
    done

    # 等待 minio-init 退出
    wait_for_exit "minio-init" "${HEALTHCHECK_TIMEOUT}" || exit 2

    # alembic upgrade head
    log_info "=== alembic upgrade head ==="
    (
        cd "${REPO_ROOT}/apps/api" || exit 2
        DATAPLAT_DATABASE_URL="${DATAPLAT_DATABASE_URL:-${DATAPLAT_DATABASE_URL_DEFAULT}}" \
            uv run alembic upgrade head
    ) || { log_error "alembic upgrade head 失败"; exit 2; }

    log_info "=== UP 完成 ==="
}

# ---------------------------------------------------------------------------
# cmd_run：设 env → 跑 pytest
# ---------------------------------------------------------------------------
cmd_run() {
    log_info "=== RUN：设置集成测试环境变量 ==="

    export DATAPLAT_DATABASE_URL="${DATAPLAT_DATABASE_URL:-${DATAPLAT_DATABASE_URL_DEFAULT}}"
    export DATAPLAT_MINIO_ENDPOINT="${DATAPLAT_MINIO_ENDPOINT:-${DATAPLAT_MINIO_ENDPOINT_DEFAULT}}"
    export DATAPLAT_MINIO_ACCESS_KEY="${DATAPLAT_MINIO_ACCESS_KEY:-${DATAPLAT_MINIO_ACCESS_KEY_DEFAULT}}"
    export DATAPLAT_MINIO_SECRET_KEY="${DATAPLAT_MINIO_SECRET_KEY:-${DATAPLAT_MINIO_SECRET_KEY_DEFAULT}}"
    export DATAPLAT_REDIS_URL="${DATAPLAT_REDIS_URL:-${DATAPLAT_REDIS_URL_DEFAULT}}"

    local run_failed=0

    log_info "=== RUN：apps/api pytest ==="
    (
        cd "${REPO_ROOT}/apps/api" || exit 1
        uv run pytest -q 2>&1 | tail -100
    ) || run_failed=1

    if [[ ${run_failed} -ne 0 ]]; then
        log_error "apps/api pytest 失败"
        return 1
    fi

    log_info "=== RUN：packages/core pytest ==="
    (
        cd "${REPO_ROOT}/packages/core" || exit 1
        uv run pytest -q 2>&1 | tail -100
    ) || run_failed=1

    if [[ ${run_failed} -ne 0 ]]; then
        log_error "packages/core pytest 失败"
        return 1
    fi

    log_info "=== RUN 完成 ==="
}

# ---------------------------------------------------------------------------
# cmd_down：docker compose down -v
# ---------------------------------------------------------------------------
cmd_down() {
    log_info "=== DOWN：清理容器和 volume ==="
    docker compose -f "${COMPOSE_FILE}" down -v || { log_error "docker compose down 失败"; exit 3; }
    log_info "=== DOWN 完成 ==="
}

# ---------------------------------------------------------------------------
# cmd_all：up → run → down（run 失败也执行 down）
# ---------------------------------------------------------------------------
cmd_all() {
    log_info "=== ALL：完整集成测试流程 ==="

    cmd_up || { log_error "UP 失败"; echo "INTEGRATION_FAIL 2"; exit 2; }

    local run_exit=0
    cmd_run || run_exit=$?

    cmd_down || { log_error "DOWN 失败（run_exit=${run_exit}）"; echo "INTEGRATION_FAIL 3"; exit 3; }

    if [[ ${run_exit} -ne 0 ]]; then
        echo "INTEGRATION_FAIL ${run_exit}"
        exit "${run_exit}"
    fi

    echo "INTEGRATION_OK"
}

# ---------------------------------------------------------------------------
# cmd_up_keep：up + alembic，不执行 down（dev 复用）
# ---------------------------------------------------------------------------
cmd_up_keep() {
    cmd_up
    log_info "容器保持运行（up-keep 模式）。运行 'bash scripts/integration_test.sh down' 清理。"
}

# ---------------------------------------------------------------------------
# 入口分发
# ---------------------------------------------------------------------------
main() {
    local subcmd="${1:-all}"

    case "${subcmd}" in
        up)
            cmd_up
            ;;
        up-keep)
            cmd_up_keep
            ;;
        run)
            cmd_run || { echo "INTEGRATION_FAIL 1"; exit 1; }
            echo "INTEGRATION_OK"
            ;;
        down)
            cmd_down
            ;;
        all)
            cmd_all
            ;;
        --help|-h|help)
            usage
            ;;
        *)
            log_error "未知子命令：${subcmd}"
            usage
            ;;
    esac
}

main "$@"
