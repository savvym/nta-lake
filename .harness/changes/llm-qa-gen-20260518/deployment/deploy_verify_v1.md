---
change_id: llm-qa-gen-20260518
version: 1
env: dev
deployed_at: 2026-05-18T10:35:00Z
image_tag: working-tree（未打 image；dev 本地 uv run）
commit_sha: (will-be-filled-at-commit)
verifier: application-owner-agent
verdict: PASS
---

# Deploy Verification v1

> Dev 用 `uv run` 直接跑。验证通过 self_check + pytest 端到端 + processor registry 含 3 个 processor + Bronze→Silver→Gold 链路打通。

## 验证矩阵

| ID | 验收项 | 验证方式 | 期望 | 实际 | 备注 |
|---|---|---|---|---|---|
| AC-3 | llm-qa-gen 注册可见 | self_check AC-3 | get is not None | True | — |
| AC-10 | 6 测试全 PASS | pytest test_llm_qa_gen.py | 6 passed | 6 passed in 2.74s | — |
| DEP-1 | API import 不报错 | `uv run python -c "from dataplat_api.main import app"` | 退出 0 | 退出 0 | — |
| DEP-2 | 第 3 个 processor 注册（markdown-normalize + llm-summarize + llm-qa-gen） | self_check 三个 processor AC | 全部 get is not None | True | — |
| DEP-3 | sft.jsonl 端到端产出 | test_f_end_to_end_succeeded | 下游 commit 含 sft.jsonl + ≥1 行 JSON + meta 含 source_path | True | — |
| DEP-4 | _parse 三层 fallback | test_a/b/c | 三种输入分别命中三层 | True | — |
| DEP-5 | 事件循环嵌套修复 | view.open 在 asyncio.run 外预读 | 不再报 RuntimeError | True | 同步预读到 list[tuple] |
| DEP-6 | 全仓 self_check 无回归 | self_check 全跑 | 212/212 PASS | 212/212 PASS | — |
| DEP-7 | adapter-firecrawl / processor-framework / llm-gateway 测试无回归 | pytest 跨变更 26 PASS | 26 passed | 26 passed | — |

## 证据

### DEP-1

```text
$ cd apps/api && uv run python -c "from dataplat_api.main import app; print(len(app.routes))"
（正常退出）
```

### DEP-3（端到端 sft.jsonl）

```text
$ cd apps/api && DATAPLAT_DATABASE_URL=... DATAPLAT_REDIS_URL=... DATAPLAT_MINIO_ENDPOINT=... \
    uv run pytest -q tests/test_llm_qa_gen.py::test_f_end_to_end_succeeded -v
test_f_end_to_end_succeeded PASSED
1 passed
```

### DEP-6 / DEP-7

```text
PASS: 212
FAIL: 0
SKIP: 0
全部通过（FAIL=0；SKIP 不阻塞）。

# 跨变更回归
26 passed in 11.38s（qa-gen 6 + processor 8 + firecrawl 6 + llm 6）
```

## 风险评估

- [ ] schema 不兼容？**否**。LLMQAGenSpec / LLMQAGenProcessor 全新；不动既有 processor / runner
- [ ] 不可回滚操作？**否**。无 DB 迁移、无数据销毁
- [ ] 需要 follow-up？**是**。已在 coding_report / code_review / test_review 列出（meta-as-object / narrow-except / concurrent / chunking / prompt-lang / template-jinja / test-call-count / test-encoding / test-fallback-meta / per-source / parquet / dedup / quality-score / multi-turn / incremental / live-test / Web UI）

## Verdict

PASS。

## 处理动作

PASS → 进入阶段 10 用户确认 → close。
