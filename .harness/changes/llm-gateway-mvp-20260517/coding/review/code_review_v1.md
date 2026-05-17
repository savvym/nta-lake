---
change_id: llm-gateway-mvp-20260517
target: coding/main（工作树）
target_head: working-tree（待 commit）
review_version: 1
reviewer: application-owner-agent
reviewed_at: 2026-05-17T20:35:00Z
verdict: APPROVED
---

# Code Review v1

## 范围与作者声明对照

- coding_report 声明的改动文件：16 个
- `git status --porcelain` 实际：16 个（+ uv.lock）
- 差异：**无**

## 正确性 / 安全 / 架构

### MUST FIX

无。

### SHOULD FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | apps/api/dataplat_api/llm/factory.py:30 | get_llm_gateway 用 lru_cache 后，env 变化在测试外不会重读 | 已提供 reset_llm_gateway()；生产用例满足。follow-up `llm-gateway-env-reload-*`（若未来需要 hot-reload provider） |

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | apps/api/dataplat_api/llm/providers/anthropic.py:25-27 | cast(Any, ...) 绕过 mypy + anthropic SDK overload 不匹配是 SDK 自身类型约束的代价，没有更好的选择 | 等 anthropic SDK 改善 TypedDict 兼容性；follow-up `llm-anthropic-typed-messages-*` |
| 2 | apps/api/dataplat_api/llm/gateway.py:48 | `last_exc: Exception | None = None` + `assert last_exc is not None` 是 type-narrowing 的 idiom，但有点丑 | 改 `raise RuntimeError("unreachable")` 也行；当前更清晰 |
| 3 | apps/api/dataplat_api/llm/cache.py:36 | 用 `redis.Redis` 同步客户端但 cache 接口是 async。这是 RQ/redis-py 5 的 pattern（同步 client 多年的现状）；后续 follow-up 可换 redis.asyncio.Redis | follow-up `redis-asyncio-migration-*` |

## 风格 / 性能 / 可观测性（参考 coding-style.md）

- ✅ async 函数全程 async；redis 同步调用包在 `await` 兼容路径里
- ✅ Pydantic schema 全部 extra=forbid
- ✅ Provider 构造惰性 → 无 API key 也能 import 类（满足 spec AC-2）
- ✅ Cache key 用 sha256(canonical_json) sort_keys=True → 跨进程稳定
- ✅ Gateway 错误路径：cache get/set 失败仅 warn 不阻塞 caller；provider 失败 retry max_retries 次后 raise last_exc
- ✅ Test mock 范围合规：LLM provider 用 spy/flaky 类，但 BlobStore / DB / Redis 用真实例（test_b/c/f）
- ✅ 反向 grep 拦 `llm=None`：processor_runner.py 不存在；AC-8 PASS

## 跨改动观察

- **Registry/Runner/Gateway 三件套对称性**：AdapterRegistry/AdapterRunner ↔ ProcessorRegistry/ProcessorRunner ↔ 现在的 LLMGateway 是三套姊妹结构。MVP 阶段不抽 base；当出现第 4 个时再考虑 BaseGateway pattern
- **anthropic SDK 加 deps 后 venv 状态**：首次 uv sync 没自动装 dev extras 导致 pytest 走系统二进制——SKILL 第 10 条候选反哺："新 change 第一次跑 pytest 前必须 `cd apps/api && uv sync --extra dev`"
- **LLMSummarizeProcessor 是 design.md §4.5 的第一个落地证据**：未来 llm-qa-gen 等 processor 也走 ctx.llm.call —— 至此 §4.5 / §11.7 #2 "LLM 调用必须走统一网关" 的约束有了机械化基础

## Deferred SHOULD FIX

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| SHOULD FIX | factory.py get_llm_gateway 不 hot-reload env | follow-up `llm-gateway-env-reload-*` |
| NICE TO HAVE | redis 同步 client → 异步 | follow-up `redis-asyncio-migration-*` |
| NICE TO HAVE | anthropic SDK MessageParam 兼容 | follow-up `llm-anthropic-typed-messages-*` |
| SKILL 反哺 | 新 change 首次跑 pytest 前必须 `uv sync --extra dev` | SKILL request-analysis 第 10 条候选 |

## Verdict

APPROVED（MUST FIX = 0；3 SHOULD/NICE 已 deferred 到各自 follow-up）。

## 后续指引

进入阶段 5 单测编写 → 6 单测评审。
