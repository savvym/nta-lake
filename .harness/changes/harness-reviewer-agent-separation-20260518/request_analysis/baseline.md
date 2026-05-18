---
change_id: harness-reviewer-agent-separation-20260518
authored_at: 2026-05-18T13:25:00Z
purpose: 为 spec_v3.md AC-12 提供 baseline 实测产物（response to spec_review_v2 MUST FIX #1）
---

# Self-check baseline 实测

## 命令

```bash
cd /data/home/zhhdzhang/nta/nta-lake
DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
  DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
  DATAPLAT_REDIS_PORT=6379 \
  bash scripts/_self_check.sh 2>&1 | grep -E "^(PASS|FAIL|SKIP):"
```

## 实测输出（2026-05-18T13:10:00Z）

```
PASS: 225
FAIL: 0
SKIP: 0
```

## 环境

- 容器：dataplat-pg-test:5433 / dataplat-minio-test:9100 / dataplat-redis-test:6379 全在线
- self_check 当前包含 16 个 change block：bootstrap-monorepo / core-domain-model / cas-storage / auth-scaffold / repo-api-mvp / commit-api-mvp / adapter-framework / web-mvp-pages / rq-worker-skeleton / web-write-flows / repo-files-tab / processor-framework / llm-gateway-mvp / adapter-firecrawl / llm-qa-gen / sdk-cli-mvp
- 累计 AC 数：17×3 (bootstrap+core+cas+auth 实际是 17 AC) + 13×12 (其余 12 block) = 51 + 156 = 207；加上各 block 内的浮动几个 AC（如 auth-scaffold 16 AC 等）实测精确数 = 225
- baseline 锁定值：**225**

## 用途

- spec_v3.md AC-12：本变更新加 1 个 global reviewer-lint AC → 期望 stage 3 末跑 self_check `PASS: 226`
- AC-12 命令使用动态计算：`expected=$(($(cat .harness/changes/harness-reviewer-agent-separation-20260518/request_analysis/baseline.md | grep -oE "baseline 锁定值：\*\*[0-9]+" | grep -oE "[0-9]+")+1))`；或硬钉 226（baseline 已实测落产物，串行变更不漂移）
- spec_v3.md 采用硬钉 226 + 本 baseline.md 提供推导证据

## 风险

- 若本变更进 stage 3 时其他变更并行 merge（修了 self_check），baseline 会漂移 → AC-12 FAIL
- mitigation：本变更串行；commit 前 `git status` 确认无其他 change 在飞；若发生 → 重新跑 baseline + 改 spec_v3 AC-12 数字
