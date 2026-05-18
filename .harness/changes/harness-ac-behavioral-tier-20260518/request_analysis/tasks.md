---
change_id: harness-ac-behavioral-tier-20260518
version: 3
authored_at: 2026-05-18T09:30:00Z
prior_version: 2
prior_review: request_analysis/review/tasks_review_v2.md
---

# Tasks

> **v3 修订说明**：闭 stage 2 tasks_review_v2.md（spec_review_v2 MUST FIX #2 联动）。T-4/T-6 双条件 (ii) 同步改 AC 行 regex；T-6 fixture-bad 增加最隐蔽反例打靶。

## v1 review 闭环表

| # | 类别 | 位置 | v1 问题 | v2 状态 |
|---|---|---|---|---|
| MUST #1 | awk + env 入口 | T-4, T-6 | awk 错误 + 无 SCAN_DIR/EXEMPT 入口 | **CLOSED**：T-4 description 改正确 awk + 加两个 env 入口；T-6 重写 fixture 用 subshell + env override |
| MUST #2 | T-1 过载 | T-1 | 单一 T-1 含 7 子项 | **CLOSED**：拆为 T-1a / T-1b / T-1c |
| MUST #3 | T-6 kind 列双检 | T-6 | 缺 spec MUST #7 联动 | **CLOSED**：T-6 加双条件断言描述 |
| MUST #4 | T-3 4 checkpoint | T-3 | 文案太空 | **CLOSED**：T-3 description 改 4 个 checkpoint |
| SHOULD #1 | P-ci/P-deploy 改 self-attest | process_tasks | 与 spec AC-5 矛盾 | **CLOSED**：改 status: self-attest + notes |
| SHOULD #2 | T-5 与 spec 非范围矛盾 | T-5 | spec 非范围说"不改 _template 表头" | **CLOSED via spec v2**：spec 翻转决策，_template 加 kind 列 |
| SHOULD #3 | T-6 fixture 应 stage unit_test | T-6 | 编码与单测混 | **CLOSED**：T-6 仅含 block 函数 + 内部 fixture 调用；T-7 改名 T-8 含真跑全仓 self_check；新 T-7 仅含 `test_ac_kind_lint_fixture.sh` 跑（unit_test） |
| SHOULD #4 | T-7 期望值动态 | T-7 | 写死 PASS 数 | **CLOSED via spec AC-8 改写** + tasks T-8 description 改"block 8/8 PASS + 2 个 global lint PASS"（不写死总数） |

## 任务清单

