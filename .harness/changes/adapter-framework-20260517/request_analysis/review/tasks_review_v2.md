---
change_id: adapter-framework-20260517
target: tasks.md
target_version: 2
review_version: 2
reviewer: claude-stage2-reviewer-v2
reviewed_at: 2026-05-17T11:35:00Z
verdict: APPROVED
---

# Tasks Review v2

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1 tasks 部分 + `.harness/skills/request-analysis/SKILL.md` § 跨 AC 自审清单第 7 条（v2 加）。

- [x] 每个任务粒度合理（T-1~T-9 实现任务 1-3 小时；T-10~T-15 process 节点；T-8 拆 13 测试）。
- [x] depends_on 形成 DAG，无环（line 185-194 依赖图新版含 T-10→T-15 串行段）。
- [x] **评审 / 单测 / CI / 部署 / close 任务全部存在**（T-10~T-15 覆盖 stage-2/4/6/7/9/10；详见 v1 MUST FIX #1 复核）。
- [x] 没有 "做完整个系统" 类目标任务。
- [x] **每条 AC 都有非 process_tasks 任务覆盖**（AC 覆盖矩阵 line 200-214；AC-12 由 T-7b 显式主；详见 v1 MUST FIX #2 复核）。

### v1 MUST FIX 复核

| v1 MUST FIX | v2 修复证据 | 状态 |
|---|---|---|
| **#1 process_tasks 6 条不达标** | T-10（stage-2 spec/tasks review）/ T-11（stage-4 coding review）/ T-12（stage-6 test review）/ T-13（stage-7 CI）/ T-14（stage-9 deploy noop）/ T-15（stage-10 close + 反哺）全部就位。`grep -cE "estimated_stage: stage-(2\|4\|6\|7\|9\|10)" tasks.md` = **6**（≥ 6，达标）。依赖图末段（line 193）显式画出串行链 `T-9 → T-10 → T-11 → T-12 → T-13 → T-14 → T-15` | **CLOSED** |
| **#2 AC-12 无主** | T-7b（line 110-117）显式覆盖 AC-12：`uv run ruff check` + `uv run mypy` 全 PASS + 失败兜底方案（mypy 报错时转 property + __init__）。AC 覆盖矩阵 line 213 显式 `AC-12 → T-7b`。**复检指引原命令 `grep "AC 覆盖:.*AC-12"` 用英文冒号匹配 0；但 tasks 实际用全角"："，匹配命令应为 `grep "AC 覆盖：.*AC-12"`，实测命中 1（T-7b line 117）**——格式偏差不影响覆盖事实 | **CLOSED** |

### v1 SHOULD FIX 复核

| v1 SHOULD FIX | v2 修复证据 | 状态 |
|---|---|---|
| **#1 T-5 step 7/8 签名漂移 (2-tuple vs 3-tuple)** | T-5 标题已改 `AdapterRunner（v2：3-tuple + parent 自动接链）`（line 60）；签名 `async run(...) -> tuple[CommitORM, bool, IngestResult]`（line 63）；step 8 返 `(commit, dedup, result)` **3-tuple**（line 81）。spec AC-4（line 72/80）也同步改为 3-tuple，两文档一字不差对齐 | CLOSED |
| **#2 T-1 缺 Field import** | T-1 line 17 显式："在 `from pydantic import ...` 行追加 `Field`（v2 SHOULD FIX）" | CLOSED |
| **#3 IngestFileRef 导出表跨任务不清** | T-1 line 20 已明确 `protocols/__init__.py` 的 `__all__` 数组追加 `IngestFileRef`；T-6 line 98 含"验证 `from dataplat_core.protocols import IngestFileRef` 不报错（T-1 跨链验证）" | CLOSED |

### v1 NICE TO HAVE 复核

