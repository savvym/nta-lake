---
change_id: tree-nested-domain-20260520
version: 2
authored_at: 2026-05-19T14:00:00Z
revised_at: 2026-05-19T14:25:00Z
revision_notes: |
  v2 修 stage 2 reviewer v1 报的 2 条 tasks MUST FIX：
  - MUST FIX-1（T-2 颗粒度违规）：拆为 T-2a（_validate_tree_paths）+ T-2b（_normalize_to_nested）。
  - MUST FIX-2（T-3 步骤 1 blob 校验范围未明）：显式注明"步骤 1 blob 存在性校验保持原位（在 normalize 之前对全扁平 entries 调用，全是 type=blob，target_hash 全是 blob hash），不要移到 normalize 之后"。
---

# Tasks

```yaml
tasks:
  - id: T-1
    title: schemas/tree.py 放宽 entry_type Literal
    description: |
      TreeEntryCreate.entry_type / TreeEntryRead.entry_type 从 Literal["blob"]
      放宽到 Literal["blob", "tree"]；顶部 docstring 移除"MVP 仅支持单层"；
      改为说明 "soft mode：调用方传扁平 name（含 /），服务端自动 nested 化"。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1]
    status: pending

  - id: T-2a
    title: services/commit.py 新增 _validate_tree_paths
    description: |
      _validate_tree_paths(entries: list[TreeEntryCreate]) -> None：
        遍历 entries，对每个 entry：
        - 拒 name == ""
        - 拒 name 含 "//"
        - 拒 name 以 "/" 起或结尾（如 "a/" / "/a" / "/" / "a/b/"）
        - 按 "/" 切 segments，对每个 segment：
          - segment == "." 或 ".." → ValueError
          - segment.strip() == "" → ValueError（空白 segment：" a" / "a/ /b" / "a/  "）
        - entry_type == "tree" 时 mode != 0o040000 (16384) → ValueError（防御性边界；soft mode 内部不会触发，但 API 直接 POST 嵌套结构时会）
      全部 entries 遍历完后做交叉校验：
        - 同名 blob 与目录冲突：扫所有 entries，对每个 entry 求其所有 prefix（"a/b/c" → ["a", "a/b"]）；若某 prefix 同时作为另一 entry 的整 name 出现（type=blob）→ ValueError
        - normalize 后同层重名：在 _normalize_to_nested 内做（在该函数里也有 detect）
      失败 raise ValueError 含详细错误消息（哪个 name 哪个 segment 为什么 reject），便于路由层 400 透传。
      颗粒度估算：~1.5h（含 6 类校验 + crossover）
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-3]
    status: pending

  - id: T-2b
    title: services/commit.py 新增 _normalize_to_nested
    description: |
      _normalize_to_nested(entries: list[TreeEntryCreate]) -> tuple[str, list[tuple[str, list[TreeEntryCreate]]]]：
        - 输入：扁平 entries（name 可含 /）；已通过 _validate_tree_paths
        - 算法：
          1. 构 in-memory trie：把每个 entry 按 / 切 segments，挂到 trie 节点；
             叶子节点存 (mode, target_hash)；内部节点是子目录
          2. 自底向上递归：每个内部节点对应一个子 tree，其 entries 包含
             (a) 该节点直接子 blob entry：name=最末 segment，mode/type/target_hash 沿用
             (b) 该节点直接子目录 entry：name=子目录 segment，mode=0o040000 (16384)，
                 type=tree，target_hash=子 tree hash（递归先算）
          3. 同层重名再次 detect → ValueError（理论上 _validate_tree_paths 已经拒，但 normalize 内冗余检查兜底）
          4. 用 _canonical_tree_bytes + sha256 算每个子 tree 的 hash
        - 返 (root_tree_hash, all_trees: list[(tree_hash, entries_at_that_level)])
          all_trees 顺序：子 tree 在前，root 在最后（持久化时按顺序 upsert 不会断 FK 引用）
        - 空 entries → 返 _tree_hash([]) + [(root_hash, [])]（空 root tree 合法）
      颗粒度估算：~2h（含 trie 构造 + 递归 hash + 顺序保证 + 空 tree 边界）
    depends_on: [T-2a]
    estimated_stage: coding
    covers_ac: [AC-2, AC-4]
    status: pending

  - id: T-3
    title: CommitService.create_commit 改步骤 2 + 步骤 4（步骤 1 不动）
    description: |
      **步骤 1（blob 存在性校验）：保持原位不动**——在 _normalize_to_nested 之前对
      payload.tree.entries（**全扁平、全 type=blob、target_hash 全是 blob hash**）调
      store.exists；不要把这个校验移到 normalize 之后（移过去会用子 tree hash 调
      store.exists 永远 miss → 400）。reviewer v1 MUST FIX-2 显式指出此风险。

      **步骤 2（算 tree_hash + commit_hash）改为：**
        - _validate_tree_paths(payload.tree.entries) → 失败抛 ValueError → 路由层 400
        - root_tree_hash, all_trees = _normalize_to_nested(payload.tree.entries)
        - tree_hash = root_tree_hash
        - 其余 _commit_hash 计算不变（基于 tree_hash）

      **步骤 4（事务内写）改为：**
        - 原逻辑：upsert 单个 tree + N 行 TreeEntryORM
        - 改为：遍历 all_trees：
            for tree_hash, entries_at_level in all_trees:
                if await session.get(TreeORM, tree_hash) is None:
                    session.add(TreeORM(hash=tree_hash, repo_id=repo_id))
                    for pos, e in enumerate(sorted(entries_at_level, key=lambda x: x.name)):
                        session.add(TreeEntryORM(tree_hash=tree_hash, position=pos,
                            name=e.name, mode=e.mode, entry_type=e.entry_type,
                            target_hash=e.target_hash))
        - commit 那行不动
        - ref upsert / race 处理不动
        - 注意：子 tree 的 entries 里 name 已经是"仅本级 segment"（不含 /）

      颗粒度估算：~1.5h（含步骤 2/4 改造 + 顺序保持事务一致性）
    depends_on: [T-2b]
    estimated_stage: coding
    covers_ac: [AC-4, AC-5, AC-6]
    status: pending

  - id: T-4
    title: routers/commits.py get_tree 加 recursive + 新增 subtree by hash 端点
    description: |
      get_tree (/{owner}/{name}/tree/{commit_hash})：
        加查询参数 recursive: bool = Query(False, alias="recursive")
        - 默认 (recursive=False)：返当前根 tree 的直接 entries（含 type=tree 的子目录 entry）
        - True：递归展开 → 输出全为 type=blob 的 leaf 列表；entry.name 为扁平全路径
          实现：辅助函数 _expand_tree_recursive(session, repo_id, tree_hash, prefix="")
            walk TreeEntryORM by tree_hash；如 type==tree 递归 + prefix=prefix+name+"/"；
            如 type==blob 直接 emit TreeEntryRead(name=prefix+name, mode, type=blob, target_hash)

      新端点 GET /repos/{owner}/{name}/trees/{tree_hash}（注意复数）：
        get_subtree_by_hash(owner, name, tree_hash: str = Path(pattern=_SHA256_PATTERN)) -> TreeRead
        - 校验 repo 可访问
        - 查 TreeORM by (hash=tree_hash, repo_id=repo.id)；
          注意：跨 repo 不暴露（即便 hash 相同；安全边界）
        - 不存在 → 404
        - 返该层 entries（含子 tree entry）

      `recursive` 默认 False 的接口契约：默认行为变了（扁平 commit 没区别；嵌套 commit 现在只看本级），但旧扁平 commit 全是 blob 故行为不变；新 commit 默认看本级符合"类 git ls-tree"语义。
    depends_on: [T-3]
    estimated_stage: coding
    covers_ac: [AC-7, AC-8, AC-9]
    status: pending

  - id: T-5
    title: tests/test_tree_nested.py 新建 ≥ 8 用例
    description: |
      apps/api/tests/test_tree_nested.py（独立测试文件；不污染 test_commits.py 现有断言）
      用 ASGITransport + AsyncClient（与 test_commits.py 一致）；admin 登录拿 cookie；
      用 PUT blobs 写若干 blob → POST commits with flat-name tree entries → 各种 GET。

      用例清单（≥ 8）：
        1. test_post_flat_input_round_trip：POST entries 含 "images/a.jpg" / "images/b.jpg" / "paper.md"
           → GET tree?recursive=1 返 3 个 leaf，name 形态与 input 一致；root tree 默认返 2 个 entry（images + paper.md）
        2. test_get_tree_default_shows_subtree：默认 GET /tree/{commit_hash} 返 type=tree 的 images entry，其 target_hash 可用于下一步 GET /trees/{subtree_hash}
        3. test_get_subtree_by_hash：用 step 2 拿到的 subtree_hash → GET /trees/{subtree_hash} 返 a.jpg + b.jpg 两 entry（type=blob）
        4. test_get_tree_legacy_flat_unchanged：直接 INSERT 一个旧扁平 TreeORM（绕过 create_commit，模拟历史数据） → GET /tree/{commit_hash} 返扁平 entries（不变形）
        5. test_dedup_same_subtree_across_commits：两个不同 commit 都含 images/{a.jpg,b.jpg} → 同 subtree_hash；DB 只有一行 images-tree TreeORM
        6. test_path_validation_rejects：覆盖 "" / "//a" / "a//b" / "a/../b" / "a" 同时 "a/b"（冲突）；预期 400
        7. test_deep_nested_3_levels：entries 含 "a/b/c/d.txt" → root.entries=[a], a-tree.entries=[b], b-tree.entries=[c], c-tree.entries=[d.txt]
        8. test_empty_tree：POST commit with tree.entries=[] → root_hash 计算成功，no subtree；GET 返空
        9. test_recursive_no_op_on_flat：旧扁平 commit GET ?recursive=1 与默认形态一致（no-op）

      fixture 复用 test_commits.py 的 _seed_admin_user / _async_client_with_app；admin 是 admin role 才能创 commit。
    depends_on: [T-4]
    estimated_stage: unit_test
    covers_ac: [AC-9, AC-10, AC-11]
    status: pending

  - id: T-6
    title: scripts/_self_check.sh 加 run_tree_nested_domain 14 AC
    description: |
      在 run_repo_files_tab_v2 后插入 run_tree_nested_domain 函数（14 AC）；
      filter case + 全跑入口 list 都加上。
      AC-9 / AC-10 / AC-11 / AC-13 用 run_ac（纯 pytest，不依赖 pg/minio/redis 之外的服务；
      但 test_tree_nested.py 是端到端 ASGI 测试，需要 pg/minio/redis；故用
      run_ac_skipif_no_pg_minio_redis 类比 test_commits.py）。
    depends_on: [T-5]
    estimated_stage: ci_result
    covers_ac: [AC-14, AC-12, AC-13]
    status: pending

  - id: T-7
    title: 本地 lint / pytest / self_check current 全绿 + 上游回归
    description: |
      uv run ruff check apps/api packages/core worker/src
      uv run mypy apps/api/dataplat_api packages/core/src worker/src
      cd apps/api && uv run pytest -q tests/test_tree_nested.py
      bash scripts/_self_check.sh current tree-nested-domain-20260520 全绿
      bash scripts/_self_check.sh current commit-api-mvp-20260517 不回归
      bash scripts/_self_check.sh current processor-framework-20260517 不回归
      bash scripts/_self_check.sh current processor-pdf-mineru-20260519 不回归
      bash scripts/_self_check.sh current processor-pdf-mineru-assets-20260520 不回归
    depends_on: [T-6]
    estimated_stage: ci_result
    covers_ac: [AC-11, AC-12, AC-13]
    status: pending
```

