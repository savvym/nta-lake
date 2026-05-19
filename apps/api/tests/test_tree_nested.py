"""Tree 嵌套支持集成测试（spec tree-nested-domain-20260520 AC-9/10/11）。

依赖 PG + MinIO（同 test_commits.py 模式）。

≥ 8 用例：
- a. test_post_flat_input_round_trip       AC-10  POST 扁平 → nested → GET ?recursive=1 还原
- b. test_get_tree_default_shows_subtree   AC-7   默认 GET 返根级 subtree entry
- c. test_get_subtree_by_hash              AC-8   GET /trees/{subtree_hash} 取子层
- d. test_get_tree_legacy_flat_unchanged   AC-9   旧扁平 commit GET 返扁平不变
- e. test_dedup_same_subtree_across_commits AC-6  同 images/ 子目录两 commit 共享 TreeORM
- f. test_path_validation_rejects          AC-3   8 类校验 + type=tree input
- g. test_deep_nested_3_levels                    a/b/c/d.txt → 4 tree
- h. test_empty_tree                              空 entries 合法
- i. test_recursive_no_op_on_flat          AC-9   旧扁平 ?recursive=1 等价默认
"""

from __future__ import annotations

import hashlib
import os
import secrets
import uuid
from collections.abc import AsyncGenerator

import boto3
import pytest
from dataplat_api.auth.password import hash_password
from dataplat_api.main import app
from dataplat_api.models import TreeEntryORM, TreeORM, UserORM
from dataplat_api.storage import get_blob_store
from dataplat_api.storage.minio_store import MinioBlobStore
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def _db_url() -> str | None:
    return os.environ.get("DATAPLAT_DATABASE_URL")


def _minio_endpoint() -> str | None:
    return os.environ.get("DATAPLAT_MINIO_ENDPOINT")


pytestmark = pytest.mark.skipif(
    not (_db_url() and _minio_endpoint()),
    reason="DATAPLAT_DATABASE_URL / DATAPLAT_MINIO_ENDPOINT 未设置；tree-nested 集成跳过",
)


# --------- fixtures（复用 test_commits.py 模式） ---------


async def _make_admin() -> dict:
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    username = f"a_{uuid.uuid4().hex[:8]}"
    password = "test-password-x"
    async with factory() as session:
        user = UserORM(
            id=uuid.uuid4(),
            username=username,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )
        session.add(user)
        await session.commit()
    return {"id": user.id, "username": username, "password": password}


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
                text("SELECT id FROM repositories WHERE owner=:o AND name=:n"),
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
            text("DELETE FROM commits WHERE repo_id=:r"), {"r": repo_id}
        )
        await session.execute(
            text("DELETE FROM trees WHERE repo_id=:r"), {"r": repo_id}
        )
        await session.execute(
            text("DELETE FROM repositories WHERE id=:r"), {"r": repo_id}
        )
        await session.commit()


@pytest.fixture(autouse=True)
def _override_blob_store() -> AsyncGenerator[None, None]:
    bucket = f"dataplat-test-{uuid.uuid4().hex[:8]}"
    endpoint = os.environ.get("DATAPLAT_MINIO_ENDPOINT", "http://localhost:9000")
    ak = os.environ.get("DATAPLAT_MINIO_ACCESS_KEY", "dataplat")
    sk = os.environ.get("DATAPLAT_MINIO_SECRET_KEY", "dataplat-dev-secret")
    store = MinioBlobStore(
        endpoint_url=endpoint, access_key=ak, secret_key=sk, bucket=bucket
    )
    app.dependency_overrides[get_blob_store] = lambda: store
    try:
        yield  # type: ignore[misc]
    finally:
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


@pytest.fixture
async def admin_user() -> AsyncGenerator[dict, None]:
    info = await _make_admin()
    try:
        yield info
    finally:
        await _delete_user(info["id"])


async def _login(client: AsyncClient, user: dict) -> None:
    resp = await client.post(
        "/auth/login",
        json={"username": user["username"], "password": user["password"]},
    )
    assert resp.status_code == 200


