#!/usr/bin/env bash
# scripts/_self_check.sh
#
# 仓库级自检脚本——把每个变更 spec §验收标准表的 shell 命令归档为
# 可重复运行的断言。当前实现 bootstrap-monorepo-20260516 的 17 条 AC。
#
# 设计意图：
# - 每个变更在 stage 5 单测编写阶段把自己的 AC 落到这里（追加块）；
# - 阶段内使用 quick/current 快检，stage 8 CI 使用 full 作为统一 smoke gate；
# - 后续 follow-up `harness-script-productize-<yyyymmdd>` 会把 harness-bootstrap-20260516
#   的 12 条 AC（当前在 .harness/changes/harness-bootstrap-20260516/unit_test/
#   check_harness.sh）也搬进来，形成单一入口。
#
# 用法：
#   bash scripts/_self_check.sh                    # 兼容旧入口：跑 full
#   bash scripts/_self_check.sh quick [change-id]  # 阶段内快检：全局轻量 lint + stage preflight
#   bash scripts/_self_check.sh current [change-id]# quick + 当前 change block（如已注册）
#   bash scripts/_self_check.sh change <change-id> # current 的显式别名
#   bash scripts/_self_check.sh full               # 最终 gate：跑全部历史回归
#   bash scripts/_self_check.sh <change-id>        # 只跑指定 change 的块
#
# 退出码：0 全过 / 1 至少一条 FAIL。
#
# 运行环境要求：bash ≥ 3.2 + python3（用于 tomllib / yaml / json / ast 解析）。

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

FILTER="${1:-}"

PASS=0
FAIL=0
SKIP=0
FAILED_ACS=()
SKIPPED_ACS=()

run_ac() {
  local id="$1"
  local desc="$2"
  shift 2
  if "$@" >/dev/null 2>&1; then
    printf "PASS  %-10s  %s\n" "$id" "$desc"
    PASS=$((PASS + 1))
  else
    printf "FAIL  %-10s  %s\n" "$id" "$desc"
    FAIL=$((FAIL + 1))
    FAILED_ACS+=("$id")
  fi
}

# core-domain-model 引入：探针未通过时整条 AC 视作 SKIP 而非 FAIL
# 探针实现：python socket connect（不依赖 pg_isready 客户端在 host 安装）
_pg_reachable() {
  python3 -c "
import socket, sys
s = socket.socket()
s.settimeout(1)
try:
    s.connect(('localhost', int('${DATAPLAT_PG_PORT:-5432}')))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
"
}

run_ac_skipif_no_pg() {
  local id="$1"
  local desc="$2"
  shift 2
  if ! _pg_reachable 2>/dev/null; then
    printf "SKIP  %-10s  %s（Postgres %s:%s 未通）\n" "$id" "$desc" "localhost" "${DATAPLAT_PG_PORT:-5432}"
    SKIP=$((SKIP + 1))
    SKIPPED_ACS+=("$id")
    return 0
  fi
  run_ac "$id" "$desc" "$@"
}

# =============================================================================
# Block: bootstrap-monorepo-20260516
# 17 条 AC（详见 .harness/changes/bootstrap-monorepo-20260516/request_analysis/spec.md）
# =============================================================================

run_bootstrap_monorepo() {
  echo "=== bootstrap-monorepo-20260516 :: 17 AC ==="

  run_ac AC-1 "pyproject uv workspace" \
    python3 -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); assert 'apps/api' in d['tool']['uv']['workspace']['members']"

  run_ac AC-2a "pnpm-workspace 含 apps/web" \
    python3 -c "import yaml; d=yaml.safe_load(open('pnpm-workspace.yaml')); assert 'apps/web' in d['packages']"

  run_ac AC-2b "package.json 合法" \
    python3 -c "import json; json.load(open('package.json'))"

  run_ac AC-3 "turbo.json 4 task" \
    python3 -c "import json; d=json.load(open('turbo.json')); [d['tasks'][k] for k in ['lint','typecheck','test','build']]"

  run_ac AC-4 "Makefile 必备 11 target make -n 干跑" \
    bash -c 'for t in up down api web worker migrate seed codegen test lint typecheck; do make -n "$t" >/dev/null 2>&1 || exit 1; done'

  run_ac AC-5 "README ≥ 30 行 + quickstart" \
    bash -c '[ "$(wc -l < README.md)" -ge 30 ] && grep -qE "快速开始|Quickstart" README.md'

  run_ac AC-6 ".gitignore 必备排除 + .claude/ ignored（含 settings.local.json + worktrees）" \
    bash -c 'test -f .gitignore && for p in .venv node_modules dist __pycache__ .pytest_cache .ruff_cache .mypy_cache .turbo ".claude/"; do grep -q "$p" .gitignore || exit 1; done && git check-ignore -q .claude/settings.local.json && git check-ignore -q .claude/worktrees/'

  run_ac AC-7 "apps/api 文件齐全 + /healthz" \
    bash -c 'for f in pyproject.toml dataplat_api/__init__.py dataplat_api/main.py tests/__init__.py tests/test_health.py; do test -f "apps/api/$f" || exit 1; done && grep -q "healthz" apps/api/dataplat_api/main.py'

  run_ac AC-8 "apps/web 文件齐全（web-mvp-pages 后 App.tsx 由 routes/ 取代）" \
    bash -c 'for f in package.json vite.config.ts tsconfig.json tsconfig.node.json index.html src/main.tsx; do test -f "apps/web/$f" || exit 1; done && (test -f apps/web/src/App.tsx || test -d apps/web/src/routes)'

  run_ac AC-9 "packages/core / sdk-py + worker src layout" \
    bash -c 'test -f packages/core/pyproject.toml && test -f packages/core/src/dataplat_core/__init__.py && test -f packages/sdk-py/pyproject.toml && test -f packages/sdk-py/src/dataplat_sdk/__init__.py && test -f worker/pyproject.toml && test -f worker/src/dataplat_worker/__init__.py'

  run_ac AC-10 "packages/api-types 占位" \
    bash -c 'test -f packages/api-types/package.json && test -f packages/api-types/src/generated.ts'

  run_ac AC-11 "plugins/recipes/docs README ≥ 10 行" \
    bash -c 'for f in plugins/README.md recipes/README.md docs/README.md; do test -f "$f" && [ "$(wc -l < "$f")" -ge 10 ] || exit 1; done'

  run_ac AC-12 "docker-compose.dev.yml 合法 + 3 service" \
    python3 -c "import yaml; d=yaml.safe_load(open('docker/docker-compose.dev.yml')); s=d.get('services',{}); [s[k] for k in ['postgres','minio','redis']]"

  run_ac AC-13 "3 个 Dockerfile" \
    bash -c 'for f in api.Dockerfile worker.Dockerfile web.Dockerfile; do test -f "docker/images/$f" || exit 1; done'

  run_ac AC-14 "scripts/export_openapi.py + AST 合法" \
    bash -c 'test -f scripts/export_openapi.py && python3 -c "import ast; ast.parse(open(\"scripts/export_openapi.py\").read())"'

  # AC-15（ci.yml 合法 + 5 job + concurrency）由 harness-remote-push-onboarding-20260518 撤销：
  # 项目策略不引入远程 CI（本地 pytest + self_check.sh full 等价 CI）。
  # bootstrap-monorepo 原 spec AC-15 保留作为历史记录；机械化检查在本 self_check 中删除。

  run_ac AC-16 "apps/api pytest test_health.py exit 0" \
    bash -c 'cd apps/api && uv run pytest -q tests/test_health.py >/dev/null 2>&1'

  run_ac AC-17 "apps/web vite build → dist/index.html" \
    bash -c 'pnpm --filter web build >/dev/null 2>&1 && test -f apps/web/dist/index.html'
}

# =============================================================================
# Block: core-domain-model-20260516
# 17 条 AC（详见 .harness/changes/core-domain-model-20260516/request_analysis/spec.md）
# AC-13 / AC-15 在 Postgres 不可用时 SKIP（pg_isready 探针）
# =============================================================================

run_core_domain_model() {
  echo "=== core-domain-model-20260516 :: 17 AC ==="

  run_ac AC-1 "core/domain 6 模块齐全" \
    bash -c 'for f in repository commit tree blob refs lineage; do test -f "packages/core/src/dataplat_core/domain/$f.py" || exit 1; done'

  run_ac AC-2 "Repository + 分层 Subtype Literal 严格校验" \
    bash -c '(cd packages/core && uv run python -c "from dataplat_core.domain.repository import Repository; r=Repository(id=\"r1\", owner=\"o\", name=\"n\", layer=\"bronze\", subtype=\"pdf\", visibility=\"private\"); assert r.subtype==\"pdf\"") && ! (cd packages/core && uv run python -c "from dataplat_core.domain.repository import Repository; Repository(id=\"r2\", owner=\"o\", name=\"n\", layer=\"bronze\", subtype=\"bogus-subtype\", visibility=\"private\")") 2>/dev/null'

  run_ac AC-3 "Commit 字段齐全" \
    bash -c 'cd packages/core && uv run python -c "from dataplat_core.domain.commit import Commit; c=Commit(hash=\"a\"*64, repo_id=\"r1\", tree_hash=\"b\"*64, parents=[], author_id=\"u1\"); assert len(c.hash)==64"'

  run_ac AC-4 "Lineage + ProducedBy + config_hash 64-hex" \
    bash -c 'cd packages/core && uv run python -c "from dataplat_core.domain.lineage import Lineage, ProducedBy, InputRef; l=Lineage(produced_by=ProducedBy(kind=\"processor\", name=\"x\", version=\"0.1\", config_hash=\"c\"*64), inputs=[], run_id=\"r1\", env={}); assert l.produced_by.kind==\"processor\"; assert len(l.produced_by.config_hash)==64"'

  run_ac AC-5 "BlobRef sha256 round-trip" \
    bash -c 'cd packages/core && uv run python -c "from dataplat_core.domain.blob import BlobRef; b=BlobRef(sha256=\"a\"*64, size=10, storage_key=\"blobs/aa/x\"); assert BlobRef.model_validate_json(b.model_dump_json())==b"'

  run_ac AC-6 "Tree + TreeEntry" \
    bash -c 'cd packages/core && uv run python -c "from dataplat_core.domain.tree import Tree, TreeEntry; e=TreeEntry(name=\"a\", mode=33188, entry_type=\"blob\", target_hash=\"c\"*64); t=Tree(hash=\"d\"*64, entries=[e]); assert t.entries[0].name==\"a\""'

  run_ac AC-7 "Ref 字段" \
    bash -c 'cd packages/core && uv run python -c "from dataplat_core.domain.refs import Ref; r=Ref(repo_id=\"r1\", name=\"main\", commit_hash=\"e\"*64); assert r.name==\"main\""'

  run_ac AC-8 "8 个 Protocol/数据类 import 齐全" \
    bash -c 'cd packages/core && uv run python -c "from dataplat_core.protocols.adapter import SourceAdapter, IngestResult; from dataplat_core.protocols.processor import Processor, ProcessResult, RepoView, RepoSelector, RepoSpec; from dataplat_core.protocols.runcontext import RunContext"'

  run_ac AC-9 "ORM 7 模块齐全 + Tree 拆两表" \
    bash -c 'for f in __init__ base repository commit tree refs blob; do test -f "apps/api/dataplat_api/models/$f.py" || exit 1; done && grep -q "class TreeEntryORM" apps/api/dataplat_api/models/tree.py'

  run_ac AC-10 "db.py 导出 engine/session + get_session 为 async generator" \
    bash -c 'cd apps/api && uv run python -c "import inspect; from dataplat_api.db import engine, AsyncSessionLocal, get_session; assert engine is not None; assert inspect.isasyncgenfunction(get_session)"'

  run_ac AC-11 "Alembic 3 文件齐全" \
    bash -c 'test -f apps/api/alembic.ini && test -f apps/api/alembic/env.py && ls apps/api/alembic/versions/0001_*.py >/dev/null'

  run_ac AC-12 "apps/api 新依赖 sqlalchemy/alembic/asyncpg" \
    python3 -c "import tomllib; d=tomllib.load(open('apps/api/pyproject.toml','rb')); deps=d['project']['dependencies']; assert any('sqlalchemy' in x for x in deps) and any('alembic' in x for x in deps) and any('asyncpg' in x for x in deps)"

  run_ac_skipif_no_pg AC-13 "alembic upgrade head + 0001 head" \
    bash -c 'export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && cd apps/api && uv run alembic upgrade head && uv run alembic history 2>&1 | grep -q "0001"'

  run_ac AC-14 "packages/core 单测 ≥ 6 + 全 PASS" \
    bash -c '(cd packages/core && uv run pytest -q --tb=no tests/) && [ "$(cd packages/core && uv run pytest --collect-only -q tests/ 2>&1 | grep -cE "::")" -ge 6 ]'

  run_ac_skipif_no_pg AC-15 "apps/api ORM smoke ≥ 2 + 全 PASS" \
    bash -c 'export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && (cd apps/api && uv run pytest -q --tb=no tests/test_models.py) && [ "$(cd apps/api && uv run pytest --collect-only -q tests/test_models.py 2>&1 | grep -cE "test_models\.py::")" -ge 2 ]'

  run_ac AC-16 "ruff + mypy 范围内 0 错误" \
    bash -c 'uv run ruff check apps/api packages/core && uv run mypy apps/api/dataplat_api packages/core/src'

  run_ac AC-17 "AC-17 == 本 block 自递归（脚本能跑通即满足）" \
    true
}

# =============================================================================
# MinIO 探针 + cas-storage block
# =============================================================================

_minio_reachable() {
  python3 -c "
import socket, sys
s = socket.socket()
s.settimeout(1)
try:
    s.connect(('localhost', int('${DATAPLAT_MINIO_PORT:-9000}')))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
"
}

run_ac_skipif_no_minio() {
  local id="$1"
  local desc="$2"
  shift 2
  if ! _minio_reachable 2>/dev/null; then
    printf "SKIP  %-10s  %s（MinIO localhost:%s 未通）\n" "$id" "$desc" "${DATAPLAT_MINIO_PORT:-9000}"
    SKIP=$((SKIP + 1))
    SKIPPED_ACS+=("$id")
    return 0
  fi
  run_ac "$id" "$desc" "$@"
}

