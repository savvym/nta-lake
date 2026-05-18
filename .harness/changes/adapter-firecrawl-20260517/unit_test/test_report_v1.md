---
change_id: adapter-firecrawl-20260517
version: 1
authored_at: 2026-05-18T09:05:00Z
status: waiting_review
---

# Test Report v1

## 验收项 ↔ 测试映射

| AC ID | 测试文件 | 测试函数 |
|---|---|---|
| AC-1 | n/a | static check（self_check AC-1 isinstance） |
| AC-2 | n/a | static check（self_check AC-2 extra=forbid） |
| AC-3 | n/a | static check（self_check AC-3 三重 grep） |
| AC-4 | n/a | static check（self_check AC-4 registry） |
| AC-5 | apps/api/tests/test_firecrawl.py | test_a_extract_image_urls_unit |
| AC-6 | n/a | static check（self_check AC-6 grep httpx） |
| AC-7 | n/a | static check（self_check AC-7 反向 grep gather） |
| AC-8 | apps/api/tests/test_firecrawl.py | test_b_adapter_ingest_unit_with_fakes + test_e_end_to_end_succeeded |
| AC-9 | apps/api/tests/test_firecrawl.py | test_b_adapter_ingest_unit_with_fakes + test_e_end_to_end_succeeded |
| AC-10 | apps/api/tests/test_firecrawl.py | 全 6 测试（pytest collect 计数 ≥ 6） |
| AC-11 | n/a | static check（self_check AC-11 ruff+mypy） |
| AC-12 | n/a | static check（self_check AC-12 default model） |
| AC-13 | scripts/_self_check.sh | run_adapter_firecrawl |

## 测试文件清单

| 文件 | 类型 | 用例数 |
|---|---|---|
| apps/api/tests/test_firecrawl.py | 单元 + 集成（PG+MinIO+Redis） | 6 |

## Mock 范围声明

- 允许 mock：httpx（用 `_FakeAsyncClient` 整体替换 module-level `httpx`）；env DATAPLAT_LLM_PROVIDER；FakeLLMProvider.call（test_e 单点）
- 禁止 mock：BlobStore（test_c/d/e/f 用真 MinIO；test_b 用 _FakeStore 但实现 Protocol）；DB（test_c/d/e/f 用真 PG）；Redis（用真 redis）

**本轮 mock**：
- `_FakeAsyncClient`（test_b/c/d/e/f）：模拟 httpx.AsyncClient；__aenter__/__aexit__ + get(url) 按 routes 表返响应 / 按 raise_for 抛 ConnectError
- `monkeypatch.setattr("dataplat_api.adapters.firecrawl_url.httpx", fake)`：只替换 firecrawl_url 模块视角的 httpx；不影响其他用 httpx 的代码（如 ASGITransport）
- `monkeypatch.setattr("dataplat_api.llm.providers.fake.FakeLLMProvider.call", _fake_md_call)`（test_e）：让 fake 返固定 markdown 含 image URL
- `monkeypatch.setenv("DATAPLAT_LLM_PROVIDER", "fake")`：测试统一用 fake provider

均与 coding-style §1.7 一致；BlobStore / DB 用真依赖。

## 本地运行结果

```text
$ uv run pytest -q tests/test_firecrawl.py
......                                                                   [100%]
6 passed in 3.21s

# 与 ingest / llm / processor 同跑无回归：
$ uv run pytest -q tests/test_firecrawl.py tests/test_ingest.py tests/test_llm.py tests/test_processor.py
.................................                                        [100%]
33 passed in 14.68s
```

## 已知 flaky / 跳过

- test_c/d/e/f 标 `pytest.mark.skipif(not _PG_MINIO_REDIS_OK)`：本地 dev 环境三件不通时跳过（与 test_processor/test_llm 同 pattern）
- 本次运行环境三件都通 → 0 skip / 0 fail / 6 passed

## 覆盖率

未配 coverage 工具；新增 2 个模块（_image_extract / firecrawl_url）的关键路径都有 ≥ 1 测试覆盖：
- extract_image_urls：test_a（HTML / md / 相对 / data: / dup / 空 src 6 条断言）
- FirecrawlURLAdapter.ingest 单元：test_b（mock httpx + _SummaryLLM + _FakeStore 验 content.md + image entry + ≥2 puts）
- 端到端：test_e（admin /jobs/ingest → worker → succeeded → 下游 commit 含 assets/0/content.md + ≥1 image）
- 错误路径：test_f（unreachable URL ConnectError → job mark_failed）
- 权限：test_c admin queued / test_d user 403

## 下一步

进入阶段 6 单测评审。
