---
change_id: bootstrap-monorepo-20260516
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-agent:bootstrap-monorepo-stage2-reviewer
reviewed_at: 2026-05-16T20:50:00Z
verdict: REVISION REQUIRED
---

# Spec Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1（plan 模式 spec.md）。

- [x] 背景写明了为什么现在做（§背景 + §问题陈述 6 条空白）。
- [x] 问题陈述与目标可被外部读者理解。
- [x] 范围 / 非范围都有（17 条 AC + 9 条非范围）。
- [~] 每条 AC 可机械化——总体可行，但 AC-9 的命令本身有 bug（详见 MUST FIX #1）。
- [x] 风险有缓解措施或显式 accept（6 条）。
- [x] 没有把 design.md 当新提案——§范围严格收敛到"骨架 + hello world"。
- [x] 待澄清问题已清零（4 项全部 `[x]`）。

## 抽样验证结论

针对 §验收标准表抽 8 条 AC 在 `/tmp` 的 mock 目录里实跑命令 syntax：

| AC | 命令 syntax | 现实结果 |
|---|---|---|
| AC-1 | OK | 命令在缺文件时 exit 1 / 文件齐全时 exit 0（行为正确） |
| AC-3 | OK | 验证 turbo v2 `tasks` 字段 |
| AC-4 | OK | `make -n` 干跑 11 个 target |
| AC-5 | OK | wc + grep 双校验 |
| AC-6 | 一处不严谨（见 SHOULD FIX #2） | grep `"claude/settings.local.json"` 因子串匹配恰好成立 |
| AC-7 | OK | 5 个文件 + healthz grep |
| AC-9 | **BUG** | 命令含 U+200B ZERO WIDTH SPACE，且与 tasks T-9/T-10/T-11 的 src layout 不兼容（详见 MUST FIX #1） |
| AC-12 | OK | yaml.safe_load + 3 service |
| AC-14 | OK | ast.parse 静态校验（但与 AC 文字"可被 `python -m scripts.export_openapi` 调用"不等价，见 NICE） |
| AC-15 | OK | yaml + 5 job + concurrency |
| AC-16 | grep 模式过松（见 SHOULD FIX #1） | `1 failed in ...` 不命中，但 `1 passed 1 failed` 会命中 |

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md §验收标准 AC-9（行 77） | 命令字符串 `$d/dataplat_*/<U+200B>__init__.py` 在 `/` 与 `__` 之间嵌入了 ZERO WIDTH SPACE（U+200B，字节 `\342 \200 \213`），直接复制到 shell 会得到不存在的路径 → `test -f` 永远失败。同时，命令使用 bash glob `dataplat_*/__init__.py`，但 tasks.md T-9/T-10/T-11 明确每个包用 **src layout**（`src/dataplat_core/__init__.py`），即真实路径是 `$d/src/dataplat_*/__init__.py`。两层 bug 叠加，AC-9 在 stage 8 自检时必 FAIL。spec 自己在末尾注"实际命令需写明包名，详见 check 脚本"，说明作者已意识到不可机械化，但 AC 表是阶段质量门禁，不能用 hand-wave 补丁。 | 二选一并写在 AC 表里：(a) 改命令为 `for d_pkg in "packages/core:dataplat_core" "packages/sdk-py:dataplat_sdk" "worker:dataplat_worker"; do d=${d_pkg%:*}; p=${d_pkg#*:}; test -f $d/pyproject.toml && test -f $d/src/$p/__init__.py \|\| exit 1; done`；或 (b) 同时修改 tasks 改用 flat layout 并保留通配。两者择一并在 spec 显式去除 U+200B 字符。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md AC-16 验证方式（行 84） | `grep -E "passed\|0 failed"` 是松匹配：`1 passed, 1 failed` 也会因匹配子串 `passed` 而 exit 0，掩盖部分失败；spec 期望列写"passed == total"但命令没实现。 | 改用 `pytest --tb=no -q` 自身退出码（`set -o pipefail; uv run pytest ... -q`，依赖 `$?`），或加 `! grep -q " failed" output` 反向断言。 |
| 2 | spec.md AC-6 验证方式（行 74） | `for p in ... "claude/settings.local.json"` 缺前导 `.`；仅因 `.gitignore` 含 `.claude/settings.local.json` 而被子串匹配命中，是脆弱的，且与 §范围 写明的 `.claude/settings.local.json` 字面值不一致。 | 将列表项改为 `.claude/settings.local.json`。 |
| 3 | spec.md AC-14 描述与命令不一致（行 48 / 82） | 文字承诺"可被 `python -m scripts.export_openapi` 调用"，但 AC 表只做 `ast.parse` 静态语法校验，并未运行 `python -m`（也需要 `scripts/__init__.py`，tasks 未要求）。stage 8 自检只跑 AC 表，承诺会落空。 | 要么补 `python -m scripts.export_openapi --help`（或最小 dry-run）到 AC 表，并在 tasks T-16 加 `scripts/__init__.py`；要么把 AC 文字降级为"语法合法"。 |
| 4 | spec.md §风险表（行 87-96） | 风险表缺 2 条已被用户 prompt 点名的风险：(a) pnpm/npm registry 域名被墙（中国大陆典型阻塞，影响 AC-17 / T-8 / T-12）；(b) Makefile recipe 用空格而非 tab 的常见手误（影响 AC-4 整片）。 | 在 §风险表追加这两条，给出缓解（registry mirror 文档化；Makefile 用 `.RECIPEPREFIX` 或显式 tab 校验）。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md §范围 AC-4（行 38） | Makefile 含 `migrate` target，但 `apps/api/alembic/` 目录与 alembic 配置完全不在本变更范围。`make -n migrate` 干跑虽可通过 AC-4，但首次实跑会立即 FAIL，可能误导新成员。 | 在 §非范围或 AC-4 备注中加一句："`make migrate` 实跑需 alembic 配置，留给 `core-domain-model` 变更"。 |
| 2 | spec.md AC-12（行 80） | tasks T-14 明确含 `minio-init`（建 bucket）service，但 AC-12 只校验 postgres/minio/redis 三个。 | 在 AC-12 验证里加入 `minio-init`，或在 §非范围说明 minio-init 是实施细节，AC 不门禁。 |
| 3 | spec.md AC-15（行 83） | CI 触发条件文字写"PR + main push"，但 yaml 解析命令未校验 `on` 字段。 | 加 `assert 'pull_request' in d['on'] and 'push' in d['on']`。 |

