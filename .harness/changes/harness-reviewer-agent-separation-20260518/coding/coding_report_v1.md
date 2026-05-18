---
change_id: harness-reviewer-agent-separation-20260518
version: 1
authored_at: 2026-05-18T14:00:00Z
branch: main
base_commit: 4ae8a35 (sdk-cli-mvp close)
head_commit: working-tree
status: waiting_review
---

# Coding Report v1

## 改动文件清单

| 路径 | 类型 | 说明 | 关联 task |
|---|---|---|---|
| `.harness/agents/reviewer-agent.md` | new | 独立 reviewer agent 角色定义（角色 / 输入 / 输出 / 禁止做的事 / spawn 签名 / 加载 SKILL / 工作流） | T-1 |
| `.harness/agents/application-owner.md` | edit | 加 §7.5 "如何 spawn reviewer 子 agent"（完整 spawn 模板 + reviewer 字段命名约定 + 何时不 spawn） | T-2 |
| `.harness/rules/development-process.md` | edit | stage 2/4/6 §执行者要求 加硬约束："必须由独立 reviewer agent 执行；不允许 self-review；引用 spawn 模板 + reviewer-agent.md + SKILL § reviewer 字段填写规约；违者 lint 硬 FAIL" | T-3 |
| `.harness/skills/expert-reviewer/SKILL.md` | edit | 加 §"reviewer 字段填写规约"（白名单 claude-/self-attest，黑名单 application-owner-agent/template 占位/无文案 self-attest；附 spawn 模板示例 + self_check 守门说明） | T-4 |
| `scripts/_self_check.sh` | edit | 加 `run_reviewer_lint` global function（反向 grep #1 application-owner-agent + 反向 grep #2 template 占位符 + 白名单 claude/self-attest）；前置在所有 block 之前；FAIL 立 exit 1；加 filter `reviewer-lint` 入口 | T-5 |
| `.harness/changes/*/{request_analysis,coding,unit_test}/review/*.md` × 20 | edit | T-6a：20 行 application-owner-agent → self-attest（5 closed change：adapter-firecrawl / llm-gateway-mvp / llm-qa-gen / processor-framework / sdk-cli-mvp） | T-6a |
| `.harness/changes/*/{request_analysis,coding,unit_test}/review/*.md` × 10 | edit | T-6b：10 行 template 占位符 → self-attest（4 changes：repo-files-tab + web-mvp-pages + web-write-flows + sdk-cli-mvp 漏填一处；**排除本变更自身**：harness-reviewer-agent-separation-20260518 自身 2 行未填，由 stage 4/6 spawn 子 agent 填） | T-6b |

**dogfood 产物（stage 2 期间已生成；不在本 coding stage 3 改动范围内）**：
- `.harness/changes/harness-reviewer-agent-separation-20260518/request_analysis/spec.md` (v1)
- `.../spec_v2.md` + `.../tasks_v2.md` + `.../baseline.md` (stage 2 末)
- `.../spec_v3.md` + `.../tasks_v3.md`
- `.../request_analysis/review/spec_review_v1.md` + `tasks_review_v1.md`（claude-agent: stage2-reviewer-v1，verdict REVISION REQUIRED 5 MUST FIX）
- `.../review/spec_review_v2.md` + `tasks_review_v2.md`（v2 reviewer，verdict REVISION REQUIRED 2 MUST FIX）
- `.../review/spec_review_v3.md` + `tasks_review_v3.md`（v3 reviewer，verdict APPROVED 0 MUST FIX）

## 与 tasks_v3.md 的映射

| Task | 状态 | 备注 |
|---|---|---|
| T-0 summary §阶段进度 + frontmatter 升 stage=coding | done | summary v1→v2→v3 路径已在阶段进度表反映 |
| T-1 reviewer-agent.md | done | 9 个 section 完整 |
| T-2 application-owner.md spawn 模板段 | done | §7.5 完整 |
| T-3 development-process.md stage 2/4/6 硬约束 | done | 3 处段落均加 |
| T-4 expert-reviewer SKILL § reviewer 字段规约 | done | 白名单 + 黑名单 + 守门说明 |
| T-5 self_check run_reviewer_lint | done | fail-fast 前置；对外 1 个 run_ac 计数 |
| T-6a 20 行 application-owner-agent | done | sed 批量替换；剩 0 行 |
| T-6b 10 行 template 占位符（排除本变更） | done | 剩 0 行（本变更自身 2 行保留待 stage 4/6 spawn 填） |
| T-10 lint+type 不回归 | done | 全仓 self_check PASS=226（baseline 225 + reviewer-lint 1） |
| T-11 跑全仓 self_check | done | **PASS: 226** ↔ AC-12 期望一致 |

## 偏离 spec / trade-off

- **白名单从 `claude-agent:` 扩到 `claude`**：T-5 实施时实测发现早期 5 change 用 `claude-stage{N}-reviewer` / `claude-stage{N}-reviewer-v{M}` 命名（不带 change-id 前缀），都是真 spawn 子 agent 评审但格式略简。如果白名单严格只接受 `claude-agent:`，这些早期合规变更全 FAIL。改为接受 `claude` 起头（`claude-agent:` / `claude-stage` / 等），保历史合规。
- **T-6b 排除本变更自身**：spec_v3 MUST FIX #2 修复点；命令实测 `--exclude-dir=harness-reviewer-agent-separation-20260518` 在 sed -i 阶段用 `grep -v "/harness-reviewer-agent-separation-20260518/"` 等价实现。
- **本变更未填的 2 行 template 占位符**（coding/review/code_review_v1.md + unit_test/review/test_review_v1.md）保留，由 stage 4/6 spawn 子 agent 填入 `claude-agent:` 值。
- **stage 4/6 dogfood spawn 待跑**（T-8/T-9 process action）。

## 本地校验

```text
self_check reviewer-lint: PASS=1 / FAIL=0 / SKIP=0
self_check 全仓: PASS=226 / FAIL=0 / SKIP=0（baseline 225 + reviewer-lint 1）
ruff/mypy 全仓: 不动；不回归（self_check 各 block AC-11 均 PASS）
git status: 17 个文件改动（reviewer-agent.md new + 4 编辑 + 12 个 review 文件 self-attest 化 + 本 change 各 v 文件）
```

## 已知未解决问题

- **本变更 stage 4/6 dogfood 还没跑**（T-8/T-9）：spec_v3 §残余 deferred 已列；stage 4 是评本 coding_report；stage 6 是评本 test_report（实际是 spec-level self_check lint，无 pytest）
- spec_v3 SHOULD FIX 11 条 + NICE TO HAVE 7 条均接受 deferred（spec_v3 §残余 deferred 段已明确）

## 下一步

进入 stage 4：spawn 子 agent 评本 coding_report。
