---
change_id: operator-eval-gen-20260520
phase: design
status: approved
authored_at: 2026-05-21T14:30:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：operator-eval-gen (W4-8，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

新增 EvalGenOperator：对每条 silver row 调 LLM 生成 1 个多选题（question + 4 options + answer）追加到 `row.stats.eval_items`。

## 背景

W4-8 roadmap：bench 风格 multiple-choice eval generation。这是第一个**真调 LLM** 的 Operator——W2-3 `image_caption_stub` 是纯文本占位、W2-1 suite 全是规则算子。前置 W4-5 cost budget / W4-7 metrics 已就位，本算子上线即被这两个切面自动覆盖。

**关键技术约束**：当前 `Operator.run()` 是同步签名（`-> list[SilverRow]`），但 LLMGateway.call() 是 `async`。两种解法：

1. **改 Operator Protocol 为可选 async**（W4-8 决策选）：在 `run_recipe_v2` 里检测 `asyncio.iscoroutine(result)` → `await`。Protocol 文档加一句"run 可返 coroutine"；现有 8 个 sync operator 不动。
2. 改全部 8 个 operator 都 async（拒）：8 个 file 都加 async；测试也都加 mark；改动量大；风险面广；同步算子语义上没必要 async。

选 (1)：1 个 elif 分支 + 1 行 Protocol 注释；现有 sync operator 零改动；eval_gen 自己 `async def run`。

**LLM 接入方式**：Operator 不直接 import `LLMGateway`（packages/core 不能依赖 apps/api）；而是通过 `ctx.llm.call(req)` —— `ctx.llm` 是 RunContext Protocol 的 attribute（W4-5 设计已在 protocols/runcontext.py 占位），具体注入由 caller（test fixture 或 worker）负责。本 change：
- packages/core 测试用 inline FakeLLMClient（返固定 JSON 串）
- apps/api 测试或 worker 接入真 gateway 是 follow-up（worker / pipeline runner 改造）

## 范围

In scope：

- `packages/core/src/dataplat_core/protocols/operator.py`（小改，+3 行注释）：
  - Protocol docstring 添加："`run` 可返 `list[SilverRow]` 同步或 `Coroutine[list[SilverRow]]` 异步；executor 自动 await"
- `packages/core/src/dataplat_core/operators/eval_gen.py`（新，~120 行）：
  - `class EvalGenOperator`：
    - `name: str = "eval_gen"`、`version: str = "1.0"`
    - `spec: OperatorSpec(...config_schema={...})`
    - config_schema 字段：
      - `model_id: str`（默认 `"fake-model"`；CI 友好）
      - `max_tokens: int`（默认 512）
      - `prompt_template: str`（默认见下）；可用变量 `{text}`、`{lang}`
      - `n_per_row: int`（默认 1；预留 1→N 扩展，本 change 实现只生成 1 条 / row）
      - `skip_if_text_chars_lt: int`（默认 50；短文本跳过 LLM 调用，行为=1→1 仅 append lineage_ops）
    - 默认 prompt template：
      ```
      根据以下文本生成 1 道多选题（中文输出 JSON，禁止任何额外文字）。
      要求：
      - 题干 question 简洁明确
      - 4 个选项 A/B/C/D 单一正确答案
      - answer 是单字符 'A' 'B' 'C' 'D'
      - 题目内容必须能由文本支持，不可外推
      
      文本：
      ```
      {text}
      ```
      
      JSON schema：
      {
        "question": "string",
        "options": {"A": "string", "B": "string", "C": "string", "D": "string"},
        "answer": "A" | "B" | "C" | "D"
      }
      ```
    - `async def run(row, config, ctx) -> list[SilverRow]`：
      1. 若 `len(row.text) < skip_if_text_chars_lt` → return [row_with_appended_lineage_op_only]（标记 `skipped: short_text`）
      2. 拼 prompt（`prompt_template.format(text=row.text, lang=row.lang or "unknown")`）
      3. 构造 `LLMRequest(model_id, messages=[LLMMessage(role="user", content=prompt)], max_tokens)`
      4. `resp = await ctx.llm.call(req)` 
      5. 解析 `resp.text`：strip + 去 markdown code fence（`json` / ` ``` `）→ `json.loads`
      6. 解析失败（JSONDecodeError / 缺字段 / answer 不在 ABCD / options 不齐 4 项）→ 不抛，append lineage_op + `eval_items: [{"error": "parse_failed", "raw": resp.text[:200]}]`；记 stats.eval_gen_parse_errors += 1
      7. 解析成功 → append `eval_items: [{question, options, answer}]`、stats.eval_gen_count += 1、lineage_ops 追加 `{op: "eval_gen", version: "1.0", model_id, parse_ok: true}`
      8. 返 `[new_row]`（始终 1→1）
- `packages/core/src/dataplat_core/operators/registry.py`（小改）：注册 `EvalGenOperator`
- `packages/core/src/dataplat_core/operators/__init__.py`（小改）：export
- `packages/core/src/dataplat_core/recipe.py`（小改，+5 行）：
  - operator 循环里支持 sync/async 双形态：
    ```python
    for row in rows:
        result = op.run(row, op_spec.config, ctx)
        if asyncio.iscoroutine(result):
            result = await result
        new_rows.extend(result)
    ```
- 测试：
  - `packages/core/tests/test_operator_eval_gen.py`（新，5 tests）：
    - happy path：FakeLLMClient 返合法 JSON → stats.eval_items 含 1 题 + 4 选项 + answer + parse_ok=True
    - short text skip：text 长度 < 50 → 仅追加 lineage_op + stats 含 skipped=short_text；**FakeLLMClient.call 未被调用**（通过计数器断言）
    - parse failure：FakeLLMClient 返 `"not json"` → stats.eval_items 含 `{"error": "parse_failed", "raw": ...}` + 不抛
    - markdown fence 包裹：FakeLLMClient 返 ` ```json\n{...}\n``` ` → 仍能解析成功
    - answer 非 ABCD 之一：FakeLLMClient 返 `{..., "answer": "E"}` → 视为 parse failure
  - `packages/core/tests/test_recipe_v2.py`（改 +1 test）：
    - `test_run_recipe_v2_supports_async_operator`：跑含 EvalGenOperator + FakeLLMClient 的 recipe → 完成 + metrics 含 1 个 eval_gen entry

Out of scope：

- **不**做 n_per_row > 1 真生成（schema 留字段；行为先返 1）：留 follow-up `operator-eval-gen-multi-*`
- **不**做 retry on parse fail（schema 错 → 标 error 不重试）：留 follow-up `operator-eval-gen-retry-*`
- **不**做 prompt 模板从 file 加载：MVP；模板字符串内联；follow-up `operator-eval-gen-prompt-file-*`
- **不**接 apps/api 集成（端到端 RunContext.llm 注入 gateway）：留 follow-up `pipeline-runner-llm-injection-*`（要改 worker / orchestrator，独立改动量）
- **不**做 web UI（dashboard / 触发 / 预览生成的题目）：留 follow-up `web-eval-preview-*`
- **不**做 dpo-pair-gen（W4-9 已规划独立 change，依赖本 change）
- **不**改 W1..W4-7 已 merge 产物，除 protocols/operator.py 加 1 行注释 + recipe.py +5 行
- **不**做 alembic migration / DB schema

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | EvalGenOperator + 注册存在 | `python -c "from dataplat_core.operators.registry import OperatorRegistry; from dataplat_core.operators.eval_gen import EvalGenOperator; assert OperatorRegistry.get('eval_gen') is EvalGenOperator; print('OK')"` | 输出 OK |
| AC-2 | behavioral | eval_gen 5 行为测试 | `cd packages/core && uv run pytest tests/test_operator_eval_gen.py -x -q` | 5 passed |
| AC-3 | behavioral | run_recipe_v2 支持 async operator | `cd packages/core && uv run pytest tests/test_recipe_v2.py::test_run_recipe_v2_supports_async_operator -x -q` | 1 passed |
| AC-4 | behavioral | 全 packages/core 测试基线无回归 | `cd packages/core && uv run pytest -x -q` | ≥ 108 passed（102 基线 + 6 new） |

## 决策

1. **Operator Protocol 改 union sync/async**：最小 surface 改动（1 行注释 + run_recipe_v2 5 行）；现有 sync operator 不动。理由：Operator 接口本质上是"row → rows"的纯函数式契约；是否 async 是实现细节；统一签名要求所有 operator 都 async 是过度规范化。
2. **eval_gen 走 ctx.llm 而非 import LLMGateway**：packages/core 不依赖 apps/api；遵循 [W4-5 cost 决策 8] 同模式。测试用 inline FakeLLMClient，真 gateway 注入留 follow-up（worker 改造）。
3. **n_per_row 字段保留但本 change 只实现 1**：避免下次扩展时改 schema；行为暂时按 1 锁死（spec 内显式注释）。
4. **short_text skip 阈值 50**：避免对 1-2 句话调 LLM 浪费 cost；50 字符约 1 句中文 / 2-3 句英文；可配置。
5. **parse failure 不抛 exception**：integration 链路应当 graceful 降级；用 stats.eval_gen_parse_errors 计数 + error 记入 eval_items；下游可 filter 掉 error row 或单独看 raw。
6. **eval_items 写入 stats 而非 row.text**：保持 text 不变（W3-7 export 看 text 字段时不被污染）；stats 是 dict[str, Any]，结构自由；UI / 后续 operator 可读 stats.eval_items。
7. **lineage_ops 追加 `{op: "eval_gen", version: "1.0", model_id, parse_ok: bool}`**：与 W2-1 score / image_strip 同模式；血缘可追溯哪个 model + 是否解析成功。
8. **markdown fence 自动剥离**：anthropic / openai 模型常在 JSON 外裹 ` ```json ... ``` `；先 strip 再 json.loads；提升 happy path 命中率。
9. **默认 `model_id="fake-model"`**：CI / 单测默认走 fake；DEFAULT_RATES 已含 fake-model 价格 0；不被 cost budget 阻断；真生产 user 显式改 recipe.yaml。
10. **prompt 用中文模板 + JSON 输出指令**：项目语言偏好中文（per memory [[doc_language_chinese]]）；JSON schema 明示防 LLM 自由输出。
11. **不强制 row.lang 为中文**：prompt 模板含 `{lang}` 占位但默认值是 "unknown"；多语料训练数据兼容；模型自己决定生成什么语言（real world：lang=en 多半返英文题目）。
12. **registry.register 在 module 末尾**：与 W2-1 同模式；import 顺序保 OperatorRegistry 单例就位。

## 风险

| 风险 | 缓解 |
|---|---|
| run_recipe_v2 加 iscoroutine 检查影响现有 sync operator 性能 | iscoroutine 检查 ~纳秒级；可忽略；现有 [filter, chunker, snapshot_tag] 测试通过即验证 |
| FakeLLMClient 与 RunContext.llm 接口不匹配 | RunContext.llm 是 `Any` Protocol；测试 fixture 自由构造；只要满足 `async def call(req) -> LLMResponse` |
| eval_gen 在大 row 上 prompt 过长导致 LLM 400 / OOM | max_tokens 限制 output；input 由 model context window 兜底；用户调 recipe.yaml 改 model_id / 截 text 用 chunker 前置 |
| LLM 返非确定 JSON 结构 | 解析失败标 parse_failed 不抛；user 看 stats.eval_gen_parse_errors 决定换 model / 改 prompt |
| async iscoroutine 在 PyPy / cython 实现差异 | CPython 标准库 asyncio.iscoroutine 跨实现一致；不引入额外风险 |
| 测试用 FakeLLMClient 不能 cover 真 LLM 边缘 | OK；本 change 只验证算子逻辑；真 LLM 验由 follow-up integration test 跑 |
| 测试 fixture 注入 ctx.llm 与 W2-5 现有 ctx (FakeRunContext) 协议冲突 | FakeRunContext 用 `Any` 属性；新增 llm attribute 不冲突；如缺手补 |
| W4-5 cost budget 在 fake-model rate=0 下永不阻断 | 设计如此（CI 友好）；真生产 user 切真 model_id 时 budget 自然生效 |
| W4-7 metrics 在 async operator 下埋点正确性 | run_recipe_v2 埋点逻辑只在 operator 完成后 record；async/sync 都先 await 再 record；不需改 metrics 代码 |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/protocols/llm.py`（LLMRequest / LLMResponse / LLMClient Protocol）
  - `packages/core/src/dataplat_core/protocols/runcontext.py`（RunContext.llm 占位）
  - `packages/core/src/dataplat_core/protocols/loader.py::SilverRow`
  - `packages/core/src/dataplat_core/operators/registry.py`（pattern + register call 位置）
  - `packages/core/src/dataplat_core/operators/score.py`（结构 + lineage_ops 模式）
- 应当不动：
  - `apps/api/dataplat_api/llm/gateway.py`（cost / retry 切面，本 change 不动）
  - `apps/api/dataplat_api/llm/cost.py`（本 change 不动）
  - W1..W4-7 已 merge 产物（除 protocols/operator.py 注释 + recipe.py operator 循环 sync/async 支持）
- 引用的其他 change：W4-5（LLMGateway + cost），W4-7（metrics 埋点），W2-1（operator suite 结构）

## 关联 follow-up

- `operator-eval-gen-multi-*`：n_per_row > 1 真生成多题
- `operator-eval-gen-retry-*`：parse fail 时重试 + 不同模型重试
- `operator-eval-gen-prompt-file-*`：prompt 模板从 YAML / file 加载
- `pipeline-runner-llm-injection-*`：worker / orchestrator 把真 LLMGateway 注入 RunContext.llm
- `web-eval-preview-*`：UI 看生成的题目 + 标注
- `operator-dpo-pair-gen-*`：W4-9（依赖本 change 的 LLM-in-operator 模式）
- `operator-eval-jsonl-export-*`：单独导出 eval_items 为 bench 格式（如 GLUE / MMLU 样式）