```yaml
tasks:
  - id: T-1a
    title: SKILL 加 AC 分层规约定义 + 判定指引（behavioral 三层）
    description: |
      .harness/skills/request-analysis/SKILL.md 末尾（"跨 AC 一致性自审清单" 后）新增段
      "AC 分层规约"，含：
        (a) kind=static/behavioral 二分定义
        (b) 判定指引（混合型必拆为两条 AC）
        (c) behavioral 三层范例：
            L1 真起服务 curl smoke（含部署面）
            L2 ASGITransport in-process roundtrip（含路由）
            L3 load_recipe / pydantic parse / bash fixture 真跑断言（含纯逻辑）
        (d) 纯 grep / test -f / dry-import 全 static
        (e) "每个非豁免 change 至少 1 条 behavioral AC" 硬约束
      预计 ~1.5h。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1, AC-2]
    status: pending
    commits: []

  - id: T-1b
    title: SKILL 加豁免清单（19 ID 分两类）+ 自声明机制 + 豁免判定标准
    description: |
      在 T-1a 同段或邻段加：
        (a) **永久豁免清单（2 个，"纯 harness"）**：
            - harness-bootstrap-20260516
            - harness-reviewer-agent-separation-20260518
        (b) **暂豁免 grandfather（17 个，实代码 change，必须 backfill）**：
            17 个 ID 全列出（见 spec AC-7）
        (c) 自声明机制：spec.md frontmatter 加 `ac_kind_lint: exempt` 字段
        (d) **豁免判定标准**：自声明必须满足"代码改动只在 .harness/* / wiki/* /
            scripts/* / *.md 范围内"，且 reviewer 复核（git diff --stat）
        (e) follow-up `harness-ac-kind-backfill-*` 标 P1（下个非紧急 sprint）
      预计 ~1h。
    depends_on: [T-1a]
    estimated_stage: coding
    covers_ac: [AC-7]
    status: pending
    commits: []

  - id: T-1c
    title: SKILL 加混合 AC 拆分示例（伪代码）
    description: |
      在 T-1a 同段加"混合型 AC 拆分"小节，附伪代码示例：
        原 "AC-N: POST /repos 返回 201 + 路由文件含 @router.post(/repos)"
        →
        AC-Na (static)：grep -q "@router.post(/repos)" routers/repos.py
        AC-Nb (behavioral)：uv run pytest tests/test_repos.py::test_create_201
      预计 ~0.5h。
    depends_on: [T-1a]
    estimated_stage: coding
    covers_ac: [AC-1]
    status: pending
    commits: []

  - id: T-2
    title: expert-reviewer SKILL 加 stage 2 reviewer 必查 3 项
    description: |
      .harness/skills/expert-reviewer/SKILL.md 在"reviewer 字段填写规约"邻段加：
        stage 2 必查 3 项：
        (i) AC 表是否有 `kind` 列
        (ii) 是否至少 1 条 behavioral
        (iii) 若 spec frontmatter 声明 `ac_kind_lint: exempt`，
             reviewer 必跑 `git diff --stat origin/main..HEAD` 验证改动只在
             .harness/* / wiki/* / scripts/* / *.md 范围内，**结果必须粘贴到 review 文件**
      违反任一项 → MUST FIX。
    depends_on: [T-1a]
    estimated_stage: coding
    covers_ac: [AC-3]
    status: pending
    commits: []

  - id: T-3
    title: development-process.md stage 9 加 4 checkpoint + self-attest 模板
    description: |
      .harness/rules/development-process.md "阶段 9 部署验证" 段加硬约束文案，
      必含 4 个 checkpoint：
        (i) 默认：有部署面的 change 必须 verdict=PASS
        (ii) 替代路径：允许 self-attest (理由)，**必填 4 字段**：
             - 理由（一句话说明为什么用 self-attest）
             - 本机证据列表（命令输出路径或粘贴）
             - 跑过的命令（bash 历史 / 命令列表）
             - 时间（ISO8601）
        (iii) **禁止纯 deferred**（无 self-attest 或证据空）
        (iv) 引用 .harness/skills/request-analysis/SKILL.md § "AC 分层规约"
      附 self-attest 模板片段（5-10 行 markdown 块示例）。
      预计 ~1h。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-5]
    status: pending
    commits: []

  - id: T-4
    title: scripts/_self_check.sh 加 run_ac_kind_lint global function
    description: |
      加 `run_ac_kind_lint()`，与 `run_reviewer_lint` 同型（fail-fast `exit 1`）：
        - env 入口：`AC_KIND_LINT_SCAN_DIR`（默认 .harness/changes）+
                    `AC_KIND_LINT_EXEMPT_OVERRIDE`（默认 19 个硬编码，逗号分隔覆盖）
        - 遍历 SCAN_DIR 下所有 spec.md
        - 跳过：豁免清单 + _template + frontmatter `ac_kind_lint: exempt`
        - 对剩余：
            * 用 `awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' "$spec"` 抽 AC 表段
            * **双条件断言（v3 加固）**：
                (i) grep -qE '^\|[^|]*\|[[:space:]]*kind[[:space:]]*\|' <段>
                    # kind 列表头存在
                (ii) grep -qE '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|' <段>
                    # **必须锚定 AC 行的 kind 单元格** —— 不接受裸 grep -q behavioral
                    # （会被 AC 描述里"behavioral 三层"等字串误命中，机械化保护失效）
            * 任一不满足 → echo "FAIL: <change_id> 缺 kind 列 / 缺 AC 行 kind=behavioral" → exit 1
        - 全部通过 → echo "PASS: ac_kind_lint" → return 0
        - 对外 1 个 run_ac 计数（与 reviewer-lint 同模式）
      在 main 末尾（reviewer-lint 之后）调用 run_ac_kind_lint。
      预计 ~2h。
    depends_on: [T-1a]
    estimated_stage: coding
    covers_ac: [AC-4, AC-6]
    status: pending
    commits: []

  - id: T-5
    title: _template/request_analysis/spec.md 示例 AC 表加 kind 列
    description: |
      .harness/changes/_template/request_analysis/spec.md 的示例 AC 表加 `kind` 列：
        | ID | kind | 描述 | 验证方式 | 期望 |
        | AC-1 | static | <e.g. 路由存在> | grep | hit |
        | AC-2 | behavioral | <e.g. POST /repos → 201> | ASGITransport pytest | 201 |
      让新 change 复制 _template 时自然带列。
      （**v2 与 spec 非范围对齐**：spec 翻转决策允许加列）
    depends_on: [T-1a]
    estimated_stage: coding
    covers_ac: [AC-1, AC-6]
    status: pending
    commits: []

  - id: T-6
    title: scripts/lint/test_ac_kind_lint_fixture.sh（AC-4 fixture 真跑脚本）
    description: |
      新建 scripts/lint/test_ac_kind_lint_fixture.sh：
        - 用 mktemp -d 造 3 个临时目录：/tmp/fixture-ok / /tmp/fixture-bad-no-kind /
          **/tmp/fixture-bad-static-but-mention-behavioral**（v3 新增最隐蔽反例）
        - /tmp/fixture-ok 下放一个最小合规 spec.md：含 kind 列表头 + AC-1 行 kind 单元格真为 behavioral
        - /tmp/fixture-bad-no-kind 下放：AC 表完全不含 kind 列
        - **/tmp/fixture-bad-static-but-mention-behavioral 下放（关键打靶）**：
            * AC 表有 kind 列
            * 所有 AC 行 kind 单元格都是 static
            * AC 描述里在多个位置塞 "behavioral" 字串（如"参考 behavioral 三层"、
              "未来可加 behavioral AC" 等）
            * 期望 lint FAIL —— 用以验证 (ii) 是 AC 行 regex 而非裸 grep
        - 在 subshell 中跑 3 次：
            (export AC_KIND_LINT_SCAN_DIR=/tmp/fixture-ok AC_KIND_LINT_EXEMPT_OVERRIDE=""; \
             source scripts/_self_check.sh; run_ac_kind_lint)  → 期望退码 0
            (export AC_KIND_LINT_SCAN_DIR=/tmp/fixture-bad-no-kind ...; run_ac_kind_lint)
              → 期望退码 != 0
            (export AC_KIND_LINT_SCAN_DIR=/tmp/fixture-bad-static-but-mention-behavioral ...; \
             run_ac_kind_lint) → 期望退码 != 0
        - trap cleanup 删除所有 /tmp/fixture-* 目录
        - 任一断言失败 → exit 1；全通过 → exit 0
      预计 ~1.5h。
    depends_on: [T-4]
    estimated_stage: coding
    covers_ac: [AC-4]
    status: pending
    commits: []

  - id: T-7
    title: scripts/_self_check.sh 本 change block (run_harness_ac_behavioral_tier)
    description: |
      加 `run_harness_ac_behavioral_tier()`，含 AC-1..AC-8 八条 AC 验证：
        - AC-1..AC-3, AC-5, AC-7：静态 grep / test -f
        - AC-4：调 `bash scripts/lint/test_ac_kind_lint_fixture.sh`
        - AC-6：grep self_check 含 run_ac_kind_lint + awk 抽本 spec AC 表用 AC 行 regex 计数 behavioral ≥ 2（**用锚定 regex 而非裸 grep**） + grep _template 含 kind 列
        - AC-7：for loop 19 ID grep + 分类字面命中（永久豁免/暂豁免）
        - AC-8：grep 自递归（确认本 block 在 main 调用链中）
      在 main 添加调用。
      预计 ~1.5h。
    depends_on: [T-4, T-6]
    estimated_stage: coding
    covers_ac: [AC-6, AC-8]
    status: pending
    commits: []

  - id: T-8
    title: 本机跑通全仓 self_check（行为型 AC-8 自验证）
    description: |
      DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
      DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
      DATAPLAT_REDIS_PORT=6379 \
      bash scripts/_self_check.sh
      期望：
        - 退码 0
        - 本 change block 8/8 PASS
        - global run_reviewer_lint PASS
        - global run_ac_kind_lint PASS
        - 不强约束总 PASS 数
      如 FAIL：
        - 若 fixture 测试本身 FAIL → 回 T-4 / T-6 修 lint 函数
        - 若豁免名单读取错误（误对豁免 change 报 FAIL）→ 回 T-4 修豁免逻辑
        - 若新 lint 抓出真违规（如某历史 closed change 不在豁免名单）→ 回 T-1b 补入豁免
    depends_on: [T-7]
    estimated_stage: unit_test
    covers_ac: [AC-4, AC-8]
    status: pending
    commits: []
