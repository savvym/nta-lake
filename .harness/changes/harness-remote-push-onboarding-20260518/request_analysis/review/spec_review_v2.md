---
change_id: harness-remote-push-onboarding-20260518
target: spec.md
target_version: 2
review_version: 2
prior_review: request_analysis/review/spec_review_v1.md
reviewer: claude-agent:harness-remote-push-onboarding-20260518-stage2-reviewer-v2
reviewed_at: 2026-05-19T00:30:00Z
verdict: APPROVED
must_fix_count: 0
should_fix_count: 0
nice_to_have_count: 0
---

# Spec Review v2

> 评审者声明：本 reviewer 是独立 sub-agent（claude-sonnet-4-6），未参与本 change spec/tasks 撰写。本次是复检导向评审（不全量重评），仅核 v1 MUST FIX / SHOULD FIX 闭环 + 检 v2 新引入 bug。本次模型：**sonnet**（claude-sonnet-4-6），符合 reviewer-agent.md §8 默认规约。

---

## v1 MUST FIX 复检

| # | v1 问题 | v2 状态 | 证据 |
|---|---|---|---|
| MUST FIX-1 | spec.md AC-8 `tail -3 \| grep -q "FAIL: 0"` 假阴性 | **CLOSED** | spec_v2 L92：AC-8 验证方式改为 `bash scripts/_self_check.sh 2>&1 \| tee /tmp/dataplat-selfcheck-all.log >/dev/null; grep -qE "^FAIL: 0\$" /tmp/dataplat-selfcheck-all.log`；`grep -n "tail -3" spec.md`（在 AC 表格中）= 仅出现在 L18 闭环说明行，不在实际验证命令中，AC-8 验证命令本身无 `tail -3` |

实跑验证（SKIP > 0 反例）：

```bash
bash -c 'printf "PASS: 25\nFAIL: 0\nSKIP: 23\n跳过详情: ...\n... 不可访问\n" > /tmp/test-log.log; grep -qE "^FAIL: 0$" /tmp/test-log.log; echo "exit=$?"'
# 输出：exit=0
```

exit=0 确认：即便 SKIP 行和额外行在 "FAIL: 0" 之后，`grep -qE "^FAIL: 0$"` 仍正确命中。MUST FIX-1 **真闭环**。

---

## v1 SHOULD FIX 复检

| # | v1 问题 | v2 状态 | 证据 |
|---|---|---|---|
| SHOULD FIX-1 | tasks T-3 含 "无 remote 项目时跳过" + `git@github.com:savvym/nta-lake.git` 字面 URL | **CLOSED** | `grep -nE "savvym\|无 remote 项目时跳过" tasks_v2.md` = 0 行（实跑确认）；T-3 description 改为通用形式：`§产出物 加 "git push origin main"` + 附注"rules 是项目通用文档，不写具体 remote URL" |
| SHOULD FIX-2 | spec AC-4 未明示"防回归断言"语义 | **CLOSED** | spec_v2 L88 AC-4 描述：`防回归断言：全文不含 "无 remote 长期未决"（既有 stage 8 已无此措辞；本断言确保未来不重新引入）`；语义明确，coding 阶段不会误解为"寻找并替换已有字符串" |

---

## stage 2 AC kind 必查 3 项（v2 不能回退）

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 1 | AC 表存在 `kind` 列 | PASS | `awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' spec_v2.md \| grep -qE '^\|[^|]*\|[[:space:]]*kind[[:space:]]*\|'` 命中（实跑 exit=0）|
| 2 | 至少 1 行 AC kind=`behavioral`（锚定 AC 行 regex）| PASS | AC-8 `**behavioral**`；锚定 regex `^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|` 命中（实跑 exit=0）|
| 3 | frontmatter 是否声明 `ac_kind_lint: exempt` | N/A | spec_v2 frontmatter 无 `ac_kind_lint: exempt`，无需 git diff 校验 |

三项全 PASS，AC 分层规约硬约束未回退。

---

## v2 新 bug 检查

### 1. AC-8 `\$` 转义语义验证

spec_v2 AC-8 验证命令（markdown 表格内）：

```
grep -qE "^FAIL: 0\$" /tmp/dataplat-selfcheck-all.log
```

