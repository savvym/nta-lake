---
change_id: adapter-firecrawl-20260517
title: FirecrawlURLAdapter（httpx 抓 HTML + ctx.llm 转 markdown + images 提取）+ AdapterRunner ctx 扩 llm/blob_store
owner: zhhdzhang
started_at: 2026-05-18T08:00:00Z
closed_at: 2026-05-18T09:25:00Z
stage: closed
status: closed
last_updated: 2026-05-18T09:25:00Z
related_changes:
  - llm-gateway-mvp-20260517
  - adapter-framework-20260517
  - processor-framework-20260517
note: 第 13 个 dataplat 变更。横向扩 Bronze 录入面——第二个 SourceAdapter，验证 AdapterRegistry 多 adapter；同时把 ctx.llm + ctx.blob_store 注入扩到 AdapterRunner（消化 adapter-runner-ctx-llm-inject-* follow-up）
---

# Summary

## 一句话目标

把 `apps/api/dataplat_api/adapters/firecrawl_url.py` 从无到有建起来：用 httpx 串行抓 URL 拿 HTML → ctx.llm.call 转 markdown → 写 `assets/<idx>/content.md` blob；同时从 markdown 中提取 `<img src=...>` / `![](...)`，httpx 下载图片 → 写 `assets/<idx>/images/<sha>.{ext}` blob；同时 AdapterRunner 构 ctx 时注入 `llm=get_llm_gateway()` + `blob_store=store`（与 ProcessorRunner 对齐）。

## 范围摘要

- **In scope**：
  - `apps/api/dataplat_api/adapters/__init__.py` + `firecrawl_url.py`（adapter 实现）
  - `apps/api/dataplat_api/adapters/_image_extract.py`（从 markdown 提取 image URL 工具）
  - `FirecrawlURLSpec` Pydantic（urls / extract_images / llm_model / max_tokens；extra=forbid）
  - `AdapterRunner` 构 ctx 时注入 `llm=get_llm_gateway()` + `blob_store=store`
  - registry 注册 firecrawl-url v0.1
  - 串行多 URL（asyncio.run 单次，内部按序处理）
  - 图片下载（httpx 拉取 + sha256 命名 + 写 blob + 加 tree entry）
  - `apps/api/tests/test_firecrawl.py` ≥ 6 集成 + 单元测试（全 mock httpx + FakeLLMProvider）
  - `scripts/_self_check.sh` 追加 13 AC + filter
- **Out of scope**：
  - 真 firecrawl-py SDK（不引入 vendor 锁定 + 不消耗 API 配额）→ follow-up `adapter-firecrawl-sdk-*`
  - JS-rendered 页面（无 headless browser）→ follow-up `adapter-firecrawl-js-render-*`
  - rate limit / 礼仪型抓取（robots.txt / sitemap）→ follow-up `adapter-firecrawl-politeness-*`
  - 并发抓取 + LLM 调用 → follow-up `adapter-firecrawl-concurrent-*`
  - 增量 / dedup URL（spec 含同 URL 时直接跳过）→ follow-up `adapter-firecrawl-incremental-*`
  - 图片 OCR / vision LLM 提取 alt text → follow-up `adapter-firecrawl-image-vision-*`
  - 多媒体（video / audio） → follow-up `adapter-firecrawl-multimodal-*`
  - 真 LLM live test → follow-up `adapter-firecrawl-live-test-*`

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
| 2026-05-18 | 抓取走 httpx + ctx.llm 转 md（**不**用 firecrawl-py SDK） | 用户 stage 0 显式选；无 vendor 锁；CI 全 mock；可贴合 design.md "FirecrawlURL adapter" 语义 | spec §抓取后端 |
| 2026-05-18 | 多 URL 串行（**不**并发） | 用户 stage 0 显式选；MVP 充分；LLM 调用串行避免 cache/retry race；follow-up `adapter-firecrawl-concurrent-*` | spec §AC-7 |
| 2026-05-18 | 输出 content.md + images/（**做** images 提取下载） | 用户 stage 0 显式选；与 design.md §2.3 "content.md + images/" 一致；不做 OCR / vision | spec §AC-9 |
| 2026-05-18 | AdapterRunner 顺手扩 ctx.llm + ctx.blob_store 注入 | 消化 `adapter-runner-ctx-llm-inject-*` follow-up；与 ProcessorRunner 对齐；FirecrawlURLAdapter 同时依赖 ctx.llm（转 md）+ ctx.blob_store（写 blob） | spec §AC-3 |
| 2026-05-18 | LLM model 走 spec.llm_model（不固化） | adapter 不同场景需不同模型；spec 可控；默认 claude-haiku-4-5-20251001 | spec §AC-2 |

## 当前阻塞

