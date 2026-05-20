---
name: deploy-verify
description: 部署完成后做行为验证，留下可复核的证据
applicable_stage: 阶段 9（部署验证）
inputs:
  - request_analysis/spec.md
  - 部署目标环境信息（dev/staging/prod）
outputs:
  - deployment/deploy_verify_v{N}.md
---

# deploy-verify Skill

> ⚠ **DEPRECATED (2026-05-20, v2 pivot)**：v2 三阶段流程下，本 skill 不再单独加载。其职责并入：
> - 设计评审 / PR 验收 → `.harness/skills/expert-reviewer/SKILL.md`（两种模式）
> - 编码 + 测试 + 端到端 → Phase 2 sonnet implementer 端到端做（见 `.harness/rules/development-process.md` § Phase 2）
> 本文件保留只为历史 change 引用。新 change 请按 v2 流程走。

## 适用范围

变更涉及以下任一部署面：

- `apps/api` 容器
- `apps/web` 静态产物
- `worker` 容器
- 任意 `plugins/<name>` 镜像
- 数据库 schema 迁移

纯文档 / 纯 harness 变更可跳过本阶段，直接到阶段 10。

## 进入条件

- 阶段 8 CI verdict = SUCCESS。
- 目标环境部署已完成（自动或手动均可），版本号 / 镜像 tag 明确。
- 数据库迁移（如有）已应用。

## 输入

1. spec.md 验收标准。
2. 部署版本信息：镜像 tag、commit SHA、运行环境（dev/staging/prod）。
3. 必要的访问凭证（按团队 SSO/VPN 流程）。

## 步骤

### 1. 列验证矩阵

把验收标准 + "部署后必查项"合并成验证矩阵：

| ID | 验收项 / 必查项 | 验证方式 | 期望结果 | 证据形式 |
|---|---|---|---|---|
| AC-1 | 创建 bronze repo 返回 201 | API curl | 201 + repo_id | 请求/响应粘贴 |
| DEP-1 | 服务健康检查 200 | curl /healthz | 200 OK | 响应粘贴 |
| DEP-2 | DB 迁移已落地 | alembic current | 头 == 最新 revision id | 命令输出 |
| DEP-3 | worker 在线 | rq info / k8s logs | active workers > 0 | 输出粘贴 |

**部署后必查项**（每次都要）：

- 服务 healthz / readyz 通过。
- 关键路径 smoke 测试。
- 关联前端能正常 SSR 或加载（白屏检测）。
- 数据库迁移 head 匹配代码期望 revision。
- 关键 metrics 与日志没有出现新增 ERROR / 5xx 异常。

### 2. 逐条执行

每条都要有**可粘贴的证据**：

- API：`curl -i ...` 完整请求/响应。
- DB：`alembic current` 输出 + 关键表 `\d` 截图或 SELECT 结果。
- 前端：浏览器实际操作（如能），截图 + DevTools network 摘录；若无人操作环境，至少跑 Playwright smoke。
- worker / plugin：相关日志 grep 与作业完成事件。

不接受"应该没问题"、"日志看着正常"。

### 3. 失败处理

任何一条验证失败：

- **立即在 `summary.md` 标记**：阶段 9 verdict=FAIL，附失败 ID 与位置。
- 评估是否需要回滚：参考 design.md 与 ADR 的回滚约定。
- 写明回退到哪一阶段（通常是 3 编码 / 5 单测 / 8 CI 之一）。

不允许"线上有问题先看着"——回滚或修复必须在本阶段决断。

### 4. 写 deploy_verify 报告

按 `deployment/deploy_verify_v{N}.md` 模板填：

```yaml
---
env: dev | staging | prod
deployed_at: <iso8601>
image_tag: <tag>
commit_sha: <sha>
verifier: <name>
verdict: PASS | FAIL
---
```

接验证矩阵 + 每条的证据。

接"风险评估"：本次部署是否引入 schema 不兼容、是否有不可回滚操作（如数据删除）、是否需要 follow-up。

## 产出

- `deployment/deploy_verify_v{N}.md`。
- `summary.md` 同步刷新（含证据文件路径）。

## 质量门禁

```text
deploy_verify_v{latest}.md 存在
验证矩阵每行都有证据字段非空
verdict ∈ {PASS, FAIL}
verdict == PASS 时：失败行数 == 0
涉及迁移的变更：alembic current 输出存在且等于代码期望 revision
```

## 失败回退

- 单条 smoke 失败但代码 bug 明确 → 回阶段 3。
- 数据库迁移失败 → 回滚迁移 + 回阶段 3（同时考虑写 ADR 补 lessons）。
- 环境基础设施失败（非本次变更引入） → 暂停本变更、通知运维、记入 summary。

## 反模式

- 把 "日志看了一眼没问题" 当 PASS。
- 只测 happy path，不测部署相关项（迁移、配置、依赖服务连接）。
- 验证矩阵和 spec 验收标准脱节。
- 部署到 prod 才发现某条验证步骤需要的访问权限没准备，留下"事后补"。
