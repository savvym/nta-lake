---
change_id: pipeline-orchestrator-mvp-20260518
version: 2
authored_at: 2026-05-18T08:45:00Z
branch: application-owner/pipeline-orchestrator-mvp-20260518
base_commit: 8a1a055
head_commit: (uncommitted; 见 git status --short)
status: waiting_review
prior_report: coding/coding_report_v1.md
prior_review: coding/review/code_review_v1.md
---

# Coding Report v2

> **v2 修订说明**：闭 stage 4 code_review_v1.md 的 2 MUST FIX + 4 高价值 SHOULD FIX，3 条 SHOULD FIX 显式 deferred。

## v1 review 闭环表

| # | 类别 | 位置 | v1 问题 | v2 状态 | 证据 |
|---|---|---|---|---|---|
| MUST #1 | 依赖完整性 | `apps/api/pyproject.toml` | PyYAML 未声明直接依赖 | **CLOSED** | `dependencies` 追加 `"PyYAML>=6.0,<7"`；`uv lock` 通过；`uv run python -c "import yaml"` OK |
| MUST #2 | 错误截断 | `runner/orchestrator.py:142` | HTTPException error 路径无 `[:500]` 截断（违 spec R-5） | **CLOSED** | 改为 `error = str(getattr(exc, "detail", exc))[:500]`；与 R-5 承诺一致；HTTPException.detail 含长 list 时不会污染 pipeline_runs.error 字段 |
| SHOULD #1 | 字段语义 | `models/pipeline.py` + `migration 0004` + `orchestrator.py` | `cache_key=""` 占位与 NOT NULL 索引语义混乱 | **CLOSED via 选 (a)** | `cache_key` / `input_commits_json` 改为 `nullable=True`；migration 0004 同步；orchestrator 兜底路径写 `None` 而非空串；index 仍存在但空串不再污染 |
| SHOULD #2 | enqueue 失败 | `routers/pipelines.py:64-78` | enqueue 失败 → PipelineRunORM(queued) 残留 orphan | **CLOSED** | `_create_run_and_enqueue` 包 try/except；enqueue 异常时 `await session.delete(run); await session.commit(); raise`；orphan 不再残留 |
| SHOULD #3 | spec ↔ self_check drift | `scripts/_self_check.sh` AC-12 引用 vs spec AC-12 引用 | spec AC-12 引 `test_pipeline_e2e.py`，self_check 用 ruff+mypy 替代 | **DEFERRED 到 stage 5** | T-7c e2e 测试在 stage 5 补；届时 spec v3 把 AC-12 命令对齐 `test_pipeline_e2e.py`；本 stage 不强制 |
| SHOULD #4 | schema 早抛错 | `schemas/pipeline.py:81` | `inputs: list[str]` 允许 [] | **CLOSED** | `inputs: list[str] = Field(min_length=1)`；空 list 在 Pydantic 阶段 422，不再进 orchestrator |
| SHOULD #5 | `@auto` 语义 | `orchestrator.py:246` | `@auto → "main"` hardcode 未在 spec 澄清 | **DEFERRED**：spec v3 补充 / follow-up `pipeline-auto-ref-semantics-*` | hardcode 当前 OK（design.md §4.3 默认 main）；spec v3 / follow-up 决定是否换更复杂方案（如 `run-<run_id-short>`）；不阻塞本 stage |
| SHOULD #6 | 事务边界 | `orchestrator.py::_run_node` | 多次 commit；cache.insert + node_run.insert 不在同一事务 | **DEFERRED + 文档化** | 现状接受"节点级 partial failure"（cache 写入但审计行缺失场景概率极低，且 cache_key 唯一性保证下一次仍命中复用）；follow-up `pipeline-transaction-model-*` 显式定义跨节点错误恢复语义 |
| NICE #2 | 冗余 except | `routers/pipelines.py:103` | `except (ValueError, Exception)` 冗余 | **CLOSED** | 改为 `except Exception as exc` 单 catch |
| NICE #7 | parse 重复调用 | `orchestrator.py:159-160` | `parse_processor_ref(node.processor)` 调 2 次 | **CLOSED** | 解一次缓存到 `fb_name, fb_version` |

