---
change_id: processor-pdf-mineru-assets-20260520
version: 1
authored_at: 2026-05-19T12:50:00Z
---

# Tasks

```yaml
tasks:
  - id: T-1
    title: _mineru_client.py 加 fetch_full_result + base64 decode + submit 透传
    description: |
      submit 签名加 return_images / return_content_list (bool, default True)；
      multipart data 字典加这两 flag（值序列化为 "true"/"false"）。
      新增 fetch_full_result(task_id) -> dict[str, Any]：
        GET /result；从 results dict 取首个文件对应的 dict；
        解码 images：value（data-URI 或裸 base64）→ bytes，保持 filename keys；
        返 {"markdown": str, "images": dict[str, bytes], "content_list": str | None}。
      新增 _decode_image_data_uri(uri) -> bytes：兼容 data:image/*;base64, 前缀与裸 base64。
      fetch_markdown 保持向后兼容。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-2, AC-3, AC-4]
    status: pending

  - id: T-2
    title: pdf_mineru.py PdfMineruSpec 加字段 + run 写 assets
    description: |
      PdfMineruSpec 加 return_images / return_content_list (bool, default True)；
      _CONFIG_SCHEMA properties 同步加。
      _process_one 改：用 fetch_full_result；按解包结果写 md / images/* / content_list.json；
      返 list[IngestFileRef]。run 主循环累加 file_count / bytes_written。
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-1, AC-5, AC-6]
    status: pending

  - id: T-3
    title: tests/test_pdf_mineru.py FakeAsyncClient 同步 + 新增 ≥ 2 用例
    description: |
      _FakeAsyncClient.result_response 默认 payload 加 md_content + images (≥2 data-URI) +
        content_list (短 JSON 字符串)；_reset_fake 同步。
      上游 7 用例兼容：
        - test_run_success: puts 多文件 → 改断言 puts[0] == md_bytes，IngestFileRef 含 md / images/ / content_list.json 三类 path。
        - test_run_skips_non_pdf: file_count == 1 改为 >= 1 且首个 path == doc.md。
        - 其他不动。
      新增：
        - test_run_with_assets: 验证 ≥ 4 IngestFileRef，path pattern 形如 images/* 与 *.content_list.json。
        - test_data_uri_base64_decode: prefix + 裸 base64 两路径解码。
    depends_on: [T-2]
    estimated_stage: unit_test
    covers_ac: [AC-7, AC-8, AC-11]
    status: pending

  - id: T-4
    title: scripts/_self_check.sh 追加 run_processor_pdf_mineru_assets 12 AC
    description: |
      在 run_processor_pdf_mineru_live_fix 后插入 run_processor_pdf_mineru_assets（12 AC）；
      filter case + 全跑入口 list 都加上。
    depends_on: [T-3]
    estimated_stage: ci_result
    covers_ac: [AC-9, AC-10, AC-12]
    status: pending

  - id: T-5
    title: 本地 lint / pytest / self_check 三 change 全绿
    description: |
      uv run ruff check + mypy；
      pytest tests/test_pdf_mineru.py；
      bash scripts/_self_check.sh current processor-pdf-mineru-assets-20260520 → 22/22 PASS；
      bash scripts/_self_check.sh current processor-pdf-mineru-live-fix-20260519 → 不回归；
      bash scripts/_self_check.sh current processor-pdf-mineru-20260519 → 不回归。
    depends_on: [T-4]
    estimated_stage: ci_result
    covers_ac: [AC-8, AC-9, AC-11]
    status: pending
```

## 阶段任务

```yaml
process_tasks:
  - id: P-spec-review
    estimated_stage: request_analysis_review
    status: deferred       # 会话级授权偏离 #1
  - id: P-code-review
    estimated_stage: coding_review
    status: deferred
  - id: P-test-review
    estimated_stage: unit_test_review
    status: deferred
  - id: P-push
    estimated_stage: stage-7
    status: pending
  - id: P-ci
    estimated_stage: ci_result
    status: pending
  - id: P-deploy
    estimated_stage: deployment
    status: pending
  - id: P-user-confirm
    estimated_stage: user_confirmation
    status: pending
```

## DAG

T-1 → T-2 → T-3 → T-4 → T-5（无环）

## 验收覆盖

| AC | 任务 |
|---|---|
| AC-1 | T-2 |
| AC-2 | T-1 |
| AC-3 | T-1 |
| AC-4 | T-1 |
| AC-5 | T-2 |
| AC-6 | T-2 |
| AC-7 | T-3 |
| AC-8 | T-3, T-5 |
| AC-9 | T-5 |
| AC-10 | T-4 |
| AC-11 | T-3, T-5 |
| AC-12 | T-4 |
