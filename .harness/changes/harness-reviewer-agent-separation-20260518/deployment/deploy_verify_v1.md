---
change_id: harness-reviewer-agent-separation-20260518
version: 1
env: dev
deployed_at: 2026-05-18T14:55:00Z
commit_sha: (will-be-filled-at-commit)
verifier: claude-agent:harness-reviewer-agent-separation-stage9-verifier-v1
verdict: PASS
---

# Deploy Verification v1

> meta-change（改 harness 文档 + shell；不动 dataplat 代码）。**无 deploy surface**——本变更生效不需重启 API/worker；只需 `git pull` + 下次 self_check 自然带入。

## 验证矩阵

| ID | 验收项 | 验证方式 | 期望 | 实际 |
|---|---|---|---|---|
| AC-10 | reviewer-lint 跑通 | `bash scripts/_self_check.sh reviewer-lint` | PASS=1 | PASS=1 |
| AC-12 | 全仓 self_check PASS=226 | `bash scripts/_self_check.sh` | PASS: 226 | PASS: 226 |
| DEP-1 | reviewer-agent.md 可被未来 Owner agent 读 | `test -f .harness/agents/reviewer-agent.md` | 存在 | 存在 |
| DEP-2 | application-owner.md §7.5 spawn 模板可粘贴使用 | grep + 模板格式校验 | 模板含 Agent + subagent_type + general-purpose | True |
| DEP-3 | expert-reviewer SKILL § reviewer 字段规约可被未来 reviewer 子 agent 读 | grep | 含白名单 + 黑名单 + 守门说明 | True |
| DEP-4 | dogfood 8 review 文件全部合规 | grep `^reviewer:` 头部 | 全 claude-agent: | True |
| DEP-5 | 历史回溯 30 行无残留 application-owner-agent | `! grep -rE "^reviewer:[[:space:]]+application-owner-agent"` | 0 命中 | 0 |

## 部署说明

- **无重启**：本变更只改 `.harness/` 文档 + `scripts/_self_check.sh`；不涉及 API/worker/web 进程
- **生效路径**：下次 self_check 跑时自动用新 reviewer-lint；下次新 change 进 stage 2 时 Owner 必须按 §7.5 spawn 子 agent；违者 self_check FAIL

## 风险评估

- [ ] schema 不兼容？**否**（无 DB / 无 API）
- [ ] 不可回滚？**否**（git revert 即可）
- [ ] follow-up？**是**——见 summary §Deferred

## Verdict

PASS。
