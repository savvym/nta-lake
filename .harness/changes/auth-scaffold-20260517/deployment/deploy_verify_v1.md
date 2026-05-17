---
change_id: <feature-slug>-<yyyymmdd>
version: 1
env: dev           # dev | staging | prod
deployed_at: <YYYY-MM-DDTHH:MM:SSZ>
image_tag: <tag>
commit_sha: <sha>
verifier: <name>
verdict: PASS      # PASS | FAIL
---

# Deploy Verification v1

> 如本变更**不涉及部署面**（纯文档 / 纯 harness），删除本目录并在 `summary.md` 阶段 9 行写 "skipped: no deploy surface"。

## 验证矩阵

| ID | 验收项 / 必查项 | 验证方式 | 期望 | 实际 | 证据 |
|---|---|---|---|---|---|
| AC-1 | _e.g. POST /repos 返回 201_ | `curl -i ...` | 201 + repo_id | 201 | [evidence](#ac-1) |
| AC-2 | _e.g. 上传同文件去重_ | 集成 smoke | blob_count == 1 | 1 | [evidence](#ac-2) |
| DEP-1 | 服务 healthz 200 | `curl /healthz` | 200 OK | 200 | [evidence](#dep-1) |
| DEP-2 | DB 迁移落地 | `alembic current` | == head | head | [evidence](#dep-2) |
| DEP-3 | worker 在线 | `rq info` | active > 0 | 2 | [evidence](#dep-3) |
| DEP-4 | 前端可加载 | 浏览器 / Playwright smoke | 主页面无 5xx | OK | [evidence](#dep-4) |
| DEP-5 | metrics / 日志无新 ERROR | grafana / `kubectl logs` | 0 新 ERROR | OK | [evidence](#dep-5) |

## 证据

### AC-1

```text
$ curl -i -X POST https://dev.dataplat.internal/api/repos \
    -H 'Cookie: access=...' \
    -d '{"owner":"my","name":"foo","layer":"bronze","subtype":"pdf-collection"}'
HTTP/1.1 201 Created
...
{"repo_id":"...", ...}
```

### AC-2

```text
(粘贴集成 smoke 脚本输出)
```

### DEP-1

```text
$ curl -i https://dev.dataplat.internal/healthz
HTTP/1.1 200 OK
```

### DEP-2

```text
$ alembic current
0042_xxx (head)
```

### DEP-3 / DEP-4 / DEP-5

```text
...
```

## 风险评估

- [ ] 涉及 schema 不兼容？_是 / 否_。如是：附迁移回滚脚本测试结果。
- [ ] 涉及不可回滚操作（数据删除、外部副作用）？_是 / 否_。
- [ ] 需要 follow-up？_是 / 否_。如是：列 follow-up change / task id。

## Verdict

PASS / FAIL

## 处理动作

- PASS → 进入阶段 10 用户确认。
- FAIL → 决断：回滚 or 修复。
  - 选择回滚 → 附回滚命令 / 镜像 tag。
  - 选择修复 → 回退到对应阶段（3 / 5 / 8）。
- 在 `summary.md` 同步更新。
