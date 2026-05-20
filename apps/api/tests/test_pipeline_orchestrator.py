"""PipelineOrchestrator 集成 + validate_recipe 单元测试
（spec pipeline-orchestrator-mvp-20260518 T-7b，AC-6 / AC-7 / AC-8）。

- 单元（无 DB）：test_unknown_processor / test_cycle / test_unknown_node_ref
- 集成（PG + MinIO + Redis）：
  test_lineage_written_on_cache_miss / test_cache_hit_skips_processor /
  test_cache_hit_updates_ref / test_cache_hit_writes_audit_fields
"""

from __future__ import annotations

import os
import uuid

import boto3
import pytest
import redis as redis_lib
from dataplat_api.auth.password import hash_password
from dataplat_api.main import app
from dataplat_api.models import (
    CommitORM,
    PipelineCacheORM,
    PipelineRunORM,
    UserORM,
)
from dataplat_api.runner.cache import compute_cache_key
from dataplat_api.runner.orchestrator import PipelineOrchestrator
from dataplat_api.schemas.pipeline import Recipe, RecipeNode
from dataplat_api.storage import get_blob_store
from dataplat_api.storage.minio_store import MinioBlobStore
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


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


# ============== validate_recipe 单元（不依赖 DB） ==============


def test_unknown_processor() -> None:
    recipe = Recipe(
        name="x",
        nodes=[
            RecipeNode(
                id="n1",
                processor="totally-unknown-processor@0.1",
                inputs=["bronze/x/y@main"],
                config={},
                output="silver/x/z@auto",
            )
        ],
    )
    with pytest.raises(ValueError, match="未注册"):
        PipelineOrchestrator.validate_recipe(recipe)


def test_cycle() -> None:
    recipe = Recipe(
        name="x",
        nodes=[
            RecipeNode(
                id="a",
                processor="markdown-normalize@0.1",
                inputs=["@b"],
                config={},
                output="silver/x/a@auto",
            ),
            RecipeNode(
                id="b",
                processor="markdown-normalize@0.1",
                inputs=["@a"],
                config={},
                output="silver/x/b@auto",
            ),
        ],
    )
    with pytest.raises(ValueError, match="cycle"):
        PipelineOrchestrator.validate_recipe(recipe)


def test_unknown_node_ref() -> None:
    recipe = Recipe(
        name="x",
        nodes=[
            RecipeNode(
                id="a",
                processor="markdown-normalize@0.1",
                inputs=["@ghost"],
                config={},
                output="silver/x/a@auto",
            ),
        ],
    )
    with pytest.raises(ValueError, match="未知 deps"):
        PipelineOrchestrator.validate_recipe(recipe)


def test_multi_input_rejected() -> None:
    """MVP single-input only（v2 修订）。"""
    recipe = Recipe(
        name="x",
        nodes=[
            RecipeNode(
                id="a",
                processor="markdown-normalize@0.1",
                inputs=["bronze/x/y@main", "bronze/x/z@main"],
                config={},
                output="silver/x/a@auto",
            ),
        ],
    )
    with pytest.raises(ValueError, match="single-input"):
        PipelineOrchestrator.validate_recipe(recipe)


# ============== 集成测试（PG + MinIO + Redis） ==============

pytestmark_int = pytest.mark.skipif(
    not (_db_url() and _minio_endpoint() and _redis_reachable()),
    reason="PG / MinIO / Redis 任一未通；orchestrator 集成跳过",
)


async def _make_admin() -> dict:
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    username = f"orch_admin_{uuid.uuid4().hex[:6]}"
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
        info = {
            "id": user.id,
            "username": username,
            "password": password,
        }
    return info


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
        # pipeline_node_runs / pipeline_runs / pipeline_cache 通过 commit
        # FK 不直接挂 repo；cache 表的 output_commit_hash → commits，commits → repos
        # 但 cache 没 repo_id；可能跨清理；这里宽松处理：
        await session.execute(
            text("DELETE FROM refs WHERE repo_id=:r"), {"r": repo_id}
        )
        # stage9-followup-cleanup-20260518：cache hit 测试用 _preseed_cache 让
        # silver ref 跨指向 bronze commit。删 bronze 时 silver ref 仍引用这些
        # commits → refs FK violation。补：删本 repo commits 之前，先清掉
        # 所有指向本 repo commits 的 refs（无论 ref 属哪个 repo）。
        await session.execute(
            text(
                "DELETE FROM refs WHERE commit_hash IN "
                "(SELECT hash FROM commits WHERE repo_id=:r)"
            ),
            {"r": repo_id},
        )
        # 先清 pipeline_cache 指向本 repo 的 commit（model 已 CASCADE，
        # 但显式清理保持向后兼容 + downgrade 路径正常）
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


