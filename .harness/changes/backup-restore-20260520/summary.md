---
change_id: backup-restore-20260520
title: backup/restore bronze CAS (W4-10)
owner: application-owner-agent
started_at: 2026-05-21T04:33:49Z
phase: merged
status: done
last_updated: 2026-05-21T18:30:00Z
related_changes: [integration-test-framework-20260520]
---

# Summary

## 一句话目标

加两条 bash 脚本：`backup_bronze.sh <out_dir>` 把 MinIO `dataplat-blobs` bucket 流式打 tar.gz；`restore_bronze.sh <tarball>` 反向上传。

## 范围摘要

- **In scope**：
  - `scripts/backup_bronze.sh`（mc cp --recursive → tar -czf；sentinel `BACKUP_OK`）
  - `scripts/restore_bronze.sh`（tar -xzf → mc cp；非空 bucket 拒 restore 除非 --force；sentinel `RESTORE_OK`）
  - `scripts/lib/backup_helpers.sh`（require_alias / bucket_exists / count_objects）
  - `apps/api/tests/test_backup_restore_smoke.py`（env-gated boto3 + subprocess roundtrip）
- **Out of scope**：PG backup / incremental / 云直传 / 加密 / cron / web UI / Wave1-W4-9 已 merge 产物

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (self) | approved | — | e30c4ba | [design.md](design.md) |
| Phase 2 Implementation | sonnet | done | — | 9866c9d | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | approved | APPROVED | 599d3d8 | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 | bash 而非 Python | mc + tar 是核心；调用 < 30 行；Python wrapper 过度 | design.md §决策 1 |
| 2026-05-21 | 依赖 mc 而非 boto3 直调 S3 | mc 是 MinIO 官方 CLI + 已是 docker-compose 依赖 | design.md §决策 2 |
| 2026-05-21 | 不备份 Postgres | DB 是 metadata 不是 truth；alembic + 业务可重建 | design.md §决策 6 |
| 2026-05-21 | 非空 bucket 默认拒 restore | 防误覆盖；--force 显式 opt-in | design.md §决策 4 |

## 当前阻塞

无

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| NICE TO HAVE | backup_bronze.sh:153-159 子 shell `exit 3` 降级为 1 | follow-up `backup-bronze-exit-code-polish-*` |
| follow-up | Postgres backup（pg_dump / WAL / PITR） | `backup-pg-*` |
| follow-up | 增量 backup（diff 上次 manifest） | `backup-bronze-incremental-*` |
| follow-up | gpg / age 加密 tarball | `backup-bronze-encrypt-*` |
| follow-up | cron / systemd timer 定时备份 | `backup-bronze-cron-*` |
| follow-up | mc mirror 直接到云上 S3 | `backup-bronze-s3-direct-*` |
| follow-up | UI 触发 backup + 列历史 tarball | `web-backup-trigger-*` |
| follow-up | full DR 演练（删整个 MinIO → restore 验业务可用） | `backup-disaster-recovery-*` |

## 交付

- Branch：`change/backup-restore-20260520`（已删，merged）
- Merge commit：`1b6ea8b`
- 关闭时间：2026-05-21T18:30:00Z

## 复盘

- **顺利**：v3 mini-design 端到端 < 15 min（design 13min + sonnet impl ~5min + opus verify ~3min）；4/4 AC PASS；0 issue。
- **意外收获**：W4-6 `scripts/lib/integration_helpers.sh` 模式被 W4-10 helper lib 完全复用（require_alias 同名同语义），证明运维脚本骨架已稳定。
- **Wave 4 收官**：10/10 全 APPROVED；0-issue 连续 24 次（W1-4..W4-10）；整个 27-change rollout 全部完成。