```

## 阶段任务（必备占位，不要漏）

```yaml
process_tasks:
  - id: P-spec-review
    estimated_stage: request_analysis_review
    status: pending  # v1 review APPROVED 后改 done

  - id: P-code-review
    estimated_stage: coding_review
    status: pending

  - id: P-test-review
    estimated_stage: unit_test_review
    status: pending

  - id: P-ci
    estimated_stage: ci_result
    status: self-attest
    notes: "项目无 remote（git remote 未配置），无法触发 GHA；长期未决；本 change 不阻塞收尾"

  - id: P-deploy
    estimated_stage: deployment
    status: self-attest
    notes: "纯 harness 变更无部署面（仅改 .harness/* + scripts/_self_check.sh + scripts/lint/test_ac_kind_lint_fixture.sh）；deploy_verify 用 self-attest 替代，理由+本机证据+命令+时间在 deployment/deploy_verify_v1.md 填齐"

  - id: P-user-confirm
    estimated_stage: user_confirmation
    status: pending
```

## DAG 健全性

```text
T-1a ──┬─→ T-1b
       ├─→ T-1c
       ├─→ T-2
       ├─→ T-4 ─→ T-6 ─→ T-7 ─→ T-8
       └─→ T-5
T-3 (独立可并行实现，覆盖 rules 文档；与 SKILL 改动解耦)
```

无环。T-8 是终点（行为型 AC-8 自验证）。

## 验收覆盖矩阵

| AC | kind | 关联任务 |
|---|---|---|
| AC-1 | static | T-1a, T-1c, T-5 |
| AC-2 | static | T-1a |
| AC-3 | static | T-2 |
| AC-4 | **behavioral** | T-4, T-6, T-8 |
| AC-5 | static | T-3 |
| AC-6 | static | T-4, T-5, T-7 |
| AC-7 | static | T-1b, T-7 |
| AC-8 | **behavioral** | T-7, T-8 |

每条 AC 至少有一个非 process_tasks 的任务覆盖。**behavioral AC 数：2（AC-4 + AC-8）**，满足规约（dogfood）。
