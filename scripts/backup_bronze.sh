#!/usr/bin/env bash
# scripts/backup_bronze.sh
#
# 用法（Usage）：
#   bash scripts/backup_bronze.sh <out_dir> [--bucket NAME] [--minio-alias ALIAS]
#
# 参数：
#   out_dir          本地输出目录（tarball 写入此目录）
#   --bucket NAME    MinIO bucket 名（默认：dataplat-blobs）
#   --minio-alias    mc alias 名（默认：local）
#   --help           打印此帮助
#
# 退码语义（sysexits.h）：
#   0   成功；stdout 输出 BACKUP_OK <tarball_path> <size_bytes> <object_count>
#  64   用法错误（EX_USAGE）
#   2   mc / bucket 错误（EX_MC）
#   3   tar 错误（EX_TAR）
#
# 输出约定：
#   成功：BACKUP_OK <tarball_abs_path> <size_bytes> <object_count>
#
# 注：脚本依赖 mc（MinIO Client）；缺则 exit 64 并提示安装方式。

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
用法：bash scripts/backup_bronze.sh <out_dir> [--bucket NAME] [--minio-alias ALIAS]

参数：
  out_dir          本地输出目录（tarball 写入此目录）
  --bucket NAME    MinIO bucket 名（默认：dataplat-blobs）
  --minio-alias    mc alias 名（默认：local）
  --help           打印此帮助

退码语义：
  0   成功；stdout 输出 BACKUP_OK <tarball_path> <size_bytes> <object_count>
 64   用法错误
  2   mc / bucket 错误
  3   tar 错误

示例：
  bash scripts/backup_bronze.sh /tmp/backups
  bash scripts/backup_bronze.sh /tmp/backups --bucket my-bucket --minio-alias prod
EOF
}

# ---------------------------------------------------------------------------
# 参数解析
# ---------------------------------------------------------------------------
out_dir=""
bucket="${DEFAULT_BUCKET}"
mc_alias="${DEFAULT_ALIAS}"

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
            [[ $# -lt 2 ]] && { echo "[backup] --bucket 需要参数" >&2; exit 64; }
            bucket="$2"; shift 2
            ;;
        --minio-alias)
            [[ $# -lt 2 ]] && { echo "[backup] --minio-alias 需要参数" >&2; exit 64; }
            mc_alias="$2"; shift 2
            ;;
        -*)
            echo "[backup] 未知选项：$1" >&2; exit 64
            ;;
        *)
            if [[ -z "${out_dir}" ]]; then
                out_dir="$1"; shift
            else
                echo "[backup] 多余的位置参数：$1" >&2; exit 64
            fi
            ;;
    esac
done

if [[ -z "${out_dir}" ]]; then
    echo "[backup] 缺少必需参数 out_dir" >&2
    usage >&2
    exit 64
fi

# ---------------------------------------------------------------------------
# 校验 out_dir
# ---------------------------------------------------------------------------
if [[ ! -d "${out_dir}" ]]; then
    echo "[backup] out_dir 不存在：${out_dir}" >&2
    exit 64
fi
if [[ ! -w "${out_dir}" ]]; then
    echo "[backup] out_dir 不可写：${out_dir}" >&2
    exit 64
fi

# ---------------------------------------------------------------------------
# 校验 mc alias
# ---------------------------------------------------------------------------
require_alias "${mc_alias}"

# ---------------------------------------------------------------------------
# 校验 bucket 存在
# ---------------------------------------------------------------------------
if ! bucket_exists "${mc_alias}" "${bucket}"; then
    echo "[backup] bucket 不存在：${mc_alias}/${bucket}" >&2
    exit 2
fi

# ---------------------------------------------------------------------------
# 创建临时目录（trap 保证清理）
# ---------------------------------------------------------------------------
ts="$(date -u +%Y%m%dT%H%M%SZ)"
tmp="${out_dir}/.tmp_${ts}"
mkdir -p "${tmp}"

trap 'rm -rf "${tmp}"' EXIT

# ---------------------------------------------------------------------------
# mc cp --recursive → tmp
# ---------------------------------------------------------------------------
if ! mc cp --recursive "${mc_alias}/${bucket}" "${tmp}/"; then
    echo "[backup] mc cp 失败" >&2
    exit 2
fi

# ---------------------------------------------------------------------------
# tar → out_dir
# ---------------------------------------------------------------------------
tarball="${out_dir}/bronze-${ts}.tar.gz"
(
    cd "${tmp}"
    if ! tar -czf "${tarball}" "${bucket}"; then
        echo "[backup] tar 失败" >&2
        exit 3
    fi
)

# ---------------------------------------------------------------------------
# 统计
# ---------------------------------------------------------------------------
object_count="$(count_objects "${mc_alias}" "${bucket}")"
size_bytes="$(wc -c < "${tarball}" | tr -d ' ')"

echo "BACKUP_OK ${tarball} ${size_bytes} ${object_count}"