## 阶段任务

```yaml
process_tasks:
  - id: P-spec-review
    estimated_stage: request_analysis_review
    status: pending       # 走完整 reviewer spawn（用户钉死本 change 不 self-attest 偏离）
  - id: P-code-review
    estimated_stage: coding_review
    status: pending       # 同上
  - id: P-test-review
    estimated_stage: unit_test_review
    status: pending       # 同上
  - id: P-push
    estimated_stage: stage-7
    status: pending
  - id: P-ci
    estimated_stage: ci_result
    status: pending
  - id: P-deploy
    estimated_stage: deployment
    status: pending        # noop（无部署面；仅后端代码 + 测试 + self_check）
  - id: P-user-confirm
    estimated_stage: user_confirmation
    status: pending
```

## DAG

T-1 → T-2a → T-2b → T-3 → T-4 → T-5 → T-6 → T-7（无环）

## 验收覆盖

| AC | 任务 |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-2b |
| AC-3 | T-2a |
| AC-4 | T-2b, T-3 |
| AC-5 | T-3 |
| AC-6 | T-3 |
| AC-7 | T-4 |
| AC-8 | T-4 |
| AC-9 | T-4, T-5 |
| AC-10 | T-5 |
| AC-11 | T-5, T-7 |
| AC-12 | T-7 |
| AC-13 | T-7 |
| AC-14 | T-6 |
