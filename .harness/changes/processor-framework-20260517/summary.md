---
change_id: processor-framework-20260517
title: Processor 框架 + markdown-normalize + POST /process + jobs dispatch
owner: zhhdzhang
started_at: 2026-05-17T18:00:00Z
closed_at: 2026-05-17T19:30:00Z
stage: closed
status: closed
last_updated: 2026-05-17T19:30:00Z
related_changes:
  - adapter-framework-20260517
  - rq-worker-skeleton-20260517
  - commit-api-mvp-20260517
  - cas-storage-20260517
note: 第 11 个 dataplat 变更，纵深扩 Silver/Gold——把 packages/core 已定义的 Processor Protocol 落到 ProcessorRegistry + ProcessorRunner + 至少 1 个 processor + HTTP 触发 + worker dispatch；解锁未来 PDF→text→SFT 端到端流水线
---

# Summary

## 一句话目标

把 packages/core 已经定义但没有 runner / 实现 / 触发面的 Processor Protocol 落地为 ProcessorRegistry + ProcessorRunner + DbRepoView + markdown-normalize + POST /process + jobs.run_process_job + service.enqueue 按 job_type dispatch，解锁后续 LLM Gateway + 真实 PDF/HTML processor 与端到端 Bronze → Silver → Gold 流水线。

## 范围摘要

- **In scope**：runner 三件套（registry/runner/repo_view）/ markdown-normalize processor / ProcessRequest+POST /process（admin）/ run_process_job + dispatch / StandardRunContext.blob_store / ≥ 8 集成测试 / self_check 13 AC
- **Out of scope**：Schema Registry / iter_records / parallel map / subprocess 隔离 / web UI / 真 PDF/HTML processor / cycle detection / LLM Processor（待 llm-gateway-mvp）

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 产物 |
|---|---|---|---|---|
| 1 需求分析 | done | v1 | — | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | done | v1 | APPROVED | [spec_review_v1.md](request_analysis/review/spec_review_v1.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md) |
| 3 编码实现 | done | v1 | — | [coding_report_v1.md](coding/coding_report_v1.md) |
| 4 编码评审 | done | v1 | APPROVED | [code_review_v1.md](coding/review/code_review_v1.md) |
| 5 单测编写 | done | v1 | — | [test_report_v1.md](unit_test/test_report_v1.md) |
| 6 单测评审 | done | v1 | APPROVED | [test_review_v1.md](unit_test/review/test_review_v1.md) |
| 7 代码推送 | done | — | — | feat commit + chore close commit（见 §交付） |
| 8 CI 验证 | done | v1 | PASS | [ci_result_v1.md](ci_result/ci_result_v1.md) |
| 9 部署验证 | done | v1 | PASS | [deploy_verify_v1.md](deployment/deploy_verify_v1.md) |
| 10 用户确认 | done | — | — | 用户 2026-05-17 显式授权 "你合理安排规划" |

## 关键决策

| 时间 | 决策 | 理由 / 取舍 | 关联文件 |
|---|---|---|---|
| 2026-05-17 | 沿 adapter framework 同构（Registry/Runner/Context 三件套） | 减少抽象成本 + 团队心智一致；MVP 不抽 BaseRegistry 避免过早抽象 | code_review §跨改动观察 |
| 2026-05-17 | run_process_job 用独立 async engine（不复用 API engine） | 跨进程隔离，与 run_ingest_job 同 pattern；engine 重复 deferred 到 `worker-engine-pool-*` | coding_report §偏离 |
| 2026-05-17 | source_ref == target_ref 允许（不做 cycle detection） | CAS 内容不变 → commit hash 不变 → 实际空操作；MVP 不必复杂化 | spec §风险 / code_review NICE TO HAVE |
| 2026-05-17 | AC-1 注册时补 test -f 前置（不改 spec） | reverse-grep checklist 第 6 条；spec_review SHOULD FIX 形式记录 | spec_review §SHOULD FIX |
| 2026-05-17 | AC-8 用双正向 grep（比 spec 严格） | service.py 必须同时含 run_process_job + run_ingest_job 才能证明 dispatch | coding_report §偏离 |

