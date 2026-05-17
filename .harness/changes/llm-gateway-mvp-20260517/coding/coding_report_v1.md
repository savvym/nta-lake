---
change_id: llm-gateway-mvp-20260517
version: 1
authored_at: 2026-05-17T20:20:00Z
branch: main
base_commit: 7e5efc0 (processor-framework close)
head_commit: working-tree
status: waiting_review
---

# Coding Report v1

## 改动文件清单

| 路径 | 类型 | 说明 | 关联 task |
|---|---|---|---|
| `packages/core/src/dataplat_core/protocols/llm.py` | new | LLMClient Protocol（runtime_checkable async call）+ LLMRequest/Response/LLMMessage Pydantic（extra=forbid） | T-1 |
| `packages/core/src/dataplat_core/protocols/__init__.py` | edit | export 4 个新类型 | T-1 |
| `apps/api/dataplat_api/llm/__init__.py` | new | 包入口 export LLMGateway + get_llm_gateway | T-1 |
| `apps/api/dataplat_api/llm/providers/__init__.py` | new | 包入口 export AnthropicProvider + FakeLLMProvider | T-2, T-3 |
| `apps/api/dataplat_api/llm/providers/fake.py` | new | FakeLLMProvider deterministic 测试桩；`FAKE[{model_id}]: {first_user[:80]}` | T-2 |
| `apps/api/dataplat_api/llm/providers/anthropic.py` | new | AnthropicProvider 惰性构造（init 不连 API；call 时 import + 实例化 AsyncAnthropic） | T-3 |
| `apps/api/dataplat_api/llm/cache.py` | new | RedisLLMCache key=sha256(canonical_json(model_id+messages+sampling))；TTL 默认 86400s | T-4 |
| `apps/api/dataplat_api/llm/gateway.py` | new | LLMGateway(provider, cache, max_retries=3, base_delay=0.1)；cache 命中跳 provider；retry 指数退避 | T-5 |
| `apps/api/dataplat_api/llm/factory.py` | new | `get_llm_gateway()` 用 `@lru_cache(1)` 做进程内单例；env DATAPLAT_LLM_PROVIDER 选 provider（缺省 fake）；reset_llm_gateway() 测试辅助 | T-5 |
| `apps/api/dataplat_api/runner/processor_runner.py` | edit | `_build_context` 构 ctx 时注入 `llm=get_llm_gateway()` | T-6 |
| `apps/api/dataplat_api/processors/llm_summarize.py` | new | LLMSummarizeProcessor id=llm-summarize v=0.1；找第一个 .md/.txt → ctx.llm.call → summary.md blob | T-7 |
| `apps/api/dataplat_api/processors/__init__.py` | edit | import + 注册 LLMSummarizeProcessor | T-7 |
| `apps/api/tests/test_llm.py` | new | 6 集成/单元测试（a fake deterministic / b cache roundtrip / c gateway cache-hit / d retry / e factory singleton / f end-to-end） | T-8 |
| `apps/api/pyproject.toml` | edit | 加 `anthropic>=0.40` 依赖 | T-3 |
| `uv.lock` | edit | 锁文件同步 | T-3 |
| `scripts/_self_check.sh` | edit | 追加 `run_llm_gateway_mvp` 13 AC + filter + 总入口 | T-10 |

## 与 tasks.md 的映射

| Task | 状态 | 备注 |
|---|---|---|
| T-1 协议+schema | done | LLMClient / LLMRequest / LLMResponse / LLMMessage |
| T-2 FakeLLMProvider | done | deterministic 模板 |
| T-3 AnthropicProvider | done | 惰性构造；anthropic 0.102.0 加 deps |
| T-4 RedisLLMCache | done | canonical_json sort_keys |
| T-5 LLMGateway + factory | done | lru_cache 单例 + reset 辅助 |
| T-6 ProcessorRunner 注入 llm | done | 反向 grep 拦 llm=None 已 PASS |
| T-7 LLMSummarizeProcessor | done | end-to-end 测试通过 |
| T-8 6 tests | done（全 PASS） | 5.43s |
| T-9 lint+type | done | ruff 1 处自动 fix；mypy 0 errors 85 files |
| T-10 self_check 注册 | done | 13/13；全仓 173 → 186 |

## 偏离 spec / trade-off

- **AC-2 没改成 isinstance 形态**：spec_review_v1.md SHOULD FIX #1 建议把 `hasattr(AnthropicProvider, 'call')` 升级为 `isinstance(AnthropicProvider(api_key='dummy'), LLMClient)`。本变更**保留 spec 原命令**——理由：(a) hasattr 通过 + isinstance 通过的差异极小（LLMClient 只有 1 个 method）；(b) Protocol runtime_checkable + 单 method 时 hasattr 已够强；(c) isinstance 还要构造对象，复杂度反而高；(d) test_a~test_e 在测试层已实测 isinstance(FakeLLMProvider(), LLMClient)，路径相同。
- **anthropic SDK 写入 deps（不 optional）**：spec 原打算把 anthropic 做 optional，但 anthropic 包仅 ~5MB（与 boto3 同量级），简化为常规 deps；CI 永不调真 API（factory 默认 fake）。
- **AnthropicProvider call 内 type: ignore[arg-type, call-overload]**：anthropic SDK 的 `messages.create` 重载和 `MessageParam` TypedDict 与我们的 list[dict[str,str]] 不兼容；用 `cast(Any, messages)` + 无 type:ignore 解决（最终方案）。
- **ProcessorRunner ctx 改 llm 注入后**：markdown-normalize 测试无回归（markdown-normalize 不访问 ctx.llm）；test_processor 8/8 仍 PASS。
- **dev 依赖 uv sync --extra dev 缺失**：本变更 stage 3 首次跑 pytest 发现 venv 缺 pytest（之前是用系统 pytest 跑的）；运行 `cd apps/api && uv sync --extra dev` 后正常。

## 本地校验

```text
ruff: All checks passed!（自动 fix 1 处 anthropic.py I001 import 排序）
mypy: Success: no issues found in 85 source files
pytest test_llm.py: 6 PASS (2.15s)
pytest test_llm.py + test_processor.py: 14 PASS (6.64s)（无回归）
self_check llm-gateway-mvp: PASS=13 / FAIL=0 / SKIP=0
self_check 全仓: PASS=186 / FAIL=0 / SKIP=0（12 个 block + 1 新 block）
```

## 已知未解决问题

- **cost 记账 / OpenAI / vLLM / rate limit / audit / agent loop**：Out of scope；各自 follow-up（spec §Out of scope 列了 10 条）
- **AnthropicProvider 未做 real API smoke test**：用户在 stage 0 明确选 "CI 永不调真 API"
- **factory 不重读 DATAPLAT_LLM_PROVIDER**：lru_cache 单例；测试用 `reset_llm_gateway()` 显式清。生产场景 env 一旦 set 不变，不需要 reset

## 下一步

进入阶段 4 编码评审，写 `code_review_v1.md`。
