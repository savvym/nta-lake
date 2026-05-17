---
change_id: auth-scaffold-20260517
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-agent:auth-scaffold-stage2-reviewer
reviewed_at: 2026-05-17T05:30:00Z
verdict: REVISION REQUIRED
---

# Spec Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1。

- [x] 背景写明了为什么现在做（前 4 个变更 + repo-api-mvp 前置）。
- [x] 问题陈述对外部读者可理解（7 条 numbered gap）。
- [x] 范围 / 非范围都有（5 条非范围明示）。
- [x] 大部分验收标准可机械化（17/17）；但**多条命令存在永真 / 二义性陷阱**——见 MUST 1/2/3。
- [x] 风险表 7 条且每条有缓解。
- [x] 没把 design.md §11.6 当新提案重复。
- [x] 待澄清问题 4 条全 [x] 关闭。

## 抽查实跑结论（三层校验依据：项目记忆 [[project-followup-harness-lint]]）

我在 /tmp 空仓库 + 本地 Python 3.13 + `uv run --with fastapi/argon2-cffi` 抽查了 AC-1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17（10 条 bash -n + 重点 5 条产物行为模拟）：

- **层 1 syntax**：17/17 PASS。
- **层 2 空仓库实跑**：所有"产物存在"类 AC 都正确 exit ≠ 0（不会因 typo 默默返 0）。
- **层 3 关键语义验证**：
  - AC-3 `issubclass + getattr(_, '_is_runtime_protocol', False) is True` 双断言在 Python 3.13 上**确实抓得到** runtime_checkable 缺失（实测属性名存在）——避开了 cas-storage 的 hasattr 永真陷阱。
  - AC-10 / AC-12 经 fastapi 实例化验证：**router prefix 归属**决定两条 AC 同时 PASS 的唯一组合（见 MUST 1）。
  - AC-7 内联 `c=[c for c in r.raw_headers ...]; raw=b'\n'.join(c[1] for c in c)`——同名变量遮蔽但语义正确，PASS——可读性差。

## 分级问题列表

### MUST FIX

**MUST 1（AC-10 / AC-12，spec L73-75 / L74-75）：router prefix 归属未钉死，AC-10 与 AC-12 互斥风险**

- **位置**：spec.md AC-10 / AC-12 / 间接波及 tasks.md T-13 / T-15。
- **问题**：AC-10 检查 `router.routes` path 必含 `/auth/login`；AC-12 检查 OpenAPI `paths` 含 `/auth/login`。实测 FastAPI 行为：
  - Case A（`APIRouter(prefix='/auth')` + main `include_router(r)`）：router.routes 与 openapi 都返 `/auth/login` → 两 AC 同 PASS。
  - Case B（`APIRouter()` + main `include_router(r, prefix='/auth')`）：router.routes 返 `/login` → **AC-10 fail**。
  - Case C（A + main 又 `prefix='/auth'`）：router.routes 返 `/auth/login`（AC-10 PASS）但 openapi 返 `/auth/auth/login` → **AC-12 fail**。

  Generator 实现时若选错就被打回，且 Stage 4 评审无法判断是实现 bug 还是 spec 不严。
- **建议**：spec §AC-10 description 或 §决策表追加一行：`APIRouter` 必须自带 `prefix='/auth'`，main `include_router(router)` 不再传 `prefix`。tasks.md T-13 / T-15 同步钉死。

**MUST 2（AC-6 / 风险表 L86）：JWT secret "lazy" 读取语义不明，可能让 conftest setenv 失效**

- **位置**：spec.md AC-6 + 风险表 L86 + tasks.md T-8 description（间接）。
- **问题**：spec 说 secret "lazy at first encode if missing"。两种实现都满足"import 不 raise"：
  - 正确：`encode_*` 函数体内每次 `os.getenv('DATAPLAT_JWT_SECRET')`；测试 conftest `monkeypatch.setenv` 后再 call 生效。
  - 错误：module-level `_SECRET = os.getenv(...)`（None 不 raise） + encode 内 `if _SECRET is None: raise` → import 时固化 None；conftest 再 setenv 不会重读，encode 全 raise。

  AC-6 命令前置 `DATAPLAT_JWT_SECRET=...` 因此独立通过；但 AC-15 集成测试如果走 conftest setenv，错误实现下集成测试全 fail。
- **建议**：spec AC-6 description 补一句"secret 在 `encode_*` / `decode_*` 函数体内每次调用 `os.getenv` 读，不得 cache 在模块级常量"。或者明示 AC-15 fixture 在 conftest.py 顶层 `os.environ['DATAPLAT_JWT_SECRET'] = ...`（早于第一次 import）。

**MUST 3（AC-15 期望列 L78）：SKIP 通道语义与命令独立运行结果不一致**

