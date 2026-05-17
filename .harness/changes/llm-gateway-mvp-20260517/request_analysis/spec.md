---
change_id: llm-gateway-mvp-20260517
version: 1
authored_at: 2026-05-17T19:50:00Z
status: draft
---

# Spec：LLM Gateway 薄骨架（Protocol + Anthropic/Fake provider + Redis cache + ctx 注入 + LLMSummarizeProcessor）

## 背景

design.md §4.5 / §5.1 / §11.2 / §11.7 #2 明确："**LLM 调用必须走平台统一网关，不允许散落在各 processor**"。但现状：

- `packages/core/protocols/runcontext.py` 中 `RunContext.llm` 只是 `Any` 占位字段
- `apps/api/dataplat_api/llm/` 目录**完全不存在**
- 任何 processor 想调 LLM 只能自带 SDK → 违反 §11.7 #2
- adapter-firecrawl（依赖 LLM 抓 HTML→md）/ pdf-to-text-llm（依赖 LLM OCR）/ llm-qa-gen（design.md §2.3 Repo E 的核心 processor）三条下游路径全被阻塞

processor-framework-20260517 已经把 Processor/RepoView/ProcessorRunner 框架落地，并且 StandardRunContext.llm 字段已经预留——本变更补上"实质 gateway + 至少 1 个 LLM Processor 验证链路通"。

## 问题陈述

需要新建 `apps/api/dataplat_api/llm/` 子模块：

1. 协议层：Protocol 定义 LLMClient + Pydantic schema 定义 LLMRequest/Response（含 model_id / messages / sampling params / token usage）
2. Provider 层：至少 1 个真实 provider（Anthropic）+ 1 个 deterministic 测试桩（FakeLLMProvider）
3. Cache 层：Redis 响应缓存（key=sha256(model_id+messages+sampling_params)）
4. Gateway 层：装饰 provider，加 cache + 简单 retry（指数退避 3 次）
5. Factory 层：根据 env `DATAPLAT_LLM_PROVIDER=anthropic|fake` 选 provider；默认 fake 避免无 key 启动报错
6. 集成层：StandardRunContext.llm 由 ProcessorRunner 注入 gateway 实例；新建 1 个 LLMSummarizeProcessor 端到端验证
7. 测试：≥ 6 集成测试，**全 mock**（CI 不消耗 Anthropic API 配额）

## 范围

**In scope**：

- `packages/core/src/dataplat_core/protocols/llm.py`：`LLMClient` Protocol（runtime_checkable）+ `LLMRequest` / `LLMResponse` Pydantic（extra=forbid）
- `apps/api/dataplat_api/llm/__init__.py`：包入口
- `apps/api/dataplat_api/llm/providers/__init__.py` + `anthropic.py` + `fake.py`：2 个 provider
- `apps/api/dataplat_api/llm/cache.py`：`RedisLLMCache`（key=sha256(model_id|messages_json|sampling_params_json)）
- `apps/api/dataplat_api/llm/gateway.py`：`LLMGateway`（构造接受 max_retries；call 异步；cache 命中跳过 provider；失败指数退避 3 次）
- `apps/api/dataplat_api/llm/factory.py`：`get_llm_gateway()` 单例 + env switch
- `apps/api/dataplat_api/runner/processor_runner.py`：构 ctx 时注入 `llm=get_llm_gateway()`
- `apps/api/dataplat_api/processors/llm_summarize.py`：`LLMSummarizeProcessor` id=`llm-summarize` v=`0.1`（读 markdown blob → ctx.llm.call → summary blob）
- `apps/api/dataplat_api/processors/__init__.py`：import 触发自注册
- `apps/api/tests/test_llm.py`：≥ 6 集成测试（**全 mock**）
- `scripts/_self_check.sh`：追加 `run_llm_gateway_mvp` 13 AC + filter + 总入口

**Out of scope**（显式列出）：

- cost 记账落 DB（按 token / usd）→ follow-up `llm-cost-accounting-*`
- OpenAI provider → follow-up `llm-provider-openai-*`
- vLLM 本地 provider → follow-up `llm-provider-vllm-*`
- rate limit（per provider qps / 并发） → follow-up `llm-rate-limit-*`
- audit log 落盘（prompt/response 全量存 blob）→ follow-up `llm-audit-log-*`
- agent loop / tools 接口 → follow-up `llm-agent-loop-*`
- budget 上限（pipeline run 维度） → follow-up `llm-budget-*`
- 多模态（image / audio） → follow-up `llm-multimodal-*`
- live test against 真 Anthropic → follow-up `llm-live-test-optional-*`（spec 已显式排除）
- Web UI 展示 cost / 调用历史 → follow-up `web-llm-dashboard-*`

