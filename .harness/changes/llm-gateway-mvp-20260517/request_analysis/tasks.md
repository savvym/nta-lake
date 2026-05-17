---
change_id: llm-gateway-mvp-20260517
version: 1
authored_at: 2026-05-17T19:55:00Z
---

# Tasks

## T-1 packages/core protocols/llm.py

- 新建 `packages/core/src/dataplat_core/protocols/llm.py`：`LLMClient` Protocol（runtime_checkable，async `call(req: LLMRequest) -> LLMResponse`）+ `LLMRequest`（model_id / messages / max_tokens / temperature / seed；extra=forbid）+ `LLMResponse`（text / model_id / input_tokens / output_tokens；extra=forbid）+ `LLMMessage`（role / content；extra=forbid）
- `packages/core/src/dataplat_core/protocols/__init__.py`：export 三件
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-1

## T-2 providers/fake.py（先做测试桩）

- `apps/api/dataplat_api/llm/providers/__init__.py` + `apps/api/dataplat_api/llm/providers/fake.py`
- `FakeLLMProvider` 实现 LLMClient：`call` 返 `LLMResponse(text=f"FAKE: {messages[0].content[:80]}", model_id=req.model_id, input_tokens=len(...), output_tokens=...)`；deterministic
- depends_on: T-1 / estimated_stage: stage-3 / AC: AC-3

## T-3 providers/anthropic.py（真 provider）

- `apps/api/dataplat_api/llm/providers/anthropic.py`：`AnthropicProvider` 实现 LLMClient
- 构造惰性：`__init__(self, api_key: str | None = None)` 不连 API，只存 key（None 时从 env `ANTHROPIC_API_KEY` 取）
- `call` 用 `anthropic.AsyncAnthropic(api_key=...)` 发 `messages.create(...)` → 转 LLMResponse
- depends_on: T-1 / estimated_stage: stage-3 / AC: AC-2

## T-4 cache.py（Redis 响应缓存）

- `apps/api/dataplat_api/llm/cache.py`：`RedisLLMCache(redis_client)` 暴露 async `get(req: LLMRequest) -> LLMResponse | None` + `set(req, resp, ttl: int = 86400)`
- Key 算法：`f"llm:{sha256(canonical_json({model_id, messages, max_tokens, temperature, seed})).hexdigest()}"`，sort_keys=True 保证跨进程稳定
- Value：LLMResponse.model_dump_json()
- depends_on: T-1 / estimated_stage: stage-3 / AC: AC-4

## T-5 gateway.py + factory.py

- `apps/api/dataplat_api/llm/gateway.py`：`LLMGateway(provider, cache=None, max_retries=3, base_delay=0.1)`；`async def call(req)`：先查 cache → miss 调 provider（指数退避 max_retries 次）→ 写 cache → 返
- retry 逻辑：`for attempt in range(max_retries + 1): try: return await provider.call(req); except Exception: if attempt == max_retries: raise; await asyncio.sleep(base_delay * 2**attempt)`
- `apps/api/dataplat_api/llm/factory.py`：`get_llm_gateway()` 用 `functools.lru_cache(maxsize=1)`；env `DATAPLAT_LLM_PROVIDER` ∈ `{anthropic, fake}`，缺省 fake；构造 RedisLLMCache（reuse `jobs/redis_client.py` get_redis）
- depends_on: T-2, T-3, T-4 / estimated_stage: stage-3 / AC: AC-5, AC-6, AC-7, AC-12

## T-6 ProcessorRunner 注入 ctx.llm

- 改 `apps/api/dataplat_api/runner/processor_runner.py`：构 StandardRunContext 时 `llm=get_llm_gateway()`
- 反向 grep 自审：`! grep -E "llm\s*=\s*None" apps/api/dataplat_api/runner/processor_runner.py`
- depends_on: T-5 / estimated_stage: stage-3 / AC: AC-8

## T-7 LLMSummarizeProcessor

