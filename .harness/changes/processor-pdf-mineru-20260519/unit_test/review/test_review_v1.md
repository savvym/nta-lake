---
change_id: processor-pdf-mineru-20260519
target: test_report_v1.md + tests/test_pdf_mineru.py (commit d7a6fe1)
target_version: 1
review_version: 1
reviewer: claude-agent:processor-pdf-mineru-20260519-stage6-reviewer-v1
reviewed_at: 2026-05-19T09:44:00Z
verdict: APPROVED
---

# Test Review v1

## 检查清单结论（artifact 模式）

| 项目 | 状态 | 说明 |
|---|---|---|
| 每条 spec behavioral AC 都映射到至少一条具体测试用例 | PASS | AC-9 / AC-10 / AC-12 均有对应 pytest 用例 |
| 没有空跑断言（`assert True` / `assert x is not None` 类） | PASS | 所有断言均有实质内容 |
| mock 范围与 coding-style.md 一致（数据访问层禁 mock） | PASS | 被测对象 PdfMineruProcessor / MinerUClient 均未 mock；httpx、BlobStore、RepoView 均是测试替身而非被测对象 |
| 测试名能反映场景 | PASS | 7 个函数名均清晰描述被测场景 |
| 测试不依赖 pg / minio / redis | PASS | FakeBlobStore（hashlib 内存计算）/ FakeRepoView（in-memory dict）/ monkeypatch httpx；纯 unit |
| 本地 pytest 7/7 PASS | PASS（以 test_report 为凭证） | 0 skip / 0 xfail |
| ruff + mypy 全绿 | PASS（以 test_report 为凭证） | 96 source files no issues |

---

## §1 测试逐个评审

### test_run_success

**覆盖目标**：AC-9 success 分支——happy path，1 个 PDF 输入，验证 ProcessResult 结构与 BlobStore 内容写入。

**是否真 behavioral**：是。调用了真实的 `PdfMineruProcessor().run()`，走完 `_process_one` 协程（含 MinerUClient.submit + fetch_markdown + blob_store.put），断言产出文件名、BlobStore 收到的 bytes、bytes_written、submit/poll 调用次数与 URL。不是单纯的类型检查。

**断言充分性**：
- `result.file_count == 1`：覆盖计数
- `result.files[0].path == "sample.md"`：覆盖 AC-8 输出文件名（with_suffix）
- `blob_store.puts == [b"# Hello\n"]`：覆盖 Markdown 内容真实写入 BlobStore
- `result.bytes_written == len(b"# Hello\n")`：覆盖字节计数
- `submit_calls[0]["url"] == "http://mineru.test/tasks"`：覆盖 HTTP submit 端点格式
- `len(submit_calls) == 1 and len(poll_calls) == 1`：覆盖 submit/poll 各调用一次

**过度/欠断言**：`result.files[0].sha256` 未断言，属轻微欠断言，但 AC-9 未要求；`BlobPutResult` 的 sha256 由 FakeBlobStore 用真实 `hashlib.sha256` 计算，正确性已被 FakeBlobStore 实现保证。整体充分。

**结论**：通过。

---

### test_run_poll_failed_raises

**覆盖目标**：AC-9 poll-failed 分支——poll 返回 `status=failed` 时 processor 抛 ValueError。

**是否真 behavioral**：是。设置 poll_sequence 为 failed 响应，真实调用 `PdfMineruProcessor().run()`，并用 `pytest.raises(ValueError, match="failed")` 断言错误类型与消息关键字。

**断言充分性**：`match="failed"` 命中 `"MinerU task task-xyz failed: ocr crashed"`，充分。

**潜在问题**：测试未调用 `monkeypatch.delenv("MINERU_API_TOKEN", raising=False)`。如果宿主环境碰巧设置了 `MINERU_API_TOKEN`，token 会被传入 client，但这不影响 `failed` 分支的错误路径——token 有无不影响 ValueError 的抛出。功能上无问题，但从测试隔离角度属轻微 NICE TO HAVE（可加 delenv 消除宿主环境变量的干扰）。

**结论**：通过。

---

### test_run_env_missing_url

**覆盖目标**：AC-5 / AC-9 env 缺失路径——unset `MINERU_API_URL` 时 processor 抛 ValueError 且消息含字段名。

**是否真 behavioral**：是。调用真实 `PdfMineruProcessor().run()`，ValueError 在 `os.environ.get(_ENV_URL, "").strip()` 空值分支抛出，`match="MINERU_API_URL"` 精确断言错误消息含 env 变量名，便于运维定位。

