# 架构总览

> 本文件描述 **dataplat 系统当前真实长什么样**。设计蓝图见 [.harness/design.md](../.harness/design.md)。
>
> **当前状态：Phase 0**——仅 `.harness/` 与 `wiki/` 骨架存在；代码尚未开始。本文件先把"我们将要长成的样子"按 design.md 摘要写下，**等真实代码落地后**由 `project-analysis` Skill 持续刷新。
>
> 在此之前，本文件标记的所有模块都属于"计划态"，不是"现状"。

## 1. 顶层组件

参考 design.md §5.1：

```
              ┌──────────────────────────────────────┐
              │            Web UI (HF-like)          │
              └──────────────────────────────────────┘
                                │
              ┌──────────────────────────────────────┐
              │   API Gateway  (REST / gRPC, AuthN)  │
              └──────────────────────────────────────┘
                │              │              │
      ┌─────────▼──┐    ┌──────▼──────┐   ┌───▼─────────┐
      │ Catalog &  │    │ Orchestrator│   │  Lineage    │
      │ Repo API   │    │ (pipelines) │   │  Service    │
      └─────┬──────┘    └──────┬──────┘   └───┬─────────┘
            │                  │              │
            ▼                  ▼              ▼
      ┌──────────────┐   ┌───────────────┐  ┌────────────┐
      │  PostgreSQL  │   │ Object Store  │  │  Lineage   │
      │ (metadata)   │   │ (S3 / MinIO)  │  │ Graph DB   │
      └──────────────┘   └───────────────┘  └────────────┘

              ┌──────────────────────────────────────┐
              │           LLM Gateway                │
              └──────────────────────────────────────┘
```

## 2. 仓库目录与模块映射

按 design.md §11.3 的 monorepo 落地：

| 顶层目录 | 角色 | 状态 |
|---|---|---|
| `apps/api` | FastAPI 后端：Catalog / Repo API / Orchestrator / Lineage / LLM Gateway | 计划 |
| `apps/web` | Vite + React 前端 | 计划 |
| `packages/core` | 共享 Pydantic 模型与接口协议（SourceAdapter / Processor / RunContext） | 计划 |
| `packages/api-types` | 由 OpenAPI 生成的 TS 类型 | 计划 |
| `packages/sdk-py` | 用户侧 Python SDK | 计划 |
| `plugins/` | Source Adapters / Processors | 计划 |
| `worker/` | Job Runner，消费 RQ 队列、subprocess 启动 plugin | 计划 |
| `recipes/` | Pipeline YAML 示例与版本化产物 | 计划 |
| `docker/` | dev/test docker-compose + 镜像 Dockerfile | 计划 |

## 3. 关键链路（计划态）

### 3.1 资产录入（Bronze 写入）

```
HTTP POST /repos/<owner>/<name>/commits
  → routers/repos.commit
  → services/commit.create
      → 调 adapter 拉/写文件到 workspace
      → storage/blob.put_many (sha256 寻址，去重)
      → services/tree.build_tree
      → models/commit.insert
      → services/lineage.record(produced_by=adapter, inputs=[])
  → 200 + commit_hash
```

### 3.2 Pipeline 执行

```
HTTP POST /pipelines/runs (yaml)
  → orchestrator.parse_dag
  → 入队 RQ：每个 node 一个 job，dependency 用 RQ 的 depends_on
worker:
  → 拉 inputs commit → 本地 workspace
  → subprocess: python -m <plugin_pkg> ...
  → 收 workspace 文件 → 走 §3.1 commit 流程
  → record lineage(inputs=父 commits, processor=...)
```

### 3.3 LLM 调用

```
plugin / processor → ctx.llm.call(model, prompt, seed=...)
  → LLM Gateway (apps/api/dataplat_api/llm/)
      → cache 命中？是 → 返回
      → provider client (anthropic / openai / vllm)
      → audit log（可选）
      → cost 记账
  → 写回 cache
```

## 4. 数据模型（计划态）

参考 design.md §4.4：

- `repositories(id, owner, name, layer, subtype, visibility, card, ...)`
- `commits(hash, repo_id, tree_hash, author_id, time, message, lineage_json, ...)`
- `refs(repo_id, name, commit_hash)`
- `blobs(sha256, size, storage_key)`
- `tree_entries(tree_hash, name, mode, type, target_hash)`
- `lineage_edges(child_commit, parent_commit, kind)`
- `users(id, username, email, password_hash, role, external_id, ...)`
- `acls(repo_id, principal_id, principal_type, permission)`（Phase 2+）

字段细节、索引、外键以实际 Alembic 迁移为准。

## 5. CI / Release

> 待 `ci-generate` Skill 在 `bootstrap-monorepo` 变更中落地后填实。当前为占位。

- 主 workflow：`.github/workflows/ci.yml`
- 触发：PR / main push
- 关键 job：python-lint-type / python-test / web-lint-type / web-test / codegen-check / docker-build
- 测试 artifact：junit XML（供阶段 8 门禁解析）

## 6. 部署拓扑

| Phase | 形态 | 备注 |
|---|---|---|
| 1 | 单 VM + docker-compose | 验证 MVP |
| 2+ | k8s：api/web 是 Deployment，worker 是 KEDA scaled job，plugins 是 Job | |

## 7. 与 design.md 的漂移记录

> 每次 `project-analysis` Skill 跑完发现实现与 design.md 不一致，记在这里。

| 时间 | 漂移点 | 是修代码还是改 design？ | 决议 |
|---|---|---|---|
| _YYYY-MM-DD_ | _e.g. lineage 表实际拆成两张_ | _改 design_ | _更新 design.md §4.4_ |

> 当前无漂移，因为代码尚未开始。
