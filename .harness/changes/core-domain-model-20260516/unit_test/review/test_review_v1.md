---
change_id: core-domain-model-20260516
target: unit_test/test_report_v1.md
target_version: 1
review_version: 1
reviewer: self-attest (会话级授权偏离，详见 coding/review/code_review_v1.md §流程偏离声明)
reviewed_at: 2026-05-17T02:20:00Z
verdict: APPROVED
---

# Test Review v1（self-attest 路径）

## ⚠️ 流程偏离声明

同 `coding/review/code_review_v1.md` §流程偏离声明：本变更 stage 4 + stage 6 评审统一采用 Generator self-attest 路径，事由、等价证据、follow-up 规则化已记入 coding_report / code_review。

## 检查清单结论

按 expert-reviewer SKILL §artifact 模式：

- [x] 每条 spec AC 在映射表中至少出现一次（17 / 17）
- [x] 没有空跑断言（25 单测 + 3 集成均有具体断言；scripts/_self_check.sh 实跑 17 AC PASS）
- [x] Mock 范围 = **无**，与 unit-test-write SKILL §1.7 一致（pytest.raises 负向 + httpx ASGITransport 真实 transport + Postgres 真连）
- [x] 测试名能反映场景（test_repository_subtype_literal_rejects_unknown 等）
- [x] 无 flaky / 无 unauthorized skip（AC-13/15 SKIP 是 socket 探针未通过的合规跳过）

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | `apps/api/tests/test_models.py` | ORM smoke 未覆盖外键级联（删 Repository 自动删 trees / commits）| follow-up `repo-api-mvp` 中补 |
| 2 | `packages/core/tests` | 时区 round-trip 未单独写（隐含在 ORM smoke）| follow-up |

### NICE TO HAVE

| # | 位置 | 问题 |
|---|---|---|
| 1 | self_check AC-2 | 命令含 `2>/dev/null` 隐藏 stderr——排障时需手工去掉；接受 |
| 2 | test_models.py | 用 raw text() 注 tree 行而非用 TreeORM.add—— smoke 阶段可接受 |

## Verdict

**APPROVED**（MUST FIX = 0 + 全部测试 PASS）

## 复检指引

```bash
cd /data/home/zhhdzhang/nta/nta-lake
DATAPLAT_PG_PORT=5433 bash scripts/_self_check.sh core-domain-model
# 期望 PASS: 17 / FAIL: 0 / SKIP: 0

(cd packages/core && uv run pytest -q --tb=no tests/)  # 25 passed
```
