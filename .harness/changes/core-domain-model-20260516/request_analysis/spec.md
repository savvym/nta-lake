---
change_id: core-domain-model-20260516
version: 1
authored_at: 2026-05-17T00:05:00Z
status: draft
---

# Spec：Pydantic 领域模型 + SQLAlchemy ORM + Alembic 首迁移

## 背景

`bootstrap-monorepo-20260516` 落地了空壳骨架（uv / pnpm workspace + hello-world `/healthz`），但 `apps/api/dataplat_api/models/` 还不存在；`packages/core/src/dataplat_core/` 只有占位 `__init__.py`。

dataplat 的所有后续业务（CAS BlobStore / Adapter / Processor / Lineage / Pipeline / Repo CRUD）都依赖一个稳定的核心领域模型。本变更**只做"模型 + ORM + 迁移"，不引入业务路由**，目的是把 design.md §2 / §4.4 的领域抽象转成代码。

## 问题陈述

当前缺：

1. Pydantic 模型未定义——Adapter/Processor 的 `accepts`/`produces` 字段无类型。
2. ORM 未定义——Catalog / Repo API 无法持久化。
3. Alembic 未初始化——数据库 schema 无版本管理。
4. 协议（SourceAdapter / Processor / RunContext）未定义——后续 plugin 实现无 import 目标。
5. `apps/api/dataplat_api/db.py` 不存在——async engine + session factory 缺失。

## 范围

In scope（每条对应可机械化验证）：