async def _seed_bronze(
    owner: str, name: str, content: bytes
) -> tuple[uuid.UUID, str]:
    """通过 HTTP 路径 seed 一个 bronze repo + 一条 commit；返 (repo_id, commit_hash).

    stage9-followup-cleanup-20260518 T-4：给 content 加 HTML 注释 uuid 前缀，
    让全局 commits.hash 唯一。原本 hardcoded byte content 跟 stage 9 demo
    同 content 撞 hash。HTML 注释（非 markdown H1）：防御性写法。
    """
    info = await _make_admin()
    transport = ASGITransport(app=app)
    unique_content = (
        f"<!-- fixture-uuid {uuid.uuid4().hex} -->\n".encode() + content
    )
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
                f"/repos/{owner}/{name}/blobs", content=unique_content
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
                    "schema_id": "silver-text-v1",
                    "row_format": "parquet",
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


def _new_run_id() -> uuid.UUID:
    return uuid.uuid4()


async def _run_orchestrator(recipe: Recipe, run_id: uuid.UUID) -> PipelineRunORM:
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    store = app.dependency_overrides[get_blob_store]()
    async with factory() as session:
        run = PipelineRunORM(
            id=run_id,
            recipe_name=recipe.name,
            recipe_json=recipe.model_dump(mode="json"),
            status="queued",
            created_by="test-admin",
        )
        session.add(run)
        await session.commit()
        result = await PipelineOrchestrator.run_pipeline(
            session=session,
            store=store,
            recipe=recipe,
            author_id="test-admin",
            run_id=run_id,
        )
    return result


@pytestmark_int
@pytest.mark.asyncio
async def test_lineage_written_on_cache_miss(_override_blob_store) -> None:
    owner = f"orch{uuid.uuid4().hex[:4]}"
    src = f"bronze-src-{uuid.uuid4().hex[:4]}"
    tgt = f"silver-tgt-{uuid.uuid4().hex[:4]}"
    try:
        _src_repo, src_commit = await _seed_bronze(
            owner, src, b"hello\r\nworld\r\n"
        )
        await _create_silver_repo(owner, tgt)

        recipe = Recipe(
            name="lineage-test",
            nodes=[
                RecipeNode(
                    id="n1",
                    processor="markdown-normalize@0.1",
                    inputs=[f"bronze/{owner}/{src}@main"],
                    config={},
                    output=f"silver/{owner}/{tgt}@main",
                )
            ],
        )
        run_id = _new_run_id()
        run = await _run_orchestrator(recipe, run_id)
        assert run.status == "succeeded", run.error

        # 验证：node_run 含 output_commit_hash；commit.lineage_json 字段级断言
        engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
        factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with factory() as session:
            node = (
                await session.execute(
                    text(
                        "SELECT output_commit_hash FROM pipeline_node_runs "
                        "WHERE run_id=:r AND node_id='n1'"
                    ),
                    {"r": run_id},
                )
            ).first()
            assert node is not None and node[0] is not None
            output_commit = node[0]

            commit = await session.get(CommitORM, output_commit)
            assert commit is not None
            assert commit.lineage_json is not None
            lj = commit.lineage_json
            assert lj["produced_by"]["kind"] == "processor"
            assert lj["produced_by"]["name"] == "markdown-normalize"
            assert lj["inputs"][0]["commit"] == src_commit
            assert lj["run_id"] == str(run_id)
    finally:
        await _delete_repo_cascade(owner, src)
        await _delete_repo_cascade(owner, tgt)


async def _preseed_cache(
    cache_key: str, output_commit_hash: str
) -> None:
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as session:
        session.add(
            PipelineCacheORM(
                cache_key=cache_key, output_commit_hash=output_commit_hash
            )
        )
        await session.commit()


