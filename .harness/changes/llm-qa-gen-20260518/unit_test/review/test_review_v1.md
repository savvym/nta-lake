---
change_id: llm-qa-gen-20260518
target: unit_test/test_report_v1.md
target_version: 1
review_version: 1
reviewer: application-owner-agent
reviewed_at: 2026-05-18T10:22:00Z
verdict: APPROVED
---

# Test Review v1

## 检查清单结论（expert-reviewer SKILL artifact 模式）

- [x] 每条 spec AC 在映射表至少出现一次（13/13；AC-1~AC-8、AC-11、AC-12 为 static check 在 self_check；AC-9/AC-10 由 test_llm_qa_gen.py 覆盖；AC-13 是 self_check 函数）
- [x] 无空跑断言（`grep -E "assert\s+True|assert\s+1\s*==\s*1" apps/api/tests/test_llm_qa_gen.py` → 空）
- [x] mock 范围与 coding-style §1.7 一致（LLM provider mock + env；BlobStore/DB/Redis 真）
- [x] 测试名清晰（test_a~test_f 都含场景 + 期望）
- [x] flaky / skip 显式说明

## 端到端覆盖深度

- test_f 是最深路径：admin POST /process llm-qa-gen → JobsService.enqueue("process") → run_process_job → ProcessorRunner.run（**含 ctx.llm + ctx.blob_store 注入**）→ LLMQAGenProcessor.run → 同步预读 view.open(doc.md)（DbRepoView 内部 asyncio.run 拿 blob）→ asyncio.run(_run_all)：for path × records_per_doc=2 调 FakeLLMProvider.call（monkeypatch 返合法 JSON）→ _parse_qa_response → records 累加 → json.dumps jsonl → ctx.blob_store.put（真 MinIO）→ ProcessResult → CommitService.create_commit → 断言 commit hash + sft.jsonl entry + 2 行 JSON + 每行含 prompt+response+meta.source_path=="doc.md"
- test_d 验同步预读 + 多 records 拼接逻辑（不走真 DB/MinIO）
- test_a/b/c 覆盖 _parse 三层 fallback

## 问题列表

### MUST FIX / SHOULD FIX

无。

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | test_f | 未断言 LLM 实际被调 2 次（只验最终 2 行 JSON） | follow-up `llm-qa-gen-test-call-count-*` |
| 2 | test_d | 未验 jsonl 末尾换行 / UTF-8 BOM 等编码细节 | follow-up `llm-qa-gen-test-encoding-*` |
| 3 | test_c | fallback test 没验 meta 字段格式 | follow-up `llm-qa-gen-test-fallback-meta-*` |

## Verdict

APPROVED。

## 后续指引

进入阶段 7 commit + push → 阶段 8 CI 验证。
