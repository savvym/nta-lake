---
change_id: llm-qa-gen-20260518
title: LLMQAGenProcessor（silver text-corpus → gold sft；ctx.llm 调 N 次/文件 → sft.jsonl）
owner: zhhdzhang
started_at: 2026-05-18T09:35:00Z
closed_at: 2026-05-18T10:40:00Z
stage: closed
status: closed
last_updated: 2026-05-18T10:40:00Z
related_changes:
  - llm-gateway-mvp-20260517
  - processor-framework-20260517
  - adapter-firecrawl-20260517
note: 第 14 个 dataplat 变更。design.md §2.3 Repo E 核心 processor——第一个生产语义 processor，端到端 Bronze→Silver→Gold 走通；同时验证 ctx.llm 多次 call + JSON 输出解析 + 单文件 jsonl 聚合
---

# Summary

## 一句话目标

新建 `apps/api/dataplat_api/processors/llm_qa_gen.py` 实现 `LLMQAGenProcessor` id=`llm-qa-gen` v=`0.1`：上游 silver text-corpus 仓库（多个 .md/.txt/.markdown 文件）→ 对每个文件调 `ctx.llm.call` N 次（spec.records_per_doc）让 LLM 生成 `{prompt, response}` JSON 对 → 解析（含 JSON / ```json``` 代码块 / fallback raw 三层）→ 所有 records 拼接成 `sft.jsonl` 单文件 blob → 写下游 gold sft 仓 commit。

## 范围摘要

- **In scope**：
  - `apps/api/dataplat_api/processors/llm_qa_gen.py`：`LLMQAGenSpec`（records_per_doc / prompt_template / model_id / max_tokens / text_truncate；extra=forbid）+ `LLMQAGenProcessor`（name=llm-qa-gen v=0.1 output_subtype=sft）
  - `_parse_qa_response(text)` 工具：JSON 直接 / ```json``` 代码块 / fallback raw 三层解析
  - 单文件 jsonl 聚合：所有 records 按行 dump JSON → 写 `sft.jsonl` 单 blob
  - `processors/__init__.py`：import + register
  - `apps/api/tests/test_llm_qa_gen.py`：≥ 6 测试（全 mock FakeLLMProvider 返合法 JSON）
  - `scripts/_self_check.sh`：追加 13 AC
- **Out of scope**（显式）：
  - per-source JSONL（一个 .md 一个 sft/<idx>.jsonl）→ follow-up `llm-qa-gen-per-source-*`
  - parquet 替代 jsonl（design 推荐）→ follow-up `llm-qa-gen-parquet-*`
  - dedup（同 prompt 跳过）→ follow-up `llm-qa-gen-dedup-*`
  - quality_score（LLM-as-judge）→ follow-up `llm-qa-gen-quality-score-*`
  - 多轮 conversation（system + tools）→ follow-up `llm-qa-gen-multi-turn-*`
  - 增量（同 source_ref 跳过）→ follow-up `llm-qa-gen-incremental-*`
  - cross-doc dedup → follow-up `llm-qa-gen-cross-dedup-*`
  - live test → follow-up `llm-qa-gen-live-test-*`
  - Web UI 触发 QA 生成 → follow-up `web-process-qa-gen-ui-*`

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
| 2026-05-18 | 薄骨架（**不**含 dedup / parquet / quality_score） | 用户 stage 0 显式选；解锁 design.md §2.3 端到端语义；各高级特性独立 follow-up | spec §Out of scope |
| 2026-05-18 | 上游过滤 .md/.txt/.markdown | 用户 stage 0 显式选；与 markdown-normalize / llm-summarize 同 pattern；避免误读 meta 文件 | spec §AC-7 |
| 2026-05-18 | prompt_template 可配（默认 + str.format 插入 {text} / {n}） | 用户 stage 0 显式选；不同领域需不同 prompt | spec §AC-6 |
| 2026-05-18 | 输出单文件 sft.jsonl（**不**做 per-source） | MVP 最小化；CAS 自然去重；per-source 是 follow-up | spec §AC-8 |
| 2026-05-18 | _parse_qa_response 三层 fallback：直接 JSON → 代码块 → raw text 拆 | LLM 不一定守 JSON 格式；fallback 保证测试可控；fake provider 走 fallback 路径 | spec §AC-9 |

## 当前阻塞