无。

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| SHOULD FIX | image GET 失败用 BLE001 broad-except | follow-up `adapter-firecrawl-narrow-except-*` |
| NICE TO HAVE | _HTML_TRUNCATE=8000 长页面丢正文 | follow-up `adapter-firecrawl-chunking-*` |
| NICE TO HAVE | prompt 仍可能被 LLM 加前缀 "Here is the markdown..." | follow-up `adapter-firecrawl-prompt-strict-*` |
| NICE TO HAVE | test_b 未验 image bytes 内容一致性 | follow-up `adapter-firecrawl-test-image-content-*` |
| NICE TO HAVE | test_e 未断言 LLM/blob_store call count | follow-up `adapter-firecrawl-test-call-count-*` |
| NICE TO HAVE | test_f 未断言 error 文案含 ConnectError 字面 | follow-up `adapter-firecrawl-test-error-msg-*` |
| harness-lint | AC-7 反向 grep 误伤 docstring 字面 "asyncio.gather" | follow-up `harness-lint-ac-precise-grep-*`（并入 [[project-followup-harness-lint]] 分层校验） |
| 工具 | FakeLLMProvider 默认模板太短截断 prompt → test_e 需 monkeypatch | follow-up `fake-llm-echo-mode-*` |
| Out of scope | firecrawl-py SDK / JS-rendered / politeness / 并发 / 增量 / image vision / 多媒体 / live test / Web UI | 各自 follow-up（9 条；详见 spec §Out of scope） |

## 交付

- Branch：`main`
- PR：n/a（本仓 MVP 不用 PR；通过 self_check 199/199 + 双 commit 验证）
- feat commit：见 git log（feat(adapter): ...）
- chore close commit：见 git log（chore(adapter): close ...）
- 部署版本：dev 本地 `uv run` 启的 API + worker（无 image）
- 用户确认：2026-05-17 通宵会话开题授权 "你合理安排规划"
- 关闭时间：2026-05-18T09:25:00Z

## 复盘

### 顺利

- **SKILL #9 第三次连胜**：summary.md frontmatter 在 stage 0 就填好（占位符 grep = 0），review 流程都从 SSoT 读，无 SSoT 漂移
- **AdapterRunner ctx 扩本变更顺手解决**：消化 llm-gateway-mvp 列的 `adapter-runner-ctx-llm-inject-*` follow-up，减少后续 change 数量
- **第二个 adapter 多 adapter registry 路径验证通过**：之前只有 raw-file-upload，FirecrawlURLAdapter 注册让 multi-adapter 工作流首次跑通
- **httpx mock 用 module-level setattr**：只替换 firecrawl_url 模块视角的 httpx，不影响 ASGITransport 等其他用 httpx 的代码——干净的隔离
- **dry-parse 提前发现陷阱**：5 条 python -c AC 在 spec 阶段全 compile 通过；stage 3 实际跑也全过

### 踩坑

1. **AC-7 反向 grep 命中 docstring 字面 "asyncio.gather"**：docstring 写了 "不用 asyncio.gather" 这个字面字符串 → grep 命中 → AC FAIL。改 docstring 措辞规避。
   - **防复发**：reverse-grep 应该用更精确 pattern（如 `^[^#"]*asyncio\.gather\(` 跳过注释 / docstring）。加 follow-up `harness-lint-ac-precise-grep-*`，并入 [[project-followup-harness-lint]] 分层校验。**不**在本次落 SKILL（单点问题，不到 SKILL 反哺阈值）。

2. **FakeLLMProvider 默认模板太短截断**：test_e 端到端用 fake provider 时，prompt prefix > 80 char 导致 truncate 后不含 image URL，extract_image_urls 返空 → 测试断言失败。改用 `monkeypatch.setattr("dataplat_api.llm.providers.fake.FakeLLMProvider.call", ...)` 替换 call 行为。
   - **防复发**：follow-up `fake-llm-echo-mode-*` 给 FakeLLMProvider 加 `echo_mode=True` 让其返回完整 prompt（或可配置 truncate 长度）。

3. **测试用了错路由 `/repos/{}/{}/ingest`**：本仓有同步 `/repos/{}/{}/ingest`（直接跑）和异步 `/jobs/ingest`（worker 跑）两条路由。async 需走 `/jobs/ingest`，payload schema 三层嵌套 `{owner, name, request: IngestRequest}`。首次抄错；改后通。
   - **防复发**：不在 SKILL 范围；属本 change 一次性问题。

### SKILL 反哺累积

- **SKILL #9 第三次连胜**：summary.md frontmatter stage 0 填好 → SSoT 全程稳定（processor-framework 反哺 + llm-gateway-mvp 验证 + 本次再验证）
- **SKILL #10 候选记账（第 2 次累积）**：本次实测前主动跑了 `cd apps/api && uv sync --extra dev`，避免 venv 漂移；该候选若再出现第 3 次同型坑则正式落 SKILL。

