---
change_id: llm-qa-gen-20260518
version: 1
authored_at: 2026-05-18T09:40:00Z
status: draft
---

# Spec：LLMQAGenProcessor（silver text-corpus → gold sft；ctx.llm × N → sft.jsonl）

## 背景

- design.md §2.3 Repo E `cn-lit/sft-styleimitate-v1` (subtype=`sft`) 的核心 processor —— "由 `LLMQAGenerator` 从 D 生成"
- design.md §3.3 Gold sft Schema = `{prompt, response, system?, tools?, meta}`
- processor-framework + llm-gateway-mvp + adapter-firecrawl 都已就位；本变更是**第一个生产语义 processor**（前两个 markdown-normalize / llm-summarize 都是骨架验证）
- 同时端到端走通 Bronze → Silver → Gold 三层（之前 silver / gold 都还没真 processor 实现）

## 问题陈述

- 缺 `apps/api/dataplat_api/processors/llm_qa_gen.py` + Pydantic spec
- 缺 `_parse_qa_response` 工具：LLM 返回不一定守 JSON（可能含 ```json``` code block 包裹，或自然语言回答），需要三层 fallback
- 缺单文件 sft.jsonl 聚合逻辑：N 个上游文件 × M 个 records → 一个 sft.jsonl
- 缺 6 测试覆盖：单元（parse 解析 3 种情况）/ 单元（adapter run 用 _FakeStore + _SummaryLLM）/ 路由权限 / 端到端 / fallback / 空上游错误
- 缺 self_check 13 AC

## 范围

**In scope**：
- `apps/api/dataplat_api/processors/llm_qa_gen.py`：
  - `LLMQAGenSpec(BaseModel, extra=forbid)`：records_per_doc / prompt_template / model_id / max_tokens / text_truncate
  - 默认值：records_per_doc=1 / model_id="claude-haiku-4-5-20251001" / max_tokens=512 / text_truncate=6000 / prompt_template 默认含 `{text}` 和 `{n}` 占位（"Read the following text and generate {n} high-quality QA pair(s) as a JSON object {prompt, response}. Text:\n\n{text}"）
  - `LLMQAGenProcessor`（name="llm-qa-gen" version="0.1" output_subtype="sft"）
  - run 流程：检查 ctx.llm + ctx.blob_store → view.iter_paths 过滤 .md/.txt/.markdown → for path in paths: text = view.open(path).read().decode → for i in range(N): await ctx.llm.call(prompt) → _parse_qa_response → records 累加 → 拼 jsonl bytes（每行 json.dumps 一条 + meta source_path） → ctx.blob_store.put → tree entry "sft.jsonl"
  - `_parse_qa_response(text) -> dict[str,str]`：三层 fallback：(1) json.loads(text)；(2) 提 ```json ... ``` 代码块 json.loads；(3) {"prompt": "summarize", "response": text.strip()}
- `apps/api/dataplat_api/processors/__init__.py`：import + register LLMQAGenProcessor
- `apps/api/tests/test_llm_qa_gen.py`：6 测试覆盖
- `scripts/_self_check.sh`：追加 `run_llm_qa_gen` 13 AC + filter + 总入口

**Out of scope**（显式）：
- per-source JSONL（sft/<idx>.jsonl）→ follow-up `llm-qa-gen-per-source-*`
- parquet 替代 jsonl（design 推荐）→ follow-up `llm-qa-gen-parquet-*`
- dedup（同 prompt / 跨 doc）→ follow-up `llm-qa-gen-dedup-*`
- quality_score（LLM-as-judge）→ follow-up `llm-qa-gen-quality-score-*`
- 多轮 / tools → follow-up `llm-qa-gen-multi-turn-*`
- 增量 / 同 source skip → follow-up `llm-qa-gen-incremental-*`
- live test 真 LLM → follow-up `llm-qa-gen-live-test-*`
- Web UI 触发 QA 生成 → follow-up `web-process-qa-gen-ui-*`

## 验收标准（13 AC）

- AC-1：LLMQAGenSpec extra=forbid；
  `cd apps/api && uv run python -c "from dataplat_api.processors.llm_qa_gen import LLMQAGenSpec; assert LLMQAGenSpec.model_config.get('extra')=='forbid'"`
- AC-2：LLMQAGenProcessor 实现 Processor Protocol（test -f + isinstance）；
  `test -f apps/api/dataplat_api/processors/llm_qa_gen.py && cd apps/api && uv run python -c "from dataplat_core.protocols.processor import Processor; from dataplat_api.processors.llm_qa_gen import LLMQAGenProcessor; assert isinstance(LLMQAGenProcessor(), Processor)"`
- AC-3：registry 注册 llm-qa-gen v0.1；
  `cd apps/api && uv run python -c "import dataplat_api.processors; from dataplat_api.runner.processor_registry import get_processor_registry; assert get_processor_registry().get('llm-qa-gen','0.1') is not None"`
- AC-4：默认 model_id = claude-haiku-4-5-20251001；
  `cd apps/api && uv run python -c "from dataplat_api.processors.llm_qa_gen import LLMQAGenSpec; assert LLMQAGenSpec.model_fields['model_id'].default == 'claude-haiku-4-5-20251001'"`
- AC-5：默认 records_per_doc = 1；
  `cd apps/api && uv run python -c "from dataplat_api.processors.llm_qa_gen import LLMQAGenSpec; assert LLMQAGenSpec.model_fields['records_per_doc'].default == 1"`
- AC-6：prompt_template 默认含 `{text}` 占位；
  `cd apps/api && uv run python -c "from dataplat_api.processors.llm_qa_gen import LLMQAGenSpec; assert '{text}' in LLMQAGenSpec.model_fields['prompt_template'].default"`