## 当前阻塞

无。

## Deferred 项（已 review 通过但未在本 change 内修）

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| SHOULD FIX | run_process_job / run_ingest_job 独立 engine 创建重复 | follow-up `worker-engine-pool-*` |
| NICE TO HAVE | ProcessorRunner.run 函数 ≈ 70 行偏长 | 加规则时再考虑拆 |
| NICE TO HAVE | end-to-end 断言可加 blob 内容验证 | follow-up `processor-test-content-assert-*` |
| Out of scope | cycle detection / iter_records / parallel map / subprocess 隔离 | 各自 follow-up change |
| harness-lint | 历史 closed change 全部漏删 _template README.md，违反模板自身明文规则 | follow-up `harness-lint-template-readme-*`；并入 [[project-followup-harness-lint]] 分层校验体系 |

## 交付

- Branch：`main`（直接在 main 上跑，沿前 10 变更 pattern）
- PR：n/a（本仓 MVP 不用 PR；改动通过 self_check 173/173 + 双 commit 验证）
- feat commit：见 git log（feat(processor): ...）
- chore close commit：见 git log（chore(processor): close ...）
- 部署版本：dev 本地 `uv run` 启的 API + worker（无 image）
- 用户确认：2026-05-17 通宵会话开题授权 "所有的东西不需要我进行确认，你合理安排规划"
- 关闭时间：2026-05-17T19:30:00Z

## 复盘

### 顺利

- **协议先行 + Registry/Runner 同构**：adapter framework 已铺好 pattern，processor 镜像化复制 → 设计零摩擦
- **8 集成测试一次性全 PASS**：得益于 rq-worker-skeleton 的 thread + 直接 dequeue trick 已成熟
- **mypy 一次过 76 files**：Pydantic v2 + Protocol + dataclass 组合稳定

### 踩坑

1. **session 启动时未读最新 summary**：summary.md 留模板 + spec/代码先写。流程上违反 "summary.md 是 SSoT，每阶段同步" 规则。本次手工补齐。
   - **防复发**：把 "进入 change 目录第一步：先把 summary.md frontmatter 填好 stage=in_progress + started_at" 加到 `.harness/skills/request-analysis/SKILL.md` checklist 第 9 条。

2. **ruff 一次 I001 import 排序错误**：test 文件内嵌 import 块未自动排序。
   - **防复发**：已用 `ruff check --fix` 解决；本类问题在 pre-commit hook 里挡掉即可（追踪在 `pre-commit-hook-setup-*` follow-up）。

3. **历史 closed change 全部漏删 README.md**：`.harness/changes/_template/README.md` 自身明文写 "本文件不应出现在任何具体 change 目录里 / 立即 rm 掉"，但前 10 个 closed change（harness-bootstrap / bootstrap-monorepo / core-domain-model / cas-storage / auth-scaffold / repo-api-mvp / commit-api-mvp / adapter-framework / web-mvp-pages / rq-worker-skeleton / web-write-flows / repo-files-tab）**全都把模板 README 一起 commit 进去了**。本变更主动 rm 掉。
   - **防复发**：harness-lint 候选规则——在 close 前扫描 `.harness/changes/<id>/README.md` 是否与 `_template/README.md` 完全一致，是则报错（参 [[project-followup-harness-lint]]）。已在 Deferred 表加 follow-up `harness-lint-template-readme-*`。

### SKILL 反哺

- `.harness/skills/request-analysis/SKILL.md` 跨 AC 自审清单累计第 9 条：**summary.md frontmatter 必须在 stage 1 启动时就填好 stage / started_at / status，避免 SSoT 漂移**（rq-worker-skeleton 第 8 条之后第 9 次反哺）；附第 9 条 grep 自查命令（模板占位符残留检查）。
- AC-8 双正向 grep 优于单 alternation grep 是新经验，记为 "dispatch wiring AC 验证模式"，可在未来 jobs-dispatch-registry-* 等变更复用。
