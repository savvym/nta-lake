---
change_id: harness-remote-push-onboarding-20260518
version: 2
authored_at: 2026-05-19T00:00:00Z
prior_version: 1
prior_review: request_analysis/review/tasks_review_v1.md
---

# Tasks

> 8 个任务 + 1 个验证。粒度 < 45 min total。
>
> **v2 修订说明**：闭 tasks_review_v1 的 1 SHOULD FIX（T-3 description 去仓库 URL + 去自相矛盾"无 remote 时跳过"）。

## 任务清单

```yaml
tasks:
  - id: T-1
    title: request-analysis SKILL L289 去"无 remote 项目"措辞，首选 origin/main
    description: |
      .harness/skills/request-analysis/SKILL.md
      § "豁免判定标准（reviewer 复核）"末段：
        删 "无 remote 项目（本仓库当前情况）：用 git log --stat <baseline-commit>..HEAD 等价。"
        改为 "首选 git diff --stat origin/main..HEAD；离线 / 异常 / 早期未 push
              的本地 baseline 时，降级 git log --stat <baseline-commit>..HEAD 等价。"
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1]
    status: pending
    commits: []

  - id: T-2
    title: expert-reviewer SKILL L172 去"无 remote 时"分支
    description: |
      .harness/skills/expert-reviewer/SKILL.md
      § stage 2 AC kind 字段必查 §必查 3 项 第 3 项：
        删 "（或 git log --stat <baseline>..HEAD 无 remote 时）"
      保留主路径 "reviewer 必跑 git diff --stat origin/main..HEAD"。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-2]
    status: pending
    commits: []

  - id: T-3
    title: development-process stage 7 加 push origin main 步骤
    description: |
      .harness/rules/development-process.md § 阶段 7：
        §产出物 加一项：
          - git push origin main
        §Quality Gate 加一项：
          - git status 显示 "up to date with 'origin/main'"（验证本地与 remote 同步）
        §Rollback Route 加一项：
          - push 失败（鉴权 / 网络）→ 重试或检查 ssh-agent；不解决前不进入下一阶段
      **注**：rules 是项目通用文档，不写具体 remote URL（如 origin =
      git@... 形式）；具体 URL 在项目 README / 顶层 CLAUDE.md 上下文里维护。
      未来如有 fork 无 remote 场景，那时再单独 change 处理（YAGNI）。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-3]
    status: pending
    commits: []

  - id: T-4
    title: development-process stage 8 self-attest 措辞重写
    description: |
      .harness/rules/development-process.md § 阶段 8：
        §self-attest 模板（如有）+ §备注：
          删 "项目无 remote 长期未决" 措辞
          改 "本项目策略：本地 pytest + self_check.sh 等价 CI；不引入 GitHub Actions
              远程跑（理由：等价覆盖 + 反馈快 + 单作者无 PR review 摩擦）。
              新 change 标 stage 8 = self-attest 时必须引用本理由文案，
              不允许新 change 引 '无 remote 长期未决'（该理由已失效）。"
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-4]
    status: pending
    commits: []

  - id: T-5
    title: .gitignore 加 .claude/
    description: |
      .gitignore 末尾加一段：
        # Claude Code session state (worktrees + scoped cache)
        .claude/
      位置：紧跟既有 "# Python 虚拟环境" 等 section 之后，保持分组语义。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-5]
    status: pending
    commits: []

  - id: T-6
    title: 删除 .github/workflows/ci.yml
    description: |
      git rm .github/workflows/ci.yml
      如 .github/workflows/ 目录为空：git rm -r .github/workflows/（或保留空目录均可；
      AC-6 仅检查 ci.yml 不存在）
      撤销 bootstrap-monorepo AC-15（原 AC 内容保留在 bootstrap spec.md，本 change
      在 summary.md 记录反向）。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-6]
    status: pending
    commits: []

  - id: T-7
    title: scripts/_self_check.sh 删 bootstrap AC-15 ci.yml 检查
    description: |
      scripts/_self_check.sh L132-133（在 run_bootstrap_monorepo 函数内）：
        删除：
          run_ac AC-15 "ci.yml 合法 + 5 job + concurrency" \
            python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/ci.yml'))..."
      同步审核 run_bootstrap_monorepo 函数头注释 AC 总数（如有 "18 AC" 之类需改 "17 AC"）。
      不动其他 block / 其他 AC。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-7]
    status: pending
    commits: []

  - id: T-8
    title: 跑全仓 self_check 验证无回归
    description: |
      DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat \
        DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 \
        bash scripts/_self_check.sh
      期望：tail 含 "FAIL: 0"，全链路 PASS。
      AC-8 验证；通过即可 close。
    depends_on: [T-1, T-2, T-3, T-4, T-5, T-6, T-7]
    estimated_stage: deployment
    covers_ac: [AC-8]
    status: pending
    commits: []
```

## 阶段任务

```yaml
process_tasks:
  - id: P-spec-review
    estimated_stage: stage-2
    status: pending
    notes: "spawn sonnet reviewer（spec 范围较大，跨 4 个文件 + 撤销既有 AC，值得独立 review）"

  - id: P-code-review
    estimated_stage: stage-4
    status: self-attest
    notes: "micro change，~10 行 diff，spawn cost > value"

  - id: P-test-review
    estimated_stage: stage-6
    status: skipped
    notes: "纯文档/配置变更无单测"

  - id: P-push
    estimated_stage: stage-7
    status: pending
    notes: "本 change 自身建立的 stage 7 新规约：commit + push origin main + git status 验证 up to date"

  - id: P-ci
    estimated_stage: stage-8
    status: self-attest
    notes: "本项目策略：本地 pytest + self_check.sh 等价 CI（本 change 自身建立的新理由）"

  - id: P-deploy
    estimated_stage: stage-9
    status: pending
    notes: "T-8 = stage 9 验证（self_check 全跑）"

  - id: P-user-confirm
    estimated_stage: stage-10
    status: pending
    notes: "用户实测：(1) 本地 git status 显示 up to date with origin/main；(2) GitHub 仓库 commit 历史含本 change merge commit"
```

## DAG 健全性

```text
T-1, T-2, T-3, T-4, T-5, T-6, T-7 (全并行) ──→ T-8（全跑 self_check）
```

无环。终点 T-8。

## 验收覆盖矩阵

| AC | kind | 关联任务 |
|---|---|---|
| AC-1 | static | T-1 |
| AC-2 | static | T-2 |
| AC-3 | static | T-3 |
| AC-4 | static | T-4 |
| AC-5 | static | T-5 |
| AC-6 | static | T-6 |
| AC-7 | static | T-7 |
| AC-8 | **behavioral** | T-8 |

每条 AC 至少 1 个非 process_tasks 任务覆盖。**behavioral AC：AC-8**（T-8 真跑 self_check 全链路）。
