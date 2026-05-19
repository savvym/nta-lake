# 代码风格规则

本文件覆盖 dataplat 项目的 Python / TypeScript 代码风格底线、注释策略、错误处理、测试与 git 约定。**评审会逐条对照本文件**。

## 0. 共同原则

1. **能用现有抽象就别造新抽象**。三处相似代码 ≠ 必须抽公共函数；先看是否真的有变化轴。
2. **不写预测性代码**。不为"将来可能用到"加参数、加层、加配置项；只为当前 spec 写代码。
3. **不写防御性废话**。框架已保证的不变式不要重复 assert；只在系统边界（用户输入、外部 API、跨网络）校验。
4. **删干净**。不留 `# TODO: removed`、`// 暂时注释`、`unused_var`；不要 _ 前缀掩盖未使用。
5. **不引入运行时秘密**。任何 key / token / 内部 URL **必须**走环境变量 + config 模块，禁止硬编码。

## 1. Python

### 1.1 工具链

- 版本：**Python 3.11+**。
- 包管理：**uv**。任何 `pip install` 都是异常。
- Lint：**ruff**（含 isort）。
- 类型：**mypy --strict**（或至少 `--disallow-untyped-defs`），关键路径全类型。
- 测试：**pytest**，异步代码用 `pytest-asyncio`。
- 数据校验：**Pydantic v2**。

### 1.2 命名

| 元素 | 风格 |
|---|---|
| 模块、变量、函数 | snake_case |
| 类、TypeAlias、Pydantic 模型 | PascalCase |
| 常量 | UPPER_SNAKE_CASE |
| 私有 | 单下划线前缀 `_helper`（不滥用） |
| Pydantic 模型字段 | snake_case；序列化别名用 `Field(alias=...)` |

### 1.3 类型与函数签名

- **公共 API 全类型注解**（路由处理函数、Service 公共方法、Pydantic 模型字段）。
- **不使用 `Any`** 除非真有不可知；用 `Annotated` / `TypedDict` / `Protocol` 替代。
- **不写 `Optional` 默认 None 作"未传"的语义**，明确区分"显式 None"与"未传"时用 `typing.Sentinel` 或 overload。
- **接口设计偏好 Protocol**（参考 design.md §4.1/4.2 的 SourceAdapter/Processor），便于多实现。

### 1.4 异步

- 后端从 Day 1 全异步：路由、Service、DB session 全部 `async def`。
- **禁止在 async 上下文里 sync IO**（`requests.get`、`open().read()` 等）。用 `httpx.AsyncClient` / `aiofiles`。
- SQLAlchemy 强制 **async session**（`AsyncSession` + `async with`），见 design.md §11.7。

### 1.5 错误处理

- 业务错误用项目内自定义异常层级（如 `DataplatError` → `RepositoryNotFound` 等），不直接 raise `Exception`。
- 系统边界（路由）统一 exception handler 转 HTTP 错误码；中间层异常一律向上抛，不要业务代码里 try/except 然后继续静默。
- **禁止 `except: pass`** 与 `except Exception: pass`。如确实要吞，必须 `logger.exception(...)` 并写明原因。

### 1.6 注释

- 默认**不写注释**。命名说不清的现象，先改命名。
- 仅当 WHY 不明显时写一行：隐式约束、绕过特定 bug、与外部规范的对齐点。
- **不写 "这个函数做什么" 类注释**——函数名+签名已经说明。
- **不写跟随当前任务的注释**：`# added for issue #123`、`# used by xxx flow` ——这些放 PR description。
- 公共 API 可以有简短 docstring，写 contract（输入约束、错误条件、副作用），不写实现细节。

### 1.7 测试

- 框架：pytest + pytest-asyncio。
- **改动驱动**：每个本次新增/修改的公共函数或路由必须有直接测试。
- **不允许无条件 mock 核心数据访问层（repository / commit / blob 服务）**——参考 harness 文章经验：mock 让测试通过但生产挂掉。集成测试必须打真实 Postgres + MinIO（测试 docker-compose 起）。
- 允许 mock 的：LLM Gateway 上游 provider、外部第三方 API（Firecrawl、Arxiv）、计时（time.time / asyncio.sleep）。
- 测试组织：与源码镜像目录结构；测试名 `test_<被测对象>_<场景>_<期望>`。
- **不接受空跑测试**：assert 必须有意义，不允许 `assert True`、`assert result is not None` 一行了事。

### 1.8 日志

- 用 `structlog` 或标准 `logging`，**结构化字段**（json formatter 生产用），不写裸字符串拼接。
- 不在循环里逐条 info；要 info 也走采样或汇总。
- 不要把 secret / token / 整条 prompt 写日志，除非显式 audit 模式。

## 2. TypeScript / React

### 2.1 工具链

- 包管理：**pnpm**，workspace。
- 构建：**Vite**。
- Lint：**eslint** + `@typescript-eslint`。
- Format：**prettier**。
- 类型：**TS strict**（`tsconfig` 中 `strict: true`，`noUncheckedIndexedAccess: true`）。
- 测试：**vitest** + **@testing-library/react**。
- 表单：**react-hook-form** + **zod**。

### 2.2 命名