## 与 design.md §11.3-§11.5 一致性

- §11.3 monorepo 树状结构与 spec §范围逐项核对：`apps/{api,web}/`、`packages/{core,api-types,sdk-py}/`、`worker/`、`plugins/`、`recipes/`、`docker/`、`scripts/`、`docs/` 均在 in-scope；`alembic/`、`docker-compose.test.yml`、`apps/api/dataplat_api/{routers,models,...}/` 子目录显式 deferred，无 scope creep。
- §11.4 Makefile 11 target 与 AC-4 一致。
- §11.5 CI 强契约（`make codegen && git diff --exit-code`）由 T-17 codegen-check job 覆盖；AC-15 显式列入 5 job，符合 design。
- 未发现 in-scope 超出 design.md 的项。

## Verdict

REVISION REQUIRED（MUST FIX 数 = 1）

## 复检指引

Generator 修完 spec_v2.md 后自检：

1. AC-9 字符层面：
   ```bash
   grep -P "[\x{200B}\x{200C}\x{200D}\x{FEFF}]" .harness/changes/bootstrap-monorepo-20260516/request_analysis/spec.md
   ```
   应无输出（无零宽字符）。
2. AC-9 与 tasks 一致性：把 AC-9 验证命令复制到 `/tmp/check9/` 下，按 T-9/T-10/T-11 的 src layout 创建文件（`src/dataplat_<core|sdk|worker>/__init__.py`），实跑 AC-9 命令 exit 0。
3. AC 表全部 8 条抽样命令在 `/tmp` 下能区分"文件齐全 / 缺文件"两种状态（齐全 exit 0，缺则 exit 1）。
4. §风险表条目数 ≥ 8（追加 pnpm registry + Makefile tab 两条），或在 spec 末尾说明为何拒绝追加。

提交 v2 后开 `spec_review_v2.md`。
