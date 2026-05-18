---
change_id: stage9-followup-cleanup-20260518
target: spec.md
target_version: 2
review_version: 2
reviewer: claude-agent:stage9-followup-cleanup-20260518-stage2-reviewer-v2
reviewed_at: 2026-05-18T10:30:00Z
verdict: REVISION REQUIRED
---

# Spec Review v2

## v1 MUST FIX / SHOULD / NICE 复检

| # | v1 类别 | v1 issue 摘要 | v2 状态 | 证据 |
|---|---|---|---|---|
| MUST #1 | spec.md AC-1 grep pattern 永远 fail（`output_commit_hash.*ForeignKey` 同行匹配跨第 86/88 行不命中） | **CLOSED** | spec v2 改用 awk 状态机：`awk '/^class PipelineCacheORM/{p=1;next} p && /^class /{exit} p' pipeline.py \| grep -q 'ondelete="CASCADE"'`。reviewer 本机两轮 dry-run 验证：(a) pre-T-1（当前 RESTRICT）跑 CASCADE grep → exit=1（fail）；(b) sed 模拟 post-T-1（改 CASCADE）跑 CASCADE grep → exit=0（pass）。pattern 行为正确，pre/post 状态机敏感 |
| SHOULD #1 | FK CASCADE 决策漏 nullable=False 硬约束 | **CLOSED** | summary.md 决策表第 56 行新增 "(a) 技术硬约束：`PipelineCacheORM.output_commit_hash` 当前 `nullable=False`（model 第 86-90 行），SET NULL 物理违反 NOT NULL，必须先改 nullable=True 才能用 SET NULL，超出本 change scope；(b) 语义：cache_key 指向无效 commit 无意义"。两层理由：硬约束 + 语义 |
| SHOULD #2 | risk 表漏 test_pipeline_e2e.py 同名 fixture 隐患 | **CLOSED** | spec v2 风险表第 78 行新增 "`test_pipeline_e2e.py` 同名 `_seed_bronze` 未跟修（v1 reviewer SHOULD #2 实证）"，显式 accept + follow-up `test-fixture-isolation-other-files-*`。措辞清晰区分 stage 9 未撞（owner/name 动态 + raw 与 demo 不同）vs 未来隐患（同测试多次重跑撞自己） |
| SHOULD #3 | AC-4 描述 vs 期望数字打架（描述 "7 集成测试" / 期望 ≥10） | **CLOSED** | spec v2 AC-4 描述改 "全部 10 个测试 PASS（4 个 sync 单元 + 6 个 @pytestmark_int 集成）"；期望写 `10 passed in Xs`。reviewer 实测 `grep -cE "^(async )?def test_" apps/api/tests/test_pipeline_orchestrator.py` = 10（4 sync: test_unknown_processor/test_cycle/test_unknown_node_ref/test_multi_input_rejected + 6 async @pytestmark_int），数字与文件一致 |
| NTH #1 | _seed_bronze 决策措辞模糊 | **CLOSED** | summary.md 决策表第 60 行改 "测试断言依赖 `_seed_bronze` 返回的 commit_hash，content 只在 seed 期被 hashed，不被任何 assertion 读取（v1 reviewer 已实读 6 处 callsite 确认）"。措辞精化 |
| NTH #2 | AC-1 0005 文件 glob 脆弱（test -f + glob 多匹配 too many arguments） | **CLOSED** | spec v2 AC-1 命令改 `ls apps/api/alembic/versions/0005_*.py >/dev/null 2>&1 && grep -q "CASCADE" apps/api/alembic/versions/0005_*.py` |
| NTH #3 | 0004 grep RESTRICT 裸字串（误命中风险） | **CLOSED** | spec v2 AC-1 命令改 `grep -q 'ondelete="RESTRICT"' apps/api/alembic/versions/0004_pipeline_orchestrator.py`。reviewer 本机验证 exit=0 |

v1 全部 7 条 issue 真闭环。**但 v2 引入 1 个新 MUST FIX（AC-3 同型 grep 窗口 bug，详下），verdict 仍 REVISION REQUIRED**。

## stage 2 AC kind 字段必查（expert-reviewer SKILL § "stage 2 AC kind 字段必查"）

