---
change_id: auth-scaffold-20260517
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-agent:auth-scaffold-stage2-reviewer
reviewed_at: 2026-05-17T05:30:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1 tasks 部分。

- [x] 每个任务粒度合理：T-1（添依赖）/T-3（init 导出）等小，T-13/T-17 偏大但合理（4 路由 / 7 集成测试约 2-4h）。整体 18 个 T-* 估计 ~2-3 工作日，可接受。
- [x] depends_on 形成 DAG（手工验：T-1 是叶子；T-3/T-4←T-2；T-6←T-5；T-9←T-8；T-10←T-2,T-5,T-7；T-12←T-7..11；T-13/T-14←T-11；T-15←T-13,T-14；T-16←T-5；T-17←T-13,T-14；T-18←T-16,T-17。无环。
- [x] process_tasks 7 条完整（spec/code/test 三轮 review + push + ci + deploy=skipped + user-confirm）。
- [x] 没有"做完整个系统"类目标任务。
- [x] 验收覆盖矩阵：AC-1..AC-17 全部有 T-* 关联。
- [ ] **但**：DAG 缺隐性依赖、部分 T-* description 缺关键字段、AC-11 行为级覆盖缺位（spec MUST 3 / SHOULD 5 的连带）。

## 抽查实跑结论

- DAG 手工成环检查：未发现循环。
- 覆盖矩阵抽查：AC-3↔T-5、AC-6↔T-8、AC-7↔T-9、AC-10↔T-13、AC-12↔T-13/T-15 一致。
- T-2 password_hash NULL 路径：T-10 description 已含"若 password_hash IS NULL → 返回 None"——✓ 风险表 L91 mitigation 落地。
- T-17 "fixture: alembic upgrade head 后用 ORM 创建 test 用户...teardown delete" 未指定 fixture scope——见 MUST 2。

## 分级问题列表

### MUST FIX

**MUST 1（T-11 depends_on 不完整）**

- **位置**：tasks.md T-11 description + `depends_on: [T-8]`。
- **问题**：T-11 实现 `get_current_user` 依赖：
  - 从 session 查 users 表 → 必依赖 `UserORM`（T-2）
  - 返回 `AuthenticatedUser` → 必依赖 `AuthenticatedUser` schema（T-5）
  - decode_token → T-8 ✓
  
  当前 `depends_on: [T-8]` 缺 T-2 与 T-5。虽然 T-12（auth/__init__ 聚合）间接通过依赖 T-11 + T-7..T-10 把图补回来，但严格 DAG 要求显式列出**任务自身**的依赖。
- **建议**：T-11 改 `depends_on: [T-2, T-5, T-8]`。同步覆盖矩阵 AC-9 → T-11, T-12 不变。

**MUST 2（T-17 fixture scope 未指定）**

- **位置**：tasks.md T-17 description。
- **问题**：T-17 写 "fixture：alembic upgrade head 后用 ORM 创建 test 用户（password_hash 真算）；teardown delete"。但未指定 `@pytest.fixture(scope=...)`。如果默认 function-scope，6 个测试每个跑一次 `alembic upgrade head` 约 6-12s 额外开销，且 schema state 在反复 upgrade 下可能不一致。
- **建议**：T-17 description 改"`@pytest.fixture(scope='session')` 跑 alembic upgrade head 一次；test 用户记录用 `scope='function'` + teardown delete row（不 drop table）"。同步 AC-15 expected behavior。

**MUST 3（T-14 admin POST 请求 schema 字段未定义；与 spec SHOULD 5 联动）**

- **位置**：tasks.md T-14 description。
- **问题**：T-14 写"POST /admin/users（接受 CreateUserRequest, role 限 admin）"，但 `CreateUserRequest` 字段未列。最小字段集应含 `username` / `password`（可选，SSO 留空）/ `email` / `role` / `external_id`。否则 Generator 实现时字段集任意，Stage 4/6 评审无判据。同 spec.md SHOULD 5：AC-11 还要补"普通用户 403"的行为级断言。
- **建议**：T-14 description 加一行"`CreateUserRequest(BaseModel)`: `username: str` / `password: str | None` / `email: str | None` / `role: Literal['admin','user']` / `external_id: str | None`；写 password 则 hash 后存 password_hash"。同步若 spec 加 AC-15(h)，T-17 应追加该测试要求。

### SHOULD FIX

**SHOULD 1（T-8 description）**：T-8 写"lazy（第一次 encode 时 raise if missing），不 import-time" —— 与 spec MUST 2 联动：必须明示"secret 在函数体内每次 `os.getenv` 读"，禁 module-level cache。

**SHOULD 2（T-9 description）**：cookies secure=True 写死。建议加 env-var `DATAPLAT_COOKIE_SECURE`（默认 True）的可配项；spec SHOULD 2 关联。

