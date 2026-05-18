---
change_id: <feature-slug>-<yyyymmdd>
version: 1
authored_at: <YYYY-MM-DDTHH:MM:SSZ>
status: waiting_review
---

# Test Report v1

## 验收项 ↔ 测试映射

| AC ID | 测试文件 | 测试函数 |
|---|---|---|
| AC-1 | apps/api/tests/api/test_repos.py | test_create_bronze_repo_returns_201 |
| AC-2 | apps/api/tests/api/test_repos.py | test_commit_blob_dedup_works |

> 每条 AC 必须在表里出现至少一次。

## 测试文件清单

| 文件 | 类型 | 用例数 |
|---|---|---|
| apps/api/tests/api/test_repos.py | 集成 | 6 |
| apps/web/src/components/RepoCard.test.tsx | 单元 | 3 |

## Mock 范围声明

> 允许 mock：LLM provider（用 FakeLLMProvider）、外部 HTTP（msw / respx）、时间。
> 禁止 mock：RepositoryService / BlobStore / LineageService 等数据访问层。

本轮 mock 了：

- _e.g. anthropic provider → 用 FakeLLMProvider 返回 fixture._

## 本地运行结果

```text
$ uv run pytest apps/api -q
.......... 24 passed in 12.34s

$ pnpm --filter web test
 PASS  src/components/RepoCard.test.tsx
 Tests: 3 passed, 3 total
```

## 已知 flaky / 跳过

> 任何 skip 必须显式说明。

- _无_

## 覆盖率（如已配置）

```text
apps/api/dataplat_api/services/repository.py    94%
apps/api/dataplat_api/storage/blob.py            87%
```

> 覆盖率不达标本身**不阻塞**，但低于 60% 的核心模块会被评审标 MUST FIX。

## 下一步

进入阶段 6 单测评审：加载 `.harness/skills/expert-reviewer/SKILL.md`（artifact 模式），写 `unit_test/review/test_review_v1.md`。