| 必查项 | 结果 | 证据 |
|---|---|---|
| (i) AC 表存在 `kind` 列 | **PASS** | `awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' spec.md \| grep -E '^\|[^\|]*\|[[:space:]]*kind[[:space:]]*\|'` 命中表头 `\| ID \| kind \| 描述 \| 验证方式 \| 期望 \|` |
| (ii) ≥1 行 AC kind 单元格真为 `behavioral`（AC 行 regex 锚定，**不接受裸字串 grep**） | **PASS** | `awk ... \| grep -E '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|'` 命中 2 行：AC-2 + AC-4，均以 `**behavioral**` 形式出现 |
| (iii) frontmatter 是否声明 `ac_kind_lint: exempt` | **N/A**（未声明） | `grep -c "ac_kind_lint" spec.md` = 0；本 change 不在自声明豁免清单；跳过 git diff 复核（按 SKILL 规约） |

必查 3 项全 PASS。

## 跨 AC 一致性自审 9 条复检（request-analysis SKILL）

| # | 条目 | 结果 | 备注 |
|---|---|---|---|
| 1 | 跨 AC 矛盾词（事务内/前/外） | PASS | 无命中 |
| 2 | hash 字段 ↔ schema ↔ idempotency ↔ fixture 四链路 | PASS | 本 change 不涉及新 hash 字段；只修 FK + fixture 前缀 |
| 3 | 每条 AC 一行式验证命令 | PASS | 4 AC 全有 |
| 4 | 风险缓解 ↔ AC 测试列表 | PASS | 风险 #1→AC-2；风险 #2→AC-4；风险 #5（test_pipeline_e2e）显式 accept + follow-up |
| 5 | parents=[] 检查 | PASS | spec 无 `parents=[]` 字面 |
| 6 | 反向 grep 配 test -f + 不吞 stderr | PASS | 无 `! grep`；无 `2>/dev/null`（除 `ls ... >/dev/null 2>&1` 静默 ls 输出，不吞 grep stderr） |
| 7 | process_tasks 6 条必填 | PASS | tasks.md 含 P-spec-review/P-code-review/P-test-review/P-ci/P-deploy/P-user-confirm |
| 8 | AC 验证命令 dry-parse | **FAIL（AC-3 跑 dry-run 命中窗口缺陷）** | 见下 MUST FIX-1 |
| 9 | summary.md 模板占位符残留 | PASS | summary.md 无任何 `<feature-slug>` / `<YYYY-MM-DDTHH:MM:SSZ>` 残留 |

## 检查清单结论

- [x] 背景写明了为什么现在做（继承 pipeline-orchestrator-mvp stage 9 deploy_verify follow-up）
- [x] 问题陈述对外部读者可理解（Bug 1 / Bug 2 各自一段）
- [x] 范围 / 非范围都有（4 AC + 5 条 out of scope）
- [ ] 每条 AC 可演示且可机械化 — **AC-3 grep 命令在 T-4 实施后仍 fail**（见 MUST FIX-1）
- [x] 风险有缓解或显式 accept（5 条风险全有缓解，含新增 test_pipeline_e2e.py）
- [x] 没有把已有架构当新提案
- [x] 待澄清问题已清零
- [x] dogfood AC 分层规约（AC-2 + AC-4 标 behavioral；≥1 满足）

## 设计合理性评估

### 1. AC-1 awk 状态机 pattern（v1 MUST FIX-1 修复方案）
**合理且通过 dry-run 验证**。reviewer 本机两轮真跑：

```bash
# pre-T-1（当前 RESTRICT）
awk '/^class PipelineCacheORM/{p=1;next} p && /^class /{exit} p' apps/api/dataplat_api/models/pipeline.py | grep -q 'ondelete="CASCADE"'
# exit=1 ✓ (fail，符合预期)
awk ... | grep -q 'ondelete="RESTRICT"'
# exit=0 ✓ (pass，模型仍为 RESTRICT)

# post-T-1（sed 模拟改 CASCADE）
sed -i 's/ondelete="RESTRICT"/ondelete="CASCADE"/' apps/api/dataplat_api/models/pipeline.py
awk ... | grep -q 'ondelete="CASCADE"'
# exit=0 ✓ (pass，符合预期)
awk ... | grep -q 'ondelete="RESTRICT"'
# exit=1 ✓ (fail，模型已是 CASCADE)
# 还原 OK
```

