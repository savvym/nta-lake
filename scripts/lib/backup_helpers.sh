#!/usr/bin/env bash
# scripts/lib/backup_helpers.sh
#
# 共享工具函数，由 backup_bronze.sh / restore_bronze.sh source 引入。
# 不直接执行；不需要 exec bit。
#
# 函数：
#   require_alias  <alias>          -- alias 未配置则 exit 64
#   bucket_exists  <alias> <bucket> -- bucket 存在返回 0；否则返回 1
#   count_objects  <alias> <bucket> -- 输出 bucket 内对象数（整数）

# ---------------------------------------------------------------------------
# require_alias <alias>
#
# 检查 mc alias 是否已配置；未配置则打印提示并以 exit 64 终止调用进程。
# ---------------------------------------------------------------------------
require_alias() {
    local alias="$1"

    if ! command -v mc >/dev/null 2>&1; then
        echo "[backup] mc 二进制未找到；请安装 MinIO Client：" >&2
        echo "  Linux:  apt-get install minio-mc  或  wget https://dl.min.io/client/mc/release/linux-amd64/mc" >&2
        echo "  macOS:  brew install minio-mc" >&2
        exit 64
    fi

    if ! mc alias list 2>/dev/null | grep -q "^${alias}"; then
        echo "[backup] mc alias '${alias}' 未配置；请先运行：" >&2
        echo "  mc alias set ${alias} <endpoint_url> <access_key> <secret_key>" >&2
        exit 64
    fi
}

# ---------------------------------------------------------------------------
# bucket_exists <alias> <bucket>
#
# 返回 0（bucket 存在）或 1（不存在）。
# ---------------------------------------------------------------------------
bucket_exists() {
    local alias="$1"
    local bucket="$2"
    mc ls "${alias}/${bucket}" >/dev/null 2>&1
}

# ---------------------------------------------------------------------------
# count_objects <alias> <bucket>
#
# 输出 bucket 内对象数（整数，0 表示空）。
# ---------------------------------------------------------------------------
count_objects() {
    local alias="$1"
    local bucket="$2"
    mc ls --recursive "${alias}/${bucket}" 2>/dev/null | wc -l | tr -d ' '
}