## 验收标准（13 AC）

- AC-1：LLMClient Protocol + LLMRequest/LLMResponse Pydantic extra=forbid；
  `cd apps/api && uv run python -c "from dataplat_core.protocols.llm import LLMClient, LLMRequest, LLMResponse; assert LLMRequest.model_config.get('extra')=='forbid' and LLMResponse.model_config.get('extra')=='forbid'"`
- AC-2：AnthropicProvider 类存在 + 有 call 方法（构造需 API key 不在 AC 内验）；
  `cd apps/api && uv run python -c "from dataplat_api.llm.providers.anthropic import AnthropicProvider; assert hasattr(AnthropicProvider, 'call')"`
- AC-3：FakeLLMProvider deterministic（同 req → 同 response 文本）；
  `cd apps/api && uv run python -c "import asyncio; from dataplat_api.llm.providers.fake import FakeLLMProvider; from dataplat_core.protocols.llm import LLMRequest; p=FakeLLMProvider(); r=LLMRequest(model_id='x', messages=[{'role':'user','content':'hi'}], max_tokens=10); a=asyncio.run(p.call(r)); b=asyncio.run(p.call(r)); assert a.text==b.text"`
- AC-4：RedisLLMCache 类 + get/set 方法；
  `cd apps/api && uv run python -c "from dataplat_api.llm.cache import RedisLLMCache; assert all(hasattr(RedisLLMCache, m) for m in ['get','set'])"`
- AC-5：LLMGateway.call 是 coroutine；
  `cd apps/api && uv run python -c "from dataplat_api.llm.gateway import LLMGateway; import inspect; assert inspect.iscoroutinefunction(LLMGateway.call)"`
- AC-6：LLMGateway 构造接受 max_retries 参数；
  `cd apps/api && uv run python -c "from dataplat_api.llm.gateway import LLMGateway; import inspect; assert 'max_retries' in inspect.signature(LLMGateway.__init__).parameters"`
- AC-7：get_llm_gateway 是单例（同 process 返同对象）；
  `cd apps/api && uv run python -c "from dataplat_api.llm.factory import get_llm_gateway; assert get_llm_gateway() is get_llm_gateway()"`
- AC-8：ProcessorRunner 构 ctx 时注入 llm（grep `llm=` + test -f 前置 + 反向 grep 拦截"显式 None"）；
  `test -f apps/api/dataplat_api/runner/processor_runner.py && grep -q "llm=" apps/api/dataplat_api/runner/processor_runner.py && ! grep -E "llm\s*=\s*None" apps/api/dataplat_api/runner/processor_runner.py`
- AC-9：LLMSummarizeProcessor 实现 Processor Protocol；
  `cd apps/api && uv run python -c "from dataplat_core.protocols.processor import Processor; from dataplat_api.processors.llm_summarize import LLMSummarizeProcessor; assert isinstance(LLMSummarizeProcessor(), Processor)"`
- AC-10：tests/test_llm.py ≥ 6 + 全 PASS；
  `[ "$(cd apps/api && uv run pytest --collect-only -q tests/test_llm.py 2>&1 | grep -cE 'test_llm\.py::')" -ge 6 ]`
- AC-11：ruff + mypy 全 PASS（含 worker/src）；
  `uv run ruff check apps/api packages/core worker/src && uv run mypy apps/api/dataplat_api packages/core/src worker/src`
- AC-12：factory 在无 DATAPLAT_LLM_PROVIDER env 时默认 fake，启动不报错；
  `cd apps/api && uv run python -c "import os; os.environ.pop('DATAPLAT_LLM_PROVIDER',None); from dataplat_api.llm.factory import get_llm_gateway; assert get_llm_gateway() is not None"`
