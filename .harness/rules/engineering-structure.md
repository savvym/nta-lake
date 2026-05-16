# 工程结构规则

本文件规定 **dataplat 仓库**的目录约定。任何新建/移动文件之前必须先对照本文件；不符合约定的改动评审会被打回。

设计依据：`.harness/design.md` §11.3 与 §11.4。

## 顶层布局

```
nta-lake/                            # 仓库根（当前目录）
├── CLAUDE.md                        # Claude 会话入口
├── README.md                        # 项目对外说明（待写）
├── Makefile                         # 一键命令入口（待写）
│
├── .harness/                        # 开发过程载体（不要在此放产物代码）
├── wiki/                            # 系统知识库
│
├── apps/
│   ├── api/                         # FastAPI 后端
│   └── web/                         # Vite + React 前端
│
├── packages/
│   ├── core/                        # 后端/SDK/worker 共用的 Pydantic 模型与接口
│   ├── api-types/                   # 由 OpenAPI 生成的 TS 类型（前端依赖）
│   └── sdk-py/                      # 面向用户的 Python SDK
│
├── plugins/                         # 可插拔 adapters / processors
│   ├── adapter-*/
│   └── processor-*/
│
├── worker/                          # Job Runner
│
├── recipes/                         # Pipeline YAML 示例与版本化产物
│
├── docker/
│   ├── docker-compose.dev.yml
│   ├── docker-compose.test.yml
│   └── images/
│       ├── api.Dockerfile
│       ├── worker.Dockerfile
│       └── web.Dockerfile
│
├── scripts/                         # codegen / migrate / seed / openapi 导出
├── docs/                            # 长篇设计文档、ADR 之外的纯文档
│
├── pnpm-workspace.yaml              # JS workspace
├── turbo.json                       # 任务编排
├── pyproject.toml                   # uv workspace 根
├── uv.lock
├── package.json                     # 根 + 共用 dev deps
└── .gitignore
```

> **当前状态**：apps / packages / plugins / worker / recipes / docker / scripts / docs 等目录**尚未创建**。它们将在 `bootstrap-monorepo` 变更中按本结构落地。

## 强约束

1. **`.harness/` 与 `wiki/` 是开发过程目录，不放产物代码**。Python 包/前端组件/SQL 迁移等放对应 apps/packages/plugins/worker 下。
2. **共享代码放 `packages/core/`，不在 apps/ 之间互相 import**。
3. **shadcn/ui 组件直接放 `apps/web/src/components/ui/`，不抽 `packages/ui`**（除非真有第二个前端 app）。
4. **plugin 必须独立成目录、独立打镜像**。不要混在 api/worker 包内。
5. **`packages/api-types` 是单向生成产物**，禁止手写；由 `make codegen` 从 FastAPI OpenAPI 生成。
6. **`recipes/` 中的 pipeline YAML 是版本化资产**，归属团队 owner，不放 ad-hoc 实验。

## 多语言 workspace

- **pnpm workspace** 管 JS（`apps/web` + `packages/api-types` + 根 dev deps）。
- **uv workspace** 管 Python（`apps/api` + `packages/core` + `packages/sdk-py` + `worker` + `plugins/*`）。
- **两套 lockfile 各管各的，不要尝试统一**。
- **Turborepo** 跨语言编排 `make` / `uv run` / `pnpm` 任务，**不引入 Nx**。

## 文件命名

- Python 包：snake_case，包名前缀统一 `dataplat_`（如 `dataplat_api`、`dataplat_worker`）。
- TS 文件：组件 PascalCase（`RepoCard.tsx`），其他 camelCase（`useRepoQuery.ts`）。
- 配置/数据文件：kebab-case（`dataset-card.yaml`、`docker-compose.dev.yml`）。
- 测试：与源文件同目录或 `tests/` 镜像目录，文件名 `test_*.py` / `*.test.ts`。

## 路径敏感约束

- **Tailwind `content`**：`apps/web/tailwind.config.ts` 必须把 `packages/` 中潜在的共享组件目录也纳入扫描（如未来引入）。漏配 = 生产样式丢失。
- **CAS blob 物理路径**：`blobs/{sha256[0:2]}/{sha256}`（与 design.md §5.2 一致），不允许 plugin 直接写入此路径，必须通过 `packages/core` 的 storage 抽象。
- **环境变量**：所有读环境变量的代码集中在 `apps/api/dataplat_api/config.py`（或对应 worker / plugin 的 config 模块），不在业务代码内 `os.environ` 散落。

## 何时新增顶层目录

- 必须经过 ADR：在 `wiki/adr/` 写一份 `adr-NNNN-add-<top-level>.md`，状态 proposed → 评审 → accepted 之后才能落地。
- 仅在以下情况考虑：(a) 多个 apps/packages 都依赖且与现有顶层不属同一关注点；(b) 现有顶层职责已过载。

## 何时新建 package

- `packages/<name>` 的判定：**有 ≥2 个 apps/packages/plugins/worker 共用**。仅一个调用方时不抽包，直接放在调用方内部。
- 创建 package 时必须同步：
  - `pyproject.toml`（Python）或 `package.json`（TS）。
  - 加入对应 workspace 配置。
  - 在 `wiki/architecture.md` 的"模块依赖图"中登记。

## 何时新建 plugin

- 任何新的 Source Adapter 或 Processor → `plugins/adapter-<name>/` 或 `plugins/processor-<name>/`。
- plugin 目录必须包含：
  - `pyproject.toml`（含 `entry_points` 注册到平台）
  - `manifest.yaml`（即使 L1/L2 也写，便于 Phase 2+ 切容器）
  - `src/<package_name>/`
  - `tests/`
  - `README.md`（用途、输入 schema、输出 subtype、示例）
