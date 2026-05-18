---
change_id: adapter-firecrawl-20260517
version: 1
env: dev
deployed_at: 2026-05-18T09:20:00Z
image_tag: working-tree（未打 image；dev 本地 uv run）
commit_sha: (will-be-filled-at-commit)
verifier: application-owner-agent
verdict: PASS
---

# Deploy Verification v1

> Dev 用 `uv run` 直接跑（无 Docker image）。验证通过 self_check + pytest 端到端 + adapter registry 可见 + AdapterRunner ctx 注入到位。

## 验证矩阵

| ID | 验收项 | 验证方式 | 期望 | 实际 | 备注 |
|---|---|---|---|---|---|
| AC-4 | firecrawl-url 注册可见 | self_check AC-4 | get is not None | True | — |
| AC-10 | 6 测试全 PASS | pytest test_firecrawl.py | 6 passed | 6 passed in 3.21s | — |
| DEP-1 | API import 不报错 | `uv run python -c "from dataplat_api.main import app"` | 退出 0 | 退出 0 | — |
| DEP-2 | 第二个 adapter 在 registry 可见 | self_check AC-4 + adapter framework AC | raw-file-upload + firecrawl-url 两个 | True | — |
| DEP-3 | AdapterRunner 构 ctx 注入 llm + blob_store | self_check AC-3 三重 grep | grep + 反向都过 | True | — |
| DEP-4 | end-to-end /jobs/ingest firecrawl-url succeeded | test_e_end_to_end_succeeded | 下游 commit 含 assets/0/content.md + ≥1 image | True | — |
| DEP-5 | 错误路径 mark_failed | test_f_unreachable_url_marks_failed | job.status == "failed" + error 非空 | True | — |
| DEP-6 | 全仓 self_check 无回归 | self_check 全跑 | 199/199 PASS | 199/199 PASS | — |
| DEP-7 | adapter-framework 13 测试无回归（AdapterRunner ctx 改动） | pytest test_ingest.py | 13 passed | 13 passed | raw-file-upload 不依赖 ctx |
| DEP-8 | processor-framework / llm-gateway 测试无回归 | pytest test_processor + test_llm | 8 + 6 passed | 14 passed | ctx 改动同 pattern 已稳定 |

## 证据

### DEP-1

```text
$ cd apps/api && uv run python -c "from dataplat_api.main import app; print(len(app.routes))"
（正常退出）
```

### DEP-4（端到端）

```text
$ cd apps/api && DATAPLAT_DATABASE_URL=... DATAPLAT_REDIS_URL=... DATAPLAT_MINIO_ENDPOINT=... \
    uv run pytest -q tests/test_firecrawl.py::test_e_end_to_end_succeeded -v
test_e_end_to_end_succeeded PASSED
1 passed
```

### DEP-6 / DEP-7 / DEP-8

```text
PASS: 199
FAIL: 0
SKIP: 0
全部通过（FAIL=0；SKIP 不阻塞）。

# 跨变更回归
33 passed in 14.68s（firecrawl 6 + ingest 13 + llm 6 + processor 8）
```

## 风险评估

- [ ] schema 不兼容？**否**。FirecrawlURLSpec / firecrawl-url adapter 新增；不动既有 schema；AdapterRunner ctx 新增字段不影响旧 caller
- [ ] 不可回滚操作？**否**。无 DB 迁移、无数据销毁
- [ ] 需要 follow-up？**是**。已在 coding_report / code_review 列出（firecrawl-sdk / js-render / politeness / concurrent / incremental / image-vision / multimodal / live-test / web-ui / narrow-except / chunking / prompt-strict / test-image-content / test-call-count / test-error-msg / fake-llm-echo-mode / harness-lint-ac-precise-grep）

## Verdict

PASS。

## 处理动作

PASS → 进入阶段 10 用户确认 → close。