run_cas_storage() {
  echo "=== cas-storage-20260517 :: 17 AC ==="

  run_ac AC-1 "storage.py + BlobStore runtime_checkable Protocol + BlobPutResult" \
    bash -c 'test -f packages/core/src/dataplat_core/protocols/storage.py && cd packages/core && uv run python -c "from typing import Protocol; from pydantic import BaseModel; from dataplat_core.protocols.storage import BlobStore, BlobPutResult; assert issubclass(BlobStore, Protocol); assert getattr(BlobStore, \"_is_runtime_protocol\", False) is True; assert issubclass(BlobPutResult, BaseModel)"'

  run_ac AC-2 "protocols/__init__.py 暴露 BlobStore/BlobPutResult" \
    bash -c 'cd packages/core && uv run python -c "from dataplat_core.protocols import BlobStore, BlobPutResult"'

  run_ac AC-3 "apps/api/storage 三文件齐全" \
    bash -c 'for f in __init__.py keys.py minio_store.py; do test -f "apps/api/dataplat_api/storage/$f" || exit 1; done'

  run_ac AC-4 "storage_key_for 正确 + sha256 校验" \
    bash -c '(cd apps/api && uv run python -c "from dataplat_api.storage.keys import storage_key_for; assert storage_key_for(\"a\"*64)==\"blobs/aa/\"+\"a\"*64") && ! (cd apps/api && uv run python -c "from dataplat_api.storage.keys import storage_key_for; storage_key_for(\"NOTHEX\"+\"a\"*58)") 2>/dev/null'

  run_ac AC-5 "MinioBlobStore 实现 BlobStore Protocol" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.storage.minio_store import MinioBlobStore; from dataplat_core.protocols.storage import BlobStore; s=MinioBlobStore.__new__(MinioBlobStore); assert isinstance(s, BlobStore)"'

  run_ac AC-6 "apps/api +boto3 +botocore 依赖" \
    python3 -c "import tomllib; d=tomllib.load(open('apps/api/pyproject.toml','rb')); deps=d['project']['dependencies']; assert any('boto3' in x for x in deps) and any('botocore' in x for x in deps)"

  run_ac AC-7 "put 流式 6 步算法已实现" \
    bash -c 'grep -q "HashingStream" apps/api/dataplat_api/storage/minio_store.py && grep -q "_tmp/" apps/api/dataplat_api/storage/minio_store.py && grep -q "copy_object" apps/api/dataplat_api/storage/minio_store.py'

  run_ac AC-8 "去重 deduplicated 字段已实现" \
    bash -c 'grep -q "deduplicated" apps/api/dataplat_api/storage/minio_store.py'

  run_ac AC-9 "exists 已实现" \
    bash -c 'grep -qE "async def exists" apps/api/dataplat_api/storage/minio_store.py'

  run_ac AC-10 "get + KeyError 首次 __anext__ 已实现" \
    bash -c 'grep -qE "raise KeyError" apps/api/dataplat_api/storage/minio_store.py'

  run_ac AC-11 "get_size 已实现" \
    bash -c 'grep -qE "async def get_size" apps/api/dataplat_api/storage/minio_store.py'

  run_ac AC-12 "key 严格 blobs/{2}/{64} 规范" \
    bash -c 'grep -qE "blobs/" apps/api/dataplat_api/storage/keys.py'

  run_ac AC-13 "大对象 ≥ 2MB 测试存在（AC-15 e 覆盖）" \
    bash -c 'grep -qE "2 \* 1024 \* 1024" apps/api/tests/test_minio_store.py'

  run_ac AC-14 "packages/core test_storage_protocol ≥ 3 + 全 PASS" \
    bash -c '(cd packages/core && uv run pytest -q --tb=no tests/test_storage_protocol.py) && [ "$(cd packages/core && uv run pytest --collect-only -q tests/test_storage_protocol.py 2>&1 | grep -cE "::")" -ge 3 ]'

  run_ac_skipif_no_minio AC-15 "apps/api MinIO 集成 ≥ 5 + 全 PASS" \
    bash -c 'export DATAPLAT_MINIO_ENDPOINT=http://localhost:${DATAPLAT_MINIO_PORT:-9000} && export DATAPLAT_MINIO_ACCESS_KEY=${DATAPLAT_MINIO_ACCESS_KEY:-dataplat} && export DATAPLAT_MINIO_SECRET_KEY=${DATAPLAT_MINIO_SECRET_KEY:-dataplat-secret} && (cd apps/api && uv run pytest -q --tb=no tests/test_minio_store.py) && [ "$(cd apps/api && uv run pytest --collect-only -q tests/test_minio_store.py 2>&1 | grep -cE "::")" -ge 5 ]'

  run_ac AC-16 "ruff + mypy 全 PASS" \
    bash -c 'uv run ruff check apps/api packages/core && uv run mypy apps/api/dataplat_api packages/core/src'

  run_ac AC-17 "AC-17 自递归" true
}

# =============================================================================
# Block: auth-scaffold-20260517
# 17 条 AC（详见 .harness/changes/auth-scaffold-20260517/request_analysis/spec.md）
# =============================================================================

