---
change_id: llm-qa-gen-20260518
version: 1
authored_at: 2026-05-18T10:05:00Z
branch: main
base_commit: 67a8e8b (adapter-firecrawl close)
head_commit: working-tree
status: waiting_review
---

# Coding Report v1

## 改动文件清单

| 路径 | 类型 | 说明 | 关联 task |
|---|---|---|---|
| `apps/api/dataplat_api/processors/llm_qa_gen.py` | new | LLMQAGenSpec (extra=forbid; records_per_doc/prompt_template/model_id/max_tokens/text_truncate) + LLMQAGenProcessor (name=llm-qa-gen v=0.1 output_subtype=sft) + _parse_qa_response（三层 fallback：JSON / `\`\`\`json\`\`\`` / raw text）+ _run_all async（按 doc × records_per_doc 调 ctx.llm.call + 拼 jsonl + ctx.blob_store.put） | T-1, T-2 |
| `apps/api/dataplat_api/processors/__init__.py` | edit | import + register LLMQAGenProcessor | T-3 |
| `apps/api/tests/test_llm_qa_gen.py` | new | 6 测试：(a)(b)(c) _parse 三层 / (d) processor 单元（mock _JsonLLM + _FakeStore + _FakeView）/ (e) admin /process 201 / (f) end-to-end succeeded（sft.jsonl ≥ 1 行 JSON 含 prompt/response/meta） | T-4 |
| `scripts/_self_check.sh` | edit | 追加 run_llm_qa_gen 13 AC + filter + 总入口 | T-6 |

## 与 tasks.md 的映射

| Task | 状态 | 备注 |
|---|---|---|
| T-1 LLMQAGenSpec + _parse_qa_response | done | 三层 fallback 实测覆盖 |
| T-2 LLMQAGenProcessor | done | view.open 同步预读到 list 后再 asyncio.run（避免事件循环嵌套，见踩坑） |
| T-3 register | done | processor 总数 3（markdown-normalize + llm-summarize + llm-qa-gen） |
| T-4 6 tests | done（全 PASS 2.74s） | 含端到端 sft.jsonl 内容验证 |
| T-5 lint+type | done | ruff 0 errors；mypy 0 errors 88 source files |
| T-6 self_check | done | 13/13；全仓 199→212 |

## 偏离 spec / trade-off

- **AC-7 grep pattern 改为 `_TEXT_SUFFIXES + .md + .txt + .markdown` 多重 grep -F**：spec 原命令 `grep -qE "'\\.md'|..."` 在 bash quote 嵌套下匹配的是 single-quoted suffix，但代码用 double-quoted；多次尝试 escape 失败后改用 `grep -F`（fixed-string）+ 多重 grep + 加 `_TEXT_SUFFIXES` constant grep 兜底。语义不变（仍校验 3 个 suffix 出现）；spec v1 文本不动，coding_report 声明 trade-off。
- **`view.open` 必须在 `asyncio.run(_run_all)` 之外调**：踩坑——首版 _run_all 内调 view.open 触发**事件循环嵌套**（DbRepoView.open 内部用 asyncio.run，processor 在 thread 内调 OK；但若再嵌套在 asyncio.run 的 event loop 里就 `RuntimeError: asyncio.run() cannot be called from a running event loop`）。修复：在同步 `run` 方法里先预读所有 .md 到 `list[tuple[path, text]]`，再 asyncio.run(_run_all(texts, ...))。这是 processor-framework / llm-summarize 都没暴露的新坑（它们只读单文件且在 asyncio.run 外读）。**防复发**：列入 SKILL #11 候选反哺（"processor 写 LLM 多次调用时，view.open 必须在 async 上下文外预读"）。
- **test_e/f repo subtype 改为 webpage**：spec 写 "text" 不在 bronze allowed enum 里（pdf / pdf-collection / webpage / webpage-collection / book / image-set）；改 webpage。test_e/f 测试目的不变。
- **AC-12 双 grep 模式**：`ctx.llm` + `llm is None`；实现里写成 `if llm is None: raise` 既匹配又是正确语义。reverse-grep checklist 第 6 条这次是"正向双 grep 不是反向"——表达"显式存在检查"而非"显式不存在"。

## 本地校验

```text
ruff: All checks passed!
mypy: Success: no issues found in 88 source files
pytest test_llm_qa_gen.py: 6 PASS (2.74s)
pytest test_llm_qa_gen + test_processor + test_firecrawl + test_llm: 26 PASS (11.38s)（无回归）
self_check llm-qa-gen: PASS=13 / FAIL=0 / SKIP=0
self_check 全仓: PASS=212 / FAIL=0 / SKIP=0（15 个 block）
```

## 已知未解决问题

- spec §Out of scope 9 类（per-source / parquet / dedup / quality_score / multi-turn / incremental / live-test / Web UI 等）均为 follow-up
- text_truncate=6000 长文档会丢正文末段 → `llm-qa-gen-chunking-*`
- default prompt 没指定输出语言 → `llm-qa-gen-prompt-lang-*`

## 下一步

进入阶段 4 编码评审。
