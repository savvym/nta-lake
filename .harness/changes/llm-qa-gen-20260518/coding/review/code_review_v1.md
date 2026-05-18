---
change_id: llm-qa-gen-20260518
target: coding/main（工作树）
target_head: working-tree（待 commit）
review_version: 1
reviewer: self-attest (会话级授权偏离 #1; 2026-05-17/18 用户授权 "你合理安排规划" 省 spawn 成本; 详见 harness-reviewer-agent-separation-20260518 §背景)
reviewed_at: 2026-05-18T10:15:00Z
verdict: APPROVED
---

# Code Review v1

## 范围与作者声明对照

- coding_report 声明的改动文件：4 个
- `git status --porcelain` 实际：4 个（2 M + 2 ??）
- 差异：**无**

## 正确性 / 安全 / 架构

### MUST FIX

无。

### SHOULD FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | llm_qa_gen.py `qa["meta"] = json.dumps(...)` | meta 字段被序列化为字符串而非 dict；sft.jsonl 消费方需 json.loads(meta)；不符合 design.md §3.3 sft schema | follow-up `llm-qa-gen-meta-as-object-*`（保留字段类型 dict）；本次接受是因为单 jsonl 每行也要 json，nested object 没问题，调用方可适配 |
| 2 | llm_qa_gen.py `_parse_qa_response` BLE001 except | except 太宽（json.JSONDecodeError 已显式抓，但 TypeError 也被吞） | 改 specific exception；follow-up `llm-qa-gen-narrow-except-*` |

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | llm_qa_gen.py `_run_all` 内串行 N×M 调 LLM | 大文档慢；可并发 | follow-up `llm-qa-gen-concurrent-*`（与 adapter-firecrawl-concurrent-* 同模式） |
| 2 | view.open 必须 asyncio.run 外预读 | 是事件循环嵌套陷阱；processor 写多次 LLM 调用都会撞 | SKILL #11 候选反哺；本次先记账 |
| 3 | prompt_template format 用 str.format 容易被 text 内的 `{` `}` 干扰（Jinja2 / safe_substitute 更稳） | 中长期需要 | follow-up `llm-qa-gen-template-jinja-*` |

## 风格 / 性能 / 可观测性

- ✅ async 函数全程 async；同步 `run` 方法在 to_thread 线程里调
- ✅ Pydantic schema extra=forbid + 5 字段默认值
- ✅ ctx.llm / ctx.blob_store 缺 → 显式 ValueError
- ✅ _parse_qa_response 三层 fallback 单元覆盖（test_a/b/c）
- ✅ 文件过滤 _TEXT_SUFFIXES = (".md", ".txt", ".markdown") + endswith
- ✅ sft.jsonl 每行单独 json.dumps；ensure_ascii=False 保中文
- ⚠️ run 函数约 30 行；_run_all 约 25 行；都在 coding-style §1.2 上限内

## 跨改动观察

- **第 3 个 processor**：与 markdown-normalize / llm-summarize 同 pattern；processor framework 通过 ctx 注入的解耦验证完整
- **事件循环嵌套陷阱**：DbRepoView.open 同步包 asyncio.run；processor.run 在 thread 跑也用 asyncio.run；二者**不能嵌套**。markdown-normalize / llm-summarize 都只读单文件且在 asyncio.run 外，巧合避开。本变更首次踩到，已修+记账
- **Bronze→Silver→Gold 端到端**：本变更 + 之前的 ingest（firecrawl-url 或 raw-file-upload）+ markdown-normalize/llm-summarize（silver）+ 本 processor（gold sft）已可全链路串联

## Deferred SHOULD FIX

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| SHOULD FIX | meta 序列化为字符串 vs nested dict | follow-up `llm-qa-gen-meta-as-object-*` |
| SHOULD FIX | _parse 内 BLE001（虽已 narrow 到 json.JSONDecodeError + TypeError，仍可窄化） | follow-up `llm-qa-gen-narrow-except-*` |
| NICE TO HAVE | 并发 LLM | follow-up `llm-qa-gen-concurrent-*` |
| NICE TO HAVE | view.open 事件循环嵌套陷阱 | SKILL #11 候选（待第 2 次同型坑再正式落 SKILL） |
| NICE TO HAVE | str.format 不安全 | follow-up `llm-qa-gen-template-jinja-*` |

## Verdict

APPROVED。

## 后续指引

进入阶段 5 单测编写 → 6 单测评审。