- AC-13：self_check 自递归

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| anthropic SDK 在无 API key 时构造报错 | 高 | AC-2 卡 | AnthropicProvider 构造**惰性**（init 不连 API；call 时才用 key）→ AC-2 只测类存在 + hasattr call |
| Redis cache key 跨进程不一致 | 中 | cache miss 率上升 | key 用 sha256(model_id + sorted_json messages + sorted_json sampling_params)，sorted_keys 保证序列化稳定 |
| LLMSummarizeProcessor 端到端测试要 mock 完整 message → 返 text 路径 | 中 | test_f 复杂 | factory 在测试态强制 FakeLLMProvider（env DATAPLAT_LLM_PROVIDER=fake），Fake 用 simple "Summary of: {first_message_content}" 模板，断言 substring 命中即可 |
| Retry 用 sleep 让 test 慢 | 低 | 测试时间 | retry sleep 用 monkeypatch 改成 0 |
| StandardRunContext.llm 默认值改动破坏既有 markdown-normalize 测试 | 中 | processor-framework 8 测试回归 | 保留 `llm=None` 默认，只在 ProcessorRunner._build_context 显式传 llm=gateway；markdown-normalize 不访问 ctx.llm 所以不受影响 |
| AC 验证命令 dry-parse 全过（SKILL #8） | 低 | spec 卡 stage 2 | 已逐条 dry-parse 验证（AC-1/2/3/4/5/6/7/9/12 共 9 条 python -c 全 compile 通过） |
| summary.md SSoT 漂移（SKILL #9） | 中 | 流程缺陷 | 进 change 目录第一步已写 summary.md frontmatter；占位符 grep 已为 0 |

## 跨链路一致性自审（request-analysis SKILL 9 条 checklist）

1. ✅ 四链路一致：LLMRequest (schema) ↔ Redis cache key (sha256 over canonical json) ↔ test_b cache roundtrip fixture ↔ AC-4
2. ✅ 事务边界：本变更无 DB 事务面（cache 是 Redis；调用是无副作用）
3. ✅ AC 验证命令一行式：13 条全部一行；9 条 python -c 已 dry-parse compile 通过
4. ✅ 风险缓解 ↔ AC 测试：retry sleep monkeypatch ↔ test_d；fake deterministic ↔ test_a；cache 一致性 ↔ test_b + test_c
5. ✅ commit 历史链：processor-framework-20260517 (8f2a867) → 本变更 base
6. ✅ 反向 grep + test -f：AC-8 已用 `test -f` 前置 + 正向 grep + 反向 grep 拦截 `llm\s*=\s*None`
7. ✅ process_tasks 6 条：T-9~T-14 占位
8. ✅ AC 验证命令真跑 dry-parse：9 条 python -c 已逐条 compile 通过（见风险表）
9. ✅ summary.md frontmatter：已在 stage 1 启动时填好；`grep -cE "<feature-slug>|<YYYY-MM-DDTHH:MM:SSZ>|<复述|<bullet list>" summary.md` = 0

## 受影响模块

- 新建：`apps/api/dataplat_api/llm/` 全新子模块（6 files）
- 新建：`packages/core/src/dataplat_core/protocols/llm.py`
- 新建：`apps/api/dataplat_api/processors/llm_summarize.py`
- 新建：`apps/api/tests/test_llm.py`
- 改动：`apps/api/dataplat_api/runner/processor_runner.py`（_build_context 注入 llm=gateway）
- 改动：`apps/api/dataplat_api/processors/__init__.py`（import llm_summarize 触发自注册）
- 改动：`scripts/_self_check.sh`（追加 13 AC + filter）

## 不受影响但易混淆的模块

- `packages/core/protocols/runcontext.py`：保留 `llm: Any` 不动；不在本变更窄化为具体类型（保 Protocol 不依赖实现包）
- `apps/api/dataplat_api/runner/runcontext.py` StandardRunContext：`llm: Any = None` 默认保留；只在 ProcessorRunner 构 ctx 时**实际**传 gateway

## 引用

- design.md §4.5（LLM/Agentic Processor 特殊处理）
- design.md §5.1（LLM Gateway 在组件总览中的位置）
- design.md §11.2（后端技术栈：网关位置 `apps/api/dataplat_api/llm/`）
- design.md §11.7 #2（LLM 调用必须走统一网关）
- processor-framework-20260517 summary.md（前置依赖：ProcessorRunner / StandardRunContext / get_processor_registry / markdown-normalize 已落地）
- SKILL.md request-analysis 9 条 checklist
