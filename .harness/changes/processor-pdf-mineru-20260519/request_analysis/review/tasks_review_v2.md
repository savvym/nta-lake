---
change_id: processor-pdf-mineru-20260519
target: tasks.md
target_version: 2
review_version: 2
reviewer: claude-agent:processor-pdf-mineru-20260519-stage2-reviewer-v2
reviewed_at: 2026-05-19T11:30:00Z
verdict: APPROVED
---

# Tasks Review v2

## §1 v1 MUST FIX 复检

| # | v1 摘要 | v2 修法 | 验证证据 | 结论 |
|---|---|---|---|---|
| MUST FIX-4 | T-5 指定 `run_ac_skipif_no_pg_minio_redis` for AC-10，测试是纯 unit 不需 pg/minio/redis，会导致 behavioral AC 在 CI 中静默 SKIP | T-5 description 将 AC-10 的调用方式改为无条件 `run_ac`，并显式注释 `**AC-10 一律用 run_ac（不是 run_ac_skipif_no_pg_minio_redis）**`；同步更新 T-4 为纯 unit 测试模式（不经 ProcessorRunner / 数据库 / MinIO / Redis） | `grep -n "run_ac_skipif_no_pg_minio_redis" tasks.md`：仅命中 revision_notes（第 10、12 行，引用旧问题文案）和 T-5 description 中的否定说明（第 112 行："AC-10 一律用 run_ac（不是 run_ac_skipif_no_pg_minio_redis）"）；T-5 正文无 `run_ac_skipif_no_pg_minio_redis` 调用指令 | **RESOLVED** |

说明：`grep` 输出仍命中 3 处，但经逐行确认：第 10/12 行在 frontmatter `revision_notes` 中（描述已修复的旧问题），第 112 行在 T-5 description 中以否定形式引用（"不是 run_ac_skipif_no_pg_minio_redis"）。T-5 实际指令为 `run_ac`。结论 RESOLVED。

---

## 检查清单结论（plan 模式 tasks.md v2）

| 项 | 结论 | 说明 |
|---|---|---|
| 每个任务粒度合理（1-3 小时） | PASS | T-1～T-6 仍为单文件级实现或本地验证，粒度合理 |
| depends_on 形成 DAG，没有循环 | PASS | 依赖链 T-1 → T-2 → T-3 → T-4 → T-5 → T-6；T-4 depends_on [T-2, T-3]；无循环 |
| 评审 / 单测 / CI / 部署阶段对应任务都存在 | PASS | process_tasks 含 P-spec-review / P-code-review / P-test-review / P-push / P-ci / P-deploy / P-user-confirm 全 7 项 |
| 没有"做完整个系统"类目标性任务 | PASS | 每个任务均指向具体文件或具体命令 |
| 每条 AC 至少有一个非 process_tasks 任务覆盖 | PASS | 覆盖矩阵 AC-1～AC-13 均有 T-1～T-6 中至少一个覆盖 |
| T-5 AC-10 使用 `run_ac`（无条件） | PASS | MUST FIX-4 已修，见 §1 |

---

## §2 v2 新增 / 调整内容审查

### 2.1 T-5 修改正确性

T-5 description v2：
- 第 1 段：`按 spec.md 表中命令逐条 run_ac`（无条件）
- 第 2 段明确否定：`**AC-10 一律用 run_ac（不是 run_ac_skipif_no_pg_minio_redis）**`
- 第 3 段：`AC-10 命令按 spec.md § "AC-10 完整验证命令" fenced block 原样落地，管道符 | 不要加反斜杠转义`

与 spec.md AC-10 fenced block 引用一致，与 T-4 纯 unit 设计一致。修法正确。

### 2.2 T-4 描述 v2 一致性

T-4 v2 将标题改为"写 tests/test_pdf_mineru.py（≥ 6 个测试，纯 unit，无 pg/minio/redis）"，description 强调"直接 new 一个 PdfMineruProcessor() 并调 .run(...)"，fixture 构造列出 FakeRepoView / FakeBlobStore / fake_ctx / monkeypatch httpx 四件套。与 spec.md T-4 / AC-9 / AC-10 / AC-12 行为描述完全对齐。

