---
change_id: repo-api-mvp-20260517
target: unit_test/test_report_v1.md
target_version: 1
review_version: 1
reviewer: claude-stage6-reviewer
reviewed_at: 2026-05-17T08:50:00Z
verdict: REVISION REQUIRED
---

# Test Review v1

> 评审依据：`.harness/skills/expert-reviewer/SKILL.md` artifact 模式 + `.harness/skills/unit-test-write/SKILL.md` + `.harness/rules/coding-style.md` §1.7。

## 复现命令（评审者已实际执行）

```bash
# 1) 集成测试 13/13 PASS
DATAPLAT_PG_PORT=5433 \
DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx \
DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat \
  uv run pytest -q apps/api/tests/test_repos.py
# 实测输出：13 passed in 6.10s

# 2) self_check 13/13 PASS
DATAPLAT_PG_PORT=5433 bash scripts/_self_check.sh repo-api-mvp
# 实测输出：PASS=13 FAIL=0 SKIP=0

# 3) test_auth 回归
DATAPLAT_PG_PORT=5433 DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx \
DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat \
  uv run pytest -q apps/api/tests/test_auth.py
# 实测输出：11 passed in 2.65s（auth-scaffold _decode_user_from_cookie 抽取无回归）
```

> 上述三条均独立复现 ✅，test_report_v1 的"本地运行结果"段落数据真实。

## 检查清单结论（expert-reviewer SKILL §1 artifact 模式）

- [x] 每条 spec AC 在映射表中至少出现一次：13 条 AC 全部出现。
- [x] 没有空跑断言：`grep -nE "assert\s+True|assert\s+1\s*==\s*1|assert\s+\w+\s+is\s+not\s+None\s*$" apps/api/tests/test_repos.py` 返回空。
- [x] mock 范围与 `coding-style.md` §1.7 一致：`grep -nE "mock|Mock\(|@patch" apps/api/tests/test_repos.py` 仅命中 `httpx` 的 `patch_resp` 变量名与 `client.patch()` 方法调用，**无 unittest.mock / 数据访问层 mock**。
- [x] flaky / skip 已显式说明：MinIO env-drift skip / PG 不可达 SKIP 都有交代。
- [/] 测试名能反映场景与期望：函数名形如 `test_a_admin_create_returns_201`——字母前缀对应 AC-11 a~m 锚点，**后缀描述符合 SKILL `test_<被测对象>_<场景>_<期望>` 模式**。可接受（见 NICE TO HAVE #1）。
- [x] 映射表所列测试函数均可被 `pytest <文件>::<函数>` 单独跑通。

## 集成 vs 自检覆盖度核验

### AC-6 visibility 矩阵：3 user × 3 visibility = 9 组合

**预测面（self_check AC-6 / `RepoService._visibility_visible`）：9/9 ✅**

scripts/_self_check.sh:371-390 对 (None / user / admin) × (public / internal / private) 调用静态方法 `_visibility_visible(...)` 全 9 组合做布尔断言，**这是真单元测试不是 `assert True` 糊弄**，与 pytest 等价。

**HTTP detail GET（runtime wiring）：4/9 直接 + 1/9 间接 = 5/9**

| user \ vis | public | internal | private |
|---|---|---|---|
| anon | test_f (200) | **未测** | test_g (404) |
| user | **未测** | test_h (200) | test_i (404) |
| admin | test_a/e（间接经 POST→GET） | **未测** | test_d (200) |

**HTTP list GET：5/9 直接断言**

| user \ vis | public | internal | private |
|---|---|---|---|
| anon | test_l 断言含 | **test_l 未涉 internal** | test_l 断言不含 |
| user | **test_m 未涉 public** | test_m 断言含 | test_m 断言不含 |
| admin | test_e（部分） | **未测** | **未测** |

**评审判断**：spec AC-11 明确列出 a~m 共 13 case，并未要求 HTTP 端 9 组合全覆盖；predicate 端 9 组合靠 self_check AC-6 覆盖，HTTP 端覆盖率（5~6/9 detail + 5/9 list）足以验证 predicate↔router 的实际接线。**不构成 MUST FIX**，但 (anon, internal, detail) 是安全敏感的独立路径，标 SHOULD FIX #1。

### AC-11 ≥ 13：13 个独立、有意义的 test_a~test_m

`grep -c "^async def test_" apps/api/tests/test_repos.py` = 13。

- (a)~(c) 创建路径：201 / 403 / 409 — 各检查独立 status code + body 字段
- (d)/(e) admin 读路径：detail / list
- (f)~(i) visibility 检查：anon-public/private + user-internal/private
- (j) PATCH visibility 实时性（覆盖 spec MUST FIX-4：旧 cookie 不构成缓存窗口）
- (k) DELETE 后再 GET 404 链路
- (l)/(m) list visibility 矩阵（spec MUST FIX-3 引入）

每条均有独立语义，**不是凑数**。

### self_check shell python `assert ...` vs pytest 等价性

| AC | shell 检查内容 | 等价性判断 |
|---|---|---|
| AC-1~AC-5 | 模块/属性/签名 introspection | ✅ 等价（pytest 写也是同样断言） |
| AC-6 | 9 组合 predicate 调用 | ✅ 等价（真布尔逻辑断言） |
| AC-7~AC-9 | 路由 `dependant.dependencies` 含 `require_admin` / `get_optional_user` | 接受（catch 漏挂依赖；运行时行为靠集成补） |
| AC-10 | **只检查 `RepositoryCreate extra=forbid`** | ❌ **不等价 spec AC-10**：spec AC-10 描述的是 `GET /repos` 的 limit/offset/layer/visibility-aware total 行为，而非 schema extra=forbid。见 MUST FIX #1 |
| AC-11 | 调用 pytest + collect-only `grep -cE "::"` ≥ 13 | ✅（实际 pytest） |
| AC-12 | 真跑 ruff + mypy | ✅ |
| AC-13 | 自递归 true | 接受 |

