---
change_id: processor-pdf-mineru-assets-20260520
version: 1
authored_at: 2026-05-19T12:50:00Z
status: draft
---

# Spec：pdf-mineru 同时保存 images + content_list 到 silver 仓

## 背景

上游 `processor-pdf-mineru-20260519` § 非范围显式 deferred 了图片/表格资源抽取（"开 follow-up `processor-pdf-mineru-assets-*`"）。`live-fix` 完成后用户提需求：silver target 仓除了 `<basename>.md`，还要装 MinerU 抽出来的 images 与结构化大纲 `content_list.json`；PDF 原件留 bronze 不复制。

实测 MinerU 3.1.x（命中 `return_images=true` + `return_content_list=true`）的真实响应：

```json
{
  "backend": "...",
  "version": "...",
  "results": {
    "<filename_stem>": {
      "md_content": "...markdown，图片引用已用相对路径 images/<sha>.jpg ...",
      "content_list": "<JSON 字符串，含 bbox/text 块>",
      "images": {"<sha>.jpg": "data:image/jpeg;base64,/9j/...", ...}
    }
  }
}
```

关键观察：
1. **MinerU 已自动把 MD 内图片引用重写为相对路径 `images/<sha>.jpg`**——本变更不需要做 MD 重写。
2. `content_list` 是预序列化的 JSON 字符串，直接落 blob 即可。
3. `images` 是 `dict[filename → data-URI base64]`；filename 含扩展名（`<sha>.jpg`）。
4. MinerU 图片 filename 用图片 sha；与本仓 CAS dedup 天然契合。

## 问题陈述