@pytestmark_int
@pytest.mark.asyncio
async def test_cache_hit_skips_processor(_override_blob_store) -> None:
    """cache hit 时 ProcessorRunner.run 不应被调用：通过 monkeypatch 验证 call_count == 0。"""
    owner = f"orch{uuid.uuid4().hex[:4]}"
    src = f"bronze-src-{uuid.uuid4().hex[:4]}"
    tgt = f"silver-tgt-{uuid.uuid4().hex[:4]}"
    try:
        _src_repo, src_commit = await _seed_bronze(
            owner, src, b"hit-test\n"
        )
        await _create_silver_repo(owner, tgt)

        config: dict[str, object] = {}
        cache_key = compute_cache_key(
            [src_commit], "markdown-normalize", "0.1", config
        )
        # 先用 src_commit 自身做 fake 复用 target；避免再产新 commit
        await _preseed_cache(cache_key, src_commit)

        # patch ProcessorRunner.run，断言 0 次
        call_count = {"n": 0}
        from dataplat_api.runner import processor_runner as pr_mod

        original_run = pr_mod.ProcessorRunner.run

        async def _spy(*args, **kwargs):  # type: ignore[no-untyped-def]
            call_count["n"] += 1
            return await original_run(*args, **kwargs)

        pr_mod.ProcessorRunner.run = staticmethod(_spy)  # type: ignore[assignment]
        try:
            recipe = Recipe(
                name="hit-test",
                nodes=[
                    RecipeNode(
                        id="n1",
                        processor="markdown-normalize@0.1",
                        inputs=[f"bronze/{owner}/{src}@main"],
                        config=config,
                        output=f"silver/{owner}/{tgt}@main",
                    )
                ],
            )
            run = await _run_orchestrator(recipe, _new_run_id())
            assert run.status == "succeeded"
            assert call_count["n"] == 0
        finally:
            pr_mod.ProcessorRunner.run = original_run  # type: ignore[assignment]
    finally:
        await _delete_repo_cascade(owner, src)
        await _delete_repo_cascade(owner, tgt)


@pytestmark_int
@pytest.mark.asyncio
async def test_cache_hit_updates_ref(_override_blob_store) -> None:
    """cache hit 后 target_repo 的 output ref 已更新指向 cache 命中的 commit。"""
    owner = f"orch{uuid.uuid4().hex[:4]}"
    src = f"bronze-src-{uuid.uuid4().hex[:4]}"
    tgt = f"silver-tgt-{uuid.uuid4().hex[:4]}"
    try:
        _src_repo, src_commit = await _seed_bronze(
            owner, src, b"hit-ref\n"
        )
        tgt_repo_id = await _create_silver_repo(owner, tgt)

        config: dict[str, object] = {}
        cache_key = compute_cache_key(
            [src_commit], "markdown-normalize", "0.1", config
        )
        await _preseed_cache(cache_key, src_commit)

        recipe = Recipe(
            name="hit-ref-test",
            nodes=[
                RecipeNode(
                    id="n1",
                    processor="markdown-normalize@0.1",
                    inputs=[f"bronze/{owner}/{src}@main"],
                    config=config,
                    output=f"silver/{owner}/{tgt}@main",
                )
            ],
        )
        await _run_orchestrator(recipe, _new_run_id())

        engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
        factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with factory() as session:
            ref_stmt = (
                await session.execute(
                    text(
                        "SELECT commit_hash FROM refs WHERE repo_id=:r AND name='main'"
                    ),
                    {"r": tgt_repo_id},
                )
            ).first()
            assert ref_stmt is not None
            assert ref_stmt[0] == src_commit
    finally:
        await _delete_repo_cascade(owner, src)
        await _delete_repo_cascade(owner, tgt)


@pytestmark_int
@pytest.mark.asyncio
async def test_node_value_error_marks_failed_with_null_audit(
    _override_blob_store,
) -> None:
    """触发 _run_node 解析阶段 ValueError（不存在的 bronze ref）→
    orchestrator catch generic Exception → 节点 failed + cache_key/input_commits_json 为 None
    （stage 4 v2 SHOULD #1 兜底路径 + stage 4 v1 SHOULD #5 error 类型细化覆盖）。
    """
    owner = f"orch{uuid.uuid4().hex[:4]}"
    src = f"bronze-src-{uuid.uuid4().hex[:4]}"
    tgt = f"silver-tgt-{uuid.uuid4().hex[:4]}"
    try:
        # seed source repo 但 ref 名故意不一致：source repo 有 main，recipe 引 ghost
        await _seed_bronze(owner, src, b"x\n")
        await _create_silver_repo(owner, tgt)

        recipe = Recipe(
            name="error-test",
            nodes=[
                RecipeNode(
                    id="n1",
                    processor="markdown-normalize@0.1",
                    inputs=[f"bronze/{owner}/{src}@ghost"],  # ref ghost 不存在
                    config={},
                    output=f"silver/{owner}/{tgt}@main",
                )
            ],
        )
        run_id = _new_run_id()
        run = await _run_orchestrator(recipe, run_id)
        assert run.status == "failed"
        assert run.error is not None
        assert "input ref" in run.error or "ghost" in run.error

        engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
        factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with factory() as session:
            row = (
                await session.execute(
                    text(
                        "SELECT status, cache_hit, cache_key, "
                        "input_commits_json, error "
                        "FROM pipeline_node_runs WHERE run_id=:r"
                    ),
                    {"r": run_id},
                )
            ).first()
            assert row is not None
            status_, cache_hit, cache_key, input_commits_json, err = row
            assert status_ == "failed"
            assert cache_hit is False
            # stage 4 v2 SHOULD #1：error 兜底路径写 NULL 而非空串
            assert cache_key is None
            assert input_commits_json is None
            assert err is not None
            assert len(err) <= 500  # v2 MUST #2 截断
    finally:
        await _delete_repo_cascade(owner, src)
        await _delete_repo_cascade(owner, tgt)