async def _create_repo(client: AsyncClient, owner: str, name: str) -> None:
    resp = await client.post(
        "/repos",
        json={
            "owner": owner,
            "name": name,
            "layer": "bronze",
            "subtype": "pdf",
            "visibility": "public",
        },
    )
    assert resp.status_code == 201, resp.text


async def _upload_blob(client: AsyncClient, owner: str, name: str, content: bytes) -> str:
    resp = await client.post(
        f"/repos/{owner}/{name}/blobs",
        content=content,
        headers={"content-length": str(len(content))},
    )
    assert resp.status_code == 201, resp.text
    sha = hashlib.sha256(content).hexdigest()
    assert resp.json()["sha256"] == sha
    return sha


async def _post_commit(
    client: AsyncClient,
    owner: str,
    name: str,
    entries: list[dict],
    message: str | None = None,
) -> dict:
    payload: dict = {
        "tree": {"entries": entries},
        "parents": [],
        "author_id": "admin",
    }
    if message is not None:
        payload["message"] = message
    resp = await client.post(f"/repos/{owner}/{name}/commits", json=payload)
    return {"status": resp.status_code, "body": resp.json() if resp.content else None}


# --------- (a) AC-10 扁平 → nested → recursive 还原 ---------


@pytest.mark.asyncio
async def test_post_flat_input_round_trip(admin_user: dict) -> None:
    owner = "u"
    name = f"r-{secrets.token_hex(3)}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _login(client, admin_user)
        try:
            await _create_repo(client, owner, name)
            # 上传 3 blob
            sha_a = await _upload_blob(client, owner, name, b"image-a-content")
            sha_b = await _upload_blob(client, owner, name, b"image-b-content")
            sha_md = await _upload_blob(client, owner, name, b"# paper title")

            res = await _post_commit(
                client,
                owner,
                name,
                [
                    {"name": "images/a.jpg", "mode": 33188, "target_hash": sha_a},
                    {"name": "images/b.jpg", "mode": 33188, "target_hash": sha_b},
                    {"name": "paper.md", "mode": 33188, "target_hash": sha_md},
                ],
                message="initial",
            )
            assert res["status"] == 200, res
            commit_hash = res["body"]["hash"]

            # 默认 GET：根 tree 应含 type=tree 的 images entry + type=blob 的 paper.md
            r = await client.get(f"/repos/{owner}/{name}/tree/{commit_hash}")
            assert r.status_code == 200
            entries = r.json()["entries"]
            names_types = sorted([(e["name"], e["entry_type"]) for e in entries])
            assert names_types == [("images", "tree"), ("paper.md", "blob")]

            # ?recursive=1：还原为 3 个 leaf blob，name 为扁平全路径
            r2 = await client.get(
                f"/repos/{owner}/{name}/tree/{commit_hash}", params={"recursive": "true"}
            )
            assert r2.status_code == 200
            leaves = sorted(
                [(e["name"], e["entry_type"], e["target_hash"]) for e in r2.json()["entries"]]
            )
            assert leaves == sorted([
                ("images/a.jpg", "blob", sha_a),
                ("images/b.jpg", "blob", sha_b),
                ("paper.md", "blob", sha_md),
            ])
        finally:
            await _delete_repo_cascade(owner, name)


# --------- (b) AC-7 默认 GET 含子 tree entry ---------


@pytest.mark.asyncio
async def test_get_tree_default_shows_subtree(admin_user: dict) -> None:
    owner = "u"
    name = f"r-{secrets.token_hex(3)}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _login(client, admin_user)
        try:
            await _create_repo(client, owner, name)
            sha_a = await _upload_blob(client, owner, name, b"a")
            res = await _post_commit(
                client,
                owner,
                name,
                [{"name": "sub/a.txt", "mode": 33188, "target_hash": sha_a}],
            )
            commit_hash = res["body"]["hash"]

            r = await client.get(f"/repos/{owner}/{name}/tree/{commit_hash}")
            entries = r.json()["entries"]
            assert len(entries) == 1
            assert entries[0]["name"] == "sub"
            assert entries[0]["entry_type"] == "tree"
            assert entries[0]["mode"] == 0o040000
        finally:
            await _delete_repo_cascade(owner, name)


