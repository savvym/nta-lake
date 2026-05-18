---
change_id: processor-framework-20260517
target: coding/main（工作树）
target_head: working-tree（待 commit）
review_version: 1
reviewer: self-attest (会话级授权偏离 #1; 2026-05-17/18 用户授权 "你合理安排规划" 省 spawn 成本; 详见 harness-reviewer-agent-separation-20260518 §背景)
reviewed_at: 2026-05-17T18:45:00Z
verdict: APPROVED
---

# Code Review v1

## 范围与作者声明对照

- coding_report 声明的改动文件：17 个（含 _self_check.sh）
- `git status --porcelain` 实际：17 个（8 M + 9 ??）
- 差异：**无**

## 正确性 / 安全 / 架构

### MUST FIX

无。

### SHOULD FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | jobs/tasks.py run_process_job | 与 run_ingest_job 重复独立 engine 创建逻辑 | follow-up `worker-engine-pool-*`（已在 session_handoff 列表） |

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | processors/markdown_normalize.py | 规则简单（CRLF + trailing ws），未来加更多 normalize 规则时建议拆 module | 体量足够大时再拆，目前 < 50 行无必要 |
| 2 | runner/processor_runner.py | source_ref == target_ref 无 cycle 检测 | 已在 coding_report 注明 deferred 到 `processor-cycle-detection-*` |

## 风格 / 性能 / 可观测性（参考 coding-style.md）

- ✅ async 函数全程 async，无 sync IO 阻塞
- ✅ Pydantic schema 全部 extra=forbid
- ✅ 复用 BlobStore Protocol，无直接 boto3 调用
- ✅ 错误路径 mark_failed 而非 raise（worker 不会因异常宕掉）
- ✅ 未引入 magic 字符串（job_type 用 Literal["ingest","process"] 在 enqueue 校验）
- ⚠️ ProcessorRunner.run 函数体偏长（≈ 70 行），可读但接近 coding-style §1.2 上限；列入 NICE TO HAVE 不阻塞

## 跨改动观察

- 与 adapter framework 强对称：ProcessorRegistry/ProcessorRunner ↔ AdapterRegistry/AdapterRunner；这种"姊妹对"未来应抽 base，但 MVP 阶段保留重复以避免过早抽象（参 coding-style §三似行而非抽象原则）
- jobs/service.py dispatch 是开放式 if/elif，未来加 job_type 时记得扩；列入 follow-up `jobs-dispatch-registry-*` 候选

## Deferred SHOULD FIX

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| SHOULD FIX | run_process_job / run_ingest_job engine 创建重复 | follow-up `worker-engine-pool-*`（session_handoff 已列） |

## Verdict

APPROVED（MUST FIX = 0；1 SHOULD FIX 已 deferred 到 follow-up）。

## 后续指引

进入阶段 5 单测编写 → 6 单测评审。
