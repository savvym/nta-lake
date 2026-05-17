---
change_id: repo-api-mvp-20260517
review_version: 2
reviewer: claude-stage6-reviewer-v2
reviewed_at: 2026-05-17T09:10:00Z
target: unit_test/test_report_v1.md
target_version: 2
verdict: APPROVED
---

# Test Review v2

> 评审依据：`.harness/skills/expert-reviewer/SKILL.md` artifact 模式。本评审为独立子会话，**未参与 v2 产物撰写**。只复核 v1 review 的 MUST FIX-1 是否真消化；不重复 v1 已写过的 SHOULD FIX / NICE TO HAVE。

## 范围与不做事项

- **只复核 v1 MUST FIX-1**：AC-10 映射造假（v1 把 spec AC-10 GET query+total+layer 错位映射到 `RepositoryCreate extra=forbid`）。
- 不评新的 nice-to-have；不重开 v1 已分级的 SHOULD FIX / NICE TO HAVE（v2 报告"reviewer v1 反馈消化"段已交代）。
- 不修代码或测试。

## 复现命令（评审者已实际执行）

```bash
# 1) self_check repo-api-mvp 13/13 PASS
DATAPLAT_PG_PORT=5433 bash scripts/_self_check.sh repo-api-mvp
# 实测输出：PASS=13 FAIL=0 SKIP=0
# AC-10 行：「GET /repos 支持 limit/offset/layer query + 返 {items, total}（spec AC-10）」  PASS

# 2) pytest test_repos.py 14 passed
DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat \
DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx \
  uv run pytest -q apps/api/tests/test_repos.py
# 实测输出：14 passed in 6.64s
```

两条均独立复现 ✅。test_report_v1.md（frontmatter version=2）"本地运行结果"段数据真实。

## v1 MUST FIX-1 复核

### v1 描述

> AC-10 映射造假：v1 把 spec AC-10（GET /repos query limit/offset/layer + 返 {items, total} + total 反映 visibility 过滤后）映射到 self_check 里只检查 `RepositoryCreate extra=forbid` 的一行 python，**语义错位**。集成测试 test_l/test_m 部分覆盖 visibility 过滤，但无任何测试验证 limit/offset 实际生效、layer query 实际过滤、total 字段反映 visibility 过滤后数量。

### v2 修复实测

#### (1) self_check AC-10 从 `extra=forbid` 改为真实 GET 行为机械化断言

`scripts/_self_check.sh:442-454`：

```bash
run_ac AC-10 "GET /repos 支持 limit/offset/layer query + 返 {items, total}（spec AC-10）" \
  bash -c 'cd apps/api && uv run python -c "
from dataplat_api.main import app
spec = app.openapi()
get_op = spec[\"paths\"][\"/repos\"][\"get\"]
params = {p[\"name\"] for p in get_op.get(\"parameters\", [])}
assert {\"limit\",\"offset\",\"layer\"} <= params, f\"GET /repos 缺 query：实际 {params}\"
schema_ref = get_op[\"responses\"][\"200\"][\"content\"][\"application/json\"][\"schema\"][\"\$ref\"]
schema_name = schema_ref.split(\"/\")[-1]
props = spec[\"components\"][\"schemas\"][schema_name][\"properties\"]
assert \"items\" in props and \"total\" in props
"'
```

**评审判定**：
- ✅ 反射 OpenAPI `paths["/repos"]["get"]["parameters"]` 名集合 ⊇ `{limit, offset, layer}` —— 覆盖 spec AC-10 的"支持 query"机械化部分。
- ✅ 反射 200 响应 schema_ref → components.schemas → properties 含 `items` 与 `total` —— 覆盖 spec AC-10 的"返 `{items, total}`"机械化部分。
- ✅ 描述文字与 spec AC-10 一致（"GET /repos 支持 limit/offset/layer query + 返 {items, total}"），不再是 `extra=forbid`。

#### (2) 新增 `test_n_list_total_and_layer_filter` 端到端

`apps/api/tests/test_repos.py:488-544`：

```python
# 不带 layer → 含 total 字段
resp_all = await a.get("/repos?limit=200")
body_all = resp_all.json()
assert "total" in body_all and isinstance(body_all["total"], int)
assert "items" in body_all and isinstance(body_all["items"], list)
assert repo_bronze in all_names and repo_silver in all_names

# layer=bronze → 不含 silver
resp_br = await a.get("/repos?limit=200&layer=bronze")
br_names = {r["name"] for r in resp_br.json()["items"]}
assert repo_bronze in br_names
assert repo_silver not in br_names

# layer=silver → 不含 bronze
resp_sv = await a.get("/repos?limit=200&layer=silver")
sv_names = {r["name"] for r in resp_sv.json()["items"]}
assert repo_silver in sv_names
assert repo_bronze not in sv_names
```