## 问题列表

### MUST FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | `unit_test/test_report_v1.md:23`（AC-10 映射行）+ `scripts/_self_check.sh:422-426` | **AC-10 映射造假**：test_report 把 AC-10 标注为 "extra=forbid"，但 spec.md:31 的 AC-10 明确描述 `GET /repos` 的 query 行为（`limit` default 50/max 200、`offset` default 0、`layer` 过滤、`total` 反映 visibility 过滤后剩余数）。当前 self_check AC-10 只检查 `RepositoryCreate extra=forbid`——与 spec AC-10 语义无关。集成测试 test_l/test_m 部分覆盖 visibility 过滤，但**无任何测试验证**：(i) `limit/offset` 实际生效；(ii) `layer` query 实际过滤；(iii) `total` 字段反映 visibility 过滤后数量（spec.md:31 显式 "不泄露 private/internal 数量给无权 caller"）。这是 spec 直接写出的 AC，必须有断言覆盖。复现：`grep -n "limit\|offset\|layer=\|\"total\"" apps/api/tests/test_repos.py` 可见无 limit/offset/layer 的等值断言、无 `total` 字段断言。建议（任选其一）：(a) 新增 1~2 个 pytest 用例（例如 `test_n_list_pagination_and_layer_filter` + `test_o_list_total_reflects_visibility_filter`）；或 (b) 在 self_check AC-10 追加真实 list 行为断言（须 PG 在线）并把 test_report 映射改写真。**注意**：若改方案 (a)，AC-11 ≥ 13 仍满足（变成 ≥ 15）；若改 (b)，需修 self_check AC-10 实现 + test_report 文字。 |

### SHOULD FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | `apps/api/tests/test_repos.py`（整体覆盖） | (anon, internal) 的 detail GET → 404 路径**无端到端测试**——self_check AC-6 predicate 层覆盖了，但 HTTP 层没验证。考虑这是和 (anon, private) → 404 一样的存在性泄露语义关键路径（spec 风险表第 1 行），值得补一个用例。建议：补 `test_n_anonymous_get_internal_404`（结构与 test_g 同构，只差 visibility=internal）。**当前 verdict 不阻塞**，因为 spec AC-11 列举 a~m 没要求这一行；但作为最小增量提升安全断言密度。 |
| 2 | `unit_test/test_report_v1.md:14-26`（映射表） | 多处 AC 映射写 "self_check AC-X + tests"，但表格未标明 self_check 与 pytest 各自覆盖哪一**子断言**。例如 AC-6 行只写 "9 组合 + test_f/g/h/i/l/m"，未说明 9 组合靠 predicate 单元、HTTP 靠 6 集成（覆盖度见本评审"集成 vs 自检覆盖度核验"段）。建议在 v2 补一栏 "predicate / HTTP / 其他" 拆开，让下一个 reviewer 一眼能看出 9 组合不是凭空数。 |

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | `apps/api/tests/test_repos.py:111-485`（所有测试函数名） | 函数名前缀 `test_a_` ~ `test_m_` 是 spec AC-11 的字母锚点，方便交叉引用；但 SKILL.md §3 反模式列了 `test_a` `test_1`。本项目接受这种"锚点+描述"形式（实际有详细后缀 `_admin_create_returns_201`），但**建议未来变更**直接用纯描述名 + 在 docstring 引用 AC-11 锚点，避免边界判定争议。不阻塞本次。 |
| 2 | `unit_test/test_report_v1.md:44` | 报告引用 `SKILL.md §1.7` 但 unit-test-write SKILL.md 实际没有"§1.7"段；§1.7 是 `coding-style.md` 的小节号。建议改为 `coding-style.md §1.7` 或 `unit-test-write SKILL "核心原则 §2"` 等准确锚点。 |
| 3 | `unit_test/test_report_v1.md:83-89`（覆盖率段） | 用"行数 / 断言数"代替 coverage 工具读数。可接受为 MVP，但 NICE TO HAVE：未来引入 `pytest --cov` 给出真实数字（避免主观估算）。 |

## Verdict

**REVISION REQUIRED**

判据：1 个 MUST FIX 未关闭（AC-10 映射造假 + spec AC-10 的 query 行为零覆盖）。

## 复检指引

Generator 修完 v2 后自查：

1. **AC-10 子断言覆盖**：
   - `grep -nE "limit=\|offset=\|layer=\|\"total\"" apps/api/tests/test_repos.py` 至少命中 4 行（pagination + layer + total 字段断言）；**或** 修 self_check AC-10 后 `bash scripts/_self_check.sh repo-api-mvp` 中 AC-10 行的描述与 spec.md:31 一致（不再是 "extra=forbid"）。
   - 若选方案 (a)，重跑：`DATAPLAT_PG_PORT=5433 DATAPLAT_JWT_SECRET=... uv run pytest -q apps/api/tests/test_repos.py` 应 ≥ 15 passed。
2. **test_report v2 映射表**：AC-10 行的"测试"栏不再是 "self_check AC-10 (extra=forbid)"；应明确指向**实际验证 list query 行为**的测试函数或 shell 块。
3. **回归**：`DATAPLAT_PG_PORT=5433 bash scripts/_self_check.sh repo-api-mvp` 仍 PASS=13（或 ≥13）FAIL=0。
4. **空断言扫描**：`grep -nE "assert\s+True|assert\s+1\s*==\s*1" apps/api/tests/` 仍为空。
5. v2 报告写入 `unit_test/test_report_v2.md`；本评审复审写入 `unit_test/review/test_review_v2.md`，**不覆盖 v1**。
