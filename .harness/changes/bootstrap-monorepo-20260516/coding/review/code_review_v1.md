---
change_id: bootstrap-monorepo-20260516
target: coding/coding_report_v1
target_head: 287d45e (尚未 commit；stage 3 工作在 working tree)
review_version: 1
reviewer: claude-agent:bootstrap-monorepo-stage4-reviewer
reviewed_at: 2026-05-16T21:12:53Z
verdict: REVISION REQUIRED
---

# Code Review v1

## 范围与作者声明对照

- coding_report 声明：38 手写 + 3 生成（`uv.lock` / `pnpm-lock.yaml` / `openapi.json`）= 41 项。
- `git status -uall` 实测 working tree 新增 / 未跟踪文件 = **42 个**（不含 `dist/` 与 `.pytest_cache/`，二者已被 `.gitignore` 命中）。
- 差异 = 4 个 **未在 coding_report 列出且未被 `.gitignore` 忽略** 的"幽灵文件"：
  - `apps/web/vite.config.js`（553 B）
  - `apps/web/vite.config.d.ts`（76 B）
  - `apps/web/tsconfig.tsbuildinfo`（104 B）
  - `apps/web/tsconfig.node.tsbuildinfo`（20.4 KB）

这 4 个文件是 `pnpm --filter web build` 中 `tsc -b && vite build` 的第一步 `tsc -b` 输出 —— 因为 `apps/web/tsconfig.node.json` 声明 `composite: true` 且没有 `noEmit: true`，TS 编译器把 `vite.config.ts`（被 `include` 指向）真编译并落盘。本仓库尚未 commit；stage 7 `git add -A` 会把 4 个文件全部带进首个 commit。

> 详见 MUST FIX #1。其它 17 条 AC 全部本地复跑 PASS（含 AC-16 pytest `1 passed`、AC-17 `dist/index.html` 生成、AC-4 `make -n` 11 个 target 全干跑、AC-15 ci.yml YAML schema + 5 job + concurrency）。

## 正确性 / 安全 / 架构问题

### MUST FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | `apps/web/tsconfig.node.json:2-10` + `apps/web/vite.config.{js,d.ts}` + `apps/web/*.tsbuildinfo` | `tsconfig.node.json` 缺 `"noEmit": true`，导致 `pnpm --filter web build` 的 `tsc -b` 步骤产生 4 个未跟踪 / 未 ignore 的产物文件，会被 stage 7 commit 误带入仓库 history。这些是构建产物，不该入库；coding_report 也未声明它们。 | 二选一：(a) 在 `apps/web/tsconfig.node.json.compilerOptions` 加 `"noEmit": true`，让 `tsc -b` 仅做类型检查不落盘（推荐）；(b) 把 `apps/web/vite.config.js`、`apps/web/vite.config.d.ts`、`apps/web/*.tsbuildinfo` 加入根 `.gitignore`。修后跑 `pnpm --filter web build && git status apps/web/` 应只看到 `dist/`（已忽略）。 |
| 2 | `.github/workflows/ci.yml:95` | `pnpm --filter web test --run --reporter=junit --outputFile=junit-web.xml` 在 pnpm 9 下实测报 `ERROR Unknown options: 'run', 'outputFile'`。coding_report §偏离 spec #2 已识别 pnpm 9 吞 `--run` 的问题并修了 `make test` / `web/package.json`，但 **ci.yml 这一行漏改**。本 job 在 CI 上必失败 → AC-15 的 web-test job 形同摆设。 | 改成 `pnpm --filter web exec vitest run --reporter=junit --outputFile=junit-web.xml`（实测可跑出 junit），并把后续 artifact upload 的 `path` 同步指向实际写出路径（见 SHOULD FIX #1）。 |