- `PdfMineruSpec` 当前不暴露 `return_images` / `return_content_list`；MinerU 默认 false，走不到 images / content_list 路径。
- `MinerUClient.submit` 不传这两个 flag。
- `MinerUClient.fetch_markdown` 只取 md text；丢弃同响应里的 images / content_list。
- `PdfMineruProcessor.run` 只写一个 `<basename>.md` IngestFileRef；缺 images/* 与 content_list.json。
- 测试 fake `_FakeAsyncClient.result_response` 没模拟 images + content_list 字段。

## 范围

In scope（与下方 AC 对齐）：

- AC-1: `PdfMineruSpec` 新增 `return_images: bool = True` + `return_content_list: bool = True`（extra=forbid 保持）
- AC-2: `_mineru_client.MinerUClient.submit` 接受 `return_images` / `return_content_list` kwargs 透传到 multipart `data`
- AC-3: 新增 `MinerUClient.fetch_full_result(task_id) -> dict`（含 `markdown: str` / `images: dict[str, bytes]`（已 base64 解码）/ `content_list: str | None`）
- AC-4: 兼容 data-URI prefix（`data:image/*;base64,`）→ bytes；裸 base64 也接受；空 images / 空 content_list 容忍
- AC-5: `PdfMineruProcessor.run` 对每个 PDF 写出 `<basename>.md` + `images/<filename>` + `<basename>.content_list.json`
- AC-6: behavioral：fake httpx 返 1 PDF + 2 image + content_list → processor.run 产 ≥ 4 IngestFileRef
- AC-7: 上游 7 个 unit tests 不回归
- AC-8: tests/test_pdf_mineru.py ≥ 9 用例全 PASS
- AC-9: ruff + mypy 全 PASS
- AC-10: scripts/_self_check.sh 含 `run_processor_pdf_mineru_assets` + filter + 全跑入口
- AC-11: 上游 client tests 不回归
- AC-12: AC-12 自递归

## 非范围

- 不动 PDF 原件位置：PDF 留 bronze
- 不重写 MD 内图片引用（MinerU 已自重写）
- 不引入 lang_list / formula_enable / table_enable / 页面范围（独立 follow-up）
- 不引入 ZIP 模式
- 不引入 image OCR 二次处理 / VLM 重描述
- 不动 UI（开 follow-up `web-pdf-mineru-ui-*`）

## 验收标准（12 AC）

| ID | kind | 描述 | 验证 | 期望 |
|---|---|---|---|---|
| AC-1 | static | PdfMineruSpec 含 return_images / return_content_list 默认 True | `cd apps/api && uv run python -c "from dataplat_api.processors.pdf_mineru import PdfMineruSpec; s=PdfMineruSpec.model_fields; assert s['return_images'].default is True and s['return_content_list'].default is True"` | 命令退出 0 |
| AC-2 | static | client.submit 签名含 return_images / return_content_list | `cd apps/api && uv run python -c "import inspect; from dataplat_api.processors._mineru_client import MinerUClient; sig=inspect.signature(MinerUClient.submit); assert 'return_images' in sig.parameters and 'return_content_list' in sig.parameters"` | 命令退出 0 |
| AC-3 | static | client 含 fetch_full_result 方法 | `cd apps/api && uv run python -c "from dataplat_api.processors._mineru_client import MinerUClient; assert hasattr(MinerUClient, 'fetch_full_result')"` | 命令退出 0 |
| AC-4 | static | client 含 base64 decode 逻辑 | `grep -qE "b64decode\|base64" apps/api/dataplat_api/processors/_mineru_client.py` | 命令退出 0 |
| AC-5 | static | pdf_mineru.py 写 images/* 路径 | `grep -F -q "images/" apps/api/dataplat_api/processors/pdf_mineru.py` | 命令退出 0 |
| AC-6 | static | pdf_mineru.py 写 content_list.json | `grep -F -q "content_list.json" apps/api/dataplat_api/processors/pdf_mineru.py` | 命令退出 0 |
| AC-7 | behavioral | fake httpx 返 1 PDF + ≥2 image + content_list → ≥ 4 IngestFileRef | `cd apps/api && uv run pytest -q --tb=no tests/test_pdf_mineru.py::test_run_with_assets` | PASS |
| AC-8 | behavioral | tests/test_pdf_mineru.py ≥ 9 + 全 PASS | 见 § "AC-8 完整命令" fenced block | ≥ 9 + 全 PASS |
| AC-9 | static | ruff + mypy 全 PASS | `uv run ruff check apps/api packages/core worker/src && uv run mypy apps/api/dataplat_api packages/core/src worker/src` | 命令退出 0 |
| AC-10 | static | self_check 含本 change AC block | `grep -q "run_processor_pdf_mineru_assets" scripts/_self_check.sh` | 命令退出 0 |
| AC-11 | behavioral | 上游 7 个核心 unit tests 不回归 | `cd apps/api && uv run pytest -q --tb=no tests/test_pdf_mineru.py::test_run_success tests/test_pdf_mineru.py::test_run_poll_failed_raises tests/test_pdf_mineru.py::test_run_env_missing_url tests/test_pdf_mineru.py::test_client_token_header_present tests/test_pdf_mineru.py::test_client_token_header_absent tests/test_pdf_mineru.py::test_run_skips_non_pdf tests/test_pdf_mineru.py::test_run_poll_timeout` | 7 PASS |
| AC-12 | static | AC-12 自递归 | `grep -q "run_processor_pdf_mineru_assets" scripts/_self_check.sh` | 命令退出 0 |

### AC-8 完整命令

```bash
[ "$(cd apps/api && uv run pytest --collect-only -q tests/test_pdf_mineru.py 2>&1 | grep -cE 'test_pdf_mineru\.py::')" -ge 9 ] && \
(cd apps/api && uv run pytest -q --tb=no tests/test_pdf_mineru.py)
```

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| MinerU data-URI 不带 prefix | 低 | 解码错 | _decode_image_data_uri 兼容裸 base64 + 显式 ValueError |
| 大 PDF images 字段巨大（实测 4.5MB JSON for 1.8MB PDF） | 中 | 内存峰值 | MVP 接受；follow-up `processor-pdf-mineru-stream-result-*` 如需 |
| MD 引用 `images/<sha>.jpg`，blob 写入路径与之不符 | 高 | viewer 看不到图 | AC-5 grep + AC-7 behavioral 在 fake 里断言 path 形如 `images/<...>` |
| content_list 缺失（未来版本变） | 中 | 跑挂 | 视为可选；None / 空 → 不写 content_list.json，warn log；不抛 |
| 图片 sha 冲突 | 极低 | 覆盖 | MinerU 用 content sha；同内容 = 同 sha = CAS dedup |
| 跳过 stage 2/4/6 reviewer | 中 | 流程偏离 | **会话级授权偏离 #1** 沿用；stage 8 回归 self_check 三块（含 live-fix）全绿作机械化补偿 |
| ProcessResult.files 数量增长 | 低 | 下游消费变化 | 下游 processor 按 iter_paths() 工作；多文件只是更多 path 不破坏 protocol |

## 跨链路一致性自审

1. ✅ summary 已写
2. ✅ 范围 / 非范围明确
3. ✅ AC 全可机械化
4. ✅ AC 分层：3 behavioral
5. ✅ 非豁免
6. ✅ 反向 grep 无前置依赖
7. ✅ spec ↔ tasks ↔ self_check 一致
8. ✅ process_tasks 6 节点（2/4/6 self-attest）

## 受影响模块

- 改：`apps/api/dataplat_api/processors/_mineru_client.py`
- 改：`apps/api/dataplat_api/processors/pdf_mineru.py`
- 改：`apps/api/tests/test_pdf_mineru.py`
- 改：`scripts/_self_check.sh`

## 不受影响

- `processors/__init__.py`：注册保持
- ProcessorRegistry / Runner / RunContext / Routers：不动
- PdfMineruProcessor 类身份 / produces / accepts / config_schema 形态：不动

## 引用

- 上游 `processor-pdf-mineru-20260519` § 非范围 deferred
- 实测 layout：`/tmp/mineru_full_result.json`（4.5MB；clbench-paper.pdf 跑出来）
- MinerU OpenAPI `/openapi.json`：fields `return_images` / `return_content_list`；data-URI 风格靠实测
