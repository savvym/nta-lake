---
change_id: processor-pdf-mineru-live-fix-20260519
version: 1
authored_at: 2026-05-19T12:30:00Z
status: draft
---

# Spec：MinerU 真实 API 对齐（X-API-Key + 202 + files 数组 + /result）

## 背景

上游 change `processor-pdf-mineru-20260519` 在 stage 1 spec § "待澄清问题" 显式 deferred 了 MinerU 真服务的字段名校对：
> "deferred to coding 阶段：MinerU 实际响应 JSON 字段名的确切拼写——本 change 在 `_mineru_client.py` 集中处理，coding 阶段联系真服务确认；若有出入仅改 client 的解析函数，不影响 spec 的 13 AC 结构。"

stage 10 用户实测期间，用户提供了部署中的 MinerU endpoint（`http://111.229.120.156:8001`）与 API key。拉 `/openapi.json` + 实测 401/200 后发现 4 处客户端假设与真实 API 不一致：

| 维度 | 上游 change MVP 假设 | 真实 MinerU 3.1.14 API |
|---|---|---|
| 认证头 | `Authorization: Bearer <token>` | `X-API-Key: <key>` |
| `POST /tasks` 成功状态码 | 200 | **202 Accepted** |
| multipart 字段名 | `file`（单数） | **`files`（数组）** |
| markdown 来源 | `GET /tasks/{id}` 响应的 `markdown` 字段 | **`GET /tasks/{id}/result`** 单独端点 |

上游 spec 已预告这是 client 层级的解析改动，**不影响产品语义、Processor Protocol 实现、测试 mock 模式、self_check AC 静态结构**。本 follow-up 严格落在「client 改动 + 测试 fake 同步 + 新 AC block」范围内。

## 问题陈述

- `apps/api/dataplat_api/processors/_mineru_client.py` 的 submit/poll/fetch_markdown 假设与真服务不符，直接 live 调用会得到：submit 422（字段名错）/ submit fail（202 被当 fail）/ 401（鉴权头错）/ fetch_markdown 抛 "markdown 字段缺失"（应去 `/result`）
- `tests/test_pdf_mineru.py` 的 `_FakeAsyncClient` 需要同步：接受 `files` + 返 202 + 暴露 `/result` 端点 + 断言 `X-API-Key` 而非 `Authorization`
- `PdfMineruSpec` 需要新增 `backend` 字段（默认 `hybrid-auto-engine`，匹配 MinerU 默认）

## 范围

In scope（与下方 AC 对齐）：

- AC-1: `_mineru_client.py` 鉴权头 `Authorization Bearer` → `X-API-Key`
- AC-2: `_mineru_client.py` submit multipart 字段 `file` → `files`
- AC-3: `_mineru_client.py` submit 接受 200 或 202
- AC-4: `_mineru_client.py` 新增 `fetch_result(task_id) -> str`（GET `/tasks/{id}/result`）；`fetch_markdown` 拆为 poll 等终态 → fetch_result
- AC-5: `pdf_mineru.py` `PdfMineruSpec` 新增 `backend: str = "hybrid-auto-engine"`（extra=forbid 保持）；client.submit 接受 backend 参数透传
- AC-6: `tests/test_pdf_mineru.py` 全部更新到新协议；≥ 7 用例全 PASS
- AC-7: ruff + mypy 全 PASS
- AC-8: 上游 change 的 `run_processor_pdf_mineru` 13 AC 仍 22/22 PASS（回归）
- AC-9: `scripts/_self_check.sh` 含 `run_processor_pdf_mineru_live_fix`（自递归）

## 非范围

- 不抽图片 / 表格 / 公式资源
- 不动 Pipeline / UI / 部署
- 不引入 `lang_list` / `formula_enable` 等 MinerU 高级字段（follow-up）
- 不向 ProcessRequest.config 渗漏 X-API-Key（仍走 env `MINERU_API_TOKEN`）
- 不动上游 change 已 close 的 history（独立 follow-up）

