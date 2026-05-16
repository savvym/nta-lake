---
name: unit-test-write
description: 改动驱动的单测编写——基于真实接口与真实数据，覆盖 spec 验收标准
applicable_stage: 阶段 5（单测编写）
inputs:
  - request_analysis/spec.md（验收标准来源）
  - coding/coding_report_v{latest}.md（改动文件清单）
  - 被测代码本身
  - .harness/rules/coding-style.md §1.7（测试规则）
outputs:
  - 测试代码（与改动同 PR）
  - unit_test/test_report_v{N}.md
---

# unit-test-write Skill

## 核心原则

1. **改动驱动**：本次改动的每一个公共函数 / 路由 / 组件，必须有直接测试。
2. **真实接口、真实数据**：核心数据访问层（repo、commit、blob、Lineage 服务）禁用无条件 mock；测试用 docker-compose 起的真实 Postgres + MinIO。
3. **覆盖验收标准**：spec.md 每条验收标准至少映射到一条测试用例。

## 进入条件

- 阶段 4 code_review verdict = APPROVED。
- `summary.md` stage=`unit_test`、status=`in_progress`。
- 测试中间件可用（`make up` 起的 docker-compose 服务正常）。

## 输入

1. 最新 spec.md（关注"验收标准"段）。
2. 最新 coding_report（关注"改动文件列表"）。
3. 被测代码。
4. 已有测试 fixture / factory（`apps/api/tests/conftest.py` 等）。

## 步骤

### 1. 建映射表

在 `test_report_v{N}.md` 的"映射表"段，列出：

```
| spec 验收项 ID | 测试文件 | 测试函数 |
| AC-1           | tests/api/test_repos.py | test_create_bronze_repo_returns_201 |
| AC-2           | tests/api/test_repos.py | test_commit_blob_dedup_works |
```

每条验收项都要有归宿；没归宿的 → 留在本阶段不进入评审。

### 2. 决定测试类型

| 类型 | 何时用 | 工具 |
|---|---|---|
| 单元测试 | 纯函数、模型方法、TS 组件 | pytest / vitest |
| 集成测试 | 路由 + service + DB + 对象存储 | pytest + httpx AsyncClient + 真实 PG/MinIO |
| 端到端 | 跨多个服务（API + worker + plugin） | pytest + docker-compose.test.yml |

**默认偏好集成测试**——能用真实组件就别 mock。

### 3. 写测试

#### Python

- 文件位置：`apps/api/tests/<对应源模块路径>.py`。
- 命名：`test_<被测对象>_<场景>_<期望>`。
- 异步用例必须 `@pytest.mark.asyncio`。
- 用项目 fixture（`async_client`、`db_session`、`s3_client`）；不要自己起 mock。
- 数据用 factory（建议 polyfactory + Pydantic 模型）生成；不要硬编码 UUID/时间字符串。
- 断言精确字段而不是整对象：`assert resp.json()["layer"] == "bronze"` 而不是 `assert resp.json() == {...}`。

#### TS

- 文件位置：与源文件同目录或 `__tests__/`。
- 组件用 `@testing-library/react`，断言 user 视角（getByRole / getByText），不断言 DOM 类名。
- API 调用用 `msw` 拦截，**不要 mock fetch 自身**。

### 4. 处理 LLM 调用

- 测试中调用 LLM Gateway 时：用项目提供的 `FakeLLMProvider` fixture（返回确定 stub）。
- 不允许测试在 CI 上打真实付费 provider。
- 但 Gateway 的 cache / retry 行为本身要有测试，使用 `FakeLLMProvider` + 模拟错误。

### 5. 本地运行

```bash
make up  # 确保中间件起着
uv run pytest apps/api -q
pnpm --filter web test
```

全部 PASS 才能写报告。

### 6. 写 test_report

按 `unit_test/test_report_v{N}.md` 模板填：

- 验收项 ↔ 测试用例映射表
- 测试文件清单 + 用例数
- 本地运行结果（粘 pytest / vitest 输出摘要）
- 已知不稳定 / flaky 测试（必须显式说明，不能默不作声）
- mock 范围声明：本轮 mock 了什么、为什么允许 mock

## 产出

- 新增 / 修改的测试文件（属于代码改动）。
- `unit_test/test_report_v{N}.md`。
- `summary.md` stage=`unit_test`、status=`waiting_review`。

## 质量门禁

```text
test_report_v{latest}.md 存在
spec 每条验收标准在"映射表"中至少出现一次
本地 pytest 总数 > 0
pytest passed == total
pnpm --filter web test passed == total
没有 mock 数据访问层（grep 测试代码: 不能出现对 RepositoryService / BlobStore / LineageService 的 unconditional mock）
没有空跑断言：grep -E "assert\s+True|assert\s+1\s*==\s*1" 结果为空
```

## 失败回退

- 测试发现实现 bug → 回阶段 3 编码（不要在单测里 work around）。
- 必须 mock 数据访问层才能写出测试 → 说明被测代码可测性差，回阶段 3 重构。
- 覆盖 spec 验收项有遗漏且改不动代码 → 回阶段 1 修 spec 或拆 change。

## 反模式

- 写完代码再补"应付门禁"的薄壳测试。
- 一行代码改动配 30 行 mock setup 才能"测试"。
- 测试断言整个响应 JSON，导致字段无关变动也挂。
- 测试名 `test_xxx_1`、`test_works`、`test_ok`。
- 把 flaky 测试 skip 掉而不修。