## v2 改动文件清单（增量；v1 已落地的不再列）

| 路径 | 改动 | 类型 |
|---|---|---|
| `apps/api/pyproject.toml` | 加 `PyYAML>=6.0,<7` 到 dependencies | mod (v2 增) |
| `apps/api/dataplat_api/runner/orchestrator.py` | MUST #2 `[:500]` 截断；NICE #7 parse 合并；SHOULD #1 兜底 `None` 而非 `""` | mod |
| `apps/api/dataplat_api/models/pipeline.py` | `input_commits_json` / `cache_key` 改 `nullable=True` | mod |
| `apps/api/alembic/versions/0004_pipeline_orchestrator.py` | 同步 nullable=True | mod |
| `apps/api/dataplat_api/schemas/pipeline.py` | `inputs: Field(min_length=1)`；`PipelineNodeRunResponse.input_commits/cache_key` 改 Optional | mod |
| `apps/api/dataplat_api/routers/pipelines.py` | enqueue 失败回滚；input_commits 序列化兼容 None；除冗余 except | mod |

合计 v2 修改 6 个既有文件；无新增源文件。

## 与 tasks.md 的映射（v2 无变化）

T-0 ~ T-8 + T-9 全 done（同 v1）；T-10 stage-4 review 当前 in_progress（v1 REVISION REQUIRED → v2 复检 pending）。

## 偏离 spec / trade-off（v2 仍存）

继承 v1 的 3 条偏离（MVP single-input only / T-7c e2e deferred / 本机 MinIO 403），均已被 stage 4 v1 reviewer 接受。v2 新增 trade-off：

### 新偏离 4：`cache_key` / `input_commits_json` 由 NOT NULL 改 nullable（SHOULD #1 修复）

- **理由**：stage 4 v1 reviewer 指出 error 兜底用 `cache_key=""` 占位会污染索引语义；选 (a) NULLABLE 比 (b) 重构 `_run_node` 改动面小。
- **影响**：
  - cache hit / miss 正常路径仍写完整 cache_key + input_commits_json（**v2 SHOULD #2 原本要求 NOT NULL 的审计完整性在正常路径仍 100% 落地**）
  - error 兜底路径写 NULL（明确表示"未解析到该步骤"）
  - 索引仍存在但 NULL 不进 b-tree index（PG 标准行为）
- **测试覆盖**：现有 `test_cache_hit_writes_audit_fields` 仍验证 cache hit 路径两字段非空；建议 stage 5 加 `test_error_path_writes_null_cache_key` 显式覆盖 error 路径

## 本地校验结果（v2）

```text
uv run ruff check apps/api packages/core worker/src
  → All checks passed!

uv run mypy apps/api/dataplat_api packages/core/src worker/src
  → Success: no issues found in 94 source files

uv run pytest -q apps/api/tests/test_pipeline_schemas.py
                  apps/api/tests/test_pipeline_dag.py
                  apps/api/tests/test_pipeline_cache.py
                  apps/api/tests/test_processor_runner_backcompat.py
                  apps/api/tests/test_pipeline_orchestrator.py::{test_unknown_processor,test_cycle,test_unknown_node_ref,test_multi_input_rejected}
  → 25 passed in 0.81s

bash scripts/_self_check.sh pipeline-orchestrator-mvp
  → 11 PASS / 2 FAIL（AC-7/AC-8，本机 MinIO 凭证问题；CI 同模板 PASS；偏离 3 已 reviewer 接受）
```

## 已知未解决问题（v2 已 reviewer 接受 deferred 部分）

- **stage 4 SHOULD #3 / #5 / #6**：见 v1 review 复检指引；本 stage 不强制；spec v3 在 stage 5 复检时一并修
- **`test_pipeline_e2e.py`**：stage 5 补；届时 self_check AC-12 命令与 spec 对齐
- **NICE TO HAVE 9 条**：3/9 在 v2 闭环（#2 / #7 / 部分 #3）；6/9 deferred 不阻塞

## 下一步

- 准备 stage 4 v2 复检：spawn `claude-agent:pipeline-orchestrator-mvp-20260518-stage4-reviewer-v2`
- summary.md stage=coding_review status=in_progress，verdict 待 v2 reviewer 决定
