# dataplat

> LLM 训练数据管理平台：Bronze → Silver → Gold 三层数据加工流水线 / 类 Git CAS 版本控制 / 可插拔 Adapter & Processor / 统一 LLM 网关。

完整设计：[.harness/design.md](.harness/design.md)。
开发流程：[.harness/agents/application-owner.md](.harness/agents/application-owner.md)。

## 快速开始 / Quickstart

```bash
# 1. 装语言工具（已装可跳）
curl -LsSf https://astral.sh/uv/install.sh | sh
curl -fsSL https://get.pnpm.io/install.sh | sh

# 2. 装依赖
make install

# 3. 起本地中间件（postgres / minio / redis）
make up

# 4. 三个终端各起一个进程
make api      # FastAPI on :8080
make web      # Vite dev on :5173
make worker   # job runner

# 5. 浏览器打开 http://localhost:5173
# 6. curl http://localhost:8080/healthz
```

## 目录结构

```
nta-lake/
├── apps/
│   ├── api/                FastAPI 后端
│   └── web/                Vite + React 前端
├── packages/
│   ├── core/               后端 / SDK / worker 共用 Pydantic 与接口
│   ├── api-types/          OpenAPI 生成的 TS 类型（单向产物）
│   └── sdk-py/             用户侧 Python SDK
├── plugins/                可插拔 adapters / processors
├── worker/                 Job runner
├── recipes/                Pipeline YAML
├── docker/                 docker-compose + Dockerfile
├── scripts/                codegen / migrate / seed
├── docs/                   长篇文档
├── .harness/               开发流程与变更档案
└── wiki/                   架构 / 术语 / ADR
```

## 工程基线

| 维度 | 选型 |
|---|---|
| Python | 3.11+ / uv / FastAPI / SQLAlchemy 2.0 async / Pydantic v2 / pytest |
| TS | Node 20+ / pnpm / Vite / React 18 / TanStack Router & Query / shadcn/ui |
| 多语言 monorepo | uv workspace + pnpm workspace + Turborepo |
| 中间件（dev）| Postgres 16 / MinIO / Redis 7 |
| 任务队列（MVP）| RQ |
| LLM | 统一 Gateway（详见 design.md §4.5） |
| 认证（MVP）| argon2 + JWT httpOnly cookie |

## 贡献流程

**所有改动必须挂在 `.harness/changes/<feature-slug>-<yyyymmdd>/` 下，按十阶段流程推进**。
详见 [.harness/rules/development-process.md](.harness/rules/development-process.md)。

## License

Internal / TBD.