**SHOULD 3（T-10 description "抛 isinstance(BlobStore-style) 检测兼容"）**

- **位置**：tasks.md T-10 末行。
- **问题**：这行措辞晦涩，"BlobStore-style" 是上一变更 cas-storage 的术语，与本变更无关——疑似 copy-paste 残留。
- **建议**：删除该行，或改为"`isinstance(p, AuthProvider)` 检查应 PASS（class 上含 `authenticate` 方法即可）"，与 AC-8 一致。

**SHOULD 4（T-12 重复 AC 覆盖）**

- **位置**：tasks.md T-12 `covers_ac: [AC-9]`。
- **问题**：AC-9（get_current_user 存在）已由 T-11 覆盖；T-12 是 `auth/__init__.py` 聚合导出，性质类同 T-3 / T-6。若 AC-9 命令需要从 `dataplat_api.auth import get_current_user`，则 T-12 必要；但 AC-9 实测命令是 `from dataplat_api.auth.deps import get_current_user`——直接走子模块，**不经过 __init__**——T-12 对 AC-9 验证无贡献。
- **建议**：T-12 description 注"非 AC-9 必要，但保持 packages style consistency"，或 covers_ac 改空 / 改 AC-12（main import 时间接受益）。

**SHOULD 5（T-13 / T-15 router prefix 归属）**

- **位置**：tasks.md T-13 / T-15。
- **问题**：与 spec MUST 1 联动。T-13 description 未明示 `APIRouter(prefix='/auth')`；T-15 未明示 `app.include_router(router)` 不再传 prefix。
- **建议**：T-13 加一行"`router = APIRouter(prefix='/auth', tags=['auth'])`"。T-15 加一行"`app.include_router(auth_router)` 不再传 prefix"。

**SHOULD 6（T-17 测试列举遗漏 admin 403）**

- **位置**：tasks.md T-17 description。
- **问题**：与 spec SHOULD 5 联动。当前列 7 个测试（hash/verify, JWT, login success cookies, login fail 401, me success, me missing 401, refresh），没有 admin 403。
- **建议**：列追加"普通用户 POST /admin/users 返 403"。

### NICE TO HAVE

**NICE 1（粒度）**：T-17 含 7+ 个集成测试 + fixture 工作，估 4-6h 超 1-3h 粒度建议。可拆分 T-17a（hash+JWT 单元）/T-17b（auth 路由集成）。当前可接受。

**NICE 2（顺序提示）**：tasks.md §DAG 健全性段已手述无环，可机械化为 `python -c "import yaml; ..."` 校验脚本，落入 `_self_check.sh`。

**NICE 3（process_tasks P-deploy 状态）**：P-deploy `status: skipped` 但未列 reason；spec.md §阶段进度表已 "skipped: 无运行时部署面"——tasks.md 可同步 reason 字段。

## Verdict

**REVISION REQUIRED**

- MUST FIX：3
- SHOULD FIX：6
- NICE TO HAVE：3

判据：3 条 MUST 未关闭（T-11 显式依赖 / T-17 fixture scope / T-14 CreateUserRequest 字段）。

## 复检指引

Generator 修完后请自查（在 nta-lake 根目录跑）：

```bash
# MUST 1：T-11 显式依赖 T-2 T-5
grep -nE "id: T-11" -A 6 .harness/changes/auth-scaffold-20260517/request_analysis/tasks.md \
  | grep -E "depends_on.*T-2.*T-5|depends_on.*T-5.*T-2"

# MUST 2：T-17 fixture scope='session'
grep -nE "scope='session'|scope=session" .harness/changes/auth-scaffold-20260517/request_analysis/tasks.md

# MUST 3：CreateUserRequest 字段
grep -nE "CreateUserRequest|username.*password.*role|password: str \| None" \
  .harness/changes/auth-scaffold-20260517/request_analysis/tasks.md

# DAG 重校（无环 + AC 全覆盖）
python3 - <<'PY'
import yaml, re, pathlib
text = pathlib.Path('.harness/changes/auth-scaffold-20260517/request_analysis/tasks.md').read_text()
yaml_block = re.search(r"```yaml\ntasks:(.*?)```", text, re.DOTALL).group(0).strip('`')
data = yaml.safe_load(yaml_block.replace('yaml\n',''))
ids = {t['id'] for t in data['tasks']}
for t in data['tasks']:
    for d in t.get('depends_on', []):
        assert d in ids, f"{t['id']} depends on missing {d}"
print("DAG OK; tasks:", len(data['tasks']))
PY
```

修完后 tasks_review_v2.md 必须列出 v1 中 3 条 MUST 的关闭位置（任务 ID + 行号）。