- **AC-1**：`packages/core/src/dataplat_core/domain/` 存在 `__init__.py` 与以下模块：`repository.py` / `commit.py` / `tree.py` / `blob.py` / `refs.py` / `lineage.py`，每个含至少一个 Pydantic v2 BaseModel。
- **AC-2**：`Layer` 是 Literal `["bronze","silver","gold"]`；`Visibility` 是 Literal `["private","internal","public"]`；按 design.md §2.2 定义**分层 Subtype Literal**：`BronzeSubtype = Literal["pdf","pdf-collection","webpage","webpage-collection","book","image-set"]`；`SilverSubtype = Literal["text-corpus","qa-records","dialog-corpus","image-text-pairs"]`；`GoldSubtype = Literal["cpt","sft","dpo","rlhf-pref","eval"]`；类型别名 `Subtype = Union[BronzeSubtype, SilverSubtype, GoldSubtype]`。`Repository` BaseModel 含 `id` / `owner` / `name` / `layer` / `subtype` / `visibility` 字段，构造非合法 Subtype 字面值时 Pydantic 必须 raise `ValidationError`。
- **AC-3**：`Commit` BaseModel 含 `hash` (SHA-256 hex string, 64 字符) / `repo_id` / `tree_hash` / `parents: list[str]` / `author_id` / `created_at` / `message: str | None` / `lineage: Lineage | None`。
- **AC-4**：`Lineage` BaseModel 含 `produced_by: ProducedBy` / `inputs: list[InputRef]` / `run_id` / `env: dict`；`ProducedBy` 含 `kind: Literal["adapter","processor","manual"]` / `name` / `version` / `config_hash`。**`config_hash` 格式与 `Commit.hash` / `BlobRef.sha256` 统一为纯 64-hex**（无 `sha256:` 前缀；前缀化引用 留给 cas-storage 变更对外引用时再加）。
- **AC-5**：`BlobRef` BaseModel 含 `sha256` (64 字符 hex) / `size: int >= 0` / `storage_key: str`；序列化与反序列化 round-trip 等价。
- **AC-6**：`TreeEntry` BaseModel 含 `name` / `mode: int` / `entry_type: Literal["blob","tree"]` / `target_hash`；`Tree` BaseModel 含 `entries: list[TreeEntry]` + `hash: str`。
- **AC-7**：`Ref` BaseModel 含 `repo_id` / `name` / `commit_hash`。
- **AC-8**：`packages/core/src/dataplat_core/protocols/` 下存在 `adapter.py` / `processor.py` / `runcontext.py`，分别定义 `SourceAdapter` / `Processor` / `RunContext` Protocol（`typing.Protocol`，至少含 design.md §4.1 / §4.2 列的方法签名）。
- **AC-9**：`apps/api/dataplat_api/models/__init__.py` + `base.py` + `repository.py` + `commit.py` + `tree.py` + `refs.py` + `blob.py` 存在；用 SQLAlchemy 2.0 `DeclarativeBase` + `Mapped[...]` 风格；每张表至少有 `id` 主键 + `created_at` / `updated_at`（commits/blobs 例外，用 hash 作主键）。**Tree 落两张表**：`trees(hash, repo_id, created_at)` + `tree_entries(tree_hash FK, position, name, mode, entry_type, target_hash)`（不嵌 JSONB；理由：tree_entries 单行可被外键引用、平展索引便于查询 / diff）。
- **AC-10**：`apps/api/dataplat_api/db.py` 存在，导出 `engine`、`AsyncSessionLocal`（async_sessionmaker）、`get_session()` async 生成器依赖（`inspect.isasyncgenfunction(get_session) is True`）；从环境变量 `DATAPLAT_DATABASE_URL` 读取（默认 `postgresql+asyncpg://dataplat:dataplat@localhost:5432/dataplat`）。
- **AC-11**：`apps/api/alembic/` 存在 `alembic.ini` + `env.py` + `versions/0001_initial_schema.py`；`env.py` 用 async pattern（`run_async_migrations`）。
- **AC-12**：`apps/api/pyproject.toml` 新增依赖：`sqlalchemy>=2.0,<3` + `alembic>=1.13` + `asyncpg>=0.29`。
- **AC-13**：`apps/api/alembic upgrade head` 在 docker-compose dev 起的 Postgres 上跑通，落下 6 张表：`repositories` / `commits` / `trees` / `tree_entries` / `refs` / `blobs`，且 `alembic current` 输出包含 `0001` revision。
- **AC-14**：`packages/core/tests/` 下含 ≥ 6 个 pytest 单元测试，覆盖：(a) Repository round-trip；(b) Commit 含 Lineage 嵌入；(c) BlobRef sha256 格式校验拒绝非 64-hex；(d) Tree.entries 列表序列化；(e) Layer/Subtype Literal 严格校验拒绝未知值；(f) Lineage produced_by.kind 校验。
- **AC-15**：`apps/api/tests/test_models.py` 含至少 2 个 ORM smoke 测试，依赖 docker-compose Postgres：(a) create + select Repository 行；(b) commit 行含 lineage JSONB 字段。
- **AC-16**：`uv run ruff check apps/api packages/core packages/sdk-py worker` 退出 0；`uv run mypy apps/api/dataplat_api packages/core/src` 退出 0。
- **AC-17**：`scripts/_self_check.sh core-domain-model` 跑通（本变更在脚本中追加自己的 block）。

## 非范围

- 不引入任何 HTTP 路由（除已存在的 `/healthz`）—— Repository CRUD 留给 `repo-api-mvp`。
- 不实现 BlobStore 真实读写（留给 `cas-storage`）—— `blobs` 表只存元数据（`sha256` / `size` / `storage_key`）。
- 不引入 users / acl 表（留给 `auth-scaffold`）。
- 不写 Card / Schema Registry / Pipeline 表（留给后续）。
- 不引入 Repository 级 ACL（Phase 2+）。
- 不写 lineage_edges 衍生图表（design.md §8 决策：起步用 PG 表，后期再加图查询；本变更只用 commits.lineage JSONB）。

## 验收标准