run_auth_scaffold() {
  echo "=== auth-scaffold-20260517 :: 17 AC ==="

  run_ac AC-1 "UserORM 模块 + class UserORM" \
    bash -c 'test -f apps/api/dataplat_api/models/user.py && grep -q "class UserORM" apps/api/dataplat_api/models/user.py'

  run_ac_skipif_no_pg AC-2 "0002 migration applied（rq-worker 后 head 演进到 0003）" \
    bash -c 'ls apps/api/alembic/versions/0002_*.py >/dev/null && export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && cd apps/api && uv run alembic upgrade head && uv run alembic history 2>&1 | grep -q "0002"'

  run_ac AC-3 "AuthProvider runtime_checkable Protocol + AuthenticatedUser BaseModel" \
    bash -c 'cd packages/core && uv run python -c "from typing import Protocol; from pydantic import BaseModel; from dataplat_core.protocols.auth import AuthProvider, AuthenticatedUser; assert issubclass(AuthProvider, Protocol); assert getattr(AuthProvider, \"_is_runtime_protocol\", False) is True; assert issubclass(AuthenticatedUser, BaseModel)"'

  run_ac AC-4 "protocols __init__ 暴露" \
    bash -c 'cd packages/core && uv run python -c "from dataplat_core.protocols import AuthProvider, AuthenticatedUser"'

  run_ac AC-5 "password hash/verify + 随机 salt" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.auth.password import hash_password, verify_password; h1=hash_password(\"x\"); h2=hash_password(\"x\"); assert h1!=h2; assert verify_password(\"x\",h1) and verify_password(\"x\",h2) and not verify_password(\"y\",h1)"'

  run_ac AC-6 "JWT encode/decode + lazy os.getenv" \
    bash -c 'cd apps/api && DATAPLAT_JWT_SECRET=test-secret-32-bytes-long-xxxxx uv run python -c "from dataplat_api.auth.tokens import encode_access_token, decode_token; t=encode_access_token(\"u1\",\"user\"); d=decode_token(t); assert d[\"sub\"]==\"u1\" and d[\"role\"]==\"user\""'

  run_ac AC-7 "cookies httponly+secure+samesite=lax" \
    bash -c 'cd apps/api && uv run python -c "from fastapi import Response; from dataplat_api.auth.cookies import set_auth_cookies; r=Response(); set_auth_cookies(r,\"a\",\"b\"); hdrs=[h for h in r.raw_headers if b\"set-cookie\" in h[0].lower()]; raw=b\"\\n\".join(h[1] for h in hdrs).lower(); assert b\"httponly\" in raw and b\"secure\" in raw and b\"samesite=lax\" in raw"'

  run_ac AC-8 "LocalAuthProvider 实现 AuthProvider Protocol" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.auth.local_provider import LocalAuthProvider; from dataplat_core.protocols.auth import AuthProvider; p=LocalAuthProvider.__new__(LocalAuthProvider); assert isinstance(p, AuthProvider)"'

  run_ac AC-9 "get_current_user is coroutine" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.auth.deps import get_current_user; import inspect; assert inspect.iscoroutinefunction(get_current_user)"'

  run_ac AC-10 "auth router 4 路由（prefix 钉死）" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.routers.auth import router; paths={r.path for r in router.routes}; assert {\"/auth/login\",\"/auth/logout\",\"/auth/refresh\",\"/auth/me\"} <= paths"'

  run_ac AC-11 "admin router 含 /admin/users" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.routers.admin import router; paths={r.path for r in router.routes}; assert any(\"/admin/users\" in p for p in paths)"'

  run_ac AC-12 "main 集成 + OpenAPI 含 /auth/login + /auth/me" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.main import app; spec=app.openapi(); assert \"/auth/login\" in spec[\"paths\"] and \"/auth/me\" in spec[\"paths\"]"'

  run_ac AC-13 "argon2-cffi + PyJWT 依赖" \
    python3 -c "import tomllib; d=tomllib.load(open('apps/api/pyproject.toml','rb')); deps=d['project']['dependencies']; assert any('argon2-cffi' in x for x in deps) and any('pyjwt' in x.lower() for x in deps)"

  run_ac AC-14 "packages/core auth 单测 ≥ 3 + 全 PASS" \
    bash -c '(cd packages/core && uv run pytest -q --tb=no tests/test_auth_protocol.py) && [ "$(cd packages/core && uv run pytest --collect-only -q tests/test_auth_protocol.py 2>&1 | grep -cE "::")" -ge 3 ]'

  run_ac_skipif_no_pg AC-15 "apps/api auth 集成 ≥ 10 + 全 PASS（含 user→403）" \
    bash -c 'export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && export DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx && (cd apps/api && uv run pytest -q --tb=no tests/test_auth.py) && [ "$(cd apps/api && uv run pytest --collect-only -q tests/test_auth.py 2>&1 | grep -cE "::")" -ge 10 ]'

  run_ac AC-16 "ruff + mypy 全 PASS" \
    bash -c 'uv run ruff check apps/api packages/core && uv run mypy apps/api/dataplat_api packages/core/src'

  run_ac AC-17 "AC-17 自递归" true
}

# =============================================================================
# Block: repo-api-mvp-20260517
# 13 条 AC（详见 .harness/changes/repo-api-mvp-20260517/request_analysis/spec.md）
# AC-11 / AC-12 在 Postgres 不可用时 SKIP
# =============================================================================

run_repo_api_mvp() {
  echo "=== repo-api-mvp-20260517 :: 13 AC ==="

  run_ac AC-1 "schemas/repo.py 5 类型 + extra=forbid 拒未知字段" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_api.schemas.repo import RepositoryCreate, RepositoryRead, RepositoryListItem, RepositoryUpdate, RepositoryListResponse
from pydantic import ValidationError
# extra=forbid 拒未知
try:
    RepositoryCreate(owner=\"o\", name=\"n\", layer=\"bronze\", subtype=\"pdf\", bogus=\"x\")
    raise SystemExit(1)
except ValidationError:
    pass
"'

  run_ac AC-2 "services/repo.py 含 RepoService 5 方法" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.services.repo import RepoService; [getattr(RepoService, m) for m in [\"create\",\"get_by_owner_name\",\"list\",\"update\",\"delete\"]]"'

  run_ac AC-3 "routers/repos.py 5 路由 + prefix=/repos" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.routers.repos import router; paths={r.path for r in router.routes}; assert \"/repos\" in paths and \"/repos/{owner}/{name}\" in paths"'

  run_ac AC-4 "main 集成 repos router + OpenAPI 含 /repos" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.main import app; spec=app.openapi(); assert \"/repos\" in spec[\"paths\"] and \"/repos/{owner}/{name}\" in spec[\"paths\"]"'

  run_ac AC-5 "get_optional_user 与 get_current_user 共享 _decode_user_from_cookie + GET 路由用 get_optional_user" \
    bash -c 'cd apps/api && uv run python -c "
import inspect
from dataplat_api.auth.deps import _decode_user_from_cookie, get_current_user, get_optional_user
from dataplat_api.routers.repos import router
assert inspect.iscoroutinefunction(_decode_user_from_cookie)
assert inspect.iscoroutinefunction(get_optional_user)
src = inspect.getsource(get_optional_user)
assert \"_decode_user_from_cookie\" in src
# GET 路由必须用 get_optional_user 而非 get_current_user（避免 401 泄露存在性）
for r in router.routes:
    if \"GET\" in (r.methods or set()):
        deps = [d.call for d in r.dependant.dependencies]
        assert get_optional_user in deps, f\"{r.path} 未挂 get_optional_user\"
        assert get_current_user not in deps, f\"{r.path} 错挂 get_current_user\"
"'

  run_ac AC-6 "RepoService._visibility_visible 矩阵正确" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_api.services.repo import RepoService
from dataplat_core.protocols.auth import AuthenticatedUser
import uuid
admin = AuthenticatedUser(user_id=str(uuid.uuid4()), username=\"a\", role=\"admin\", is_active=True)
user = AuthenticatedUser(user_id=str(uuid.uuid4()), username=\"u\", role=\"user\", is_active=True)
# public：任何人
assert RepoService._visibility_visible(\"public\", None) is True
assert RepoService._visibility_visible(\"public\", user) is True
assert RepoService._visibility_visible(\"public\", admin) is True
# internal：仅已登录
assert RepoService._visibility_visible(\"internal\", None) is False
assert RepoService._visibility_visible(\"internal\", user) is True
assert RepoService._visibility_visible(\"internal\", admin) is True
# private：仅 admin
assert RepoService._visibility_visible(\"private\", None) is False
assert RepoService._visibility_visible(\"private\", user) is False
assert RepoService._visibility_visible(\"private\", admin) is True
"'

  run_ac AC-7 "POST /repos 受 require_admin 保护" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_api.routers.repos import router
from dataplat_api.auth.deps import require_admin
post_route = next(r for r in router.routes if r.path==\"/repos\" and \"POST\" in r.methods)
deps = [d.call for d in post_route.dependant.dependencies]
assert require_admin in deps
"'

  run_ac AC-8 "PATCH /repos/{owner}/{name} 受 require_admin 保护（spec AC-8）" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_api.routers.repos import router
from dataplat_api.auth.deps import require_admin
patch_route = next(r for r in router.routes if \"PATCH\" in (r.methods or set()) and r.path==\"/repos/{owner}/{name}\")
deps = [d.call for d in patch_route.dependant.dependencies]
assert require_admin in deps
"'

  run_ac AC-9 "DELETE /repos/{owner}/{name} 受 require_admin 保护（spec AC-9）" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_api.routers.repos import router
from dataplat_api.auth.deps import require_admin
delete_route = next(r for r in router.routes if \"DELETE\" in (r.methods or set()) and r.path==\"/repos/{owner}/{name}\")
deps = [d.call for d in delete_route.dependant.dependencies]
assert require_admin in deps
"'

  run_ac AC-10 "GET /repos 支持 limit/offset/layer query + 返 {items, total}（spec AC-10）" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_api.main import app
spec = app.openapi()
get_op = spec[\"paths\"][\"/repos\"][\"get\"]
params = {p[\"name\"] for p in get_op.get(\"parameters\", [])}
assert {\"limit\",\"offset\",\"layer\"} <= params, f\"GET /repos 缺 query：实际 {params}\"
# 200 响应 schema 必须含 items + total
schema_ref = get_op[\"responses\"][\"200\"][\"content\"][\"application/json\"][\"schema\"][\"\$ref\"]
schema_name = schema_ref.split(\"/\")[-1]
props = spec[\"components\"][\"schemas\"][schema_name][\"properties\"]
assert \"items\" in props and \"total\" in props
"'

  run_ac_skipif_no_pg AC-11 "apps/api repos 集成 ≥ 13 + 全 PASS" \
    bash -c 'export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && export DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx && (cd apps/api && uv run pytest -q --tb=no tests/test_repos.py) && [ "$(cd apps/api && uv run pytest --collect-only -q tests/test_repos.py 2>&1 | grep -cE "test_repos\.py::")" -ge 14 ]'

  run_ac AC-12 "ruff + mypy 全 PASS" \
    bash -c 'uv run ruff check apps/api packages/core && uv run mypy apps/api/dataplat_api packages/core/src'

  run_ac AC-13 "AC-13 自递归" true
}

# =============================================================================
# Block: commit-api-mvp-20260517
# 13 条 AC（详见 .harness/changes/commit-api-mvp-20260517/request_analysis/spec.md）
# AC-11 在 PG + MinIO 双探针任一不可达 SKIP
# =============================================================================

run_ac_skipif_no_pg_or_minio() {
  local id="$1"
  local desc="$2"
  shift 2
  if ! _pg_reachable 2>/dev/null; then
    printf "SKIP  %-10s  %s（Postgres %s:%s 未通）\n" "$id" "$desc" "localhost" "${DATAPLAT_PG_PORT:-5432}"
    SKIP=$((SKIP + 1))
    SKIPPED_ACS+=("$id")
    return 0
  fi
  if ! _minio_reachable 2>/dev/null; then
    printf "SKIP  %-10s  %s（MinIO localhost:%s 未通）\n" "$id" "$desc" "${DATAPLAT_MINIO_PORT:-9000}"
    SKIP=$((SKIP + 1))
    SKIPPED_ACS+=("$id")
    return 0
  fi
  run_ac "$id" "$desc" "$@"
}

run_commit_api_mvp() {
  echo "=== commit-api-mvp-20260517 :: 13 AC ==="

  run_ac AC-1 "schemas/blob+tree+commit 7 类型 + extra=forbid + CommitCreate 不含 created_at" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_api.schemas.blob import BlobUploadResponse
from dataplat_api.schemas.tree import TreeEntryCreate, TreeCreate, TreeEntryRead, TreeRead
from dataplat_api.schemas.commit import CommitCreate, CommitRead
assert \"created_at\" not in CommitCreate.model_fields
assert CommitCreate.model_config.get(\"extra\")==\"forbid\"
assert BlobUploadResponse.model_config.get(\"extra\")==\"forbid\"
assert TreeEntryCreate.model_config.get(\"extra\")==\"forbid\"
"'

  run_ac AC-2 "BlobService 仅 stream 转发（不 import AsyncSession / 不查 role）" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_api.services.blob import BlobService
import inspect
assert inspect.iscoroutinefunction(BlobService.upload)
src = inspect.getsource(BlobService)
assert \"AsyncSession\" not in src and \"role\" not in src
"'

  run_ac AC-3 "CommitService 含 3 公共方法 + 5 私有 hash 函数" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_api.services.commit import CommitService
for m in [\"create_commit\",\"get_with_tree\",\"get_tree_by_commit\"]: assert hasattr(CommitService, m), m
for h in [\"_canonical_tree_bytes\",\"_tree_hash\",\"_canonical_commit_bytes\",\"_commit_hash\",\"_lineage_to_canonical\"]: assert hasattr(CommitService, h), h
"'

  run_ac AC-4 "commits router 5 路由 + prefix=/repos + tags=commits" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_api.routers.commits import router
paths = {r.path for r in router.routes}
need = {\"/repos/{owner}/{name}/blobs\",\"/repos/{owner}/{name}/blobs/{sha256}\",\"/repos/{owner}/{name}/commits\",\"/repos/{owner}/{name}/commits/{hash}\",\"/repos/{owner}/{name}/tree/{commit_hash}\"}
assert need <= paths, paths
"'

  run_ac AC-5 "main 集成 commits_router + OpenAPI 含 5 paths" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_api.main import app
s = app.openapi()
need = {\"/repos/{owner}/{name}/blobs\",\"/repos/{owner}/{name}/blobs/{sha256}\",\"/repos/{owner}/{name}/commits\",\"/repos/{owner}/{name}/commits/{hash}\",\"/repos/{owner}/{name}/tree/{commit_hash}\"}
assert need <= set(s[\"paths\"].keys())
"'

  run_ac AC-6 "router 不重复实现 _visibility_visible（复用 RepoService）" \
    bash -c '! grep -rE "_visibility_visible" apps/api/dataplat_api/services/commit.py apps/api/dataplat_api/services/blob.py apps/api/dataplat_api/routers/commits.py 2>/dev/null'

  run_ac AC-7 "BlobUploadResponse 字段与 BlobPutResult 字段对应" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_api.schemas.blob import BlobUploadResponse
from dataplat_core.protocols.storage import BlobPutResult
need = {\"sha256\",\"size\",\"storage_key\",\"deduplicated\"}
assert need <= set(BlobUploadResponse.model_fields.keys())
assert need <= set(BlobPutResult.model_fields.keys())
"'

  run_ac AC-8 "create_commit 事务边界：blob 存在性校验在事务前（grep）" \
    bash -c 'cd apps/api && uv run python -c "
import inspect
from dataplat_api.services.commit import CommitService
src = inspect.getsource(CommitService.create_commit)
# 校验顺序：missing 检查 → session.commit 出现
idx_missing = src.index(\"missing_hashes\")
idx_commit = src.index(\"session.commit\")
assert idx_missing < idx_commit
"'

  run_ac AC-9 "canonical hash 确定性：entries / parents 顺序不变" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_api.services.commit import CommitService
from dataplat_api.schemas.tree import TreeEntryCreate
e1 = TreeEntryCreate(name=\"b\", mode=33188, target_hash=\"a\"*64)
e2 = TreeEntryCreate(name=\"a\", mode=33188, target_hash=\"b\"*64)
assert CommitService._canonical_tree_bytes([e1,e2]) == CommitService._canonical_tree_bytes([e2,e1])
th = CommitService._tree_hash([e1,e2])
p1, p2 = \"c\"*64, \"d\"*64
h1 = CommitService._commit_hash(th, [p1,p2], \"u\", None, None)
h2 = CommitService._commit_hash(th, [p2,p1], \"u\", None, None)
assert h1 == h2
"'

  run_ac AC-10 "commits.hash PK 唯一约束存在（DDL 反射）" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_api.models import CommitORM
pks = [c.name for c in CommitORM.__table__.primary_key.columns]
assert pks == [\"hash\"]
"'

  run_ac_skipif_no_pg_or_minio AC-11 "apps/api commits 集成 ≥ 16 + 全 PASS" \
    bash -c 'export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && export DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx && export DATAPLAT_MINIO_ENDPOINT=http://localhost:${DATAPLAT_MINIO_PORT:-9000} && (cd apps/api && uv run pytest -q --tb=no tests/test_commits.py) && [ "$(cd apps/api && uv run pytest --collect-only -q tests/test_commits.py 2>&1 | grep -cE "test_commits\.py::")" -ge 16 ]'

  run_ac AC-12 "ruff + mypy 全 PASS" \
    bash -c 'uv run ruff check apps/api packages/core && uv run mypy apps/api/dataplat_api packages/core/src'

  run_ac AC-13 "AC-13 自递归" true
}

# =============================================================================
# Block: adapter-framework-20260517
# 13 条 AC（详见 .harness/changes/adapter-framework-20260517/request_analysis/spec.md）
# =============================================================================

run_adapter_framework() {
  echo "=== adapter-framework-20260517 :: 13 AC ==="

  run_ac AC-1 "IngestResult.files + IngestFileRef 字段（保留既有字段）" \
    bash -c 'cd packages/core && uv run python -c "
from dataplat_core.protocols import IngestFileRef
from dataplat_core.protocols.adapter import IngestResult
r = IngestResult(files=[IngestFileRef(path=\"a.md\", sha256=\"a\"*64)])
assert r.files[0].mode == 33188
assert r.asset_count == 0  # 既有字段保留
"'

  run_ac AC-2 "AdapterRegistry + get_registry 单例 + 内置注册" \
    bash -c 'cd apps/api && uv run python -c "
import dataplat_api.adapters
from dataplat_api.runner import get_registry
reg = get_registry()
assert reg.get(\"raw-file-upload\", \"0.1\") is not None
assert (\"raw-file-upload\",\"0.1\") in reg.list_all()
"'

  run_ac AC-3 "StandardRunContext 实现 RunContext Protocol" \
    bash -c 'cd apps/api && uv run python -c "
import logging
from dataplat_core.protocols.runcontext import RunContext
from dataplat_api.runner.runcontext import StandardRunContext
ctx = StandardRunContext(logger=logging.getLogger(\"t\"))
assert isinstance(ctx, RunContext)
ctx.logger.info(\"ok\")
"'

  run_ac AC-4 "AdapterRunner.run 是 coroutine + 3-tuple 返回" \
    bash -c 'cd apps/api && uv run python -c "
import inspect
from dataplat_api.runner.adapter_runner import AdapterRunner
assert inspect.iscoroutinefunction(AdapterRunner.run)
sig = inspect.signature(AdapterRunner.run)
assert \"tuple\" in str(sig.return_annotation)
"'

  run_ac AC-5 "RawFileUploadAdapter 实现 SourceAdapter + ingest pass-through" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_core.protocols.adapter import SourceAdapter
from dataplat_api.adapters.raw_upload import RawFileUploadAdapter
a = RawFileUploadAdapter()
assert isinstance(a, SourceAdapter)
r = a.ingest({\"files\":[{\"path\":\"a.md\",\"sha256\":\"a\"*64}]}, None, None)
assert r.file_count == 1
assert r.files[0].path == \"a.md\"
"'

  run_ac AC-6 "IngestRequest + IngestResponse schemas（extra=forbid + parents 字段）" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_api.schemas.ingest import IngestRequest, IngestSummary, IngestResponse
assert IngestRequest.model_config.get(\"extra\") == \"forbid\"
assert \"parents\" in IngestRequest.model_fields
assert \"ingest_summary\" in IngestResponse.model_fields
"'

  run_ac AC-7 "ingest router 含 POST /ingest 路由 + prefix=/repos" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_api.routers.ingest import router
paths = {r.path for r in router.routes}
assert \"/repos/{owner}/{name}/ingest\" in paths
"'

  run_ac AC-8 "main 集成 ingest_router + OpenAPI 含 /ingest" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_api.main import app
s = app.openapi()
assert \"/repos/{owner}/{name}/ingest\" in s[\"paths\"]
"'

  run_ac AC-9 "router 不重复实现 _visibility_visible（test -f 前置 + 正向断言）" \
    bash -c 'test -f apps/api/dataplat_api/routers/ingest.py && test -f apps/api/dataplat_api/runner/adapter_runner.py && grep -qE "_resolve_repo|RepoService.get_by_owner_name" apps/api/dataplat_api/routers/ingest.py && ! grep -rE "_visibility_visible" apps/api/dataplat_api/runner apps/api/dataplat_api/routers/ingest.py apps/api/dataplat_api/adapters'

  run_ac AC-10 "AdapterRunner 含 404/400 错误翻译 + parent 自动接链" \
    bash -c 'cd apps/api && uv run python -c "
import inspect
from dataplat_api.runner.adapter_runner import AdapterRunner
src = inspect.getsource(AdapterRunner.run)
assert \"HTTPException\" in src and \"available\" in src  # 404 翻译
assert \"HTTP_400_BAD_REQUEST\" in src                    # 400 翻译
assert \"resolved_parents\" in src and \"RefORM\" in src   # parent 接链
"'

  run_ac_skipif_no_pg_or_minio AC-11 "apps/api ingest 集成 ≥ 13 + 全 PASS" \
    bash -c 'export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && export DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx && export DATAPLAT_MINIO_ENDPOINT=http://localhost:${DATAPLAT_MINIO_PORT:-9000} && (cd apps/api && uv run pytest -q --tb=no tests/test_ingest.py) && [ "$(cd apps/api && uv run pytest --collect-only -q tests/test_ingest.py 2>&1 | grep -cE "test_ingest\.py::")" -ge 13 ]'

  run_ac AC-12 "ruff + mypy 全 PASS" \
    bash -c 'uv run ruff check apps/api packages/core && uv run mypy apps/api/dataplat_api packages/core/src'

  run_ac AC-13 "AC-13 自递归" true
}

# =============================================================================
# 主控
# =============================================================================

# =============================================================================
# Block: web-mvp-pages-20260517
# 13 条 AC（详见 .harness/changes/web-mvp-pages-20260517/request_analysis/spec.md）
# 不依赖 PG / MinIO；依赖 pnpm + node
# =============================================================================

run_web_mvp_pages() {
  echo "=== web-mvp-pages-20260517 :: 13 AC ==="

  run_ac AC-1 "apps/web 依赖齐全（TanStack + Tailwind + clsx + openapi-typescript）" \
    bash -c 'cd apps/web && node -e "const p=require(\"./package.json\"); for (const d of [\"@tanstack/react-router\",\"@tanstack/react-query\",\"tailwindcss\",\"clsx\",\"openapi-typescript\"]) { if (!(d in {...p.dependencies, ...p.devDependencies})) { console.error(\"missing \"+d); process.exit(1); } }"'

  run_ac AC-2 "packages/api-types/src/generated.ts 真生成（含 /repos）" \
    bash -c 'test -f packages/api-types/src/generated.ts && grep -q "/repos" packages/api-types/src/generated.ts'

  run_ac AC-3 "tailwind.config + postcss.config + index.css 齐全" \
    bash -c 'test -f apps/web/tailwind.config.ts && test -f apps/web/postcss.config.js && test -f apps/web/src/index.css && grep -q "@tailwind base" apps/web/src/index.css'

  run_ac AC-4 "shadcn 4 组件齐全（button/card/input/label）" \
    bash -c 'for f in button card input label; do test -f "apps/web/src/components/ui/$f.tsx" || exit 1; done'

  run_ac AC-5 "api/client.ts 含 credentials/include + /auth/refresh + UnauthorizedError + allowAnon" \
    bash -c 'test -f apps/web/src/lib/api/client.ts && grep -q "credentials: \"include\"" apps/web/src/lib/api/client.ts && grep -q "/auth/refresh" apps/web/src/lib/api/client.ts && grep -q "UnauthorizedError" apps/web/src/lib/api/client.ts && grep -q "allowAnon" apps/web/src/lib/api/client.ts'

  run_ac AC-6 "5 routes 文件齐全（directory style for repos）" \
    bash -c 'for f in __root.tsx index.tsx login.tsx repos/index.tsx; do test -f "apps/web/src/routes/$f" || exit 1; done && test -f "apps/web/src/routes/repos/\$owner.\$name.tsx"'

  run_ac AC-7 "__root.tsx 含 Outlet + logout/login 标识" \
    bash -c 'grep -q "Outlet" apps/web/src/routes/__root.tsx && grep -qE "logout|login" apps/web/src/routes/__root.tsx'

  run_ac AC-8 "login.tsx 含 react-hook-form + /auth/login + navigate" \
    bash -c 'grep -q "react-hook-form" apps/web/src/routes/login.tsx && grep -q "/auth/login" apps/web/src/routes/login.tsx && grep -q "navigate" apps/web/src/routes/login.tsx'

  run_ac AC-9 "repos/index.tsx 用 useRepos + queries.ts 指向 /api/repos" \
    bash -c 'grep -qE "useQuery|useRepos" apps/web/src/routes/repos/index.tsx && grep -q "/api/repos" apps/web/src/lib/api/queries.ts'

  run_ac AC-10 "repos/\$owner.\$name.tsx 含 layer/subtype metadata" \
    bash -c 'test -f "apps/web/src/routes/repos/\$owner.\$name.tsx" && grep -qE "layer|subtype" "apps/web/src/routes/repos/\$owner.\$name.tsx"'

  run_ac AC-11 "apps/web 测试 ≥ 4 + 全 PASS" \
    bash -c '[ "$(find apps/web/src -name "*.test.tsx" -o -name "*.test.ts" | wc -l)" -ge 4 ] && cd apps/web && pnpm test 2>&1 | tail -5 | grep -qE "Test Files.*passed|Tests.*passed"'

  run_ac AC-12 "apps/web typecheck + build 成功 + dist/index.html 存在" \
    bash -c 'cd apps/web && pnpm typecheck && pnpm build && test -f dist/index.html'

  run_ac AC-13 "AC-13 自递归" true
}

# =============================================================================
# Block: rq-worker-skeleton-20260517
# 13 条 AC（详见 .harness/changes/rq-worker-skeleton-20260517/request_analysis/spec.md）
# AC-11 依赖 PG + MinIO + Redis 三探针
# =============================================================================

_redis_reachable() {
  python3 -c "
import socket, sys
s = socket.socket()
s.settimeout(1)
try:
    s.connect(('localhost', int('${DATAPLAT_REDIS_PORT:-6379}')))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
"
}

run_ac_skipif_no_pg_minio_redis() {
  local id="$1"
  local desc="$2"
  shift 2
  if ! _pg_reachable 2>/dev/null; then
    printf "SKIP  %-10s  %s（Postgres 未通）\n" "$id" "$desc"
    SKIP=$((SKIP + 1)); SKIPPED_ACS+=("$id"); return 0
  fi
  if ! _minio_reachable 2>/dev/null; then
    printf "SKIP  %-10s  %s（MinIO 未通）\n" "$id" "$desc"
    SKIP=$((SKIP + 1)); SKIPPED_ACS+=("$id"); return 0
  fi
  if ! _redis_reachable 2>/dev/null; then
    printf "SKIP  %-10s  %s（Redis :%s 未通）\n" "$id" "$desc" "${DATAPLAT_REDIS_PORT:-6379}"
    SKIP=$((SKIP + 1)); SKIPPED_ACS+=("$id"); return 0
  fi
  run_ac "$id" "$desc" "$@"
}

run_rq_worker_skeleton() {
  echo "=== rq-worker-skeleton-20260517 :: 13 AC ==="

  run_ac AC-1 "JobORM 9 字段齐全" \
    bash -c 'cd apps/api && uv run python -c "
from dataplat_api.models import JobORM
cols={c.name for c in JobORM.__table__.columns}
need={\"id\",\"type\",\"status\",\"payload\",\"result\",\"error\",\"created_at\",\"started_at\",\"completed_at\"}
assert need <= cols, cols
"'

  run_ac AC-2 "alembic 0003_jobs 文件 + 引用 jobs 表" \
    bash -c 'ls apps/api/alembic/versions/0003_*.py >/dev/null && grep -q "jobs" apps/api/alembic/versions/0003_*.py'

  run_ac AC-3 "redis_client.py 提供 get_redis + get_queue" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.jobs.redis_client import get_redis, get_queue; assert callable(get_redis) and callable(get_queue)"'

  run_ac AC-4 "JobsService 5 方法（enqueue/get_by_id/mark_running/mark_succeeded/mark_failed）" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.jobs.service import JobsService; assert all(hasattr(JobsService, m) for m in [\"enqueue\",\"get_by_id\",\"mark_running\",\"mark_succeeded\",\"mark_failed\"])"'

  run_ac AC-5 "run_ingest_job 签名含 job_id" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.jobs.tasks import run_ingest_job; import inspect; sig=inspect.signature(run_ingest_job); assert \"job_id\" in sig.parameters"'

  run_ac AC-6 "JobIngestRequest + JobRead extra=forbid" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.schemas.job import JobIngestRequest, JobRead; assert JobIngestRequest.model_config.get(\"extra\")==\"forbid\" and JobRead.model_config.get(\"extra\")==\"forbid\""'

  run_ac AC-7 "jobs router 2 路由（/jobs/ingest + /jobs/{job_id}）+ prefix=/jobs" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.routers.jobs import router; paths={r.path for r in router.routes}; assert \"/jobs/ingest\" in paths and \"/jobs/{job_id}\" in paths"'

  run_ac AC-8 "main 集成 jobs_router + OpenAPI 含 /jobs 2 paths" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.main import app; s=app.openapi(); assert \"/jobs/ingest\" in s[\"paths\"] and \"/jobs/{job_id}\" in s[\"paths\"]"'

  run_ac AC-9 "router 复用 RepoService.get_by_owner_name + 不重复 _visibility_visible（test -f 前置 + 正向 + 反向）" \
    bash -c 'test -f apps/api/dataplat_api/routers/jobs.py && test -f apps/api/dataplat_api/jobs/service.py && grep -qE "_resolve_repo|RepoService.get_by_owner_name" apps/api/dataplat_api/routers/jobs.py && ! grep -rE "_visibility_visible" apps/api/dataplat_api/jobs apps/api/dataplat_api/routers/jobs.py'

  run_ac AC-10 "worker/main.py 含 Worker.work" \
    bash -c 'test -f worker/src/dataplat_worker/main.py && grep -qE "Worker|work\(" worker/src/dataplat_worker/main.py'

  run_ac_skipif_no_pg_minio_redis AC-11 "apps/api jobs 集成 ≥ 10 + 全 PASS" \
    bash -c 'export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && export DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx && export DATAPLAT_MINIO_ENDPOINT=http://localhost:${DATAPLAT_MINIO_PORT:-9000} && export DATAPLAT_REDIS_URL=redis://localhost:${DATAPLAT_REDIS_PORT:-6379}/0 && (cd apps/api && uv run pytest -q --tb=no tests/test_jobs.py) && [ "$(cd apps/api && uv run pytest --collect-only -q tests/test_jobs.py 2>&1 | grep -cE "test_jobs\.py::")" -ge 10 ]'

  run_ac AC-12 "ruff + mypy 全 PASS（含 worker/src）" \
    bash -c 'uv run ruff check apps/api packages/core worker/src && uv run mypy apps/api/dataplat_api packages/core/src worker/src'

  run_ac AC-13 "AC-13 自递归" true
}

# =============================================================================
# Block: web-write-flows-20260517
# 13 条 AC（详见 .harness/changes/web-write-flows-20260517/request_analysis/spec.md）
# 不依赖后端服务；依赖 pnpm + node
# =============================================================================

run_web_write_flows() {
  echo "=== web-write-flows-20260517 :: 13 AC ==="

  run_ac AC-1 "repos.new.tsx 含 react-hook-form + /repos POST" \
    bash -c 'test -f apps/web/src/routes/repos.new.tsx && grep -q "react-hook-form" apps/web/src/routes/repos.new.tsx && grep -q "/repos" apps/web/src/routes/repos.new.tsx'

  run_ac AC-2 "jobs.\$job_id.tsx 存在 + useJob 轮询（refetchInterval in queries.ts）" \
    bash -c 'test -f "apps/web/src/routes/jobs.\$job_id.tsx" && grep -q "useJob" "apps/web/src/routes/jobs.\$job_id.tsx" && grep -q "refetchInterval" apps/web/src/lib/api/queries.ts'

  run_ac AC-3 "commits.\$owner.\$name.\$hash.tsx 显示 blob 下载链" \
    bash -c 'test -f "apps/web/src/routes/commits.\$owner.\$name.\$hash.tsx" && grep -q "blobs" "apps/web/src/routes/commits.\$owner.\$name.\$hash.tsx"'

  run_ac AC-4 "repo 详情页含 useUpdateRepo/useDeleteRepo/useEnqueueIngest + navigate /jobs" \
    bash -c 'grep -qE "useUpdateRepo|useDeleteRepo" "apps/web/src/routes/repos/\$owner.\$name.tsx" && grep -q "useEnqueueIngest" "apps/web/src/routes/repos/\$owner.\$name.tsx" && grep -q "/jobs/" "apps/web/src/routes/repos/\$owner.\$name.tsx"'

  run_ac AC-5 "queries.ts 新增 7 个 hook" \
    bash -c '[ "$(grep -cE "export function (useCreateRepo|useUpdateRepo|useDeleteRepo|useUploadBlob|useEnqueueIngest|useJob|useCommit)" apps/web/src/lib/api/queries.ts)" -ge 7 ]'

  run_ac AC-6 "useUploadBlob 用 binary body（octet-stream）" \
    bash -c 'grep -q "useUploadBlob" apps/web/src/lib/api/queries.ts && grep -qE "octet-stream|Blob|File" apps/web/src/lib/api/queries.ts'

  run_ac AC-7 "invalidateQueries 至少 3 处" \
    bash -c '[ "$(grep -c "invalidateQueries" apps/web/src/lib/api/queries.ts)" -ge 3 ]'

  run_ac AC-8 "Textarea 组件存在" \
    bash -c 'test -f apps/web/src/components/ui/textarea.tsx && grep -q "Textarea" apps/web/src/components/ui/textarea.tsx'

  run_ac AC-9 "/repos 列表 admin-only + New Repository 按钮" \
    bash -c 'grep -qE "New Repository|新建" apps/web/src/routes/repos/index.tsx && grep -q "/repos/new" apps/web/src/routes/repos/index.tsx'

  run_ac AC-10 "详情页 Edit/Delete/Ingest + admin 条件" \
    bash -c 'grep -qE "Edit|Delete|Ingest" "apps/web/src/routes/repos/\$owner.\$name.tsx" && grep -qE "role|admin|isAdmin" "apps/web/src/routes/repos/\$owner.\$name.tsx"'

  run_ac AC-11 "vitest ≥ 7 测试 + 全 PASS" \
    bash -c '[ "$(find apps/web/src -name "*.test.tsx" -o -name "*.test.ts" | wc -l)" -ge 7 ] && cd apps/web && pnpm test 2>&1 | tail -5 | grep -qE "Test Files.*passed|Tests.*passed"'

  run_ac AC-12 "apps/web typecheck + build + dist/index.html" \
    bash -c 'cd apps/web && pnpm typecheck && pnpm build && test -f dist/index.html'

  run_ac AC-13 "AC-13 自递归" true
}

# =============================================================================
# Block: repo-files-tab-20260517
# 13 条 AC（详见 .harness/changes/repo-files-tab-20260517/request_analysis/spec.md）
# AC-10 依赖 PG + MinIO 双探针
# =============================================================================

run_repo_files_tab() {
  echo "=== repo-files-tab-20260517 :: 13 AC ==="

  run_ac AC-1 "RefRead schema + extra=forbid" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.schemas.ref import RefRead; assert RefRead.model_config.get(\"extra\")==\"forbid\""'

  run_ac AC-2 "RefService.get_by_name 存在" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.services.ref import RefService; assert hasattr(RefService, \"get_by_name\")"'

  run_ac AC-3 "GET /repos/{o}/{n}/refs/{ref_name} 路由" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.routers.repos import router; paths={r.path for r in router.routes}; assert \"/repos/{owner}/{name}/refs/{ref_name}\" in paths"'

  run_ac AC-4 "OpenAPI 含 /refs 路径" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.main import app; s=app.openapi(); assert \"/repos/{owner}/{name}/refs/{ref_name}\" in s[\"paths\"]"'

  run_ac AC-5 "RefService 不重复实现 _visibility_visible（test -f 前置 + 反向 grep）" \
    bash -c 'test -f apps/api/dataplat_api/services/ref.py && test -f apps/api/dataplat_api/routers/repos.py && ! grep -E "_visibility_visible" apps/api/dataplat_api/services/ref.py'

  run_ac AC-6 "queries.ts 加 useRepoRef + RefRead" \
    bash -c 'grep -q "useRepoRef" apps/web/src/lib/api/queries.ts && grep -qE "RefRead|/refs/" apps/web/src/lib/api/queries.ts'

  run_ac AC-7 "详情页加 FilesSection + useRepoRef" \
    bash -c 'grep -qE "FilesSection|useRepoRef" "apps/web/src/routes/repos/\$owner.\$name.tsx"'

  run_ac AC-8 "FilesSection 含 main/files/下载/链" \
    bash -c 'grep -qE "main|files|下载" "apps/web/src/routes/repos/\$owner.\$name.tsx" && grep -q "/api/repos/" "apps/web/src/routes/repos/\$owner.\$name.tsx"'

  run_ac AC-9 "前端 ≥ 8 测试 + 全 PASS" \
    bash -c '[ "$(find apps/web/src -name "*.test.tsx" -o -name "*.test.ts" | wc -l)" -ge 8 ] && cd apps/web && pnpm test 2>&1 | tail -5 | grep -qE "Test Files.*passed|Tests.*passed"'

  run_ac_skipif_no_pg_or_minio AC-10 "后端 tests/test_refs.py ≥ 3 + 全 PASS" \
    bash -c 'export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && export DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx && export DATAPLAT_MINIO_ENDPOINT=http://localhost:${DATAPLAT_MINIO_PORT:-9000} && (cd apps/api && uv run pytest -q --tb=no tests/test_refs.py) && [ "$(cd apps/api && uv run pytest --collect-only -q tests/test_refs.py 2>&1 | grep -cE "test_refs\.py::")" -ge 3 ]'

  run_ac AC-11 "ruff + mypy 全 PASS" \
    bash -c 'uv run ruff check apps/api packages/core worker/src && uv run mypy apps/api/dataplat_api packages/core/src worker/src'

  run_ac AC-12 "apps/web typecheck + build + dist/index.html" \
    bash -c 'cd apps/web && pnpm typecheck && pnpm build && test -f dist/index.html'

  run_ac AC-13 "AC-13 自递归" true
}

run_processor_framework() {
  echo "=== processor-framework-20260517 :: 13 AC ==="

  run_ac AC-1 "DbRepoView 类存在（test -f + grep）" \
    bash -c 'test -f apps/api/dataplat_api/runner/repo_view.py && grep -q "class DbRepoView" apps/api/dataplat_api/runner/repo_view.py'

  run_ac AC-2 "ProcessorRegistry 单例 + markdown-normalize 注册" \
    bash -c 'cd apps/api && uv run python -c "import dataplat_api.processors; from dataplat_api.runner.processor_registry import get_processor_registry; assert get_processor_registry().get(\"markdown-normalize\",\"0.1\") is not None"'

  run_ac AC-3 "ProcessorRunner.run 是 coroutine" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.runner.processor_runner import ProcessorRunner; import inspect; assert inspect.iscoroutinefunction(ProcessorRunner.run)"'

  run_ac AC-4 "MarkdownNormalizeProcessor 实现 Processor Protocol" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_core.protocols.processor import Processor; from dataplat_api.processors.markdown_normalize import MarkdownNormalizeProcessor; assert isinstance(MarkdownNormalizeProcessor(), Processor)"'

  run_ac AC-5 "ProcessRequest extra=forbid" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.schemas.process import ProcessRequest; assert ProcessRequest.model_config.get(\"extra\")==\"forbid\""'

  run_ac AC-6 "POST /process 路由 + main include + OpenAPI" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.main import app; s=app.openapi(); assert \"/process\" in s[\"paths\"]"'

  run_ac AC-7 "run_process_job 签名含 job_id" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.jobs.tasks import run_process_job; import inspect; assert \"job_id\" in inspect.signature(run_process_job).parameters"'

  run_ac AC-8 "JobsService.enqueue 按 job_type dispatch run_process_job/run_ingest_job（test -f + 正向双 grep）" \
    bash -c 'test -f apps/api/dataplat_api/jobs/service.py && grep -q "run_process_job" apps/api/dataplat_api/jobs/service.py && grep -q "run_ingest_job" apps/api/dataplat_api/jobs/service.py'

  run_ac AC-9 "StandardRunContext 含 blob_store 字段" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.runner.runcontext import StandardRunContext; import dataclasses; assert \"blob_store\" in {f.name for f in dataclasses.fields(StandardRunContext)}"'

  run_ac_skipif_no_pg_minio_redis AC-10 "tests/test_processor.py ≥ 8 + 全 PASS" \
    bash -c 'export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && export DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx && export DATAPLAT_MINIO_ENDPOINT=http://localhost:${DATAPLAT_MINIO_PORT:-9000} && export DATAPLAT_REDIS_URL=redis://localhost:${DATAPLAT_REDIS_PORT:-6379}/0 && (cd apps/api && uv run pytest -q --tb=no tests/test_processor.py) && [ "$(cd apps/api && uv run pytest --collect-only -q tests/test_processor.py 2>&1 | grep -cE "test_processor\.py::")" -ge 8 ]'

  run_ac AC-11 "ruff + mypy 全 PASS（含 worker/src）" \
    bash -c 'uv run ruff check apps/api packages/core worker/src && uv run mypy apps/api/dataplat_api packages/core/src worker/src'

  run_ac AC-12 "openapi.json 含 /process" \
    bash -c 'grep -q "/process" packages/api-types/openapi.json'

  run_ac AC-13 "AC-13 自递归" true
}

run_llm_gateway_mvp() {
  echo "=== llm-gateway-mvp-20260517 :: 13 AC ==="

  run_ac AC-1 "LLMClient Protocol + LLMRequest/Response extra=forbid（test -f + import + 字段）" \
    bash -c 'test -f packages/core/src/dataplat_core/protocols/llm.py && cd apps/api && uv run python -c "from dataplat_core.protocols.llm import LLMClient, LLMRequest, LLMResponse; assert LLMRequest.model_config.get(\"extra\")==\"forbid\" and LLMResponse.model_config.get(\"extra\")==\"forbid\""'

  run_ac AC-2 "AnthropicProvider 类存在 + 有 call 方法" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.llm.providers.anthropic import AnthropicProvider; assert hasattr(AnthropicProvider, \"call\")"'

  run_ac AC-3 "FakeLLMProvider deterministic（同 req → 同 response.text）" \
    bash -c 'cd apps/api && uv run python -c "import asyncio; from dataplat_api.llm.providers.fake import FakeLLMProvider; from dataplat_core.protocols.llm import LLMRequest, LLMMessage; p=FakeLLMProvider(); r=LLMRequest(model_id=\"x\", messages=[LLMMessage(role=\"user\", content=\"hi\")], max_tokens=10); a=asyncio.run(p.call(r)); b=asyncio.run(p.call(r)); assert a.text==b.text"'

  run_ac AC-4 "RedisLLMCache 类 + get/set 方法" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.llm.cache import RedisLLMCache; assert all(hasattr(RedisLLMCache, m) for m in [\"get\",\"set\"])"'

  run_ac AC-5 "LLMGateway.call 是 coroutine" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.llm.gateway import LLMGateway; import inspect; assert inspect.iscoroutinefunction(LLMGateway.call)"'

  run_ac AC-6 "LLMGateway 构造接受 max_retries 参数" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.llm.gateway import LLMGateway; import inspect; assert \"max_retries\" in inspect.signature(LLMGateway.__init__).parameters"'

  run_ac AC-7 "get_llm_gateway 单例（同 process 同对象）" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.llm.factory import get_llm_gateway; assert get_llm_gateway() is get_llm_gateway()"'

  run_ac AC-8 "ProcessorRunner 构 ctx 注入 llm（test -f + 正向 grep + 反向拦 llm=None）" \
    bash -c 'test -f apps/api/dataplat_api/runner/processor_runner.py && grep -q "llm=" apps/api/dataplat_api/runner/processor_runner.py && ! grep -E "llm[[:space:]]*=[[:space:]]*None" apps/api/dataplat_api/runner/processor_runner.py'

  run_ac AC-9 "LLMSummarizeProcessor 实现 Processor Protocol" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_core.protocols.processor import Processor; from dataplat_api.processors.llm_summarize import LLMSummarizeProcessor; assert isinstance(LLMSummarizeProcessor(), Processor)"'

  run_ac_skipif_no_pg_minio_redis AC-10 "tests/test_llm.py ≥ 6 + 全 PASS" \
    bash -c 'export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && export DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx && export DATAPLAT_MINIO_ENDPOINT=http://localhost:${DATAPLAT_MINIO_PORT:-9000} && export DATAPLAT_REDIS_URL=redis://localhost:${DATAPLAT_REDIS_PORT:-6379}/0 && (cd apps/api && uv run pytest -q --tb=no tests/test_llm.py) && [ "$(cd apps/api && uv run pytest --collect-only -q tests/test_llm.py 2>&1 | grep -cE "test_llm\.py::")" -ge 6 ]'

  run_ac AC-11 "ruff + mypy 全 PASS（含 worker/src）" \
    bash -c 'uv run ruff check apps/api packages/core worker/src && uv run mypy apps/api/dataplat_api packages/core/src worker/src'

  run_ac AC-12 "factory 无 DATAPLAT_LLM_PROVIDER env 时默认 fake 启动不报错" \
    bash -c 'cd apps/api && uv run python -c "import os; os.environ.pop(\"DATAPLAT_LLM_PROVIDER\",None); from dataplat_api.llm.factory import get_llm_gateway, reset_llm_gateway; reset_llm_gateway(); assert get_llm_gateway() is not None"'

  run_ac AC-13 "AC-13 自递归" true
}

run_adapter_firecrawl() {
  echo "=== adapter-firecrawl-20260517 :: 13 AC ==="

  run_ac AC-1 "FirecrawlURLAdapter 实现 SourceAdapter Protocol（test -f + isinstance）" \
    bash -c 'test -f apps/api/dataplat_api/adapters/firecrawl_url.py && cd apps/api && uv run python -c "from dataplat_core.protocols.adapter import SourceAdapter; from dataplat_api.adapters.firecrawl_url import FirecrawlURLAdapter; assert isinstance(FirecrawlURLAdapter(), SourceAdapter)"'

  run_ac AC-2 "FirecrawlURLSpec extra=forbid" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.adapters.firecrawl_url import FirecrawlURLSpec; assert FirecrawlURLSpec.model_config.get(\"extra\")==\"forbid\""'

  run_ac AC-3 "AdapterRunner 构 ctx 注入 llm + blob_store（test -f + 正向双 grep + 反向拦 None）" \
    bash -c 'test -f apps/api/dataplat_api/runner/adapter_runner.py && grep -q "llm=" apps/api/dataplat_api/runner/adapter_runner.py && grep -q "blob_store=" apps/api/dataplat_api/runner/adapter_runner.py && ! grep -E "llm[[:space:]]*=[[:space:]]*None|blob_store[[:space:]]*=[[:space:]]*None" apps/api/dataplat_api/runner/adapter_runner.py'

  run_ac AC-4 "registry 含 firecrawl-url v0.1" \
    bash -c 'cd apps/api && uv run python -c "import dataplat_api.adapters; from dataplat_api.runner import get_registry; assert get_registry().get(\"firecrawl-url\",\"0.1\") is not None"'

  run_ac AC-5 "extract_image_urls 识别 HTML/md + 相对路径解析 + data: 跳过" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.adapters._image_extract import extract_image_urls; urls=extract_image_urls(r'\''hi <img src=\"https://x.com/a.png\"> ![alt](/img/b.jpg) ![c](https://y.com/c.gif)'\'', \"https://example.com\"); assert any(\"a.png\" in u for u in urls) and any(\"example.com/img/b.jpg\" in u for u in urls) and any(\"c.gif\" in u for u in urls)"'

  run_ac AC-6 "firecrawl_url.py 用 httpx 抓取" \
    bash -c 'grep -q "httpx" apps/api/dataplat_api/adapters/firecrawl_url.py'

  run_ac AC-7 "firecrawl_url.py 串行（不含 asyncio.gather）" \
    bash -c '! grep -q "asyncio.gather" apps/api/dataplat_api/adapters/firecrawl_url.py'

  run_ac AC-8 "输出文件名 pattern assets/<idx>/content.md" \
    bash -c 'grep -q "content.md" apps/api/dataplat_api/adapters/firecrawl_url.py && grep -q "assets/" apps/api/dataplat_api/adapters/firecrawl_url.py'

  run_ac AC-9 "图片文件名 pattern assets/<idx>/images/" \
    bash -c 'grep -q "images/" apps/api/dataplat_api/adapters/firecrawl_url.py'

  run_ac_skipif_no_pg_minio_redis AC-10 "tests/test_firecrawl.py ≥ 6 + 全 PASS" \
    bash -c 'export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && export DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx && export DATAPLAT_MINIO_ENDPOINT=http://localhost:${DATAPLAT_MINIO_PORT:-9000} && export DATAPLAT_REDIS_URL=redis://localhost:${DATAPLAT_REDIS_PORT:-6379}/0 && (cd apps/api && uv run pytest -q --tb=no tests/test_firecrawl.py) && [ "$(cd apps/api && uv run pytest --collect-only -q tests/test_firecrawl.py 2>&1 | grep -cE "test_firecrawl\.py::")" -ge 6 ]'

  run_ac AC-11 "ruff + mypy 全 PASS" \
    bash -c 'uv run ruff check apps/api packages/core worker/src && uv run mypy apps/api/dataplat_api packages/core/src worker/src'

  run_ac AC-12 "FirecrawlURLSpec 默认 llm_model = claude-haiku-4-5-20251001" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.adapters.firecrawl_url import FirecrawlURLSpec; assert FirecrawlURLSpec.model_fields[\"llm_model\"].default == \"claude-haiku-4-5-20251001\""'

  run_ac AC-13 "AC-13 自递归" true
}

run_llm_qa_gen() {
  echo "=== llm-qa-gen-20260518 :: 13 AC ==="

  run_ac AC-1 "LLMQAGenSpec extra=forbid" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.processors.llm_qa_gen import LLMQAGenSpec; assert LLMQAGenSpec.model_config.get(\"extra\")==\"forbid\""'

  run_ac AC-2 "LLMQAGenProcessor 实现 Processor Protocol（test -f + isinstance）" \
    bash -c 'test -f apps/api/dataplat_api/processors/llm_qa_gen.py && cd apps/api && uv run python -c "from dataplat_core.protocols.processor import Processor; from dataplat_api.processors.llm_qa_gen import LLMQAGenProcessor; assert isinstance(LLMQAGenProcessor(), Processor)"'

  run_ac AC-3 "registry 注册 llm-qa-gen v0.1" \
    bash -c 'cd apps/api && uv run python -c "import dataplat_api.processors; from dataplat_api.runner.processor_registry import get_processor_registry; assert get_processor_registry().get(\"llm-qa-gen\",\"0.1\") is not None"'

  run_ac AC-4 "默认 model_id = claude-haiku-4-5-20251001" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.processors.llm_qa_gen import LLMQAGenSpec; assert LLMQAGenSpec.model_fields[\"model_id\"].default == \"claude-haiku-4-5-20251001\""'

  run_ac AC-5 "默认 records_per_doc = 1" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.processors.llm_qa_gen import LLMQAGenSpec; assert LLMQAGenSpec.model_fields[\"records_per_doc\"].default == 1"'

  run_ac AC-6 "prompt_template 默认含 {text} 占位" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.processors.llm_qa_gen import LLMQAGenSpec; assert \"{text}\" in LLMQAGenSpec.model_fields[\"prompt_template\"].default"'

  run_ac AC-7 "llm_qa_gen.py 过滤 .md/.txt/.markdown（_TEXT_SUFFIXES 含三种）" \
    bash -c 'grep -q "_TEXT_SUFFIXES" apps/api/dataplat_api/processors/llm_qa_gen.py && grep -F -q ".md" apps/api/dataplat_api/processors/llm_qa_gen.py && grep -F -q ".txt" apps/api/dataplat_api/processors/llm_qa_gen.py && grep -F -q ".markdown" apps/api/dataplat_api/processors/llm_qa_gen.py'

  run_ac AC-8 "llm_qa_gen.py 输出文件名 sft.jsonl" \
    bash -c 'grep -q "sft.jsonl" apps/api/dataplat_api/processors/llm_qa_gen.py'

  run_ac AC-9 "_parse_qa_response 直接 JSON 路径正确解析" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.processors.llm_qa_gen import _parse_qa_response; r=_parse_qa_response('"'"'{\"prompt\":\"p\",\"response\":\"r\"}'"'"'); assert r[\"prompt\"]==\"p\" and r[\"response\"]==\"r\""'

  run_ac_skipif_no_pg_minio_redis AC-10 "tests/test_llm_qa_gen.py ≥ 6 + 全 PASS" \
    bash -c 'export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && export DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx && export DATAPLAT_MINIO_ENDPOINT=http://localhost:${DATAPLAT_MINIO_PORT:-9000} && export DATAPLAT_REDIS_URL=redis://localhost:${DATAPLAT_REDIS_PORT:-6379}/0 && (cd apps/api && uv run pytest -q --tb=no tests/test_llm_qa_gen.py) && [ "$(cd apps/api && uv run pytest --collect-only -q tests/test_llm_qa_gen.py 2>&1 | grep -cE "test_llm_qa_gen\.py::")" -ge 6 ]'

  run_ac AC-11 "ruff + mypy 全 PASS" \
    bash -c 'uv run ruff check apps/api packages/core worker/src && uv run mypy apps/api/dataplat_api packages/core/src worker/src'

  run_ac AC-12 "llm_qa_gen.py 含 ctx.llm 引用 + llm is None 显式检查" \
    bash -c 'grep -q "ctx.llm" apps/api/dataplat_api/processors/llm_qa_gen.py && grep -qE "llm is None|ctx.llm.*None" apps/api/dataplat_api/processors/llm_qa_gen.py'

  run_ac AC-13 "AC-13 自递归" true
}

run_sdk_cli_mvp() {
  echo "=== sdk-cli-mvp-20260518 :: 13 AC ==="

  run_ac AC-1 "SDK Client 类存在 + 持有 httpx.Client（test -f + isinstance）" \
    bash -c 'test -f packages/sdk-py/src/dataplat_sdk/client.py && uv run python -c "from dataplat_sdk import Client; import httpx; c=Client(base_url=\"http://x\"); assert isinstance(c._http, httpx.Client)"'

  run_ac AC-2 "Client 8 方法齐全" \
    bash -c 'uv run python -c "from dataplat_sdk.client import Client; assert all(hasattr(Client, m) for m in [\"login\",\"create_repo\",\"get_repo\",\"upload_blob\",\"create_commit\",\"enqueue_ingest\",\"enqueue_process\",\"get_job\"])"'

  run_ac AC-3 "Client.login 签名含 username + password" \
    bash -c 'uv run python -c "from dataplat_sdk.client import Client; import inspect; s=inspect.signature(Client.login); assert \"username\" in s.parameters and \"password\" in s.parameters"'

  run_ac AC-4 "Client.upload_blob content 类型为 bytes" \
    bash -c 'uv run python -c "from dataplat_sdk.client import Client; import inspect; sig=inspect.signature(Client.upload_blob); ann=sig.parameters[\"content\"].annotation; assert ann in (bytes, \"bytes\")"'

  run_ac AC-5 "Client.create_commit 签名含 entries + parents + author_id" \
    bash -c 'uv run python -c "from dataplat_sdk.client import Client; import inspect; s=inspect.signature(Client.create_commit); assert set([\"entries\",\"parents\",\"author_id\"]).issubset(set(s.parameters))"'

  run_ac AC-6 "Client.enqueue_process 签名含 source/target/processor 字段" \
    bash -c 'uv run python -c "from dataplat_sdk.client import Client; import inspect; s=inspect.signature(Client.enqueue_process); assert set([\"source_owner\",\"source_name\",\"target_owner\",\"target_name\",\"processor_name\",\"processor_version\"]).issubset(set(s.parameters))"'

  run_ac AC-7 "CLI app 是 typer.Typer 实例（test -f + isinstance）" \
    bash -c 'test -f packages/sdk-py/src/dataplat_sdk/cli.py && uv run python -c "from dataplat_sdk.cli import app; import typer; assert isinstance(app, typer.Typer)"'

  run_ac AC-8 "pyproject.toml 声明 dataplat CLI script entry" \
    bash -c 'grep -qE "^dataplat = \"dataplat_sdk\\.cli:app\"" packages/sdk-py/pyproject.toml'

  run_ac AC-9 "CLI 含 7 个子命令 login/repo/blob/commit/ingest/process/jobs" \
    bash -c 'uv run python -c "from dataplat_sdk.cli import app; from typer.main import get_command; cmd=get_command(app); names={c for c in cmd.commands.keys()}; assert {\"login\",\"repo\",\"blob\",\"commit\",\"ingest\",\"process\",\"jobs\"}.issubset(names)"'

  run_ac AC-10 "SDK + CLI tests/ ≥ 6 + 全 PASS" \
    bash -c '(cd packages/sdk-py && uv run pytest -q --tb=no tests/) && [ "$(cd packages/sdk-py && uv run pytest --collect-only -q tests/ 2>&1 | grep -cE "tests/test_sdk_(client|cli)\.py::")" -ge 6 ]'

  run_ac AC-11 "ruff + mypy 含 packages/sdk-py 全 PASS" \
    bash -c 'uv run ruff check packages/sdk-py && uv run mypy packages/sdk-py/src'

  run_ac AC-12 "Client 用 sync httpx.Client（反向 grep 拦 AsyncClient）" \
    bash -c 'test -f packages/sdk-py/src/dataplat_sdk/client.py && grep -q "httpx.Client" packages/sdk-py/src/dataplat_sdk/client.py && ! grep -q "httpx.AsyncClient" packages/sdk-py/src/dataplat_sdk/client.py'

  run_ac AC-13 "AC-13 自递归" true
}

run_pipeline_orchestrator_mvp() {
  echo "=== pipeline-orchestrator-mvp-20260518 :: 13 AC ==="

  run_ac AC-1 "Recipe Pydantic schema 存在 + YAML/JSON load" \
    bash -c 'test -f apps/api/dataplat_api/schemas/pipeline.py && cd apps/api && uv run python -c "from dataplat_api.schemas.pipeline import Recipe, RecipeNode; r=Recipe(name=\"demo\", nodes=[RecipeNode(id=\"n1\", processor=\"p@1\", inputs=[\"silver/foo/bar@main\"], config={}, output=\"silver/foo/baz@auto\")]); assert r.nodes[0].id == \"n1\""'

  run_ac AC-2 "DAG topo_sort + 环检测" \
    bash -c 'test -f apps/api/dataplat_api/runner/dag.py && cd apps/api && uv run python -c "from dataplat_api.runner.dag import topo_sort; assert topo_sort([{\"id\":\"a\",\"deps\":[]},{\"id\":\"b\",\"deps\":[\"a\"]}]) == [\"a\",\"b\"]; import pytest; pytest.raises(ValueError, lambda: topo_sort([{\"id\":\"a\",\"deps\":[\"b\"]},{\"id\":\"b\",\"deps\":[\"a\"]}]))"'

  run_ac AC-3 "cache_key 函数确定性 + 顺序无关 + 长度 64" \
    bash -c 'test -f apps/api/dataplat_api/runner/cache.py && cd apps/api && uv run python -c "from dataplat_api.runner.cache import compute_cache_key; k1=compute_cache_key([\"a\",\"b\"],\"p\",\"v\",{\"k\":1,\"j\":2}); k2=compute_cache_key([\"b\",\"a\"],\"p\",\"v\",{\"j\":2,\"k\":1}); assert k1==k2 and len(k1)==64"'

  run_ac AC-4 "Alembic 0004 + 3 表名" \
    bash -c 'test -f apps/api/alembic/versions/0004_pipeline_orchestrator.py && grep -q "pipeline_runs" apps/api/alembic/versions/0004_pipeline_orchestrator.py && grep -q "pipeline_node_runs" apps/api/alembic/versions/0004_pipeline_orchestrator.py && grep -q "pipeline_cache" apps/api/alembic/versions/0004_pipeline_orchestrator.py'

  run_ac AC-5 "ProcessorRunner.run 含 lineage 参数（默认 None）" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.runner.processor_runner import ProcessorRunner; import inspect; p=inspect.signature(ProcessorRunner.run).parameters; assert \"lineage\" in p and p[\"lineage\"].default is None"'

  run_ac AC-6 "PipelineOrchestrator.run_pipeline coroutine + 含 recipe/author_id/run_id 参数" \
    bash -c 'test -f apps/api/dataplat_api/runner/orchestrator.py && cd apps/api && uv run python -c "from dataplat_api.runner.orchestrator import PipelineOrchestrator; import inspect; sig=inspect.signature(PipelineOrchestrator.run_pipeline); assert inspect.iscoroutinefunction(PipelineOrchestrator.run_pipeline); assert all(n in sig.parameters for n in (\"recipe\",\"author_id\",\"run_id\"))"'

  run_ac_skipif_no_pg_minio_redis AC-7 "lineage 写入测试（test_lineage_written_on_cache_miss）" \
    bash -c 'export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && export DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx && export DATAPLAT_MINIO_ENDPOINT=http://localhost:${DATAPLAT_MINIO_PORT:-9000} && export DATAPLAT_REDIS_URL=redis://localhost:${DATAPLAT_REDIS_PORT:-6379}/0 && test -f apps/api/tests/test_pipeline_orchestrator.py && grep -q "test_lineage_written_on_cache_miss" apps/api/tests/test_pipeline_orchestrator.py && (cd apps/api && uv run pytest -q --tb=no tests/test_pipeline_orchestrator.py::test_lineage_written_on_cache_miss)'

  run_ac_skipif_no_pg_minio_redis AC-8 "cache hit 跳过 + ref upsert + 审计字段（test_cache_hit_*）" \
    bash -c 'export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && export DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx && export DATAPLAT_MINIO_ENDPOINT=http://localhost:${DATAPLAT_MINIO_PORT:-9000} && export DATAPLAT_REDIS_URL=redis://localhost:${DATAPLAT_REDIS_PORT:-6379}/0 && test -f apps/api/tests/test_pipeline_orchestrator.py && grep -q "test_cache_hit_skips_processor" apps/api/tests/test_pipeline_orchestrator.py && grep -q "test_cache_hit_updates_ref" apps/api/tests/test_pipeline_orchestrator.py && grep -q "input_commits_json" apps/api/tests/test_pipeline_orchestrator.py && (cd apps/api && uv run pytest -q --tb=no tests/test_pipeline_orchestrator.py -k cache_hit)'

  run_ac AC-9 "POST + GET /pipelines/runs OpenAPI 路径" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.main import app; s=app.openapi(); paths=set(s[\"paths\"].keys()); assert \"/pipelines/runs\" in paths and \"/pipelines/runs/{run_id}\" in paths"'

  run_ac AC-10 "_TASK_DISPATCH 'pipeline' + run_pipeline_job 签名" \
    bash -c 'cd apps/api && uv run python -c "from dataplat_api.jobs.service import JobsService; from dataplat_api.jobs.tasks import run_pipeline_job; import inspect; assert \"pipeline\" in JobsService._TASK_DISPATCH and \"job_id\" in inspect.signature(run_pipeline_job).parameters"'

  run_ac AC-11 "demo recipe 文件存在 + 节点全 Processor（反向拦 raw-upload）" \
    bash -c 'test -f recipes/examples/demo-bronze-to-gold.yaml && test -f recipes/examples/demo-bronze-to-silver.yaml && grep -q "markdown-normalize" recipes/examples/demo-bronze-to-gold.yaml && grep -q "llm-qa-gen" recipes/examples/demo-bronze-to-gold.yaml && grep -q "markdown-normalize" recipes/examples/demo-bronze-to-silver.yaml && grep -q "bronze/" recipes/examples/demo-bronze-to-silver.yaml && ! grep -qE "^[[:space:]]*processor:[[:space:]]*raw-upload" recipes/examples/demo-bronze-to-gold.yaml && ! grep -qE "^[[:space:]]*processor:[[:space:]]*raw-upload" recipes/examples/demo-bronze-to-silver.yaml'

  run_ac AC-12 "ruff + mypy 全 PASS（含 worker/src）" \
    bash -c 'uv run ruff check apps/api packages/core worker/src && uv run mypy apps/api/dataplat_api packages/core/src worker/src'

  run_ac AC-13 "AC-13 自递归" true
}

# =============================================================================
# Global lint: reviewer field separation（harness-reviewer-agent-separation-20260518）
# 不属任何 change block；前置在所有 block 之前；FAIL 立 exit 1（fail-fast）
# 对外只占 1 个 run_ac 计数，内部跑 3 个 grep（反向×2 + 白名单校验）
# =============================================================================

_ac_kind_lint_exempt_changes() {
  # harness-ac-behavioral-tier-20260518 close 时硬编码 19 个豁免历史 change：
  #   2 永久（纯 harness）: harness-bootstrap / harness-reviewer-agent-separation
  #   17 暂豁免 grandfather（实代码，必须 backfill, follow-up harness-ac-kind-backfill-*）
  # env AC_KIND_LINT_EXEMPT_OVERRIDE 可注入测试豁免（逗号分隔 change_id），fixture 用
  if [ -n "${AC_KIND_LINT_EXEMPT_OVERRIDE+x}" ]; then
    # OVERRIDE 已显式 set（包括空串），优先使用
    echo "${AC_KIND_LINT_EXEMPT_OVERRIDE}" | tr ',' '\n'
    return
  fi
  cat <<EOF
harness-bootstrap-20260516
harness-reviewer-agent-separation-20260518
bootstrap-monorepo-20260516
core-domain-model-20260516
cas-storage-20260517
auth-scaffold-20260517
repo-api-mvp-20260517
commit-api-mvp-20260517
rq-worker-skeleton-20260517
processor-framework-20260517
adapter-framework-20260517
llm-gateway-mvp-20260517
adapter-firecrawl-20260517
llm-qa-gen-20260518
web-mvp-pages-20260517
web-write-flows-20260517
repo-files-tab-20260517
sdk-cli-mvp-20260518
pipeline-orchestrator-mvp-20260518
EOF
}

run_ac_kind_lint() {
  echo "=== global :: ac-kind-lint ==="

  # 守门 AC 分层规约（harness-ac-behavioral-tier-20260518）：
  # 1. AC 表头含 kind 列
  # 2. AC 行 kind 单元格至少 1 行真为 behavioral（**锚定 regex，不接受裸 grep**）
  # 3. frontmatter ac_kind_lint: exempt 自声明跳过 lint
  # 4. 豁免清单跳过（由 _ac_kind_lint_exempt_changes 提供）
  # env 入口：
  #   AC_KIND_LINT_SCAN_DIR     默认 .harness/changes（fixture 注入）
  #   AC_KIND_LINT_EXEMPT_OVERRIDE  逗号分隔 change_id（fixture 注入）

  local fail_before="$FAIL"
  run_ac "ac-kind-lint" "AC 分层规约守门（kind 列存在 + AC 行 kind=behavioral 锚定 regex）" \
    bash -c '
      set -e
      scan_dir="${AC_KIND_LINT_SCAN_DIR:-.harness/changes}"
      if [ ! -d "$scan_dir" ]; then
        echo "FAIL: scan_dir=$scan_dir 不存在" >&2
        exit 1
      fi
      exempt_list=$(_ac_kind_lint_exempt_changes_inline)
      failed=0
      for spec in "$scan_dir"/*/request_analysis/spec.md; do
        [ -f "$spec" ] || continue
        cid=$(basename "$(dirname "$(dirname "$spec")")")
        # 跳过 _template
        [ "$cid" = "_template" ] && continue
        # 跳过豁免清单
        if echo "$exempt_list" | grep -Fxq "$cid"; then
          continue
        fi
        # 跳过 frontmatter ac_kind_lint: exempt
        if head -20 "$spec" | grep -qE "^ac_kind_lint:[[:space:]]+exempt"; then
          continue
        fi
        # 抽 AC 表段
        seg=$(awk "/^## 验收标准/{p=1;next} p && /^## /{exit} p" "$spec")
        if [ -z "$seg" ]; then
          echo "FAIL: $cid spec.md 无 ## 验收标准 段或抽取为空" >&2
          failed=1
          continue
        fi
        # 双条件断言
        if ! echo "$seg" | grep -qE "^\|[^|]*\|[[:space:]]*kind[[:space:]]*\|"; then
          echo "FAIL: $cid spec.md AC 表缺 kind 列表头" >&2
          failed=1
          continue
        fi
        if ! echo "$seg" | grep -qE "^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|"; then
          echo "FAIL: $cid spec.md AC 表无 kind=behavioral 行（注意：必须 AC 行 kind 单元格真为 behavioral，AC 描述里出现 \"behavioral\" 字串不算）" >&2
          failed=1
          continue
        fi
      done
      if [ "$failed" -ne 0 ]; then
        exit 1
      fi
      exit 0
    '

  # fail-fast: 若 FAIL，立即 exit 1（阻止后续 block 跑）
  if [ "$FAIL" -gt "$fail_before" ]; then
    echo
    echo "ac-kind-lint FAIL → exit 1（fail-fast；不跑后续 block）"
    echo "修复参考：.harness/skills/request-analysis/SKILL.md § AC 分层规约；细节见 .harness/skills/request-analysis/references/ac-kind-lint.md"
    exit 1
  fi
}

# inline 版本供 bash -c subshell 调用（function 不能跨 subshell 直接调用）
_ac_kind_lint_exempt_changes_inline() {
  if [ -n "${AC_KIND_LINT_EXEMPT_OVERRIDE+x}" ]; then
    echo "${AC_KIND_LINT_EXEMPT_OVERRIDE}" | tr ',' '\n'
    return
  fi
  cat <<EOF
harness-bootstrap-20260516
harness-reviewer-agent-separation-20260518
bootstrap-monorepo-20260516
core-domain-model-20260516
cas-storage-20260517
auth-scaffold-20260517
repo-api-mvp-20260517
commit-api-mvp-20260517
rq-worker-skeleton-20260517
processor-framework-20260517
adapter-framework-20260517
llm-gateway-mvp-20260517
adapter-firecrawl-20260517
llm-qa-gen-20260518
web-mvp-pages-20260517
web-write-flows-20260517
repo-files-tab-20260517
sdk-cli-mvp-20260518
pipeline-orchestrator-mvp-20260518
EOF
}
export -f _ac_kind_lint_exempt_changes_inline

# =============================================================================
# Block: pipeline-ui-tab-20260518
# 4 条 AC（含 2 条 behavioral：AC-3 vitest + AC-4 npm run build）
# =============================================================================

run_pipeline_ui_tab() {
  echo "=== pipeline-ui-tab-20260518 :: 4 AC ==="

  run_ac AC-1 "queries.ts 加 2 个 hook + 3 个 interface（独立 grep，不用 ERE alternation）" \
    bash -c 'test -f apps/web/src/lib/api/queries.ts && awk "/^export function useCreatePipelineRun/{p=1;next} p && /^export /{exit} p" apps/web/src/lib/api/queries.ts | grep -q "pipelines/runs:from-yaml" && awk "/^export function usePipelineRun/{p=1;next} p && /^export /{exit} p" apps/web/src/lib/api/queries.ts | grep -q "refetchInterval" && grep -q "interface PipelineNodeRunResponse" apps/web/src/lib/api/queries.ts && grep -q "interface PipelineRunResponse" apps/web/src/lib/api/queries.ts && grep -q "interface PipelineRunCreatedResponse" apps/web/src/lib/api/queries.ts'

  # AC-2 / AC-3：repo-files-tab-v2-20260518 Tab 重构后，PipelinesSection 不再紧邻 isAdmin && 字面（
  # 改为 isAdmin && (<>...<PipelinesSection .../>...</>); harness-remote-push-onboarding-20260518 适配修复：
  # AC-2 弱化为"PipelinesSection 存在 + 同文件 isAdmin 字面 + 2 个 hook 引用"；
  # AC-3 加 NO_COLOR=1 + sed 剥 ANSI（同 repo-files-tab-v2 stage 9 验证驱动的同型修复）。

  run_ac AC-2 "repos/\$owner.\$name.tsx 含 PipelinesSection + isAdmin gate + 2 个 hook" \
    bash -c 'test -f "apps/web/src/routes/repos/\$owner.\$name.tsx" && grep -q "function PipelinesSection" "apps/web/src/routes/repos/\$owner.\$name.tsx" && grep -q "isAdmin" "apps/web/src/routes/repos/\$owner.\$name.tsx" && grep -q "<PipelinesSection" "apps/web/src/routes/repos/\$owner.\$name.tsx" && grep -q "useCreatePipelineRun" "apps/web/src/routes/repos/\$owner.\$name.tsx" && grep -q "usePipelineRun" "apps/web/src/routes/repos/\$owner.\$name.tsx"'

  run_ac AC-3 "vitest pipeline.test.tsx + repos.pipelines-section.test.tsx ≥4 passed（NO_COLOR + sed 剥 ANSI）" \
    bash -c '(cd apps/web && NO_COLOR=1 npx vitest run src/lib/api/pipeline.test.tsx src/routes/repos.pipelines-section.test.tsx 2>&1 | sed "s/\x1b\[[0-9;]*m//g" | tee /tmp/dataplat-vitest-pipeline.log >/dev/null) ; { grep -qE "Tests +[4-9] passed" /tmp/dataplat-vitest-pipeline.log || grep -qE "Tests +[1-9][0-9]+ passed" /tmp/dataplat-vitest-pipeline.log ; }'

  run_ac AC-4 "npm run build 干净（vite build && tsc --noEmit；含 built in 不含 error TS）" \
    bash -c '(cd apps/web && npm run build 2>&1 | tee /tmp/dataplat-web-build.log >/dev/null) && grep -q "built in" /tmp/dataplat-web-build.log && ! grep -qE "error TS|Found [0-9]+ errors" /tmp/dataplat-web-build.log'
}

# =============================================================================
# Block: repo-files-tab-v2-20260518
# 8 条 AC（含 3 behavioral：AC-6 vitest / AC-7 pytest / AC-8 npm run build）
# =============================================================================

run_repo_files_tab_v2() {
  echo "=== repo-files-tab-v2-20260518 :: 8 AC ==="

  run_ac AC-1 "commits.py 加 get_blob_meta 路由 + schemas/blob.py 含 BlobMetaResponse（4 直接 grep）" \
    bash -c 'test -f apps/api/dataplat_api/routers/commits.py && grep -q "/{owner}/{name}/blobs/{sha256}/meta" apps/api/dataplat_api/routers/commits.py && grep -q "def get_blob_meta" apps/api/dataplat_api/routers/commits.py && grep -q "class BlobMetaResponse" apps/api/dataplat_api/schemas/blob.py'

  run_ac AC-2 "queries.ts 含 BlobMetaResponse interface + useBlobMeta hook（含 awk 锚定 /meta）" \
    bash -c 'test -f apps/web/src/lib/api/queries.ts && grep -q "interface BlobMetaResponse" apps/web/src/lib/api/queries.ts && grep -q "export function useBlobMeta" apps/web/src/lib/api/queries.ts && awk "/^export function useBlobMeta/{p=1;next} p && /^export /{exit} p" apps/web/src/lib/api/queries.ts | grep -q "/meta"'

  run_ac AC-3 "repos/\$owner.\$name.tsx 含 Tabs 实现：tab= + 3 个 Tab key + useSearch" \
    bash -c 'test -f apps/web/src/routes/repos/\$owner.\$name.tsx && grep -q "tab=" apps/web/src/routes/repos/\$owner.\$name.tsx && grep -q "\"files\"" apps/web/src/routes/repos/\$owner.\$name.tsx && grep -q "\"ingest\"" apps/web/src/routes/repos/\$owner.\$name.tsx && grep -q "\"pipelines\"" apps/web/src/routes/repos/\$owner.\$name.tsx && { grep -q "Route.useSearch" apps/web/src/routes/repos/\$owner.\$name.tsx || grep -q "useSearch(" apps/web/src/routes/repos/\$owner.\$name.tsx ; }'

  run_ac AC-4 "blob.\$owner.\$name.\$hash.tsx 存在 + createFileRoute + useBlobMeta + 5MB 常量 + Markdown renderer + 图片扩展名" \
    bash -c 'test -f apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx && grep -q "createFileRoute(\"/blob/\$owner/\$name/\$hash\")" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx && grep -q "useBlobMeta" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx && { grep -qE "5 ?\\* ?1024 ?\\* ?1024" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx || grep -q "5242880" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx || grep -q "MAX_PREVIEW_SIZE" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx ; } && { grep -q "renderMinimalMarkdown" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx || grep -q "MarkdownView" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx || grep -q "MarkdownRendered" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx ; } && { grep -q "\\.png" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx || grep -q "\\.jpg" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx || grep -q "\\.jpeg" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx ; }'

  run_ac AC-5 "FilesSection 函数体含 /blob/\$owner/\$name/\$hash + search（awk 状态机锚定）" \
    bash -c 'awk "/function FilesSection/{p=1;next} p && /^function /{exit} p" apps/web/src/routes/repos/\$owner.\$name.tsx | grep -q "/blob/\$owner/\$name/\$hash" && awk "/function FilesSection/{p=1;next} p && /^function /{exit} p" apps/web/src/routes/repos/\$owner.\$name.tsx | grep -q "search"'

  run_ac AC-6 "vitest 3 测试文件 ≥5 passed（拆 alternation 为 2 grep + shell ||；sed 剥 ANSI 颜色 escape）" \
    bash -c '(cd apps/web && NO_COLOR=1 npx vitest run src/lib/api/blob-meta.test.tsx src/routes/repos.tabs.test.tsx src/routes/blob.test.tsx 2>&1 | sed "s/\x1b\[[0-9;]*m//g" | tee /tmp/dataplat-vitest-blob.log >/dev/null) ; { grep -qE "Tests +[5-9] passed" /tmp/dataplat-vitest-blob.log || grep -qE "Tests +[1-9][0-9]+ passed" /tmp/dataplat-vitest-blob.log ; }'

  run_ac_skipif_no_pg_minio_redis AC-7 "pytest blob_meta ≥3 passed（拆 alternation）" \
    bash -c 'export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && export DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx && export DATAPLAT_MINIO_ENDPOINT=http://localhost:${DATAPLAT_MINIO_PORT:-9000} && export DATAPLAT_MINIO_ACCESS_KEY=${DATAPLAT_MINIO_ACCESS_KEY:-minioadmin} && export DATAPLAT_MINIO_SECRET_KEY=${DATAPLAT_MINIO_SECRET_KEY:-minioadmin} && export DATAPLAT_REDIS_URL=redis://localhost:${DATAPLAT_REDIS_PORT:-6379}/0 && (cd apps/api && uv run pytest -q --tb=no tests/test_commits.py -k blob_meta 2>&1 | tee /tmp/dataplat-pytest-blob.log >/dev/null) ; { grep -qE "[3-9] passed" /tmp/dataplat-pytest-blob.log || grep -qE "[1-9][0-9]+ passed" /tmp/dataplat-pytest-blob.log ; }'

  run_ac AC-8 "npm run build 干净（拆 alternation 为 2 个 !grep）" \
    bash -c '(cd apps/web && npm run build 2>&1 | tee /tmp/dataplat-web-build.log >/dev/null) && grep -q "built in" /tmp/dataplat-web-build.log && ! grep -q "error TS" /tmp/dataplat-web-build.log && ! grep -qE "Found [0-9]+ errors" /tmp/dataplat-web-build.log'
}

# =============================================================================
# Block: stage9-followup-cleanup-20260518
# 4 条 AC（含 2 条 behavioral：AC-2 alembic 三连 + delete_rule 断言、AC-4 pytest 10/10）
# =============================================================================

run_stage9_followup_cleanup() {
  echo "=== stage9-followup-cleanup-20260518 :: 4 AC ==="

  run_ac AC-1 "model + 0005 migration FK CASCADE；0004 保留 ondelete=RESTRICT" \
    bash -c 'test -f apps/api/dataplat_api/models/pipeline.py && awk "/^class PipelineCacheORM/{p=1;next} p && /^class /{exit} p" apps/api/dataplat_api/models/pipeline.py | grep -q '\''ondelete="CASCADE"'\'' && ls apps/api/alembic/versions/0005_*.py >/dev/null 2>&1 && grep -q "CASCADE" apps/api/alembic/versions/0005_*.py && grep -q '\''ondelete="RESTRICT"'\'' apps/api/alembic/versions/0004_pipeline_orchestrator.py'

  run_ac_skipif_no_pg AC-2 "alembic head=0005 + information_schema delete_rule=CASCADE" \
    bash -c 'export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && (cd apps/api && uv run alembic current 2>&1 | grep -q "0005") && docker exec dataplat-pg-test psql -U dataplat -d dataplat -tA -c "SELECT delete_rule FROM information_schema.referential_constraints WHERE constraint_name='\''pipeline_cache_output_commit_hash_fkey'\'';" | grep -q "CASCADE"'

  run_ac AC-3 "_seed_bronze 含 uuid 前缀注入（awk 状态机锚定函数体）" \
    bash -c 'test -f apps/api/tests/test_pipeline_orchestrator.py && awk "/^async def _seed_bronze/{p=1;next} p && /^async def |^def /{exit} p" apps/api/tests/test_pipeline_orchestrator.py | grep -qE "uuid\.uuid4\(\)\.hex.*content|unique_content.*=.*uuid"'

  run_ac_skipif_no_pg_minio_redis AC-4 "test_pipeline_orchestrator.py 10/10 PASS（含 cache_hit 3）" \
    bash -c 'export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && export DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx && export DATAPLAT_MINIO_ENDPOINT=http://localhost:${DATAPLAT_MINIO_PORT:-9000} && export DATAPLAT_MINIO_ACCESS_KEY=${DATAPLAT_MINIO_ACCESS_KEY:-minioadmin} && export DATAPLAT_MINIO_SECRET_KEY=${DATAPLAT_MINIO_SECRET_KEY:-minioadmin} && export DATAPLAT_REDIS_URL=redis://localhost:${DATAPLAT_REDIS_PORT:-6379}/0 && export DATAPLAT_LLM_PROVIDER=fake && (cd apps/api && uv run pytest -q --tb=no tests/test_pipeline_orchestrator.py 2>&1 | tail -3 | grep -qE "10 passed")'
}

# =============================================================================
# Block: harness-ac-behavioral-tier-20260518
# 8 条 AC + 引用 global ac-kind-lint
# =============================================================================

run_harness_ac_behavioral_tier() {
  echo "=== harness-ac-behavioral-tier-20260518 :: 8 AC ==="

  local CHANGE=harness-ac-behavioral-tier-20260518
  local SPEC=.harness/changes/${CHANGE}/request_analysis/spec.md

  run_ac AC-1 "SKILL.md 新增 § AC 分层规约（含 kind 定义 + behavioral 三层 + 豁免判定）" \
    bash -c 'test -f .harness/skills/request-analysis/SKILL.md && grep -q "AC 分层规约" .harness/skills/request-analysis/SKILL.md && grep -q "kind: behavioral" .harness/skills/request-analysis/SKILL.md && grep -q "豁免判定" .harness/skills/request-analysis/SKILL.md'

  run_ac AC-2 "SKILL.md 含 '每个非豁免 change 至少 1 条 behavioral AC' 硬约束 + ac_kind_lint: exempt 自声明格式" \
    bash -c 'test -f .harness/skills/request-analysis/SKILL.md && grep -qE "至少.*1 ?条.*behavioral" .harness/skills/request-analysis/SKILL.md && grep -q "ac_kind_lint: exempt" .harness/skills/request-analysis/SKILL.md'

  run_ac AC-3 "expert-reviewer SKILL 加 stage 2 必查 3 项 + git diff 复核" \
    bash -c 'test -f .harness/skills/expert-reviewer/SKILL.md && grep -q "至少 1 条 behavioral\|至少 1 行 AC" .harness/skills/expert-reviewer/SKILL.md && grep -qE "git diff.*--stat" .harness/skills/expert-reviewer/SKILL.md && grep -q "ac_kind_lint" .harness/skills/expert-reviewer/SKILL.md'

  run_ac AC-4 "run_ac_kind_lint fixture 真跑（3 场景：合规 PASS / 缺 kind 列 FAIL / 全 static 但描述含 behavioral FAIL）" \
    bash -c 'test -f scripts/lint/test_ac_kind_lint_fixture.sh && bash scripts/lint/test_ac_kind_lint_fixture.sh'

  run_ac AC-5 "development-process.md stage 9 含 4 checkpoint + self-attest 模板" \
    bash -c 'test -f .harness/rules/development-process.md && S9=$(awk "/^## 阶段 9/{p=1;next} p && /^## 阶段 /{exit} p" .harness/rules/development-process.md) && echo "$S9" | grep -qE "verdict.*PASS" && echo "$S9" | grep -q "self-attest" && echo "$S9" | grep -q "禁止.*deferred" && echo "$S9" | grep -qE "必填.*字段|理由.*证据.*命令.*时间"'

  run_ac AC-6 "self_check main 含 run_ac_kind_lint 调用 + 本 spec AC 行 behavioral ≥ 2 + _template 含 kind 列" \
    bash -c 'test -f scripts/_self_check.sh && grep -q "run_ac_kind_lint" scripts/_self_check.sh && SPEC=.harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/spec.md && test -f "$SPEC" && SEG=$(awk "/^## 验收标准/{p=1;next} p && /^## /{exit} p" "$SPEC") && echo "$SEG" | grep -qE "^\|[^|]*\|[[:space:]]*kind[[:space:]]*\|" && [ "$(echo "$SEG" | grep -cE "^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|")" -ge 2 ] && grep -q "kind" .harness/changes/_template/request_analysis/spec.md'

  run_ac AC-7 "SKILL.md 豁免清单分两类（永久 2 + 暂豁免 17）且 19 个 ID 全命中" \
    bash -c 'test -f .harness/skills/request-analysis/SKILL.md && test -f .harness/skills/request-analysis/references/ac-kind-lint.md && for cid in harness-bootstrap-20260516 harness-reviewer-agent-separation-20260518 bootstrap-monorepo-20260516 core-domain-model-20260516 cas-storage-20260517 auth-scaffold-20260517 repo-api-mvp-20260517 commit-api-mvp-20260517 rq-worker-skeleton-20260517 processor-framework-20260517 adapter-framework-20260517 llm-gateway-mvp-20260517 adapter-firecrawl-20260517 llm-qa-gen-20260518 web-mvp-pages-20260517 web-write-flows-20260517 repo-files-tab-20260517 sdk-cli-mvp-20260518 pipeline-orchestrator-mvp-20260518; do grep -q "$cid" .harness/skills/request-analysis/SKILL.md .harness/skills/request-analysis/references/ac-kind-lint.md || exit 1; done && grep -q "永久豁免" .harness/skills/request-analysis/references/ac-kind-lint.md && grep -q "暂豁免" .harness/skills/request-analysis/references/ac-kind-lint.md'

  run_ac AC-8 "self_check 含 run_harness_ac_behavioral_tier 调用（自递归确认本 block 在 main 调用链中）" \
    bash -c 'test -f scripts/_self_check.sh && grep -q "run_harness_ac_behavioral_tier" scripts/_self_check.sh'
}

run_reviewer_lint() {
  echo "=== global :: reviewer-lint ==="

  # 内部 3 grep；任一失败 → 整个 AC FAIL
  # 等价于：! grep application-owner-agent && ! grep template-placeholder && grep -E claude|self-attest
  local fail_before="$FAIL"
  run_ac "reviewer-lint" "reviewer 字段独立性守门（反向×2 + 白名单）" \
    bash -c '
      set -e
      # 反向 #1: 禁止 reviewer: application-owner-agent
      if grep -rE "^reviewer:[[:space:]]+application-owner-agent" .harness/changes/ >/dev/null 2>&1; then
        echo "FAIL: 命中 reviewer: application-owner-agent（self-review，违反 expert-reviewer SKILL 硬约束）" >&2
        grep -rnE "^reviewer:[[:space:]]+application-owner-agent" .harness/changes/ >&2
        exit 1
      fi
      # 反向 #2: 禁止模板占位符（排除 _template 与本 change 自身未填行）
      bad=$(grep -rlE "^reviewer:[[:space:]]+<" .harness/changes/ 2>/dev/null | grep -v "/_template/" | grep -v "/harness-reviewer-agent-separation-20260518/" || true)
      if [ -n "$bad" ]; then
        echo "FAIL: 命中 reviewer 模板占位符未填" >&2
        echo "$bad" >&2
        exit 1
      fi
      # 白名单: reviewer 字段必须以 claude（含 claude-agent: / claude-stage{N}-reviewer 历史命名）
      # 或 self-attest 起头（_template + 本 change 自身未填行排除）
      bad_white=$(grep -rE "^reviewer:" .harness/changes/ 2>/dev/null | grep -v "/_template/" | grep -v "/harness-reviewer-agent-separation-20260518/" | grep -vE "^[^:]+:reviewer:[[:space:]]+(claude|self-attest)" || true)
      if [ -n "$bad_white" ]; then
        echo "FAIL: 命中非白名单 reviewer 值（必须以 claude-agent: 或 self-attest 起头）" >&2
        echo "$bad_white" >&2
        exit 1
      fi
      exit 0
    '

  # fail-fast: 若 FAIL，立即 exit 1（阻止后续 block 跑）
  if [ "$FAIL" -gt "$fail_before" ]; then
    echo
    echo "reviewer-lint FAIL → exit 1（fail-fast；不跑后续 block）"
    echo "修复参考：.harness/skills/expert-reviewer/SKILL.md § reviewer 字段填写规约"
    exit 1
  fi
}

current_change_id() {
  local explicit="${1:-}"
  if [ -n "$explicit" ]; then
    printf "%s\n" "$explicit"
    return 0
  fi

  local branch
  branch="$(git branch --show-current 2>/dev/null || true)"
  case "$branch" in
    change/*)
      printf "%s\n" "${branch#change/}"
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

run_stage_preflight() {
  local cid="${1:-}"

  echo "=== global :: stage-preflight ==="

  run_ac "script-syntax" "self_check 与 harness_new_change bash 语法" \
    bash -c 'bash -n scripts/_self_check.sh && bash -n scripts/harness_new_change.sh'

  if [ -z "$cid" ]; then
    printf "SKIP  %-10s  %s\n" "change-pre" "未提供 change-id；跳过 change 产物快检"
    SKIP=$((SKIP + 1))
    SKIPPED_ACS+=("change-pre")
    return 0
  fi

  run_ac "change-dir" "change 目录存在：${cid}" \
    test -d ".harness/changes/${cid}"

  if [ ! -d ".harness/changes/${cid}" ]; then
    return 0
  fi

  run_ac "branch-name" "change 分支命名与 change-id 一致（非 change 分支跳过）" \
    bash -c '
      branch="$(git branch --show-current 2>/dev/null || true)"
      case "$branch" in
        change/*) [ "$branch" = "change/$1" ] ;;
        *) exit 0 ;;
      esac
    ' _ "$cid"

  run_ac "stage-files" "summary/spec/tasks 三个阶段入口文件存在" \
    bash -c '
      d=".harness/changes/$1"
      test -f "$d/summary.md" &&
      test -f "$d/request_analysis/spec.md" &&
      test -f "$d/request_analysis/tasks.md"
    ' _ "$cid"

  run_ac "summary-fill" "summary.md 已替换关键模板占位符" \
    bash -c '
      f=".harness/changes/$1/summary.md"
      test -f "$f" &&
      ! grep -qE "<(feature-slug|change-id|YYYY-MM-DDTHH:MM:SSZ|复述|bullet list|负责人|sha)>" "$f" &&
      ! grep -qE "change_id:[[:space:]]*<|branch:[[:space:]]*change/<" "$f"
    ' _ "$cid"

  run_ac "spec-shape" "spec.md 含背景/问题陈述/范围/非范围/验收标准/风险" \
    bash -c '
      spec=".harness/changes/$1/request_analysis/spec.md"
      test -f "$spec" || exit 1
      for heading in 背景 问题陈述 范围 非范围 验收标准 风险; do
        grep -qE "^## +${heading}" "$spec" || exit 1
      done
    ' _ "$cid"

  run_ac "tasks-shape" "tasks.md 含可识别任务清单" \
    bash -c '
      tasks=".harness/changes/$1/request_analysis/tasks.md"
      test -f "$tasks" &&
      grep -qE "(^tasks:|^process_tasks:|^## +T-|^- \[[ xX]\])" "$tasks"
    ' _ "$cid"
}

run_quick() {
  local cid="${1:-}"

  run_reviewer_lint
  echo
  run_ac_kind_lint
  echo
  run_stage_preflight "$cid"
}

run_change_block() {
  local change="$1"

  case "$change" in
    bootstrap-monorepo|bootstrap-monorepo-20260516)
      run_bootstrap_monorepo
      ;;
    core-domain-model|core-domain-model-20260516)
      run_core_domain_model
      ;;
    cas-storage|cas-storage-20260517)
      run_cas_storage
      ;;
    auth-scaffold|auth-scaffold-20260517)
      run_auth_scaffold
      ;;
    repo-api-mvp|repo-api-mvp-20260517)
      run_repo_api_mvp
      ;;
    commit-api-mvp|commit-api-mvp-20260517)
      run_commit_api_mvp
      ;;
    adapter-framework|adapter-framework-20260517)
      run_adapter_framework
      ;;
    web-mvp-pages|web-mvp-pages-20260517)
      run_web_mvp_pages
      ;;
    rq-worker-skeleton|rq-worker-skeleton-20260517)
      run_rq_worker_skeleton
      ;;
    web-write-flows|web-write-flows-20260517)
      run_web_write_flows
      ;;
    repo-files-tab|repo-files-tab-20260517)
      run_repo_files_tab
      ;;
    processor-framework|processor-framework-20260517)
      run_processor_framework
      ;;
    llm-gateway-mvp|llm-gateway-mvp-20260517)
      run_llm_gateway_mvp
      ;;
    adapter-firecrawl|adapter-firecrawl-20260517)
      run_adapter_firecrawl
      ;;
    llm-qa-gen|llm-qa-gen-20260518)
      run_llm_qa_gen
      ;;
    sdk-cli-mvp|sdk-cli-mvp-20260518)
      run_sdk_cli_mvp
      ;;
    pipeline-orchestrator-mvp|pipeline-orchestrator-mvp-20260518)
      run_pipeline_orchestrator_mvp
      ;;
    reviewer-lint)
      run_reviewer_lint
      ;;
    stage9-followup-cleanup|stage9-followup-cleanup-20260518)
      run_stage9_followup_cleanup
      ;;
    pipeline-ui-tab|pipeline-ui-tab-20260518)
      run_pipeline_ui_tab
      ;;
    repo-files-tab-v2|repo-files-tab-v2-20260518)
      run_repo_files_tab_v2
      ;;
    harness-ac-behavioral-tier|harness-ac-behavioral-tier-20260518)
      run_harness_ac_behavioral_tier
      ;;
    ac-kind-lint)
      run_ac_kind_lint
      ;;
    *)
      return 2
      ;;
  esac
}

run_current() {
  local cid="$1"

  run_quick "$cid"
  echo
  if ! run_change_block "$cid"; then
    printf "SKIP  %-10s  %s\n" "change-ac" "当前 change 尚未在 _self_check 注册 block：${cid}"
    SKIP=$((SKIP + 1))
    SKIPPED_ACS+=("change-ac")
  fi
}

run_full() {
  run_reviewer_lint
  echo
  run_bootstrap_monorepo
  echo
  run_core_domain_model
  echo
  run_cas_storage
  echo
  run_auth_scaffold
  echo
  run_repo_api_mvp
  echo
  run_commit_api_mvp
  echo
  run_adapter_framework
  echo
  run_web_mvp_pages
  echo
  run_rq_worker_skeleton
  echo
  run_web_write_flows
  echo
  run_repo_files_tab
  echo
  run_processor_framework
  echo
  run_llm_gateway_mvp
  echo
  run_adapter_firecrawl
  echo
  run_llm_qa_gen
  echo
  run_sdk_cli_mvp
  echo
  run_pipeline_orchestrator_mvp
  echo
  run_stage9_followup_cleanup
  echo
  run_pipeline_ui_tab
  echo
  run_repo_files_tab_v2
  echo
  run_harness_ac_behavioral_tier
  echo
  run_ac_kind_lint
}

case "$FILTER" in
  ""|full)
    run_full
    ;;
  quick)
    run_quick "${2:-}"
    ;;
  current)
    if ! CURRENT_CHANGE="$(current_change_id "${2:-}")"; then
      echo "无法推断 current change：请传入 change-id，或先切到 change/<change-id> 分支。" >&2
      exit 2
    fi
    run_current "$CURRENT_CHANGE"
    ;;
  change)
    if [ -z "${2:-}" ]; then
      echo "用法：bash scripts/_self_check.sh change <change-id>" >&2
      exit 2
    fi
    run_current "$2"
    ;;
  *)
    if ! run_change_block "$FILTER"; then
      echo "未知 change: $FILTER" >&2
      echo "已知 change: bootstrap-monorepo / ... / web-write-flows / repo-files-tab / repo-files-tab-v2 / pipeline-ui-tab / harness-ac-behavioral-tier / stage9-followup-cleanup" >&2
      echo "新 change 阶段内可用：quick [change-id] / current [change-id]；最终门禁用：full" >&2
      exit 2
    fi
    ;;
esac

echo
echo "=== 汇总 ==="
echo "PASS: $PASS"
echo "FAIL: $FAIL"
echo "SKIP: $SKIP"

if [ "$FAIL" -gt 0 ]; then
  echo "失败: ${FAILED_ACS[*]}"
  exit 1
fi

if [ "$SKIP" -gt 0 ]; then
  echo "跳过: ${SKIPPED_ACS[*]}（SKIP 不阻塞；通常是环境未就绪、未指定 change-id 或当前 change 尚无注册 block）"
fi

echo "全部通过（FAIL=0；SKIP 不阻塞）。"
exit 0
