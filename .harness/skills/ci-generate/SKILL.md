---
name: ci-generate
description: 生成或维护 CI 配置（GitHub Actions），让阶段 8 的门禁可被机械化验证
applicable_stage: 支援型（CI 配置专门变更或新增项目时触发）
inputs:
  - 现有 .github/workflows/（如有）
  - 项目语言栈与子项目结构
  - .harness/rules/development-process.md §阶段 8 门禁要求
outputs:
  - .github/workflows/*.yml（新增或修改）
  - 配套的 codegen 校验脚本（如 make codegen）
---

# ci-generate Skill

## 进入条件

> 本 Skill 是**支援型**，不在十阶段主流程内自动触发。出现以下任一情形时显式加载：

- 项目从零搭 CI（如 `bootstrap-monorepo` 变更内）。
- 现有 CI 不能产出阶段 8 要求的结构化字段（status / total_tests / passed_tests）。
- 增加新子项目（新 plugin / 新 package）需要单独 job。
- CI 跑得太慢需要拆分 / 加缓存。
- 主流程阶段 8 多次回退指向"CI 配置 bug"——开独立子变更走本 Skill。

## 目标产出（最小可用 CI）

### 1. `ci.yml`：PR + main push 触发

包含以下 job：

| Job | 用途 | 必要产物 |
|---|---|---|
| `python-lint-type` | ruff + mypy | 终止于失败 |
| `python-test` | uv run pytest --junitxml=… | junit XML artifact |
| `web-lint-type` | pnpm lint + tsc --noEmit | 终止于失败 |
| `web-test` | pnpm test --reporter=junit | junit XML artifact |
| `codegen-check` | make codegen && git diff --exit-code | 终止于失败 |
| `docker-build` | api / web / worker / plugins 镜像构建（不 push） | 镜像 tag 输出 |

### 2. `release.yml`：tag / main 触发

镜像 build + push 到 registry；前端 dist 上传 CDN。**MVP 可后置**。

### 3. 关键配置约束

- **uv 缓存**：`actions/cache` 缓存 `.venv` 与 `uv.lock`。
- **pnpm 缓存**：`actions/setup-node` 自带 pnpm store cache。
- **docker layer 缓存**：用 buildx + gha cache。
- **并发**：同分支重叠 push 自动 cancel-in-progress。
- **artifact**：junit XML 必须 upload-artifact，retention 至少 7 天，供阶段 8 收集。
- **secrets**：所有 token / registry 凭证走 GitHub Secrets，不允许在 workflow yaml 明文。

## 步骤

### 1. 盘点子项目

- 列出当前所有可独立 lint / test 的 unit（apps/api、apps/web、worker、plugins/*、packages/*）。
- 决定每个 unit 是单独 job 还是合并 job（plugin 数量多时建议 matrix）。

### 2. 写 workflow

最小骨架（示例片段，落地时按实际目录调整）：

```yaml
name: ci
on:
  pull_request:
  push:
    branches: [main]
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  python-lint-type:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --all-extras
      - run: uv run ruff check apps/api packages worker plugins
      - run: uv run mypy apps/api/dataplat_api packages/core
  python-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env: { POSTGRES_PASSWORD: postgres }
        ports: ['5432:5432']
      minio:
        image: minio/minio
        ports: ['9000:9000']
        options: --health-cmd="curl -f localhost:9000/minio/health/live"
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --all-extras
      - run: uv run pytest apps/api --junitxml=junit-api.xml
      - uses: actions/upload-artifact@v4
        with: { name: junit-api, path: junit-api.xml }
  codegen-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make codegen
      - run: git diff --exit-code
```

### 3. 确认门禁可机械化抓取

阶段 8 的判定需要：

```text
status: SUCCESS | FAILURE
total_tests / passed_tests / failed_tests / skipped_tests
```

CI 配置必须保证：

- 每个 test job 输出 junit XML 作为 artifact。
- `unit-test-ci` Skill 能通过 `gh run download` 拉到 XML 解析。

不要靠 grep stdout 凑数。

### 4. 验证

- 在功能分支推一次空 commit，看所有 job 是否触发。
- 故意制造 1 个测试失败，确认 CI 标红 + junit 中 failed_tests=1。
- 删掉 failed_tests，确认绿。

### 5. 文档

- 把 CI 行为记入 `wiki/architecture.md` 的 "CI / Release" 章节。
- 在 `.harness/changes/<id>/summary.md` 关联到 CI 文件路径。

## 产出

- `.github/workflows/<file>.yml` 新增或修改。
- 配套脚本（如 `scripts/export_openapi.py` 与 `Makefile` 的 codegen 目标）。
- `wiki/architecture.md` 的 CI 章节更新。

## 质量门禁

```text
ci.yml 存在
所有 job 在 PR 分支上能触发
test job 产出 junit XML artifact
codegen-check job 存在且能阻塞类型漂移
concurrency.cancel-in-progress: true 已配置
secrets 在 workflow 中没有明文
```

## 失败回退

- CI workflow 在 PR 分支无法触发（路径/事件配错） → 留在本 Skill 修配置；不要绕道用 `workflow_dispatch` 充数。
- 验证用的"故意制造失败"步骤显示绿，说明门禁判定逻辑有 bug（如 grep 而非 junit）→ 留在本 Skill 修；不要"差不多就行"。
- 镜像 build 需要的 registry credentials 缺失 → 暂停本 Skill，先走运维拿 secret；不要把 token 提交到分支。
- 缓存命中导致测试假绿（旧 cache 不清理） → 在 workflow 加上 cache key 含 lockfile hash；如已发生回到 stage 5 重写测试用例。
- 触发到本 Skill 是因为主流程阶段 8 失败 → 修完 CI 配置后，回到原变更的阶段 8 重跑；不要把 CI 修复与原变更代码混在一个 PR。

## 反模式

- 把 build / test 全塞一个超长 job，失败定位困难。
- 不产出 junit，让阶段 8 的门禁只能靠 stdout grep。
- 漏配 `cancel-in-progress`，分支多次推送排队耗资源。
- 把 token 写进 yaml 明文。
- CI 通过条件是"job 都跑完了"而不是"测试都通过了"——subtle 但致命。