| ID | 描述 | 验证方式 | 期望 |
|---|---|---|---|
| AC-1 | core/domain 6 模块齐全 | `for f in repository commit tree blob refs lineage; do test -f "packages/core/src/dataplat_core/domain/$f.py" \|\| exit 1; done` | exit 0 |
| AC-2 | Repository + 分层 Subtype Literal 严格校验 | `(cd packages/core && uv run python -c "from dataplat_core.domain.repository import Repository; r=Repository(id='r1', owner='o', name='n', layer='bronze', subtype='pdf', visibility='private'); assert r.subtype=='pdf'") && ! (cd packages/core && uv run python -c "from dataplat_core.domain.repository import Repository; Repository(id='r2', owner='o', name='n', layer='bronze', subtype='bogus-subtype', visibility='private')") 2>/dev/null` | exit 0（subshell 隔离：合法构造 + 反逻辑非法构造必 raise） |
| AC-3 | Commit 字段齐全 | `cd packages/core && uv run python -c "from dataplat_core.domain.commit import Commit; c=Commit(hash='a'*64, repo_id='r1', tree_hash='b'*64, parents=[], author_id='u1'); assert len(c.hash)==64"` | exit 0 |
| AC-4 | Lineage + ProducedBy 字段 + config_hash 纯 64-hex | `cd packages/core && uv run python -c "from dataplat_core.domain.lineage import Lineage, ProducedBy, InputRef; l=Lineage(produced_by=ProducedBy(kind='processor', name='x', version='0.1', config_hash='c'*64), inputs=[], run_id='r1', env={}); assert l.produced_by.kind=='processor'; assert len(l.produced_by.config_hash)==64 and all(c in '0123456789abcdef' for c in l.produced_by.config_hash)"` | exit 0 |
| AC-5 | BlobRef sha256 + round-trip | `cd packages/core && uv run python -c "from dataplat_core.domain.blob import BlobRef; b=BlobRef(sha256='a'*64, size=10, storage_key='blobs/aa/aa..'); assert BlobRef.model_validate_json(b.model_dump_json())==b"` | exit 0 |
| AC-6 | Tree / TreeEntry | `cd packages/core && uv run python -c "from dataplat_core.domain.tree import Tree, TreeEntry; e=TreeEntry(name='a', mode=33188, entry_type='blob', target_hash='c'*64); t=Tree(hash='d'*64, entries=[e]); assert t.entries[0].name=='a'"` | exit 0 |
| AC-7 | Ref 字段 | `cd packages/core && uv run python -c "from dataplat_core.domain.refs import Ref; r=Ref(repo_id='r1', name='main', commit_hash='e'*64); assert r.name=='main'"` | exit 0 |
| AC-8 | 8 个 Protocol / 数据类 import 齐全 | `cd packages/core && uv run python -c "from dataplat_core.protocols.adapter import SourceAdapter, IngestResult; from dataplat_core.protocols.processor import Processor, ProcessResult, RepoView, RepoSelector, RepoSpec; from dataplat_core.protocols.runcontext import RunContext"` | exit 0 |
| AC-9 | ORM 7 模块齐全 | `for f in __init__ base repository commit tree refs blob; do test -f "apps/api/dataplat_api/models/$f.py" \|\| exit 1; done` | exit 0 |
| AC-10 | db.py 导出 engine/session + get_session 为 async generator | `cd apps/api && uv run python -c "import inspect; from dataplat_api.db import engine, AsyncSessionLocal, get_session; assert engine is not None; assert inspect.isasyncgenfunction(get_session), 'get_session 必须是 async generator (yield session)'"` | exit 0 |
| AC-11 | Alembic 3 文件齐全 | `test -f apps/api/alembic.ini && test -f apps/api/alembic/env.py && ls apps/api/alembic/versions/0001_*.py >/dev/null` | exit 0 |
| AC-12 | apps/api 新依赖 | `python3 -c "import tomllib; d=tomllib.load(open('apps/api/pyproject.toml','rb')); deps=d['project']['dependencies']; assert any('sqlalchemy' in x for x in deps) and any('alembic' in x for x in deps) and any('asyncpg' in x for x in deps)"` | exit 0 |
| AC-13 | `alembic upgrade head` PASS（需 Postgres 起来；端口由 `DATAPLAT_PG_PORT` 控制，默认 5432）| `pg_isready -h localhost -p ${DATAPLAT_PG_PORT:-5432} -q && (cd apps/api && export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && uv run alembic upgrade head && uv run alembic current 2>&1 \| grep -q "0001")`（pg_isready 失败 → SKIP）| exit 0 或 SKIP |
| AC-14 | packages/core 单测 ≥ 6 | `(cd packages/core && uv run pytest -q --tb=no tests/) && [ "$(cd packages/core && uv run pytest --collect-only -q tests/ 2>&1 \| grep -cE "^tests/")" -ge 6 ]` | exit 0 |
| AC-15 | apps/api ORM smoke ≥ 2 | `pg_isready -h localhost -p ${DATAPLAT_PG_PORT:-5432} -q && (cd apps/api && export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && uv run pytest -q --tb=no tests/test_models.py) && [ "$(cd apps/api && uv run pytest --collect-only -q tests/test_models.py 2>&1 \| grep -cE "test_models\.py::")" -ge 2 ]`（pg_isready 失败时 self_check 视为 SKIP 而非 FAIL）| exit 0 或 SKIP |
| AC-16 | ruff + mypy（范围收窄到本变更模块） | `uv run ruff check apps/api packages/core && uv run mypy apps/api/dataplat_api packages/core/src` | exit 0 |
| AC-17 | _self_check core-domain-model 块 | `bash scripts/_self_check.sh core-domain-model` 退出 0 + 17/17 PASS | exit 0 |

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| docker-compose Postgres 未起 | 中 | AC-13 / AC-15 FAIL | spec 显式要求 `make up` 先跑；test_report 自陈"AC-13/15 是集成测试，依赖外部容器" |
| async Alembic env.py 写错触发 event loop 冲突 | 中 | AC-13 FAIL | 用 `asyncio.run` + `connection.run_sync(do_migrations)` 标准 pattern |
| SQLAlchemy 2.0 vs 1.4 语法混用 | 低 | mypy / ruff 报错 | 严格只用 `Mapped[]` + `mapped_column()` + `async_sessionmaker` |
| asyncpg + Postgres 16 兼容 | 低 | 连接失败 | asyncpg 0.29+ 支持 PG 16 |
| Pydantic v2 类型严格度高，Layer 用 Literal 在某些 IDE 报警 | 低 | 不影响运行 | 接受；mypy --strict 通过即可 |
| 命名冲突：domain.commit vs Python 标准 commit | 低 | 无 | dataplat_core.domain.commit 命名空间隔离 |
| Pydantic v2 与 SQLAlchemy ORM 类型不一致（如 UUID 在 ORM 是 sa.types.UUID 而 Pydantic 用 str；datetime tz-aware 在 ORM 是 TIMESTAMP WITH TIME ZONE 但 Pydantic 默认 naive）| 中 | API 序列化时报类型错或时区错 | 严格用 `Mapped[uuid.UUID]` + `Mapped[datetime]` (with timezone=True)；Pydantic 模型用 `uuid.UUID` + `datetime` 类型，平台调用时 `model_validate(orm_obj.__dict__)` 自动转换；单测专门覆盖时区往返 |
| `dataplat_core.domain` 与 `dataplat_core.protocols` 间循环 import（protocols 依赖 domain 的 Pydantic 模型签名）| 中 | 包初始化时 ImportError | protocols 仅 import 具体 domain 子模块（如 `from dataplat_core.domain.repository import Repository`）不导整个 domain；不让 domain/__init__.py 反向 import protocols；单测对 8 个 protocol import 同时跑 |

## 受影响模块

- `packages/core/src/dataplat_core/domain/`（新建）
- `packages/core/src/dataplat_core/protocols/`（新建）
- `packages/core/tests/`（新建）
- `apps/api/dataplat_api/models/`（新建）
- `apps/api/dataplat_api/db.py`（新建）
- `apps/api/alembic*`（新建）
- `apps/api/tests/test_models.py`（新建）
- `apps/api/pyproject.toml`（+3 依赖）
- `scripts/_self_check.sh`（追加 block）
- `Makefile` 不变

## 不受影响

- `.harness/` / `wiki/` / `CLAUDE.md` / `apps/web/`：完全不动。
- `apps/api/dataplat_api/main.py` 与 `/healthz`：不动。

## 待澄清问题

- [x] async vs sync Alembic：选 async（design.md §11.7 强约束）
- [x] Lineage 存 JSONB vs 拆表：本变更只用 JSONB，lineage_edges 衍生表留给后续

## 引用

- `.harness/design.md` §2 / §4.1 / §4.2 / §4.4 / §11.2 / §11.7
- `.harness/rules/coding-style.md` §1（Python） / §3（SQL）