@pytestmark_int
@pytest.mark.asyncio
async def test_node_400_marks_failed(_override_blob_store) -> None:
    """触发 ProcessorRunner 内 HTTPException(404)：unknown processor name 走
    ProcessorRunner.run 内 404 抛错路径 → orchestrator catch HTTPException → node failed。

    注：validate_recipe 已经预检 processor，所以这里直接 monkeypatch 让
    ProcessorRunner.run 抛 HTTPException(400) 模拟 detail=dict 的长 list 场景，
    验证 v2 MUST #2 [:500] 截断。
    """
    from dataplat_api.runner import processor_runner as pr_mod
    from fastapi import HTTPException as _HE

    owner = f"orch{uuid.uuid4().hex[:4]}"
    src = f"bronze-src-{uuid.uuid4().hex[:4]}"
    tgt = f"silver-tgt-{uuid.uuid4().hex[:4]}"
    try:
        await _seed_bronze(owner, src, b"x\n")
        await _create_silver_repo(owner, tgt)

        # detail 是 dict 含大 list，str(detail) 超长
        big_detail = {
            "detail": "processor 400",
            "available": [f"p{i}@v" for i in range(200)],
        }

        async def _raise(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            raise _HE(status_code=400, detail=big_detail)

        original = pr_mod.ProcessorRunner.run
        pr_mod.ProcessorRunner.run = staticmethod(_raise)  # type: ignore[assignment]
        try:
            recipe = Recipe(
                name="err400",
                nodes=[
                    RecipeNode(
                        id="n1",
                        processor="markdown-normalize@0.1",
                        inputs=[f"bronze/{owner}/{src}@main"],
                        config={},
                        output=f"silver/{owner}/{tgt}@main",
                    )
                ],
            )
            run = await _run_orchestrator(recipe, _new_run_id())
            assert run.status == "failed"
            # v2 MUST #2：HTTPException detail 路径也按 500 截断
            assert run.error is not None
            # run.error 是 "node 'n1' failed: <node error>"；node error 已 ≤500
            # 所以 run.error 整体大约 ≤520
            assert len(run.error) <= 600
        finally:
            pr_mod.ProcessorRunner.run = original  # type: ignore[assignment]
    finally:
        await _delete_repo_cascade(owner, src)
        await _delete_repo_cascade(owner, tgt)


@pytestmark_int
@pytest.mark.asyncio
async def test_cache_hit_writes_audit_fields(_override_blob_store) -> None:
    """cache hit 时 pipeline_node_runs.input_commits_json + cache_key 字段非空。"""
    owner = f"orch{uuid.uuid4().hex[:4]}"
    src = f"bronze-src-{uuid.uuid4().hex[:4]}"
    tgt = f"silver-tgt-{uuid.uuid4().hex[:4]}"
    try:
        _src_repo, src_commit = await _seed_bronze(
            owner, src, b"audit\n"
        )
        await _create_silver_repo(owner, tgt)

        config: dict[str, object] = {}
        cache_key = compute_cache_key(
            [src_commit], "markdown-normalize", "0.1", config
        )
        await _preseed_cache(cache_key, src_commit)

        recipe = Recipe(
            name="audit-test",
            nodes=[
                RecipeNode(
                    id="n1",
                    processor="markdown-normalize@0.1",
                    inputs=[f"bronze/{owner}/{src}@main"],
                    config=config,
                    output=f"silver/{owner}/{tgt}@main",
                )
            ],
        )
        run_id = _new_run_id()
        await _run_orchestrator(recipe, run_id)

        engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
        factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with factory() as session:
            row = (
                await session.execute(
                    text(
                        "SELECT cache_hit, input_commits_json, cache_key "
                        "FROM pipeline_node_runs WHERE run_id=:r AND node_id='n1'"
                    ),
                    {"r": run_id},
                )
            ).first()
            assert row is not None
            cache_hit, input_commits_json, ck = row
            assert cache_hit is True
            assert list(input_commits_json) == [src_commit]
            assert ck == cache_key
    finally:
        await _delete_repo_cascade(owner, src)
        await _delete_repo_cascade(owner, tgt)