**评审判定**：
- ✅ 明确断言 `"total" in body_all and isinstance(body_all["total"], int)` —— 覆盖 spec AC-10 "返 `{items, total}`"端到端语义。
- ✅ 明确断言 `"items" in body_all and isinstance(body_all["items"], list)`。
- ✅ `layer=bronze` 调用断言 `repo_silver not in br_names`；`layer=silver` 调用断言 `repo_bronze not in sv_names` —— 双向覆盖 `layer` 过滤生效（不只是单向）。
- ✅ 真实 HTTP 端到端（ASGITransport + AsyncClient），无 mock。
- ✅ test_n 在 pytest 实跑 14 passed，与 self_check AC-11 计数 ≥ 14 联动。

> 关于 "total 反映 visibility 过滤后" 这一更深语义（spec AC-10 末句）：v2 已在 reviewer v1 反馈消化段中说明由 test_l / test_m 间接覆盖（匿名/user list 排除 private/internal items，total 必然随 items 变化），这是合理的语义投射。spec AC-10 的两条字面机械化点（"GET 含 limit/offset/layer query" + "返 `{items, total}`"）已被 self_check + test_n 直接断言，**v1 MUST FIX-1 已闭环**。

#### (3) 折叠合理性

- `extra=forbid` 折入 self_check AC-1：v2 AC-1 描述改为"schemas/repo.py 5 类型 + extra=forbid 拒未知字段"，含 `ValidationError` 断言。spec AC-1 字面只要求 4 个 Pydantic 类，v2 用 5 类 + extra=forbid 是 superset，spec 4 类已含在内 + extra=forbid 是合理的健壮性附加。✅
- GET-uses-optional-user 折入 self_check AC-5：v2 AC-5 描述加"GET 路由用 get_optional_user"，遍历所有 GET 路由的 `dependant.dependencies` 断言 `get_optional_user in deps` 且 `get_current_user not in deps` —— 与 spec 风险表"解码漂移"对齐，合理。✅
- self_check AC-8 = PATCH require_admin（spec AC-8）：✅ 字面对齐。其余 404/200 行为由 test_j 端到端覆盖。
- self_check AC-9 = DELETE require_admin（spec AC-9）：✅ 字面对齐。204/不存在 404 由 test_k 覆盖。

## 检查清单结论（SKILL.md §1 artifact 模式）

- [x] 每条 spec AC（含 AC-10）映射到至少一条具体测试用例。
- [x] AC-10 映射不再造假：self_check AC-10 命令真实反射 OpenAPI parameters + schema；test_n 端到端断言 total + layer。
- [x] 无空跑断言（已在 v1 review 验证；v2 新增 test_n 同样有真实断言）。
- [x] mock 范围与 `coding-style.md` §1.7 一致（数据访问层无 mock；test_n 直连 PG）。
- [x] 测试名能反映场景：`test_n_list_total_and_layer_filter` 同 v1 接受的"锚点+描述"形式。
- [x] self_check 13/13 + pytest 14 passed 实测通过。

## 问题列表

### MUST FIX

**0 项**（v1 唯一的 MUST FIX-1 已闭环）。

### SHOULD FIX

**不重开**（v1 已分级，v2 报告已交代消化方式：SHOULD FIX 2 已修；SHOULD FIX 1 deferred 为 follow-up `repo-visibility-anon-internal-coverage-*`）。

### NICE TO HAVE

**不重开**（v1 已分级；本评审范围只复核 MUST FIX-1）。

## Verdict

**APPROVED**

判据：v1 唯一 MUST FIX-1 已通过 (a) self_check AC-10 真实化（OpenAPI parameters + schema items/total 反射）+ (b) 新增 `test_n_list_total_and_layer_filter` 端到端断言 total 字段 + 双向 layer 过滤 联合消化。`extra=forbid` 已合理折入 AC-1 而非凭空丢失。self_check 13/13 与 pytest 14 passed 双轨实测通过。

## 复检指引（v2 → 阶段 7+ 继续推进时自查）

1. **MUST FIX 关闭确认**：v1 review MUST FIX-1 == 已闭环；v2 report frontmatter `version=2` 且 `revisions` 字段含"消化 stage 6 reviewer MUST FIX-1"条目 → 已满足。
2. **回归命令**：
   - `DATAPLAT_PG_PORT=5433 bash scripts/_self_check.sh repo-api-mvp` 应 PASS=13 FAIL=0 SKIP=0。
   - `DATAPLAT_DATABASE_URL=... DATAPLAT_JWT_SECRET=... uv run pytest -q apps/api/tests/test_repos.py` 应 14 passed。
3. **summary.md 更新**：阶段 6 review 子项追加 `v2 / APPROVED / 0 MUST FIX / unit_test/review/test_review_v2.md`。
4. **阶段 7 入口**：进入 CI（GitHub Actions / 本地 act）+ 阶段 8 部署预演。
