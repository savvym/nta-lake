---
change_id: adapter-firecrawl-20260517
target: coding/main（工作树）
target_head: working-tree（待 commit）
review_version: 1
reviewer: application-owner-agent
reviewed_at: 2026-05-18T09:00:00Z
verdict: APPROVED
---

# Code Review v1

## 范围与作者声明对照

- coding_report 声明的改动文件：6 个
- `git status --porcelain` 实际：6 个（2 M + 4 ??）
- 差异：**无**

## 正确性 / 安全 / 架构

### MUST FIX

无。

### SHOULD FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | apps/api/dataplat_api/adapters/firecrawl_url.py:_run_all | image 失败"吞掉不阻塞"用 BLE001（broad-except）；丢失原始 traceback | follow-up `adapter-firecrawl-narrow-except-*`（参 adapter-narrow-except-* 同模式） |

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | firecrawl_url.py:_HTML_TRUNCATE=8000 | 8000 字符截断对长页面会丢正文；MVP 可接受但需 follow-up 改为递归分块 | follow-up `adapter-firecrawl-chunking-*` |
| 2 | firecrawl_url.py prompt | "Output only the Markdown." 仍可能被 LLM 加 "Here is the markdown:" 前缀 | follow-up `adapter-firecrawl-prompt-strict-*` |
| 3 | _image_extract.py | data: / javascript: / ftp: / mailto: 跳过列表硬编码；可抽 constant | 改动小不阻塞 |
| 4 | test_firecrawl.py test_e | monkeypatch `FakeLLMProvider.call` 用了 class-level 方法替换；同进程内可能泄漏到其他 test。pytest monkeypatch 会自动 undo，但 OK 时机 | 测试结尾 reset_llm_gateway() 也清；OK |

## 风格 / 性能 / 可观测性（参考 coding-style.md）

- ✅ async 函数全程 async；httpx.AsyncClient 用 async with
- ✅ Pydantic schema extra=forbid + field_validator urls 校验 http(s)://
- ✅ ctx.llm / ctx.blob_store 缺 → 显式 ValueError（不静默 fallback）
- ✅ blob_store.put 用 BytesIO 流式接口（processor-framework 同 pattern）
- ✅ 反向 grep 拦 None：adapter_runner.py 不存在 `llm=None` / `blob_store=None`
- ✅ AC-7 反向拦 asyncio.gather 在文件级（含 docstring 都不允许字面）→ 强约束
- ⚠️ _run_all 函数 ≈ 60 行，单 URL 循环体 ≈ 35 行，可读性 OK；接近 coding-style §1.2 上限

## 跨改动观察

- **AdapterRunner / ProcessorRunner 对称**：现在两个 runner 都注入 `llm + blob_store + logger`；下次出现第 4 个 ctx 字段时建议抽 `build_run_context(store)` helper
- **第二个 adapter 跑通**：AdapterRegistry 多 adapter 的关键路径首次验证（之前只 raw-file-upload 一个）；test_a registry 单元已隐式覆盖
- **ctx.llm 路径全打通**：processor-framework / llm-gateway-mvp / adapter-firecrawl 三层依赖到此完整；下游 llm-qa-gen 可直接 use

## Deferred SHOULD FIX

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| SHOULD FIX | image GET 失败用 BLE001 broad-except | follow-up `adapter-firecrawl-narrow-except-*` |
| NICE TO HAVE | _HTML_TRUNCATE=8000 长页丢正文 | follow-up `adapter-firecrawl-chunking-*` |
| NICE TO HAVE | prompt 仍可能被 LLM 加前缀 | follow-up `adapter-firecrawl-prompt-strict-*` |

## Verdict

APPROVED（MUST FIX = 0；3 SHOULD/NICE 已 deferred）。

## 后续指引

进入阶段 5 单测编写 → 6 单测评审。
