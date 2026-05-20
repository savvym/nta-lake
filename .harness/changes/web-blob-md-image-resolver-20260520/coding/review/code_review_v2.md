---
change_id: web-blob-md-image-resolver-20260520
target: coding_report_v1.md
target_version: 1
review_version: 2
reviewer: claude-agent:web-blob-md-image-resolver-20260520-stage4and6-reviewer-v2
reviewed_at: 2026-05-20T14:00:00Z
verdict: APPROVED
---

# Code Review v2

## v1 MUST FIX 复检

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| MUST-1 | `scripts/_self_check.sh` line 1609：`run_repo_files_tab_v2` AC-4 alternation 缺 `ReactMarkdown` 第四分支，删除 `renderMinimalMarkdown` 后必然 FAIL | **RESOLVED** | `grep -n "ReactMarkdown" scripts/_self_check.sh` 确认 line 1609 已加 `\|\| grep -q "ReactMarkdown" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx`；`bash scripts/_self_check.sh repo-files-tab-v2` 实跑输出：AC-4 PASS（7/8 PASS，唯一 FAIL 为 AC-7 pytest blob_meta，需 PG/MinIO/Redis 基础设施，`run_ac_skipif_no_pg_minio_redis` 标记，与本 change 无关，属预存 skip-when-infra-absent 设计）。 |

## 检查清单结论

| 项 | 结论 |
|---|---|
| MUST-1 fix 的正确性：alternation 语法 | PASS — `\|\| grep -q "ReactMarkdown" ...` 语法与前三分支一致，bash -c 单引号作用域无转义问题 |
| `run_web_blob_md_image_resolver` 9 AC 全 PASS | PASS — `bash scripts/_self_check.sh web-blob-md-image-resolver` 输出 `PASS: 9 / FAIL: 0` |
| `run_repo_files_tab_v2` AC-4 向前兼容 | PASS — 同上实跑确认 |
| `run_repo_files_tab_v2` AC-7（pytest blob_meta）FAIL | 预存 infra-absent SKIP/FAIL；`run_ac_skipif_no_pg_minio_redis` 包裹；与本 change 无关；不记为新引入回归 |
| v2 引入新回归 | PASS（无新回归）— alternation 仅新增第四 OR 分支，不修改已存在的三分支；其他文件未改动 |
| v1 SHOULD-1/2 处理情况 | 见 test_review_v2；code review 侧无需复核 |

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1（继承 v1 NTH-2）| `blob.$owner.$name.$hash.tsx` TextOrMarkdownBody | 大 MD 文件每次重渲染 ReactMarkdown 重解析全 AST；可用 `useMemo` 缓存 | defer 至独立 follow-up；不阻本变更 |

注：v1 NTH-1（`./` 前缀覆盖缺测）在 test_review_v2 NTH 层继续跟进，code 侧功能实现正确，无需在此重列。

## Verdict

**APPROVED**

v1 唯一 MUST FIX（scripts/_self_check.sh line 1609 alternation 缺 `ReactMarkdown` 第四分支）已准确修复，`bash scripts/_self_check.sh repo-files-tab-v2` AC-4 实跑 PASS；`web-blob-md-image-resolver` 9/9 PASS；无新引入回归。SHOULD/NICE 问题无变化，交 test review 处理。

## 复检指引（已执行，供存档）

```bash
# 1. 确认 alternation 已加 ReactMarkdown
grep -n "ReactMarkdown" scripts/_self_check.sh | grep 1609
# → 输出含 grep -q "ReactMarkdown"

# 2. 旧 block 实跑
bash scripts/_self_check.sh repo-files-tab-v2 2>&1 | grep "AC-4"
# → PASS  AC-4  blob.$owner.$name.$hash.tsx 存在 + ...

# 3. 新 block 实跑
bash scripts/_self_check.sh web-blob-md-image-resolver 2>&1 | tail -5
# → PASS: 9 / FAIL: 0 / SKIP: 0
```
