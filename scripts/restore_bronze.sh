#!/usr/bin/env bash
# scripts/restore_bronze.sh
#
# 用法（Usage）：
#   bash scripts/restore_bronze.sh <tarball> [--bucket NAME] [--minio-alias ALIAS] [--force]
#
# 参数：
#   tarball          backup_bronze.sh 生成的 bronze-*.tar.gz 路径
#   --bucket NAME    目标 MinIO bucket 名（默认：dataplat-blobs）
#   --minio-alias    mc alias 名（默认：local）
#   --force          强制覆盖非空 bucket（默认：非空时拒绝）
#   --help           打印此帮助
#
# 退码语义（sysexits.h）：
#   0   成功；stdout 输出 RESTORE_OK <object_count>
#  64   用法错误（EX_USAGE）
#   2   mc 错误（EX_MC）
#   3   tar 错误（EX_TAR）
#   4   拒绝（bucket 非空且未 --force）（EX_REFUSED）
#
# 输出约定：
#   成功：RESTORE_OK <object_count>
#   拒绝：RESTORE_REFUSED bucket_not_empty

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# shellcheck source=scripts/lib/backup_helpers.sh
source "${REPO_ROOT}/scripts/lib/backup_helpers.sh"

# ---------------------------------------------------------------------------
# 常量默认值
# ---------------------------------------------------------------------------
DEFAULT_BUCKET="dataplat-blobs"
DEFAULT_ALIAS="local"

# ---------------------------------------------------------------------------
# usage
# ---------------------------------------------------------------------------
usage() {
    cat <<'EOF'
用法：bash scripts/restore_bronze.sh <tarball> [--bucket NAME] [--minio-alias ALIAS] [--force]

参数：
  tarball          backup_bronze.sh 生成的 bronze-*.tar.gz 路径
  --bucket NAME    目标 MinIO bucket 名（默认：dataplat-blobs）
  --minio-alias    mc alias 名（默认：local）
  --force          强制覆盖非空 bucket（默认：非空时拒绝）
  --help           打印此帮助

退码语义：
  0   成功；stdout 输出 RESTORE_OK <object_count>
 64   用法错误
  2   mc 错误
  3   tar 错误
  4   拒绝（bucket 非空且未 --force）

示例：
  bash scripts/restore_bronze.sh /tmp/backups/bronze-20260521T120000Z.tar.gz
  bash scripts/restore_bronze.sh /tmp/backups/bronze-20260521T120000Z.tar.gz --bucket staging-blobs --force
EOF
}

# ---------------------------------------------------------------------------
# 参数解析
# ---------------------------------------------------------------------------
tarball=""
bucket="${DEFAULT_BUCKET}"
mc_alias="${DEFAULT_ALIAS}"
force=0

if [[ $# -eq 0 ]]; then
    usage >&2
    exit 64
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h)
            usage
            exit 0
            ;;
        --bucket)
            [[ $# -lt 2 ]] && { echo "[restore] --bucket 需要参数" >&2; exit 64; }
            bucket="$2"; shift 2
            ;;
        --minio-alias)
            [[ $# -lt 2 ]] && { echo "[restore] --minio-alias 需要参数" >&2; exit 64; }
            mc_alias="$2"; shift 2
            ;;
        --force)
            force=1; shift
            ;;
        -*)
            echo "[restore] 未知选项：$1" >&2; exit 64
            ;;
        *)
            if [[ -z "${tarball}" ]]; then
                tarball="$1"; shift
            else
                echo "[restore] 多余的位置参数：$1" >&2; exit 64
            fi
            ;;
    esac
done

if [[ -z "${tarball}" ]]; then
    echo "[restore] 缺少必需参数 tarball" >&2
    usage >&2
    exit 64
fi

# ---------------------------------------------------------------------------
# 校验 tarball 存在
# ---------------------------------------------------------------------------
if [[ ! -f "${tarball}" ]]; then
    echo "[restore] tarball 不存在：${tarball}" >&2
    exit 64
fi

# ---------------------------------------------------------------------------
# 校验 mc alias
# ---------------------------------------------------------------------------
require_alias "${mc_alias}"

# ---------------------------------------------------------------------------
# 确保 bucket 存在（不存在则创建）
# ---------------------------------------------------------------------------
if ! bucket_exists "${mc_alias}" "${bucket}"; then
    if ! mc mb -p "${mc_alias}/${bucket}" >/dev/null 2>&1; then
        echo "[restore] 创建 bucket 失败：${mc_alias}/${bucket}" >&2
        exit 2
    fi
fi

# ---------------------------------------------------------------------------
# 非空 bucket 保护
# ---------------------------------------------------------------------------
obj_count="$(count_objects "${mc_alias}" "${bucket}")"
if [[ "${obj_count}" -gt 0 ]] && [[ "${force}" -eq 0 ]]; then
    echo "RESTORE_REFUSED bucket_not_empty"
    exit 4
fi

# ---------------------------------------------------------------------------
# 创建临时目录（trap 保证清理）
# ---------------------------------------------------------------------------
ts="$(date -u +%Y%m%dT%H%M%SZ)"
tmp_base="$(dirname "${tarball}")"
tmp="${tmp_base}/.tmp_restore_${ts}"
mkdir -p "${tmp}"

trap 'rm -rf "${tmp}"' EXIT

# ---------------------------------------------------------------------------
# tar 解压
# ---------------------------------------------------------------------------
if ! tar -xzf "${tarball}" -C "${tmp}"; then
    echo "[restore] tar 解压失败：${tarball}" >&2
    exit 3
fi

# ---------------------------------------------------------------------------
# mc cp --recursive → bucket
# ---------------------------------------------------------------------------
if ! mc cp --recursive "${tmp}/${bucket}/" "${mc_alias}/${bucket}/"; then
    echo "[restore] mc cp 失败" >&2
    exit 2
fi

# ---------------------------------------------------------------------------
# 统计并输出
# ---------------------------------------------------------------------------
restored_count="$(count_objects "${mc_alias}" "${bucket}")"
echo "RESTORE_OK ${restored_count}"