### SHOULD FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | `.github/workflows/ci.yml:95-102` | `--outputFile=junit-web.xml` 在 `working-directory` 缺省（= repo root）时会写到仓库根 `junit-web.xml`，但同 job 第 101 行 `path: apps/web/junit-web.xml` 期望文件在 `apps/web/` 下 → artifact 上传必报 `No files found`。 | 与 MUST FIX #2 同改：要么 `--outputFile=apps/web/junit-web.xml` + 上传路径不变；要么改为 cd 进 apps/web 再跑（与 `python-test` 风格对齐）。 |
| 2 | `turbo.json:12-15` | `test: { dependsOn: ["^build"] }` 让任何 `pnpm test` / `turbo run test` 都先跑 build → 既慢、又会把 `dist/` 产物在 PR CI 上意外生成（虽然被 .gitignore，但 codegen-check job 的 `git diff --exit-code` 之前会跑 codegen 并不会跑 build，所以暂未失败）。本骨架阶段 test 不该依赖 build。 | 删 `test.dependsOn` 或改为 `["^typecheck"]`。 |
| 3 | `Makefile:55-60` | `lint` / `typecheck` 两 target 收尾 `\|\| true` 把所有 lint / mypy 失败吞掉。coding_report §已知未解决问题 #1 提到 follow-up 但未挂具体 task。当前 `make typecheck` 即使 mypy 报 100 个错也 exit 0，stage 5 等价校验时容易给出"PASS"假象。 | 现阶段策略二选一：(a) 立刻去掉 `\|\| true`，让 lint / typecheck 失败暴露；(b) 保留 `\|\| true` 但在 spec/tasks 加一个明确 follow-up（如 `harness-makefile-strict-lint-*` 变更 id 写入 summary §Deferred）。本评审接受 (b) 但要求落到 Deferred 表里。 |
| 4 | `coding_report_v1.md §改动文件清单` | 报告写"38 手写 + 3 生成 = 41"，但实测 working tree 多了 4 个 ghost build artifact 文件（见 MUST FIX #1），且未把它们披露在 §偏离 spec 或 §已知未解决问题里。报告本身的完备性掉线。 | 修完 MUST FIX #1 后，在 coding_report v2 §改动文件清单注脚加一行"apps/web/*.tsbuildinfo / vite.config.{js,d.ts} 是 tsc -b 的构建副产物，已通过 noEmit / gitignore 排除入库"。 |
| 5 | `.github/workflows/ci.yml:21,54,115` 与 `apps/api/pyproject.toml` | CI 全部 `uv sync --all-extras`，但 `apps/api/pyproject.toml` 的 dev 依赖（pytest / ruff / mypy）只在 `[project.optional-dependencies].dev` 下。`uv sync --all-extras` 在 workspace 根能否解出 member 包的 extras 取决于 uv 版本（≥ 0.4 才完整支持）；至少应显式 `uv sync --all-packages --all-extras` 与 stage 3 实跑命令对齐（coding_report §本地校验提到 `uv sync --all-packages --all-extras`，而 ci.yml 只有 `--all-extras`）。 | 改成 `uv sync --all-packages --all-extras`，保证 CI 与本地命令一致。 |
| 6 | `.github/workflows/ci.yml:77,93,116` | `pnpm install --frozen-lockfile` 要求 `pnpm-lock.yaml` 入库。本变更确实生成了 lockfile（且 `.gitignore` 通过 `!pnpm-lock.yaml` 显式不忽略）——但 stage 7 commit 必须把 `pnpm-lock.yaml` 一并入库，否则首个 PR 跑 CI 全失败。请在 coding_report §下一步 / summary §交付里明示。 | 在 coding_report v2 §下一步 + summary §交付里加"stage 7 commit 必须包含 `uv.lock` + `pnpm-lock.yaml` + `packages/api-types/openapi.json`"。 |

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | `apps/web/vite.config.ts:1` | `/// <reference types="vitest" />` 是 workaround；vitest 官方更推荐 `import { defineConfig } from "vitest/config"`，零三斜杠注释，类型完备。coding_report 已诚实披露 trade-off。 | 后续变更若引入更多 vitest 配置（coverage / threads / projects），切到 `vitest/config`。当前不阻塞。 |
| 2 | `apps/api/dataplat_api/main.py:17-23` | `HealthResponse` Pydantic 模型在 `/healthz` 仅返回一个字面量 `{"status": "ok"}`，相对 `coding-style.md` §0.3 "不写防御性废话" 稍偏重；直接 `return {"status": "ok"}` + `response_model=None` 也能过 AC-16。 | 接受现状（用 Pydantic 模型与后续业务路由风格一致，反而有利）。 |
| 3 | `docker/docker-compose.dev.yml:62-68` | `mailpit` service 无 healthcheck，与 postgres / minio / redis 三者风格不一致；coding_report 未提到。 | mailpit 非关键，AC-12 不门禁；如要补一致性，加 `healthcheck.test: ["CMD", "wget", "-qO-", "http://localhost:8025/"]`。 |
| 4 | `apps/web/tsconfig.json:14-19` | `strict + noUnusedLocals + noUnusedParameters + noUncheckedIndexedAccess` 一次性开满，是好事；但 `"types": ["vitest/globals", "@testing-library/jest-dom"]` 会让 `src/` 下生产代码也看到 vitest 全局类型（轻微污染）。 | 后续在 `tsconfig.test.json` 分离 test types。当前不阻塞。 |