## 验收标准（9 AC）

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | _mineru_client.py 含 X-API-Key；无 Authorization/Bearer 残留 | `grep -q "X-API-Key" apps/api/dataplat_api/processors/_mineru_client.py && ! grep -qE "Authorization\|Bearer" apps/api/dataplat_api/processors/_mineru_client.py` | 命令退出 0 |
| AC-2 | static | submit 用 `files` 字段（双引号包裹 grep） | `grep -F -q '"files"' apps/api/dataplat_api/processors/_mineru_client.py` | 命令退出 0 |
| AC-3 | static | submit 接受 200 或 202 | `grep -qE "200,[[:space:]]*202\|status_code[[:space:]]+in[[:space:]]+\\(200" apps/api/dataplat_api/processors/_mineru_client.py` | 命令退出 0 |
| AC-4 | static | client 含 fetch_result 方法 + 含 `/result` 路径 | `cd apps/api && uv run python -c "from dataplat_api.processors._mineru_client import MinerUClient; assert hasattr(MinerUClient, 'fetch_result')" && grep -q "/result" apps/api/dataplat_api/processors/_mineru_client.py` | 命令退出 0 |
| AC-5 | static | PdfMineruSpec 含 backend 字段默认 hybrid-auto-engine | `cd apps/api && uv run python -c "from dataplat_api.processors.pdf_mineru import PdfMineruSpec; assert PdfMineruSpec.model_fields['backend'].default == 'hybrid-auto-engine'"` | 命令退出 0 |
| AC-6 | behavioral | tests/test_pdf_mineru.py ≥ 7 + 全 PASS | 见 § "AC-6 完整命令" fenced block | ≥ 7 + 全 PASS |
| AC-7 | static | ruff + mypy 全 PASS | `uv run ruff check apps/api packages/core worker/src && uv run mypy apps/api/dataplat_api packages/core/src worker/src` | 命令退出 0 |
| AC-8 | behavioral | 上游 `run_processor_pdf_mineru` 13 AC 不回归 | `bash scripts/_self_check.sh current processor-pdf-mineru-20260519` | 22/22 PASS |
| AC-9 | static | self_check 含本 change AC block | `grep -q "run_processor_pdf_mineru_live_fix" scripts/_self_check.sh` | 命令退出 0 |

### AC-6 完整命令

```bash
[ "$(cd apps/api && uv run pytest --collect-only -q tests/test_pdf_mineru.py 2>&1 | grep -cE 'test_pdf_mineru\.py::')" -ge 7 ] && \
(cd apps/api && uv run pytest -q --tb=no tests/test_pdf_mineru.py)
```

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| `/result` 响应 schema 不在 OpenAPI；markdown 可能在子字段 | 中 | live 仍失败 | fetch_result 解多种典型 layout（顶层 `markdown` / `md_content` / `results[0].markdown`）；都不命中 → raise ValueError 含 keys |
| 状态枚举不在 OpenAPI | 低 | hang in poll | 沿用宽松 _TERMINAL_OK/FAIL 集合；后续真测有偏差再修 |
| 反向 grep `! grep Authorization` 命中 import 或注释里的字面意外 | 低 | AC-1 误 fail | 实现里彻底删干净；不留 "Bearer" 字样 |
| 跳过 stage 2/4/6 reviewer | 中 | 流程偏离 | **会话级授权偏离 #1**：本 change 范围小（API 字段对齐 + 测试同步，无新业务）；用户已授权"一气呵成"演示；summary.md 标 self-attest 留痕 |
| API key 泄漏到 git / log | 高 | 凭据 | env 注入，不进代码 / 测试 / commit；token 值不打印 |

## 跨链路一致性自审

1. ✅ summary 已填；占位符 grep = 0（待 quick 自查）
2. ✅ 范围 / 非范围明确
3. ✅ AC 全可机械化
4. ✅ AC 分层：2 behavioral（AC-6 / AC-8）
5. ✅ 非豁免（动 apps/api + scripts/_self_check.sh）
6. ✅ AC-1 反向 grep + 强 grep；其他无需 test -f 前置
7. ✅ spec ↔ tasks ↔ self_check 一致
8. ✅ process_tasks 6 节点全列

## 受影响模块

- 改：`apps/api/dataplat_api/processors/_mineru_client.py`
- 改：`apps/api/dataplat_api/processors/pdf_mineru.py`
- 改：`apps/api/tests/test_pdf_mineru.py`
- 改：`scripts/_self_check.sh`

## 不受影响

- `processors/__init__.py`：pdf-mineru 注册保持
- ProcessorRegistry / Runner / RunContext / Routers / Pipeline：不动
- PdfMineruProcessor 类身份 / produces / accepts / config_schema 形态：不动（PdfMineruSpec 新增字段不破坏 forbid，因为字段在 schema 里）

## 引用

- 上游 change：`.harness/changes/processor-pdf-mineru-20260519/` § 待澄清 deferred 条款
- MinerU OpenAPI：`http://111.229.120.156:8001/openapi.json`（v3.1.14 实测）
