"""端到端 demo recipe（spec pipeline-orchestrator-mvp-20260518 T-7c，AC-11 / AC-12）。

跑 `recipes/examples/demo-bronze-to-silver.yaml`：fixture 预 seed bronze repo →
orchestrator 调 markdown-normalize → 验证 silver repo 的 ref 指向新 commit +
commit.lineage_json 含 produced_by/inputs/run_id。

依赖 PG + MinIO + Redis；skipif 不通则跳过（同 test_pipeline_orchestrator.py 模式）。
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import boto3
import pytest
import redis as redis_lib
from dataplat_api.auth.password import hash_password
from dataplat_api.main import app
from dataplat_api.models import CommitORM, PipelineRunORM, UserORM
from dataplat_api.runner.orchestrator import PipelineOrchestrator
from dataplat_api.schemas.pipeline import load_recipe
from dataplat_api.storage import get_blob_store
from dataplat_api.storage.minio_store import MinioBlobStore
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

REPO_ROOT = Path(__file__).resolve().parents[3]


def _db_url() -> str | None:
    return os.environ.get("DATAPLAT_DATABASE_URL")


def _minio_endpoint() -> str | None:
    return os.environ.get("DATAPLAT_MINIO_ENDPOINT")


def _redis_url() -> str:
    return os.environ.get("DATAPLAT_REDIS_URL", "redis://localhost:6379/0")


def _redis_reachable() -> bool:
    try:
        r = redis_lib.Redis.from_url(_redis_url(), socket_connect_timeout=1)
        r.ping()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not (_db_url() and _minio_endpoint() and _redis_reachable()),
    reason="PG / MinIO / Redis 任一未通；pipeline e2e 跳过",
)


@pytest.fixture
def _override_blob_store(monkeypatch):  # type: ignore[no-untyped-def]
    bucket = f"dataplat-test-{uuid.uuid4().hex[:8]}"
    endpoint = os.environ.get("DATAPLAT_MINIO_ENDPOINT", "http://localhost:9000")
    ak = os.environ.get("DATAPLAT_MINIO_ACCESS_KEY", "dataplat")
    sk = os.environ.get(
        "DATAPLAT_MINIO_SECRET_KEY", "dataplat-dev-secret"
    )
    store = MinioBlobStore(
        endpoint_url=endpoint, access_key=ak, secret_key=sk, bucket=bucket
    )
    app.dependency_overrides[get_blob_store] = lambda: store

    import dataplat_api.storage as storage_mod

    monkeypatch.setattr(storage_mod, "_blob_store", None)
    monkeypatch.setenv("DATAPLAT_BLOB_BUCKET", bucket)
    monkeypatch.setenv("DATAPLAT_MINIO_ENDPOINT", endpoint)
    monkeypatch.setenv("DATAPLAT_MINIO_ACCESS_KEY", ak)
    monkeypatch.setenv("DATAPLAT_MINIO_SECRET_KEY", sk)
    try:
        yield
    finally:
        storage_mod._blob_store = None
        app.dependency_overrides.pop(get_blob_store, None)
        raw = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=ak,
            aws_secret_access_key=sk,
            region_name="us-east-1",
        )
        try:
            paginator = raw.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=bucket):
                for obj in page.get("Contents") or []:
                    raw.delete_object(Bucket=bucket, Key=obj["Key"])
            raw.delete_bucket(Bucket=bucket)
        except Exception:  # noqa: BLE001
            pass


async def _make_admin() -> dict:
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    username = f"e2e_admin_{uuid.uuid4().hex[:6]}"
    password = "test-password-x"
    async with factory() as session:
        user = UserORM(
            id=uuid.uuid4(),
            username=username,
            email=None,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return {
            "id": user.id,
            "username": username,
            "password": password,
        }


async def _delete_user(user_id: uuid.UUID) -> None:
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as session:
        await session.execute(delete(UserORM).where(UserORM.id == user_id))
        await session.commit()


async def _delete_repo_cascade(owner: str, name: str) -> None:
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as session:
        repo_row = (
            await session.execute(
                text(
                    "SELECT id FROM repositories WHERE owner=:o AND name=:n"
                ),
                {"o": owner, "n": name},
            )
        ).first()
        if repo_row is None:
            await session.commit()
            return
        repo_id = repo_row[0]
        await session.execute(
            text("DELETE FROM refs WHERE repo_id=:r"), {"r": repo_id}
        )
        await session.execute(
            text(
                "DELETE FROM pipeline_cache WHERE output_commit_hash IN "
                "(SELECT hash FROM commits WHERE repo_id=:r)"
            ),
            {"r": repo_id},
        )
        await session.execute(
            text("DELETE FROM commits WHERE repo_id=:r"), {"r": repo_id}
        )
        await session.execute(
            text("DELETE FROM trees WHERE repo_id=:r"), {"r": repo_id}
        )
        await session.execute(
            text("DELETE FROM repositories WHERE id=:r"), {"r": repo_id}
        )
        await session.commit()


async def _seed_bronze(
    owner: str, name: str, content: bytes
) -> tuple[uuid.UUID, str]:
    info = await _make_admin()
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(
            transport=transport, base_url="https://test"
        ) as c:
            await c.post(
                "/auth/login",
                json={
                    "username": info["username"],
                    "password": info["password"],
                },
            )
            await c.post(
                "/repos",
                json={
                    "owner": owner,
                    "name": name,
                    "layer": "bronze",
                    "subtype": "pdf",
                    "visibility": "public",
                },
            )
            r_blob = await c.post(
                f"/repos/{owner}/{name}/blobs", content=content
            )
            sha = r_blob.json()["sha256"]
            r_commit = await c.post(
                f"/repos/{owner}/{name}/commits",
                json={
                    "tree": {
                        "entries": [
                            {
                                "name": "doc.md",
                                "mode": 33188,
                                "entry_type": "blob",
                                "target_hash": sha,
                            }
                        ]
                    },
                    "parents": [],
                    "author_id": "u1",
                    "ref": "main",
                },
            )
            commit_hash = r_commit.json()["hash"]
    finally:
        await _delete_user(info["id"])

    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as session:
        repo_row = (
            await session.execute(
                text(
                    "SELECT id FROM repositories WHERE owner=:o AND name=:n"
                ),
                {"o": owner, "n": name},
            )
        ).first()
    assert repo_row is not None
    return repo_row[0], commit_hash


async def _create_silver_repo(owner: str, name: str) -> uuid.UUID:
    info = await _make_admin()
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(
            transport=transport, base_url="https://test"
        ) as c:
            await c.post(
                "/auth/login",
                json={
                    "username": info["username"],
                    "password": info["password"],
                },
            )
            await c.post(
                "/repos",
                json={
                    "owner": owner,
                    "name": name,
                    "layer": "silver",
                    "subtype": "text-corpus",
                    "visibility": "public",
                },
            )
    finally:
        await _delete_user(info["id"])

    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as session:
        repo_row = (
            await session.execute(
                text(
                    "SELECT id FROM repositories WHERE owner=:o AND name=:n"
                ),
                {"o": owner, "n": name},
            )
        ).first()
    assert repo_row is not None
    return repo_row[0]


@pytest.mark.asyncio
async def test_demo_bronze_to_silver_e2e(_override_blob_store) -> None:
    """端到端：load demo-bronze-to-silver.yaml → 修改 inputs/output 到 fixture
    repo → 跑 orchestrator → 验证 silver ref 指向新 commit。

    注：demo-bronze-to-silver.yaml 节点用占位 `bronze/demo/raw-md@main`；测试
    fixture 不会用 demo/raw-md 这个仓库，而是动态生成 owner/name；因此我们
    直接构造 recipe（不从 yaml 文件加载）以避免与 yaml 占位耦合。AC-11 是
    grep yaml 文件存在性 + 关键字校验，与本测试解耦。
    """
    # 仍然 load 一下 demo recipe 校验 yaml 可解析（AC-11 间接覆盖）
    demo_yaml = (REPO_ROOT / "recipes/examples/demo-bronze-to-silver.yaml").read_text()
    demo_recipe = load_recipe(demo_yaml)
    assert demo_recipe.name == "demo-bronze-to-silver"
    assert len(demo_recipe.nodes) == 1
    assert demo_recipe.nodes[0].processor == "markdown-normalize@0.1"

    # 动态生成 owner/name 跑 e2e
    owner = f"e2e{uuid.uuid4().hex[:4]}"
    src = f"bronze-{uuid.uuid4().hex[:4]}"
    tgt = f"silver-{uuid.uuid4().hex[:4]}"
    raw = b"hello\r\nworld   \r\n\r\n\r\n\r\nend\r\n"

    try:
        _src_repo_id, src_commit = await _seed_bronze(owner, src, raw)
        tgt_repo_id = await _create_silver_repo(owner, tgt)

        from dataplat_api.schemas.pipeline import Recipe, RecipeNode

        recipe = Recipe(
            name="demo-bronze-to-silver",
            nodes=[
                RecipeNode(
                    id="normalize",
                    processor="markdown-normalize@0.1",
                    inputs=[f"bronze/{owner}/{src}@main"],
                    config={},
                    output=f"silver/{owner}/{tgt}@main",
                )
            ],
        )

        # 直接调 orchestrator（绕过 jobs 队列，简化 e2e）
        engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
        factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        store = app.dependency_overrides[get_blob_store]()
        run_id = uuid.uuid4()
        async with factory() as session:
            session.add(
                PipelineRunORM(
                    id=run_id,
                    recipe_name=recipe.name,
                    recipe_json=recipe.model_dump(mode="json"),
                    status="queued",
                    created_by="e2e",
                )
            )
            await session.commit()
            result = await PipelineOrchestrator.run_pipeline(
                session=session,
                store=store,
                recipe=recipe,
                author_id="e2e",
                run_id=run_id,
            )
        assert result.status == "succeeded", result.error

        # 验证 silver ref 指向新 commit + commit.lineage_json 完整
        async with factory() as session:
            ref_row = (
                await session.execute(
                    text(
                        "SELECT commit_hash FROM refs "
                        "WHERE repo_id=:r AND name='main'"
                    ),
                    {"r": tgt_repo_id},
                )
            ).first()
            assert ref_row is not None
            new_commit_hash = ref_row[0]
            assert new_commit_hash != src_commit  # 真新 commit

            commit = await session.get(CommitORM, new_commit_hash)
            assert commit is not None
            assert commit.lineage_json is not None
            lj = commit.lineage_json
            assert lj["produced_by"]["name"] == "markdown-normalize"
            assert lj["inputs"][0]["commit"] == src_commit
            assert lj["run_id"] == str(run_id)
    finally:
        await _delete_repo_cascade(owner, src)
        await _delete_repo_cascade(owner, tgt)
