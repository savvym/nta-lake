---
change_id: adapter-framework-20260517
target: unit_test/test_report_v1.md
target_version: 1
review_version: 1
reviewer: claude-stage6-reviewer
reviewed_at: 2026-05-17T12:00:00Z
verdict: APPROVED
---

# Test Review v1

> 评审依据：`.harness/skills/expert-reviewer/SKILL.md` artifact 模式 + `.harness/skills/unit-test-write/SKILL.md` §核心原则 + spec v2 13 AC（含 v2 新增 AC-11 (m)）。
> 评审范围：`unit_test/test_report_v1.md` + `apps/api/tests/test_ingest.py`（13 用例）+ `scripts/_self_check.sh` 中 `run_adapter_framework`（13 AC block）。

## 验证动作（已机械化执行）

| 动作 | 结果 |
|---|---|
| `DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret bash scripts/_self_check.sh adapter-framework` | `PASS=13 FAIL=0 SKIP=0` ✓ |
| `uv run pytest -v tests/test_ingest.py`（PG 5433 + MinIO 9100） | `13 passed in 6.37s` ✓ |
| `grep -nE "assert\s+True\|assert\s+1\s*==\s*1" tests/test_ingest.py` | 空 ✓ |

## 检查清单结论

- [x] **每条 spec AC 在映射表中至少出现一次**：AC-1~AC-13 全 13 条 spec v2 AC 在 test_report_v1.md 映射表逐条列出且每条至少一个具体测试或 self_check block。
- [x] **没有空跑断言**：`grep -nE "assert\s+True\|assert\s+1\s*==\s*1" tests/test_ingest.py` 返回空。
- [x] **mock 范围与 coding-style.md §1.7 一致**：test_report §Mock 范围声明明确"无 mock 数据访问层；`dependency_overrides[get_blob_store]` 注入的是真实 `MinioBlobStore`（per-test bucket）"。adapter / runner / CommitService 全真跑 PG + MinIO。RawFileUploadAdapter 单元测试 (b) 传 `workspace=None / ctx=None` 已在偏离声明栏标注且属 Protocol contravariance（adapter 本身不依赖），不是数据访问层 mock。
- [x] **测试名能反映场景与期望**：13 测试命名规范 `test_<letter>_<场景>_<期望>`，一例（(j) 命名 `_404` 但断言 `401`）见下方 SHOULD FIX #1。
- [x] **flaky / skip 已显式说明**：test_report §"已知 flaky / 跳过"列出 PG/MinIO 不可达双探针 SKIP + 默认端口冲突 + 非标准凭据；无未声明 flaky。

## AC ↔ 测试映射诚实性逐条复核

| AC | 测试归宿 | 实测断言 | 诚实性 |
|---|---|---|---|
| AC-1 | self_check AC-1 + packages/core 33 回归 | self_check 用 python 一行实例化 `IngestResult(files=[IngestFileRef(...)])` 并断言 `mode==33188 + asset_count==0`；33 既有测试全 pass | ✓ 一行式合理（纯 schema 字段存在 + 既有字段保留） |
| AC-2 | self_check AC-2 + **test_a**（单元） | test_a 实测 `register` 后 `list_all()` 含 key / `get` 命中 / 重复 register `len(list_all())==1` 幂等 / `get_registry()` 单例已注册——**四子项全覆盖** | ✓ 不是 self_check 糊弄 |
| AC-3 | self_check AC-3（独立） | `isinstance(ctx, RunContext)` + `ctx.logger.info("ok")` 调用 | ✓ Protocol 结构校验一行式合理 |
| AC-4 | self_check AC-4 + 集成 c~m | self_check 断言 `iscoroutinefunction` + 返回类型注解含 "tuple"；c/d/g/h/i/k/l/m 实跑 `await AdapterRunner.run(...)` 路径 | ✓ 单元 + 集成双覆盖 |
| AC-5 | self_check AC-5 + **test_b**（单元） | test_b 实测 pass-through（file_count/path/sha256/mode 全断言）+ **path 重复 `pytest.raises(ValueError, match="重复")`**——两子项均真覆盖 | ✓ 第三块要求 path 重复 ValueError 真覆盖 |
| AC-6 | self_check AC-6 + 集成 payload | self_check 断言 `extra=="forbid"` + `parents in model_fields` + `ingest_summary in IngestResponse.model_fields` | ✓ 三关键字段断言完整 |
| AC-7 | self_check AC-7 + 11 集成 | self_check 断言路径在 router.routes；c~m 实跑该路径 | ✓ |
| AC-8 | self_check AC-8 | OpenAPI dict 含 path | ✓ 一行式合理（路由暴露纯结构） |
| AC-9 | self_check AC-9（v2 三重防沉默） | **`test -f` 前置两文件** + 正向 `grep -qE "_resolve_repo\|RepoService.get_by_owner_name"` + 反向 `! grep -rE "_visibility_visible" ...`（删 `2>/dev/null` 防文件不存在沉默通过）；实测 `routers/ingest.py` 第 35 行 `RepoService.get_by_owner_name(...)` 调用真实存在 | ✓ v2 修复后真复用、不重复；防沉默通过链完整 |
| AC-10 | self_check AC-10 + test_f / test_l / test_g / test_m | self_check grep `HTTPException`/`available`/`HTTP_400_BAD_REQUEST`/`resolved_parents`/`RefORM` 五关键词；4 集成测试对应 unknown adapter→404 / validation→400 / 幂等→dedup / parent 接链——四 case 独立断言 | ✓ |
| AC-11 | 13 测试 ≥ 13 | self_check `grep -cE "test_ingest\.py::"` ≥ 13；pytest 13/13 PASS | ✓ |
| AC-12 | self_check AC-12 | ruff + mypy 联合 PASS | ✓ |
| AC-13 | 自递归 | `true` | ✓ 约定 |

