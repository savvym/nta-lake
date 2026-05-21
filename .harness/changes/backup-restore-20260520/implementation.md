---
change_id: backup-restore-20260520
phase: implementation
status: done
authored_at: 2026-05-21T16:30:00Z
author: sonnet-implementer
model_used: sonnet
branch: change/backup-restore-20260520
base_commit: 18db6be
head_commit: (see commit below)
pr_url: n/a
---

# Implementation：backup-restore bronze CAS (W4-10)

## 改动文件清单

| 路径 | 类型 | 一句话说明 |
|---|---|---|
| `scripts/backup_bronze.sh` | new | 主 backup 脚本；mc cp + tar -czf；BACKUP_OK sentinel |
| `scripts/restore_bronze.sh` | new | 主 restore 脚本；tar -xzf + mc cp；RESTORE_OK sentinel |
| `scripts/lib/backup_helpers.sh` | new | 共享函数库（require_alias / bucket_exists / count_objects） |
| `apps/api/tests/test_backup_restore_smoke.py` | new | env-gated smoke test（boto3 + subprocess round-trip） |
| `.harness/changes/backup-restore-20260520/implementation.md` | edit | Phase 2 实现记录（本文件） |

## 脚本实现说明

### scripts/lib/backup_helpers.sh（51 行）

三个函数：

- `require_alias(alias)`：先 `command -v mc` 检查 mc 是否安装，再 `mc alias list | grep -q "^${alias}"` 检查 alias 已配置。缺任一则 exit 64 并输出安装 / 配置提示。
- `bucket_exists(alias, bucket)`：`mc ls "${alias}/${bucket}"` → 返回 0/1，stdout/stderr 全静默。
- `count_objects(alias, bucket)`：`mc ls --recursive ... | wc -l | tr -d ' '`；空 bucket 输出 "0"。

文件不设 exec bit（仅 source 引入，与 integration_helpers.sh 同模式）。

### scripts/backup_bronze.sh（101 行）

关键 shell 惯用法：

- `set -euo pipefail` + `trap 'rm -rf "${tmp}"' EXIT`：任何子命令失败立即终止并清理临时目录。
- 临时目录：`out_dir/.tmp_<utc_ts>`，UTC ISO8601 戳，多次并发不冲突。
- `mc cp --recursive "${mc_alias}/${bucket}" "${tmp}/"`：拉到本地 `tmp/<bucket>/` 子目录。
- tar：`cd "${tmp}" && tar -czf "${tarball}" "${bucket}"`，相对路径打包，restore 解压后目录结构与 bucket 名对齐。
- 输出：`BACKUP_OK <tarball_abs_path> <size_bytes> <object_count>`，grep-friendly。
- 退码：0 OK / 64 usage / 2 mc-or-bucket / 3 tar。

### scripts/restore_bronze.sh（116 行）

关键设计：

- `mc mb -p`：`--parents` 语义，bucket 不存在时静默创建，存在时 no-op。
- 非空 bucket 保护：`count_objects > 0 && !force` → `RESTORE_REFUSED bucket_not_empty` + exit 4，区别于 mc 错误 exit 2。
- `tar -xzf "${tarball}" -C "${tmp}"`；解出为 `tmp/<bucket>/sha256/...`。
- `mc cp --recursive "${tmp}/${bucket}/" "${mc_alias}/${bucket}/"`；末尾 slash 确保只上传目录内容。
- 退码：0 / 64 usage / 2 mc / 3 tar / 4 refused。

### smoke test 设计（116 行）

- `pytestmark = pytest.mark.skipif(not DATAPLAT_MINIO_ENDPOINT, ...)`：env gate，无 MinIO 时整模块 SKIP（与 W4-6 同模式）。
- 测试 bucket 独立：`dataplat-blobs-test-backup` / `dataplat-blobs-test-restore`，不污染生产 / dev `dataplat-blobs`。
- boto3 client 读 `DATAPLAT_MINIO_ENDPOINT` / `DATAPLAT_MINIO_ACCESS_KEY` / `DATAPLAT_MINIO_SECRET_KEY`。
- `repo_root = Path(__file__).parent.parent.parent.parent`：从 apps/api/tests/ 向上四级到仓库根，定位 scripts/。
- `try/finally` 保证清理，即使断言失败。
- tarball 路径从 `BACKUP_OK` 输出行 split()[1] 解析，不假设文件名。

## 测试通过证据

### AC-2 bash -n lint

```
$ bash -n scripts/backup_bronze.sh && bash -n scripts/restore_bronze.sh && bash -n scripts/lib/backup_helpers.sh && echo "ALL PASS"
ALL PASS
```

### AC-3 --help grep

```
$ bash scripts/backup_bronze.sh --help 2>&1 | grep -qE 'out_dir.*--bucket' && echo PASS
PASS

$ bash scripts/restore_bronze.sh --help 2>&1 | grep -qE 'tarball.*--bucket' && echo PASS
PASS
```

### AC-1 exec bits + sentinels

```
$ test -x scripts/backup_bronze.sh && test -x scripts/restore_bronze.sh && echo "exec bits PASS"
exec bits PASS

$ grep -q 'BACKUP_OK' scripts/backup_bronze.sh && grep -q 'RESTORE_OK' scripts/restore_bronze.sh && echo "sentinels PASS"
sentinels PASS
```

### AC-4 pytest（env 缺位，SKIP=PASS）

```
$ cd apps/api && uv run pytest -x -q 2>&1 | tail -3
51 passed, 132 skipped in 1.88s
```

新 smoke test `test_backup_restore_smoke.py::test_backup_restore_roundtrip` 在 SKIP 列表中（env 缺位）。全套 51 passed，无回归。

## 偏离 design.md

无偏离。

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验 PR。