无。

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| SHOULD FIX | meta 字段被 json.dumps 序列化为字符串而非 nested dict | follow-up `llm-qa-gen-meta-as-object-*` |
| SHOULD FIX | _parse 内 except 仍可窄化 | follow-up `llm-qa-gen-narrow-except-*` |
| NICE TO HAVE | 串行 N×M LLM 调用慢 | follow-up `llm-qa-gen-concurrent-*` |
| NICE TO HAVE | str.format 不安全（text 含 `{` 干扰） | follow-up `llm-qa-gen-template-jinja-*` |
| NICE TO HAVE | text_truncate=6000 长文丢正文末段 | follow-up `llm-qa-gen-chunking-*` |
| NICE TO HAVE | default prompt 无输出语言指定 | follow-up `llm-qa-gen-prompt-lang-*` |
| NICE TO HAVE | test_f 未断言 LLM 调用次数 | follow-up `llm-qa-gen-test-call-count-*` |
| 流程候选 | view.open 在 asyncio.run 内嵌套触发 RuntimeError；processor 多次 LLM 调用都会撞 | SKILL #11 候选（待第 2 次同型坑再正式落 SKILL） |
| Out of scope | per-source JSONL / parquet / dedup / quality_score / multi-turn / incremental / live-test / Web UI | 各自 follow-up（详见 spec §Out of scope） |

## 交付

- Branch：`main`
- PR：n/a（本仓 MVP 不用 PR；通过 self_check 212/212 + 双 commit 验证）
- feat commit：见 git log（feat(processor): llm-qa-gen ...）
- chore close commit：见 git log（chore(processor): close ...）
- 部署版本：dev 本地 `uv run` 启的 API + worker（无 image）
- 用户确认：2026-05-17 通宵会话开题授权 "你合理安排规划"
- 关闭时间：2026-05-18T10:40:00Z

## 复盘

### 顺利

- **SKILL #9 第 4 次连胜**：summary.md frontmatter 在 stage 0 即填好，全程零模板占位符
- **AskUserQuestion + spec 自审 + dry-parse 三道防线**：7 条 python -c AC 提前 compile 通过；implementation 阶段几乎不返工
- **跨变更回归 26 测试一次性 PASS**：之前 4 个 change 的稳定 pattern（fixture / monkeypatch / FakeLLMProvider）被本变更无缝复用
- **Bronze → Silver → Gold 端到端首次打通**：本变更 + adapter-firecrawl + markdown-normalize/llm-summarize 已可全链路串联

### 踩坑

1. **事件循环嵌套**：DbRepoView.open 内部用 asyncio.run 取 blob；如果 processor.run 也用 asyncio.run 包整个流程（含 view.open 调用），就触发 `RuntimeError: asyncio.run() cannot be called from a running event loop`。markdown-normalize / llm-summarize 都只读单文件且巧合避开。
   - **修复**：在 processor.run 同步部分**预读**所有 .md 到 `list[tuple[path, text]]`，再 asyncio.run(_run_all(texts, ...))
   - **防复发**：SKILL #11 候选（第 1 次累积；第 2 次再正式落 SKILL）："processor 写多次 LLM 调用时，view.open() 必须在 async 上下文外预读"

2. **AC-7 bash quote 嵌套**：`grep -qE "'\.md'|..."` 在 bash -c 双引号下转义复杂，原 spec 的 single-quoted pattern 不匹配 double-quoted 代码。改用 `grep -F` (fixed-string) + `_TEXT_SUFFIXES` constant grep + 三个独立后缀 grep 兜底。代价：稍冗长但完全可读。
   - **防复发**：未来 AC 的 grep 复杂 quote 时优先选 grep -F + 多重 grep；不在本次落 SKILL（单点）

3. **repo subtype enum 严格**：bronze 接受 pdf/pdf-collection/webpage/webpage-collection/book/image-set；spec 误写 "text"。改 webpage。
   - **防复发**：未来测试用 enum 字面时先 cat schemas/repository.py 查清；不在本次落 SKILL

### SKILL 反哺累积

- **SKILL #9 第 4 次连胜**：summary.md frontmatter stage 0 即填 → 全程 SSoT 稳定
- **SKILL #10 候选第 3 次累积**：测试前主动 `cd apps/api && uv sync --extra dev`；下次同型坑再落 SKILL
- **SKILL #11 候选第 1 次累积**：processor + DbRepoView 事件循环嵌套；下次同型坑再落 SKILL