**设计亮点**：未调用 `_patch_httpx`，因为 ValueError 在 httpx 被访问前已抛出——这正确体现了代码中 env 检查在 client 构造之前的顺序，是逻辑正确性的隐式验证。

**结论**：通过。

---

### test_client_token_header_present

**覆盖目标**：AC-12 token 存在分支——`MinerUClient(token="secret-token")` 的 submit 与 poll 请求头均含 `Authorization: Bearer <token>`。

**是否真 behavioral**：是。直接实例化 `MinerUClient`，通过 `asyncio.run(client.submit(...))` / `asyncio.run(client.poll(...))` 触发真实 HTTP 逻辑（httpx 已 monkeypatch），断言 `submit_calls[0]["headers"]["Authorization"] == "Bearer secret-token"` 和 `poll_calls[0]["headers"]["Authorization"] == "Bearer secret-token"`。

**覆盖范围说明**：测试直接构造 `MinerUClient(token=...)` 而非通过 env var 端到端测试。AC-12 规范为 `MinerUClient 在请求头注入 Authorization Bearer`，与测试范围一致，不要求 env var 端到端覆盖（AC-5 的 env 读取由 test_run_env_missing_url 覆盖）。

**断言完整性**：submit 和 poll 两个方法的 header 都做了断言，充分覆盖 `_headers()` 的作用面。

**结论**：通过。

---

### test_client_token_header_absent

**覆盖目标**：AC-12 token 缺失分支——`MinerUClient(token=None)` 的 submit/poll 请求头不含 `Authorization`。

**是否真 behavioral**：是。构造 `MinerUClient(token=None)`，调用 submit/poll 后断言 `"Authorization" not in headers`，精确验证 `_headers()` 在 token=None 时返回空 dict 的行为。

**结论**：通过。

---

### test_run_skips_non_pdf

**覆盖目标**：AC-7 非 PDF 过滤——上游含 `.txt` / `.pdf` / `.md` 三个文件时，产出仅含 1 个 `.md`，非 PDF 不进产出 tree。

**是否真 behavioral**：是。FakeRepoView 有 3 个文件，调用真实 `PdfMineruProcessor().run()`，断言 `result.file_count == 1`、`result.files[0].path == "doc.md"`，且反向断言 `"notes.txt" not in paths` / `"readme.md" not in paths`。

**断言完整性**：正向（只有 1 个 .md）+ 反向（非 PDF 不进 tree）双重断言，充分。FakeRepoView 的 `.md` 文件（`readme.md`）也被过滤，体现大小写不敏感以外的文件类型过滤逻辑。

**结论**：通过。

---

### test_run_poll_timeout

**覆盖目标**：tasks.md T-4 可选第 7 条——`fetch_markdown` 循环轮询超时后抛 `ValueError("轮询超时")`。

**是否真 behavioral**：是。FakeClient 永远返回 `{status: "running"}`（`len(seq)==1` 分支不弹出，永远返回同一项），配合 `poll_interval_seconds=0.01 / poll_timeout_seconds=0.05` 让超时迅速触发，`pytest.raises(ValueError, match="轮询超时")` 断言错误消息含中文字段，与 `_mineru_client.py:102-104` 错误文案对齐。

**已知风险（test_report 已说明）**：测试依赖真实 `asyncio.sleep(0.01)` 的 wallclock 时间，在极端 CI 系统抖动下（sleep 精度 > 50ms）可能导致测试慢 / 偶发 flaky。0.05s timeout 经过 5 次循环（5×10ms）应可触发，但这是系统时钟精度依赖，非完全确定性。见 §4 SHOULD FIX-1。

**结论**：通过（含已知风险）。

---

## §2 behavioral AC 对照表

| AC ID | 描述（摘自 spec.md） | 对应测试 | 通过条件 | 状态 |
|---|---|---|---|---|
| AC-9 | mock httpx，跑 pdf-mineru success 路径产出 `<basename>.md` blob；轮询 status=failed → raise ValueError | `test_run_success` + `test_run_poll_failed_raises` | 两个用例 PASS | COVERED |
| AC-10 | `tests/test_pdf_mineru.py` ≥ 6 测试 + 全 PASS（含 `test_run_env_missing_url`） | 7 个测试全部（含 `test_run_env_missing_url`） | collect ≥ 6 且全 PASS | COVERED（7 ≥ 6，含要求用例） |
| AC-12 | `MINERU_API_TOKEN` 存在时请求头含 `Authorization: Bearer <token>`；不存在时无 | `test_client_token_header_present` + `test_client_token_header_absent` | 两个用例 PASS | COVERED |

