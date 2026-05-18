---
change_id: adapter-firecrawl-20260517
version: 1
authored_at: 2026-05-18T08:50:00Z
branch: main
base_commit: fee46ee (llm-gateway-mvp close)
head_commit: working-tree
status: waiting_review
---

# Coding Report v1

## 改动文件清单

| 路径 | 类型 | 说明 | 关联 task |
|---|---|---|---|
| `apps/api/dataplat_api/adapters/_image_extract.py` | new | extract_image_urls(content, base_url)：HTML `<img>` + md `![]()` 合并，文档出现顺序保序 + 去重 + urljoin 解析 + data:/javascript:/ftp:/mailto: 跳过 | T-1 |
| `apps/api/dataplat_api/adapters/firecrawl_url.py` | new | FirecrawlURLSpec（extra=forbid + field_validator urls）+ FirecrawlURLAdapter（name=firecrawl-url v=0.1 output_subtype=webpage-collection）+ _run_all 串行抓 URL → ctx.llm → blob_store + 可选 image 提取下载 | T-2 |
| `apps/api/dataplat_api/adapters/__init__.py` | edit | import + register FirecrawlURLAdapter | T-3 |
| `apps/api/dataplat_api/runner/adapter_runner.py` | edit | 构 ctx 时 `llm=get_llm_gateway()` + `blob_store=store`（与 ProcessorRunner 对齐；消化 adapter-runner-ctx-llm-inject-* follow-up） | T-3 |
| `apps/api/tests/test_firecrawl.py` | new | 6 测试：(a) extract_image_urls 单元 / (b) adapter.ingest 单元（_FakeAsyncClient + _SummaryLLM + _FakeStore）/ (c) admin /jobs/ingest 201 / (d) user 403 / (e) end-to-end succeeded 含 assets/0/content.md + ≥1 image / (f) unreachable URL marks_failed | T-4 |
| `scripts/_self_check.sh` | edit | 追加 run_adapter_firecrawl 13 AC + filter + 总入口 | T-6 |

## 与 tasks.md 的映射

| Task | 状态 | 备注 |
|---|---|---|
| T-1 _image_extract | done | 文档出现顺序（按 match.start() 排序）|
| T-2 FirecrawlURLAdapter | done | _run_all 共享 httpx.AsyncClient；image 失败 warn + skip 不阻塞 |
| T-3 register + AdapterRunner ctx 扩 | done | raw-file-upload 13 测试无回归 |
| T-4 6 tests | done（全 PASS） | 3.21s |
| T-5 lint+type | done | ruff 自动 fix 1 处 UP037；mypy 87 source files 0 errors |
| T-6 self_check | done | 13/13；全仓 186→199 |

## 偏离 spec / trade-off

- **_image_extract 改为文档出现顺序**：spec §AC-5 没要求严格顺序，但 test_a_extract_image_urls_unit 期望"HTML 第 1 行优先于 md 第 2 行"。最初实现是"HTML 全部 → MD 全部"（更省事），但单元测试看到顺序混乱。改用 `matches.sort(key=lambda m: m.start())` 按文档出现位置排序，语义更清晰。spec AC-5 用 any() 不验顺序，仍 PASS。
- **AC-7 反向 grep 误伤 docstring**：firecrawl_url.py 原 docstring 含 "asyncio.gather" 字面 → grep 命中 → AC-7 FAIL。改 docstring 措辞规避。这是 reverse-grep 的本质代价（"行内 token 严格不存在"）；后续 follow-up 可考虑用更精确 pattern（如 `^\s*[^#]*asyncio\.gather\(`）。
- **测试用 `/jobs/ingest` 而非 `/repos/{}/{}/ingest`**：本仓 ingest 是同步路由 + jobs/ingest 是异步路由，本变更"async via worker"要走 jobs/ingest（payload schema = JobIngestRequest 含 owner+name+request 三层嵌套）。最初按 spec 抄错；ingest router 没有 async_ 字段。
- **test_e fake provider 行为不适配**：FakeLLMProvider 默认模板 `FAKE[{model_id}]: {first_user[:80]}`，prompt 前缀长度 > 80 → 截断后不含 image URL。改用 monkeypatch.setattr 直接替换 `FakeLLMProvider.call` 让它返固定的 `![pic](https://imgs.test/x.png)` markdown。生产无影响，仅 test_e 一处。
- **AdapterRunner ctx.llm + ctx.blob_store 顺手加**：消化 llm-gateway-mvp 列的 `adapter-runner-ctx-llm-inject-*` follow-up；与 ProcessorRunner 对齐；test_ingest.py 13 个旧测试无回归（raw-file-upload 不访问 ctx.llm/blob_store）。

## 本地校验

```text
ruff: All checks passed!（自动 fix 1 处 UP037 quotes-from-annotation）
mypy: Success: no issues found in 87 source files
pytest test_firecrawl.py: 6 PASS (3.21s)
pytest test_firecrawl + test_ingest + test_llm + test_processor: 33 PASS (14.68s)（含 13 ingest 旧测试 + 8 processor + 6 llm 全无回归）
self_check adapter-firecrawl: PASS=13 / FAIL=0 / SKIP=0
self_check 全仓: PASS=199 / FAIL=0 / SKIP=0（14 个 block）
```

## 已知未解决问题

- **firecrawl-py SDK / JS-rendered / rate-limit / robots.txt / 并发 / 增量 / image OCR / 多媒体 / live test / Web UI**：均在 spec §Out of scope；各自 follow-up（9 条）
- **fake provider 默认模板太短截断 prompt**：test_e 需 monkeypatch 绕过；可考虑 FakeLLMProvider 加 `echo_mode` 参数返回完整 prompt（follow-up `fake-llm-echo-mode-*`）
- **AC-7 reverse grep 误伤 docstring**：可改更精确 pattern（follow-up `harness-lint-ac-precise-grep-*`）

## 下一步

进入阶段 4 编码评审。