- **位置**：spec.md AC-15 验证命令 + 期望列"exit 0 或 SKIP"。
- **问题**：AC-15 命令独立运行时 socket probe 失败 → `&&` 短路 → exit 1。但期望列写 "exit 0 或 SKIP"——SKIP→exit 0 必须靠 wrapper `_self_check.sh` 显式转，而 AC-17 才挂 `_self_check.sh`。AC-15 独立验证不可能返 SKIP=exit 0；这条与 spec 期望列字面冲突。
- **建议**：AC-15 期望列改"PG up：exit 0；PG down：本命令 exit 1，AC-17 内由 `_self_check.sh` SKIP 通道转 exit 0"。

### SHOULD FIX

**SHOULD 1（AC-6 L69）**：JWT 测试 secret 字符串名号称 "32-bytes" 实测 31 字节，< HS256 推荐 32。改为 `test-secret-32-bytes-long-xxxxxx`（加一位）或更显式的 32-byte 字面量。AC-15 用的 secret（35 字符）已 OK。

**SHOULD 2（AC-7 / T-9）**：cookies `secure=True` 对本地 http://localhost dev 不友好（浏览器拒绝 set-cookie）。测试 httpx 直连 ASGI 不受影响。建议 `cookies.py` 接 env var `DATAPLAT_COOKIE_SECURE`（默认 True）；spec 风险表加一条本地 dev 走 https 反向代理或显式 false。

**SHOULD 3（AC-15 / T-7）**：argon2 默认 `PasswordHasher()` 单次 hash ~65ms（CI runner 估 80-150ms）；AC-15 6 测试 + fixture 共 ~9 op = 0.6-1.4s。可接受，但 spec 未明示测试参数策略。T-7 / T-17 加注"测试用默认参数；如果 CI 慢可在 conftest monkeypatch low-cost params"。

**SHOULD 4（AC-8）**：`LocalAuthProvider.__new__(LocalAuthProvider)` + `isinstance(p, AuthProvider)` 是结构断言不是行为断言——runtime_checkable Protocol 只检查方法名存在，不验签名。建议追加 `inspect.signature(LocalAuthProvider.authenticate).parameters` 含 `username` 和 `password` 两参数；或在 AC-15 行为级测试覆盖。

**SHOULD 5（AC-11 / AC-15）**：AC-11 admin 路由"普通用户访问返 403"写在 description 但**无任何 AC 测试覆盖**。AC-15 列出的 7 个集成测试也不含 admin 403。建议 AC-15 测试列追加 "(h) 普通用户访问 `/admin/users` 返 403"，并把 ≥ 6 改 ≥ 7。

**SHOULD 6（AC-14 / AC-15）**：`pytest --collect-only | grep -cE "::"` 在 collection error 时有理论上误判风险（traceback 文本含 `::`）。但前半段 `pytest -q --tb=no` 失败时 `&&` 短路返 1 已拦截。建议 description 注释"测试函数体不可空（仅 pass）；行为级断言由 Stage 6 reviewer 兜底"，降低占位测试通过风险。

### NICE TO HAVE

**NICE 1**：spec §引用只列 design.md / core-domain-model；可加 cas-storage commit `fc73193` 作为前置成熟度证据。

**NICE 2**：OpenAPI tags / response_model 未规定。当前 router 不指定 tags，OpenAPI doc 会把所有路由平铺到 "default" tag。建议 AC-12 或 T-13 / T-14 注一句 `tags=["auth"]` / `["admin"]`。

**NICE 3**：风险表已 7 条覆盖；可加一行"`/auth/login` 暴力枚举（rate limit follow-up）"——已在非范围列。

## Verdict

**REVISION REQUIRED**

- MUST FIX：3
- SHOULD FIX：6
- NICE TO HAVE：3

判据：3 条 MUST 未关闭。

## 复检指引

Generator 修完后请自查（在 nta-lake 根目录跑）：

```bash
# MUST 1：router prefix 钉死后，应能 grep 到关键约束
grep -nE "router.*prefix.*'/auth'|prefix='/auth'|不再传 prefix" \
  .harness/changes/auth-scaffold-20260517/request_analysis/spec.md \
  .harness/changes/auth-scaffold-20260517/request_analysis/tasks.md

# MUST 2：secret 必须 fn-scope 读 env
grep -nE "每次调用|每次 encode|不得 cache|fn-scope|conftest.*顶层" \
  .harness/changes/auth-scaffold-20260517/request_analysis/spec.md

# MUST 3：AC-15 期望列与 SKIP 通道描述更新
grep -nE "PG up.*exit 0.*PG down|_self_check.sh.*SKIP" \
  .harness/changes/auth-scaffold-20260517/request_analysis/spec.md

# 三层校验抽样（参考 [[project-followup-harness-lint]]）
mkdir -p /tmp/auth-scaffold-recheck && cd /tmp/auth-scaffold-recheck
# 把 spec v2 AC-10 / AC-12 命令拷过来 bash -n + 实跑（应 exit != 0 因产物缺）
```

修完后 spec_review_v2.md 必须列出 v1 中 3 条 MUST 的关闭位置（行号 / 章节）。