- `apps/api/dataplat_api/processors/llm_summarize.py`：`LLMSummarizeProcessor` id=`llm-summarize` v=`0.1`
- run：打开 source repo_view 第一个 .md 文件 → 调 `await ctx.llm.call(LLMRequest(model_id="claude-haiku-4-5-20251001", messages=[{role:"user", content: f"Summarize: {content[:2000]}"}], max_tokens=256))` → 把 response.text 写 `summary.md` blob
- `apps/api/dataplat_api/processors/__init__.py`：import 触发自注册
- depends_on: T-1, T-6 / estimated_stage: stage-3 / AC: AC-9

## T-8 测试 tests/test_llm.py ≥ 6

- 新建 `apps/api/tests/test_llm.py`（**全 mock**，需 Redis）：
  - test_a_fake_provider_deterministic：同 req 调 2 次 → 同 text
  - test_b_redis_cache_get_set_roundtrip：set + get 返同 response；不同 req → None
  - test_c_gateway_cache_hit_skips_provider：第二次 call 不调 provider（用 spy/counter）
  - test_d_gateway_retry_then_success：mock provider 前 3 次 raise，第 4 次成功；monkeypatch asyncio.sleep → 0 加速
  - test_e_factory_singleton_and_default_fake：env 清空时 default fake；两次 get_llm_gateway() is 同对象
  - test_f_llm_summarize_processor_end_to_end：env 强制 fake；admin POST /process（先 ingest 1 个 .md）→ run_process_job → ProcessorRunner.run → 输出 summary.md blob 含 "FAKE:" 前缀
- depends_on: T-2~T-7 / estimated_stage: stage-3 / AC: AC-10

## T-9 codegen + lint + type

- 本变更**不增** HTTP endpoint（llm-summarize 走已有 /process），故 openapi.json 不变
- `uv run ruff check apps/api packages/core worker/src` 0 errors
- `uv run mypy apps/api/dataplat_api packages/core/src worker/src` 0 errors
- depends_on: T-1~T-8 / estimated_stage: stage-3 / AC: AC-11

## T-10 self_check llm-gateway-mvp block

- `scripts/_self_check.sh` 追加 `run_llm_gateway_mvp` 13 AC + filter + 总入口
- AC-10 走 `run_ac_skipif_no_pg_minio_redis` 探针（test_f 端到端要 PG+MinIO+Redis）
- depends_on: T-1~T-9 / estimated_stage: stage-3 / AC: AC-13

## process_tasks

## T-11 stage-2 spec/tasks review

- depends_on: T-10 v1 完
- estimated_stage: stage-2

## T-12 stage-4 coding review

- depends_on: T-1~T-9
- estimated_stage: stage-4

## T-13 stage-5/6 test_report + review

- depends_on: T-8
- estimated_stage: stage-6

## T-14 stage-7 CI（本地 self_check 等价）

- depends_on: T-10, T-13
- estimated_stage: stage-7

## T-15 stage-9 deploy verify

- depends_on: T-14
- estimated_stage: stage-9

## T-16 stage-10 close

- depends_on: T-14, T-15
- estimated_stage: stage-10

## 任务依赖图

```
T-1 (协议+schema)
  ├→ T-2 (fake provider)
  ├→ T-3 (anthropic provider)
  ├→ T-4 (redis cache)
  ├→ T-7 (llm-summarize) ← T-6 (ctx 注入)
  ↓
T-5 (gateway+factory) ← T-2, T-3, T-4
  ↓
T-6 (processor_runner 注入)
  ↓
T-7 (llm-summarize)
  ↓
T-8 (6 tests) ← T-2~T-7
  ↓
T-9 (lint+type)
  ↓
T-10 (self_check)
  ↓
T-11 → T-12 → T-13 → T-14 → T-15 → T-16
```

## AC 覆盖矩阵

| AC | task |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-3 |
| AC-3 | T-2 |
| AC-4 | T-4 |
| AC-5 | T-5 |
| AC-6 | T-5 |
| AC-7 | T-5 |
| AC-8 | T-6 |
| AC-9 | T-7 |
| AC-10 | T-8 |
| AC-11 | T-9 |
| AC-12 | T-5 |
| AC-13 | T-10 |
