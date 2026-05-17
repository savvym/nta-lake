---
change_id: adapter-framework-20260517
version: 1
authored_at: 2026-05-17T11:50:00Z
branch: main (session 直推 main 等价模式)
base_commit: c1a9e0a (commit-api-mvp close)
head_commit: working-tree
status: waiting_review
---

# Coding Report v1

## 改动文件清单

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `packages/core/src/dataplat_core/protocols/adapter.py` | edit | 新增 `IngestFileRef` + `IngestResult.files` 字段（既有字段保留；33 core 测试 0 回归） | T-1 |
| `packages/core/src/dataplat_core/protocols/__init__.py` | edit | export `IngestFileRef` | T-1 |
| `apps/api/dataplat_api/runner/__init__.py` | new | 模块入口；export Registry/Context/Runner | T-2/3/5 |
| `apps/api/dataplat_api/runner/registry.py` | new | `AdapterRegistry` + `get_registry()` 单例（幂等 register） | T-2 |
| `apps/api/dataplat_api/runner/runcontext.py` | new | `StandardRunContext` dataclass 满足 RunContext Protocol | T-3 |
| `apps/api/dataplat_api/runner/adapter_runner.py` | new | `AdapterRunner.run` async 3-tuple；含 parent 自动接链 + 错误翻译 | T-5 |
| `apps/api/dataplat_api/adapters/__init__.py` | new | module load 自动注册 RawFileUploadAdapter | T-4 |
| `apps/api/dataplat_api/adapters/raw_upload.py` | new | `RawFileUploadAdapter` 校验 + pass-through | T-4 |
| `apps/api/dataplat_api/schemas/ingest.py` | new | `IngestRequest` / `IngestSummary` / `IngestResponse`（含 `parents`） | T-6 |
| `apps/api/dataplat_api/schemas/__init__.py` | edit | export 3 ingest schemas | T-6 |
| `apps/api/dataplat_api/routers/ingest.py` | new | `POST /repos/{o}/{n}/ingest` admin only + `_resolve_repo` | T-6 |
| `apps/api/dataplat_api/main.py` | edit | import adapters 触发自动注册 + `include_router(ingest_router)` | T-6 |
| `packages/api-types/openapi.json` | edit | `make codegen` 同步：`/repos/{o}/{n}/ingest` 1 新 path | T-7 |
| `apps/api/tests/test_ingest.py` | new | 13 测试（a 单元 registry + b 单元 raw + c~m 集成；含 m parent 链） | T-8 |
| `scripts/_self_check.sh` | edit | 追加 `run_adapter_framework` 13 AC + filter | T-9 |
| `.harness/skills/request-analysis/SKILL.md` | edit | 反哺：跨 AC 自审清单 4→7 条（commit-history 连续性 / 反向 grep / process_tasks 6 条） | stage-2 review v1 反哺 |

> **门禁**：与 `git status --short` 完全一致。

## 与 tasks.md 的映射

| Task | 状态 | 备注 |
|---|---|---|
| T-1 IngestResult.files | done | 既有 33 core 测试无回归 |
| T-2 Registry | done | 幂等 register；warning 跳过；AC-11 (a) 单元覆盖 |
| T-3 StandardRunContext | done | dataclass 5 字段；runtime_checkable 通过 |
| T-4 RawFileUploadAdapter | done | 内部 Pydantic 校验；不写 workspace；不依赖 ctx |
| T-5 AdapterRunner | done | 3-tuple `(commit, dedup, result)`；parent 自动接链（spec v2 修 MUST FIX-1） |
| T-6 schemas + router | done | `IngestRequest.parents: list[SHA256]` 允许 client 显式传 |
| T-7 codegen | done | openapi.json 同步 1 新 path |
| T-7b lint+mypy gate | done | ruff All / mypy 57 files Success |
| T-8 tests | done | 13 测试 PASS（PG 5433 + MinIO 9100） |
| T-9 self_check | done | 13 AC + 双探针 helper 复用 |

## 偏离 spec / trade-off

- **AC-9 反向 grep 沉默通过修复落地**：实现端的 `routers/ingest.py` + `runner/adapter_runner.py` 创建后，spec v2 AC-9 命令 `test -f ... && grep -qE "_resolve_repo|RepoService.get_by_owner_name" ... && ! grep -rE "_visibility_visible" ...` 实测 exit=0；这是 [project-followup-harness-lint] 第 6 次教训反哺的回归证据。
- **parent 自动接链行为**：第二次 ingest 到相同 ref 时，C2.parents = [C1.hash]；test_m 端到端覆盖。spec v2 风险 #8 提到的"不传 ref 也不传 parents → root commit"边界由 client 自负历史链——MVP 接受。
- **`IngestRequest.parents` 字段**：v2 加 `list[SHA256]` 允许 client 显式 override 自动接链；与 commit-api `CommitCreate.parents` 同构。

## 本地校验结果

```text
=== ruff check ===
All checks passed!

=== mypy ===
Success: no issues found in 57 source files

=== pytest（PG 5433 + MinIO 9100 dataplat-secret）===
apps/api/tests: 64 passed in ~24s
  - 13 新 test_ingest.py (a 单元 + b 单元 + c~m 集成)
  - 18 既有 test_commits.py 回归
  - 14 既有 test_repos.py 回归
  - 11 既有 test_auth.py 回归
  - 5 MinIO + 2 ORM smoke + 1 health
packages/core/tests: 33 passed（IngestResult 加字段无回归）

=== bash scripts/_self_check.sh adapter-framework ===
PASS=13 FAIL=0 SKIP=0

=== bash scripts/_self_check.sh （全仓）===
PASS=108 FAIL=0 SKIP=0

=== make codegen ===
openapi.json 同步：/repos 命名空间 9 paths（含 /ingest）
```

## 已知未解决问题

- **`IngestRequest.parents` 默认空 + 不传 ref**：第二次 ingest 走 root commit 路径（孤立）。MVP 接受；spec v2 风险 #8 标注；client 自负此责。
- **Protocol property vs dataclass 字段**：StandardRunContext 用 dataclass 字段实现 RunContext Protocol 的 @property——runtime_checkable + mypy 通过；未来若 Protocol 升级 read-only property（setter raise），需改为 `property + __init__`。

## reviewer 重点关注

1. **parent 自动接链正确性**：test_m 是否真覆盖父子链？C1.parents=[]、C2.parents=[C1.hash]、C1 仍可达？
2. **AC-9 反向 grep 修复**：实际跑 self_check AC-9 应为 PASS（实现端真复用 RepoService.get_by_owner_name 且不重复 _visibility_visible）
3. **adapter 注册时机**：main.py `import dataplat_api.adapters as _adapters` 是否在 router include 之前？是否会因 import 顺序漏注册？
4. **dependency_overrides 漏关**：test fixture teardown 是否会污染下个测试？跨 test_commits / test_ingest 共存时？
5. **`asyncio.to_thread` 真的让 ingest 不阻塞 event loop 吗**：对 RawFileUpload 这种 pass-through 微秒级 adapter 是否过度设计？长跑 adapter 留 RQ follow-up 是否清晰？
6. **`IngestResult.files` 加字段**：core 既有 33 测试无回归——已实测。是否影响 SDK 客户端？（尚无 SDK；packages/sdk-py 是空壳）

## 下一步

stage 4 编码评审：独立 reviewer 复核 working-tree diff（base = c1a9e0a）。
