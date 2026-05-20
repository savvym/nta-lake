---
change_id: web-pdf-mineru-ui-v2-20260520
phase: implementation
status: <in_progress | done>
authored_at: <YYYY-MM-DDTHH:MM:SSZ>
author: sonnet-phase2-implementer
model_used: sonnet
branch: change/web-pdf-mineru-ui-v2-20260520
base_commit: d706fd1
head_commit: <sonnet push 后回填>
pr_url: <gh pr URL 或 "n/a (gh PAT 缺 pr:write)">
---

# Implementation

> Phase 2 sonnet 端到端产物。**一次 sonnet 调用内**完成：编码 + 单元测试 + 端到端验证 + commit + push（+ PR 如可用）。Application Owner spawn sonnet 后 sonnet 自管完整 Phase 2，结束写本文件。

## 改动文件清单

执行 `git diff --name-only main...HEAD`，列在这里：

| 路径 | 类型 (new/edit/delete/rename) | 一句话说明 | 关联 task |
|---|---|---|---|
| <path> | <type> | <说明> | T-1 |

> **门禁**：本表必须与 `git diff --name-only main...HEAD` 完全一致。

## 任务完成情况

对照 design.md § 任务清单：

| Task | 状态 | commit | 备注 |
|---|---|---|---|
| T-1 | done / partial / deferred | <sha> | <如 partial / deferred 必填理由> |

## 测试通过证据

### 单元测试

```text
$ uv run pytest tests/test_xxx.py
============================== N passed in M.Ms ==============================

$ pnpm --filter web test
   Test Files  N passed
        Tests  M passed
```

### 自检 AC block

```text
$ bash scripts/_self_check.sh <change-id>
=== <change-id> :: N AC ===
PASS  AC-1  ...
PASS  AC-2  ...
...
PASS: N / FAIL: 0 / SKIP: 0
全部通过
```

### 端到端验证

> 如涉及 API：curl 真打一次新端点  
> 如涉及 UI：vite dev server 起来 / build 不挂 / 关键页面 smoke  
> 如涉及 CLI：跑一次实际命令

```text
$ curl -H "Cookie: ..." http://localhost:8080/api/new-endpoint
{"ok": true, ...}

$ pnpm --filter web build
✓ built in N.Ns
```

## 偏离 design.md（如有）

> 凡未在 design.md 声明的偏离，**全部**列在这里。Phase 3 reviewer 把"未声明的隐式偏离"算 MUST FIX。

| # | 偏离点 | 原因 | 评审请关注 |
|---|---|---|---|
| D-1 | <e.g. 改用 folder routing 不是 spec 写的 flat dot 形态> | <技术原因> | <reviewer 是否接受> |

## 跨 change / 上游回归

- 全 web vitest：N/N PASS（M files）
- 全 pytest 本 module：N/N PASS
- self_check full（如已跑）：PASS 总 / FAIL 总 / FAIL 列表 + 标 pre-existing 或本 change 引入

## PR 描述（用于 gh pr create body）

```markdown
## Summary
<1-3 bullets>

## Test plan
- [ ] <bullet>
- [ ] <bullet>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验 PR。