| 元素 | 风格 |
|---|---|
| 组件文件、组件名 | PascalCase（`RepoCard.tsx`） |
| Hook 文件、Hook 名 | camelCase 且 `use` 前缀（`useRepoQuery.ts`） |
| 普通工具函数 | camelCase |
| 常量 | UPPER_SNAKE_CASE |
| 类型/接口 | PascalCase；不要加 `I` 前缀 |

### 2.3 类型

- **不用 `any`**。临时用 `unknown` 然后 narrow，不允许 `any` 进 commit。
- **API 类型一律来自 `@dataplat/api-types`**（OpenAPI 生成），禁止手写后端响应类型。
- 组件 props 用 `type` 不用 `interface`（无继承场景）。

### 2.4 状态与数据获取

- 服务器状态全走 **TanStack Query**。**不要**把后端数据存进 Redux/Zustand。
- 表单状态、局部 UI 状态用 React Hook Form / `useState`。
- 全局非服务器状态尽量避免；真要时用 Zustand，**不引 Redux**。

### 2.5 组件

- 默认 functional + hooks。
- **不写 default export**，统一 named export（除非工具链强制，比如某些 router 文件）。
- shadcn 组件保持原样在 `components/ui/`，业务封装在 `components/<domain>/` 调用 ui。

### 2.6 注释

- 同 Python：默认不写。命名说不清才写。
- 不写 "TODO: 后续优化"。要做就开 task；不做就别提。

### 2.7 测试

- 单测：vitest，组件用 @testing-library。
- 不直接断言 DOM 结构细节（`querySelector('.btn-primary')`），用 `getByRole`/`getByLabelText`。
- API 调用用 MSW mock，**不要 mock fetch 本身**。

## 3. SQL / 数据库

- 迁移用 **Alembic**，所有 schema 变更生成 migration 文件提交。
- **不允许 in-place 修改已合并的 migration**——加新文件，旧的当历史。
- 字段命名 snake_case，主键统一 `id`（UUID 或 bigserial 看实体），外键 `<table>_id`。
- 时间字段必须带时区（`TIMESTAMP WITH TIME ZONE`）；表至少有 `created_at`、`updated_at`。
- **不允许在生产路径用 raw SQL 字符串拼接用户输入**——一律 SQLAlchemy 表达式或参数绑定。

## 4. Git

### 4.0 变更边界

- 一个 change 只在一个 `change/<change-id>` 分支上推进。
- 每个阶段的产物在该阶段 Quality Gate 通过后单独 commit；不要把阶段 1 spec、阶段 3 代码、阶段 5 测试和阶段 8 验证结果揉进同一个 commit。
- 阶段评审优先看 git diff：`git diff <上一阶段commit>...HEAD -- .harness/changes/<change-id>/` 或对应代码目录。
- `summary.md` 的阶段进度必须记录该阶段最新 commit SHA，便于后续 reviewer 精准复核增量。

### 4.1 分支

- 主干：`main`。
- 功能分支：`change/<change-id>`，例如 `change/bootstrap-monorepo-20260516`。
- 新 change 必须通过 `bash scripts/harness_new_change.sh <change-id> [title]` 创建；脚本会复制 `_template/` 并自动 `git switch -c change/<change-id>`。
- **禁止 force push 到 main**。功能分支 force push 须在 PR 评论说明。

### 4.2 Commit message

格式：

```
<type>(<scope>): <subject>

<body, 可选>

<footer, 可选>
```

- `type` 取值：`feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `ci` / `style`。
- `scope`：apps/api、apps/web、worker、plugin-<name>、core、harness、wiki 之一。
- `subject` ≤ 60 字符，命令式现在时（"add" 而非 "added"）。
- body 解释 WHY，不解释 WHAT。
- footer 可放 `Closes change/<id>` 或 `Refs change/<id>`。

### 4.3 PR

- 标题与首条 commit 保持一致风格。
- description 必须链接到对应 `.harness/changes/<id>/summary.md`。
- PR 不接受混合多个 change 的改动。

## 5. LLM 调用

- **禁止在 plugin / processor / 业务代码直接 import provider SDK**（如 `anthropic`、`openai`）。
- **必须**通过 `apps/api/dataplat_api/llm/` 提供的 Gateway 客户端调用（`ctx.llm.call(...)`）。
- 调用必须传：`model`（显式）、`seed`（如 provider 支持）、`temperature`、可选 `cache_key_hint`。
- prompt 模板放 `apps/api/dataplat_api/llm/prompts/<name>.j2`，**不允许**在业务代码中拼字符串构造 prompt。

## 6. 安全与合规底线

1. 不打印 / 记录 secret、access token、用户 password、cookie。
2. JWT 必须 httpOnly + Secure + SameSite=Lax cookie（见 design.md §11.6）。
3. 不在测试 fixture 中放真实生产 token，全用 dummy。
4. 任何接收用户上传文件的入口：限制 size、限制 MIME、扫病毒（Phase 2+）、隔离工作区。
5. SQL / Shell / Path 注入：参数化 / quote / 显式 allowlist；不拼接。

## 7. 性能底线

1. N+1 查询是评审硬性打回项；必须用 join / batch / dataloader 解决。
2. 大列表必虚拟滚动（前端 TanStack Virtual）。
3. 后端列表接口默认分页，page_size 上限平台统一（建议 100），不允许 `limit None`。
4. CAS blob 读写用流式 IO，不要 `bytes = file.read()` 全量加载大对象。