# --------- (c) AC-8 GET /trees/{subtree_hash} ---------


@pytest.mark.asyncio
async def test_get_subtree_by_hash(admin_user: dict) -> None:
    owner = "u"
    name = f"r-{secrets.token_hex(3)}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _login(client, admin_user)
        try:
            await _create_repo(client, owner, name)
            sha_a = await _upload_blob(client, owner, name, b"a")
            sha_b = await _upload_blob(client, owner, name, b"b")
            res = await _post_commit(
                client,
                owner,
                name,
                [
                    {"name": "images/a.jpg", "mode": 33188, "target_hash": sha_a},
                    {"name": "images/b.jpg", "mode": 33188, "target_hash": sha_b},
                ],
            )
            commit_hash = res["body"]["hash"]

            root = await client.get(f"/repos/{owner}/{name}/tree/{commit_hash}")
            subtree_hash = next(
                e["target_hash"] for e in root.json()["entries"] if e["name"] == "images"
            )

            r = await client.get(f"/repos/{owner}/{name}/trees/{subtree_hash}")
            assert r.status_code == 200
            entries = sorted([(e["name"], e["entry_type"]) for e in r.json()["entries"]])
            assert entries == [("a.jpg", "blob"), ("b.jpg", "blob")]

            # 404：随机 hash 不存在
            r2 = await client.get(f"/repos/{owner}/{name}/trees/{'0' * 64}")
            assert r2.status_code == 404
        finally:
            await _delete_repo_cascade(owner, name)


# --------- (d) AC-9 旧扁平 commit 不变形 ---------


@pytest.mark.asyncio
async def test_get_tree_legacy_flat_unchanged(admin_user: dict) -> None:
    """直接 INSERT 一个旧扁平 TreeORM（含 / 但全 type=blob，单层），
    然后 GET → 应返扁平 entries 不变（向后兼容）。"""
    owner = "u"
    name = f"r-{secrets.token_hex(3)}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _login(client, admin_user)
        try:
            await _create_repo(client, owner, name)
            sha_a = await _upload_blob(client, owner, name, b"a")

            # 直接 INSERT 扁平 tree（绕过 normalize）
            engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
            factory = async_sessionmaker(bind=engine, expire_on_commit=False)
            tree_hash = "1" * 64
            commit_hash = "2" * 64
            async with factory() as session:
                repo_row = (
                    await session.execute(
                        text("SELECT id FROM repositories WHERE owner=:o AND name=:n"),
                        {"o": owner, "n": name},
                    )
                ).first()
                repo_id = repo_row[0]
                session.add(TreeORM(hash=tree_hash, repo_id=repo_id))
                session.add(
                    TreeEntryORM(
                        tree_hash=tree_hash,
                        position=0,
                        name="images/old-flat.jpg",
                        mode=33188,
                        entry_type="blob",
                        target_hash=sha_a,
                    )
                )
                await session.flush()  # 让 FK 检查能看到刚 add 的 tree
                await session.execute(
                    text(
                        "INSERT INTO commits (hash, repo_id, tree_hash, parents, author_id, created_at, message) "
                        "VALUES (:h, :r, :t, ARRAY[]::text[], 'legacy', NOW(), NULL)"
                    ),
                    {"h": commit_hash, "r": repo_id, "t": tree_hash},
                )
                await session.commit()

            r = await client.get(f"/repos/{owner}/{name}/tree/{commit_hash}")
            assert r.status_code == 200
            entries = r.json()["entries"]
            assert len(entries) == 1
            # 旧扁平 entry：name 仍含 /，type=blob
            assert entries[0]["name"] == "images/old-flat.jpg"
            assert entries[0]["entry_type"] == "blob"
        finally:
            await _delete_repo_cascade(owner, name)


# --------- (e) AC-6 同子目录 dedup ---------


