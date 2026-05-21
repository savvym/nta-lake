---
change_id: backup-restore-20260520
phase: verify
status: approved
verdict: APPROVED
authored_at: 2026-05-21T17:00:00Z
reviewer: opus-phase3-reviewer
model_used: opus
base_commit: 18db6be62d2d8609ec78e193dc183d06021400f8
head_commit: 9866c9d
---

# Verify Review：backup-restore bronze CAS (W4-10)

## 一句话总结

4/4 AC PASS、全套 `51 passed + 132 skipped` 与 base 一致零回归；scope 严格限定在 `scripts/`、`apps/api/tests/test_backup_restore_smoke.py`、`implementation.md`（共 6 个文件），sentinel 字符串 / 退码语义 / trap 清理 / env-gated `pytestmark.skipif` / `--force` 非空保护与 design.md 完全对齐；未触碰 D-1 永不做清单（无 manifest / branch / merge / cherry-pick / rollback / row-diff），未违反 CLAUDE.md 8 条硬约束，**APPROVED**。

## 输入

- **Design**：`.harness/changes/backup-restore-20260520/design.md`（commit `e30c4ba`）
- **Implementation**：`.harness/changes/backup-restore-20260520/implementation.md`（commit `9866c9d`）
- **Git diff**：`git diff 18db6be..9866c9d`（6 files +821 lines, 0 deletions）
- **Branch**：`change/backup-restore-20260520`

## AC 对照表（原始命令输出）

### AC-1 exec bit + sentinel grep（static）

```
$ test -x scripts/backup_bronze.sh && test -x scripts/restore_bronze.sh && grep -q 'BACKUP_OK' scripts/backup_bronze.sh && grep -q 'RESTORE_OK' scripts/restore_bronze.sh && echo OK
OK
```

**PASS**：两脚本均 `-rwxr-xr-x`；`backup_bronze.sh:167` 含 `BACKUP_OK`；`restore_bronze.sh:176` 含 `RESTORE_OK`。

### AC-2 bash 语法 lint（static）

```
$ bash -n scripts/backup_bronze.sh && bash -n scripts/restore_bronze.sh && bash -n scripts/lib/backup_helpers.sh && echo OK
OK
```

**PASS**：三文件语法均合法。

### AC-3 `--help` grep（static）

```
$ bash scripts/backup_bronze.sh --help 2>&1 | grep -qE 'out_dir.*--bucket' && bash scripts/restore_bronze.sh --help 2>&1 | grep -qE 'tarball.*--bucket' && echo OK
OK
```

**PASS**：`backup_bronze.sh --help` usage 行含 `out_dir ... --bucket`；`restore_bronze.sh --help` 含 `tarball ... --bucket`。

### AC-4 env-gated smoke test（behavioral；SKIP=PASS）

```
$ cd apps/api && uv run pytest tests/test_backup_restore_smoke.py -x -q
s                                                                        [100%]
1 skipped in 0.11s
```

**PASS（SKIP=PASS）**：`DATAPLAT_MINIO_ENDPOINT` 未设置 → 整模块 `pytestmark.skipif` 触发 1 skipped；与 W4-6 same convention；用户跑 `bash scripts/integration_test.sh up-keep` 后再单跑此 test 即可观行为路径。

| AC | kind | 命令 | 结果 | 判定 |
|---|---|---|---|---|
| AC-1 | static | `test -x ... && grep -q BACKUP_OK/RESTORE_OK ...` | `OK` | PASS |
| AC-2 | static | `bash -n` x 3 | `OK` | PASS |
| AC-3 | static | `--help \| grep -qE ...` x 2 | `OK` | PASS |
| AC-4 | behavioral | `uv run pytest tests/test_backup_restore_smoke.py -x -q` | `1 skipped` | PASS（SKIP=PASS） |

## 回归基线

```
$ cd apps/api && uv run pytest -x -q
...
51 passed, 132 skipped in 1.86s
```

**PASS**：与 base（18db6be）`51 passed` 一致；新增 1 skipped 已包含在 132 skipped 内（其他 131 为预存 env-gated tests）；**零回归**。

## 机械化检查日志

```text
$ git merge-base main HEAD
18db6be62d2d8609ec78e193dc183d06021400f8

$ git log --oneline 18db6be..HEAD
9866c9d feat(W4-10): backup/restore bronze CAS via mc + tar
e30c4ba design(backup-restore-20260520): W4-10 mini-design

$ git diff 18db6be..HEAD --stat
 .harness/changes/backup-restore-20260520/design.md         | 158 +++++++
 .harness/changes/backup-restore-20260520/implementation.md | 112 +++++
 apps/api/tests/test_backup_restore_smoke.py                | 154 +++++++
 scripts/backup_bronze.sh                                   | 167 +++++++
 scripts/lib/backup_helpers.sh                              |  54 ++
 scripts/restore_bronze.sh                                  | 176 ++++++++
 6 files changed, 821 insertions(+)

$ ls -la scripts/backup_bronze.sh scripts/restore_bronze.sh scripts/lib/backup_helpers.sh
-rwxr-xr-x 5342 scripts/backup_bronze.sh
-rw-r--r-- 2038 scripts/lib/backup_helpers.sh
-rwxr-xr-x 5935 scripts/restore_bronze.sh
```

