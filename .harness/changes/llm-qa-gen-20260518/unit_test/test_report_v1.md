---
change_id: llm-qa-gen-20260518
version: 1
authored_at: 2026-05-18T10:20:00Z
status: waiting_review
---

# Test Report v1

## 验收项 ↔ 测试映射

| AC ID | 测试文件 | 测试函数 |
|---|---|---|
| AC-1 | n/a | static check（self_check AC-1 extra=forbid） |
| AC-2 | n/a | static check（self_check AC-2 test -f + isinstance） |
| AC-3 | n/a | static check（self_check AC-3 registry） |
| AC-4 | n/a | static check（self_check AC-4 default model） |
| AC-5 | n/a | static check（self_check AC-5 default records） |
| AC-6 | n/a | static check（self_check AC-6 prompt 含 {text}） |
| AC-7 | n/a | static check（self_check AC-7 _TEXT_SUFFIXES + 3 suffix） |
| AC-8 | n/a | static check（self_check AC-8 sft.jsonl 字面） |
| AC-9 | apps/api/tests/test_llm_qa_gen.py | test_a_parse_qa_direct_json + test_b_parse_qa_code_block + test_c_parse_qa_fallback_raw |
| AC-10 | apps/api/tests/test_llm_qa_gen.py | 全 6 测试 |
| AC-11 | n/a | static check（self_check AC-11 ruff+mypy） |
| AC-12 | n/a | static check（self_check AC-12 ctx.llm + llm is None） |
| AC-13 | scripts/_self_check.sh | run_llm_qa_gen |

## 测试文件清单

| 文件 | 类型 | 用例数 |
|---|---|---|
| apps/api/tests/test_llm_qa_gen.py | 单元（a/b/c/d） + 集成（e/f；PG+MinIO+Redis） | 6 |

## Mock 范围声明

- 允许 mock：LLM provider（_JsonLLM 实现 LLMClient 返合法 JSON；_SummaryLLM 同理）；env DATAPLAT_LLM_PROVIDER；FakeLLMProvider.call（test_f 单点）
- 禁止 mock：BlobStore（test_e/f 用真 MinIO；test_d 用 _FakeStore 但实现 Protocol）；DB（用真 PG）；Redis（用真）

**本轮 mock**：
- `_JsonLLM`（test_d）：返 `{"prompt": "q{N}", "response": "a{N}"}` 计数调用次数
- `monkeypatch FakeLLMProvider.call`（test_f）：让端到端测试 fake provider 返合法 JSON 而非截断 80-char 模板（adapter-firecrawl 同 pattern）
- `monkeypatch.setenv("DATAPLAT_LLM_PROVIDER", "fake")`：测试统一用 fake provider

均与 coding-style §1.7 一致；BlobStore / DB / Redis 用真依赖。

## 本地运行结果

```text
$ uv run pytest -q tests/test_llm_qa_gen.py
......                                                                   [100%]
6 passed in 2.74s

# 跨变更回归：
$ uv run pytest -q tests/test_llm_qa_gen.py tests/test_processor.py tests/test_firecrawl.py tests/test_llm.py
..........................                                               [100%]
26 passed in 11.38s
```

## 已知 flaky / 跳过

- test_e/f 标 `pytest.mark.skipif(not _PG_MINIO_REDIS_OK)`：PG/MinIO/Redis 任一不通跳过
- 本次运行三件都通 → 0 skip / 0 fail / 6 passed

## 覆盖率

- _parse_qa_response：3 测试全覆盖（直接 JSON / 代码块 / fallback）
- LLMQAGenProcessor.run + _run_all：test_d 单元 + test_f 端到端覆盖（含多 records_per_doc / meta 注入 / sft.jsonl 拼接 / blob put）
- LLM 调用真路径：test_f 走 worker → ProcessorRunner → ctx.llm.call → blob put → CommitService

## 下一步

进入阶段 6 单测评审。
