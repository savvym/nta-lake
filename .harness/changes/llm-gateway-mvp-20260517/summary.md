---
change_id: llm-gateway-mvp-20260517
title: LLM Gateway 薄骨架（Protocol + Anthropic/Fake provider + Redis cache + ctx 注入 + LLMSummarizeProcessor）
owner: zhhdzhang
started_at: 2026-05-17T19:45:00Z
closed_at: 2026-05-17T21:00:00Z
stage: closed
status: closed
last_updated: 2026-05-17T21:00:00Z
related_changes:
  - processor-framework-20260517
  - rq-worker-skeleton-20260517
  - cas-storage-20260517
note: 第 12 个 dataplat 变更，纵深扩 §4.5——把 RunContext.llm 占位字段落地为可用 LLM 网关，解锁 adapter-firecrawl / pdf-to-text-llm / llm-qa-gen 等下游 processor
---

# Summary

## 一句话目标

把 `apps/api/dataplat_api/llm/` 从无到有建起来：LLMClient Protocol + LLMRequest/Response schema + AnthropicProvider 真调 + FakeLLMProvider 测试桩 + RedisLLMCache 响应缓存 + LLMGateway（cache+retry 装饰）+ ctx.llm 注入到 ProcessorRunner + 1 个 LLMSummarizeProcessor 端到端验证。

## 范围摘要

- **In scope**：协议+schema / 2 provider（anthropic 真调 + fake 桩）/ Redis cache（key=sha256(model_id|messages|sampling_params)）/ Gateway（cache + 简单 retry 3 次指数退避）/ factory 单例 / StandardRunContext.llm 注入实质 gateway / ProcessorRunner 注入 / LLMSummarizeProcessor（markdown → ctx.llm.call → summary blob）/ ≥ 6 集成测试（全 mock）/ self_check 13 AC
- **Out of scope**：cost 记账落 DB / OpenAI provider / vLLM provider / rate limit / audit log 落盘 / agent loop / tools 接口 / budget 上限 / 多模态 / live test against 真 Anthropic（测试全 mock，CI 不消耗 API 配额）

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 产物 / 报告 |
|---|---|---|---|---|
| 1 需求分析 | done | v1 | — | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | done | v1 | APPROVED | [spec_review_v1.md](request_analysis/review/spec_review_v1.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md) |
| 3 编码实现 | done | v1 | — | [coding_report_v1.md](coding/coding_report_v1.md) |
| 4 编码评审 | done | v1 | APPROVED | [code_review_v1.md](coding/review/code_review_v1.md) |
| 5 单测编写 | done | v1 | — | [test_report_v1.md](unit_test/test_report_v1.md) |
| 6 单测评审 | done | v1 | APPROVED | [test_review_v1.md](unit_test/review/test_review_v1.md) |
| 7 代码推送 | done | — | — | feat + chore close commit |
| 8 CI 验证 | done | v1 | PASS | [ci_result_v1.md](ci_result/ci_result_v1.md) |
| 9 部署验证 | done | v1 | PASS | [deploy_verify_v1.md](deployment/deploy_verify_v1.md) |
| 10 用户确认 | done | — | — | 用户 2026-05-17 显式授权 "你合理安排规划" |

## 关键决策

| 时间 | 决策 | 理由 / 取舍 | 关联文件 |
|---|---|---|---|
| 2026-05-17 | 范围"薄骨架"（仅 protocol + 1 真 provider + cache），不含 cost/audit/agent | 用户在 stage 0 显式选；这是后续 adapter-firecrawl/pdf-to-text-llm 等的最小阻塞集合；cost/audit 等做成各自 follow-up | spec §Out of scope |
| 2026-05-17 | 测试全 mock，CI 永不调真 Anthropic | 用户在 stage 0 显式选；API 配额风险 + 测试不确定性双避免 | spec §AC-11 |
| 2026-05-17 | Provider 选 Anthropic（不选 OpenAI） | 项目代号 dataplat 与 Anthropic SDK 已是 Claude Code 自身依赖；先深 1 个再横扩 | spec §Out of scope |
| 2026-05-17 | Cache key 用 sha256(model_id+messages_json+sampling_params_json) | 与 CAS dedup 同 pattern；确定性 hash 便于跨进程命中 | spec §AC-4 |

