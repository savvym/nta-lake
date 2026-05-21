#!/usr/bin/env bash
# scripts/lib/integration_helpers.sh
#
# 共享工具函数，由 integration_test.sh source 引入。
# 不直接执行；chmod 不强求 exec bit。
#
# 函数：
#   log_info  <msg>            -- 带 [integration] 前缀的标准输出
#   log_error <msg>            -- 带 [integration][ERROR] 前缀的 stderr
#   wait_for_healthy <service> <timeout_s>
#                              -- 轮询 docker compose ps 直到 service 状态含 "(healthy)"
#                                 或超时退出（退码 2）

# ---------------------------------------------------------------------------
# 环境变量（由 integration_test.sh 设 REPO_ROOT 后 source 本文件）
# ---------------------------------------------------------------------------
COMPOSE_FILE="${REPO_ROOT}/docker/docker-compose.dev.yml"

# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------
log_info() {
    echo "[integration] $*"
}

log_error() {
    echo "[integration][ERROR] $*" >&2
}

# ---------------------------------------------------------------------------
# wait_for_healthy <service_name> <timeout_s>
#
# 每 2s 检查一次 `docker compose ps` 文本输出中是否含 "(healthy)" 子串。
# 不依赖 jq，兼容 minimal 环境。
# ---------------------------------------------------------------------------
wait_for_healthy() {
    local service="$1"
    local timeout_s="${2:-60}"
    local elapsed=0

    log_info "等待 ${service} healthy（最多 ${timeout_s}s）..."

    while true; do
        local ps_out
        ps_out="$(docker compose -f "${COMPOSE_FILE}" ps "${service}" 2>/dev/null || true)"

        if echo "${ps_out}" | grep -q "(healthy)"; then
            log_info "${service} 已 healthy（${elapsed}s）"
            return 0
        fi

        if [[ ${elapsed} -ge ${timeout_s} ]]  ; then
            log_error "${service} 在 ${timeout_s}s 内未达 healthy 状态"
            log_error "当前 ps 输出："
            echo "${ps_out}" >&2
            return 2
        fi

        sleep 2
        elapsed=$((elapsed + 2))
    done
}

# ---------------------------------------------------------------------------
# wait_for_exit <service_name> <timeout_s>
#
# 等待一次性 init 容器（如 minio-init）正常退出（exit code 0）。
# ---------------------------------------------------------------------------
wait_for_exit() {
    local service="$1"
    local timeout_s="${2:-60}"
    local elapsed=0

    log_info "等待 ${service} 完成（最多 ${timeout_s}s）..."

    while true; do
        local ps_out
        ps_out="$(docker compose -f "${COMPOSE_FILE}" ps "${service}" 2>/dev/null || true)"

        # "Exited (0)" 或 "exited (0)" 均匹配
        if echo "${ps_out}" | grep -qiE "Exited \(0\)|exited \(0\)"; then
            log_info "${service} 已正常退出（${elapsed}s）"
            return 0
        fi

        if [[ ${elapsed} -ge ${timeout_s} ]]; then
            log_error "${service} 在 ${timeout_s}s 内未正常退出"
            log_error "当前 ps 输出："
            echo "${ps_out}" >&2
            return 2
        fi

        sleep 2
        elapsed=$((elapsed + 2))
    done
}