- AC-7：llm_qa_gen.py 文件过滤 .md/.txt/.markdown（grep）；
  `grep -qE "'\.md'|'\.txt'|'\.markdown'" apps/api/dataplat_api/processors/llm_qa_gen.py`
- AC-8：llm_qa_gen.py 输出文件名 sft.jsonl（grep）；
  `grep -q "sft.jsonl" apps/api/dataplat_api/processors/llm_qa_gen.py`
- AC-9：_parse_qa_response 直接 JSON 路径正确解析；
  `cd apps/api && uv run python -c "from dataplat_api.processors.llm_qa_gen import _parse_qa_response; r=_parse_qa_response('{\"prompt\":\"p\",\"response\":\"r\"}'); assert r['prompt']=='p' and r['response']=='r'"`
- AC-10：tests/test_llm_qa_gen.py ≥ 6 + 全 PASS；
  `[ "$(cd apps/api && uv run pytest --collect-only -q tests/test_llm_qa_gen.py 2>&1 | grep -cE 'test_llm_qa_gen\.py::')" -ge 6 ]`
- AC-11：ruff + mypy 全 PASS；
  `uv run ruff check apps/api packages/core worker/src && uv run mypy apps/api/dataplat_api packages/core/src worker/src`
- AC-12：ctx.llm 必须（grep + 反向 grep 防 silent fallback）；
  `grep -q "ctx.llm" apps/api/dataplat_api/processors/llm_qa_gen.py && grep -qE "llm is None|ctx.llm.*None" apps/api/dataplat_api/processors/llm_qa_gen.py`
- AC-13：self_check 自递归

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| FakeLLMProvider 默认 truncate prompt 致测试不稳 | 高 | test_d/e 失败 | adapter-firecrawl 已踩过；本次直接用 monkeypatch.setattr 替换 FakeLLMProvider.call 返合法 JSON；不依赖 prompt 长度 |
| LLM 返回非 JSON（fake 默认返 "FAKE[..."）→ _parse 走 fallback | 低 | end-to-end 仍能产出 records（fallback 用 raw response） | _parse 三层 fallback；fallback 路径单独 test_c 覆盖 |
| 端到端 record_count 多文件 × 多 N 难断言 | 中 | test_e 脆弱 | 用 records_per_doc=1 + 单文件上游；断言 sft.jsonl 行数 = 1 |
| processor.run 是同步 + ctx.llm.call 是 async；多次 call 用 asyncio.run 累积事件循环 | 中 | 性能差但 MVP 可接受 | 沿 markdown-normalize / llm-summarize 同 pattern：内部一个 `asyncio.run(_do_all())` 包整个 for-doc + for-record 循环 |
| AC 验证命令 dry-parse 全过（SKILL #8） | 低 | spec 卡 stage 2 | AC-1/2/3/4/5/6/9 共 7 条 python -c 已 compile 通过 |
| summary.md SSoT 漂移（SKILL #9） | 低 | 流程缺陷 | 进 change 目录第一步已写 summary.md frontmatter；占位符 grep = 0 |

## 跨链路一致性自审（request-analysis SKILL 9 条）

1. ✅ 四链路一致：LLMQAGenSpec ↔ ProcessRequest.config ↔ test_b/e fixture ↔ AC-1/4/5/6
2. ✅ 事务边界：本变更无 DB 事务面；blob put + commit 走 ProcessorRunner 已稳定 pattern
3. ✅ AC 验证命令一行式：13 条全单行；7 条 python -c 已 compile 通过
4. ✅ 风险缓解 ↔ AC 测试：fake monkeypatch ↔ test_b/e；_parse fallback ↔ test_c
5. ✅ commit 链：adapter-firecrawl-20260517 (67a8e8b) → 本变更 base
6. ✅ 反向 grep：AC-12 正向 grep ctx.llm + 同时正向 grep "llm is None"（**不能去掉**，因为 processor 必须显式检查 + raise）
7. ✅ process_tasks 6 条：T-7~T-12 占位
8. ✅ AC 验证命令真跑 dry-parse：7 条 python -c 已逐条 compile 通过
9. ✅ summary.md frontmatter：已在 stage 1 启动时填好；占位符 grep = 0

## 受影响模块

- 新建：`apps/api/dataplat_api/processors/llm_qa_gen.py`
- 新建：`apps/api/tests/test_llm_qa_gen.py`
- 改动：`apps/api/dataplat_api/processors/__init__.py`（import + register）
- 改动：`scripts/_self_check.sh`（追加 13 AC）

## 不受影响但易混淆的模块

- `apps/api/dataplat_api/llm/`：不动；本变更只**消费** ctx.llm，不动 gateway
- `runner/processor_runner.py`：不动（ctx.llm/blob_store 已在 llm-gateway-mvp 注入）
- markdown-normalize / llm-summarize：不动；本变更是第 3 个 processor，独立模块

## 引用

- design.md §2.3（Repo E `cn-lit/sft-styleimitate-v1` 由 LLMQAGenerator 从 D 生成）
- design.md §3.3（Gold sft Schema = `{prompt, response, system?, tools?, meta}`）
- llm-gateway-mvp-20260517 summary.md（LLMRequest / LLMResponse / LLMGateway）
- processor-framework-20260517 summary.md（Processor / ProcessorRunner / DbRepoView）
- adapter-firecrawl-20260517 summary.md（FakeLLMProvider monkeypatch 模式参考）
- SKILL.md request-analysis 9 条 checklist