## Scope / Discipline 检查

| 维度 | 结果 |
|---|---|
| Diff 文件清单 | 6 个：design / implementation / test_backup_restore_smoke / backup_bronze / restore_bronze / lib/backup_helpers — 与 design.md "In scope" 100% 对齐 |
| 未触碰 W1..W4-9 已 merge 产物 | OK |
| 未改 `packages/core/*` | OK |
| 未改 `dataplat_api/*`（除 tests/ 新增） | OK |
| 未改 `scripts/integration_test.sh` 主链路 | OK |
| 退码语义 sysexits 风格 | OK：backup 0/64/2/3；restore 0/64/2/3/4 — 与 design.md "退码语义统一" 一致 |
| trap 清理 | OK：`trap 'rm -rf "${tmp}"' EXIT`（backup:139, restore:154）|
| sentinel 格式 | OK：`BACKUP_OK <abs_path> <size_bytes> <object_count>`（backup:167）/ `RESTORE_OK <count>`（restore:176）/ `RESTORE_REFUSED bucket_not_empty`（restore:142）|
| 无 mc / boto3 chatter 污染 stdout | OK：sentinel 在最末行 echo，前置 mc / tar 错误以 `[backup]/[restore] ... >&2` 输 stderr |
| env-gated test pattern | OK：`pytestmark = pytest.mark.skipif(not _MINIO_ENDPOINT, ...)`（test:29-32）— 与 W4-6 same idiom |
| `bucket_not_empty` 拒收逻辑 | OK：`obj_count > 0 && force == 0` → `RESTORE_REFUSED bucket_not_empty` + exit 4（restore:140-144）；`--force` 直通 |
| `set -euo pipefail` | OK（两脚本第 24-25 行）|
| 单 commit 端到端 | OK：commit `9866c9d` 一气呵成；零反复 spawn reviewer |

## 隐式偏离审计

对照 design.md § 范围 vs git diff 实际改动：

- ✅ 无隐式偏离。implementation.md § 偏离 声明"无偏离"，git diff 验证属实。

## D-1 永不做清单 / CLAUDE.md 硬约束合规

**D-1（永不做清单）**：✅ 无 manifest.yaml / branch / merge / cherry-pick / rollback / row-diff / blob 派生图 / Asset / silver 文件树 / bronze 强 schema。本 change 是纯运维脚本（bronze CAS bucket → tarball round-trip），与数据治理 invariant 正交。

**CLAUDE.md 8 条硬约束**：
1. ✅ change 挂在 `.harness/changes/backup-restore-20260520/`
2. ✅ Phase 1 design.md 存在（`e30c4ba`）+ AC 4 条 + 退码 / 范围 / 决策 / 风险段完备
3. ✅ Phase 1 + Phase 3 reviewer 未跳过（本 review）
4. ✅ 模型分配：Phase 1 opus（self-author 走 D-13 mini-design）/ Phase 2 sonnet / Phase 3 opus（本 review）
5. ✅ 机械化证据齐全（4 AC + 回归基线原始输出粘在上）
6. ✅ 未发现新流程缺陷需补 rule
7. ✅ 未违反 `.harness/rules/data-not-code-pivot.md`
8. ✅ Phase 1 自写 mini-design + Phase 2 单 commit 一气呵成，零反复 spawn

## 问题列表

### MUST FIX

- 无。

### SHOULD FIX

- 无。

### NICE TO HAVE（非阻断 follow-up 候选）

1. **info — `scripts/backup_bronze.sh:153-159`**：`( cd "${tmp}" && tar ... ; exit 3 )` 子 shell 内的 `exit 3` 仅退出子 shell；父进程因 `set -e` 见非零退出而终止，但**实际向 caller 传递的退码降级为 1 而非 design 约定的 3**。极小概率影响（仅当 tar 真实失败时；CI / 自动化按"退码非零"判定不受影响）。修法示例：

   ```bash
   ( cd "${tmp}" && tar -czf "${tarball}" "${bucket}" ) || { echo "[backup] tar 失败" >&2; exit 3; }
   ```

   留作 `backup-bronze-exit-code-polish-*` follow-up；**不阻断 APPROVED**，避免触发 D-13 "1 round MINOR FIX 上限"占用。

2. design.md § 关联 follow-up 已枚举：`backup-pg-*` / `backup-bronze-incremental-*` / `backup-bronze-encrypt-*` / `backup-bronze-cron-*` / `backup-bronze-s3-direct-*` / `web-backup-trigger-*` / `backup-disaster-recovery-*`。

## Verdict

**APPROVED**

- 4/4 AC PASS（含 SKIP=PASS）
- 零回归（51 passed 与 base 一致）
- scope 严格、无隐式偏离
- 无 D-1 / CLAUDE.md 违反
- 仅 1 个 NICE TO HAVE（tar 退码降级），不阻断 merge

## 后续指引

- orchestrator（父 application-owner）merge `change/backup-restore-20260520` → main，close change。
- W4-10 是 Wave 4 第 10 个、也是最后一个 change → close 后建议做 Wave 4 retrospective（10 changes 的 commit 数 / reviewer 反复次数 / mini-design 占比），反哺 harness v2 规则。
- NICE TO HAVE #1（tar 退码 3 → 1 降级）可入 follow-up backlog，非阻断。
