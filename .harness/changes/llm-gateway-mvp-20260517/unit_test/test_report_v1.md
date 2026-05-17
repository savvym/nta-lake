---
change_id: llm-gateway-mvp-20260517
version: 1
authored_at: 2026-05-17T20:40:00Z
status: waiting_review
---

# Test Report v1

## 验收项 ↔ 测试映射

| AC ID | 测试文件 | 测试函数 |
|---|---|---|
| AC-1 | n/a | static check（self_check AC-1 import + extra=forbid） |
| AC-2 | n/a | static check（self_check AC-2 hasattr） |
| AC-3 | apps/api/tests/test_llm.py | test_a_fake_provider_deterministic |
| AC-4 | apps/api/tests/test_llm.py | test_b_redis_cache_get_set_roundtrip |
| AC-5 | apps/api/tests/test_llm.py | test_c_gateway_cache_hit_skips_provider（间接：调 await gw.call） |
| AC-6 | apps/api/tests/test_llm.py | test_d_gateway_retry_then_success（max_retries=3 实测） |
| AC-7 | apps/api/tests/test_llm.py | test_e_factory_singleton_and_default_fake |
| AC-8 | n/a | static check（self_check AC-8 grep test -f + 正向 + 反向 None） |
| AC-9 | apps/api/tests/test_llm.py | test_f_llm_summarize_end_to_end（间接：跑 LLMSummarizeProcessor，必须实现 Protocol） |
| AC-10 | apps/api/tests/test_llm.py | 全部 6 个测试（pytest --collect-only 计数 ≥ 6） |
| AC-11 | n/a | static check（self_check AC-11 ruff + mypy） |
| AC-12 | apps/api/tests/test_llm.py | test_e_factory_singleton_and_default_fake（同测覆盖 env 缺省 fake） |
| AC-13 | scripts/_self_check.sh | run_llm_gateway_mvp 函数本身 |

## 测试文件清单

| 文件 | 类型 | 用例数 |
|---|---|---|
| apps/api/tests/test_llm.py | 单元 + 集成（PG + MinIO + Redis） | 6 |

## Mock 范围声明

- 允许 mock：LLM provider（test_c spy / test_d flaky 用类实现 LLMClient Protocol）；env（monkeypatch DATAPLAT_LLM_PROVIDER）；asyncio.sleep（test_d 加速）
- 禁止 mock：RedisLLMCache（用真 Redis）；BlobStore（test_f 用真 MinIO）；CommitService / ProcessorRunner / RepoService（test_f 端到端走真 DB + 真 HTTP）

**本轮 mock 了**：
- `_SpyProvider`（test_c）：本地类实现 LLMClient.call，计数调用次数
- `_FlakyProvider`（test_d）：本地类实现 LLMClient.call，前 3 次 raise，第 4 次成功
- `monkeypatch.setattr("dataplat_api.llm.gateway.asyncio.sleep", _no_sleep)`（test_d）：跳过真 sleep 加速
- `monkeypatch.setenv("DATAPLAT_LLM_PROVIDER", "fake")`（test_f）：强制 fake provider，避免端到端调真 Anthropic

均与 coding-style §1.7 一致。

## 本地运行结果

```text
$ cd apps/api && DATAPLAT_DATABASE_URL=... DATAPLAT_REDIS_URL=... DATAPLAT_MINIO_ENDPOINT=... \
    uv run pytest -q tests/test_llm.py
......                                                                   [100%]
6 passed in 2.15s

# 与 processor-framework 同跑无回归：
$ uv run pytest -q tests/test_llm.py tests/test_processor.py
..............                                                           [100%]
14 passed in 6.64s
```

## 已知 flaky / 跳过

- test_b / test_c 标 `pytest.mark.skipif(not _redis_reachable())`：本地 dev 环境 Redis 不通时跳过（与 test_processor.py 同模式）
- test_f 标 `pytest.mark.skipif(not _PG_MINIO_REDIS_OK)`：PG/MinIO/Redis 任一不通跳过
- 本次运行环境三件都通 → 0 skip / 0 fail / 6 passed

## 覆盖率

未配 coverage 工具；新增 7 个模块（llm/__init__ / providers/fake / providers/anthropic / cache / gateway / factory / processors/llm_summarize）的关键路径都至少 1 个测试覆盖：
- FakeLLMProvider.call → test_a
- RedisLLMCache.get/set → test_b
- LLMGateway.call cache-hit + retry → test_c + test_d
- get_llm_gateway / reset_llm_gateway / 默认 fake → test_e
- LLMSummarizeProcessor.run（ctx.llm.call + ctx.blob_store.put + commit）→ test_f
- AnthropicProvider.call：未测真 API 路径（spec Out of scope）；但 import + hasattr 静态可见

## 下一步

进入阶段 6 单测评审。
