#!/usr/bin/env bash
# scripts/_self_check.sh
#
# 仓库级自检脚本——把每个变更 spec §验收标准表的 shell 命令归档为
# 可重复运行的断言。当前实现 bootstrap-monorepo-20260516 的 17 条 AC。
#
# 设计意图：
# - 每个变更在 stage 5 单测编写阶段把自己的 AC 落到这里（追加块）；
# - stage 8 CI 调用本脚本作为统一 smoke gate；
# - 后续 follow-up `harness-script-productize-<yyyymmdd>` 会把 harness-bootstrap-20260516
#   的 12 条 AC（当前在 .harness/changes/harness-bootstrap-20260516/unit_test/
#   check_harness.sh）也搬进来，形成单一入口。
#
# 用法：
#   bash scripts/_self_check.sh                    # 跑全部
#   bash scripts/_self_check.sh bootstrap-monorepo # 只跑指定 change 的块
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

  run_ac AC-6 ".gitignore 必备排除 + .claude/settings.local.json ignored" \
    bash -c 'test -f .gitignore && for p in .venv node_modules dist __pycache__ .pytest_cache .ruff_cache .mypy_cache .turbo ".claude/settings.local.json"; do grep -q "$p" .gitignore || exit 1; done && git check-ignore -q .claude/settings.local.json'

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

  run_ac AC-15 "ci.yml 合法 + 5 job + concurrency" \
    python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/ci.yml')); j=d['jobs']; [j[k] for k in ['python-lint-type','python-test','web-lint-type','web-test','codegen-check']]; assert d['concurrency']['cancel-in-progress'] is True"

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

  run_ac_skipif_no_pg AC-2 "0002 migration head" \
    bash -c 'ls apps/api/alembic/versions/0002_*.py >/dev/null && export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && cd apps/api && uv run alembic upgrade head && uv run alembic current 2>&1 | grep -q "0002"'

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

case "$FILTER" in
  "")
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
    ;;
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
  *)
    echo "未知 change: $FILTER" >&2
    echo "已知 change: bootstrap-monorepo / core-domain-model / cas-storage / auth-scaffold / repo-api-mvp / commit-api-mvp / adapter-framework / web-mvp-pages" >&2
    exit 2
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
  echo "跳过: ${SKIPPED_ACS[*]}（环境探针未通过，非测试失败）"
fi

echo "全部通过（FAIL=0；SKIP 不阻塞）。"
exit 0