## 风格 / 性能 / 可观测性

- `apps/web/src/App.tsx` 用 named export `export function App`（符合 `coding-style.md` §2.5"不写 default export"）；无 `any`；无注释（符合 §2.6）。
- `apps/api/dataplat_api/main.py` 全 async（符合 §1.4）；类型完整；docstring 是 WHY 而非 WHAT（符合 §1.6）。
- `scripts/export_openapi.py` 用 `__future__ annotations` + Path + 仓库根定位逻辑健壮；`# noqa: PLC0415` 局部禁用合理（运行期插入 sys.path 之后才能 import）。
- `Makefile` recipe 全 tab（`cat -A` 实测均 `^I` 起手）；AC-4 兜底已覆盖此风险。
- `coding-style.md` §1.7 关于测试质量底线：`apps/api/tests/test_health.py` 断言 `resp.status_code == 200 and resp.json() == {"status":"ok"}` 同时校验了 status code 与 body，符合 §1.7"不允许空跑测试"。

## 跨改动观察

- `coding_report §偏离 spec #2`（pnpm 9 吞 `--run`）只修了 `make test` 与 `web/package.json`，但 **ci.yml 的同款命令未同步修**。MUST FIX #2 的根因是"同一类问题没全量扫修改面"。建议后续 stage 3 编码完工后跑一次 `grep -rn "pnpm.*--run" .` 兜底。
- 4 个 ghost build artifact + 1 处 ci.yml 漏改 = 两处"局部修改未带全局扫描"。建议落到 `.harness/rules/coding-style.md` 或 skill 里加一条"修一处偏离时跑同模式 grep"。

## Deferred SHOULD FIX

> verdict = REVISION REQUIRED，本节暂不固化；待 v2 修完 MUST FIX 后，若 SHOULD FIX #3（Makefile `\|\| true`）选择 defer 路径，需在 summary §Deferred 表登记 follow-up 变更 id。

## 上轮遗留 SHOULD FIX 自查

- spec_review_v1 SHOULD #1（AC-16 grep 松匹配）：本轮 AC-16 用 `pytest -q tests/test_health.py` 直接取退出码，**已绕过 grep 问题**，不再相关。
- spec_review_v1 SHOULD #2（AC-6 缺前导 `.`）：spec 已修 → AC-6 实跑 PASS，闭环。
- spec_review_v1 SHOULD #3（AC-14 文字 vs 命令不一致）：本变更 `scripts/__init__.py` 已建，`python -m scripts.export_openapi` 实跑成功，闭环。
- spec_review_v1 SHOULD #4（风险表追加 2 条）：spec v2 已补；本评审接受。
- tasks_review_v1 SHOULD #1（T-16 缺 `__init__.py`）：已修，闭环。
- tasks_review_v1 SHOULD #2-#4：均为流程性 / 表述性，不阻塞本编码评审。

## Verdict

REVISION REQUIRED（MUST FIX 数 = 2）

## 复检指引

Generator 修完 v2 后，在仓库根逐条自检：

1. **MUST FIX #1 验证**（ghost 文件根除）：
   ```bash
   rm -f apps/web/vite.config.{js,d.ts} apps/web/*.tsbuildinfo
   pnpm --filter web build
   git status --porcelain apps/web/ | grep -E "tsbuildinfo|vite\.config\.(js|d\.ts)" && echo FAIL || echo PASS
   ```
   期望 PASS（输出 `PASS`）。
2. **MUST FIX #2 验证**（ci.yml web-test 命令）：
   ```bash
   grep -nE "pnpm.*--filter.*web.*test.*--run" .github/workflows/ci.yml && echo FAIL || echo PASS
   pnpm --filter web exec vitest run --reporter=junit --outputFile=/tmp/junit-web-test.xml && test -f /tmp/junit-web-test.xml && echo PASS
   ```
   两条均 PASS。
3. **SHOULD FIX #1 验证**：ci.yml `web-test` job 的 `--outputFile=` 路径与 `actions/upload-artifact.with.path` 完全一致（同为 `apps/web/junit-web.xml` 或同为 repo-root 相对路径）。
4. **17 条 AC 全量复跑**：按 spec §验收标准表 17 条 shell 命令逐条 exit 0，并附上 stage 5 test_report v1 的 pytest / vitest 输出片段。
5. **coding_report v2 §改动文件清单**：实测 `git status --porcelain` 的非 `??` 行数 = 报告声明的文件数（含 3 个生成产物 lockfile + openapi.json），无幽灵。
6. 修完后提交 `coding/review/code_review_v2.md`，本文件保留作历史。
