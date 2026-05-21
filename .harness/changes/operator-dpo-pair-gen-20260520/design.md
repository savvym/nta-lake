---
change_id: operator-dpo-pair-gen-20260520
phase: design
status: approved
authored_at: 2026-05-21T15:30:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：operator-dpo-pair-gen (W4-9，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

新增 DPOPairGenOperator：对每条 silver row 调 LLM 2 次（chosen 走完整指令 / rejected 走"低质量"指令）→ 写 `row.stats.dpo_pairs = [{prompt, chosen, rejected}]`。

## 背景

W4-9 roadmap：DPO preference pair generation。DPO（Direct Preference Optimization）训练数据需 `(prompt, chosen_response, rejected_response)` 三元组。本算子产线化构造它：同一 prompt 走两次 LLM——`chosen` 用高质量指令 / `rejected` 用刻意降级指令——形成偏好对。

前置 W4-8 已落 LLM-in-operator 模式：
- `ctx.llm.call(req)` 接入（packages/core 不直接依赖 apps/api）
- `async def run` 通过 `run_recipe_v2` 的 iscoroutine 分支自动 await
- Cost budget / metrics 切面自动覆盖（W4-5 / W4-7）

本 change 几乎完全复用 W4-8 的 EvalGenOperator 实现骨架（同样的 short-text skip / parse-failure graceful / lineage_ops 追加），但：
- **2 次 LLM 调用**：先 chosen prompt 再 rejected prompt（**串行**；并行用 `asyncio.gather` 留 follow-up）
- **解析逻辑更宽松**：chosen / rejected 都是自由文本（LLM 续写），不要求 JSON
- **失败语义**：任一调用失败 → 标 pair_failed 不抛；不写 dpo_pairs entry
- **lineage_ops + stats 字段**：`{op: "dpo_pair_gen", version, model_id, chosen_tokens, rejected_tokens}` + `stats.dpo_pair_count` / `stats.dpo_pair_failures`

## 范围

In scope：

- `packages/core/src/dataplat_core/operators/dpo_pair_gen.py`（新，~140 行）：
  - `class DPOPairGenOperator`：
    - `name: str = "dpo_pair_gen"`、`version: str = "1.0"`
    - config_schema 字段：
      - `model_id: str`（默认 `"fake-model"`）
      - `max_tokens: int`（默认 512）
      - `prompt_template: str`（默认见下；可用变量 `{text}` `{lang}`）
      - `chosen_instruction: str`（默认 "请仔细阅读以上文本，写一份完整、准确、有条理的回答。"）
      - `rejected_instruction: str`（默认 "请用简单粗暴的方式回答，可省略细节，可包含小错误。"）
      - `skip_if_text_chars_lt: int`（默认 50）
    - 默认 prompt_template：
      ```
      根据以下文本生成 1 个开放式问题，并给出回答。
      
      文本：
      ```
      {text}
      ```
      
      问题（请基于文本生成一个有信息量的开放式问题，不要求选择题）：
      然后请按 {instruction} 回答这个问题。
      ```
    - `async def run(row, config, ctx) -> list[SilverRow]`：
      1. short-text skip：`len(row.text) < skip_if_text_chars_lt` → 仅追 lineage_op + stats.skipped="short_text"
      2. **chosen 调用**：拼 prompt（用 chosen_instruction）→ `await ctx.llm.call(...)` → 失败（exception / 空文本）→ 标 pair_failed=True
      3. **rejected 调用**：拼 prompt（用 rejected_instruction）→ `await ctx.llm.call(...)` → 失败同上
      4. 任一失败 → `dpo_pairs` 不追加 + `stats.dpo_pair_failures += 1` + lineage_ops 追 `{op, version, model_id, success: False, reason}`
      5. 两次成功 → 提取 prompt（chosen response 的"问题"部分；为简化 MVP 直接用 row.text[:200] 作 prompt，**不真从 LLM 输出抽取**；自动抽取留 follow-up），追加 `{prompt: row.text[:200], chosen: chosen_resp.text, rejected: rejected_resp.text}` 到 stats.dpo_pairs + stats.dpo_pair_count += 1 + lineage_ops 追 `{op, version, model_id, success: True, chosen_tokens, rejected_tokens}`
      6. 始终 1→1（成功失败都返 1 row）
- `packages/core/src/dataplat_core/operators/registry.py`（小改）：注册 `DPOPairGenOperator`
- `packages/core/src/dataplat_core/operators/__init__.py`（小改）：export
- 测试：
  - `packages/core/tests/test_operator_dpo_pair_gen.py`（新，5 tests）：
    - happy path：FakeLLMClient 2 次都返合法文本 → stats.dpo_pairs 含 1 entry + prompt/chosen/rejected 字段齐 + dpo_pair_count=1
    - short_text_skip：text < 50 → llm 未调用（0 次）+ stats.skipped + 不追 dpo_pairs
    - chosen_failure：FakeLLMClient 第 1 次抛 exception → 不抛 + stats.dpo_pair_failures=1 + 不追 dpo_pairs + lineage_ops 含 success=False
    - rejected_failure：第 2 次抛 → 同上
    - empty_response：FakeLLMClient 返 text="" → 视为失败 + stats.dpo_pair_failures=1
  - `packages/core/tests/test_operator_dpo_pair_gen.py` 还含 1 个 integration：
    - `test_registry_lookup`：OperatorRegistry.get("dpo_pair_gen") is DPOPairGenOperator

Out of scope：

- **不**做真从 LLM 输出抽取 prompt（MVP 直接 text 前缀）：留 follow-up `operator-dpo-prompt-extract-*`
- **不**做并行 2 LLM 调用（asyncio.gather）：串行更易理解错误归因；并行 follow-up `operator-dpo-parallel-*`
- **不**做 chosen / rejected 用不同 model_id（如 chosen=opus / rejected=haiku）：MVP 同 model 不同 instruction；follow-up `operator-dpo-mixed-models-*`
- **不**做 retry on LLM error：单次失败即标 pair_failed；retry follow-up `operator-dpo-retry-*`
- **不**接 apps/api 集成（pipeline runner 注入真 gateway）：与 W4-8 同 follow-up `pipeline-runner-llm-injection-*`
- **不**做 web UI（dpo pair 预览）：follow-up `web-dpo-pair-preview-*`
- **不**做 dpo 单独导出格式（如 HF datasets DPO loader）：follow-up `gold-exporter-dpo-*`
- **不**改 W1..W4-8 已 merge 产物（registry / __init__.py 注册除外）

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | DPOPairGenOperator + 注册存在 | `python -c "from dataplat_core.operators.registry import OperatorRegistry; from dataplat_core.operators.dpo_pair_gen import DPOPairGenOperator; assert OperatorRegistry.get('dpo_pair_gen') is DPOPairGenOperator; print('OK')"` | 输出 OK |
| AC-2 | behavioral | dpo_pair_gen 5 行为测试 | `cd packages/core && uv run pytest tests/test_operator_dpo_pair_gen.py -x -q` | ≥ 5 passed |
| AC-3 | behavioral | run_recipe_v2 跑含 dpo_pair_gen 的 recipe → 完成 + metrics 含 dpo_pair_gen entry | `cd packages/core && uv run pytest tests/test_recipe_v2.py::test_run_recipe_v2_supports_async_operator -x -q`（**复用 W4-8 测试，dpo 只是另一种 async operator**，本 change 不新增该测试） | 1 passed |
| AC-4 | behavioral | 全 packages/core 测试基线无回归 | `cd packages/core && uv run pytest -x -q` | ≥ 113 passed（108 基线 + 5 new dpo + 0 registry test merged into file） |

> 注：AC-3 显式声明复用 W4-8 已落 test（async operator 通用支持），本 change 不重复造；reviewer 跑这条只是验证 dpo 不破现有 async 路径。

## 决策

1. **复用 W4-8 实现骨架**：架构上 dpo_pair_gen 与 eval_gen 是兄弟算子（都调 LLM、都 1→1、都写 stats）；拷贝 + 改 prompt 模板 + 改输出 schema；不抽公共基类（提早抽象 = 过早泛化，违反 CLAUDE.md "三相似优于过早抽象"）。
2. **串行 2 调用而非并行 asyncio.gather**：错误归因更容易（chosen / rejected 哪个失败一目了然）；fake-model 测试也更可预测；并行优化留 follow-up。
3. **prompt 字段简化为 row.text[:200]**：真正"问题抽取"涉及 LLM 第 3 次调用 / regex parse；MVP 接受 prompt = source text 前缀，让 chosen / rejected 是"对同一上下文的不同质量回答"。这与 DPO 论文经典 setup（同 prompt + 两 response）语义一致。
4. **rejected 用降级 instruction 而非另一个低质量 model**：单一 model_id 简化 cost / metrics 归因；instruction-based degradation 是文献常用方式（如 SFT model 在 system prompt 切换下生成弱回答）。混合模型 follow-up。
5. **失败 graceful 不抛**：与 W4-8 eval_gen 同模式；下游可 filter 掉 dpo_pair_count=0 的 row。
6. **lineage_ops 含 chosen_tokens / rejected_tokens**：W4-5 cost 切面已记 ledger；这里再记 lineage 便于"per-row cost 归因"未来 follow-up。
7. **不引入新依赖**：FakeLLMClient 已在 W4-8 测试中存在；本 change 测试复用同模式 inline 构造。
8. **registry 注册位置**：与 W4-8 同——module 末尾 `OperatorRegistry.register(DPOPairGenOperator)`。
9. **`empty_response` 视为失败**：LLM 返空字符串通常是 prompt 触发拒答 / max_tokens=0；不应视为合法 chosen/rejected；标 failure 让 user 知道质量问题。
10. **`text[:200]` 中文截断风险**：Python str 切片按 unicode codepoint，不会切坏中文字符；接受 200 char 上限（中文 ≈ 100 字够 prompt 上下文）。
11. **测试覆盖 5 个场景**：happy / short_text / chosen_fail / rejected_fail / empty_response；分别覆盖 normal path + 早返 + 两个失败分支 + 空响应判定。
12. **不写 test_recipe_v2 新 case**：W4-8 已落 `test_run_recipe_v2_supports_async_operator`；dpo_pair_gen 通过 OperatorRegistry 注册即被 async 路径覆盖；新增 case 会重复造轮子。

## 风险

| 风险 | 缓解 |
|---|---|
| 2 次 LLM 调用 cost 翻倍 | W4-5 cost budget 自动卡（fake-model rate=0 不被阻；真 model 走 budget）；user 可调 model_id |
| rejected instruction "可包含小错误" 可能触发 LLM 拒答 | empty_response 视为失败标 pair_failed；user 看 metrics 决定换 instruction |
| chosen / rejected 文本太相似（model 不 follow instruction degradation） | MVP 接受；future evaluation 用 reward model 二筛 follow-up `operator-dpo-reward-filter-*` |
| stats.dpo_pairs 字段大（chosen + rejected 长文本） | 单 row 仅 1 pair；DPO 训练通常每 row 1 对；体积可控 |
| FakeLLMClient 接口与 W4-8 不一致 | 本 change inline 构造 FakeLLMClient（与 W4-8 test 同模式）；不复用 W4-8 测试文件 fixture（避免跨 file import 复杂） |
| 测试 fake llm 抛 exception 时 retry / iscoroutine 行为 | 测试明确：exception 在 `await ctx.llm.call(req)` 处冒泡；operator try/except 包 → 标 failure；不抛到 run_recipe_v2 |
| short_text=50 阈值与 W4-8 一致 | 一致设计；user 觉得 50 太小可改 config；默认对齐 |
| W4-8 metrics 在 dpo_pair_gen 1→1 下计数正确 | metrics 记 rows_in / rows_out=均 1；不依赖 stats.dpo_pair_count |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/protocols/llm.py`（LLMRequest / LLMResponse / LLMClient）
  - `packages/core/src/dataplat_core/protocols/runcontext.py`（ctx.llm 占位）
  - `packages/core/src/dataplat_core/protocols/loader.py::SilverRow`
  - `packages/core/src/dataplat_core/operators/eval_gen.py`（W4-8 sibling，结构参考）
  - `packages/core/src/dataplat_core/operators/registry.py`（pattern）
  - `packages/core/src/dataplat_core/recipe.py`（W4-8 改的 iscoroutine 分支已覆盖）
- 应当不动：
  - `apps/api/dataplat_api/llm/gateway.py` / `cost.py`
  - W1..W4-8 已 merge 产物（除 operators/registry.py + __init__.py 注册新 op）
- 引用的其他 change：W4-8（eval_gen 模式 + async operator 支持），W4-7（metrics 覆盖），W4-5（cost 覆盖）

## 关联 follow-up

- `operator-dpo-parallel-*`：asyncio.gather 并行 2 LLM 调用
- `operator-dpo-mixed-models-*`：chosen / rejected 用不同 model_id
- `operator-dpo-prompt-extract-*`：从 LLM 输出真正抽取 prompt（不用 text 前缀）
- `operator-dpo-retry-*`：失败时重试
- `operator-dpo-reward-filter-*`：reward model 二筛保留质量真有差距的 pair
- `pipeline-runner-llm-injection-*`：worker / orchestrator 注入 LLMGateway 到 ctx.llm
- `gold-exporter-dpo-*`：DPO 格式专用 exporter
- `web-dpo-pair-preview-*`：UI 看 chosen vs rejected diff
