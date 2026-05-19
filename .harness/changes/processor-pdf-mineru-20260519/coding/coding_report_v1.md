---
change_id: processor-pdf-mineru-20260519
version: 1
authored_at: 2026-05-19T10:30:00Z
branch: change/processor-pdf-mineru-20260519
base_commit: 17bf2c1
head_commit: 6e726e5
status: waiting_review
---

# Coding Report v1

## 改动文件清单

| 路径 | 类型 | 一句话说明（改了什么 / 为什么） | 关联 task |
|---|---|---|---|
| `apps/api/dataplat_api/processors/_mineru_client.py` | new | MinerUClient（薄 HTTP 客户端，submit / poll / fetch_markdown，httpx.AsyncClient + 可选 Bearer token） | T-1 |
| `apps/api/dataplat_api/processors/pdf_mineru.py` | new | PdfMineruSpec（extra=forbid）+ PdfMineruProcessor（accepts 任意 / produces silver/pdf-markdown / 串行处理 .pdf → .md） | T-2 |
| `apps/api/dataplat_api/processors/__init__.py` | modify | import PdfMineruProcessor + register；`__all__` 加 `PdfMineruProcessor` | T-3 |

> 单测 / self_check AC block 留到 stage 5 / stage 8（按 tasks.md DAG）。

## 与 tasks.md 的映射

| Task ID | 状态 | commits | 备注 |
|---|---|---|---|
| T-1 | done | 6e726e5 | MinerUClient 三方法齐全；JSON 解析集中到 `_parse_submit_response` / `_parse_poll_response`；token via `_headers()` |
| T-2 | done | 6e726e5 | 五项 Processor Protocol 数据属性（含 config_schema）+ run()；asyncio.run 模式与 llm-summarize 对齐；输出 path 用 `Path(src).with_suffix(".md")` |
| T-3 | done | 6e726e5 | __init__.py import + register；__all__ 同步更新 |
| T-4 | pending | — | 单测，stage 5 起 |
| T-5 | pending | — | self_check AC block，stage 8 起 |
| T-6 | pending | — | local lint + self_check current 全绿，stage 8 |

## 偏离 spec / trade-off

- **轮询超时 raise 信息中包含 task_id 与 timeout 阈值**：spec 没明确，但加入有助于排查；不增加 AC 负担。
- **submit 响应字段双兼容（`task_id` 或 `id`）**：spec.md "deferred to coding 阶段" 提到 MinerU 真服务字段名未确认；这里集中在 `_parse_submit_response`，若实测后字段唯一，可后续 follow-up 简化。
- **`_TERMINAL_OK` / `_TERMINAL_FAIL` 集合扩展兼容多名**（succeeded / success / done / completed；failed / error）：spec 未约束，但 MinerU 部署版本多样，先放宽，给真服务联调留余地。
- **client 每次请求新建 AsyncClient**：与 firecrawl 行为一致；MVP 不持久化连接池（poll 间隔默认 5s 远大于 keepalive 收益）。

## 本地校验结果

```text
uv run python -c "<AC-1/2/3/4/5/6 dry imports>"     → 全部 True
uv run ruff check apps/api packages/core worker/src  → All checks passed!
uv run mypy apps/api/dataplat_api packages/core/src worker/src → Success: no issues found in 96 source files
```

## 已知未解决问题

- **MinerU 实际响应 JSON schema 尚未联调确认**：本变更 `_mineru_client.py` 用宽松假设（task_id/id 双兼容，多终态枚举）；live 联调归 follow-up `processor-pdf-mineru-live-*`。
- **大 PDF 上传 multipart 是否需要分块**：MVP 直接整 bytes 提交；如 MinerU 接受上限 < 待处理 PDF 大小，需 follow-up `processor-pdf-mineru-multipart-chunk-*`。
- **httpx 连接复用**：每次请求新建 AsyncClient，poll 频繁时浪费 TCP；如真测下来 100+ PDF/小时则需 follow-up `processor-pdf-mineru-conn-pool-*`。

## 下一步

进入阶段 4 编码评审：spawn 独立 sonnet reviewer 子 agent，加载 `.harness/skills/code-review/SKILL.md`，写 `code_review_v1.md`。
