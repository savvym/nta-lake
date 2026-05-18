---
change_id: llm-qa-gen-20260518
version: 1
authored_at: 2026-05-18T09:45:00Z
---

# Tasks

## T-1 LLMQAGenSpec + _parse_qa_response 工具

- `apps/api/dataplat_api/processors/llm_qa_gen.py` (顶部)：
  - `LLMQAGenSpec(BaseModel, extra=forbid)`：records_per_doc=1 / prompt_template=默认 / model_id="claude-haiku-4-5-20251001" / max_tokens=512 / text_truncate=6000
  - default prompt_template = "Read the following text and generate {n} high-quality QA pair(s) as a JSON object with keys 'prompt' and 'response'. Output JSON only. Text:\n\n{text}"
  - `_parse_qa_response(text: str) -> dict[str, str]`：
    1. json.loads(text.strip()) 成功且含 prompt+response → 返
    2. regex 提 ```json ... ``` 代码块，json.loads 成功 → 返
    3. fallback：返 {"prompt": "Summarize the following text.", "response": text.strip()[:1000]}
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-1, AC-4, AC-5, AC-6, AC-9

## T-2 LLMQAGenProcessor 实现

- 同文件 `llm_qa_gen.py` (类)：
  - `LLMQAGenProcessor`（name=llm-qa-gen v=0.1 output_subtype=sft；accepts=任意 layer；produces=RepoSpec(layer="gold", subtype="sft")）
  - input_schema: dict + additionalProperties=False
  - `run(inputs, config, workspace, ctx)`：
    - parsed = LLMQAGenSpec.model_validate(config)（ValueError 抛）
    - ctx.llm / ctx.blob_store 必须；缺 → raise ValueError（**显式 None 检查 + raise**）
    - view = inputs[0]
    - paths = [p for p in view.iter_paths() if p.lower().endswith((".md", ".txt", ".markdown"))]
    - if not paths: raise ValueError("llm-qa-gen 上游无 .md/.txt/.markdown 文件")
    - asyncio.run(_run_all(view, paths, parsed, ctx))
  - `_run_all`：
    - records: list[dict] = []
    - for path in paths:
      - raw = view.open(path).read() → text = decode utf-8
      - for i in range(parsed.records_per_doc):
        - prompt_text = parsed.prompt_template.format(text=text[:parsed.text_truncate], n=parsed.records_per_doc)
        - resp = await ctx.llm.call(LLMRequest(model_id=..., messages=[LLMMessage(role="user", content=prompt_text)], max_tokens=parsed.max_tokens))
        - qa = _parse_qa_response(resp.text)
        - qa["meta"] = {"source_path": path, "model_id": parsed.model_id, "idx": i}
        - records.append(qa)
    - jsonl_text = "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n"
    - jsonl_bytes = jsonl_text.encode("utf-8")
    - put = await ctx.blob_store.put(BytesIO(jsonl_bytes), declared_size=len(jsonl_bytes))
    - return ProcessResult(record_count=len(records), file_count=1, bytes_written=put.size, files=[IngestFileRef(path="sft.jsonl", sha256=put.sha256)])
- depends_on: T-1 / estimated_stage: stage-3 / AC: AC-2, AC-7, AC-8, AC-12

## T-3 processors/__init__.py 注册

- import + register LLMQAGenProcessor
- depends_on: T-2 / estimated_stage: stage-3 / AC: AC-3

## T-4 测试 tests/test_llm_qa_gen.py ≥ 6

- 新建 `apps/api/tests/test_llm_qa_gen.py`（部分需 PG + MinIO + Redis）：
  - test_a_parse_qa_direct_json：'{"prompt":"p","response":"r"}' → {"prompt":"p","response":"r"}
  - test_b_parse_qa_code_block：'```json\n{"prompt":"p","response":"r"}\n```' → 同上
  - test_c_parse_qa_fallback_raw：'not json' → fallback {"prompt": "Summarize...", "response": "not json"}
  - test_d_processor_unit_with_fakes：用 _SummaryLLM 返 JSON + _FakeStore + _FakeView 单 .md → 验 records[0] + sft.jsonl path
  - test_e_admin_process_returns_queued：admin POST /process llm-qa-gen → 201
  - test_f_end_to_end_succeeded：admin ingest 1 .md → admin POST /process llm-qa-gen → worker → succeeded；下游 commit 含 sft.jsonl + 内容是合法 jsonl ≥ 1 行 + 每行含 prompt+response+meta.source_path
- monkeypatch FakeLLMProvider.call 返 JSON（不走 truncate 80-char fallback）
- depends_on: T-1, T-2, T-3 / estimated_stage: stage-3 / AC: AC-10

## T-5 lint + type

- `cd apps/api && uv sync --extra dev`（SKILL #10 候选第 3 次累积）
- ruff + mypy 全 PASS
- depends_on: T-1~T-4 / estimated_stage: stage-3 / AC: AC-11

## T-6 self_check llm-qa-gen block

- `scripts/_self_check.sh` 追加 `run_llm_qa_gen` 13 AC + filter + 总入口
- AC-10 走 `run_ac_skipif_no_pg_minio_redis`
- depends_on: T-1~T-5 / estimated_stage: stage-3 / AC: AC-13

## process_tasks

- T-7 stage-2 spec/tasks review（depends_on T-6 v1 完）
- T-8 stage-4 coding review
- T-9 stage-5/6 test_report + review
- T-10 stage-7 CI
- T-11 stage-9 deploy verify
- T-12 stage-10 close

## 任务依赖图

```
T-1 (Spec + _parse) → T-2 (Processor) → T-3 (register)
                                          ↓
                                        T-4 (6 tests)
                                          ↓
                                        T-5 (lint+type)
                                          ↓
                                        T-6 (self_check)
                                          ↓
                              T-7 → T-8 → T-9 → T-10 → T-11 → T-12
```

## AC 覆盖矩阵

| AC | task |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-2 |
| AC-3 | T-3 |
| AC-4 | T-1 |
| AC-5 | T-1 |
| AC-6 | T-1 |
| AC-7 | T-2 |
| AC-8 | T-2 |
| AC-9 | T-1 |
| AC-10 | T-4 |
| AC-11 | T-5 |
| AC-12 | T-2 |
| AC-13 | T-6 |
