---
change_id: web-blob-md-image-resolver-20260520
target: coding_report_v1.md
target_version: 1
review_version: 1
reviewer: claude-agent:web-blob-md-image-resolver-20260520-stage4and6-reviewer-v1
reviewed_at: 2026-05-20T00:00:00Z
verdict: REVISION REQUIRED
---

# Code Review v1

## 检查清单结论

| 项 | 结论 |
|---|---|
| resolveImagePath / resolveRelative 算法正确性（3 路径模式） | PASS |
| 绝对 URL 透传 | PASS |
| `/` 起头仓根绝对路径 | PASS |
| `..` 路径解析 | PASS |
| `..` 跳出仓（`../../../etc/passwd`）安全性 | PASS（pop 在空数组无效；路径缩短为 `etc/passwd`，不会逃出仓根，useSubtreeByPath 查询只在仓内树，无路径注入）|
| CustomImage hooks 无条件调用规则 | PASS（commit="" 传入使 enabled=false） |
| commit 缺时降级路径 | PASS |
| SHA256_RE 校验 commit 合法性 | PASS |
| react-markdown 默认不解析 raw HTML | PASS（未引入 rehype-raw） |
| FilesSection commit 来自 commitQuery.data?.hash | PASS |
| renderMinimalMarkdown 完整删除 | PASS（grep 确认文件无此字符串） |
| AC-4 new self_check 反向 grep `! grep "renderMinimalMarkdown"` | PASS |
| **旧 run_repo_files_tab_v2 AC-4 兼容性** | **FAIL（MUST FIX）** |

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST-1 | `scripts/_self_check.sh` line 1609（`run_repo_files_tab_v2` AC-4） | 旧变更 `repo-files-tab-v2-20260518` 的 AC-4 grep 要求 `renderMinimalMarkdown` OR `MarkdownView` OR `MarkdownRendered` 三选一存在（`{ grep -q "renderMinimalMarkdown" ... \|\| grep -q "MarkdownView" ... \|\| grep -q "MarkdownRendered" ... }`）。本 change 完整删除 `renderMinimalMarkdown`，又未加 `MarkdownView`/`MarkdownRendered` 字面量，导致旧 AC-4 在 `run_repo_files_tab_v2`（主路 line 1903/1984 均调用）必然 FAIL。coding_report 声称 `self_check 18/18 PASS`，与此矛盾，要么测试时旧 block 未被执行，要么统计有误。 | 在 `run_repo_files_tab_v2` AC-4 的 grep alternation 里补加 `grep -q "ReactMarkdown"` 作为第四个 OR 分支（`\|\| grep -q "ReactMarkdown" ...`），向前兼容新 renderer；或改成用 `MarkdownRendered` 统一字面量（需两处文件同步）。两者均可，优先前者改动最小。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD-1 | `blob.$owner.$name.$hash.tsx` line 197–208（entry 找不到 + isError 分支） | `isError` 和 "找不到 entry" 两种降级均渲染原 src（可能是 `images/a.jpg` 相对路径）直接作 `<img src>`，在浏览器里会 resolve 成 `/blob/demo/r/images/a.jpg` → 404，且无视觉区分。建议在降级 `<img>` 加 `onError` 隐藏破损图标，或直接不渲染 img 仅显文字提示，避免用户看到破损图片 icon + 提示混合。 | 将 isError / entry 找不到两个分支的降级改为不渲染 `<img>`，仅显示文字说明（类似 isLoading 的 `<span>` 模式）；或保留 img 但加 `style={{display:'none'}}` 仅显文字。 |
| SHOULD-2 | `blob.$owner.$name.$hash.tsx` line 151（`resolved !== null` 判断） | `resolveRelative` 对极端输入 `src = ""` 时，`resolveImagePath("paper.md", "")` 返回 `""` 而非 `null`（空字符串不满足 `isAbsoluteUrl`，不以 `/` 起头），导致 `resolved = ""`、`base = ""`，CustomImage 会执行 `splitDirAndBasename("")` → `["", ""]`，最终在 entries 里找 `name === ""`，逻辑不崩但结果必然找不到 entry，走降级。技术上安全，但最好对 `src === ""` 在 CustomImage 顶部提前 return null（已有 `if (!src) return null`，注意 `src=""` 在 JS 是 falsy）— 其实已处理：`!src` covers empty string。标记为 SHOULD，可不改。 |  对 `src` 为空串的情况无需改动（已有 `!src` guard）；文档化说明即可。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | `blob.$owner.$name.$hash.tsx` line 160–165（`resolveImagePath` 对 `./` 前缀） | `./images/a.jpg` 经 `resolveRelative(dir, "./images/a.jpg")` 正确展开（`.` 段被 skip），但 spec AC-5 及 test 没有显式覆盖 `./` 前缀用例。功能正确，测试可补。 | 在 helper 单测加一条 `./images/a.jpg` 用例（stage 6 已有机会，见 test_review）。 |
| NTH-2 | `blob.$owner.$name.$hash.tsx` TextOrMarkdownBody | 当前在 Rendered mode 下每次渲染 `<ReactMarkdown>` 时，react-markdown 重解析整个 markdown AST。对 >100KB MD 文件（接近 5MB 上限）可能造成渲染卡顿。可用 `useMemo` 缓存 `text` 变化时的解析结果（需 react-markdown ≥9 支持 children memoize）。 | 可 defer 至独立 follow-up change；本变更不阻塞。 |

## Verdict

**REVISION REQUIRED**

MUST-1：旧 `run_repo_files_tab_v2` AC-4 的 grep alternation 未兼容 `ReactMarkdown` 字面量，删除 `renderMinimalMarkdown` 后此 AC 必然 FAIL，与 coding_report 声称的 `18/18 PASS` 矛盾。generator 需修复 `scripts/_self_check.sh` line 1609 的 alternation 并重跑 self_check 确认 PASS。

## 复检指引

Generator 修完后自查命令：

```bash
# 1. 确认旧 AC-4 alternation 已加 ReactMarkdown 分支
grep -n "run_repo_files_tab_v2" scripts/_self_check.sh | head -3
grep -n "renderMinimalMarkdown\|MarkdownView\|MarkdownRendered\|ReactMarkdown" scripts/_self_check.sh | grep 160[0-9]

# 2. 完整跑 self_check（含旧 block）
bash scripts/_self_check.sh run_repo_files_tab_v2 2>&1 | tail -20

# 3. 新 block 验证
bash scripts/_self_check.sh run_web_blob_md_image_resolver 2>&1 | tail -15

# 4. 全量
bash scripts/_self_check.sh all 2>&1 | grep -E "PASS|FAIL|ERROR"
```

MUST-1 关闭判据：`run_repo_files_tab_v2` AC-4 输出 `PASS`，且 `run_web_blob_md_image_resolver` 全 9 AC PASS，`all` 总 FAIL 数 = 0。
