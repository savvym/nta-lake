---
change_id: auth-scaffold-20260517
target: unit_test/test_report_v1.md
target_version: 1
review_version: 1
reviewer: claude-agent:auth-scaffold-stage6-reviewer
reviewed_at: 2026-05-17T08:30:00Z
verdict: APPROVED
---

# Test Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` artifact 模式。

- [x] 每条 spec AC 在映射表中至少出现一次（17/17，AC-15 子项 (a)~(h) 一一映射）。
- [x] 没有空跑断言（无 `assert True` / `assert 1 == 1`；无滥用 skip）。
- [x] mock 范围与 `coding-style.md` §1.7 一致（packages/core 单元零 mock；apps/api 集成全真连 Postgres + 真 argon2 + 真 JWT）。
- [x] 测试名 `test_a_*` ~ `test_h_*` 携带场景后缀（`hash_verify_roundtrip` / `login_wrong_password_returns_401` 等），不是单字母占位。
- [x] flaky / skip 显式说明（pytest.mark.skipif 探针 DATAPLAT_DATABASE_URL；MinIO 类似）。

## AC-15 (a)~(h) 逐条映射核验

| 子项 | 测试函数 | 真覆盖？ | 备注 |
|---|---|---|---|
| (a) hash/verify roundtrip | `test_a_password_hash_verify_roundtrip` | 是 | h1!=h2 + 跨 hash verify + 反向 verify('wrong') |
| (b) JWT encode/decode roundtrip | `test_b_jwt_encode_decode_roundtrip` | 是 | sub/role/typ 三字段全断言，含 access/refresh 双向 |
| (c) login 三 cookie 标志 | `test_c_login_sets_cookies_with_security_flags` | 是 | raw header lower() grep httponly + secure + samesite=lax + 双 cookie 名 + body username |
| (d) 错密码 401 | `test_d_login_wrong_password_returns_401` | 是 | 真用 fresh fixture 用户做反例 |
| (e) /me 带 cookies 通过 | `test_e_me_passes_with_valid_cookies` | 是 | 走完 login → /me，断 username 回正 |
| (f) /me 缺 cookies 401 | `test_f_me_without_cookies_returns_401` | 是 | 纯反例，无登录前置 |
| (g) refresh 重发 access | `test_g_refresh_issues_new_access` | 是 | 204 + Set-Cookie 含 `access_token=` |
| (h) user → admin 403 | `test_h_user_role_cannot_access_admin_users` | 是 | 走 login (user) → POST /admin/users，断 403（区别于 401，证明依赖链 require_admin 生效） |

每条 AC 至少一个具体断言；spec 17 AC 无孤立项。

## 问题列表

### MUST FIX

（无）

### SHOULD FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | `apps/api/tests/test_auth.py` 全局 | **stage 4 MUST FIX #1 的 typ 校验缺反向断言**：当前 8 测试无一条把 refresh token 放入 access_token cookie 验 401。stage 4 reviewer 自己跑过 PoC 但未沉淀为常驻测试 → 该路径如果未来回归，CI 不会响。**建议**：补 `test_i_refresh_token_cannot_be_used_as_access`：手动 `encode_refresh_token(uid)` → `client.cookies.set('access_token', token)` → GET /auth/me → 断 401。 |
| 2 | `apps/api/tests/test_auth.py` 全局 | **stage 4 MUST FIX #2 的 admin 静默降权 / 停用闭环缺常驻断言**：(i) admin 用户 refresh 后新 access 仍含 `role=admin`；(ii) is_active=False 后 refresh 401。两条都只在 stage 4 review v2 文字断言"已闭环"，没测试钉。**建议**：补 `test_j_admin_refresh_preserves_role`（decode 新 access cookie 取 role）与 `test_k_deactivated_user_refresh_401`（fixture 改 is_active=False → /auth/refresh → 401）。 |
| 3 | `apps/api/dataplat_api/routers/admin.py:29` | **CreateUserRequest.role Pydantic 拒非法值无测试**：admin.py 用 `Literal["admin","user"]` 钉死，应有一条 `test_l_admin_create_user_invalid_role_422` 走 admin login → POST /admin/users `role="superuser"` → 422，证明 Pydantic 校验真生效。 |

