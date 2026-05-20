---
change_id: web-jobs-list-page-20260520
target: spec.md
target_version: 2
review_version: 2
reviewer: claude-agent:web-jobs-list-page-20260520-stage2-reviewer-v2
reviewed_at: 2026-05-20T14:00:00Z
verdict: REVISION REQUIRED
---

# Spec Review v2

## v1 MUST FIX 复检

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| MUST FIX-1 | AC-3 grep 与 T-3 路由 path 不一致（AC-3 grep `"/"` vs T-3 `""`） | **RESOLVED** | spec v2 AC-3 grep 改为 `'@router\.get\(\s*[\"\x27][\"\x27]\s*[,)]'`（匹配空字符串），T-3 统一写 `@router.get("")`；两者一致 |

## v1 SHOULD FIX 复检

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| SHOULD FIX-1 | 非范围未明确"不往 JobORM 加任何新列" | **RESOLVED** | spec v2 §非范围第 1 条补了"不加 JobORM 任何新列（含 owner_id / cancel_reason / retry_count 等）" |
| SHOULD FIX-2 | AC-3 仅校验函数存在 + require_admin，未验证 400 白名单守门行为 | **PARTIAL** | T-4 用例 (e) 已升为必选（400 测试），但 spec AC-8 表描述仍写"≥ 4"，AC-8 完整命令末尾也是 `[ ... -ge 4 ]`；T-4 升为 ≥5 的意图未同步回 spec AC-8（见 MUST FIX-1 下方） |
| SHOULD FIX-3 | §跨链路自审 第 6 条描述与 T-3 `""` 矛盾 | **NOT RESOLVED** | spec v2 §跨链路自审第 6 条仍写"✅ AC-3 grep 精确（含 @router.get 锚定 path **"/"**）"——v2 已选 `""` 但自审条目仍写 `"/"`，文字错误未修 |

## 检查清单结论

| 条目 | 状态 | 说明 |
|---|---|---|
| 背景写明了为什么现在做 | PASS | 现状/用户痛点/用户选定三段清晰 |
| 问题陈述与目标可被外部读者理解 | PASS | 5 个问题点逐条列出 |
| 范围 / 非范围都有 | PASS | 非范围已补 JobORM 新列约束 |
| 验收标准每条都可演示且可机械化 | PARTIAL | AC-3 grep 已修一致；AC-8 count 与 T-4 不一致（见 MUST FIX-1） |
| 风险有缓解措施或显式 accept | PASS | 风险表 7 行均有缓解 |
| 没有把已有架构当新提案重复 | PASS | 未重复 design.md |
| AC 表存在 `kind` 列 | PASS | 含 kind 列 |
| 至少 1 行 AC kind=behavioral | PASS | AC-7 / AC-8 均为 behavioral |
| ac_kind_lint 非 exempt | PASS | frontmatter 无 exempt |

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | spec.md AC-8 描述 + AC-8 完整命令 | **AC-8 count 与 T-4 不一致**：v2 把 T-4 (e) "status=invalid → 400" 从可选改为必选，T-4 用例下限升为 ≥ 5；但 spec AC-8 表描述仍写"≥ 4 + 全 PASS（admin / user 403 / 过滤 / 分页）"，AC-8 完整命令末尾校验也是 `[ ... -ge 4 ]`。v2 意图已写入 revision_notes 但未落地到 spec 正文，导致 self_check 校验用 `-ge 4` 实际无法保证 (e) 用例存在，守门形同虚设。 | 将 AC-8 表描述改为"≥ 5 + 全 PASS（admin / user 403 / 过滤 / 分页 / invalid status → 400）"；将 AC-8 完整命令末尾 `-ge 4` 改为 `-ge 5` |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | spec.md §跨链路自审 第 6 条 | 自审第 6 条仍写"含 @router.get 锚定 path `"/"`"，与已选择的 `""` 矛盾；读者看到此处会误认为路径又改回 `"/"`。这是 v1 SHOULD FIX-3 未关闭。 | 改为"✅ AC-3 grep 精确（匹配 @router.get 空字符串路径 `""`，拼 prefix=/jobs = `/jobs`）" |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | spec.md AC-8 完整命令（v1 NTH-1 未处理） | `grep -cE ... || true` 修法未落地——原命令无 `|| true`，若测试文件仅含 3 个 `test_jobs_list.py::` 匹配行，`[ ... -ge 4 ]` 会 FAIL 但不反映真实测试执行结果。此 bug 在 v2 修为 `-ge 5` 时仍存在。 | 在 `grep -cE 'test_jobs_list\.py::'` 后加 `\|\| true` 防止 0 命中使整条命令提前 exit 1 |
| NTH-2 | spec.md AC-5 描述（v1 NTH-2 未处理） | started_at/completed_at 为 null 时"用时"无法计算；UI null guard 未在 spec 说明。 | AC-5 中补"当 started_at 或 completed_at 为 null 时显示 —" |

## Verdict

**REVISION REQUIRED**

存在 1 个未关闭 MUST FIX：AC-8 在 spec 正文中的 count 下限（≥ 4）与 T-4 已升级的下限（≥ 5）不一致，revision_notes 记录了意图但未修正 spec 正文。该不一致会导致 self_check 用宽松门禁（-ge 4）误放过缺少"invalid status → 400"测试的实现。

另有 v1 SHOULD FIX-3（自审第 6 条 path 描述）仍未关闭，降级为本轮 SHOULD FIX。

## 后续指引

Generator 修 spec v3 时：

1. **MUST FIX-1（阻塞）**：
   - AC-8 表描述：改"≥ 4"→"≥ 5"，括号内补"/ invalid status → 400"
   - AC-8 完整命令末尾：`-ge 4` → `-ge 5`

2. **SHOULD FIX-1（强烈建议）**：
   - §跨链路自审第 6 条：删"path `"/"`"，改为"path `""`（空字符串）"

3. 自查命令：
   ```bash
   # 确认 AC-8 count 已升为 5
   grep "AC-8" .harness/changes/web-jobs-list-page-20260520/request_analysis/spec.md | grep -E "≥ [0-9]+"
   # 确认命令末尾 -ge 5
   grep "\-ge" .harness/changes/web-jobs-list-page-20260520/request_analysis/spec.md
   # 确认自审第 6 条已修正
   grep -A1 "6\." .harness/changes/web-jobs-list-page-20260520/request_analysis/spec.md | grep "AC-3"
   ```