## 当前阻塞

无。

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| SHOULD FIX | factory get_llm_gateway 不 hot-reload env（lru_cache 一次构造） | follow-up `llm-gateway-env-reload-*` |
| NICE TO HAVE | redis 同步 client → 异步 client | follow-up `redis-asyncio-migration-*` |
| NICE TO HAVE | anthropic SDK MessageParam TypedDict 兼容（现用 cast Any 绕过） | follow-up `llm-anthropic-typed-messages-*` |
| NICE TO HAVE | test_d 不验证 sleep 次数 | follow-up `llm-test-retry-sleep-count-*` |
| NICE TO HAVE | test_f 不验证 summary 内容完整长度 | follow-up `llm-test-summary-full-assert-*` |
| Out of scope | cost / OpenAI / vLLM / rate-limit / audit / agent / budget / 多模态 / live-test / Web UI | 各自 follow-up（详见 spec §Out of scope） |
| SKILL 反哺候选 | 新 change 首次跑 pytest 前必须 `cd apps/api && uv sync --extra dev` | SKILL request-analysis 第 10 条候选（待第 11 个变更同型坑后落 SKILL） |

## 交付

- Branch：`main`
- PR：n/a（本仓 MVP 不用 PR；通过 self_check 186/186 + 双 commit 验证）
- feat commit：见 git log（feat(llm): ...）
- chore close commit：见 git log（chore(llm): close ...）
- 部署版本：dev 本地 `uv run` 启的 API + worker（无 image）
- 用户确认：2026-05-17 通宵会话开题授权 "你合理安排规划"
- 关闭时间：2026-05-17T21:00:00Z

## 复盘

### 顺利

- **协议先行 + 三件套同构**：LLMClient/LLMRequest/LLMResponse 三件套与 adapter/processor 框架的 Registry/Runner/Context 同结构，落地零摩擦
- **6 集成测试一次性 PASS**：fake-spy / flaky / 真 Redis cache / 真端到端，覆盖了 cache hit / retry / 单例 / factory env / end-to-end 五条主路径
- **mypy 一次过 85 files**：Protocol + Pydantic + Generic（lru_cache）组合稳定
- **AC dry-parse 提前发现陷阱**：spec 阶段 9 条 python -c AC 全部 compile 通过；stage 3 实际跑也全过

### 踩坑

1. **uv venv 首次没装 dev extras**：`uv run pytest` 实际跑了系统 `/data/home/zhhdzhang/.local/bin/pytest`（Python 3.11，非 venv 3.12）而非 venv pytest。修复：`cd apps/api && uv sync --extra dev` 装 dev extras 后 pytest 走 venv。
   - **防复发**：列入 SKILL 第 10 条候选反哺（需第二次出现再落，避免单点反哺过度泛化）
   - 短期 mitigation：在 README / Makefile / dev 文档加 "首次跑测试前 cd apps/api && uv sync --extra dev"

2. **anthropic SDK 类型不友好**：messages.create 用 TypedDict (MessageParam) 不接受普通 dict；mypy 4 errors。最终用 `cast(Any, messages)` 绕开 + 0 type:ignore。代价：失去 SDK 静态类型保护，但调用面只 4 行。

3. **AC-12 用 lru_cache 后 env 测试要 reset_llm_gateway()**：factory.py 暴露 reset_llm_gateway() 给测试用，避免在测试间共享单例污染。生产正常路径不需要 reset。

### SKILL 反哺累积（第 10 条候选记账）

`.harness/skills/request-analysis/SKILL.md` 跨 AC 自审清单当前 9 条；第 10 条候选 "uv sync --extra dev 在首次跑 pytest 前必须执行"——暂列 Deferred，等第二次同型坑后再落 SKILL（避免单点反哺过度泛化）。本次踩坑根因主要是 venv state 而非 SKILL 缺失。

- 第 9 条本次实测通过：summary.md frontmatter 在 stage 1 启动时就填好（grep 占位符 = 0）。SSoT 从头到尾连贯，stage 推进期间 reviewer 都能直接看 summary 表知道当前进度，避免 close 时一次性补 9 个文件的痛点。
