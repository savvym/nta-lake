---
change_id: auth-scaffold-20260517
target: tasks.md
target_version: 2
review_version: 2
reviewer: claude-agent:auth-scaffold-stage2-reviewer
reviewed_at: 2026-05-17T05:50:00Z
verdict: APPROVED
---

# Tasks Review v2

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1 tasks 部分。

- [x] 18 个 T-* + 7 个 P-* 完整；粒度合理（T-17 含 7 集成测试稍大但可接受）。
- [x] DAG 无环；T-11 显式依赖修后无遗漏（见下"v1 MUST 关闭核对"）。
- [x] process_tasks 完整覆盖 spec/code/test review + push + ci + deploy(skipped) + user-confirm。
- [x] AC-1..AC-17 全部有 T-* 关联（覆盖矩阵未变）；AC-15 (h) 由 T-14（路由）+ T-17（测试）共同覆盖。

## v1 MUST 关闭核对

| v1 MUST | 关闭位置 | 验证 |
|---|---|---|
| **MUST 1**（T-11 显式依赖 T-2/T-5） | tasks.md L114：`depends_on: [T-2, T-5, T-8]` + 行内注释「tasks MUST FIX-1：显式补 T-2（UserORM）+ T-5（AuthenticatedUser）」 | `grep -nE "depends_on.*T-2.*T-5.*T-8"` 命中 L114 |
| **MUST 2**（T-17 fixture scope） | tasks.md L177-180：`@pytest.fixture(scope='session')` 跑 alembic upgrade head 一次 + `scope='function'` teardown delete row + conftest.py 顶层 `os.environ.setdefault('DATAPLAT_JWT_SECRET', 'test-secret-not-prod-x32-bytes-xxxxx')` 早于任何 dataplat_api import | `grep -nE "scope='session'.*alembic|os.environ.setdefault"` 命中 L177/L179 |
| **MUST 3**（T-14 CreateUserRequest / UpdateUserRequest 字段） | tasks.md L141-148：CreateUserRequest 字段（username/password\|None/email\|None/role: Literal['admin','user']/external_id\|None）+ UpdateUserRequest（role/new_password/is_active 全 Optional）+ admin 路由 403 断言 | `grep -nE "CreateUserRequest\|UpdateUserRequest\|Literal\['admin','user'\]"` 命中 L141/L145/L148 |

## v2 抽查（DAG 重校 + 关键字段）

- DAG 手工重校：T-1 叶子；T-3/T-4 → T-2；T-6 → T-5；T-9 → T-8；T-10 → T-2/T-5/T-7；T-11 → T-2/T-5/T-8（**已修**）；T-12 → T-7..T-11；T-13 → T-9/T-10/T-11；T-14 → T-11；T-15 → T-13/T-14；T-16 → T-5；T-17 → T-13/T-14；T-18 → T-16/T-17。无环。
- 覆盖矩阵 AC-11 现由 T-14 cover；AC-15 由 T-17 cover，行为级 403 测试由 T-14 admin 路由 + T-17 测试 (h) 同时落地。T-14 `covers_ac: [AC-11, AC-15]` 显式包含 AC-15——OK。
- T-14 明示 `APIRouter(prefix='/admin')`（L140），与 spec MUST 1 router prefix 钉死同模式落地。
- T-17 conftest.py 顶层 setdefault 经实测可让 lazy fn-scope `os.environ.get` 正确拿到值——闭环。

## 残留问题（不阻塞 APPROVED）

### SHOULD

- **SHOULD（旧 v1 SHOULD 3）**：T-10 description 末行「抛 isinstance(BlobStore-style) 检测兼容」仍为 cas-storage 的语义残留，与 auth 无关。建议 Stage 3 编码前删除或改为「`isinstance(p, AuthProvider)` PASS（class 上含 `authenticate` 方法即可）」。
- **SHOULD（旧 v1 SHOULD 5）**：T-13 description 没显式重复 spec AC-10 的 `APIRouter(prefix="/auth")`。spec L43 已钉死，Generator 必读 spec，但 T-13 同步一行更稳。T-14 已写明 `APIRouter(prefix='/admin')`。
- **SHOULD（旧 v1 SHOULD 4）**：T-12 `covers_ac: [AC-9]` 严格说 AC-9 是 `from dataplat_api.auth.deps import ...` 直接路径，不走 __init__——T-12 实质是聚合不影响 AC-9 验收。可改 covers_ac 空或备注 "聚合，不直接 cover AC"。
- **SHOULD（v2 新增）**：tasks.md `authored_at: 2026-05-17T05:20:00Z` / 无 `version` 字段未更新到 v2——frontmatter 卫生。

### NICE

- §DAG 健全性段未机械化（仍是手述），可用 Python yaml.safe_load 校验脚本落进 `_self_check.sh`，但属流程级 follow-up 而非本变更范围。
- P-deploy 没有 reason 字段（spec §阶段进度已写"skipped: 无运行时部署面"，可同步）。

## Verdict

**APPROVED**

判据：v1 三条 MUST（T-11 显式依赖 / T-17 fixture scope + conftest secret / T-14 CreateUserRequest 字段）全部关闭；DAG 重校无环；覆盖矩阵完整。SHOULD/NICE 残留不阻塞 Stage 3。

## 复检指引（Stage 3 编码前 / Stage 4 评审时使用）

```bash
# 1. tasks v2 MUST 关闭点 grep
grep -nE "depends_on: \[T-2, T-5, T-8\]" .harness/changes/auth-scaffold-20260517/request_analysis/tasks.md
grep -nE "scope='session'.*alembic|conftest.py 顶层" .harness/changes/auth-scaffold-20260517/request_analysis/tasks.md
grep -nE "CreateUserRequest|UpdateUserRequest|Literal\['admin','user'\]" .harness/changes/auth-scaffold-20260517/request_analysis/tasks.md

# 2. DAG 重校（Stage 3 编码前可机械化）
python3 - <<'PY'
import re, pathlib, yaml
text = pathlib.Path('.harness/changes/auth-scaffold-20260517/request_analysis/tasks.md').read_text()
block = re.search(r"```yaml\ntasks:.*?```", text, re.DOTALL).group(0)
inner = block.replace('```yaml\n','').rstrip('`').rstrip()
data = yaml.safe_load(inner)
ids = {t['id'] for t in data['tasks']}
for t in data['tasks']:
    for d in t.get('depends_on') or []:
        assert d in ids, f"{t['id']} depends on missing {d}"
print("DAG OK; tasks:", len(data['tasks']))
PY
```
