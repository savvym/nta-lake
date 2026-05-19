---
change_id: processor-pdf-mineru-20260519
title: PDF→MD via MinerU Processor
owner: application-owner-agent
started_at: 2026-05-19T08:56:58Z
stage: user_confirmation
status: done
last_updated: 2026-05-19T13:30:00Z
related_changes: []                      # 依赖或被依赖的其他 change id
---

# Summary

> 这是本变更的 Single Source of Truth。任何阶段开始 / 通过 / 失败都必须同步更新这里。

## 一句话目标

新增 `pdf-mineru` Processor：把 Bronze 仓里的 PDF 文件通过 MinerU HTTP API（异步 job + 轮询）转成 Silver 层的 Markdown 文件。

## 范围摘要

- **In scope**：
  - `apps/api/dataplat_api/processors/_mineru_client.py`：薄 HTTP 客户端（submit / poll / fetch_md）
  - `apps/api/dataplat_api/processors/pdf_mineru.py`：`PdfMineruSpec` Pydantic + `PdfMineruProcessor`（Bronze PDF → Silver Markdown）
  - 注册 `pdf-mineru` v0.1 到 ProcessorRegistry
  - env 读 `MINERU_API_URL` (必需) + `MINERU_API_TOKEN` (可选)；缺失时显式 ValueError
  - `apps/api/tests/test_pdf_mineru.py`：≥ 6 测试，monkeypatch `httpx.AsyncClient`，无真实 MinerU 依赖
  - `scripts/_self_check.sh`：追加 `run_processor_pdf_mineru` 13 AC + filter + 总入口
- **Out of scope**（显式）：
  - Pipeline / Recipe 自动触发 → follow-up `recipe-pdf-mineru-*`
  - Web UI 上传 PDF 入口 → follow-up `web-pdf-mineru-ui-*`
  - 真 MinerU 服务的 live CI 测试 → follow-up `processor-pdf-mineru-live-*`
  - 图片 / 表格 / 公式资源单独抽取（仅取 markdown 文本） → follow-up `processor-pdf-mineru-assets-*`
  - 并发处理多 PDF / 并发轮询 → follow-up `processor-pdf-mineru-concurrent-*`
  - 增量（同 PDF 跳过）→ follow-up `processor-pdf-mineru-incremental-*`

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 阶段 commit | 产物 / 报告 |
|---|---|---|---|---|---|
| 1 需求分析 | done | v2 | — | 3537913 | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | done | v2 | APPROVED (spec+tasks) | 3537913 | v1: [spec_review_v1.md](request_analysis/review/spec_review_v1.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md) <br>v2: [spec_review_v2.md](request_analysis/review/spec_review_v2.md) · [tasks_review_v2.md](request_analysis/review/tasks_review_v2.md) |
| 3 编码实现 | done | v1 | — | 6e726e5 | [coding_report_v1.md](coding/coding_report_v1.md) |
| 4 编码评审 | done | v1 | APPROVED (0 MUST / 2 SHOULD) | 59ea59e | [code_review_v1.md](coding/review/code_review_v1.md) |
| 5 单测编写 | done | v1 | — | d7a6fe1 | [test_report_v1.md](unit_test/test_report_v1.md) |
| 6 单测评审 | done | v1 | APPROVED (0 MUST / 2 SHOULD) | d7a6fe1 | [test_review_v1.md](unit_test/review/test_review_v1.md) |
| 7 代码推送 | done | — | — | 9882377 | origin/change/processor-pdf-mineru-20260519 |
| 8 CI 验证 | done | v1 | PASS（本 change 13/13；12 carry-over FAIL 非本 change 引入） | 9a8d4a3 | [ci_result_v1.md](ci_result/ci_result_v1.md) |
| 9 部署验证 | done | v1 | SKIPPED (noop) | 9a8d4a3 | [deploy_verify_v1.md](deployment/deploy_verify_v1.md) |
| 10 用户确认 | waiting | — | — | — | 待用户实测 |

## 关键决策

| 时间 | 决策 | 理由 / 取舍 | 关联文件 |
|---|---|---|---|
| 2026-05-19 | MinerU 集成走 HTTP API 而非 in-process import | 用户选定；GPU 资源隔离，worker 镜像不绑定 mineru/torch 依赖 | spec.md §背景 |
| 2026-05-19 | API 形态：异步 job（POST /tasks + GET /tasks/{id} 轮询） | 用户选定；支持大文件 / 集群部署 | spec.md §背景 |
| 2026-05-19 | endpoint / token 走环境变量 MINERU_API_URL / MINERU_API_TOKEN | 用户选定；与 LLM Gateway env 注入习惯对齐，避免 token 泄漏到 ProcessRequest.config | spec.md §背景 |
| 2026-05-19 | 输出层 = Silver / subtype="pdf-markdown" | 用户选定；符合 design.md Bronze(raw) → Silver(cleaned) 语义 | spec.md §范围 |
| 2026-05-19 | 本变更只做 Processor 实现 + 单测，不动 Pipeline / UI / live CI | 用户选定；防止 scope creep，依赖项分别开 follow-up change | spec.md §非范围 |

## 当前阻塞

- <如有阻塞，列在这里：等待谁的输入 / 待哪个上游 change 完成 / 待某个 ADR 决议>

## Deferred 项（已 review 通过但未在本 change 内修）

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| stage4 SHOULD FIX S-2 | `_mineru_client.py` 解析失败错误消息用 `payload!r` 全量，poll 含大 markdown 时异常体积膨胀且可能漏 doc 内容到日志 | follow-up change `processor-pdf-mineru-live-*`（联调时一并 truncate payload + 调整错误消息） |
| stage4 NICE TO HAVE | RepoView Protocol 漏 `iter_paths` 声明（系统性，跨多 processor） | follow-up change `core-repoview-protocol-iter-paths-*`（独立 change） |
| stage6 SHOULD FIX | `test_run_poll_timeout` 依赖 wallclock（asyncio.sleep 0.01）；当前 <1s 不阻塞 | follow-up change `processor-pdf-mineru-test-clock-mock-*`（接 CI flake 监控真出现再做） |

## 交付

> 关闭本变更时填写。

- Branch：`change/processor-pdf-mineru-20260519`（已 push 到 origin）
- PR：跳过 PR（PAT 缺 pull-requests scope）→ 直接 no-ff merge 到 main，与 PR #1 风格一致
- Merge commit：`4faaa5e`（main 上的 merge commit）
- 部署版本（如有）：n/a（stage 9 SKIPPED noop；env vars 由部署侧注入 `MINERU_API_URL` + 可选 `MINERU_API_TOKEN`）
- 用户确认：TBD（等用户实测后填）
- 关闭时间：TBD（stage 10 用户确认后填）

## 复盘（可选）

- 哪些步骤超预期顺利
- 哪些步骤踩坑：根因 + 防复发机制（一定要落到 rules / skills 的修订）