`\$` 是 markdown 表格列分隔符转义（`|` → `\|`）后，`$` 本身**不需要**特殊转义。分析：

- markdown 表格内反引号代码块：`\|` 是表格转义，渲染/复制后为 `|`（pipe）
- `\$` 中的 `\` 在 ERE 中：`\$` = 字面 `$`，与 `$`（行末锚定）在 ERE 行为等价（均匹配行末）
- 实跑确认：`bash -c 'grep -qE "^FAIL: 0\$" /tmp/dataplat-selfcheck-all.log && echo PASS || echo FAIL'` → PASS

结论：**无 bug**，`\$` 在 shell + ERE 上下文均正确工作。

### 2. tee 方案语义正确性

AC-8 命令链：`bash scripts/_self_check.sh 2>&1 | tee /tmp/dataplat-selfcheck-all.log >/dev/null; grep -qE "^FAIL: 0\$" /tmp/dataplat-selfcheck-all.log`

- `tee` 将 stdout+stderr 写入 log 文件，同时 `>/dev/null` 避免终端刷屏
- `;` 分隔两条命令，`grep` 在 `tee` 结束后读 log 文件（非管道，无缓冲问题）
- `grep -qE "^FAIL: 0$"` 全文搜索，不受 SKIP 行数影响

结论：**无 bug**，tee 方案语义完全正确。

### 3. v2 闭环说明表（L14-22）重复 "## 背景" 标题

spec_v2 L26-27 存在 `## 背景\n\n## 背景` 重复标题（两个 `## 背景`）。这是 markdown 文档格式问题，不影响验收标准的可执行性，也不影响 coding 实现。

结论：**NICE TO HAVE**（不阻塞），不升级为 MUST FIX。

---

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-1 | spec_v2.md L26-27 | `## 背景` 标题重复出现两次（L25 和 L27），markdown 文档冗余 | 删除其中一个重复的 `## 背景` 行；不影响可执行性，可在 coding 阶段顺手清理 |

---

## Verdict

**APPROVED**

理由：

1. **MUST FIX-1 真闭环**：AC-8 验证命令已去掉 `tail -3`，改为 `tee /tmp/...log >/dev/null; grep -qE "^FAIL: 0\$"` 方案，实跑 SKIP > 0 反例 exit=0 确认。
2. **SHOULD FIX-1 真闭环**：tasks_v2 T-3 无 "savvym" URL / 无 "无 remote 项目时跳过"，实跑 `grep -nE "savvym|无 remote 项目时跳过" tasks_v2.md` = 0 行。
3. **SHOULD FIX-2 真闭环**：spec_v2 AC-4 含"防回归断言"语义明文，语义无歧义。
4. **AC kind 必查 3 项全 PASS**，未回退。
5. **v2 无新引入 MUST/SHOULD 级 bug**：`\$` 转义语义正确；tee 方案语义完整；唯一发现为 NICE TO HAVE 级重复标题。

spec_v2 可进入 stage 3（coding）。

---

## 后续指引

```bash
# 开始 coding 前自查（确认 v2 spec AC 仍正确）：
cd /data/home/zhhdzhang/nta/nta-lake/.claude/worktrees/harness-remote-push

SPEC=.harness/changes/harness-remote-push-onboarding-20260518/request_analysis/spec.md

# AC-8 验证命令不含 tail -3（仅 AC 表格中不含，闭环表不算）
grep -n "tail -3" "$SPEC"
# 期望：仅 L18（闭环说明行），不在 L92 AC 表格验证命令中

# 验证 kind 分层完整
awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' "$SPEC" \
  | grep -qE '^\|[^|]*\|[[:space:]]*kind[[:space:]]*\|' && echo "kind col OK"
awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' "$SPEC" \
  | grep -qE '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|' && echo "behavioral row OK"
```

---

## 本次用模型

**sonnet**（claude-sonnet-4-6）。符合 reviewer-agent.md §8 默认规约。本次主要工作为复检导向：实跑 AC-8 SKIP > 0 反例 + `\$` 转义语义验证 + tee 方案语义分析 + `grep -nE "savvym|无 remote 项目时跳过"` 零行验证，sonnet 完全胜任。