@pytest.mark.asyncio
async def test_dedup_same_subtree_across_commits(admin_user: dict) -> None:
    owner = "u"
    name = f"r-{secrets.token_hex(3)}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _login(client, admin_user)
        try:
            await _create_repo(client, owner, name)
            sha_a = await _upload_blob(client, owner, name, b"img-a")
            sha_b = await _upload_blob(client, owner, name, b"img-b")
            # commit 1: images/{a,b} + paper.md
            sha_md1 = await _upload_blob(client, owner, name, b"v1")
            res1 = await _post_commit(
                client, owner, name,
                [
                    {"name": "images/a.jpg", "mode": 33188, "target_hash": sha_a},
                    {"name": "images/b.jpg", "mode": 33188, "target_hash": sha_b},
                    {"name": "paper.md", "mode": 33188, "target_hash": sha_md1},
                ],
                message="v1",
            )
            commit1 = res1["body"]["hash"]
            # commit 2: 同 images/ + 不同 paper.md
            sha_md2 = await _upload_blob(client, owner, name, b"v2")
            res2 = await _post_commit(
                client, owner, name,
                [
                    {"name": "images/a.jpg", "mode": 33188, "target_hash": sha_a},
                    {"name": "images/b.jpg", "mode": 33188, "target_hash": sha_b},
                    {"name": "paper.md", "mode": 33188, "target_hash": sha_md2},
                ],
                message="v2",
            )
            commit2 = res2["body"]["hash"]
            assert commit1 != commit2

            # 取两 commit 的 images subtree hash → 应相同
            root1 = await client.get(f"/repos/{owner}/{name}/tree/{commit1}")
            root2 = await client.get(f"/repos/{owner}/{name}/tree/{commit2}")
            sub1 = next(e["target_hash"] for e in root1.json()["entries"] if e["name"] == "images")
            sub2 = next(e["target_hash"] for e in root2.json()["entries"] if e["name"] == "images")
            assert sub1 == sub2  # CAS dedup
        finally:
            await _delete_repo_cascade(owner, name)


# --------- (f) AC-3 路径校验 ---------


@pytest.mark.asyncio
async def test_path_validation_rejects(admin_user: dict) -> None:
    owner = "u"
    name = f"r-{secrets.token_hex(3)}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _login(client, admin_user)
        try:
            await _create_repo(client, owner, name)
            sha_a = await _upload_blob(client, owner, name, b"a")
            sha_b = await _upload_blob(client, owner, name, b"b")

            bad_inputs = [
                ([{"name": "", "mode": 33188, "target_hash": sha_a}], "空"),
                ([{"name": "/a", "mode": 33188, "target_hash": sha_a}], "起头 /"),
                ([{"name": "a/", "mode": 33188, "target_hash": sha_a}], "结尾 /"),
                ([{"name": "a//b", "mode": 33188, "target_hash": sha_a}], "连续 /"),
                ([{"name": "a/../b", "mode": 33188, "target_hash": sha_a}], ".. segment"),
                ([{"name": "a/./b", "mode": 33188, "target_hash": sha_a}], ". segment"),
                ([{"name": "a/ /b", "mode": 33188, "target_hash": sha_a}], "空白 segment"),
                (
                    [
                        {"name": "a", "mode": 33188, "target_hash": sha_a},
                        {"name": "a/b", "mode": 33188, "target_hash": sha_b},
                    ],
                    "blob-dir conflict",
                ),
                (
                    [
                        {
                            "name": "dir",
                            "mode": 16384,
                            "entry_type": "tree",
                            "target_hash": sha_a,
                        }
                    ],
                    "type=tree 输入被拒",
                ),
                (
                    [
                        {"name": "a/dup.txt", "mode": 33188, "target_hash": sha_a},
                        {"name": "a/dup.txt", "mode": 33188, "target_hash": sha_b},
                    ],
                    "同层重名 (full name 重复)",
                ),
            ]
            for entries, label in bad_inputs:
                res = await _post_commit(client, owner, name, entries)
                assert res["status"] == 400, f"应拒 {label}：{res}"
        finally:
            await _delete_repo_cascade(owner, name)


# --------- (g) 深嵌套 3 层 ---------