**备注**：
- AC-9 要求覆盖 success + poll-failed 两个分支，test_run_success 覆盖 success，test_run_poll_failed_raises 覆盖 poll-failed，完整。
- AC-10 要求 `test_run_env_missing_url` 明确存在，已确认：第 3 个测试即为该用例。
- AC-12 的 pytest 命令（`test_client_token_header_present` + `test_client_token_header_absent`）与 spec 验证方式完全对应。

---

## §3 stage 4 SHOULD FIX 复检

### S-1：合并 asyncio.run（两次 → 一次）

**状态：已修复（CLOSED）**

**证据**：`apps/api/dataplat_api/processors/pdf_mineru.py:107-118` 定义 `async def _process_one(pdf_bytes, filename)`，将 `client.submit` + `client.fetch_markdown` + `blob_store.put` 合并为一个协程；`line 128`：`sha, size = asyncio.run(_process_one(raw, filename))`，每个 PDF 只有一次 `asyncio.run`。与 code_review_v1.md S-1 建议一致（"将 _convert_one 与 _upload 合并为一个 _process_one 协程"）。

### S-2：payload 截断（`{payload!r}` → 截断 repr）

**状态：未修复（deferred）**

**证据**：`apps/api/dataplat_api/processors/_mineru_client.py:113`：`f"MinerU submit 响应无 task_id / id 字段：{payload!r}"`；`line 122`：`f"MinerU poll 响应缺 status 字段或类型错误：{payload!r}"`，均仍使用全量 repr。

**评估**：code_review_v1.md §4 建议下一步明确 `S-2 若不在本 change 修，在 processor-pdf-mineru-live-* follow-up 时补截断`。test_report_v1.md 未明示 S-2 deferred 路径，但未修改该代码属于合理的显式 deferred（code review verdict 已说明）。本次测试评审中不阻塞；保持 SHOULD FIX 状态，建议在 `summary.md` 的阶段 4 SHOULD FIX 子项里补记 deferred 理由与跟进点（见 §4 SHOULD FIX-2）。

---

## §4 问题列表

### MUST FIX（0 条）

无。

---

### SHOULD FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | `tests/test_pdf_mineru.py:270-285` (`test_run_poll_timeout`) | 测试依赖真实 `asyncio.sleep(0.01)` 的 wallclock 时间（`poll_timeout_seconds=0.05`）。在高负载 CI 环境或虚拟化时钟精度差的容器中，`asyncio.sleep(0.01)` 实际 sleep 时间可能显著偏高，导致超时判断延迟触发或测试本身变慢。test_report 已坦承此点但将风险推后到 "stage 8 CI 第一次跑结果"——这对于已知可改进的确定性问题略显被动。 | 将 `asyncio.sleep` mock 掉：`monkeypatch.setattr("dataplat_api.processors._mineru_client.asyncio.sleep", lambda _: asyncio.sleep(0))`（或直接替换为 no-op coroutine），消除对系统时钟的依赖，使超时测试在任何环境下即时触发。此改法不影响超时判断逻辑（`time.monotonic` 仍被真实调用，极短 0.05s 会在第一次 monotonic 检查时命中）。 |
| SHOULD FIX-2 | `apps/api/dataplat_api/processors/_mineru_client.py:113,122` | S-2（payload!r 截断）在 test_report 及 summary.md 中未见 deferred 原因和跟进点记录。code_review_v1.md §4 已说明 "S-2 若不在本 change 修，在 processor-pdf-mineru-live-* follow-up 时补截断"，但该声明应同步反映在 `summary.md` 的阶段 4 SHOULD FIX 子项中（development-process.md §4 Quality Gate："SHOULD FIX 若有未关闭项，须在 summary.md 显式说明 deferred 原因和跟进位置"）。 | 在 `.harness/changes/processor-pdf-mineru-20260519/summary.md` 的 coding/review 行下，添加 `deferred_should_fix: S-2 _mineru_client.py payload!r 截断 → deferred to processor-pdf-mineru-live-* follow-up`，使流程闭环。 |