| v1 NICE TO HAVE | v2 修复 |
|---|---|
| #1 依赖图 T-1 画两次 | line 186-194 已重画 fanout 风格（T-1/T-2/T-3 并行 → T-4 / T-5），可读性提升 |
| #2 T-8 fixture 复用 | T-8 line 123 加："优先 import 自 `apps/api/tests/conftest.py` 已有 fixtures（`admin_user`/`normal_user`/`_override_blob_store`）；未提供再本地新增" |

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无新增。

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md line 117 `- AC 覆盖：AC-12` | 全文 `AC 覆盖` 后接全角"："（中文冒号），但 v1 review 复检指引给的命令是英文冒号 `grep "AC 覆盖:.*AC-12"`——格式偏差导致 v1 reviewer 自查命令在 v2 文件上误报 0 命中。覆盖事实没问题（矩阵 line 213 显式 AC-12→T-7b），但形式审查工具需对齐 | 建议统一为单一冒号样式，或更新 v2 SKILL grep 模板用 `[:：]` 兼容全角/半角。不阻塞 |
| 2 | tasks.md line 141-181（T-10~T-15 owner 字段） | T-10 line 145 标明 "owner：由 reviewer agent 完成"，但 T-11/T-12/T-13/T-14/T-15 未显式标 owner——v1 复检指引第 1 条第三项要求"每个 process_tasks 任务 owner 字段或 description 标明 '由 reviewer / CI agent / human 完成'"。当前仅 T-10 满足，其余靠 description 隐含 | 建议每个 T-11~T-15 加显式 `- owner: ...` 字段。不阻塞——description 已蕴含语义 |
| 3 | tasks.md line 144 (T-10 depends_on) | T-10 写 `depends_on: T-1~T-9（v1 spec/tasks 完）`——但实际 stage-2 review 评的是 spec.md + tasks.md，不依赖 T-1~T-9 实现；正确依赖应是"v1 spec/tasks 文档草稿就绪"，而 T-1~T-9 是 stage-3 实现任务。当前 depends_on 把 review 排到实现之后，倒置流程时序 | 修正：T-10 depends_on 应为空（或 `request_analysis/spec.md v1 generator 完成`）；T-11 coding review 才 depends_on T-1~T-9 完成。不阻塞——本变更 v1 spec 已在 reviewer v1 评完，实际流程已正确发生 |

## Verdict

**APPROVED**（MUST FIX = 0）

## 复检指引

v2 已通过 stage 2 tasks review，可进入 stage 3 coding。

下游 coding agent 自查（实施 T-1~T-9 时）：

1. **AC 覆盖矩阵零孤儿**：实施过程任何 AC 新增 → 同步更新 line 200-214 矩阵；任何 task 拆分/合并 → 同步更新映射。
2. **T-5 3-tuple 强制对齐**：实现 `AdapterRunner.run` 必须 return `(commit, dedup, result)`；T-6 构造 `IngestResponse` 必须用这个 dedup（不允许丢弃）。stage-4 coding review 时 `grep -nE "tuple\[CommitORM, bool, IngestResult\]" apps/api/dataplat_api/runner/adapter_runner.py` 期望命中 1。
3. **T-7b lint+mypy 不许跳过**：即使时间紧也不允许把 ruff/mypy fail 推到 stage 4 coding review。T-7b 失败 → 暂停后续 task。
4. **T-10~T-15 process 节点逐个 fire**：每个 stage 末尾产物（v* 文档）落地后 TaskUpdate completed。
5. **T-15 SKILL 反哺**：close 阶段必须落实 SKILL 4→7 条扩充已生效（reviewer v2 实测已在 SKILL.md 中，T-15 主要是 cross-check + 落 followup memory）。

## 评审实跑证据

```bash
# v1 MUST FIX 复核 grep
grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" tasks.md  # = 6（达标）
grep -nE "T-10|T-11|T-12|T-13|T-14|T-15" tasks.md          # 全部存在 + 矩阵 + 依赖图三处
grep -nE "AC-12" tasks.md                                   # T-7b 标题 + 覆盖 + 矩阵 = 4 命中
grep "AC 覆盖：.*AC-12" tasks.md                            # 1 命中（全角冒号）

# 3-tuple 跨文档一致
grep -nE "tuple\[CommitORM, bool, IngestResult\]" tasks.md  # T-5 line 63
grep -nE "tuple\[CommitORM, bool, IngestResult\]" spec.md   # AC-4 line 72

# parent 接链伪代码
grep -nE "resolved_parents|ref_row" tasks.md                # T-5 step 2 三分支
grep -nE "select\(RefORM\)" tasks.md                        # 显式 SQLAlchemy

# DAG 无环（手工拓扑）
# T-1, T-2, T-3 → T-4 / T-5 → T-6 → T-7 → T-7b → T-8 → T-9 → T-10 → T-11 → T-12 → T-13 → T-14 → T-15
# 无环、无悬挂依赖
```

**v1 → v2 修复完整性**：tasks 2 MUST FIX + 3 SHOULD FIX + 2 NICE TO HAVE 全部消化；新增 3 条 NICE TO HAVE（冒号/格式 / owner 字段 / T-10 depends 时序）均不阻塞。verdict **APPROVED**。