@pytest.mark.asyncio
async def test_deep_nested_3_levels(admin_user: dict) -> None:
    owner = "u"
    name = f"r-{secrets.token_hex(3)}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _login(client, admin_user)
        try:
            await _create_repo(client, owner, name)
            sha_d = await _upload_blob(client, owner, name, b"deep")
            res = await _post_commit(
                client, owner, name,
                [{"name": "a/b/c/d.txt", "mode": 33188, "target_hash": sha_d}],
            )
            assert res["status"] == 200
            commit_hash = res["body"]["hash"]

            # 默认 GET 看到根级 "a" type=tree
            root = await client.get(f"/repos/{owner}/{name}/tree/{commit_hash}")
            assert root.json()["entries"] == [
                {
                    "name": "a",
                    "mode": 0o040000,
                    "entry_type": "tree",
                    "target_hash": root.json()["entries"][0]["target_hash"],
                }
            ]
            # recursive=1 看到 leaf
            full = await client.get(
                f"/repos/{owner}/{name}/tree/{commit_hash}", params={"recursive": "true"}
            )
            assert [(e["name"], e["entry_type"]) for e in full.json()["entries"]] == [
                ("a/b/c/d.txt", "blob")
            ]
        finally:
            await _delete_repo_cascade(owner, name)


# --------- (h) 空 tree ---------


@pytest.mark.asyncio
async def test_empty_tree(admin_user: dict) -> None:
    owner = "u"
    name = f"r-{secrets.token_hex(3)}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _login(client, admin_user)
        try:
            await _create_repo(client, owner, name)
            res = await _post_commit(client, owner, name, [])
            assert res["status"] == 200
            commit_hash = res["body"]["hash"]

            r = await client.get(f"/repos/{owner}/{name}/tree/{commit_hash}")
            assert r.status_code == 200
            assert r.json()["entries"] == []

            r2 = await client.get(
                f"/repos/{owner}/{name}/tree/{commit_hash}", params={"recursive": "true"}
            )
            assert r2.json()["entries"] == []
        finally:
            await _delete_repo_cascade(owner, name)


# --------- (i) 旧扁平 ?recursive=1 等价默认 ---------


@pytest.mark.asyncio
async def test_recursive_no_op_on_flat(admin_user: dict) -> None:
    """旧扁平 commit（无 type=tree entry）的 ?recursive=1 与默认应一致。"""
    owner = "u"
    name = f"r-{secrets.token_hex(3)}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _login(client, admin_user)
        try:
            await _create_repo(client, owner, name)
            sha_a = await _upload_blob(client, owner, name, b"a")

            # 直接 INSERT 扁平
            engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
            factory = async_sessionmaker(bind=engine, expire_on_commit=False)
            tree_hash = "3" * 64
            commit_hash = "4" * 64
            async with factory() as session:
                repo_id = (
                    await session.execute(
                        text("SELECT id FROM repositories WHERE owner=:o AND name=:n"),
                        {"o": owner, "n": name},
                    )
                ).first()[0]
                session.add(TreeORM(hash=tree_hash, repo_id=repo_id))
                session.add(
                    TreeEntryORM(
                        tree_hash=tree_hash, position=0,
                        name="dir/file.txt", mode=33188,
                        entry_type="blob", target_hash=sha_a,
                    )
                )
                await session.flush()
                await session.execute(
                    text(
                        "INSERT INTO commits (hash, repo_id, tree_hash, parents, author_id, created_at, message) "
                        "VALUES (:h, :r, :t, ARRAY[]::text[], 'legacy', NOW(), NULL)"
                    ),
                    {"h": commit_hash, "r": repo_id, "t": tree_hash},
                )
                await session.commit()

            r1 = await client.get(f"/repos/{owner}/{name}/tree/{commit_hash}")
            r2 = await client.get(
                f"/repos/{owner}/{name}/tree/{commit_hash}", params={"recursive": "true"}
            )
            # 都应返扁平 entries（旧扁平无 type=tree，recursive 是 no-op）
            assert r1.json()["entries"] == r2.json()["entries"]
            assert r1.json()["entries"][0]["name"] == "dir/file.txt"
        finally:
            await _delete_repo_cascade(owner, name)