---

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| N-1 | `tests/test_pdf_mineru.py:190-202` (`test_run_poll_failed_raises`) | 测试未调用 `monkeypatch.delenv("MINERU_API_TOKEN", raising=False)`。若宿主环境碰巧设置了该环境变量，token 会被传入 client（但不影响 failed 分支的 ValueError 抛出）。 | 加一行 `monkeypatch.delenv("MINERU_API_TOKEN", raising=False)` 与 test_run_success 保持一致，明确宿主环境隔离意图。 |
| N-2 | `tests/test_pdf_mineru.py:167-187` (`test_run_success`) | `result.files[0].sha256` 未断言。当前 FakeBlobStore 用真实 `hashlib.sha256(b"# Hello\n")` 计算 sha256，若将来 BlobPutResult 构造错误，测试不会发现。 | 可加 `import hashlib; assert result.files[0].sha256 == hashlib.sha256(b"# Hello\n").hexdigest()` 强化内容完整性断言。 |
| N-3 | `tests/test_pdf_mineru.py:45-100` (`_FakeAsyncClient` 类变量) | `_FakeAsyncClient.submit_calls / poll_calls / poll_sequence` 是类级变量，通过 `type(self).xxx` 访问。当前用 `_reset_fake()` 在每个测试开头重置，顺序单线程运行无问题。但 `pytest-xdist` 并行模式下，多个 worker 共享同一进程时类变量会产生竞争。 | 若未来引入 xdist 并行化，将类变量改为实例变量（在 `__init__` 中初始化），并通过 fixture 参数或测试内局部实例化 `_FakeAsyncClient` 避免跨测试共享。当前顺序跑无问题，记录为 N 级。 |

---

## §5 Verdict 与建议下一步

### Verdict：APPROVED

**理由：**

- **MUST FIX = 0**。7 个测试全部真跑被测代码（PdfMineruProcessor / MinerUClient），所有断言有实质内容，无空跑断言。
- **behavioral AC 全覆盖**：AC-9（success + poll-failed）/ AC-10（≥6 用例 + 含 test_run_env_missing_url）/ AC-12（token 在/不在）均有明确对应的可自动运行的 pytest 用例，且 7/7 PASS。
- **mock 范围合理**：被测对象（PdfMineruProcessor、MinerUClient）未被 mock；mock 层为 httpx（外部 HTTP）/ BlobStore（存储 I/O）/ RepoView（上游数据）三层，与项目 coding-style 一致；FakeBlobStore 用真实 hashlib 计算 hash，不是硬编码假值。
- **stage 4 SHOULD FIX S-1 已修复**：`asyncio.run` 合并为单次，通过代码审查。
- **测试独立性可接受**：每个测试开头调用 `_reset_fake()` 显式重置类变量，顺序运行下无状态泄漏；class-variable 模式在当前 non-xdist 场景下安全（N-3 归入 NICE TO HAVE）。
- **SHOULD FIX 2 条**：SHOULD FIX-1（asyncio.sleep mock）不影响测试正确性，属防御性改进；SHOULD FIX-2（summary.md S-2 deferred 记录）是流程规范性问题，不阻塞 stage 7。

### 建议下一步

1. **进入 stage 7（push）**。MUST FIX = 0，verdict = APPROVED，满足 development-process.md §6 Quality Gate。
2. **SHOULD FIX-2 建议在 push 前补完**：在 `summary.md` 阶段 4 行补记 `S-2 deferred to processor-pdf-mineru-live-*`，消除流程记录空洞。
3. **SHOULD FIX-1** 可在 stage 8 CI 第一次运行后决策是否补 mock，作为 follow-up 低优先级处理。
4. **NICE TO HAVE N-1/N-2/N-3** 可视后续迭代需要按需处理，不阻塞本 change。

---

## 复检指引（Generator 修 SHOULD FIX 后应运行）

```bash
# 复检 SHOULD FIX-1（若决定修 asyncio.sleep mock）：
cd apps/api && uv run pytest -v tests/test_pdf_mineru.py::test_run_poll_timeout
# 确认 PASS 且运行时间 < 0.5s（无真实 sleep 则即时完成）

# 复检 SHOULD FIX-2（summary.md S-2 deferred 记录）：
grep -q "S-2" .harness/changes/processor-pdf-mineru-20260519/summary.md && \
  grep -q "deferred" .harness/changes/processor-pdf-mineru-20260519/summary.md && \
  echo "OK: S-2 deferred recorded" || echo "FAIL: summary.md missing S-2 deferred note"

# 全量回归（确保改动不破坏其他测试）：
cd apps/api && uv run pytest -q tests/test_pdf_mineru.py
# 期望：7 passed
```