awk 状态机锚定 PipelineCacheORM 类范围（`/^class PipelineCacheORM/{p=1;next}` 起、`p && /^class /{exit}` 止），即使未来 PipelineNodeRunORM.output_commit_hash 类似字段也加 FK，不会误命中。pre/post 真状态机敏感。

### 2. FK CASCADE 决策的 nullable=False 硬约束补充
**合理**。决策表 (a) 技术硬约束 + (b) 语义两层理由完整。SET NULL 物理不可行（违反 NOT NULL）这条硬约束让 CASCADE 成为当下唯一可行选项，决策链路扎实。

### 3. risk 表 test_pipeline_e2e.py 显式 accept 条目（v1 SHOULD #2 修复方案）
**措辞清楚**。reviewer 复核：

- test_pipeline_e2e.py 第 172 行确有同名 `_seed_bronze`（独立函数；与 test_pipeline_orchestrator.py 不共享）
- 第 305 行 `raw = b"hello\r\nworld   \r\n\r\n\r\n\r\nend\r\n"`，确实与 stage 9 demo `sample.md` 内容不同
- owner/name 用 uuid 动态生成（`f"e2e{uuid.uuid4().hex[:4]}"`）→ 单测内 commit 撞 hash 不显（因 commit_hash 受 parent_ref/tree 影响；详 design.md §4.4，但本 change scope 不分析）

spec v2 风险表行 "stage 9 未 trigger 撞（该文件 raw 与 demo 不同），CI 单跑也不撞；隐患是未来同测试多次重跑撞自己（同 content 第二次进 db 必撞 commits.hash PK）；follow-up `test-fixture-isolation-other-files-*` 待累积证据再处理" — 区分了 **当下不撞** 与 **未来隐患** 两个层面，显式 accept 路径明确。措辞清楚。

### 4. AC-4 数字校准（v1 SHOULD #3 修复方案）
**合理且数字与文件一致**。reviewer 实测：

```bash
grep -nE "^(async )?def test_" apps/api/tests/test_pipeline_orchestrator.py
# 60:def test_unknown_processor() -> None:        # sync 1
# 77:def test_cycle() -> None:                     # sync 2
# 101:def test_unknown_node_ref() -> None:         # sync 3
# 118:def test_multi_input_rejected() -> None:     # sync 4
# 401:async def test_lineage_written_on_cache_miss # async 1
# 472:async def test_cache_hit_skips_processor     # async 2 (stage 9 fail)
# 526:async def test_cache_hit_updates_ref         # async 3 (stage 9 fail)
# 577:async def test_node_value_error_marks_failed_with_null_audit # async 4
# 639:async def test_node_400_marks_failed         # async 5
# 697:async def test_cache_hit_writes_audit_fields # async 6 (stage 9 fail)
```

10 个 = 4 sync + 6 async，期望写 `10 passed in Xs`，数字一致。三个 stage 9 后曾 FAIL 的 cache_hit 测试名都在文件中正确存在。

### 5. AC-2 / AC-4 真 behavioral？
**真 behavioral**：

- AC-2 → L3（脚本真跑断言）：alembic upgrade/downgrade 三连 + information_schema SQL 后置断言
- AC-4 → L2（ASGITransport in-process roundtrip）：pytest 真跑 10 个集成测试

满足 SKILL § "AC 分层规约" ≥1 条 behavioral AC 硬约束。

### 6. AC-3 grep 窗口长度问题（**新发现 MUST FIX**）

**这是 v2 引入的新 MUST FIX，与 v1 MUST FIX-1（AC-1 grep 跨行匹配）完全同型，但发生在 AC-3 上、v1 review 未捕获。** reviewer 实证如下：

spec v2 AC-3 命令：
```bash
test -f apps/api/tests/test_pipeline_orchestrator.py \
  && grep -A 15 "async def _seed_bronze" apps/api/tests/test_pipeline_orchestrator.py \
  | grep -qE "uuid\.uuid4\(\)\.hex.*content|uuid_prefix.*content"
```

实测：
- `async def _seed_bronze` 在 test_pipeline_orchestrator.py **第 261 行**
- T-4 合理实施位置（`unique_content = ...` 注入到 r_blob post 之前）= **第 288 行**
- **距离 = 27 行**
- `grep -A 15` 窗口只到第 276 行 → `unique_content` 行不在窗口内 → grep 永远 fail

reviewer dry-run（用 python 注入 T-4 合理实施代码，跑 spec v2 AC-3 命令）：

