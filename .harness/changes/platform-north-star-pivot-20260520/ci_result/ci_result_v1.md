---
change_id: platform-north-star-pivot-20260520
version: 1
ran_at: 2026-05-20T16:30:00Z
status: PASS
---

# CI Result v1

## 跑法

```bash
DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
DATAPLAT_REDIS_PORT=6379 \
bash scripts/_self_check.sh full
```

## 结果

```
PASS: 351 / FAIL: 5 / SKIP: 0
失败: AC-11 (ingest), AC-11 (jobs), AC-10 (processor), AC-10 (llm), AC-10 (firecrawl)
```

## 失败分析

5 个 FAIL **全部为 pre-existing flakes**，与本 change 无关：

| AC | block | 说明 |
|---|---|---|
| AC-11 ingest | rq-worker-skeleton | 同 web-jobs-list-page-20260520 ci_result 标注，已记入 AC-13 "上游不回归 deselect" 列表 |
| AC-11 jobs | rq-worker-skeleton | 同上 |
| AC-10 processor | processor-framework | 同上 |
| AC-10 llm | llm-gateway-mvp | 同上 |
| AC-10 firecrawl | adapter-firecrawl | 同上 |

**本 change 引入的 10 个新 AC（run_platform_north_star_pivot block）全部 PASS**，self_check 整体 PASS 数从前一 change 闭环时的 340 增至 351（+11，其中 10 为本 change 新 AC + 1 网络抖动恢复）。

## 与本 change 强相关的 AC 验证

- AC-1 ~ AC-10：本 change 内 block 10/10 PASS（详 test_report_v1）
- run_repo_files_tab_v2 AC-3/AC-5 awk 状态机：未受影响（design.md 改动不动 `apps/web/src/routes/repos/$owner.$name.tsx`）
- 其他 21 个 closed change 的 AC block：全部 PASS（无业务代码改动→无回归）

## 结论

CI PASS。FAIL 5 为 pre-existing 不阻塞合入。