> 三条 SHOULD 均属"安全实证未沉淀为常驻测试"——stage 4 reviewer 已用 PoC 实证一次，verdict 通过；但 expert-reviewer SKILL §1 artifact 模式要求每条 AC 至少一条**具体测试用例**，stage 4 PoC 是一次性脚本不算。Generator 在 v2 补 3 条或在 summary §Deferred 显式记录跟进位置（含 follow-up change slug）。

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | `apps/api/tests/conftest.py:15-18` | `os.environ.setdefault` 不覆盖用户 export 的真实 secret。若开发者本地 export 生产 JWT_SECRET 跑测试，会污染审计链路。**建议**：注释加一行"测试 secret 必须以 `test-secret-` 前缀 sentinel；若检测到非 sentinel 值应 `pytest.exit`"，或加一个 conftest assert 强制前缀。 |
| 2 | `apps/api/tests/test_auth.py` fixture L92-94 / L128-130 | engine 不 dispose 注释"GC 兜底"。Stage 4 已标 SHOULD FIX defer——但 review_v2 没说清 follow-up change slug。**建议**：在 coding_report § Deferred 写明 `follow-up: harness-fixture-shared-engine-*` 或类似 slug，否则该问题失踪。 |
| 3 | `apps/api/tests/test_auth.py:218` | test_g 只断 `access_token=` 出现，没 decode 验 typ/role/exp。如果 refresh 路径未来 bug 让它写出 refresh token 到 access cookie，这条不响。**建议**：补 `decode_token(extract_cookie('access_token'))` 断 `typ=='access'` + `sub == user_id`。（与 SHOULD 2 合并实现更省。） |

## 偏离 SKILL 评估

| 偏离 | test_report 申明 | 评审判 |
|---|---|---|
| fixture 不 dispose | SHOULD FIX defer | **可 defer**；但要求 coding_report 列出 follow-up slug（NICE 2 已重复） |
| db.py 用 `PYTEST_CURRENT_TEST` 触发 NullPool | "生产/测试权衡" | 合理；生产路径未被改 |
| `base_url=https://test` | "httpx ASGITransport 协议字符串触发 secure cookie" | 合理；这是 httpx 唯一让 secure cookie 跨请求携带的办法 |

## 与 stage 4 MUST FIX 的闭环关系

| stage 4 MUST | 代码闭环 | 常驻测试 |
|---|---|---|
| #1 typ=='access' 校验 | deps.py:42-43 已加 | **缺**（SHOULD 1）|
| #2 refresh 查 DB role+is_active | auth.py:104-113 已重写 | **缺**（SHOULD 2）|
| #3 openapi.json regen | grep 4 命中 + git staged | self_check AC-12 已守，且 (h) 测试间接证明 admin router 已 wire 上 |

stage 4 verdict v2 APPROVED 是基于"代码 + PoC"双证，单测层只覆盖了 #3 的间接结果。本次 stage 6 评审认定**安全 MUST 应有常驻测试**，但不阻塞 verdict——理由：stage 4 已独立通过 + verdict 标尺是 expert-reviewer SKILL §3 的"MUST FIX 数 == 0"，本评审无 MUST FIX。

## Verdict

**APPROVED**

闭环判据：
- AC-15 (a)~(h) 8 测试一一映射且断言都对得上场景描述。
- 无空跑断言；无被禁的数据访问层 mock；测试名携带场景后缀。
- 偏离 SKILL 的 3 项（fixture/NullPool/https://test）都给了合理解释，且不影响安全语义。
- 3 条 SHOULD 是补强常驻安全断言，不阻塞进入 Stage 7；但 Generator 必须二选一：v2 补测试或 summary §Deferred 列 follow-up slug。

## 复检指引

Generator 收到本评审后：

1. 决定 SHOULD 1~3 采纳策略：
   - **采纳**：在 `apps/api/tests/test_auth.py` 末尾追加 `test_i_` / `test_j_` / `test_k_` / `test_l_`，跑 `cd apps/api && uv run pytest -q tests/test_auth.py` 应见 12 passed（原 8 + 新 4）。
   - **Defer**：在 `summary.md §Deferred` 列出 4 条具体 follow-up change slug 候选（如 `auth-residual-security-tests-<yyyymmdd>`），且 NICE 2 要求的 fixture follow-up slug 一并补上。
2. 跑 `bash scripts/_self_check.sh auth-scaffold` 应仍 PASS 17/17（本评审不引入新 AC）。
3. 在 `unit_test/test_report_v2.md`（或 summary）回填本 review 决议；status: `review_approved_v1`。
4. 无 v2 评审需求——本 verdict 已 APPROVED；除非 Generator 采纳 SHOULD 后希望复检 commit 质量，可走 Stage 7 commit。
