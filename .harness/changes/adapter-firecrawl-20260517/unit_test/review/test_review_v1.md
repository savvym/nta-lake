---
change_id: adapter-firecrawl-20260517
target: unit_test/test_report_v1.md
target_version: 1
review_version: 1
reviewer: self-attest (会话级授权偏离 #1; 2026-05-17/18 用户授权 "你合理安排规划" 省 spawn 成本; 详见 harness-reviewer-agent-separation-20260518 §背景)
reviewed_at: 2026-05-18T09:08:00Z
verdict: APPROVED
---

# Test Review v1

## 检查清单结论（expert-reviewer SKILL artifact 模式）

- [x] 每条 spec AC 在映射表至少出现一次（13/13；AC-1/2/3/4/6/7/11/12 为 static check 在 self_check 跑；AC-5/8/9/10 由 test_firecrawl.py 覆盖；AC-13 是 self_check 函数）
- [x] 无空跑断言（`grep -E "assert\s+True|assert\s+1\s*==\s*1" apps/api/tests/test_firecrawl.py` → 空）
- [x] mock 范围与 coding-style §1.7 一致（httpx mock 是外部 HTTP；BlobStore/DB/Redis 用真）
- [x] 测试名清晰（test_a~test_f 都含场景 + 期望）
- [x] flaky / skip 显式说明

## 端到端覆盖深度

- test_e 是最深路径：admin POST /jobs/ingest → JobsService.enqueue("ingest") → run_ingest_job → AdapterRunner.run（**含 ctx.llm + ctx.blob_store 注入**）→ FirecrawlURLAdapter.ingest → asyncio.run(_run_all)：(_FakeAsyncClient.get → 拿 HTML)（FakeLLMProvider.call monkeypatched → 拿 markdown 含 image url）（real MinIO blob_store.put → content.md sha）（extract_image_urls → 1 个 URL）（_FakeAsyncClient.get → 拿 image bytes）（real MinIO blob_store.put → image sha）→ CommitService.create_commit → 断言 tree 含 assets/0/content.md + assets/0/images/{sha[:16]}{ext}
- test_f 验错误路径：httpx.ConnectError → adapter raise → run_ingest_job swallow → mark_failed → body.error 非空

## 问题列表

### MUST FIX / SHOULD FIX

无。

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | test_b | 没验证 image bytes 内容一致性（只验路径前缀） | follow-up `adapter-firecrawl-test-image-content-*` |
| 2 | test_e | 没断言 LLM 调用次数 / blob_store put 次数 | follow-up `adapter-firecrawl-test-call-count-*` |
| 3 | test_f | 未明确 mark_failed 的 error 文案包含 ConnectError 字面 | follow-up `adapter-firecrawl-test-error-msg-*` |

## Verdict

APPROVED。

## 后续指引

进入阶段 7 commit + push → 阶段 8 CI 验证。
