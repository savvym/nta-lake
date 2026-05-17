---
change_id: auth-scaffold-20260517
target: spec.md
target_version: 2
review_version: 2
reviewer: claude-agent:auth-scaffold-stage2-reviewer
reviewed_at: 2026-05-17T05:50:00Z
verdict: APPROVED
---

# Spec Review v2

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1。

- [x] 背景 / 问题陈述 / 范围 / 非范围 / 风险 / 待澄清 全保留并自洽。
- [x] v1 三条 MUST 关闭判据全部命中（见下"v1 MUST 关闭核对"）。
- [x] 抽查命令 syntax + 空仓库实跑无静默吞错（见下"v2 抽查实跑"）。

## v1 MUST 关闭核对

| v1 MUST | 关闭位置 | 验证 |
|---|---|---|
| **MUST 1**（AC-10/12 router prefix 钉死） | spec.md L43 AC-10 描述：「**Prefix 钉死**：必须用 `router = APIRouter(prefix="/auth")` + main 用 `app.include_router(router)` **不再传 prefix**——这是让 AC-10 `router.routes` 与 AC-12 `app.openapi()['paths']` 同时含 `/auth/login` 的唯一组合。」 | `grep -nE "APIRouter\(prefix=\"/auth\"\)|不再传 prefix"` 命中 L43 |
| **MUST 2**（JWT secret lazy 语义） | spec.md L39 AC-6 描述：「**Secret 读取明确**：`encode_*` / `decode_*` 函数体内**每次**调用 `os.environ.get("DATAPLAT_JWT_SECRET")` 读取，**不得 cache 在模块级常量**（避免 conftest `monkeypatch.setenv` 失效）；若读到 None / 空串 raise `TokenError`（不在 import time）。」 | `grep -nE "每次.*os.environ|不得 cache 在模块级常量"` 命中 L39 |
| **MUST 3**（AC-15 SKIP 通道） | spec.md L78 期望列：「**PG up → exit 0；PG down → 本命令 exit 1，AC-17 内由 `_self_check.sh` SKIP 通道转 exit 0**（spec MUST FIX-3 澄清）」 | `grep -nE "PG up.*exit 0.*PG down"` 命中 L78 |

另：**AC-15 (h) 普通 user 403** 已写进 L48（spec MUST FIX-3 + tasks MUST 3 联动），AC-15 集成测试数 ≥6 → ≥7，命令尾 `-ge 7` 同步。

## v2 抽查实跑（三层校验，参考 [[project-followup-harness-lint]]）

我在 /tmp 空仓库 + 本地 Python 3.13 + `uv run --with fastapi/argon2-cffi` 重抽 AC-6/10/12/15：

- **层 1 syntax**：v2_ac6/10/12/15 bash -n 全 PASS。
- **层 2 空仓库实跑**：4/4 正确 exit ≠ 0（产物缺）。
- **层 3 语义**：
  - AC-6 命令前置 `DATAPLAT_JWT_SECRET=test-secret-32-bytes-long-xxxxx`（31 字节）——SHOULD 1 仍未升 32+，但 AC-15 用的 secret 改为 `test-secret-not-prod-x32-bytes-xxxxx`（**36 字节**，OK）。AC-6 是隔离 unit-style，不阻塞。
  - 模拟 conftest.py 顶层 `os.environ.setdefault(...)` + fn-scope `os.environ.get(...)` 的组合实测正确（值能透过去）。
  - AC-10/12 prefix 钉死与 fastapi 实测组合一致：`APIRouter(prefix="/auth")` + `include_router(r)` 不再传 prefix → router.routes 与 openapi paths 同时含 `/auth/login`。

## 残留问题（不阻塞 APPROVED）

### SHOULD（建议在 Stage 3 编码时顺手吸收）

- **SHOULD（旧 v1 SHOULD 1）**：spec L69 AC-6 测试 secret `test-secret-32-bytes-long-xxxxx` 实测 31 字节 < 32。AC-15 已是 36 字节 OK。AC-6 可改 `test-secret-32-bytes-long-xxxxxx`（加 1 位）。
- **SHOULD（v2 新增）**：spec L78 表格描述列首句仍写「apps/api auth 集成 **≥ 6** + 全 PASS（含...403）」，但 L48 in-scope 与命令尾 `-ge 7` 都是 ≥ 7。建议描述列也改 ≥ 7 文字一致。
- **SHOULD（旧 v1 SHOULD 2/3/4/6）**：cookies `secure` env-driven / argon2 测试参数策略 / AC-8 行为级签名断言 / AC-14 pytest+grep+awk 链注释——均未在 v2 关闭，但都明确划为非 MUST，可在编码阶段处理或 follow-up。

### NICE

- spec.md frontmatter `version: 1` / `authored_at: 2026-05-17T05:10:00Z` 未更新到 v2（建议改 version: 2 + updated_at）。这是 harness frontmatter 卫生，不影响内容门禁。
- §引用未加 cas-storage `fc73193`、OpenAPI tags 未规定——保留 NICE 级。

## Verdict

**APPROVED**

判据：v1 三条 MUST（router prefix 钉死 / JWT secret lazy 语义 / AC-15 SKIP 通道）全部关闭；spec MUST FIX-3 顺带把 AC-15 (h) 普通用户 403 落进 in-scope。SHOULD/NICE 残留不阻塞下一阶段。

## 复检指引（Stage 3 编码前 / Stage 4 评审时使用）

```bash
# 1. v2 关键约束的"必现 grep"——若 Generator 实现偏离，spec/tasks 与代码会同步触红
grep -nE "APIRouter\(prefix=\"/auth\"\)" .harness/changes/auth-scaffold-20260517/request_analysis/spec.md
grep -nE "每次.*os.environ.get" .harness/changes/auth-scaffold-20260517/request_analysis/spec.md
grep -nE "(h) 普通 user|≥ 7 集成" .harness/changes/auth-scaffold-20260517/request_analysis/spec.md

# 2. Stage 3 实现完成后，三层校验抽样（防回归）
mkdir -p /tmp/auth-scaffold-stage4 && cd /tmp/auth-scaffold-stage4
# 把 AC-6/AC-10/AC-12 命令拷过来 bash -n + 在真实仓库下实跑应当 exit 0
```
