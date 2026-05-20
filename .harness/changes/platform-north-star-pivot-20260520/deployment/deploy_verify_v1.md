---
change_id: platform-north-star-pivot-20260520
version: 1
env: n/a (doc-only)
deployed_at: 2026-05-20T16:30:00Z
verifier: application-owner-agent
status: PASS
---

# Deploy Verify v1 (n/a)

## 部署？

纯文档 / 治理 change，**无业务代码改动**：

```
$ git diff --stat main~1...main | tail -5
 .harness/design.md                                 | 350 +++++++++++++++
 .harness/rules/data-not-code-pivot.md              | 100 +++
 CLAUDE.md                                          |   2 +
 scripts/lint/check_design_north_star.sh            | 100 +++
 scripts/_self_check.sh                             |  44 ++
```

5 个文件：design.md / rule / CLAUDE.md / lint 脚本 / self_check。**无 .py / .ts / .tsx 改动**，无需重启 uvicorn / vite / worker。

## 验证：本 change 的"运行时"行为

文档 change 的"deploy" = "新 rule 被后续 change reviewer 真的引用"。这个验证留给下一个 change（`api-snapshot-rename-*` 或 `operator-protocol-*`）的 stage 2 reviewer 在其 review 报告里**显式 check `.harness/rules/data-not-code-pivot.md`** 完成。

本 change 自身的验证已经完成（stage 8 CI 10/10 PASS）。

## 后续指引

stage 10 用户确认。
