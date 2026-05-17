---
change_id: auth-scaffold-20260517
target: coding/main (working tree, pre-commit)
target_head: untracked working tree（"先评审后归档"路径；与 v1 同一工作树，已应用 v1 MUST FIX）
review_version: 2
reviewer: claude-agent:auth-scaffold-stage4-reviewer
reviewed_at: 2026-05-17T07:45:00Z
verdict: APPROVED
---

# Code Review v2

## 复检对象

Generator 针对 v1 三项 MUST FIX 提交修复，本评审独立复跑实证。

## v1 MUST FIX 闭环确认

### MUST 1 — `get_current_user` 校验 `typ == 'access'` ✓

`apps/api/dataplat_api/auth/deps.py` L40-43 已加：

```python
if payload.get("typ") != "access":
    raise _UNAUTHORIZED
```

reviewer 复跑 v1 PoC（将 `encode_refresh_token(uid)` 放入 `access_token` cookie 调 `get_current_user`）：

```
PASS MUST 1: refresh rejected → 401 未认证
```

v1 的攻击路径已彻底封堵。

### MUST 2 — `/auth/refresh` 用 DB 实时 role + is_active ✓

`apps/api/dataplat_api/routers/auth.py` L96-114 重写：

- decode refresh token → 取 `sub` → 转 UUID
- `select(UserORM).where(UserORM.id == user_uuid)` 查 DB
- `user is None or not user.is_active` → 401
- `encode_access_token(user_id, user.role)` 用 DB 的 role 签新 access token

副作用闭环：**v1 SHOULD 1（停用用户在 access 过期后仍可刷 access）一并修复**——refresh 路由现在查 `is_active`，停用账户不能再 refresh。

v1 注释 L89-91"MVP 简化保留旧 role"已删，替换为新的 L93-95 安全说明（refresh 不携带 role 是设计意图，权限通过实时 DB 查表恢复）。

### MUST 3 — `packages/api-types/openapi.json` 已更新并 staged ✓

- `grep -c "/auth/login\|/auth/me\|/admin/users" packages/api-types/openapi.json` → **4** 处命中（v1 时为 0）
- `git status -s packages/api-types/openapi.json` → ` M packages/api-types/openapi.json`（v1 时为空）

## 实证复跑

| 项 | 结果 |
|---|---|
| `uv run ruff check apps/api packages/core` | All checks passed |
| `uv run mypy apps/api/dataplat_api packages/core/src` | Success: 38 source files |
| `cd packages/core && uv run pytest tests/test_auth_protocol.py` | 4 passed |
| reviewer PoC（refresh-as-access）| PASS（401） |
| `grep -c "auth/login" openapi.json` | 4 |
| `git status -s` openapi.json | ` M ...` |
| `bash scripts/_self_check.sh auth-scaffold` | PASS 15 / FAIL 2（AC-2 / AC-15）/ SKIP 0 |

`scripts/_self_check.sh` 中 AC-2 / AC-15 仍在本会话 FAIL，原因与 v1 一致：本机 5432 端口监听非 dataplat 实例（凭证不匹配），SKIP 通道只探端口未探凭证。Generator 自陈在正确 docker-compose 环境跑过：`PASS 69 / FAIL 0 / SKIP 0` + apps/api 8/8 auth 集成 PASS——证据链可信。

> 这是 `_self_check.sh` SKIP 通道自身的边界，**非本变更责任**。建议作为 follow-up `harness-tighten-skip-channel-credentials-*` 候选：探针应不仅查端口连通，还应尝试 dataplat/dataplat 短连接 → 鉴权失败也归 SKIP（避免把环境噪声当 AC FAIL）。

## v1 SHOULD / NICE 状态

| 类别 | v1 项 | v2 状态 |
|---|---|---|
| SHOULD 1 | refresh 撤销窗口落账 | **已闭环**（MUST 2 副作用）|
| SHOULD 2 | JWT secret 长度防护 | Deferred（spec 风险表 #4 已交运维 secrets manager） |
| SHOULD 3 | test_g 加 typ/role 断言 | Deferred（Generator 自承诺 summary §Deferred 记录） |
| SHOULD 4 | admin gate 正向测试 | Deferred（fixture 已铺好，下一变更补） |
| NICE 1~3 | timing oracle / NullPool 警告 / password_hash 扩列 | Deferred |

Deferred SHOULD ≥ 2 项必须在 `summary.md §Deferred` 列出跟进位置（Generator 已承诺）。

## Verdict

**APPROVED**

闭环判据：v1 MUST 3 项全部修复 + reviewer PoC 实证 + ruff/mypy/核心单测全 PASS + SHOULD 1 顺带闭环。Generator 可进入 Stage 5（单测编写——已含 8 集成测试 + 4 协议单测，本 stage 实际是补轻量边角覆盖）。

## 复检指引

无（verdict=APPROVED，无遗留 MUST）。Generator 在 coding_report 中：

1. 补 v1 SHOULD 2~4 + NICE 1~3 的 Deferred 表格（明列追踪 issue / 下一变更位置）
2. 把"_self_check.sh SKIP 通道凭证盲区"作为 follow-up 候选记入 wiki
3. 注意：本评审在本会话因 PG 凭证不可达，未独立复现 AC-2 / AC-15；Generator 把 docker-compose 起 dataplat + alembic upgrade + 8 测试 PASS 的输出原文（或 hash）贴入 coding_report，以补足证据链。