```bash
# 模拟 T-4 实施
python3 -c "
with open('apps/api/tests/test_pipeline_orchestrator.py') as f: lines = f.readlines()
out = []; inserted = False
for line in lines:
    if not inserted and 'r_blob = await c.post(' in line:
        indent = line[:len(line)-len(line.lstrip())]
        out.append(f'{indent}unique_content = f\"<!-- fixture-uuid {{uuid.uuid4().hex}} -->\\\\n\".encode() + content\n')
        inserted = True
    if 'f\"/repos/{owner}/{name}/blobs\", content=content' in line:
        line = line.replace('content=content', 'content=unique_content')
    out.append(line)
open('apps/api/tests/test_pipeline_orchestrator.py', 'w').writelines(out)
"
# 跑 AC-3
grep -A 15 "async def _seed_bronze" apps/api/tests/test_pipeline_orchestrator.py | grep -qE "uuid\.uuid4\(\)\.hex.*content|uuid_prefix.*content"
echo "exit=$?"  # → exit=1（fail！） 
# 用 -A 30 看
grep -A 30 "async def _seed_bronze" apps/api/tests/test_pipeline_orchestrator.py | grep "unique_content"
# → 命中（unique_content 行在 -A 30 窗口内）
```

**根因**：`_seed_bronze` 函数体含 `_make_admin()` + `transport = ASGITransport(app=app)` + `async with AsyncClient(...)` + `/auth/login` post（多行 json）+ `/repos` post（多行 json）+ `r_blob = await c.post(...)`，前置代码已占 27 行；`-A 15` 远远不够。

**这与 v1 MUST FIX-1 完全同型**（v1 是 `grep -A 2` 窗口跨行 `output_commit_hash` 到 `ForeignKey` 不命中；v2 AC-3 是 `grep -A 15` 跨第 261→288 行不命中）。v1 reviewer 复检 AC-1 awk 修复时**未类比检查 AC-3**，导致同型 bug 漏网。

**建议**：扩窗口或换 anchor。三种方案：

(a) 简单扩窗口：`grep -A 35 "async def _seed_bronze" ...`（实测 -A 30 已够，预留 5 行余量）
(b) awk 状态机（与 AC-1 同模式）：`awk '/^async def _seed_bronze/{p=1;next} p && /^async def |^def /{exit} p' apps/api/tests/test_pipeline_orchestrator.py | grep -qE "uuid\.uuid4\(\)\.hex.*content|uuid_prefix.*content"`
(c) python parser：复杂度过高，不推荐

强推 (b)：与 AC-1 awk 模式一致，符合 v2 修复思路；未来若 _seed_bronze 函数继续扩，也不会失败。reviewer 已 dry-run 验证 (b) 方案：模拟 T-4 实施后，awk 状态机命令命中第 288 行 unique_content，exit=0。

### 7. T-3 alembic current 前置在 spec AC-2 命令中未体现
**SHOULD FIX**。tasks v2 T-3 description 第 0 步加了 `uv run alembic current` 期望 `0004 (head)` 前置（响应 v1 tasks_review SHOULD #2），但 spec v2 AC-2 验证命令仍只有三连（upgrade head + downgrade 0004 + upgrade head），**未加前置**。一致性不完美：tasks T-3 是手动跑、spec AC-2 是 self_check 跑，可能 dev db 状态不在 0004 时 spec AC-2 误判 fail。