**结论**：13 AC 中**无一条**靠"self_check 一行式糊弄关键 AC"。spec v2 重点的 AC-11 (m) 父子链场景由集成测试 test_m **真断言** `C1.parents=[] + C2.parents=[c1_hash] + GET C1=200`；spec v2 重点的 AC-9 反向 grep 已加 `test -f` 前置 + 正向断言三重防沉默通过。

## 重点针对评审目标的 7 项验证

1. **AC ↔ 测试映射诚实**：✓ 见上表逐条对账。
2. **(a) registry 单元真覆盖**：✓ test_a 四子项（register / get / list_all / 幂等 / 模块单例）全断言（行 180-191）。
3. **(b) RawAdapter path 重复 ValueError**：✓ test_b 行 207-212 `pytest.raises(ValueError, match="重复")` 真覆盖。
4. **(m) parent 自动接链**：✓ test_m 行 571 `assert r1.json()["commit"]["parents"] == []`、行 586 `assert r2.json()["commit"]["parents"] == [c1_hash]`、行 589-590 `assert r_c1.status_code == 200`——MUST FIX-1 v2 修复回归断言完整。
5. **(j) 匿名 ingest private repo → 401 不是 404 是否合理**：✓ 合理。`routers/ingest.py:49` 函数签名 `_admin: AuthenticatedUser = Depends(require_admin)` 在 `_resolve_repo` 之前——require_admin gate 早于 visibility 校验，无 cookie 匿名 → 401（未登录）而非 404。这与 spec v2 AC-9 "非 admin → 403 (require_admin gate)" 语义一致（401 对应未登录，403 对应已登录 user）。test_j 行 461 注释也明确说明此 ordering 合理。**唯一问题**：测试函数名以 `_404` 结尾但断言 401，命名歧义，见 SHOULD FIX #1。
6. **(l) adapter 校验失败两 case**：✓ test_l 行 517-543 同函数内串联两 case——r1 `spec={}` 缺 files → 400；r2 重复 path → 400。两 status_code 各自独立断言。
7. **mock 范围声明诚实**：✓ test_report §"Mock 范围声明"逐项说明：`dependency_overrides[get_blob_store]` 注入**真实** MinioBlobStore（不是 mock）；adapter/runner/service 全真跑；test_b 单元传 `None` 是 Protocol contravariance（adapter 不依赖 ctx），与数据访问层 mock 无关。conftest 也无 unconditional mock。

## 问题列表

### MUST FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|

（0 条 MUST FIX）

### SHOULD FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | `apps/api/tests/test_ingest.py:442` | 测试函数名 `test_j_anonymous_ingest_private_repo_404` 与实际断言 `assert resp.status_code == 401`（行 461）不一致——SKILL §3 要求"测试名能反映场景与期望"。代码内注释行 460 已解释 401 的合理性，但函数名仍称 `_404`，未来读者会误读 | 重命名为 `test_j_anonymous_ingest_private_repo_401`；同步更新 test_report v1 行 51 第十项 `anon → 401` 与函数名对齐（当前 report 已写 401，仅函数名滞后） |

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | `apps/api/tests/test_ingest.py:200` | test_b 单元测试传 `workspace=None, ctx=None`，依赖 `RawFileUploadAdapter` 实现端不读 ctx/workspace。test_report §偏离已声明 "Protocol contravariance"，但未来其他 adapter 实现可能依赖 ctx——单元测试模板若被复制可能埋坑 | （非阻塞）后续 adapter follow-up 可在 conftest 抽 `_dummy_run_context()` fixture 返回真实 `StandardRunContext(logger=...)`，供需要 ctx 的 adapter 复用 |
| 2 | `apps/api/tests/test_ingest.py:497-499` | test_k 断言 `names == sorted(names)` 但 `paths` 已按 lexicographic 升序硬编码（"content/ch01..03"），无法独立证明 CommitService 内部 canonical 排序——只能证明 entries 顺序与 client 提交一致 | （非阻塞）若想真验证 canonical 排序，可提交时打乱 order（如 ch03/ch01/ch02），断言响应仍按 name 升序；当前 test_k 主要价值在多文件回归，可接受 |

## Verdict

**APPROVED**

判据：MUST FIX 数 = 0。

SHOULD FIX #1 是命名一致性问题，不阻塞 stage 6 通过，但建议在 stage 7 CI 阶段顺手修。NICE TO HAVE 两条留 follow-up，不阻塞流程。

## 复检指引

作者本轮无 MUST FIX 需修；进入 stage 7 (CI) 前可选自查：

1. （可选 / SHOULD FIX #1）`grep -n "test_j_anonymous_ingest_private_repo" apps/api/tests/test_ingest.py` → 改函数名为 `_401` 后，重跑 `uv run pytest -v tests/test_ingest.py::test_j_anonymous_ingest_private_repo_401` 应通过。
2. 在 `summary.md` stage 6 review 子项追加 `v1 / APPROVED / 0 MUST FIX / 1 SHOULD FIX / 2 NICE TO HAVE / 报告路径`。
3. 推进 `summary.md` stage=`unit_test` `status=approved` → 起 stage 7 CI。
4. （回归保险）下次跨 AC 自审：spec v2 跨 AC 自审 grep 已固化于 spec.md §"跨 AC 自审 grep"五条，CI 阶段可纳入 lint check。