### 2.3 T-2 config_schema 字段新增

T-2 description v2 新增：
```
- config_schema: dict[str, Any] = {"type":"object","additionalProperties":False,
    "properties":{"parse_method":{"type":"string"},
                  "poll_interval_seconds":{"type":"number"},
                  "poll_timeout_seconds":{"type":"number"}}}
```
与 spec.md AC-1 `isinstance(p.config_schema, dict)` 断言一致；字段内容也与 PdfMineruSpec 三个字段（`parse_method` / `poll_interval_seconds` / `poll_timeout_seconds`）完全对应。

### 2.4 DAG 健全性

依赖链 T-1 → T-2 → T-3 → T-4 → T-5 → T-6 无变化，无环。T-4 → T-5 → T-6 为写测试 → 写 self_check → 本地验证，顺序合理。

### 2.5 覆盖矩阵

AC-1 ～ AC-13 全覆盖，与 tasks 中各 T 的 `covers_ac` 字段一致。

### 2.6 T-5 covers_ac 字段（v1 NICE-1 延续）

T-5 covers_ac 仍为 `[AC-11, AC-13]`，v1 NICE-1 建议改为 `[AC-13]`（AC-11 的实际运行在 T-6）。v2 未修改。该项为 NICE TO HAVE 级别，不阻塞通过，但保留以下观察：

- T-5 "追加 AC block" 本身不运行 ruff/mypy，AC-11 的实际门禁由 T-6 执行
- 将 AC-11 挂在 T-5 上会造成 stage 6 reviewer 追溯覆盖责任时轻微混淆

---

## §3 v2 verdict 与问题列表

### MUST FIX

（无）

### SHOULD FIX

（无）

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-1 | tasks.md T-5 `covers_ac` | T-5 `covers_ac: [AC-11, AC-13]`，但 AC-11（ruff+mypy）的实际运行入口是 T-6；T-5 只负责把 AC block 写入 self_check.sh，不直接验证 AC-11 | 将 T-5 `covers_ac` 改为 `[AC-13]`，AC-11 仅保留在 T-6，语义更精确；不阻塞通过 |

---

## Verdict

**APPROVED**

v1 唯一 MUST FIX-4（T-5 用 `run_ac_skipif_no_pg_minio_redis` 静默 SKIP behavioral AC）已修为无条件 `run_ac`，逻辑正确，与 spec 纯 unit 测试设计对齐。

v2 无新 MUST FIX。tasks 可随 spec APPROVED 一同进入 stage 3 编码阶段。

---

## 复检指引

```bash
# 复检 MUST FIX-4：T-5 正文不含 run_ac_skipif 调用指令（revision_notes 引用除外）
awk '/^  - id: T-5/{p=1} p && /^  - id: T-6/{exit} p' \
  .harness/changes/processor-pdf-mineru-20260519/request_analysis/tasks.md \
  | grep "run_ac_skipif_no_pg_minio_redis" \
  && echo "STILL IN T-5 BODY" || echo "PASS: not in T-5 body"

# 确认 T-5 description 含 run_ac 无条件路径
awk '/^  - id: T-5/{p=1} p && /^  - id: T-6/{exit} p' \
  .harness/changes/processor-pdf-mineru-20260519/request_analysis/tasks.md \
  | grep -q "run_ac" && echo "run_ac found in T-5" || echo "MISSING"

# DAG 无环验证
grep "depends_on" .harness/changes/processor-pdf-mineru-20260519/request_analysis/tasks.md

# process_tasks 全 7 节点
grep -cE "estimated_stage:.*(request_analysis_review|coding_review|unit_test_review|stage-7|ci_result|deployment|user_confirmation)" \
  .harness/changes/processor-pdf-mineru-20260519/request_analysis/tasks.md
```