**建议**：spec AC-2 命令加前置 `uv run alembic current 2>&1 | grep -q '0004' && ...`，或在 spec AC-2 期望里加注 "假设 dev db baseline = 0004（详 T-3 第 0 步）"。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | spec.md §验收标准 AC-1 验证命令（AC-3 子段） | AC-3 grep 命令 `grep -A 15 "async def _seed_bronze" ...` 窗口只 15 行；T-4 合理实施位置（第 288 行 `unique_content = ...`）距 `async def _seed_bronze`（第 261 行）= 27 行，窗口不够 → grep 永远 fail。这是 v1 MUST FIX-1（AC-1 跨行匹配）的**同型 bug**，v1 reviewer 漏检。reviewer 已 dry-run 验证：python 注入合理 T-4 后跑 AC-3 命令 → exit=1（fail，但应 pass） | 改为 awk 状态机（与 AC-1 同模式）：`awk '/^async def _seed_bronze/{p=1;next} p && /^async def \|^def /{exit} p' apps/api/tests/test_pipeline_orchestrator.py \| grep -qE "uuid\.uuid4\(\)\.hex.*content\|uuid_prefix.*content"`。或简单扩窗口 `grep -A 35`（实测 -A 30 已够，留余量）。务必本机两轮 dry-run（pre-T-4 fail / post-T-4 pass）确认。同步 T-6 description AC-3 验证命令引用新 pattern |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | spec.md §验收标准 AC-2 验证命令 | tasks v2 T-3 加了 alembic current 前置（响应 v1 SHOULD #2），但 spec AC-2 命令仍只三连，无前置。dev db 状态不在 0004（head）时 self_check 误判 fail | spec AC-2 加前置 `uv run alembic current 2>&1 \| grep -q "0004" && <三连命令>`；或期望表显式注 "假设 dev db baseline = 0004（详 tasks T-3 第 0 步）" |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | spec.md §验收标准 AC-3 命令 grep 正则 | grep -E 备用 pattern `uuid_prefix.*content` 是为兼容某种 "提取局部变量 uuid_prefix" 形态，但 T-4 description 明示用 `f"<!-- fixture-uuid {uuid.uuid4().hex} -->\n".encode() + content` 形态，`uuid_prefix` 备用永不命中。不阻塞 v2，但冗余可清理 | 删除 `\|uuid_prefix.*content` 备用，简化为 `uuid\.uuid4\(\)\.hex` 主形态；或保留作向后兼容显式注 "若实现改用局部变量名 uuid_prefix 也兼容" |
| NTH-2 | spec.md §引用 | 引用列表已含 design.md / harness-ac-behavioral-tier；可加 v1 review 路径作为审计链 | 加 `.harness/changes/stage9-followup-cleanup-20260518/request_analysis/review/spec_review_v1.md` 到引用，方便追溯 |

## Verdict

**REVISION REQUIRED**

理由：MUST FIX-1（AC-3 grep 窗口同型 bug，v1 漏检）是阻塞型——T-4 改对了 `_seed_bronze` 代码、AC-3 仍判 fail，self_check 会持续误报 → AC-3 永远不能 pass → 流程卡死。必须在 v3 修复后再评。MUST FIX 数：1 → verdict 唯一判据未通过。

v1 全部 7 个 issue 真闭环（实测 dry-run + 文件 diff 复核），修复质量好。v2 引入的新 bug 是 v1 reviewer 视野盲区（修了 AC-1 同型未类比检查 AC-3），下一轮 v3 修完即可通过。

## 复检指引

Generator 修 v3 后自查：

1. **修复 AC-3 grep 窗口缺陷**：在 dev 本机两轮 dry-run：
   ```bash
   # pre-T-4（当前 _seed_bronze 无 uuid 前缀逻辑）
   <新 AC-3 命令>; echo "pre-T-4 exit=$? expect=非0(fail)"

   # 模拟 T-4 实施
   python3 <<'EOF'
   with open('apps/api/tests/test_pipeline_orchestrator.py') as f: lines = f.readlines()
   out = []; inserted = False
   for line in lines:
       if not inserted and 'r_blob = await c.post(' in line:
           indent = line[:len(line)-len(line.lstrip())]
           out.append(f'{indent}unique_content = f"<!-- fixture-uuid {{uuid.uuid4().hex}} -->\\n".encode() + content\n')
           inserted = True
       if 'f"/repos/{owner}/{name}/blobs", content=content' in line:
           line = line.replace('content=content', 'content=unique_content')
       out.append(line)
   open('apps/api/tests/test_pipeline_orchestrator.py', 'w').writelines(out)
   EOF

   <新 AC-3 命令>; echo "post-T-4 exit=$? expect=0(pass)"

   # 还原
   git checkout apps/api/tests/test_pipeline_orchestrator.py
   ```
   两轮都符合预期再写进 spec v3。

2. **spec AC-2 加 alembic current 前置**（SHOULD FIX-1）。

3. **同步 tasks v3 T-6 description AC-3 验证命令**引用新 awk pattern。

4. NICE TO HAVE 两条可选改进，不阻塞 v3 通过。

5. 提交 v3 后开 `spec_review_v3.md` 复检 MUST FIX 状态 + 全部 AC dry-run。
