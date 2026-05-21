---
change_id: backup-restore-20260520
phase: design
status: approved
authored_at: 2026-05-21T16:00:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：backup-restore bronze CAS (W4-10，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

加两条 bash 脚本：`backup_bronze.sh <out_dir>` 把 MinIO `dataplat-blobs` bucket 流式打 tar.gz；`restore_bronze.sh <tarball>` 反向上传。

## 背景

W4-10 是 Wave 4 收尾——基础设施工程化。dataplat 把所有不可变 Bronze blob（含 silver JSONL / loader 中间产物 / adapter raw 文件）写入 MinIO `dataplat-blobs` bucket，按 CAS（content-addressable storage）以 sha256 命名。当前**没有 backup 机制**：

1. user / 运维**无法离机备份**——MinIO volume 损坏 → 全量 Bronze 丢失 → 所有 silver / gold snapshot 失效（CAS 拉不回 blob）
2. **环境迁移痛**：dev / staging / prod 之间复制数据需手工 `mc mirror`，缺脚本化
3. **harness 流程 demo** 阶段没法把 user 的"3 个 PDF 测试集"序列化为可分发的 fixture

W4-10 落两条最小化 bash 脚本（不引入 Python / 不引入 backup framework）：
- `scripts/backup_bronze.sh <out_dir> [--bucket NAME]`：调 `mc cp --recursive` 把 bucket 拉到本地 → `tar -czf`
- `scripts/restore_bronze.sh <tarball> [--bucket NAME]`：`tar -xzf` → `mc cp --recursive` 上传

**关键约束**：
- 只备份 bronze（MinIO blob CAS）；**不备份 Postgres**（DB schema / commits / refs 已被 alembic + 业务代码定义，可重建；Postgres backup follow-up `backup-pg-*`）
- 不做 incremental / delta backup（CAS sha256 命名天然 dedup；full snapshot 简单可靠；增量留 follow-up）
- 不做云上 S3 / GCS 直接备份（mc 已可指向 S3-compatible endpoint；用户改 mc alias 即可；脚本只做 local tarball）
- 不做加密 / 签名（local tarball；如需加密 user 套 gpg；留 follow-up `backup-bronze-encrypt-*`）

## 范围

In scope：

- `scripts/backup_bronze.sh`（新，~70 行 bash）：
  - 用法：`bash scripts/backup_bronze.sh <out_dir> [--bucket NAME] [--minio-alias ALIAS]`
  - 默认 bucket: `dataplat-blobs`；默认 mc alias: `local`（与 docker-compose.dev.yml minio-init 创建的一致）
  - 流程：
    1. 校验 `out_dir` 存在且可写
    2. 校验 mc alias 已配置（`mc alias list | grep -q "^<alias>"`；失败 → exit 64 with usage 提示）
    3. 校验 bucket 存在（`mc ls <alias>/<bucket>`；不存在 → exit 2）
    4. 创建临时目录 `out_dir/.tmp_<timestamp>`
    5. `mc cp --recursive <alias>/<bucket> <tmp>/<bucket>`
    6. 进 `out_dir`，`tar -czf bronze-<timestamp>.tar.gz <bucket>`（相对路径打包，restore 时落到 bucket 根）
    7. 删临时目录
    8. 打印 `BACKUP_OK <tarball_path> <size_bytes> <object_count>`
  - 退码：0 OK / 64 usage 错 / 2 mc / bucket 错 / 3 tar 错
  - `set -euo pipefail` + `trap` 清理临时目录
- `scripts/restore_bronze.sh`（新，~70 行 bash）：
  - 用法：`bash scripts/restore_bronze.sh <tarball> [--bucket NAME] [--minio-alias ALIAS] [--force]`
  - 默认同 backup；`--force` 跳过"bucket 非空"确认
  - 流程：
    1. 校验 tarball 存在
    2. 校验 mc alias / bucket
    3. 如 bucket 非空且未 `--force` → exit 2 with `RESTORE_REFUSED bucket_not_empty`（防误覆盖；mc cp 默认 overwrite 同名 key OK，但用户应显式确认）
    4. 创建临时目录 → `tar -xzf <tarball> -C <tmp>`
    5. `mc cp --recursive <tmp>/<bucket> <alias>/<bucket>/`
    6. 删临时目录
    7. 打印 `RESTORE_OK <object_count>`
  - 退码：0 OK / 64 usage / 2 mc / 3 tar / 4 refused (bucket not empty without --force)
- `scripts/lib/backup_helpers.sh`（新，~30 行）：
  - `count_objects(alias, bucket) -> int`（`mc ls --recursive | wc -l`）
  - `bucket_exists(alias, bucket) -> 0|1`
  - `require_alias(alias)`（缺则 exit 64 with 提示 mc alias set）
- `apps/api/tests/test_backup_restore_smoke.py`（新，~30 行，env-gated 与 W4-6 smoke 同模式）：
  - `pytestmark = pytest.mark.skipif(not DATAPLAT_MINIO_ENDPOINT)`
  - 1 个 behavioral test：
    - 用 boto3 client（已是 minio_store 依赖）`put_object` 3 个 fake blob 到 `dataplat-blobs-test-backup` bucket
    - subprocess 跑 `scripts/backup_bronze.sh ./tmp_dir --bucket dataplat-blobs-test-backup`
    - 断言 stdout 含 `BACKUP_OK` + tarball 存在 + tar -tzf 列出 3 个 file
    - subprocess 跑 `scripts/restore_bronze.sh <tarball> --bucket dataplat-blobs-test-restore --force`
    - 断言 stdout 含 `RESTORE_OK 3` + boto3 list_objects 在 restore bucket 看到 3 个 key
    - 清理：删 2 个 bucket + tmp_dir
- `scripts/integration_test.sh`（小改）：**不动**——backup/restore 不在 integration_test 主链路（独立运维脚本）；不污染 W4-6 主脚本

Out of scope：

- **不**做 Postgres backup / restore：alembic + 业务代码可重建 schema；DB 是 metadata 不是 truth；留 follow-up `backup-pg-*`
- **不**做 incremental / delta backup：CAS 天然 dedup；full snapshot 简单；留 follow-up `backup-bronze-incremental-*`
- **不**做云上 S3 / GCS 直接备份：mc alias 切换即可；用户运维层面解决
- **不**做加密 / 签名 tarball：用户套 gpg；follow-up `backup-bronze-encrypt-*`
- **不**做定时任务 / cron：脚本只是手动触发；cron 接 follow-up `backup-bronze-cron-*`
- **不**做进度条：tarball / mc 自有输出；用户 `tail -f` 看
- **不**做并行 / multipart upload 优化：mc 内部已是 multipart；wrapper 不优化
- **不**接 web UI（backup / restore 按钮）：运维操作不放 UI；follow-up `web-backup-trigger-*`
- **不**改 W1..W4-9 已 merge 产物
- **不**做 alembic migration / DB schema
- **不**做 manifest.yaml / dataset-card.yaml（永不做清单）

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | 两条脚本可执行 + usage 含 `BACKUP_OK` / `RESTORE_OK` sentinel | `test -x scripts/backup_bronze.sh && test -x scripts/restore_bronze.sh && grep -q 'BACKUP_OK' scripts/backup_bronze.sh && grep -q 'RESTORE_OK' scripts/restore_bronze.sh` | 0 退出码 |
| AC-2 | static | bash 语法 lint | `bash -n scripts/backup_bronze.sh && bash -n scripts/restore_bronze.sh && bash -n scripts/lib/backup_helpers.sh` | 0 退出码 |
| AC-3 | static | usage --help 含基本字段 | `bash scripts/backup_bronze.sh --help 2>&1 \| grep -qE 'out_dir.*--bucket' && bash scripts/restore_bronze.sh --help 2>&1 \| grep -qE 'tarball.*--bucket'` | 命中 |
| AC-4 | behavioral | env-gated smoke：put 3 blob → backup → restore → 验 3 blob 在新 bucket | `cd apps/api && uv run pytest tests/test_backup_restore_smoke.py -x -q` | 1 passed (env 就位) / skipped (env 缺) |

> 注：AC-4 在 docker / MinIO 缺位时 SKIP；reviewer / user 跑 `bash scripts/integration_test.sh up-keep` 后再单跑此 test 看真行为；与 W4-6 同 SKIP=PASS 模式。

## 决策

1. **bash 脚本而非 Python**：mc / tar 是核心；bash 调外部工具 < 30 行；Python wrapper 增 boto3 / asyncio / argparse 复杂度过度。
2. **依赖 mc 而非 boto3 直接调 S3 API**：mc 是 MinIO 官方 CLI；`mc cp --recursive` 一键 mirror；boto3 需手写 list / get / put 循环 50+ 行；mc 已是 docker-compose minio-init 依赖（不增运行时依赖）。
3. **CAS 天然 dedup → full snapshot 简单**：同一 blob_sha 只占 1 份；重复内容不放大；增量 backup 复杂度不必要。
4. **bucket 非空时拒 restore（除非 --force）**：防误覆盖；mc cp 默认 overwrite 同 key 但不会删 extra key（restore 上的 + 原有的混合）；显式 --force 让用户确认意图。
5. **tarball 命名 `bronze-<timestamp>.tar.gz`**：UTC ISO（`date -u +%Y%m%dT%H%M%SZ`）；用户多次备份不冲突；user 自己管命名约定。
6. **不备份 Postgres**：Postgres 存 commits / refs / repos 元数据；dataplat 设计上 alembic schema + 业务再现可重建（git-like：blob is the truth，DB is index）；data integrity 关键是 blob 不丢，pg 可重建。pg backup 独立 change（涉及 pg_dump / point-in-time recovery / WAL）。
7. **smoke test 用 boto3 直接 put / list 验 backup-restore round-trip**：subprocess 跑 shell 脚本 + boto3 验 state；与 W4-6 smoke test 同模式（test_integration_smoke 用 httpx ASGI）。
8. **bucket 名 `dataplat-blobs`**：与 docker-compose.dev.yml minio-init `mc mb -p local/dataplat-blobs` 完全一致；user 改名时改 docker-compose + 脚本 default 同步。
9. **退码语义统一**：sysexits-style（与 W4-6 integration_test.sh 一致）；usage 64 / 业务错 2 / tar 错 3 / refused 4。
10. **sentinel 字符串 `BACKUP_OK` / `RESTORE_OK <count>`**：与 W4-6 `INTEGRATION_OK` 同模式；grep 友好；非业务输出不冲突。
11. **scripts/lib/backup_helpers.sh 抽取**：与 W4-6 `scripts/lib/integration_helpers.sh` 同模式；共享逻辑（require_alias / count_objects）；不污染主脚本。
12. **smoke test 用独立 test bucket**：避免污染生产 / dev `dataplat-blobs`；test setUp 创建 / tearDown 删 `dataplat-blobs-test-backup` + `dataplat-blobs-test-restore`。

## 风险

| 风险 | 缓解 |
|---|---|
| mc 二进制在 user 机器未安装 | usage 检查 `command -v mc`；缺则 exit 64 with 提示 `brew install minio-mc` / `apt-get install minio-mc` |
| tar 在 macOS bsdtar vs Linux gnu-tar 行为差异 | 用基础 `tar -czf / -xzf -C` 参数（共通子集）；不用 GNU-only flag（如 `--owner=0`）|
| backup 大 bucket 时 mc cp 时长无上限 | 接受；运维操作；user 决定何时跑；不加 timeout |
| restore 到错 bucket 误覆盖 | 默认拒 non-empty；--force 显式 opt-in |
| smoke test 在 CI / dev 机器 boto3 不通 | env-gated SKIP；与 W4-6 同模式 |
| 临时目录 `out_dir/.tmp_<ts>` 在异常中断未清理 | `trap 'rm -rf "$tmp"' EXIT` 兜底 |
| tarball 体积大（几 GB） | 接受；CAS blob 已 sha256-dedup；gzip 对二进制 PDF / docx 压缩比 ~10%；用户提供足够磁盘 |
| mc alias 指向云上 S3 时 cp recursive 时长 / 流量费 | 接受；user 选 alias = 选成本；wrapper 不限速 |
| Wave 4 收尾不该引入新依赖 | mc 已是 docker-compose 依赖；boto3 已是 apps/api 依赖；零新增 |
| W4-6 integration_test.sh 与 W4-10 脚本冲突 | 不冲突；W4-10 是独立运维脚本（不在 integration_test 链路中调用）|

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `docker/docker-compose.dev.yml`（minio service / bucket name）
  - `apps/api/dataplat_api/storage/minio_store.py`（boto3 client / bucket 命名约定）
  - `scripts/lib/integration_helpers.sh`（结构参考；不复用）
  - `scripts/integration_test.sh`（结构参考；不动）
- 应当不动：
  - `packages/core/*`（运维脚本与 core 业务正交）
  - `apps/api/dataplat_api/*`（除 tests/test_backup_restore_smoke.py 新增）
  - W1..W4-9 已 merge 产物
- 引用的其他 change：W4-6（integration_test.sh 结构 / smoke test 模式）

## 关联 follow-up

- `backup-pg-*`：Postgres pg_dump / restore + WAL 流式
- `backup-bronze-incremental-*`：增量 backup（diff 上次 manifest）
- `backup-bronze-encrypt-*`：gpg / age 加密 tarball
- `backup-bronze-cron-*`：定时备份 cron / systemd timer
- `backup-bronze-s3-direct-*`：直接 mc mirror 到云上 S3，不本地 tar
- `web-backup-trigger-*`：UI 触发 backup + 列历史 tarball
- `backup-disaster-recovery-*`：full DR 演练（删整个 MinIO → restore 验业务可用）
